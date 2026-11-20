# FIXTURES

Recorded, scrubbed GitHub API responses for offline tests. One folder per repo: `tests/fixtures/<owner>__<repo>/`.

Rules (see `docs/INGEST_SPEC.md`):
- Record once with the ingest `--record` dev flag, then scrub: no tokens, no emails, no private data.
- Keep each fixture small (a few pages). Tests never hit the network.
