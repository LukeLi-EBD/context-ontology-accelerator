# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Ontology registry provider backed by the local PostgreSQL item table.

``coa_ontology.dynamo_store`` keeps the ontology catalog in DynamoDB. In the
local deployment the same item semantics live in ``public.coa_local_items``
(see ``control_plane_pg.PgDatastoreDAO``), so the registry read/write
functions are re-pointed at PostgreSQL at process start.

Only the catalog registry functions are replaced. Job / proposal bookkeeping
(induction write path) keeps its upstream implementation and is out of scope
for the local read path — callers of those routes will fail loudly rather than
silently return empty data.

Configuration (fails closed):

    COA_CONTROL_PLANE_PG_DSN     PostgreSQL DSN (required)
    DYNAMODB_TABLE               logical table name (default ``ontology-engine``)
    COA_ONTOLOGY_REGISTRY_TABLE  overrides the logical table name (optional)
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from coa_local_providers.control_plane_pg import PgDatastoreDAO

_SK_PREFIX = "ONTOLOGY#"


def _namespace_pk(namespace: str) -> str:
    return f"NAMESPACE#{namespace}"


def _ontology_sk(ontology_id: str) -> str:
    return f"{_SK_PREFIX}{ontology_id}"


def _table_name() -> str:
    name = os.environ.get("COA_ONTOLOGY_REGISTRY_TABLE", "").strip() or os.environ.get("DYNAMODB_TABLE", "").strip()
    if not name:
        raise RuntimeError(
            "COA_ONTOLOGY_REGISTRY_TABLE (or DYNAMODB_TABLE) is required when "
            "COA_PROVIDER_ONTOLOGY_REGISTRY=postgres"
        )
    return name


def _dao() -> PgDatastoreDAO:
    return PgDatastoreDAO(_table_name(), region=os.environ.get("AWS_REGION"))


def _rows(namespace: str) -> list[dict[str, Any]]:
    pk = _namespace_pk(namespace)
    return [
        item
        for item in _dao()._fetch_all()
        if item.get("PK") == pk and str(item.get("SK", "")).startswith(_SK_PREFIX)
    ]


def _matches(
    row: dict[str, Any],
    ontology_type: str | None,
    domain_tag: str | None,
    attribute_equals: dict[str, str] | None,
) -> bool:
    if ontology_type and row.get("ontology_type") != ontology_type:
        return False
    if domain_tag:
        tags = row.get("domain_tags") or []
        if domain_tag not in tags:
            return False
    for attr, want in (attribute_equals or {}).items():
        if str(row.get(attr)) != str(want):
            return False
    return True


def list_ontologies_registry(
    namespace: str,
    ontology_type: str | None = None,
    domain_tag: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    rows = [
        row
        for row in _rows(namespace)
        if _matches(row, ontology_type, domain_tag, None)
    ]
    rows.sort(key=lambda r: str(r.get("SK", "")))
    return rows if limit is None else rows[:limit]


def list_ontologies_registry_page(
    namespace: str,
    ontology_type: str | None = None,
    domain_tag: str | None = None,
    attribute_equals: dict[str, str] | None = None,
    limit: int = 50,
    exclusive_start_key: dict[str, str] | None = None,
) -> tuple[list[dict], dict[str, str] | None]:
    rows = [
        row
        for row in _rows(namespace)
        if _matches(row, ontology_type, domain_tag, attribute_equals)
    ]
    rows.sort(key=lambda r: str(r.get("SK", "")))

    if exclusive_start_key:
        start_sk = str(exclusive_start_key.get("SK", ""))
        rows = [row for row in rows if str(row.get("SK", "")) > start_sk]

    page = rows[:limit]
    next_key = None
    if len(rows) > limit and page:
        last = page[-1]
        next_key = {"PK": last.get("PK"), "SK": last.get("SK")}
    return page, next_key


def get_ontology_registry(namespace: str, ontology_id: str) -> dict | None:
    return _dao().get({"PK": _namespace_pk(namespace), "SK": _ontology_sk(ontology_id)})


def put_ontology_registry(namespace: str, ontology_id: str, data: dict) -> dict:
    ts = datetime.now(UTC).isoformat()
    existing = get_ontology_registry(namespace, ontology_id)
    item: dict[str, Any] = {
        "PK": _namespace_pk(namespace),
        "SK": _ontology_sk(ontology_id),
        "namespace": namespace,
        "ontology_id": ontology_id,
        "created_at": (existing or {}).get("created_at", ts),
        "updated_at": ts,
    }
    if existing:
        item = {**existing, **item}
    item.update({k: v for k, v in data.items() if v is not None})
    if "status" not in data and item.get("status") in ("ingesting", "deleting"):
        item.pop("status", None)
    _dao().put(item, auto_timestamp=False)
    return item


def install_ontology_registry() -> str:
    """Patch the registry functions; returns the selected provider.

    ``COA_PROVIDER_ONTOLOGY_REGISTRY`` must be set explicitly (``postgres`` or
    ``dynamodb``). ``dynamodb`` keeps the upstream AWS implementation.
    """
    provider = os.environ.get("COA_PROVIDER_ONTOLOGY_REGISTRY", "").strip().lower()
    if not provider:
        raise RuntimeError(
            "COA_PROVIDER_ONTOLOGY_REGISTRY is required (postgres|dynamodb); refusing to start "
            "without an explicitly selected ontology registry"
        )
    if provider not in ("postgres", "dynamodb"):
        raise RuntimeError(
            f"Unknown COA_PROVIDER_ONTOLOGY_REGISTRY={provider!r}; expected postgres|dynamodb"
        )
    if provider == "dynamodb":
        return provider

    # Validate keys up front so a missing DSN/table fails at startup.
    _table_name()
    if not os.environ.get("COA_CONTROL_PLANE_PG_DSN", "").strip():
        raise RuntimeError(
            "COA_CONTROL_PLANE_PG_DSN is required when COA_PROVIDER_ONTOLOGY_REGISTRY=postgres"
        )

    from coa_ontology import dynamo_store

    dynamo_store.list_ontologies_registry = list_ontologies_registry  # type: ignore[assignment]
    dynamo_store.list_ontologies_registry_page = list_ontologies_registry_page  # type: ignore[assignment]
    dynamo_store.get_ontology_registry = get_ontology_registry  # type: ignore[assignment]
    dynamo_store.put_ontology_registry = put_ontology_registry  # type: ignore[assignment]
    return provider
