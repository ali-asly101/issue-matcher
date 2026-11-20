# CLI SPEC

Owner: Architect (wiring); each command calls the owning module. Commands, flags and exit codes are fixed in `docs/CONTRACT.md` section 5.

## Output style

- Default: a readable table (rank, issue, title, fit label, effort label, confidence label) followed by reasons and first steps for each pick. No raw numbers in the default output; `--json` carries both numbers and labels.
- `--json`: machine-readable, exactly the contract models.
- Unavailable counts are summarised in one line ("Filtered 212: 120 assigned, 61 open PR, 31 stale"); `--show-filtered` lists them.
- Errors: one plain sentence saying what went wrong and what to do ("No GITHUB_TOKEN found. Copy .env.example to .env and add a token.").

## Example

```text
$ issuematch match psf/requests --user alyelbasir --top 3

#1  psf/requests#6512  Retry adapter ignores backoff on 503     Great fit  ·  Small, about 2 to 4 hours  ·  High confidence
    - You've merged 2 PRs touching src/requests/adapters.py (#6301, #6420).
    - Similar issues took 30 to 90 changed lines (#6044, #6187).
    Start: read src/requests/adapters.py, then PR #6187.
...
Filtered 140: 88 assigned, 31 open PR, 21 stale.
```

(Illustrative only; the numbers are invented to show the layout.)

## Demo mode

`issuematch map --demo` and (later) `issuematch match --demo` run on built-in sample data, so the CLI can be shown without a token.
