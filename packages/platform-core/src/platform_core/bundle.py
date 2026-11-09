"""Migration-friendly bundle export / import (20-迁移导出导入-设计).

Export is strictly read-only on the production database, Oxigraph and CAS.
Import defaults to a throw-away restore database. The only exception is the
explicit ``--into-empty-platform`` migration path, which is refused unless the
target database holds no documents, fact events or metric observations.
T-Box restore goes through the same governance pipeline as G-01
(``import_document`` -> ``publish``); GSP is never used.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg.types.json import Jsonb
from rdflib import Graph

from .adapters.metadata_pg import SUPPORTED_SCHEMA_VERSION
from .adapters.object_fs import FsCasBackend
from .assembly import Runtime, assemble
from .config import ConfigBundle
from .errors import PlatformError, PortError
from .fact_export import read_ndjson
from .facts import verify_records
from .replay import _insert_replay, reconstruct

BUNDLE_VERSION = 1
VECTOR_SAMPLE = 20

REQUIRED_FILES = [
    "graph/tbox.ttl",
    "graph/abox.ttl",
    "graph/shapes.ttl",
    "meta/ontology_import.jsonl",
    "meta/documents.jsonl",
    "meta/chunks.jsonl",
    "vectors/embeddings.npz",
    "vectors/README",
    "ledger/fact_events.jsonl",
    "ledger/verify.json",
]

# S17: the metric registry, its observations and the two entity fact tables
# travel with the bundle. They are optional on read so bundles exported before
# S17 still verify; every new export always writes all four.
METRIC_DEFINITIONS_FILE = "meta/metric_definitions.jsonl"
METRIC_OBSERVATIONS_FILE = "meta/metric_observations.jsonl"
METRIC_ENTITY_FILE = "meta/metric_entity_facts.jsonl"
DOCUMENT_PAGES_FILE = "meta/document_pages.jsonl"
BLOB_MANIFEST_FILE = "meta/blobs.jsonl"

ENTITY_TABLES = {
    "platform.ins_payment_record": "insPaymentRecord",
    "platform.loan_installment_plan": "loanInstallmentPlan",
}

_METRIC_DEF_COLUMNS = (
    "metric_id", "name_zh", "domain", "evidence_basis", "publishable",
    "inference", "formula_disabled", "missing", "evidence_status", "note",
    "definition_version", "metric_kind", "formula_expr", "numerator_agg",
    "denominator_agg", "window_kind", "min_window_days", "grain", "unit",
    "fact_function", "aggregation_semantics", "updated_at",
)
_METRIC_DEF_UPSERT = f"""
INSERT INTO platform.metric_definition ({", ".join(_METRIC_DEF_COLUMNS)})
VALUES ({", ".join(["%s"] * len(_METRIC_DEF_COLUMNS))})
ON CONFLICT (metric_id) DO UPDATE SET
{", ".join(f"{name} = EXCLUDED.{name}" for name in _METRIC_DEF_COLUMNS[1:])}
"""

_METRIC_OBS_COLUMNS = (
    "metric_id", "definition_version", "institution", "product", "entity_key",
    "as_of", "period_start", "period_end", "numerator", "denominator",
    "window_start", "window_end", "data_source", "fixture", "computed_at",
)
_METRIC_OBS_UPSERT = f"""
INSERT INTO platform.metric_observation ({", ".join(_METRIC_OBS_COLUMNS)})
VALUES ({", ".join(["%s"] * len(_METRIC_OBS_COLUMNS))})
ON CONFLICT ON CONSTRAINT metric_observation_window_key DO UPDATE SET
{", ".join(f"{name} = EXCLUDED.{name}" for name in _METRIC_OBS_COLUMNS[7:])}
"""

_INS_COLUMNS = (
    "policy_no", "product", "installment_no", "due_date", "due_amount",
    "paid_amount", "paid_date", "payment_status", "policy_status",
    "status_as_of", "institution", "data_source", "fixture",
)
_INS_UPSERT = f"""
INSERT INTO platform.ins_payment_record ({", ".join(_INS_COLUMNS)})
VALUES ({", ".join(["%s"] * len(_INS_COLUMNS))})
ON CONFLICT ON CONSTRAINT ins_payment_record_key DO UPDATE SET
{", ".join(f"{name} = EXCLUDED.{name}" for name in ("product", "due_date", "due_amount", "paid_amount", "paid_date", "payment_status", "policy_status", "institution", "fixture"))}
"""

_LOAN_COLUMNS = (
    "agreement_id", "installment_no", "due_date", "due_amount", "paid_amount",
    "paid_date", "overdue_days", "status_as_of", "institution",
    "data_source", "fixture",
)
_LOAN_UPSERT = f"""
INSERT INTO platform.loan_installment_plan ({", ".join(_LOAN_COLUMNS)})
VALUES ({", ".join(["%s"] * len(_LOAN_COLUMNS))})
ON CONFLICT ON CONSTRAINT loan_installment_plan_key DO UPDATE SET
{", ".join(f"{name} = EXCLUDED.{name}" for name in ("due_date", "due_amount", "paid_amount", "paid_date", "overdue_days", "institution", "fixture"))}
"""

# OQ-69: restore-test graphs are the only graphs a cleanup may delete.
RESTORE_GRAPH_PREFIX = "urn:platform:graph:restore:"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _err(code: str, message: str, provider: str = "platform", **details: Any) -> PortError:
    return PortError(
        code="InvalidArgument" if code.startswith("E_BUNDLE_") else "Internal",
        message=message,
        provider=provider,
        provider_code=code,
        details=details or None,
    )


def select_restore_graphs(
    graph_iris: Iterable[str], keep: Iterable[str] = ()
) -> list[str]:
    """Return the graphs a restore cleanup may delete (OQ-69).

    Matching is an exact prefix whitelist: only ``urn:platform:graph:restore:*``
    graphs created by ``import-bundle`` qualify. Historical T-Box / A-Box /
    inferred graphs must never be selected by fuzzy names such as ``tbox:*``.
    """
    keep_set = set(keep)
    return sorted(
        {
            iri for iri in graph_iris
            if iri.startswith(RESTORE_GRAPH_PREFIX) and iri not in keep_set
        }
    )


def cleanup_restore_graphs(
    graph: Any, graph_iris: Iterable[str], keep: Iterable[str] = ()
) -> dict[str, Any]:
    """Delete restore-only graphs; never touches production/history graphs."""
    deleted = []
    for iri in select_restore_graphs(graph_iris, keep):
        graph.clear_graph(iri)
        deleted.append(iri)
    return {"deleted": deleted, "count": len(deleted)}


def _json_default(value: Any) -> Any:
    from datetime import date
    from decimal import Decimal

    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _as_date(value: Any) -> Any:
    from datetime import date

    if value in (None, ""):
        return None
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _as_datetime(value: Any) -> Any:
    if value in (None, ""):
        return None
    return datetime.fromisoformat(str(value))


def _as_decimal(value: Any) -> Any:
    from decimal import Decimal

    if value in (None, ""):
        return None
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _metric_def_hash(rows: list[dict[str, Any]]) -> str:
    """Stable fingerprint of the registry (timestamps excluded).

    Row counts alone cannot tell a restored registry from the migration seed,
    so the bundle also carries this content hash.
    """

    lines = []
    for row in rows:
        values = [
            "" if row.get(name) is None else str(row.get(name))
            for name in _METRIC_DEF_COLUMNS[:-1]
        ]
        lines.append("|".join(values))
    return hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def _term_entry_count(graph: Graph) -> int:
    from rdflib import URIRef

    return len(
        list(
            graph.subjects(
                predicate=URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                object=URIRef("https://w3id.org/fsldm/terms#TermEntry"),
            )
        )
    )


def _metric_def_params(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["metric_id"], row["name_zh"], row["domain"], row["evidence_basis"],
        bool(row["publishable"]), bool(row["inference"]), bool(row["formula_disabled"]),
        row.get("missing"), row["evidence_status"], row.get("note"),
        row.get("definition_version") or "v3.0", row.get("metric_kind"),
        row.get("formula_expr"), row.get("numerator_agg"),
        row.get("denominator_agg"), row.get("window_kind"),
        int(row["min_window_days"]) if row.get("min_window_days") is not None else None,
        row.get("grain"), row.get("unit"), row.get("fact_function"),
        row.get("aggregation_semantics") or "sum",
        _as_datetime(row.get("updated_at")),
    )


def _metric_obs_params(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["metric_id"], row.get("definition_version") or "v3.0",
        row.get("institution"), row.get("product"), row["entity_key"],
        _as_date(row.get("as_of")), _as_date(row.get("period_start")),
        _as_date(row.get("period_end")), _as_decimal(row["numerator"]),
        _as_decimal(row.get("denominator")),
        _as_date(row["window_start"]), _as_date(row["window_end"]),
        row["data_source"], bool(row.get("fixture")),
        _as_datetime(row.get("computed_at")),
    )


def _ins_params(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["policy_no"], row["product"], int(row["installment_no"]),
        _as_date(row["due_date"]), _as_decimal(row["due_amount"]),
        _as_decimal(row.get("paid_amount")), _as_date(row.get("paid_date")),
        row["payment_status"], row["policy_status"], _as_date(row["status_as_of"]),
        row.get("institution"), row["data_source"], bool(row.get("fixture")),
    )


def _loan_params(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["agreement_id"], int(row["installment_no"]), _as_date(row["due_date"]),
        _as_decimal(row["due_amount"]), _as_decimal(row.get("paid_amount")),
        _as_date(row.get("paid_date")),
        int(row["overdue_days"]) if row.get("overdue_days") is not None else None,
        _as_date(row["status_as_of"]), row.get("institution"),
        row["data_source"], bool(row.get("fixture")),
    )


def _canonical_hash(graph: Graph) -> str:
    """Environment-stable hash over triples (blank nodes canonicalized).

    ``ontology_version.content_hash`` is a hash of the *source bytes* and changes
    whenever a graph is reserialized; the bundle therefore also records this
    canonical triple hash as the cross-environment equivalence anchor.
    """

    from decimal import Decimal

    from rdflib import Literal
    from rdflib.compare import to_canonical_graph
    from rdflib.namespace import XSD

    numeric = {
        XSD.decimal, XSD.double, XSD.float, XSD.integer, XSD.long, XSD.int,
        XSD.short, XSD.byte, XSD.nonNegativeInteger, XSD.nonPositiveInteger,
        XSD.negativeInteger, XSD.positiveInteger, XSD.unsignedLong, XSD.unsignedInt,
        XSD.unsignedShort, XSD.unsignedByte,
    }

    def term(value: Any) -> str:
        # Oxigraph normalizes numeric lexical forms ("699.0" -> "699"), rdflib
        # keeps them. Compare by value so a reserialized graph stays equal.
        if isinstance(value, Literal) and value.datatype in numeric and value.value is not None:
            raw = value.value
            if isinstance(raw, Decimal):
                return "num:" + format(raw.normalize(), "f")
            return "num:" + str(raw)
        return value.n3()

    canonical = to_canonical_graph(graph)
    lines = sorted(f"{term(s)} {p.n3()} {term(o)} ." for s, p, o in canonical)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _file_entry(bundle_dir: Path, rel: str, kind: str, records: int | None = None) -> dict[str, Any]:
    path = bundle_dir / rel
    return {
        "path": rel,
        "kind": kind,
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "lines": _line_count(path) if kind in ("ttl", "jsonl", "text") else None,
        "records": records,
    }


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    _write_text(path, "".join(_dumps(row) + "\n" for row in rows))


def _norm_tag(tag: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in tag)
    if not clean:
        raise _err("E_BUNDLE_TAG", "tag must contain at least one alphanumeric character")
    return clean


def _admin_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/postgres", parts.query, parts.fragment))


def _db_url(url: str, name: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{name}", parts.query, parts.fragment))


def _create_database(url: str, name: str) -> None:
    with psycopg.connect(_admin_url(url), autocommit=True, connect_timeout=10) as conn:
        conn.execute(f'CREATE DATABASE "{name}"')


def _drop_database(url: str, name: str) -> None:
    with psycopg.connect(_admin_url(url), autocommit=True, connect_timeout=10) as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def _database_exists(url: str, name: str) -> bool:
    with psycopg.connect(_admin_url(url), autocommit=True, connect_timeout=10) as conn:
        row = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
    return row is not None


def _target_is_empty(url: str) -> bool:
    """True when the target database holds no business rows.

    Used only for the opt-in ``--into-empty-platform`` restore path. A stack
    that has merely run its migrations (and optionally auto-imported the
    bootstrap T-Box) still counts as empty; any document or fact event means
    the database is in use and the restore is refused.
    """

    probes = (
        "platform.document",
        "platform.fact_event",
        "platform.metric_observation",
    )
    with psycopg.connect(url, autocommit=True, connect_timeout=10) as conn:
        for table in probes:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except psycopg.errors.UndefinedTable:
                return True
            if int(count) > 0:
                return False
    return True


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


def export_bundle(
    runtime: Runtime,
    out_root: str | Path,
    tag: str,
    include_blobs: bool = False,
) -> dict[str, Any]:
    """Write a bundle under ``<out_root>/<tag>``. Read-only on every source."""

    cfg = runtime.config
    tag = _norm_tag(tag)
    bundle_dir = Path(out_root) / tag
    if bundle_dir.exists() and any(bundle_dir.iterdir()):
        raise _err("E_BUNDLE_EXISTS", f"bundle directory already exists: {bundle_dir}")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    try:
        generated = datetime.now().astimezone()
        pointer = runtime.ontology.current()
        if not pointer:
            raise _err("E_BUNDLE_NO_TBOX", "no published T-Box pointer; export refused")
        embedding_pointer = runtime.vectors.pointer()
        model = embedding_pointer["model"]
        dimensions = int(embedding_pointer["dimensions"])

        schema_rows = runtime.metadata.query(
            "SELECT MAX(version) AS v FROM platform.schema_version"
        )
        schema_version = int(schema_rows[0]["v"]) if schema_rows and schema_rows[0]["v"] else 0

        # ---- T-Box -------------------------------------------------------
        tbox = runtime.ontology.export_version(pointer["versionId"], "turtle")
        _write_text(bundle_dir / "graph/tbox.ttl", tbox["content"])
        tbox_graph = Graph()
        tbox_graph.parse(data=tbox["content"], format="turtle")
        tbox_canonical = _canonical_hash(tbox_graph)

        # ---- A-Box (union of configured graphs) --------------------------
        abox_graphs = list(cfg.reasoning.abox_graphs)
        abox_union = Graph()
        for iri in abox_graphs:
            nt = runtime.graph.export_graph(iri)
            if nt.strip():
                abox_union.parse(data=nt.decode("utf-8"), format="nt")
        abox_turtle = abox_union.serialize(format="turtle") if len(abox_union) else ""
        _write_text(bundle_dir / "graph/abox.ttl", abox_turtle)

        # ---- shapes registry --------------------------------------------
        shape_rows = runtime.metadata.query(
            """
            SELECT DISTINCT ON (shapes_id)
                   shapes_id, namespace, version, content, content_format,
                   content_hash, triple_count, created_at
              FROM platform.shapes_registry
             ORDER BY shapes_id, created_at DESC, version DESC
            """
        )
        shapes_entries: list[dict[str, Any]] = []
        shape_blocks: list[str] = []
        for row in shape_rows:
            content = row["content"]
            fmt = row["content_format"] or "turtle"
            if fmt == "turtle":
                rendered = content
            else:
                graph = Graph()
                graph.parse(data=content, format=fmt)
                rendered = graph.serialize(format="turtle")
            header = (
                f"# shapesId={row['shapes_id']} version={row['version']} "
                f"namespace={row['namespace']} contentHash={row['content_hash']} "
                f"triples={int(row['triple_count'])} format={fmt}\n"
            )
            shape_blocks.append(header + rendered)
            shapes_entries.append(
                {
                    "shapesId": row["shapes_id"],
                    "namespace": row["namespace"],
                    "version": row["version"],
                    "contentHash": row["content_hash"],
                    "triples": int(row["triple_count"]),
                    "contentFormat": fmt,
                    "content": content,
                }
            )
        _write_text(bundle_dir / "graph/shapes.ttl", "\n".join(shape_blocks))

        # ---- metadata ----------------------------------------------------
        imports = runtime.metadata.query(
            """
            SELECT import_id, version_id, target_namespace, author, change_summary,
                   base_triples, total_triples, classes, object_properties,
                   data_properties, shapes_id, shapes_version, conforms,
                   violation_count, usable, reason, source_sha256, staging_graph,
                   payload, created_at
              FROM platform.ontology_import
             ORDER BY created_at, import_id
            """
        )
        documents = runtime.metadata.query(
            """
            SELECT document_id, sha256, bucket, object_key, filename, mime_type,
                   size_bytes, status, page_count, char_count, chunk_count,
                   parser, parser_version, warnings, manifest, metadata,
                   created_at, parsed_at
              FROM platform.document
             ORDER BY created_at, document_id
            """
        )
        raw_chunks = runtime.metadata.query(
            """
            SELECT chunk_id, document_id, seq, page_from, page_to, char_start,
                   char_end, text, token_estimate, created_at
              FROM platform.document_chunk
             ORDER BY document_id, seq
            """
        )
        # Ingest may still be running: keep the snapshot referentially closed by
        # dropping chunks whose document row was not in the earlier snapshot.
        document_ids = {row["document_id"] for row in documents}
        chunks = [row for row in raw_chunks if row["document_id"] in document_ids]
        chunks_excluded = len(raw_chunks) - len(chunks)
        _write_jsonl(bundle_dir / "meta/ontology_import.jsonl", imports)
        _write_jsonl(bundle_dir / "meta/documents.jsonl", documents)
        _write_jsonl(bundle_dir / "meta/chunks.jsonl", chunks)

        # ---- vectors (active partition only) -----------------------------
        import numpy as np

        raw_vectors = runtime.metadata.query(
            """
            SELECT chunk_id, embedding::text AS embedding
              FROM platform.chunk_embedding
             WHERE model = %s AND dimensions = %s
             ORDER BY chunk_id
            """,
            (model, dimensions),
        )
        exported_chunk_ids = {row["chunk_id"] for row in chunks}
        vector_rows = [row for row in raw_vectors if row["chunk_id"] in exported_chunk_ids]
        embeddings_excluded = len(raw_vectors) - len(vector_rows)
        id_width = max([len(row["chunk_id"]) for row in vector_rows] + [1])
        chunk_ids = np.array(
            [row["chunk_id"] for row in vector_rows], dtype=f"<U{id_width}"
        )
        embeddings = np.zeros((len(vector_rows), dimensions), dtype=np.float32)
        for index, row in enumerate(vector_rows):
            text = row["embedding"].strip()
            if text.startswith("["):
                text = text[1:-1]
            embeddings[index] = np.fromstring(text, sep=",", dtype=np.float32)
        (bundle_dir / "vectors").mkdir(parents=True, exist_ok=True)
        np.savez(bundle_dir / "vectors/embeddings.npz", chunk_ids=chunk_ids, embeddings=embeddings)
        readme = (
            f"provider={embedding_pointer['provider']}\n"
            f"model={model}\n"
            f"dimensions={dimensions}\n"
            f"partition={embedding_pointer['provider']}:{model}@{dimensions}\n"
            f"count={len(vector_rows)}\n"
            "encoding=float32, L2-normalized by BAAI/bge-m3 as returned by TEI; "
            "stored as-is, import does not re-normalize.\n"
        )
        _write_text(bundle_dir / "vectors/README", readme)

        # ---- fact ledger --------------------------------------------------
        event_rows = runtime.metadata.query(
            """
            SELECT e.event_id, e.fact_id, e.action, e.actor, e.reason, e.batch_id,
                   e.payload, e.prev_event, e.hash, e.created_at,
                   a.source_document_id, a.source_run_id
              FROM platform.fact_event e
              LEFT JOIN platform.fact_assertion a ON a.fact_id = e.fact_id
             ORDER BY e.event_id
            """
        )
        events = [_event_item(row) for row in event_rows]
        chain = verify_records(events)
        _write_jsonl(bundle_dir / "ledger/fact_events.jsonl", events)
        _write_text(bundle_dir / "ledger/verify.json", json.dumps(chain, ensure_ascii=False, indent=2))
        if not chain.get("ok"):
            raise _err("E_BUNDLE_LEDGER_CHAIN", f"fact audit chain is broken: {chain.get('error')}")

        fact_assertion_rows = runtime.metadata.query(
            "SELECT COUNT(*) AS n FROM platform.fact_assertion"
        )

        # ---- metric registry, observations and entity facts -------------
        metric_defs = runtime.metadata.query(
            """
            SELECT metric_id, name_zh, domain, evidence_basis, publishable,
                   inference, formula_disabled, missing, evidence_status, note,
                   definition_version, metric_kind, formula_expr, numerator_agg,
                   denominator_agg, window_kind, min_window_days, grain, unit,
                   fact_function, updated_at
              FROM platform.metric_definition
             ORDER BY metric_id
            """
        )
        metric_obs = runtime.metadata.query(
            """
            SELECT metric_id, definition_version, institution, product, entity_key,
                   as_of, period_start, period_end, numerator, denominator,
                   window_start, window_end, data_source, fixture, computed_at
              FROM platform.metric_observation
             ORDER BY metric_id, definition_version, entity_key, window_start, window_end
            """
        )
        ins_payments = runtime.metadata.query(
            """
            SELECT policy_no, product, installment_no, due_date, due_amount,
                   paid_amount, paid_date, payment_status, policy_status,
                   status_as_of, institution, data_source, fixture
              FROM platform.ins_payment_record
             ORDER BY policy_no, installment_no, status_as_of, data_source
            """
        )
        loan_plans = runtime.metadata.query(
            """
            SELECT agreement_id, installment_no, due_date, due_amount, paid_amount,
                   paid_date, overdue_days, status_as_of, institution,
                   data_source, fixture
              FROM platform.loan_installment_plan
             ORDER BY agreement_id, installment_no, status_as_of, data_source
            """
        )
        entity_rows = [
            dict(row, table="platform.ins_payment_record") for row in ins_payments
        ] + [
            dict(row, table="platform.loan_installment_plan") for row in loan_plans
        ]
        _write_jsonl(bundle_dir / METRIC_DEFINITIONS_FILE, metric_defs)
        _write_jsonl(bundle_dir / METRIC_OBSERVATIONS_FILE, metric_obs)
        _write_jsonl(bundle_dir / METRIC_ENTITY_FILE, entity_rows)

        # ---- per-page text (document detail / page-count consistency) -----
        page_rows = runtime.metadata.query(
            """
            SELECT document_id, page_number, text, char_count
              FROM platform.document_page
             ORDER BY document_id, page_number
            """
        )
        _write_jsonl(bundle_dir / DOCUMENT_PAGES_FILE, page_rows)

        # ---- optional blobs (CAS payloads + reference manifest) ----------
        blob_entries: list[dict[str, Any]] = []
        blob_missing: list[str] = []
        blob_bytes = 0
        blob_rows: list[dict[str, Any]] = []
        blob_refs: list[dict[str, Any]] = []
        if include_blobs:
            root = Path(cfg.storage.root)
            # Every committed blob travels, not only document originals: stale
            # object references would otherwise make the target store differ
            # from the source with no way to tell why.
            blob_rows = runtime.metadata.query(
                """
                SELECT hash, size, mime, tier, state, metadata, created_at
                  FROM platform.blob
                 WHERE state = 'committed'
                 ORDER BY hash
                """
            )
            blob_refs = runtime.metadata.query(
                """
                SELECT hash, owner_type, owner_id
                  FROM platform.blob_ref
                 WHERE hash IN (SELECT hash FROM platform.blob WHERE state = 'committed')
                 ORDER BY hash, owner_type, owner_id
                """
            )
            refs_by_hash: dict[str, list[dict[str, str]]] = {}
            for ref in blob_refs:
                refs_by_hash.setdefault(ref["hash"], []).append(
                    {"ownerType": ref["owner_type"], "ownerId": ref["owner_id"]}
                )
            pg_payloads: dict[str, bytes] = {}
            pg_hashes = [row["hash"] for row in blob_rows if row["tier"] == "pg"]
            if pg_hashes:
                payload_rows = runtime.metadata.query(
                    "SELECT hash, content FROM platform.blob_bytea WHERE hash = ANY(%s)",
                    (pg_hashes,),
                )
                pg_payloads = {row["hash"]: bytes(row["content"]) for row in payload_rows}

            blob_manifest: list[dict[str, Any]] = []
            for row in blob_rows:
                sha = str(row["hash"]).strip()
                target = bundle_dir / "blobs" / sha[:2] / sha
                target.parent.mkdir(parents=True, exist_ok=True)
                if row["tier"] == "pg":
                    data = pg_payloads.get(sha)
                    if data is None:
                        blob_missing.append(sha)
                        continue
                    target.write_bytes(data)
                else:
                    source = root / "blobs" / sha[:2] / sha
                    if not source.is_file():
                        blob_missing.append(sha)
                        continue
                    shutil.copyfile(source, target)
                size = int(row["size"])
                if target.stat().st_size != size:
                    raise _err(
                        "E_BUNDLE_BLOB_SIZE",
                        f"blob {sha} size mismatch: row={size} payload={target.stat().st_size}",
                        hash=sha,
                    )
                blob_bytes += size
                blob_entries.append(_file_entry(bundle_dir, f"blobs/{sha[:2]}/{sha}", "blob"))
                blob_manifest.append(
                    {
                        "hash": sha,
                        "size": size,
                        "mime": row["mime"],
                        "tier": row["tier"],
                        "metadata": row["metadata"] or {},
                        "createdAt": row["created_at"],
                        "refs": refs_by_hash.get(sha, []),
                    }
                )
            if blob_missing:
                # A partial bundle is worse than no bundle: fail the export.
                raise _err(
                    "E_BUNDLE_BLOB_MISSING",
                    f"{len(blob_missing)} committed blob payload(s) are unreadable; "
                    "refusing to write a partial migration bundle",
                    missing=blob_missing[:20],
                )
            _write_jsonl(bundle_dir / BLOB_MANIFEST_FILE, blob_manifest)

        # ---- manifest ----------------------------------------------------
        files: list[dict[str, Any]] = [
            _file_entry(bundle_dir, "graph/tbox.ttl", "ttl"),
            _file_entry(bundle_dir, "graph/abox.ttl", "ttl"),
            _file_entry(bundle_dir, "graph/shapes.ttl", "ttl"),
            _file_entry(bundle_dir, "meta/ontology_import.jsonl", "jsonl", len(imports)),
            _file_entry(bundle_dir, "meta/documents.jsonl", "jsonl", len(documents)),
            _file_entry(bundle_dir, "meta/chunks.jsonl", "jsonl", len(chunks)),
            _file_entry(bundle_dir, "vectors/embeddings.npz", "npz", len(vector_rows)),
            _file_entry(bundle_dir, "vectors/README", "text"),
            _file_entry(bundle_dir, "ledger/fact_events.jsonl", "jsonl", len(events)),
            _file_entry(bundle_dir, "ledger/verify.json", "json"),
            _file_entry(bundle_dir, METRIC_DEFINITIONS_FILE, "jsonl", len(metric_defs)),
            _file_entry(bundle_dir, METRIC_OBSERVATIONS_FILE, "jsonl", len(metric_obs)),
            _file_entry(bundle_dir, METRIC_ENTITY_FILE, "jsonl", len(entity_rows)),
            _file_entry(bundle_dir, DOCUMENT_PAGES_FILE, "jsonl", len(page_rows)),
        ]
        files.extend(blob_entries)
        if include_blobs:
            files.append(
                _file_entry(bundle_dir, BLOB_MANIFEST_FILE, "jsonl", len(blob_rows))
            )

        tbox_triples = int(tbox["triples"])
        abox_triples = len(abox_union)
        manifest = {
            "bundleVersion": BUNDLE_VERSION,
            "schemaVersion": schema_version,
            "tag": tag,
            "generatedAt": generated.isoformat(),
            "source": {
                "database": urlsplit(cfg.database.url).path.lstrip("/"),
                "graphEndpoint": cfg.graph.endpoint,
                "tbox": {
                    "versionId": pointer["versionId"],
                    "semver": pointer["semver"],
                    "contentHash": pointer["contentHash"],
                    "canonicalHash": tbox_canonical,
                    "graph": pointer["graph"],
                    "triples": tbox_triples,
                    "termEntries": _term_entry_count(tbox_graph),
                },
                "embedding": {
                    "provider": embedding_pointer["provider"],
                    "model": model,
                    "dimensions": dimensions,
                    "partition": f"{embedding_pointer['provider']}:{model}@{dimensions}",
                },
                "aboxGraphs": abox_graphs,
                "shapes": shapes_entries,
            },
            "totals": {
                "documents": len(documents),
                "chunks": len(chunks),
                "chunksExcluded": chunks_excluded,
                "embeddings": len(vector_rows),
                "embeddingsExcluded": embeddings_excluded,
                "triples": tbox_triples + abox_triples,
                "tripleBreakdown": {"tbox": tbox_triples, "abox": abox_triples},
                "factEvents": len(events),
                "factAssertions": int(fact_assertion_rows[0]["n"]),
                "ontologyImports": len(imports),
                "shapes": len(shapes_entries),
                "metricDefinitions": len(metric_defs),
                "metricDefinitionsHash": _metric_def_hash(metric_defs),
                "metricObservations": len(metric_obs),
                "documentPages": len(page_rows),
                "metricEntityFacts": {
                    "insPaymentRecord": len(ins_payments),
                    "loanInstallmentPlan": len(loan_plans),
                },
                "blobs": {
                    "included": bool(include_blobs),
                    "count": len(blob_entries),
                    "bytes": blob_bytes,
                    "missing": len(blob_missing),
                    "refs": len(blob_refs),
                    "byTier": {
                        "pg": sum(1 for row in blob_rows if row["tier"] == "pg"),
                        "fs": sum(1 for row in blob_rows if row["tier"] == "fs"),
                    },
                },
            },
            "files": sorted(files, key=lambda item: item["path"]),
        }
        _write_text(bundle_dir / "MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        total_bytes = sum(item["bytes"] for item in manifest["files"])
        return {
            "bundleDir": str(bundle_dir.resolve()),
            "tag": tag,
            "schemaVersion": schema_version,
            "generatedAt": manifest["generatedAt"],
            "tbox": manifest["source"]["tbox"],
            "embedding": manifest["source"]["embedding"],
            "totals": manifest["totals"],
            "bytes": total_bytes,
            "files": len(manifest["files"]),
            "ledger": chain,
            "blobs": manifest["totals"]["blobs"],
            "blobMissing": blob_missing[:20],
        }
    except Exception:
        # Never leave a half-written bundle behind.
        try:
            if bundle_dir.exists():
                for path in sorted(bundle_dir.rglob("*"), reverse=True):
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        try:
                            path.rmdir()
                        except OSError:
                            pass
                bundle_dir.rmdir()
        except OSError:
            pass
        raise


def _event_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "eventId": int(row["event_id"]),
        "factId": row["fact_id"],
        "action": row["action"],
        "actor": row["actor"],
        "reason": row["reason"],
        "batchId": row["batch_id"],
        "payload": row["payload"],
        "prevEvent": int(row["prev_event"]) if row["prev_event"] else None,
        "hash": row["hash"],
        "createdAt": row["created_at"].isoformat(),
        "source": {
            "documentId": row["source_document_id"],
            "runId": row["source_run_id"],
        },
    }


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------


def verify_bundle(bundle_dir: str | Path, expected_schema: int | None = None) -> dict[str, Any]:
    """Check manifest structure, every file hash/size/line count, vectors and ledger."""

    import numpy as np

    root = Path(bundle_dir)
    manifest_path = root / "MANIFEST.json"
    if not manifest_path.is_file():
        raise _err("E_BUNDLE_MANIFEST", f"MANIFEST.json not found under {root}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise _err("E_BUNDLE_MANIFEST", f"MANIFEST.json is not valid JSON: {exc}") from exc
    if int(manifest.get("bundleVersion") or 0) != BUNDLE_VERSION:
        raise _err(
            "E_BUNDLE_FORMAT",
            f"unsupported bundleVersion={manifest.get('bundleVersion')!r} "
            f"(expected {BUNDLE_VERSION})",
        )
    schema = int(manifest.get("schemaVersion") or 0)
    expected = SUPPORTED_SCHEMA_VERSION if expected_schema is None else expected_schema
    if schema != expected:
        raise _err(
            "E_BUNDLE_SCHEMA_MISMATCH",
            f"bundle schemaVersion={schema} does not match code schema {expected}",
            schemaVersion=schema,
            expected=expected,
        )

    entries = manifest.get("files") or []
    listed = {item.get("path") for item in entries}
    missing = [rel for rel in REQUIRED_FILES if rel not in listed]
    if missing:
        raise _err("E_BUNDLE_MISSING", f"manifest does not list required files: {missing}", missing=missing)

    for item in entries:
        rel = item.get("path")
        path = root / str(rel)
        if not path.is_file():
            raise _err("E_BUNDLE_MISSING", f"file missing: {rel}", path=rel)
        size = path.stat().st_size
        declared_bytes = item.get("bytes")
        if declared_bytes is None or int(declared_bytes) != size:
            raise _err(
                "E_BUNDLE_SIZE",
                f"size mismatch for {rel}: manifest={item.get('bytes')} actual={size}",
                path=rel,
            )
        digest = _sha256_file(path)
        if digest != item.get("sha256"):
            raise _err(
                "E_BUNDLE_SHA",
                f"sha256 mismatch for {rel}: manifest={item.get('sha256')} actual={digest}",
                path=rel,
                expected=item.get("sha256"),
                actual=digest,
            )
        if item.get("lines") is not None and int(item["lines"]) != _line_count(path):
            raise _err(
                "E_BUNDLE_LINES",
                f"line count mismatch for {rel}: manifest={item['lines']} "
                f"actual={_line_count(path)}",
                path=rel,
            )

    # ---- blobs (optional; present when --include-blobs was used) ---------
    totals = manifest.get("totals") or {}
    if BLOB_MANIFEST_FILE in listed:
        blob_rows = read_ndjson(root / BLOB_MANIFEST_FILE)
        declared_blobs = totals.get("blobs") or {}
        expected_count = int(declared_blobs.get("count") or 0)
        expected_bytes = int(declared_blobs.get("bytes") or 0)
        if len(blob_rows) != expected_count:
            raise _err(
                "E_BUNDLE_BLOB_COUNT",
                f"blob manifest count mismatch: file={len(blob_rows)} "
                f"manifest={expected_count}",
                path=BLOB_MANIFEST_FILE,
            )
        actual_bytes = sum(int(row["size"]) for row in blob_rows)
        if actual_bytes != expected_bytes:
            raise _err(
                "E_BUNDLE_BLOB_BYTES",
                f"blob byte total mismatch: file={actual_bytes} "
                f"manifest={expected_bytes}",
                path=BLOB_MANIFEST_FILE,
            )
        file_by_path = {item.get("path"): item for item in entries}
        declared_refs = 0
        for row in blob_rows:
            sha = str(row.get("hash") or "")
            rel = f"blobs/{sha[:2]}/{sha}"
            item = file_by_path.get(rel)
            if item is None:
                raise _err(
                    "E_BUNDLE_BLOB_MISSING",
                    f"blob payload is not listed in the manifest: {rel}",
                    path=rel,
                )
            if int(item.get("bytes")) != int(row["size"]):
                raise _err(
                    "E_BUNDLE_BLOB_SIZE",
                    f"blob size mismatch for {rel}: manifest={item.get('bytes')} "
                    f"blobIndex={row['size']}",
                    path=rel,
                )
            if item.get("sha256") != sha:
                raise _err(
                    "E_BUNDLE_BLOB_SHA",
                    f"blob payload hash does not match its CAS name: {rel}",
                    path=rel,
                )
            declared_refs += len(row.get("refs") or [])
        if declared_refs != int(declared_blobs.get("refs") or 0):
            raise _err(
                "E_BUNDLE_BLOB_REFS",
                f"blob reference count mismatch: file={declared_refs} "
                f"manifest={declared_blobs.get('refs')}",
                path=BLOB_MANIFEST_FILE,
            )

    # ---- vectors --------------------------------------------------------
    vec_path = root / "vectors/embeddings.npz"
    try:
        data = np.load(vec_path)
        chunk_ids = data["chunk_ids"].tolist()
        embeddings = data["embeddings"]
    except Exception as exc:  # noqa: BLE001 - report, never swallow
        raise _err("E_BUNDLE_VECTOR_FILE", f"cannot read vectors/embeddings.npz: {exc}") from exc
    declared = dict(manifest.get("source", {}).get("embedding") or {})
    dims = int(declared.get("dimensions") or 0)
    if embeddings.ndim != 2:
        raise _err("E_BUNDLE_VECTOR_DIM", f"embeddings must be 2-D, got shape {embeddings.shape}")
    if dims and embeddings.shape[1] != dims:
        raise _err(
            "E_BUNDLE_VECTOR_DIM",
            f"vector dimension mismatch: manifest={dims} actual={embeddings.shape[1]}",
            expected=dims,
            actual=int(embeddings.shape[1]),
        )
    if 1024 != embeddings.shape[1]:
        raise _err(
            "E_BUNDLE_VECTOR_DIM",
            f"pgvector schema supports 1024 dims, bundle has {embeddings.shape[1]}",
            expected=1024,
            actual=int(embeddings.shape[1]),
        )
    if len(chunk_ids) != len(embeddings) or len(chunk_ids) != int(totals.get("embeddings") or 0):
        raise _err(
            "E_BUNDLE_VECTOR_COUNT",
            f"vector count mismatch: ids={len(chunk_ids)} rows={len(embeddings)} "
            f"manifest={totals.get('embeddings')}",
        )
    ids = {item for item in chunk_ids}
    known_chunks = {
        row.get("chunk_id") for row in read_ndjson(root / "meta/chunks.jsonl")
    }
    orphans = sorted(item for item in ids if item not in known_chunks)
    if orphans:
        raise _err(
            "E_BUNDLE_VECTOR_CHUNK",
            f"{len(orphans)} embedding row(s) reference chunks missing from meta/chunks.jsonl",
            chunkIds=orphans[:5],
        )

    # ---- ledger ---------------------------------------------------------
    events = read_ndjson(root / "ledger/fact_events.jsonl")
    if len(events) != int(totals.get("factEvents") or 0):
        raise _err(
            "E_BUNDLE_LEDGER_COUNT",
            f"ledger event count mismatch: file={len(events)} "
            f"manifest={totals.get('factEvents')}",
        )
    chain = verify_records(events)
    if not chain.get("ok"):
        raise _err("E_BUNDLE_LEDGER_CHAIN", f"fact audit chain is broken: {chain.get('error')}")
    verify_file = root / "ledger/verify.json"
    try:
        declared_verify = json.loads(verify_file.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise _err("E_BUNDLE_LEDGER_CHAIN", f"ledger/verify.json is invalid: {exc}") from exc
    if not declared_verify.get("ok"):
        raise _err("E_BUNDLE_LEDGER_CHAIN", "ledger/verify.json reports ok=false")

    # ---- metric registry / observations / entity facts (optional) -------
    for rel, key in (
        (METRIC_DEFINITIONS_FILE, "metricDefinitions"),
        (METRIC_OBSERVATIONS_FILE, "metricObservations"),
    ):
        if rel not in listed:
            continue
        rows = read_ndjson(root / rel)
        if len(rows) != int(totals.get(key) or 0):
            raise _err(
                "E_BUNDLE_METRIC_COUNT",
                f"metric count mismatch for {rel}: file={len(rows)} "
                f"manifest={totals.get(key)}",
                path=rel,
            )
    if METRIC_DEFINITIONS_FILE in listed:
        rows = read_ndjson(root / METRIC_DEFINITIONS_FILE)
        declared_hash = totals.get("metricDefinitionsHash")
        if declared_hash and _metric_def_hash(rows) != declared_hash:
            raise _err(
                "E_BUNDLE_METRIC_HASH",
                "metric definition content hash does not match the manifest",
                path=METRIC_DEFINITIONS_FILE,
            )
    if DOCUMENT_PAGES_FILE in listed:
        rows = read_ndjson(root / DOCUMENT_PAGES_FILE)
        if len(rows) != int(totals.get("documentPages") or 0):
            raise _err(
                "E_BUNDLE_PAGE_COUNT",
                f"document page count mismatch: file={len(rows)} "
                f"manifest={totals.get('documentPages')}",
                path=DOCUMENT_PAGES_FILE,
            )
    if METRIC_ENTITY_FILE in listed:
        from collections import Counter
        rows = read_ndjson(root / METRIC_ENTITY_FILE)
        counts = Counter(str(row.get("table") or "") for row in rows)
        declared_entities = totals.get("metricEntityFacts") or {}
        for table, key in ENTITY_TABLES.items():
            if counts.get(table, 0) != int(declared_entities.get(key) or 0):
                raise _err(
                    "E_BUNDLE_METRIC_COUNT",
                    f"entity fact count mismatch for {table}: "
                    f"file={counts.get(table, 0)} manifest={declared_entities.get(key)}",
                    path=METRIC_ENTITY_FILE,
                )
    declared_terms = int((manifest.get("source") or {}).get("tbox", {}).get("termEntries") or 0)
    if declared_terms:
        graph = Graph()
        try:
            graph.parse(root / "graph/tbox.ttl", format="turtle")
        except Exception as exc:  # noqa: BLE001 - report parse failure explicitly
            raise _err("E_BUNDLE_TBOX", f"cannot parse graph/tbox.ttl: {exc}") from exc
        actual_terms = _term_entry_count(graph)
        if actual_terms != declared_terms:
            raise _err(
                "E_BUNDLE_TERMS",
                f"term entry count mismatch: manifest={declared_terms} actual={actual_terms}",
                expected=declared_terms,
                actual=actual_terms,
            )

    return manifest


# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------


_BLOB_UPSERT = """
INSERT INTO platform.blob
  (hash, size, mime, tier, path, state, metadata, created_at, refcount,
   last_verified_at, verified_ok)
