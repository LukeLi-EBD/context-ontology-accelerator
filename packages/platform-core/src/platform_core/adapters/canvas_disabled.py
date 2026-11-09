"""``canvas.provider=off``: the canvas port is assembled but disabled.

The endpoint answers 503 ``E_CANVAS_DISABLED`` and nothing else changes
(design 53 §5.2, A-04).
"""

from __future__ import annotations

from typing import Any

from ..errors import PortError
from ..ports import Manifest

DISABLED_CODE = "E_CANVAS_DISABLED"


class DisabledCanvas:
    port = "CanvasPort"

    def __init__(self, reason: str = "canvas.provider=off") -> None:
        self._reason = reason

    def manifest(self) -> Manifest:
        return Manifest(
            provider="absent",
            port=self.port,
            capabilities=[],
            notes={"status": "disabled", "reason": self._reason},
        )

    def _raise(self, method: str) -> Any:
        raise PortError(
            code="Unavailable",
            message=f"canvas is disabled: {self._reason} ({method})",
            provider="absent",
            provider_code=DISABLED_CODE,
            details={"reason": self._reason, "method": method},
        )

    def subgraph(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return self._raise("subgraph")

    def path(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return self._raise("path")

    def expand(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return self._raise("expand")
