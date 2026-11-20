# IssueMatch

Point it at a GitHub repo and your username. It finds the open issues you can realistically finish and would learn from, explains **why** with evidence, and draws a **map** of how the repo's issues relate.

> Status: **S0 Setup.** Foundation, docs and pure scoring/filter/graph modules are in place. GitHub ingest is next (milestone M2). See `docs/todo/MILESTONES.md`.

## Quick start

```bash
git clone <your-repo-url> issue-matcher && cd issue-matcher
./scripts/setup.sh        # installs uv, Python 3.12, deps; creates .env
./scripts/check.sh        # lint, format, types, tests
uv run issuematch map --demo   # issue map of built-in sample data (Mermaid)
```

Then put a read-only GitHub token in `.env` (`GITHUB_TOKEN=...`). A fine-grained token with "Public repositories (read-only)" is enough.

## Commands

| Command | Status |
| --- | --- |
| `issuematch version` | works |
| `issuematch map --demo [--format mermaid\|json]` | works (sample data) |
| `issuematch ingest owner/repo` | M2 |
| `issuematch profile LOGIN` | M3 |
| `issuematch match owner/repo --user LOGIN` | M5 |
| `issuematch map owner/repo --format html` | M7 |
| `issuematch eval owner/repo` | M6 |

## Building it with Claude Code

This repo is set up for a multi-agent workflow:

- `CLAUDE.md` holds the rules every agent follows (ownership, hard rules, definition of done).
- `docs/` holds the plan, the contract (shared models/config/CLI), one spec per system, milestones and the handoff log.
- `.claude/agents/` defines one agent per area: ingest, profile, estimator, ranking, map, qa.
- `.claude/commands/` adds `/next` (pick up the next milestone task), `/check` (run the checks) and `/handoff` (write the handoff entry).

A typical loop: open the repo in Claude Code, run `/next`, approve the plan, let the owning agent build it, then `/check` and `/handoff`. Ask for several agents in parallel only on tasks that touch different folders.

## Layout

```text
CLAUDE.md               agent rules
docs/                   PLAN, CONTRACT, HANDOFF, *_SPEC, todo/, evals/, decisions/, reference/
src/issuematch/         config, models, availability, ranking, graph, cli, demo, prompts/
tests/                  offline tests and fixtures
scripts/                setup.sh, check.sh
.github/workflows/      CI runs scripts/check.sh
.claude/                agents, commands, permissions
```

## Stack

Python 3.12, uv, Typer, httpx, Pydantic v2, SQLite; ruff, mypy (strict), pytest. Decisions and open questions are in `docs/PLAN.md`.
