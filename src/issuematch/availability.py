"""Availability filter. Pure: no I/O. See docs/AVAILABILITY_SPEC.md. Owner: Ranking agent."""

from __future__ import annotations

from datetime import datetime, timedelta

from issuematch.config import Settings
from issuematch.models import AvailabilityResult, Issue, UnavailableReason


def _has_label(issue: Issue, wanted: tuple[str, ...]) -> bool:
    labels = {label.strip().lower() for label in issue.labels}
    return any(w.lower() in labels for w in wanted)


def is_available(issue: Issue, settings: Settings, now: datetime) -> AvailabilityResult:
    """Return whether someone could start this issue today, and every reason they can't."""
    reasons: list[UnavailableReason] = []

    if issue.state != "open":
        reasons.append(UnavailableReason.CLOSED)
    if issue.assignees:
        reasons.append(UnavailableReason.ASSIGNED)
    if any(pr.state == "open" for pr in issue.linked_prs):
        reasons.append(UnavailableReason.OPEN_PR)

    last_activity = issue.last_maintainer_activity_at or issue.updated_at
    if now - last_activity > timedelta(days=settings.STALE_DAYS):
        reasons.append(UnavailableReason.STALE)

    if _has_label(issue, settings.BLOCKED_LABELS):
        reasons.append(UnavailableReason.BLOCKED)
    if _has_label(issue, settings.NEEDS_DESIGN_LABELS):
        reasons.append(UnavailableReason.NEEDS_DESIGN)
    if _has_label(issue, settings.NOT_ACTIONABLE_LABELS):
        reasons.append(UnavailableReason.NOT_ACTIONABLE)

    return AvailabilityResult(available=not reasons, reasons=reasons)
