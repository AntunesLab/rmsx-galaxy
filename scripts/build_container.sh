#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/detect_docker.sh
source "$ROOT/scripts/detect_docker.sh"

TAG="${FLIPBOOK_GALAXY_CONTAINER_TAG:-${RMSX_GALAXY_CONTAINER_TAG:-ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0}}"
LOCAL_TAG="${FLIPBOOK_GALAXY_LOCAL_TAG:-${RMSX_GALAXY_LOCAL_TAG:-flipbook-galaxy:0.2.3-galaxy0}}"

if ! DOCKER_BIN="$(detect_docker_cmd)"; then
  echo "Docker was not found. Install Docker Desktop or set DOCKER_CMD=/path/to/docker." >&2
  exit 1
fi

if ! "$DOCKER_BIN" info >/dev/null 2>&1; then
  echo "Docker is installed but not running or not reachable: $DOCKER_BIN" >&2
  exit 1
fi

echo "Building Flipbook Galaxy runtime image..."
echo "Docker: $DOCKER_BIN"
echo "Tags:   $TAG, $LOCAL_TAG"
"$DOCKER_BIN" build -t "$TAG" -t "$LOCAL_TAG" packaging/flipbook-galaxy

echo "Container ready:"
"$DOCKER_BIN" image inspect "$TAG" --format '  {{.RepoTags}}'
