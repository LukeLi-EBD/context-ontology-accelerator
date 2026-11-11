"""P9: mark the 78 retired fixture rows in serve_local (no deletes).

Runs only after serve_local reached schema 53 (attribution_source exists).
Guard: ``attribution_source IS NULL``, so an already-marked row is never rewritten.
Expected hit counts: version 10, proposal 7, event 61.

依赖：``psycopg[binary]>=3.1``；环境变量 ``SERVE_LOCAL_DSN``（默认指向
``postgresql://platform:platform_dev@127.0.0.1:5944/serve_local``）。
默认 dry-run；``--apply`` 才写库，且与 ontology_event 审计事件同事务。
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import psycopg
from audit import Change, Plan, common_parser, resolve_actor, resolve_batch_id, run
from psycopg.rows import dict_row

SCRIPT = "scripts/data-fix/mark_legacy_fixtures.py"

# 从 .p1-evidence/serve_local_disposition.py 原样内联（该文件本身只读、未收录）。
FIXTURE_VERSIONS = {
    "ont-cd9b53f05264",
    "ont-cea17d4fac11",
    "ont-528f9760b4ef",
    "ont-2a3d108e40d9",
    "ont-f6a1c0901c3f",
    "ont-9dd9da99a996",
    "ont-f11f9eb6b10c",
    "ont-4d72d1111669",
    "ont-c7a8ec5bff28",
    "ont-6b12938750ac",
}
FIXTURE_PROPOSALS = {
    "prop-6aab801478bd",
    "prop-eb83fe6140d5",
    "prop-87b7ee81d74a",
    "prop-b7c69b032d9c",
    "prop-9a870d411250",
    "prop-cf1599fd0ee1",
    "prop-5112d5d78361",
}
VERSIONS = sorted(FIXTURE_VERSIONS)
PROPOSALS = sorted(FIXTURE_PROPOSALS)
MARK = "legacy_fixture"

PLAN_VERSION = """
SELECT count(*) AS n FROM platform.ontology_version
 WHERE version_id = ANY(%s) AND attribution_source IS NULL
"""
PLAN_PROPOSAL = """
SELECT count(*) AS n FROM platform.ontology_proposal
 WHERE proposal_id = ANY(%s) AND attribution_source IS NULL
"""
PLAN_EVENT = """
SELECT count(*) AS n FROM platform.ontology_event
 WHERE version_id = ANY(%s) AND attribution_source IS NULL
"""


def plan(conn: Any) -> Plan:
    n_version = int(conn.execute(PLAN_VERSION, (VERSIONS,)).fetchone()["n"])
    n_proposal = int(conn.execute(PLAN_PROPOSAL, (PROPOSALS,)).fetchone()["n"])
    n_event = int(conn.execute(PLAN_EVENT, (VERSIONS,)).fetchone()["n"])
    return Plan(
        changes=(
            Change("platform.ontology_version", "update", "version_id in fixture set AND source IS NULL", n_version),
            Change("platform.ontology_proposal", "update", "proposal_id in fixture set AND source IS NULL", n_proposal),
            Change("platform.ontology_event", "update", "version_id in fixture set AND source IS NULL", n_event),
        ),
        params={
            "mark": MARK,
            "guard": "attribution_source IS NULL",
            "versions": VERSIONS,
            "proposals": PROPOSALS,
        },
        notes=("retirement = mark, never delete; serve_local rows stay in place",),
    )


def apply(conn: Any, _plan: Plan) -> dict[str, int]:
    n_version = conn.execute(
        "UPDATE platform.ontology_version SET attribution_source = %s "
        "WHERE version_id = ANY(%s) AND attribution_source IS NULL",
        (MARK, VERSIONS),
    ).rowcount
    n_proposal = conn.execute(
        "UPDATE platform.ontology_proposal SET attribution_source = %s "
        "WHERE proposal_id = ANY(%s) AND attribution_source IS NULL",
        (MARK, PROPOSALS),
    ).rowcount
    n_event = conn.execute(
        "UPDATE platform.ontology_event SET attribution_source = %s "
        "WHERE version_id = ANY(%s) AND attribution_source IS NULL",
        (MARK, VERSIONS),
    ).rowcount
    return {
        "platform.ontology_version": n_version,
        "platform.ontology_proposal": n_proposal,
        "platform.ontology_event": n_event,
    }


def verify(conn: Any) -> int:
    marked = {
        "version": int(
            conn.execute(
                "SELECT count(*) AS n FROM platform.ontology_version "
                "WHERE version_id = ANY(%s) AND attribution_source = %s",
                (VERSIONS, MARK),
            ).fetchone()["n"]
        ),
        "proposal": int(
            conn.execute(
                "SELECT count(*) AS n FROM platform.ontology_proposal "
                "WHERE proposal_id = ANY(%s) AND attribution_source = %s",
                (PROPOSALS, MARK),
            ).fetchone()["n"]
        ),
        "event": int(
            conn.execute(
                "SELECT count(*) AS n FROM platform.ontology_event "
                "WHERE version_id = ANY(%s) AND attribution_source = %s",
                (VERSIONS, MARK),
            ).fetchone()["n"]
        ),
    }
    for table in ("ontology_version", "ontology_proposal", "ontology_event"):
        dist = conn.execute(
            f"SELECT coalesce(attribution_source, '<NULL>') AS src, count(*) AS n "
            f"FROM platform.{table} GROUP BY 1 ORDER BY 2 DESC"
        ).fetchall()
        print(table, {row["src"]: row["n"] for row in dist})
    remaining = int(
        conn.execute(
            "SELECT count(*) AS n FROM platform.ontology_event "
            "WHERE version_id = ANY(%s) AND attribution_source IS DISTINCT FROM %s",
            (VERSIONS, MARK),
        ).fetchone()["n"]
    )
    expected = {"version": 10, "proposal": 7, "event": 61}
    print(f"marked: {marked} expected: {expected} event_leftovers: {remaining}")
    ok = marked == expected and remaining == 0
    print("P9_RESULT=" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = common_parser(__doc__ or SCRIPT)
    args = parser.parse_args(argv)
    dsn = os.environ.get(
        "SERVE_LOCAL_DSN",
        "postgresql://platform:platform_dev@127.0.0.1:5944/serve_local",
    )

    conn = psycopg.connect(dsn, row_factory=dict_row)
    try:
        code = run(
            conn,
            script=SCRIPT,
            batch_id=resolve_batch_id(args.batch_id),
            actor=resolve_actor(args.actor),
            plan_fn=plan,
            apply_fn=apply,
            apply=args.apply,
            dsn=dsn,
        )
        if code == 0 and args.apply:
            print(json.dumps({"expected": {"version": 10, "proposal": 7, "event": 61}}, ensure_ascii=False))
            return verify(conn)
        return code
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
