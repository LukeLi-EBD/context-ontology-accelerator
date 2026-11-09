"""COA ``GraphClient`` backed by platform_core's Oxigraph AD (PF-0008).

The platform adapter ``OxigraphHttpStore`` is synchronous and returns SPARQL
results as ``{"bindings": [{"values": {name: term}}]}``. This module adapts it to
the COA ``GraphClient`` contract: async methods, flat ``{variable: value}`` rows.

Read-only by construction: only ``query`` (SELECT) and ``ask`` are exposed; the
underlying store's ``update`` / ``clear_graph`` are never called here.
"""

from __future__ import annotations

import asyncio
from typing import Any

from coa_serve.clients.base import GraphClient  # noqa: F401 - runtime contract
from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.errors import PortError


def _flat(term: dict[str, Any]) -> str | None:
    """One platform term dict -> the plain string a COA binding row carries."""
    kind = term.get("kind")
    if kind == "iri":
        return term.get("iri")
    if kind == "bnode":
        return term.get("label")
    return term.get("value")


class PlatformGraphStoreClient:
    """Async ``GraphClient`` over a synchronous platform_core GraphStore."""

    backend = "platform-graph"

    def __init__(self, store: Any, endpoint: str) -> None:
        self._store = store
        self._endpoint = endpoint

    async def query(self, sparql: str) -> list[dict[str, Any]]:
        result = await asyncio.to_thread(self._store.query, sparql)
        if result.get("kind") != "select":
            raise PortError(
                code="InvalidArgument",
                message="query() expected a SELECT result",
                provider=self.backend,
                provider_code="E_GRAPH_RESULT_KIND",
            )
        return [
            {name: _flat(term) for name, term in row.get("values", {}).items()}
            for row in result.get("bindings", [])
        ]

    async def ask(self, sparql: str) -> bool:
        return await asyncio.to_thread(self._store.ask, sparql)

    async def health_check(self) -> dict[str, Any]:
        """Probe reachability; never raises (COA contract requirement)."""
        try:
            await self.ask("ASK {}")
            return {"ok": True, "backend": self.backend, "endpoint": self._endpoint}
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "backend": self.backend,
                "endpoint": self._endpoint,
                "error": f"{type(exc).__name__}: {exc}",
            }

    async def close(self) -> None:
        await asyncio.to_thread(self._store.close)


class OxigraphGraphClient(PlatformGraphStoreClient):
    """``GraphClient`` over the platform Oxigraph HTTP adapter."""

    backend = "oxigraph"

    def __init__(self, endpoint: str, *, timeout_ms: int = 30000, max_rows: int = 10000) -> None:
        base = endpoint.rstrip("/")
        super().__init__(
            OxigraphHttpStore(base, timeout_ms=timeout_ms, max_rows=max_rows),
            base,
        )


__all__ = ["OxigraphGraphClient", "PlatformGraphStoreClient"]
