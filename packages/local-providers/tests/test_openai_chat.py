"""``openai-http`` chat provider, exercised against a real socket.

The peer below is a stdlib HTTP server speaking the two routes an
OpenAI-compatible endpoint must serve (``/v1/chat/completions``,
``/v1/models``). It is not a model: it only implements the wire format, so the
translation from JSON/SSE to ``ConverseResult``/text deltas is proven over TCP.
The real generation run lives outside pytest (llama.cpp server).
"""

from __future__ import annotations

import asyncio
import json
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from coa_ports import PortError, PortErrorCode

from coa_local_providers.contracts import ConverseResult
from coa_local_providers.openai_chat import OpenAICompatChat

_PACKAGES = Path(__file__).resolve().parents[2]
_RUNTIME_SRC = str(_PACKAGES / "coa-runtime" / "src")
if _RUNTIME_SRC not in sys.path:
    sys.path.insert(0, _RUNTIME_SRC)

_DELTAS = ("Hello", " from", " the endpoint")


class FakeChatEndpoint:
    """``/v1/chat/completions`` (JSON + SSE) and ``/v1/models`` on a real port."""

    def __init__(
        self,
        *,
        http_status: int = 200,
        finish_reason: str = "stop",
        deltas: tuple[str, ...] = _DELTAS,
    ) -> None:
        self.requests: list[dict[str, Any]] = []
        self._http_status = http_status
        self._finish_reason = finish_reason
        self._deltas = deltas
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        peer = self

        class Handler(BaseHTTPRequestHandler):
            # HTTP/1.0 + close-delimited body lets the SSE route write frames as
            # they happen instead of buffering the whole answer first.
            protocol_version = "HTTP/1.0"

            def do_GET(self) -> None:  # noqa: N802 - http.server API
                peer.requests.append(
                    {
                        "method": "GET",
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                    }
                )
                if self.path == "/v1/models":
                    self._send_json(200, {"object": "list", "data": [{"id": "test-model"}]})
                else:
                    self._send_json(404, {"error": "not found"})

            def do_POST(self) -> None:  # noqa: N802 - http.server API
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length).decode("utf-8")
                payload = json.loads(raw) if raw else {}
                peer.requests.append(
                    {
                        "method": "POST",
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                        "content_type": self.headers.get("Content-Type"),
                        "payload": payload,
                    }
                )
                if self.path != "/v1/chat/completions":
                    self._send_json(404, {"error": "not found"})
                    return
                if peer._http_status >= 400:
                    self._send_json(
                        peer._http_status,
                        {"error": {"message": "endpoint rejected the request"}},
                    )
                    return
                if payload.get("stream"):
                    self._send_sse()
                else:
                    self._send_json(
                        200,
                        {
                            "id": "chatcmpl-test",
                            "object": "chat.completion",
                            "model": payload.get("model"),
                            "choices": [
                                {
                                    "index": 0,
                                    "message": {
                                        "role": "assistant",
                                        "content": "".join(peer._deltas),
                                    },
                                    "finish_reason": peer._finish_reason,
                                }
                            ],
                        },
                    )

            def _send_sse(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                for delta in peer._deltas:
                    frame = {
                        "id": "chatcmpl-test",
                        "choices": [{"index": 0, "delta": {"content": delta}}],
                    }
                    self.wfile.write(
                        ("data: " + json.dumps(frame) + "\n\n").encode("utf-8")
                    )
                    self.wfile.flush()
                    time.sleep(0.01)
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()

            def _send_json(self, status: int, body: dict[str, Any]) -> None:
                data = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args: Any) -> None:  # keep pytest output clean
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}/v1"

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)


async def _converse_and_close(client: OpenAICompatChat, **kwargs: Any) -> ConverseResult:
    try:
        return await client.converse("What is revenue?", **kwargs)
    finally:
        await client.close()


