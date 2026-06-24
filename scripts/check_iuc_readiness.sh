#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MAX_BYTES="${IUC_MAX_FILE_BYTES:-1048576}"

echo "== IUC candidate file-size audit =="
echo "Limit: $MAX_BYTES bytes"

mapfile -t large_files < <(
  find tools/rmsx \
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

echo "No oversized files in tools/rmsx."

echo "== Conservative wrapper checks =="
grep -q 'profile="26.0"' tools/rmsx/rmsx.xml
grep -q '<data name="viewer_manifest" format="json"' tools/rmsx/rmsx.xml
grep -q 'RMSX_REF=v0.2.3' packaging/rmsx-galaxy/Dockerfile
grep -q '@VERSION_SUFFIX@' tools/rmsx/rmsx.xml
echo "Wrapper readiness markers are present."
