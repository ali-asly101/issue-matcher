from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from issuematch.config import Settings
from issuematch.models import Issue, IssueRef

NOW = datetime(2026, 11, 20, tzinfo=UTC)


@pytest.fixture
def settings() -> Settings:
    # Ignore any local .env so tests are deterministic.
    return Settings(_env_file=None)


@pytest.fixture
def now() -> datetime:
    return NOW


def make_issue(number: int = 1, **overrides: Any) -> Issue:
    data: dict[str, Any] = {
        "ref": IssueRef(repo="o/r", number=number),
        "title": f"Issue {number}",
        "state": "open",
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return Issue(**data)
