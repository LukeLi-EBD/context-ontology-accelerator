"""统一审计包装：所有 data-fix 脚本每次执行都必须写一条 ``platform.ontology_event``。

约定（2026-11-11 无痕写入事故后定）：

* 默认 dry-run：只统计「会改多少行、哪些表」，不写库；必须显式传 ``--apply`` 才执行。
* 数据改动与审计事件在**同一个事务**里：事件写不进去就整体回滚，绝不允许静默成功。
* 审计事件写入 ``platform.ontology_event``：

  - ``action``       = ``data-fix``
  - ``version_id``   = ``data-fix:<batch_id>``（合成 id，只用于给数据修复事件一个归属；
    该表对 ``version_id`` 没有外键，真实版本 id 形如 ``ont-<12 hex>``，不会撞号）
  - ``actor``        = ``--actor`` / ``$COA_ACTOR`` / ``<系统用户>@<主机名>``
  - ``payload``      = script / batchId / affectedRows / plannedRows / params /
    beforeCounts / afterCounts / dsn（脱敏）/ host / pid / startedAt / finishedAt
  - ``prev_event`` / ``hash`` 复刻 ``platform_core.facts.event_hash`` 与
    ``ontology_pg._append_event`` 的规则，脚本不依赖 platform-core 安装包。

依赖：``psycopg[binary]>=3.1``。
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import socket
import sys
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from psycopg.types.json import Jsonb

AUDIT_ACTION = "data-fix"
AUDIT_VERSION_PREFIX = "data-fix:"


class AuditWriteError(RuntimeError):
    """审计事件没有写成；调用方必须让整个事务回滚。"""


@dataclass(frozen=True)
class Change:
    """一条计划中的变更：表、动作、谓词、预计影响行数。"""

    table: str
    operation: str
    predicate: str
    planned_rows: int


@dataclass(frozen=True)
class Plan:
    """脚本给出的执行计划，dry-run 与 apply 都先打印它。"""

    changes: tuple[Change, ...]
    params: Mapping[str, Any] = field(default_factory=dict)
    notes: tuple[str, ...] = ()


ApplyFn = Callable[[Any, Plan], Mapping[str, int]]


def utc_now() -> str:
    """返回秒级 UTC 时间戳，便于和库里的 ``created_at`` 对时。"""
    return datetime.now(UTC).isoformat(timespec="seconds")


def new_batch_id() -> str:
    """生成默认批次 id：UTC 时间 + 8 位随机后缀，避免同一秒重复。"""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def resolve_actor(actor: str | None) -> str:
    """确定审计 actor，优先级：命令行 > COA_ACTOR > 系统用户@主机。"""
    return actor or os.environ.get("COA_ACTOR") or f"{getpass.getuser()}@{socket.gethostname()}"


def mask_dsn(dsn: str) -> str:
    """把 DSN 里的密码替换成 ``***``，审计事件里只留可复核的连接位置。"""
    if "://" not in dsn:
        return "<non-url-dsn>"
    parts = urlsplit(dsn)
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    auth = f"{parts.username}:***@" if parts.username else ""
    return urlunsplit((parts.scheme, f"{auth}{host}{port}", parts.path, "", ""))


def _event_body(
    event_id: int,
    version_id: str,
    proposal_id: str | None,
    action: str,
    actor: str | None,
    reason: str | None,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """与 ``platform_core.adapters.ontology_pg.ontology_event_body`` 逐字段一致。"""
    return {
        "eventId": int(event_id),
        "versionId": version_id,
        "proposalId": proposal_id,
        "action": action,
        "actor": actor,
        "reason": reason,
        "payload": dict(payload or {}),
    }


def event_hash(prev_hash: str, body: Mapping[str, Any]) -> str:
    """与 ``platform_core.facts.event_hash`` 同规则：sha256(prev_hash + "\\n" + 规范化 JSON)。"""
    text = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev_hash + "\n" + text).encode("utf-8")).hexdigest()


def _value(row: Any, key: str) -> Any:
    """兼容 dict_row 与默认 tuple row。"""
    if isinstance(row, Mapping):
        return row[key]
    return row[0]


def _count(conn: Any, table: str) -> int:
    """读取整表行数；表还不存在（例如首次迁移）时按 0 计。"""
    exists = _value(conn.execute("SELECT to_regclass(%s) AS reg", (table,)).fetchone(), "reg")
    if not exists:
        return 0
    return int(_value(conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone(), "n"))


def append_audit_event(
    conn: Any,
    *,
    script: str,
    batch_id: str,
    actor: str,
    reason: str,
    payload: Mapping[str, Any],
    dsn: str,
) -> int:
    """在当前事务里追加一条 data-fix 审计事件，并回读确认它真的落库。

    任何一步失败都抛 ``AuditWriteError``；调用方不要捕获后继续提交。
    """
    try:
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('platform:ontology:event'))")
        last = conn.execute(
            "SELECT event_id, hash FROM platform.ontology_event ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    except Exception as exc:  # noqa: BLE001 - 统一转换成审计失败
        raise AuditWriteError(f"cannot read ontology_event chain head: {exc}") from exc

    if last:
        prev_id = int(_value(last, "event_id"))
        raw_prev_hash = last.get("hash") if isinstance(last, Mapping) else last[1]
        prev_hash = raw_prev_hash or ""
    else:
        prev_id = None
        prev_hash = ""
    version_id = f"{AUDIT_VERSION_PREFIX}{batch_id}"
    full_payload = {**dict(payload), "dsn": mask_dsn(dsn)}

    try:
        row = conn.execute(
            """
            INSERT INTO platform.ontology_event
              (version_id, proposal_id, action, actor, reason, payload, prev_event)
            VALUES (%s, NULL, %s, %s, %s, %s, %s)
            RETURNING event_id
            """,
            (version_id, AUDIT_ACTION, actor, reason, Jsonb(full_payload), prev_id),
        ).fetchone()
        if row is None:
            raise AuditWriteError("INSERT ... RETURNING returned no row")
        event_id = int(_value(row, "event_id"))
        body = _event_body(event_id, version_id, None, AUDIT_ACTION, actor, reason, full_payload)
        digest = event_hash(prev_hash, body)
        updated = conn.execute(
            "UPDATE platform.ontology_event SET hash = %s WHERE event_id = %s",
            (digest, event_id),
        )
        if updated.rowcount != 1:
            raise AuditWriteError(f"hash update touched {updated.rowcount} rows, expected 1")
        confirmed = conn.execute(
            "SELECT action, hash FROM platform.ontology_event WHERE event_id = %s",
            (event_id,),
        ).fetchone()
        if confirmed is None or _value(confirmed, "hash") != digest:
            raise AuditWriteError("audit event read-back mismatch")
    except AuditWriteError:
        raise
    except Exception as exc:  # noqa: BLE001 - 统一转换成审计失败
        raise AuditWriteError(f"cannot append data-fix audit event: {exc}") from exc

    return event_id


def print_plan(script: str, batch_id: str, plan: Plan, apply: bool) -> None:
    """先打印计划再动手；dry-run 与 apply 输出同一份计划。"""
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode}] script={script} batch_id={batch_id}")
    for change in plan.changes:
        print(
            f"  {change.table:<34} {change.operation:<8} "
            f"rows={change.planned_rows:<8} where={change.predicate}"
        )
    if plan.params:
        print("  params=" + json.dumps(plan.params, ensure_ascii=False, sort_keys=True, default=str))
    for note in plan.notes:
        print(f"  note: {note}")


def run(
    conn: Any,
    *,
    script: str,
    batch_id: str,
    actor: str,
    plan_fn: Callable[[Any], Plan],
    apply_fn: ApplyFn,
    apply: bool,
    dsn: str,
) -> int:
    """执行一次 data-fix：dry-run 只统计；apply 时数据与审计事件同事务提交。

    ``apply=False`` 使用 ``force_rollback``，即使脚本写了东西也不会留下。
    ``apply_fn`` 返回的映射就是审计事件里的 ``affectedRows``。
    """
    started_at = utc_now()
    with conn.transaction(force_rollback=not apply):
        plan = plan_fn(conn)
        print_plan(script, batch_id, plan, apply)
        if not apply:
            print("[DRY-RUN] 未写库；确认计划后加 --apply 执行。")
            return 0

        before = {change.table: _count(conn, change.table) for change in plan.changes}
        affected = {key: int(value) for key, value in apply_fn(conn, plan).items()}
        after = {change.table: _count(conn, change.table) for change in plan.changes}

        payload = {
            "script": script,
            "batchId": batch_id,
            "affectedRows": affected,
            "plannedRows": {change.table: change.planned_rows for change in plan.changes},
            "params": dict(plan.params),
            "beforeCounts": before,
            "afterCounts": after,
            "host": socket.gethostname(),
            "pid": os.getpid(),
            "startedAt": started_at,
            "finishedAt": utc_now(),
        }
        reason = f"{script} batch={batch_id} affected={json.dumps(affected, sort_keys=True)}"
        try:
            event_id = append_audit_event(
                conn,
                script=script,
                batch_id=batch_id,
                actor=actor,
                reason=reason,
                payload=payload,
                dsn=dsn,
            )
        except AuditWriteError:
            print(
                f"[AUDIT-FAILED] {script} batch={batch_id} 未写成 ontology_event，"
                "事务整体回滚，数据改动不生效。",
                file=sys.stderr,
            )
            raise

    print(
        json.dumps(
            {
                "eventId": event_id,
                "affectedRows": affected,
                "beforeCounts": before,
                "afterCounts": after,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def common_parser(description: str) -> argparse.ArgumentParser:
    """所有 data-fix 脚本共用的参数：--apply / --batch-id / --actor。"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="真正写库；不传时只做 dry-run（默认）",
    )
    parser.add_argument(
        "--batch-id",
        default=None,
        help="批次 id；默认按 UTC 时间 + 随机后缀生成",
    )
    parser.add_argument(
        "--actor",
        default=None,
        help="审计 actor；默认 $COA_ACTOR 或 系统用户@主机名",
    )
    return parser


def resolve_batch_id(value: str | None) -> str:
    """命令行给了就用，否则生成新批次 id。"""
    return value or new_batch_id()
