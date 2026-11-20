"""The one GitHub GraphQL client. Every network call to GitHub goes through it.

Behaviour (docs/INGEST_SPEC.md, "Rules"):

- Rate limit: every response's ``rateLimit { remaining resetAt cost }`` is read and
  logged at debug. When ``remaining`` drops below ``GITHUB_MIN_RATE_REMAINING`` the
  *next* request first waits until ``resetAt`` (not capped). Checking before the next
  request means the data already paid for is never thrown away.
- Inline-wait limit: any single wait longer than ``GITHUB_MAX_INLINE_WAIT_SECONDS``
  (a ``Retry-After`` or a rate-limit reset) sleeps only when ``wait_on_rate_limit``
  is True; otherwise it raises ``RateLimitExhaustedError`` without sleeping. Waits at
  or below the limit always sleep. Computed back-off is capped lower, so it never
  reaches this limit. Every sleep logs one INFO line with its length and reason.
- Back-off on HTTP 403/429/502: retry ``n`` (0-based) waits
  ``min(min(BASE * 2**n, MAX) * (1 + JITTER * r), MAX)`` with ``r`` in [0, 1).
  Jitter is added on top of the capped wait and the total is capped again, so no
  computed wait ever exceeds ``GITHUB_BACKOFF_MAX_SECONDS`` (once the raw wait hits
  the cap, jitter has no room left and the wait is exactly the cap).
- ``Retry-After`` replaces the computed wait exactly: no jitter, no cap. It still
  counts as a retry.
- 403/429 with ``x-ratelimit-remaining: 0`` (and no ``Retry-After``) is GitHub's
  primary rate limit, so it takes the rate-limit path, like a GraphQL error of
  type ``RATE_LIMITED``: wait until reset (counts as a retry; long waits follow the
  inline-wait limit). If GitHub gives no reset time, the normal back-off is used.
- Any other GraphQL error raises ``GraphQLError`` at once. 401 raises
  ``BadTokenError`` at once. Neither is retried.

The token is only ever placed in the Authorization header of the HTTP client; it is
never stored on this object, logged, or put in an error message.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from issuematch.config import Settings
from issuematch.github.errors import (
    BadTokenError,
    GraphQLError,
    MissingTokenError,
    RateLimitExhaustedError,
    RetriesExhaustedError,
    UnexpectedResponseError,
)

logger = logging.getLogger(__name__)

JSONObject = dict[str, Any]
"""A decoded GraphQL JSON object. Mapped into models by the ingest layer, not here."""

# HTTP statuses that are retried with back-off (fixed by INGEST_SPEC, not tunables).
_RETRY_STATUSES = frozenset({403, 429, 502})
_RATE_LIMIT_STATUSES = frozenset({403, 429})
_RATE_LIMITED_TYPE = "RATE_LIMITED"


class GitHubClient:
    """GraphQL client with pagination, rate-limit tracking and back-off.

    Args:
        settings: tunables (endpoint, page size, timeouts, retry rules).
        token: GitHub token. Missing or blank raises ``MissingTokenError`` at once.
        transport: optional httpx transport; tests pass ``httpx.MockTransport``.
        wait_on_rate_limit: for waits longer than GITHUB_MAX_INLINE_WAIT_SECONDS
            (rate-limit reset or Retry-After): sleep (True) or raise
            ``RateLimitExhaustedError`` (False).
        sleep: called with seconds to wait (injectable so tests never sleep).
        clock: returns the current Unix time in seconds.
        rand: returns a float in [0, 1) used for back-off jitter.
    """

    def __init__(
        self,
        settings: Settings,
        token: str | None,
        *,
        transport: httpx.BaseTransport | None = None,
        wait_on_rate_limit: bool = False,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        rand: Callable[[], float] = random.random,
    ) -> None:
        if token is None or not token.strip():
            raise MissingTokenError()
        self._settings = settings
        self._wait_on_rate_limit = wait_on_rate_limit
        self._sleep = sleep
        self._clock = clock
        self._rand = rand
        self._remaining: int | None = None
        self._reset_at: datetime | None = None
        self._http = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(settings.GITHUB_HTTP_TIMEOUT_SECONDS),
            headers={
                "Authorization": f"bearer {token.strip()}",
                "Accept": "application/json",
                "User-Agent": settings.APP_NAME,
            },
        )

    def __repr__(self) -> str:
        return (
            f"GitHubClient(url={self._settings.GITHUB_API_URL!r}, "
            f"wait_on_rate_limit={self._wait_on_rate_limit})"
        )

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    # --- public API ---

    def query(self, query: str, variables: Mapping[str, Any] | None = None) -> JSONObject:
        """Run one GraphQL query and return its ``data`` object.

        Retries 403/429/502 with back-off, honours ``Retry-After`` and the rate
        limit, and raises a ``GitHubError`` subclass on anything it cannot fix.
        """
        self._check_budget()
        payload = {"query": query, "variables": dict(variables or {})}
        retries = 0
        while True:
            response = self._http.post(self._settings.GITHUB_API_URL, json=payload)
            status = response.status_code

            if status == 401:
                raise BadTokenError()

            if status in _RETRY_STATUSES:
                retry_after = self._retry_after_seconds(response)
                if retry_after is not None:
                    retries = self._before_retry(
                        retries,
                        status,
                        retry_after,
                        f"Retry-After from GitHub (HTTP {status})",
                        long_wait_allowed=self._wait_on_rate_limit,
                    )
                elif self._is_primary_rate_limit(response):
                    retries = self._rate_limit_retry(
                        retries, status, self._header_reset(response), 0, f"HTTP {status}"
                    )
                else:
                    wait = self.backoff_seconds(retries)
                    reason = f"back-off after HTTP {status}"
                    retries = self._before_retry(retries, status, wait, reason)
                continue

            if status != 200:
                raise UnexpectedResponseError(status, "status is not retried")

            body = self._decode(response)
            data = body.get("data")
            if isinstance(data, dict):
                self._record_rate_limit(data.get("rateLimit"))

            errors = body.get("errors")
            if errors:
                messages, types = _error_details(errors)
                if _RATE_LIMITED_TYPE in types:
                    reset = self._header_reset(response) or self._reset_at
                    retries = self._rate_limit_retry(
                        retries, status, reset, self._remaining, "GraphQL RATE_LIMITED"
                    )
                    continue
                raise GraphQLError(messages, types)

            if not isinstance(data, dict):
                raise UnexpectedResponseError(status, "response has no 'data' object")
            return data

    def paginate(
        self,
        query: str,
        variables: Mapping[str, Any],
        *,
        connection_path: Sequence[str],
        limit: int | None = None,
    ) -> Iterator[JSONObject]:
        """Yield every node of a paginated connection, page by page.

        The query must declare ``$first: Int!`` and ``$after: String`` and select
        ``pageInfo { hasNextPage endCursor }`` and ``nodes`` on the connection found
        at ``connection_path`` inside ``data`` (e.g. ``("repository", "issues")``).
        ``first`` is ``GITHUB_PAGE_SIZE`` (smaller on the last page when ``limit``
        is set). Stops after ``limit`` nodes when given.
        """
        page_size = self._settings.GITHUB_PAGE_SIZE
        cursor: str | None = None
        yielded = 0
        while True:
            first = page_size if limit is None else min(page_size, limit - yielded)
            if first <= 0:
                return
            data = self.query(query, {**variables, "first": first, "after": cursor})
            connection = _dig(data, connection_path)
            for node in connection.get("nodes") or []:
                if node is None:
                    continue
                yield node
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            page_info = connection.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                return
            cursor = page_info.get("endCursor")
            if not cursor:
                raise UnexpectedResponseError(200, "hasNextPage is true but endCursor is empty")

    def backoff_seconds(self, retry: int) -> float:
        """Computed wait before retry number ``retry`` (0-based); see module docstring."""
        s = self._settings
        cap = s.GITHUB_BACKOFF_MAX_SECONDS
        wait = min(s.GITHUB_BACKOFF_BASE_SECONDS * 2.0**retry, cap)
        jitter = wait * s.GITHUB_BACKOFF_JITTER_FRACTION * self._rand()
        return min(wait + jitter, cap)

    # --- internals ---

    def _before_retry(
        self,
        retries: int,
        status: int,
        wait: float,
        reason: str,
        *,
        reset_at: datetime | None = None,
        remaining: int | None = None,
        long_wait_allowed: bool = True,
    ) -> int:
        """Sleep before the next attempt, or give up. Returns the new retry count."""
        max_retries = self._settings.GITHUB_MAX_RETRIES
        if wait > self._settings.GITHUB_MAX_INLINE_WAIT_SECONDS and not long_wait_allowed:
            self._raise_long_wait(wait, reset_at, remaining)
        if retries >= max_retries:
            raise RetriesExhaustedError(retries, status)
        self._wait(wait, f"{reason}, retry {retries + 1}/{max_retries}", reset_at, remaining)
        return retries + 1

    def _rate_limit_retry(
        self,
        retries: int,
        status: int,
        reset_at: datetime | None,
        remaining: int | None,
        source: str,
    ) -> int:
        """Rate-limit case on a response: wait until reset (counts as a retry) or raise."""
        if reset_at is None:
            # GitHub did not say when it resets; fall back to the normal back-off.
            return self._before_retry(
                retries,
                status,
                self.backoff_seconds(retries),
                f"back-off after {source} with unknown reset",
            )
        return self._before_retry(
            retries,
            status,
            self._seconds_until(reset_at),
            f"rate limit reset ({source})",
            reset_at=reset_at,
            remaining=remaining,
            long_wait_allowed=self._wait_on_rate_limit,
        )

    def _wait(
        self,
        seconds: float,
        reason: str,
        reset_at: datetime | None = None,
        remaining: int | None = None,
    ) -> None:
        """The only place the client sleeps. Logs exactly one INFO line per sleep.

        A wait longer than GITHUB_MAX_INLINE_WAIT_SECONDS only happens when
        ``wait_on_rate_limit`` is True; otherwise RateLimitExhaustedError is raised.
        """
        if seconds > self._settings.GITHUB_MAX_INLINE_WAIT_SECONDS and not (
            self._wait_on_rate_limit
        ):
            self._raise_long_wait(seconds, reset_at, remaining)
        logger.info("Waiting %.1f s: %s", seconds, reason)
        self._sleep(seconds)

    def _raise_long_wait(
        self, seconds: float, reset_at: datetime | None, remaining: int | None
    ) -> None:
        if reset_at is None:
            reset_at = datetime.fromtimestamp(self._clock() + seconds, UTC)
        raise RateLimitExhaustedError(reset_at, remaining, wait_seconds=seconds)

    def _check_budget(self) -> None:
        """Before a request: wait (or raise) if the last response left too few points."""
        if self._remaining is None or self._remaining >= self._settings.GITHUB_MIN_RATE_REMAINING:
            return
        if self._reset_at is None or self._seconds_until(self._reset_at) <= 0:
            self._remaining = None  # reset has passed (or is unknown): budget refilled
            return
        self._wait(
            self._seconds_until(self._reset_at),
            f"rate limit reset ({self._remaining} points left)",
            self._reset_at,
            self._remaining,
        )
        self._remaining = None

    def _record_rate_limit(self, rate_limit: object) -> None:
        if not isinstance(rate_limit, dict):
            logger.debug("GitHub response has no rateLimit field")
            return
        remaining = rate_limit.get("remaining")
        reset_raw = rate_limit.get("resetAt")
        if isinstance(remaining, int):
            self._remaining = remaining
        if isinstance(reset_raw, str):
            try:
                self._reset_at = datetime.fromisoformat(reset_raw)
            except ValueError:
                logger.debug("Unparseable rateLimit.resetAt: %r", reset_raw)
        logger.debug(
            "GitHub rate limit: remaining=%s cost=%s resetAt=%s",
            remaining,
            rate_limit.get("cost"),
            reset_raw,
        )

    def _seconds_until(self, moment: datetime) -> float:
        return max(0.0, moment.timestamp() - self._clock())

    def _retry_after_seconds(self, response: httpx.Response) -> float | None:
        raw = response.headers.get("retry-after")
        if raw is None:
            return None
        try:
            return max(0.0, float(raw))
        except ValueError:
            pass
        try:
            return self._seconds_until(parsedate_to_datetime(raw))
        except (TypeError, ValueError):
            logger.debug("Unparseable Retry-After header: %r", raw)
            return None

    @staticmethod
    def _is_primary_rate_limit(response: httpx.Response) -> bool:
        return (
            response.status_code in _RATE_LIMIT_STATUSES
            and response.headers.get("x-ratelimit-remaining") == "0"
        )

    @staticmethod
    def _header_reset(response: httpx.Response) -> datetime | None:
        raw = response.headers.get("x-ratelimit-reset")
        if raw is None:
            return None
        try:
            return datetime.fromtimestamp(int(raw), UTC)
        except ValueError:
            return None

    @staticmethod
    def _decode(response: httpx.Response) -> JSONObject:
        try:
            body = response.json()
        except ValueError as e:
            raise UnexpectedResponseError(response.status_code, "body is not JSON") from e
        if not isinstance(body, dict):
            raise UnexpectedResponseError(response.status_code, "body is not a JSON object")
        return body


def _error_details(errors: object) -> tuple[list[str], list[str]]:
    """Messages and types from a GraphQL ``errors`` array."""
    messages: list[str] = []
    types: list[str] = []
    items = errors if isinstance(errors, list) else [errors]
    for item in items:
        if isinstance(item, dict):
            messages.append(str(item.get("message", "")))
            types.append(str(item.get("type", "")))
        else:
            messages.append(str(item))
            types.append("")
    return messages, types


def _dig(data: JSONObject, path: Sequence[str]) -> JSONObject:
    node: Any = data
    for key in path:
        if not isinstance(node, dict) or not isinstance(node.get(key), dict):
            raise UnexpectedResponseError(200, f"no connection at {'.'.join(path)}")
        node = node[key]
    result: JSONObject = node
    return result
