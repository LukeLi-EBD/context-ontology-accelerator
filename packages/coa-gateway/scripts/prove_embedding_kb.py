"""Prove the embedding port (bge-local + external-http) and the KBSearch shape.

Real calls only: local BGE-M3 via TEI, real pgvector chunks from
``platform.chunk_embedding``, and the OpenAI-compatible HTTP implementation
against the same configured endpoint with a caller-supplied key.

Also checks the contract failures: dimension mismatch (400 with both numbers),
missing key (explicit config error), and a dead backend (503, not 502).
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import sys
import uuid

import httpx

from coa_gateway import ProviderSettings, build_client, build_gateway
from coa_gateway.http_api import create_app
from coa_local_providers.embedding_base import EmbeddingProvider

DSN = os.environ["COA_VECTOR_PG_DSN"]
NAMESPACE = "00000000-0000-0000-0000-000000000000"
TEXT_A = "员工差旅报销标准"
TEXT_B = "公司年度采购计划"


def settings_for(extra: dict[str, str]) -> ProviderSettings:
    mapping = {
        "COA_PROVIDER_GRAPH": "none",
        "COA_PROVIDER_VECTOR": "platform-pgvector",
        "COA_VECTOR_PG_DSN": DSN,
        "COA_PROVIDER_LLM": "none",
        "COA_PROVIDER_QUERY_EXECUTOR": "none",
        "COA_PROVIDER_SOURCE_CATALOG": "none",
        "COA_PROVIDER_CONVERSATION": "none",
        "COA_PROVIDER_MEMORY": "none",
        "COA_PROVIDER_OBJECT_STORE": "none",
        **extra,
    }
    return ProviderSettings.from_mapping(mapping)


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    n1 = math.sqrt(sum(a * a for a in left))
    n2 = math.sqrt(sum(b * b for b in right))
    return round(dot / (n1 * n2), 6) if n1 and n2 else 0.0


async def provider_proof(label: str, settings: ProviderSettings) -> dict[str, object]:
    gateway = build_gateway(settings)
    embedding = gateway.embedding_client
    assert isinstance(embedding, EmbeddingProvider), type(embedding)
    health = await embedding.health_check()
    first = (await embedding.embed([TEXT_A]))[0]
    second = (await embedding.embed([TEXT_A]))[0]
    other = (await embedding.embed([TEXT_B]))[0]
    result = {
        "label": label,
        "provider": embedding.provider,
        "model": embedding.model,
        "dimensions": len(first),
        "declared_dimensions": embedding.dimensions,
        "health": health,
        "same_text_bitwise_equal": first == second,
        "cosine_a_b": cosine(first, other),
    }
    await embedding.close()
    await gateway.vector_client.close()
    return result


async def route_proof(label: str, settings: ProviderSettings, expect: dict[str, int]) -> dict[str, object]:
    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://gateway") as client:
        vector = await client.post("/vector/search", json={"query": TEXT_A, "top_k": 3})
        kb = await client.post(
            f"/namespaces/{NAMESPACE}/kb/search",
            json={"query": TEXT_B, "topK": 3, "minScore": 0.0},
        )
    return {
        "label": label,
        "vector_status": vector.status_code,
        "vector_hits": len(vector.json().get("hits", [])),
        "vector_model": vector.json().get("queryEmbeddingModel"),
        "vector_first": (vector.json().get("hits") or [{}])[0],
        "kb_status": kb.status_code,
        "kb_chunks": len(kb.json().get("chunks", [])),
        "kb_first": (kb.json().get("chunks") or [{}])[0],
        "kb_trace": kb.json().get("trace"),
        "expected": expect,
    }


async def main() -> int:
    bge = await provider_proof(
        "bge-local",
        settings_for({"COA_PROVIDER_EMBEDDING": "bge-local"}),
    )
    external = await provider_proof(
        "external-http",
        settings_for(
            {
                "COA_PROVIDER_EMBEDDING": "external-http",
                "COA_EMBEDDING_HTTP_ENDPOINT": os.environ.get(
                    "COA_EMBEDDING_HTTP_ENDPOINT", "http://embedding:80/v1"
                ),
                "COA_EMBEDDING_HTTP_MODEL": "BAAI/bge-m3",
                "COA_EMBEDDING_HTTP_API_KEY": "local-key",
                "COA_EMBEDDING_HTTP_DIMENSIONS": "1024",
            }
        ),
    )
    bge_routes = await route_proof(
        "bge-local routes",
        settings_for({"COA_PROVIDER_EMBEDDING": "bge-local"}),
        {"vector": 200, "kb": 200},
    )
    external_routes = await route_proof(
        "external-http routes",
        settings_for(
            {
                "COA_PROVIDER_EMBEDDING": "external-http",
                "COA_EMBEDDING_HTTP_ENDPOINT": os.environ.get(
                    "COA_EMBEDDING_HTTP_ENDPOINT", "http://embedding:80/v1"
                ),
                "COA_EMBEDDING_HTTP_MODEL": "BAAI/bge-m3",
                "COA_EMBEDDING_HTTP_API_KEY": "local-key",
                "COA_EMBEDDING_HTTP_DIMENSIONS": "1024",
            }
        ),
        {"vector": 200, "kb": 200},
    )

    mismatch_settings = settings_for(
        {"COA_PROVIDER_EMBEDDING": "bge-local", "COA_EMBEDDING_BGE_DIMENSIONS": "768"}
    )
    app = create_app(mismatch_settings)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway") as client:
        mismatch = await client.post("/vector/search", json={"query": TEXT_A, "top_k": 3})

    dead_settings = settings_for(
        {
            "COA_PROVIDER_EMBEDDING": "bge-local",
            "COA_EMBEDDING_BGE_ENDPOINT": "http://127.0.0.1:9/v1",
        }
    )
    app = create_app(dead_settings)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway") as client:
        dead = await client.post("/vector/search", json={"query": TEXT_A, "top_k": 3})

    missing_key_error = None
    try:
        build_client(
            "embedding",
            ProviderSettings.from_mapping(
                {
                    "COA_PROVIDER_EMBEDDING": "external-http",
                    "COA_EMBEDDING_HTTP_ENDPOINT": "http://embedding:80/v1",
                    "COA_EMBEDDING_HTTP_MODEL": "BAAI/bge-m3",
                    "COA_EMBEDDING_HTTP_DIMENSIONS": "1024",
                }
            ),
        )
    except Exception as exc:  # noqa: BLE001 - the refusal is the evidence
        missing_key_error = f"{type(exc).__name__}: {exc}"

    payload = {
        "bge_local": bge,
        "external_http": external,
        "bge_routes": bge_routes,
        "external_http_routes": external_routes,
        "dimension_mismatch": {
            "status": mismatch.status_code,
            "detail": mismatch.json().get("detail"),
        },
        "dead_backend": {
            "status": dead.status_code,
            "detail": dead.json().get("detail"),
        },
        "missing_key": missing_key_error,
    }
    checks = {
        "bge_protocol": bge["provider"] == "bge-local",
        "bge_dimensions": bge["dimensions"] == 1024,
        "bge_deterministic": bge["same_text_bitwise_equal"] is True,
        "external_protocol": external["provider"] == "external-http",
        "external_dimensions": external["dimensions"] == 1024,
        "bge_vector_route": bge_routes["vector_status"] == 200 and bge_routes["vector_hits"] >= 1,
        "bge_kb_route": bge_routes["kb_status"] == 200 and bge_routes["kb_chunks"] >= 1,
        "external_vector_route": external_routes["vector_status"] == 200
        and external_routes["vector_hits"] >= 1,
        "external_kb_route": external_routes["kb_status"] == 200
        and external_routes["kb_chunks"] >= 1,
        "mismatch_is_400": mismatch.status_code == 400,
        "mismatch_names_both": "768" in str(mismatch.json().get("detail"))
        and "1024" in str(mismatch.json().get("detail")),
        "dead_backend_is_503": dead.status_code == 503,
        "missing_key_names_key": missing_key_error is not None
        and "COA_EMBEDDING_HTTP_API_KEY" in missing_key_error,
    }
    print(json.dumps({"results": payload, "checks": checks}, ensure_ascii=False, indent=2, default=str))
    ok = all(checks.values())
    print(f"LOCAL_BGE={'yes' if bge['dimensions'] == 1024 else 'no'} dim={bge['dimensions']}")
    print(f"EXTERNAL_HTTP={'yes' if external['provider'] == 'external-http' else 'no'}")
    print(f"KBSEARCH={'supported' if bge_routes['kb_chunks'] else 'not-supported'}")
    if ok:
        print("EMBEDDING_KB_OK")
    else:
        print("EMBEDDING_KB_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
