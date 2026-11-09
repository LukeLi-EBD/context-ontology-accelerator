"""Prove N5 get_history is no longer empty once N6 MemoryStore writes turns.

Runs one gateway with conversation + memory on the same SQLite file, appends
two turns, then reads them back through ``ConversationStore.get_history`` and
through ``MemoryStore.get_window`` / ``MemoryStore.search``. Also exercises the
HTTP facade in-process (ASGI transport, no port): ``/memory/append_turn`` then
``/conversation/get_history`` must show three turns. Prints the JSON so the
round trip is verifiable, not asserted silently.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile

import httpx

from coa_gateway.registry import build_gateway
from coa_gateway.settings import ProviderSettings

USER_ID = "u-demo"
NAMESPACE = "ns-demo"

TURNS = [
    {"role": "user", "content": "会话历史现在真的落盘了吗？"},
    {"role": "assistant", "content": "是：MemoryStore 写入 session_turn，ConversationStore 读同一条记录。"},
]


async def _http_roundtrip(settings, session_id: str) -> dict:
    from coa_gateway.http_api import create_app

    app = create_app(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway"
    ) as client:
        append = await client.post(
            "/memory/append_turn",
            json={
                "session_id": session_id,
                "turn": {"role": "user", "content": "HTTP 门面追加的第三轮"},
            },
        )
        history = await client.post(
            "/conversation/get_history", json={"session_id": session_id, "limit": 10}
        )
        search = await client.post(
            "/memory/search", json={"namespace": NAMESPACE, "query": "HTTP", "top_k": 5}
        )
    return {
        "append_status": append.status_code,
        "append": append.json(),
        "history_status": history.status_code,
        "history_turns": history.json()["turns"],
        "search_status": search.status_code,
        "search": search.json(),
    }


def main() -> None:
    path = os.environ.get("PROVE_DB_PATH") or os.path.join(
        tempfile.mkdtemp(prefix="coa-memory-"), "sessions.db"
    )
    mapping = {
        "COA_PROVIDER_GRAPH": "none",
        "COA_PROVIDER_VECTOR": "none",
        "COA_PROVIDER_LLM": "none",
        "COA_PROVIDER_QUERY_EXECUTOR": "none",
        "COA_PROVIDER_SOURCE_CATALOG": "none",
        "COA_PROVIDER_CONVERSATION": "sqlite",
        "COA_CONVERSATION_SQLITE_PATH": path,
        "COA_PROVIDER_MEMORY": "sqlite",
        "COA_MEMORY_SQLITE_PATH": path,
        "COA_PROVIDER_OBJECT_STORE": "none",
    }
    gateway = build_gateway(ProviderSettings.from_mapping(mapping))
    settings = ProviderSettings.from_mapping(mapping)

    session = gateway.conversation_store.create(USER_ID, NAMESPACE, "roundtrip")
    before = gateway.conversation_store.get_history(session.session_id, limit=10)
    appended = [
        gateway.memory_store.append_turn(session.session_id, turn) for turn in TURNS
    ]
    history = gateway.conversation_store.get_history(session.session_id, limit=10)
    window = gateway.memory_store.get_window(session.session_id, turns=10)
    hits = gateway.memory_store.search(NAMESPACE, "落盘", top_k=5)
    http_facade = asyncio.run(_http_roundtrip(settings, session.session_id))

    print(
        json.dumps(
            {
                "db_path": path,
                "capabilities": gateway.capabilities(),
                "session": session.__dict__,
                "history_before_append": before,
                "appended": [turn.__dict__ for turn in appended],
                "get_history_after_append": history,
                "get_window": [turn.__dict__ for turn in window],
                "search": {"query": "落盘", "mode": hits[0]["mode"] if hits else None, "hits": hits},
                "http_facade": http_facade,
                "health": {
                    "conversation": gateway.conversation_store.health_check(),
                    "memory": gateway.memory_store.health_check(),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    assert len(history) == len(TURNS), f"history should carry {len(TURNS)} turns, got {len(history)}"
    assert [turn["role"] for turn in history] == [turn["role"] for turn in TURNS]
    assert hits and hits[0]["mode"] == "lexical-approx"
    assert http_facade["append_status"] == 200
    assert len(http_facade["history_turns"]) == len(TURNS) + 1
    assert http_facade["search"]["mode"] == "lexical-approx"
    assert http_facade["search"]["hits"], "HTTP search should hit the appended turn"
    print("MEMORY_ROUNDTRIP_OK")


if __name__ == "__main__":
    main()
