# EVALS

One file per evaluation run: `<YYYY-MM-DD>-<owner>-<repo>.md`. Follow `docs/EVALUATION_SPEC.md`.

## Template

```markdown
# Eval <date> <owner/repo>
**Cutoff:** <date>   **Commit:** <git sha>   **Config changes from default:** ...
| Metric | Ours | Random | Label only | Label + language |
| --- | --- | --- | --- | --- |
| recall@5 (person -> issues) | | | | |
| Spearman (effort vs PR lines) | | n/a | n/a | n/a |
| Availability precision | | | | |
**Notes:** what changed, what looks wrong, next tuning step.
```

Aggregate numbers only. No raw personal data.
