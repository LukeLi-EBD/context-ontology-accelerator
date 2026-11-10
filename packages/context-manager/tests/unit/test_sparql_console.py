# SPDX-License-Identifier: Apache-2.0

"""SPARQL console (P6 F72–F74) — the gates that must hold before a query runs."""

from __future__ import annotations

import asyncio

import pytest

from coa_serve.tier2.sparql import console
from coa_serve.tier2.sparql.console import (
    SparqlConsole,
    SparqlConsoleError,
    build_console_from_env,
)

pytestmark = pytest.mark.unit

_NS = "acme"
_G = "https://coa.local/graph/acme/data"
_OTHER = "https://coa.local/graph/other/data"


class _Backend:
    """A recording backend: it either answers or fails the way a provider would."""

    name = "fake"

    def __init__(self, *, graphs=(_G,), variables=("s",), rows=None, fail=None) -> None:
        self._graphs = list(graphs)
        self._variables = list(variables)
        self._rows = rows if rows is not None else [["<http://example.org/a>"]]
        self._fail = fail
        self.queries: list[str] = []

    async def list_graphs(self, namespace):
        return list(self._graphs)

    async def select(self, sparql):
        self.queries.append(sparql)
        if self._fail is not None:
            raise self._fail
        return list(self._variables), [list(r) for r in self._rows]

    async def ask(self, sparql):
        self.queries.append(sparql)
        if self._fail is not None:
            raise self._fail
        return True


def _run(backend, sparql, namespace=_NS):
    return asyncio.run(SparqlConsole(backend).run(namespace, sparql))


def _rejected(backend, sparql, code, status, namespace=_NS) -> SparqlConsoleError:
    with pytest.raises(SparqlConsoleError) as exc:
        _run(backend, sparql, namespace)
    assert exc.value.code == code
    assert exc.value.status == status
    return exc.value


class TestAdmitted:
    def test_a_select_returns_the_provider_variables_and_rows(self):
        backend = _Backend(variables=("s", "p"), rows=[["<a>", "<b>"]])
        result = _run(backend, "SELECT ?s ?p WHERE { ?s ?p ?o }")
        assert result.form == "SELECT"
        assert result.variables == ("s", "p")
        assert result.rows == (("<a>", "<b>"),)
        assert result.row_count == 1
        assert result.truncated is False
        assert result.graph_count == 1

    def test_the_executed_query_is_scoped_to_the_namespace_graphs(self):
        backend = _Backend()
        _run(backend, "SELECT ?s WHERE { ?s ?p ?o }")
        text = backend.queries[-1]
        assert f"FROM <{_G}>" in text
        assert f"FROM NAMED <{_G}>" in text

    def test_an_ask_returns_the_boolean(self):
        result = _run(_Backend(), "ASK { ?s ?p ?o }")
        assert result.form == "ASK"
        assert result.answer is True
        assert result.rows == ()


class TestStatementForm:
    @pytest.mark.parametrize(
        "query",
        [
            "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
            "DESCRIBE <http://example.org/a>",
        ],
    )
    def test_only_select_and_ask_are_admitted(self, query):
        _rejected(_Backend(), query, "E_SPARQL_STATEMENT_NOT_ALLOWED", 400)

    @pytest.mark.parametrize(
        "query",
        [
            "INSERT DATA { <http://a> <http://b> <http://c> }",
            "DELETE WHERE { ?s ?p ?o }",
            "DROP ALL",
        ],
    )
    def test_updates_are_rejected(self, query):
        _rejected(_Backend(), query, "E_SPARQL_SYNTAX", 400)


class TestForbiddenClauses:
    def test_from_is_rejected(self):
        _rejected(
            _Backend(),
            f"SELECT ?s FROM <{_OTHER}> WHERE {{ ?s ?p ?o }}",
            "E_SPARQL_DATASET_FORBIDDEN",
            400,
        )

    def test_service_is_rejected(self):
        _rejected(
            _Backend(),
            "SELECT ?s WHERE { SERVICE <http://evil/sparql> { ?s ?p ?o } }",
            "E_SPARQL_FEDERATED",
            400,
        )

    def test_load_is_rejected(self):
        _rejected(
            _Backend(),
            "LOAD <http://evil/data.ttl>",
            "E_SPARQL_LOAD_NOT_ALLOWED",
            400,
        )

    def test_a_graph_outside_the_namespace_is_rejected(self):
        _rejected(
            _Backend(),
            f"SELECT ?s WHERE {{ GRAPH <{_OTHER}> {{ ?s ?p ?o }} }}",
            "E_SPARQL_GRAPH_FORBIDDEN",
            400,
        )


