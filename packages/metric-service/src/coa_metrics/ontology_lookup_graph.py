# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Ontology class-existence lookup over a local Oxigraph SPARQL endpoint.

Synchronous by contract (``OntologyLookup.class_exists`` is called from a
synchronous Lambda handler), so this uses ``platform_core``'s synchronous
``OxigraphHttpStore`` rather than the async ``OxigraphGraphClient`` used by
the COA ``GraphClient`` port.

The ASK query is byte-for-byte the shape ``NeptuneOntologyLookup`` issues
(``CLASSES``): an ``owl:Class`` triple inside a named graph whose IRI starts
with ``{graph_base}/{namespace}/``. Failure is fail-open, as on Neptune.
"""

from __future__ import annotations

import re

import structlog

from coa_metrics.lookups import OntologyLookup
from coa_metrics.neptune_client import OWL, RDF, _esc, _resolve_graph_base

logger = structlog.get_logger(__name__)

# Same defence-in-depth check as NeptuneOntologyLookup: the concept URI comes
# from the request body, so it may only carry characters legal in an IRI.
_SAFE_CONCEPT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:[A-Za-z0-9_.:/#\-]+$")


class GraphOntologyLookup(OntologyLookup):
    """``class_exists`` backed by a local Oxigraph triple store."""

    backend = "oxigraph"

    def __init__(self, store, graph_base: str | None = None) -> None:
        self._store = store
        self._graph_base = (graph_base or _resolve_graph_base()).rstrip("/")

    def class_exists(self, class_uri: str, namespace: str) -> bool:
        """ASK whether ``class_uri`` is an ``owl:Class`` in this namespace."""
        if not isinstance(class_uri, str) or not _SAFE_CONCEPT_RE.match(class_uri):
            logger.warning("ontology_concept_rejected", class_uri=class_uri, namespace=namespace)
            return False

        ns_prefix = f"{self._graph_base}/{namespace}/"
        query = (
            f"ASK {{ GRAPH ?g {{ <{class_uri}> <{RDF}type> <{OWL}Class> . }} "
            f'FILTER(STRSTARTS(STR(?g), "{_esc(ns_prefix)}")) }}'
        )
        try:
            return bool(self._store.ask(query))
        except Exception as exc:  # noqa: BLE001 - fail open, matching Neptune
            logger.warning(
                "ontology_lookup_failed",
                class_uri=class_uri,
                namespace=namespace,
                error=str(exc),
            )
            return False


__all__ = ["GraphOntologyLookup"]
