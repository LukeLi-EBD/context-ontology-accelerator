"""Tests for the ``GraphStorePort`` ACL shell.

The shape cases use a stand-in inner object. One live case runs when
``COA_TEST_OXIGRAPH_URL`` points at a real Oxigraph (no mocks there); without
it that case skips rather than pretending to pass.
"""

from __future__ import annotations

import os
import uuid

import pytest

from coa_local_providers.shells import GraphStoreShell
from coa_ports import GraphQueryResult, GraphStorePort, PortError, PortErrorCode

PROBE_GRAPH = "urn:platform:coa:selfcheck:graph-shell"


class _Minimal:
    """Shape stand-in for the isinstance/constructor checks only."""

    def query(self, sparql: str) -> dict:
        return {"kind": "select", "variables": [], "bindings": []}

    def ask(self, sparql: str) -> bool:
        return True

    def update(self, sparql: str) -> None:
        return None

    def clear_graph(self, graph_uri: str) -> None:
        return None


class _Envelope:
    def query(self, sparql: str) -> dict:
        return {
            "kind": "select",
            "variables": ["s", "label"],
            "bindings": [
                {"values": {"s": {"kind": "iri", "iri": "urn:coa:x"}, "label": {"kind": "literal", "value": "X"}}}
            ],
        }

    def ask(self, sparql: str) -> bool:
        return False

    def update(self, sparql: str) -> None:
        return None

    def clear_graph(self, graph_uri: str) -> None:
        return None


def test_shell_is_a_graph_store_port() -> None:
    assert isinstance(GraphStoreShell(_Minimal()), GraphStorePort)


def test_constructor_rejects_an_object_missing_a_method() -> None:
    class NoClear:
        def query(self, *a): ...
        def ask(self, *a): ...
        def update(self, *a): ...

    with pytest.raises(TypeError):
        GraphStoreShell(NoClear())


def test_query_flattens_platform_bindings() -> None:
    result = GraphStoreShell(_Envelope()).query("SELECT ?s ?label WHERE {}")
    assert isinstance(result, GraphQueryResult)
    assert result.kind == "select"
    assert result.rows == ({"s": "urn:coa:x", "label": "X"},)


def test_unexpected_failure_becomes_internal() -> None:
    class Broken(_Minimal):
        def update(self, sparql: str) -> None:
            raise RuntimeError("boom")

    with pytest.raises(PortError) as excinfo:
        GraphStoreShell(Broken()).update("INSERT DATA {}")
    assert excinfo.value.code is PortErrorCode.INTERNAL
    assert excinfo.value.provider == "oxigraph"


@pytest.fixture()
def live_shell():
    endpoint = os.environ.get("COA_TEST_OXIGRAPH_URL", "")
    if not endpoint:
        pytest.skip("COA_TEST_OXIGRAPH_URL 未设置（真实调用测试需要本地 Oxigraph）")
    from platform_core.adapters.graph_oxigraph import OxigraphHttpStore

    store = OxigraphHttpStore(endpoint, timeout_ms=5000)
    try:
        store.ask("ASK {}")
    except Exception as exc:  # noqa: BLE001 - unreachable means "skip"
        pytest.skip(f"Oxigraph 不可达: {type(exc).__name__}")
    shell = GraphStoreShell(store)
    yield shell
    store.close()


def test_live_write_read_clear_and_probe(live_shell) -> None:
    marker = uuid.uuid4().hex
    subject = "urn:platform:coa:selfcheck:subject"
    try:
        live_shell.update(
            f'INSERT DATA {{ GRAPH <{PROBE_GRAPH}> {{ <{subject}> <urn:platform:coa:selfcheck:predicate> "{marker}" }} }}'
        )
        rows = live_shell.query(
            f"SELECT ?o WHERE {{ GRAPH <{PROBE_GRAPH}> {{ <{subject}> ?p ?o }} }}"
        )
        assert rows.kind == "select"
        assert [row["o"] for row in rows.rows] == [marker]
        assert live_shell.ask(f"ASK {{ GRAPH <{PROBE_GRAPH}> {{ ?s ?p ?o }} }}") is True
    finally:
        live_shell.clear_graph(PROBE_GRAPH)
    snapshot = live_shell.probe()
    assert snapshot["status"] == "ok"
    assert snapshot["provider"] == "oxigraph"
