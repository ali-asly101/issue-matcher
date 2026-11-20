# AVAILABILITY SPEC

Owner: Ranking agent. Code: `src/issuematch/availability.py` (pure).

## Goal

Decide which issues to **recommend** (someone could start them today) and which issues a person can **claim**. These are different on purpose: availability shapes recommendations, it never blocks a person (CLAUDE.md hard rule 10).

- **Recommended** (`available`): no reasons below. Only these appear as picks.
- **Claimable** (`claimable`): open and not assigned to someone else. A person can claim any claimable issue from the full ticket list, even if it is not recommended for them. Stale, blocked, needs-design or not-actionable issues stay claimable and show their reason as a note ("No maintainer activity for 6 months") so the person decides.

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

`AvailabilityResult(available = not reasons, claimable = not (closed or assigned), reasons = [...])`. An issue with an open linked PR by someone else stays claimable but is labelled "Someone has a PR open". The CLI can show not-recommended counts by reason (`--show-filtered`); the web app always offers "Show all tickets".

## Acceptance tests

- [x] One test per reason (see `tests/test_availability.py`).
- [x] A clean open issue is available with no reasons.
- [x] Multiple reasons are all reported.
- [x] Stale, blocked, needs-design and not-actionable issues are not recommended but remain claimable; closed or assigned issues are not claimable.
