"""MetadataStore adapter: PostgreSQL (psycopg 3 + pool)."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from importlib.resources import files
from typing import Any, Iterator

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ..errors import PortError, PlatformError, EXIT_CONFIG
from ..ports import Manifest
from ..sqlsplit import split_sql_statements

log = logging.getLogger(__name__)

SUPPORTED_SCHEMA_VERSION = 20

MIGRATIONS: list[tuple[int, str, str]] = [
    (1, "V1__s0.sql", "S0 skeleton: blob/blob_ref/blob_bytea"),
    (2, "V2__s1.sql", "S1 ontology: ontology_version/graph_pointer/ontology_job"),
    (3, "V3__s2.sql", "S2 documents: document/document_page/document_chunk"),
    (4, "V4__s3.sql", "S3 retrieval: text_search/GIN/pg_trgm + chunk_embedding/HNSW"),
    (5, "V5__s4.sql", "S4 extraction: extraction_candidate"),
    (6, "V6__s5.sql", "S5 reasoning: reasoning_job/inferred_pointer"),
    (7, "V7__s8.sql", "S8 governance: fact_assertion/fact_event"),
    (8, "V8__s9.sql", "S9 adjudication + audit chain: resolution fields/prev_event/hash"),
    (9, "V9__s10.sql", "S10 reversible adjudication: unmerged/resolution_undo events"),
    (10, "V10__s11.sql", "S11 T-Box governance: proposal/ontology_event + lifecycle statuses"),
    (11, "V11__s12.sql", "S12 purge audit + prefix export: purged_test_graph event"),
    (12, "V12__s13.sql", "S13 bulk import: import_batch/import_item"),
    (13, "V13__embed_partition.sql", "embedding partitions: dimension-free vector + per-dim HNSW + active pointer"),
    (14, "V14__extract_progress.sql", "S14 extraction resume: extraction_progress per LLM batch"),
    (15, "V15__ontology_import.sql", "G-01 import records: ontology_import + staging graph reference"),
    (16, "V16__shapes_registry.sql", "G-03 shapes registry: versioned SHACL deployment"),
    (17, "V17__import_batch_stale.sql", "bulk import lease timeout: running -> stale"),
    (18, "V18__metric_definition.sql", "v3 metric registry: evidence_basis + publishable"),
    (19, "V19__metric_observation.sql", "metric observations + definition-driven calculator fields"),
    (20, "V20__metric_entities.sql", "S14H-04 entity facts: payment records + installment plans"),
]


class Tx:
    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def query(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        return self._conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        return self._conn.execute(sql, params).rowcount

    def execute_returning(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        return self._conn.execute(sql, params).fetchall()

    def executemany(self, sql: str, params: list[tuple | list]) -> int:
        """Bulk insert/update inside the caller's transaction."""
        if not params:
            return 0
        with self._conn.cursor() as cursor:
            cursor.executemany(sql, params)
            return cursor.rowcount


