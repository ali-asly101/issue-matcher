# PLAN: IssueMatch

Last updated: 2026-11-20. Current development stage: **S0 (Setup)**. Next milestone: **M1**.

## Vision

Point it at a repo and your GitHub username. It tells you the 3 to 5 open issues you can most likely finish and would learn from, **why** each one fits, where to start, and shows a map of how the repo's issues fit together.

Later, the same engine helps a team lead match tickets to people using Git, Jira and CV evidence.

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
| Team mode | Git org + Jira + CVs, roles/rank, workload balancing, manager view | S3 |
| Web app | Hosted UI, GitHub OAuth, saved profiles | S4 |

## Development stages

| Stage | Goal | Done when |
| --- | --- | --- |
| S0 Setup | Repo, toolchain, docs, CI | `./scripts/check.sh` green locally and in CI (M1) |
| S1 Solo MVP | Ingest, profile, availability, history-based difficulty, ranking, CLI | Owner gets useful picks on 3 repos they know (M2 to M5) |
| S2 Quality + map | LLM estimator with calibration, eval harness, issue map | Eval beats the label-only baseline; map renders for a 1k-issue repo |
| S3 Team mode | Jira and CV sources, roles, assignment optimisation, privacy controls | "Best person for ticket" matches historical fixer above baseline |
| S4 Web | UI, auth, hosting | See `docs/todo/BACKLOG.md` |

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

## Open questions (owner or Architect decides)

1. **Embedding provider?** Default: local `sentence-transformers` (free, offline) behind an interface; API embeddings as an option. Decide in M4.
2. **LLM model for estimates?** Default: a small, cheap Claude model for the shortlist; configurable in `config.py`.
3. **How is "stale" defined?** Default: no maintainer activity for 180 days. Tune from evals.
4. **Do we read code for difficulty in S1?** Default: no, only issue text + linked PR stats. File retrieval arrives with the LLM estimator in S2.
5. **Interactive map tech?** Default: single self-contained HTML file with Cytoscape.js.
6. **Team-mode first integration?** Default: Jira Cloud export (CSV/JSON) before live API.

## Risks

- **Bad picks erode trust fast.** Mitigation: evidence, confidence, eval harness, availability filter.
- **Rate limits and cost on big repos.** Mitigation: GraphQL, caching, shortlist before LLM.
- **Vague issues.** Many issues are questions or wishes. Mitigation: classify and exclude non-actionable issues.
- **Team mode feels like surveillance.** Mitigation: `docs/PRIVACY_SPEC.md`; match, never rate people.
- **Crowded space** (Jira/Linear AI assignment, good-first-issue finders). Wedge: code-aware difficulty + a real skill graph + the issue map.
