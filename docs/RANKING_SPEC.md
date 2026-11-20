# RANKING SPEC

Owner: Ranking agent. Code: `src/issuematch/ranking.py` (pure).

## Goal

Order available issues by how good a fit they are for this person **now**, and explain why. Ranking never removes a claimable issue from what a person can see or claim; it only decides the order and what is highlighted.

## Components (each 0 to 1)

| Component | Meaning | v1 formula |
| --- | --- | --- |
| `skill_overlap` | how much of what the issue needs the person has | mean over required skills of the person's `level` for that skill (0 if missing); no required skills -> 0.5 |
| `stretch` | is it the right amount harder than comfortable | Gaussian on `gap = effort - comfort`, centred on `STRETCH_TARGET`, width `STRETCH_WIDTH`. `comfort` = mean skill level of required skills. Bonus when a required skill is in `want_to_learn`. |
| `effort_fit` | fits the time they have | 1 if `est_hours_high <= hours_per_week`; decays linearly to 0 at 4x; 0.7 if hours unknown |
| `responsiveness` | will maintainers review it | from repo PR review latency; 0.5 until measured |

`score = sum(weight_i * component_i) / sum(weights)` with `WEIGHT_SKILL`, `WEIGHT_STRETCH`, `WEIGHT_EFFORT`, `WEIGHT_RESPONSIVENESS`.

`confidence = min(difficulty.confidence, mean skill confidence of matched skills)` (0.3 floor if no skills). Picks below `MIN_CONFIDENCE` go in a separate "Less sure" group after the confident picks.

## Labels (what people see)

Numbers stay inside the engine. `Match` carries labels computed from config thresholds; every UI, CLI table, tracker comment and notification shows these, never the numbers.

| Label | Rule | Config |
| --- | --- | --- |
| Fit: **Great fit** / **Good fit** / **Possible fit** / **Weak match** | score at or above `FIT_LABEL_GREAT` / `FIT_LABEL_GOOD` / `FIT_LABEL_POSSIBLE` / below | `FIT_LABEL_*` |
| **Stretch** tag (extra, not a fit level) | `stretch` component high and effort above comfort | uses `STRETCH_TARGET` |
| Confidence: **High** / **Medium** / **Low confidence** | confidence at or above `CONFIDENCE_LABEL_HIGH` / `CONFIDENCE_LABEL_MEDIUM` / below | `CONFIDENCE_LABEL_*` |
| Effort: **Small** / **Medium** / **Large** / **Very large** | effort below `EFFORT_LABEL_SMALL` / `EFFORT_LABEL_MEDIUM` / `EFFORT_LABEL_LARGE` / above; shown with the hour range ("Medium, about 6 to 10 hours") | `EFFORT_LABEL_*` |

## Weak fit is advice, not a wall

When a person opens or claims a ticket labelled Weak match or Possible fit, the claim goes through as normal. Alongside it, show "These match your skills better" with up to 3 recommended tickets. Never a blocking dialog, never a disabled button, never a warning colour.

## Required skills for an issue

Built from the difficulty estimate: `concept:*` from `concepts`, `area:*` from top-level dirs of `likely_files`, `lang:*` from their extensions.

## Explanations

`reasons` are short, evidence-based sentences generated from the breakdown, e.g.:
- "You've merged 4 PRs touching `src/parser` (#812, #840...)."
- "Similar issues took 40 to 120 changed lines (#655, #702)."
- "Uses async, which you said you want to learn."

`first_steps`: likely files to read first, the nearest similar merged PR to study, and `CONTRIBUTING.md` if present.

## Acceptance tests

- [x] Score is in [0, 1] and monotonic in each component (see `tests/test_ranking.py`).
- [x] Stretch peaks at the target gap.
- [x] `rank()` sorts descending and respects `TOP_N`.
- [x] Labels: fit, confidence and effort labels follow the config thresholds (`tests/test_ranking.py`).
- [ ] Reasons cite at least one evidence ref per pick.
