"""Backfill ``platform.fact_assertion`` from the facts approved before the two
books were connected.

Before this change candidate approval wrote the A-Box triple and the namespace
``coa-local-facts`` item but never the platform ledger, so ``/facts`` was empty.
This script copies every approved assertion into the ledger and cross-checks the
A-Box, using the same runtime and the same term normalisation as the bridge.

    python backfill_fact_ledger.py            # read-only: report only
    python backfill_fact_ledger.py --apply    # write the missing ledger rows

Re-runnable: the ledger's active-duplicate check turns a second run into pure
``duplicate`` hits, so the assertion count does not move.  Exit code 1 when the
books do not reconcile after the run.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import psycopg

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
sys.path.insert(0, str(TOOLS))

import coa_api_local as bridge  # noqa: E402  (adds workspace src to sys.path)
from coa_sources.api.candidate_routes import _term, _triple_from_terms  # noqa: E402

FACTS_TABLE = "coa-local-facts"


def _sources_rows() -> list[dict[str, Any]]:
    dsn = os.environ["COA_CONTROL_PLANE_PG_DSN"]
    with psycopg.connect(dsn) as conn:
        rows = conn.execute(
            "SELECT item FROM public.coa_local_items "
            " WHERE table_name = %s ORDER BY pk, sk",
            (FACTS_TABLE,),
        ).fetchall()
    return [row[0] for row in rows]


def _normalise(item: dict[str, Any]) -> dict[str, Any]:
    subject, subject_kind = _term(str(item["subject"]), "subject")
    predicate, predicate_kind = _term(str(item["predicate"]), "predicate")
    obj, object_kind = _term(str(item["object"]), "object")
    return {
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "objectKind": object_kind,
        "graph": item["graphUri"],
        "documentId": item.get("documentId"),
        "candidateId": item.get("candidateId"),
        "triple": _triple_from_terms(
            (subject, subject_kind), (predicate, predicate_kind), (obj, object_kind)
        ),
        "storedTriple": item.get("triple"),
    }


def _abox_ask(graph: str, triple: str) -> bool:
    url = (
        os.environ.get("COA_GRAPH_OXIGRAPH_URL")
        or os.environ.get("OXIGRAPH_URL")
        or "http://127.0.0.1:7878"
    ).rstrip("/")
    query = f"ASK WHERE {{ GRAPH <{graph}> {{ {triple} }} }}"
    response = httpx.post(
        f"{url}/query",
        content=query.encode("utf-8"),
        headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
        timeout=15.0,
    )
    response.raise_for_status()
    return bool(response.json().get("boolean"))


def _ledger_active(runtime: Any, row: dict[str, Any]) -> bool:
    found = runtime.metadata.query(
        """
        SELECT 1 FROM platform.fact_assertion
         WHERE state = 'active' AND subject_iri = %s AND predicate_iri = %s
           AND object_kind = %s AND object_value = %s AND graph_iri = %s
         LIMIT 1
        """,
        (row["subject"], row["predicate"], row["objectKind"], row["object"], row["graph"]),
    )
    return bool(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the missing ledger rows")
    args = parser.parse_args()

    bridge._configure_environment()
    runtime = bridge._lifecycle_runtime()
    items = _sources_rows()
    rows = [_normalise(item) for item in items]

    distinct: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        key = (row["subject"], row["predicate"], row["objectKind"], row["object"], row["graph"])
        distinct.setdefault(key, row)

    triple_mismatch = [row for row in rows if row["storedTriple"] != row["triple"]]
    missing_ledger = [row for row in distinct.values() if not _ledger_active(runtime, row)]
    missing_abox = [row for row in distinct.values() if not _abox_ask(row["graph"], row["triple"])]

    print(f"sources facts rows      : {len(rows)}")
    print(f"distinct assertions     : {len(distinct)}")
    print(f"ledger active before    : {len(distinct) - len(missing_ledger)}/{len(distinct)}")
    print(f"A-Box triples present   : {len(distinct) - len(missing_abox)}/{len(distinct)}")
    print(f"stored triple mismatch  : {len(triple_mismatch)}")
    for row in triple_mismatch[:10]:
        print(f"  ! {row['candidateId']}: stored={row['storedTriple']!r} expected={row['triple']!r}")

    inserted = duplicates = 0
    if args.apply:
        for row in missing_ledger:
            fact = runtime.facts.record(
                subject=row["subject"],
                predicate=row["predicate"],
                object_value=row["object"],
                object_kind=row["objectKind"],
                graph=row["graph"],
                source_kind="extraction",
                source_document_id=row["documentId"],
                candidate_id=row["candidateId"],
                actor="backfill",
            )
            if fact.get("duplicate"):
                duplicates += 1
            else:
                inserted += 1
        print(f"inserted this run       : {inserted}")
        print(f"duplicates this run     : {duplicates}")

    ledger_after = [row for row in distinct.values() if not _ledger_active(runtime, row)]
    abox_after = [row for row in distinct.values() if not _abox_ask(row["graph"], row["triple"])]
    print(f"ledger active after     : {len(distinct) - len(ledger_after)}/{len(distinct)}")
    print(f"A-Box triples after     : {len(distinct) - len(abox_after)}/{len(distinct)}")
    for row in ledger_after[:10]:
        print(f"  ! ledger missing {row['candidateId']}: {row['triple']} (graph {row['graph']})")
    for row in abox_after[:10]:
        print(f"  ! A-Box missing  {row['candidateId']}: {row['triple']} (graph {row['graph']})")

    reconciled = not ledger_after and not abox_after and not triple_mismatch
    print("RESULT                  :", "reconciled" if reconciled else "MISMATCH")
    return 0 if reconciled else 1


if __name__ == "__main__":
    raise SystemExit(main())
