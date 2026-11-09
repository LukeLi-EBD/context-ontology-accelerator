"""Make the package tree importable when running this test directory directly."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGES = Path(__file__).resolve().parents[2]
_REPO = _PACKAGES.parent
for _path in (
    str(_PACKAGES / "control-plane" / "src"),
    str(_PACKAGES / "coa-ports" / "src"),
    str(_PACKAGES / "local-providers" / "src"),
    str(_REPO / "libs" / "common" / "src"),
):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# ``coa_common`` imports the Unix-only ``resource`` module; the local provider
# package ships the shim, so install it before the package is imported.
try:  # pragma: no cover - platform dependent
    from coa_local_providers.win_compat import ensure_resource_module

    ensure_resource_module()
except Exception:  # noqa: BLE001
    pass
