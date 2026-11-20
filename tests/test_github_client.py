"""GitHubClient: pagination, rate limits, back-off, error handling. Offline only.

Every test injects httpx.MockTransport, a fake sleep that records waits, a fixed clock
and a fixed random source, so nothing touches the network or actually sleeps.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from issuematch.config import Settings
from issuematch.github import (
    BadTokenError,
    GitHubClient,
    GraphQLError,
    MissingTokenError,
    RateLimitExhaustedError,
    RetriesExhaustedError,
)

FAKE_TOKEN = "ghp_FAKE_TOKEN_never_real_0123456789"
NOW = datetime(2026, 11, 20, 12, 0, 0, tzinfo=UTC)
RESET = NOW + timedelta(minutes=10)
RESET_ISO = RESET.strftime("%Y-%m-%dT%H:%M:%SZ")

ISSUES_QUERY = """
query($owner: String!, $name: String!, $first: Int!, $after: String) {
  rateLimit { remaining resetAt cost }
  repository(owner: $owner, name: $name) {
    issues(first: $first, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { number }
    }
  }
}
"""


def rate(remaining: int = 4000, reset: str = RESET_ISO) -> dict[str, Any]:
    return {"remaining": remaining, "resetAt": reset, "cost": 1}


def ok(data: dict[str, Any] | None = None, remaining: int = 4000) -> httpx.Response:
    payload = {"rateLimit": rate(remaining), **(data or {})}
    return httpx.Response(200, json={"data": payload})


class Recorder:
    """MockTransport handler that replays queued responses and records requests."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        assert self.responses, "client made more requests than the test expected"
        return self.responses.pop(0)

    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(r.content) for r in self.requests]


class FakeSleep:
    def __init__(self) -> None:
        self.waits: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.waits.append(seconds)


def make_client(
    settings: Settings,
    recorder: Recorder,
    *,
    sleep: FakeSleep | None = None,
    wait_on_rate_limit: bool = False,
    rand: Callable[[], float] = lambda: 0.0,
    token: str | None = FAKE_TOKEN,
) -> GitHubClient:
    return GitHubClient(
        settings,
        token,
        transport=httpx.MockTransport(recorder),
        wait_on_rate_limit=wait_on_rate_limit,
        sleep=sleep or FakeSleep(),
        clock=lambda: NOW.timestamp(),
        rand=rand,
    )


def issues_page(numbers: list[int], cursor: str | None, has_next: bool) -> httpx.Response:
    return ok(
        {
            "repository": {
                "issues": {
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                    "nodes": [{"number": n} for n in numbers],
                }
            }
        }
    )


# --- 1. Pagination ---


def test_paginate_three_pages_yields_every_node_once(settings: Settings) -> None:
    rec = Recorder(
        [
            issues_page([1, 2], "c1", True),
            issues_page([3, 4], "c2", True),
            issues_page([5], "c3", False),
        ]
    )
    client = make_client(settings, rec)
    nodes = list(
        client.paginate(
            ISSUES_QUERY, {"owner": "o", "name": "r"}, connection_path=("repository", "issues")
        )
    )
    assert [n["number"] for n in nodes] == [1, 2, 3, 4, 5]
    bodies = rec.bodies()
    assert [b["variables"]["after"] for b in bodies] == [None, "c1", "c2"]
    assert all(b["variables"]["first"] == settings.GITHUB_PAGE_SIZE for b in bodies)
    assert all(b["variables"]["owner"] == "o" for b in bodies)


def test_paginate_stops_at_limit(settings: Settings) -> None:
    rec = Recorder([issues_page([1, 2], "c1", True), issues_page([3, 4], "c2", True)])
    client = make_client(settings, rec)
    nodes = list(
        client.paginate(ISSUES_QUERY, {}, connection_path=("repository", "issues"), limit=3)
    )
    assert [n["number"] for n in nodes] == [1, 2, 3]
    assert len(rec.requests) == 2


def test_request_sends_bearer_token_and_query(settings: Settings) -> None:
    rec = Recorder([ok({"viewer": {"login": "x"}})])
    client = make_client(settings, rec)
    data = client.query("{ viewer { login } }")
    assert data["viewer"] == {"login": "x"}
    req = rec.requests[0]
    assert req.method == "POST"
    assert str(req.url) == settings.GITHUB_API_URL
    assert req.headers["Authorization"] == f"bearer {FAKE_TOKEN}"
    assert rec.bodies()[0] == {"query": "{ viewer { login } }", "variables": {}}


