"""``bge-local``: platform_core's ``EmbeddingClient`` over a local BGE endpoint.

The platform adapter already owns batching, adaptive timeouts and the
single-flight gate. This module only adds the async COA-facing shape and the
dimension contract check.
"""

from __future__ import annotations

import asyncio
from typing import Any

from platform_core.adapters.embedding import EmbeddingClient
from platform_core.config import EmbeddingConfig
from platform_core.ports import EnvSecretProvider

from .embedding_base import check_dimensions


class BgeLocalEmbedding:
    """Local BGE-M3 (or any local OpenAI-compatible embedding server)."""

    provider = "bge-local"

    def __init__(
        self,
        endpoint: str = "http://embedding:80/v1",
        *,
        model: str = "BAAI/bge-m3",
        dimensions: int = 1024,
        timeout_ms: int = 30000,
        batch_size: int = 2,
        max_chunks_per_sec: float = 1.0,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self.endpoint = endpoint.rstrip("/")
        self._client = EmbeddingClient(
            EmbeddingConfig(
                provider="local-bge",
                model=model,
                dimensions=dimensions,
                endpoint=self.endpoint,
                timeout_ms=timeout_ms,
                batch_size=batch_size,
                batch_max=batch_size,
                max_chunks_per_sec=max_chunks_per_sec,
            ),
            EnvSecretProvider(),
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = await asyncio.to_thread(
            self._client.embed_with,
            "local-bge",
            self.model,
            list(texts),
            self.dimensions,
            False,  # interactive query: no indexing throttle
        )
        check_dimensions(
            provider=self.provider,
            model=self.model,
            expected=self.dimensions,
            vectors=vectors,
        )
        return vectors

    async def health_check(self) -> dict[str, Any]:
        """Probe the service identity; never raises."""
        try:
            info = await asyncio.to_thread(self._client.service_info)
            return {
                "ok": True,
                "provider": self.provider,
                "model": self.model,
                "dimensions": self.dimensions,
                "endpoint": self.endpoint,
                "service": info,
            }
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "provider": self.provider,
                "model": self.model,
                "dimensions": self.dimensions,
                "endpoint": self.endpoint,
                "error": f"{type(exc).__name__}: {exc}",
            }

    async def close(self) -> None:
        await asyncio.to_thread(self._client.close)


__all__ = ["BgeLocalEmbedding"]
