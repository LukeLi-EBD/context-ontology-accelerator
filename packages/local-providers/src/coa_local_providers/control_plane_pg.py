# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""PostgreSQL implementation of the control-plane item store.

The upstream control-plane/sources handlers talk to DynamoDB through
``coa_common.dao.DynamoDBDAO`` (item semantics: PK/SK, GSI queries, conditional
writes).  Locally there is no DynamoDB, so this module implements the same
duck-typed surface on top of a single JSONB table in PostgreSQL.

It is *not* a second data model: the item stays the source of truth and the
PG columns are only the DynamoDB key attributes used for lookups/ordering.

Selected explicitly with ``COA_PROVIDER_CONTROL_PLANE_STORE=postgres`` and
installed by the local API composition root
(``doc/coa-x/tools/coa_api_local.py``).  There is no implicit fallback: if the
DSN is missing the store refuses to start.
"""

from __future__ import annotations

import copy
import json
import os
import re
import threading
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import structlog
from botocore.exceptions import ClientError
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

logger = structlog.get_logger(__name__)

_TABLE = "public.coa_local_items"
_PROJECT_TABLE = "public.coa_local_projects"

# DynamoDB GSI name -> attribute that orders the index.  Control-plane tables
# use PK/SK as their base keys and expose named indexes with different keys.
_INDEX_SORT_KEYS: dict[str, str] = {
    "ByNamespace": "sourceTypeCreatedAt",
    "BySourceType": "sourceTypeCreatedAt",
    "NameByIndex": "name",
}

_pools: dict[str, ConnectionPool] = {}
_pools_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _get_pool(dsn: str) -> ConnectionPool:
    with _pools_lock:
        pool = _pools.get(dsn)
        if pool is not None:
            return pool
        pool = ConnectionPool(
            dsn,
            min_size=1,
            max_size=8,
            timeout=15,
            kwargs={"autocommit": True},
            open=True,
        )
        pool.wait(timeout=20)
        with pool.connection() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TABLE} (
                    table_name text NOT NULL,
                    pk         text NOT NULL,
                    sk         text NOT NULL DEFAULT '',
                    item       jsonb NOT NULL,
                    PRIMARY KEY (table_name, pk, sk)
                )
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS coa_local_items_table_idx ON {_TABLE} (table_name)"
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_PROJECT_TABLE} (
                    project_id text PRIMARY KEY,
                    name       text NOT NULL,
                    description text,
                    created_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
        _pools[dsn] = pool
        return pool


# ---------------------------------------------------------------------------
# Expression evaluation (the subset used by the control-plane/sources code)
# ---------------------------------------------------------------------------


def _split_top(expr: str, operator: str) -> list[str]:
    """Split on a top-level boolean operator, respecting parentheses."""
    parts: list[str] = []
    depth = 0
    start = 0
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0:
            candidate = expr[i : i + len(operator)]
            if candidate.upper() == operator:
                before_ok = i == 0 or not expr[i - 1].isalnum()
                after = i + len(operator)
                after_ok = after >= len(expr) or not expr[after].isalnum()
                if before_ok and after_ok:
                    parts.append(expr[start:i])
                    start = after
                    i = after
                    continue
        i += 1
    parts.append(expr[start:])
    return [p.strip() for p in parts if p.strip()]


def _strip_parens(expr: str) -> str:
    expr = expr.strip()
    if expr.startswith("(") and expr.endswith(")"):
        depth = 0
        for idx, ch in enumerate(expr):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and idx != len(expr) - 1:
                    return expr
        return expr[1:-1].strip()
    return expr


def _resolve(name: str, names: dict[str, str] | None) -> str:
    name = name.strip()
    if names and name in names:
        return names[name]
    return name.lstrip("#")


_ATOM_RES = (
    (re.compile(r"^attribute_not_exists\(\s*([^)]+?)\s*\)$", re.I), "not_exists"),
    (re.compile(r"^attribute_exists\(\s*([^)]+?)\s*\)$", re.I), "exists"),
    (re.compile(r"^begins_with\(\s*([^,]+?)\s*,\s*(:\w+)\s*\)$", re.I), "begins_with"),
    (re.compile(r"^contains\(\s*([^,]+?)\s*,\s*(:\w+)\s*\)$", re.I), "contains"),
    (re.compile(r"^(.+?)\s*(<=|>=|<>|=|<|>)\s*(:\w+)$"), "compare"),
)


def _eval_atom(
    expr: str,
    item: dict[str, Any],
    values: dict[str, Any],
    names: dict[str, str] | None,
) -> bool:
    for pattern, kind in _ATOM_RES:
        match = pattern.match(expr)
        if not match:
            continue
        if kind == "not_exists":
            return _resolve(match.group(1), names) not in item
        if kind == "exists":
            return _resolve(match.group(1), names) in item
        if kind in {"begins_with", "contains"}:
            actual = item.get(_resolve(match.group(1), names))
            expected = values.get(match.group(2))
            if not isinstance(actual, str) or not isinstance(expected, str):
                return False
            return actual.startswith(expected) if kind == "begins_with" else expected in actual
        if kind == "compare":
            attr = _resolve(match.group(1), names)
            op = match.group(2)
            expected = values.get(match.group(3))
            if attr not in item:
                return False
            actual = item[attr]
            try:
                if op == "=":
                    return actual == expected
                if op == "<>":
                    return actual != expected
                if op == "<":
                    return actual < expected
                if op == ">":
                    return actual > expected
                if op == "<=":
                    return actual <= expected
                if op == ">=":
                    return actual >= expected
            except TypeError:
                return False
    raise ValueError(f"Unsupported DynamoDB expression: {expr}")


def _eval_condition(
    expr: str,
    item: dict[str, Any],
    values: dict[str, Any] | None = None,
    names: dict[str, str] | None = None,
    *,
    empty_item: bool = False,
) -> bool:
    values = values or {}
    expr = _strip_parens(expr)
    ors = _split_top(expr, "OR")
    if len(ors) > 1:
        return any(_eval_condition(p, item, values, names, empty_item=empty_item) for p in ors)
    ands = _split_top(expr, "AND")
    if len(ands) > 1:
        return all(_eval_condition(p, item, values, names, empty_item=empty_item) for p in ands)
    if empty_item:
        item = {}
    return _eval_atom(expr, item, values, names)


def _eval_condition_object(condition: Any, item: dict[str, Any]) -> bool:
    """Evaluate a boto3 ``ConditionBase`` (e.g. ``Attr(...).is_in([...])``)."""
    expression = condition.get_expression()
    fmt = expression.get("format", "")
    values = expression.get("values", [])
    operator = expression.get("operator")
    if fmt == "{0} {operator} {1}" and operator == "IN":
        attr = getattr(values[0], "name", None)
        return item.get(attr) in values[1]
    raise ValueError(f"Unsupported ConditionBase expression: {expression!r}")


def _conditional_error(operation: str) -> ClientError:
    return ClientError(
        {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "The conditional request failed",
            }
        },
        operation,
    )


# ---------------------------------------------------------------------------
# Key-condition handling
# ---------------------------------------------------------------------------


def _parse_key_condition(
    expr: str,
    values: dict[str, Any],
    names: dict[str, str] | None,
) -> tuple[list[tuple[str, str, Any]], str | None]:
    """Return (equalities as (attr, op, value), sort attribute)."""
    conditions: list[tuple[str, str, Any]] = []
    sort_attr: str | None = None
    for part in _split_top(expr, "AND"):
        part = part.strip()
        begin = re.match(r"^begins_with\(\s*([^,]+?)\s*,\s*(:\w+)\s*\)$", part, re.I)
        if begin:
            attr = _resolve(begin.group(1), names)
            conditions.append((attr, "begins_with", values.get(begin.group(2))))
            sort_attr = attr
            continue
        compare = re.match(r"^(.+?)\s*=\s*(:\w+)$", part)
        if compare:
            attr = _resolve(compare.group(1), names)
            conditions.append((attr, "=", values.get(compare.group(2))))
            continue
        between = re.match(
            r"^(.+?)\s+BETWEEN\s+(:\w+)\s+AND\s+(:\w+)$", part, re.I
        )
        if between:
            attr = _resolve(between.group(1), names)
            conditions.append(
                (attr, "between", (values.get(between.group(2)), values.get(between.group(3))))
            )
            sort_attr = attr
            continue
        raise ValueError(f"Unsupported key condition: {part}")
    return conditions, sort_attr


def _matches_key(item: dict[str, Any], conditions: list[tuple[str, str, Any]]) -> bool:
    for attr, op, expected in conditions:
        actual = item.get(attr)
        if op == "=":
            if actual != expected:
                return False
        elif op == "begins_with":
            if not isinstance(actual, str) or not isinstance(expected, str) or not actual.startswith(expected):
                return False
        elif op == "between":
            low, high = expected
            try:
                if not (low <= actual <= high):
                    return False
            except TypeError:
                return False
    return True


def _sort_value(item: dict[str, Any], attr: str) -> str:
    value = item.get(attr, "")
    if isinstance(value, (int, float, Decimal)):
        # Zero-pad so numeric keys order naturally as strings.
        return f"{float(value):020.6f}"
    return str(value)


class _Page:
    __slots__ = ("items", "last_evaluated_key")

    def __init__(self, items: list[dict[str, Any]], last_evaluated_key: dict[str, Any] | None):
        self.items = items
        self.last_evaluated_key = last_evaluated_key


class PgDatastoreDAO:
    """Drop-in replacement for ``coa_common.dao.dynamodb.DynamoDBDAO``."""

    def __init__(self, table_name: str, *, region: str | None = None, config: Any = None) -> None:
        dsn = os.environ.get("COA_CONTROL_PLANE_PG_DSN", "").strip()
        if not dsn:
            raise RuntimeError(
                "COA_CONTROL_PLANE_PG_DSN is required when COA_PROVIDER_CONTROL_PLANE_STORE=postgres"
            )
        self._table_name = table_name
        self._region = region
        self._pool = _get_pool(dsn)

    # -- low level ---------------------------------------------------------

    def _keys(self, item: dict[str, Any]) -> tuple[str, str]:
        return str(item.get("PK", "")), str(item.get("SK", ""))

    def _fetch(self, pk: str, sk: str) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                f"SELECT item FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = %s",
                (self._table_name, pk, sk),
            ).fetchone()
        return row[0] if row else None

    def _fetch_all(self) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                f"SELECT item FROM {_TABLE} WHERE table_name = %s", (self._table_name,)
            ).fetchall()
        return [row[0] for row in rows]

    def _write(self, item: dict[str, Any], conn: Any) -> None:
        pk, sk = self._keys(item)
        conn.execute(
            f"""
            INSERT INTO {_TABLE} (table_name, pk, sk, item)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (table_name, pk, sk) DO UPDATE SET item = EXCLUDED.item
            """,
            (self._table_name, pk, sk, Jsonb(item, dumps=lambda v: json.dumps(v, default=_json_default))),
        )

    def _delete(self, pk: str, sk: str, conn: Any) -> None:
        conn.execute(
            f"DELETE FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = %s",
            (self._table_name, pk, sk),
        )

    # -- DatastoreDAO surface ---------------------------------------------

    def get(
        self,
        key: dict[str, Any],
        projection_expression: str | None = None,
        consistent_read: bool = False,
    ) -> dict[str, Any] | None:
        pk, sk = self._keys(key)
        return self._fetch(pk, sk)

    def get_attribute(self, key: dict[str, Any], attribute: str) -> Any:
        item = self.get(key)
        return None if item is None else item.get(attribute)

    def put(
        self,
        item: dict[str, Any],
        condition: str | Any | None = None,
        auto_timestamp: bool = True,
    ) -> None:
        item = dict(item)
        pk, sk = self._keys(item)
        existing = self._fetch(pk, sk)
        if condition is not None:
            if existing is not None:
                ok = (
                    _eval_condition_object(condition, existing)
                    if not isinstance(condition, str)
                    else _eval_condition(condition, existing)
                )
            else:
                ok = (
                    False
                    if not isinstance(condition, str)
                    else _eval_condition(condition, {}, empty_item=True)
                )
            if not ok:
                raise _conditional_error("PutItem")
        if auto_timestamp:
            now = _now_iso()
            item.setdefault("createdAt", now)
            item["updatedAt"] = now
        with self._pool.connection() as conn:
            self._write(item, conn)

    def update(
        self,
        key: dict[str, Any],
        update_fields: dict[str, Any] | None = None,
        remove_fields: list[str] | None = None,
        condition: str | None = None,
        condition_values: dict[str, Any] | None = None,
        condition_names: dict[str, str] | None = None,
        auto_timestamp: bool = True,
        raise_on_error: bool = True,
    ) -> bool:
        pk, sk = self._keys(key)
        try:
            with self._pool.connection() as conn:
                row = conn.execute(
                    f"SELECT item FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = %s FOR UPDATE",
                    (self._table_name, pk, sk),
                ).fetchone()
                item = dict(row[0]) if row else {"PK": key.get("PK"), "SK": key.get("SK")}
                if condition:
                    values = dict(condition_values or {})
                    if not _eval_condition(
                        condition,
                        item,
                        values,
                        condition_names,
                        empty_item=row is None,
                    ):
                        raise _conditional_error("UpdateItem")
                for name, value in (update_fields or {}).items():
                    item[name] = value
                for name in remove_fields or []:
                    item.pop(name, None)
                if auto_timestamp:
                    item.setdefault("createdAt", _now_iso())
                    item["updatedAt"] = _now_iso()
                self._write(item, conn)
            return True
        except ClientError:
            if raise_on_error:
                raise
            logger.info("conditional_update_skipped", table=self._table_name, pk=pk, sk=sk)
            return False

    def delete(self, key: dict[str, Any]) -> None:
        pk, sk = self._keys(key)
        with self._pool.connection() as conn:
            self._delete(pk, sk, conn)

    def query(self, params: Any) -> _Page:
        values = dict(getattr(params, "expression_values", None) or {})
        names = getattr(params, "expression_names", None)
        conditions, sort_attr = _parse_key_condition(params.key_condition, values, names)
        matched = [item for item in self._fetch_all() if _matches_key(item, conditions)]

        sort_attr = sort_attr or _INDEX_SORT_KEYS.get(getattr(params, "index_name", None) or "", "")
        scan_forward = getattr(params, "scan_forward", True)

        if sort_attr:
            matched.sort(
                key=lambda i: (_sort_value(i, sort_attr), str(i.get("PK", "")), str(i.get("SK", ""))),
                reverse=not scan_forward,
            )
        else:
            matched.sort(
                key=lambda i: (str(i.get("PK", "")), str(i.get("SK", ""))),
                reverse=not scan_forward,
            )

        start_key = getattr(params, "exclusive_start_key", None)
        if start_key:
            start_pk, start_sk = self._keys(start_key)
            for idx, item in enumerate(matched):
                if str(item.get("PK", "")) == start_pk and str(item.get("SK", "")) == start_sk:
                    matched = matched[idx + 1 :] if scan_forward else matched[:idx]
                    break

        limit = getattr(params, "limit", None)
        page_items = matched[:limit] if limit else matched
        last_key: dict[str, Any] | None = None
        if limit and len(matched) > limit and page_items:
            last = page_items[-1]
            last_key = {attr: last.get(attr) for attr, _, _ in conditions if attr in last}
            last_key["PK"] = last.get("PK")
            last_key["SK"] = last.get("SK")
        return _Page(page_items, last_key)

    def query_all(self, params: Any, max_items: int | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        current = copy.copy(params)
        while True:
            page = self.query(current)
            results.extend(page.items)
            if max_items is not None and len(results) >= max_items:
                return results[:max_items]
            if not page.last_evaluated_key:
                return results
            current.exclusive_start_key = page.last_evaluated_key

    def scan(
        self,
        *,
        filter_expression: str | None = None,
        expression_values: dict[str, Any] | None = None,
        limit: int | None = None,
        exclusive_start_key: dict[str, Any] | None = None,
    ) -> _Page:
        items = self._fetch_all()
        if filter_expression:
            items = [
                item
                for item in items
                if _eval_condition(filter_expression, item, expression_values or {})
            ]
        items.sort(key=lambda i: (str(i.get("PK", "")), str(i.get("SK", ""))))
        if exclusive_start_key:
            start_pk, start_sk = self._keys(exclusive_start_key)
            for idx, item in enumerate(items):
                if str(item.get("PK", "")) == start_pk and str(item.get("SK", "")) == start_sk:
                    items = items[idx + 1 :]
                    break
        page_items = items[:limit] if limit else items
        last_key = None
        if limit and len(items) > limit and page_items:
            last = page_items[-1]
            last_key = {"PK": last.get("PK"), "SK": last.get("SK")}
        return _Page(page_items, last_key)

    def batch_get(self, keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for key in keys:
            item = self.get(key)
            if item is not None:
                results.append(item)
        return results

    def batch_delete(self, keys: list[dict[str, Any]]) -> None:
        with self._pool.connection() as conn:
            for key in keys:
                pk, sk = self._keys(key)
                self._delete(pk, sk, conn)

    def atomic_increment(
        self,
        key: dict[str, Any],
        attribute: str,
        amount: int = 1,
    ) -> int:
        return self._add_attributes(key, {attribute: amount})[attribute]

    def atomic_add(self, key: dict[str, Any], increments: dict[str, Any]) -> None:
        if not increments:
            return
        self._add_attributes(key, increments)

    def _add_attributes(self, key: dict[str, Any], increments: dict[str, Any]) -> dict[str, int]:
        pk, sk = self._keys(key)
        with self._pool.connection() as conn:
            row = conn.execute(
                f"SELECT item FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = %s FOR UPDATE",
                (self._table_name, pk, sk),
            ).fetchone()
            item = dict(row[0]) if row else {"PK": key.get("PK"), "SK": key.get("SK")}
            result: dict[str, int] = {}
            for attribute, delta in increments.items():
                current = item.get(attribute, 0)
                try:
                    current_int = int(current)
                except (TypeError, ValueError):
                    current_int = 0
                value = current_int + int(delta)
                item[attribute] = value
                result[attribute] = value
            item.setdefault("createdAt", _now_iso())
            item["updatedAt"] = _now_iso()
            self._write(item, conn)
        return result

    def transact_write(self, items: list[dict[str, Any]]) -> None:
        """Minimal TransactWriteItems: Put/Update/Delete/ConditionCheck in one txn."""
        with self._pool.connection() as conn, conn.transaction():
            for entry in items:
                if "Put" in entry:
                    put = entry["Put"]
                    item = dict(put["Item"])
                    condition = put.get("ConditionExpression")
                    if condition:
                        pk, sk = self._keys(item)
                        row = conn.execute(
                            f"SELECT item FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = %s",
                            (self._table_name, pk, sk),
                        ).fetchone()
                        existing = row[0] if row else None
                        if not _eval_condition(
                            condition,
                            existing or item,
                            put.get("ExpressionAttributeValues"),
                            put.get("ExpressionAttributeNames"),
                            empty_item=existing is None,
                        ):
                            raise _conditional_error("TransactWriteItems")
                    item.setdefault("createdAt", _now_iso())
                    item["updatedAt"] = _now_iso()
                    self._write(item, conn)
                elif "Delete" in entry:
                    pk, sk = self._keys(entry["Delete"]["Key"])
                    self._delete(pk, sk, conn)
                elif "Update" in entry:
                    update = entry["Update"]
                    key = update["Key"]
                    pk, sk = self._keys(key)
                    row = conn.execute(
                        f"SELECT item FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = %s FOR UPDATE",
                        (self._table_name, pk, sk),
                    ).fetchone()
                    item = dict(row[0]) if row else dict(key)
                    values = dict(update.get("ExpressionAttributeValues") or {})
                    # Only plain "SET a = :v, b = :w" style is used locally.
                    set_clause = update.get("UpdateExpression", "")
                    if set_clause.upper().startswith("SET "):
                        for assignment in set_clause[4:].split(","):
                            if "=" not in assignment:
                                continue
                            name, token = (part.strip() for part in assignment.split("=", 1))
                            names = update.get("ExpressionAttributeNames") or {}
                            attr = names.get(name, name.lstrip("#"))
                            item[attr] = values.get(token)
                    if update.get("ConditionExpression"):
                        if not _eval_condition(
                            update["ConditionExpression"],
                            item,
                            values,
                            update.get("ExpressionAttributeNames"),
                        ):
                            raise _conditional_error("TransactWriteItems")
                    item["updatedAt"] = _now_iso()
                    self._write(item, conn)
                elif "ConditionCheck" in entry:
                    check = entry["ConditionCheck"]
                    pk, sk = self._keys(check["Key"])
                    row = conn.execute(
                        f"SELECT item FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = %s",
                        (self._table_name, pk, sk),
                    ).fetchone()
                    existing = row[0] if row else None
                    if not _eval_condition(
                        check["ConditionExpression"],
                        existing or {},
                        check.get("ExpressionAttributeValues"),
                        check.get("ExpressionAttributeNames"),
                        empty_item=existing is None,
                    ):
                        raise _conditional_error("TransactWriteItems")
                else:
                    raise ValueError(f"Unsupported transact item: {list(entry)}")


class PgProjectStore:
    """Local stand-in for the DataZone project APIs used by namespace create."""

    def __init__(
        self,
        *,
        domain_id: str | None = None,
        region: str | None = None,
        region_name: str | None = None,
        **_: Any,
    ) -> None:
        self._domain_id = domain_id
        self._region = region or region_name
        dsn = os.environ.get("COA_CONTROL_PLANE_PG_DSN", "").strip()
        if not dsn:
            raise RuntimeError(
                "COA_CONTROL_PLANE_PG_DSN is required when COA_PROVIDER_CONTROL_PLANE_STORE=postgres"
            )
        self._pool = _get_pool(dsn)

    def create_project(
        self,
        *,
        name: str,
        description: str | None = None,
        project_profile_id: str | None = None,
        **_: Any,
    ) -> Any:
        project_id = f"local-{uuid.uuid4()}"
        with self._pool.connection() as conn:
            conn.execute(
                f"INSERT INTO {_PROJECT_TABLE} (project_id, name, description) VALUES (%s, %s, %s)",
                (project_id, name, description),
            )

        class _Project:
            pass

        project = _Project()
        project.project_id = project_id
        project.name = name
        logger.info("local_datazone_project_created", project_id=project_id, name=name)
        return project

    def delete_project(self, project_id: str, **_: Any) -> None:
        with self._pool.connection() as conn:
            conn.execute(f"DELETE FROM {_PROJECT_TABLE} WHERE project_id = %s", (project_id,))

    def create_project_membership(self, **_: Any) -> None:
        # Local deployments have no IAM principals to add to a DataZone project.
        return None


class PgIdempotencyStore:
    """PostgreSQL store for ``coa_common.idempotency`` records.

    The upstream store is a PK-only DynamoDB table with a conditional claim,
    an owned-record takeover, a completion write and a release.  The same
    lifecycle is implemented here over one JSONB row per idempotency key, with
    ``SELECT ... FOR UPDATE`` standing in for DynamoDB's conditional writes.
    """

    def __init__(self, table_name: str, *, dsn: str | None = None) -> None:
        self._table_name = table_name
        dsn = dsn or os.environ.get("COA_CONTROL_PLANE_PG_DSN", "").strip()
        if not dsn:
            raise RuntimeError(
                "COA_CONTROL_PLANE_PG_DSN is required when COA_PROVIDER_CONTROL_PLANE_STORE=postgres"
            )
        self._pool = _get_pool(dsn)

    # -- helpers -----------------------------------------------------------

    def _load(self, conn: Any, key: str, *, lock: bool) -> dict[str, Any] | None:
        sql = f"SELECT item FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = ''"
        if lock:
            sql += " FOR UPDATE"
        row = conn.execute(sql, (self._table_name, key)).fetchone()
        return dict(row[0]) if row else None

    def _save(self, conn: Any, key: str, item: dict[str, Any]) -> None:
        conn.execute(
            f"""
            INSERT INTO {_TABLE} (table_name, pk, sk, item) VALUES (%s, %s, '', %s)
            ON CONFLICT (table_name, pk, sk) DO UPDATE SET item = EXCLUDED.item
            """,
            (self._table_name, key, Jsonb(item, dumps=lambda v: json.dumps(v, default=_json_default))),
        )

    def _delete(self, conn: Any, key: str) -> None:
        conn.execute(
            f"DELETE FROM {_TABLE} WHERE table_name = %s AND pk = %s AND sk = ''",
            (self._table_name, key),
        )

    # -- store surface -----------------------------------------------------

    def get(self, key: str) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            return self._load(conn, key, lock=False)

    def claim(self, key: str, *, operation: str, fingerprint: str, now: int) -> bool:
        item = {
            "PK": key,
            "operation": operation,
            "status": "IN_PROGRESS",
            "fingerprint": fingerprint,
            "created_at": now,
            "ttl": now + 86400,
        }
        with self._pool.connection() as conn:
            with conn.transaction():
                if self._load(conn, key, lock=True) is not None:
                    return False
                self._save(conn, key, item)
        return True

    def take_over(
        self, key: str, *, operation: str, fingerprint: str, old_created_at: int, now: int
    ) -> bool:
        with self._pool.connection() as conn:
            with conn.transaction():
                item = self._load(conn, key, lock=True)
                if item is None or item.get("created_at") != old_created_at:
                    return False
                for key_name in ("status_code", "body", "headers", "body_omitted"):
                    item.pop(key_name, None)
                item.update(
                    {
                        "operation": operation,
                        "status": "IN_PROGRESS",
                        "fingerprint": fingerprint,
                        "created_at": now,
                        "ttl": now + 86400,
                    }
                )
                self._save(conn, key, item)
        return True

    def complete(
        self, key: str, *, created_at: int, response: dict[str, Any], omit_body: bool = False
    ) -> bool:
        body = response.get("body") or ""
        if not isinstance(body, str):
            body = json.dumps(body, default=str)
        headers = {
            k: str(v)
            for k, v in (response.get("headers") or {}).items()
            if not k.lower().startswith("access-control-")
        }
        with self._pool.connection() as conn:
            with conn.transaction():
                item = self._load(conn, key, lock=True)
                if item is None or item.get("created_at") != created_at:
                    return False
                item["status"] = "COMPLETED"
                item["status_code"] = int(response.get("statusCode", 200))
                item["headers"] = headers
                if omit_body or len(body.encode("utf-8")) > 350 * 1024:
                    item["body_omitted"] = True
                    item.pop("body", None)
                else:
                    item["body"] = body
                self._save(conn, key, item)
        return True

    def release(self, key: str, *, created_at: int) -> None:
        with self._pool.connection() as conn:
            with conn.transaction():
                item = self._load(conn, key, lock=True)
                if item is not None and item.get("created_at") == created_at:
                    self._delete(conn, key)
