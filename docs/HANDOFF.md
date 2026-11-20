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
