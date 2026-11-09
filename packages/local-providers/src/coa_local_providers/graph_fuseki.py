"""COA ``GraphClient`` backed by platform_core's Fuseki AD (PF-0007).

Same adaptation as ``graph_oxigraph``: the platform ``FusekiHttpStore`` is
synchronous, so the COA method surface is an async thin shell. The platform
adapter expects the Fuseki **server root** (it appends ``/{dataset}``), which is
different from the gateway-native provider's ``.../ds/sparql`` URL.
"""

from __future__ import annotations

from platform_core.adapters.graph_fuseki import FusekiHttpStore

from .graph_oxigraph import PlatformGraphStoreClient


class FusekiGraphClient(PlatformGraphStoreClient):
    """``GraphClient`` over the platform Fuseki HTTP adapter."""

    backend = "jena-fuseki"

    def __init__(
        self,
        endpoint: str,
        *,
        dataset: str = "ds",
        timeout_ms: int = 30000,
        max_rows: int = 10000,
    ) -> None:
        base = endpoint.rstrip("/")
        super().__init__(
            FusekiHttpStore(base, dataset=dataset, timeout_ms=timeout_ms, max_rows=max_rows),
            f"{base}/{dataset.strip('/')}",
        )


__all__ = ["FusekiGraphClient"]
