# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Data-dictionary surfaces for the P4 ops (F60-F66).

The five contract routes are namespace/source scoped and backed by
``DictionaryPg`` (``platform.dictionary_column`` and
``platform.dictionary_refresh_run``). ``RefreshDictionaries`` introspects a
source through an injected adapter; when no adapter is installed the route
fails with an explicit 503 instead of returning an empty snapshot.

Binding is resolved against the *published* T-Box only. When the published
graph has no properties every column is stored unbound and the response says
so via ``bindingBasis`` and ``warnings`` - there is no silent fallback to the
compiled static property list.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse

from . import catalog as catalog_module
from .adapters.dictionary_pg import (
    BINDING_METHODS,
    SOURCE_KINDS,
    DictionaryColumnInput,
    DictionaryError,
    DictionaryPg,
)

PAGE_DEFAULT = 50
PAGE_MAX = 200
DICT_VIEWS = ("all", "missing_comment", "unbound", "mappable_unbound")

_OWL = "http://www.w3.org/2002/07/owl#"


@dataclass(frozen=True)
class SourceColumn:
    """One physical column returned by a source introspection adapter."""

    table: str
    column: str
    data_type: str
    is_nullable: bool
    comment: str | None = None


@dataclass(frozen=True)
class SourceIntrospection:
    """Physical snapshot of one data source."""

    source_kind: str
    catalog: str
    schema: str
    columns: Sequence[SourceColumn]
    warnings: Sequence[str] = field(default_factory=tuple)


