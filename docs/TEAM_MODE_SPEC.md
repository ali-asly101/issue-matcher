# TEAM MODE SPEC

**Stage S4.** Written now so solo-mode models do not block it. Owner: Architect. Delivery is through the web app (`WEB_APP_SPEC.md`) and the connectors (`INTEGRATIONS_SPEC.md`), including write-back of approved assignments to Jira, GitLab or GitHub.

## Goal

Help a team lead or a team match tickets and people using real evidence, while keeping humans in charge and employees comfortable.

## What changes from solo mode

| Area | Solo | Team |
| --- | --- | --- |
| People | one contributor | everyone in a team |
| Evidence | public GitHub | org Git history, Jira/Linear history, review activity, CV / self-declared skills |
| Constraints | hours per week | role and seniority, workload, deadlines, sign-off areas |
| Output | best issues for me | best ticket for a person, best person for a ticket, sprint suggestions, onboarding path |
| Map | fit overlay for me | knowledge-silo view: clusters only one person can touch |

## Evidence sources

- **Git (org):** paths touched, languages, review requests received, reverted changes.
- **Jira/Linear:** ticket types and components completed, cycle time vs estimate.
- **CV / self-declared:** cold start for new hires; weaker signal that history confirms or overrides.

## Seniority as constraints

- Junior: well-scoped issues, effort cap, a named reviewer from the people strongest in that area.
- Senior: allowed ambiguous or cross-cutting issues; may be suggested as mentor.
- Sign-off areas (e.g. payments) require a role flag.

## Assignment optimisation

Balance across the team: workload, deadlines, growth goals, and bus factor (pair a second person onto areas held by one). Always suggestions with reasons; the lead decides.

## Must-haves before building

All of `docs/PRIVACY_SPEC.md`.
