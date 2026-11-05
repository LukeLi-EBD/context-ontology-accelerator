"""S10 audit replay: rebuild the assertion ledger from an exported event chain.

No new dependencies: psycopg is already the metadata driver. A real replay creates
a throw-away database on the configured PostgreSQL server, applies the same SQL
migrations, then fills it only from the NDJSON events. `--dry-run` stops after
chain verification and in-memory reconstruction.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg.types.json import Jsonb

from .adapters.metadata_pg import MetadataPg
from .fact_export import read_ndjson
from .facts import _row, verify_records

def _admin_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/postgres", parts.query, parts.fragment))


def _replay_url(url: str, name: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{name}", parts.query, parts.fragment))


def _create_database(url: str, name: str) -> None:
    with psycopg.connect(_admin_url(url), autocommit=True, connect_timeout=10) as conn:
        conn.execute(f'CREATE DATABASE "{name}"')


def _drop_database(url: str, name: str) -> None:
    with psycopg.connect(_admin_url(url), autocommit=True, connect_timeout=10) as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def _blank(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject": payload.get("subject"),
        "predicate": payload.get("predicate"),
        "objectKind": payload.get("objectKind", "iri"),
        "object": payload.get("object"),
        "graph": payload.get("graph"),
        "state": "active",
        "acceptedConflict": False,
        "resolution": None,
        "supersededBy": None,
        "mergedFrom": None,
        "sourceDocumentId": None,
        "sourceRunId": None,
    }


def reconstruct(records: list[dict[str, Any]]) -> tuple[dict[str, Any], str | None]:
    """Replay events in order into a factId -> assertion map."""
    facts: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        action = record.get("action")
        fact_id = record.get("factId")
        payload = record.get("payload") or {}
        source = record.get("source") or {}
        if action == "asserted":
            fact = _blank(payload)
            fact["sourceDocumentId"] = source.get("documentId")
            fact["sourceRunId"] = source.get("runId")
            facts[fact_id] = fact
            continue
        if action == "merged":
            fact = _blank(payload)
            fact["resolution"] = "merge"
            fact["mergedFrom"] = payload.get("from") or []
            fact["sourceDocumentId"] = source.get("documentId")
            fact["sourceRunId"] = source.get("runId")
            facts[fact_id] = fact
            continue
        if action == "purged_test_graph":
            # S12/OQ-45: cleanup is part of the chain, so replay must drop the fact
            # instead of resurrecting an assertion the export snapshot no longer has.
            facts.pop(fact_id, None)
            continue
        if fact_id not in facts:
            return {}, (
                f"event {record.get('eventId')} ({action}) references unknown fact "
                f"{fact_id}; export window is incomplete"
            )
        fact = facts[fact_id]
        if action in ("retracted", "batch_retracted"):
            fact["state"] = "retracted"
        elif action == "restored":
            fact["state"] = "active"
        elif action == "conflict_kept":
            fact["state"] = "active" if payload.get("role") == "kept" else "retracted"
            fact["resolution"] = "keep"
        elif action == "conflict_accepted":
            fact["acceptedConflict"] = True
            fact["resolution"] = "accepted_conflict"
        elif action == "merge_superseded":
            fact["state"] = "retracted"
            fact["resolution"] = "merge"
            fact["supersededBy"] = payload.get("supersededBy")
        elif action == "unmerged":
            fact["resolution"] = None
            if payload.get("role") == "restored":
                fact["state"] = "active"
                fact["supersededBy"] = None
                fact["acceptedConflict"] = False
            else:
                fact["state"] = "retracted"
        elif action == "resolution_undo":
            if payload.get("role") == "retired_restored":
                fact["state"] = "active"
                fact["supersededBy"] = None
            fact["acceptedConflict"] = False
            fact["resolution"] = None
        else:
            return {}, f"unknown event action at index {index}: {action!r}"
    return facts, None


def _norm(item: dict[str, Any]) -> dict[str, Any]:
    raw = item.get("object")
    if isinstance(raw, dict):
        object_kind = raw.get("kind") or item.get("objectKind")
        object_value = raw.get("value")
    else:
        object_kind = item.get("objectKind")
        object_value = raw
    return {
        "subject": item.get("subject"),
        "predicate": item.get("predicate"),
        "objectKind": object_kind,
        "object": object_value,
        "graph": item.get("graph"),
        "state": item.get("state"),
        "acceptedConflict": bool(item.get("acceptedConflict")),
        "resolution": item.get("resolution"),
        "supersededBy": item.get("supersededBy"),
        "mergedFrom": item.get("mergedFrom") or None,
    }


def compare(replayed: dict[str, dict[str, Any]],
            snapshot: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {item["factId"]: _norm(item) for item in snapshot}
    matched = 0
    mismatched: list[dict[str, Any]] = []
    for fact_id, want in expected.items():
        got = replayed.get(fact_id)
        if got is None:
            mismatched.append({"factId": fact_id, "field": "missing"})
            continue
        diffs = {
            key: {"expected": want[key], "actual": got.get(key)}
            for key in want if want[key] != got.get(key)
        }
        if diffs:
            mismatched.append({"factId": fact_id, "fields": diffs})
        else:
            matched += 1
    extra = sorted(set(replayed) - set(expected))
    return {
        "matched": matched, "mismatched": mismatched, "extra": extra,
        "ok": not mismatched and not extra,
    }


def _insert_replay(meta: MetadataPg, records: list[dict[str, Any]],
                   facts: dict[str, dict[str, Any]]) -> None:
    with meta.tx() as tx:
        for record in records:
            created_at = record.get("createdAt")
            if created_at:
                created_at = datetime.fromisoformat(str(created_at))
            tx.execute(
                """
                INSERT INTO platform.fact_event
                  (event_id, fact_id, action, actor, reason, batch_id, payload,
                   prev_event, hash, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                        COALESCE(%s::timestamptz, now()))
                """,
                (
                    int(record["eventId"]), record["factId"], record["action"],
                    record.get("actor"), record.get("reason"), record.get("batchId"),
                    Jsonb(record.get("payload") or {}), record.get("prevEvent"),
                    record.get("hash"), created_at,
                ),
            )
        for fact_id, fact in facts.items():
            merged_from = fact.get("mergedFrom") or None
            tx.execute(
                """
                INSERT INTO platform.fact_assertion
                  (fact_id, subject_iri, predicate_iri, object_kind, object_value,
                   graph_iri, source_kind, source_document_id, source_run_id,
                   state, accepted_conflict, resolution, superseded_by, merged_from)
                VALUES (%s, %s, %s, %s, %s, %s, 'import', %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    fact_id, fact["subject"], fact["predicate"],
                    fact["objectKind"], fact["object"], fact["graph"],
                    fact.get("sourceDocumentId"), fact.get("sourceRunId"),
                    fact["state"], bool(fact.get("acceptedConflict")),
                    fact.get("resolution"), fact.get("supersededBy"),
                    Jsonb(merged_from) if merged_from else None,
                ),
            )


