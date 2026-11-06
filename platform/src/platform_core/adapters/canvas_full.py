"""D1-2 canvas provider skeleton (recognised but not assembled yet).

``canvas.provider=full`` is rejected at config load with
``E_PROVIDER_NOT_IMPLEMENTED``; this class exists so the port signature and
manifest stay defined and both implementations cannot drift (design 53 §4.2).
"""

from __future__ import annotations

from typing import Any

from ..errors import PortError
from ..ports import Manifest

HARD_HOPS = 6
HARD_NODES = 1000
HARD_EDGES = 1500
HARD_PATHS = 50


class FullCanvas:
    """Placeholder: every call fails explicitly, no fake graph data."""

    port = "CanvasPort"

    def manifest(self) -> Manifest:
        return Manifest(
            provider="full",
            port=self.port,
            capabilities=["canvas.subgraph", "canvas.path", "canvas.expand"],
            limits={
                "hops": HARD_HOPS,
                "nodes": HARD_NODES,
                "edges": HARD_EDGES,
                "paths": HARD_PATHS,
            },
            notes={"status": "not_implemented", "slice": "D1-2"},
        )

    def _raise(self, method: str) -> Any:
        raise PortError(
            code="Unsupported",
            message=f"canvas.provider=full: {method} is a known provider but no adapter is assembled (D1-2)",
            provider="full",
            provider_code="E_PROVIDER_NOT_IMPLEMENTED",
            details={"provider": "full", "slice": "D1-2", "method": method},
        )

    def subgraph(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return self._raise("subgraph")

    def path(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return self._raise("path")

    def expand(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return self._raise("expand")
