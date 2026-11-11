"""SPARQL 1.1 Query transport shared by the local graph providers.

The upstream contract is read-only, so this transport only ever posts SELECT/ASK
to a query endpoint; there is no Update path here.
"""

from __future__ import annotations

from typing import Any

import httpx

SPARQL_RESULTS_JSON = "application/sparql-results+json"

# Oxigraph's ``serve --timeout-s`` answers a cancelled query with HTTP 200: the
# body stops mid-stream and this sentence is appended to it.
CANCELLED_NOTICE = "The SPARQL operation has been cancelled"


class SparqlOperationCancelled(RuntimeError):
    """The endpoint cancelled the query at its own deadline; the rows are partial."""


# The acceptance graph store keeps its data in named graphs, so a bare
# ``?s ?p ?o`` default-graph ASK answers false on a store that is not empty.
GRAPH_HAS_TRIPLES = "ASK { { ?s ?p ?o } UNION { GRAPH ?g { ?s ?p ?o } } }"


class SparqlHttpGraphClient:
    """Read-only ``GraphClient`` over an HTTP SPARQL 1.1 query endpoint."""

    backend = "sparql-http"

    def __init__(
        self,
        query_url: str,
        *,
        endpoint: str | None = None,
        timeout_s: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._query_url = query_url
        self._endpoint = endpoint or query_url
        self._timeout_s = timeout_s
        self._transport = transport

    async def _post(self, sparql: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout_s, transport=self._transport) as client:
            response = await client.post(
                self._query_url,
                data={"query": sparql},
                headers={"Accept": SPARQL_RESULTS_JSON},
            )
            response.raise_for_status()
            if response.content[-len(CANCELLED_NOTICE) - 8 :].rstrip().endswith(CANCELLED_NOTICE.encode()):
                # The query was stopped at the endpoint's deadline; the body is a
                # fragment and must not be read as a complete answer.
                raise SparqlOperationCancelled(
                    f"{self._endpoint} cancelled the query at its server limit; the result is partial"
                )
            return response.json()

    async def query(self, sparql: str) -> list[dict[str, Any]]:
        """Execute a SPARQL SELECT; one flat ``{var: value}`` dict per solution."""
        payload = await self._post(sparql)
        bindings = payload.get("results", {}).get("bindings", [])
        return [{name: term.get("value") for name, term in row.items()} for row in bindings]

    async def ask(self, sparql: str) -> bool:
        """Execute a SPARQL ASK; return the boolean answer."""
        return bool((await self._post(sparql)).get("boolean", False))

    async def health_check(self) -> dict[str, Any]:
        """Probe reachability; never raises (contract requirement)."""
        try:
            has_data = await self.ask(GRAPH_HAS_TRIPLES)
            return {"ok": True, "backend": self.backend, "endpoint": self._endpoint, "has_data": has_data}
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "backend": self.backend,
                "endpoint": self._endpoint,
                "error": f"{type(exc).__name__}: {exc}",
            }
