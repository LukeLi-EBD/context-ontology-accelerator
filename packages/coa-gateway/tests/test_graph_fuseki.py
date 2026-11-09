"""Fuseki adapter: endpoint shaping and SPARQL 1.1 result handling (no service)."""

from __future__ import annotations

import unittest

import httpx

from coa_gateway.graph_fuseki import FusekiGraphClient


class FusekiGraphClientTest(unittest.IsolatedAsyncioTestCase):
    def test_endpoint_forms(self) -> None:
        self.assertEqual(
            FusekiGraphClient("http://fuseki:3030")._query_url,
            "http://fuseki:3030/ds/sparql",
        )
        self.assertEqual(
            FusekiGraphClient("http://fuseki:3030/ds/sparql")._query_url,
            "http://fuseki:3030/ds/sparql",
        )

    async def test_query_posts_form_and_flattens(self) -> None:
        seen: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["method"] = request.method
            seen["accept"] = request.headers.get("accept")
            seen["body"] = request.content.decode("utf-8")
            return httpx.Response(
                200,
                json={
                    "head": {"vars": ["s", "label"]},
                    "results": {"bindings": [{"s": {"type": "uri", "value": "urn:a"}, "label": {"type": "literal", "value": "A"}}]},
                },
            )

        client = FusekiGraphClient("http://fuseki:3030", transport=httpx.MockTransport(handler))
        rows = await client.query("SELECT ?s ?label WHERE { ?s ?p ?label }")

        self.assertEqual(rows, [{"s": "urn:a", "label": "A"}])
        self.assertEqual(seen["url"], "http://fuseki:3030/ds/sparql")
        self.assertEqual(seen["method"], "POST")
        self.assertEqual(seen["accept"], "application/sparql-results+json")
        self.assertIn("query=", str(seen["body"]))

    async def test_ask_returns_boolean(self) -> None:
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"boolean": True}))
        self.assertTrue(await FusekiGraphClient("http://fuseki:3030", transport=transport).ask("ASK {}"))

    async def test_health_check_never_raises(self) -> None:
        def boom(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=request)

        health = await FusekiGraphClient(
            "http://127.0.0.1:1", transport=httpx.MockTransport(boom)
        ).health_check()
        self.assertFalse(health["ok"])
        self.assertEqual(health["backend"], "jena-fuseki")
        self.assertIn("ConnectError", health["error"])


if __name__ == "__main__":
    unittest.main()
