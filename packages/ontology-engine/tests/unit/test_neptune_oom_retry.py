# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Neptune ``MemoryLimitExceededException`` handling and the kind-scoped search scan.

Under concurrent integ load the shared Neptune cluster answered
``/graph/search`` with HTTP 500 ``MemoryLimitExceededException`` (pipelines
2861430, 2861563, 2871155, 2871465). These tests pin the three parts of the fix:

* the transport retries an OOM (and only an OOM), then raises
  :class:`NeptuneMemoryLimitError` on exhaustion;
* the API maps that error to a retryable 503 instead of a bare 500;
* a ``kind``-filtered search/count no longer scans every quad in the cluster.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from urllib.parse import unquote_plus

import httpx
import pytest
from coa_ontology.main import app
from coa_ontology.stores import neptune_db_graph as ndb
from coa_ontology.stores.base import FilteredSearchTooLarge, GraphQueryCancelled, GraphScanTooLarge, SearchScopeTooLarge
from coa_ontology.stores.neptune_db_graph import NeptuneDBGraphStore, NeptuneMemoryLimitError
from fastapi.testclient import TestClient

NS = "test-ns"
_OOM_BODY = {
    "code": "MemoryLimitExceededException",
    "detailedMessage": "Operation terminated (out of memory)",
}
_EMPTY_RESULTS = {"head": {"vars": []}, "results": {"bindings": []}}

_real_client = httpx.Client


@pytest.fixture
def neptune(monkeypatch):
    """Route the store's httpx calls to a scripted handler; no signing, no sleeps.

    Yields a list the test fills with responses (one per request, in order) and
    reads back as the number of requests actually made.
    """
    responses: list[httpx.Response] = []
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return responses.pop(0)

    monkeypatch.setattr(ndb, "NDB_ENDPOINT", "https://fake:8182")
    monkeypatch.setattr(ndb, "_sign", lambda *a, **k: {})
    monkeypatch.setattr(ndb.httpx, "Client", lambda **kw: _real_client(transport=httpx.MockTransport(handler), **kw))
    with patch("coa_common.opensearch.retry.time.sleep"):
        yield responses, calls


@pytest.mark.unit
class TestOomRetry:
    def test_query_retries_oom_then_succeeds(self, neptune):
        responses, calls = neptune
        responses += [httpx.Response(500, json=_OOM_BODY), httpx.Response(200, json=_EMPTY_RESULTS)]
        assert ndb._sparql_query("SELECT * WHERE { ?s ?p ?o }") == _EMPTY_RESULTS
        assert len(calls) == 2

    def test_query_raises_memory_limit_error_on_exhaustion(self, neptune):
        responses, calls = neptune
        responses += [httpx.Response(500, json=_OOM_BODY)] * (ndb._NDB_MAX_RETRIES + 1)
        with pytest.raises(NeptuneMemoryLimitError) as exc:
            ndb._sparql_query("SELECT * WHERE { ?s ?p ?o }")
        # Still an HTTPStatusError, so existing ``except`` sites keep catching it.
        assert isinstance(exc.value, httpx.HTTPStatusError)
        assert len(calls) == ndb._NDB_MAX_RETRIES + 1

    def test_other_500_is_not_retried(self, neptune):
        responses, calls = neptune
        responses.append(httpx.Response(500, json={"code": "MalformedQueryException"}))
        with pytest.raises(httpx.HTTPStatusError) as exc:
            ndb._sparql_query("SELECT nonsense")
        assert not isinstance(exc.value, NeptuneMemoryLimitError)
        assert len(calls) == 1

    def test_non_json_error_body_is_not_retried(self, neptune):
        responses, calls = neptune
        responses.append(httpx.Response(502, text="Bad Gateway"))
        with pytest.raises(httpx.HTTPStatusError):
            ndb._sparql_query("SELECT * WHERE { ?s ?p ?o }")
        assert len(calls) == 1

    @pytest.mark.parametrize("body", [["not", "an", "object"], "oops", None])
    def test_non_object_json_error_body_raises_http_error(self, neptune, body):
        # Must surface as HTTPStatusError, not AttributeError — /graph/search maps
        # AttributeError to 501, which the integ test would silently skip.
        responses, calls = neptune
        responses.append(httpx.Response(500, json=body))
        with pytest.raises(httpx.HTTPStatusError) as exc:
            ndb._sparql_query("SELECT * WHERE { ?s ?p ?o }")
        assert not isinstance(exc.value, NeptuneMemoryLimitError)
        assert len(calls) == 1

    def test_update_retries_oom(self, neptune):
        responses, calls = neptune
        responses += [httpx.Response(500, json=_OOM_BODY), httpx.Response(200, json={})]
        ndb._sparql_update("DROP SILENT GRAPH <urn:g>")
        assert len(calls) == 2

    def test_gsp_post_retries_oom(self, neptune):
        responses, calls = neptune
        responses += [httpx.Response(500, json=_OOM_BODY), httpx.Response(200, json={})]
        assert ndb._gsp_post_turtle("urn:g", "<urn:s> <urn:p> <urn:o> .")["status"] == "ok"
        assert len(calls) == 2

    def test_gsp_get_retries_oom(self, neptune):
        responses, calls = neptune
        responses += [httpx.Response(500, json=_OOM_BODY), httpx.Response(200, text="# empty")]
        assert ndb._gsp_get_turtle("urn:g") == "# empty"
        assert len(calls) == 2


