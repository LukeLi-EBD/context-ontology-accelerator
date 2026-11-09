"""Synchronous SPARQL transport for the metric graph.

``MetricNeptuneClient`` generates SPARQL and parses Neptune's result envelope
(``{"results": {"bindings": [{"o": {"value": ..., "type": "uri"}}]}}``). The
term *type* is part of that contract: ``_parse_metric`` distinguishes an
untagged label from a language-tagged one, and ``resolve_class_uris`` rejects
non-URI bindings.

``coa_ports.GraphStorePort`` deliberately flattens terms to strings, so routing
the metric path through it would silently change both checks. This module keeps
the existing parser and swaps only the transport: an implementation returns
Neptune-shaped JSON, method for method. The provider is selected by
``COA_PROVIDER_METRIC_GRAPH`` in the composition root; nothing here constructs
a Neptune client.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SparqlTransport(Protocol):
    """One synchronous SPARQL endpoint, speaking Neptune's result shape."""

    def query(self, sparql: str) -> dict[str, Any]:
        """Run SELECT/ASK and return Neptune's JSON envelope."""
        ...

    def update(self, sparql: str) -> None:
        """Apply one SPARQL Update statement."""
        ...


__all__ = ["SparqlTransport"]
