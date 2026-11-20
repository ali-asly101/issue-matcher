# SKILL PROFILE SPEC

Owner: Profile agent. Code: `src/issuematch/profile/`.

## Goal

Describe what a Person can do, from **evidence**, not self-report. Self-report adds goals and constraints, and fills gaps for new people.

## Skill names

Namespaced strings so they compare cleanly:

| Prefix | Example | From |
| --- | --- | --- |
| `lang:` | `lang:python`, `lang:rust` | file extensions in their commits/PRs, repo languages |
| `area:` | `area:src/parser` | paths touched in the **target repo** (strongest signal) |
| `concept:` | `concept:async`, `concept:sql`, `concept:ci` | imports, frameworks, config files, labels of issues they closed |
| `tool:` | `tool:docker`, `tool:github-actions` | files like `Dockerfile`, `.github/workflows/*` |

## Evidence sources (solo mode)

1. Merged PRs by the person in the target repo (weight high).
2. Merged PRs by the person anywhere public (weight medium).
3. Their own repos: languages, recent commits (weight low to medium; recent beats old).
4. Self-declared: `--learn X` (adds to `want_to_learn`, not to skills), `--hours N`.

## Level and confidence

- `level` grows with volume and recency of evidence, saturating (e.g. `1 - exp(-n / k)` with recency decay). Put `k` and the decay half-life in config when implemented.
- `confidence` grows with the number of independent sources.
- `typical_change_lines` = median additions + deletions over their merged PRs.

## Rules

- Every `Skill` lists the evidence refs that produced it.
- Never infer anything personal beyond technical skills.
- Profiles are cached in the store and rebuilt when older than 7 days or on `--refresh`.

## Acceptance tests

- [ ] Fixture user with Python + Rust PRs gets `lang:python` and `lang:rust`, each with evidence.
- [ ] Paths touched in the target repo become `area:` skills.
- [ ] `--learn` values never appear as skills.
- [ ] A user with no history gets an empty profile with low confidence, not a crash.
