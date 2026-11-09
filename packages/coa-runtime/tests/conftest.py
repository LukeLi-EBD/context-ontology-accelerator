"""Import path for the runtime tests: coa-ports plus the local implementations."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for relative in (
    "packages/coa-runtime/src",
    "packages/coa-ports/src",
    "packages/local-providers/src",
    "packages/platform-core/src",
    "packages/context-manager/src",
    "packages/control-plane/src",
    "packages/metric-service/src",
    "libs/common/src",
):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

# COA's shared library imports the Unix-only ``resource`` module; the local
# provider package ships the shim, so import it before anything else does.
try:  # pragma: no cover - platform dependent
    from coa_local_providers.win_compat import ensure_resource_module

    ensure_resource_module()
except Exception:  # noqa: BLE001 - absence of the shim must not break collection
    pass
