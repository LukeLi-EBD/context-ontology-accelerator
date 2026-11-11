"""Migrate the 8080 ontology triplet into the takeover ``platform`` DB (doc 24 §5.1).

Order follows §5.1: freeze baselines -> versions (rollback_of deferred) ->
proposals -> events (explicit event_id, then setval). Values travel as COPY
text so timestamps and JSON survive byte-for-byte; no Python type round-trip.

Refuses to run when the target already holds rows or ids overlap (conflict
count must be 0). Re-reads the source afterwards and aborts on drift.

用法：``python migrate_ontology.py <SOURCE_DSN> <TARGET_DSN> [--apply]``。
依赖：``psycopg[binary]>=3.1``。默认 dry-run；``--apply`` 才写库，且与
ontology_event 审计事件同事务；审计事件写进目标库。
"""

from __future__ import annotations

import json
import sys
from functools import partial
from typing import Any

import psycopg
from audit import Change, Plan, common_parser, mask_dsn, resolve_actor, resolve_batch_id, run
from psycopg.rows import dict_row

SCRIPT = "scripts/data-fix/migrate_ontology.py"

V_COLS = (
    "version_id",
    "semver",
    "status",
    "content_hash",
    "triple_count",
    "source_format",
    "source_key",
    "graph_iri",
    "rollback_of",
    "label",
    "created_at",
    "published_at",
)
P_COLS = (
    "proposal_id",
    "version_id",
    "against_version",
    "change_summary",
    "status",
    "breaking",
    "acknowledged_breaking",
    "diff",
    "impact",
    "created_by",
    "created_at",
    "approved_by",
    "approved_at",
    "published_at",
)
E_COLS = (
    "event_id",
    "version_id",
    "proposal_id",
    "action",
    "actor",
    "reason",
    "payload",
    "prev_event",
    "hash",
    "created_at",
)

TABLES = [
    ("platform.ontology_version", V_COLS, "version_id", "created_at, version_id", None),
    ("platform.ontology_proposal", P_COLS, "proposal_id", "proposal_id", None),
    # data-fix 审计事件是本库的运维记录，不属于被迁移的本体数据，不跨库搬。
    ("platform.ontology_event", E_COLS, "event_id", "event_id", "action <> 'data-fix'"),
]


def baseline(conn: Any) -> dict[str, Any]:
    v = conn.execute("SELECT count(*) AS n FROM platform.ontology_version").fetchone()["n"]
    p = conn.execute("SELECT count(*) AS n FROM platform.ontology_proposal").fetchone()["n"]
    events = conn.execute(
        "SELECT count(*) FILTER (WHERE action <> 'data-fix') AS n, "
        "coalesce(max(event_id), 0) AS max_id, max(created_at) AS max_at "
        "FROM platform.ontology_event"
    ).fetchone()
    return {
        "versions": v,
        "proposals": p,
        "events": events["n"],
        "maxEventId": events["max_id"],
        "maxCreatedAt": str(events["max_at"]),
    }


def copy_table(
    src: Any,
    tgt: Any,
    table: str,
    cols: tuple[str, ...],
    order: str,
    where: str | None = None,
    null_rollback: bool = False,
) -> int:
    select_cols = ", ".join("NULL" if (null_rollback and col == "rollback_of") else col for col in cols)
    clause = f" WHERE {where}" if where else ""
    out_sql = f"COPY (SELECT {select_cols} FROM {table}{clause} ORDER BY {order}) TO STDOUT"
    in_sql = f"COPY {table} ({', '.join(cols)}) FROM STDIN"
    with src.cursor() as sc, tgt.cursor() as tc, sc.copy(out_sql) as out, tc.copy(in_sql) as incoming:
        for chunk in out:
            incoming.write(chunk)
    return int(tgt.execute(f"SELECT count(*) AS n FROM {table}{clause}").fetchone()["n"])


