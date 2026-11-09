"""Reconcile the three places an approved assertion lives.

The local stack has no 2PC: the ledger (``platform.fact_assertion``), the
namespace candidate item (``public.coa_local_items`` / ``coa-local-fact-candidates``)
and the A-Box graph are written in a fixed order, with in-request compensation.
If the process dies between the ledger commit and the candidate status update,
the books disagree. Retrying the approval converges, but nothing *notices* the
disagreement until this command runs.

    python reconcile_fact_ledger.py              # read-only report
    python reconcile_fact_ledger.py --json       # same, machine-readable
    python reconcile_fact_ledger.py --fix        # repair what is provably safe
    python reconcile_fact_ledger.py --fix --actor ops

Exit code is 0 only when the books agree, so the command drops straight into a
health check, a cron entry or ``10-本地起栈.ps1``.

Reported differences (each one is a separate bucket):

``candidate_status_mismatch``
    the ledger has an ACTIVE fact whose candidate is not APPROVED (the crash
    window: ledger committed, status update never ran).
``candidate_fact_id_drift``
    both sides agree the fact exists, but the candidate still points at the
    pre-ledger identity (historical backfill wrote a fresh ledger row).
``ledger_without_candidate``
    the ledger references a candidate id that is not in the sources store.
``approved_candidate_missing_fact``
    a candidate is APPROVED but its factId is not in the ledger at all.
``abox_only`` / ``ledger_only``
    the A-Box document graph and the ACTIVE ledger rows disagree on a triple.

``--fix`` repairs only: status mismatch, factId drift, and a missing A-Box
triple for an existing active ledger row. Every repair appends a ``reconciled``
event to the fact's hash chain, so the repair is visible in the audit trail.
It never deletes a triple, never invents a ledger row (that is
``backfill_fact_ledger.py``'s job) and never touches ``urn:platform:`` graphs.

Relationship to ``backfill_fact_ledger.py``:

* ``backfill_fact_ledger.py`` is a one-off history import: approved candidates
  from before the two books were connected -> ledger rows.  Run once per
  environment; ``--apply`` is its write switch.
* this command is the standing reconciliation: it assumes the books *should*
  agree now and reports/repairs drift.  Run it after every schema change, on a
  schedule, and from the stack script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import psycopg

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
sys.path.insert(0, str(TOOLS))

import coa_api_local as bridge  # noqa: E402  (adds workspace src to sys.path)
from coa_sources.api.candidate_routes import _term, _triple_from_terms  # noqa: E402

CANDIDATES_TABLE = "coa-local-fact-candidates"
BUCKETS = (
    "candidate_status_mismatch",
    "candidate_fact_id_drift",
    "ledger_without_candidate",
    "approved_candidate_missing_fact",
    "abox_only",
    "ledger_only",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sources_items(table: str) -> list[dict[str, Any]]:
    dsn = os.environ["COA_CONTROL_PLANE_PG_DSN"]
    with psycopg.connect(dsn) as conn:
        rows = conn.execute(
            "SELECT item FROM public.coa_local_items "
            " WHERE table_name = %s ORDER BY pk, sk",
            (table,),
        ).fetchall()
    return [row[0] for row in rows]


def _update_candidate(candidate_id: str, fields: dict[str, Any]) -> int:
    dsn = os.environ["COA_CONTROL_PLANE_PG_DSN"]
    with psycopg.connect(dsn) as conn:
        cursor = conn.execute(
            "UPDATE public.coa_local_items "
            "   SET item = item || %s::jsonb "
            " WHERE table_name = %s AND item->>'candidateId' = %s",
            (json.dumps(fields, ensure_ascii=False), CANDIDATES_TABLE, candidate_id),
        )
        conn.commit()
        return cursor.rowcount


def _ledger_rows(runtime: Any) -> list[dict[str, Any]]:
    return runtime.metadata.query(
        """
        SELECT fact_id, subject_iri, predicate_iri, object_kind, object_value,
               graph_iri, state, source_kind, source_document_id, candidate_id
          FROM platform.fact_assertion
         ORDER BY fact_id
        """
    )


def _oxigraph_url() -> str:
    return (
        os.environ.get("COA_GRAPH_OXIGRAPH_URL")
        or os.environ.get("OXIGRAPH_URL")
        or "http://127.0.0.1:7878"
    ).rstrip("/")


def _abox_triples(graph: str) -> set[tuple[str, str, str, str]]:
    """Every triple in one graph, keyed the same way as a ledger row."""
    query = f"SELECT ?s ?p ?o WHERE {{ GRAPH <{graph}> {{ ?s ?p ?o }} }}"
    response = httpx.post(
        f"{_oxigraph_url()}/query",
        content=query.encode("utf-8"),
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    found: set[tuple[str, str, str, str]] = set()
    for row in response.json().get("results", {}).get("bindings", []):
        obj = row["o"]
        kind = {"uri": "iri", "bnode": "bnode"}.get(obj["type"], "literal")
        found.add((row["s"]["value"], row["p"]["value"], obj["value"], kind))
    return found


def _triple_text(row: dict[str, Any]) -> str:
    from rdflib import Literal, URIRef

    subject = (URIRef(row["subject_iri"]).n3(), "iri")
    predicate = (URIRef(row["predicate_iri"]).n3(), "iri")
    if row["object_kind"] == "iri":
        obj = (URIRef(row["object_value"]).n3(), "iri")
    else:
        obj = (Literal(row["object_value"]).n3(), "literal")
    return _triple_from_terms(subject, predicate, obj)


def _project(graph: str, triple: str) -> None:
    response = httpx.post(
        f"{_oxigraph_url()}/update",
        content=f"INSERT DATA {{ GRAPH <{graph}> {{ {triple} }} }}".encode("utf-8"),
        headers={"Content-Type": "application/sparql-update"},
        timeout=30.0,
    )
    response.raise_for_status()


def _ledger_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        row["subject_iri"], row["predicate_iri"],
        row["object_value"], row["object_kind"],
    )


def _doc_graphs(rows: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> set[str]:
    graphs = {
        row["graph_iri"]
        for row in rows
        if row["graph_iri"] and not str(row["graph_iri"]).startswith("urn:platform:")
    }
    graphs.update(
        item["graphUri"]
        for item in candidates
        if item.get("status") == "APPROVED" and item.get("graphUri")
    )
    return graphs


def _diff(
    rows: list[dict[str, Any]], candidates: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    found: dict[str, list[dict[str, Any]]] = {name: [] for name in BUCKETS}
    by_fact = {row["fact_id"]: row for row in rows}
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["candidate_id"]:
            by_candidate.setdefault(str(row["candidate_id"]), []).append(row)

    for row in rows:
        if row["state"] != "active" or not row["candidate_id"]:
            continue
        candidate_id = str(row["candidate_id"])
        candidate = next(
            (item for item in candidates if item.get("candidateId") == candidate_id), None
        )
        if candidate is None:
            found["ledger_without_candidate"].append(
                {"factId": row["fact_id"], "candidateId": candidate_id,
                 "graph": row["graph_iri"]}
            )
            continue
        if candidate.get("status") != "APPROVED":
            found["candidate_status_mismatch"].append(
                {
                    "factId": row["fact_id"], "candidateId": candidate_id,
                    "candidateStatus": candidate.get("status"),
                    "candidateFactId": candidate.get("factId"),
                    "graph": row["graph_iri"], "subject": row["subject_iri"],
                    "predicate": row["predicate_iri"],
                }
            )
        elif str(candidate.get("factId") or "") != row["fact_id"]:
            found["candidate_fact_id_drift"].append(
                {
                    "factId": row["fact_id"], "candidateId": candidate_id,
                    "candidateFactId": candidate.get("factId"),
                }
            )

    for item in candidates:
        if item.get("status") != "APPROVED":
            continue
        candidate_id = str(item.get("candidateId") or "")
        if candidate_id and candidate_id in by_candidate:
            continue  # drift is reported from the ledger side
        fact_id = str(item.get("factId") or "")
        if not fact_id or fact_id not in by_fact:
            found["approved_candidate_missing_fact"].append(
                {
                    "candidateId": candidate_id,
                    "factId": fact_id or None,
                    "documentId": item.get("documentId"),
                    "graph": item.get("graphUri"),
                    "subject": item.get("subject"),
                    "predicate": item.get("predicate"),
                    "object": item.get("object"),
                }
            )

    active_by_graph: dict[str, set[tuple[str, str, str, str]]] = {}
    for row in rows:
        if row["state"] == "active" and row["graph_iri"]:
            active_by_graph.setdefault(str(row["graph_iri"]), set()).add(_ledger_key(row))

    graphs = _doc_graphs(rows, candidates)
    for graph in sorted(graphs):
        expected = active_by_graph.get(graph, set())
        actual = _abox_triples(graph)
        for key in sorted(actual - expected):
            found["abox_only"].append(
                {"graph": graph, "subject": key[0], "predicate": key[1],
                 "object": key[2], "objectKind": key[3]}
            )
        for key in sorted(expected - actual):
            found["ledger_only"].append(
                {"graph": graph, "subject": key[0], "predicate": key[1],
                 "object": key[2], "objectKind": key[3]}
            )
    return found


def _apply_fixes(
    runtime: Any,
    found: dict[str, list[dict[str, Any]]],
    rows: list[dict[str, Any]],
    actor: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply the safe repairs. Returns ``(fixed, errors)``.

    Each repair is one cross-store pair (candidate item + ledger event) and the
    two stores have no shared transaction. The candidate write goes first and the
    audit event second: a crash in between leaves an *untraced* repair, never an
    event that claims a repair which did not happen. A failed event therefore
    becomes an error (non-zero exit), not a silent success.
    """
    fixed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    stamp = _utc_now()

    def record(bucket: str, item: dict[str, Any], fact_id: str, reason: str,
               payload: dict[str, Any]) -> None:
        try:
            runtime.facts.annotate(fact_id, "reconciled", actor, reason, payload)
        except Exception as exc:  # the candidate write already landed
            errors.append(
                {"bucket": bucket, "factId": fact_id, "payload": payload,
                 "error": f"{type(exc).__name__}: {exc}",
                 "note": "candidate item was updated but the audit event was not written"}
            )
            return
        fixed.append({"bucket": bucket, **item})

    for item in found["candidate_status_mismatch"]:
        if not _update_candidate(
            item["candidateId"],
            {
                "status": "APPROVED",
                "factId": item["factId"],
                "reconciledBy": actor,
                "reconciledAt": stamp,
            },
        ):
            continue
        record(
            "candidate_status_mismatch", item, item["factId"],
            "reconcile: candidate status advanced to APPROVED",
            {"candidateId": item["candidateId"],
             "previousStatus": item.get("candidateStatus")},
        )

    for item in found["candidate_fact_id_drift"]:
        if not _update_candidate(
            item["candidateId"],
            {"factId": item["factId"], "reconciledBy": actor, "reconciledAt": stamp},
        ):
            continue
        record(
            "candidate_fact_id_drift", item, item["factId"],
            "reconcile: candidate factId aligned with the ledger",
            {"candidateId": item["candidateId"],
             "previousFactId": item.get("candidateFactId")},
        )

    for item in found["ledger_only"]:
        row = next(
            (candidate for candidate in rows
             if candidate["graph_iri"] == item["graph"]
             and _ledger_key(candidate) == (
                 item["subject"], item["predicate"], item["object"], item["objectKind"]
             ) and candidate["state"] == "active"),
            None,
        )
        if row is None:
            continue
        triple = _triple_text(row)
        _project(item["graph"], triple)
        record(
            "ledger_only", {"factId": row["fact_id"], **item}, row["fact_id"],
            "reconcile: re-projected the A-Box triple",
            {"graph": item["graph"], "triple": triple},
        )
    return fixed, errors