async def _stream_and_close(
    client: OpenAICompatChat, **kwargs: Any
) -> tuple[list[str], str]:
    tokens: list[str] = []
    try:
        async for token in client.converse_stream("Say hello", **kwargs):
            tokens.append(token)
    finally:
        await client.close()
    return tokens, "".join(tokens)


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_converse_returns_plain_text_and_forwards_sampling_knobs() -> None:
    peer = FakeChatEndpoint()
    url = peer.start()
    client = OpenAICompatChat(base_url=url, model="configured-model")
    try:
        result = _run(
            _converse_and_close(
                client,
                system="Be brief.",
                max_tokens=77,
                temperature=0.25,
                top_p=0.9,
                guard_content="Question: What is revenue?",
            )
        )
    finally:
        peer.stop()

    assert result.text == "Hello from the endpoint"
    assert result.stop_reason == "stop"
    payload = peer.requests[0]["payload"]
    assert peer.requests[0]["path"] == "/v1/chat/completions"
    assert payload["model"] == "configured-model"
    assert payload["temperature"] == 0.25
    assert payload["top_p"] == 0.9
    assert payload["max_tokens"] == 77
    assert payload["stream"] is False
    assert payload["messages"][0] == {"role": "system", "content": "Be brief."}
    # guard_content has no guardrail to score it, but must still reach the model.
    assert payload["messages"][1]["content"] == (
        "What is revenue?\n\nQuestion: What is revenue?"
    )


def test_per_call_model_id_overrides_the_configured_model() -> None:
    peer = FakeChatEndpoint()
    url = peer.start()
    client = OpenAICompatChat(base_url=url, model="configured-model")
    try:
        _run(_converse_and_close(client, model_id="override-model", temperature=0.0))
    finally:
        peer.stop()

    payload = peer.requests[0]["payload"]
    assert payload["model"] == "override-model"
    # temperature=0.0 is a real value and must not be dropped by truthiness.
    assert payload["temperature"] == 0.0


def test_absent_sampling_knobs_are_omitted_not_defaulted() -> None:
    peer = FakeChatEndpoint()
    url = peer.start()
    client = OpenAICompatChat(base_url=url, model="configured-model")
    try:
        _run(_converse_and_close(client))
    finally:
        peer.stop()

    payload = peer.requests[0]["payload"]
    assert "temperature" not in payload
    assert "top_p" not in payload


def test_converse_stream_yields_each_delta_and_joins_to_the_answer() -> None:
    peer = FakeChatEndpoint()
    url = peer.start()
    client = OpenAICompatChat(base_url=url, model="configured-model")
    try:
        tokens, joined = _run(_stream_and_close(client, max_tokens=64))
    finally:
        peer.stop()

    assert tokens == list(_DELTAS)
    assert joined == "Hello from the endpoint"
    payload = peer.requests[0]["payload"]
    assert payload["stream"] is True
    assert payload["max_tokens"] == 64


def test_stream_disabled_raises_unsupported_without_calling_the_endpoint() -> None:
    peer = FakeChatEndpoint()
    url = peer.start()
    client = OpenAICompatChat(
        base_url=url, model="configured-model", stream_enabled=False
    )
    try:
        with pytest.raises(PortError) as excinfo:
            _run(_stream_and_close(client))
    finally:
        peer.stop()

    assert excinfo.value.code is PortErrorCode.UNSUPPORTED
    assert excinfo.value.provider_code == "E_LLM_STREAM_DISABLED"
    assert peer.requests == []


def test_guardrail_id_is_rejected_by_default() -> None:
    peer = FakeChatEndpoint()
    url = peer.start()
    client = OpenAICompatChat(base_url=url, model="configured-model")
    try:
        with pytest.raises(PortError) as excinfo:
            _run(
                _converse_and_close(
                    client, guardrail_id="gr-123", guard_content="Question: x"
                )
            )
    finally:
        peer.stop()

    assert excinfo.value.code is PortErrorCode.UNSUPPORTED
    assert excinfo.value.provider_code == "E_LLM_GUARDRAIL_UNSUPPORTED"
    assert excinfo.value.details == {"guardrail_id": "gr-123"}
    assert peer.requests == []


