# IssueMatch: Agent Rules

Working title. The name lives in one config value (`settings.APP_NAME` in `src/issuematch/config.py`); never hard-code it.

## What we're building

A tool that reads a GitHub repository, finds open issues, and recommends the ones a specific person can realistically handle and would grow from. It also draws a **map of the issues**: how they relate, cluster and block each other.

The pipeline is: **Ingest repo -> Profile the person -> Estimate issue difficulty -> Filter unavailable issues -> Rank by fit -> Explain + map.**

- **End goal:** a web platform that connects to Jira, GitLab and GitHub, matches tickets to people, and after a human approves, writes the assignment back to the tracker and notifies the person. See `docs/WEB_APP_SPEC.md` and `docs/INTEGRATIONS_SPEC.md`.
- **Solo mode** (first): one contributor, one open-source repo, as a CLI. This proves the matching engine.
- **Team mode** (S4): a team, their tracker and code history, roles; "best ticket for this person" and "best person for this ticket". See `docs/TEAM_MODE_SPEC.md`.
- Only build the stage `docs/PLAN.md` says is current. Later-stage specs exist so early code does not block them.

## Read first, in this order

1. This file.
2. `docs/PLAN.md` (roadmap, current stage, open questions).
3. `docs/CONTRACT.md` (data models, config keys, CLI, storage, output formats).
4. `docs/HANDOFF.md` (newest entry at the top).
5. `docs/todo/MILESTONES.md` (what is being worked on).
6. The `docs/*_SPEC.md` for the system you are touching.

If these files disagree, stop and list the conflict in `docs/HANDOFF.md`. Do not pick a side silently.

## Vocabulary

| Term | Meaning |
| --- | --- |
| Target repo | The GitHub repo being analysed (`owner/name`). |
| Person | Whoever we recommend issues to. A contributor in solo mode, an employee in team mode. |
| Skill profile | Evidence-backed skills of a Person (languages, areas, concepts, change size), each with a confidence. |
| Difficulty estimate | Structured guess of an issue's effort, concepts and files, with evidence and confidence. |
| Available | An issue someone could start today (not assigned, no open PR, not blocked, not stale-dead). |
| Fit score | 0 to 1 score combining skill overlap, stretch, effort vs time, and maintainer responsiveness. |
| Issue map | Graph of issues: nodes are issues, edges are relations, clusters are subsystems. |
| Stage S0 to S4 | **Development** stages in `docs/PLAN.md`. Not the same as product modes. |

## Folder map and ownership

| Path | What it is | Owner |
| --- | --- | --- |
| `src/issuematch/config.py`, `models.py` | Tunables and shared data models (the contract in code) | Architect only |
| `src/issuematch/github/` | GitHub GraphQL/REST client, rate limiting, caching | Ingest agent |
| `src/issuematch/store/` | SQLite cache and schema migrations | Ingest agent |
| `src/issuematch/profile/` | Skill profile builder | Profile agent |
| `src/issuematch/difficulty/` | Difficulty estimator (history + LLM) | Estimator agent |
| `src/issuematch/availability.py`, `ranking.py` | Filtering and fit scoring (pure) | Ranking agent |
| `src/issuematch/graph.py`, `src/issuematch/mapview/` | Issue map building and export | Map agent |
| `src/issuematch/llm/`, `src/issuematch/prompts/` | LLM client wrapper and prompt templates | Estimator agent |
| `src/issuematch/cli.py` | Command-line interface | Architect (wiring only) |
| `src/issuematch/connectors/` | Tracker connectors (GitHub, GitLab, Jira) and write-back (S4) | Integrations agent |
| `src/issuematch/api/`, `src/issuematch/worker/`, `web/` | Web backend, background jobs, frontend (S3+) | Web agent |
| `tests/`, `docs/evals/` | Tests, fixtures, evaluation runs | QA agent |
| `docs/` | Plans and specs | Architect, plus the spec's author |

## Hard rules

