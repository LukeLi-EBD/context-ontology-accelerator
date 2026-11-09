"""``local-http`` ContextManagerPort, exercised against a real socket.

The peer below is a stdlib HTTP server on 127.0.0.1: it validates nothing and
answers no question — it only speaks the two transport routes, so the client is
proven over TCP rather than against a mock object.
"""

from __future__ import annotations

import asyncio
import json
import socket
import sys
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from coa_ports import (
    ContextAction,
    ContextRequest,
    NamespaceId,
    PortError,
    PortErrorCode,
    Principal,
)

from coa_local_providers.context_manager_http import LocalHttpContextManager

_PACKAGES = Path(__file__).resolve().parents[2]
_RUNTIME_SRC = str(_PACKAGES / "coa-runtime" / "src")
if _RUNTIME_SRC not in sys.path:
    sys.path.insert(0, _RUNTIME_SRC)


class FakeContextManagerPeer:
    """``GET /ping`` + ``POST /invocations`` (SSE) on a real ephemeral port."""

    def __init__(
        self,
        respond: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        *,
        http_status: int = 200,
    ) -> None:
        self.requests: list[dict[str, Any]] = []
        self.responses: list[str] = []
        self._respond = respond or self._echo
        self._http_status = http_status
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        peer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:  # noqa: N802 - http.server API
                peer.requests.append(
                    {
                        "method": "GET",
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                    }
                )
                if self.path == "/ping":
                    self._send_json(200, {"status": "Healthy"})
                else:
                    self._send_json(404, {"error": "not found"})

            def do_POST(self) -> None:  # noqa: N802 - http.server API
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length).decode("utf-8")
                try:
                    payload = json.loads(raw)
                except ValueError:
                    payload = {"__unparsed__": raw}
                peer.requests.append(
                    {
                        "method": "POST",
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                        "content_type": self.headers.get("Content-Type"),
                        "accept": self.headers.get("Accept"),
                        "raw": raw,
                        "payload": payload,
                    }
                )
                if self.path != "/invocations":
                    self._send_json(404, {"error": "not found"})
                    return
                if peer._http_status >= 400:
                    self._send_json(peer._http_status, {"message": "peer rejected"})
                    return
                self._send_sse(peer._respond(payload))

            def _send_sse(self, body: dict[str, Any]) -> None:
                text = "data: " + json.dumps(body, ensure_ascii=False) + "\n\n"
                peer.responses.append(text)
                data = text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

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
        return f"http://{host}:{port}"

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)

    @staticmethod
    def _echo(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "statusCode": 200,
            "requestId": "fake-request-1",
            "sessionId": "fake-session-1",
            "result": {
                "answer": f"peer received: {payload.get('query', '')}",
                "action": payload.get("action", "query"),
                "namespace": payload.get("namespace"),
            },
        }


async def _invoke_and_close(
    client: LocalHttpContextManager, request: ContextRequest
) -> Any:
    """One event loop for the call and the close: httpx pools bind to a loop."""
    try:
        return await client.invoke(request)
    finally:
        await client.aclose()


async def _health_and_close(client: LocalHttpContextManager) -> Any:
    try:
        return await client.health_check()
    finally:
        await client.aclose()


async def _invoke_error_then_health(
    client: LocalHttpContextManager, request: ContextRequest
) -> tuple[PortError, Any]:
    try:
        await client.invoke(request)
    except PortError as exc:
        return exc, await client.health_check()
    finally:
        await client.aclose()
    raise AssertionError("invoke did not raise")


def _request(
    action: ContextAction = ContextAction.TRANSLATE,
    *,
    query: str = "2024 年收入是多少",
    options: dict[str, Any] | None = None,
) -> ContextRequest:
    return ContextRequest(
        action=action,
        namespace_id=NamespaceId("ns-demo"),
        query=query,
        principal=Principal(
            principal_id="user-1",
            email="analyst@example.com",
            groups=("finance",),
            global_roles=("viewer",),
        ),
        auth_token="jwt-token-1",
        options=options or {},
    )