VALUES (%s, %s, %s, 'fs', %s, 'committed', %s, %s, %s, now(), true)
ON CONFLICT (hash) DO UPDATE SET
  size = EXCLUDED.size,
  mime = EXCLUDED.mime,
  tier = EXCLUDED.tier,
  path = EXCLUDED.path,
  state = EXCLUDED.state,
  metadata = EXCLUDED.metadata,
  refcount = EXCLUDED.refcount,
  deleted_at = NULL,
  last_verified_at = now(),
  verified_ok = true
"""

_BLOB_REF_INSERT = """
INSERT INTO platform.blob_ref (hash, owner_type, owner_id)
VALUES (%s, %s, %s)
ON CONFLICT (hash, owner_type, owner_id) DO NOTHING
"""


def _blob_plan(
    bundle_dir: Path, manifest: dict[str, Any], cfg: ConfigBundle
) -> dict[str, Any]:
    """Dry-run: count blobs that would be written, already present or broken."""

    declared = (manifest.get("totals") or {}).get("blobs") or {}
    blob_file = bundle_dir / BLOB_MANIFEST_FILE
    rows = read_ndjson(blob_file) if blob_file.is_file() else []
    fs = FsCasBackend(cfg.storage.root, cfg.storage.tmp_dir)
    to_write = 0
    existing = 0
    missing: list[str] = []
    conflicts: list[dict[str, Any]] = []
    for row in rows:
        sha = str(row["hash"])
        source = bundle_dir / "blobs" / sha[:2] / sha
        if not source.is_file():
            missing.append(sha)
            continue
        size = int(row["size"])
        if source.stat().st_size != size:
            conflicts.append({"hash": sha, "reason": "bundle size mismatch"})
            continue
        target = fs.path_for(sha)
        if target.is_file():
            if target.stat().st_size != size:
                conflicts.append({"hash": sha, "reason": "target size mismatch"})
            else:
                existing += 1
        else:
            to_write += 1
    return {
        "ok": not missing and not conflicts,
        "dryRun": True,
        "bundle": str(bundle_dir.resolve()),
        "blobs": {
            "included": bool(declared.get("included")),
            "total": len(rows),
            "bytes": sum(int(row["size"]) for row in rows),
            "toWrite": to_write,
            "existing": existing,
            "missing": len(missing),
            "conflicts": len(conflicts),
            "missingHashes": missing[:20],
            "conflictDetails": conflicts[:20],
        },
    }


def _restore_blobs(
    bundle_dir: Path, manifest: dict[str, Any], cfg: ConfigBundle
) -> dict[str, Any]:
    """Write every bundle blob into the target CAS, all-or-nothing.

    Files already present are re-verified and never rewritten. Any size or
    sha256 mismatch aborts the whole batch and removes files written by this
    call, so a caller can never observe a half-restored blob store.
    """

    declared = (manifest.get("totals") or {}).get("blobs") or {}
    blob_file = bundle_dir / BLOB_MANIFEST_FILE
    if not blob_file.is_file():
        if declared.get("included"):
            raise _err(
                "E_BUNDLE_BLOB_MISSING",
                "bundle declares blobs but meta/blobs.jsonl is missing",
            )
        return {"included": False, "rows": [], "written": [], "existing": 0}

    rows = read_ndjson(blob_file)
    fs = FsCasBackend(cfg.storage.root, cfg.storage.tmp_dir)
    fs.ensure_dirs()
    written: list[Path] = []
    existing = 0
    differences: list[dict[str, Any]] = []
    for row in rows:
        sha = str(row["hash"])
        size = int(row["size"])
        source = bundle_dir / "blobs" / sha[:2] / sha
        if not source.is_file():
            differences.append({"hash": sha, "reason": "payload missing from bundle"})
            continue
        if source.stat().st_size != size:
            differences.append({"hash": sha, "reason": "bundle size mismatch"})
            continue
        target = fs.path_for(sha)
        if target.is_file():
            if target.stat().st_size != size or _sha256_file(target) != sha:
                differences.append({"hash": sha, "reason": "target differs; refusing to overwrite"})
            else:
                existing += 1
            continue
        data = source.read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != sha:
            differences.append({"hash": sha, "reason": "bundle payload failed re-hash"})
            continue
        fs.write(sha, data)
        target = fs.path_for(sha)
        if target.stat().st_size != size or _sha256_file(target) != sha:
            differences.append({"hash": sha, "reason": "written file failed verification"})
            continue
        written.append(target)
    if differences:
        for path in written:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise _err(
            "E_BUNDLE_BLOBS",
            f"{len(differences)} blob(s) failed verification; batch aborted, "
            "no partially restored blob store was left behind",
            differences=differences[:20],
        )
    return {"included": True, "rows": rows, "written": written, "existing": existing}


def import_bundle(
    bundle: ConfigBundle,
    bundle_dir: str | Path,
    database: str = "platform_restore_test",
    replace: bool = False,
    keep_db_on_failure: bool = False,
    into_empty_target: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Restore a bundle into a throw-away database. Never writes ``platform``.

    ``into_empty_target`` is the explicit migration path: it allows the target
    to be the configured database itself, but only while that database holds no
    documents, fact events or metric observations (a freshly started stack).
    """

    cfg = bundle.config
    prod_name = urlsplit(cfg.database.url).path.lstrip("/")
    if database == prod_name:
        if not into_empty_target:
            return {
                "ok": False,
                "error": "refusing to import into the production database "
                "(use --into-empty-platform on a freshly started stack)",
                "providerCode": "E_BUNDLE_PROD_TARGET",
            }
        if not _target_is_empty(cfg.database.url):
            return {
                "ok": False,
                "error": f"database {database} already holds business data; "
                "an in-place restore is only allowed on an empty stack",
                "providerCode": "E_BUNDLE_TARGET_NOT_EMPTY",
            }

    step = "verify"
    runtime: Runtime | None = None
    created_graphs: list[str] = []
    target_url = _db_url(cfg.database.url, database)
    try:
        manifest = verify_bundle(bundle_dir)
        tag = _norm_tag(str(manifest.get("tag") or ""))
        expected = manifest.get("totals") or {}

        if dry_run:
            # Blob-only plan: report what a real import would write, never touch
            # the target database or the CAS.
            plan = _blob_plan(Path(bundle_dir), manifest, cfg)
            plan["tag"] = tag
            plan["counts"] = expected
            return plan

        # ---- create the restore database -------------------------------
        step = "create-database"
        if database == prod_name:
            # Opt-in in-place restore: keep the configured database as-is.
            pass
        elif _database_exists(cfg.database.url, database):
            if not replace:
                raise _err(
                    "E_BUNDLE_DB_EXISTS",
                    f"database {database} already exists (use --replace)",
                    database=database,
                )
            _drop_database(cfg.database.url, database)
        if database != prod_name:
            _create_database(cfg.database.url, database)

        # ---- restore runtime: same graph, separate metadata -----------
        step = "assemble"
        restore_abox = f"urn:platform:graph:restore:{tag}:abox"
        bundle_abox = Graph()
        abox_source = (Path(bundle_dir) / "graph/abox.ttl").read_bytes()
        if abox_source.strip():
            bundle_abox.parse(data=abox_source.decode("utf-8"), format="turtle")
        has_abox = len(bundle_abox) > 0
        # Non-empty A-Box: only run the SHACL gate (inferred graphs are rebuildable
        # and must not be written during a restore). Empty A-Box cannot be
        # "validated" (pyshacl rejects empty graphs), so fall back to a full
        # materialization of the restored T-Box, which is the only honest way to
        # satisfy the publish gate.
        restore_cfg = cfg.model_copy(
            update={
                "database": cfg.database.model_copy(update={"url": target_url}),
                "reasoning": cfg.reasoning.model_copy(
                    update={
                        "mode": "validate" if has_abox else "materialize",
                        "abox_graphs": [restore_abox] if has_abox else [],
                    }
                ),
            }
        )
        restore_bundle = ConfigBundle(
            config=restore_cfg,
            path=bundle.path,
            sources=dict(bundle.sources),
            warnings=list(bundle.warnings),
        )
        runtime = assemble(restore_bundle)
        runtime.metadata.open(retry_seconds=10.0)
        runtime.metadata.migrate()

        # ---- shapes -----------------------------------------------------
        step = "shapes"
        for item in manifest.get("source", {}).get("shapes") or []:
            runtime.shapes.deploy(
                item["namespace"],
                item["content"].encode("utf-8"),
                rdf_format=item.get("contentFormat") or "turtle",
                shapes_id=item["shapesId"],
                version=item["version"],
                source="restore",
                actor="import-bundle",
            )

        # ---- A-Box into an isolated restore graph -----------------------
        step = "abox"
        if has_abox:
            runtime.graph.replace_graph(restore_abox, abox_source, "turtle")
            created_graphs.append(restore_abox)

        # ---- T-Box through governance ----------------------------------
        step = "tbox-import"
        tbox_source = manifest["source"]["tbox"]
        imported = runtime.ontology.import_document(
            raw=(Path(bundle_dir) / "graph/tbox.ttl").read_bytes(),
            rdf_format="turtle",
            semver=tbox_source["semver"],
            label=f"restore:{tag}",
            actor="import-bundle",
            validate_shacl=True,
            check_consistency=False,
        )
        created_graphs.append(imported["graph"])
        if imported.get("unresolvedImports"):
            raise _err(
                "E_BUNDLE_TBOX_IMPORTS",
                f"unresolved owl:imports: {imported['unresolvedImports']}",
                imports=imported["unresolvedImports"],
            )
        if (imported.get("shacl") or {}).get("conforms") is False:
            raise _err(
                "E_BUNDLE_SHACL",
                "restored T-Box fails the SHACL gate",
                violations=(imported.get("shacl") or {}).get("violationCount"),
            )
        if not imported.get("usable", False):
            raise _err(
                "E_BUNDLE_TBOX_UNUSABLE",
                f"imported T-Box is not usable: {imported.get('usableReasons')}",
                reasons=imported.get("usableReasons"),
            )
        step = "tbox-publish"
        published = runtime.ontology.publish(
            imported["versionId"],
            acknowledge_breaking=True,
            actor="import-bundle",
            reason=f"bundle restore {tag}",
        )
        if str(published.get("id")) != str(imported["versionId"]):
            raise _err("E_BUNDLE_TBOX_PUBLISH", "publish returned an unexpected version id")
        created_graphs.append(
            f"{restore_cfg.reasoning.inferred_graph_prefix}{imported['versionId']}"
        )

        # ---- metadata rows ---------------------------------------------
        step = "metadata"
        imports = read_ndjson(Path(bundle_dir) / "meta/ontology_import.jsonl")
        documents = read_ndjson(Path(bundle_dir) / "meta/documents.jsonl")
        chunks = read_ndjson(Path(bundle_dir) / "meta/chunks.jsonl")
        with runtime.metadata.tx() as tx:
            tx.executemany(
                """
                INSERT INTO platform.ontology_import
                  (import_id, version_id, target_namespace, author, change_summary,
                   base_triples, total_triples, classes, object_properties,
                   data_properties, shapes_id, shapes_version, conforms,
                   violation_count, usable, reason, source_sha256, staging_graph,
                   payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        row["import_id"], row["version_id"], row["target_namespace"],
                        row["author"], row["change_summary"], int(row["base_triples"]),
                        int(row["total_triples"]), int(row["classes"]),
                        int(row["object_properties"]), int(row["data_properties"]),
                        row["shapes_id"], row["shapes_version"], row["conforms"],
                        int(row["violation_count"]), bool(row["usable"]), row["reason"],
                        row["source_sha256"], row["staging_graph"], Jsonb(row["payload"]),
                        row["created_at"],
                    )
                    for row in imports
                ],
            )
            tx.executemany(
                """
                INSERT INTO platform.document
                  (document_id, sha256, bucket, object_key, filename, mime_type,
                   size_bytes, status, page_count, char_count, chunk_count,
                   parser, parser_version, warnings, manifest, metadata,
                   created_at, parsed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s)
                """,
                [
                    (
                        row["document_id"], row["sha256"], row["bucket"],
                        row["object_key"], row["filename"], row["mime_type"],
                        int(row["size_bytes"]), row["status"], int(row["page_count"]),
                        int(row["char_count"]), int(row["chunk_count"]), row["parser"],
                        row["parser_version"], Jsonb(row["warnings"]),
                        Jsonb(row["manifest"]), Jsonb(row["metadata"]),
                        row["created_at"], row["parsed_at"],
                    )
                    for row in documents
                ],
            )
            tx.executemany(
                """
                INSERT INTO platform.document_chunk
                  (chunk_id, document_id, seq, page_from, page_to, char_start,
                   char_end, text, token_estimate, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        row["chunk_id"], row["document_id"], int(row["seq"]),
                        int(row["page_from"]), int(row["page_to"]),
                        int(row["char_start"]), int(row["char_end"]), row["text"],
                        int(row["token_estimate"]), row["created_at"],
                    )
                    for row in chunks
                ],
            )

        # ---- blobs (CAS payloads + references) --------------------------
        step = "blobs"
        blob_result = _restore_blobs(Path(bundle_dir), manifest, cfg)
        if blob_result["included"]:
            try:
                with runtime.metadata.tx() as tx:
                    tx.executemany(
                        _BLOB_UPSERT,
                        [
                            (
                                row["hash"],
                                int(row["size"]),
                                row["mime"],
                                f"blobs/{row['hash'][:2]}/{row['hash']}",
                                Jsonb(row.get("metadata") or {}),
                                _as_datetime(row.get("createdAt")),
                                len(row.get("refs") or []),
                            )
                            for row in blob_result["rows"]
                        ],
                    )
                    tx.executemany(
                        _BLOB_REF_INSERT,
                        [
                            (row["hash"], ref["ownerType"], ref["ownerId"])
                            for row in blob_result["rows"]
                            for ref in (row.get("refs") or [])
                        ],
                    )
            except Exception:
                for path in blob_result["written"]:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
                raise

        # ---- vectors ----------------------------------------------------
        step = "vectors"
        import numpy as np

        vec = np.load(Path(bundle_dir) / "vectors/embeddings.npz")
        vec_ids = vec["chunk_ids"].tolist()
        vec_rows = vec["embeddings"]
        model = manifest["source"]["embedding"]["model"]
        dimensions = int(manifest["source"]["embedding"]["dimensions"])
        document_of_chunk = chunks_by_id(chunks)
        by_document: dict[str, list[dict[str, Any]]] = {}
        for index, chunk_id in enumerate(vec_ids):
            document_id = document_of_chunk[chunk_id]
            by_document.setdefault(document_id, []).append(
                {"chunkId": chunk_id, "vector": vec_rows[index].tolist()}
            )
        for document_id, items in by_document.items():
            runtime.vectors.upsert(document_id, items, model, enforce_active=False)
        runtime.vectors.set_pointer(
            manifest["source"]["embedding"]["provider"], model, dimensions
        )

        # ---- fact ledger ------------------------------------------------
        step = "ledger"
        records = read_ndjson(Path(bundle_dir) / "ledger/fact_events.jsonl")
        facts, error = reconstruct(records)
        if error:
            raise _err("E_BUNDLE_LEDGER_REPLAY", error)
        _insert_replay(runtime.metadata, records, facts)

        # ---- metric registry, observations and entity facts -------------
        step = "metrics"
        root = Path(bundle_dir)
        definitions = (
            read_ndjson(root / METRIC_DEFINITIONS_FILE)
            if (root / METRIC_DEFINITIONS_FILE).is_file() else []
        )
        observations = (
            read_ndjson(root / METRIC_OBSERVATIONS_FILE)
            if (root / METRIC_OBSERVATIONS_FILE).is_file() else []
        )
        entity_facts = (
            read_ndjson(root / METRIC_ENTITY_FILE)
            if (root / METRIC_ENTITY_FILE).is_file() else []
        )
        page_rows = (
            read_ndjson(root / DOCUMENT_PAGES_FILE)
            if (root / DOCUMENT_PAGES_FILE).is_file() else []
        )
        with runtime.metadata.tx() as tx:
            if definitions:
                tx.executemany(
                    _METRIC_DEF_UPSERT,
                    [_metric_def_params(row) for row in definitions],
                )
            if observations:
                tx.executemany(
                    _METRIC_OBS_UPSERT,
                    [_metric_obs_params(row) for row in observations],
                )
            insurance = [
                _ins_params(row) for row in entity_facts
                if row.get("table") == "platform.ins_payment_record"
            ]
            loans = [
                _loan_params(row) for row in entity_facts
                if row.get("table") == "platform.loan_installment_plan"
            ]
            if insurance:
                tx.executemany(_INS_UPSERT, insurance)
            if loans:
                tx.executemany(_LOAN_UPSERT, loans)
            if page_rows:
                tx.executemany(
                    """
                    INSERT INTO platform.document_page
                      (document_id, page_number, text, char_count)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (document_id, page_number) DO UPDATE SET
                      text = EXCLUDED.text,
                      char_count = EXCLUDED.char_count
                    """,
                    [
                        (
                            row["document_id"], int(row["page_number"]),
                            row["text"], int(row["char_count"]),
                        )
                        for row in page_rows
                    ],
                )

        # ---- consistency checks -----------------------------------------
        step = "checks"
        checks = _verify_restored(
            runtime, manifest, vec_ids, vec_rows, restore_abox, chunks,
            blob_result["rows"],
        )
        ok = all(item["ok"] for item in checks)
        return {
            "ok": ok,
            "database": database,
            "bundle": str(Path(bundle_dir).resolve()),
            "tbox": {
                "versionId": imported["versionId"],
                "contentHash": imported["contentHash"],
                "graph": imported["graph"],
            },
            "tboxPointer": runtime.ontology.current(),
            "aboxGraph": restore_abox,
            "checks": checks,
            "ledger": {"events": len(records), "facts": len(facts), "chain": chain_ok(records)},
            "blobs": {
                "included": bool(blob_result["included"]),
                "count": len(blob_result["rows"]),
                "bytes": sum(int(row["size"]) for row in blob_result["rows"]),
                "written": len(blob_result["written"]),
                "existing": blob_result["existing"],
            },
            "counts": expected,
        }
    except (PortError, PlatformError) as exc:
        code = getattr(exc, "provider_code", None) or getattr(exc, "code", "E_BUNDLE_FAILED")
        message = getattr(exc, "message", None) or getattr(exc, "detail", str(exc))
        if runtime is not None:
            for iri in created_graphs:
                try:
                    runtime.graph.clear_graph(iri)
                except Exception:  # noqa: BLE001 - cleanup must not mask the failure
                    pass
            runtime.close()
            runtime = None
        if not keep_db_on_failure:
            try:
                _drop_database(cfg.database.url, database)
            except Exception:  # noqa: BLE001
                pass
        return {
            "ok": False,
            "failedStep": step,
            "database": database,
            "error": message,
            "providerCode": code,
            "details": getattr(exc, "details", None),
        }
    except Exception as exc:  # noqa: BLE001 - always report a concrete failure
        if runtime is not None:
            for iri in created_graphs:
                try:
                    runtime.graph.clear_graph(iri)
                except Exception:  # noqa: BLE001
                    pass
            runtime.close()
            runtime = None
        if not keep_db_on_failure:
            try:
                _drop_database(cfg.database.url, database)
            except Exception:  # noqa: BLE001
                pass
        return {
            "ok": False,
            "failedStep": step,
            "database": database,
            "error": f"{type(exc).__name__}: {exc}",
            "providerCode": "E_BUNDLE_FAILED",
        }
    finally:
        if runtime is not None:
            try:
                runtime.close()
            except Exception:  # noqa: BLE001
                pass


