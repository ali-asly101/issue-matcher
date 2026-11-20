# CONTRACT

The shared interfaces every agent builds against. Version: **1**. Change this file only on purpose, and log it in `docs/HANDOFF.md`. The code form of this contract is `src/issuematch/models.py` and `src/issuematch/config.py`; if they disagree with this file, that is a bug: report it.

## 1. Principles

- Modules talk through the Pydantic models below, never raw dicts.
- Pure modules (`availability`, `ranking`, `graph`, calibration) take models and `Settings`, return models. No I/O.
- Network and disk live in `github/`, `llm/`, `store/` only.
- Every score is in `[0, 1]`. Every estimate has `confidence` in `[0, 1]` and a list of `Evidence`.

## 2. Package layout

```text
src/issuematch/
  config.py          Settings (all tunables) - Architect
  models.py          shared Pydantic models - Architect
  cli.py             Typer app, wiring only - Architect
  github/            client.py (GraphQL + REST), queries.py, ratelimit.py - Ingest
  store/             db.py (SQLite), schema.sql, migrations - Ingest
  profile/           builder.py (evidence -> SkillProfile) - Profile
  difficulty/        history.py (similar closed issues), llm_estimator.py, calibrate.py - Estimator
  llm/               client.py (provider wrapper, response cache) - Estimator
  prompts/           *.md prompt templates - Estimator
  availability.py    is_available(issue, settings) -> AvailabilityResult - Ranking
  ranking.py         fit_score(...) and rank(...) - Ranking
  graph.py           build_issue_graph(...), to_mermaid(...), to_json(...) - Map
  mapview/           interactive HTML export (S2) - Map
  connectors/        Connector protocol + github/gitlab/jira (S4, contract v2) - Integrations
  api/, worker/      FastAPI app and background jobs (S3+) - Web
web/                 React frontend (S3+) - Web
```

Planned for contract v2 (M10): provider-neutral `WorkItem`, `ExternalPerson`, `Contribution`, `Project`, `WriteResult`, `ChangeEvent`, `Approval`, and the `Connector` protocol in `docs/INTEGRATIONS_SPEC.md`. Until then the engine uses `Issue`.

## 3. Data models (`models.py`)

| Model | Key fields |
| --- | --- |
| `Evidence` | `kind` (`pr`, `issue`, `commit`, `file`, `review`, `self_declared`, `cv`), `ref` (URL or id), `note` |
| `IssueRef` | `repo` (`owner/name`), `number` |
| `Issue` | `ref`, `title`, `body`, `state` (`open`/`closed`), `labels`, `author`, `assignees`, `created_at`, `updated_at`, `closed_at?`, `comments_count`, `last_maintainer_activity_at?`, `linked_prs: list[LinkedPR]`, `mentions: list[IssueRef]` |
| `LinkedPR` | `number`, `state` (`open`/`merged`/`closed`), `files_changed: list[str]`, `additions`, `deletions`, `merged_at?`, `created_at` |
| `Skill` | `name` (e.g. `lang:rust`, `area:src/parser`, `concept:async`), `level` 0 to 1, `confidence` 0 to 1, `status` (`declared`, `practising`, `verified`), `evidence` |
| `SkillProfile` | `person` (login or employee id), `skills: list[Skill]`, `typical_change_lines` (median), `want_to_learn: list[str]`, `hours_per_week?`, `seniority?` (team mode) |
| `DifficultyEstimate` | `issue`, `effort` 0 to 1 (0 trivial, 1 very hard), `est_hours_low`, `est_hours_high`, `concepts: list[str]`, `likely_files: list[str]`, `unknowns: list[str]`, `confidence`, `source` (`history`, `llm`, `blended`), `evidence` |
| `AvailabilityResult` | `available: bool` (recommendable), `claimable: bool` (open and unassigned), `reasons: list[UnavailableReason]` |
| `UnavailableReason` | enum: `assigned`, `open_pr`, `stale`, `blocked`, `needs_design`, `not_actionable`, `closed` |
| `FitBreakdown` | `skill_overlap`, `stretch`, `effort_fit`, `responsiveness` (each 0 to 1) |
| `Match` | `issue`, `score` 0 to 1, `breakdown`, `difficulty`, `reasons: list[str]`, `first_steps: list[str]`, `evidence`, `confidence`, `fit_label`, `confidence_label`, `effort_label`, `stretch: bool` (labels are what people see; numbers stay internal) |
| `EdgeKind` | enum: `mentions`, `duplicate`, `blocks`, `same_files`, `same_cluster` |
| `IssueEdge` | `source: IssueRef`, `target: IssueRef`, `kind`, `weight` 0 to 1 |
| `IssueNode` | `ref`, `title`, `cluster?`, `effort?`, `fit?` |
| `IssueGraph` | `repo`, `nodes`, `edges`, `clusters: dict[str, list[IssueRef]]` |

## 4. Config keys (`config.py`, class `Settings`)

Read from environment with prefix `ISSUEMATCH_` (e.g. `ISSUEMATCH_TOP_N=10`); secrets have no prefix.

