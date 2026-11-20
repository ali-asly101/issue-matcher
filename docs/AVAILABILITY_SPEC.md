# AVAILABILITY SPEC

Owner: Ranking agent. Code: `src/issuematch/availability.py` (pure).

## Goal

Never recommend an issue someone can't actually start today. This is where most "good first issue" finders fail.

## Reasons (an issue can have several)

| Reason | Rule | Config |
| --- | --- | --- |
| `closed` | `state != open` | - |
| `assigned` | `assignees` not empty | - |
| `open_pr` | any `linked_prs` with `state == open` | - |
| `stale` | no maintainer activity for `STALE_DAYS` (falls back to `updated_at`) | `STALE_DAYS` |
| `blocked` | has a label in `BLOCKED_LABELS` | `BLOCKED_LABELS` |
| `needs_design` | has a label in `NEEDS_DESIGN_LABELS` | `NEEDS_DESIGN_LABELS` |
| `not_actionable` | has a label in `NOT_ACTIONABLE_LABELS` (later also the classifier) | `NOT_ACTIONABLE_LABELS` |

Label matching is case-insensitive.

## Output

`AvailabilityResult(available = not reasons, reasons = [...])`. The CLI can show filtered-out counts by reason (`--show-filtered`).

## Acceptance tests

- [x] One test per reason (see `tests/test_availability.py`).
- [x] A clean open issue is available with no reasons.
- [x] Multiple reasons are all reported.
