# INTEGRATIONS SPEC (connectors and write-back)

**Stage S4** (GitHub connector is refactored into this shape at M10). Owner: Integrations agent. Code: `src/issuematch/connectors/`.

## Goal

Read work items and people from any tracker, and write approved assignments back, through one interface. The matching engine never sees provider-specific data.

## Providers (in order)

| Provider | Items | History for skills | Auth | Webhooks |
| --- | --- | --- | --- | --- |
| GitHub | issues, PRs | merged PRs, files, reviews | GitHub App (org install) or OAuth | issues, pull_request |
| GitLab | issues, merge requests | merged MRs, files, approvals | OAuth 2.0 (gitlab.com and self-managed) | issue, merge_request |
| Jira Cloud | issues (any type), sprints, components | resolved issues, linked dev info (commits/PRs via the Jira-GitHub/GitLab link) | Atlassian OAuth 2.0 (3LO) | issue created/updated |
| Later: Linear, Azure DevOps, Jira Data Center | | | | |

A workspace can connect several providers at once (typical: Jira for tickets + GitHub/GitLab for code history). Identity linking maps one person across providers (see below).

## Dynamic connections: registry and manifests

Connectors are plug-ins. Each one ships a **manifest**, and the website builds its Integrations directory, connect flow and settings forms from the manifests, so adding a tracker never needs new UI code.

```yaml
# src/issuematch/connectors/jira/manifest.yaml
id: jira
name: Jira Cloud
category: ticketing            # ticketing | code | chat
logo: jira.svg
auth:
  type: oauth2                 # oauth2 | github_app | api_token | none
  scopes: [read:jira-work, write:jira-work, read:jira-user, offline_access]
  scope_reasons:               # shown to the user before the OAuth redirect
    read:jira-work: "Read tickets, components and history to learn skills and find work"
    write:jira-work: "Set the assignee and add a comment, only after you approve"
capabilities: [read_items, read_people, read_history, assign, comment, label, webhooks]
config:                        # rendered as a form after connecting (JSON-Schema-like)
  - key: projects
    label: Projects to include
    type: multiselect
    source: list_projects
  - key: done_statuses
    label: Statuses that count as done
    type: multiselect
    source: list_statuses
    advanced: true
  - key: story_points_field
    label: Story points field
    type: select
    source: list_fields
    advanced: true
defaults: {write_label: false, dry_run: true}
```

Rules:
- The registry discovers connectors at start-up (`connectors/*/manifest.yaml`) and validates each manifest against a schema; a bad manifest disables that connector, not the app.
- Capabilities gate the UI: no `assign` capability means no "Assign" button for that tracker's items.
- Fields marked `advanced` stay collapsed; every connector works with defaults only (progressive configuration).
- A workspace can connect the same provider more than once (two Jira sites, GitLab.com plus a self-managed GitLab).

### Long-tail trackers

Native connectors cover GitHub, GitLab and Jira (deep features: history, webhooks, write-back). For everything else, in order of preference:
1. **Unified ticketing API provider** (e.g. Merge, Apideck, Knit) wrapped as one connector with `category: ticketing`. Fast coverage of Linear, Asana, Azure DevOps and others; trade-offs are cost per connection, less history detail, and another processor of customer data (document it in the privacy notice). Decide at S5.
2. **CSV / JSON import** connector (`auth.type: none`): upload an export of tickets and assignees; read-only, no write-back.
3. **Generic webhook** connector: the tracker pushes item events to us; write-back is not available.

## Integrations UX (what the user sees)

- **Directory:** search, categories (Ticketing, Code, Chat), "Connected" and "Official" badges, one line per tracker on what it adds.
- **Before the redirect:** a short panel listing each requested permission in plain words (from `scope_reasons`) and what we will never do ("We never change priorities, sprints or descriptions").
- **After connecting:** return to the same page with a success message and the setup form (projects first; advanced fields collapsed), then a progress bar for the first backfill.
- **Connected state:** each connection shows account/site, projects, last sync time, health badge (Healthy / Syncing / Needs attention / Disconnected), write mode (Dry run / Live), and Manage.
- **Errors:** a plain banner with one-click Reconnect when a token expires or a scope is revoked; health checks run every sync, failures never stay silent.
- **Disconnect:** clear and reversible; says what data is removed and that nothing in the tracker is changed.

