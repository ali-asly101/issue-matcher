"""Errors raised by the GitHub client. Messages never contain the token."""

from __future__ import annotations

from datetime import datetime


class GitHubError(Exception):
    """Base class for every GitHub client error."""


class MissingTokenError(GitHubError):
    """No GITHUB_TOKEN was given. Raised before any request is made."""

    def __init__(self) -> None:
        super().__init__(
            "GITHUB_TOKEN is not set. Copy .env.example to .env and put a read-only "
            "GitHub token in GITHUB_TOKEN (see .env.example for how to create one)."
        )


class BadTokenError(GitHubError):
    """GitHub answered 401: the token is wrong, expired or revoked. Never retried."""

    def __init__(self) -> None:
        super().__init__(
            "GitHub rejected the token (HTTP 401). Check GITHUB_TOKEN in .env: it may be "
            "mistyped, expired or revoked."
        )


class RateLimitExhaustedError(GitHubError):
    """GitHub asked for a wait longer than allowed inline, and waiting was not allowed.

    Raised for a rate-limit reset or a ``Retry-After`` longer than
    GITHUB_MAX_INLINE_WAIT_SECONDS when ``wait_on_rate_limit`` is False. The CLI maps
    this to exit code 3. ``reset_at`` is when the wait would end (None if unknown);
    ``wait_seconds`` is how long the wait would have been.
    """

    def __init__(
        self,
        reset_at: datetime | None,
        remaining: int | None = None,
        wait_seconds: float | None = None,
    ) -> None:
        self.reset_at = reset_at
        self.remaining = remaining
        self.wait_seconds = wait_seconds
        when = reset_at.isoformat() if reset_at else "an unknown time"
        left = f" ({remaining} points left)" if remaining is not None else ""
        super().__init__(
            f"GitHub rate limit reached{left}; it resets at {when}. "
            "Try again after that, or allow waiting for the reset."
        )


class RetriesExhaustedError(GitHubError):
    """GitHub kept answering 403/429/502 after every allowed retry."""

    def __init__(self, retries: int, last_status: int) -> None:
        self.retries = retries
        self.last_status = last_status
        super().__init__(
            f"GitHub still failed after {retries} retries (last HTTP status {last_status})."
        )


class GraphQLError(GitHubError):
    """GitHub answered with a GraphQL ``errors`` array (not a rate-limit error)."""

    def __init__(self, messages: list[str], types: list[str]) -> None:
        self.messages = messages
        self.types = types
        joined = "; ".join(f"{t}: {m}" if t else m for t, m in zip(types, messages, strict=True))
        super().__init__(f"GitHub GraphQL error: {joined}")


class UnexpectedResponseError(GitHubError):
    """Any other HTTP status, or a body that is not the expected GraphQL JSON."""

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        super().__init__(f"Unexpected GitHub response (HTTP {status}): {detail}")