@pytest.mark.unit
def test_api_maps_memory_limit_error_to_503():
    graph = MagicMock()
    graph.search_entities.side_effect = NeptuneMemoryLimitError(
        "Neptune MemoryLimitExceededException (500)",
        request=httpx.Request("POST", "https://fake:8182/sparql"),
        response=httpx.Response(500, json=_OOM_BODY),
    )
    with patch("coa_ontology.catalog.routers.graph.build_stores", return_value=(graph, MagicMock())):
        resp = TestClient(app).get("/graph/search", params={"q": "*", "kind": "class", "namespace": NS})
    assert resp.status_code == 503


@pytest.mark.unit
class TestKindScopedScan:
    """A kind filter must not also carry the unbound ``GRAPH ?g { ?s ?_p ?_o }`` scan."""

    @staticmethod
    def _captured_queries(fn) -> list[str]:
        captured: list[str] = []

        def capture(q):
            captured.append(q)
            return _EMPTY_RESULTS

        with patch.object(ndb, "_sparql_query", side_effect=capture):
            fn()
        return captured

    def test_kind_search_and_count_use_type_pattern_only(self):
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        queries = self._captured_queries(
            lambda: (
                store.search_entities(query="*", namespace=NS, kind="class", limit=100),
                store.count_entities(query="*", namespace=NS, kind="class"),
            )
        )
        # Each call issues its pre-flight entity count, then the query itself.
        assert len(queries) == 4
        for q in queries:
            assert "?_p ?_o" not in q
            assert "STRSTARTS(STR(?g)" in q  # namespace scoping is unchanged
        for preflight in (queries[0], queries[2]):
            assert "VALUES ?type" in preflight
            assert "COUNT(DISTINCT ?s) AS ?n" in preflight
        for scan in (queries[1], queries[3]):
            assert "?s a ?requiredType" in scan

    def test_no_kind_keeps_full_subject_pattern(self):
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        queries = self._captured_queries(lambda: store.count_entities(query="pub", namespace=NS))
        # First query is the pre-flight quad budget check added for the
        # unfiltered path; the search itself still uses the full subject pattern.
        assert "COUNT(*) AS ?n" in queries[0]
        assert "?s ?_p ?_o" in queries[1]


def _quad_count_response(n: int) -> httpx.Response:
    return httpx.Response(
        200,
        json={"head": {"vars": ["n"]}, "results": {"bindings": [{"n": {"type": "literal", "value": str(n)}}]}},
    )


@pytest.mark.unit
class TestUnfilteredSearchBudget:
    """An unfiltered search is refused explicitly, never silently timed out."""

    def test_over_budget_refuses_before_scanning(self, neptune, monkeypatch):
        monkeypatch.setenv("COA_ONTOLOGY_GRAPH_SCOPE", "prefix")
        responses, calls = neptune
        over = ndb._MAX_UNFILTERED_SEARCH_QUADS + 1
        responses.append(_quad_count_response(over))
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        with pytest.raises(SearchScopeTooLarge) as excinfo:
            store.search_entities(query="Claim", namespace=NS, limit=20)
        assert excinfo.value.quads == over
        assert len(calls) == 1  # pre-flight COUNT only: the scan never ran

    def test_kind_scoped_search_does_not_measure_the_namespace(self, neptune, monkeypatch):
        monkeypatch.setenv("COA_ONTOLOGY_GRAPH_SCOPE", "prefix")
        responses, calls = neptune
        responses += [httpx.Response(200, json=_EMPTY_RESULTS)] * 2
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        assert store.search_entities(query="Claim", namespace=NS, kind="class") == []
        assert len(calls) == 2  # type-subject pre-flight, then the search
        preflight = unquote_plus(calls[0].content.decode())
        assert "VALUES ?type" in preflight
        assert "COUNT(DISTINCT ?s) AS ?n" in preflight
        # The namespace-wide quad count is not what bounds a kind search.
        assert "COUNT(*) AS ?n" not in preflight

    def test_api_maps_scope_too_large_to_422(self):
        graph = MagicMock()
        graph.search_entities.side_effect = SearchScopeTooLarge(121_130, ndb._MAX_UNFILTERED_SEARCH_QUADS, NS)
        with patch("coa_ontology.catalog.routers.graph.build_stores", return_value=(graph, MagicMock())):
            resp = TestClient(app).get("/graph/search", params={"q": "Claim", "namespace": NS})
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "121130" in detail
        assert "kind=class|object-property|datatype-property" in detail


