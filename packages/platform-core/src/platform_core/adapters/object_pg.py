"""Object bytes backend: PostgreSQL bytea (small-object tier, 07 section 3.2)."""

from __future__ import annotations

from typing import Any

from ..adapters.metadata_pg import MetadataPg


class PgByteaBackend:
    provider = "pg"

    def __init__(self, metadata: MetadataPg) -> None:
        self._metadata = metadata

    def write(self, tx: Any, hash_hex: str, data: bytes) -> None:
        tx.execute(
            "INSERT INTO platform.blob_bytea (hash, content) VALUES (%s, %s) "
            "ON CONFLICT (hash) DO NOTHING",
            (hash_hex, data),
        )

    def read(self, hash_hex: str) -> bytes | None:
        rows = self._metadata.query(
            "SELECT content FROM platform.blob_bytea WHERE hash = %s", (hash_hex,)
        )
        if not rows:
            return None
        return rows[0]["content"]

    def exists(self, hash_hex: str) -> bool:
        rows = self._metadata.query(
            "SELECT 1 AS one FROM platform.blob_bytea WHERE hash = %s", (hash_hex,)
        )
        return bool(rows)
