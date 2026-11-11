"""Backfill ontology ownership columns on the 5944 target (post-V52).

Rules (agreed with the owner on 2026-11-11):
  * ontology_id      derived from graph_iri; proposals/events join via version_id
  * namespace_id     never invented -> stays NULL
  * attribution_source = 'legacy_unmapped' because no namespace is derivable

Idempotent: every UPDATE is guarded by ``ontology_id IS NULL``.

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

SCRIPT = "scripts/data-fix/backfill_ownership.py"

DERIVE = r"substring(graph_iri from '^urn:platform:graph:tbox:(ont-[0-9a-f]{12})$')"

BACKFILL_VERSION = f"""
UPDATE platform.ontology_version
   SET ontology_id = {DERIVE},
       attribution_source = 'legacy_unmapped'
 WHERE ontology_id IS NULL
   AND graph_iri ~ '^urn:platform:graph:tbox:ont-[0-9a-f]{{12}}$'
"""

BACKFILL_PROPOSAL = """
UPDATE platform.ontology_proposal p
   SET ontology_id = v.ontology_id,
       attribution_source = 'legacy_unmapped'
  FROM platform.ontology_version v
 WHERE v.version_id = p.version_id
   AND p.ontology_id IS NULL
"""

BACKFILL_EVENT = """
UPDATE platform.ontology_event e
   SET ontology_id = v.ontology_id,
       attribution_source = 'legacy_unmapped'
  FROM platform.ontology_version v
 WHERE v.version_id = e.version_id
   AND e.ontology_id IS NULL
   AND v.ontology_id IS NOT NULL
"""

# 计划用计数：与三条 UPDATE 的 WHERE 逐条对齐。event 必须在版本回填之后才有
# ontology_id，所以这里用 COALESCE(已有值, 待派生值) 预测执行后的结果。
PLAN_VERSION = """
SELECT count(*) AS n FROM platform.ontology_version
 WHERE ontology_id IS NULL
   AND graph_iri ~ '^urn:platform:graph:tbox:ont-[0-9a-f]{12}$'
"""

PLAN_PROPOSAL = """
SELECT count(*) AS n FROM platform.ontology_proposal p
  JOIN platform.ontology_version v USING (version_id)
 WHERE p.ontology_id IS NULL
"""

PLAN_EVENT = f"""
SELECT count(*) AS n
  FROM platform.ontology_event e
  JOIN platform.ontology_version v USING (version_id)
 WHERE e.ontology_id IS NULL
   AND COALESCE(v.ontology_id, {DERIVE}) IS NOT NULL