def _summary(diffs: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {name: len(diffs[name]) for name in BUCKETS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true",
                        help="repair status drift / factId drift / missing A-Box triples")
    parser.add_argument("--actor", default="reconcile",
                        help="actor recorded on every repair event (default: reconcile)")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = parser.parse_args()

    bridge._configure_environment()
    runtime = bridge._lifecycle_runtime()
    rows = _ledger_rows(runtime)
    candidates = _sources_items(CANDIDATES_TABLE)
    diffs = _diff(rows, candidates)

    fixed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if args.fix:
        fixed, errors = _apply_fixes(runtime, diffs, rows, args.actor)
        rows = _ledger_rows(runtime)
        candidates = _sources_items(CANDIDATES_TABLE)
        diffs = _diff(rows, candidates)

    counts = _summary(diffs)
    report = {
        "generatedAt": _utc_now(),
        "mode": "fix" if args.fix else "report",
        "actor": args.actor if args.fix else None,
        "ledgerRows": len(rows),
        "candidates": len(candidates),
        "counts": counts,
        "fixed": fixed,
        "errors": errors,
        "diffs": diffs,
    }
    total = sum(counts.values())
    ok = total == 0 and not errors

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"ledger rows            : {len(rows)}")
        print(f"candidate items        : {len(candidates)}")
        for name in BUCKETS:
            print(f"{name:<30}: {counts[name]}")
        for name in BUCKETS:
            for item in diffs[name][:5]:
                printable = json.dumps(item, ensure_ascii=False)
                print(f"  ! {name}: {printable}")
        if args.fix:
            print(f"repaired this run      : {len(fixed)}")
            for item in errors:
                print(f"  ! repair trace failed: {json.dumps(item, ensure_ascii=False)}")
        print("RESULT                 :", "reconciled" if ok else "MISMATCH")
        if not ok and not args.fix:
            print("hint: inspect the buckets above, then re-run with --fix for the safe repairs;")
            print("      approved candidates with no ledger row are backfill_fact_ledger.py's job.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
