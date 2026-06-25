#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/detect_docker.sh
source "$ROOT/scripts/detect_docker.sh"

BUILD_IMAGE=0
for arg in "$@"; do
  case "$arg" in
    --build)
      BUILD_IMAGE=1
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/run_planemo_tests.sh [--build]

Run the Docker-backed Planemo test suite for tools/flipbook/flipbook.xml.
Use --build to build the local Flipbook Galaxy runtime image first.
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ ! -x .venv-planemo/bin/planemo ]]; then
  echo "Planemo is missing. Run scripts/bootstrap_dev.sh first." >&2
  exit 1
fi

if ! DOCKER_BIN="$(detect_docker_cmd)"; then
  echo "Docker was not found. Install Docker Desktop or set DOCKER_CMD=/path/to/docker." >&2
  exit 1
fi

if [[ "$BUILD_IMAGE" -eq 1 ]]; then
  scripts/build_container.sh
fi

python3 scripts/build_flipbook_datatypes_config.py

env HOME="$ROOT/.planemo-home" \
  GALAXY_CONFIG_OVERRIDE_DATATYPES_CONFIG_FILE="$ROOT/config/datatypes/merged_datatypes_conf.xml" \
  .venv-planemo/bin/planemo test \
    --install_galaxy \
    --docker \
    --docker_cmd "$DOCKER_BIN" \
    --job_config_file config/planemo_docker_job_conf.yml \
    --no_conda_auto_install \
    --no_conda_auto_init \
    --test_output tool_test_output.html \
    --test_output_json tool_test_output.json \
    --job_output_files planemo-test-output \
    --test_timeout "${PLANEMO_TEST_TIMEOUT:-300}" \
    tools/flipbook/flipbook.xml