| Group | Keys |
| --- | --- |
| App | `APP_NAME`, `DATA_DIR`, `LOG_LEVEL` |
| GitHub | `GITHUB_API_URL`, `GITHUB_PAGE_SIZE`, `GITHUB_MAX_ISSUES`, `GITHUB_CLOSED_HISTORY_DAYS`, `GITHUB_MIN_RATE_REMAINING`, `GITHUB_HTTP_TIMEOUT_SECONDS`, `GITHUB_MAX_RETRIES`, `GITHUB_BACKOFF_BASE_SECONDS`, `GITHUB_BACKOFF_MAX_SECONDS`, `GITHUB_BACKOFF_JITTER_FRACTION`, `GITHUB_MAX_INLINE_WAIT_SECONDS`, `GITHUB_PR_FILES_CAP` |
| Availability | `STALE_DAYS`, `BLOCKED_LABELS`, `NEEDS_DESIGN_LABELS`, `NOT_ACTIONABLE_LABELS` |
| Ranking | `WEIGHT_SKILL`, `WEIGHT_STRETCH`, `WEIGHT_EFFORT`, `WEIGHT_RESPONSIVENESS`, `STRETCH_TARGET`, `STRETCH_WIDTH`, `TOP_N`, `MIN_CONFIDENCE`, `FIT_LABEL_GREAT`, `FIT_LABEL_GOOD`, `FIT_LABEL_POSSIBLE`, `CONFIDENCE_LABEL_HIGH`, `CONFIDENCE_LABEL_MEDIUM`, `EFFORT_LABEL_SMALL`, `EFFORT_LABEL_MEDIUM`, `EFFORT_LABEL_LARGE`, `STRETCH_TAG_MIN` |
| Profile | `EVIDENCE_CONFIDENCE`, `CV_CONFIDENCE`, `DECLARED_CONFIDENCE`, `DECLARED_MAX_LEVEL`, `VERIFIED_MIN_EVIDENCE`, `DECLARED_DECAY_DAYS`, `LEVEL_SATURATION`, `COLD_START_MIN_SKILLS`, `COLD_START_PREFERRED_EFFORT`, `CV_MAX_BYTES` |
| Difficulty | `SIMILAR_K`, `HISTORY_WEIGHT`, `EFFORT_LINES_SATURATION` |
| LLM | `LLM_MODEL`, `LLM_SHORTLIST_SIZE`, `LLM_MAX_TOKENS`, `LLM_BUDGET_USD_PER_RUN` |
| Embeddings | `EMBEDDING_BACKEND`, `EMBEDDING_MODEL`, `DUPLICATE_SIMILARITY` |
| Map | `MAP_MAX_NODES`, `SAME_FILES_MIN_OVERLAP` |

Secrets (env only, never in config defaults): `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, later `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`.

## 5. CLI (`issuematch`)

| Command | Does | Output |
| --- | --- | --- |
| `issuematch version` | prints name and version | text |
| `issuematch ingest OWNER/REPO` | fetches and caches issues + PRs | summary counts |
| `issuematch profile LOGIN [--learn X]... [--hours N] [--skill X]... [--cv FILE]` | builds and caches a SkillProfile; `--skill` and `--cv` add declared skills (cold start) | table, or `--json` |
| `issuematch match OWNER/REPO --user LOGIN [--top N] [--stretch 0..1]` | full pipeline | ranked table, or `--json` (list of `Match`) |
| `issuematch map OWNER/REPO [--user LOGIN] [--format json\|mermaid\|html]` | builds the issue graph | file in `build/` |
| `issuematch eval OWNER/REPO` | runs the evaluation in `EVALUATION_SPEC` | report in `docs/evals/` |

Exit codes: `0` ok, `1` user error (bad input), `2` upstream error (GitHub/LLM), `3` rate-limited, `4` not implemented yet.

## 6. Storage (`store/`, SQLite at `DATA_DIR/issuematch.db`)

| Table | Key | Holds |
| --- | --- | --- |
| `repos` | `full_name` | last ingest time, default branch |
| `issues` | `repo, number` | serialized `Issue` JSON, `updated_at` |
| `profiles` | `person` | serialized `SkillProfile` JSON, built_at |
| `estimates` | `repo, number, source, input_hash` | serialized `DifficultyEstimate` |
| `llm_cache` | `input_hash` | model, response, cost_usd, created_at |
| `embeddings` | `repo, number, model` | vector blob |
| `schema_version` | single row | integer |

Ingest is incremental: fetch only issues with `updated_at` newer than the stored value.

## 7. Output formats

- `match --json`: a JSON array of `Match.model_dump(mode="json")`.
- `map --format json`: `IssueGraph.model_dump(mode="json")`.
- `map --format mermaid`: `graph LR` with one subgraph per cluster, node labels `#123 short title`, edge labels by `EdgeKind`.

## Change log

| Date | Version | Change |
| --- | --- | --- |
| 2026-11-20 | 1 | Initial contract |
| 2026-11-20 | 1.2 | `AvailabilityResult.claimable`; `Match` label fields; label threshold config keys; `COLD_START_MAX_EFFORT` renamed `COLD_START_PREFERRED_EFFORT` (ranks lower, never hides) |
| 2026-11-20 | 1.3 | GitHub client config keys: `GITHUB_HTTP_TIMEOUT_SECONDS`, `GITHUB_MAX_RETRIES`, `GITHUB_BACKOFF_BASE_SECONDS`, `GITHUB_BACKOFF_MAX_SECONDS`, `GITHUB_BACKOFF_JITTER_FRACTION`, `GITHUB_MAX_INLINE_WAIT_SECONDS`, `GITHUB_PR_FILES_CAP` |
| 2026-11-20 | 1.1 | `Skill.status`; profile/cold-start config keys; `profile --skill/--cv` flags; connector manifest planned for v2 |
