#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/detect_docker.sh
source "$ROOT/scripts/detect_docker.sh"

HOST="${GALAXY_HOST:-127.0.0.1}"
PORT="${GALAXY_PORT:-9090}"
BUILD_IMAGE=0

for arg in "$@"; do
  case "$arg" in
    --build)
      BUILD_IMAGE=1
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/serve_galaxy_demo.sh [--build]

Start a local Planemo/Galaxy demo with the RMSX tool and native Molstar
visualization plugin registered. Set GALAXY_PORT to use a port other than 9090.
Use --build to build the local RMSX Galaxy runtime image first.
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

python3 scripts/build_rmsx_datatypes_config.py

echo "Starting Galaxy on http://$HOST:$PORT"
echo "After Galaxy opens: Tools -> RMSX trajectory analysis -> Load example data -> Execute."
echo "Then open the Molstar viewer manifest with Visualize -> RMSX Molstar FlipBook."

GALAXY_CONFIG_OVERRIDE_DATATYPES_CONFIG_FILE="$ROOT/config/datatypes/merged_datatypes_conf.xml" \
GALAXY_CONFIG_OVERRIDE_VISUALIZATION_PLUGINS_DIRECTORY="$ROOT/config/plugins/visualizations" \
env HOME="$ROOT/.planemo-home" \
  .venv-planemo/bin/planemo serve \
    --host "$HOST" \
    --port "$PORT" \
    --install_prebuilt_client \
    --docker \
    --docker_cmd "$DOCKER_BIN" \
    --job_config_file config/planemo_docker_job_conf.yml \
    --no_conda_auto_install \
    --no_conda_auto_init \
    tools/rmsx/rmsx.xml &

PLANEMO_PID=$!

cleanup() {
  if kill -0 "$PLANEMO_PID" >/dev/null 2>&1; then
    kill "$PLANEMO_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup INT TERM EXIT

SYNC_LOG="/tmp/rmsx_galaxy_visualization_sync.log"
SYNCED=0
for _ in {1..90}; do
  if python3 scripts/sync_visualization_static.py >"$SYNC_LOG" 2>&1; then
    cat "$SYNC_LOG"
    SYNCED=1
    break
  fi
  if ! kill -0 "$PLANEMO_PID" >/dev/null 2>&1; then
    cat "$SYNC_LOG" 2>/dev/null || true
    wait "$PLANEMO_PID"
    exit $?
  fi
  sleep 2
done

if [[ "$SYNCED" -eq 0 ]]; then
  echo "Galaxy is still starting, but the visualization static sync did not finish yet."
  echo "Once Galaxy is fully up, run: python3 scripts/sync_visualization_static.py"
else
  echo "Visualization assets synced."
fi

echo "Demo URL: http://$HOST:$PORT"
wait "$PLANEMO_PID"
