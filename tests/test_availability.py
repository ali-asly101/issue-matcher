from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from issuematch.availability import is_available
from issuematch.config import Settings
from issuematch.models import LinkedPR, UnavailableReason
from tests.conftest import make_issue


def test_clean_open_issue_is_available(settings: Settings, now: datetime) -> None:
    result = is_available(make_issue(), settings, now)
    assert result.available
    assert result.reasons == []


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"state": "closed"}, UnavailableReason.CLOSED),
        ({"assignees": ["someone"]}, UnavailableReason.ASSIGNED),
        ({"labels": ["Blocked"]}, UnavailableReason.BLOCKED),
        ({"labels": ["needs design"]}, UnavailableReason.NEEDS_DESIGN),
        ({"labels": ["question"]}, UnavailableReason.NOT_ACTIONABLE),
    ],
)
def test_each_reason(
    settings: Settings, now: datetime, overrides: dict[str, object], reason: UnavailableReason
) -> None:
    result = is_available(make_issue(**overrides), settings, now)
    assert not result.available
    assert reason in result.reasons


def test_open_pr_blocks(settings: Settings, now: datetime) -> None:
    pr = LinkedPR(number=5, state="open", created_at=now)
    result = is_available(make_issue(linked_prs=[pr]), settings, now)
    assert UnavailableReason.OPEN_PR in result.reasons


def test_merged_pr_does_not_block(settings: Settings, now: datetime) -> None:
    pr = LinkedPR(number=5, state="closed", created_at=now)
    assert is_available(make_issue(linked_prs=[pr]), settings, now).available


def test_stale_uses_maintainer_activity_then_updated_at(settings: Settings, now: datetime) -> None:
    old = now - timedelta(days=settings.STALE_DAYS + 1)
    stale = is_available(make_issue(updated_at=old), settings, now)
    assert UnavailableReason.STALE in stale.reasons
    fresh_maint = make_issue(updated_at=old, last_maintainer_activity_at=now)
    assert is_available(fresh_maint, settings, now).available


def test_multiple_reasons_all_reported(settings: Settings, now: datetime) -> None:
    issue = make_issue(assignees=["a"], labels=["blocked", "question"])
    reasons = set(is_available(issue, settings, now).reasons)
    expected = {
        UnavailableReason.ASSIGNED,
        UnavailableReason.BLOCKED,
        UnavailableReason.NOT_ACTIONABLE,
    }
    assert expected <= reasons
