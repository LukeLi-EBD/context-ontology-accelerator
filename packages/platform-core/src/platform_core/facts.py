"""S8 fact governance: assertion ledger over PG, active projection over the A-Box.

Design (S8 section 2): an assertion is a first-class row with source/status/audit.
Retraction is an explicit state change, never an overwrite. The graph only holds
ACTIVE assertions, so SPARQL and materialization see the current truth while the
ledger keeps the full history.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime
from typing import Any

from psycopg.types.json import Jsonb
from rdflib import Literal, URIRef

from .adapters.metadata_pg import MetadataPg
from .errors import PortError
from .ports import Manifest

IRI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^<>\"{}|^`\\\s]+$")
STATES = ("active", "retracted", "superseded")
SOURCE_KINDS = ("extraction", "manual", "import")
# Adjudication is append-only in `fact_event`; the undo events point back at the
# adjudication they reverse, so the console can show both (what was decided and
# whether it still holds) without a second table.
ADJUDICATION_ACTIONS = ("conflict_kept", "conflict_accepted", "merged")
UNDO_ACTIONS = ("resolution_undo", "unmerged")
_ADJUDICATION_LABELS = {
    "conflict_kept": "keep",
    "conflict_accepted": "keep_both",
    "merged": "merge",
    "resolution_undo": "undo",
    "unmerged": "undo",
}
PLATFORM_GRAPH_PREFIX = "urn:platform:"
# Document facts are materialised into the COA A-Box graph
# ``{NDB_GRAPH_URI_BASE}/{namespace}/{ontology}``.  The ledger has to record the
# graph that actually holds the triple, otherwise retract/restore would delete
# from a graph the triple was never written to.  The base is read from the
# environment (the same key the metric service uses); when it is unset no A-Box
# graph is accepted and the caller gets an explicit E_FACT_BAD_GRAPH.
ABOX_GRAPH_BASE_ENV = "NDB_GRAPH_URI_BASE"


def _abox_graph_prefixes() -> tuple[str, ...]:
    base = (os.environ.get(ABOX_GRAPH_BASE_ENV) or "").strip().rstrip("/")
    return (f"{base}/",) if base else ()


def _graph_ok(graph: str) -> bool:
    if not IRI_RE.match(graph or ""):
        return False
    if graph.startswith(PLATFORM_GRAPH_PREFIX):
        return True
    return any(graph.startswith(prefix) for prefix in _abox_graph_prefixes())


def _err(code: str, detail: str, provider_code: str, **details: Any) -> PortError:
    return PortError(
        code=code,
        message=detail,
        provider="platform",
        provider_code=provider_code,
        details=details,
    )


def _term(value: str, kind: str) -> str:
    return URIRef(value).n3() if kind == "iri" else Literal(value).n3()


def event_body(event_id: int, fact_id: str, action: str, actor: str | None,
               reason: str | None, batch_id: str | None,
               payload: dict[str, Any]) -> dict[str, Any]:
    """Canonical event content. The hash covers every field except timestamps."""
    return {
        "eventId": int(event_id),
        "factId": fact_id,
        "action": action,
        "actor": actor,
        "reason": reason,
        "batchId": batch_id,
        "payload": payload or {},
    }


def event_hash(prev_hash: str, body: dict[str, Any]) -> str:
    text = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev_hash + "\n" + text).encode("utf-8")).hexdigest()


def _parse_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def verify_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute the hash chain. Any edited/removed/reordered event fails."""
    prev_id: int | None = None
    prev_hash = ""
    for index, record in enumerate(records):
        if index and int(record.get("prevEvent") or 0) != prev_id:
            return {
                "ok": False, "checked": index,
                "error": f"event {record['eventId']} prevEvent="
                         f"{record.get('prevEvent')} expected={prev_id}",
            }
        body = event_body(
            int(record["eventId"]), record["factId"], record["action"],
            record.get("actor"), record.get("reason"), record.get("batchId"),
            record.get("payload") or {},
        )
        digest = event_hash(prev_hash, body)
        if digest != record.get("hash"):
            return {
                "ok": False, "checked": index,
                "error": f"event {record['eventId']} hash mismatch "
                         f"(recomputed {digest[:12]}, file {str(record.get('hash'))[:12]})",
            }
        prev_id = int(record["eventId"])
        prev_hash = digest
    return {"ok": True, "checked": len(records), "error": None}


def _row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "factId": row["fact_id"],
        "subject": row["subject_iri"],
        "predicate": row["predicate_iri"],
        "object": {
            "kind": row["object_kind"],
            "value": row["object_value"],
            **({"iri": row["object_value"]} if row["object_kind"] == "iri" else {}),
        },
        "graph": row["graph_iri"],
        "state": row["state"],
        "source": {
            "kind": row["source_kind"],
            "documentId": row["source_document_id"],
            "runId": row["source_run_id"],
            "candidateId": row["candidate_id"],
        },
        "assertedAt": row["asserted_at"].isoformat(),
        "retractedAt": row["retracted_at"].isoformat() if row["retracted_at"] else None,
        "retractReason": row["retract_reason"],
        "acceptedConflict": bool(row.get("accepted_conflict")),
        "resolution": row.get("resolution"),
        "resolvedBy": row.get("resolved_by"),
        "resolvedAt": row.get("resolved_at").isoformat() if row.get("resolved_at") else None,
        "supersededBy": row.get("superseded_by"),
        "mergedFrom": row.get("merged_from"),
    }


