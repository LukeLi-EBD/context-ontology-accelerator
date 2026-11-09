"""B-01 value-level provenance: stable ``source_ref`` builders, registry, resolver.

A ``source_ref`` is a compact, self-describing URI that points at the *natural
key* of a value's source row, never at a surrogate id and never at a content
hash. Natural keys survive the two events that invalidate surrogate ids:

* recomputation  -- the observation table upserts on
  ``(metric_id, definition_version, entity_key, window_start, window_end)``, so
  a recomputed value lands on the same row;
* version switch -- ``definition_version`` is part of that key, so a ref issued
  against v7 keeps resolving to the v7 row after the definition is promoted.

Three ref kinds are supported, matching the three value sources in the
platform:

======  ============================================  ==================
kind    canonical form                                live target
======  ============================================  ==================
obs     ``src://obs/<metric>@<version>?entity=..``    metric_observation
obs-set ``src://obs-set/<metric>@<version>?..``       metric_observation
fact    ``src://fact/<table>?<key columns>``          fact table row
doc     ``src://doc/<document_id>#c<seq>``            document_chunk
computation ``src://computation/<id>``                source_ref_registry
======  ============================================  ==================

A ``computation`` ref is different on purpose: it points at an *audit record*
(a computation event -- metric, window, data source, caller, time), not at a
live value row. It is the traceability carrier for the value endpoints and is
deliberately kept out of the PROV decision chain, which only records rulings.

``platform.source_ref_registry`` records every ref that an API response handed
out. The registry is audit storage, not the source of truth: resolution always
re-reads the live table. That split is what separates "never existed"
(``E_SOURCE_REF_NOT_FOUND``) from "was issued, target now gone"
(``E_SOURCE_REF_STALE``).
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse

from .errors import PortError

log = logging.getLogger(__name__)

MALFORMED = "E_SOURCE_REF_MALFORMED"
TYPE_UNSUPPORTED = "E_SOURCE_REF_TYPE_UNSUPPORTED"
NOT_FOUND = "E_SOURCE_REF_NOT_FOUND"
STALE = "E_SOURCE_REF_STALE"
FORBIDDEN = "E_SOURCE_REF_FORBIDDEN"

REF_SCHEME = "src"
OBSERVATION_SET = "metric_observation_set"
OBSERVATION_ROW = "metric_observation_row"
FACT_ROW = "fact_row"
DOCUMENT_CHUNK = "document_chunk"
METRIC_COMPUTATION = "metric_computation"

_TABLE_RE = re.compile(r"^platform\.[a-z0-9_]+$")
_COL_RE = re.compile(r"^[a-z0-9_]+$")
_METRIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_DOC_RE = re.compile(r"^[0-9a-f]{8,128}$")
_COMPUTATION_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_CHUNK_FRAGMENT_RE = re.compile(r"^c(\d+)$")
_CHUNK_SUFFIX_RE = re.compile(r":(\d+)$")

SAMPLE_LIMIT = 3


def _err(code: str, message: str, **details: Any) -> PortError:
    return PortError(
        code="PermissionDenied" if code == FORBIDDEN else "InvalidArgument",
        message=message,
        provider="platform",
        provider_code=code,
        details=details,
    )


def _canonical_query(values: dict[str, Any]) -> str:
    def norm(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    pairs = [(key, norm(value)) for key, value in values.items() if value is not None]
    return urlencode(sorted(pairs), quote_via=quote)


def _set_locator(
    metric_id: str,
    definition_version: str,
    *,
    as_of: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    entity_key: str | None = None,
    institution: str | None = None,
    fixture: bool | None = None,
) -> dict[str, Any]:
    locator: dict[str, Any] = {
        "metricId": metric_id,
        "definitionVersion": definition_version,
    }
    if as_of:
        locator["asOf"] = as_of
    if period_start or period_end:
        locator["periodStart"] = period_start
        locator["periodEnd"] = period_end
    if entity_key:
        locator["entityKey"] = entity_key
    if institution:
        locator["institution"] = institution
    if fixture is not None:
        locator["fixture"] = bool(fixture)
    return locator


def _set_query(locator: dict[str, Any]) -> str:
    """Query part for an obs-set ref; the metric/version already live in the path."""
    return _canonical_query(
        {key: value for key, value in locator.items()
         if key not in ("metricId", "definitionVersion")}
    )


def observation_set_ref(
    metric_id: str,
    definition_version: str,
    *,
    as_of: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    entity_key: str | None = None,
    institution: str | None = None,
    fixture: bool | None = None,
) -> str:
    """Ref for an aggregated metric value: the observation filter that produced it."""
    locator = _set_locator(
        metric_id, definition_version,
        as_of=as_of, period_start=period_start, period_end=period_end,
        entity_key=entity_key, institution=institution, fixture=fixture,
    )
    return f"{REF_SCHEME}://obs-set/{metric_id}@{definition_version}?{_set_query(locator)}"


def observation_ref(
    metric_id: str,
    definition_version: str,
    entity_key: str,
    window_start: str,
    window_end: str,
) -> str:
    """Ref for one observation row, keyed by its unique natural key."""
    query = _canonical_query(
        {"entity": entity_key, "we": window_end, "ws": window_start}
    )
    return f"{REF_SCHEME}://obs/{metric_id}@{definition_version}?{query}"


def fact_row_ref(table: str, key: dict[str, Any]) -> str:
    """Ref for one fact-table row: table + the columns that make it unique."""
    return f"{REF_SCHEME}://fact/{table}?{_canonical_query(key)}"


def chunk_ref(document_id: str, chunk_no: int) -> str:
    """Ref for one document chunk: document id + 0-based chunk ordinal."""
    return f"{REF_SCHEME}://doc/{document_id}#c{int(chunk_no)}"


def computation_ref(computation_id: str) -> str:
    """Ref for one computation event; the registry row is the record itself."""
    return f"{REF_SCHEME}://computation/{computation_id}"


def computation_descriptor(computation_id: str, locator: dict[str, Any]) -> dict[str, Any]:
    return _descriptor(
        METRIC_COMPUTATION, computation_ref(computation_id),
        "platform.source_ref_registry", locator,
    )


def register_computation(metadata: Any, locator: dict[str, Any]) -> dict[str, Any]:
    """Record one computation event and return its ``computation`` ref descriptor.

    Computations are not rulings, so they do not go to the PROV decision chain;
    this registry row is the audit record: definition version, window, source,
    caller and time all live in its locator.
    """
    descriptor = computation_descriptor(uuid.uuid4().hex, locator)
    register_ref(metadata, descriptor)
    return descriptor


def _resolve_url(ref: str) -> str:
    return "/source/resolve?ref=" + quote(ref, safe="")


def _descriptor(
    ref_type: str, ref: str, target_table: str, locator: dict[str, Any]
) -> dict[str, Any]:
    """Minimal fields a provenance badge needs: kind, target, locator, click URL."""
    return {
        "type": ref_type,
        "ref": ref,
        "targetTable": target_table,
        "locator": locator,
        "resolveUrl": _resolve_url(ref),
    }


def observation_set_descriptor(
    metric_id: str,
    definition_version: str,
    *,
    as_of: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    entity_key: str | None = None,
    institution: str | None = None,
    fixture: bool | None = None,
    row_count: int | None = None,
) -> dict[str, Any]:
    locator = _set_locator(
        metric_id, definition_version,
        as_of=as_of, period_start=period_start, period_end=period_end,
        entity_key=entity_key, institution=institution, fixture=fixture,
    )
    desc = _descriptor(
        OBSERVATION_SET,
        observation_set_ref(
            metric_id, definition_version,
            as_of=as_of, period_start=period_start, period_end=period_end,
            entity_key=entity_key, institution=institution, fixture=fixture,
        ),
        "platform.metric_observation",
        locator,
    )
    if row_count is not None:
        desc["rowCount"] = int(row_count)
    return desc


def observation_row_descriptor(row: dict[str, Any]) -> dict[str, Any]:
    ref = observation_ref(
        str(row["metric_id"]), str(row["definition_version"]),
        str(row["entity_key"]),
        str(row.get("window_start") or ""),
        str(row.get("window_end") or ""),
    )
    return _descriptor(
        OBSERVATION_ROW, ref, "platform.metric_observation",
        {
            "metricId": str(row["metric_id"]),
            "definitionVersion": str(row["definition_version"]),
            "entityKey": str(row["entity_key"]),
            "windowStart": str(row.get("window_start") or ""),
            "windowEnd": str(row.get("window_end") or ""),
        },
    )


def fact_row_descriptor(table: str, key: dict[str, Any], row: dict[str, Any] | None = None) -> dict[str, Any]:
    desc = _descriptor(
        FACT_ROW, fact_row_ref(table, key), table,
        {"table": table, "key": {k: str(v) for k, v in key.items()}},
    )
    if row is not None:
        desc["row"] = _jsonable(row)
    return desc


def chunk_descriptor(
    document_id: str, chunk_no: int, chunk_id: str | None = None
) -> dict[str, Any]:
    locator = {"documentId": document_id, "chunkNo": int(chunk_no)}
    if chunk_id:
        locator["chunkId"] = chunk_id
    return _descriptor(
        DOCUMENT_CHUNK, chunk_ref(document_id, chunk_no),
        "platform.document_chunk", locator,
    )


def chunk_no_from_id(chunk_id: str | None) -> int | None:
    """``<document_id>:0000`` -> 0. Returns None when the id has no ordinal."""
    if not chunk_id:
        return None
    match = _CHUNK_SUFFIX_RE.search(str(chunk_id))
    return int(match.group(1)) if match else None


# ---------------------------------------------------------------- registry


def register_ref(metadata: Any, descriptor: dict[str, Any]) -> bool:
    """Remember that this ref was emitted. Best effort: never fails a response."""
    ref = descriptor.get("ref")
    if not ref:
        return False
    try:
        metadata.execute(
            """
            INSERT INTO platform.source_ref_registry
              (source_ref, ref_kind, target_table, locator)
            VALUES (%s, %s, %s, %s::jsonb)
            ON CONFLICT (source_ref) DO NOTHING
            """,
            (
                ref,
                descriptor.get("type"),
                descriptor.get("targetTable"),
                json.dumps(descriptor.get("locator") or {}, ensure_ascii=False, default=str),
            ),
        )
        return True
    except Exception as exc:  # noqa: BLE001 - provenance must not break the answer
        log.warning("source_ref registry unavailable: %s", exc)
        return False


# ------------------------------------------------------------------ parse


def parse_ref(ref: str) -> dict[str, Any]:
    parsed = urlparse(ref or "")
    if parsed.scheme != REF_SCHEME:
        raise _err(MALFORMED, "source_ref must use the src:// scheme", ref=ref)
    kind = parsed.netloc
    if kind not in ("obs", "obs-set", "fact", "doc", "computation"):
        raise _err(TYPE_UNSUPPORTED, f"unsupported source_ref kind: {kind}", ref=ref)
    query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
    if kind == "computation":
        computation_id = unquote(parsed.path.lstrip("/"))
        if not _COMPUTATION_RE.match(computation_id):
            raise _err(MALFORMED, "invalid computation id in ref", ref=ref)
        return {"kind": kind, "computationId": computation_id,
                "locator": {"computationId": computation_id}}
    if kind in ("obs", "obs-set"):
        target = unquote(parsed.path.lstrip("/"))
        if "@" not in target:
            raise _err(MALFORMED, "observation ref must be <metric>@<version>", ref=ref)
        metric_id, version = target.rsplit("@", 1)
        if not _METRIC_RE.match(metric_id) or not _METRIC_RE.match(version):
            raise _err(MALFORMED, "invalid metric or version in observation ref", ref=ref)
        locator: dict[str, Any] = {
            "metricId": metric_id, "definitionVersion": version,
        }
        if kind == "obs":
            locator.update({
                "entityKey": query.get("entity"),
                "windowStart": query.get("ws"),
                "windowEnd": query.get("we"),
            })
        else:
            for source_key, target_key in (
                ("asOf", "asOf"), ("periodStart", "periodStart"),
                ("periodEnd", "periodEnd"), ("entityKey", "entityKey"),
                ("institution", "institution"),
            ):
                if query.get(source_key) is not None:
                    locator[target_key] = query[source_key]
            if query.get("fixture") in ("true", "false"):
                locator["fixture"] = query["fixture"] == "true"
        return {"kind": kind, "metricId": metric_id,
                "definitionVersion": version, "query": query, "locator": locator}
    if kind == "fact":
        table = unquote(parsed.path.lstrip("/"))
        if not _TABLE_RE.match(table):
            raise _err(FORBIDDEN, "fact ref must name a platform fact table", ref=ref,
                       table=table)
        if not query:
            raise _err(MALFORMED, "fact ref needs its unique key columns", ref=ref)
        for column in query:
            if not _COL_RE.match(column):
                raise _err(MALFORMED, f"invalid key column {column!r}", ref=ref)
        return {"kind": kind, "table": table, "key": query,
                "locator": {"table": table, "key": query}}
    document_id = unquote(parsed.path.lstrip("/"))
    if not _DOC_RE.match(document_id):
        raise _err(MALFORMED, "invalid document id in chunk ref", ref=ref)
    match = _CHUNK_FRAGMENT_RE.match(parsed.fragment or "")
    if not match:
        raise _err(MALFORMED, "chunk ref must end with #c<ordinal>", ref=ref)
    return {
        "kind": kind, "documentId": document_id, "chunkNo": int(match.group(1)),
        "locator": {"documentId": document_id, "chunkNo": int(match.group(1))},
    }


# ----------------------------------------------------------------- resolve


def _table_columns(metadata: Any, table: str) -> set[str] | None:
    rows = metadata.query(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'platform' AND table_name = %s",
        (table.split(".", 1)[1],),
    )
    return {str(row["column_name"]) for row in rows} if rows else None


def _fact_key_columns(metadata: Any, table: str) -> list[str] | None:
    rows = metadata.query(
        "SELECT key_columns FROM platform.fact_source_key WHERE table_name = %s",
        (table,),
    )
    if not rows:
        return None
    return [str(item) for item in (rows[0]["key_columns"] or [])]


def _jsonable(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            out[key] = float(value)
        elif hasattr(value, "isoformat"):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


def jsonable(row: dict[str, Any]) -> dict[str, Any]:
    """Public conversion for API rows (Decimal/date -> JSON scalars)."""
    return _jsonable(row)


def _registry_row(metadata: Any, ref: str) -> dict[str, Any] | None:
    try:
        rows = metadata.query(
            "SELECT source_ref, ref_kind, target_table, locator, issued_at, resolve_count "
            "FROM platform.source_ref_registry WHERE source_ref = %s",
            (ref,),
        )
    except Exception:  # noqa: BLE001 - older schema without the registry
        return None
    return rows[0] if rows else None


def _resolve_computation(metadata: Any, parsed: dict[str, Any], ref: str) -> dict[str, Any]:
    """A computation ref resolves to its own audit record, not to a value row."""
    row = _registry_row(metadata, ref)
    if not row:
        return {"rows": [], "rowCount": 0}
    return {
        "rows": [{
            "ref": row["source_ref"],
            "refKind": row["ref_kind"],
            "targetTable": row["target_table"],
            "locator": row.get("locator") or {},
            "issuedAt": _jsonable({"issued_at": row["issued_at"]})["issued_at"],
            "resolveCount": row.get("resolve_count"),
        }],
        "rowCount": 1,
    }


def _resolve_observation(metadata: Any, parsed: dict[str, Any], ref: str) -> dict[str, Any]:
    query = parsed["query"]
    missing = [name for name in ("entity", "ws", "we") if not query.get(name)]
    if missing:
        raise _err(MALFORMED, "observation ref is missing its natural key", ref=ref,
                   missing=missing)
    rows = metadata.query(
        """
        SELECT observation_id, metric_id, definition_version, institution, product,
               entity_key, as_of, period_start, period_end, numerator, denominator,
               window_start, window_end, data_source, fixture, computed_at
          FROM platform.metric_observation
         WHERE metric_id = %s AND definition_version = %s
           AND entity_key = %s AND window_start = %s AND window_end = %s
        """,
        (
            parsed["metricId"], parsed["definitionVersion"],
            query["entity"], query["ws"], query["we"],
        ),
    )
    return {"rows": [_jsonable(row) for row in rows], "rowCount": len(rows)}


def _resolve_observation_set(metadata: Any, parsed: dict[str, Any], ref: str) -> dict[str, Any]:
    query = parsed["query"]
    clauses = ["metric_id = %s", "definition_version = %s"]
    params: list[Any] = [parsed["metricId"], parsed["definitionVersion"]]
    if query.get("asOf"):
        clauses.append("as_of = %s")
        params.append(query["asOf"])
    elif query.get("periodStart") or query.get("periodEnd"):
        if not (query.get("periodStart") and query.get("periodEnd")):
            raise _err(MALFORMED, "period ref needs both periodStart and periodEnd", ref=ref)
        clauses.append("window_start >= %s AND window_end <= %s")
        params.extend([query["periodStart"], query["periodEnd"]])
    else:
        raise _err(MALFORMED, "observation-set ref has no asOf/period window", ref=ref)
    if query.get("entityKey"):
        clauses.append("entity_key = %s")
        params.append(query["entityKey"])
    if query.get("institution"):
        clauses.append("institution = %s")
        params.append(query["institution"])
    if query.get("fixture") in ("true", "false"):
        clauses.append("fixture = %s")
        params.append(query["fixture"] == "true")
    where = " AND ".join(clauses)
    stats = metadata.query(
        f"SELECT COUNT(*) AS n FROM platform.metric_observation WHERE {where}",
        tuple(params),
    )
    rows = metadata.query(
        "SELECT observation_id, metric_id, definition_version, entity_key, as_of, "
        "window_start, window_end, numerator, denominator, data_source, fixture, computed_at "
        f"FROM platform.metric_observation WHERE {where} "
        "ORDER BY window_start, entity_key LIMIT %s",
        tuple(params + [SAMPLE_LIMIT]),
    )
    return {
        "rows": [_jsonable(row) for row in rows],
        "rowCount": int(stats[0]["n"]) if stats else 0,
    }


def _resolve_fact(metadata: Any, parsed: dict[str, Any], ref: str) -> dict[str, Any]:
    table = parsed["table"]
    key_columns = _fact_key_columns(metadata, table)
    if key_columns is None:
        raise _err(FORBIDDEN, "table is not a registered fact source", ref=ref, table=table)
    given = sorted(parsed["key"])
    if given != sorted(key_columns):
        raise _err(MALFORMED, "fact ref key does not match the registered natural key",
                   ref=ref, table=table, expected=sorted(key_columns), given=given)
    columns = _table_columns(metadata, table)
    if columns is None:
        raise _err(STALE, "fact table no longer exists", ref=ref, table=table)
    missing = [name for name in key_columns if name not in columns]
    if missing:
        raise _err(STALE, "fact table lost key columns", ref=ref, table=table, missing=missing)
    where = " AND ".join(f"{name} = %s" for name in key_columns)
    rows = metadata.query(
        f"SELECT * FROM {table} WHERE {where} LIMIT 1",
        tuple(parsed["key"][name] for name in key_columns),
    )
    return {"rows": [_jsonable(row) for row in rows], "rowCount": len(rows)}


def _resolve_chunk(metadata: Any, parsed: dict[str, Any], ref: str) -> dict[str, Any]:
    rows = metadata.query(
        """
        SELECT chunk_id, document_id, seq, page_from, page_to, char_start, char_end,
               left(text, 200) AS text_preview, created_at
          FROM platform.document_chunk
         WHERE document_id = %s AND seq = %s
        """,
        (parsed["documentId"], parsed["chunkNo"]),
    )
    return {"rows": [_jsonable(row) for row in rows], "rowCount": len(rows)}


def resolve(metadata: Any, ref: str) -> dict[str, Any]:
    """Resolve a ref against the live tables, using the registry to spot staleness."""
    parsed = parse_ref(ref)
    registered = _registry_row(metadata, ref)
    if parsed["kind"] == "obs":
        live = _resolve_observation(metadata, parsed, ref)
    elif parsed["kind"] == "obs-set":
        live = _resolve_observation_set(metadata, parsed, ref)
    elif parsed["kind"] == "fact":
        live = _resolve_fact(metadata, parsed, ref)
    elif parsed["kind"] == "computation":
        live = _resolve_computation(metadata, parsed, ref)
    else:
        live = _resolve_chunk(metadata, parsed, ref)

    if live["rowCount"] == 0:
        if registered:
            raise _err(
                STALE,
                "ref was issued but its source row is gone",
                ref=ref,
                issuedAt=_jsonable({"issued_at": registered["issued_at"]})["issued_at"],
                targetTable=registered.get("target_table"),
            )
        raise _err(NOT_FOUND, "source_ref does not resolve", ref=ref)

    if parsed["kind"] == "obs":
        ref_type, target_table = OBSERVATION_ROW, "platform.metric_observation"
    elif parsed["kind"] == "obs-set":
        ref_type, target_table = OBSERVATION_SET, "platform.metric_observation"
    elif parsed["kind"] == "fact":
        ref_type, target_table = FACT_ROW, parsed["table"]
    elif parsed["kind"] == "computation":
        ref_type, target_table = METRIC_COMPUTATION, "platform.source_ref_registry"
    else:
        ref_type, target_table = DOCUMENT_CHUNK, "platform.document_chunk"
    descriptor = _descriptor(
        ref_type, ref, target_table, parsed["locator"],
    )
    payload = {
        **descriptor,
        "found": True,
        "issued": bool(registered),
        "issuedAt": (
            _jsonable({"issued_at": registered["issued_at"]})["issued_at"]
            if registered else None
        ),
        "state": "live",
        **live,
    }
    if not registered:
        register_ref(metadata, descriptor)
    return payload


def metric_source_payload(
    metadata: Any,
    *,
    metric_id: str,
    definition_version: str,
    as_of: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    entity_key: str | None = None,
    institution: str | None = None,
    fixture: bool | None = None,
    row_count: int | None = None,
) -> dict[str, Any]:
    """Register + return the set ref and up to 3 row refs for a computed value."""
    descriptor = observation_set_descriptor(
        metric_id, definition_version,
        as_of=as_of, period_start=period_start, period_end=period_end,
        entity_key=entity_key, institution=institution, fixture=fixture,
        row_count=row_count,
    )
    register_ref(metadata, descriptor)
    clauses = ["metric_id = %s", "definition_version = %s"]
    params: list[Any] = [metric_id, definition_version]
    if as_of:
        clauses.append("as_of = %s")
        params.append(as_of)
    elif period_start and period_end:
        clauses.append("window_start >= %s AND window_end <= %s")
        params.extend([period_start, period_end])
    if entity_key:
        clauses.append("entity_key = %s")
        params.append(entity_key)
    if institution:
        clauses.append("institution = %s")
        params.append(institution)
    if fixture is not None:
        clauses.append("fixture = %s")
        params.append(bool(fixture))
    rows = metadata.query(
        "SELECT metric_id, definition_version, entity_key, window_start, window_end "
        f"FROM platform.metric_observation WHERE {' AND '.join(clauses)} "
        "ORDER BY entity_key LIMIT %s",
        tuple(params + [SAMPLE_LIMIT]),
    )
    refs = [observation_row_descriptor(row) for row in rows]
    for item in refs:
        register_ref(metadata, item)
    return {"sourceRef": descriptor, "sourceRefs": refs}
