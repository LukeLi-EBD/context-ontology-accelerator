"""Prove the provider switch: one probe function, two graph backends.

Same call code both times; only ``COA_PROVIDER_GRAPH`` (and its endpoint) changes.
Runs in the gateway verify image on the acceptance network — no published port.

    docker run --rm --network platform-acceptance_default \
      --entrypoint python \
      -e COA_GATEWAY_SEED_FUSEKI=1 \
      -e COA_GRAPH_FUSEKI_URL=http://coa-gateway-fuseki:3030/ds/sparql \
      -e PYTHONPATH=/repo/libs/common/src:/repo/packages/context-manager/src:/repo/packages/coa-gateway/src \
      -v <repo>:/repo:ro coa-gateway-verify:0.1 \
      /repo/packages/coa-gateway/scripts/prove_provider_switch.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

import httpx

from coa_gateway import ProviderConfigError, ProviderSettings, build_gateway
from coa_gateway.sparql_http import GRAPH_HAS_TRIPLES

DEMO_GRAPH = "urn:coa:gateway:demo"
DEMO_TRIPLES = (
    f'<urn:coa:gateway:demo#s1> <urn:coa:gateway:demo#p> "one" .\n'
    f'<urn:coa:gateway:demo#s2> <urn:coa:gateway:demo#p> "two" .'
)

PROVIDERS = ("oxigraph", "fuseki")


async def seed_fuseki(query_url: str) -> None:
    """Fixture only: the ephemeral Fuseki container starts empty."""
    update_url = query_url[: -len("sparql")] + "update"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            update_url,
            data={"update": f"INSERT DATA {{ GRAPH <{DEMO_GRAPH}> {{ {DEMO_TRIPLES} }} }}"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()


async def probe(gateway: Any) -> dict[str, Any]:
    """The one piece of call code both providers go through."""
    client = gateway.graph_client
    health = await client.health_check()
    asked = await client.ask(GRAPH_HAS_TRIPLES)
    rows = await client.query(
        "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g ORDER BY ?g LIMIT 3"
    )
    return {"backend": health.get("backend"), "health_ok": health.get("ok"), "ask": asked, "rows": rows}


def env_for(provider: str) -> dict[str, str]:
    env = {
        "COA_PROVIDER_GRAPH": provider,
        "COA_PROVIDER_VECTOR": "none",
        "COA_GRAPH_OXIGRAPH_URL": os.environ.get("COA_GRAPH_OXIGRAPH_URL", "http://oxigraph:7878"),
        "COA_GRAPH_FUSEKI_URL": os.environ.get("COA_GRAPH_FUSEKI_URL", "http://coa-gateway-fuseki:3030/ds/sparql"),
    }
    return env


async def main() -> int:
    if os.environ.get("COA_GATEWAY_SEED_FUSEKI") == "1":
        await seed_fuseki(env_for("fuseki")["COA_GRAPH_FUSEKI_URL"])

    results: dict[str, Any] = {}
    for provider in PROVIDERS:
        results[provider] = await probe(build_gateway(ProviderSettings.from_mapping(env_for(provider))))

    neptune_error: str | None = None
    try:
        build_gateway(ProviderSettings.from_mapping({"COA_PROVIDER_GRAPH": "neptune"}))
    except ProviderConfigError as exc:
        neptune_error = str(exc)

    checks = {
        "both_healthy": all(results[p]["health_ok"] for p in PROVIDERS),
        "backends_differ": len({results[p]["backend"] for p in PROVIDERS}) == 2,
        "both_ask_true": all(results[p]["ask"] for p in PROVIDERS),
        "both_have_rows": all(results[p]["rows"] for p in PROVIDERS),
        "neptune_fails_loudly": neptune_error is not None,
    }
    payload = {"results": results, "neptune_error": neptune_error, "checks": checks}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    ok = all(checks.values())
    print("SWITCH OK" if ok else "SWITCH FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
