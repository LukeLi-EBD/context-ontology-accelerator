"""Dictionary storage provider (PostgreSQL), namespace scoped.

Storage for F60-F66 (P4). Two tables, both created by V46:

* ``platform.dictionary_refresh_run`` - one row per introspection attempt.
  ``(namespace_id, source_id, idempotency_key)`` is unique, which is what makes
  a repeated RefreshDictionaries call a no-op instead of a second write.
* ``platform.dictionary_column`` - the current introspection snapshot, keyed by
  namespace, source and the four-part column identity.

Design notes that matter for the COA side:

* ``namespace_id`` and ``source_id`` are text references to the control-plane
  item store. There is intentionally no cross-schema foreign key because
  namespaces and sources do not live in this database. Empty values are
  rejected instead of defaulted.
* The legacy ``platform.data_dictionary`` table is single tenant and is not
  read or written here. Reusing it would either leak rows across namespaces or
  require inventing a namespace for existing rows.
* Manual bindings are operator input: a refresh never overwrites
  ``binding_method = 'manual'`` rows, matching V39's contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from ..errors import PortError
from .metadata_pg import MetadataPg

PROVIDER = "postgres"

SOURCE_KINDS = frozenset(
    {"postgresql", "mysql", "redshift", "sqlserver", "snowflake", "glue", "duckdb"}
)
BINDING_METHODS = frozenset({"explicit", "name_match", "manual", "none"})
LIST_VIEWS = frozenset({"all", "missing_comment", "unbound", "mappable_unbound"})

_PAGE_DEFAULT = 20
_PAGE_MAX = 200


class DictionaryError(PortError):
    """PortError subtype so callers can catch dictionary failures precisely."""


def _invalid(field: str, message: str, provider_code: str = "E_DICTIONARY_INVALID") -> DictionaryError:
    return DictionaryError(
        code="InvalidArgument",
        message=message,
        provider=PROVIDER,
        provider_code=provider_code,
        details={"field": field},
    )


def _conflict(message: str, provider_code: str, details: dict[str, Any] | None = None) -> DictionaryError:
    return DictionaryError(
        code="Conflict",
        message=message,
        provider=PROVIDER,
        provider_code=provider_code,
        details=details,
    )


def _not_found(message: str, provider_code: str) -> DictionaryError:
    return DictionaryError(
        code="NotFound",
        message=message,
        provider=PROVIDER,
        provider_code=provider_code,
    )


def _required_text(value: Any, field: str) -> str:
    if value is None:
        raise _invalid(field, f"{field} is required")
    text = str(value).strip()
    if not text:
        raise _invalid(field, f"{field} must not be empty")
    return text


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_confidence(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise _invalid("confidence", "confidence must be a number, not a boolean")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise _invalid("confidence", f"confidence is not a number: {value!r}") from exc
    if number < 0 or number > 1:
        raise _invalid("confidence", f"confidence must be within [0, 1]: {value!r}")
    return number.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class DictionaryColumnInput:
    """One introspected column. Required fields have no defaults on purpose."""

    catalog: str
    schema: str
    table: str
    column: str
    data_type: str
    is_nullable: bool
    source_kind: str
    comment: str | None = None
    property_iri: str | None = None
    binding_method: str = "none"
    confidence: Decimal | float | str | None = None
    binding_note: str | None = None


@dataclass(frozen=True)
class _NormalizedColumn:
    catalog: str
    schema: str
    table: str
    column: str
    data_type: str
    is_nullable: bool
    source_kind: str
    comment: str | None
    property_iri: str | None
    binding_method: str
    confidence: Decimal | None
    binding_note: str | None

    def identity(self) -> tuple[str, str, str, str]:
        return (self.catalog, self.schema, self.table, self.column)

    def business(self) -> tuple[Any, ...]:
        return (
            self.data_type,
            self.is_nullable,
            self.comment,
            self.source_kind,
            self.property_iri,
            self.binding_method,
            self.confidence,
            self.binding_note,
        )


def _normalize(column: DictionaryColumnInput) -> _NormalizedColumn:
    if not isinstance(column, DictionaryColumnInput):
        raise _invalid("columns", "each column must be a DictionaryColumnInput instance")
    if not isinstance(column.is_nullable, bool):
        raise _invalid("isNullable", "isNullable must be a boolean")
    source_kind = _required_text(column.source_kind, "sourceKind")
    if source_kind not in SOURCE_KINDS:
        raise _invalid(
            "sourceKind",
            f"unsupported sourceKind {source_kind!r}; expected one of {sorted(SOURCE_KINDS)}",
        )
    binding_method = _required_text(column.binding_method, "bindingMethod")
    if binding_method not in BINDING_METHODS:
        raise _invalid(
            "bindingMethod",
            f"unsupported bindingMethod {binding_method!r}; expected one of {sorted(BINDING_METHODS)}",
        )
    return _NormalizedColumn(
        catalog=_required_text(column.catalog, "catalog"),
        schema=_required_text(column.schema, "schema"),
        table=_required_text(column.table, "table"),
        column=_required_text(column.column, "column"),
        data_type=_required_text(column.data_type, "dataType"),
        is_nullable=column.is_nullable,
        source_kind=source_kind,
        comment=_optional_text(column.comment, "comment"),
        property_iri=_optional_text(column.property_iri, "propertyIri"),
        binding_method=binding_method,
        confidence=_normalize_confidence(column.confidence),
        binding_note=_optional_text(column.binding_note, "bindingNote"),
    )


def _run_out(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "runId": row["run_id"],
        "namespaceId": row["namespace_id"],
        "sourceId": row["source_id"],
        "idempotencyKey": row["idempotency_key"],
        "requestedBy": row["requested_by"],
        "status": row["status"],
        "startedAt": row["started_at"],
        "finishedAt": row["finished_at"],
        "processed": row["processed"],
        "inserted": row["inserted"],
        "updated": row["updated"],
        "unchanged": row["unchanged"],
        "removed": row["removed"],
        "error": row["error"],
    }


def _column_out(row: Mapping[str, Any]) -> dict[str, Any]:
    confidence = row["confidence"]
    return {
        "namespaceId": row["namespace_id"],
        "sourceId": row["source_id"],
        "catalog": row["catalog_name"],
        "schema": row["schema_name"],
        "table": row["table_name"],
        "column": row["column_name"],
        "dataType": row["data_type"],
        "isNullable": row["is_nullable"],
        "comment": row["comment"],
        "sourceKind": row["source_kind"],
        "propertyIri": row["property_iri"],
        "bindingMethod": row["binding_method"],
        "confidence": None if confidence is None else float(confidence),
        "bindingNote": row["binding_note"],
        "observedAt": row["observed_at"],
        "lastRefreshRunId": row["last_refresh_run_id"],
    }


_RUN_COLUMNS = (
    "run_id, namespace_id, source_id, idempotency_key, requested_by, status, "
    "started_at, finished_at, processed, inserted, updated, unchanged, removed, error"
)

_COLUMN_COLUMNS = (
    "namespace_id, source_id, catalog_name, schema_name, table_name, column_name, "
    "data_type, is_nullable, comment, source_kind, property_iri, binding_method, "
    "confidence, binding_note, observed_at, last_refresh_run_id"
)


class DictionaryPg:
    """Namespace-scoped dictionary snapshot + refresh ledger on PostgreSQL."""

    port = "DictionaryStore"

    def __init__(self, metadata: MetadataPg) -> None:
        self._metadata = metadata

    # ------------------------------------------------------------------ refresh

    def begin_refresh(
        self,
        namespace_id: str,
        source_id: str,
        idempotency_key: str,
        requested_by: str | None = None,
    ) -> dict[str, Any]:
        """Open a refresh run, or return the run already using this key.

        ``created`` is False for a repeated key. A repeated key never starts a
        second introspection pass. A still-running duplicate raises Conflict so
        the caller cannot silently double-write.
        """
        namespace = _required_text(namespace_id, "namespaceId")
        source = _required_text(source_id, "sourceId")
        key = _required_text(idempotency_key, "idempotencyKey")
        run_id = _new_run_id()
        with self._metadata.tx() as tx:
            tx.execute(
                "INSERT INTO platform.dictionary_refresh_run "
                "(run_id, namespace_id, source_id, idempotency_key, requested_by, status) "
                "VALUES (%s, %s, %s, %s, %s, 'running') "
                "ON CONFLICT (namespace_id, source_id, idempotency_key) DO NOTHING",
                (run_id, namespace, source, key, _optional_text(requested_by, "requestedBy")),
            )
            rows = tx.query(
                f"SELECT {_RUN_COLUMNS} FROM platform.dictionary_refresh_run "
                "WHERE namespace_id = %s AND source_id = %s AND idempotency_key = %s "
                "FOR UPDATE",
                (namespace, source, key),
            )
        if not rows:
            raise _not_found(
                "refresh run disappeared after insert", "E_REFRESH_RUN_MISSING"
            )
        row = rows[0]
        created = row["run_id"] == run_id
        if row["status"] == "running" and not created:
            raise _conflict(
                "the same idempotencyKey is already running",
                "E_REFRESH_IN_PROGRESS",
                {"runId": row["run_id"], "idempotencyKey": key},
            )
        result = _run_out(row)
        result["created"] = created
        return result

    def upsert_snapshot(
        self,
        namespace_id: str,
        source_id: str,
        run_id: str,
        columns: Sequence[DictionaryColumnInput],
    ) -> dict[str, int]:
        """Write one introspection snapshot for an open run.

        Counts are computed against the previous snapshot, so a repeated
        refresh of unchanged data reports ``unchanged`` and leaves the row count
        identical. Manual bindings are carried over untouched.
        """
        namespace = _required_text(namespace_id, "namespaceId")
        source = _required_text(source_id, "sourceId")
        run = _required_text(run_id, "runId")
        normalized: list[_NormalizedColumn] = []
        seen: set[tuple[str, str, str, str]] = set()
        for column in columns:
            item = _normalize(column)
            identity = item.identity()
            if identity in seen:
                raise _invalid(
                    "columns",
                    f"duplicate column in snapshot: {'.'.join(identity)}",
                    "E_DUPLICATE_COLUMN",
                )
            seen.add(identity)
            normalized.append(item)

        inserted = 0
        updated = 0
        unchanged = 0
        with self._metadata.tx() as tx:
            run_rows = tx.query(
                "SELECT namespace_id, source_id, status FROM platform.dictionary_refresh_run "
                "WHERE run_id = %s FOR UPDATE",
                (run,),
            )
            if not run_rows:
                raise _not_found(f"refresh run {run} does not exist", "E_REFRESH_RUN_MISSING")
            current = run_rows[0]
            if current["namespace_id"] != namespace or current["source_id"] != source:
                raise _invalid(
                    "runId",
                    "refresh run belongs to a different namespace or source",
                    "E_REFRESH_SCOPE_MISMATCH",
                )
            if current["status"] != "running":
                raise _conflict(
                    f"refresh run {run} is {current['status']}, not running",
                    "E_REFRESH_NOT_RUNNING",
                    {"runId": run, "status": current["status"]},
                )

            existing_rows = tx.query(
                f"SELECT {_COLUMN_COLUMNS} FROM platform.dictionary_column "
                "WHERE namespace_id = %s AND source_id = %s",
                (namespace, source),
            )
            existing = {
                (row["catalog_name"], row["schema_name"], row["table_name"], row["column_name"]): row
                for row in existing_rows
            }

            to_insert: list[tuple[Any, ...]] = []
            to_update: list[tuple[Any, ...]] = []
            for item in normalized:
                previous = existing.get(item.identity())
                effective = item
                if previous is not None and previous["binding_method"] == "manual":
                    effective = _keep_manual(item, previous)
                changed = previous is None or _business_changed(effective, previous)
                if previous is None:
                    inserted += 1
                    to_insert.append(
                        (
                            namespace,
                            source,
                            item.catalog,
                            item.schema,
                            item.table,
                            item.column,
                            effective.data_type,
                            effective.is_nullable,
                            effective.comment,
                            effective.source_kind,
                            effective.property_iri,
                            effective.binding_method,
                            effective.confidence,
                            effective.binding_note,
                            run,
                        )
                    )
                else:
                    if changed:
                        updated += 1
                    else:
                        unchanged += 1
                    to_update.append(
                        (
                            effective.data_type,
                            effective.is_nullable,
                            effective.comment,
                            effective.source_kind,
                            effective.property_iri,
                            effective.binding_method,
                            effective.confidence,
                            effective.binding_note,
                            changed,
                            run,
                            namespace,
                            source,
                            item.catalog,
                            item.schema,
                            item.table,
                            item.column,
                        )
                    )

            # Insert first so the foreign key to the run is satisfied in one pass.
            tx.executemany(
                "INSERT INTO platform.dictionary_column "
                "(namespace_id, source_id, catalog_name, schema_name, table_name, column_name, "
                "data_type, is_nullable, comment, source_kind, property_iri, binding_method, "
                "confidence, binding_note, last_refresh_run_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                to_insert,
            )
            tx.executemany(
                "UPDATE platform.dictionary_column SET "
                "data_type = %s, is_nullable = %s, comment = %s, source_kind = %s, "
                "property_iri = %s, binding_method = %s, confidence = %s, binding_note = %s, "
                "observed_at = CASE WHEN %s THEN now() ELSE observed_at END, "
                "last_refresh_run_id = %s "
                "WHERE namespace_id = %s AND source_id = %s AND catalog_name = %s "
                "AND schema_name = %s AND table_name = %s AND column_name = %s",
                to_update,
            )
        return {
            "processed": len(normalized),
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "removed": 0,
        }

    def finish_refresh(
        self,
        run_id: str,
        *,
        status: str,
        processed: int = 0,
        inserted: int = 0,
        updated: int = 0,
        unchanged: int = 0,
        removed: int = 0,
        error: str | None = None,
    ) -> dict[str, Any]:
        run = _required_text(run_id, "runId")
        if status not in ("succeeded", "failed"):
            raise _invalid("status", "status must be 'succeeded' or 'failed'")
        counts = {
            "processed": processed,
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "removed": removed,
        }
        for field, value in counts.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise _invalid(field, f"{field} must be a non-negative integer")
        message = _optional_text(error, "error")
        if status == "failed" and not message:
            raise _invalid("error", "a failed refresh must record a non-empty error")
        if status == "succeeded" and message:
            raise _invalid("error", "a succeeded refresh must not carry an error")

        with self._metadata.tx() as tx:
            rows = tx.execute_returning(
                "UPDATE platform.dictionary_refresh_run SET "
                "status = %s, finished_at = now(), processed = %s, inserted = %s, "
                "updated = %s, unchanged = %s, removed = %s, error = %s "
                "WHERE run_id = %s AND status = 'running' "
                f"RETURNING {_RUN_COLUMNS}",
                (
                    status,
                    processed,
                    inserted,
                    updated,
                    unchanged,
                    removed,
                    message,
                    run,
                ),
            )
            if rows:
                return _run_out(rows[0])
            previous = tx.query(
                "SELECT status FROM platform.dictionary_refresh_run WHERE run_id = %s", (run,)
            )
        if not previous:
            raise _not_found(f"refresh run {run} does not exist", "E_REFRESH_RUN_MISSING")
        raise _conflict(
            f"refresh run {run} is already {previous[0]['status']}",
            "E_REFRESH_NOT_RUNNING",
            {"runId": run, "status": previous[0]["status"]},
        )

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = _required_text(run_id, "runId")
        rows = self._metadata.query(
            f"SELECT {_RUN_COLUMNS} FROM platform.dictionary_refresh_run WHERE run_id = %s",
            (run,),
        )
        if not rows:
            raise _not_found(f"refresh run {run} does not exist", "E_REFRESH_RUN_MISSING")
        return _run_out(rows[0])

    def latest_run(self, namespace_id: str, source_id: str) -> dict[str, Any] | None:
        namespace = _required_text(namespace_id, "namespaceId")
        source = _required_text(source_id, "sourceId")
        rows = self._metadata.query(
            f"SELECT {_RUN_COLUMNS} FROM platform.dictionary_refresh_run "
            "WHERE namespace_id = %s AND source_id = %s "
            "ORDER BY started_at DESC, run_id DESC LIMIT 1",
            (namespace, source),
        )
        return _run_out(rows[0]) if rows else None

    # -------------------------------------------------------------------- reads

    def list_columns(
        self,
        namespace_id: str,
        *,
        table: str | None = None,
        column: str | None = None,
        source_id: str | None = None,
        source_kind: str | None = None,
        binding_method: str | None = None,
        q: str | None = None,
        view: str = "all",
        mappable_pairs: Sequence[tuple[str, str]] | None = None,
        limit: int = _PAGE_DEFAULT,
        offset: int = 0,
    ) -> dict[str, Any]:
        namespace = _required_text(namespace_id, "namespaceId")
        if view not in LIST_VIEWS:
            raise _invalid("view", f"unsupported view {view!r}; expected one of {sorted(LIST_VIEWS)}")
        page_size = _page_size(limit)
        page_offset = _page_offset(offset)

        where = ["namespace_id = %s"]
        params: list[Any] = [namespace]
        if table:
            where.append("table_name = %s")
            params.append(_required_text(table, "table"))
        if column:
            where.append("column_name = %s")
            params.append(_required_text(column, "column"))
        if source_id:
            where.append("source_id = %s")
            params.append(_required_text(source_id, "sourceId"))
        if source_kind:
            kind = _required_text(source_kind, "sourceKind")
            if kind not in SOURCE_KINDS:
                raise _invalid("sourceKind", f"unsupported sourceKind {kind!r}")
            where.append("source_kind = %s")
            params.append(kind)
        if binding_method:
            method = _required_text(binding_method, "bindingMethod")
            if method not in BINDING_METHODS:
                raise _invalid("bindingMethod", f"unsupported bindingMethod {method!r}")
            where.append("binding_method = %s")
            params.append(method)
        if q:
            pattern = f"%{_required_text(q, 'q')}%"
            where.append(
                "(table_name ILIKE %s OR column_name ILIKE %s OR COALESCE(comment, '') ILIKE %s)"
            )
            params.extend([pattern, pattern, pattern])
        if view == "missing_comment":
            where.append("(comment IS NULL OR btrim(comment) = '')")
        elif view == "unbound":
            where.append("binding_method = 'none'")
        elif view == "mappable_unbound":
            pairs = list(mappable_pairs or [])
            if not pairs:
                raise _invalid(
                    "mappablePairs",
                    "view=mappable_unbound requires the caller's mappable table/column pairs",
                    "E_MAPPABLE_PAIRS_REQUIRED",
                )
            where.append("binding_method = 'none'")
            ors: list[str] = []
            for pair in pairs:
                if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                    raise _invalid(
                        "mappablePairs",
                        "each mappable pair must be a (table, column) pair",
                    )
                ors.append("(table_name = %s AND column_name = %s)")
                params.extend(
                    [
                        _required_text(pair[0], "mappablePairs.table"),
                        _required_text(pair[1], "mappablePairs.column"),
                    ]
                )
            where.append("(" + " OR ".join(ors) + ")")

        clause = " AND ".join(where)
        total_rows = self._metadata.query(
            f"SELECT COUNT(*) AS total FROM platform.dictionary_column WHERE {clause}",
            tuple(params),
        )
        rows = self._metadata.query(
            f"SELECT {_COLUMN_COLUMNS} FROM platform.dictionary_column WHERE {clause} "
            "ORDER BY table_name, column_name, source_id, schema_name, catalog_name "
            "LIMIT %s OFFSET %s",
            tuple(params) + (page_size, page_offset),
        )
        return {
            "items": [_column_out(row) for row in rows],
            "total": int(total_rows[0]["total"]) if total_rows else 0,
            "limit": page_size,
            "offset": page_offset,
        }

    def table_columns(
        self,
        namespace_id: str,
        *,
        table: str,
        source_id: str | None = None,
        catalog: str | None = None,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        """Ten-column view for one table (F63). No limit: tables are bounded."""
        namespace = _required_text(namespace_id, "namespaceId")
        where = ["namespace_id = %s", "table_name = %s"]
        params: list[Any] = [namespace, _required_text(table, "table")]
        if source_id:
            where.append("source_id = %s")
            params.append(_required_text(source_id, "sourceId"))
        if catalog:
            where.append("catalog_name = %s")
            params.append(_required_text(catalog, "catalog"))
        if schema:
            where.append("schema_name = %s")
            params.append(_required_text(schema, "schema"))
        rows = self._metadata.query(
            f"SELECT {_COLUMN_COLUMNS} FROM platform.dictionary_column "
            f"WHERE {' AND '.join(where)} "
            "ORDER BY column_name, source_id",
            tuple(params),
        )
        return [_column_out(row) for row in rows]

    def comment_coverage(
        self,
        namespace_id: str,
        *,
        source_id: str | None = None,
        catalog: str | None = None,
        schema: str | None = None,
        table: str | None = None,
    ) -> dict[str, Any]:
        """Comment coverage (F66). ``ratio`` is None when there is no row."""
        namespace = _required_text(namespace_id, "namespaceId")
        where = ["namespace_id = %s"]
        params: list[Any] = [namespace]
        if source_id:
            where.append("source_id = %s")
            params.append(_required_text(source_id, "sourceId"))
        if catalog:
            where.append("catalog_name = %s")
            params.append(_required_text(catalog, "catalog"))
        if schema:
            where.append("schema_name = %s")
            params.append(_required_text(schema, "schema"))
        if table:
            where.append("table_name = %s")
            params.append(_required_text(table, "table"))
        clause = " AND ".join(where)
        rows = self._metadata.query(
            "SELECT source_id, table_name, "
            "COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE comment IS NOT NULL AND btrim(comment) <> '') AS commented, "
            "COUNT(*) FILTER (WHERE comment IS NULL OR btrim(comment) = '') AS missing "
            f"FROM platform.dictionary_column WHERE {clause} "
            "GROUP BY source_id, table_name ORDER BY table_name, source_id",
            tuple(params),
        )
        tables = [
            {
                "sourceId": row["source_id"],
                "table": row["table_name"],
                "total": int(row["total"]),
                "commented": int(row["commented"]),
                "missing": int(row["missing"]),
                "ratio": _ratio(int(row["commented"]), int(row["total"])),
            }
            for row in rows
        ]
        total = sum(item["total"] for item in tables)
        commented = sum(item["commented"] for item in tables)
        return {
            "total": total,
            "commented": commented,
            "missing": total - commented,
            "ratio": _ratio(commented, total),
            "tables": tables,
        }


def _new_run_id() -> str:
    import uuid

    return uuid.uuid4().hex


def _keep_manual(item: _NormalizedColumn, previous: Mapping[str, Any]) -> _NormalizedColumn:
    return _NormalizedColumn(
        catalog=item.catalog,
        schema=item.schema,
        table=item.table,
        column=item.column,
        data_type=item.data_type,
        is_nullable=item.is_nullable,
        source_kind=item.source_kind,
        comment=item.comment,
        property_iri=previous["property_iri"],
        binding_method="manual",
        confidence=previous["confidence"],
        binding_note=previous["binding_note"],
    )


def _business_changed(item: _NormalizedColumn, previous: Mapping[str, Any]) -> bool:
    previous_confidence = previous["confidence"]
    return item.business() != (
        previous["data_type"],
        previous["is_nullable"],
        previous["comment"],
        previous["source_kind"],
        previous["property_iri"],
        previous["binding_method"],
        previous_confidence,
        previous["binding_note"],
    )


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _page_size(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise _invalid("limit", "limit must be an integer")
    if limit < 1 or limit > _PAGE_MAX:
        raise _invalid("limit", f"limit must be within [1, {_PAGE_MAX}]")
    return limit


def _page_offset(offset: int) -> int:
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise _invalid("offset", "offset must be a non-negative integer")
    return offset


__all__ = [
    "BINDING_METHODS",
    "SOURCE_KINDS",
    "DictionaryColumnInput",
    "DictionaryError",
    "DictionaryPg",
]