class SourceIntrospectionError(Exception):
    """Raised by an adapter when the source cannot be introspected."""

    def __init__(self, code: str, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


Introspector = Callable[[str, str], SourceIntrospection]
_INTROSPECTOR: Introspector | None = None


def install_source_introspector(introspector: Introspector | None) -> None:
    """Install the process-wide source introspection adapter.

    The local harness installs a PostgreSQL-backed adapter. Production wiring
    must install its own (Glue/DataZone, MySQL, ...) adapter; without one,
    refreshes fail explicitly.
    """
    global _INTROSPECTOR
    _INTROSPECTOR = introspector


def _error(status_code: int, code: str, message: str, **extra: Any) -> JSONResponse:
    payload = {"code": code, "message": message}
    payload.update(extra)
    return JSONResponse(status_code=status_code, content=payload)


def _dict_error(exc: DictionaryError) -> JSONResponse:
    status = {
        "InvalidArgument": 400,
        "NotFound": 404,
        "Conflict": 409,
        "Unavailable": 503,
    }.get(exc.code, 500)
    return _error(
        status,
        exc.code,
        exc.message,
        providerCode=exc.provider_code,
        details=exc.details,
    )


def _no_snapshot(namespace_id: str, source_id: str) -> JSONResponse:
    return _error(
        404,
        "NotFoundError",
        f"source {source_id} has no dictionary snapshot; run RefreshDictionaries first",
        namespaceId=namespace_id,
        sourceId=source_id,
    )


def _published_property_index(runtime: Any) -> tuple[dict[str, dict[str, str]], str, list[str]]:
    """Read property IRIs from the published graph without swallowing errors."""
    warnings: list[str] = []
    pointer = runtime.ontology.current()
    if not pointer:
        return {}, "published-ontology-empty", ["E_NO_PUBLISHED_ONTOLOGY"]
    graph_iri = str(pointer.get("graph") or "")
    if not graph_iri:
        return {}, "published-ontology-empty", ["E_NO_PUBLISHED_ONTOLOGY"]
    rows = runtime.graph.query(
        f"""
        SELECT ?p FROM <{graph_iri}> WHERE {{
          VALUES ?kind {{
            <{_OWL}ObjectProperty>
            <{_OWL}DatatypeProperty>
            <{_OWL}AnnotationProperty>
          }}
          ?p a ?kind .
        }}
        LIMIT 5000
        """
    ).get("bindings", [])
    properties: list[tuple[str, str]] = []
    for row in rows:
        value = (row.get("values") or {}).get("p")
        if not isinstance(value, dict):
            continue
        iri = str(value.get("iri") or value.get("value") or "")
        if iri:
            properties.append((catalog_module.local_name(iri), iri))
    if not properties:
        return {}, "published-ontology-empty", ["E_PUBLISHED_ONTOLOGY_NO_PROPERTIES"]
    return (
        catalog_module.build_property_index(properties),
        "published-ontology",
        warnings,
    )


def _table_summaries(
    store: DictionaryPg,
    metadata: Any,
    namespace_id: str,
    source_id: str,
    *,
    table: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    coverage = store.comment_coverage(
        namespace_id, source_id=source_id, table=table
    )
    where = ["namespace_id = %s", "source_id = %s"]
    params: list[Any] = [namespace_id, source_id]
    if table:
        where.append("table_name = %s")
        params.append(table)
    rows = metadata.query(
        "SELECT table_name, "
        "COUNT(*) FILTER (WHERE binding_method <> 'none') AS bound, "
        "COUNT(*) FILTER (WHERE binding_method = 'none') AS unbound "
        "FROM platform.dictionary_column WHERE " + " AND ".join(where) + " "
        "GROUP BY table_name",
        tuple(params),
    )
    bindings = {
        row["table_name"]: (int(row["bound"]), int(row["unbound"])) for row in rows
    }
    summaries = []
    for item in coverage["tables"]:
        bound, unbound = bindings.get(item["table"], (0, item["total"]))
        summaries.append(
            {
                "table": item["table"],
                "columns": item["total"],
                "commented": item["commented"],
                "bound": bound,
                "missingComment": item["missing"],
                "unbound": unbound,
            }
        )
    return summaries, coverage


def register_dictionary_routes(app: FastAPI, runtime: Any) -> None:
    """Mount the five dictionary contract routes on the platform-core app."""

    store = DictionaryPg(runtime.metadata)

    @app.get("/namespaces/{namespace_id}/dictionaries")
    def list_dictionaries(
        namespace_id: str,
        limit: int = PAGE_DEFAULT,
        offset: int = 0,
    ) -> Any:
        if limit < 1 or limit > PAGE_MAX:
            return _error(
                400, "ValidationError", f"limit must be between 1 and {PAGE_MAX}"
            )
        if offset < 0:
            return _error(400, "ValidationError", "offset must be >= 0")
        try:
            total_rows = runtime.metadata.query(
                "SELECT COUNT(DISTINCT source_id) AS total "
                "FROM platform.dictionary_column WHERE namespace_id = %s",
                (namespace_id,),
            )
            total = int(total_rows[0]["total"]) if total_rows else 0
            rows = runtime.metadata.query(
                "SELECT source_id, MAX(source_kind) AS source_kind, "
                "COUNT(*) AS columns, COUNT(DISTINCT table_name) AS tables, "
                "COUNT(*) FILTER (WHERE comment IS NOT NULL AND btrim(comment) <> '') "
                "AS commented, "
                "COUNT(*) FILTER (WHERE binding_method <> 'none') AS bound, "
                "MAX(observed_at)::text AS observed_at "
                "FROM platform.dictionary_column WHERE namespace_id = %s "
                "GROUP BY source_id ORDER BY source_id LIMIT %s OFFSET %s",
                (namespace_id, limit, offset),
            )
            items = []
            for row in rows:
                items.append(
                    {
                        "sourceId": row["source_id"],
                        "sourceKind": row["source_kind"],
                        "tables": int(row["tables"]),
                        "columns": int(row["columns"]),
                        "commented": int(row["commented"]),
                        "bound": int(row["bound"]),
                        "observedAt": row["observed_at"],
                        "lastRun": store.latest_run(namespace_id, row["source_id"]),
                    }
                )
        except DictionaryError as exc:
            return _dict_error(exc)
        return {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    @app.get("/namespaces/{namespace_id}/dictionaries/{source_id}")
    def get_dictionary(
        namespace_id: str,
        source_id: str,
        table: str | None = None,
    ) -> Any:
        latest_run = store.latest_run(namespace_id, source_id)
        if latest_run is None:
            return _no_snapshot(namespace_id, source_id)
        try:
            summaries, coverage = _table_summaries(
                store, runtime.metadata, namespace_id, source_id, table=table
            )
            identity_rows = runtime.metadata.query(
                "SELECT catalog_name, schema_name, source_kind "
                "FROM platform.dictionary_column "
                "WHERE namespace_id = %s AND source_id = %s LIMIT 1",
                (namespace_id, source_id),
            )
        except DictionaryError as exc:
            return _dict_error(exc)
        identity = identity_rows[0] if identity_rows else {}
        return {
            "sourceId": source_id,
            "sourceKind": identity.get("source_kind"),
            "catalog": identity.get("catalog_name"),
            "schema": identity.get("schema_name"),
            "tables": summaries,
            "totals": {
                "total": coverage["total"],
                "commented": coverage["commented"],
                "missing": coverage["missing"],
                "ratio": coverage["ratio"],
            },
            "boundColumns": sum(item["bound"] for item in summaries),
            "latestRun": latest_run,
        }

    @app.get("/namespaces/{namespace_id}/dictionaries/{source_id}/view")
    def get_dictionary_view(
        namespace_id: str,
        source_id: str,
        view: str = "all",
        table: str | None = None,
        column: str | None = None,
        bindingMethod: str | None = None,
        sourceKind: str | None = None,
        q: str | None = None,
        limit: int = PAGE_DEFAULT,
        offset: int = 0,
    ) -> Any:
        if store.latest_run(namespace_id, source_id) is None:
            return _no_snapshot(namespace_id, source_id)
        if view not in DICT_VIEWS:
            return _error(
                400,
                "ValidationError",
                f"view must be one of {list(DICT_VIEWS)}",
            )
        if bindingMethod is not None and bindingMethod not in BINDING_METHODS:
            return _error(
                400,
                "ValidationError",
                f"bindingMethod must be one of {sorted(BINDING_METHODS)}",
            )
        if sourceKind is not None and sourceKind not in SOURCE_KINDS:
            return _error(
                400,
                "ValidationError",
                f"sourceKind must be one of {sorted(SOURCE_KINDS)}",
            )
        if limit < 1 or limit > PAGE_MAX:
            return _error(
                400, "ValidationError", f"limit must be between 1 and {PAGE_MAX}"
            )
        if offset < 0:
            return _error(400, "ValidationError", "offset must be >= 0")

        warnings: list[str] = []
        mappable_pairs: list[tuple[str, str]] = []
        try:
            if view == "mappable_unbound":
                candidates = runtime.metadata.query(
                    "SELECT DISTINCT table_name, column_name "
                    "FROM platform.dictionary_column "
                    "WHERE namespace_id = %s AND source_id = %s "
                    "AND binding_method = 'none'",
                    (namespace_id, source_id),
                )
                mappable_pairs = [
                    (row["table_name"], row["column_name"])
                    for row in candidates
                    if catalog_module.is_mappable(row["table_name"], row["column_name"])
                ]
                if not mappable_pairs:
                    coverage = store.comment_coverage(
                        namespace_id, source_id=source_id
                    )
                    return {
                        "items": [],
                        "total": 0,
                        "offset": offset,
                        "limit": limit,
                        "view": view,
                        "coverage": {
                            "total": coverage["total"],
                            "commented": coverage["commented"],
                            "missing": coverage["missing"],
                            "ratio": coverage["ratio"],
                        },
                        "warnings": ["E_MAPPABLE_PAIRS_EMPTY"],
                    }
            page = store.list_columns(
                namespace_id,
                source_id=source_id,
                table=table,
                column=column,
                binding_method=bindingMethod,
                source_kind=sourceKind,
                q=q,
                view=view,
                mappable_pairs=mappable_pairs,
                limit=limit,
                offset=offset,
            )
            coverage = store.comment_coverage(
                namespace_id, source_id=source_id, table=table
            )
        except DictionaryError as exc:
            return _dict_error(exc)
        return {
            "items": page["items"],
            "total": page["total"],
            "offset": page["offset"],
            "limit": page["limit"],
            "view": view,
            "coverage": {
                "total": coverage["total"],
                "commented": coverage["commented"],
                "missing": coverage["missing"],
                "ratio": coverage["ratio"],
            },
            "warnings": warnings,
        }

    @app.get("/namespaces/{namespace_id}/dictionaries/{source_id}/comment-coverage")
    def get_dictionary_comment_coverage(
        namespace_id: str,
        source_id: str,
        table: str | None = None,
    ) -> Any:
        if store.latest_run(namespace_id, source_id) is None:
            return _no_snapshot(namespace_id, source_id)
        try:
            summaries, coverage = _table_summaries(
                store, runtime.metadata, namespace_id, source_id, table=table
            )
        except DictionaryError as exc:
            return _dict_error(exc)
        return {
            "sourceId": source_id,
            "coverage": {
                "total": coverage["total"],
                "commented": coverage["commented"],
                "missing": coverage["missing"],
                "ratio": coverage["ratio"],
            },
            "tables": summaries,
        }

    @app.post("/namespaces/{namespace_id}/dictionaries/{source_id}/refresh")
    def refresh_dictionaries(
        namespace_id: str,
        source_id: str,
        payload: dict[str, Any] | None = Body(default=None),
    ) -> Any:
        body = payload or {}
        key = body.get("idempotencyKey") or f"auto-{uuid4().hex}"
        requested_by = body.get("requestedBy")
        if not isinstance(key, str) or not key or len(key) > 128:
            return _error(
                400,
                "ValidationError",
                "idempotencyKey must be a non-empty string of at most 128 chars",
            )
        if requested_by is not None and (
            not isinstance(requested_by, str) or len(requested_by) > 128
        ):
            return _error(
                400,
                "ValidationError",
                "requestedBy must be a string of at most 128 chars",
            )
        if _INTROSPECTOR is None:
            return _error(
                503,
                "ServiceUnavailableError",
                "no source introspection adapter is installed for RefreshDictionaries",
                providerCode="E_DICTIONARY_INTROSPECTOR_UNAVAILABLE",
            )
        try:
            begun = store.begin_refresh(
                namespace_id, source_id, key, requested_by=requested_by
            )
        except DictionaryError as exc:
            return _dict_error(exc)
        if not begun["created"]:
            if begun["status"] == "succeeded":
                return {
                    "run": begun,
                    "bindingBasis": "replay",
                    "warnings": ["E_REFRESH_REPLAYED"],
                }
            return _error(
                409,
                "Conflict",
                "the idempotencyKey belongs to a failed run; retry with a new key",
                providerCode="E_REFRESH_KEY_FAILED",
                details={"runId": begun["runId"], "status": begun["status"]},
            )

        run_id = begun["runId"]
        try:
            introspection = _INTROSPECTOR(namespace_id, source_id)
            if introspection.source_kind not in SOURCE_KINDS:
                raise SourceIntrospectionError(
                    "E_DICTIONARY_SOURCE_KIND_UNSUPPORTED",
                    f"source kind {introspection.source_kind!r} is not supported",
                    status_code=422,
                )
            if not introspection.columns:
                raise SourceIntrospectionError(
                    "E_DICTIONARY_SOURCE_EMPTY",
                    f"source {source_id!r} exposed zero columns; refusing to write an empty snapshot",
                    status_code=422,
                )
            index, basis, binding_warnings = _published_property_index(runtime)
            inputs: list[DictionaryColumnInput] = []
            for item in introspection.columns:
                binding = catalog_module.resolve_binding(item.table, item.column, index)
                inputs.append(
                    DictionaryColumnInput(
                        catalog=introspection.catalog,
                        schema=introspection.schema,
                        table=item.table,
                        column=item.column,
                        data_type=item.data_type,
                        is_nullable=item.is_nullable,
                        source_kind=introspection.source_kind,
                        comment=item.comment,
                        property_iri=binding["propertyIri"],
                        binding_method=binding["bindingMethod"],
                        confidence=binding["confidence"],
                        binding_note=binding["bindingNote"],
                    )
                )
            counts = store.upsert_snapshot(namespace_id, source_id, run_id, inputs)
            finished = store.finish_refresh(
                run_id, status="succeeded", **counts
            )
        except SourceIntrospectionError as exc:
            store.finish_refresh(run_id, status="failed", error=exc.message)
            return _error(
                exc.status_code, exc.code, exc.message, runId=run_id
            )
        except DictionaryError as exc:
            store.finish_refresh(run_id, status="failed", error=exc.message)
            return _dict_error(exc)
        except Exception as exc:  # noqa: BLE001 - the run must not stay 'running'
            message = str(exc) or type(exc).__name__
            store.finish_refresh(run_id, status="failed", error=message)
            return _error(
                500,
                "InternalServerError",
                f"dictionary refresh failed: {message}",
                runId=run_id,
            )
        return {
            "run": finished,
            "bindingBasis": basis,
            "warnings": list(binding_warnings) + list(introspection.warnings),
        }
