"""Write per-ontology graph pointers on the 5944 target.

Decision (owner, 2026-11-11): a pointer row exists only for graphs that have at
least one approved/published version; it points at the newest such version.
Graphs whose versions are all draft/deprecated/superseded get no row — pointing
at a replaced or retired version is worse than having no pointer.

The legacy global row ``tbox/current`` (updated_by='smoke-restore') is a smoke
fixture and is deliberately NOT migrated; it is reported separately.

依赖：``psycopg[binary]>=3.1``；环境变量 ``TARGET_DSN`` 必填。
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

SCRIPT = "scripts/data-fix/write_pointers.py"

CANDIDATES = r"""
SELECT DISTINCT ON (ont) ont, version_id
  FROM (
        SELECT substring(graph_iri from '^urn:platform:graph:tbox:(ont-[0-9a-f]{12})$') AS ont,
               version_id, status, created_at
          FROM platform.ontology_version
         WHERE status IN ('approved', 'published')
       ) s
 ORDER BY ont, created_at DESC, version_id DESC
"""

INSERT = f"""
INSERT INTO platform.graph_pointer (name, version_id, updated_by)
SELECT 'tbox/' || ont || '/current', version_id, 'p1-backfill:v52'
  FROM ({CANDIDATES}) c
 WHERE NOT EXISTS (
        SELECT 1 FROM platform.graph_pointer p
         WHERE p.name = 'tbox/' || c.ont || '/current'
       )
"""

PLAN_INSERT = f"""
SELECT count(*) AS n
  FROM ({CANDIDATES}) c
 WHERE NOT EXISTS (
        SELECT 1 FROM platform.graph_pointer p
         WHERE p.name = 'tbox/' || c.ont || '/current'
       )
"""

COUNTS = """
SELECT
  (SELECT count(DISTINCT substring(graph_iri from '^urn:platform:graph:tbox:(ont-[0-9a-f]{12})$'))
     FROM platform.ontology_version) AS graphs_total,
  (SELECT count(*) FROM platform.graph_pointer) AS pointer_rows,
  (SELECT count(*) FROM platform.graph_pointer p
     JOIN platform.ontology_version v USING (version_id)
    WHERE v.status NOT IN ('approved', 'published')) AS pointer_to_non_ap,
  (SELECT count(*) FROM platform.graph_pointer
    WHERE name !~ '^tbox/ont-[0-9a-f]{12}/current$') AS pointer_bad_name,
  (SELECT count(*) FROM platform.graph_pointer
    WHERE name = 'tbox/current') AS legacy_global_rows
"""

NOT_LATEST_AP = """
WITH ap AS (
  SELECT substring(graph_iri from '^urn:platform:graph:tbox:(ont-[0-9a-f]{12})$') AS ont,
         version_id, created_at
    FROM platform.ontology_version
   WHERE status IN ('approved', 'published')
), newest AS (
  SELECT DISTINCT ON (ont) ont, version_id FROM ap
   ORDER BY ont, created_at DESC, version_id DESC
)
SELECT count(*) AS n
  FROM platform.graph_pointer p
  JOIN ap a ON p.version_id = a.version_id
  LEFT JOIN newest n ON n.ont = a.ont AND n.version_id = a.version_id
 WHERE n.version_id IS NULL
"""


def plan(conn: Any) -> Plan:
    planned = int(conn.execute(PLAN_INSERT).fetchone()["n"])
    return Plan(
        changes=(
            Change(
                "platform.graph_pointer",
                "insert",
                "missing tbox/<ont>/current for newest approved/published version",
                planned,
            ),
        ),
        params={
            "pointer_name": "tbox/<ont>/current",
            "updated_by": "p1-backfill:v52",
            "selection": "newest approved/published version per ontology",
        },
        notes=("legacy global row tbox/current is a smoke fixture and is not migrated",),
    )


def apply(conn: Any, _plan: Plan) -> dict[str, int]:
    inserted = conn.execute(INSERT).rowcount
    return {"platform.graph_pointer": inserted}


def verify(conn: Any) -> int:
    counts = conn.execute(COUNTS).fetchone()
    not_latest = int(conn.execute(NOT_LATEST_AP).fetchone()["n"])
    with_pointer = counts["pointer_rows"] - counts["legacy_global_rows"]
    report = {
        "graphs_total": counts["graphs_total"],
        "graphs_with_pointer": with_pointer,
        "graphs_without_pointer": counts["graphs_total"] - with_pointer,
        "pointer_rows_total": counts["pointer_rows"],
        "pointer_to_non_approved_version": counts["pointer_to_non_ap"],
        "pointer_bad_name": counts["pointer_bad_name"],
        "pointer_not_newest_ap": not_latest,
        "legacy_global_rows": counts["legacy_global_rows"],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    bad = counts["pointer_to_non_ap"] or counts["pointer_bad_name"] or not_latest
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    parser = common_parser(__doc__ or SCRIPT)
    args = parser.parse_args(argv)
    dsn = os.environ.get("TARGET_DSN")
    if not dsn:
        parser.error("TARGET_DSN 未设置")

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
            return verify(conn)
        return code
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
