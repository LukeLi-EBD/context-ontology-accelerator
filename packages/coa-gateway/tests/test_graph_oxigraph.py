"""Unit tests for the Oxigraph GraphClient adapter (no live service needed)."""

from __future__ import annotations

import unittest

import httpx

from coa_gateway.gateway import LocalGateway
from coa_gateway.graph_oxigraph import OxigraphGraphClient
from coa_gateway.sparql_http import SparqlOperationCancelled


def _results(vars_: list[str], rows: list[dict[str, str]]) -> httpx.Response:
    bindings = [{k: {"type": "uri", "value": v} for k, v in row.items()} for row in rows]
    return httpx.Response(200, json={"head": {"vars": vars_}, "results": {"bindings": bindings}})


class OxigraphGraphClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_query_flattens_bindings(self) -> None:
        transport = httpx.MockTransport(
            lambda request: _results(["s", "p", "o"], [{"s": "urn:a", "p": "urn:b", "o": "urn:c"}])
        )
        client = OxigraphGraphClient("http://oxigraph:7878", transport=transport)
        self.assertEqual(
            await client.query("SELECT ?s ?p ?o WHERE { ?s ?p ?o }"),
            [{"s": "urn:a", "p": "urn:b", "o": "urn:c"}],
        )

    async def test_ask_returns_boolean(self) -> None:
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"boolean": True}))
        self.assertTrue(await OxigraphGraphClient("http://oxigraph:7878", transport=transport).ask("ASK {}"))

    async def test_health_check_never_raises(self) -> None:
        def boom(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=request)

        health = await OxigraphGraphClient(
            "http://127.0.0.1:1", transport=httpx.MockTransport(boom)
        ).health_check()
        self.assertFalse(health["ok"])
        self.assertIn("ConnectError", health["error"])

    async def test_gateway_declares_only_graph(self) -> None:
        gateway = LocalGateway(OxigraphGraphClient("http://oxigraph:7878"))
        self.assertEqual(
            gateway.capabilities(),
            {
                "graph": True,
                "vector": False,
                "embedding": False,
                "llm": False,
                "query_executor": False,
                "source_catalog": False,
                "conversation": False,
                "memory": False,
                "object_store": False,
                "metadata": False,
            },
        )

    async def test_a_cancelled_query_is_an_error_not_a_partial_result(self) -> None:
        # Oxigraph answers a query it cancelled at its own deadline with 200 and a
        # truncated body followed by this notice; a status-code caller would treat
        # it as a complete answer.
        body = (
            '{"head":{"vars":["s","p","o"]},"results":{"bindings":[{"s":{"type":"uri","value":"urn:a"}}]}}'
            "The SPARQL operation has been cancelled"
        )
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body))
        client = OxigraphGraphClient("http://oxigraph:7878", transport=transport)
        with self.assertRaises(SparqlOperationCancelled):
            await client.query("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")

    async def test_a_cancelled_ask_does_not_read_as_false(self) -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, text='{"boolean":true}The SPARQL operation has been cancelled')
        )
        client = OxigraphGraphClient("http://oxigraph:7878", transport=transport)
        with self.assertRaises(SparqlOperationCancelled):
            await client.ask("ASK { ?s ?p ?o }")

    async def test_a_cancelled_health_check_reports_unhealthy(self) -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, text='{"boolean":true}The SPARQL operation has been cancelled')
        )
        health = await OxigraphGraphClient("http://oxigraph:7878", transport=transport).health_check()
        self.assertFalse(health["ok"])
        self.assertIn("cancelled", health["error"])


class CancelledQueryMappingTest(unittest.TestCase):
    def test_a_cancelled_query_is_a_504_not_a_success(self) -> None:
        from coa_gateway.http_api import _http_error

        self.assertEqual(_http_error(SparqlOperationCancelled("deadline")).status_code, 504)


if __name__ == "__main__":
    unittest.main()