1. **Evidence or it didn't happen.** Every recommendation, difficulty estimate and skill claim carries the evidence behind it (linked PRs, files, commits) and a confidence. Never output a bare "you can do this".
2. **No magic numbers.** Every weight, threshold, limit and model name lives in `src/issuematch/config.py` with a comment saying what it does and its unit.
3. **Do not change `docs/CONTRACT.md` casually.** A new model field, CLI flag, config key or table goes into the contract in the same change and is listed under "Changed contract" in `docs/HANDOFF.md`.
4. **Stay in your lane.** Edit only the folders your task owns. Need a change elsewhere? Write it as a request in `docs/HANDOFF.md`.
5. **Small, reviewable changes.** One task, one commit.
6. **Pure core, thin edges.** Scoring, filtering, graph building and calibration are pure functions on models with no network or disk, so they are unit-tested without mocks. Network (GitHub, LLM) and storage live at the edges.
7. **Respect GitHub.** Use GraphQL with pagination, honour rate-limit headers, back off on 403/429, cache everything in the store, never hammer an API in a loop. Tests never hit the network; use fixtures in `tests/fixtures/`.
8. **LLM spend is budgeted.** Embeddings and cheap filters first; the LLM only runs on the shortlist (`settings.LLM_SHORTLIST_SIZE`). Cache every LLM response by input hash.
9. **Writes to a tracker need approval.** Only the approval flow may call connector write methods, always with an idempotency key, honouring dry-run and the kill switch (`docs/INTEGRATIONS_SPEC.md`).
10. **Never block a person from work.** Anyone may claim any open, unassigned ticket, whatever their fit, seniority, skills or profile strength. Fit only orders and explains; it never hides or disables. When the fit is weak, suggest better-matching tickets alongside, never in place of the claim. Only closed tickets and tickets already assigned to someone else are not claimable (taking over someone's ticket goes through the lead or the tracker as usual).
11. **Labels, not numbers, for people.** Scores and confidences are numbers inside the engine only. Every user-facing surface (web, CLI default output, comments written to trackers, notifications) shows plain labels: "Great fit", "Good fit", "Possible fit", "Weak match"; "High / Medium / Low confidence"; "Small / Medium / Large / Very large". Raw numbers appear only in `--json`, logs and evals.
12. **Never invent features.** If a spec is silent, pick the simplest sensible default, put it in config, state it in the handoff, and add an open question to `docs/PLAN.md` if it matters.

## Python conventions

- Python 3.12+. Type hints on everything public; `mypy --strict` must pass on `src/`.
- Data models are Pydantic v2 models in `models.py`. Do not pass raw dicts between modules.
- `httpx` for HTTP, `typer` for the CLI, stdlib `sqlite3` for the store. Ask before adding a dependency; add it with `uv add` and say why in the handoff.
- No global mutable state. Pass `Settings` and clients in explicitly.
- Logging through `logging`, never `print` (except CLI output in `cli.py`).
- Prefer the simplest thing that works. No frameworks for their own sake.

## Secrets and privacy

- Tokens come from environment variables only (`GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, later `JIRA_*`). See `.env.example`. Never write a token into a file, log, fixture or test.
- Fixtures are scrubbed: no tokens, no emails, no private repo data.
- Team mode handles personal data. Follow `docs/PRIVACY_SPEC.md`: profiles are visible and editable by the person, data is used for matching only (never ranking people against each other), and a human always makes the final assignment.

## Definition of done

A task is done only when all of these pass. Say which you could not run.

1. `uv run ruff check .` is clean.
2. `uv run ruff format --check .` is clean.
3. `uv run mypy` is clean.
4. `uv run pytest` passes (offline, fixtures only).
5. If you touched matching quality: an eval run is recorded in `docs/evals/` (see `docs/EVALUATION_SPEC.md`).
6. `docs/HANDOFF.md` has a new entry using the template.

Shortcut: `./scripts/check.sh` runs 1 to 4.

## Working in parallel

Split by folder and spec, never by "feature slices" that touch the same files.

| Agent | Owns | Spec |
| --- | --- | --- |
| Architect (main session) | `CLAUDE.md`, `docs/`, `config.py`, `models.py`, `cli.py` wiring | all |
| Ingest | `github/`, `store/` | INGEST |
| Profile | `profile/` | SKILL_PROFILE |
| Estimator | `difficulty/`, `llm/`, `prompts/` | DIFFICULTY |
| Ranking | `availability.py`, `ranking.py` | AVAILABILITY, RANKING |
| Map | `graph.py`, `mapview/` | ISSUE_MAP |
| Integrations (S4) | `connectors/` | INTEGRATIONS |
| Web (S3+) | `api/`, `worker/`, `web/` | WEB_APP |
| QA | `tests/`, `docs/evals/` | EVALUATION, all acceptance tests |

Agent definitions live in `.claude/agents/`. Two agents never edit the same file; if they must, the Architect decides the order.

## Handoff

When you finish a task, add an entry at the top of `docs/HANDOFF.md` using its template: changed contract, files, how it was tested, what the owner must do by hand, and what was **not** tested. Do not claim more than you verified.

## Git

- Commit after every green task: `M2: availability filter for assigned and PR-linked issues`.
- Never force-push or rewrite history. Never commit `.env`, tokens, `data/` caches or `build/` output.

## Talking to the owner

Explain decisions in plain language with the trade-off. Ask only when the answer would change the direction; otherwise choose a default, say what you chose and why, and make it a config value.
