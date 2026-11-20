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
**Requests to others:** none. Current work is still M2 (ingest).

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
