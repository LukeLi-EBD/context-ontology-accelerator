"""The ontology transport must treat Oxigraph's cancelled-200 as an error.

``serve --timeout-s`` answers a cancelled query with HTTP 200, the payload cut
short and ``The SPARQL operation has been cancelled`` appended. Checking only the
status code would hand the engine a truncated result (or report a cancelled write
as applied).
"""

from __future__ import annotations

import pytest

from coa_local_providers import ontology_oxigraph as ox
from coa_ontology.stores.base import GraphQueryCancelled

pytestmark = pytest.mark.unit

CANCELLED_NOTICE = "The SPARQL operation has been cancelled"
_ROW = '{"head":{"vars":["a"]},"results":{"bindings":[{"a":{"type":"uri","value":"urn:x"}}]}}'


class _Response:
    status_code = 200

    def __init__(self, body: str) -> None:
        self.content = body.encode()
        self.text = body

    def json(self):
        import json

        return json.loads(self.content)


@pytest.fixture(autouse=True)
def _endpoint(monkeypatch):
    monkeypatch.setenv("COA_PROVIDER_ONTOLOGY_GRAPH", "oxigraph")
    monkeypatch.setenv("COA_ONTOLOGY_OXIGRAPH_URL", "http://oxigraph.test")
    monkeypatch.setenv("COA_ONTOLOGY_OXIGRAPH_TIMEOUT", "20")


def _respond(monkeypatch, body: str) -> None:
    monkeypatch.setattr(ox.httpx, "post", lambda *args, **kwargs: _Response(body))


class TestCancelledQuery:
    def test_a_truncated_body_raises_cancelled(self, monkeypatch):
        _respond(monkeypatch, _ROW[:-3] + CANCELLED_NOTICE)
        with pytest.raises(GraphQueryCancelled):
            ox.sparql_query("SELECT * WHERE { ?s ?p ?o }")

    def test_a_parseable_body_plus_the_notice_raises_cancelled(self, monkeypatch):
        # A cut after the last complete row parses; it must still not be returned.
        _respond(monkeypatch, _ROW + CANCELLED_NOTICE)
        with pytest.raises(GraphQueryCancelled):
            ox.sparql_query("SELECT * WHERE { ?s ?p ?o }")

    def test_a_normal_result_is_returned(self, monkeypatch):
        _respond(monkeypatch, _ROW)
        assert ox.sparql_query("SELECT * WHERE { ?s ?p ?o }")["results"]["bindings"]

    def test_a_result_that_merely_contains_the_sentence_is_returned(self, monkeypatch):
        body = (
            '{"head":{"vars":["a"]},"results":{"bindings":[{"a":{"type":"literal","value":"'
            + CANCELLED_NOTICE
            + '"}}]}}'
        )
        _respond(monkeypatch, body)
        assert ox.sparql_query("SELECT * WHERE { ?s ?p ?o }")["results"]["bindings"]


class TestCancelledUpdate:
    def test_a_cancelled_update_is_not_a_success(self, monkeypatch):
        _respond(monkeypatch, CANCELLED_NOTICE)
        with pytest.raises(GraphQueryCancelled):
            ox.sparql_update("INSERT DATA { <urn:s> <urn:p> <urn:o> }")

    def test_a_completed_update_returns(self, monkeypatch):
        _respond(monkeypatch, "")
        ox.sparql_update("INSERT DATA { <urn:s> <urn:p> <urn:o> }")


class TestDropUsesTheGuardedUpdate:
    def test_drop_graph_goes_through_sparql_update(self, monkeypatch):
        calls = []
        monkeypatch.setattr(ox.httpx, "post", lambda *a, **k: calls.append(1) or _Response(CANCELLED_NOTICE))
        with pytest.raises(GraphQueryCancelled):
            ox.drop_graph("urn:platform:test")
        assert calls
