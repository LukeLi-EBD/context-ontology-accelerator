"""SPARQL transports for the metric graph, in Neptune's result shape.

``MetricNeptuneClient`` (metric-service) generates SPARQL and parses Neptune's
envelope ``{"results": {"bindings": [{"o": {"value": ..., "type": ...}}]}}``.
The term type is load-bearing: ``_parse_metric`` separates plain literals from
language-tagged ones and ``resolve_class_uris`` rejects non-URI bindings.

Two implementations of ``coa_metrics.graph_transport.SparqlTransport`` live
here:

* ``neptune`` — the historical SigV4 HTTP transport, unchanged, reached through
  metric-service's own module functions.
* ``oxigraph`` — platform_core's synchronous Oxigraph adapter, whose typed term
  shape is converted back to Neptune's JSON.

The Oxigraph adapter only accepts graphs under an allow-list; the caller passes
the metric graph base so ``{base}/{namespace}/{ontology_id}`` is permitted.
A truncated SELECT raises instead of returning a partial result: Neptune never
truncates, and a short list here would silently drop metrics.
"""

from __future__ import annotations

from typing import Any

from coa_ports import PortError, PortErrorCode


def _neptune_term(term: dict[str, Any]) -> dict[str, Any]:
    """Turn one platform term into Neptune's ``{"value", "type", ...}``."""
    kind = term.get("kind")
    if kind == "iri":
        return {"type": "uri", "value": term.get("iri") or ""}
    if kind == "bnode":
        return {"type": "bnode", "value": term.get("label") or ""}
    out: dict[str, Any] = {"type": "literal", "value": term.get("value") or ""}
    datatype = term.get("datatype")
    if datatype:
        out["type"] = "typed-literal"
        out["datatype"] = datatype
    lang = term.get("lang")
    if lang:
        out["xml:lang"] = lang
    return out


class OxigraphSparqlTransport:
    """``SparqlTransport`` over platform_core's ``OxigraphHttpStore``."""

    backend = "oxigraph"

    def __init__(self, store: Any, *, name: str = "oxigraph") -> None:
        self._store = store
        self._name = name

    def query(self, sparql: str) -> dict[str, Any]:
        result = self._store.query(sparql)
        if result.get("kind") == "ask":
            return {"boolean": bool(result.get("boolean"))}
        if result.get("truncated"):
            raise PortError(
                PortErrorCode.INTERNAL,
                "metric graph query was truncated; raise the row limit",
                provider=self._name,
                provider_code="E_METRIC_GRAPH_TRUNCATED",
                details={"variables": list(result.get("variables", []))},
            )
        bindings = [
            {name: _neptune_term(term) for name, term in row.get("values", {}).items()}
            for row in result.get("bindings", [])
        ]
        return {
            "head": {"vars": list(result.get("variables", []))},
            "results": {"bindings": bindings},
        }

    def update(self, sparql: str) -> None:
        self._store.update(sparql)

    def close(self) -> None:
        self._store.close()


class NeptuneSparqlTransport:
    """The existing SigV4 Neptune transport, behind the same seam.

    Imported lazily: local-providers already depends on coa-metrics, but the
    transport must not be built until it is selected.
    """

    backend = "neptune"

    def query(self, sparql: str) -> dict[str, Any]:
        from coa_metrics.neptune_client import _sparql_query

        return _sparql_query(sparql)

    def update(self, sparql: str) -> None:
        from coa_metrics.neptune_client import _sparql_update

        _sparql_update(sparql)


def oxigraph_transport(
    endpoint: str,
    *,
    graph_base: str,
    timeout_ms: int = 30000,
    max_rows: int = 10000,
) -> OxigraphSparqlTransport:
    """Build an ``OxigraphSparqlTransport`` that allows the metric graph base."""
    from platform_core.adapters.graph_oxigraph import OxigraphHttpStore

    prefix = graph_base.rstrip("/") + "/"
    store = OxigraphHttpStore(
        endpoint,
        timeout_ms=timeout_ms,
        max_rows=max_rows,
        allowed_graph_prefixes=(prefix,),
    )
    return OxigraphSparqlTransport(store)
