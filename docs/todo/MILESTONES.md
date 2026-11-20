# MILESTONES

Update the checkboxes as work completes. Each milestone ends with its acceptance check and a `docs/HANDOFF.md` entry. Owners come from the agent table in `CLAUDE.md`.

Legend: **[ ]** not started, **[~]** in progress, **[x]** done.

## M1: Foundation (Architect, QA) — Stage S0

- [x] Repo scaffold, docs, contract v1.
- [x] Toolchain: uv, ruff, mypy (strict), pytest. `./scripts/check.sh` green locally.
- [x] `config.py` and `models.py` match the contract.
- [x] Pure modules stubbed with tests: availability, ranking, graph.
- [ ] Repo pushed to GitHub, CI green on the first push.
- [ ] `.env` created from `.env.example` with a read-only `GITHUB_TOKEN`.

**Acceptance:** fresh clone -> `./scripts/setup.sh` -> `./scripts/check.sh` passes on the owner's machine and in CI.

## M2: Ingest (Ingest) — Stage S1

- [ ] GraphQL client with pagination, rate-limit tracking and back-off (`INGEST_SPEC`).
- [ ] Fetch open issues, closed issues (last `GITHUB_CLOSED_HISTORY_DAYS`), linked PRs with files changed and line counts.
- [ ] Map responses into `Issue` / `LinkedPR` models.
- [ ] SQLite store with incremental ingest.
- [ ] Recorded, scrubbed fixtures for 2 small repos in `tests/fixtures/`.
- [ ] `issuematch ingest owner/repo` prints counts.

**Acceptance:** ingest a ~500-issue repo twice; the second run makes only incremental requests and finishes in seconds.

## M3: Availability + profile (Ranking, Profile) — Stage S1

- [ ] Availability filter covers every `UnavailableReason` (`AVAILABILITY_SPEC`), with tests per reason.
- [ ] Skill profile from a user's public repos, commits and merged PRs (`SKILL_PROFILE_SPEC`).
- [ ] `--learn` and `--hours` self-declared inputs merged into the profile.
- [ ] `issuematch profile LOGIN` shows skills with evidence.

**Acceptance:** owner agrees their own profile is roughly right; zero assigned/PR-linked issues survive the filter on a real repo.

## M4: History-based difficulty (Estimator) — Stage S1

- [ ] Similar-closed-issue finder (labels + text similarity first, embeddings when decided).
- [ ] Effort from neighbours' PR size, files touched and time to merge (`DIFFICULTY_SPEC`).
- [ ] Confidence from neighbour count and agreement.

**Acceptance:** on held-out closed issues, predicted effort correlates with actual PR size (record the number in `docs/evals/`).

## M5: Ranking + CLI MVP (Ranking, Architect) — Stage S1

- [ ] `rank()` combines breakdown components with config weights (`RANKING_SPEC`).
- [ ] Reasons and first steps generated from evidence (no LLM yet).
- [ ] `issuematch match owner/repo --user LOGIN` end to end.

**Acceptance:** MVP success test in `docs/PLAN.md` on 3 repos.

## M6: LLM estimator + evals (Estimator, QA) — Stage S2

- [ ] LLM estimator on the shortlist with prompt in `prompts/difficulty_estimate.md`, structured output, cached.
- [ ] Calibration against closed issues; blended estimate.
- [ ] `issuematch eval` harness and baseline comparison (`EVALUATION_SPEC`).

**Acceptance:** blended estimate beats history-only on the eval set, within budget.

## M7: Issue map (Map) — Stage S2

- [ ] Edges: mentions, duplicates (embedding similarity), blocks (text patterns), same files (linked PRs).
- [ ] Clusters by area (paths + labels), cluster names.
- [ ] Exports: JSON, Mermaid, self-contained HTML (Cytoscape.js) with difficulty/fit colouring.
- [ ] Onboarding path: suggest A before B when B builds on A.

**Acceptance:** map for a 1,000-issue repo renders and the owner can name what each big cluster is.

## Standing tasks (every milestone)

- [ ] Run the definition-of-done checks from `CLAUDE.md`.
- [ ] Commit after every green task.
- [ ] Write a `HANDOFF.md` entry.
- [ ] Update this file.