def _graph_list_response(*graphs: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "head": {"vars": ["g"]},
            "results": {
                "bindings": [{"g": {"type": "uri", "value": g}} for g in graphs],
            },
        },
    )


@pytest.mark.unit
class TestGraphReadBudgets:
    """Canvas, path and kind search are bounded before they scan, not after.

    All three used to run until the transport gave up: the caller saw a 504 at
    28 s while the store kept burning CPU. Each now answers 422 from a cheap
    aggregate pre-check over the same 100k-quad set that produced the 504.
    """

    def test_kind_search_refuses_over_the_entity_budget(self, neptune, monkeypatch):
        monkeypatch.setenv("COA_ONTOLOGY_GRAPH_SCOPE", "prefix")
        responses, calls = neptune
        over = ndb._MAX_FILTERED_SEARCH_ENTITIES + 1
        responses.append(_quad_count_response(over))
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        with pytest.raises(FilteredSearchTooLarge) as excinfo:
            store.search_entities(query="*", namespace=NS, kind="class", limit=50)
        assert excinfo.value.entities == over
        assert len(calls) == 1  # pre-flight count only: the label scan never ran

    def test_canvas_refuses_over_the_quad_budget(self, neptune, monkeypatch):
        monkeypatch.setenv("COA_ONTOLOGY_GRAPH_SCOPE", "prefix")
        responses, calls = neptune
        responses += [_graph_list_response("urn:coa:g:1"), _quad_count_response(ndb._MAX_CANVAS_QUADS + 1)]
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        with pytest.raises(GraphScanTooLarge) as excinfo:
            store.get_canvas_subgraph(namespace=NS, limit=50)
        assert excinfo.value.limit == ndb._MAX_CANVAS_QUADS
        assert len(calls) == 2  # graph enumeration + quad count

    def test_path_refuses_over_the_quad_budget(self, neptune, monkeypatch):
        monkeypatch.setenv("COA_ONTOLOGY_GRAPH_SCOPE", "prefix")
        responses, calls = neptune
        responses += [_graph_list_response("urn:coa:g:1"), _quad_count_response(ndb._MAX_PATH_QUADS + 1)]
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        with pytest.raises(GraphScanTooLarge) as excinfo:
            store.find_graph_path(namespace=NS, start="urn:coa:a", end="urn:coa:b", max_hops=2)
        assert excinfo.value.limit == ndb._MAX_PATH_QUADS
        assert len(calls) == 2

    def test_statement_page_is_totally_ordered(self):
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        captured: list[str] = []

        def respond(q: str) -> dict:
            captured.append(q)
            if "SELECT DISTINCT ?g" in q:
                return {"results": {"bindings": [{"g": {"value": "urn:coa:g:1"}}]}}
            return {"results": {"bindings": []}}

        with patch.object(ndb, "_sparql_query", side_effect=respond):
            store.list_statements(namespace=NS, limit=10)
        # Paging without a total order can repeat one quad and skip another.
        assert any("ORDER BY ?s ?p ?o ?g" in q for q in captured)

    def test_statement_page_refuses_over_the_sort_budget(self, neptune, monkeypatch):
        monkeypatch.setenv("COA_ONTOLOGY_GRAPH_SCOPE", "prefix")
        responses, calls = neptune
        responses += [
            _graph_list_response("urn:coa:g:1"),
            _quad_count_response(ndb._MAX_STATEMENT_PAGE_QUADS + 1),
        ]
        store = NeptuneDBGraphStore(endpoint="https://fake:8182", namespace=NS)
        with pytest.raises(GraphScanTooLarge) as excinfo:
            store.list_statements(namespace=NS, limit=10)
        assert excinfo.value.limit == ndb._MAX_STATEMENT_PAGE_QUADS
        assert len(calls) == 2  # graph enumeration + match count, no sort

    def test_cancelled_search_maps_to_504(self):
        graph = MagicMock()
        graph.search_entities.side_effect = GraphQueryCancelled("store cancelled the query")
        with patch("coa_ontology.catalog.routers.graph.build_stores", return_value=(graph, MagicMock())):
            resp = TestClient(app).get("/graph/search", params={"q": "Claim", "namespace": NS})
        assert resp.status_code == 504
        assert "cancelled" in resp.json()["detail"]