# --- 2. Rate limit (rateLimit.remaining) ---


def test_low_remaining_raises_without_wait(settings: Settings) -> None:
    low = settings.GITHUB_MIN_RATE_REMAINING - 1
    rec = Recorder([ok(remaining=low), ok()])
    client = make_client(settings, rec)
    client.query("{ a }")  # the response itself is fine and returned
    with pytest.raises(RateLimitExhaustedError) as exc:
        client.query("{ b }")
    assert exc.value.reset_at == RESET
    assert len(rec.requests) == 1  # the second request was never sent


def test_low_remaining_waits_until_reset_when_allowed(settings: Settings) -> None:
    low = settings.GITHUB_MIN_RATE_REMAINING - 1
    rec = Recorder([ok(remaining=low), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, wait_on_rate_limit=True)
    client.query("{ a }")
    client.query("{ b }")
    # 10 minutes, not capped by GITHUB_BACKOFF_MAX_SECONDS
    assert sleep.waits == [600.0]
    assert len(rec.requests) == 2


def test_remaining_at_threshold_does_not_wait(settings: Settings) -> None:
    rec = Recorder([ok(remaining=settings.GITHUB_MIN_RATE_REMAINING), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep)
    client.query("{ a }")
    client.query("{ b }")
    assert sleep.waits == []


def test_rate_limit_logged_at_debug(settings: Settings, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="issuematch.github")
    client = make_client(settings, Recorder([ok(remaining=4321)]))
    client.query("{ a }")
    assert any("4321" in r.getMessage() and r.levelno == logging.DEBUG for r in caplog.records)


def test_http_rate_limit_headers_follow_rate_limit_path(settings: Settings) -> None:
    headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(RESET.timestamp()))}
    rec = Recorder([httpx.Response(403, headers=headers, json={"message": "rate limit"})])
    client = make_client(settings, rec)
    with pytest.raises(RateLimitExhaustedError) as exc:
        client.query("{ a }")
    assert exc.value.reset_at == RESET
    assert len(rec.requests) == 1


# --- 3. Back-off on 403 / 429 / 502 ---


@pytest.mark.parametrize("status", [403, 429, 502])
def test_backoff_waits_grow_then_succeed(settings: Settings, status: int) -> None:
    rec = Recorder([httpx.Response(status), httpx.Response(status), httpx.Response(status), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep)
    client.query("{ a }")
    base = settings.GITHUB_BACKOFF_BASE_SECONDS
    assert sleep.waits == [base, base * 2, base * 4]
    assert len(rec.requests) == 4


def test_backoff_adds_jitter(settings: Settings) -> None:
    rec = Recorder([httpx.Response(502), httpx.Response(502), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, rand=lambda: 0.5)
    client.query("{ a }")
    base = settings.GITHUB_BACKOFF_BASE_SECONDS
    frac = settings.GITHUB_BACKOFF_JITTER_FRACTION
    assert sleep.waits == pytest.approx([base * (1 + 0.5 * frac), 2 * base * (1 + 0.5 * frac)])


def test_backoff_is_capped_including_jitter(settings: Settings) -> None:
    s = settings.model_copy(
        update={
            "GITHUB_BACKOFF_BASE_SECONDS": 10.0,
            "GITHUB_BACKOFF_MAX_SECONDS": 30.0,
            "GITHUB_MAX_RETRIES": 4,
        }
    )
    rec = Recorder([httpx.Response(429)] * 4 + [ok()])
    sleep = FakeSleep()
    client = make_client(s, rec, sleep=sleep, rand=lambda: 0.999)
    client.query("{ a }")
    # raw waits 10, 20, 40, 80 (+ up to 25% jitter): every total stays within 30
    assert sleep.waits[0] == pytest.approx(10.0 * (1 + 0.999 * 0.25))
    assert sleep.waits[1:] == pytest.approx([20.0 * (1 + 0.999 * 0.25), 30.0, 30.0])
    assert max(sleep.waits) <= 30.0


def test_backoff_gives_up_after_max_retries(settings: Settings) -> None:
    n = settings.GITHUB_MAX_RETRIES
    rec = Recorder([httpx.Response(502)] * (n + 1))
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep)
    with pytest.raises(RetriesExhaustedError) as exc:
        client.query("{ a }")
    assert len(rec.requests) == n + 1  # first try plus n retries
    assert len(sleep.waits) == n
    assert exc.value.last_status == 502


# --- 4. Retry-After ---


def test_retry_after_used_instead_of_backoff_and_not_capped(settings: Settings) -> None:
    big = settings.GITHUB_BACKOFF_MAX_SECONDS + 60
    rec = Recorder([httpx.Response(403, headers={"Retry-After": str(int(big))}), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, rand=lambda: 0.9)
    client.query("{ a }")
    assert sleep.waits == [big]  # exact: no jitter, no cap


def test_retry_after_counts_as_retry(settings: Settings) -> None:
    n = settings.GITHUB_MAX_RETRIES
    rec = Recorder([httpx.Response(403, headers={"Retry-After": "7"})] * (n + 1))
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep)
    with pytest.raises(RetriesExhaustedError):
        client.query("{ a }")
    assert sleep.waits == [7.0] * n
    assert len(rec.requests) == n + 1


# --- 5. GraphQL errors on HTTP 200 ---


def rate_limited(with_rate: bool = True) -> httpx.Response:
    body: dict[str, Any] = {"errors": [{"type": "RATE_LIMITED", "message": "API rate limit"}]}
    if with_rate:
        body["data"] = {"rateLimit": rate(0)}
    return httpx.Response(200, json=body)


def test_graphql_rate_limited_raises_without_wait(settings: Settings) -> None:
    rec = Recorder([rate_limited()])
    client = make_client(settings, rec)
    with pytest.raises(RateLimitExhaustedError) as exc:
        client.query("{ a }")
    assert exc.value.reset_at == RESET
    assert len(rec.requests) == 1


def test_graphql_rate_limited_waits_until_reset_then_retries(settings: Settings) -> None:
    rec = Recorder([rate_limited(), ok({"x": 1})])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, wait_on_rate_limit=True)
    data = client.query("{ a }")
    assert data["x"] == 1
    assert sleep.waits == [600.0]
    assert len(rec.requests) == 2