class TestScope:
    def test_an_empty_namespace_scope_is_refused(self):
        _rejected(_Backend(graphs=()), "SELECT ?s WHERE { ?s ?p ?o }", "E_SPARQL_SCOPE_EMPTY", 503)

    def test_too_many_graphs_are_refused(self):
        graphs = [f"https://coa.local/graph/acme/g{i}" for i in range(console.MAX_GRAPHS + 1)]
        _rejected(_Backend(graphs=graphs), "SELECT ?s WHERE { ?s ?p ?o }", "E_SPARQL_SCOPE_TOO_LARGE", 503)


class TestBounds:
    def test_a_query_over_the_byte_cap_is_refused(self):
        _rejected(
            _Backend(),
            "SELECT ?s WHERE { ?s ?p ?o } #" + "x" * console.MAX_QUERY_BYTES,
            "E_SPARQL_TOO_LONG",
            400,
        )

    def test_an_empty_query_is_refused(self):
        _rejected(_Backend(), "   ", "E_SPARQL_EMPTY", 400)

    def test_a_bad_namespace_is_refused(self):
        _rejected(_Backend(), "SELECT ?s WHERE { ?s ?p ?o }", "E_SPARQL_BAD_NAMESPACE", 400, namespace="../etc")

    def test_a_timeout_is_reported_as_504(self, monkeypatch):
        monkeypatch.setattr(console, "TIMEOUT_S", 0.05)

        class _Slow(_Backend):
            async def select(self, sparql):
                await asyncio.sleep(1.0)
                return [], []

        _rejected(_Slow(), "SELECT ?s WHERE { ?s ?p ?o }", "E_SPARQL_TIMEOUT", 504)

    def test_extra_rows_mark_the_result_truncated(self):
        rows = [[f"<http://example.org/{i}>"] for i in range(console.MAX_ROWS + 1)]
        result = _run(_Backend(rows=rows), "SELECT ?s WHERE { ?s ?p ?o }")
        assert result.row_count == console.MAX_ROWS + 1
        assert result.returned_rows == console.MAX_ROWS
        assert result.truncated is True
        assert len(result.rows) == console.MAX_ROWS

    def test_exactly_the_cap_is_not_truncated(self):
        rows = [[f"<http://example.org/{i}>"] for i in range(console.MAX_ROWS)]
        result = _run(_Backend(rows=rows), "SELECT ?s WHERE { ?s ?p ?o }")
        assert result.truncated is False
        assert result.returned_rows == console.MAX_ROWS


class TestProviderErrors:
    def test_a_provider_4xx_keeps_its_status_code_and_body(self):
        failure = console._ProviderRejected(400, "HTTP_400", "Parse error at line 1")
        error = _rejected(_Backend(fail=failure), "SELECT ?s WHERE { ?s ?p ?o }", "E_SPARQL_PROVIDER_REJECTED", 400)
        assert error.provider_code == "HTTP_400"
        assert error.provider_message == "Parse error at line 1"

    def test_a_provider_5xx_maps_to_502(self):
        failure = console._ProviderRejected(503, "HTTP_503", "busy")
        _rejected(_Backend(fail=failure), "SELECT ?s WHERE { ?s ?p ?o }", "E_SPARQL_PROVIDER_ERROR", 502)

    def test_an_oversized_body_maps_to_413(self):
        _rejected(_Backend(fail=console._TooLarge()), "SELECT ?s WHERE { ?s ?p ?o }", "E_SPARQL_RESULT_TOO_LARGE", 413)


class TestBackendSelection:
    def test_no_provider_fails_explicitly(self, monkeypatch):
        monkeypatch.delenv("COA_SPARQL_BACKEND", raising=False)
        monkeypatch.delenv("COA_PROVIDER_GRAPH", raising=False)
        assert build_console_from_env() is None

    def test_an_unknown_provider_fails_explicitly(self, monkeypatch):
        monkeypatch.setenv("COA_SPARQL_BACKEND", "mystery")
        with pytest.raises(SparqlConsoleError) as exc:
            build_console_from_env()
        assert exc.value.code == "E_SPARQL_BACKEND_NOT_CONFIGURED"

    def test_oxigraph_without_a_url_fails_explicitly(self, monkeypatch):
        monkeypatch.setenv("COA_SPARQL_BACKEND", "oxigraph")
        monkeypatch.delenv("COA_GRAPH_OXIGRAPH_URL", raising=False)
        with pytest.raises(SparqlConsoleError) as exc:
            build_console_from_env()
        assert exc.value.code == "E_SPARQL_BACKEND_NOT_CONFIGURED"
