"""COA ``LLMClient`` over the synchronized platform ``LlmClient``.

The platform adapter speaks one thing: ``complete_json(system, user) -> dict``.
The COA contract asks for four: ``converse``, ``converse_stream``, ``embed`` and
``health_check``. Two of them can be served honestly by a thin shell and two
cannot:

* ``converse`` — the platform call runs on :class:`SyncToAsyncShell`; the JSON
  body is returned as text, because that is the only thing the backend emits.
* ``health_check`` — a configuration snapshot taken through the same shell. It
  is not a live probe: the platform client has no health endpoint.
* ``converse_stream`` — **unsupported**. There is no streaming API underneath,
  and replaying a finished answer chunk-by-chunk would fake a stream.
* ``embed`` — **unsupported**. ``LlmClient`` has no embedding method; embeddings
  belong to ``EmbeddingPort`` and are served by a separate provider.

Unsupported capabilities raise ``PortError(UNSUPPORTED)`` instead of silently
degrading, so a caller that needs them fails where the cause is visible.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Mapping
from typing import Any

from coa_ports import PortError, PortErrorCode
from coa_serve.clients.base import ConverseResult

from .async_bridge import SyncToAsyncShell
from .errors import to_port_error


class PlatformLLMShell:
    """``LLMClient`` over a synchronous ``complete_json`` client."""

    backend = "openai-compatible"

    def __init__(
        self,
        client: Any,
        *,
        timeout_s: float = 60.0,
        max_workers: int = 4,
    ) -> None:
        self._client = client
        self._bridge = SyncToAsyncShell(
            provider=self.backend,
            max_workers=max_workers,
            timeout_s=timeout_s,
            thread_name_prefix="coa-llm",
        )

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
        """Return the platform's JSON answer as text.

        ``max_tokens`` is ignored: the platform configuration owns the limit.
        Every other knob the backend cannot honour raises ``UNSUPPORTED`` rather
        than being dropped, because a caller that asked for a guardrail or a
        specific model must not silently get neither.
        """
        unsupported = {
            name: value
            for name, value in (
                ("guardrail_id", guardrail_id),
                ("guard_content", guard_content),
                ("model_id", model_id),
                ("temperature", temperature),
                ("top_p", top_p),
            )
            if value is not None
        }
        if unsupported:
            raise PortError(
                PortErrorCode.UNSUPPORTED,
                "platform complete_json cannot honour: " + ", ".join(sorted(unsupported)),
                provider=self.backend,
                provider_code="E_LLM_KNOB_UNSUPPORTED",
                details={"knobs": sorted(unsupported)},
            )

        payload = await self._call(self._client.complete_json, system or "", prompt)
        return ConverseResult(text=json.dumps(payload, ensure_ascii=False, sort_keys=True))

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
        """Always ``UNSUPPORTED``; declared ``async`` so the error surfaces on iteration."""
        raise PortError(
            PortErrorCode.UNSUPPORTED,
            "platform LlmClient has no streaming API; converse_stream cannot be shelled",
            provider=self.backend,
            provider_code="E_LLM_STREAM_UNAVAILABLE",
        )
        yield  # pragma: no cover - unreachable, keeps this an async generator

    async def embed(self, text: str) -> list[float]:
        """Always ``UNSUPPORTED``; embeddings belong to ``EmbeddingPort``."""
        raise PortError(
            PortErrorCode.UNSUPPORTED,
            "embeddings are served by EmbeddingPort; platform LlmClient has no embed method",
            provider=self.backend,
            provider_code="E_LLM_EMBED_UNAVAILABLE",
        )

    async def health_check(self) -> dict[str, Any]:
        """Configuration snapshot, never raises. Not a live backend probe."""
        try:
            return await self._bridge.call(self._snapshot, timeout_s=min(5.0, self._bridge.timeout_s))
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {"ok": False, "backend": self.backend, "error": f"{type(exc).__name__}: {exc}"}

    async def close(self) -> None:
        self._bridge.close()
        close = getattr(self._client, "close", None)
        if callable(close):
            await asyncio.to_thread(close)

    def _snapshot(self) -> dict[str, Any]:
        configured = getattr(self._client, "configured", None)
        is_configured = bool(configured()) if callable(configured) else False
        config = getattr(self._client, "_config", None)
        return {
            "ok": is_configured,
            "backend": self.backend,
            "configured": is_configured,
            "model": getattr(config, "model", "") or "",
            "probe": "configuration-snapshot",
        }

    async def _call(self, fn: Any, *args: Any) -> Any:
        try:
            return await self._bridge.call(fn, *args)
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001 - platform failures become port errors
            raise to_port_error(exc, provider=self.backend, message="LLM call failed") from exc


__all__ = ["PlatformLLMShell"]
