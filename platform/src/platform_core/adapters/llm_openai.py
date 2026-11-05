"""LlmClient adapter (S4): OpenAI-compatible chat completions with JSON output.

Boundary (D18): no prompt engineering pipeline or entity resolution here; the
service builds the prompt, this adapter only speaks HTTP and maps errors.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from ..config import LlmConfig
from ..errors import PortError
from ..ports import EnvSecretProvider, Manifest

log = logging.getLogger(__name__)


class LlmClient:
    port = "LLMClient"

    def __init__(self, config: LlmConfig, secrets: EnvSecretProvider) -> None:
        self._config = config
        self._secrets = secrets
        self._http: httpx.Client | None = None

    def manifest(self) -> Manifest:
        return Manifest(
            provider=self._config.provider,
            port=self.port,
            provider_version="s4.1",
            capabilities=[] if not self.configured() else ["llm.json"],
            limits={"timeout_ms": self._config.timeout_ms, "max_retries": self._config.max_retries},
            notes={
                "slice": "S4",
                "configured": self.configured(),
                "model": self._config.model,
                "base_url": self._config.base_url if self.configured() else None,
            },
        )

    def configured(self) -> bool:
        return bool(
            self._config.provider in ("openai-compatible", "ark")
            and self._config.base_url
            and self._config.model
        )

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(timeout=httpx.Timeout(self._config.timeout_ms / 1000.0))
        return self._http

    def _headers(self) -> dict[str, str]:
        # Contract key (04) wins, then the adapter-local default, then the
        # legacy single-provider variable. The value is never logged.
        for name in (self._config.api_key_env, "PLATFORM__LLM__API_KEY", "LLM_API_KEY"):
            try:
                key = self._secrets.get(name)
            except PortError:
                continue
            if key:
                return {"Authorization": f"Bearer {key}"}
        return {}

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        if self._config.provider == "disabled":
            raise PortError(
                code="Unsupported",
                message="llm.provider=disabled: no LLM client is assembled",
                provider="disabled",
                provider_code="E_LLM_NOT_CONFIGURED",
                details={"key": "llm.provider"},
            )
        if not self.configured():
            raise PortError(
                code="Unsupported",
                message="llm.base_url and llm.model are required for LLM extraction",
                provider="openai-compatible",
                provider_code="E_LLM_NOT_CONFIGURED",
                details={"key": "llm.base_url"},
            )

        attempts = self._config.max_retries + 1
        last: PortError | None = None
        for attempt in range(1, attempts + 1):
            try:
                return self._request(system, user)
            except PortError as exc:
                if exc.provider_code != "E_LLM_BAD_RESPONSE":
                    raise
                last = exc
                log.warning(
                    "llm response was not valid JSON",
                    extra={"event": {"event": "llm_bad_response", "attempt": attempt}},
                )
        assert last is not None
        raise last

    def _payload(self, system: str, user: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._config.model,
            "temperature": self._config.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if self._config.provider == "ark":
            # Verified 2026-11-05: Ark coding plan supports native tool calling,
            # so the JSON contract is enforced by a function call instead of
            # prompt-only formatting.
            # Ark rejects a schema without `properties`, so the tool mirrors
            # exactly what ExtractionService reads (triples[]).
            # Measured 2026-11-05 on deepseek-v4-1-flash-261017 (one 1.2k-char
            # Chinese chunk): 5.8s, 1540 completion tokens (629 reasoning),
            # finish_reason=tool_calls with a complete, parseable argument.
            # 8192 leaves headroom for reasoning plus 10 triples.
            payload["max_tokens"] = 8192
            payload["tools"] = [{
                "type": "function",
                "function": {
                    "name": "emit_json",
                    "description": "Return the extraction result as a JSON object",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "triples": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "subject": {"type": "string"},
                                        "predicate": {"type": "string"},
                                        "object": {"type": "string"},
                                        "objectKind": {
                                            "type": "string",
                                            "enum": ["iri", "literal"],
                                        },
                                    },
                                    "required": ["subject", "predicate", "object"],
                                },
                            }
                        },
                        "required": ["triples"],
                    },
                },
            }]
            # Ark rejects `tool_choice` as a forced-function object
            # (HTTP 400 InvalidParameter, measured 2026-11-05), so the tool is
            # offered with `auto` and the JSON contract is enforced by the
            # normal parse + one retry fallback (max_retries=1).
            payload["tool_choice"] = "auto"
        else:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _request(self, system: str, user: str) -> dict[str, Any]:
        url = f"{self._config.base_url.rstrip('/')}/chat/completions"
        payload = self._payload(system, user)
        try:
            response = self._client().post(url, json=payload, headers=self._headers())
        except httpx.TimeoutException as exc:
            raise PortError(
                code="DeadlineExceeded",
                message=f"llm request timed out after {self._config.timeout_ms} ms",
                provider="openai-compatible",
                provider_code="E_LLM_TIMEOUT",
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"cannot reach llm endpoint {self._config.base_url}: {exc}",
                provider="openai-compatible",
                provider_code="E_LLM_UNAVAILABLE",
                retryable=True,
            ) from exc

        if response.status_code in (401, 403):
            raise PortError(
                code="PermissionDenied",
                message=f"llm endpoint rejected credentials (HTTP {response.status_code})",
                provider="openai-compatible",
                provider_code="E_LLM_AUTH",
            )
        if response.status_code == 429:
            raise PortError(
                code="ResourceExhausted",
                message="llm endpoint rate-limited the request (HTTP 429)",
                provider="openai-compatible",
                provider_code="E_LLM_RATE",
                retryable=True,
            )
        if response.status_code >= 400:
            raise PortError(
                code="Unavailable",
                message=(
                    f"llm endpoint returned HTTP {response.status_code}: {response.text[:200]}"
                ),
                provider="openai-compatible",
                provider_code="E_LLM_UNAVAILABLE",
            )

        try:
            body = response.json()
            message = body["choices"][0]["message"]
            usage = body.get("usage") or {}
            log.info(
                "llm completion",
                extra={"event": {
                    "event": "llm_completion",
                    "provider": self._config.provider,
                    "model": self._config.model,
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "tool_call": bool(message.get("tool_calls")),
                }},
            )
            calls = message.get("tool_calls") or []
            if calls:
                content = calls[0]["function"]["arguments"]
            else:
                content = message["content"]
            parsed = json.loads(content) if isinstance(content, str) else content
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise PortError(
                code="DataLoss",
                message="llm endpoint returned a malformed chat completion",
                provider="openai-compatible",
                provider_code="E_LLM_BAD_RESPONSE",
                details={"body": response.text[:200]},
            ) from exc
        if not isinstance(parsed, dict):
            raise PortError(
                code="DataLoss",
                message="llm response JSON must be an object",
                provider="openai-compatible",
                provider_code="E_LLM_BAD_RESPONSE",
            )
        return parsed
