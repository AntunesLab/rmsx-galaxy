#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WITH_CONTAINER=0
for arg in "$@"; do
  case "$arg" in
    --with-container)
      WITH_CONTAINER=1
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/bootstrap_dev.sh [--with-container]

Create the project-local Planemo environment and install browser-test
dependencies. Add --with-container to also build the local RMSX Galaxy runtime
image tagged as ghcr.io/antuneslab/rmsx-galaxy:0.1.0.
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if [[ ! -x .venv-planemo/bin/planemo ]]; then
  echo "Creating .venv-planemo and installing Planemo..."
  python3 -m venv .venv-planemo
  .venv-planemo/bin/python -m pip install --upgrade pip
  .venv-planemo/bin/python -m pip install planemo
else
  echo "Planemo environment already exists: .venv-planemo"
fi

if command -v pnpm >/dev/null 2>&1; then
  echo "Installing Node dependencies with pnpm..."
  pnpm install
elif command -v corepack >/dev/null 2>&1; then
  echo "Installing Node dependencies with corepack/pnpm..."
  if ! corepack pnpm install; then
    echo "corepack could not run pnpm; skipping optional Playwright dependencies."
    echo "The Galaxy tool demo can still run. Install pnpm later for browser checks."
  fi
else
  echo "pnpm/corepack not found; skipping optional Playwright dependencies."
  echo "Install Node.js with corepack or pnpm before running browser checks."
fi

if [[ "$WITH_CONTAINER" -eq 1 ]]; then
  scripts/build_container.sh
else
  echo "Container build skipped. Run scripts/build_container.sh before Planemo Docker tests or demos."
fi

echo "Bootstrap complete."
