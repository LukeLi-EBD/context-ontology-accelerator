"""Local ``LLMClient`` implementation: llama.cpp GGUF inference, in-process.

Contract source: ``packages/context-manager/src/coa_serve/clients/base.py::LLMClient``
— ``converse`` / ``converse_stream`` / ``embed`` / ``health_check``.

Implemented for real: ``converse`` runs a chat completion on a local GGUF model
through ``llama-cpp-python`` (CPU, no server, no network port). Not implemented,
and deliberately not faked: ``converse_stream`` (this build has no token callback
plumbing) and ``embed`` (no embedding model ships). Both raise
:class:`LlmCapabilityUnsupported` instead of returning a shaped stub.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any


class LlmCapabilityUnsupported(NotImplementedError):
    """The local LLM backend cannot honour this contract method."""


class LlamaCppLLMClient:
    """``LLMClient`` backed by one GGUF file, loaded in-process."""

    backend = "llama-cpp"

    def __init__(
        self,
        model_path: str | Path,
        *,
        n_ctx: int = 2048,
        n_threads: int | None = None,
        n_batch: int = 512,
    ) -> None:
        self._model_path = Path(model_path)
        if not self._model_path.is_file():
            raise FileNotFoundError(f"GGUF model not found: {self._model_path}")
        self._n_ctx = n_ctx
        self._n_threads = n_threads
        self._n_batch = n_batch
        try:
            from llama_cpp import Llama
        except ImportError as exc:  # pragma: no cover - depends on local install
            raise RuntimeError(
                "llama-cpp-python is not installed; install the CPU wheel before "
                "selecting COA_PROVIDER_LLM=llama-cpp"
            ) from exc
        self._llm = Llama(
            model_path=str(self._model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_batch=n_batch,
            verbose=False,
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
    ) -> Any:
        """Run a real chat completion; returns the contract's ``ConverseResult``."""
        from coa_serve.clients.base import STOP_REASON_MAX_TOKENS, ConverseResult

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.8 if temperature is None else temperature,
        }
        if top_p is not None:
            kwargs["top_p"] = top_p
        payload = await asyncio.to_thread(self._llm.create_chat_completion, **kwargs)

        choice = payload["choices"][0]
        text = choice["message"]["content"] or ""
        finish_reason = choice.get("finish_reason")
        stop_reason = STOP_REASON_MAX_TOKENS if finish_reason == "length" else "end_turn"
        return ConverseResult(text=text, stop_reason=stop_reason)

    def converse_stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        guardrail_id: str | None = None,
        max_tokens: int = 4096,
        guard_content: str | None = None,
        model_id: str | None = None,
    ) -> Any:
        """Not implemented: no token callback plumbing in this build."""
        raise LlmCapabilityUnsupported(
            "converse_stream is not implemented by the local llama.cpp backend; "
            "use converse() and stream at the caller"
        )

    async def embed(self, text: str) -> list[float]:
        """Not implemented: this build ships no embedding model."""
        raise LlmCapabilityUnsupported(
            "embed is not implemented by the local llama.cpp backend; no embedding "
            "model is loaded, and returning a placeholder vector would be fake"
        )

    async def health_check(self) -> dict[str, Any]:
        try:
            size = self._model_path.stat().st_size
            return {
                "ok": True,
                "backend": self.backend,
                "model": self._model_path.name,
                "model_path": str(self._model_path),
                "model_bytes": size,
                "n_ctx": self._n_ctx,
                "n_threads": self._n_threads,
            }
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "backend": self.backend,
                "model_path": str(self._model_path),
                "error": f"{type(exc).__name__}: {exc}",
            }


__all__ = ["LlmCapabilityUnsupported", "LlamaCppLLMClient"]