def test_graphql_rate_limited_reset_from_header(settings: Settings) -> None:
    body = {"errors": [{"type": "RATE_LIMITED", "message": "API rate limit"}]}
    headers = {"x-ratelimit-reset": str(int(RESET.timestamp()))}
    rec = Recorder([httpx.Response(200, headers=headers, json=body)])
    client = make_client(settings, rec)
    with pytest.raises(RateLimitExhaustedError) as exc:
        client.query("{ a }")
    assert exc.value.reset_at == RESET


def test_other_graphql_error_raises_without_retry(settings: Settings) -> None:
    body = {
        "data": None,
        "errors": [{"type": "NOT_FOUND", "message": "Could not resolve to a Repository"}],
    }
    rec = Recorder([httpx.Response(200, json=body), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep)
    with pytest.raises(GraphQLError) as exc:
        client.query("{ a }")
    assert len(rec.requests) == 1
    assert sleep.waits == []
    assert exc.value.types == ["NOT_FOUND"]
    assert "Could not resolve to a Repository" in str(exc.value)


# --- 6. 401 ---


def test_401_no_retry_and_points_to_env(settings: Settings) -> None:
    rec = Recorder([httpx.Response(401, json={"message": "Bad credentials"}), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep)
    with pytest.raises(BadTokenError) as exc:
        client.query("{ a }")
    assert len(rec.requests) == 1
    assert sleep.waits == []
    assert "GITHUB_TOKEN" in str(exc.value)
    assert ".env" in str(exc.value)


# --- 7. Missing token ---


@pytest.mark.parametrize("token", [None, "", "   "])
def test_missing_token_fails_before_any_request(settings: Settings, token: str | None) -> None:
    rec = Recorder([])
    with pytest.raises(MissingTokenError) as exc:
        make_client(settings, rec, token=token)
    assert ".env.example" in str(exc.value)
    assert rec.requests == []


# --- 8. Token never leaks ---


def test_token_never_in_logs_or_errors(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    errors: list[Exception] = []
    scenarios: list[list[httpx.Response]] = [
        [ok(), ok(remaining=0), ok()],
        [httpx.Response(401)],
        [httpx.Response(502)] * (settings.GITHUB_MAX_RETRIES + 1),
        [httpx.Response(200, json={"errors": [{"type": "X", "message": "boom"}]})],
        [rate_limited()],
    ]
    for responses in scenarios:
        client = make_client(settings, Recorder(responses))
        try:
            for _ in range(3):
                client.query("{ a }")
        except Exception as e:
            errors.append(e)
        assert FAKE_TOKEN not in repr(client)
    assert len(errors) == len(scenarios)
    for e in errors:
        assert FAKE_TOKEN not in str(e)
        assert FAKE_TOKEN not in repr(e)
    assert FAKE_TOKEN not in caplog.text
    for record in caplog.records:
        assert FAKE_TOKEN not in record.getMessage()


# --- 9. Inline-wait limit (GITHUB_MAX_INLINE_WAIT_SECONDS) ---


@pytest.mark.parametrize("wait_allowed", [False, True])
def test_long_retry_after_follows_wait_setting(settings: Settings, wait_allowed: bool) -> None:
    long_wait = settings.GITHUB_MAX_INLINE_WAIT_SECONDS + 1
    rec = Recorder([httpx.Response(403, headers={"Retry-After": str(long_wait)}), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, wait_on_rate_limit=wait_allowed)
    if wait_allowed:
        client.query("{ a }")
        assert sleep.waits == [long_wait]
        assert len(rec.requests) == 2
    else:
        with pytest.raises(RateLimitExhaustedError) as exc:
            client.query("{ a }")
        assert sleep.waits == []
        assert len(rec.requests) == 1
        assert exc.value.wait_seconds == long_wait
        assert exc.value.reset_at == NOW + timedelta(seconds=long_wait)


@pytest.mark.parametrize("wait_allowed", [False, True])
def test_long_reset_follows_wait_setting(settings: Settings, wait_allowed: bool) -> None:
    # GraphQL RATE_LIMITED with a reset 600 s away (> 300 s limit)
    rec = Recorder([rate_limited(), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, wait_on_rate_limit=wait_allowed)
    if wait_allowed:
        client.query("{ a }")
        assert sleep.waits == [600.0]
    else:
        with pytest.raises(RateLimitExhaustedError) as exc:
            client.query("{ a }")
        assert sleep.waits == []
        assert exc.value.reset_at == RESET
        assert exc.value.wait_seconds == 600.0


def test_retry_after_at_limit_sleeps_even_without_wait(settings: Settings) -> None:
    limit = settings.GITHUB_MAX_INLINE_WAIT_SECONDS
    rec = Recorder([httpx.Response(429, headers={"Retry-After": str(limit)}), ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, wait_on_rate_limit=False)
    client.query("{ a }")
    assert sleep.waits == [limit]


def test_short_reset_sleeps_even_without_wait(settings: Settings) -> None:
    soon = (NOW + timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "data": {"rateLimit": rate(0, reset=soon)},
        "errors": [{"type": "RATE_LIMITED", "message": "API rate limit"}],
    }
    rec = Recorder([httpx.Response(200, json=body), ok({"x": 1})])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, wait_on_rate_limit=False)
    assert client.query("{ a }")["x"] == 1
    assert sleep.waits == [20.0]


def test_short_low_remaining_reset_sleeps_even_without_wait(settings: Settings) -> None:
    soon = (NOW + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    low = settings.GITHUB_MIN_RATE_REMAINING - 1
    first = httpx.Response(200, json={"data": {"rateLimit": rate(low, reset=soon)}})
    rec = Recorder([first, ok()])
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, wait_on_rate_limit=False)
    client.query("{ a }")
    client.query("{ b }")
    assert sleep.waits == [5.0]


def test_each_sleep_logs_one_info_line(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger="issuematch.github")
    low = settings.GITHUB_MIN_RATE_REMAINING - 1
    rec = Recorder(
        [
            httpx.Response(502),
            httpx.Response(403, headers={"Retry-After": "9"}),
            rate_limited(),
            ok(remaining=low),
            ok(),
        ]
    )
    sleep = FakeSleep()
    client = make_client(settings, rec, sleep=sleep, wait_on_rate_limit=True)
    client.query("{ a }")
    client.query("{ b }")
    info = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert len(info) == len(sleep.waits) == 4
    n = settings.GITHUB_MAX_RETRIES
    assert "1.0 s" in info[0] and f"back-off after HTTP 502, retry 1/{n}" in info[0]
    assert "9.0 s" in info[1] and "Retry-After from GitHub" in info[1]
    assert "600.0 s" in info[2] and "rate limit reset" in info[2]
    assert "600.0 s" in info[3] and "rate limit reset" in info[3]
    assert all(FAKE_TOKEN not in m for m in info)
