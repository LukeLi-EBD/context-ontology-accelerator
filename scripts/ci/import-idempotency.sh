#!/usr/bin/env bash
# P1-02: repeatable-import gate.
#
# Starts a throwaway PostgreSQL (pgvector image), runs the real `import` CLI
# three times over a fixed three-file corpus, then an embedding-outage /
# --retry-failed pair, and asserts the outcome. The container is removed when
# the script exits, pass or fail.
#
# Local use is the same command; set IMPORT_GATE_PG_DSN to point at an existing
# disposable database and no container is started. IMPORT_GATE_USE_UV=1 uses
# `uv run python` (what CI does after setup-build).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

IMAGE="${IMPORT_GATE_PG_IMAGE:-pgvector/pgvector:pg18-trixie}"
CONTAINER=""
STARTED_PG=0

cleanup() {
  if [[ -n "$CONTAINER" ]]; then
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ -z "${IMPORT_GATE_PG_DSN:-}" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "import-gate: docker is required to start the throwaway PostgreSQL" >&2
    exit 2
  fi
  PORT="${IMPORT_GATE_PORT:-}"
  if [[ -z "$PORT" ]]; then
    PORT="$(python3 - <<'PY' 2>/dev/null || echo 55432
import socket
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1])
sock.close()
PY
)"
  fi
  CONTAINER="p1-02-import-gate-$$"
  echo "import-gate: starting $IMAGE on 127.0.0.1:${PORT} (${CONTAINER})"
  docker run -d --rm --name "$CONTAINER" \
    -e POSTGRES_USER=platform \
    -e POSTGRES_PASSWORD=gate \
    -e POSTGRES_DB=platform \
    -p "127.0.0.1:${PORT}:5432" \
    "$IMAGE" >/dev/null
  STARTED_PG=1
  ready=0
  for _ in $(seq 1 60); do
    if docker exec "$CONTAINER" pg_isready -U platform -d platform >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "$ready" -ne 1 ]]; then
    echo "import-gate: PostgreSQL did not become ready" >&2
    docker logs "$CONTAINER" >&2 || true
    exit 2
  fi
  export IMPORT_GATE_PG_DSN="postgresql://platform:gate@127.0.0.1:${PORT}/platform"
fi

# The DB-backed importer suite uses TEST_PG_DSN; reuse the same throwaway.
export TEST_PG_DSN="${TEST_PG_DSN:-$IMPORT_GATE_PG_DSN}"

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

if [[ "${IMPORT_GATE_USE_UV:-0}" == "1" ]]; then
  PY=(uv run python)
else
  PY=("${PYTHON:-python3}")
fi

echo "import-gate: three-run idempotency"
"${PY[@]}" -m unittest discover \
  -s packages/platform-core/tests -p 'test_import_gate.py' -v

echo "import-gate: importer ledger regressions"
"${PY[@]}" -m unittest discover \
  -s packages/platform-core/tests -p 'test_importer_runs.py' -v

if [[ "$STARTED_PG" -eq 1 ]]; then
  echo "import-gate: pass; removing $CONTAINER"
fi
