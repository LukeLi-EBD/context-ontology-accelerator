# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""FindLinks store semantics: hop ceiling, direction and the empty answer.

These run against a fake SPARQL evaluator so the BFS itself is exercised
(frontier per hop, dedupe, caps) without an Oxigraph endpoint. The live
3-hop ceiling is additionally verified against a real store in the P15
acceptance run; this file pins the algorithm.
"""
from __future__ import annotations

import re

import pytest

import coa_ontology.stores.neptune_db_graph as ndb

NAMESPACE = "ns-p15"
GRAPH = "https://coa.local/graph/ns-p15/onto"
P = "https://example.org/p/next"

# A → B → C → D → E: four hops out, so a 3-hop expansion must stop at D.
CHAIN = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")]


def _iri(name: str) -> str:
    return f"https://example.org/onto#{name}"


TRIPLES = [(_iri(s), P, _iri(o)) for s, o in CHAIN]


def _fake_sparql(query: str) -> dict:
    """Evaluate only the shape find_links emits: VALUES ?s / VALUES ?o + GRAPH."""
    if "VALUES ?s" in query:
        marker, outgoing = "VALUES ?s", True
    elif "VALUES ?o" in query:
        marker, outgoing = "VALUES ?o", False
    else:  # pragma: no cover - find_links never sends anything else
        raise AssertionError(f"unexpected query: {query}")

    frontier_block = query.split(marker, 1)[1].split("}", 1)[0]
    frontier = set(re.findall(r"<([^>]+)>", frontier_block))
    bindings = []
    for s, p, o in TRIPLES:
        if (s in frontier) if outgoing else (o in frontier):
            bindings.append(
                {
                    "s": {"value": s},
                    "p": {"value": p},
                    "o": {"value": o},
                    "g": {"value": GRAPH},
                }
            )
    return {"results": {"bindings": bindings}}


@pytest.fixture
def store(monkeypatch):
    monkeypatch.setattr(ndb, "_namespace_graphs", lambda scope: [GRAPH])
    monkeypatch.setattr(ndb, "_sparql_query", _fake_sparql)
    # Label lookups are out of scope here; nodes keep their IRI and no label.
    monkeypatch.setattr(ndb.NeptuneDBGraphStore, "_path_nodes", lambda self, ns, uris: {})
    return ndb.NeptuneDBGraphStore(endpoint="http://localhost:0", namespace=NAMESPACE)


def test_hops_never_exceed_three(store):
    result = store.find_links(NAMESPACE, uri=_iri("A"), direction="outgoing", max_hops=3)

    assert [(n["uri"], n["hops"]) for n in result["nodes"]] == [
        (_iri("B"), 1),
        (_iri("C"), 2),
        (_iri("D"), 3),
    ]
    # The fourth hop (E) must not appear, neither as a node nor as an edge.
    assert all(n["uri"] != _iri("E") for n in result["nodes"])
    assert all(e["target"] != _iri("E") for e in result["edges"])
    assert len(result["edges"]) == 3
    assert result["truncated"] is False


def test_max_hops_caps_shorter(store):
    result = store.find_links(NAMESPACE, uri=_iri("A"), direction="outgoing", max_hops=2)

    assert [n["uri"] for n in result["nodes"]] == [_iri("B"), _iri("C")]
    assert len(result["edges"]) == 2


def test_incoming_direction_walks_backwards(store):
    result = store.find_links(NAMESPACE, uri=_iri("D"), direction="incoming", max_hops=3)

    assert [(n["uri"], n["hops"]) for n in result["nodes"]] == [
        (_iri("C"), 1),
        (_iri("B"), 2),
        (_iri("A"), 3),
    ]
    assert all(e["direction"] == "incoming" for e in result["edges"])


def test_empty_neighbourhood_is_empty_not_error(store):
    result = store.find_links(NAMESPACE, uri=_iri("Unknown"), direction="both", max_hops=3)

    assert result == {"nodes": [], "edges": [], "truncated": False}


def test_limit_truncates_and_says_so(store):
    result = store.find_links(NAMESPACE, uri=_iri("A"), direction="outgoing", max_hops=3, limit=1)

    assert len(result["edges"]) == 1
    assert result["truncated"] is True


def test_meta_predicates_are_not_links(store, monkeypatch):
    rdfs_type = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    monkeypatch.setattr(
        ndb,
        "_sparql_query",
        lambda q: {
            "results": {
                "bindings": [
                    {
                        "s": {"value": _iri("A")},
                        "p": {"value": rdfs_type},
                        "o": {"value": _iri("Class")},
                        "g": {"value": GRAPH},
                    }
                ]
            }
        },
    )

    result = store.find_links(NAMESPACE, uri=_iri("A"), direction="outgoing", max_hops=1)

    assert result == {"nodes": [], "edges": [], "truncated": False}
