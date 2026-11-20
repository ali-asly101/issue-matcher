# HANDOFF

Newest entry first. Every agent adds an entry when a task is finished. Keep the last 10 entries here and move older ones to the **Archive** at the bottom.

## Template (copy this)

```markdown
## <task name> (<YYYY-MM-DD>, <agent>)
**Changed contract:** new models, fields, config keys, CLI flags or tables (or "none")
**Files:** every file added or changed
**How tested:** commands run and what you saw (ruff, mypy, pytest, eval numbers)
**Needs from owner:** things only a human can do (create a token, pick a repo, answer an open question)
**Not tested:** what was skipped and why
**Requests to others:** changes needed in another agent's area
```

Rules:

- Be specific. "Works" is not a test. Say what you ran and what you saw.
- Put **everything** you did not verify under "Not tested".
- If a spec and the code disagree, say which one you followed.

---

## M2: GraphQL client with pagination, rate limits and back-off (2026-11-20, Ingest)
**Changed contract:** `GITHUB_MAX_INLINE_WAIT_SECONDS` (added by Architect: `src/issuematch/config.py`, `docs/CONTRACT.md` v1.3 row). No other contract change. New package `issuematch.github` (public: `GitHubClient`, `JSONObject`, errors `GitHubError`, `MissingTokenError`, `BadTokenError`, `RateLimitExhaustedError` (`reset_at`, `remaining`, `wait_seconds`), `RetriesExhaustedError` (`retries`, `last_status`), `GraphQLError` (`messages`, `types`), `UnexpectedResponseError` (`status`)).
**Files:** `src/issuematch/github/__init__.py`, `src/issuematch/github/client.py`, `src/issuematch/github/errors.py` (new); `tests/test_github_client.py` (new, 33 test cases from 27 functions); `docs/INGEST_SPEC.md` (inline-wait rule, "Inline wait test" box, ticked 7 boxes); `docs/todo/MILESTONES.md` (M2 item 1 ticked); `docs/HANDOFF.md`. Committed alongside, edited by Architect: `src/issuematch/config.py`, `docs/CONTRACT.md`.
**How tested:** `uv run ruff check src tests` minus config.py clean, `uv run mypy` clean (11 files, strict), `uv run pytest`: 70 passed (all offline; MockTransport, fake sleep/clock/random). `./scripts/check.sh` was not green at hand-back: `config.py` line 37 (Architect's new key) was too long for ruff. **Architect fix and review:** shortened that comment, reviewed `client.py` against INGEST_SPEC, reran `./scripts/check.sh`: ruff check clean, ruff format check clean, mypy strict clean (11 files), pytest 70 passed.
**Needs from owner:** none.
**Not tested:** no real GitHub call was made (no token used, `.env` not read); real response headers/shapes are assumed from GitHub docs: `x-ratelimit-remaining`/`x-ratelimit-reset` on 403/429, `Retry-After` as seconds or HTTP date, `RATE_LIMITED` error `type`. HTTP-date form of `Retry-After` is implemented but has no test. Network errors and timeouts (`httpx.TransportError`) are not caught or retried; they propagate as httpx exceptions (spec is silent). Non-retried statuses (e.g. 500, 404) raise `UnexpectedResponseError` without retry and have no dedicated test. No CLI mapping to exit codes 1/3 yet (CLI wiring is out of scope).
**Requests to others:** Architect (config.py line fixed): map `MissingTokenError` and `BadTokenError` -> exit 1 and `RateLimitExhaustedError` -> exit 3 in `cli.py`, and add the `--wait`-style flag that sets `wait_on_rate_limit`.
**Decisions (spec was silent or open):**
- Back-off for retry n (0-based): `min(min(BASE * 2**n, MAX) * (1 + JITTER * r), MAX)`, r in [0, 1). Jitter is added on top and the total re-capped, so no computed wait goes over `GITHUB_BACKOFF_MAX_SECONDS`; once the raw wait reaches the cap there is no room for jitter and the wait is exactly the cap. Trade-off: less spread at the cap, but the cap is a hard promise.
- `GITHUB_MAX_RETRIES` = retries after the first try, so up to 1 + 5 requests. Retry-After waits and rate-limit-reset waits count as retries.
- Low `remaining` is checked **before the next request**, not by throwing away the response that reported it, so paid-for data is kept.
- 403/429 with `x-ratelimit-remaining: 0` and no `Retry-After` is treated as the primary rate limit (wait until `x-ratelimit-reset`, or raise), not blind back-off. `Retry-After` wins when both are present.
- `RATE_LIMITED` reset time comes from the `x-ratelimit-reset` header, else the last known `rateLimit.resetAt`; if neither is known, the normal back-off is used.
- A long wait the client may not take raises `RateLimitExhaustedError` before the retry-count check, so the user gets the more useful "resets at" message.
- The client reads `rateLimit` only if the query selects it (logs a debug line otherwise); the ingest queries must select `rateLimit { remaining resetAt cost }`.
- `paginate(..., limit=)` asks for only as many nodes as are still needed on the last page; the query must declare `$first: Int!` and `$after: String`.
- User-Agent header is `settings.APP_NAME`.

---

## GitHub client config keys and retry rules (2026-11-20, Architect)
**Changed contract:** new config keys `GITHUB_HTTP_TIMEOUT_SECONDS` (30), `GITHUB_MAX_RETRIES` (5), `GITHUB_BACKOFF_BASE_SECONDS` (1.0), `GITHUB_BACKOFF_MAX_SECONDS` (60), `GITHUB_BACKOFF_JITTER_FRACTION` (0.25), `GITHUB_PR_FILES_CAP` (100). Contract v1.3.
**Files:** `src/issuematch/config.py`, `docs/CONTRACT.md`, `docs/INGEST_SPEC.md` (retry rules: jitter, `Retry-After`, GraphQL `errors`, 401; four new acceptance tests), `docs/HANDOFF.md`.
**How tested:** `./scripts/check.sh` (contract test checks the new keys exist).
**Needs from owner:** none.
**Not tested:** nothing uses these keys yet; the ingest agent builds the client next.
**Requests to others:** Ingest agent: build the GraphQL client to these rules (M2 item 1).
**Defaults chosen (spec was silent):** `Retry-After` is honoured in full, not cut to `GITHUB_BACKOFF_MAX_SECONDS`, because waiting less makes GitHub's secondary limit worse; it still counts as a retry. Waiting for the primary rate-limit reset is not capped either (it can be up to an hour); that is what the wait-or-exit-3 choice is for. Jitter adds 0–25% on top of the computed wait. HTTP timeout 30 s, since httpx's 5 s default is too short for big GraphQL pages.

---

## M1 closed: CI green, token in place, stage S1 (2026-11-20, Architect)
**Changed contract:** none.
**Files:** `docs/todo/MILESTONES.md` (last two M1 items ticked), `docs/PLAN.md` (stage S1, next milestone M2), `docs/HANDOFF.md` (this entry; corrected the "Current work is still M2" line in the end-goal entry, which conflicted with PLAN.md saying M1).
**How tested:** owner reports: `main` pushed, CI green on `780fdd6`, `./scripts/setup.sh` and `./scripts/check.sh` pass on their Mac, `.env` holds a read-only `GITHUB_TOKEN`. Architect did not re-run these and did not read `.env`.
**Needs from owner:** none.
**Not tested:** token scope and validity not checked by the Architect (first real check is the M2 ingest run).
**Requests to others:** Ingest agent: M2 is current; start with the GraphQL client (`INGEST_SPEC`).

---

## Never block members; labels instead of numbers (2026-11-20, Architect)
**Changed contract:** `AvailabilityResult.claimable`; `Match.fit_label`, `confidence_label`, `effort_label`, `stretch`; config `FIT_LABEL_*`, `CONFIDENCE_LABEL_*`, `EFFORT_LABEL_*`, `STRETCH_TAG_MIN`; `COLD_START_MAX_EFFORT` renamed `COLD_START_PREFERRED_EFFORT` (ranks lower, never hides). Contract v1.2.
**Files:** `CLAUDE.md` (hard rules 10 and 11), `docs/AVAILABILITY_SPEC.md`, `docs/RANKING_SPEC.md`, `docs/DESIGN_SYSTEM.md`, `docs/WEB_APP_SPEC.md`, `docs/CLI_SPEC.md`, `docs/TEAM_MODE_SPEC.md`, `docs/SKILL_PROFILE_SPEC.md`, `docs/CONTRACT.md`, `src/issuematch/{config,models,availability,ranking}.py`, `tests/test_availability.py`, `tests/test_ranking.py`. Designs: numbers replaced with labels; new "All open tickets" screen.
**How tested:** `./scripts/check.sh` green, 37 tests (new: claimable rules, label thresholds, labels on Match).
**Needs from owner:** none.
**Not tested:** label thresholds are starting values; tune them with real picks in M5.
**Requests to others:** Ranking agent: CLI and web output must show labels only (numbers only in `--json`). Web agent: every unassigned ticket gets an enabled Claim button.

---

## Design system, cold-start profiles, dynamic connectors (2026-11-20, Architect)
**Changed contract:** `Skill.status` (`declared`/`practising`/`verified`, default `verified`); new Profile config keys (`EVIDENCE_CONFIDENCE`, `CV_CONFIDENCE`, `DECLARED_CONFIDENCE`, `DECLARED_MAX_LEVEL`, `VERIFIED_MIN_EVIDENCE`, `DECLARED_DECAY_DAYS`, `LEVEL_SATURATION`, `COLD_START_MIN_SKILLS`, `COLD_START_MAX_EFFORT`, `CV_MAX_BYTES`); `profile --skill/--cv` flags (planned for M3); connector manifests planned for contract v2.
**Files:** `docs/DESIGN_SYSTEM.md` (new), `docs/SKILL_PROFILE_SPEC.md`, `docs/INTEGRATIONS_SPEC.md`, `docs/WEB_APP_SPEC.md`, `docs/CONTRACT.md`, `docs/todo/MILESTONES.md`, `src/issuematch/models.py`, `src/issuematch/config.py`, `README.md`.
**How tested:** `./scripts/check.sh` green (contract test confirms every new config key exists).
**Needs from owner:** review the screen designs and the palette; say if you want a different accent colour.
**Not tested:** CV extraction and connector manifests are designs only; nothing is implemented yet.
**Requests to others:** Profile agent: cold start is part of M3. Web agent: use `DESIGN_SYSTEM.md` tokens from M9.

---

## End goal set: web platform with tracker connectors and write-back (2026-11-20, Architect)
**Changed contract:** no code changes. Contract now lists planned v2 models (`WorkItem`, `ExternalPerson`, `Connector`, `Approval`, ...) and new packages `connectors/`, `api/`, `worker/`, `web/` for M10 onward.
**Files:** `CLAUDE.md`, `README.md`, `docs/PLAN.md`, `docs/CONTRACT.md`, `docs/INTEGRATIONS_SPEC.md` (new), `docs/WEB_APP_SPEC.md` (new), `docs/TEAM_MODE_SPEC.md`, `docs/PRIVACY_SPEC.md`, `docs/todo/MILESTONES.md`, `docs/todo/BACKLOG.md`, `.claude/agents/integrations.md` (new), `.claude/agents/web.md` (new).
**How tested:** `./scripts/check.sh` still green (docs-only change; contract test still passes).
**Needs from owner:** confirm the web stack default (FastAPI + Postgres + React) before M8; answer PLAN open questions 6 to 9 if you want different defaults.
**Not tested:** nothing new is implemented; the S3/S4 specs are designs, not verified against the GitHub, GitLab or Jira APIs yet.
**Requests to others:** none. (Wording corrected 2026-11-20: at the time M1 was still open; M2 is next only after M1 closed. See the M1 entry above.)

---

## Project scaffold, toolchain and foundation (2026-11-20, Architect)
**Changed contract:** none (initial contract v1 written).
**Files:** `CLAUDE.md`, `README.md`, `pyproject.toml`, `uv.lock`, `.env.example`, `.gitignore`, `.gitattributes`, `.pre-commit-config.yaml`, `docs/**`, `src/issuematch/{__init__,config,models,availability,ranking,graph,cli}.py`, `src/issuematch/prompts/difficulty_estimate.md`, `tests/**`, `scripts/{setup,check}.sh`, `.github/workflows/ci.yml`, `.claude/agents/*`, `.claude/commands/*`, `.claude/settings.json`.
**How tested:** `./scripts/check.sh` in a clean Linux sandbox with Python 3.12 via uv: ruff check clean, ruff format check clean, mypy strict clean, pytest all passing (offline). `uv run issuematch version` and `uv run issuematch map --demo --format mermaid` run.
**Needs from owner:** create a GitHub fine-grained token (public repo read only) and put it in `.env` as `GITHUB_TOKEN`; push the repo to GitHub so CI runs; answer open questions in `docs/PLAN.md` if you want different defaults.
**Not tested:** CI on GitHub itself (workflow written, not yet run there); macOS setup script on a real Mac; anything needing the network (no GitHub client yet).
**Requests to others:** none.

---

## Archive

(older entries go here)
