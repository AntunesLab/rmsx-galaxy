#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REMOTE=1
if [[ "${1:-}" == "--local" ]]; then
  REMOTE=0
elif [[ -n "${1:-}" ]]; then
  echo "Usage: scripts/check_server_deployment_readiness.sh [--local]" >&2
  exit 2
fi

# The preferred public-server route is the computational chemistry repository,
# which publishes under the established chemteam Tool Shed owner.
TOOL_OWNER="${FLIPBOOK_TOOL_SHED_OWNER:-chemteam}"
TOOL_NAME="flipbook"
VIEWER_VERSION="0.0.2"
PENDING=0

if [[ -x /usr/bin/curl ]]; then
  CURL_BIN=/usr/bin/curl
elif command -v curl >/dev/null 2>&1; then
  CURL_BIN="$(command -v curl)"
else
  CURL_BIN=""
fi

pass() {
  printf 'PASS     %s\n' "$1"
}

pending() {
  printf 'PENDING  %s\n' "$1"
  PENDING=$((PENDING + 1))
}

echo "== Local release metadata =="
container_image="$({ python3 - <<'PY'
from pathlib import Path
from xml.etree import ElementTree

root = ElementTree.parse(Path("tools/flipbook/macros.xml")).getroot()
for token in root.findall("token"):
    if token.attrib.get("name") == "@CONTAINER_IMAGE@":
        print((token.text or "").strip())
        break
else:
    raise SystemExit("@CONTAINER_IMAGE@ token not found")
PY
} )"

if [[ "$container_image" == "ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0" ]]; then
  pass "wrapper pins ${container_image}"
else
  pending "wrapper container tag is unexpected: ${container_image}"
fi

if grep -Fq 'org.opencontainers.image.source="https://github.com/AntunesLab/rmsx-galaxy"' \
  packaging/flipbook-galaxy/Dockerfile; then
  pass "container is linked to the public source repository"
else
  pending "container is missing its GHCR source-repository label"
fi

if [[ -f tools/flipbook/static/images/flipbook_logo.png ]]; then
  pass "tool logo is packaged with the wrapper"
else
  pending "tool logo is missing"
fi

scripts/check_iuc_readiness.sh
pass "local IUC candidate checks"

if [[ "$REMOTE" -eq 0 ]]; then
  echo
  echo "Remote checks skipped."
  exit "$PENDING"
fi

echo
echo "== Public deployment artifacts =="
if docker manifest inspect "$container_image" >/dev/null 2>&1; then
  pass "container is anonymously resolvable from GHCR"
else
  pending "container is not anonymously resolvable from GHCR"
fi

for shed in \
  "Test Tool Shed|https://testtoolshed.g2.bx.psu.edu" \
  "Main Tool Shed|https://toolshed.g2.bx.psu.edu"; do
  label="${shed%%|*}"
  base_url="${shed#*|}"
  if [[ -n "$CURL_BIN" ]]; then
    response="$("$CURL_BIN" -fsSL "${base_url}/api/repositories?name=${TOOL_NAME}&owner=${TOOL_OWNER}" || printf '[]')"
  else
    response='[]'
  fi
  count="$(python3 -c 'import json,sys; print(len(json.load(sys.stdin)))' <<<"$response" 2>/dev/null || printf '0')"
  if [[ "$count" -gt 0 ]]; then
    pass "${TOOL_OWNER}/${TOOL_NAME} exists in ${label}"
  else
    pending "${TOOL_OWNER}/${TOOL_NAME} is absent from ${label}"
  fi
done

if [[ -n "$CURL_BIN" ]] && "$CURL_BIN" -fsSL "https://registry.npmjs.org/@galaxyproject%2Frmsxflipbook/${VIEWER_VERSION}" >/dev/null 2>&1; then
  pass "@galaxyproject/rmsxflipbook@${VIEWER_VERSION} is published"
else
  pending "@galaxyproject/rmsxflipbook@${VIEWER_VERSION} is not published"
fi

if command -v gh >/dev/null 2>&1; then
  for pr in \
    "galaxyproject/galaxy-visualizations|174|viewer package" \
    "galaxyproject/galaxy|23009|Galaxy datatype and visualization registration"; do
    repo="${pr%%|*}"
    remainder="${pr#*|}"
    number="${remainder%%|*}"
    label="${remainder#*|}"
    state="$(gh pr view "$number" --repo "$repo" --json state --jq .state 2>/dev/null || printf 'UNKNOWN')"
    if [[ "$state" == "MERGED" ]]; then
      pass "${label} PR is merged"
    else
      pending "${label} PR is ${state} (${repo}#${number})"
    fi
  done
else
  pending "GitHub CLI is unavailable; upstream viewer PRs were not checked"
fi

echo
if [[ "$PENDING" -eq 0 ]]; then
  echo "READY: Europe and Galaxy Main tool-list entries can be locked and proposed."
else
  echo "NOT READY: ${PENDING} deployment prerequisite(s) remain."
fi
exit "$PENDING"
