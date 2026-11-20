# EVALUATION SPEC

Owner: QA agent. Code: `issuematch eval`, results in `docs/evals/`.

## Goal

Know whether matching is good with a number, using the repo's own history as ground truth.

## Back-testing (no humans needed)

1. Pick a cutoff date `T` (e.g. 6 months ago).
2. Pretend it is `T`: issues open at `T` are candidates; each contributor's profile uses only evidence before `T`.
3. Ground truth: who actually fixed each issue after `T` (author of the merged linked PR).
4. Metrics:
   - **Person -> issues:** for each contributor who fixed something after `T`, recall@5 of the issues they actually fixed among their top picks.
   - **Issue -> person (team mode):** rank of the real fixer among candidate people.
   - **Difficulty:** Spearman correlation between predicted `effort` and actual PR lines changed.
   - **Availability:** precision (no picked issue had an open PR or assignee at `T`).
5. Baselines: random available issue; "good first issue" label only; label + language match.

## Human check

The MVP success test in `docs/PLAN.md`: 3 repos, owner + 2 friends rate picks (useful / not useful / already taken).

## Recording

One markdown file per run: `docs/evals/<YYYY-MM-DD>-<repo>.md` with config values used, metrics vs baselines, and notes. Never commit raw personal data; aggregate numbers only.
