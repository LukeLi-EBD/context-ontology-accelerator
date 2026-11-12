#!/bin/sh
# Thin POSIX launcher for check-missing-tracked.py (the real implementation).
# Finds python3/python and execs the .py next to this file, so the exit code
# (0/1/2/3) and stdout/stderr pass through unchanged.
#
# Interpreter search order: $COA_PYTHON, python3, python.
set -u

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
script="$here/check-missing-tracked.py"

py=${COA_PYTHON:-}
if [ -z "$py" ]; then
    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            py=$candidate
            break
        fi
    done
fi

if [ -z "$py" ]; then
    echo "[COA-WATCH][ERR] no Python 3 found; install python3 or set COA_PYTHON" >&2
    exit 3
fi

exec "$py" "$script" "$@"