"""

CHECKS = {
    "versions": """
        SELECT count(*) AS rows,
               count(ontology_id) AS ont_not_null,
               count(namespace_id) AS ns_not_null,
               count(*) FILTER (WHERE ontology_id IS NULL) AS ont_null,
               count(*) FILTER (WHERE ontology_id !~ '^ont-[0-9a-f]{12}$') AS ont_bad_shape,
               count(DISTINCT ontology_id) AS ont_distinct
          FROM platform.ontology_version
    """,
    "proposals": """
        SELECT count(*) AS rows,
               count(ontology_id) AS ont_not_null,
               count(namespace_id) AS ns_not_null,
               count(*) FILTER (WHERE ontology_id IS NULL) AS ont_null,
               count(*) FILTER (WHERE ontology_id !~ '^ont-[0-9a-f]{12}$') AS ont_bad_shape,
               count(DISTINCT ontology_id) AS ont_distinct
          FROM platform.ontology_proposal
    """,
    "events": """
        SELECT count(*) AS rows,
               count(ontology_id) AS ont_not_null,
               count(namespace_id) AS ns_not_null,
               count(*) FILTER (
                 WHERE ontology_id IS NULL
                   AND EXISTS (SELECT 1 FROM platform.ontology_version v
                                WHERE v.version_id = e.version_id)
               ) AS ont_null,
               count(*) FILTER (WHERE ontology_id !~ '^ont-[0-9a-f]{12}$') AS ont_bad_shape,
               count(DISTINCT ontology_id) AS ont_distinct
          FROM platform.ontology_event e
    """,
}

CROSS = {
    "version_ont_ne_graph_iri": """
        SELECT count(*) AS n FROM platform.ontology_version
         WHERE ontology_id IS DISTINCT FROM
               substring(graph_iri from '^urn:platform:graph:tbox:(ont-[0-9a-f]{12})$')
    """,
    "proposal_ont_ne_version_ont": """
        SELECT count(*) AS n FROM platform.ontology_proposal p
          JOIN platform.ontology_version v USING (version_id)
         WHERE p.ontology_id IS DISTINCT FROM v.ontology_id
    """,
    "proposal_ns_ne_version_ns": """
        SELECT count(*) AS n FROM platform.ontology_proposal p
          JOIN platform.ontology_version v USING (version_id)
         WHERE p.namespace_id IS DISTINCT FROM v.namespace_id
    """,
    "event_ont_ne_version_ont": """
        SELECT count(*) AS n FROM platform.ontology_event e
          JOIN platform.ontology_version v USING (version_id)
         WHERE e.ontology_id IS DISTINCT FROM v.ontology_id
    """,
}

DISTRIBUTION = """
SELECT table_name, attribution_source, count(*) AS n
  FROM (
        SELECT 'ontology_version' AS table_name, attribution_source FROM platform.ontology_version
        UNION ALL
        SELECT 'ontology_proposal', attribution_source FROM platform.ontology_proposal
        UNION ALL
        SELECT 'ontology_event', attribution_source FROM platform.ontology_event
       ) s
 GROUP BY 1, 2
 ORDER BY 1, 3 DESC
"""


def _count(conn: Any, sql: str) -> int:
    return int(conn.execute(sql).fetchone()["n"])


def plan(conn: Any) -> Plan:
    """dry-run 与 apply 共用：只读统计三条 UPDATE 会命中多少行。"""
    versions = _count(conn, PLAN_VERSION)
    proposals = _count(conn, PLAN_PROPOSAL)
    events = _count(conn, PLAN_EVENT)
    return Plan(
        changes=(
            Change("platform.ontology_version", "update", "ontology_id IS NULL AND graph_iri matches", versions),
            Change("platform.ontology_proposal", "update", "ontology_id IS NULL AND version exists", proposals),
            Change(
                "platform.ontology_event",
                "update",
                "ontology_id IS NULL AND post-backfill version.ontology_id IS NOT NULL",
                events,
            ),
        ),
        params={
            "attribution_source": "legacy_unmapped",
            "derive": DERIVE,
            "namespace_id": "left NULL on purpose",
        },
    )


def apply(conn: Any, _plan: Plan) -> dict[str, int]:
    """在一个事务里按 versions -> proposals -> events 顺序回填。"""
    rv = conn.execute(BACKFILL_VERSION).rowcount
    rp = conn.execute(BACKFILL_PROPOSAL).rowcount
    re_ = conn.execute(BACKFILL_EVENT).rowcount
    return {
        "platform.ontology_version": rv,
        "platform.ontology_proposal": rp,
        "platform.ontology_event": re_,
    }


def verify(conn: Any) -> int:
    """落库后的只读对账；有问题返回 1，但审计事件已经如实提交。"""
    report = {
        "checks": {name: conn.execute(sql).fetchone() for name, sql in CHECKS.items()},
        "cross": {name: conn.execute(sql).fetchone() for name, sql in CROSS.items()},
        "attribution_source": conn.execute(DISTRIBUTION).fetchall(),
    }
    problems = [
        f"{name}.{field}={value}"
        for name, row in report["checks"].items()
        for field, value in row.items()
        if field in ("ont_null", "ont_bad_shape") and value
    ]
    problems += [f"{name}={row['n']}" for name, row in report["cross"].items() if row["n"]]
    report["problems"] = problems
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 1 if problems else 0


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
