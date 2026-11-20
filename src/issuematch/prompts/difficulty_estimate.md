# Prompt: difficulty estimate (draft, milestone M6)

Owner: Estimator agent. Loaded by `llm/` at runtime. Placeholders in `{braces}` are filled in code. Changes to this prompt need an eval run (`docs/EVALUATION_SPEC.md`).

---

You are estimating how hard a GitHub issue is for a contributor who is new to this repository.

Repository: {repo}
Contributing notes (excerpt):
{contributing_excerpt}

Top-level file tree (excerpt):
{file_tree_excerpt}

Similar issues that were already fixed, with their merged PRs:
{neighbours}

The issue to estimate:
Title: {title}
Labels: {labels}
Body:
{body}

Return only JSON with these fields:
- "effort": number 0 to 1 (0 = trivial one-liner, 1 = multi-week, design-heavy)
- "est_hours_low", "est_hours_high": numbers, for a competent newcomer
- "concepts": short lowercase concepts needed, e.g. ["async", "unicode", "sql"]
- "likely_files": repo paths you expect to change, only from the tree or neighbours
- "unknowns": what is unclear in the issue that would change the estimate
- "confidence": number 0 to 1

Base the estimate mainly on the similar fixed issues. If the issue is a question or has no clear task, set effort to 0, confidence to 0, and put "not actionable" in unknowns.