def _source_counts(src: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table, _, _, _, where in TABLES:
        clause = f" WHERE {where}" if where else ""
        counts[table] = int(src.execute(f"SELECT count(*) AS n FROM {table}{clause}").fetchone()["n"])
    return counts


def plan(conn: Any, *, source: Any, source_dsn: str, target_dsn: str) -> Plan:
    target = conn
    before_src = baseline(source)
    before_tgt = baseline(target)
    if any(before_tgt[key] for key in ("versions", "proposals", "events")):
        raise SystemExit(f"target not empty: {before_tgt}")

    overlaps = {}
    for table, _, key, _, where in TABLES:
        clause = f" WHERE {where}" if where else ""
        src_ids = {row[key] for row in source.execute(f"SELECT {key} FROM {table}{clause}").fetchall()}
        tgt_ids = {row[key] for row in target.execute(f"SELECT {key} FROM {table}{clause}").fetchall()}
        overlaps[key] = len(src_ids & tgt_ids)
    if any(overlaps.values()):
        raise SystemExit(f"id overlap is not zero: {overlaps}")

    counts = _source_counts(source)
    return Plan(
        changes=tuple(
            Change(table, "copy", "COPY into empty target", counts[table]) for table, _, _, _, _ in TABLES
        ),
        params={
            "source": mask_dsn(source_dsn),
            "target": mask_dsn(target_dsn),
            "sourceBaseline": before_src,
            "targetBefore": before_tgt,
            "idOverlap": overlaps,
            "eventSequence": "setval to max(event_id)",
        },
        notes=("refuses non-empty target and any id overlap",),
    )


def apply(conn: Any, _plan: Plan, *, source: Any) -> dict[str, int]:
    target = conn
    before_src = baseline(source)

    inserted_versions = copy_table(
        source, target, TABLES[0][0], V_COLS, TABLES[0][3], null_rollback=True
    )
    backfill = source.execute(
        "SELECT version_id, rollback_of FROM platform.ontology_version "
        "WHERE rollback_of IS NOT NULL ORDER BY version_id"
    ).fetchall()
    with target.cursor() as tc:
        tc.executemany(
            "UPDATE platform.ontology_version SET rollback_of = %s WHERE version_id = %s",
            [(row["rollback_of"], row["version_id"]) for row in backfill],
        )

    inserted_proposals = copy_table(
        source, target, TABLES[1][0], P_COLS, TABLES[1][3], where=TABLES[1][4]
    )
    inserted_events = copy_table(
        source, target, TABLES[2][0], E_COLS, TABLES[2][3], where=TABLES[2][4]
    )
    target.execute(
        "SELECT setval('platform.ontology_event_event_id_seq', "
        "(SELECT max(event_id) FROM platform.ontology_event), true)"
    )

    after_src = baseline(source)
    if after_src != before_src:
        raise SystemExit(f"source drifted during migration: {before_src} -> {after_src}")

    return {
        "platform.ontology_version": inserted_versions,
        "platform.ontology_proposal": inserted_proposals,
        "platform.ontology_event": inserted_events,
        "rollback_backfilled": len(backfill),
    }


def verify(conn: Any) -> int:
    report = {"targetAfter": baseline(conn)}
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = common_parser(__doc__ or SCRIPT)
    parser.add_argument("source_dsn", help="源库 DSN（8080 老栈 platform）")
    parser.add_argument("target_dsn", help="目标库 DSN（接管 platform）")
    args = parser.parse_args(argv)

    source = psycopg.connect(args.source_dsn, row_factory=dict_row)
    with source.transaction():
        source.execute("SET TIME ZONE 'UTC'")
    target = psycopg.connect(args.target_dsn, row_factory=dict_row)
    with target.transaction():
        target.execute("SET TIME ZONE 'UTC'")

    try:
        code = run(
            target,
            script=SCRIPT,
            batch_id=resolve_batch_id(args.batch_id),
            actor=resolve_actor(args.actor),
            plan_fn=partial(
                plan,
                source=source,
                source_dsn=args.source_dsn,
                target_dsn=args.target_dsn,
            ),
            apply_fn=partial(apply, source=source),
            apply=args.apply,
            dsn=args.target_dsn,
        )
        if code == 0 and args.apply:
            return verify(target)
        return code
    finally:
        target.close()
        source.close()


if __name__ == "__main__":
    sys.exit(main())
