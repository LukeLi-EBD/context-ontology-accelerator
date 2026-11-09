# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Ontology job / proposal storage on PostgreSQL (local) instead of DynamoDB.

``coa_ontology.dynamo_store`` keeps every non-graph record — induction jobs,
async ingest jobs, validation jobs, proposals — in one DynamoDB table. All of
those call sites go through exactly two seams:

    _get_table()   boto3 ``Table``   (put_item / get_item / update_item /
                                      delete_item / scan / query / batch_writer)
    _get_dao()     ``DynamoDBDAO``   (ingest-job helpers)

This module swaps both seams for a PostgreSQL-backed item table
(``public.coa_local_items``, the same table ``control_plane_pg`` uses) at
process start, so the call sites stay untouched. It is the write-path sibling
of ``ontology_registry_pg``: that one replaced the *catalog* functions, this one
replaces the *item table* itself, which is why jobs and proposals come along
for free.

Configuration (no default provider — startup fails closed):

    COA_PROVIDER_ONTOLOGY_JOBS   postgres | dynamodb   (required)
    COA_CONTROL_PLANE_PG_DSN     PostgreSQL DSN        (required for postgres)
    DYNAMODB_TABLE               logical table name    (default ``ontology-engine``)

``dynamodb`` leaves the upstream AWS implementation untouched.
"""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from typing import Any, Iterator

from coa_local_providers.control_plane_pg import (
    PgDatastoreDAO,
    _conditional_error,
    _eval_condition,
    _matches_key,
    _parse_key_condition,
    _sort_value,
)

_PROVIDERS = ("postgres", "dynamodb")

_SET_PART = re.compile(r"^([#\w.\-]+)\s*=\s*(:\w+)$")
_REMOVE_PART = re.compile(r"^([#\w.\-]+)$")


def _provider() -> str:
    raw = os.environ.get("COA_PROVIDER_ONTOLOGY_JOBS", "").strip().lower()
    if not raw:
        raise RuntimeError(
            "COA_PROVIDER_ONTOLOGY_JOBS is required (postgres|dynamodb); refusing to start "
            "without an explicitly selected ontology job store"
        )
    if raw not in _PROVIDERS:
        raise RuntimeError(f"Unknown COA_PROVIDER_ONTOLOGY_JOBS={raw!r}; expected one of {_PROVIDERS}")
    return raw


def _table_name() -> str:
    return os.environ.get("DYNAMODB_TABLE", "").strip() or "ontology-engine"


def _resolve(name: str, names: dict[str, str] | None) -> str:
    name = name.strip()
    if names and name in names:
        return names[name]
    return name.lstrip("#")


def _project(item: dict[str, Any], expression: str | None) -> dict[str, Any]:
    if not expression:
        return item
    wanted = [part.strip() for part in expression.split(",") if part.strip()]
    return {k: v for k, v in item.items() if k in wanted}


def _apply_update(
    item: dict[str, Any],
    update_expression: str,
    names: dict[str, str] | None,
    values: dict[str, Any] | None,
) -> None:
    """Apply the ``SET``/``REMOVE`` subset the ontology engine actually emits.

    ``dynamo_store`` only ever writes ``SET a = :v[, #b = :v2]`` and
    ``SET updated_at = :ts``; anything else is a bug worth failing loudly on
    rather than silently dropping.
    """
    values = values or {}
    expression = update_expression.strip()
    upper = expression.upper()
    if not upper.startswith("SET "):
        raise ValueError(f"Unsupported UpdateExpression: {update_expression!r}")
    for part in expression[4:].split(","):
        part = part.strip()
        if not part:
            continue
        if part.upper().startswith("REMOVE "):
            for removed in part[7:].split(","):
                item.pop(_resolve(removed, names), None)
            continue
        match = _SET_PART.match(part)
        if not match:
            raise ValueError(f"Unsupported UpdateExpression part: {part!r}")
        attr = _resolve(match.group(1), names)
        if match.group(2) not in values:
            raise ValueError(f"UpdateExpression placeholder {match.group(2)} has no value")
        item[attr] = values[match.group(2)]


class PgTable:
    """boto3 ``Table`` subset over :class:`PgDatastoreDAO`, backed by PG rows."""

    def __init__(self, dao: PgDatastoreDAO) -> None:
        self._dao = dao

    # -- single item -------------------------------------------------------

    def put_item(
        self,
        Item: dict[str, Any],
        ConditionExpression: str | None = None,
        ExpressionAttributeNames: dict[str, str] | None = None,
        ExpressionAttributeValues: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        item = dict(Item)
        pk, sk = self._dao._keys(item)
        existing = self._dao._fetch(pk, sk)
        if ConditionExpression:
            ok = _eval_condition(
                ConditionExpression,
                existing or {},
                ExpressionAttributeValues,
                ExpressionAttributeNames,
                empty_item=existing is None,
            )
            if not ok:
                raise _conditional_error("PutItem")
        with self._dao._pool.connection() as conn:
            self._dao._write(item, conn)
        return {}

    def get_item(self, Key: dict[str, Any], **_: Any) -> dict[str, Any]:
        pk, sk = self._dao._keys(Key)
        item = self._dao._fetch(pk, sk)
        return {"Item": item} if item is not None else {}

    def update_item(
        self,
        Key: dict[str, Any],
        UpdateExpression: str,
        ExpressionAttributeNames: dict[str, str] | None = None,
        ExpressionAttributeValues: dict[str, Any] | None = None,
        ConditionExpression: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        pk, sk = self._dao._keys(Key)
        with self._dao._pool.connection() as conn:
            existing = self._dao._fetch(pk, sk)
            item = dict(existing) if existing else {"PK": Key.get("PK"), "SK": Key.get("SK")}
            if ConditionExpression:
                ok = _eval_condition(
                    ConditionExpression,
                    item,
                    ExpressionAttributeValues,
                    ExpressionAttributeNames,
                    empty_item=existing is None,
                )
                if not ok:
                    raise _conditional_error("UpdateItem")
            _apply_update(item, UpdateExpression, ExpressionAttributeNames, ExpressionAttributeValues)
            self._dao._write(item, conn)
        return {}

    def delete_item(
        self,
        Key: dict[str, Any],
        ConditionExpression: str | None = None,
        ExpressionAttributeNames: dict[str, str] | None = None,
        ExpressionAttributeValues: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        pk, sk = self._dao._keys(Key)
        if ConditionExpression:
            existing = self._dao._fetch(pk, sk)
            ok = _eval_condition(
                ConditionExpression,
                existing or {},
                ExpressionAttributeValues,
                ExpressionAttributeNames,
                empty_item=existing is None,
            )
            if not ok:
                raise _conditional_error("DeleteItem")
        with self._dao._pool.connection() as conn:
            self._dao._delete(pk, sk, conn)
        return {}

    # -- collections -------------------------------------------------------

    def _select(
        self,
        *,
        filter_expression: str | None,
        values: dict[str, Any] | None,
        names: dict[str, str] | None,
        key_condition: str | None,
        scan_forward: bool,
        exclusive_start_key: dict[str, Any] | None,
        limit: int | None,
    ) -> dict[str, Any]:
        items = self._dao._fetch_all()
        sort_attr: str | None = None
        if key_condition:
            conditions, sort_attr = _parse_key_condition(key_condition, values or {}, names)
            items = [item for item in items if _matches_key(item, conditions)]
        if filter_expression:
            items = [
                item
                for item in items
                if _eval_condition(filter_expression, item, values, names)
            ]
        if sort_attr:
            items.sort(
                key=lambda i: (_sort_value(i, sort_attr), str(i.get("PK", "")), str(i.get("SK", ""))),
                reverse=not scan_forward,
            )
        else:
            items.sort(
                key=lambda i: (str(i.get("PK", "")), str(i.get("SK", ""))),
                reverse=not scan_forward,
            )
        if exclusive_start_key:
            pk, sk = self._dao._keys(exclusive_start_key)
            for idx, item in enumerate(items):
                if str(item.get("PK", "")) == pk and str(item.get("SK", "")) == sk:
                    items = items[idx + 1 :] if scan_forward else items[:idx]
                    break
        last_key = None
        if limit is not None and len(items) > limit:
            items = items[:limit]
            last_key = {"PK": items[-1].get("PK"), "SK": items[-1].get("SK")}
        return {"Items": items, "LastEvaluatedKey": last_key}

    def scan(
        self,
        FilterExpression: str | None = None,
        ExpressionAttributeValues: dict[str, Any] | None = None,
        ExpressionAttributeNames: dict[str, str] | None = None,
        ProjectionExpression: str | None = None,
        Limit: int | None = None,
        ExclusiveStartKey: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        page = self._select(
            filter_expression=FilterExpression,
            values=ExpressionAttributeValues,
            names=ExpressionAttributeNames,
            key_condition=None,
            scan_forward=True,
            exclusive_start_key=ExclusiveStartKey,
            limit=Limit,
        )
        return {
            "Items": [_project(item, ProjectionExpression) for item in page["Items"]],
            "LastEvaluatedKey": page["LastEvaluatedKey"],
        }

    def query(
        self,
        KeyConditionExpression: str,
        ExpressionAttributeValues: dict[str, Any] | None = None,
        ExpressionAttributeNames: dict[str, str] | None = None,
        FilterExpression: str | None = None,
        ProjectionExpression: str | None = None,
        Limit: int | None = None,
        ExclusiveStartKey: dict[str, Any] | None = None,
        ScanIndexForward: bool = True,
        **_: Any,
    ) -> dict[str, Any]:
        page = self._select(
            filter_expression=FilterExpression,
            values=ExpressionAttributeValues,
            names=ExpressionAttributeNames,
            key_condition=KeyConditionExpression,
            scan_forward=ScanIndexForward,
            exclusive_start_key=ExclusiveStartKey,
            limit=Limit,
        )
        return {
            "Items": [_project(item, ProjectionExpression) for item in page["Items"]],
            "LastEvaluatedKey": page["LastEvaluatedKey"],
        }

    @contextmanager
    def batch_writer(self) -> Iterator["_BatchWriter"]:
        writer = _BatchWriter(self._dao)
        yield writer
        writer.flush()


class _BatchWriter:
    def __init__(self, dao: PgDatastoreDAO) -> None:
        self._dao = dao
        self._deletes: list[tuple[str, str]] = []

    def delete_item(self, Key: dict[str, Any], **_: Any) -> None:
        self._deletes.append(self._dao._keys(Key))

    def put_item(self, Item: dict[str, Any], **_: Any) -> None:
        with self._dao._pool.connection() as conn:
            self._dao._write(dict(Item), conn)

    def flush(self) -> None:
        if not self._deletes:
            return
        with self._dao._pool.connection() as conn:
            for pk, sk in self._deletes:
                self._dao._delete(pk, sk, conn)
        self._deletes.clear()


def install_ontology_jobs() -> str:
    """Patch the ontology engine's item-table seams; returns the provider."""
    provider = _provider()
    if provider == "dynamodb":
        return provider
    if not os.environ.get("COA_CONTROL_PLANE_PG_DSN", "").strip():
        raise RuntimeError(
            "COA_CONTROL_PLANE_PG_DSN is required when COA_PROVIDER_ONTOLOGY_JOBS=postgres"
        )

    from coa_ontology import dynamo_store

    dao = PgDatastoreDAO(_table_name(), region=os.environ.get("AWS_REGION"))
    table = PgTable(dao)
    dynamo_store._get_table = lambda: table  # type: ignore[assignment]
    dynamo_store._get_dao = lambda: dao  # type: ignore[assignment]
    return provider
