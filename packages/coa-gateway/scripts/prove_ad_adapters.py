"""Prove the three AD-backed COA providers selectable through ``COA_PROVIDER_*``.

Each section builds the gateway through the real provider selector, asserts the
concrete client satisfies the COA Protocol, then makes a real call:

- ``platform-oxigraph`` -> ``GraphClient`` over platform_core ``OxigraphHttpStore``
- ``platform-fuseki``   -> ``GraphClient`` over platform_core ``FusekiHttpStore``
- ``platform-pg``       -> ``QueryExecutor`` over platform_core ``MetadataPg``

Run inside the verify image on the acceptance network. No published ports.

    docker run --rm --network platform-acceptance_default --entrypoint python \
      -e COA_AD_FUSEKI_URL=http://coa-ad-fuseki:3030 \
      -e COA_EXECUTOR_POSTGRES_DSN=... \
      -e PYTHONPATH=... \
      -v <repo>:/repo:ro coa-gateway-verify:0.1 \
      /repo/packages/coa-gateway/scripts/prove_ad_adapters.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

import httpx

from coa_gateway import ProviderSettings, build_gateway
from coa_gateway.coa_operations import get_entity
from coa_serve.clients.base import GraphClient, QueryExecutor

DEMO_GRAPH = "urn:platform:ad-proof"
DEMO_SUBJECT = "urn:platform:ad-proof#s1"
DEMO_TRIPLES = (
    f'<{DEMO_SUBJECT}> <urn:platform:ad-proof#p> "one" .\n'
    f'<urn:platform:ad-proof#s2> <urn:platform:ad-proof#p> "two" .'
)


def settings_for(interface: str, provider: str, extra: dict[str, str]) -> ProviderSettings:
    mapping: dict[str, str] = {
        "COA_PROVIDER_GRAPH": "none",
        "COA_PROVIDER_VECTOR": "none",
        "COA_PROVIDER_LLM": "none",
        "COA_PROVIDER_QUERY_EXECUTOR": "none",
        "COA_PROVIDER_SOURCE_CATALOG": "none",
        "COA_PROVIDER_CONVERSATION": "none",
        "COA_PROVIDER_MEMORY": "none",
        "COA_PROVIDER_OBJECT_STORE": "none",
        **extra,
    }
    mapping[f"COA_PROVIDER_{interface.upper()}"] = provider
    return ProviderSettings.from_mapping(mapping)


async def seed_fuseki(server_root: str) -> None:
    """Fixture only: the ephemeral Fuseki dataset starts empty."""
    url = f"{server_root.rstrip('/')}/ds/update"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            data={"update": f"INSERT DATA {{ GRAPH <{DEMO_GRAPH}> {{ {DEMO_TRIPLES} }} }}"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()


async def oxigraph_proof() -> dict[str, Any]:
    gateway = build_gateway(
        settings_for(
            "graph",
            "platform-oxigraph",
            {
                "COA_GRAPH_OXIGRAPH_URL": os.environ.get(
                    "COA_GRAPH_OXIGRAPH_URL", "http://oxigraph:7878"
                )
            },
        )
    )
    client = gateway.graph_client
    assert isinstance(client, GraphClient), type(client)
    health = await client.health_check()
    rows = await client.query(
        "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g ORDER BY ?g LIMIT 3"
    )
    target = os.environ.get("COA_AD_ENTITY_URI", "http://example.org/tbox#Department")
    entity = await get_entity(client, uri=target)
    await client.close()
    return {
        "protocol": "GraphClient",
        "concrete": type(client).__name__,
        "health": health,
        "named_graphs": rows,
        "get_entity": entity,
    }


async def fuseki_proof() -> dict[str, Any]:
    server_root = os.environ["COA_AD_FUSEKI_URL"]
    await seed_fuseki(server_root)
    gateway = build_gateway(
        settings_for(
            "graph",
            "platform-fuseki",
            {"COA_GRAPH_FUSEKI_SERVER_URL": server_root},
        )
    )
    client = gateway.graph_client
    assert isinstance(client, GraphClient), type(client)
    health = await client.health_check()
    asked = await client.ask(f"ASK {{ GRAPH <{DEMO_GRAPH}> {{ ?s ?p ?o }} }}")
    rows = await client.query(f"SELECT ?s ?p ?o WHERE {{ GRAPH <{DEMO_GRAPH}> {{ ?s ?p ?o }} }}")
    entity = await get_entity(client, uri=DEMO_SUBJECT)
    await client.close()
    return {
        "protocol": "GraphClient",
        "concrete": type(client).__name__,
        "health": health,
        "ask": asked,
        "rows": rows,
        "get_entity": entity,
    }


async def postgres_proof() -> dict[str, Any]:
    dsn = os.environ["COA_EXECUTOR_POSTGRES_DSN"]
    gateway = build_gateway(
        settings_for(
            "query_executor",
            "platform-pg",
            {"COA_EXECUTOR_POSTGRES_DSN": dsn, "COA_EXECUTOR_MAX_ROWS": "5"},
        )
    )
    executor = gateway.query_executor
    assert isinstance(executor, QueryExecutor), type(executor)
    health = await executor.health_check()
    one = await executor.execute(
        "SELECT 1 AS ok", namespace="", data_source_id="", max_rows=5
    )
    schema = await executor.execute(
        "SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema = 'platform'",
        namespace="",
        data_source_id="",
    )
    truncated = await executor.execute(
        "SELECT generate_series(1, 10) AS n", namespace="", data_source_id="", max_rows=5
    )
    await executor.close()
    return {
        "protocol": "QueryExecutor",
        "concrete": type(executor).__name__,
        "health": health,
        "select_one": {"rows": one.rows, "columns": one.columns, "engine": one.engine},
        "platform_tables": schema.rows,
        "truncated": {
            "row_count": truncated.row_count,
            "truncated": truncated.truncated,
            "rows": truncated.rows,
        },
    }


async def main() -> int:
    payload: dict[str, Any] = {}
    payload["oxigraph"] = await oxigraph_proof()
    payload["fuseki"] = await fuseki_proof()
    payload["postgres"] = await postgres_proof()

    checks = {
        "oxigraph_protocol": payload["oxigraph"]["concrete"] == "OxigraphGraphClient",
        "oxigraph_healthy": payload["oxigraph"]["health"].get("ok") is True,
        "oxigraph_entity": bool(payload["oxigraph"]["get_entity"]["statements"]),
        "fuseki_protocol": payload["fuseki"]["concrete"] == "FusekiGraphClient",
        "fuseki_healthy": payload["fuseki"]["health"].get("ok") is True,
        "fuseki_ask": payload["fuseki"]["ask"] is True,
        "fuseki_rows": len(payload["fuseki"]["rows"]) >= 1,
        "fuseki_entity": bool(payload["fuseki"]["get_entity"]["statements"]),
        "postgres_protocol": payload["postgres"]["concrete"] == "PostgresQueryExecutor",
        "postgres_healthy": payload["postgres"]["health"].get("ok") is True,
        "postgres_select": payload["postgres"]["select_one"]["rows"] == [{"ok": 1}],
        "postgres_truncates": payload["postgres"]["truncated"]["truncated"] is True,
    }
    print(json.dumps({"results": payload, "checks": checks}, ensure_ascii=False, indent=2, default=str))
    ok = all(checks.values())
    if ok:
        print("AD_OXIGRAPH_OK")
        print("AD_FUSEKI_OK")
        print("AD_POSTGRES_OK")
        print("AD_ADAPTERS_OK")
    else:
        print("AD_ADAPTERS_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
