#!/usr/bin/env bash
# Migration idempotency gate (P1-03).
#
# Starts a throwaway PostgreSQL (no volume, random host port), applies the real
# migration registry twice from an empty database, then asserts: full registry in
# one run ending at V53, max(schema_version)=53, second run applies nothing, no
# gaps, the nine V52 columns are nullable with no default, and the V53 pointer
# index exists. The container is removed when the script exits, pass or fail.
#
# Local use is the same command; set MIGRATION_GATE_PG_DSN to point at an
# existing disposable database and no container is started.
# MIGRATION_GATE_USE_UV=1 uses `uv run python` (what CI does after setup-build).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYBIN="${PYTHON:-python3}"

IMAGE="${MIGRATION_GATE_PG_IMAGE:-pgvector/pgvector:pg18-trixie}"
CONTAINER=""

cleanup() {
  if [[ -n "$CONTAINER" ]]; then
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# Never take a port the local stacks rely on.
pick_port() {
  "$PYBIN" - <<'PY'
import socket

blocked = {5444, 5944, 8799, 8099, 8102}
for _ in range(50):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    if port not in blocked:
        print(port)
        break
else:
    raise SystemExit("no free port found")
PY
}

if [[ -z "${MIGRATION_GATE_PG_DSN:-}" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "migration-gate: docker is required to start the throwaway PostgreSQL" >&2
    exit 2
  fi
  PORT="${MIGRATION_GATE_PORT:-$(pick_port)}"
  PORT="${PORT//$'\r'/}"
  PORT="${PORT//[[:space:]]/}"
  CONTAINER="p1-mig-gate-$$"
  echo "migration-gate: starting $IMAGE on 127.0.0.1:${PORT} (${CONTAINER})"
  docker run -d --rm --name "$CONTAINER" \
    -e POSTGRES_USER=platform \
    -e POSTGRES_PASSWORD=gate \
    -e POSTGRES_DB=platform \
    -p "127.0.0.1:${PORT}:5432" \
    "$IMAGE" >/dev/null
  ready=0
  for _ in $(seq 1 60); do
    if docker exec "$CONTAINER" pg_isready -U platform -d platform >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "$ready" -ne 1 ]]; then
    echo "migration-gate: PostgreSQL did not become ready" >&2
    docker logs "$CONTAINER" >&2 || true
    exit 2
  fi
  export MIGRATION_GATE_PG_DSN="postgresql://platform:gate@127.0.0.1:${PORT}/platform"
fi

python_path="$ROOT/packages/platform-core/src"
for dir in "$ROOT"/packages/*/src "$ROOT"/libs/*/src; do
  [[ -d "$dir" ]] || continue
  case "$python_path" in
    *"$dir"*) ;;
    *) python_path="$python_path:$dir" ;;
  esac
done
python_path="$python_path:$ROOT/smithy-generated/control-plane-python-server"
export PYTHONPATH="$python_path${PYTHONPATH:+:$PYTHONPATH}"

if [[ "${MIGRATION_GATE_USE_UV:-0}" == "1" ]]; then
  PY=(uv run python)
else
  PY=("$PYBIN")
fi

echo "migration-gate: apply twice and assert schema invariants"
"${PY[@]}" "$ROOT/scripts/ci/migration_idempotency_gate.py"

if [[ -n "$CONTAINER" ]]; then
  echo "migration-gate: pass; removing $CONTAINER"
fi
