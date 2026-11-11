"""Migration registry for the platform database schema.

Why this lives in ``coa_control_plane`` instead of ``platform-core``:
``platform-core`` is being dismantled, and the migration chain is live code
(the local stack's only source of truth for the ``platform`` / ``serve_local``
databases). Keeping it next to the adapter would leave the chain inside a
package that R3 archives. ``metadata_store`` is not a fit because that module
re-exports the SMUS metadata-store client, an unrelated concern. So the
registry, the version gate and the SQL files sit in this package, while the
``MetadataPg`` adapter in ``platform-core`` only delegates here until it is
moved (R2/R3).

Nothing in this module opens a connection: it is pure data plus path handling.
"""

from __future__ import annotations

from importlib.resources import files

SUPPORTED_SCHEMA_VERSION = 51

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
    (
        30,
        "V30__metric_decisions_v9.sql",
        "v9 final ruling: 27 metric definitions (25 table-2 + INS-012 + BANK-036 index)",
    ),
    (31, "V31__data_dictionary.sql", "B-06 data dictionary: fact-table column introspection + property binding"),
    (32, "V32__ontology_lifecycle.sql", "O-02 lifecycle transitions + O-04 publish evidence registry"),
    (33, "V33__term_governance.sql", "O-05 term check/import registry"),
    (34, "V34__metrics_core_m01_m06.sql", "G2 metrics-core: M-01 binding fixes + M-06 readiness ledger"),
    # 集成期重排（doc/_design/54 §2.2 为准）：V35/V36 永久退休，未应用迁移
    # 统一压成 37–40 连续段；旧号对照见 doc 54 的"新旧号对照表"。
    (
        37,
        "V37__metric_observation_synthetic.sql",
        "metric_observation data_source gains synthetic (idempotent CHECK swap)",
    ),
    (38, "V38__ontology_orphan_mark.sql", "append-only orphan markers for lifecycle/evidence rows"),
    (39, "V39__dict_bindings.sql", "persist 79 dictionary bindings (69 explicit + 10 name_match)"),
    (40, "V40__term_high_water.sql", "O-05 vocab guard: effective term-set high-water mark"),
    (41, "V41__metric_semantics.sql", "M-02 observation aggregation semantics + 015/016/018/021/025 alignment"),
    (
        42,
        "V42__dict_column_comments.sql",
        "O-01b dictionary column comments: 283 Chinese business meaning comments "
        "(bindings already at V39)",
    ),
    (
        43,
        "V43__source_ref_stale_mark.sql",
        "B-01 tier-1 stale source-ref markers: append-only "
        "platform.source_ref_stale_mark (idempotent)",
    ),
    (44, "V44__fact_reconcile_event.sql", "fact ledger reconciliation: allow the `reconciled` audit event"),
    (45, "V45__answer_quality_run.sql", "F86 answer quality: one row per full golden-set run (no trend)"),
    # V46 belongs to the P4 branch (quota/plan work) and is deliberately absent
    # here. This branch only adds V47, so the merged registry must stay ordered
    # 45 -> 46 -> 47. Never run this branch's migrate() against a shared
    # environment before V46 lands: the resulting high-water mark would skip it
    # and migration_gap_versions() would then refuse the merged build.
    # （后改为 V48：主线已跳到 47，46 从未落库。上面这段是当时的判断，保留原文；
    #   实际合入顺序是 45 -> 47 -> 48，见 §8.4。）
    (47, "V47__import_batch_namespace.sql", "P8 import batch namespace: namespace_id + insert-time requirement"),
    # P4 dictionary storage: written as V46 on the branch, but 46 never reached
    # any database and main is at 47, so it merges as V48 to keep the registry
    # gapless against MAX(version) (see doc/coa-x/14-契约批次设计.md §8.4).
    (48, "V48__dictionary_storage.sql", "P4 dictionary storage: namespace-scoped snapshot + idempotent refresh runs"),
    (49, "V49__import_failed_feed_index.sql", "P8 ingestion runs: partial index for the namespace-scoped failure feed"),
    # C2 quota landed after V49: 35 is retired forever (see below), so the
    # daily ledger takes the next free number instead of its original V35.
    (50, "V50__quota_usage.sql", "C2-1 quota ledger: daily token/request counters per scope"),
    (51, "V51__import_run.sql", "P1 import run ledger: per-invocation status, counters and failure"),
]

# Retired migration numbers, kept permanently empty.
# 35 belonged to the withdrawn C2 quota branch; 36 was never used.
# Numbers are never recycled: renumbering a pending migration into a retired
# slot makes every environment already at a higher version skip it silently,
# because the runner applies only versions above the recorded high-water mark.
RETIRED_MIGRATION_VERSIONS: tuple[int, ...] = (35, 36)

MIGRATION_GAP_HINT = "该迁移不会被自动执行，请人工确认"

MIGRATIONS_SUBDIR = "migrations"

# Traversable, not a filesystem path: works for editable installs and wheels.
MIGRATIONS_DIR = files(__package__) / MIGRATIONS_SUBDIR


def migration_text(filename: str) -> str:
    """Read one registered migration exactly as committed (no rewriting)."""
    return (MIGRATIONS_DIR / filename).read_text(encoding="utf-8")


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


def registry_rows(registry: list[tuple[int, str, str]] | None = None) -> list[tuple[int, str, str]]:
    """Return the registry in apply order."""
    return list(registry if registry is not None else MIGRATIONS)


__all__: list[str] = [
    "MIGRATION_GAP_HINT",
    "MIGRATIONS",
    "MIGRATIONS_DIR",
    "MIGRATIONS_SUBDIR",
    "RETIRED_MIGRATION_VERSIONS",
    "SUPPORTED_SCHEMA_VERSION",
    "migration_gap_versions",
    "migration_text",
    "registry_rows",
]
