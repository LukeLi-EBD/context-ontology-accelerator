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

SUPPORTED_SCHEMA_VERSION = 48

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
    (21, "V21__metric_definition_v5.sql", "v5 metric verdict: variants/rules/effective_date"),
    (22, "V22__fact_model_v6.sql", "v6 fact model: bank/insurance/customer + 7 projections"),
    (23, "V23__metric_quartet_v7.sql", "v7 metric quartet derivation + compiler field bindings"),
    (24, "V24__metric_decisions_v8.sql", "v8 partial decisions + machine-readable rule specs"),
    (25, "V25__fact_model_v7.sql", "v7 fact model: 8 tables + 2 extensions + 44 metric bindings"),
    (26, "V26__datagen.sql", "datagen: synthetic provenance label on fact tables + run ledger"),
    (27, "V27__source_ref.sql", "B-01 value-level provenance: fact natural keys + ref registry"),
    (28, "V28__prov.sql", "B-02 PROV-O judgement provenance: append-only prov_event ledger"),
    (29, "V29__metric_gap_v6.sql", "v6 gap-fill seed: 26 metric definitions (25 table-2 + INS-012)"),
    (30, "V30__metric_decisions_v9.sql", "v9 final ruling: 27 metric definitions (25 table-2 + INS-012 + BANK-036 index)"),
    (31, "V31__data_dictionary.sql", "B-06 data dictionary: fact-table column introspection + property binding"),
    (32, "V32__ontology_lifecycle.sql", "O-02 lifecycle transitions + O-04 publish evidence registry"),
    (33, "V33__term_governance.sql", "O-05 term check/import registry"),
    (34, "V34__metrics_core_m01_m06.sql", "G2 metrics-core: M-01 binding fixes + M-06 readiness ledger"),
    # 集成期重排（doc/_design/54 §2.2 为准）：V35/V36 永久退休，未应用迁移
    # 统一压成 37–40 连续段；旧号对照见 doc 54 的"新旧号对照表"。
    (37, "V37__metric_observation_synthetic.sql", "metric_observation data_source gains synthetic (idempotent CHECK swap)"),
    (38, "V38__ontology_orphan_mark.sql", "append-only orphan markers for lifecycle/evidence rows"),
    (39, "V39__dict_bindings.sql", "persist 79 dictionary bindings (69 explicit + 10 name_match)"),
    (40, "V40__term_high_water.sql", "O-05 vocab guard: effective term-set high-water mark"),
    (41, "V41__metric_semantics.sql", "M-02 observation aggregation semantics + 015/016/018/021/025 alignment"),
    (42, "V42__dict_column_comments.sql", "O-01b dictionary column comments: 283 Chinese business meaning comments (bindings already at V39)"),
    (43, "V43__source_ref_stale_mark.sql", "B-01 tier-1 stale source-ref markers: append-only platform.source_ref_stale_mark (idempotent)"),
    (44, "V44__fact_reconcile_event.sql", "fact ledger reconciliation: allow the `reconciled` audit event"),
    (45, "V45__answer_quality_run.sql", "F86 answer quality: one row per full golden-set run (no trend)"),
    # 原 V46，主线先进了 V47（V47__import_batch_namespace）且 46 从未落库，
    # 合入时改号为 V48，保持注册表与库内 MAX 连续（见 doc/coa-x/16-合并预检.md）。
    (48, "V48__dictionary_storage.sql", "P4 dictionary storage: namespace-scoped snapshot + idempotent refresh runs"),
]

# Retired migration numbers, kept permanently empty.
# 35 belonged to the withdrawn C2 quota branch; 36 was never used.
# Numbers are never recycled: renumbering a pending migration into a retired
# slot makes every environment already at a higher version skip it silently,
# because the runner applies only versions above the recorded high-water mark.
RETIRED_MIGRATION_VERSIONS: tuple[int, ...] = (35, 36)

MIGRATION_GAP_HINT = "该迁移不会被自动执行，请人工确认"


def migration_gap_versions(
    current: int,
    history: set[int] | None,
    registry: list[tuple[int, str, str]] | None = None,
) -> list[int]:
    """Return registered versions <= current that cannot be confirmed as applied.

    Exact check: every registered version at or below the recorded high-water
    mark must have its own row in platform.schema_version. Retired numbers are
    excluded from the check because they are intentionally absent forever.

    Degraded check (no platform.schema_version table): only the high-water mark
    is known, so any non-retired registered version strictly below `current`
    counts as unconfirmed. Capability boundary: a brand-new database has
    `current == 0`, where this can prove nothing and returns an empty list.
    """
    versions = [row[0] for row in (registry if registry is not None else MIGRATIONS)]
    if history is not None:
        return sorted(
            version
            for version in versions
            if version <= current
            and version not in history
            and version not in RETIRED_MIGRATION_VERSIONS
        )
    return sorted(
        version
        for version in versions
        if 0 < version < current and version not in RETIRED_MIGRATION_VERSIONS
    )



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
                history: set[int] | None = None
                if existing and existing["reg"]:
                    history = {
                        int(row["version"])
                        for row in conn.execute(
                            "SELECT version FROM platform.schema_version"
                        ).fetchall()
                    }
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
                gaps = migration_gap_versions(current, history)
                if gaps:
                    raise PlatformError(
                        code="E_DB_MIGRATION_GAP",
                        detail=(
                            f"registered migrations {gaps} are at or below current version "
                            f"{current} but have no row in platform.schema_version; "
                            f"retired versions {list(RETIRED_MIGRATION_VERSIONS)} are exempt; "
                            f"{MIGRATION_GAP_HINT}"
                        ),
                        stage="db",
                        key="schema_version",
                        provider="postgres",
                        hint=MIGRATION_GAP_HINT,
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
                # Seed scripts (V25 ON CONFLICT DO UPDATE) can rewind later binding fixes.
                # Replay the published registry on every migrate(), including no-op runs.
                reg = conn.execute(
                    "SELECT to_regclass('platform.metric_field_binding') AS reg"
                ).fetchone()
                if reg and reg["reg"]:
                    from ..metric_binding_overrides import replay_binding_overrides

                    replay_binding_overrides(conn)
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
