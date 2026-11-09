"""``openai-http``: a chat provider over any OpenAI-compatible endpoint.

One provider serves llama.cpp's server, Volcano Ark, and any other endpoint that
speaks ``POST {base_url}/chat/completions``. Unlike :class:`PlatformLLMShell`
(which wraps the platform's ``complete_json`` and therefore cannot stream or
honour sampling knobs), this provider talks the wire protocol directly:

* ``converse``        -> ``stream: false``, returns the assistant text;
* ``converse_stream`` -> ``stream: true``, yields ``choices[0].delta.content``
                          from each SSE frame as it arrives;
* ``model_id`` / ``temperature`` / ``top_p`` / ``max_tokens`` are placed in the
  request body unchanged — the endpoint decides what to do with them.

Two Bedrock-only concepts have no counterpart here:

* ``guardrail_id`` — there is no guardrail to invoke. Default behaviour is to
  raise ``UNSUPPORTED``; an operator who knowingly runs unguarded can opt into
  ``COA_LLM_HTTP_GUARDRAIL=ignore``, which logs a warning and proceeds.
* ``guard_content`` — a tag that says "evaluate only this text". Without a
  guardrail nothing is evaluated, but the text still has to reach the model
  (the Bedrock client sends it as an ordinary text block when no guardrail is
  configured). It is therefore appended to the user message and the loss of
  evaluation is logged once, never silently pretended.

``embed`` is not served here: embeddings belong to ``EmbeddingPort``.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Mapping
from typing import Any

import httpx
import structlog
from coa_ports import PortError, PortErrorCode

from .contracts import ConverseResult

logger = structlog.get_logger(__name__)

_GUARDRAIL_MODES = ("reject", "ignore")

# OpenAI finish reasons -> the COA vocabulary ConverseResult understands.
# ``length`` is what drives ConverseResult.truncated, so the mapping matters.
_STOP_REASONS = {
    "stop": "stop",
    "length": "max_tokens",
    "content_filter": "content_filtered",
    "tool_calls": "tool_calls",
}


class OpenAICompatChat:
    """``LLMClient`` over ``/v1/chat/completions`` (chat only, no embeddings)."""

    provider = "openai-http"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout_s: float = 120.0,
        stream_enabled: bool = True,
        guardrail_mode: str = "reject",
    ) -> None:
        if not base_url:
            raise ValueError("openai-http chat requires a base_url")
        if not model:
            raise ValueError("openai-http chat requires a model")
        if guardrail_mode not in _GUARDRAIL_MODES:
            raise ValueError(
                f"guardrail_mode must be one of {_GUARDRAIL_MODES}, got {guardrail_mode!r}"
            )
        if timeout_s <= 0:
            raise ValueError("openai-http chat requires a positive timeout_s")

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.stream_enabled = stream_enabled
        self.guardrail_mode = guardrail_mode
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._headers = headers
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s, connect=min(10.0, timeout_s))
        )
        self._guardrail_warned = False
        self._guard_content_warned = False

    @property
    def model_id(self) -> str:
        """Default model for ``converse``/``converse_stream`` when none is passed."""
        return self.model

    async def converse(
        self,
        prompt: str,
        *,
        system: str | None = None,
        guardrail_id: str | None = None,
        max_tokens: int = 4096,
        temperature: float | None = None,
        top_p: float | None = None,
        guard_content: str | None = None,
        model_id: str | None = None,
    ) -> ConverseResult:
        """One non-streaming completion; returns the assistant text."""
        payload = self._payload(
            prompt,
            system=system,
            guardrail_id=guardrail_id,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            guard_content=guard_content,
            model_id=model_id,
            stream=False,
        )
        data = await self._post_json(payload)
        choices = data.get("choices") or []
        if not choices or not isinstance(choices[0], Mapping):
            raise PortError(
                PortErrorCode.INTERNAL,
                "chat endpoint returned no choices",
                provider=self.provider,
                provider_code="E_LLM_HTTP_NO_CHOICES",
            )
        choice = choices[0]
        text = _content_text((choice.get("message") or {}).get("content"))
        if text is None:
            raise PortError(
                PortErrorCode.INTERNAL,
                "chat endpoint returned a choice without message content",
                provider=self.provider,
                provider_code="E_LLM_HTTP_NO_CONTENT",
            )
        finish = choice.get("finish_reason") or ""
        return ConverseResult(text=text, stop_reason=_STOP_REASONS.get(finish, finish))

    async def converse_stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        guardrail_id: str | None = None,
        max_tokens: int = 4096,
        guard_content: str | None = None,
        model_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Yield ``delta.content`` from each SSE frame until ``[DONE]``."""
        if not self.stream_enabled:
            raise PortError(
                PortErrorCode.UNSUPPORTED,
                "streaming is disabled for this provider (COA_LLM_HTTP_STREAM=0); "
                "use converse via the caller's fallback",
                provider=self.provider,
                provider_code="E_LLM_STREAM_DISABLED",
            )

        payload = self._payload(
            prompt,
            system=system,
            guardrail_id=guardrail_id,
            max_tokens=max_tokens,
            temperature=None,
            top_p=None,
            guard_content=guard_content,
            model_id=model_id,
            stream=True,
        )
        url = f"{self.base_url}/chat/completions"
        try:
            async with self._client.stream(
                "POST", url, json=payload, headers=self._headers
            ) as response:
                if response.status_code >= 400:
                    body = (await response.aread()).decode("utf-8", "replace")
                    raise self._status_error(response.status_code, body)
                async for line in response.aiter_lines():
                    data = _sse_data(line)
                    if data is None:
                        continue
                    if data == "[DONE]":
                        break
                    chunk = _parse_frame(data, provider=self.provider)
                    if chunk is None:
                        continue
                    delta = (chunk.get("choices") or [{}])[0].get("delta") or {}
                    text = delta.get("content")
                    if text:
                        yield text
        except (PortError, GeneratorExit):
            raise
        except httpx.TimeoutException as exc:
            raise PortError(
                PortErrorCode.TIMEOUT,
                f"chat endpoint {self.base_url} timed out mid-stream",
                provider=self.provider,
                provider_code="E_LLM_HTTP_TIMEOUT",
                details={"error": type(exc).__name__},
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                PortErrorCode.UNAVAILABLE,
                f"cannot reach chat endpoint {self.base_url}: {type(exc).__name__}",
                provider=self.provider,
                provider_code="E_LLM_HTTP_UNREACHABLE",
            ) from exc

    async def embed(self, text: str) -> list[float]:
        """Not served here; embeddings belong to ``EmbeddingPort``."""
        raise PortError(
            PortErrorCode.UNSUPPORTED,
            "openai-http chat does not embed; embeddings are served by EmbeddingPort",
            provider=self.provider,
            provider_code="E_LLM_EMBED_UNAVAILABLE",
        )

    async def health_check(self) -> dict[str, Any]:
        """GET ``{base_url}/models``; never raises."""
        try:
            response = await self._client.get(
                f"{self.base_url}/models", headers=self._headers
            )
            response.raise_for_status()
            payload = response.json()
            served = [
                item.get("id", "")
                for item in payload.get("data", [])
                if isinstance(item, Mapping)
            ]
            return {
                "ok": True,
                "provider": self.provider,
                "model": self.model,
                "endpoint": self.base_url,
                "served_models": served,
            }
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "provider": self.provider,
                "model": self.model,
                "endpoint": self.base_url,
                "error": f"{type(exc).__name__}: {exc}",
            }

    async def close(self) -> None:
        await self._client.aclose()

    # ── request building / transport ───────────────────────────────────────

    def _payload(
        self,
        prompt: str,
        *,
        system: str | None,
        guardrail_id: str | None,
        max_tokens: int,
        temperature: float | None,
        top_p: float | None,
        guard_content: str | None,
        model_id: str | None,
        stream: bool,
    ) -> dict[str, Any]:
        self._check_guardrail(guardrail_id, guard_content)
        user_text = _join_text(prompt, guard_content)
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_text})

        payload: dict[str, Any] = {
            "model": model_id or self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        # Only forward what the caller actually set: sending temperature=None or
        # 0-for-absent would override the endpoint's own defaults.
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        return payload

    def _check_guardrail(self, guardrail_id: str | None, guard_content: str | None) -> None:
        if guardrail_id:
            if self.guardrail_mode == "reject":
                raise PortError(
                    PortErrorCode.UNSUPPORTED,
                    "openai-http has no guardrail; guardrail_id cannot be honoured "
                    "(set COA_LLM_HTTP_GUARDRAIL=ignore to run unguarded on purpose)",
                    provider=self.provider,
                    provider_code="E_LLM_GUARDRAIL_UNSUPPORTED",
                    details={"guardrail_id": guardrail_id},
                )
            if not self._guardrail_warned:
                self._guardrail_warned = True
                logger.warning(
                    "llm_http_guardrail_bypassed",
                    provider=self.provider,
                    endpoint=self.base_url,
                    guardrail_id=guardrail_id,
                    msg="COA_LLM_HTTP_GUARDRAIL=ignore: content is NOT guardrail-evaluated",
                )
        if guard_content and not self._guard_content_warned:
            self._guard_content_warned = True
            logger.info(
                "llm_http_guard_content_unchecked",
                provider=self.provider,
                endpoint=self.base_url,
                msg="guard_content is sent as plain user text; no guardrail evaluates it",
            )

    async def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        try:
            response = await self._client.post(url, json=payload, headers=self._headers)
        except httpx.TimeoutException as exc:
            raise PortError(
                PortErrorCode.TIMEOUT,
                f"chat endpoint {self.base_url} timed out",
                provider=self.provider,
                provider_code="E_LLM_HTTP_TIMEOUT",
                details={"error": type(exc).__name__},
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                PortErrorCode.UNAVAILABLE,
                f"cannot reach chat endpoint {self.base_url}: {type(exc).__name__}",
                provider=self.provider,
                provider_code="E_LLM_HTTP_UNREACHABLE",
            ) from exc
        if response.status_code >= 400:
            raise self._status_error(response.status_code, response.text)
        try:
            data = response.json()
        except ValueError as exc:
            raise PortError(
                PortErrorCode.INTERNAL,
                "chat endpoint returned a non-JSON body",
                provider=self.provider,
                provider_code="E_LLM_HTTP_BAD_BODY",
            ) from exc
        if not isinstance(data, dict):
            raise PortError(
                PortErrorCode.INTERNAL,
                "chat endpoint returned a non-object JSON body",
                provider=self.provider,
                provider_code="E_LLM_HTTP_BAD_BODY",
            )
        return data

    def _status_error(self, status: int, body: str) -> PortError:
        if status in (401, 403):
            code, provider_code = PortErrorCode.UNAVAILABLE, "E_LLM_HTTP_AUTH"
            message = f"chat endpoint rejected the credentials (HTTP {status})"
        elif status == 404:
            code, provider_code = PortErrorCode.NOT_FOUND, "E_LLM_HTTP_NOT_FOUND"
            message = f"chat endpoint path not found (HTTP {status})"
        elif status == 429 or status >= 500:
            code, provider_code = PortErrorCode.UNAVAILABLE, "E_LLM_HTTP_UPSTREAM"
            message = f"chat endpoint unavailable (HTTP {status})"
        elif 400 <= status < 500:
            code, provider_code = PortErrorCode.INVALID_ARGUMENT, "E_LLM_HTTP_REJECTED"
            message = f"chat endpoint rejected the request (HTTP {status})"
        else:
            code, provider_code = PortErrorCode.INTERNAL, "E_LLM_HTTP_STATUS"
            message = f"chat endpoint returned HTTP {status}"
        # Body snippets help debugging but may echo request content; trim hard.
        return PortError(
            code,
            message,
            provider=self.provider,
            provider_code=provider_code,
            details={"status": status, "body": body[:500]},
        )


def _join_text(prompt: str, guard_content: str | None) -> str:
    """One user message: prompt, then guard_content, preserving both texts."""
    parts = [part for part in (prompt, guard_content) if part]
    return "\n\n".join(parts)


def _content_text(content: Any) -> str | None:
    """Extract assistant text from a string or content-parts array."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, Mapping) and isinstance(part.get("text"), str)
        )
    return None


def _sse_data(line: str) -> str | None:
    """The payload of one ``data:`` SSE line, or None for comments/blank lines."""
    if not line or line.startswith(":"):
        return None
    if not line.startswith("data:"):
        return None
    return line[5:].strip()


def _parse_frame(data: str, *, provider: str) -> dict[str, Any] | None:
    """Parse one JSON frame; malformed frames are skipped and logged.

    Some servers emit keep-alive frames that are not JSON. Skipping them keeps a
    valid stream alive; a genuinely broken response still fails at the HTTP
    layer or produces no text.
    """
    try:
        frame = json.loads(data)
    except ValueError:
        logger.debug("llm_http_sse_bad_frame", provider=provider, frame=data[:200])
        return None
    return frame if isinstance(frame, dict) else None


__all__ = ["OpenAICompatChat"]
