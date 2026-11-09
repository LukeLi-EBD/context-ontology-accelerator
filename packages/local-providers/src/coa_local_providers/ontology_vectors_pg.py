# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""``VectorStore`` on PostgreSQL + pgvector (local) instead of OpenSearch.

``coa_ontology.stores.opensearch_vector.OpenSearchVectorStore`` is the AWS
implementation: AOSS collection per namespace, ``cosinesimil`` k-NN, append-only
documents. Locally the same ``VectorStore`` protocol is served by
``public.coa_ontology_embeddings`` with an HNSW cosine index. The document
schema mirrors the OpenSearch one field for field, so callers (ingest, proposal
accept, readiness wait) are unchanged.

Configuration (fails closed):

    COA_PROVIDER_ONTOLOGY_VECTOR   pgvector | opensearch   (required)
    COA_CONTROL_PLANE_PG_DSN       PostgreSQL DSN          (required for pgvector)
    COA_VECTOR_DIMENSIONS          embedding dimensions    (default 1024)

``opensearch`` leaves the upstream AWS implementation untouched. The returned
``score`` is cosine similarity in ``[-1, 1]`` — pgvector's ``<=>`` is cosine
distance, so ``score = 1 - distance``. This is the conformance the OpenSearch
implementation still lacks.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any, Iterable

import psycopg

from coa_ontology.stores.base import EmbeddingHit

DEFAULT_NAMESPACE = "default"

_PROVIDERS = ("pgvector", "opensearch")

_DDL = """
CREATE TABLE IF NOT EXISTS public.coa_ontology_embeddings (
    namespace      text NOT NULL,
    ontology_id    text NOT NULL DEFAULT '',
    entity_uri     text NOT NULL,
    entity_type    text,
    embedding_type text NOT NULL,
    model_id       text NOT NULL,
    text           text NOT NULL DEFAULT '',
    metadata       jsonb NOT NULL DEFAULT '{{}}'::jsonb,
    vector         vector({dims}) NOT NULL,
    updated_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (namespace, ontology_id, entity_uri, embedding_type, model_id)
)
"""

_INDEX = """
CREATE INDEX IF NOT EXISTS coa_ontology_embeddings_vec_idx
    ON public.coa_ontology_embeddings USING hnsw (vector vector_cosine_ops)
"""


def _provider() -> str:
    raw = os.environ.get("COA_PROVIDER_ONTOLOGY_VECTOR", "").strip().lower()
    if not raw:
        raise RuntimeError(
            "COA_PROVIDER_ONTOLOGY_VECTOR is required (pgvector|opensearch); refusing to start "
            "without an explicitly selected ontology vector store"
        )
    if raw not in _PROVIDERS:
        raise RuntimeError(f"Unknown COA_PROVIDER_ONTOLOGY_VECTOR={raw!r}; expected one of {_PROVIDERS}")
    return raw


def _dsn() -> str:
    dsn = os.environ.get("COA_CONTROL_PLANE_PG_DSN", "").strip()
    if not dsn:
        raise RuntimeError("COA_CONTROL_PLANE_PG_DSN is required when COA_PROVIDER_ONTOLOGY_VECTOR=pgvector")
    return dsn


def _dimensions() -> int:
    return int(os.environ.get("COA_VECTOR_DIMENSIONS", "1024"))


def _lit(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(v):.8f}" for v in vector) + "]"


def _as_vector(value: Any) -> list[float]:
    """Normalize a pgvector value (text literal or list) to ``list[float]``."""
    if value is None:
        return []
    if isinstance(value, str):
        return [float(part) for part in value.strip().strip("[]").split(",") if part.strip()]
    return [float(item) for item in value]


