"""Make the source tree importable and install the Windows resource shim."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGES = Path(__file__).resolve().parents[2]
_REPO = _PACKAGES.parent
for _path in (
    str(_PACKAGES / "local-providers" / "src"),
    str(_PACKAGES / "coa-ports" / "src"),
    str(_PACKAGES / "platform-core" / "src"),
    str(_PACKAGES / "metric-service" / "src"),
    str(_REPO / "libs" / "common" / "src"),
):
    if _path not in sys.path:
        sys.path.insert(0, _path)

try:  # pragma: no cover - platform dependent
    from coa_local_providers.win_compat import ensure_resource_module

    ensure_resource_module()
except Exception:  # noqa: BLE001
    pass
