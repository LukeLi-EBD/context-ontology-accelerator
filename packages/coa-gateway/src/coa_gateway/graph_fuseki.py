"""Apache Jena Fuseki implementation of the COA ``GraphClient`` contract.

Fuseki exposes SPARQL 1.1 Query at ``{server}/{dataset}/sparql`` and accepts the
same ``query=`` form body as Oxigraph, so it reuses the shared transport.
"""

from __future__ import annotations

import httpx

from .sparql_http import SparqlHttpGraphClient


class FusekiGraphClient(SparqlHttpGraphClient):
    """Local, read-only ``GraphClient`` backed by a Jena Fuseki dataset."""

    backend = "jena-fuseki"

    def __init__(
        self,
        endpoint: str,
        *,
        dataset: str = "ds",
        timeout_s: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        base = endpoint.rstrip("/")
        # Accept either the server root or the dataset's query endpoint.
        query_url = base if base.endswith("/sparql") else f"{base}/{dataset.strip('/')}/sparql"
        super().__init__(query_url, endpoint=query_url, timeout_s=timeout_s, transport=transport)
