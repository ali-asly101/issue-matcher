# INGEST SPEC

Owner: Ingest agent. Code: `src/issuematch/github/`, `src/issuematch/store/`.

## Goal

Get everything the rest of the pipeline needs about a repo, cheaply and incrementally, into `Issue` / `LinkedPR` models in the store.

## What to fetch

| Data | Why | Source |
| --- | --- | --- |
| Open issues: title, body, labels, author, assignees, dates, comment count | candidates | GraphQL `repository.issues(states: OPEN)` |
| Closed issues from the last `GITHUB_CLOSED_HISTORY_DAYS` | difficulty history | GraphQL `issues(states: CLOSED)` |
| Linked PRs per issue (closing references and cross-references): state, files changed, additions, deletions, created/merged dates | effort evidence, "open PR" filter, same-files edges | GraphQL `timelineItems(itemTypes: [CROSS_REFERENCED_EVENT, CONNECTED_EVENT])`, `closedByPullRequestsReferences`; files via `pullRequest.files` |
| Last maintainer activity per issue | stale filter | comments/events by users with `authorAssociation` in `OWNER`, `MEMBER`, `COLLABORATOR` |
| `CONTRIBUTING.md`, `CODEOWNERS`, top-level file tree | first steps, areas | GraphQL `object(expression: "HEAD:...")` |
| Issue mentions (`#123` in bodies/comments) | map edges | parse text locally |

## Rules

- Page size `GITHUB_PAGE_SIZE` (default 50). Stop at `GITHUB_MAX_ISSUES` per state and say so in output.
- Read `rateLimit { remaining resetAt cost }` on every GraphQL call. If `remaining < GITHUB_MIN_RATE_REMAINING`, sleep until reset or exit with code 3 (CLI flag decides).
- Back off exponentially on 403/429/502, max 5 retries.
- Incremental: query with `filterBy: { since: <stored max updated_at> }`.
- Pull request file lists can be large; cap at 100 files per PR and record the cap.
- No token -> exit code 1 with a clear message pointing to `.env.example`.
- Every network call goes through one client class so tests can inject a fake transport (`httpx.MockTransport`).

## Fixtures

- Record real responses once with a `--record` dev flag, scrub (no tokens, no emails), save in `tests/fixtures/<repo>/`.
- Tests replay fixtures; they never touch the network.

## Acceptance tests

- [ ] Mapping from fixture JSON to `Issue` models is lossless for every contract field.
- [ ] Pagination test: 3 fake pages produce all issues exactly once.
- [ ] Rate-limit test: low `remaining` triggers wait or exit 3.
- [ ] Incremental test: second ingest only requests issues updated since the first.
