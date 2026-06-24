#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Python compile checks =="
python3 -m py_compile tools/flipbook/*.py scripts/*.py

echo "== Manifest and visualization smoke test =="
python3 tests/flipbook/test_manifest_and_visualization.py

if command -v node >/dev/null 2>&1; then
  echo "== Native visualization JavaScript syntax check =="
  node --check config/plugins/visualizations/flipbook_molstar/static/script.js
else
  echo "Node.js not found; skipping JavaScript syntax check."
fi

if [[ -x .venv-planemo/bin/planemo ]]; then
  echo "== Planemo lint =="
  .venv-planemo/bin/planemo lint --fail_level error tools/flipbook/flipbook.xml

  echo "== Planemo shed_lint =="
  if python3 -c 'import socket; socket.getaddrinfo("toolshed.g2.bx.psu.edu", 443)' >/dev/null 2>&1; then
    if [[ "${STRICT_SHED_LINT:-0}" == "1" ]]; then
      .venv-planemo/bin/planemo shed_lint tools/flipbook
    elif ! .venv-planemo/bin/planemo shed_lint tools/flipbook; then
      echo "planemo shed_lint did not complete. Set STRICT_SHED_LINT=1 in CI or publication checks if this should fail the run."
    fi
  elif [[ "${STRICT_SHED_LINT:-0}" == "1" ]]; then
    echo "Cannot resolve toolshed.g2.bx.psu.edu, and STRICT_SHED_LINT=1 was set." >&2
    exit 1
  else
    echo "Skipping planemo shed_lint because toolshed.g2.bx.psu.edu is not reachable."
    echo "Set STRICT_SHED_LINT=1 in CI or publication checks if this should fail the run."
  fi
else
  echo "Planemo environment missing; skipping Planemo lint."
  echo "Run scripts/bootstrap_dev.sh to create .venv-planemo."
fi

if [[ "${CHECK_IUC_READY:-0}" == "1" ]]; then
  echo "== IUC readiness gate =="
  scripts/check_iuc_readiness.sh
else
  echo "Skipping IUC readiness gate. Set CHECK_IUC_READY=1 to enforce the Tool Shed candidate file-size and metadata checks."
fi

echo "Static checks complete."
