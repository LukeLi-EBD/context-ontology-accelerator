"""One process: graph + vector + query_executor (+ catalog), one combined call.

Chain: read an entity label from the published T-Box graph -> use it to retrieve a
similar document from the vector index -> run one SQL statement against the
acceptance database with the query executor.

    docker run --rm --network platform-acceptance_default --entrypoint python \
      -e COA_EXECUTOR_POSTGRES_DSN=postgresql://platform:<password>@postgres:5432/platform \
      -e COA_SOURCE_CATALOG_JSON_PATH=/repo/doc/_evidence-coa-integration/s1-2026-11-08/snapshot/catalog.json \
      -e PYTHONPATH=/repo/libs/common/src:/repo/packages/context-manager/src:/repo/packages/metric-service/src:/repo/packages/local-providers/src:/repo/packages/coa-gateway/src \
      -v <repo>:/repo:ro coa-gateway-verify:0.1 \
      /repo/packages/coa-gateway/scripts/prove_combined.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from coa_gateway import ProviderSettings, build_gateway

RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
DEFAULT_SNAPSHOT = "/repo/doc/_evidence-coa-integration/s1-2026-11-08/snapshot/catalog.json"


def embed(text: str, dim: int = 16) -> list[float]:
    """Deterministic local embedding (character hashing), not a model."""
    vector = [0.0] * dim
    for char in text.lower():
        vector[ord(char) % dim] += 1.0
    return vector


async def main() -> int:
    workdir = Path(tempfile.mkdtemp(prefix="coa-gw-"))
    vector_path = workdir / "vectors.jsonl"

    env = {
        "COA_PROVIDER_GRAPH": "oxigraph",
        "COA_PROVIDER_VECTOR": "in-memory",
        "COA_PROVIDER_QUERY_EXECUTOR": "postgres",
        "COA_PROVIDER_SOURCE_CATALOG": "json",
        "COA_GRAPH_OXIGRAPH_URL": os.environ.get("COA_GRAPH_OXIGRAPH_URL", "http://oxigraph:7878"),
        "COA_VECTOR_IN_MEMORY_PATH": str(vector_path),
        "COA_EXECUTOR_POSTGRES_DSN": os.environ.get("COA_EXECUTOR_POSTGRES_DSN", ""),
        "COA_SOURCE_CATALOG_JSON_PATH": os.environ.get("COA_SOURCE_CATALOG_JSON_PATH", DEFAULT_SNAPSHOT),
    }
    gateway = build_gateway(ProviderSettings.from_mapping(env))
    capabilities = gateway.capabilities()

    # 1) graph: one real entity + label from the published T-Box graph
    rows = await gateway.graph_client.query(
        f"SELECT ?s ?label WHERE {{ GRAPH ?g {{ ?s <{RDFS_LABEL}> ?label }} }} ORDER BY ?s LIMIT 3"
    )

    # 2) vector: the graph label becomes a document; cosine retrieval over it
    texts = [rows[0]["label"] if rows else "信用申请", "信用 申请 审批", "催收 回收 案件"]
    with vector_path.open("w", encoding="utf-8") as handle:
        for index, text in enumerate(texts):
            record = {"id": f"doc-{index}", "text": text, "vector": embed(text), "metadata": {"namespace": "platform"}}
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    query_text = rows[0]["label"] if rows else texts[0]
    hits = await gateway.vector_client.search(embed(query_text), namespace="platform", top_k=2)

    # 3) executor: one real SQL statement, max_rows=1 to show truncation tagging
    result = await gateway.query_executor.execute(
        "SELECT metric_id, name_zh FROM platform.metric_definition ORDER BY metric_id LIMIT 3",
        namespace="platform",
        data_source_id="platform",
        max_rows=1,
        timeout_seconds=10,
    )

    # 4) catalog: assembled in the same process, still the S1 lookup
    catalog_ok = gateway.source_catalog.data_source_exists("platform")

    checks = {
        "four_interfaces_ready": all(
            capabilities[key] for key in ("graph", "vector", "query_executor", "source_catalog")
        ),
        "graph_returned_entity": bool(rows),
        "vector_returned_hit": bool(hits),
        "sql_returned_row": result.row_count > 0,
        "sql_engine_tagged": result.engine == "postgres",
        "sql_truncation_tagged": result.truncated,
        "catalog_answered": catalog_ok,
    }
    payload = {
        "capabilities": capabilities,
        "steps": {
            "graph": {"rows": rows, "entity": rows[0]["s"] if rows else None},
            "vector": {"query_text": query_text, "hits": [{"id": h.id, "score": h.score} for h in hits]},
            "query_executor": {
                "sql": "SELECT metric_id, name_zh FROM platform.metric_definition ORDER BY metric_id LIMIT 3",
                "columns": result.columns,
                "rows": result.rows,
                "row_count": result.row_count,
                "truncated": result.truncated,
                "duration_ms": result.duration_ms,
                "engine": result.engine,
            },
            "source_catalog": {"data_source_exists": catalog_ok},
        },
        "checks": checks,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    ok = all(checks.values())
    print("COMBINED OK" if ok else "COMBINED FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
