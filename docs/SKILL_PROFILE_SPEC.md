# SKILL PROFILE SPEC

Owner: Profile agent. Code: `src/issuematch/profile/`.

## Goal

Describe what a Person can do. Real history is the strongest evidence, but **nobody starts at zero**: a person with little or no history can upload a CV or add skills and keywords so they get matched from day one. Their profile then gets stronger automatically as they merge PRs and close tickets.

## Skill names

Namespaced strings so they compare cleanly:

| Prefix | Example | From |
| --- | --- | --- |
| `lang:` | `lang:python`, `lang:rust` | file extensions in their commits/PRs, repo languages, CV |
| `area:` | `area:src/parser`, `area:payments` | paths touched in the target repo; Jira components |
| `concept:` | `concept:async`, `concept:sql`, `concept:ci` | imports, frameworks, issue labels, CV |
| `tool:` | `tool:docker`, `tool:github-actions` | files like `Dockerfile`, `.github/workflows/*`, CV |

Free-text keywords from a CV or the person ("React", "REST APIs", "reverse engineering") are normalised to these names with a synonym table plus embedding similarity, e.g. "ReactJS" and "React.js" become `concept:react`. Unknown keywords are kept as `concept:<slug>` so nothing the person typed is lost. Optional later: map to the ESCO skills taxonomy for non-engineering roles.

## Evidence sources and how much they count

| Source | Example | Starting confidence | Skill status |
| --- | --- | --- | --- |
| Merged PR / MR in the target repo or workspace | 4 PRs touching `src/parser` | high (`EVIDENCE_CONFIDENCE`) | `verified` |
| Resolved ticket assigned to them (Jira/GitLab) | 6 tickets in component `payments` | high | `verified` |
| Code review they gave | reviewed 10 PRs in `api/` | medium | `verified` |
| Merged PR anywhere public | contributions to other repos | medium | `verified` |
| Their own repos | languages, recent commits | low to medium | `practising` |
| CV upload (PDF or DOCX) | "3 years Python, Django, PostgreSQL" | `CV_CONFIDENCE` | `declared` |
| Self-declared skills / keywords | chips the person adds, with a level | `DECLARED_CONFIDENCE` | `declared` |
| "Want to learn" | `async`, `rust` | n/a (goal, not a skill) | - |

`Skill.status` is one of:
- `declared`: only CV or self-declared evidence. Used for matching, shown with an amber dot.
- `practising`: some activity (own repos, small contributions) but below the verified threshold.
- `verified`: at least `VERIFIED_MIN_EVIDENCE` independent pieces of work evidence. Green dot.

## Cold start flow (person with little or no history)

1. On first sign-in, if the profile has fewer than `COLD_START_MIN_SKILLS` skills with work evidence, show the "Build your profile" step instead of empty picks.
2. Three ways in, all optional and combinable:
   - **Upload CV** (PDF or DOCX, max 5 MB). The LLM extracts skills, years, and technologies into a list of suggestions. The person reviews it: keep, remove or adjust the level of each before anything is saved. Nothing from the CV is used until they confirm.
   - **Add skills and keywords**: type-ahead chips from the skill taxonomy, each with a level (Learning / Comfortable / Strong).
   - **Paste links**: GitHub/GitLab profile, portfolio, personal repos. These are fetched as normal evidence.
3. Picks appear immediately, marked "Based on your declared skills" with lower confidence, and favour well-scoped, smaller tickets (effort cap `COLD_START_MAX_EFFORT`) so a first win is likely.

## How the profile grows

- Every merged PR/MR, resolved ticket or review is new evidence, added automatically on sync.
- A declared skill that gains work evidence moves `declared -> practising -> verified`; its confidence rises and its dot turns green. The person sees a short note: "Python is now verified by 3 merged PRs."
- Declared confidence decays slowly if nothing ever backs it up (half-life `DECLARED_DECAY_DAYS`), so the profile drifts towards what the person actually does. It never drops below a floor while the person keeps it on the profile.
- Work evidence also decays with age (recent beats old), so the profile follows the person's current work.
- The profile page shows a "strength" summary: how many skills are verified vs declared, and the single next step that would help most ("Merge one PR in `api/` to verify REST APIs").

## Level and confidence

- `level` grows with volume and recency of evidence, saturating: `1 - exp(-n / LEVEL_SATURATION)` with recency decay. Declared skills start at the level the person picked (Learning 0.25, Comfortable 0.5, Strong 0.75) capped by `DECLARED_MAX_LEVEL` until verified.
- `confidence` grows with the number of independent sources; declared-only skills stay at or below `DECLARED_CONFIDENCE` / `CV_CONFIDENCE`.
- `typical_change_lines` = median additions + deletions over their merged PRs (unknown for new people; ranking then uses the repo median).

## Rules

- Every `Skill` lists the evidence that produced it, including `cv` and `self_declared` evidence.
- Technical and work skills only. The CV parser must ignore and never store personal details (age, photo, address, nationality, marital status, etc.).
- The raw CV file is deleted after extraction by default; the workspace can opt to keep it. Only confirmed skills are stored.
- The person can edit, hide or remove any skill. Hidden skills are not used for matching and never shown to leads.
- Profiles are rebuilt on sync and at least every 7 days.

## Acceptance tests

- [ ] Fixture user with Python + Rust PRs gets `lang:python` and `lang:rust` as `verified`, each with evidence.
- [ ] Paths touched in the target repo become `area:` skills.
- [ ] `--learn` / "want to learn" values never appear as skills.
- [ ] A user with no history and three declared skills gets a profile with three `declared` skills at capped confidence, and picks limited by `COLD_START_MAX_EFFORT`.
- [ ] CV extraction on a fixture CV returns suggestions only; nothing is stored until confirmed; personal details are absent from the output.
- [ ] A declared skill that gains `VERIFIED_MIN_EVIDENCE` merged PRs becomes `verified`.
- [ ] A user with no history and no declared skills gets an empty profile with low confidence, not a crash.
