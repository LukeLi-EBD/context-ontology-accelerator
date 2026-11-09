"""Oxigraph implementation of the COA ``GraphClient`` contract.

Read-only by construction: SELECT/ASK against ``POST {endpoint}/query``.
"""

from __future__ import annotations

import httpx

from .sparql_http import SparqlHttpGraphClient


class OxigraphGraphClient(SparqlHttpGraphClient):
    """Local, read-only ``GraphClient`` backed by an Oxigraph SPARQL endpoint."""

    backend = "oxigraph"

    def __init__(
        self,
        endpoint: str,
        *,
        timeout_s: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base = endpoint.rstrip("/")
        super().__init__(
            self._base + "/query",
            endpoint=self._base,
            timeout_s=timeout_s,
            transport=transport,
        )