class FactLedger:
    port = "FactLedger"

    def __init__(self, metadata: MetadataPg, graph: Any) -> None:
        self._meta = metadata
        self._graph = graph

    def manifest(self) -> Manifest:
        return Manifest(
            provider="platform",
            port=self.port,
            provider_version="s10.1",
            capabilities=[
                "fact.record", "fact.retract", "fact.retract_by_source",
                "fact.batch_retract", "fact.events",
                "fact.restore", "fact.list", "fact.conflicts",
                "fact.conflict_adjudications",
                "fact.conflict_resolve", "fact.conflict_undo",
                "fact.conflict_batch", "fact.audit_export", "fact.audit_verify",
                "fact.audit_replay", "fact.annotate",
            ],
            limits={"maxLimit": 500},
            notes={
                "slice": "S10",
                "retraction": "explicit state, never an overwrite",
                "audit": "append-only fact_event with prev_event/hash chain",
                "conflicts": "operator adjudication only: keep/keep both/merge",
                "undo": "adjudication is reversible via unmerged/resolution_undo events",
            },
        )

    # ---- write -----------------------------------------------------------

    def record(
        self,
        subject: str,
        predicate: str,
        object_value: str,
        object_kind: str,
        graph: str,
        source_kind: str = "manual",
        source_document_id: str | None = None,
        source_run_id: str | None = None,
        candidate_id: str | None = None,
        actor: str = "api",
    ) -> dict[str, Any]:
        for value, label in ((subject, "subject"), (predicate, "predicate")):
            if not IRI_RE.match(value or ""):
                raise _err(
                    "InvalidArgument", f"fact {label} is not an IRI: {value!r}",
                    "E_FACT_BAD_IRI", field=label, value=value,
                )
        if object_kind not in ("iri", "literal"):
            raise _err(
                "InvalidArgument", f"objectKind must be iri|literal, got {object_kind!r}",
                "E_FACT_BAD_IRI", field="objectKind", value=object_kind,
            )
        if object_kind == "iri" and not IRI_RE.match(object_value or ""):
            raise _err(
                "InvalidArgument", f"fact object is not an IRI: {object_value!r}",
                "E_FACT_BAD_IRI", field="object", value=object_value,
            )
        if source_kind not in SOURCE_KINDS:
            raise _err(
                "InvalidArgument", f"unsupported source kind: {source_kind!r}",
                "E_FACT_BAD_SOURCE", allowed=list(SOURCE_KINDS),
            )
        if not _graph_ok(graph):
            raise _err(
                "InvalidArgument",
                f"graph must be a urn:platform: IRI or an A-Box graph under "
                f"{os.environ.get(ABOX_GRAPH_BASE_ENV) or ABOX_GRAPH_BASE_ENV + ' (unset)'}, "
                f"got {graph!r}",
                "E_FACT_BAD_GRAPH", graph=graph,
            )
        self.ensure_chain()

        existing = self._meta.query(
            """
            SELECT * FROM platform.fact_assertion
             WHERE state = 'active' AND subject_iri = %s AND predicate_iri = %s
               AND object_kind = %s AND object_value = %s AND graph_iri = %s
               AND COALESCE(source_document_id, '') = %s
               AND COALESCE(source_run_id, '') = %s
            """,
            (
                subject, predicate, object_kind, object_value, graph,
                source_document_id or "", source_run_id or "",
            ),
        )
        if existing:
            fact = _row(existing[0])
            fact["duplicate"] = True
            self._mark_conflicts([fact])
            return fact

        fact_id = f"fact-{uuid.uuid4().hex[:12]}"
        with self._meta.tx() as tx:
            tx.execute(
                """
                INSERT INTO platform.fact_assertion (
                  fact_id, subject_iri, predicate_iri, object_kind, object_value,
                  graph_iri, source_kind, source_document_id, source_run_id, candidate_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    fact_id, subject, predicate, object_kind, object_value,
                    graph, source_kind, source_document_id, source_run_id, candidate_id,
                ),
            )
            self._event(tx, fact_id, "asserted", actor, None, None, {
                "subject": subject, "predicate": predicate,
                "object": object_value, "objectKind": object_kind, "graph": graph,
            })
        fact = self.get(fact_id)
        fact["duplicate"] = False
        self._insert_triple(self._fetch(fact_id))
        self._mark_conflicts([fact])
        return fact

    def retract(self, fact_id: str, reason: str | None = None, actor: str = "api") -> dict[str, Any]:
        return self._retract_one(fact_id, reason, actor, None)

    def _retract_one(
        self, fact_id: str, reason: str | None, actor: str, batch_id: str | None
    ) -> dict[str, Any] | None:
        row = self._fetch(fact_id)
        if row is None:
            raise _err("NotFound", f"fact not found: {fact_id}", "E_FACT_NOT_FOUND", factId=fact_id)
        if row["state"] != "active":
            return None
        self.ensure_chain()
        with self._meta.tx() as tx:
            updated = tx.execute(
                """
                UPDATE platform.fact_assertion
                   SET state = 'retracted', updated_at = now(), retracted_at = now(),
                       retract_reason = %s
                 WHERE fact_id = %s AND state = 'active'
                """,
                (reason, fact_id),
            )
            if updated:
                self._event(
                    tx, fact_id, "batch_retracted" if batch_id else "retracted",
                    actor, reason, batch_id,
                    {"subject": row["subject_iri"], "predicate": row["predicate_iri"],
                     "object": row["object_value"], "graph": row["graph_iri"]},
                )
        if not updated:
            return None
        remaining = self._meta.query(
            """
            SELECT COUNT(*) AS n FROM platform.fact_assertion
             WHERE state = 'active' AND subject_iri = %s AND predicate_iri = %s
               AND object_kind = %s AND object_value = %s AND graph_iri = %s
            """,
            (
                row["subject_iri"], row["predicate_iri"], row["object_kind"],
                row["object_value"], row["graph_iri"],
            ),
        )
        if int(remaining[0]["n"]) == 0:
            self._delete_triple(row)
        fact = self._fetch(fact_id)
        return _row(fact)

    def retract_by_source(
        self,
        document_id: str | None = None,
        run_id: str | None = None,
        reason: str | None = None,
        actor: str = "api",
    ) -> dict[str, Any]:
        if not document_id and not run_id:
            raise _err(
                "InvalidArgument",
                "one of sourceDocumentId/sourceRunId is required",
                "E_FACT_BAD_SOURCE",
            )
        self.ensure_chain()
        clauses = ["state = 'active'"]
        params: list[Any] = []
        if document_id:
            clauses.append("source_document_id = %s")
            params.append(document_id)
        if run_id:
            clauses.append("source_run_id = %s")
            params.append(run_id)
        rows = self._meta.query(
            "SELECT fact_id FROM platform.fact_assertion WHERE "
            + " AND ".join(clauses) + " ORDER BY fact_id",
            tuple(params),
        )
        batch_id = f"batch-{uuid.uuid4().hex[:10]}"
        fact_ids: list[str] = []
        for row in rows:
            if self._retract_one(row["fact_id"], reason, actor, batch_id) is not None:
                fact_ids.append(row["fact_id"])
        return {
            "batchId": batch_id,
            "retracted": len(fact_ids),
            "factIds": fact_ids,
            "source": {"documentId": document_id, "runId": run_id},
        }

    def batch_retract(
        self,
        fact_ids: list[str] | None = None,
        subject: str | None = None,
        predicate: str | None = None,
        graph: str | None = None,
        source_document_id: str | None = None,
        actor: str = "operator",
        reason: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Withdraw many assertions in one batch.

        Batch retract is the only operation that can move a large part of the
        ledger at once, so the default caller path is a *preview*: `dry_run=True`
        returns exactly what would change (and what would be skipped and why)
        without writing.  Executing stamps one `batch_id` on every event, so the
        batch is reconstructable from the chain and every row carries `actor`
        and `reason`.
        """
        explicit = [str(fact_id) for fact_id in (fact_ids or []) if fact_id]
        filters = {
            "subject": subject, "predicate": predicate, "graph": graph,
            "source_document_id": source_document_id,
        }
        selected = {key: value for key, value in filters.items() if value}
        if not explicit and not selected:
            raise _err(
                "InvalidArgument",
                "batch retract needs factIds or at least one filter (subject/predicate/graph/sourceDocumentId)",
                "E_FACT_BATCH_SELECTOR",
            )
        if not actor:
            raise _err(
                "InvalidArgument", "actor is required for batch retract",
                "E_FACT_EVENT", field="actor",
            )

        rows: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        if explicit:
            for fact_id in explicit:
                row = self._fetch(fact_id)
                if row is None:
                    skipped.append({"factId": fact_id, "reason": "not_found"})
                elif row["state"] != "active":
                    skipped.append(
                        {"factId": fact_id, "reason": f"not_active:{row['state']}"}
                    )
                else:
                    rows.append(row)
        else:
            clauses = ["state = 'active'"]
            params: list[Any] = []
            if subject:
                clauses.append("subject_iri = %s")
                params.append(subject)
            if predicate:
                clauses.append("predicate_iri = %s")
                params.append(predicate)
            if graph:
                clauses.append("graph_iri = %s")
                params.append(graph)
            if source_document_id:
                clauses.append("source_document_id = %s")
                params.append(source_document_id)
            rows = self._meta.query(
                "SELECT fact_id FROM platform.fact_assertion WHERE "
                + " AND ".join(clauses) + " ORDER BY fact_id",
                tuple(params),
            )
            rows = [self._fetch(row["fact_id"]) for row in rows]
            rows = [row for row in rows if row is not None]

        items = [
            {
                "factId": row["fact_id"],
                "subject": row["subject_iri"],
                "predicate": row["predicate_iri"],
                "object": row["object_value"],
                "objectKind": row["object_kind"],
                "graph": row["graph_iri"],
                "candidateId": row["candidate_id"],
            }
            for row in rows
        ]
        result: dict[str, Any] = {
            "dryRun": bool(dry_run),
            "batchId": None,
            "count": len(items),
            "items": items,
            "skipped": skipped,
            "actor": actor,
            "reason": reason,
        }
        if dry_run:
            return result

        batch_id = f"batch-{uuid.uuid4().hex[:10]}"
        retracted: list[str] = []
        for row in rows:
            if self._retract_one(row["fact_id"], reason, actor, batch_id) is not None:
                retracted.append(row["fact_id"])
            else:
                skipped.append({"factId": row["fact_id"], "reason": "raced_not_active"})
        result.update(
            {"batchId": batch_id, "count": len(retracted),
             "retracted": retracted, "skipped": skipped}
        )
        return result

    def restore(self, fact_id: str, actor: str = "api") -> dict[str, Any]:
        row = self._fetch(fact_id)
        if row is None:
            raise _err("NotFound", f"fact not found: {fact_id}", "E_FACT_NOT_FOUND", factId=fact_id)
        if row["state"] == "active":
            return _row(row)
        if row["state"] == "superseded" or row["superseded_by"]:
            raise _err(
                "Conflict", f"fact {fact_id} was superseded and cannot be restored",
                "E_FACT_SUPERSEDED", factId=fact_id,
            )
        self.ensure_chain()
        with self._meta.tx() as tx:
            tx.execute(
                """
                UPDATE platform.fact_assertion
                   SET state = 'active', updated_at = now(), retracted_at = NULL,
                       retract_reason = NULL
                 WHERE fact_id = %s AND state = 'retracted'
                """,
                (fact_id,),
            )
            self._event(tx, fact_id, "restored", actor, None, None, {
                "subject": row["subject_iri"], "predicate": row["predicate_iri"],
                "object": row["object_value"], "graph": row["graph_iri"],
            })
        self._insert_triple(row)
        return _row(self._fetch(fact_id))

    def resolve_conflict(
        self,
        subject: str,
        predicate: str,
        action: str,
        actor: str = "operator",
        reason: str | None = None,
        keep: str | None = None,
        merged_object: str | None = None,
        merged_object_kind: str = "iri",
        graph: str | None = None,
        source_document_id: str | None = None,
        batch_id: str | None = None,
    ) -> dict[str, Any]:
        """Operator adjudication. Only keep / keep_both / merge, never heuristics."""
        if action not in ("keep", "keep_both", "merge"):
            raise _err(
                "InvalidArgument", f"unsupported conflict action: {action!r}",
                "E_FACT_RESOLUTION", allowed=["keep", "keep_both", "merge"],
            )
        if not actor:
            raise _err(
                "InvalidArgument", "actor is required for adjudication",
                "E_FACT_RESOLUTION", field="actor",
            )
        for value, label in ((subject, "subject"), (predicate, "predicate")):
            if not IRI_RE.match(value or ""):
                raise _err(
                    "InvalidArgument", f"conflict {label} is not an IRI: {value!r}",
                    "E_FACT_BAD_IRI", field=label, value=value,
                )
        self.ensure_chain()
        clauses = ["state = 'active'", "subject_iri = %s", "predicate_iri = %s"]
        params: list[Any] = [subject, predicate]
        if graph:
            clauses.append("graph_iri = %s")
            params.append(graph)
        rows = self._meta.query(
            "SELECT * FROM platform.fact_assertion WHERE "
            + " AND ".join(clauses) + " ORDER BY object_value",
            tuple(params),
        )
        values = sorted({row["object_value"] for row in rows})
        if len(values) < 2:
            raise _err(
                "Conflict", f"no conflict for ({subject}, {predicate})",
                "E_FACT_NO_CONFLICT", subject=subject, predicate=predicate,
            )

        if action == "keep":
            if keep not in values:
                raise _err(
                    "InvalidArgument", f"keep must be one of {values}",
                    "E_FACT_RESOLUTION", field="keep", allowed=values,
                )
            retired_ids: list[str] = []
            kept_ids: list[str] = []
            with self._meta.tx() as tx:
                for row in rows:
                    if row["object_value"] == keep:
                        kept_ids.append(row["fact_id"])
                        tx.execute(
                            """
                            UPDATE platform.fact_assertion
                               SET accepted_conflict = false, resolution = 'keep',
                                   resolved_by = %s, resolved_at = now(), updated_at = now()
                             WHERE fact_id = %s
                            """,
                            (actor, row["fact_id"]),
                        )
                        self._event(
                            tx, row["fact_id"], "conflict_kept", actor,
                            reason or f"keep {keep}", batch_id,
                            {"role": "kept", "kept": keep, "values": values,
                             "subject": subject, "predicate": predicate},
                        )
                        continue
                    retired_ids.append(row["fact_id"])
                    tx.execute(
                        """
                        UPDATE platform.fact_assertion
                           SET state = 'retracted', updated_at = now(), retracted_at = now(),
                               retract_reason = %s, resolution = 'keep',
                               resolved_by = %s, resolved_at = now()
                         WHERE fact_id = %s AND state = 'active'
                        """,
                        (reason or f"conflict: keep {keep}", actor, row["fact_id"]),
                    )
                    self._event(
                        tx, row["fact_id"], "conflict_kept", actor,
                        reason or f"conflict: keep {keep}", batch_id,
                        {"role": "retired", "kept": keep, "retired": row["object_value"],
                         "previousState": "active", "subject": subject,
                         "predicate": predicate},
                    )
            for row in rows:
                if row["object_value"] != keep:
                    self._delete_if_unused(row)
            return {
                "action": action, "subject": subject, "predicate": predicate,
                "kept": keep, "keptFactIds": kept_ids,
                "retiredFactIds": retired_ids, "retired": len(retired_ids),
            }

        if action == "keep_both":
            with self._meta.tx() as tx:
                for row in rows:
                    tx.execute(
                        """
                        UPDATE platform.fact_assertion
                           SET accepted_conflict = true, resolution = 'accepted_conflict',
                               resolved_by = %s, resolved_at = now(), updated_at = now()
                         WHERE fact_id = %s
                        """,
                        (actor, row["fact_id"]),
                    )
                    self._event(
                        tx, row["fact_id"], "conflict_accepted", actor,
                        reason or "keep both", batch_id,
                        {"values": values, "object": row["object_value"],
                         "subject": subject, "predicate": predicate},
                    )
            return {
                "action": action, "subject": subject, "predicate": predicate,
                "values": values, "acceptedFactIds": [row["fact_id"] for row in rows],
            }

        if not merged_object or (
            merged_object_kind == "iri" and not IRI_RE.match(merged_object)
        ):
            raise _err(
                "InvalidArgument", "merge requires a valid mergedObject",
                "E_FACT_RESOLUTION", field="mergedObject",
            )
        target_graph = graph or rows[0]["graph_iri"]
        if not _graph_ok(target_graph):
            raise _err(
                "InvalidArgument",
                f"graph must be a urn:platform: IRI or an A-Box graph under "
                f"{os.environ.get(ABOX_GRAPH_BASE_ENV) or ABOX_GRAPH_BASE_ENV + ' (unset)'}: "
                f"{target_graph!r}",
                "E_FACT_BAD_GRAPH", graph=target_graph,
            )
        new_id = f"fact-{uuid.uuid4().hex[:12]}"
        originals = [row["fact_id"] for row in rows]
        with self._meta.tx() as tx:
            tx.execute(
                """
                INSERT INTO platform.fact_assertion (
                  fact_id, subject_iri, predicate_iri, object_kind, object_value,
                  graph_iri, source_kind, source_document_id, resolution,
                  resolved_by, resolved_at, merged_from
                ) VALUES (%s, %s, %s, %s, %s, %s, 'manual', %s, 'merge', %s, now(), %s)
                """,
                (new_id, subject, predicate, merged_object_kind, merged_object,
                 target_graph, source_document_id, actor, Jsonb(originals)),
            )
            self._event(
                tx, new_id, "merged", actor, reason or "merge conflict", batch_id,
                {"from": originals, "values": values, "object": merged_object,
                 "objectKind": merged_object_kind, "graph": target_graph,
                 "subject": subject, "predicate": predicate},
            )
            for row in rows:
                tx.execute(
                    """
                    UPDATE platform.fact_assertion
                       SET state = 'retracted', updated_at = now(), retracted_at = now(),
                           retract_reason = %s, superseded_by = %s,
                           resolution = 'merge', resolved_by = %s, resolved_at = now()
                     WHERE fact_id = %s AND state = 'active'
                    """,
                    (reason or f"merged into {new_id}", new_id, actor, row["fact_id"]),
                )
                self._event(
                    tx, row["fact_id"], "merge_superseded", actor,
                    reason or f"merged into {new_id}", batch_id,
                    {"supersededBy": new_id, "object": row["object_value"],
                     "previousState": "active", "subject": subject,
                     "predicate": predicate},
                )
        for row in rows:
            self._delete_if_unused(row)
        new_row = self._fetch(new_id)
        self._insert_triple(new_row)
        return {
            "action": action, "subject": subject, "predicate": predicate,
            "newFact": self.get(new_id), "originalFactIds": originals,
            "mergedFrom": originals,
        }

    def undo_resolution(
        self,
        event_id: int | None = None,
        subject: str | None = None,
        predicate: str | None = None,
        actor: str = "operator",
        reason: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Reverse the latest adjudication for one (s,p).

        The reversal is itself append-only: `unmerged` for merge, `resolution_undo`
        for keep/keep_both. The original events stay untouched, so the hash chain
        keeps verifying after an undo.
        """
        if not actor:
            raise _err(
                "InvalidArgument", "actor is required for an undo",
                "E_FACT_RESOLUTION", field="actor",
            )
        if event_id is None and (not subject or not predicate):
            raise _err(
                "InvalidArgument", "either eventId or subject+predicate is required",
                "E_FACT_UNDO_TARGET",
            )
        self.ensure_chain()
        anchor: dict[str, Any] | None = None
        if event_id is not None:
            rows = self._meta.query(
                "SELECT * FROM platform.fact_event WHERE event_id = %s",
                (int(event_id),),
            )
            if not rows:
                raise _err(
                    "NotFound", f"fact event not found: {event_id}",
                    "E_FACT_EVENT_NOT_FOUND", eventId=event_id,
                )
            anchor = rows[0]
            if anchor["action"] not in ("merged", "conflict_accepted", "conflict_kept"):
                raise _err(
                    "InvalidArgument", f"event {event_id} is not an adjudication",
                    "E_FACT_NOT_ADJUDICATION", eventId=event_id,
                    action=anchor["action"],
                )
            fact_row = self._fetch(anchor["fact_id"])
            if fact_row is None:
                raise _err(
                    "NotFound", f"fact not found: {anchor['fact_id']}",
                    "E_FACT_NOT_FOUND", factId=anchor["fact_id"],
                )
            subject = fact_row["subject_iri"]
            predicate = fact_row["predicate_iri"]

        kind, group, _resolved_at = self._latest_resolution(subject, predicate)  # type: ignore[arg-type]
        latest_event = self._latest_adjudication_event_id(subject, predicate)  # type: ignore[arg-type]
        link_event = int(event_id) if event_id is not None else latest_event
        if anchor is not None and anchor["fact_id"] not in {
            item["fact_id"] for item in group
        }:
            raise _err(
                "Conflict",
                f"event {event_id} is not the latest adjudication for "
                f"({subject}, {predicate})",
                "E_FACT_STALE_RESOLUTION", eventId=event_id,
            )

        if kind == "merge":
            new_row = next(
                (item for item in group if item.get("merged_from")), None
            )
            if new_row is None:
                raise _err(
                    "Conflict", "merge resolution has no merged assertion",
                    "E_FACT_NO_RESOLUTION", subject=subject, predicate=predicate,
                )
            original_ids = list(new_row.get("merged_from") or [])
            original_rows = [self._fetch(fact_id) for fact_id in original_ids]
            if any(item is None for item in original_rows):
                raise _err(
                    "NotFound", "merged originals are missing",
                    "E_FACT_NOT_FOUND", factIds=original_ids,
                )
            if new_row["state"] != "active":
                raise _err(
                    "Conflict",
                    f"merged fact {new_row['fact_id']} is not active",
                    "E_FACT_UNDO_STATE", factId=new_row["fact_id"],
                    state=new_row["state"],
                )
            result: dict[str, Any] = {
                "action": "undo", "undoOf": "merge", "undoOfEventId": link_event,
                "subject": subject, "predicate": predicate,
                "restoredFactIds": original_ids,
                "retiredFactIds": [new_row["fact_id"]],
                "affected": len(original_ids) + 1, "dryRun": bool(dry_run),
            }
            if dry_run:
                return result
            with self._meta.tx() as tx:
                tx.execute(
                    """
                    UPDATE platform.fact_assertion
                       SET state = 'retracted', updated_at = now(), retracted_at = now(),
                           retract_reason = %s, resolution = NULL,
                           resolved_by = NULL, resolved_at = NULL
                     WHERE fact_id = %s AND state = 'active'
                    """,
                    (reason or "unmerge", new_row["fact_id"]),
                )
                self._event(
                    tx, new_row["fact_id"], "unmerged", actor, reason or "unmerge", None,
                    {"role": "merged_fact", "undoOfEventId": link_event,
                     "previousState": "active", "mergedFrom": original_ids,
                     "subject": subject, "predicate": predicate,
                     "object": new_row["object_value"], "graph": new_row["graph_iri"]},
                )
                for item in original_rows:
                    tx.execute(
                        """
                        UPDATE platform.fact_assertion
                           SET state = 'active', updated_at = now(), retracted_at = NULL,
                               retract_reason = NULL, superseded_by = NULL,
                               resolution = NULL, resolved_by = NULL, resolved_at = NULL,
                               accepted_conflict = false
                         WHERE fact_id = %s AND state = 'retracted'
                        """,
                        (item["fact_id"],),
                    )
                    self._event(
                        tx, item["fact_id"], "unmerged", actor, reason or "unmerge", None,
                        {"role": "restored", "undoOfEventId": link_event,
                         "previousState": "retracted", "supersededBy": new_row["fact_id"],
                         "subject": subject, "predicate": predicate,
                         "object": item["object_value"], "graph": item["graph_iri"]},
                    )
            self._delete_if_unused(new_row)
            for item in original_rows:
                self._insert_triple(item)
            result["ok"] = True
            return result

        if kind == "keep":
            kept_rows = [item for item in group if item["state"] == "active"]
            retired_rows = [item for item in group if item["state"] == "retracted"]
            result = {
                "action": "undo", "undoOf": "keep", "undoOfEventId": link_event,
                "subject": subject, "predicate": predicate,
                "restoredFactIds": [item["fact_id"] for item in retired_rows],
                "keptFactIds": [item["fact_id"] for item in kept_rows],
                "retiredFactIds": [], "affected": len(group),
                "dryRun": bool(dry_run),
            }
            if dry_run:
                return result
            with self._meta.tx() as tx:
                for item in retired_rows:
                    tx.execute(
                        """
                        UPDATE platform.fact_assertion
                           SET state = 'active', updated_at = now(), retracted_at = NULL,
                               retract_reason = NULL, superseded_by = NULL,
                               resolution = NULL, resolved_by = NULL, resolved_at = NULL,
                               accepted_conflict = false
                         WHERE fact_id = %s AND state = 'retracted'
                        """,
                        (item["fact_id"],),
                    )
                    self._event(
                        tx, item["fact_id"], "resolution_undo", actor,
                        reason or "undo keep", None,
                        {"role": "retired_restored", "undoOf": "keep",
                         "undoOfEventId": link_event, "previousState": "retracted",
                         "subject": subject, "predicate": predicate,
                         "object": item["object_value"], "graph": item["graph_iri"]},
                    )
                for item in kept_rows:
                    tx.execute(
                        """
                        UPDATE platform.fact_assertion
                           SET updated_at = now(), accepted_conflict = false,
                               resolution = NULL, resolved_by = NULL, resolved_at = NULL
                         WHERE fact_id = %s
                        """,
                        (item["fact_id"],),
                    )
                    self._event(
                        tx, item["fact_id"], "resolution_undo", actor,
                        reason or "undo keep", None,
                        {"role": "kept", "undoOf": "keep",
                         "undoOfEventId": link_event, "previousState": "active",
                         "subject": subject, "predicate": predicate,
                         "object": item["object_value"], "graph": item["graph_iri"]},
                    )
            for item in retired_rows:
                self._insert_triple(item)
            result["ok"] = True
            return result

        if kind == "accepted_conflict":
            rows = [item for item in group if item["accepted_conflict"]]
            result = {
                "action": "undo", "undoOf": "keep_both", "undoOfEventId": link_event,
                "subject": subject, "predicate": predicate,
                "restoredFactIds": [], "retiredFactIds": [],
                "acceptedFactIds": [item["fact_id"] for item in rows],
                "affected": len(rows), "dryRun": bool(dry_run),
            }
            if dry_run:
                return result
            with self._meta.tx() as tx:
                for item in rows:
                    tx.execute(
                        """
                        UPDATE platform.fact_assertion
                           SET updated_at = now(), accepted_conflict = false,
                               resolution = NULL, resolved_by = NULL, resolved_at = NULL
                         WHERE fact_id = %s
                        """,
                        (item["fact_id"],),
                    )
                    self._event(
                        tx, item["fact_id"], "resolution_undo", actor,
                        reason or "undo keep both", None,
                        {"role": "accepted", "undoOf": "keep_both",
                         "undoOfEventId": link_event, "previousState": "active",
                         "subject": subject, "predicate": predicate,
                         "object": item["object_value"], "graph": item["graph_iri"]},
                    )
            result["ok"] = True
            return result

        raise _err(
            "Conflict", f"unsupported resolution kind: {kind!r}",
            "E_FACT_NO_RESOLUTION", subject=subject, predicate=predicate,
        )

    def unmerge(
        self,
        merge_event_id: int,
        actor: str = "operator",
        reason: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        return self.undo_resolution(
            event_id=merge_event_id, actor=actor,
            reason=reason or "unmerge", dry_run=dry_run,
        )

    def batch_keep(
        self,
        keep: str | None,
        predicate: str | None = None,
        subject: str | None = None,
        source_document_id: str | None = None,
        actor: str = "operator",
        reason: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Apply one operator-chosen `keep A` rule to every pending conflict.

        The rule is always explicit (predicate/subject/source + the value to keep);
        nothing is inferred. dry_run defaults to true so a caller must opt into writes.
        """
        if not keep:
            raise _err(
                "InvalidArgument", "batch keep requires the value to keep",
                "E_FACT_RESOLUTION", field="keep",
            )
        if not (predicate or subject or source_document_id):
            raise _err(
                "InvalidArgument",
                "batch keep requires a predicate, subject or source document filter",
                "E_FACT_RESOLUTION", field="filter",
            )
        batch_id = f"resolve-{uuid.uuid4().hex[:10]}"
        candidates = self.conflicts(include_accepted=False)
        results: list[dict[str, Any]] = []
        matched = kept = skipped = affected_facts = 0
        for entry in candidates:
            if predicate and entry["predicate"] != predicate:
                continue
            if subject and entry["subject"] != subject:
                continue
            if source_document_id and not any(
                (item.get("source") or {}).get("documentId") == source_document_id
                for item in entry.get("facts", [])
            ):
                continue
            matched += 1
            retired = sum(
                1 for item in entry.get("facts", [])
                if item.get("object") != keep
            )
            if keep not in entry.get("values", []):
                skipped += 1
                results.append({
                    "subject": entry["subject"], "predicate": entry["predicate"],
                    "status": "skipped", "reason": "keep value not present",
                    "values": entry["values"],
                })
                continue
            if dry_run:
                kept += 1
                affected_facts += retired
                results.append({
                    "subject": entry["subject"], "predicate": entry["predicate"],
                    "status": "would_keep", "retired": retired,
                    "values": entry["values"],
                })
                continue
            outcome = self.resolve_conflict(
                entry["subject"], entry["predicate"], "keep", actor=actor,
                reason=reason or f"batch keep {keep}", keep=keep,
                batch_id=batch_id,
            )
            kept += 1
            affected_facts += int(outcome.get("retired", retired))
            results.append({
                "subject": entry["subject"], "predicate": entry["predicate"],
                "status": "kept", "retired": outcome.get("retired", retired),
                "keptFactIds": outcome.get("keptFactIds", []),
                "retiredFactIds": outcome.get("retiredFactIds", []),
            })
        return {
            "batchId": batch_id, "dryRun": bool(dry_run), "keep": keep,
            "filter": {
                "subject": subject, "predicate": predicate,
                "sourceDocumentId": source_document_id,
            },
            "matched": matched, "kept": kept, "skipped": skipped,
            "affectedFacts": affected_facts, "results": results,
        }

    def purge_test(self, graph: str) -> int:
        """Test-only cleanup. Assertion rows go, the purge itself is audited.

        S12/OQ-45: every removal appends a `purged_test_graph` event so a replay
        reproduces the post-purge state instead of resurrecting deleted facts.
        Audit events are never deleted.
        """
        if not graph.startswith("urn:platform:test:"):
            raise _err(
                "InvalidArgument", "purge_test only accepts urn:platform:test: graphs",
                "E_FACT_BAD_GRAPH", graph=graph,
            )
        self.ensure_chain()
        with self._meta.tx() as tx:
            rows = tx.query(
                "SELECT fact_id FROM platform.fact_assertion "
                "WHERE graph_iri = %s ORDER BY fact_id",
                (graph,),
            )
            tx.execute(
                "DELETE FROM platform.fact_assertion WHERE graph_iri = %s", (graph,)
            )
            for row in rows:
                self._event(
                    tx, row["fact_id"], "purged_test_graph", None,
                    "test graph cleanup", None,
                    {"graph": graph, "reconciled": False},
                )
        return len(rows)

    # ---- read -----------------------------------------------------------

    def get(self, fact_id: str) -> dict[str, Any]:
        row = self._fetch(fact_id)
        if row is None:
            raise _err("NotFound", f"fact not found: {fact_id}", "E_FACT_NOT_FOUND", factId=fact_id)
        return _row(row)

    def events(self, fact_id: str) -> list[dict[str, Any]]:
        self.ensure_chain()
        rows = self._meta.query(
            """
            SELECT event_id, fact_id, action, actor, reason, batch_id, payload,
                   prev_event, hash, created_at
              FROM platform.fact_event WHERE fact_id = %s ORDER BY event_id
            """,
            (fact_id,),
        )
        return [
            {
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
            }
            for row in rows
        ]

    def list(
        self,
        state: str = "active",
        subject: str | None = None,
        predicate: str | None = None,
        source_document_id: str | None = None,
        conflict_only: bool = False,
        limit: int = 100,
    ) -> dict[str, Any]:
        if state != "all" and state not in STATES:
            raise _err(
                "InvalidArgument", f"unsupported state: {state!r}",
                "E_FACT_STATE", allowed=list(STATES) + ["all"],
            )
        clauses: list[str] = []
        params: list[Any] = []
        if state != "all":
            clauses.append("f.state = %s")
            params.append(state)
        if subject:
            clauses.append("f.subject_iri = %s")
            params.append(subject)
        if predicate:
            clauses.append("f.predicate_iri = %s")
            params.append(predicate)
        if source_document_id:
            clauses.append("f.source_document_id = %s")
            params.append(source_document_id)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = self._meta.query(
            f"""
            SELECT f.* FROM platform.fact_assertion f
              {where}
             ORDER BY f.asserted_at DESC, f.fact_id
             LIMIT %s
            """,
            tuple(params + [max(1, min(limit, 500))]),
        )
        items = [_row(row) for row in rows]
        self._mark_conflicts(items)
        if conflict_only:
            items = [item for item in items if item.get("conflict")]
        return {"state": state, "items": items, "count": len(items)}

    def annotate(self, facts: list[dict[str, Any]]) -> None:
        """Attach factId/source/conflict to ContextResolver facts (mutates in place)."""
        if not facts:
            return
        rows = self._meta.query(
            """
            SELECT * FROM platform.fact_assertion
             WHERE state = 'active' AND graph_iri = ANY(%s)
            """,
            (sorted({str(item.get("graph")) for item in facts}),),
        )
        by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for row in rows:
            key = (row["subject_iri"], row["predicate_iri"], row["object_kind"],
                   row["object_value"])
            by_key[key] = _row(row)
        pairs: dict[tuple[str, str], set[str]] = {}
        for item in facts:
            if item.get("inferred"):
                continue
            obj = item.get("object") or {}
            kind = str(obj.get("kind") or "")
            value = str(obj.get("iri") or obj.get("value") or "")
            fact = by_key.get((item.get("subject"), item.get("predicate"), kind, value))
            if not fact:
                continue
            item["factId"] = fact["factId"]
            item["source"] = fact["source"]
            item["status"] = fact["state"]
            pairs.setdefault((fact["subject"], fact["predicate"]), set()).add(
                str(fact["object"].get("value"))
            )
        conflicts = {pair: sorted(values) for pair, values in pairs.items() if len(values) > 1}
        accepted = {
            (fact["subject"], fact["predicate"]): fact.get("acceptedConflict", False)
            for fact in by_key.values()
        }
        for item in facts:
            pair = (item.get("subject"), item.get("predicate"))
            if pair in conflicts:
                item["conflict"] = True
                item["conflictValues"] = conflicts[pair]
                item["acceptedConflict"] = bool(accepted.get(pair))

    def filter_retracted(self, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Drop facts that no source asserts anymore.

        Inferred graphs stay stale until materialization reruns, so filtering at
        read time is what makes a retraction visible to ContextResolver at once.
        A triple survives when any active assertion still backs it (or the
        ledger never saw it: seed data, T-Box axioms).
        """
        if not facts:
            return facts
        rows = self._meta.query(
            """
            SELECT subject_iri, predicate_iri, object_kind, object_value, state
              FROM platform.fact_assertion WHERE state IN ('active', 'retracted')
            """
        )
        active: set[tuple[str, str, str, str]] = set()
        retracted: set[tuple[str, str, str, str]] = set()
        for row in rows:
            key = (
                row["subject_iri"], row["predicate_iri"],
                row["object_kind"], row["object_value"],
            )
            (active if row["state"] == "active" else retracted).add(key)
        kept: list[dict[str, Any]] = []
        for item in facts:
            obj = item.get("object") or {}
            kind = str(obj.get("kind") or "")
            value = str(obj.get("iri") or obj.get("value") or "")
            key = (str(item.get("subject")), str(item.get("predicate")), kind, value)
            if key in retracted and key not in active:
                continue
            kept.append(item)
        return kept

    def conflicts(self, include_accepted: bool = False) -> list[dict[str, Any]]:
        rows = self._meta.query(
            """
            SELECT subject_iri, predicate_iri,
                   COUNT(DISTINCT object_value) AS n,
                   array_agg(DISTINCT object_value ORDER BY object_value) AS values,
                   bool_and(accepted_conflict) AS accepted
              FROM platform.fact_assertion
             WHERE state = 'active'
             GROUP BY subject_iri, predicate_iri
             HAVING COUNT(DISTINCT object_value) > 1
             ORDER BY subject_iri, predicate_iri
            """
        )
        entries: list[dict[str, Any]] = []
        for row in rows:
            details = self._meta.query(
                """
                SELECT fact_id, object_kind, object_value, source_kind,
                       source_document_id, source_run_id, candidate_id, asserted_at
                  FROM platform.fact_assertion
                 WHERE state = 'active' AND subject_iri = %s AND predicate_iri = %s
                 ORDER BY object_value, asserted_at
                """,
                (row["subject_iri"], row["predicate_iri"]),
            )
            entries.append(
                {
                    "subject": row["subject_iri"],
                    "predicate": row["predicate_iri"],
                    "values": list(row["values"]),
                    "accepted": bool(row["accepted"]),
                    "pending": not bool(row["accepted"]),
                    "facts": [
                        {
                            "factId": item["fact_id"],
                            "object": item["object_value"],
                            "objectKind": item["object_kind"],
                            "source": {
                                "kind": item["source_kind"],
                                "documentId": item["source_document_id"],
                                "runId": item["source_run_id"],
                                "candidateId": item["candidate_id"],
                            },
                            "assertedAt": item["asserted_at"].isoformat(),
                        }
                        for item in details
                    ],
                }
            )
        if include_accepted:
            return entries
        return [entry for entry in entries if entry["pending"]]

    def adjudications(self, limit: int = 20) -> list[dict[str, Any]]:
        """Latest adjudication per (subject, predicate), plus its own history.

        `conflicts()` only sees live groups, so a `keep` or `merge` decision makes
        its conflict disappear from that list.  The console still needs to show
        what was decided, by whom and when -- and to offer undo.  This read model
        walks the append-only event chain instead of the current row state.
        """
        rows = self._meta.query(
            """
            SELECT e.event_id, e.fact_id, e.action, e.actor, e.reason, e.payload,
                   e.created_at, f.subject_iri, f.predicate_iri
              FROM platform.fact_event e
              JOIN platform.fact_assertion f ON f.fact_id = e.fact_id
             WHERE e.action = ANY(%s)
             ORDER BY e.event_id DESC
            """,
            (list(ADJUDICATION_ACTIONS + UNDO_ACTIONS),),
        )
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        order: list[tuple[str, str]] = []
        for row in rows:
            key = (row["subject_iri"], row["predicate_iri"])
            if key not in grouped:
                grouped[key] = []
                order.append(key)
            grouped[key].append(row)

        entries: list[dict[str, Any]] = []
        for subject, predicate in order[: max(int(limit), 0)]:
            history = grouped[(subject, predicate)]
            latest = history[0]
            undone = latest["action"] in UNDO_ACTIONS
            anchor = (
                next(
                    (item for item in history[1:] if item["action"] in ADJUDICATION_ACTIONS),
                    None,
                )
                if undone
                else latest
            )
            anchor_payload = dict(anchor.get("payload") or {}) if anchor else {}
            reference = anchor or latest
            entries.append(
                {
                    "subject": subject,
                    "predicate": predicate,
                    "eventId": int(anchor["event_id"]) if anchor else None,
                    "action": _ADJUDICATION_LABELS.get(anchor["action"]) if anchor else None,
                    "actor": reference.get("actor"),
                    "reason": reference.get("reason"),
                    "at": reference["created_at"].isoformat(),
                    "status": "undone" if undone else "in_effect",
                    "kept": anchor_payload.get("kept"),
                    "values": anchor_payload.get("values") or [],
                    "object": anchor_payload.get("object"),
                    "undoneBy": (
                        {
                            "eventId": int(latest["event_id"]),
                            "actor": latest.get("actor"),
                            "reason": latest.get("reason"),
                            "at": latest["created_at"].isoformat(),
                        }
                        if undone
                        else None
                    ),
                    "history": [
                        {
                            "eventId": int(item["event_id"]),
                            "action": _ADJUDICATION_LABELS.get(item["action"], item["action"]),
                            "actor": item.get("actor"),
                            "reason": item.get("reason"),
                            "at": item["created_at"].isoformat(),
                            "payload": dict(item.get("payload") or {}),
                        }
                        for item in history[:10]
                    ],
                    "effective": self._effective_state(subject, predicate),
                }
            )
        return entries

    def _effective_state(self, subject: str, predicate: str) -> dict[str, Any]:
        rows = self._meta.query(
            """
            SELECT object_value, accepted_conflict
              FROM platform.fact_assertion
             WHERE state = 'active' AND subject_iri = %s AND predicate_iri = %s
             ORDER BY object_value
            """,
            (subject, predicate),
        )
        values = sorted({row["object_value"] for row in rows})
        return {
            "activeCount": len(rows),
            "values": values,
            "conflict": len(values) > 1,
            "acceptedConflict": any(bool(row["accepted_conflict"]) for row in rows),
        }

    def annotate(
        self,
        fact_id: str,
        action: str,
        actor: str = "reconcile",
        reason: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append an audit marker to the chain without touching the assertion.

        Reconciliation repairs (identity drift, missing candidate status) must be
        visible in the same hash chain as every other fact event, not in a
        side-channel log.  This never changes `state` or the graph.
        """
        if not fact_id:
            raise _err(
                "InvalidArgument", "factId is required", "E_FACT_NOT_FOUND",
                field="factId",
            )
        if not action:
            raise _err(
                "InvalidArgument", "action is required", "E_FACT_EVENT",
                field="action",
            )
        if not actor:
            raise _err(
                "InvalidArgument", "actor is required for an audit marker",
                "E_FACT_EVENT", field="actor",
            )
        self.ensure_chain()
        if self._fetch(fact_id) is None:
            raise _err(
                "NotFound", f"fact not found: {fact_id}", "E_FACT_NOT_FOUND",
                factId=fact_id,
            )
        with self._meta.tx() as tx:
            event_id = self._event(
                tx, fact_id, action, actor, reason, None, dict(payload or {})
            )
        return {
            "factId": fact_id, "eventId": event_id, "action": action,
            "actor": actor, "reason": reason, "payload": payload or {},
        }

    def reconcile_purges(self) -> int:
        """Backfill purge events for facts removed before S12 (OQ-45).

        Only `urn:platform:test:` graphs are eligible: `purge_test` was the only
        code path that deleted assertion rows, and it never accepted other graphs.
        Each repaired event is marked `reconciled=true` so the backfill is visible
        in the audit chain instead of pretending it was recorded at the time.
        """
        self.ensure_chain()
        rows = self._meta.query(
            """
            SELECT DISTINCT e.fact_id
              FROM platform.fact_event e
             WHERE e.action IN ('asserted', 'merged')
               AND NOT EXISTS (
                     SELECT 1 FROM platform.fact_assertion a WHERE a.fact_id = e.fact_id
               )
               AND NOT EXISTS (
                     SELECT 1 FROM platform.fact_event p
                      WHERE p.fact_id = e.fact_id AND p.action = 'purged_test_graph'
               )
             ORDER BY e.fact_id
            """
        )
        repaired = 0
        with self._meta.tx() as tx:
            for row in rows:
                graph_row = tx.query(
                    """
                    SELECT payload->>'graph' AS graph FROM platform.fact_event
                     WHERE fact_id = %s AND action IN ('asserted', 'merged')
                     ORDER BY event_id DESC LIMIT 1
                    """,
                    (row["fact_id"],),
                )
                graph = graph_row[0]["graph"] if graph_row else None
                if not graph or not str(graph).startswith("urn:platform:test:"):
                    continue
                self._event(
                    tx, row["fact_id"], "purged_test_graph", None,
                    "backfill: purge recorded before S12", None,
                    {"graph": graph, "reconciled": True},
                )
                repaired += 1
        return repaired

    def assertion_count(self) -> int:
        rows = self._meta.query("SELECT COUNT(*) AS n FROM platform.fact_assertion")
        return int(rows[0]["n"])

    @staticmethod
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

    def export_events(
        self,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        source_document_id: str | None = None,
    ) -> dict[str, Any]:
        """Prefix-complete export (S12/OQ-46).

        `items` is always the complete chain prefix up to the cutoff event, so the
        NDJSON verifies offline. The date/source filters only pick the window used
        for views (summary + assertions snapshot); they never truncate the chain.
        """
        self.reconcile_purges()
        self.ensure_chain()
        clauses: list[str] = []
        params: list[Any] = []
        if source_document_id:
            clauses.append("f.source_document_id = %s")
            params.append(source_document_id)
        if start is not None:
            clauses.append("e.created_at >= %s")
            params.append(_parse_time(start))
        if end is not None:
            clauses.append("e.created_at <= %s")
            params.append(_parse_time(end))
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        select = """
            SELECT e.event_id, e.fact_id, e.action, e.actor, e.reason, e.batch_id,
                   e.payload, e.prev_event, e.hash, e.created_at,
                   f.source_document_id, f.source_run_id
              FROM platform.fact_event e
              LEFT JOIN platform.fact_assertion f ON f.fact_id = e.fact_id
        """
        window_rows = self._meta.query(
            f"{select} {where} ORDER BY e.event_id", tuple(params)
        )
        window_items = [self._event_item(row) for row in window_rows]
        cutoff = window_rows[-1] if window_rows else None
        cutoff_seq = int(cutoff["event_id"]) if cutoff else 0
        prefix_rows = (
            self._meta.query(
                f"{select} WHERE e.event_id <= %s ORDER BY e.event_id", (cutoff_seq,)
            )
            if cutoff_seq
            else []
        )
        items = [self._event_item(row) for row in prefix_rows]
        return {
            "items": items,
            "count": len(items),
            "windowItems": window_items,
            "windowCount": len(window_items),
            "cutoff": (
                {
                    "seq": cutoff_seq,
                    "hash": cutoff["hash"],
                    "at": cutoff["created_at"].isoformat(),
                }
                if cutoff
                else None
            ),
            "chain": self.verify_records(items),
        }

    def verify_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return verify_records(records)

    def snapshot(
        self,
        fact_ids: list[str] | None = None,
        source_document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Ledger state snapshot, used as the reference for audit replay."""
        clauses: list[str] = []
        params: list[Any] = []
        if fact_ids is not None:
            if not fact_ids:
                return []
            clauses.append("fact_id = ANY(%s)")
            params.append(sorted(set(fact_ids)))
        if source_document_id:
            clauses.append("source_document_id = %s")
            params.append(source_document_id)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = self._meta.query(
            f"SELECT * FROM platform.fact_assertion {where} ORDER BY fact_id",
            tuple(params),
        )
        return [_row(row) for row in rows]

    # ---- internals -------------------------------------------------------

    def _latest_resolution(
        self, subject: str, predicate: str
    ) -> tuple[str, list[dict[str, Any]], datetime]:
        rows = self._meta.query(
            """
            SELECT * FROM platform.fact_assertion
             WHERE subject_iri = %s AND predicate_iri = %s AND resolution IS NOT NULL
             ORDER BY resolved_at DESC NULLS LAST, fact_id
            """,
            (subject, predicate),
        )
        if not rows:
            raise _err(
                "Conflict", f"no adjudication recorded for ({subject}, {predicate})",
                "E_FACT_NO_RESOLUTION", subject=subject, predicate=predicate,
            )
        latest = rows[0]["resolved_at"]
        group = [row for row in rows if row["resolved_at"] == latest]
        return str(rows[0]["resolution"]), group, latest

    def _latest_adjudication_event_id(
        self, subject: str, predicate: str
    ) -> int | None:
        rows = self._meta.query(
            """
            SELECT e.event_id FROM platform.fact_event e
              JOIN platform.fact_assertion f ON f.fact_id = e.fact_id
             WHERE f.subject_iri = %s AND f.predicate_iri = %s
               AND e.action IN ('conflict_kept', 'conflict_accepted', 'merged')
             ORDER BY e.event_id DESC LIMIT 1
            """,
            (subject, predicate),
        )
        return int(rows[0]["event_id"]) if rows else None

    def _fetch(self, fact_id: str) -> dict[str, Any] | None:
        rows = self._meta.query(
            "SELECT * FROM platform.fact_assertion WHERE fact_id = %s", (fact_id,)
        )
        return rows[0] if rows else None

    def _event(self, tx: Any, fact_id: str, action: str, actor: str | None,
               reason: str | None, batch_id: str | None,
               payload: dict[str, Any]) -> int:
        last = tx.query(
            "SELECT event_id, hash FROM platform.fact_event ORDER BY event_id DESC LIMIT 1"
        )
        prev_id = int(last[0]["event_id"]) if last else None
        prev_hash = (last[0]["hash"] or "") if last else ""
        inserted = tx.execute_returning(
            """
            INSERT INTO platform.fact_event
              (fact_id, action, actor, reason, batch_id, payload, prev_event)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING event_id
            """,
            (fact_id, action, actor, reason, batch_id, Jsonb(payload), prev_id),
        )
        event_id = int(inserted[0]["event_id"])
        digest = event_hash(
            prev_hash,
            event_body(event_id, fact_id, action, actor, reason, batch_id, payload),
        )
        tx.execute(
            "UPDATE platform.fact_event SET hash = %s WHERE event_id = %s",
            (digest, event_id),
        )
        return event_id

    def ensure_chain(self) -> int:
        """Backfill prev_event/hash for events written before S9. Idempotent."""
        rows = self._meta.query(
            """
            SELECT event_id, fact_id, action, actor, reason, batch_id, payload,
                   prev_event, hash
              FROM platform.fact_event ORDER BY event_id
            """
        )
        prev_id: int | None = None
        prev_hash = ""
        pending: list[tuple[int | None, str, int]] = []
        for row in rows:
            if row["hash"]:
                prev_id = int(row["event_id"])
                prev_hash = row["hash"]
                continue
            body = event_body(
                int(row["event_id"]), row["fact_id"], row["action"], row["actor"],
                row["reason"], row["batch_id"], row["payload"],
            )
            digest = event_hash(prev_hash, body)
            pending.append((prev_id, digest, int(row["event_id"])))
            prev_id = int(row["event_id"])
            prev_hash = digest
        if not pending:
            return 0
        with self._meta.tx() as tx:
            for link, digest, event_id in pending:
                tx.execute(
                    "UPDATE platform.fact_event SET prev_event = %s, hash = %s "
                    "WHERE event_id = %s",
                    (link, digest, event_id),
                )
        return len(pending)

    def _insert_triple(self, row: dict[str, Any]) -> None:
        triple = f"{_term(row['subject_iri'], 'iri')} {_term(row['predicate_iri'], 'iri')} " \
                 f"{_term(row['object_value'], row['object_kind'])} ."
        self._graph.update(f"INSERT DATA {{ GRAPH <{row['graph_iri']}> {{ {triple} }} }}")

    def _delete_triple(self, row: dict[str, Any]) -> None:
        triple = f"{_term(row['subject_iri'], 'iri')} {_term(row['predicate_iri'], 'iri')} " \
                 f"{_term(row['object_value'], row['object_kind'])} ."
        self._graph.update(f"DELETE DATA {{ GRAPH <{row['graph_iri']}> {{ {triple} }} }}")

    def _delete_if_unused(self, row: dict[str, Any]) -> None:
        remaining = self._meta.query(
            """
            SELECT COUNT(*) AS n FROM platform.fact_assertion
             WHERE state = 'active' AND subject_iri = %s AND predicate_iri = %s
               AND object_kind = %s AND object_value = %s AND graph_iri = %s
            """,
            (row["subject_iri"], row["predicate_iri"], row["object_kind"],
             row["object_value"], row["graph_iri"]),
        )
        if int(remaining[0]["n"]) == 0:
            self._delete_triple(row)

    def _mark_conflicts(self, items: list[dict[str, Any]]) -> None:
        conflicts = {
            (entry["subject"], entry["predicate"]): entry
            for entry in self.conflicts(include_accepted=True)
        }
        for item in items:
            entry = conflicts.get((item["subject"], item["predicate"]))
            if entry:
                item["conflict"] = True
                item["conflictValues"] = entry["values"]
                item["acceptedConflict"] = entry["accepted"]
