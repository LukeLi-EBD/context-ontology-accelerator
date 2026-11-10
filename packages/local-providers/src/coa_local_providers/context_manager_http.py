"""``local-http``: the :class:`ContextManagerPort` over a local context-manager.

The peer is the ``context-manager`` service. On AWS it is reached through
Bedrock AgentCore Runtime; locally the same entrypoint is served over plain
HTTP, so this provider speaks the AgentCore *transport contract*, not an AWS
API:

``POST {endpoint}/invocations``
    JSON envelope (the ``InvokeRequest`` payload the data layer already builds)::

        {"action": "translate" | "kbSearch" | "graphTraverse",   # omitted for Query
         "namespace": "<namespace id>",
         "query": "<text>",                                      # not used by graphTraverse
         "profile": {"userId": ..., "email": ..., "groups": [...], "globalRoles": [...]},
         "options": {...}}

    ``Authorization: Bearer <token>`` carries the caller's JWT; the peer decides
    what to do with it. The reply is ``text/event-stream`` with ``data: {json}``
    frames (AgentCore's async-generator shape) or a bare JSON object for a
    non-streaming peer. The first JSON object is the response; an in-band
    ``statusCode`` >= 400 is a peer-level rejection even though the HTTP status
    was 200.

``GET {endpoint}/ping``
    Health probe (AgentCore's built-in route). Any 2xx is healthy.

The two routes above are the whole surface this client needs. No AWS call is
made by the client itself; whether the peer can serve a request depends on the
peer's own dependencies (documented in ``doc/coa-x/`` and reported alongside
this provider).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import httpx

from coa_ports import ContextRequest, ContextResponse, PortError, PortErrorCode

# In-band error name -> the port's coarse code. The remote's own name stays in
# ``provider_code`` for diagnostics; callers must switch on ``code`` only.
_ERROR_CODES: Mapping[str, PortErrorCode] = {
    "AccessDeniedError": PortErrorCode.INVALID_ARGUMENT,
    "AmbiguousReferenceError": PortErrorCode.INVALID_ARGUMENT,
    "ValidationError": PortErrorCode.INVALID_ARGUMENT,
    "NamespaceNotFoundError": PortErrorCode.NOT_FOUND,
    "NoResultError": PortErrorCode.NOT_FOUND,
    "DataSourceUnavailableError": PortErrorCode.UNAVAILABLE,
    "TimeoutError": PortErrorCode.TIMEOUT,
    "QueryTranslationError": PortErrorCode.INTERNAL,
    "InternalError": PortErrorCode.INTERNAL,
    "E_SPARQL_SYNTAX": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_STATEMENT_NOT_ALLOWED": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_FEDERATED": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_DATASET_FORBIDDEN": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_GRAPH_FORBIDDEN": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_LOAD_NOT_ALLOWED": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_TOO_LONG": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_EMPTY": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_BAD_NAMESPACE": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_TIMEOUT": PortErrorCode.TIMEOUT,
    "E_SPARQL_PROVIDER_REJECTED": PortErrorCode.INVALID_ARGUMENT,
    "E_SPARQL_PROVIDER_ERROR": PortErrorCode.UNAVAILABLE,
    "E_SPARQL_SCOPE_TOO_LARGE": PortErrorCode.UNAVAILABLE,
    "E_SPARQL_SCOPE_EMPTY": PortErrorCode.UNAVAILABLE,
    "E_SPARQL_BACKEND_NOT_CONFIGURED": PortErrorCode.UNAVAILABLE,
    "E_SPARQL_INTERNAL": PortErrorCode.INTERNAL,
}


def _status_code(code: int) -> PortErrorCode:
    if code in (400, 401, 403, 422):
        return PortErrorCode.INVALID_ARGUMENT
    if code == 404:
        return PortErrorCode.NOT_FOUND
    if code in (408, 504):
        return PortErrorCode.TIMEOUT
    if code in (502, 503):
        return PortErrorCode.UNAVAILABLE
    return PortErrorCode.INTERNAL


def _first_json_frame(text: str) -> Any:
    """First complete JSON object in an SSE body, else the body parsed whole.

    Mirrors ``coa_data_layer.handler._parse_first_sse_event``: the data layer
    already reads AgentCore replies this way, so a local peer that emits the
    same frames gives identical results. Raises ``ValueError`` on malformed
    input.
    """
    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                frame = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            return frame
    return json.loads(text)


class LocalHttpContextManager:
    """``ContextManagerPort`` over a plain HTTP context-manager endpoint."""

    provider = "local-http"

    def __init__(
        self,
        *,
        endpoint: str,
        token: str = "",
        timeout_s: float = 30.0,
        invoke_path: str = "/invocations",
        ping_path: str = "/ping",
    ) -> None:
        if not endpoint:
            raise ValueError("local-http context manager requires an endpoint")
        if timeout_s <= 0:
            raise ValueError("local-http context manager requires a positive timeout")
        self.endpoint = endpoint.rstrip("/")
        self._token = token
        self._invoke_url = self.endpoint + invoke_path
        self._ping_url = self.endpoint + ping_path
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout_s))

    # ── the port ────────────────────────────────────────────────────────────

    async def invoke(self, request: ContextRequest) -> ContextResponse:
        payload: dict[str, Any] = {
            "namespace": str(request.namespace_id),
            "profile": _profile(request),
            "options": dict(request.options),
        }
        # The Query path is the peer's default when ``action`` is absent; the
        # other actions are selected by the camelCase names on the wire.
        action = str(request.action)
        if action != "query":
            payload["action"] = action
        if request.query:
            payload["query"] = request.query

        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        token = request.auth_token or self._token
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = await self._client.post(self._invoke_url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise PortError(
                PortErrorCode.TIMEOUT,
                f"context manager timed out: {type(exc).__name__}",
                provider=self.provider,
                provider_code=type(exc).__name__,
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                PortErrorCode.UNAVAILABLE,
                f"context manager unreachable: {type(exc).__name__}",
                provider=self.provider,
                provider_code=type(exc).__name__,
            ) from exc

        if response.status_code >= 400:
            raise _http_error(response)

        try:
            body = _first_json_frame(response.text)
        except ValueError as exc:
            raise PortError(
                PortErrorCode.INTERNAL,
                "context manager returned a body that is not JSON",
                provider=self.provider,
                provider_code="invalid_response",
            ) from exc
        if not isinstance(body, dict):
            raise PortError(
                PortErrorCode.INTERNAL,
                "context manager returned a JSON value that is not an object",
                provider=self.provider,
                provider_code="invalid_response",
            )

        status_code = body.get("statusCode", 200)
        if isinstance(status_code, int) and status_code >= 400:
            raise _in_band_error(body, status_code)

        return ContextResponse(
            body=body,
            request_id=body.get("requestId"),
            session_id=body.get("sessionId"),
        )

    async def health_check(self) -> Mapping[str, Any]:
        try:
            response = await self._client.get(self._ping_url)
            return {
                "ok": 200 <= response.status_code < 300,
                "provider": self.provider,
                "endpoint": self.endpoint,
                "status_code": response.status_code,
                "body": _safe_json(response.text),
            }
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "provider": self.provider,
                "endpoint": self.endpoint,
                "error": f"{type(exc).__name__}: {exc}",
            }

    async def aclose(self) -> None:
        await self._client.aclose()


def _profile(request: ContextRequest) -> dict[str, Any]:
    """Map the port's ``Principal`` to the peer's ``profile`` object."""
    principal = request.principal
    return {
        "userId": str(principal.principal_id),
        "email": principal.email,
        "groups": list(principal.groups),
        "globalRoles": list(principal.global_roles),
    }


def _safe_json(text: str) -> Any:
    try:
        return json.loads(text) if text else None
    except ValueError:
        return text[:200]


def _http_error(response: httpx.Response) -> PortError:
    detail = _safe_json(response.text)
    message = f"context manager rejected the request (HTTP {response.status_code})"
    provider_code = str(response.status_code)
    if isinstance(detail, dict):
        if isinstance(detail.get("message"), str) and detail["message"]:
            message = detail["message"]
        if isinstance(detail.get("error"), str):
            provider_code = detail["error"]
    return PortError(
        _status_code(response.status_code),
        message,
        provider=LocalHttpContextManager.provider,
        provider_code=provider_code,
    )


def _in_band_error(body: Mapping[str, Any], status_code: int) -> PortError:
    name = body.get("error")
    name = name if isinstance(name, str) else ""
    return PortError(
        _ERROR_CODES.get(name, PortErrorCode.INTERNAL),
        str(body.get("message") or f"context manager returned statusCode {status_code}"),
        provider=LocalHttpContextManager.provider,
        provider_code=name or str(status_code),
        details={
            "statusCode": status_code,
            "providerCode": body.get("providerCode"),
            "providerMessage": body.get("providerMessage"),
        },
    )


__all__ = ["LocalHttpContextManager"]
