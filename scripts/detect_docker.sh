#!/usr/bin/env bash
# Shared Docker command detection for local Galaxy/Planemo helpers.

detect_docker_cmd() {
  if [[ -n "${DOCKER_CMD:-}" ]]; then
    printf '%s\n' "$DOCKER_CMD"
    return 0
  fi

  if command -v docker >/dev/null 2>&1; then
    command -v docker
    return 0
  fi

  local macos_docker="/Applications/Docker.app/Contents/Resources/bin/docker"
  if [[ -x "$macos_docker" ]]; then
    printf '%s\n' "$macos_docker"
    return 0
  fi

  return 1
}
