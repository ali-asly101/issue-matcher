# MILESTONES

Update the checkboxes as work completes. Each milestone ends with its acceptance check and a `docs/HANDOFF.md` entry. Owners come from the agent table in `CLAUDE.md`.

Legend: **[ ]** not started, **[~]** in progress, **[x]** done.

## M1: Foundation (Architect, QA) — Stage S0

- [x] Repo scaffold, docs, contract v1.
- [x] Toolchain: uv, ruff, mypy (strict), pytest. `./scripts/check.sh` green locally.
- [x] `config.py` and `models.py` match the contract.
- [x] Pure modules stubbed with tests: availability, ranking, graph.
- [x] Repo pushed to GitHub, CI green on the first push.
- [x] `.env` created from `.env.example` with a read-only `GITHUB_TOKEN`.

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
- [ ] Cold start: `--skill` declared skills and `--cv FILE` extraction (suggestions only until confirmed), `Skill.status` declared/practising/verified (`SKILL_PROFILE_SPEC`).
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

## Later stages (outline; detail each milestone when its stage starts)

### S3: Web app (solo)

- **M8 Backend skeleton (Web, Architect):** confirm stack; FastAPI app, Postgres schema + migrations, background worker, GitHub sign-in, Docker Compose for local dev. Engine runs as worker jobs.
- **M9 Solo web UI (Web, Map):** design system tokens (`DESIGN_SYSTEM`), landing page, onboarding with CV upload and skill chips, My work, My profile, Issue map for one GitHub repo; claim = assign to me on GitHub (with dry-run). Acceptance: owner uses the site instead of the CLI; a friend with no GitHub history gets useful picks from a CV alone.

### S4: Team platform

- **M10 Connector layer (Integrations, Architect):** contract v2 (`WorkItem`, `ExternalPerson`, ...); connector manifests + registry; Integrations directory rendered from manifests; refactor GitHub ingest into a `Connector`; shared connector contract tests; webhooks.
- **M11 GitLab + Jira connectors (Integrations):** OAuth, backfill, sync, webhooks, status/link mapping, identity linking.
- **M12 Team mode + approval flow (Ranking, Web):** workspaces, roles, best person per ticket, team board, approve -> write-back (assignee + comment), audit log, kill switch.
- **M13 Notifications (Web):** tracker-native notifications plus optional email/Slack digest of picks and assignments.

**S4 acceptance:** a test team plans a sprint through the site; Jira (or GitLab) shows the assignments and comments; every write is in the audit log.

## Standing tasks (every milestone)

- [ ] Run the definition-of-done checks from `CLAUDE.md`.
- [ ] Commit after every green task.
- [ ] Write a `HANDOFF.md` entry.
- [ ] Update this file.
