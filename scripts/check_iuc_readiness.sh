#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MAX_BYTES="${IUC_MAX_FILE_BYTES:-1048576}"

echo "== IUC candidate file-size audit =="
echo "Limit: $MAX_BYTES bytes"

mapfile -t large_files < <(
  find tools/flipbook \
    -type f \
    -not -path '*/__pycache__/*' \
    -size +"${MAX_BYTES}"c \
    -print | sort
)

if ((${#large_files[@]} > 0)); then
  echo "Files over the IUC candidate limit:"
  for path in "${large_files[@]}"; do
    bytes="$(wc -c < "$path" | tr -d ' ')"
    echo "  $bytes  $path"
  done
  echo
  echo "Replace oversized test fixtures before opening a tools-iuc PR." >&2
  exit 1
fi

echo "No oversized files in tools/flipbook."

echo "== Runtime package-install audit =="
if grep -RInE 'install\.packages|BiocManager::install|remotes::install_|pak::pkg_install|renv::restore' \
  tools/flipbook packaging/flipbook-galaxy config 2>/dev/null; then
  echo
  echo "Found runtime package-install markers in the IUC candidate tree." >&2
  echo "Galaxy jobs should use declared Conda/container dependencies, not install packages at runtime." >&2
  exit 1
fi
echo "No runtime package-install markers found in the checked project paths."

echo "== Conservative wrapper checks =="
grep -q 'profile="26.0"' tools/flipbook/flipbook.xml
grep -q '<data name="viewer_manifest" format="json"' tools/flipbook/flipbook.xml
grep -q 'RMSX_REF=v0.2.3' packaging/flipbook-galaxy/Dockerfile
grep -q '@VERSION_SUFFIX@' tools/flipbook/flipbook.xml
echo "Wrapper readiness markers are present."