class PgVectorStore:
    """``VectorStore`` protocol over one pgvector table."""

    def __init__(self, namespace: str | None = None, dimensions: int | None = None) -> None:
        self.namespace = namespace or DEFAULT_NAMESPACE
        self.dimensions = dimensions or _dimensions()

    # -- plumbing ----------------------------------------------------------

    def _connect(self) -> psycopg.Connection:
        conn = psycopg.connect(_dsn())
        # Without the pgvector adapter psycopg returns ``vector`` as the text
        # literal ``'[0.1,0.2,...]'``; the protocol (and the API response
        # model) requires ``list[float]``.
        try:
            from pgvector.psycopg import register_vector

            register_vector(conn)
        except Exception:  # pragma: no cover - adapter is optional at runtime
            pass
        return conn

    def _ns(self, namespace: str | None) -> str:
        return namespace or self.namespace or DEFAULT_NAMESPACE

    def _doc(self, item: dict) -> dict:
        vector = list(item["vector"])
        if len(vector) < self.dimensions:
            vector = vector + [0.0] * (self.dimensions - len(vector))
        doc = {
            "entity_uri": item["entity_uri"],
            "ontology_id": item.get("ontology_id") or "",
            "entity_type": item.get("entity_type"),
            "embedding_type": item.get("embedding_type") or "lexical",
            "model_id": item["model_id"],
            "namespace": self._ns(item.get("namespace")),
            "text": item.get("text", ""),
            "vector": vector,
            "metadata": {
                **{
                    key: item[key]
                    for key in ("context_text", "data_source_id", "query_backend")
                    if item.get(key)
                },
                # Callers may attach their own provenance (e.g. document chunk
                # ids/offsets written by the local ingestion worker). Keep it
                # alongside the legacy whitelist so existing callers are
                # unaffected.
                **{
                    str(key): value
                    for key, value in (item.get("metadata") or {}).items()
                    if value is not None
                },
            },
        }
        return doc

    @staticmethod
    def _row_to_doc(row: tuple, include_vector: bool = True) -> dict:
        (
            namespace,
            ontology_id,
            entity_uri,
            entity_type,
            embedding_type,
            model_id,
            text,
            metadata,
            vector,
            updated_at,
        ) = row
        doc = {
            "entity_uri": entity_uri,
            "ontology_id": ontology_id,
            "entity_type": entity_type,
            "embedding_type": embedding_type,
            "model_id": model_id,
            "namespace": namespace,
            "text": text,
            "metadata": metadata or {},
            "updated_at": updated_at.isoformat() if updated_at else None,
        }
        if include_vector:
            doc["vector"] = _as_vector(vector)
        return doc

    # -- writes ------------------------------------------------------------

    def store_embedding(self, data: dict) -> dict:
        doc = self._doc(data)
        with self._connect() as conn:
            self._upsert(conn, [doc])
        return doc

    def store_embeddings_batch(self, items: list[dict]) -> list[dict]:
        if not items:
            return []
        docs = [self._doc(item) for item in items]
        with self._connect() as conn:
            self._upsert(conn, docs)
        return docs

    @staticmethod
    def _upsert(conn: psycopg.Connection, docs: list[dict]) -> None:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO public.coa_ontology_embeddings
                    (namespace, ontology_id, entity_uri, entity_type, embedding_type,
                     model_id, text, metadata, vector, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector, %s)
                ON CONFLICT (namespace, ontology_id, entity_uri, embedding_type, model_id)
                DO UPDATE SET entity_type = EXCLUDED.entity_type,
                              text = EXCLUDED.text,
                              metadata = EXCLUDED.metadata,
                              vector = EXCLUDED.vector,
                              updated_at = EXCLUDED.updated_at
                """,
                [
                    (
                        doc["namespace"],
                        doc["ontology_id"],
                        doc["entity_uri"],
                        doc["entity_type"],
                        doc["embedding_type"],
                        doc["model_id"],
                        doc["text"],
                        json.dumps(doc["metadata"]),
                        _lit(doc["vector"]),
                        datetime.now(UTC),
                    )
                    for doc in docs
                ],
            )

    # -- reads -------------------------------------------------------------

    def get_embeddings_for_entity(
        self,
        entity_uri: str,
        entity_type: str | None = None,
        embedding_type: str | None = None,
        namespace: str | None = None,
    ) -> list[dict]:
        sql = (
            "SELECT namespace, ontology_id, entity_uri, entity_type, embedding_type, model_id, "
            "text, metadata, vector, updated_at FROM public.coa_ontology_embeddings "
            "WHERE namespace = %s AND entity_uri = %s"
        )
        params: list[Any] = [self._ns(namespace), entity_uri]
        if entity_type:
            sql += " AND entity_type = %s"
            params.append(entity_type)
        if embedding_type:
            sql += " AND embedding_type = %s"
            params.append(embedding_type)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return [self._row_to_doc(row) for row in cur.fetchall()]

    def list_embeddings_for_ontology(
        self,
        ontology_id: str,
        entity_type: str | None = None,
        embedding_type: str | None = None,
        namespace: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        sql = (
            "SELECT namespace, ontology_id, entity_uri, entity_type, embedding_type, model_id, "
            "text, metadata, vector, updated_at FROM public.coa_ontology_embeddings "
            "WHERE namespace = %s AND ontology_id = %s"
        )
        params: list[Any] = [self._ns(namespace), ontology_id]
        if entity_type:
            sql += " AND entity_type = %s"
            params.append(entity_type)
        if embedding_type:
            sql += " AND embedding_type = %s"
            params.append(embedding_type)
        if limit is not None:
            sql += " LIMIT %s"
            params.append(int(limit))
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return [self._row_to_doc(row, include_vector=limit is None) for row in cur.fetchall()]

    def list_searchable_entity_uris(self, ontology_id: str, namespace: str | None = None) -> list[str]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT entity_uri FROM public.coa_ontology_embeddings "
                "WHERE namespace = %s AND ontology_id = %s",
                (self._ns(namespace), ontology_id),
            )
            return [row[0] for row in cur.fetchall()]

    def search_nearest(
        self,
        vector: list[float],
        embedding_type: str,
        model_id: str,
        entity_type: str | None = None,
        ontology_id: str | None = None,
        top_k: int = 10,
        namespace: str | None = None,
    ) -> list[EmbeddingHit]:
        sql = (
            "SELECT entity_uri, entity_type, ontology_id, embedding_type, model_id, text, "
            "metadata, vector, 1 - (vector <=> %s::vector) AS score "
            "FROM public.coa_ontology_embeddings "
            "WHERE namespace = %s AND embedding_type = %s AND model_id = %s"
        )
        params: list[Any] = [_lit(vector), self._ns(namespace), embedding_type, model_id]
        if entity_type:
            sql += " AND entity_type = %s"
            params.append(entity_type)
        if ontology_id:
            sql += " AND ontology_id = %s"
            params.append(ontology_id)
        sql += " ORDER BY vector <=> %s::vector ASC LIMIT %s"
        params.extend([_lit(vector), int(top_k)])
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [
            EmbeddingHit(
                entity_uri=row[0],
                entity_type=row[1],
                ontology_id=row[2] or None,
                embedding_type=row[3],
                model_id=row[4],
                text=row[5],
                metadata=row[6] or {},
                vector=_as_vector(row[7]),
                score=float(row[8]),
            )
            for row in rows
        ]

    # -- deletes -----------------------------------------------------------

    def delete_embeddings_for_ontology(self, ontology_id: str, namespace: str | None = None) -> int:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public.coa_ontology_embeddings WHERE namespace = %s AND ontology_id = %s",
                (self._ns(namespace), ontology_id),
            )
            return cur.rowcount

    def delete_embeddings_for_entities(
        self,
        entity_uris: Iterable[str],
        ontology_id: str,
        namespace: str | None = None,
    ) -> int:
        uris = list(entity_uris)
        if not uris:
            return 0
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public.coa_ontology_embeddings "
                "WHERE namespace = %s AND ontology_id = %s AND entity_uri = ANY(%s)",
                (self._ns(namespace), ontology_id, uris),
            )
            return cur.rowcount

    def delete_index(self, namespace: str | None = None) -> bool:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public.coa_ontology_embeddings WHERE namespace = %s",
                (self._ns(namespace),),
            )
        return True

    def health_check(self) -> dict:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM public.coa_ontology_embeddings")
                total = cur.fetchone()[0]
            return {
                "ok": True,
                "backend": "pgvector",
                "dimensions": self.dimensions,
                "embeddings": total,
            }
        except Exception as exc:  # noqa: BLE001 - probe must never raise
            return {"ok": False, "backend": "pgvector", "error": str(exc)}


def install_pg_vector_store() -> str:
    """Patch the backend factory to serve ``VectorStore`` from pgvector."""
    provider = _provider()
    if provider == "opensearch":
        return provider

    dsn = _dsn()
    dims = _dimensions()

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(_DDL.format(dims=dims))
        cur.execute(_INDEX)

    from coa_ontology import stores as stores_pkg
    from coa_ontology.stores import factory

    def build_stores(namespace: str | None = None):
        from coa_ontology.stores.neptune_db_graph import NeptuneDBGraphStore

        if namespace in factory._store_cache:
            return factory._store_cache[namespace]
        pair = (NeptuneDBGraphStore(namespace=namespace), PgVectorStore(namespace=namespace))
        factory._store_cache[namespace] = pair
        return pair

    # The package re-exports ``build_stores`` by value, and every router does
    # ``from coa_ontology.stores import build_stores``; patching only the
    # factory module would leave those references pointing at the AWS pair.
    factory.build_stores = build_stores  # type: ignore[assignment]
    stores_pkg.build_stores = build_stores  # type: ignore[attr-defined]
    factory.get_vector_store = lambda: build_stores()[1]  # type: ignore[assignment]
    factory.get_graph_store = lambda: build_stores()[0]  # type: ignore[assignment]
    stores_pkg.get_vector_store = factory.get_vector_store  # type: ignore[attr-defined]
    stores_pkg.get_graph_store = factory.get_graph_store  # type: ignore[attr-defined]
    print(
        f"[coa-local-vector] provider=pgvector dsn={dsn.split('@')[-1]} dimensions={dims}",
        flush=True,
    )
    return provider
