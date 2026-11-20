#!/usr/bin/env bash
# One-time setup on macOS or Linux. Run from the project root: ./scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv (Python package manager)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing Python 3.12 and dependencies..."
uv python install 3.12
uv sync

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Add your GITHUB_TOKEN to it."
fi

if command -v git >/dev/null 2>&1 && [ ! -d .git ]; then
  git init -q -b main
  echo "Initialised a git repo on branch main."
fi

if uv run pre-commit --version >/dev/null 2>&1; then
  uv run pre-commit install
fi

echo
echo "Setup done. Next: ./scripts/check.sh"
