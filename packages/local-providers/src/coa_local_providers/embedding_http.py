"""``external-http``: a configured OpenAI-compatible embedding endpoint.

Endpoint, model, API key and dimensions all come from configuration; nothing is
defaulted or discovered. A missing endpoint/model/key fails at construction with
the exact key name, never by falling back to another provider.
"""

from __future__ import annotations

from typing import Any

import httpx

from .embedding_base import check_dimensions


class ExternalHttpEmbedding:
    """OpenAI-compatible ``POST {endpoint}/embeddings``."""

    provider = "external-http"

    def __init__(
        self,
        *,
        endpoint: str,
        model: str,
        api_key: str,
        dimensions: int,
        timeout_s: float = 30.0,
    ) -> None:
        if not endpoint or not model or not api_key:
            raise ValueError("external-http embedding requires endpoint, model and api_key")
        if dimensions <= 0:
            raise ValueError("external-http embedding requires a positive dimensions value")
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.dimensions = dimensions
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout_s))
        self._headers = {"Authorization": f"Bearer {api_key}"}

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.post(
            f"{self.endpoint}/embeddings",
            json={"model": self.model, "input": list(texts)},
            headers=self._headers,
        )
        response.raise_for_status()
        payload = response.json()
        vectors = [item["embedding"] for item in payload["data"]]
        check_dimensions(
            provider=self.provider,
            model=self.model,
            expected=self.dimensions,
            vectors=vectors,
        )
        return vectors

    async def health_check(self) -> dict[str, Any]:
        """Functional probe: one tiny embed, dimension-checked; never raises."""
        try:
            vectors = await self.embed(["health"])
            return {
                "ok": True,
                "provider": self.provider,
                "model": self.model,
                "dimensions": self.dimensions,
                "returned_dimensions": len(vectors[0]),
                "endpoint": self.endpoint,
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
        await self._client.aclose()


__all__ = ["ExternalHttpEmbedding"]
