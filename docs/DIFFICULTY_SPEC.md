# DIFFICULTY SPEC

Owner: Estimator agent. Code: `src/issuematch/difficulty/`, `src/issuematch/llm/`, `src/issuematch/prompts/`.

## Goal

For each available open issue, estimate effort, concepts and likely files, with evidence and a confidence we can trust because it was **calibrated on closed issues**.

## Signal 1: history (primary, S1)

1. Find the `SIMILAR_K` most similar **closed** issues that have a merged linked PR (labels overlap + text similarity; embeddings when decided).
2. From their PRs: lines changed, files changed, time open to merge.
3. `effort` = weighted median of neighbours' normalised size: `min(1, lines / EFFORT_LINES_SATURATION)` blended with files count.
4. `est_hours_low/high` = interquartile range mapped through a simple lookup in config.
5. `likely_files` = most common files among neighbours' PRs.
6. `confidence` = f(neighbour count, neighbour agreement, similarity).

## Signal 2: LLM (S2, shortlist only)

- Run only on the top `LLM_SHORTLIST_SIZE` after history-based ranking.
- Input: issue title/body (truncated), labels, neighbours' summaries, repo file tree excerpt, `CONTRIBUTING.md` excerpt. Later: retrieved file contents.
- Output: JSON matching `DifficultyEstimate` fields (prompt: `prompts/difficulty_estimate.md`). Validate with Pydantic; on failure retry once, then fall back to history.
- Cache by hash of the full input.

## Blending and calibration

- `blended.effort = HISTORY_WEIGHT * history.effort + (1 - HISTORY_WEIGHT) * llm.effort`.
- Calibrate: run both estimators on held-out closed issues, compare to actual PR size, fit `HISTORY_WEIGHT` and a monotonic correction. Record results in `docs/evals/`.

## Non-actionable detection

Flag issues that are questions, discussions or wishes with no clear task (labels + simple text rules first). Report via `UnavailableReason.not_actionable`.

## Acceptance tests

- [ ] History estimator on fixtures returns effort in [0, 1] with evidence listing neighbour issue refs.
- [ ] No neighbours -> low confidence estimate, not an exception.
- [ ] LLM output that fails validation falls back to history.
- [ ] LLM is never called for issues outside the shortlist (test with a counting fake client).
