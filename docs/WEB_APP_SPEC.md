# WEB APP SPEC

**Stages S3 (solo web) and S4 (team platform).** Owner: Web agent (backend + frontend). Code: `web/` (frontend), `src/issuematch/api/` and `src/issuematch/worker/` (backend). Stack choice is recorded in `docs/PLAN.md` and confirmed at M8.

## Goal

A website where a person sees the work that fits them, and a team lead turns good suggestions into real assignments in their tracker, in a few clicks, with the reasoning visible.

## Architecture

```text
 Browser (React/Vite)
   |  HTTPS, session cookie
   v
 API (FastAPI)  ---- Postgres (workspaces, people, profiles, items, matches, approvals, audit)
   |                      ^
   | enqueue jobs         |
   v                      |
 Worker (background jobs: backfill, sync, profile build, estimates, matching, write-back, notifications)
   |
   +--> Connectors (GitHub / GitLab / Jira)      +--> LLM provider (shortlist only)
   ^
 Webhooks from trackers -> API -> enqueue sync
```

The engine modules (`profile`, `difficulty`, `availability`, `ranking`, `graph`) are imported unchanged by the worker. The API never calls a tracker or the LLM inside a request; it enqueues a job.

## Roles

| Role | Can |
| --- | --- |
| Member | See and correct their own profile, set growth goals and hours, see their picks, browse all open tickets, **claim** any unassigned ticket |
| Lead | Everything a member can, plus: see suggestions for their team's tickets, **approve/assign**, run sprint suggestions, see the team map |
| Admin | Connect trackers, manage members and roles, dry-run and kill switch, audit log, data deletion |

## Screens

Visual language: `docs/DESIGN_SYSTEM.md` (Arial, cobalt accent, Stripe-like calm and clarity). Screen designs: see the Design canvas linked in the README.

| Screen | For | What's on it |
| --- | --- | --- |
| Landing page | visitors | One-line promise, product screenshot of My work, three proof points (evidence-backed picks, works with your tracker, you approve every change), integrations strip, security note, sign-up |
| Sign in | all | GitHub / GitLab / Atlassian sign-in |
| Onboarding | new member | 1) connect a source or skip, 2) build your profile: upload CV, add skills/keywords with a level, paste profile links, 3) set hours and "want to learn", 4) first picks. Each step skippable; progress shown |
| My work | member | Ranked picks with fit, confidence and effort labels, reasons and first steps; stretch slider; "Claim" button (assigns to me in the tracker); "Not for me" feedback; "All open tickets" tab listing every claimable ticket with its label. Cold-start users see "Based on your declared skills", with smaller tickets ranked first |
| Ticket (member view) | member | Any ticket can be opened and claimed. Shows the person's fit label and reasons; if the fit is weak, a side list "These match your skills better" (never blocks the claim) |
| My profile | member | Profile strength summary (verified vs declared), skill chips with status dots and evidence, CV upload, add skills, "want to learn", hours per week, the next step that would strengthen the profile |
| Ticket | lead | One ticket: best 3 people with reasons, workload, growth fit; "Assign" button |
| Team board | lead | Unassigned tickets on the left, people on the right with load; drag a suggestion to approve; bulk "approve sprint suggestions" |
| Issue map | all | Clusters, relations, fit colouring; knowledge-silo view for leads |
| Integrations | admin | Directory built from connector manifests (search, categories, badges); permission preview before OAuth; connected list with health, last sync, write mode; identity linking; dry-run toggle; kill switch (see `INTEGRATIONS_SPEC` "Integrations UX") |
| Activity | lead, admin | Audit log of approvals and write-backs |

## The approval -> write-back -> notify flow

1. Worker produces suggestions (person <-> ticket) with reasons and confidence.
2. A lead clicks **Assign** (or a member clicks **Claim** on their own pick).
3. API records an `Approval` and enqueues a write-back job.
4. Worker re-checks the ticket is still available, then calls the connector (`assign`, `comment`, optional `add_label`) with an idempotency key. In dry-run, it records what would happen instead.
5. Result is shown in the UI and written to the audit log.
6. The person is notified: by the tracker itself (assignment notification) and optionally by an IssueMatch email/Slack message with the reasons and first steps.
7. Webhook from the tracker confirms the change and updates the item.

Suggestions are never written to a tracker without step 2.

## Background jobs

`backfill(workspace, provider)`, `sync(workspace, provider)`, `build_profiles(workspace)`, `estimate(workspace, items)`, `match(workspace)`, `write_back(approval_id)`, `notify(approval_id)`, `digest(person)`. Jobs are idempotent and retried with back-off. Default queue: Postgres-backed (simple), revisit if it becomes a bottleneck.

## Multi-tenancy and security

- Every row belongs to a `workspace_id`; every query is scoped to it (enforced in one data-access layer, tested).
- Session cookies (HttpOnly, Secure, SameSite=Lax), CSRF protection on writes.
- OAuth tokens encrypted at rest (see `INTEGRATIONS_SPEC`).
- Follow `PRIVACY_SPEC`: members see their full profile; leads see matches and reasons, not raw history beyond what the member allows.

## UX principles

- Every suggestion shows **why** in one or two lines, with links to the evidence.
- One primary action per screen (Claim, Assign, Approve sprint).
- Show fit, confidence and effort as words, never numbers; less certain suggestions sit in a "Less sure" group.
- Never block a member from a ticket: every unassigned ticket can be claimed; weak fits get better-matching suggestions alongside.
- Write-back is reversible from the UI (unassign + comment) and always logged.

## Acceptance tests

- [ ] A member signs in, sees picks from a connected GitHub repo, and claims one; the issue is assigned in GitHub with a comment.
- [ ] A lead approves a suggestion for a Jira ticket; Jira shows the assignee and comment; the audit log shows who approved.
- [ ] Dry-run workspace: the same flow writes nothing and shows the would-be changes.
- [ ] A user from workspace A can never read workspace B's data (tested at the data-access layer).
