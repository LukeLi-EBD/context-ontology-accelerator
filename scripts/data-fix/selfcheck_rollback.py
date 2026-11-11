"""自检：ontology_event 写失败时，data-fix 的数据改动必须整体回滚。

用法::

    python scripts/data-fix/selfcheck_rollback.py \
        --dsn postgresql://platform:platform_dev@127.0.0.1:55944/datafix_selfcheck

安全闸：

* 必须显式给 ``--dsn``，不读生产环境变量；
* 库名必须包含 ``test`` / ``selfcheck`` / ``datafix`` 之一；
* 明确拒绝 ``platform`` / ``serve_local`` / ``postgres`` / ``realcorpus`` 这些生产库名。

脚本会自动建最小化的 ``platform.ontology_event``（V10 + V52 列）与
``datafix_selfcheck.items``。三步验证：

1. 给 ``ontology_event`` 装一个必然报错的 BEFORE INSERT 触发器，执行 apply：
   必须抛 ``AuditWriteError``，且 items 一行都不能改、事件一行都不能留。
2. 删掉触发器后重跑：items 必须全部改掉，且恰好留下一条 ``action='data-fix'``
   事件，payload 字段齐全、hash 与 ``platform_core`` 规则一致。
3. dry-run 再跑一次：items 与事件数都不变。

依赖：``psycopg[binary]>=3.1``。
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.parse import urlsplit

import psycopg
from audit import (
    AUDIT_ACTION,
    AuditWriteError,
    Change,
    Plan,
    event_hash,
    mask_dsn,
    run,
)
from psycopg.rows import dict_row

SCRIPT = "scripts/data-fix/selfcheck_rollback.py"
FORBIDDEN_DATABASES = {"platform", "serve_local", "postgres", "realcorpus", "template1"}
ALLOWED_MARKERS = ("test", "selfcheck", "datafix")

EVENT_DDL = """
CREATE TABLE IF NOT EXISTS platform.ontology_event (
  event_id     bigserial PRIMARY KEY,
  version_id   text NOT NULL,
  proposal_id  text,
  action       text NOT NULL,
  actor        text,
  reason       text,
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  prev_event   bigint,
  hash         char(64),
  created_at   timestamptz NOT NULL DEFAULT now(),
  ontology_id  text,
  namespace_id uuid,
  attribution_source text
)
"""

FAIL_FUNCTION = """
CREATE OR REPLACE FUNCTION datafix_selfcheck.fail_audit() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'selfcheck: ontology_event write must fail';
END
$$
"""

FAIL_TRIGGER = """
CREATE TRIGGER fail_audit
BEFORE INSERT ON platform.ontology_event
FOR EACH ROW EXECUTE FUNCTION datafix_selfcheck.fail_audit()
"""


def books(conn: Any) -> dict[str, int]:
    items = int(conn.execute("SELECT count(*) AS n FROM datafix_selfcheck.items").fetchone()["n"])
    touched = int(
        conn.execute("SELECT count(*) AS n FROM datafix_selfcheck.items WHERE note IS NOT NULL").fetchone()["n"]
    )
    events = int(conn.execute("SELECT count(*) AS n FROM platform.ontology_event").fetchone()["n"])
    return {"items": items, "touched": touched, "events": events}


def plan_fn(conn: Any) -> Plan:
    pending = int(
        conn.execute("SELECT count(*) AS n FROM datafix_selfcheck.items WHERE note IS NULL").fetchone()["n"]
    )
    return Plan(
        changes=(Change("datafix_selfcheck.items", "update", "note IS NULL", pending),),
        params={"selfcheck": True},
    )


def apply_fn(conn: Any, _plan: Plan) -> dict[str, int]:
    changed = conn.execute(
        "UPDATE datafix_selfcheck.items SET note = 'touched' WHERE note IS NULL"
    ).rowcount
    return {"datafix_selfcheck.items": changed}


def setup(conn: Any) -> None:
    conn.execute("DROP SCHEMA IF EXISTS datafix_selfcheck CASCADE")
    conn.execute("CREATE SCHEMA datafix_selfcheck")
    conn.execute("CREATE SCHEMA IF NOT EXISTS platform")
    conn.execute(EVENT_DDL)
    conn.execute(
        "CREATE TABLE datafix_selfcheck.items (id integer PRIMARY KEY, note text)"
    )
    conn.execute(
        "INSERT INTO datafix_selfcheck.items (id, note) VALUES (1, NULL), (2, NULL), (3, NULL)"
    )


def drop_fail_trigger(conn: Any) -> None:
    conn.execute("DROP TRIGGER IF EXISTS fail_audit ON platform.ontology_event")
    conn.execute("DROP FUNCTION IF EXISTS datafix_selfcheck.fail_audit()")


def check_event(conn: Any, batch_id: str) -> list[str]:
    problems: list[str] = []
    rows = conn.execute(
        "SELECT event_id, version_id, proposal_id, action, actor, reason, payload, prev_event, hash "
        "FROM platform.ontology_event ORDER BY event_id"
    ).fetchall()
    if len(rows) != 1:
        return [f"expected exactly 1 audit event, got {len(rows)}"]
    row = rows[0]
    payload = row["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    if row["action"] != AUDIT_ACTION:
        problems.append(f"action={row['action']!r}, expected {AUDIT_ACTION!r}")
    if row["version_id"] != f"data-fix:{batch_id}":
        problems.append(f"version_id={row['version_id']!r}, expected data-fix:{batch_id}")
    if row["prev_event"] is not None:
        problems.append(f"first event prev_event={row['prev_event']!r}, expected NULL")
    for field in (
        "script",
        "batchId",
        "affectedRows",
        "plannedRows",
        "params",
        "beforeCounts",
        "afterCounts",
        "dsn",
        "host",
        "pid",
        "startedAt",
        "finishedAt",
    ):
        if field not in payload:
            problems.append(f"payload missing {field}")
    if payload.get("batchId") != batch_id:
        problems.append(f"payload.batchId={payload.get('batchId')!r}")
    if payload.get("affectedRows") != {"datafix_selfcheck.items": 3}:
        problems.append(f"payload.affectedRows={payload.get('affectedRows')!r}")
    body = {
        "eventId": int(row["event_id"]),
        "versionId": row["version_id"],
        "proposalId": row["proposal_id"],
        "action": row["action"],
        "actor": row["actor"],
        "reason": row["reason"],
        "payload": payload,
    }
    if event_hash("", body) != row["hash"]:
        problems.append("hash does not match the platform_core chain rule")
    if "***" not in str(payload.get("dsn", "")):
        problems.append("payload.dsn is not masked")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", required=True, help="一次性测试库 DSN（禁止指向生产库）")
    args = parser.parse_args(argv)

    parts = urlsplit(args.dsn)
    database = parts.path.lstrip("/")
    if database in FORBIDDEN_DATABASES or not any(marker in database for marker in ALLOWED_MARKERS):
        parser.error(
            f"refusing database {database!r}: name must contain one of {ALLOWED_MARKERS} "
            f"and must not be {sorted(FORBIDDEN_DATABASES)}"
        )

    conn = psycopg.connect(args.dsn, row_factory=dict_row)
    # 全程 autocommit：run() 自己显式开事务，读写之间不会留下隐式事务。
    conn.autocommit = True
    results: dict[str, Any] = {"dsn": mask_dsn(args.dsn), "database": database}
    try:
        setup(conn)
        initial = books(conn)
        results["initial"] = initial

        conn.execute(FAIL_FUNCTION)
        conn.execute(FAIL_TRIGGER)

        failed_as_expected = False
        try:
            run(
                conn,
                script=SCRIPT,
                batch_id="selfcheck-fail",
                actor="selfcheck",
                plan_fn=plan_fn,
                apply_fn=apply_fn,
                apply=True,
                dsn=args.dsn,
            )
        except AuditWriteError:
            failed_as_expected = True
        after_failure = books(conn)
        results["afterFailure"] = after_failure
        rollback_ok = failed_as_expected and after_failure == initial
        results["rollbackOk"] = rollback_ok

        drop_fail_trigger(conn)

        run(
            conn,
            script=SCRIPT,
            batch_id="selfcheck-ok",
            actor="selfcheck",
            plan_fn=plan_fn,
            apply_fn=apply_fn,
            apply=True,
            dsn=args.dsn,
        )
        after_success = books(conn)
        results["afterSuccess"] = after_success
        event_problems = check_event(conn, "selfcheck-ok")
        success_ok = after_success == {"items": 3, "touched": 3, "events": 1} and not event_problems
        results["eventProblems"] = event_problems
        results["successOk"] = success_ok

        conn.execute("INSERT INTO datafix_selfcheck.items (id, note) VALUES (4, NULL)")
        run(
            conn,
            script=SCRIPT,
            batch_id="selfcheck-dry-run",
            actor="selfcheck",
            plan_fn=plan_fn,
            apply_fn=apply_fn,
            apply=False,
            dsn=args.dsn,
        )
        after_dry_run = books(conn)
        results["afterDryRun"] = after_dry_run
        dry_run_ok = after_dry_run == {"items": 4, "touched": 3, "events": 1}
        results["dryRunOk"] = dry_run_ok

        passed = rollback_ok and success_ok and dry_run_ok
        results["result"] = "PASS" if passed else "FAIL"
        print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if passed else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