def test_guardrail_ignore_bypass_is_explicit_and_proceeds() -> None:
    peer = FakeChatEndpoint()
    url = peer.start()
    client = OpenAICompatChat(
        base_url=url, model="configured-model", guardrail_mode="ignore"
    )
    try:
        result = _run(_converse_and_close(client, guardrail_id="gr-123"))
    finally:
        peer.stop()

    assert result.text == "Hello from the endpoint"
    assert peer.requests[0]["payload"]["model"] == "configured-model"


def test_http_401_is_a_clear_auth_error_without_bedrock_mentions() -> None:
    peer = FakeChatEndpoint(http_status=401)
    url = peer.start()
    client = OpenAICompatChat(base_url=url, model="configured-model", api_key="wrong")
    try:
        with pytest.raises(PortError) as excinfo:
            _run(_converse_and_close(client))
    finally:
        peer.stop()

    error = excinfo.value
    assert error.code is PortErrorCode.UNAVAILABLE
    assert error.provider_code == "E_LLM_HTTP_AUTH"
    assert "401" in error.message
    assert peer.requests[0]["authorization"] == "Bearer wrong"
    # A failed local call must never look like an AWS fallback happened.
    assert "bedrock" not in str(error.to_dict()).lower()


def test_dead_endpoint_is_unavailable_and_health_check_never_raises() -> None:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()

    async def _call() -> tuple[PortError, dict[str, Any]]:
        client = OpenAICompatChat(
            base_url=f"http://127.0.0.1:{port}/v1", model="configured-model"
        )
        try:
            with pytest.raises(PortError) as excinfo:
                await client.converse("hi")
            return excinfo.value, await client.health_check()
        finally:
            await client.close()

    error, health = _run(_call())
    assert error.code is PortErrorCode.UNAVAILABLE
    assert error.provider_code == "E_LLM_HTTP_UNREACHABLE"
    assert health["ok"] is False
    assert health["provider"] == "openai-http"


def test_finish_reason_length_marks_the_result_truncated() -> None:
    peer = FakeChatEndpoint(finish_reason="length")
    url = peer.start()
    client = OpenAICompatChat(base_url=url, model="configured-model")
    try:
        result = _run(_converse_and_close(client))
    finally:
        peer.stop()

    assert result.stop_reason == "max_tokens"
    assert result.truncated is True


def test_health_check_reads_the_models_route() -> None:
    peer = FakeChatEndpoint()
    url = peer.start()
    client = OpenAICompatChat(base_url=url, model="configured-model")
    try:
        health = _run(_health_and_close(client))
    finally:
        peer.stop()

    assert health["ok"] is True
    assert health["served_models"] == ["test-model"]
    assert peer.requests[0]["path"] == "/v1/models"


async def _health_and_close(client: OpenAICompatChat) -> dict[str, Any]:
    try:
        return await client.health_check()
    finally:
        await client.close()


def test_catalog_resolves_openai_http_through_the_port() -> None:
    from coa_runtime.errors import MissingConfigurationError
    from coa_runtime.registry import resolve
    from coa_runtime.settings import Settings

    resolution = resolve(
        "LLMClient",
        Settings(
            {
                "COA_PROVIDER_LLM": "openai-http",
                "COA_LLM_HTTP_BASE_URL": "http://127.0.0.1:1/v1",
                "COA_LLM_HTTP_MODEL": "test-model",
            }
        ),
    )
    try:
        assert resolution.provider == "openai-http"
        assert type(resolution.instance).__name__ == "OpenAICompatChat"
        assert resolution.instance.model_id == "test-model"
    finally:
        _run(resolution.instance.close())

    with pytest.raises(MissingConfigurationError) as excinfo:
        resolve(
            "LLMClient",
            Settings({"COA_PROVIDER_LLM": "openai-http", "COA_LLM_HTTP_MODEL": "m"}),
        )
    assert excinfo.value.key == "COA_LLM_HTTP_BASE_URL"


def test_unknown_guardrail_mode_fails_at_construction() -> None:
    with pytest.raises(ValueError):
        OpenAICompatChat(
            base_url="http://127.0.0.1:1/v1", model="m", guardrail_mode="maybe"
        )