def test_invoke_round_trips_the_agentcore_envelope_over_tcp() -> None:
    peer = FakeContextManagerPeer()
    url = peer.start()
    client = LocalHttpContextManager(endpoint=url, token="configured-token")
    try:
        response = asyncio.run(_invoke_and_close(client, _request(options={"topK": 3})))
    finally:
        peer.stop()

    sent = peer.requests[0]
    assert sent["method"] == "POST"
    assert sent["path"] == "/invocations"
    assert sent["content_type"] == "application/json"
    # The per-request token wins over the configured default.
    assert sent["authorization"] == "Bearer jwt-token-1"
    assert sent["payload"] == {
        "action": "translate",
        "namespace": "ns-demo",
        "query": "2024 年收入是多少",
        "profile": {
            "userId": "user-1",
            "email": "analyst@example.com",
            "groups": ["finance"],
            "globalRoles": ["viewer"],
        },
        "options": {"topK": 3},
    }
    assert response.request_id == "fake-request-1"
    assert response.session_id == "fake-session-1"
    assert response.body["result"]["action"] == "translate"


def test_query_action_is_the_peer_default_and_omits_action() -> None:
    peer = FakeContextManagerPeer()
    url = peer.start()
    client = LocalHttpContextManager(endpoint=url)
    try:
        asyncio.run(_invoke_and_close(client, _request(ContextAction.QUERY)))
    finally:
        peer.stop()

    payload = peer.requests[0]["payload"]
    assert "action" not in payload
    assert payload["namespace"] == "ns-demo"


def test_in_band_error_status_becomes_a_port_error() -> None:
    peer = FakeContextManagerPeer(
        respond=lambda _payload: {
            "error": "NamespaceNotFoundError",
            "message": "Namespace 'ns-demo' not found",
            "requestId": "fake-request-2",
            "statusCode": 404,
        }
    )
    url = peer.start()
    client = LocalHttpContextManager(endpoint=url)
    try:
        with pytest.raises(PortError) as excinfo:
            asyncio.run(_invoke_and_close(client, _request(ContextAction.KB_SEARCH)))
    finally:
        peer.stop()

    assert excinfo.value.code is PortErrorCode.NOT_FOUND
    assert excinfo.value.provider_code == "NamespaceNotFoundError"
    assert excinfo.value.details == {"statusCode": 404}


def test_http_rejection_keeps_the_remote_message() -> None:
    peer = FakeContextManagerPeer(http_status=503)
    url = peer.start()
    client = LocalHttpContextManager(endpoint=url)
    try:
        with pytest.raises(PortError) as excinfo:
            asyncio.run(_invoke_and_close(client, _request()))
    finally:
        peer.stop()

    assert excinfo.value.code is PortErrorCode.UNAVAILABLE
    assert excinfo.value.message == "peer rejected"


def test_transport_failure_is_unavailable_and_health_check_never_raises() -> None:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()

    client = LocalHttpContextManager(endpoint=f"http://127.0.0.1:{port}")
    error, health = asyncio.run(_invoke_error_then_health(client, _request()))

    assert error.code is PortErrorCode.UNAVAILABLE
    assert health["ok"] is False
    assert health["provider"] == "local-http"


def test_health_check_reads_the_ping_route() -> None:
    peer = FakeContextManagerPeer()
    url = peer.start()
    client = LocalHttpContextManager(endpoint=url)
    try:
        health = asyncio.run(_health_and_close(client))
    finally:
        peer.stop()

    assert health["ok"] is True
    assert health["status_code"] == 200
    assert health["body"] == {"status": "Healthy"}
    assert peer.requests[0]["path"] == "/ping"


def test_catalog_resolves_local_http_through_the_port() -> None:
    from coa_ports import ContextManagerPort
    from coa_runtime.errors import MissingConfigurationError
    from coa_runtime.registry import resolve
    from coa_runtime.settings import Settings

    resolution = resolve(
        "ContextManagerPort",
        Settings(
            {
                "COA_PROVIDER_CONTEXT_MANAGER": "local-http",
                "COA_CONTEXT_MANAGER_ENDPOINT": "http://127.0.0.1:1",
            }
        ),
    )
    try:
        assert resolution.provider == "local-http"
        assert isinstance(resolution.instance, ContextManagerPort)
    finally:
        asyncio.run(resolution.instance.aclose())

    with pytest.raises(MissingConfigurationError) as excinfo:
        resolve(
            "ContextManagerPort",
            Settings({"COA_PROVIDER_CONTEXT_MANAGER": "local-http"}),
        )
    assert excinfo.value.key == "COA_CONTEXT_MANAGER_ENDPOINT"
