"""P2 rehearsal: the same call site, only the provider config changes.

Run twice from the shell, changing *only* ``COA_PROVIDER_GRAPH`` and its
provider-specific env:

  oxigraph  -> real local Oxigraph in the acceptance network
  neptune   -> SigV4-shaped client against the local Neptune stub

The Python below never branches on the provider.
"""

from __future__ import annotations

import asyncio
import json
import os

from coa_gateway.registry import build_gateway
from coa_gateway.settings import ProviderSettings

SPARQL = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?s ?label WHERE { GRAPH ?g { ?s rdfs:label ?label } } LIMIT 2"
ASK = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ASK { GRAPH ?g { ?s rdfs:label ?label } }"


async def main() -> None:
    for key in (
        "COA_PROVIDER_VECTOR",
        "COA_PROVIDER_QUERY_EXECUTOR",
        "COA_PROVIDER_SOURCE_CATALOG",
        "COA_PROVIDER_CONVERSATION",
        "COA_PROVIDER_OBJECT_STORE",
    ):
        os.environ.setdefault(key, "none")

    gateway = build_gateway(ProviderSettings.from_env())
    print(f"config.graph={os.environ.get('COA_PROVIDER_GRAPH')} health={await gateway.health()}")
    rows = await gateway.graph_client.query(SPARQL)
    print("query.rows=" + json.dumps(rows, ensure_ascii=False))
    print("ask=" + json.dumps(await gateway.graph_client.ask(ASK)))
    print("PROVIDER_SWITCH_OK" if rows else "PROVIDER_SWITCH_FAILED")


if __name__ == "__main__":
    asyncio.run(main())
