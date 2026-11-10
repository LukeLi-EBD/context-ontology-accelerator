# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Ontology graph transport provider: Oxigraph (local) / Neptune (AWS).

``coa_ontology.stores.neptune_db_graph`` speaks SPARQL 1.1 over Neptune DB,
but every call goes through four module-level functions:

    _sparql_query / _sparql_update / _gsp_post_turtle / _gsp_get_turtle

The local deployment reuses the Oxigraph instance that also backs the metric
graph (``COA_GRAPH_OXIGRAPH_URL``) instead of standing up a second graph
store. The transport is swapped at process start, so no call site changes and
no "local branch" is compiled into the engine.

Configuration (no default provider — startup fails closed):

    COA_PROVIDER_ONTOLOGY_GRAPH   oxigraph | neptune   (required)
    COA_ONTOLOGY_OXIGRAPH_URL     base URL for ``oxigraph`` (required for it)
    COA_ONTOLOGY_OXIGRAPH_TIMEOUT request timeout in seconds (default 30)

The client timeout only stops *waiting*; Oxigraph keeps evaluating the query
after the socket closes (measured: ~1 core held for as long as the query runs).
The container must therefore also be started with ``serve --timeout-s N``: that
is the server-side deadline, and it is the only mechanism that actually stops a
runaway query. It reports cancellation as a truncated 200 (not an HTTP error),
which :func:`sparql_query` turns into ``GraphQueryCancelled``.

``neptune`` leaves the engine untouched: it keeps its SigV4-signed AWS path
and still requires ``NDB_ENDPOINT`` from the deployment.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import quote

import httpx

_PROVIDERS = ("oxigraph", "neptune")

# Oxigraph appends this notice to the response body when ``--timeout-s`` fires.
# The response is still HTTP 200 and the JSON is truncated mid-stream, so it has
# to be recognised before the body is parsed.
_CANCELLED_NOTICE = "The SPARQL operation has been cancelled"


def _provider() -> str:
    raw = os.environ.get("COA_PROVIDER_ONTOLOGY_GRAPH", "").strip().lower()
    if not raw:
        raise RuntimeError(
            "COA_PROVIDER_ONTOLOGY_GRAPH is required (oxigraph|neptune); refusing to start "
            "without an explicitly selected ontology graph transport"
        )
    if raw not in _PROVIDERS:
        raise RuntimeError(f"Unknown COA_PROVIDER_ONTOLOGY_GRAPH={raw!r}; expected one of {_PROVIDERS}")
    return raw


def _base_url() -> str:
    url = os.environ.get("COA_ONTOLOGY_OXIGRAPH_URL", "").strip().rstrip("/")
    if not url:
        raise RuntimeError(
            "COA_ONTOLOGY_OXIGRAPH_URL is required when COA_PROVIDER_ONTOLOGY_GRAPH=oxigraph"
        )
    return url


def _timeout() -> float:
    return float(os.environ.get("COA_ONTOLOGY_OXIGRAPH_TIMEOUT", "30"))


def _fail(op: str, r: httpx.Response) -> None:
    snippet = r.text[:800].replace("\n", " ")
    raise RuntimeError(f"oxigraph {op} failed ({r.status_code}): {snippet}")


def sparql_query(query: str) -> dict[str, Any]:
    """SPARQL SELECT/ASK → SPARQL 1.1 JSON results (same shape Neptune returns)."""
    url = f"{_base_url()}/query"
    r = httpx.post(
        url,
        content=query.encode("utf-8"),
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
        timeout=_timeout(),
    )
    if r.status_code >= 400:
        _fail("query", r)
    try:
        return r.json()
    except json.JSONDecodeError:
        if _CANCELLED_NOTICE in r.text:
            from coa_ontology.stores.base import GraphQueryCancelled

            raise GraphQueryCancelled(
                f"oxigraph cancelled the query at its {_timeout()}s server limit; it is no longer running"
            ) from None
        raise


def sparql_update(update: str) -> None:
    url = f"{_base_url()}/update"
    r = httpx.post(
        url,
        content=update.encode("utf-8"),
        headers={"Content-Type": "application/sparql-update"},
        timeout=_timeout(),
    )
    if r.status_code >= 400:
        _fail("update", r)


def gsp_post_turtle(graph_uri: str, turtle: str) -> dict[str, Any]:
    """Append Turtle to one named graph (Graph Store Protocol POST)."""
    url = f"{_base_url()}/store?graph={quote(graph_uri, safe='')}"
    body = turtle.encode("utf-8")
    r = httpx.post(url, content=body, headers={"Content-Type": "text/turtle"}, timeout=_timeout())
    if r.status_code >= 400:
        _fail("gsp post", r)
    return {"graph_uri": graph_uri, "bytes_loaded": len(body), "status": "ok"}


def gsp_get_turtle(graph_uri: str) -> str | None:
    """Read one named graph as Turtle; ``None`` when the graph does not exist."""
    url = f"{_base_url()}/store?graph={quote(graph_uri, safe='')}"
    r = httpx.get(url, headers={"Accept": "text/turtle"}, timeout=_timeout())
    if r.status_code in (404, 410):
        return None
    if r.status_code >= 400:
        _fail("gsp get", r)
    return r.text


def replace_graph_turtle(graph_uri: str, turtle: str) -> dict[str, Any]:
    """Replace a named graph's contents (GSP PUT), for idempotent seeding."""
    url = f"{_base_url()}/store?graph={quote(graph_uri, safe='')}"
    body = turtle.encode("utf-8")
    r = httpx.put(url, content=body, headers={"Content-Type": "text/turtle"}, timeout=_timeout())
    if r.status_code >= 400:
        _fail("gsp put", r)
    return {"graph_uri": graph_uri, "bytes_loaded": len(body), "status": "ok"}


def drop_graph(graph_uri: str) -> None:
    sparql_update(f"DROP SILENT GRAPH <{graph_uri}>")


def install_ontology_graph_transport() -> str:
    """Patch the ontology engine's graph transport; returns the selected provider.

    Must run before the first graph request (the FastAPI app builds its stores
    at import time, but the module-level transport is looked up per call).
    """
    provider = _provider()
    if provider == "neptune":
        return provider

    # Validate the endpoint key before touching the engine so a missing URL
    # fails at startup rather than on the first request.
    _base_url()

    from coa_ontology.stores import neptune_db_graph as ndb

    ndb._sparql_query = sparql_query  # type: ignore[assignment]
    ndb._sparql_update = sparql_update  # type: ignore[assignment]
    ndb._gsp_post_turtle = gsp_post_turtle  # type: ignore[assignment]
    ndb._gsp_get_turtle = gsp_get_turtle  # type: ignore[assignment]
    return provider
