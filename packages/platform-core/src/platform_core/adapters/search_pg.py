"""SearchIndex adapter (S3): PostgreSQL FTS + pg_trgm. No ranking code in Python.

S16: the trigram predicate uses the indexable operator `q.raw <% c.text`
(word_similarity(q.raw, c.text) >= pg_trgm.word_similarity_threshold). The
threshold is set on the connection (see MetadataPg) to search.min_similarity;
using `word_similarity(...) >= x` in WHERE forced a 14k-row seq scan (~1.8 s).
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import SearchConfig
from ..ports import Manifest
from .metadata_pg import MetadataPg

log = logging.getLogger(__name__)


class PgSearchIndex:
    port = "SearchIndex"

    def __init__(self, metadata: MetadataPg, config: SearchConfig) -> None:
        self._meta = metadata
        self._config = config

    def manifest(self) -> Manifest:
        return Manifest(
            provider="postgres-fts",
            port=self.port,
            provider_version="s3.1",
            capabilities=["search.lexical"],
            limits={
                "parser": "simple",
                "trgm": "word_similarity",
                "min_similarity": self._config.min_similarity,
            },
            notes={
                "slice": "S3",
                "chinese": "`simple` has no word segmentation; pg_trgm covers substring match",
            },
        )

    def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        text = (query or "").strip()
        if not text:
            return []
        rows = self._meta.query(
            """
            WITH q AS (
                SELECT plainto_tsquery('simple', %(q)s) AS tsq, %(q)s::text AS raw
            )
            SELECT c.chunk_id, c.document_id, c.page_from, c.page_to, c.text,
                   ts_rank_cd(c.text_search, q.tsq) + word_similarity(q.raw, c.text) AS score
              FROM platform.document_chunk c
              CROSS JOIN q
             WHERE c.text_search @@ q.tsq
                OR q.raw <%% c.text
             ORDER BY score DESC, c.chunk_id
             LIMIT %(limit)s
            """,
            {"q": text, "limit": limit},
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
