# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the Oxigraph-backed :class:`OntologyLookup` shell."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

_GRAPH_BASE = "https://ontology-workbench.local"
_CLASS = "https://w3id.org/fsldm/core#Classification"


class _RecordingStore:
    """Minimal ``OxigraphHttpStore`` stand-in that records the ASK it receives."""

    def __init__(self, answer: bool = True) -> None:
        self.answer = answer
        self.queries: list[str] = []

    def ask(self, sparql: str) -> bool:
        self.queries.append(sparql)
        return self.answer


def _lookup(store: _RecordingStore):
    from coa_metrics.ontology_lookup_graph import GraphOntologyLookup

    return GraphOntologyLookup(store, graph_base=_GRAPH_BASE)


def test_valid_namespace_queries_only_its_own_graph():
    store = _RecordingStore(answer=True)

    assert _lookup(store).class_exists(_CLASS, "fsldm") is True

    assert len(store.queries) == 1
    assert f'STRSTARTS(STR(?g), "{_GRAPH_BASE}/fsldm/")' in store.queries[0]


@pytest.mark.parametrize(
    "namespace",
    ["", "other/tenant", "../other-tenant", "fsldm/../other", "fsldm*", "ns 1", "x" * 65],
)
def test_namespace_outside_the_graph_scope_is_rejected_before_querying(namespace: str):
    """``GRAPH ?g`` is invisible to the store whitelist, so the shell must bound it.

    Anything that is not a single path segment is refused before a query is
    built: the only way this shell can widen ``{graph_base}/{namespace}/`` is
    through the namespace it interpolates.
    """
    store = _RecordingStore(answer=True)

    assert _lookup(store).class_exists(_CLASS, namespace) is False
    assert store.queries == []
