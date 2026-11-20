#!/usr/bin/env bash
# Definition-of-done checks 1 to 4 from CLAUDE.md. Run from anywhere: ./scripts/check.sh
# Pass --fix to auto-fix lint and formatting first.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" = "--fix" ]; then
  uv run ruff check --fix .
  uv run ruff format .
fi

echo "== 1. ruff check";        uv run ruff check .
echo "== 2. ruff format --check"; uv run ruff format --check .
echo "== 3. mypy (strict)";     uv run mypy
echo "== 4. pytest";            uv run pytest
echo
echo "All checks passed."
