"""Contract tests for the synchronous-to-async LLM shell."""

from __future__ import annotations

import asyncio
import json
import time

import pytest
from coa_local_providers.shells.async_bridge import SyncToAsyncShell
from coa_local_providers.shells.llm import PlatformLLMShell
from coa_ports import PortError, PortErrorCode
from coa_serve.clients.base import LLMClient


class _FakeClient:
    def __init__(self, *, payload: dict | None = None, delay_s: float = 0.0) -> None:
        self.payload = payload if payload is not None else {"answer": "ok"}
        self.delay_s = delay_s
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system: str, user: str) -> dict:
        self.calls.append((system, user))
        if self.delay_s:
            time.sleep(self.delay_s)
        return self.payload

    def configured(self) -> bool:
        return True

    class _Config:
        model = "fake-model"

    _config = _Config()

    def close(self) -> None:
        return None


def _shell(client: _FakeClient, *, timeout_s: float = 1.0) -> PlatformLLMShell:
    return PlatformLLMShell(client, timeout_s=timeout_s, max_workers=2)


def test_implements_the_coa_contract() -> None:
    assert isinstance(_shell(_FakeClient()), LLMClient)


def test_converse_returns_the_json_body_as_text() -> None:
    client = _FakeClient(payload={"answer": "ok"})
    result = asyncio.run(_shell(client).converse("question", system="be terse"))

    assert json.loads(result.text) == {"answer": "ok"}
    assert client.calls == [("be terse", "question")]


def test_converse_rejects_knobs_the_backend_cannot_honour() -> None:
    with pytest.raises(PortError) as excinfo:
        asyncio.run(_shell(_FakeClient()).converse("q", temperature=0.0))

    assert excinfo.value.code is PortErrorCode.UNSUPPORTED
    assert excinfo.value.provider_code == "E_LLM_KNOB_UNSUPPORTED"


def test_converse_stream_is_unsupported_on_iteration() -> None:
    async def iterate() -> list[str]:
        return [chunk async for chunk in _shell(_FakeClient()).converse_stream("q")]

    with pytest.raises(PortError) as excinfo:
        asyncio.run(iterate())

    assert excinfo.value.code is PortErrorCode.UNSUPPORTED
    assert excinfo.value.provider_code == "E_LLM_STREAM_UNAVAILABLE"


def test_embed_is_unsupported_and_points_at_the_embedding_port() -> None:
    with pytest.raises(PortError) as excinfo:
        asyncio.run(_shell(_FakeClient()).embed("text"))

    assert excinfo.value.code is PortErrorCode.UNSUPPORTED
    assert excinfo.value.provider_code == "E_LLM_EMBED_UNAVAILABLE"


def test_health_check_reports_the_snapshot_and_never_raises() -> None:
    healthy = asyncio.run(_shell(_FakeClient()).health_check())
    assert healthy["ok"] is True
    assert healthy["model"] == "fake-model"
    assert healthy["probe"] == "configuration-snapshot"


def test_a_slow_call_times_out_with_the_port_timeout_code() -> None:
    with pytest.raises(PortError) as excinfo:
        asyncio.run(_shell(_FakeClient(delay_s=0.4), timeout_s=0.01).converse("q"))

    assert excinfo.value.code is PortErrorCode.TIMEOUT
    assert excinfo.value.provider_code == "E_SYNC_TIMEOUT"


def test_a_cancelled_caller_stops_waiting() -> None:
    async def scenario() -> None:
        shell = _shell(_FakeClient(delay_s=0.4), timeout_s=2.0)
        task = asyncio.create_task(shell.converse("q"))
        await asyncio.sleep(0.02)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_bridge_rejects_non_positive_limits() -> None:
    with pytest.raises(ValueError):
        SyncToAsyncShell(provider="x", max_workers=0)
    with pytest.raises(ValueError):
        SyncToAsyncShell(provider="x", timeout_s=0)