## Connector interface

```python
class Connector(Protocol):
    provider: str  # "github", "gitlab", "jira"

    def list_projects(self) -> list[Project]: ...
    def list_items(self, project: Project, since: datetime | None) -> Iterator[WorkItem]: ...
    def list_people(self, project: Project) -> list[ExternalPerson]: ...
    def history_for(self, person: ExternalPerson, since: datetime) -> Iterator[Contribution]: ...
    # write-back (only called by the approval flow)
    def assign(self, item: WorkItemRef, person: ExternalPerson, idem_key: str) -> WriteResult: ...
    def comment(self, item: WorkItemRef, body: str, idem_key: str) -> WriteResult: ...
    def add_label(self, item: WorkItemRef, label: str, idem_key: str) -> WriteResult: ...
    def parse_webhook(self, headers: Mapping[str, str], body: bytes) -> list[ChangeEvent]: ...
```

Models `Project`, `WorkItem`, `ExternalPerson`, `Contribution`, `WriteResult`, `ChangeEvent` are added to the contract (v2) when M10 starts. `WorkItem` generalises today's `Issue`: provider, key (`PROJ-123` or `owner/repo#123`), type, status category (todo/in progress/done), assignee, labels/components, sprint, story points, links (blocks/duplicates/relates), linked code changes.

## Mapping notes

- **Status:** map each provider's statuses to `todo / in_progress / done`; Jira via `statusCategory`.
- **Availability:** "assigned", "in progress", "in an active sprint for someone else" all mean unavailable.
- **Effort:** Jira story points and time tracking feed the difficulty estimate as extra evidence, not truth.
- **Links:** Jira issue links and GitLab related/blocking issues become map edges directly.
- **Areas:** Jira components and GitLab/GitHub paths both become `area:` skills.

## Identity linking

One `Person` in a workspace can have accounts on several providers. Link by: verified email match (if the provider exposes it and the person consents), else manual linking by the person or an admin. Never guess from display names.

## Write-back rules

1. Only the approval flow calls write methods (see `WEB_APP_SPEC.md`). No other code path may write.
2. Every write carries an idempotency key (`workspace:item:action:approval_id`); retries never double-comment or double-assign.
3. Default writes: set assignee, add one comment ("Suggested by IssueMatch for @person: <2 to 3 reasons>. Approved by @lead."). Label optional per workspace. Never edit description, priority, sprint or status in v1.
4. **Dry-run mode** per workspace: show what would be written, write nothing. New workspaces start in dry-run.
5. Before writing, re-fetch the item; if it changed (already assigned, closed), stop and tell the approver.
6. Every write is recorded in the audit log with who approved it and the provider's response.
7. Workspace kill switch disables all writes immediately.

## Sync

- Initial backfill by background job; then webhooks for changes, plus a periodic incremental sync (every 15 minutes) to catch missed webhooks.
- Verify webhook signatures (GitHub `X-Hub-Signature-256`, GitLab `X-Gitlab-Token`, Jira JWT/secret).
- Respect each provider's rate limits; back off and resume.

## Secrets

OAuth tokens are encrypted at rest (envelope encryption, key from the environment/KMS), refreshed automatically, never logged, never sent to the LLM. Request the minimum scopes; document them per provider in this file when implemented.

## Acceptance tests

- [ ] Each connector passes the shared connector contract test suite against recorded fixtures.
- [ ] Write methods are idempotent (same key twice -> one comment).
- [ ] Dry-run writes nothing (fake transport asserts zero write calls).
- [ ] Item changed since approval -> write is refused.
- [ ] Invalid webhook signature -> rejected.
