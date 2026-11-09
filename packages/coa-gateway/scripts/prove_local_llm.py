"""Prove the local LLMClient really completes a prompt in-process (no server).

Builds a gateway with only ``COA_PROVIDER_LLM=llama-cpp``, asserts the instance
satisfies the upstream ``LLMClient`` protocol, runs one real chat completion on
a local GGUF file, and reports the text plus latency. Also shows that ``embed``
is refused rather than returning a fake vector.
"""

from __future__ import annotations

import asyncio
import json
import os
import time

import httpx

from coa_gateway.registry import build_gateway
from coa_gateway.settings import ProviderSettings

PROMPT = "用一句中文回答：本地推理是否可用？"
SYSTEM = "你是一个简洁的中文助手，只回答一句话。"


async def _http_converse(settings) -> dict:
    from coa_gateway.http_api import create_app

    app = create_app(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway"
    ) as client:
        response = await client.post(
            "/llm/converse",
            json={
                "prompt": PROMPT,
                "system": SYSTEM,
                "max_tokens": 64,
                "temperature": 0.0,
            },
        )
    return {"status": response.status_code, "body": response.json()}


async def main() -> None:
    model_path = os.environ.get("COA_LLM_LLAMA_CPP_MODEL_PATH", "").strip()
    if not model_path:
        raise SystemExit("set COA_LLM_LLAMA_CPP_MODEL_PATH to a local .gguf file")

    mapping = {
        "COA_PROVIDER_GRAPH": "none",
        "COA_PROVIDER_VECTOR": "none",
        "COA_PROVIDER_LLM": "llama-cpp",
        "COA_LLM_LLAMA_CPP_MODEL_PATH": model_path,
        "COA_LLM_LLAMA_CPP_N_CTX": "2048",
        "COA_LLM_LLAMA_CPP_N_THREADS": "10",
        "COA_PROVIDER_QUERY_EXECUTOR": "none",
        "COA_PROVIDER_SOURCE_CATALOG": "none",
        "COA_PROVIDER_CONVERSATION": "none",
        "COA_PROVIDER_MEMORY": "none",
        "COA_PROVIDER_OBJECT_STORE": "none",
    }

    started = time.perf_counter()
    settings = ProviderSettings.from_mapping(mapping)
    gateway = build_gateway(settings)
    load_seconds = round(time.perf_counter() - started, 2)

    client = gateway.llm_client
    from coa_serve.clients.base import LLMClient

    health = await client.health_check()

    started = time.perf_counter()
    result = await client.converse(PROMPT, system=SYSTEM, max_tokens=64, temperature=0.0)
    latency_ms = round((time.perf_counter() - started) * 1000, 1)

    embed_error = None
    try:
        await client.embed("本地推理")
    except NotImplementedError as exc:
        embed_error = f"{type(exc).__name__}: {exc}"

    http_facade = await _http_converse(settings)

    print(
        json.dumps(
            {
                "capabilities": gateway.capabilities(),
                "contract": {"isinstance_LLMClient": isinstance(client, LLMClient)},
                "model_load_seconds": load_seconds,
                "health": health,
                "prompt": PROMPT,
                "system": SYSTEM,
                "result": {
                    "text": result.text,
                    "stop_reason": result.stop_reason,
                    "truncated": result.truncated,
                },
                "latency_ms": latency_ms,
                "embed": embed_error,
                "http_facade": http_facade,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    assert isinstance(client, LLMClient)
    assert result.text.strip(), "local completion returned empty text"
    assert http_facade["status"] == 200
    assert http_facade["body"]["text"].strip(), "HTTP converse returned empty text"
    print("LOCAL_LLM_OK")


if __name__ == "__main__":
    asyncio.run(main())
