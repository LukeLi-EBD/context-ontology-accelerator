"""Prove the COA DataLayerService.GraphTraverse path reaches the local graph.

Asks the acceptance Oxigraph for a starting IRI, then calls the COA-named route
``POST /namespaces/{namespaceId}/graph/traverse`` over an in-process ASGI
transport (no port) and checks the Smithy output fields: entities /
relationships / trace.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid

import httpx

from coa_gateway.http_api import create_app
from coa_gateway.registry import build_gateway
from coa_gateway.settings import ProviderSettings

NAMESPACE = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))


async def main() -> None:
    mapping = {
        "COA_PROVIDER_GRAPH": "oxigraph",
        "COA_GRAPH_OXIGRAPH_URL": os.environ.get("COA_GRAPH_OXIGRAPH_URL", "http://oxigraph:7878"),
        "COA_PROVIDER_VECTOR": "none",
        "COA_PROVIDER_LLM": "none",
        "COA_PROVIDER_QUERY_EXECUTOR": "none",
        "COA_PROVIDER_SOURCE_CATALOG": "none",
        "COA_PROVIDER_CONVERSATION": "none",
        "COA_PROVIDER_MEMORY": "none",
        "COA_PROVIDER_OBJECT_STORE": "none",
    }
    settings = ProviderSettings.from_mapping(mapping)
    gateway = build_gateway(settings)

    seeds = await gateway.graph_client.query(
        "SELECT ?s ?p ?o WHERE { GRAPH ?g { ?s ?p ?o } FILTER(isIRI(?o)) } LIMIT 5"
    )
    if not seeds:
        seeds = await gateway.graph_client.query(
            "SELECT ?s ?p ?o WHERE { ?s ?p ?o FILTER(isIRI(?o)) } LIMIT 5"
        )
    start_uri = seeds[0]["s"]
    print("start_uri:", start_uri)

    app = create_app(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway"
    ) as client:
        response = await client.post(
            f"/namespaces/{NAMESPACE}/graph/traverse",
            json={"startUri": start_uri, "maxDepth": 2, "direction": "both", "maxResults": 50},
        )
        bad_namespace = await client.post(
            "/namespaces/not-a-uuid/graph/traverse", json={"startUri": start_uri}
        )
        bad_direction = await client.post(
            f"/namespaces/{NAMESPACE}/graph/traverse",
            json={"startUri": start_uri, "direction": "sideways"},
        )

    body = response.json()
    print(
        json.dumps(
            {
                "status": response.status_code,
                "entities": body.get("entities"),
                "relationships": body.get("relationships"),
                "trace": body.get("trace"),
                "bad_namespace": {"status": bad_namespace.status_code, "body": bad_namespace.json()},
                "bad_direction": {"status": bad_direction.status_code, "body": bad_direction.json()},
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    assert response.status_code == 200, response.text
    assert body["entities"] and all({"uri", "label"} <= set(entity) for entity in body["entities"])
    assert body["relationships"] and all(
        {"sourceUri", "predicateUri", "targetUri"} <= set(edge) for edge in body["relationships"]
    )
    assert body["trace"] and all({"step", "status"} <= set(step) for step in body["trace"])
    assert bad_namespace.status_code == 400 and set(bad_namespace.json()) == {"message"}
    assert bad_direction.status_code == 400 and set(bad_direction.json()) == {"message"}
    print("COA_GRAPH_TRAVERSE_OK")


if __name__ == "__main__":
    asyncio.run(main())
