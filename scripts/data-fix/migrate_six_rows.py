"""Migrate the 6 retained serve_local rows (2 versions / 1 proposal / 3 events).

- versions/proposal keep their ids; ontology_id is derived from graph_iri,
  namespace_id stays NULL, attribution_source = 'legacy_unmapped'.
- events are renumbered with base 18573 (94->18667, 95->18668, 96->18669) and
  prev_event is remapped; the head event's predecessor (93) was a fixture and
  is not migrated, so prev_event becomes NULL.
- serve_local rows are not touched (retirement = keep, never delete).

依赖：``psycopg[binary]>=3.1``；环境变量 ``SERVE_LOCAL_DSN``（源）、``TARGET_DSN``
（目标）均可省略，默认均为 5944 上的本地库。
默认 dry-run；``--apply`` 才写库，且与 ontology_event 审计事件同事务。
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any

import psycopg
from audit import Change, Plan, common_parser, resolve_actor, resolve_batch_id, run
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

SCRIPT = "scripts/data-fix/migrate_six_rows.py"

SERVE_DSN = os.environ.get(
    "SERVE_LOCAL_DSN",
    "postgresql://platform:platform_dev@127.0.0.1:5944/serve_local",
)
PLATFORM_DSN = os.environ.get(
    "TARGET_DSN",
    "postgresql://platform:platform_dev@127.0.0.1:5944/platform",
)

VERSIONS = ["ont-57544cc6264b", "ont-53fb5cb43f5b"]
PROPOSALS = ["prop-32e6cc1834cd"]
EVENTS = [94, 95, 96]
BASE = 18573
NEW_EVENT = {old: BASE + old for old in EVENTS}
PREV_EVENT = {93: None, 94: NEW_EVENT[94], 95: NEW_EVENT[95]}
ONT_RE = re.compile(r"^urn:platform:graph:tbox:(ont-[0-9a-f]{12})$")


def columns(conn: Any, table: str) -> list[str]:
    return [
        row["column_name"]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='platform' AND table_name=%s ORDER BY ordinal_position",
            (table,),
        ).fetchall()
    ]


def ontology_of(version_id: str, graph_iri: str | None) -> str:
    match = ONT_RE.match(graph_iri or "")
    return match.group(1) if match else version_id


def values(row: dict[str, Any], cols: list[str]) -> list[Any]:
    return [Jsonb(row[col]) if isinstance(row[col], (dict, list)) else row[col] for col in cols]


def read_source(src: Any, table: str, cols: list[str], where: str, params: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in src.execute(
            f"SELECT {', '.join(cols)} FROM platform.{table} WHERE {where} ORDER BY 1",
            params,
        ).fetchall()
    ]


def plan(conn: Any) -> Plan:
    src = psycopg.connect(SERVE_DSN, row_factory=dict_row)
    try:
        vcols = columns(conn, "ontology_version")
        pcols = columns(conn, "ontology_proposal")
        ecols = columns(conn, "ontology_event")
        versions = read_source(src, "ontology_version", vcols, "version_id = ANY(%s)", (VERSIONS,))
        proposals = read_source(src, "ontology_proposal", pcols, "proposal_id = ANY(%s)", (PROPOSALS,))
        events = read_source(src, "ontology_event", ecols, "event_id = ANY(%s)", (EVENTS,))
    finally:
        src.close()

    if len(versions) != 2:
        raise SystemExit(f"expected 2 versions in serve_local, got {len(versions)}")
    if len(proposals) != 1:
        raise SystemExit(f"expected 1 proposal in serve_local, got {len(proposals)}")
    if len(events) != 3:
        raise SystemExit(f"expected 3 events in serve_local, got {len(events)}")

    existing_versions = int(
        conn.execute(
            "SELECT count(*) AS n FROM platform.ontology_version WHERE version_id = ANY(%s)",
            (VERSIONS,),
        ).fetchone()["n"]
    )
    existing_proposals = int(
        conn.execute(
            "SELECT count(*) AS n FROM platform.ontology_proposal WHERE proposal_id = ANY(%s)",
            (PROPOSALS,),
        ).fetchone()["n"]
    )
    new_ids = list(NEW_EVENT.values())
    existing_events = int(
        conn.execute(
            "SELECT count(*) AS n FROM platform.ontology_event WHERE event_id = ANY(%s)",
            (new_ids,),
        ).fetchone()["n"]
    )
    return Plan(
        changes=(
            Change(
                "platform.ontology_version",
                "insert",
                "6-row migration, ON CONFLICT DO NOTHING",
                max(0, 2 - existing_versions),
            ),
            Change(
                "platform.ontology_proposal",
                "insert",
                "6-row migration, ON CONFLICT DO NOTHING",
                max(0, 1 - existing_proposals),
            ),
            Change(
                "platform.ontology_event",
                "insert",
                f"renumber {EVENTS} -> {new_ids}, ON CONFLICT DO NOTHING",
                max(0, 3 - existing_events),
            ),
        ),
        params={
            "versions": VERSIONS,
            "proposals": PROPOSALS,
            "event_id_map": {str(old): new for old, new in NEW_EVENT.items()},
            "prev_event_map": {str(old): new for old, new in PREV_EVENT.items()},
            "attribution_source": "legacy_unmapped",
        },
        notes=("serve_local source rows are never deleted",),
    )


def apply(conn: Any, _plan: Plan) -> dict[str, int]:
    src = psycopg.connect(SERVE_DSN, row_factory=dict_row)
    try:
        vcols = columns(conn, "ontology_version")
        pcols = columns(conn, "ontology_proposal")
        ecols = columns(conn, "ontology_event")
        versions = read_source(src, "ontology_version", vcols, "version_id = ANY(%s)", (VERSIONS,))
        proposals = read_source(src, "ontology_proposal", pcols, "proposal_id = ANY(%s)", (PROPOSALS,))
        events = read_source(src, "ontology_event", ecols, "event_id = ANY(%s)", (EVENTS,))
    finally:
        src.close()

    graph_of = {row["version_id"]: row["graph_iri"] for row in versions}
    written = {"platform.ontology_version": 0, "platform.ontology_proposal": 0, "platform.ontology_event": 0}

    for row in versions:
        row["ontology_id"] = ontology_of(row["version_id"], row["graph_iri"])
        row["namespace_id"] = None
        row["attribution_source"] = "legacy_unmapped"
        written["platform.ontology_version"] += conn.execute(
            f"INSERT INTO platform.ontology_version ({', '.join(vcols)}) "
            f"VALUES ({', '.join(['%s'] * len(vcols))}) ON CONFLICT (version_id) DO NOTHING",
            values(row, vcols),
        ).rowcount

    for row in proposals:
        version = row["version_id"]
        row["ontology_id"] = ontology_of(version, graph_of.get(version))
        row["namespace_id"] = None
        row["attribution_source"] = "legacy_unmapped"
        written["platform.ontology_proposal"] += conn.execute(
            f"INSERT INTO platform.ontology_proposal ({', '.join(pcols)}) "
            f"VALUES ({', '.join(['%s'] * len(pcols))}) ON CONFLICT (proposal_id) DO NOTHING",
            values(row, pcols),
        ).rowcount

    for row in events:
        old = row["event_id"]
        row["event_id"] = NEW_EVENT[old]
        row["prev_event"] = PREV_EVENT.get(row["prev_event"], row["prev_event"])
        row["ontology_id"] = ontology_of(row["version_id"], graph_of.get(row["version_id"]))
        row["namespace_id"] = None
        row["attribution_source"] = "legacy_unmapped"
        written["platform.ontology_event"] += conn.execute(
            f"INSERT INTO platform.ontology_event ({', '.join(ecols)}) "
            f"VALUES ({', '.join(['%s'] * len(ecols))}) ON CONFLICT (event_id) DO NOTHING",
            values(row, ecols),
        ).rowcount

    return written


def verify(conn: Any) -> int:
    counts = conn.execute(
        "SELECT (SELECT count(*) FROM platform.ontology_version WHERE version_id = ANY(%s)) AS v, "
        "(SELECT count(*) FROM platform.ontology_proposal WHERE proposal_id = ANY(%s)) AS p, "
        "(SELECT count(*) FROM platform.ontology_event WHERE event_id = ANY(%s)) AS e",
        (VERSIONS, PROPOSALS, list(NEW_EVENT.values())),
    ).fetchone()
    print("present after migration:", counts)
    ok = (counts["v"], counts["p"], counts["e"]) == (2, 1, 3)
    print("MIGRATE6_RESULT=" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = common_parser(__doc__ or SCRIPT)
    args = parser.parse_args(argv)

    conn = psycopg.connect(PLATFORM_DSN, row_factory=dict_row)
    try:
        code = run(
            conn,
            script=SCRIPT,
            batch_id=resolve_batch_id(args.batch_id),
            actor=resolve_actor(args.actor),
            plan_fn=plan,
            apply_fn=apply,
            apply=args.apply,
            dsn=PLATFORM_DSN,
        )
        if code == 0 and args.apply:
            return verify(conn)
        return code
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
