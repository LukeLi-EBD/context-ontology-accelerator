"""End-to-end proof: real COA GraphClient contract -> local Oxigraph.

Run inside a container on the acceptance network (no published port):

    docker run --rm --network platform-acceptance_default \
      --entrypoint python -e COA_GATEWAY_OXIGRAPH_URL=http://oxigraph:7878 \
      -e PYTHONPATH=/repo/libs/common/src:/repo/packages/context-manager/src:/repo/packages/coa-gateway/src \
      -v <repo>:/repo:ro coa-gateway-verify:0.1 \
      /repo/packages/coa-gateway/scripts/prove_graph_e2e.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from coa_gateway import LocalGateway, OxigraphGraphClient, ProviderSettings, build_gateway
from coa_gateway.sparql_http import GRAPH_HAS_TRIPLES
from coa_serve.clients.base import GraphClient


async def main() -> int:
    endpoint = os.environ.get("COA_GATEWAY_OXIGRAPH_URL", "http://oxigraph:7878")
    client = OxigraphGraphClient(endpoint)
    gateway = LocalGateway(client)

    checks: dict[str, bool] = {}
    checks["isinstance_graph_client"] = isinstance(client, GraphClient)
    checks["capabilities_graph"] = gateway.capabilities()["graph"]

    health = await gateway.health()
    checks["health_ok"] = bool(health["graph"].get("ok"))

    asked = await client.ask(GRAPH_HAS_TRIPLES)
    checks["ask_has_triples"] = asked

    rows = await client.query(
        "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g LIMIT 3"
    )
    checks["query_returns_rows"] = len(rows) == 3 and all({"g", "n"} <= set(r) for r in rows)

    # The registry path the gateway actually uses must resolve to the same client.
    built = build_gateway(
        ProviderSettings.from_mapping({"COA_PROVIDER_GRAPH": "oxigraph", "COA_PROVIDER_VECTOR": "none"})
    )
    checks["registry_builds_oxigraph"] = isinstance(built.graph_client, OxigraphGraphClient)

    print(
        json.dumps(
            {"endpoint": endpoint, "checks": checks, "health": health, "sample": rows[:2]},
            ensure_ascii=False,
            indent=2,
        )
    )
    ok = all(checks.values())
    print("PROOF OK" if ok else "PROOF FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
