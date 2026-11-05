"""Reindex one embedding partition (S13b): rebuild, resume, then switch pointer.

Rules:
- The active partition is chosen by the single-row pointer, never by config.
- A rebuild writes into the target partition only, so the active partition keeps
  serving queries until the operator switches.
- The run is resumable: rows already present for the target model are skipped.
- Segments are bounded by batch_size and max_seconds so one invocation stays short.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .adapters.embedding import EmbeddingClient
from .adapters.metadata_pg import MetadataPg
from .adapters.vector_pg import PgVectorStore

log = logging.getLogger(__name__)

PENDING_SQL = """
SELECT c.chunk_id, c.document_id, c.seq, c.text
  FROM platform.document_chunk c
  LEFT JOIN platform.chunk_embedding e
         ON e.chunk_id = c.chunk_id AND e.model = %s
 WHERE e.chunk_id IS NULL
 ORDER BY c.document_id, c.seq
"""


class ReindexService:
    port = "ReindexService"

    def __init__(
        self,
        metadata: MetadataPg,
        embedding: EmbeddingClient,
        vectors: PgVectorStore,
    ) -> None:
        self._meta = metadata
        self._embedding = embedding
        self._vectors = vectors

    def run(
        self,
        provider: str,
        batch_size: int = 32,
        max_seconds: float = 180.0,
        activate_only: bool = False,
    ) -> dict[str, Any]:
        partition = self._embedding.partition(provider)
        model = partition["model"]
        dimensions = partition["dimensions"]

        if activate_only:
            pointer = self._vectors.set_pointer(provider, model, dimensions)
            return {
                "mode": "activate-only",
                "target": {"provider": provider, **partition},
                "pointer": pointer,
                "partitions": self._vectors.partitions(),
            }

        pending = self._meta.query(PENDING_SQL, (model,))
        total = len(pending)
        started = time.monotonic()
        processed = 0
        offset = 0
        size = max(1, int(batch_size))

        while offset < total:
            if max_seconds and (time.monotonic() - started) >= max_seconds:
                break
            batch = pending[offset : offset + size]
            by_document: dict[str, list[dict[str, Any]]] = {}
            for row in batch:
                by_document.setdefault(str(row["document_id"]), []).append(row)
            for document_id, rows in by_document.items():
                vectors = self._embedding.embed_with(
                    provider, model, [str(row["text"]) for row in rows], dimensions
                )
                self._vectors.upsert(
                    document_id,
                    [
                        {"chunkId": str(row["chunk_id"]), "vector": vector}
                        for row, vector in zip(rows, vectors)
                    ],
                    model,
                    enforce_active=False,
                )
                processed += len(rows)
            offset += len(batch)
            elapsed = time.monotonic() - started
            rate = processed / elapsed if elapsed > 0 else 0.0
            print(
                f"[reindex] {processed}/{total} chunks model={model} "
                f"rate={rate:.2f} chunks/s elapsed={elapsed:.0f}s",
                flush=True,
            )

        remaining = max(0, total - offset)
        activated = False
        pointer = self._vectors.pointer()
        if remaining == 0:
            pointer = self._vectors.set_pointer(provider, model, dimensions)
            activated = True

        elapsed = round(time.monotonic() - started, 2)
        summary = {
            "mode": "rebuild",
            "target": {"provider": provider, **partition},
            "totalChunks": total,
            "processedChunks": processed,
            "remainingChunks": remaining,
            "activated": activated,
            "pointer": pointer,
            "elapsedSeconds": elapsed,
            "batchSize": size,
            "maxSeconds": max_seconds,
            "partitions": self._vectors.partitions(),
        }
        log.info(
            "reindex finished",
            extra={"event": {"event": "reindex", **summary}},
        )
        return summary
