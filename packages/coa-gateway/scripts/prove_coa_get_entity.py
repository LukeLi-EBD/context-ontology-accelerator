"""Prove PlatformKnowledgeService.GetEntity reaches the real local graph.

Picks a labelled, typed IRI from the acceptance Oxigraph, then calls
``GET /namespaces/{namespaceId}/graph/entity?uri=`` over an in-process ASGI
transport (no port) and prints the real response.
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
MISSING = "urn:coa:gateway:missing:entity"


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

    candidates = await gateway.graph_client.query(
        "SELECT ?s WHERE { GRAPH ?g { ?s <http://www.w3.org/2000/01/rdf-schema#label> ?l } "
        "GRAPH ?g2 { ?s a ?t } } LIMIT 3"
    )
    target = candidates[0]["s"]
    print("target_uri:", target)

    app = create_app(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway"
    ) as client:
        response = await client.get(
            f"/namespaces/{NAMESPACE}/graph/entity", params={"uri": target}
        )
        missing = await client.get(
            f"/namespaces/{NAMESPACE}/graph/entity", params={"uri": MISSING}
        )
        no_uri = await client.get(f"/namespaces/{NAMESPACE}/graph/entity")
        bad_namespace = await client.get(
            "/namespaces/not-a-uuid/graph/entity", params={"uri": target}
        )

    body = response.json()
    print(json.dumps({"status": response.status_code, **body}, ensure_ascii=False, indent=2))
    print(
        json.dumps(
            {
                "missing": {"status": missing.status_code, "body": missing.json()},
                "no_uri": {"status": no_uri.status_code, "body": no_uri.json()},
                "bad_namespace": {"status": bad_namespace.status_code, "body": bad_namespace.json()},
            },
            ensure_ascii=False,
        )
    )

    assert response.status_code == 200, response.text
    entity, statements = body["entity"], body["statements"]
    assert entity["uri"] == target and entity["label"]
    assert {"uri", "label", "properties"} <= set(entity)
    assert {"subject", "predicate", "object", "objectIsLiteral"} <= set(statements[0])
    assert any(s["predicate"].endswith("#label") and s["objectIsLiteral"] for s in statements)
    assert any(s["predicate"].endswith("#type") and not s["objectIsLiteral"] for s in statements)
    assert missing.status_code == 404 and set(missing.json()) == {"message"}
    assert no_uri.status_code == 400 and set(no_uri.json()) == {"message"}
    assert bad_namespace.status_code == 400 and set(bad_namespace.json()) == {"message"}
    print("COA_GET_ENTITY_OK")


if __name__ == "__main__":
    asyncio.run(main())
