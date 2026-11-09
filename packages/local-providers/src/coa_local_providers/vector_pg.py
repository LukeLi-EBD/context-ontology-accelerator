"""COA ``VectorClient`` backed by platform_core's pgvector AD (PF-0021/PF-0022).

Reuses ``PgVectorStore.search`` (cosine, hnsw-per-dimension, model isolation)
and ``PgSearchIndex.search`` (FTS + pg_trgm) for the lexical half of
``hybrid_search``. The platform guards stay authoritative: a query never crosses
into another model/dimension partition, and the refusal carries both numbers.
"""

from __future__ import annotations

import asyncio
from typing import Any

from coa_serve.clients.base import StructuredBackend, VectorClient, VectorHit  # noqa: F401
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.search_pg import PgSearchIndex
from platform_core.adapters.vector_pg import PgVectorStore
from platform_core.config import EmbeddingConfig, SearchConfig
from platform_core.errors import PortError

from .embedding_base import EmbeddingDimensionMismatch, EmbeddingModelMismatch


class PgVectorClient:
    """``VectorClient`` over the platform pgvector partition."""

    backend = "pgvector"

    def __init__(
        self,
        dsn: str,
        *,
        model: str = "BAAI/bge-m3",
        dimensions: int = 1024,
        pool_max: int = 4,
        open_timeout_seconds: float = 10.0,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self._meta = MetadataPg(dsn, pool_max=pool_max)
        self._meta.open(retry_seconds=open_timeout_seconds)
        self._store = PgVectorStore(
            self._meta,
            EmbeddingConfig(
                provider="local-bge",
                model=model,
                dimensions=dimensions,
            ),
        )
        self._lexical = PgSearchIndex(self._meta, SearchConfig())

    async def search(
        self,
        query_vector: list[float],
        *,
        namespace: str = "",
        top_k: int = 5,
        index: str | None = None,
        entity_type: str | None = None,
        require_mapped: bool = False,
        ontology_ids: list[str] | None = None,
        query_backend: StructuredBackend | None = None,
    ) -> list[VectorHit]:
        try:
            rows = await asyncio.to_thread(
                self._store.search, query_vector, self.model, max(top_k, 0)
            )
        except PortError as exc:
            if exc.provider_code == "E_EMBED_DIM_MISMATCH":
                details = exc.details or {}
                raise EmbeddingDimensionMismatch(
                    provider=self.backend,
                    model=self.model,
                    expected=int(details.get("expected", self.dimensions)),
                    actual=int(details.get("got", len(query_vector))),
                ) from exc
            if exc.provider_code == "E_EMBED_MODEL_MISMATCH":
                details = exc.details or {}
                raise EmbeddingModelMismatch(
                    got=str(details.get("got", self.model)),
                    expected=str(details.get("expected", self.model)),
                ) from exc
            raise
        return [_hit(row, self.backend) for row in rows]

    async def hybrid_search(
        self,
        query_text: str,
        query_vector: list[float],
        *,
        namespace: str = "",
        top_k: int = 5,
        index: str | None = None,
    ) -> list[VectorHit]:
        """RRF (k=60) over the vector and lexical rankings, as platform SearchConfig does."""
        if top_k <= 0:
            return []
        candidate_k = max(top_k * 3, top_k)
        vector_rows, lexical_rows = await asyncio.gather(
            asyncio.to_thread(self._store.search, query_vector, self.model, candidate_k),
            asyncio.to_thread(self._lexical.search, query_text, candidate_k),
        )
        merged: dict[str, dict[str, Any]] = {}
        for rank, row in enumerate(vector_rows, start=1):
            item = merged.setdefault(row["chunkId"], {**row, "rrf": 0.0})
            item["rrf"] += 1.0 / (60 + rank)
        for rank, row in enumerate(lexical_rows, start=1):
            item = merged.setdefault(
                row["chunkId"],
                {**row, "score": 0.0, "rrf": 0.0},
            )
            item["rrf"] += 1.0 / (60 + rank)
        ordered = sorted(merged.values(), key=lambda row: (-row["rrf"], row["chunkId"]))
        return [_hit({**row, "score": row["rrf"]}, self.backend) for row in ordered[:top_k]]

    async def health_check(self) -> dict[str, Any]:
        """Report partition identity; never raises."""
        try:
            pointer = await asyncio.to_thread(self._store.pointer)
            partitions = await asyncio.to_thread(self._store.partitions)
            return {
                "ok": True,
                "backend": self.backend,
                "model": self.model,
                "dimensions": self.dimensions,
                "pointer": pointer,
                "partitions": partitions,
            }
        except Exception as exc:
            return {
                "ok": False,
                "backend": self.backend,
                "model": self.model,
                "dimensions": self.dimensions,
                "error": f"{type(exc).__name__}: {exc}",
            }

    async def close(self) -> None:
        await asyncio.to_thread(self._meta.close)


def _hit(row: dict[str, Any], backend: str) -> VectorHit:
    return VectorHit(
        id=str(row["chunkId"]),
        text=str(row.get("text", "")),
        score=max(0.0, min(1.0, float(row.get("score", 0.0)))),
        metadata={
            "documentId": row.get("documentId"),
            "pageFrom": row.get("pageFrom"),
            "pageTo": row.get("pageTo"),
            "backend": backend,
        },
    )


__all__ = ["PgVectorClient"]
