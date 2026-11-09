"""Oxigraph results are rendered back into Neptune's envelope."""

from __future__ import annotations

from typing import Any

import pytest
from coa_ports import PortError

from coa_local_providers.metric_graph import OxigraphSparqlTransport


class FakeStore:
    def __init__(self, result: dict[str, Any] | None = None) -> None:
        self.result = result or {}
        self.calls: list[str] = []
        self.updates: list[str] = []
        self.closed = False

    def query(self, sparql: str) -> dict[str, Any]:
        self.calls.append(sparql)
        return self.result

    def update(self, sparql: str) -> None:
        self.updates.append(sparql)

    def close(self) -> None:
        self.closed = True


def _select(*rows: dict[str, Any]) -> dict[str, Any]:
    variables = list(rows[0]["values"]) if rows else []
    return {"kind": "select", "variables": variables, "bindings": list(rows), "truncated": False}


def test_select_keeps_neptune_term_types() -> None:
    store = FakeStore(
        _select(
            {
                "values": {
                    "s": {"kind": "iri", "iri": "urn:coa:metric:demo:revenue"},
                    "label": {"kind": "literal", "value": "收入", "datatype": None, "lang": "zh"},
                    "amount": {
                        "kind": "literal",
                        "value": "1",
                        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                        "lang": None,
                    },
                }
            }
        )
    )

    result = OxigraphSparqlTransport(store).query("SELECT * WHERE {}")

    binding = result["results"]["bindings"][0]
    assert binding["s"] == {"type": "uri", "value": "urn:coa:metric:demo:revenue"}
    assert binding["label"] == {"type": "literal", "value": "收入", "xml:lang": "zh"}
    assert binding["amount"] == {
        "type": "typed-literal",
        "value": "1",
        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
    }
    assert result["head"]["vars"] == ["s", "label", "amount"]


def test_ask_returns_the_boolean_envelope() -> None:
    store = FakeStore({"kind": "ask", "variables": [], "bindings": [], "boolean": True, "truncated": False})

    assert OxigraphSparqlTransport(store).query("ASK {}") == {"boolean": True}


def test_truncated_select_fails_instead_of_returning_a_partial_list() -> None:
    store = FakeStore({"kind": "select", "variables": ["s"], "bindings": [], "truncated": True})

    with pytest.raises(PortError) as excinfo:
        OxigraphSparqlTransport(store).query("SELECT * WHERE {}")

    assert excinfo.value.provider_code == "E_METRIC_GRAPH_TRUNCATED"


def test_update_and_close_delegate() -> None:
    store = FakeStore()
    transport = OxigraphSparqlTransport(store)

    transport.update("INSERT DATA { GRAPH <urn:x> { <a> <b> <c> } }")
    transport.close()

    assert store.updates == ["INSERT DATA { GRAPH <urn:x> { <a> <b> <c> } }"]
    assert store.closed is True