def chunks_by_id(chunks: list[dict[str, Any]]) -> dict[str, str]:
    return {row["chunk_id"]: row["document_id"] for row in chunks}


def chain_ok(records: list[dict[str, Any]]) -> dict[str, Any]:
    return verify_records(records)


def _verify_restored(
    runtime: Runtime,
    manifest: dict[str, Any],
    vec_ids: list[str],
    vec_rows: Any,
    restore_abox: str,
    chunks: list[dict[str, Any]],
    blob_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    import numpy as np

    totals = manifest["totals"]
    model = manifest["source"]["embedding"]["model"]
    dimensions = int(manifest["source"]["embedding"]["dimensions"])
    rows = []

    def add(name: str, exported: Any, imported: Any, ok: bool, detail: str | None = None) -> None:
        rows.append(
            {
                "name": name,
                "exported": exported,
                "imported": imported,
                "ok": bool(ok),
                "detail": detail,
            }
        )

    doc_count = int(runtime.metadata.query("SELECT COUNT(*) AS n FROM platform.document")[0]["n"])
    add("documents", totals["documents"], doc_count, doc_count == int(totals["documents"]))

    chunk_count = int(
        runtime.metadata.query("SELECT COUNT(*) AS n FROM platform.document_chunk")[0]["n"]
    )
    add("chunks", totals["chunks"], chunk_count, chunk_count == int(totals["chunks"]))

    vec_count = int(
        runtime.metadata.query(
            "SELECT COUNT(*) AS n FROM platform.chunk_embedding WHERE model = %s",
            (model,),
        )[0]["n"]
    )
    restored_ids = runtime.metadata.query(
        "SELECT chunk_id FROM platform.chunk_embedding WHERE model = %s ORDER BY chunk_id",
        (model,),
    )
    restored_set = {row["chunk_id"] for row in restored_ids}
    sample = [vec_ids[index] for index in _sample_indices(len(vec_ids), VECTOR_SAMPLE)]
    min_cosine = 1.0
    if sample:
        restored = runtime.metadata.query(
            "SELECT chunk_id, embedding::text AS embedding "
            "FROM platform.chunk_embedding WHERE model = %s AND chunk_id = ANY(%s)",
            (model, sample),
        )
        found = {row["chunk_id"]: row["embedding"] for row in restored}
        index_map = {chunk_id: index for index, chunk_id in enumerate(vec_ids)}
        for chunk_id in sample:
            if chunk_id not in found:
                min_cosine = -1.0
                break
            raw = found[chunk_id].strip()
            if raw.startswith("["):
                raw = raw[1:-1]
            actual = np.fromstring(raw, sep=",", dtype=np.float32)
            expected = vec_rows[index_map[chunk_id]]
            denom = float(np.linalg.norm(actual) * np.linalg.norm(expected))
            cosine = float(np.dot(actual, expected) / denom) if denom else 0.0
            min_cosine = min(min_cosine, cosine)
    vec_ok = (
        vec_count == int(totals["embeddings"])
        and restored_set == set(vec_ids)
        and len(sample) == min(VECTOR_SAMPLE, len(vec_ids))
        and min_cosine >= 0.999
    )
    add(
        "vectors",
        totals["embeddings"],
        vec_count,
        vec_ok,
        f"sample={len(sample)} minCosine={min_cosine:.6f} dims={dimensions}",
    )

    pointer = runtime.ontology.current()
    tbox_triples = runtime.ontology.graph_count(pointer["versionId"])
    abox_triples = runtime.graph.count_graph(restore_abox)
    triple_total = tbox_triples + abox_triples
    add(
        "triples",
        totals["triples"],
        triple_total,
        triple_total == int(totals["triples"]),
        f"tbox={tbox_triples} abox={abox_triples}",
    )

    fact_events = int(
        runtime.metadata.query("SELECT COUNT(*) AS n FROM platform.fact_event")[0]["n"]
    )
    fact_assertions = int(
        runtime.metadata.query("SELECT COUNT(*) AS n FROM platform.fact_assertion")[0]["n"]
    )
    add(
        "facts",
        totals["factEvents"],
        fact_events,
        fact_events == int(totals["factEvents"])
        and fact_assertions == int(totals.get("factAssertions") or 0),
        f"assertions={fact_assertions}",
    )

    if "metricDefinitions" in totals:
        metric_count = int(
            runtime.metadata.query("SELECT COUNT(*) AS n FROM platform.metric_definition")[0]["n"]
        )
        restored_defs = runtime.metadata.query(
            f"SELECT {', '.join(_METRIC_DEF_COLUMNS)} FROM platform.metric_definition"
        )
        defs_ok = (
            metric_count == int(totals["metricDefinitions"])
            and _metric_def_hash(restored_defs) == str(totals.get("metricDefinitionsHash") or "")
        )
        add(
            "metricDefinitions",
            totals["metricDefinitions"],
            metric_count,
            defs_ok,
            f"hash={_metric_def_hash(restored_defs)[:12]}",
        )
    if "metricObservations" in totals:
        obs_count = int(
            runtime.metadata.query(
                "SELECT COUNT(*) AS n FROM platform.metric_observation"
            )[0]["n"]
        )
        add(
            "metricObservations",
            totals["metricObservations"],
            obs_count,
            obs_count == int(totals["metricObservations"]),
        )
    if "documentPages" in totals:
        page_count = int(
            runtime.metadata.query(
                "SELECT COUNT(*) AS n FROM platform.document_page"
            )[0]["n"]
        )
        add(
            "documentPages",
            totals["documentPages"],
            page_count,
            page_count == int(totals["documentPages"]),
        )
    declared_entities = totals.get("metricEntityFacts") or {}
    if declared_entities:
        for table, key in ENTITY_TABLES.items():
            entity_count = int(
                runtime.metadata.query(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"]
            )
            add(
                f"entity:{table.split('.')[-1]}",
                int(declared_entities.get(key) or 0),
                entity_count,
                entity_count == int(declared_entities.get(key) or 0),
            )

    declared_blobs = totals.get("blobs") or {}
    if declared_blobs.get("included"):
        target_blobs = runtime.metadata.query(
            """
            SELECT hash, size FROM platform.blob WHERE state = 'committed'
            """
        )
        by_hash = {str(row["hash"]): int(row["size"]) for row in target_blobs}
        bundle_rows = list(blob_rows or [])
        missing = []
        size_bad = []
        declared_bytes = 0
        for row in bundle_rows:
            sha = str(row["hash"])
            size = int(row["size"])
            declared_bytes += size
            if sha not in by_hash:
                missing.append(sha)
            elif by_hash[sha] != size:
                size_bad.append(sha)
        import_hashes = {
            str(row["hash"])
            for row in runtime.metadata.query(
                """
                SELECT DISTINCT hash FROM platform.blob_ref
                 WHERE owner_id LIKE 'ontology/sources/%%'
                """
            )
        }
        bundled = {str(row["hash"]) for row in bundle_rows}
        extras = [
            sha for sha in by_hash
            if sha not in bundled and sha not in import_hashes
        ]
        refs_declared = sum(len(row.get("refs") or []) for row in bundle_rows)
        refs_restored = int(
            runtime.metadata.query("SELECT COUNT(*) AS n FROM platform.blob_ref")[0]["n"]
        )
        # Import regenerates one ontology source TTL for provenance, so the
        # aggregate store can be one blob larger than the bundle. The contract
        # asserted here is stronger than a total: every bundled blob exists with
        # the exact byte size, and no unexplained extra blob appears.
        blobs_ok = (
            not missing
            and not size_bad
            and not extras
            and refs_restored >= refs_declared
        )
        extra_bytes = sum(by_hash[sha] for sha in extras)
        generated = [sha for sha in by_hash if sha not in bundled and sha in import_hashes]
        generated_bytes = sum(by_hash[sha] for sha in generated)
        add(
            "blobs",
            declared_blobs.get("count") or 0,
            len(bundle_rows) - len(missing),
            blobs_ok,
            f"bytes={declared_bytes} missing={len(missing)} "
            f"sizeBad={len(size_bad)} refs={refs_restored}/{refs_declared} "
            f"unexplainedExtras={len(extras)}(+{extra_bytes}B) "
            f"importGenerated={len(generated)}(+{generated_bytes}B)",
        )

    restored_graph = Graph()
    nt = runtime.graph.export_graph(pointer["graph"])
    if nt.strip():
        restored_graph.parse(data=nt.decode("utf-8"), format="nt")
    restored_canonical = _canonical_hash(restored_graph)
    declared_terms = int(manifest["source"]["tbox"].get("termEntries") or 0)
    if declared_terms:
        actual_terms = _term_entry_count(restored_graph)
        add(
            "termEntries",
            declared_terms,
            actual_terms,
            actual_terms == declared_terms,
        )
    expected_canonical = manifest["source"]["tbox"].get("canonicalHash") or manifest["source"]["tbox"][
        "contentHash"
    ]
    pointer_ok = restored_canonical == expected_canonical
    add(
        "tboxPointerHash",
        expected_canonical,
        restored_canonical,
        pointer_ok,
        f"sourceBytesHash export={manifest['source']['tbox']['contentHash']} "
        f"import={pointer.get('contentHash')}",
    )

    query = ""
    for row in chunks:
        text = (row.get("text") or "").strip()
        if text:
            query = text[:60]
            break
    try:
        result = runtime.search.hybrid_search(query, limit=1)
        hits = result.get("results") or []
        search_ok = bool(hits)
        detail = f"routes={result.get('routes')} lexicalOnly={result.get('lexicalOnly')}"
    except (PortError, PlatformError) as exc:
        hits = []
        search_ok = False
        detail = getattr(exc, "provider_code", None) or getattr(exc, "message", str(exc))
    add("hybridSearch", ">=1 hit", len(hits), search_ok, detail)

    return rows


def _sample_indices(total: int, count: int) -> list[int]:
    if total <= count:
        return list(range(total))
    step = max(1, math.floor(total / count))
    return [min(total - 1, index * step) for index in range(count)]