class MetadataPg:
    port = "MetadataStore"

    def __init__(
        self,
        url: str,
        pool_max: int = 10,
        statement_timeout_ms: int | None = None,
        trgm_word_similarity_threshold: float | None = None,
    ) -> None:
        self._url = url
        self._pool_max = pool_max
        self._statement_timeout_ms = statement_timeout_ms
        # S16: `q.raw <% c.text` (pg_trgm word similarity) is GIN-indexable only
        # at a lowered threshold. The session value must equal search.min_similarity.
        self._trgm_threshold = trgm_word_similarity_threshold
        self._pool: ConnectionPool | None = None

    def manifest(self) -> Manifest:
        return Manifest(
            provider="postgres",
            port=self.port,
            capabilities=["db.tx", "db.query", "db.advisory_lock", "db.migrate"],
            provider_version="pg18",
            notes={"client": "psycopg3"},
        )

    def open(self, retry_seconds: float = 60.0) -> None:
        if self._pool is not None:
            return
        kwargs: dict[str, Any] = {"row_factory": dict_row}
        options: list[str] = []
        if self._statement_timeout_ms:
            options.append(f"statement_timeout={self._statement_timeout_ms}")
        if self._trgm_threshold is not None:
            options.append(f"pg_trgm.word_similarity_threshold={self._trgm_threshold}")
        if options:
            kwargs["options"] = "-c " + " -c ".join(options)
        self._pool = ConnectionPool(
            conninfo=self._url,
            min_size=1,
            max_size=self._pool_max,
            open=False,
            timeout=10,
            kwargs=kwargs,
        )
        try:
            self._pool.open(wait=True, timeout=retry_seconds)
        except Exception as exc:  # psycopg_pool.PoolTimeout / OperationalError
            self._pool = None
            raise PortError(
                code="Unavailable",
                message=f"cannot connect to PostgreSQL: {exc}",
                provider="postgres",
                provider_code="E_DB_UNAVAILABLE",
                retryable=True,
            ) from exc

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None

    def _require_pool(self) -> ConnectionPool:
        if self._pool is None:
            raise PortError(
                code="Unavailable",
                message="metadata pool is not open",
                provider="postgres",
                provider_code="E_DB_UNAVAILABLE",
                retryable=True,
            )
        return self._pool

    def query(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        with self._require_pool().connection() as conn:
            return conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        with self._require_pool().connection() as conn:
            return conn.execute(sql, params).rowcount

    @contextmanager
    def tx(self) -> Iterator[Tx]:
        with self._require_pool().connection() as conn:
            with conn.transaction():
                yield Tx(conn)

    @contextmanager
    def advisory_lock(self, key: str, blocking: bool = False) -> Iterator[bool]:
        """Session-scoped advisory lock. Yields True when acquired."""
        with self._require_pool().connection() as conn:
            fn = "pg_advisory_lock" if blocking else "pg_try_advisory_lock"
            row = conn.execute(f"SELECT {fn}(hashtext(%s)) AS ok", (key,)).fetchone()
            acquired = bool(row["ok"]) if row else False
            try:
                yield acquired
            finally:
                if acquired:
                    conn.execute("SELECT pg_advisory_unlock(hashtext(%s))", (key,))

    def migrate(self) -> dict[str, Any]:
        """Apply forward migrations idempotently; refuses a newer schema."""
        applied: list[str] = []
        with self._require_pool().connection() as conn:
            with conn.transaction():
                # Transaction-scoped lock: released automatically on commit/rollback.
                conn.execute("SELECT pg_advisory_xact_lock(hashtext('platform:migrate'))")
                existing = conn.execute(
                    "SELECT to_regclass('platform.schema_version') AS reg"
                ).fetchone()
                current = 0
                if existing and existing["reg"]:
                    row = conn.execute(
                        "SELECT COALESCE(MAX(version), 0) AS v FROM platform.schema_version"
                    ).fetchone()
                    current = int(row["v"])
                    if current > SUPPORTED_SCHEMA_VERSION:
                        raise PlatformError(
                            code="E_DB_MIGRATION_MISMATCH",
                            detail=(
                                f"database schema version {current} is newer than "
                                f"code version {SUPPORTED_SCHEMA_VERSION}"
                            ),
                            stage="db",
                            key="schema_version",
                            provider="postgres",
                            hint="run the matching platform image; do not downgrade data",
                            exit_code=EXIT_CONFIG,
                        )
                for version, filename, description in MIGRATIONS:
                    if version <= current:
                        continue
                    sql_text = files("platform_core").joinpath(f"sql/{filename}").read_text(
                        encoding="utf-8"
                    )
                    for statement in split_sql_statements(sql_text):
                        conn.execute(statement)
                    conn.execute(
                        "INSERT INTO platform.schema_version (version, description) VALUES (%s, %s) "
                        "ON CONFLICT (version) DO NOTHING",
                        (version, description),
                    )
                    applied.append(f"V{version}")
        log.info("migration applied", extra={"event": {"event": "migrate", "to": applied}})
        return {"to": str(SUPPORTED_SCHEMA_VERSION), "applied": applied}

    def health(self) -> None:
        self.query("SELECT 1 AS ok")

    def count_blobs(self) -> int:
        rows = self.query("SELECT COUNT(*) AS n FROM platform.blob WHERE state = 'committed'")
        return int(rows[0]["n"]) if rows else 0

    def count_refs(self) -> int:
        rows = self.query("SELECT COUNT(*) AS n FROM platform.blob_ref")
        return int(rows[0]["n"]) if rows else 0
