"""SearchService (S3): orchestration of embedding -> vector search + lexical search -> RRF.

Boundary (D18/D19): similarity scores and ranks come from PostgreSQL/pgvector; the
only formula here is the fixed RRF `sum(1 / (k + rank))` with k=60 (03 D19).
Embedding/lexical failures degrade explicitly instead of returning silent partials.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
from collections import OrderedDict
from typing import Any, Literal

from .adapters.embedding import EmbeddingClient
from .adapters.metadata_pg import MetadataPg
from .adapters.search_pg import PgSearchIndex
from .adapters.vector_pg import PgVectorStore
from .config import SearchConfig
from .errors import PortError
from .ports import Manifest

log = logging.getLogger(__name__)

Mode = Literal["hybrid", "vector", "lexical"]
_CJK = re.compile(r"[\u4e00-\u9fff]")


def _has_cjk(text: str) -> bool:
    return bool(_CJK.search(text))


class SearchService:
    port = "SearchService"

    def __init__(
        self,
        config: SearchConfig,
        metadata: MetadataPg,
        embedding: EmbeddingClient,
        vectors: PgVectorStore,
        index: PgSearchIndex,
    ) -> None:
        self._config = config
        self._meta = metadata
        self._embedding = embedding
        self._vectors = vectors
        self._index = index
        # S16: query-string embedding cache. The pointer/model/dimension tuple is
        # part of the key so a partition switch never serves a stale vector.
        self._query_cache: OrderedDict[tuple[str, str, int, str], list[float]] = OrderedDict()
        self._cache_lock = threading.Lock()
        self._cache_hits = 0
        self._cache_misses = 0

    def manifest(self) -> Manifest:
        return Manifest(
            provider="pg+embedding",
            port=self.port,
            provider_version="s3.1",
            capabilities=["search.hybrid", "search.vector", "search.lexical", "index.document"],
            limits={
                "top_k": self._config.top_k,
                "candidate_k": self._config.candidate_k,
                "rrf_k": self._config.rrf_k,
                "dimensions": self._embedding.dimensions(),
            },
            notes={
                "slice": "S3",
                "model": self._embedding.model_name(),
                "fusion": "rrf",
                "degrade": "embedding unavailable -> lexical only + degraded",
            },
        )

    # ---- indexing --------------------------------------------------------

    def index_document(self, document_id: str, max_batches: int | None = None) -> dict[str, Any]:
        """Embed one document in bounded, resumable batches (S14H-17).

        - normal docs commit every 50 chunks; >500-chunk docs use batches of 100
        - checkpoint {lastOrdinal, embedded} lands in document.manifest after each
          commit; a rerun skips chunks that already have a vector for this model
        - timeouts are retried inside EmbeddingClient (2x backoff); a batch that
          still fails is recorded, the rest continue, and the document is marked
          degraded with failureCode so callers never report "indexed with 0 vectors"
        - max_batches pauses between batches and returns paused=true + checkpoint
        """
        started = time.monotonic()
        self._document(document_id)
        chunks = self._meta.query(
            """
            SELECT chunk_id, seq, text
              FROM platform.document_chunk
             WHERE document_id = %s
             ORDER BY seq
            """,
            (document_id,),
        )
        partition = self._vectors.pointer()
        model = partition["model"]
        dimensions = partition["dimensions"]

        done = {
            row["chunk_id"]
            for row in self._meta.query(
                """
                SELECT e.chunk_id FROM platform.chunk_embedding e
                  JOIN platform.document_chunk c ON c.chunk_id = e.chunk_id
                 WHERE c.document_id = %s AND e.model = %s
                """,
                (document_id, model),
            )
        }
        pending = [chunk for chunk in chunks if chunk["chunk_id"] not in done]

        # Content-hash duplicate audit (verification only; chunk_id is the key).
        duplicates = 0
        seen: set[str] = set()
        for chunk in chunks:
            digest = hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()
            if digest in seen:
                duplicates += 1
            seen.add(digest)

        batch_size = (
            self._config.large_doc_batch_chunks
            if len(chunks) > self._config.large_doc_chunks
            else self._config.index_commit_chunks
        )
        reasons: list[str] = []
        embedded_this_run = 0
        batches = 0
        paused = False
        # S14H-CORES: phase accounting so a throughput run can be split into
        # TEI service time, gate wait, and platform-side overhead.
        prep_ms = (time.monotonic() - started) * 1000.0
        embed_ms = 0.0
        upsert_ms = 0.0
        checkpoint_ms = 0.0
        if pending and max_batches is not None and max_batches <= 0:
            paused = True
            pending = []
        for start in range(0, len(pending), batch_size):
            if max_batches is not None and batches >= max_batches:
                paused = True
                break
            batch = pending[start : start + batch_size]
            try:
                embed_started = time.monotonic()
                vectors = self._embedding.embed_with(
                    partition["provider"], model, [chunk["text"] for chunk in batch], dimensions
                )
                embed_ms += (time.monotonic() - embed_started) * 1000.0
                upsert_started = time.monotonic()
                result = self._vectors.upsert(
                    document_id,
                    [
                        {"chunkId": chunk["chunk_id"], "vector": vector}
                        for chunk, vector in zip(batch, vectors)
                    ],
                    model,
                )
                upsert_ms += (time.monotonic() - upsert_started) * 1000.0
            except PortError as exc:
                if exc.code in ("InvalidArgument", "DataLoss", "PermissionDenied"):
                    raise
                reasons.append(exc.provider_code or exc.code)
                batches += 1
                log.warning(
                    "embed batch failed after retries",
                    extra={
                        "event": {
                            "event": "embed_batch_failed",
                            "documentId": document_id,
                            "code": exc.provider_code,
                            "from": int(batch[0]["seq"]),
                            "to": int(batch[-1]["seq"]),
                        }
                    },
                )
                continue
            embedded_this_run += int(result["upserted"])
            batches += 1
            checkpoint_started = time.monotonic()
            total = self._count_embeddings(document_id, model)
            self._write_checkpoint(document_id, model, int(batch[-1]["seq"]), total)
            checkpoint_ms += (time.monotonic() - checkpoint_started) * 1000.0
            log.info(
                "embed checkpoint",
                extra={
                    "event": {
                        "event": "embed_checkpoint",
                        "documentId": document_id,
                        "lastOrdinal": int(batch[-1]["seq"]),
                        "embedded": total,
                        "batches": batches,
                    }
                },
            )

        total_embedded = self._count_embeddings(document_id, model)
        remaining = len(chunks) - total_embedded
        # An explicit pause (max_batches) is not a failure: only report degraded
        # when vectors are missing without being paused, or a batch really failed.
        degraded = (remaining > 0 and not paused) or bool(reasons)
        failure_code = None
        if degraded:
            failure_code = reasons[0] if reasons else "E_EMBED_INCOMPLETE"
            self._mark_embed_degraded(document_id, failure_code, total_embedded, len(chunks), reasons)
        else:
            # Recover a document that an earlier paused/failed run left degraded;
            # documents degraded at parse time have no manifest.embed key.
            self._meta.execute(
                """
                UPDATE platform.document
                   SET status = 'parsed',
                       manifest = jsonb_set(
                           COALESCE(manifest, '{}'::jsonb), '{embed}', %s::jsonb)
                 WHERE document_id = %s
                   AND status = 'degraded'
                   AND manifest ? 'embed'
                """,
                (
                    json.dumps(
                        {
                            "degraded": False,
                            "embedded": int(total_embedded),
                            "chunks": len(chunks),
                            "reasons": [],
                        }
                    ),
                    document_id,
                ),
            )
        checkpoint = self._checkpoint(document_id)
        result = {
            "documentId": document_id,
            "chunks": len(chunks),
            "lexical": len(chunks),
            "embedded": total_embedded,
            "embeddedThisRun": embedded_this_run,
            "model": model,
            "dimensions": dimensions,
            "batchSize": batch_size,
            "batches": batches,
            "paused": paused,
            "remaining": remaining,
            "checkpoint": checkpoint,
            "contentHashDuplicates": duplicates,
            "degraded": degraded,
            "failureCode": failure_code,
            "reasons": reasons,
            "timingMs": {
                "prep": round(prep_ms, 3),
                "embed": round(embed_ms, 3),
                "upsert": round(upsert_ms, 3),
                "checkpoint": round(checkpoint_ms, 3),
                "total": round((time.monotonic() - started) * 1000.0, 3),
            },
        }
        log.info(
            "document indexed",
            extra={"event": {"event": "index_document", **result}},
        )
        return result

    def _count_embeddings(self, document_id: str, model: str) -> int:
        rows = self._meta.query(
            """
            SELECT COUNT(*) AS n FROM platform.chunk_embedding e
              JOIN platform.document_chunk c ON c.chunk_id = e.chunk_id
             WHERE c.document_id = %s AND e.model = %s
            """,
            (document_id, model),
        )
        return int(rows[0]["n"]) if rows else 0

    def _checkpoint(self, document_id: str) -> dict[str, Any]:
        rows = self._meta.query(
            "SELECT manifest FROM platform.document WHERE document_id = %s", (document_id,)
        )
        data = (rows[0]["manifest"] or {}) if rows else {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                data = {}
        return dict(data.get("embedCheckpoint") or {})

    def _write_checkpoint(
        self, document_id: str, model: str, last_ordinal: int, embedded: int
    ) -> None:
        payload = json.dumps(
            {"model": model, "lastOrdinal": int(last_ordinal), "embedded": int(embedded)}
        )
        self._meta.execute(
            """
            UPDATE platform.document
               SET manifest = jsonb_set(
                       COALESCE(manifest, '{}'::jsonb), '{embedCheckpoint}', %s::jsonb)
             WHERE document_id = %s
            """,
            (payload, document_id),
        )

    def _mark_embed_degraded(
        self,
        document_id: str,
        failure_code: str,
        embedded: int,
        chunks: int,
        reasons: list[str],
    ) -> None:
        payload = json.dumps(
            {
                "degraded": True,
                "failureCode": failure_code,
                "embedded": int(embedded),
                "chunks": int(chunks),
                "reasons": reasons,
            }
        )
        self._meta.execute(
            """
            UPDATE platform.document
               SET status = 'degraded',
                   manifest = jsonb_set(
                       COALESCE(manifest, '{}'::jsonb), '{embed}', %s::jsonb)
             WHERE document_id = %s
            """,
            (payload, document_id),
        )

    def index_all(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        documents = self._meta.query(
            """
            SELECT document_id
              FROM platform.document
             ORDER BY created_at, document_id
             LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        totals = {
            "documents": 0,
            "chunks": 0,
            "embedded": 0,
            "degraded": 0,
            "reasons": [],
        }
        for row in documents:
            result = self.index_document(row["document_id"])
            totals["documents"] += 1
            totals["chunks"] += result["chunks"]
            totals["embedded"] += result["embedded"]
            totals["degraded"] += 1 if result["degraded"] else 0
            for reason in result["reasons"]:
                if reason not in totals["reasons"]:
                    totals["reasons"].append(reason)
        return totals

    # ---- search ----------------------------------------------------------

    def _merge_lexical(
        self, text: str, extra: list[str], candidates: int
    ) -> list[dict[str, Any]]:
        """Merge term aliases into the single lexical route without demoting the query.

        The original query stays authoritative: its rows keep their ranks and any
        alias-only row is appended strictly below them (a short alias such as
        "帐户" matches far more chunks and would otherwise displace the gold
        chunk). Aliases therefore only add recall when the query itself left
        slots empty; they never change the top of the list.
        """
        base = self._index.search(text, candidates)
        merged: dict[str, dict[str, Any]] = {row["chunkId"]: row for row in base}
        room = max(0, candidates - len(base))
        if extra and room:
            tail: dict[str, dict[str, Any]] = {}
            for candidate in extra:
                for row in self._index.search(candidate, room + len(base)):
                    if row["chunkId"] in merged:
                        continue
                    current = tail.get(row["chunkId"])
                    if current is None or row["score"] > current["score"]:
                        tail[row["chunkId"]] = row
            ordered = sorted(
                tail.values(), key=lambda item: (-item["score"], item["chunkId"])
            )
            floor = min((row["score"] for row in base), default=0.0)
            gap = max(abs(floor), 1.0) * 1e-6
            for offset, row in enumerate(ordered[:room]):
                merged[row["chunkId"]] = {**row, "score": floor - gap * (offset + 1)}
        ranked = sorted(merged.values(), key=lambda item: (-item["score"], item["chunkId"]))
        return ranked[:candidates]

    def hybrid_search(
        self,
        query: str,
        limit: int | None = None,
        mode: Mode = "hybrid",
        expansions: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self._config.enabled:
            raise PortError(
                code="Unsupported",
                message="search.enabled=false: hybrid search is disabled",
                provider="platform",
                provider_code="E_SEARCH_DISABLED",
                details={"key": "search.enabled"},
            )
        text = (query or "").strip()
        if not text:
            raise PortError(
                code="InvalidArgument",
                message="search query must not be empty",
                provider="platform",
                provider_code="E_SEARCH_QUERY_EMPTY",
            )
        top_k = self._config.top_k if limit is None else max(1, min(limit, 100))
        candidates = max(self._config.candidate_k, top_k)

        routes: list[str] = []
        reasons: list[str] = []
        vector_list: list[dict[str, Any]] = []
        lexical_list: list[dict[str, Any]] = []
        cache_hit = False
        pointer_ms = embed_ms = vector_ms = lexical_ms = rrf_ms = 0.0
        total_started = time.monotonic()

        if mode in ("hybrid", "vector"):
            try:
                pointer_started = time.monotonic()
                partition = self._vectors.pointer()
                pointer_ms = (time.monotonic() - pointer_started) * 1000.0
                embed_started = time.monotonic()
                vector, cache_hit = self._embed_query(
                    partition["provider"], partition["model"],
                    partition["dimensions"], text,
                )
                embed_ms = (time.monotonic() - embed_started) * 1000.0
                vector_started = time.monotonic()
                vector_list = self._vectors.search(
                    vector, partition["model"], candidates
                )
                vector_ms = (time.monotonic() - vector_started) * 1000.0
                routes.append("vector")
                if not vector_list:
                    reasons.append("E_NO_VECTOR_INDEX")
            except PortError as exc:
                if mode == "vector":
                    raise
                reasons.append(exc.provider_code or exc.code)
                log.warning(
                    "search degraded: vector route unavailable",
                    extra={"event": {"event": "search_degraded", "code": exc.provider_code}},
                )

        if mode in ("hybrid", "lexical"):
            extra: list[str] = []
            if self._config.lexical_expand and expansions:
                for item in expansions:
                    item = (item or "").strip()
                    if item and item != text and item not in extra:
                        extra.append(item)
                # S16: non-CJK synonyms (e.g. "Account") match ~70% of the Chinese
                # corpus at the 0.1 trigram threshold, costing seconds for rows that
                # are floored below the base route anyway. Drop them for CJK queries.
                if _has_cjk(text):
                    extra = [item for item in extra if _has_cjk(item)]
                extra = extra[: max(0, self._config.lexical_expand_max - 1)]
            # T2: each alias string is its own lexical query; a chunk keeps its
            # best score. Still exactly one lexical route into RRF below.
            lexical_started = time.monotonic()
            lexical_list = self._merge_lexical(text, extra, candidates)
            lexical_ms = (time.monotonic() - lexical_started) * 1000.0
            routes.append("lexical")

        rrf_started = time.monotonic()
        fused = self._rrf(
            [vector_list, lexical_list],
            k=self._config.rrf_k,
            limit=top_k,
        )
        rrf_ms = (time.monotonic() - rrf_started) * 1000.0
        # S14H-17: explicit flag instead of a silent lexical fallback (hybrid/vector only).
        lexical_only = mode != "lexical" and "vector" not in routes
        if lexical_only and "lexicalOnly" not in reasons:
            # UI renders reasons as badges, so the flag is visible without JS changes.
            reasons.append("lexicalOnly")
        result = {
            "query": text,
            "mode": mode,
            "rrfK": self._config.rrf_k,
            "routes": routes,
            "lexicalOnly": lexical_only,
            "degraded": bool(reasons) or lexical_only,
            "reasons": reasons,
            "results": fused,
            "timingMs": {
                "pointer": round(pointer_ms, 3),
                "embed": round(embed_ms, 3),
                "vector": round(vector_ms, 3),
                "lexical": round(lexical_ms, 3),
                "rrf": round(rrf_ms, 3),
                "total": round((time.monotonic() - total_started) * 1000.0, 3),
            },
            "embeddingCache": {**self.cache_stats(), "hit": cache_hit},
        }
        log.info(
            "search",
            extra={
                "event": {
                    "event": "search",
                    "mode": mode,
                    "routes": routes,
                    "hits": len(fused),
                    "degraded": bool(reasons),
                }
            },
        )
        return result

    # ---- helpers ---------------------------------------------------------

    def _embed_query(
        self, provider: str, model: str, dimensions: int, text: str
    ) -> tuple[list[float], bool]:
        """Return the query vector, reusing the LRU cache when available.

        Only the query string is cached (interactive, repeated across turns);
        document chunks are never served from here. Returns (vector, cacheHit).
        """
        key = (provider, model, dimensions, text)
        capacity = self._config.query_embedding_cache_size
        if capacity > 0:
            with self._cache_lock:
                cached = self._query_cache.get(key)
                if cached is not None:
                    self._query_cache.move_to_end(key)
                    self._cache_hits += 1
                    return cached, True
        with self._cache_lock:
            self._cache_misses += 1
        # Interactive path: no indexing throttle (see EmbeddingClient.embed_with).
        vector = self._embedding.embed_with(
            provider, model, [text], dimensions, rate_limit=False
        )[0]
        if capacity > 0:
            with self._cache_lock:
                self._query_cache[key] = vector
                self._query_cache.move_to_end(key)
                while len(self._query_cache) > capacity:
                    self._query_cache.popitem(last=False)
        return vector, False

    def cache_stats(self) -> dict[str, Any]:
        with self._cache_lock:
            hits = self._cache_hits
            misses = self._cache_misses
            entries = len(self._query_cache)
        total = hits + misses
        return {
            "hits": hits,
            "misses": misses,
            "entries": entries,
            "hitRate": round(hits / total, 4) if total else 0.0,
            "capacity": self._config.query_embedding_cache_size,
        }

    def counts(self) -> dict[str, Any]:
        rows = self._meta.query(
            """
            SELECT COUNT(*) AS chunks,
                   (SELECT COUNT(*) FROM platform.chunk_embedding) AS embeddings
              FROM platform.document_chunk
            """
        )
        models = self._meta.query(
            """
            SELECT model, COUNT(*) AS n
              FROM platform.chunk_embedding
             GROUP BY model
             ORDER BY model
            """
        )
        base = rows[0] if rows else {"chunks": 0, "embeddings": 0}
        pointer = self._vectors.pointer()
        return {
            "chunks": int(base["chunks"]),
            "embeddings": int(base["embeddings"]),
            "models": {row["model"]: int(row["n"]) for row in models},
            "activeModel": pointer["model"],
            "activeDimensions": pointer["dimensions"],
            "activeProvider": pointer["provider"],
            "partitions": self._vectors.partitions(),
            "available": self._embedding.available(),
            "queryCache": self.cache_stats(),
        }

    def _document(self, document_id: str) -> dict[str, Any]:
        rows = self._meta.query(
            "SELECT document_id FROM platform.document WHERE document_id = %s",
            (document_id,),
        )
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"document not found: {document_id}",
                provider="postgres",
                provider_code="E_DOC_NOT_FOUND",
            )
        return rows[0]

    @staticmethod
    def _rrf(
        lists: list[list[dict[str, Any]]],
        k: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Fixed reciprocal-rank fusion: sum(1 / (k + rank)); ties by chunk_id."""
        fused: dict[str, dict[str, Any]] = {}
        for route_name, items in zip(("vector", "lexical"), lists):
            for rank, item in enumerate(items, start=1):
                entry = fused.get(item["chunkId"])
                if entry is None:
                    entry = {
                        "chunkId": item["chunkId"],
                        "documentId": item["documentId"],
                        "pageFrom": item["pageFrom"],
                        "pageTo": item["pageTo"],
                        "text": item["text"],
                        "score": 0.0,
                        "ranks": {},
                        "scores": {},
                    }
                    fused[item["chunkId"]] = entry
                entry["score"] += 1.0 / (k + rank)
                entry["ranks"][route_name] = rank
                entry["scores"][route_name] = round(float(item["score"]), 6)
                if len(item["text"]) > len(entry["text"]):
                    entry["text"] = item["text"]
        results = sorted(fused.values(), key=lambda item: (-item["score"], item["chunkId"]))
        for item in results:
            item["score"] = round(item["score"], 6)
        return results[:limit]