def replay_file(
    path: str | Path,
    snapshot_path: str | Path | None = None,
    dry_run: bool = False,
    database_url: str | None = None,
    keep_db: bool = False,
) -> dict[str, Any]:
    try:
        records = read_ndjson(path)
    except (OSError, ValueError) as exc:
        return {"ok": False, "events": 0, "error": f"cannot read NDJSON: {exc}"}
    chain = verify_records(records)
    if not chain.get("ok"):
        return {
            "ok": False, "events": len(records), "chain": chain,
            "error": "audit chain verification failed; replay refused",
        }
    facts, error = reconstruct(records)
    if error:
        return {"ok": False, "events": len(records), "chain": chain, "error": error}

    reference = snapshot_path
    if reference is None:
        candidate = Path(path).with_name("assertions.ndjson")
        if candidate.is_file():
            reference = str(candidate)
    snapshot: list[dict[str, Any]] | None = None
    if reference is not None:
        try:
            snapshot = read_ndjson(reference)
        except (OSError, ValueError) as exc:
            return {"ok": False, "error": f"cannot read snapshot: {exc}"}

    result: dict[str, Any] = {
        "ok": True, "dryRun": bool(dry_run), "events": len(records),
        "facts": len(facts), "chain": chain,
        "snapshot": str(reference) if reference is not None else None,
    }
    if snapshot is not None:
        result.update(compare(facts, snapshot))
        result["ok"] = not result["mismatched"] and not result["extra"]
    if dry_run:
        return result

    if not database_url:
        result["ok"] = False
        result["error"] = "databaseUrl is required for a real replay"
        return result

    name = f"platform_replay_{uuid.uuid4().hex[:10]}"
    try:
        _create_database(database_url, name)
        meta = MetadataPg(_replay_url(database_url, name))
        try:
            meta.open(retry_seconds=10.0)
            meta.migrate()
            _insert_replay(meta, records, facts)
            rows = meta.query("SELECT * FROM platform.fact_assertion")
            replayed = {row["fact_id"]: _norm(_row(row)) for row in rows}
        finally:
            meta.close()
        result["database"] = name
        result["facts"] = len(replayed)
        if snapshot is not None:
            result.update(compare(replayed, snapshot))
            result["ok"] = not result["mismatched"] and not result["extra"]
        result["replayed"] = True
        return result
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        result["ok"] = False
        result["error"] = f"replay failed: {exc}"
        return result
    finally:
        if not keep_db:
            try:
                _drop_database(database_url, name)
            except Exception:  # noqa: BLE001 - cleanup must not mask the result
                result["cleanupError"] = f"database {name} was not dropped"
