# PLAN: IssueMatch

Last updated: 2026-11-20. Current development stage: **S0 (Setup)**. Next milestone: **M1**.

## Vision

**End goal:** a web platform a team connects to its work trackers (Jira, GitLab, GitHub, later Linear and others). It learns each person's skills from their real history, suggests the right ticket for each person and the right person for each ticket, and when a human approves, **writes the assignment back** to the tracker (assignee, comment with the reasoning, label) and notifies the person.

**First step:** the same engine as a CLI for one person and one GitHub repo: the 3 to 5 open issues you can most likely finish and would learn from, **why** each fits, where to start, and a map of how the issues relate. The CLI proves the matching works before we build the platform around it.

See `docs/WEB_APP_SPEC.md` and `docs/INTEGRATIONS_SPEC.md` for the end-state design.

## Pillars

1. **Trustworthy.** Every pick shows its evidence and confidence. A wrong "you can handle this" costs someone hours.
2. **Actually available.** Never recommend an issue someone is already working on or that maintainers won't review.
3. **Growth, not just comfort.** Picks include a deliberate stretch, controlled by a dial.
4. **Cheap to run.** Heavy work (embeddings, LLM) only on a shortlist, everything cached.
5. **Measurable.** Matching quality is a number we track on held-out history, not a feeling.

## The pipeline

```text
 owner/repo + person
   |
   v
 Ingest (GraphQL): open + closed issues, merged PRs, files changed, CONTRIBUTING, CODEOWNERS
   |
   v
 Skill profile: person's repos/commits/PRs  (+ self-declared goals and hours)
   |
   v
 Availability filter: drop assigned / has open PR / blocked / stale / needs-design
   |
   v
 Difficulty estimate: similar closed issues (history)  +  LLM on shortlist  -> calibrated
   |
   v
 Rank by fit: skill overlap, stretch, effort vs time, maintainer responsiveness
   |
   v
 Output: top N with reasons + first steps      Issue map: relations, clusters, fit overlay
```

## Product modes

| Mode | What it is | Stage |
| --- | --- | --- |
| Solo CLI | `issuematch match owner/repo --user me` prints ranked picks | S1 |
| Issue map | Graph JSON + Mermaid export, then an interactive HTML view | S2 |
| Web app (solo) | Sign in with GitHub, pick a repo, see picks and the map in the browser | S3 |
| Team platform | Connect Jira / GitLab / GitHub, team members and roles, best person per ticket, approve -> write back to the tracker, notify the person | S4 |
| Hosted SaaS | Multi-tenant hosting, org admin, billing, security review | S5 |

## Development stages

| Stage | Goal | Done when |
| --- | --- | --- |
| S0 Setup | Repo, toolchain, docs, CI | `./scripts/check.sh` green locally and in CI (M1) |
| S1 Solo MVP | Ingest, profile, availability, history-based difficulty, ranking, CLI | Owner gets useful picks on 3 repos they know (M2 to M5) |
| S2 Quality + map | LLM estimator with calibration, eval harness, issue map | Eval beats the label-only baseline; map renders for a 1k-issue repo (M6, M7) |
| S3 Web app | API server, database, background sync, web UI for solo mode | Owner uses the website instead of the CLI (M8, M9) |
| S4 Team platform | Connector layer, GitLab + Jira, team mode, approval flow, write-back, notifications | A test team assigns a sprint's tickets through the site and Jira shows the result (M10 to M13) |
| S5 Hosted SaaS | Multi-tenant hosting, admin, billing, compliance | See `docs/todo/BACKLOG.md` |

## MVP success test

Run on 3 repos the owner knows well, as themselves and as 2 friends with different skills:

- At least 3 of the top 5 picks are things the person agrees they could do and would want to.
- No recommended issue is already assigned or has an open PR.
- Every pick shows evidence the person finds convincing.
- A full run on a repo with ~1,000 issues finishes in under 5 minutes on a warm cache and under the LLM budget.

Record results in `docs/evals/`.

## Decisions log

| Date | Decision | Why |
| --- | --- | --- |
| 2026-11-20 | Python 3.12, uv, Typer, httpx, Pydantic, SQLite | Fast to build, strong typing, easy to test offline |
| 2026-11-20 | GitHub GraphQL first, REST only where GraphQL lacks data | Fewer requests, better rate-limit budget |
| 2026-11-20 | History-based difficulty is the primary signal; LLM refines | Raw LLM difficulty guesses are noisy; history can be calibrated |
| 2026-11-20 | Solo mode before team mode | Self-contained, no personal-data handling, works as a portfolio demo |
| 2026-11-20 | Map ships as JSON + Mermaid before an interactive view | Proves the graph is right before investing in UI |
| 2026-11-20 | Suggestions only, never auto-assign | Trust, and required for team-mode privacy |
| 2026-11-20 | End goal is a web platform with Jira/GitLab/GitHub connectors and write-back | Owner's target product; the CLI engine is the first step |
| 2026-11-20 | Write-back only after a human approves (lead assigns, or the person claims) | Keeps people in charge; avoids surprise assignments in a team's tracker |
| 2026-11-20 | One connector interface for every tracker; the engine never sees provider-specific data | Adding Linear or Azure DevOps later is one new connector, not a rewrite |
| 2026-11-20 | Web stack: FastAPI + Postgres + background worker, React (Vite) frontend | Reuses the Python engine directly; standard, hireable stack (revisit at M8) |

## Open questions (owner or Architect decides)

1. **Embedding provider?** Default: local `sentence-transformers` (free, offline) behind an interface; API embeddings as an option. Decide in M4.
2. **LLM model for estimates?** Default: a small, cheap Claude model for the shortlist; configurable in `config.py`.
3. **How is "stale" defined?** Default: no maintainer activity for 180 days. Tune from evals.
4. **Do we read code for difficulty in S1?** Default: no, only issue text + linked PR stats. File retrieval arrives with the LLM estimator in S2.
5. **Interactive map tech?** Default: single self-contained HTML file with Cytoscape.js.
6. **First tracker after GitHub?** Default: GitLab (similar model to GitHub, free self-test), then Jira Cloud. Jira Server/Data Center later.
7. **What does write-back do by default?** Default: set assignee + add one comment with the reasons; a label `issuematch` is optional per workspace. Never edits descriptions, priorities or sprints in v1.
8. **Notifications?** Default: rely on the tracker's own assignment notification, plus an optional email/Slack digest of new picks. Decide at M13.
9. **Hosting?** Default: one Docker Compose setup for self-hosting first, managed hosting in S5.

## Risks

- **Bad picks erode trust fast.** Mitigation: evidence, confidence, eval harness, availability filter.
- **Rate limits and cost on big repos.** Mitigation: GraphQL, caching, shortlist before LLM.
- **Vague issues.** Many issues are questions or wishes. Mitigation: classify and exclude non-actionable issues.
- **Team mode feels like surveillance.** Mitigation: `docs/PRIVACY_SPEC.md`; match, never rate people.
- **Writing into a team's tracker is high-trust.** A bug could spam comments or reassign tickets. Mitigation: approval required, idempotent writes, dry-run mode, audit log, per-workspace kill switch.
- **Integration surface is large** (OAuth per provider, webhooks, API differences, Jira custom fields). Mitigation: connector interface, one provider at a time, contract tests per connector.
- **Crowded space** (Jira/Linear AI assignment, good-first-issue finders). Wedge: code-aware difficulty + a real skill graph + the issue map.
