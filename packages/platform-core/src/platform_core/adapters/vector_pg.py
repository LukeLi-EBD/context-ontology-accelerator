"""VectorStore adapter (S3): pgvector cosine/HNSW. No distance math in Python."""

from __future__ import annotations

import logging
from typing import Any, Sequence

from psycopg.types.json import Jsonb  # noqa: F401  (kept for parity with other adapters)

from ..config import EmbeddingConfig
from ..errors import PortError
from ..ports import Manifest
from .metadata_pg import MetadataPg

log = logging.getLogger(__name__)


def _literal(vector: Sequence[float]) -> str:
    return "[" + ",".join(f"{float(value):.7g}" for value in vector) + "]"


class PgVectorStore:
    port = "VectorStore"

    def __init__(self, metadata: MetadataPg, config: EmbeddingConfig) -> None:
        self._meta = metadata
        self._dimensions = config.dimensions

    def manifest(self) -> Manifest:
        pointer = self.pointer()
        return Manifest(
            provider="pgvector",
            port=self.port,
            provider_version="s3.2",
            capabilities=["vector.upsert", "vector.search", "vector.delete"],
            limits={
                "dimensions": pointer["dimensions"],
                "index": "hnsw-per-dimension",
            },
            notes={
                "slice": "S3",
                "metric": "cosine",
                "model_isolation": "(chunk_id, model) primary key",
                "partition": f"{pointer['provider']}:{pointer['model']}@{pointer['dimensions']}",
            },
        )

    # ---- active partition ------------------------------------------------

    def pointer(self) -> dict[str, Any]:
        """Return the active embedding partition (single-row pointer table)."""
        rows = self._meta.query(
            "SELECT provider, model, dimensions FROM platform.embedding_pointer WHERE id"
        )
        if not rows:
            return {"provider": "local-bge", "model": "BAAI/bge-m3", "dimensions": 1024}
        return {
            "provider": str(rows[0]["provider"]),
            "model": str(rows[0]["model"]),
            "dimensions": int(rows[0]["dimensions"]),
        }

    def set_pointer(self, provider: str, model: str, dimensions: int) -> dict[str, Any]:
        with self._meta.tx() as tx:
            tx.execute(
                """
                INSERT INTO platform.embedding_pointer (id, provider, model, dimensions)
                VALUES (true, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                   SET provider = EXCLUDED.provider,
                       model = EXCLUDED.model,
                       dimensions = EXCLUDED.dimensions,
                       updated_at = now()
                """,
                (provider, model, dimensions),
            )
        return self.pointer()

    def partitions(self) -> list[dict[str, Any]]:
        rows = self._meta.query(
            """
            SELECT model, dimensions, COUNT(*) AS n
              FROM platform.chunk_embedding
             GROUP BY model, dimensions
             ORDER BY model
            """
        )
        return [
            {"model": row["model"], "dimensions": int(row["dimensions"]), "chunks": int(row["n"])}
            for row in rows
        ]

    def _guard(self, model: str, dimensions: int, enforce_active: bool) -> None:
        if not enforce_active:
            return
        pointer = self.pointer()
        if model != pointer["model"]:
            raise PortError(
                code="InvalidArgument",
                message=(
                    f"embedding model mismatch: got {model}, "
                    f"active partition is {pointer['model']}"
                ),
                provider="pgvector",
                provider_code="E_EMBED_MODEL_MISMATCH",
                details={"got": model, "expected": pointer["model"]},
            )
        if dimensions != pointer["dimensions"]:
            raise PortError(
                code="InvalidArgument",
                message=(
                    f"embedding dimension mismatch: got {dimensions}, "
                    f"active partition expects {pointer['dimensions']}"
                ),
                provider="pgvector",
                provider_code="E_EMBED_DIM_MISMATCH",
                details={"got": dimensions, "expected": pointer["dimensions"]},
            )

    # ---- VectorStore v1 --------------------------------------------------

    def upsert(
        self,
        document_id: str,
        items: list[dict[str, Any]],
        model: str,
        enforce_active: bool = True,
    ) -> dict[str, Any]:
        if not items:
            return {"upserted": 0}
        dimensions = len(items[0]["vector"])
        for item in items:
            if len(item["vector"]) != dimensions:
                raise PortError(
                    code="InvalidArgument",
                    message=(
                        f"vector dimension mismatch for {item.get('chunkId')}: "
                        f"got {len(item['vector'])}, expected {dimensions}"
                    ),
                    provider="pgvector",
                    provider_code="E_EMBED_DIM_MISMATCH",
                    details={"chunkId": item.get("chunkId"), "got": len(item["vector"])},
                )
        self._guard(model, dimensions, enforce_active)

        with self._meta.tx() as tx:
            found = {
                row["chunk_id"]
                for row in tx.query(
                    "SELECT chunk_id FROM platform.document_chunk WHERE document_id = %s",
                    (document_id,),
                )
            }
            missing = [item["chunkId"] for item in items if item["chunkId"] not in found]
            if missing:
                raise PortError(
                    code="InvalidArgument",
                    message=(
                        f"{len(missing)} chunk(s) do not belong to document {document_id}"
                    ),
                    provider="pgvector",
                    provider_code="E_VECTOR_CHUNK_MISMATCH",
                    details={"documentId": document_id, "chunkIds": missing[:5]},
                )
            upserted = 0
            for item in items:
                tx.execute(
                    """
                    INSERT INTO platform.chunk_embedding (chunk_id, model, dimensions, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    ON CONFLICT (chunk_id, model) DO UPDATE
                       SET embedding = EXCLUDED.embedding,
                           dimensions = EXCLUDED.dimensions
                    """,
                    (item["chunkId"], model, dimensions, _literal(item["vector"])),
                )
                upserted += 1

        log.info(
            "vectors upserted",
            extra={
                "event": {
                    "event": "vector_upsert",
                    "documentId": document_id,
                    "model": model,
                    "count": upserted,
                }
            },
        )
        return {"upserted": upserted}

    def search(
        self, vector: Sequence[float], model: str, limit: int
    ) -> list[dict[str, Any]]:
        dimensions = len(vector)
        # Strong guard: a query never crosses into another model/dimension
        # partition, even if a caller passes a stale model name.
        self._guard(model, dimensions, True)
        # pgvector caps `vector` HNSW at 2000 dims (0.8.7), so wider partitions
        # are indexed and compared as halfvec. The expression must match V13.
        if dimensions <= 2000:
            expr = f"e.embedding::vector({dimensions})"
            qexpr = "q.v"
        else:
            expr = f"e.embedding::halfvec({dimensions})"
            qexpr = f"q.v::halfvec({dimensions})"
        rows = self._meta.query(
            f"""
            WITH q AS (SELECT %s::vector AS v)
            SELECT e.chunk_id, c.document_id, c.page_from, c.page_to, c.text,
                   1 - ({expr} <=> {qexpr}) AS score
              FROM platform.chunk_embedding e
              JOIN platform.document_chunk c ON c.chunk_id = e.chunk_id
              CROSS JOIN q
             WHERE e.model = %s AND e.dimensions = %s
             ORDER BY {expr} <=> {qexpr}
             LIMIT %s
            """,
            (_literal(vector), model, dimensions, limit),
        )
        return [
            {
                "chunkId": row["chunk_id"],
                "documentId": row["document_id"],
                "pageFrom": row["page_from"],
                "pageTo": row["page_to"],
                "text": row["text"],
                "score": float(row["score"]),
            }
            for row in rows
        ]

    def delete_document(self, document_id: str, model: str) -> dict[str, Any]:
        with self._meta.tx() as tx:
            deleted = tx.execute(
                """
                DELETE FROM platform.chunk_embedding e
                 USING platform.document_chunk c
                 WHERE e.chunk_id = c.chunk_id
                   AND c.document_id = %s
                   AND e.model = %s
                """,
                (document_id, model),
            )
        return {"deleted": deleted}

    def count(self, model: str | None = None) -> int:
        if model is None:
            rows = self._meta.query("SELECT COUNT(*) AS n FROM platform.chunk_embedding")
        else:
            rows = self._meta.query(
                "SELECT COUNT(*) AS n FROM platform.chunk_embedding WHERE model = %s",
                (model,),
            )
        return int(rows[0]["n"]) if rows else 0
