"""HTTP surface: health/readiness/status + S2 document ingest.

No auth, no metrics, no queue. Errors are mapped from PortError to stable HTTP
codes so clients see provider codes instead of stack traces.
"""

from __future__ import annotations

import json
import re
import shutil
import time
import uuid
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, File, Form, Query, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from . import __version__
from . import entity_view
from . import healthboard
from .adapters.ontology_pg import (
    build_import_document,
    get_import_record,
    import_format_from_name,
    parse_import_document,
    persist_import,
    publish_import,
)
from .answerable import PUNCT as _ANSWER_PUNCT
from .answerable import STOPWORDS as _ANSWER_STOPWORDS
from .assembly import Runtime
from .bootstrap import CheckResult
from . import catalog as catalog_module
from .errors import PortError
from . import webui
from . import prov as prov_module
from . import source_ref

WEB_DIR = Path(__file__).resolve().parents[2] / "web"

_HTTP_STATUS = {
    "InvalidArgument": 400,
    "NotFound": 404,
    "Conflict": 409,
    "PreconditionFailed": 412,
    "Unsupported": 400,
    "PermissionDenied": 403,
    "PolicyRejected": 422,
    "ResourceExhausted": 413,
    "DeadlineExceeded": 504,
    "Unavailable": 503,
    "Aborted": 409,
    "Internal": 500,
    "DataLoss": 500,
}

# ---- read-only browse helpers -------------------------------------------

_BROWSE_IRI = re.compile(r"^[^<>\"{}|^`\\\s]+$")
_OWL = "http://www.w3.org/2002/07/owl#"
_RDFS = "http://www.w3.org/2000/01/rdf-schema#"
_RDFS_LABEL = _RDFS + "label"
_SKOS = "http://www.w3.org/2004/02/skos/core#"
_TERM = "https://w3id.org/fsldm/terms#"
_READ_ONLY_QUERY = re.compile(
    r"(?is)^(?:prefix\s+[^:\s]+:\s*<[^>]*>\s*|base\s*<[^>]*>\s*)*"
    r"(select|ask)\b"
)


def _browse_error(code: str, message: str, details: dict[str, Any] | None = None) -> PortError:
    return PortError(
        code="InvalidArgument",
        message=message,
        provider="platform",
        provider_code=code,
        details=details or {},
    )


def _require_iri(value: str | None, field: str) -> str:
    if not value:
        raise _browse_error("E_BROWSE_IRI_REQUIRED", f"{field} is required", {"field": field})
    if not _BROWSE_IRI.match(value) or not value.startswith(("http://", "https://", "urn:")):
        raise _browse_error(
            "E_BROWSE_BAD_IRI",
            f"{field} is not a safe absolute IRI",
            {"field": field, "value": value},
        )
    return value


def _binding(binding: dict[str, Any], name: str) -> str | None:
    term = (binding.get("values") or {}).get(name)
    if not isinstance(term, dict):
        return None
    kind = term.get("kind")
    if kind == "iri":
        return term.get("iri")
    if kind == "bnode":
        return term.get("label")
    return term.get("value")


def _local_name(iri: str | None) -> str | None:
    if not iri:
        return None
    for sep in ("#", "/"):
        if sep in iri:
            return iri.rsplit(sep, 1)[-1]
    return iri


def _current_graph(runtime: Runtime) -> str | None:
    pointer = runtime.ontology.current()
    return pointer.get("graph") if pointer else None


def _metric_json(row: dict[str, Any], detail: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "metricId": row["metric_id"],
        "nameZh": row["name_zh"],
        "domain": row["domain"],
        "evidenceBasis": row["evidence_basis"],
        "publishable": row["publishable"],
        "inference": row["inference"],
        "formulaDisabled": row["formula_disabled"],
        "missing": row["missing"],
        "definitionStatus": row["evidence_status"],
        "note": row["note"],
        "definitionVersion": row["definition_version"],
        "unit": row["unit"],
        "effectiveDate": (
            row["effective_date"].isoformat() if row.get("effective_date") else None
        ),
        "variantOf": row.get("variant_of"),
        "outputMode": row.get("output_mode"),
    }
    if detail:
        payload.update(
            {
                "metricKind": row["metric_kind"],
                "formula": row["formula_expr"],
                "numeratorAgg": row["numerator_agg"],
                "denominator": row["denominator_agg"],
                "observationPeriod": {
                    "kind": row["window_kind"],
                    "minWindowDays": row["min_window_days"],
                },
                "grain": row["grain"],
                "displayName": row.get("display_name"),
                "definition": row.get("definition"),
                "formulaText": row.get("formula_text"),
                "denominatorText": row.get("denominator_text"),
                "observationPeriodText": row.get("observation_period"),
                "granularityText": row.get("granularity"),
                "provenanceLabel": row.get("provenance_label"),
                "ruleSet": row.get("rule_set_json"),
            }
        )
    return payload


# ---- layered coverage / citation QA helpers -----------------------------

_QA_DRIVABLE_KINDS = ("ratio", "duration", "sum")
_QA_NUMERIC_RE = re.compile(
    r"(是多少|多少|几个|几[天月年次]|计算|算一下|占比|比例|百分比|百分|率是|率有多|"
    r"数值|求值|统计|合计|总计|平均|最大|最小|趋势)"
)
_QA_DEFINITION_RE = re.compile(r"(口径|定义|公式|规则|怎么算|如何计算|是什么|含义|解释)")
_QA_METRIC_HINT_RE = re.compile(
    r"(指标|口径|率|占比|比例|余额|集中度|覆盖率|迁徙率|持续率|继续率|坏账|拨备|"
    r"逾期|分档|AUM|RFM|留存|流失)"
)
_QA_FACT_TABLE_RE = re.compile(r"^platform\.[a-z0-9_]+$")
_QA_OBS_SQL = (
    "SELECT metric_id, definition_version, count(*) AS n, "
    "bool_or(fixture) AS has_fixture, min(window_start) AS ws, max(window_end) AS we "
    "FROM platform.metric_observation GROUP BY metric_id, definition_version"
)
_QA_BINDING_SQL = (
    "SELECT metric_id, definition_version, role, fact_table, entity_column, "
    "value_expr, agg, window_column, window_mode FROM platform.metric_field_binding"
)
_QA_MAX_CANDIDATES = 6


def _qa_query(body: dict[str, Any], required: bool = True) -> str:
    for key in ("query", "q", "question", "metric", "metricId"):
        value = body.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if required:
        raise PortError(
            code="InvalidArgument",
            message="query must not be empty",
            provider="platform",
            provider_code="E_ANSWER_QUERY_EMPTY",
        )
    return ""


def _qa_metric_id(body: dict[str, Any]) -> str | None:
    value = body.get("metricId") or body.get("metric")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _qa_intent(query: str, metric_id: str | None, hint: str | None = None) -> str:
    if hint in ("value", "definition"):
        return hint
    if metric_id and not _QA_DEFINITION_RE.search(query):
        return "value"
    if _QA_NUMERIC_RE.search(query):
        return "value"
    return "definition"


def _qa_norm(text: Any) -> str:
    return re.sub(r"\s+", "", str(text or "").lower())


def _qa_graph_entries(runtime: Runtime, graph_iri: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sparql = (
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
        "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> "
        f"SELECT ?s ?p ?l FROM <{graph_iri}> WHERE {{ ?s ?p ?l . "
        "FILTER(?p IN (skos:prefLabel, skos:altLabel, rdfs:label)) }"
    )
    payload = runtime.graph.query(sparql)
    ontology: list[dict[str, Any]] = []
    terms: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for binding in payload.get("bindings", []):
        values = binding.get("values", {})
        subject = values.get("s")
        predicate = values.get("p")
        label = values.get("l")
        if not (subject and predicate and label):
            continue
        if subject.get("kind") != "iri" or label.get("kind") != "literal":
            continue
        iri = str(subject.get("iri") or "")
        pred = str(predicate.get("iri") or "")
        text = str(label.get("value") or "").strip()
        if not iri or not text:
            continue
        key = (pred, iri, text.lower())
        if key in seen:
            continue
        seen.add(key)
        entry = {"id": iri, "label": text, "predicate": pred}
        if pred == _RDFS_LABEL:
            ontology.append({**entry, "source": "rdfs:label"})
        elif pred in (_SKOS + "prefLabel", _SKOS + "altLabel"):
            terms.append({**entry, "source": "skos"})
    return ontology, terms


def _qa_metric_rows(runtime: Runtime) -> list[dict[str, Any]]:
    try:
        return list(runtime.metadata.query("SELECT * FROM platform.metric_definition ORDER BY metric_id"))
    except Exception:
        return []


def _qa_metric_candidates(
    query: str, rows: list[dict[str, Any]], metric_id: str | None = None
) -> list[dict[str, Any]]:
    wanted = _qa_norm(query)
    scored: list[dict[str, Any]] = []
    for row in rows:
        mid = str(row.get("metric_id") or "")
        if not mid:
            continue
        name = str(row.get("name_zh") or "")
        base_name = re.sub(r"[（(][^）)]*[）)]", "", name).strip()
        display = str(row.get("display_name") or "")
        score = 0.0
        reason: str | None = None
        if metric_id and mid == metric_id:
            score, reason = 1.0, "metric_id"
        elif wanted and wanted == _qa_norm(mid):
            score, reason = 1.0, "metric_id"
        elif wanted and _qa_norm(name) and _qa_norm(name) in wanted:
            score, reason = 0.98, "exact_name"
        elif wanted and len(_qa_norm(base_name)) >= 2 and _qa_norm(base_name) in wanted:
            score, reason = 0.95, "name_substring"
        elif wanted and _qa_norm(display) and _qa_norm(display) in wanted:
            score, reason = 0.9, "display_name"
        elif wanted and len(wanted) >= 2 and wanted in _qa_norm(name):
            score, reason = 0.85, "query_in_name"
        else:
            ratio = SequenceMatcher(None, wanted, _qa_norm(base_name or name)).ratio()
            if ratio >= 0.62:
                score, reason = round(ratio * 0.7, 4), "fuzzy_name"
        if reason is None:
            continue
        scored.append(
            {
                "layer": "metrics",
                "id": mid,
                "label": name or mid,
                "reason": reason,
                "score": score,
            }
        )
    scored.sort(key=lambda item: (-float(item["score"]), item["id"]))
    return scored[:_QA_MAX_CANDIDATES]


def _qa_rule_list(row: dict[str, Any]) -> list[Any]:
    value = row.get("rule_set_json")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return []
    return value if isinstance(value, list) else []


def _qa_content_mask(normalized: str) -> tuple[list[bool], int]:
    mask = [char not in _ANSWER_PUNCT for char in normalized]
    for stopword in sorted(_ANSWER_STOPWORDS, key=len, reverse=True):
        start = normalized.find(stopword)
        while start != -1:
            for index in range(start, start + len(stopword)):
                mask[index] = False
            start = normalized.find(stopword, start + 1)
    return mask, sum(1 for flag in mask if flag)


def _qa_match_entries(
    normalized: str, mask: list[bool], entries: list[dict[str, Any]]
) -> dict[str, Any]:
    taken = [False] * len(normalized)
    matched: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    labeled = sorted(
        ((entry, _qa_norm(entry.get("label"))) for entry in entries),
        key=lambda item: len(item[1]),
        reverse=True,
    )
    for entry, key in labeled:
        if len(key) < 2:
            continue
        start = normalized.find(key)
        while start != -1:
            end = start + len(key)
            if not any(taken[start:end]):
                for index in range(start, end):
                    taken[index] = True
                identity = (str(entry.get("id")), start)
                if identity not in seen:
                    seen.add(identity)
                    matched.append(
                        {
                            "id": entry.get("id"),
                            "label": entry.get("label"),
                            "span": [start, end],
                            "source": entry.get("source"),
                        }
                    )
            start = normalized.find(key, start + 1)
    total = sum(1 for flag in mask if flag)
    covered = sum(1 for index, flag in enumerate(mask) if flag and taken[index])
    fragments: list[str] = []
    start_index: int | None = None
    for index in range(len(normalized)):
        uncovered = mask[index] and not taken[index]
        if uncovered and start_index is None:
            start_index = index
        elif not uncovered and start_index is not None:
            fragments.append(normalized[start_index:index])
            start_index = None
    if start_index is not None:
        fragments.append(normalized[start_index:])
    return {
        "matched": matched,
        "covered": covered,
        "total": total,
        "coverage": round(covered / total, 4) if total else 0.0,
        "missing": [item for item in fragments if item],
    }


def _qa_table_count(runtime: Runtime, table: str, cache: dict[str, int | None]) -> int | None:
    if not _QA_FACT_TABLE_RE.match(table or ""):
        return None
    if table in cache:
        return cache[table]
    try:
        rows = runtime.metadata.query(f"SELECT count(*) AS n FROM {table}")
        cache[table] = int((rows[0] or {}).get("n") or 0) if rows else 0
    except Exception:
        cache[table] = None
    return cache[table]


def _qa_fact_eval(
    row: dict[str, Any],
    obs_row: dict[str, Any] | None,
    bindings: list[dict[str, Any]],
    table_counts: dict[str, int | None],
) -> dict[str, Any]:
    mid = str(row.get("metric_id") or "")
    version = str(row.get("definition_version") or "")
    output_mode = str(row.get("output_mode") or "")
    kind = str(row.get("metric_kind") or "")
    formula = str(row.get("formula_expr") or "")
    window_kind = str(row.get("window_kind") or "")
    numerator_agg = str(row.get("numerator_agg") or "")
    denominator_agg = str(row.get("denominator_agg") or "")
    fact_function = str(row.get("fact_function") or "")
    obs_count = int((obs_row or {}).get("n") or 0)
    has_fixture = bool((obs_row or {}).get("has_fixture"))
    rule_count = len(_qa_rule_list(row))
    fact_tables = sorted({str(item.get("fact_table")) for item in bindings if item.get("fact_table")})
    fields = [
        {
            "role": item.get("role"),
            "table": item.get("fact_table"),
            "column": item.get("entity_column"),
            "expr": item.get("value_expr"),
            "agg": item.get("agg"),
            "windowColumn": item.get("window_column"),
        }
        for item in bindings
    ]
    structural = (
        kind in _QA_DRIVABLE_KINDS
        and bool(formula)
        and bool(window_kind)
        and bool(numerator_agg)
        and (kind != "ratio" or bool(denominator_agg))
    )
    payload: dict[str, Any] = {
        "id": f"{mid}@{version}",
        "metricId": mid,
        "name": row.get("name_zh"),
        "definitionVersion": version,
        "outputMode": output_mode or None,
        "metricKind": kind or None,
        "publishable": bool(row.get("publishable")),
        "structural": structural,
        "drivable": False,
        "observationRows": obs_count,
        "fixture": has_fixture,
        "dataSource": ("fixture" if has_fixture else "business") if obs_count else None,
        "factTables": [
            {"table": table, "rows": table_counts.get(table)} for table in fact_tables
        ],
        "fields": fields,
        "factFunction": fact_function or None,
        "ruleCount": rule_count,
        "window": {
            "start": _qa_iso((obs_row or {}).get("ws")),
            "end": _qa_iso((obs_row or {}).get("we")),
        },
        "status": "missing",
        "code": None,
        "what": None,
        "howToFix": None,
    }
    if output_mode == "rule_set":
        payload.update(
            status="degraded",
            code="E_FACTS_RULE_INPUTS",
            what=f"规则型口径（{rule_count} 条规则）缺事实输入",
            howToFix=f"提交 as_of 时点的客户/账户事实后调用 POST /metrics/{mid}/rules",
        )
        return payload
    if bool(row.get("formula_disabled")):
        payload.update(
            status="missing",
            code="E_FACTS_FORMULA_DISABLED",
            what=f"{mid} 的公式被禁用",
            howToFix="在口径治理中启用公式或改用变体指标",
        )
        return payload
    if kind not in _QA_DRIVABLE_KINDS:
        payload.update(
            status="missing",
            code="E_FACTS_NOT_SCALAR",
            what=f"{mid} 的 metricKind={kind or 'unknown'} 不是标量可计算类型",
            howToFix="按口径卡/规则集读取，或选择可标量计算的变体",
        )
        return payload
    if not structural:
        payload.update(
            status="missing",
            code="E_FACTS_DEFINITION_QUARTET",
            what=f"{mid} 的四元组不完整（formula/window/aggregate/denominator）",
            howToFix="补齐 formula_expr、window_kind、numerator_agg（ratio 还需 denominator_agg）",
        )
        return payload
    payload["drivable"] = not bool(row.get("formula_disabled"))
    if obs_count > 0:
        payload.update(status="covered", code="E_FACTS_OBSERVED")
        return payload
    if bindings:
        required = {"numerator", "denominator"} if kind == "ratio" else {"numerator"}
        roles = {str(item.get("role")) for item in bindings}
        if not required.issubset(roles):
            payload.update(
                status="missing",
                code="E_FACTS_FIELD_BINDING",
                what=f"{mid} 缺字段绑定：需要 {sorted(required)}，已有 {sorted(roles)}",
                howToFix="在 metric_field_binding 登记缺失角色后重新投影",
            )
            return payload
        empty_tables = [
            table for table in fact_tables if table_counts.get(table) == 0
        ]
        if empty_tables:
            payload.update(
                status="degraded",
                code="E_FACTS_TABLE_EMPTY",
                what=f"{', '.join(empty_tables)} 存在但 0 行",
                howToFix="装载事实 CSV 后运行 facts-project，再重试",
            )
            return payload
        payload.update(
            status="degraded",
            code="E_FACTS_NO_OBSERVATION",
            what=f"{mid} 有字段绑定，但 metric_observation 无观察值",
            howToFix="运行 facts-project 写入观察值后重试",
        )
        return payload
    if fact_function:
        payload.update(
            status="degraded",
            code="E_FACTS_NO_OBSERVATION",
            what=f"{fact_function} 已登记，但 metric_observation 无观察值",
            howToFix="装载事实表后运行 facts-project（投影函数）",
        )
        return payload
    payload.update(
        status="missing",
        code="E_FACTS_FIELD_BINDING",
        what=f"{mid} 缺字段绑定/事实投影函数（metric_field_binding 无记录）",
        howToFix="登记 metric_field_binding 或 metric_definition.fact_function",
    )
    return payload


def _qa_iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _qa_facts_for_metrics(
    runtime: Runtime, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not rows:
        return []
    try:
        obs_rows = runtime.metadata.query(_QA_OBS_SQL)
    except Exception:
        obs_rows = []
    try:
        binding_rows = runtime.metadata.query(_QA_BINDING_SQL)
    except Exception:
        binding_rows = []
    obs_by: dict[str, dict[str, Any]] = {}
    for item in obs_rows:
        mid = str(item.get("metric_id") or "")
        if mid and mid not in obs_by:
            obs_by[mid] = item
    bindings_by: dict[str, list[dict[str, Any]]] = {}
    for item in binding_rows:
        mid = str(item.get("metric_id") or "")
        if not mid or not item.get("role") or not item.get("fact_table"):
            continue
        bindings_by.setdefault(mid, []).append(item)
    table_counts: dict[str, int | None] = {}
    result: list[dict[str, Any]] = []
    for row in rows:
        mid = str(row.get("metric_id") or "")
        bindings = bindings_by.get(mid, [])
        for item in bindings:
            table = str(item.get("fact_table") or "")
            if table:
                _qa_table_count(runtime, table, table_counts)
        result.append(_qa_fact_eval(row, obs_by.get(mid), bindings, table_counts))
    return result


def _qa_answerable(
    runtime: Runtime,
    query: str,
    ontology_version: str | None = None,
    min_coverage: float | None = None,
    metric_id: str | None = None,
    intent_hint: str | None = None,
    include_layers: bool = True,
) -> dict[str, Any]:
    base = runtime.answerable.check(
        query, ontology_version=ontology_version, min_coverage=min_coverage
    )
    if not include_layers:
        return base
    intent = _qa_intent(query, metric_id, intent_hint)
    threshold = float(base.get("threshold") or 0.0)
    timings: dict[str, int] = {}

    started = time.monotonic()
    graph_iri = base.get("ontologyGraph")
    graph_ok = bool(graph_iri)
    ontology_entries: list[dict[str, Any]] = []
    term_entries: list[dict[str, Any]] = []
    if graph_ok:
        try:
            ontology_entries, term_entries = _qa_graph_entries(runtime, str(graph_iri))
        except Exception:
            graph_ok = False
    timings["termsMs"] = int((time.monotonic() - started) * 1000)

    started = time.monotonic()
    metric_rows = _qa_metric_rows(runtime)
    metric_candidates = _qa_metric_candidates(query, metric_rows, metric_id)
    selected_candidates = [
        item for item in metric_candidates if float(item.get("score") or 0) >= 0.85
    ][:1]
    row_by_id = {str(row.get("metric_id")): row for row in metric_rows}
    selected_rows = [
        row_by_id[item["id"]] for item in selected_candidates if item["id"] in row_by_id
    ]
    timings["metricMs"] = int((time.monotonic() - started) * 1000)

    normalized = re.sub(r"\s+", "", query.lower())
    mask, _ = _qa_content_mask(normalized)
    ontology_match = _qa_match_entries(normalized, mask, ontology_entries)
    terms_match = _qa_match_entries(normalized, mask, term_entries)

    if not graph_ok:
        ontology_status = "unavailable"
    elif ontology_match["matched"] and ontology_match["coverage"] >= threshold:
        ontology_status = "covered"
    elif ontology_match["matched"]:
        ontology_status = "partial"
    else:
        ontology_status = "missing"

    if not graph_ok:
        terms_status = "unavailable"
    elif terms_match["matched"]:
        terms_status = "covered"
    elif ontology_status == "covered" or selected_rows:
        terms_status = "not_applicable"
    else:
        terms_status = "missing"

    metric_hint = bool(_QA_METRIC_HINT_RE.search(query))
    if selected_rows:
        metrics_status = "covered"
    elif intent == "value" or metric_hint:
        metrics_status = "missing"
    else:
        metrics_status = "not_applicable"

    started = time.monotonic()
    fact_evals = _qa_facts_for_metrics(runtime, selected_rows)
    timings["factsMs"] = int((time.monotonic() - started) * 1000)

    if not fact_evals:
        facts_status = "not_applicable"
    elif any(item.get("status") == "unavailable" for item in fact_evals):
        facts_status = "unavailable"
    elif any(item.get("status") == "missing" for item in fact_evals):
        facts_status = "missing"
    elif any(item.get("status") == "degraded" for item in fact_evals):
        facts_status = "degraded"
    elif all(item.get("status") == "covered" for item in fact_evals):
        facts_status = "covered"
    else:
        facts_status = "degraded"

    value_answerable = (
        intent == "value"
        and facts_status == "covered"
        and bool(fact_evals)
        and all(item.get("drivable") and item.get("publishable") for item in fact_evals)
    )
    blocking_facts = facts_status in ("missing", "unavailable")
    if intent == "value":
        answerable = bool(selected_rows) and not blocking_facts
    else:
        answerable = bool(base.get("answerable")) or bool(selected_rows)

    if answerable:
        reason_code = None
    elif intent == "value" and not selected_rows:
        reason_code = "E_ANSWER_METRIC_NOT_FOUND"
    elif blocking_facts:
        reason_code = "E_ANSWER_FACTS_MISSING"
    else:
        reason_code = base.get("reasonCode") or "E_ANSWER_NOT_COVERED"

    missing: list[dict[str, Any]] = []
    seen_missing: set[tuple[str, str, str]] = set()

    def add_missing(item: dict[str, Any]) -> None:
        key = (
            str(item.get("layer") or ""),
            str(item.get("code") or ""),
            str(item.get("metricId") or item.get("text") or ""),
        )
        if key in seen_missing:
            return
        seen_missing.add(key)
        missing.append(item)

    for item in base.get("missing") or []:
        text = str(item.get("text") or "")
        add_missing(
            {
                **item,
                "layer": "ontology",
                "code": "E_LAYER_ONTOLOGY_GAP",
                "what": f"本体未声明「{text}」",
                "howToFix": "补充 rdfs:label / skos:prefLabel，或收窄问题范围",
            }
        )
    if ontology_status == "unavailable":
        add_missing(
            {
                "layer": "ontology",
                "code": "E_LAYER_ONTOLOGY_UNAVAILABLE",
                "text": "",
                "what": "T-Box 命名图不可读",
                "howToFix": "检查 graph/ontology 指针与 Oxigraph 可用性",
            }
        )
    if terms_status == "missing" and intent == "value":
        add_missing(
            {
                "layer": "terms",
                "code": "E_LAYER_TERMS_GAP",
                "text": "",
                "what": "问题中的概念没有 SKOS 术语/别名命中",
                "howToFix": "在术语层补充 skos:altLabel 或 term:TermEntry",
            }
        )
    if metrics_status == "missing":
        add_missing(
            {
                "layer": "metrics",
                "code": "E_LAYER_METRICS_GAP",
                "text": "",
                "what": "未匹配到可求值口径指标",
                "howToFix": "指定 metricId，或补充指标名称/别名",
                "candidates": [
                    {"id": item["id"], "label": item["label"], "score": item["score"]}
                    for item in metric_candidates[:3]
                ],
            }
        )
    for item in fact_evals:
        if item.get("status") in ("missing", "degraded"):
            add_missing(
                {
                    "layer": "facts",
                    "code": item.get("code"),
                    "metricId": item.get("metricId"),
                    "text": item.get("what"),
                    "what": item.get("what"),
                    "howToFix": item.get("howToFix"),
                }
            )

    selected_metrics: list[dict[str, Any]] = []
    facts_by_metric = {str(item.get("metricId")): item for item in fact_evals}
    for item in selected_candidates:
        row = row_by_id.get(item["id"])
        if not row:
            continue
        fact = facts_by_metric.get(item["id"]) or {}
        selected_metrics.append(
            {
                "metricId": item["id"],
                "name": item["label"],
                "definitionVersion": row.get("definition_version"),
                "outputMode": row.get("output_mode") or None,
                "metricKind": row.get("metric_kind"),
                "formula": row.get("formula_expr"),
                "formulaText": row.get("formula_text"),
                "definition": row.get("definition"),
                "windowKind": row.get("window_kind"),
                "minWindowDays": row.get("min_window_days"),
                "evidenceBasis": row.get("evidence_basis"),
                "publishable": bool(row.get("publishable")),
                "unit": row.get("unit"),
                "grain": row.get("grain"),
                "factFunction": row.get("fact_function"),
                "ruleCount": len(_qa_rule_list(row)),
                "score": item["score"],
                "factsStatus": fact.get("status"),
                "factsCode": fact.get("code"),
                "observationRows": fact.get("observationRows", 0),
                "dataSource": fact.get("dataSource"),
            }
        )

    candidates: list[dict[str, Any]] = []
    for entry in ontology_match["matched"]:
        candidates.append(
            {
                "layer": "ontology",
                "id": entry.get("id"),
                "label": entry.get("label"),
                "reason": "rdfs_label_match",
                "score": 1.0,
            }
        )
    for entry in terms_match["matched"]:
        candidates.append(
            {
                "layer": "terms",
                "id": entry.get("id"),
                "label": entry.get("label"),
                "reason": "skos_alias_match",
                "score": 1.0,
            }
        )
    candidates.extend(metric_candidates)
    candidates = candidates[:_QA_MAX_CANDIDATES]

    layers = [
        {
            "layer": "ontology",
            "status": ontology_status,
            "coverage": ontology_match["coverage"],
            "matched": ontology_match["matched"],
            "missing": ontology_match["missing"],
        },
        {
            "layer": "terms",
            "status": terms_status,
            "coverage": terms_match["coverage"],
            "matched": terms_match["matched"],
            "missing": terms_match["missing"],
        },
        {
            "layer": "metrics",
            "status": metrics_status,
            "coverage": 1.0 if selected_rows else 0.0,
            "matched": [
                {"id": item["id"], "label": item["label"], "score": item["score"]}
                for item in selected_candidates
            ],
            "missing": [] if selected_rows else metric_candidates[:3],
        },
        {
            "layer": "facts",
            "status": facts_status,
            "coverage": (
                round(
                    sum(1 for item in fact_evals if item.get("status") == "covered")
                    / len(fact_evals),
                    4,
                )
                if fact_evals
                else 0.0
            ),
            "matched": fact_evals,
            "missing": [
                item.get("what")
                for item in fact_evals
                if item.get("status") in ("missing", "degraded")
            ],
        },
    ]

    payload = dict(base)
    payload.update(
        {
            "inputType": "metric" if metric_id else "question",
            "intent": intent,
            "answerable": answerable,
            "valueAnswerable": value_answerable,
            "answerMode": "value" if value_answerable else ("definition" if answerable else "none"),
            "degraded": bool(base.get("degraded")) or facts_status == "degraded" or not graph_ok,
            "missing": missing,
            "layers": layers,
            "candidates": candidates,
            "selectedMetrics": selected_metrics,
            "reasonCode": reason_code,
            "hint": base.get("hint") if not answerable else None,
            "timings": timings,
        }
    )
    return payload


def _qa_retrieve(
    runtime: Runtime, query: str, top_k: int, strategy: str
) -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {
        "status": "degraded",
        "chunks": 0,
        "facts": 0,
        "citations": [],
        "strategy": strategy,
        "error": None,
    }
    try:
        context = getattr(runtime, "context", None)
        if context is not None:
            pack = context.resolve(
                {
                    "query": query,
                    "topK": top_k,
                    "tokenBudget": 512,
                    "taskType": "answer",
                    "strategy": strategy,
                }
            )
            result.update(
                status="degraded" if pack.get("degraded") else "ok",
                chunks=len(pack.get("chunks") or []),
                facts=len(pack.get("facts") or []),
                citations=list(pack.get("citations") or []),
                packId=pack.get("id"),
                warnings=list(pack.get("warnings") or []),
            )
        else:
            search = getattr(runtime, "search", None)
            if search is None:
                result.update(status="skipped", error="retrieval_unavailable")
            else:
                hits = search.hybrid_search(query, limit=top_k, mode=strategy)
                results = list(hits.get("results") or [])
                result.update(
                    status="degraded" if hits.get("degraded") else "ok",
                    chunks=len(results),
                    citations=[
                        {
                            "id": f"doc:{item.get('documentId')}#{item.get('chunkId')}",
                            "kind": "chunk",
                            "ref": item.get("chunkId"),
                            "documentId": item.get("documentId"),
                        }
                        for item in results
                    ],
                    warnings=list(hits.get("reasons") or []),
                )
    except PortError as exc:
        result.update(status="degraded", error=exc.provider_code or exc.code)
    except Exception as exc:  # retrieval must never turn the answer into a 500
        result.update(status="degraded", error=str(exc))
    result["durationMs"] = int((time.monotonic() - started) * 1000)
    return result


def _qa_answer(
    runtime: Runtime,
    query: str,
    ontology_version: str | None = None,
    metric_id: str | None = None,
    top_k: int = 5,
    strategy: str = "lexical",
    request_id: str | None = None,
) -> dict[str, Any]:
    coverage = _qa_answerable(
        runtime,
        query,
        ontology_version=ontology_version,
        metric_id=metric_id,
        include_layers=True,
    )
    retrieve = _qa_retrieve(runtime, query, top_k, strategy)
    for item in retrieve.get("citations") or []:
        if item.get("kind") != "chunk" or not item.get("documentId"):
            continue
        chunk_no = source_ref.chunk_no_from_id(item.get("ref"))
        if chunk_no is None:
            continue
        item["sourceRef"] = source_ref.chunk_descriptor(
            str(item["documentId"]), chunk_no, item.get("ref")
        )
        source_ref.register_ref(runtime.metadata, item["sourceRef"])
    selected = list(coverage.get("selectedMetrics") or [])
    selected_metric = selected[0] if selected else None
    layers = {item.get("layer"): item for item in coverage.get("layers") or []}
    facts_layer = layers.get("facts") or {}
    facts_status = str(facts_layer.get("status") or "not_applicable")
    facts_evals = list(facts_layer.get("matched") or [])
    fact_eval = facts_evals[0] if facts_evals else {}
    intent = str(coverage.get("intent") or "definition")
    timings = coverage.get("timings") or {}
    timings_terms = int(timings.get("termsMs") or 0)
    timings_metric = int(timings.get("metricMs") or 0)
    timings_facts = int(timings.get("factsMs") or 0)

    citations: list[dict[str, Any]] = []

    def add_citation(item: dict[str, Any]) -> None:
        if not item.get("id"):
            return
        if any(existing.get("id") == item.get("id") and existing.get("kind") == item.get("kind") for existing in citations):
            return
        citations.append(item)

    version_id = coverage.get("ontologyVersion")
    graph_iri = coverage.get("ontologyGraph")
    if version_id:
        add_citation(
            {
                "id": str(version_id),
                "kind": "ontology-version",
                "ref": graph_iri,
                "versionId": version_id,
            }
        )
    for layer_name in ("ontology", "terms"):
        layer = layers.get(layer_name) or {}
        for entry in layer.get("matched") or []:
            add_citation(
                {
                    "id": entry.get("id"),
                    "kind": "rdfs-term" if layer_name == "ontology" else "skos-term",
                    "ref": entry.get("label"),
                    "label": entry.get("label"),
                    "layer": layer_name,
                    "span": entry.get("span"),
                }
            )
    if selected_metric:
        metric_ref = f"{selected_metric['metricId']}@{selected_metric['definitionVersion']}"
        add_citation(
            {
                "id": f"metric:{metric_ref}",
                "kind": "metric-definition",
                "ref": metric_ref,
                "metricId": selected_metric["metricId"],
                "definitionVersion": selected_metric["definitionVersion"],
                "name": selected_metric.get("name"),
                "fields": {
                    "formula": selected_metric.get("formula"),
                    "windowKind": selected_metric.get("windowKind"),
                    "minWindowDays": selected_metric.get("minWindowDays"),
                    "evidenceBasis": selected_metric.get("evidenceBasis"),
                    "publishable": selected_metric.get("publishable"),
                    "unit": selected_metric.get("unit"),
                },
            }
        )
        formula = selected_metric.get("formula")
        if formula:
            add_citation(
                {
                    "id": f"formula:{metric_ref}",
                    "kind": "formula",
                    "ref": formula,
                    "metricId": selected_metric["metricId"],
                    "definitionVersion": selected_metric["definitionVersion"],
                }
            )
        if selected_metric.get("outputMode") == "rule_set":
            add_citation(
                {
                    "id": f"rules:{metric_ref}",
                    "kind": "rule-set",
                    "ref": metric_ref,
                    "metricId": selected_metric["metricId"],
                    "definitionVersion": selected_metric["definitionVersion"],
                    "ruleCount": selected_metric.get("ruleCount"),
                }
            )
        if fact_eval:
            if fact_eval.get("factFunction"):
                add_citation(
                    {
                        "id": f"factfn:{fact_eval['factFunction']}",
                        "kind": "fact-projection",
                        "ref": fact_eval["factFunction"],
                        "metricId": fact_eval.get("metricId"),
                        "observationRows": fact_eval.get("observationRows"),
                    }
                )
            for table in fact_eval.get("factTables") or []:
                add_citation(
                    {
                        "id": f"table:{table.get('table')}",
                        "kind": "fact-table",
                        "ref": table.get("table"),
                        "rows": table.get("rows"),
                        "metricId": fact_eval.get("metricId"),
                    }
                )
            for field in fact_eval.get("fields") or []:
                field_ref = f"{field.get('table')}.{field.get('expr') or field.get('column') or ''}"
                add_citation(
                    {
                        "id": f"field:{field_ref}",
                        "kind": "fact-table-field",
                        "ref": field_ref,
                        "role": field.get("role"),
                        "agg": field.get("agg"),
                        "metricId": fact_eval.get("metricId"),
                    }
                )
            if int(fact_eval.get("observationRows") or 0) > 0:
                window = fact_eval.get("window") or {}
                citation: dict[str, Any] = {
                    "id": f"obs:{fact_eval.get('metricId')}@{fact_eval.get('definitionVersion')}",
                    "kind": "fact-observation",
                    "ref": "platform.metric_observation",
                    "metricId": fact_eval.get("metricId"),
                    "definitionVersion": fact_eval.get("definitionVersion"),
                    "rows": fact_eval.get("observationRows"),
                    "dataSource": fact_eval.get("dataSource"),
                }
                if window.get("start") and window.get("end"):
                    citation["sourceRef"] = source_ref.observation_set_descriptor(
                        str(fact_eval.get("metricId")),
                        str(fact_eval.get("definitionVersion")),
                        period_start=str(window["start"]),
                        period_end=str(window["end"]),
                        fixture=bool(fact_eval.get("fixture")),
                        row_count=int(fact_eval.get("observationRows") or 0),
                    )
                    source_ref.register_ref(runtime.metadata, citation["sourceRef"])
                add_citation(citation)
    for item in (retrieve.get("citations") or [])[:5]:
        add_citation(item)

    compute = {
        "step": "compute",
        "status": "skipped",
        "input": {"metricId": selected_metric.get("metricId") if selected_metric else None},
        "output": {"reason": "no_metric", "value": None},
        "durationMs": 0,
    }
    answer_type = "none"
    value: dict[str, Any] | None = None
    refused = not bool(coverage.get("answerable"))
    value_refused = not bool(coverage.get("valueAnswerable")) and intent == "value"
    reason_code = coverage.get("reasonCode")

    if selected_metric:
        metric_id_value = selected_metric["metricId"]
        if selected_metric.get("outputMode") == "rule_set":
            answer_type = "rule_set"
            started = time.monotonic()
            rules = getattr(runtime, "rules", None)
            route_output: dict[str, Any] = {
                "mode": "rule_set",
                "value": None,
                "ruleCount": selected_metric.get("ruleCount"),
            }
            if rules is None:
                route_output["error"] = "rule_executor_unavailable"
            else:
                try:
                    executed = rules.execute(metric_id_value, [])
                    route_output["result"] = executed
                except PortError as exc:
                    route_output["error"] = exc.provider_code or exc.code
                except Exception as exc:
                    route_output["error"] = str(exc)
            compute.update(
                status="routed",
                output=route_output,
                durationMs=int((time.monotonic() - started) * 1000),
            )
            if intent == "value":
                refused = True
                value_refused = True
                reason_code = "E_ANSWER_RULE_SET_NEEDS_FACTS"
        elif value_refused and facts_status in ("missing", "unavailable"):
            refused = True
            reason_code = "E_ANSWER_FACTS_MISSING"
        elif coverage.get("valueAnswerable") and selected_metric.get("publishable"):
            answer_type = "value"
            started = time.monotonic()
            metrics_port = getattr(runtime, "metrics", None)
            compute_output: dict[str, Any] = {"value": None}
            if metrics_port is None:
                compute_output["error"] = "metric_service_unavailable"
            else:
                try:
                    computed = metrics_port.compute(
                        metric_id_value,
                        internal=False,
                    )
                    value = computed
                    answer_type = "value"
                    compute_output = {
                        "value": computed.get("value"),
                        "unit": computed.get("unit"),
                        "dataSource": computed.get("dataSource"),
                        "definitionVersion": computed.get("definitionVersion"),
                        "window": computed.get("window"),
                        "sourceRef": computed.get("sourceRef"),
                        "sourceRefs": computed.get("sourceRefs") or [],
                    }
                    if computed.get("sourceRef"):
                        add_citation(
                            {
                                "id": computed["sourceRef"]["ref"],
                                "kind": "value-source",
                                "ref": computed["sourceRef"]["ref"],
                                "targetTable": computed["sourceRef"]["targetTable"],
                                "sourceRef": computed["sourceRef"],
                                "metricId": metric_id_value,
                            }
                        )
                except PortError as exc:
                    compute_output["error"] = exc.provider_code or exc.code
                    answer_type = "definition"
                    value_refused = True
                    if not refused:
                        reason_code = "E_ANSWER_VALUE_DEGRADED"
                except Exception as exc:
                    compute_output["error"] = str(exc)
                    answer_type = "definition"
                    value_refused = True
            compute.update(
                status="ok" if value is not None else "failed",
                output=compute_output,
                durationMs=int((time.monotonic() - started) * 1000),
            )
        else:
            answer_type = "definition"
            compute["output"] = {
                "reason": f"facts.{facts_status}",
                "value": None,
                "dataSource": None,
            }
            if intent == "value" and not refused:
                value_refused = True
                reason_code = "E_ANSWER_VALUE_DEGRADED"
    elif coverage.get("answerable"):
        answer_type = "ontology"
    if refused and reason_code is None:
        reason_code = "E_ANSWER_NOT_COVERED"
    if value_refused and not refused and reason_code is None:
        reason_code = "E_ANSWER_VALUE_DEGRADED"

    missing = list(coverage.get("missing") or [])
    if refused:
        answer_text = "证据不足，拒绝作答。缺口：" + "；".join(
            str(item.get("what") or item.get("text") or item.get("code"))
            for item in missing[:4]
        )
    elif value and selected_metric:
        answer_text = (
            f"{selected_metric.get('name')} = {value.get('value')} "
            f"{value.get('unit') or selected_metric.get('unit') or ''}"
            f"（{selected_metric['metricId']}@{selected_metric['definitionVersion']}，"
            f"dataSource={value.get('dataSource')}）"
        )
    elif answer_type == "rule_set" and selected_metric:
        answer_text = (
            f"「{selected_metric.get('name')}」是规则型口径"
            f"（outputMode=rule_set，{selected_metric.get('ruleCount')} 条规则）；"
            "当前事实输入不足，不给出标量结果。"
        )
    elif selected_metric:
        detail = (
            selected_metric.get("formulaText")
            or selected_metric.get("definition")
            or selected_metric.get("formula")
            or "无公式文本"
        )
        answer_text = (
            f"「{selected_metric.get('name')}」"
            f"（{selected_metric['metricId']}@{selected_metric['definitionVersion']}）口径：{detail}；"
            f"观察期 {selected_metric.get('windowKind')}；证据 {selected_metric.get('evidenceBasis')}。"
            f"事实层 {facts_status}，不给出数值。"
        )
    else:
        names = "、".join(
            str(item.get("label"))
            for item in (layers.get("ontology") or {}).get("matched") or []
        ) or "（无）"
        answer_text = f"本体命中：{names}；未匹配到可求值口径，按定义/关系回答。"

    steps = [
        {
            "step": "retrieve",
            "status": retrieve.get("status"),
            "input": {"query": query, "strategy": strategy, "topK": top_k},
            "output": {
                "chunks": retrieve.get("chunks"),
                "facts": retrieve.get("facts"),
                "packId": retrieve.get("packId"),
                "error": retrieve.get("error"),
            },
            "durationMs": retrieve.get("durationMs"),
        },
        {
            "step": "terms",
            "status": "ok" if graph_iri else "degraded",
            "input": {"ontologyVersion": version_id},
            "output": {
                "ontologyMatched": len((layers.get("ontology") or {}).get("matched") or []),
                "termsMatched": len((layers.get("terms") or {}).get("matched") or []),
                "ontologyStatus": (layers.get("ontology") or {}).get("status"),
                "termsStatus": (layers.get("terms") or {}).get("status"),
            },
            "durationMs": timings_terms,
        },
        {
            "step": "metric",
            "status": (layers.get("metrics") or {}).get("status"),
            "input": {"query": query, "metricId": metric_id},
            "output": {
                "metricId": selected_metric.get("metricId") if selected_metric else None,
                "name": selected_metric.get("name") if selected_metric else None,
                "definitionVersion": (
                    selected_metric.get("definitionVersion") if selected_metric else None
                ),
                "candidates": [
                    {"id": item["id"], "label": item["label"], "score": item["score"]}
                    for item in (coverage.get("candidates") or [])
                    if item.get("layer") == "metrics"
                ][:3],
            },
            "durationMs": timings_metric,
        },
        {
            "step": "facts",
            "status": facts_status,
            "input": {"metricId": selected_metric.get("metricId") if selected_metric else None},
            "output": {
                "observationRows": fact_eval.get("observationRows", 0),
                "factFunction": fact_eval.get("factFunction"),
                "factTables": fact_eval.get("factTables") or [],
                "code": fact_eval.get("code"),
                "dataSource": fact_eval.get("dataSource"),
            },
            "durationMs": timings_facts,
        },
        compute,
    ]

    payload = dict(coverage)
    payload.update(
        {
            "refused": refused,
            "valueRefused": value_refused,
            "reasonCode": reason_code,
            "answerMode": "value" if value else ("definition" if coverage.get("answerable") else "none"),
            "answerType": answer_type,
            "answer": answer_text,
            "value": value.get("value") if value else None,
            "dataSource": value.get("dataSource") if value else None,
            "sourceRef": value.get("sourceRef") if value else None,
            "sourceRefs": (value.get("sourceRefs") or []) if value else [],
            "steps": steps,
            "citations": citations,
            "missing": missing,
        }
    )
    # B-02: every answer that refuses, or that applies a metric's口径判定,
    # appends one PROV activity. The chain is append-only; nothing is rewritten.
    payload["requestId"] = request_id or f"req-{uuid.uuid4().hex[:12]}"
    payload["prov"] = None
    recorder = getattr(runtime, "prov", None)
    if recorder is not None:
        try:
            if refused:
                record = recorder.record_refusal(
                    query=query,
                    coverage=payload,
                    retrieve=retrieve,
                    request_id=payload["requestId"],
                    strategy=strategy,
                    top_k=top_k,
                )
            elif selected_metric:
                record = recorder.record_decision(
                    str(selected_metric["metricId"]),
                    reason="answer",
                    request_id=payload["requestId"],
                )
            else:
                record = None
            if record:
                payload["prov"] = {
                    "graph": prov_module.PROV_GRAPH,
                    "activityId": record["activityId"],
                    "activityIri": record["activityIri"],
                    "kind": record["kind"],
                }
        except Exception as exc:  # provenance must not break answering
            payload["prov"] = {"graph": prov_module.PROV_GRAPH, "error": str(exc)}
    return payload


# ---- governance console helpers ----------------------------------------

ACTOR_REQUIRED = "E_GOVERNANCE_ACTOR_REQUIRED"
REASON_REQUIRED = "E_GOVERNANCE_REASON_REQUIRED"


def _governance_rejection(code: str, message: str, field: str | None = None) -> PortError:
    return PortError(
        code="InvalidArgument",
        message=message,
        provider="platform",
        provider_code=code,
        details={"field": field} if field else {},
    )


def _governance_field(body: dict[str, Any], field: str, code: str) -> str:
    value = body.get(field) if isinstance(body, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise _governance_rejection(code, f"{field} is required", field)
    return value.strip()


def _governance_actor(body: dict[str, Any]) -> str:
    return _governance_field(body, "actor", ACTOR_REQUIRED)


def _governance_reason(body: dict[str, Any]) -> str:
    return _governance_field(body, "reason", REASON_REQUIRED)


def _governance_impact(diff: dict[str, Any]) -> dict[str, Any]:
    summary = diff.get("summary") or {}
    return {
        "addedTriples": summary.get("addedTriples", 0),
        "removedTriples": summary.get("removedTriples", 0),
        "addedClasses": len(summary.get("addedClasses") or []),
        "removedClasses": len(summary.get("removedClasses") or []),
        "addedProperties": len(summary.get("addedProperties") or []),
        "removedProperties": len(summary.get("removedProperties") or []),
        "domainChanges": len(summary.get("domainChanges") or []),
        "rangeChanges": len(summary.get("rangeChanges") or []),
        "removedClassInstances": sum(
            int(item.get("instances") or 0)
            for item in summary.get("removedClassInstances") or []
        ),
        "breakingItems": len(diff.get("breakingItems") or []),
    }


def _governance_publish_dry_run(
    runtime: Runtime,
    version_id: str,
    proposal_id: str | None,
    acknowledge_breaking: bool,
    publish_existing: bool,
) -> dict[str, Any]:
    """Re-run publish's own gates without writing anything.

    The gate helpers below are the exact ones ``publish`` calls; this function
    only translates their typed errors into a per-gate report, so a dry-run
    cannot diverge from the real publish or open a bypass path.
    """
    version = runtime.ontology.get(version_id)
    current = runtime.ontology.current()
    result: dict[str, Any] = {
        "dryRun": True,
        "versionId": version_id,
        "versionStatus": version.get("status"),
        "currentVersionId": (current or {}).get("versionId"),
        "publishExisting": publish_existing,
        "wouldPublish": False,
        "unchanged": False,
        "governed": False,
        "implicit": False,
        "breaking": False,
        "acknowledgeBreaking": acknowledge_breaking,
        "impact": {},
        "gates": {},
        "blockers": [],
    }

    def block(gate: str, code: str, message: str, details: Any = None) -> None:
        result["blockers"].append(
            {"gate": gate, "code": code, "message": message, "details": details or {}}
        )

    if (
        not proposal_id
        and version.get("status") == "published"
        and current
        and current.get("versionId") == version_id
    ):
        result.update(
            {
                "wouldPublish": True,
                "unchanged": True,
                "gates": {"pointer": {"ok": True, "current": version_id}},
            }
        )
        return result

    declared = int(version.get("tripleCount") or 0)
    count = runtime.ontology.graph_count(version_id)
    integrity_ok = count == declared
    result["gates"]["integrity"] = {"ok": integrity_ok, "triples": count, "declared": declared}
    if not integrity_ok:
        block(
            "integrity",
            "E_ONTOLOGY_TRIPLE_MISMATCH",
            "graph triple count differs from the version record",
            {"graphTriples": count, "declared": declared},
        )

    proposal: dict[str, Any] | None = None
    if proposal_id:
        try:
            proposal = runtime.ontology.get_proposal(proposal_id)
        except PortError as exc:
            block("proposal", exc.provider_code or exc.code, exc.message)
    elif version.get("status") in ("proposed", "approved"):
        items = runtime.ontology.list_proposals(version_id).get("items") or []
        pending = [item for item in items if item.get("status") in ("proposed", "approved")]
        proposal = pending[0] if pending else None

    governed = proposal is not None
    implicit = proposal is None and not proposal_id
    result["governed"] = governed
    result["implicit"] = implicit
    diff: dict[str, Any] = {}
    if governed:
        if proposal.get("versionId") != version_id:
            block(
                "proposal",
                "E_ONTOLOGY_PROPOSAL_VERSION_MISMATCH",
                "proposal does not belong to the requested version",
            )
        if version.get("status") != "approved":
            block(
                "status",
                "E_ONTOLOGY_NOT_APPROVED",
                f"version is {version.get('status')}; an approved proposal is required",
            )
        if proposal.get("status") != "approved":
            block(
                "proposal",
                "E_ONTOLOGY_PROPOSAL_NOT_APPROVED",
                f"proposal is {proposal.get('status')}; approve it before publish",
            )
        diff = proposal.get("diff") or {}
        breaking = bool(proposal.get("breaking"))
        acknowledged = bool(
            acknowledge_breaking or proposal.get("acknowledgedBreaking")
        )
        result["impact"] = proposal.get("impact") or _governance_impact(diff)
    elif implicit:
        if version.get("status") not in ("draft", "approved", "superseded"):
            block(
                "status",
                "E_ONTOLOGY_STATUS",
                f"version is {version.get('status')}; publish requires draft/approved/superseded",
            )
        try:
            diff = runtime.ontology.diff((current or {}).get("versionId"), version_id)
        except PortError as exc:
            block("diff", exc.provider_code or exc.code, exc.message)
        breaking = bool(diff.get("breaking"))
        acknowledged = bool(acknowledge_breaking)
        result["impact"] = _governance_impact(diff) if diff else {}
    else:
        breaking = False
        acknowledged = False

    result["breaking"] = breaking
    result["gates"]["breaking"] = {
        "ok": not breaking or acknowledged,
        "breaking": breaking,
        "acknowledged": acknowledged,
    }
    if breaking and not acknowledged:
        block(
            "breaking",
            "E_ONTOLOGY_BREAKING",
            "breaking changes require acknowledgeBreaking=true",
            {"breakingItems": diff.get("breakingItems", [])},
        )

    graph_iri = str(version.get("graph") or "")
    nt = b""
    try:
        nt = runtime.graph.export_graph(graph_iri)
        result["gates"]["graph"] = {
            "ok": True, "graph": graph_iri, "bytes": len(nt),
        }
    except PortError as exc:
        result["gates"]["graph"] = {
            "ok": False, "code": exc.provider_code or exc.code, "message": exc.message,
        }
        block("graph", exc.provider_code or exc.code, exc.message)

    if nt:
        try:
            shacl = runtime.ontology._gate_shacl(nt, graph_iri)
            result["gates"]["shacl"] = {"ok": True, "conforms": shacl.get("conforms", True)}
        except PortError as exc:
            result["gates"]["shacl"] = {
                "ok": False, "code": exc.provider_code or exc.code,
                "message": exc.message, "details": exc.details or {},
            }
            block("shacl", exc.provider_code or exc.code, exc.message, exc.details)
        try:
            consistency = runtime.ontology._gate_consistency(nt)
            result["gates"]["consistency"] = {
                "ok": True,
                "consistent": consistency.get("consistent", True),
                "profile": consistency.get("profile"),
            }
        except PortError as exc:
            result["gates"]["consistency"] = {
                "ok": False, "code": exc.provider_code or exc.code,
                "message": exc.message, "details": exc.details or {},
            }
            block("consistency", exc.provider_code or exc.code, exc.message, exc.details)

    result["wouldPublish"] = not result["blockers"]
    result["changed"] = bool((current or {}).get("versionId") != version_id)
    return result


def create_app(runtime: Runtime, checks: list[CheckResult]) -> FastAPI:
    app = FastAPI(
        title="Platform Kernel",
        version=__version__,
        description="S0-S2: health, readiness, status, document ingest.",
    )
    # S7: the static UI also works when opened from disk (Origin: null). There
    # is no auth, so this is not a security boundary -- it only lets the
    # file:// entry point reach 127.0.0.1:8080.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["null", "http://127.0.0.1:8080", "http://localhost:8080"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(PortError)
    def port_error_handler(_request: Request, exc: PortError) -> JSONResponse:
        body = {
            "error": {
                "code": exc.code,
                "provider": exc.provider,
                "providerCode": exc.provider_code,
                "message": exc.message,
                "retryable": exc.retryable,
                "details": exc.details or {},
            }
        }
        return JSONResponse(status_code=_HTTP_STATUS.get(exc.code, 500), content=body)

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {"status": "ok", "version": __version__}

    @app.get("/readyz")
    def readyz() -> JSONResponse:
        results: dict[str, Any] = {}

        try:
            runtime.metadata.health()
            results["database"] = {"status": "ok"}
        except Exception as exc:
            results["database"] = {"status": "fail", "detail": str(exc)}

        try:
            runtime.graph.ask("ASK {}")
            results["graph"] = {"status": "ok"}
        except Exception as exc:
            results["graph"] = {"status": "fail", "detail": str(exc)}

        try:
            root = Path(runtime.config.storage.root)
            blobs = root / "blobs"
            if not blobs.is_dir():
                raise RuntimeError(f"blobs directory missing: {blobs}")
            usage = shutil.disk_usage(root)
            free_pct = (usage.free / usage.total) * 100 if usage.total else 0
            if free_pct < runtime.config.storage.min_free_pct:
                raise RuntimeError(
                    f"disk free {free_pct:.1f}% < min_free_pct={runtime.config.storage.min_free_pct}%"
                )
            results["storage"] = {"status": "ok", "disk_free_pct": round(free_pct, 2)}
        except Exception as exc:
            results["storage"] = {"status": "fail", "detail": str(exc)}

        try:
            pointer = healthboard.pointer_status(runtime)
        except Exception as exc:  # 观测项不得影响就绪状态码
            pointer = {
                "name": "tbox/current",
                "ok": False,
                "level": "error",
                "status": "unreadable",
                "warning": f"tbox/current 指针状态不可读：{exc}",
            }
        warnings = [] if pointer.get("ok") else [pointer.get("warning") or "tbox/current 非 published"]
        healthy = all(item["status"] == "ok" for item in results.values())
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={
                "status": "ok" if healthy else "degraded",
                "checks": results,
                "pointerStatus": pointer,
                "warnings": warnings,
                "note": "pointerStatus 仅告警，不参与就绪状态码（避免启动即崩）",
            },
        )

    @app.get("/health/dashboard")
    def health_dashboard() -> dict[str, Any]:
        """B-04 read-only aggregate: coverage, orphans, SHACL, inference, schema."""
        return healthboard.dashboard(runtime)

    @app.get("/health/ontology-diff")
    def health_ontology_diff(
        from_version: str | None = Query(default=None, alias="from", max_length=120),
        to_version: str | None = Query(default=None, alias="to", max_length=120),
    ) -> dict[str, Any]:
        """B-04 read-only T-Box diff; defaults to tbox/current vs previous version."""
        return healthboard.ontology_diff(runtime, from_version, to_version)

    # ---- S2 documents ---------------------------------------------------

    @app.post("/documents")
    def upload_document(
        file: UploadFile = File(...),
        filename: str | None = Form(default=None),
        metadata: str | None = Form(default=None),
    ) -> JSONResponse:
        try:
            extra = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError as exc:
            raise PortError(
                code="InvalidArgument",
                message=f"metadata is not valid JSON: {exc}",
                provider="platform",
                provider_code="E_DOC_METADATA",
            ) from exc
        if not isinstance(extra, dict):
            raise PortError(
                code="InvalidArgument",
                message="metadata must be a JSON object",
                provider="platform",
                provider_code="E_DOC_METADATA",
            )
        effective_name = filename or file.filename or "upload.bin"
        result = runtime.documents.ingest_stream(file.file, effective_name, extra)
        status_code = 200 if result.get("deduplicated") else 201
        return JSONResponse(status_code=status_code, content=result)

    @app.get("/documents")
    def list_documents(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        return runtime.documents.list(limit=limit, offset=offset)

    @app.get("/documents/{document_id}")
    def get_document(
        document_id: str,
        include: str | None = Query(default=None),
    ) -> dict[str, Any]:
        return runtime.documents.get(document_id, include_pages="pages" in (include or ""))

    @app.get("/documents/{document_id}/chunks")
    def document_chunks(
        document_id: str,
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        return runtime.documents.chunks(document_id, limit=limit, offset=offset)

    @app.get("/documents/{document_id}/source")
    def document_source(document_id: str) -> Response:
        from urllib.parse import quote

        data, meta = runtime.documents.source(document_id)
        content_type = meta.get("contentType", "application/octet-stream")
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(document_id)}",
            "X-Content-Sha256": meta.get("ref", {}).get("checksum", {}).get("value", ""),
            "X-Presign": "false",
        }
        return Response(content=data, media_type=content_type, headers=headers)

    @app.get("/imports/batches")
    def import_batches(limit: int = Query(default=5, ge=1, le=50)) -> dict[str, Any]:
        from .importer import batches_overview

        return batches_overview(runtime, limit)

    @app.get("/imports/items")
    def import_items(
        batch_id: str | None = Query(default=None),
        status: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> dict[str, Any]:
        from .importer import list_items

        return {"items": list_items(runtime, batch_id, status, limit)}

    # ---- S3 retrieval ----------------------------------------------------

    @app.post("/documents/{document_id}/index")
    def index_document(
        document_id: str,
        max_batches: int | None = Query(default=None, ge=0, le=100),
    ) -> dict[str, Any]:
        # maxBatches=N pauses between batches; re-POST with the same/None to resume
        # (the checkpoint + chunk_embedding rows make the resume idempotent).
        return runtime.search.index_document(document_id, max_batches=max_batches)

    @app.get("/search")
    def search(
        q: str = Query(min_length=1, max_length=2000),
        limit: int | None = Query(default=None, ge=1, le=100),
        mode: str = Query(default="hybrid"),
    ) -> dict[str, Any]:
        if mode not in ("hybrid", "vector", "lexical"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported search mode: {mode}",
                provider="platform",
                provider_code="E_SEARCH_MODE",
                details={"mode": mode, "allowed": ["hybrid", "vector", "lexical"]},
            )
        return runtime.search.hybrid_search(q, limit=limit, mode=mode)  # type: ignore[arg-type]

    # ---- Q4: ontology coverage pre-check ---------------------------------

    @app.get("/answerable")
    def answerable_get(
        q: str = Query(min_length=1, max_length=2000),
        ontologyVersion: str | None = Query(default=None),
        minCoverage: float | None = Query(default=None, ge=0.0, le=1.0),
        metricId: str | None = Query(default=None),
        intent: str | None = Query(default=None),
        layers: bool = Query(default=True),
    ) -> dict[str, Any]:
        return _qa_answerable(
            runtime,
            q,
            ontology_version=ontologyVersion,
            min_coverage=minCoverage,
            metric_id=metricId,
            intent_hint=intent,
            include_layers=layers,
        )

    @app.post("/answerable")
    def answerable_post(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        query = _qa_query(body)
        return _qa_answerable(
            runtime,
            query,
            ontology_version=body.get("ontologyVersion"),
            min_coverage=body.get("minCoverage"),
            metric_id=_qa_metric_id(body),
            intent_hint=body.get("intent"),
            include_layers=bool(body.get("layers", True)),
        )

    @app.get("/answer")
    def answer_get(
        q: str = Query(min_length=1, max_length=2000),
        ontologyVersion: str | None = Query(default=None),
        metricId: str | None = Query(default=None),
        topK: int = Query(default=5, ge=1, le=20),
        strategy: str = Query(default="lexical"),
        requestId: str | None = Query(default=None),
    ) -> dict[str, Any]:
        if strategy not in ("lexical", "vector", "hybrid"):
            raise PortError(
                code="InvalidArgument",
                message="strategy must be lexical/vector/hybrid",
                provider="platform",
                provider_code="E_ANSWER_STRATEGY_INVALID",
            )
        return _qa_answer(
            runtime,
            q,
            ontology_version=ontologyVersion,
            metric_id=metricId,
            top_k=topK,
            strategy=strategy,
            request_id=requestId,
        )

    @app.post("/answer")
    def answer_post(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        query = _qa_query(body)
        strategy = str(body.get("strategy") or "lexical")
        if strategy not in ("lexical", "vector", "hybrid"):
            raise PortError(
                code="InvalidArgument",
                message="strategy must be lexical/vector/hybrid",
                provider="platform",
                provider_code="E_ANSWER_STRATEGY_INVALID",
            )
        top_k = body.get("topK", 5)
        try:
            top_k = max(1, min(20, int(top_k)))
        except (TypeError, ValueError):
            top_k = 5
        return _qa_answer(
            runtime,
            query,
            ontology_version=body.get("ontologyVersion"),
            metric_id=_qa_metric_id(body),
            top_k=top_k,
            strategy=strategy,
            request_id=body.get("requestId"),
        )

    @app.get("/browse/facts")
    def browse_facts(
        table: str = Query(min_length=1, max_length=80),
        limit: int = Query(default=5, ge=1, le=20),
    ) -> dict[str, Any]:
        """Sample fact rows plus a resolvable source_ref for each row."""
        key_columns = source_ref._fact_key_columns(runtime.metadata, table)
        if key_columns is None:
            raise PortError(
                code="PermissionDenied",
                message="table is not a registered fact source",
                provider="platform",
                provider_code=source_ref.FORBIDDEN,
                details={"table": table},
            )
        rows = runtime.metadata.query(f"SELECT * FROM {table} LIMIT {int(limit)}")
        items = []
        for row in rows:
            key = {name: row[name] for name in key_columns}
            items.append(
                {
                    "row": source_ref.jsonable(row),
                    "sourceRef": source_ref.fact_row_descriptor(table, key),
                }
            )
        return {
            "table": table,
            "keyColumns": key_columns,
            "items": items,
            "count": len(items),
            "readOnly": True,
        }

    @app.get("/source/resolve")
    def source_resolve(ref: str = Query(min_length=1, max_length=2000)) -> dict[str, Any]:
        return source_ref.resolve(runtime.metadata, ref)

    # ---- v3 metric registry / publishability guard -----------------------

    @app.get("/metrics")
    def metrics_list(domain: str | None = None) -> dict[str, Any]:
        return {"metrics": runtime.metrics.list(domain=domain)}

    @app.get("/metrics/{metric_id}")
    def metric_get(metric_id: str) -> dict[str, Any]:
        return runtime.metrics.get(metric_id)

    @app.get("/metrics/{metric_id}/output")
    def metric_output(
        metric_id: str,
        internal: bool = False,
        compute: bool = False,
        as_of: date | None = Query(None, alias="asOf"),
        period_start: date | None = Query(None, alias="periodStart"),
        period_end: date | None = Query(None, alias="periodEnd"),
        entity_key: str | None = Query(None, alias="entityKey"),
        institution: str | None = None,
    ) -> dict[str, Any]:
        if not compute:
            return runtime.metrics.output(metric_id, internal=internal)
        return runtime.metrics.compute(
            metric_id,
            internal=internal,
            as_of=as_of,
            period_start=period_start,
            period_end=period_end,
            entity_key=entity_key,
            institution=institution,
        )

    # ---- read-only browse API (metrics / ontology / terms) ---------------

    @app.post("/metrics/{metric_id}/rules")
    def metric_rules(metric_id: str, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        executed = runtime.rules.execute(
            metric_id,
            list(body.get("facts") or []),
            as_of=body.get("asOf"),
        )
        # B-02: one PROV activity per triggered rule instance.
        prov = runtime.prov.record_rule_execution(
            metric_id,
            executed,
            actor=str(body.get("actor") or "system:rule-executor"),
            request_id=body.get("requestId"),
        )
        return {**executed, "prov": prov, "provGraph": prov_module.PROV_GRAPH}

    @app.post("/metrics/{metric_id}/decision")
    def metric_decision(
        metric_id: str, body: dict[str, Any] | None = Body(default=None)
    ) -> dict[str, Any]:
        """Record (or re-record) one口径判定. A re-judgement derives from the previous."""
        payload = body or {}
        return runtime.prov.record_decision(
            metric_id,
            actor=str(payload.get("actor") or "operator"),
            reason=payload.get("reason"),
            request_id=payload.get("requestId"),
        )

    # ---- B-02 PROV reverse lookups -------------------------------------

    @app.get("/prov/decisions")
    def prov_decisions(
        metricId: str = Query(min_length=1),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> dict[str, Any]:
        return runtime.prov.decision_history(metricId, limit=limit)

    @app.get("/prov/rules")
    def prov_rules(
        ruleId: str = Query(min_length=1),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> dict[str, Any]:
        return runtime.prov.rule_triggers(ruleId, limit=limit)

    @app.get("/prov/refusals")
    def prov_refusals(
        requestId: str | None = Query(default=None),
        query: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> dict[str, Any]:
        return runtime.prov.refusal(
            request_id=requestId, query=query, limit=limit
        )

    @app.get("/prov/verify")
    def prov_verify() -> dict[str, Any]:
        return {**runtime.prov.verify(), "separation": runtime.prov.separation()}

    @app.post("/prov/graph/guard")
    def prov_graph_guard(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        """Pure check: only <urn:platform:prov> may receive PROV triples."""
        return runtime.prov.guard(body.get("graph"))

    @app.delete("/prov/activities/{activity_id}")
    def prov_delete(activity_id: str) -> dict[str, Any]:
        runtime.prov.refuse_delete(activity_id)
        return {"ok": False}

    @app.get("/browse/metrics")
    def browse_metrics(
        domain: str | None = None,
        evidenceBasis: str | None = None,
        publishable: bool | None = None,
    ) -> dict[str, Any]:
        clauses: list[str] = []
        params: list[Any] = []
        if domain:
            clauses.append("domain = %s")
            params.append(domain)
        if evidenceBasis:
            clauses.append("evidence_basis = %s")
            params.append(evidenceBasis)
        if publishable is not None:
            clauses.append("publishable = %s")
            params.append(publishable)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = runtime.metadata.query(
            """
            SELECT metric_id, name_zh, domain, evidence_basis, publishable, inference,
                   formula_disabled, missing, evidence_status, note, definition_version,
                   metric_kind, formula_expr, numerator_agg, denominator_agg, window_kind,
                   min_window_days, grain, unit, effective_date, variant_of, output_mode,
                   display_name, definition, formula_text, denominator_text,
                   observation_period, granularity, provenance_label, rule_set_json
              FROM platform.metric_definition
            """
            + where
            + " ORDER BY metric_id",
            tuple(params),
        )
        items = [_metric_json(row) for row in rows]
        return {
            "items": items,
            "count": len(items),
            "source": "metric_definition",
            "filters": {
                "domain": domain,
                "evidenceBasis": evidenceBasis,
                "publishable": publishable,
            },
        }

    @app.get("/browse/metrics/{metric_id}")
    def browse_metric_detail(metric_id: str) -> dict[str, Any]:
        rows = runtime.metadata.query(
            """
            SELECT metric_id, name_zh, domain, evidence_basis, publishable, inference,
                   formula_disabled, missing, evidence_status, note, definition_version,
                   metric_kind, formula_expr, numerator_agg, denominator_agg, window_kind,
                   min_window_days, grain, unit, effective_date, variant_of, output_mode,
                   display_name, definition, formula_text, denominator_text,
                   observation_period, granularity, provenance_label, rule_set_json
              FROM platform.metric_definition
             WHERE metric_id = %s
            """,
            (metric_id,),
        )
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"metric not found: {metric_id}",
                provider="platform",
                provider_code="E_METRIC_NOT_FOUND",
                details={"metricId": metric_id},
            )
        return {
            "metric": _metric_json(rows[0], detail=True),
            "source": "metric_definition",
        }

    @app.get("/browse/ontology/tree")
    def browse_ontology_tree() -> dict[str, Any]:
        graph_iri = _current_graph(runtime)
        if not graph_iri:
            return {
                "pointer": None,
                "tree": [],
                "classes": [],
                "properties": [],
                "counts": {"classes": 0, "properties": 0},
            }
        class_rows = runtime.graph.query(
            f"""
            SELECT ?iri ?label ?parent FROM <{graph_iri}> WHERE {{
              {{ ?iri a <{_OWL}Class> }} UNION {{ ?iri a <{_RDFS}Class> }}
              OPTIONAL {{ ?iri <{_SKOS}prefLabel> ?pref }}
              OPTIONAL {{ ?iri <{_RDFS}label> ?rlab }}
              OPTIONAL {{ ?iri <{_RDFS}subClassOf> ?parent }}
              BIND(COALESCE(?pref, ?rlab, STR(?iri)) AS ?label)
            }}
            LIMIT 5000
            """
        ).get("bindings", [])
        prop_rows = runtime.graph.query(
            f"""
            SELECT ?iri ?label ?kind FROM <{graph_iri}> WHERE {{
              VALUES ?kind {{
                <{_OWL}ObjectProperty> <{_OWL}DatatypeProperty> <{_OWL}AnnotationProperty>
              }}
              ?iri a ?kind .
              OPTIONAL {{ ?iri <{_SKOS}prefLabel> ?pref }}
              OPTIONAL {{ ?iri <{_RDFS}label> ?rlab }}
              BIND(COALESCE(?pref, ?rlab, STR(?iri)) AS ?label)
            }}
            LIMIT 5000
            """
        ).get("bindings", [])

        classes: dict[str, dict[str, Any]] = {}
        for row in class_rows:
            iri = _binding(row, "iri")
            if not iri:
                continue
            entry = classes.setdefault(
                iri, {"iri": iri, "label": _binding(row, "label") or _local_name(iri), "parents": []}
            )
            parent = _binding(row, "parent")
            if parent and parent not in entry["parents"]:
                entry["parents"].append(parent)
        properties: dict[str, dict[str, Any]] = {}
        for row in prop_rows:
            iri = _binding(row, "iri")
            if not iri:
                continue
            properties.setdefault(
                iri,
                {
                    "iri": iri,
                    "label": _binding(row, "label") or _local_name(iri),
                    "kind": _local_name(_binding(row, "kind")),
                },
            )
        children: dict[str, list[dict[str, Any]]] = {}
        roots: list[dict[str, Any]] = []
        for entry in classes.values():
            parent = entry["parents"][0] if entry["parents"] else None
            if parent and parent in classes and parent != entry["iri"]:
                children.setdefault(parent, []).append(entry)
            else:
                roots.append(entry)

        def node(entry: dict[str, Any], seen: set[str]) -> dict[str, Any]:
            kids = []
            if entry["iri"] not in seen:
                seen.add(entry["iri"])
                kids = [node(child, seen) for child in sorted(
                    children.get(entry["iri"], []), key=lambda item: item["label"] or ""
                )]
            return {
                "iri": entry["iri"],
                "label": entry["label"],
                "parents": entry["parents"],
                "children": kids,
            }

        tree = [node(entry, set()) for entry in sorted(roots, key=lambda item: item["label"] or "")]
        return {
            "pointer": runtime.ontology.current(),
            "tree": tree,
            "classes": sorted(classes.values(), key=lambda item: item["label"] or ""),
            "properties": sorted(properties.values(), key=lambda item: item["label"] or ""),
            "counts": {"classes": len(classes), "properties": len(properties)},
        }

    @app.get("/browse/ontology/instances")
    def browse_ontology_instances(
        class_iri: str | None = Query(default=None, alias="class"),
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        target = _require_iri(class_iri, "class")
        graph_iri = _current_graph(runtime)
        if not graph_iri:
            return {
                "class": target,
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "pointer": None,
            }
        count_rows = runtime.graph.query(
            f"""
            SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {{
              GRAPH ?g {{ ?s a <{target}> }}
            }}
            """
        ).get("bindings", [])
        total = int(_binding(count_rows[0], "n") or 0) if count_rows else 0
        item_rows = runtime.graph.query(
            f"""
            SELECT DISTINCT ?s ?label ?g WHERE {{
              GRAPH ?g {{
                ?s a <{target}> .
                OPTIONAL {{ ?s <{_RDFS}label> ?label }}
              }}
            }}
            ORDER BY ?s
            LIMIT {limit} OFFSET {offset}
            """
        ).get("bindings", [])
        items = []
        for row in item_rows:
            iri = _binding(row, "s")
            if not iri:
                continue
            items.append(
                {
                    "iri": iri,
                    "label": _binding(row, "label") or _local_name(iri),
                    "graph": _binding(row, "g"),
                }
            )
        return {
            "class": target,
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "pointer": runtime.ontology.current(),
        }

    @app.get("/browse/triples")
    def browse_triples(
        subject: str | None = None,
        predicate: str | None = None,
        object: str | None = None,
        graph: str | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        subject_term = f"<{_require_iri(subject, 'subject')}>" if subject else "?s"
        predicate_term = f"<{_require_iri(predicate, 'predicate')}>" if predicate else "?p"
        if object:
            if object.startswith(("http://", "https://", "urn:")):
                object_term = f"<{_require_iri(object, 'object')}>"
            else:
                escaped = object.replace("\\", "\\\\").replace('"', '\\"')
                object_term = f'"{escaped}"'
        else:
            object_term = "?o"
        triple_pattern = f"{subject_term} {predicate_term} {object_term}"
        graph_pattern = (
            f"GRAPH <{_require_iri(graph, 'graph')}> {{ {triple_pattern} }} BIND(<{graph}> AS ?g)"
            if graph
            else f"GRAPH ?g {{ {triple_pattern} }}"
        )
        result = runtime.graph.query(
            f"""
            SELECT ?g ?s ?p ?o WHERE {{
              {graph_pattern}
            }}
            LIMIT {limit} OFFSET {offset}
            """
        )
        items = [
            {
                "graph": _binding(row, "g") or graph,
                "subject": _binding(row, "s") or subject,
                "predicate": _binding(row, "p") or predicate,
                # Fixed terms never bind a variable, so fall back to the input.
                "object": _binding(row, "o") or object,
            }
            for row in result.get("bindings", [])
        ]
        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "truncated": result.get("truncated", False),
        }

    @app.get("/browse/sparql")
    def browse_sparql(
        query: str = Query(min_length=1, max_length=5000),
    ) -> dict[str, Any]:
        if not _READ_ONLY_QUERY.match(query.strip()):
            raise _browse_error(
                "E_BROWSE_NOT_READ_ONLY",
                "only SELECT/ASK queries are allowed on the read-only browse endpoint",
                {"allowed": ["SELECT", "ASK"]},
            )
        result = runtime.graph.query(query)
        return {"readOnly": True, **result}

    @app.get("/browse/terms")
    def browse_terms() -> dict[str, Any]:
        graph_iri = _current_graph(runtime)
        if not graph_iri:
            return {
                "pointer": None,
                "entries": [],
                "classes": [],
                "counts": {"anchorClasses": 0, "altLabels": 0, "evidenced": 0, "inferred": 0},
            }
        rows = runtime.graph.query(
            f"""
            SELECT ?e ?c ?classLabel ?label ?status ?confidence ?guard ?canonical ?suppressed
              FROM <{graph_iri}> WHERE {{
              ?e a <{_TERM}TermEntry> ;
                 <{_TERM}forClass> ?c ;
                 <{_TERM}label> ?label .
              OPTIONAL {{ ?c <{_SKOS}prefLabel> ?classLabel }}
              OPTIONAL {{ ?e <{_TERM}status> ?status }}
              OPTIONAL {{ ?e <{_TERM}confidence> ?confidence }}
              OPTIONAL {{ ?e <{_TERM}guardRegex> ?guard }}
              OPTIONAL {{ ?c <{_TERM}canonicalFor> ?canonical }}
              OPTIONAL {{ ?c <{_TERM}suppressedSurface> ?suppressed }}
            }}
            """
        ).get("bindings", [])
        entries: dict[str, dict[str, Any]] = {}
        for row in rows:
            entry_iri = _binding(row, "e")
            if not entry_iri:
                continue
            entry = entries.setdefault(
                entry_iri,
                {
                    "entry": entry_iri,
                    "classIri": _binding(row, "c"),
                    "classLabel": _binding(row, "classLabel") or _local_name(_binding(row, "c")),
                    "label": _binding(row, "label"),
                    "status": _local_name(_binding(row, "status")),
                    "confidence": _local_name(_binding(row, "confidence")),
                    "guardRegex": _binding(row, "guard"),
                    "canonicalFor": [],
                    "suppressedSurface": [],
                },
            )
            for field, key in (("canonical", "canonicalFor"), ("suppressed", "suppressedSurface")):
                value = _binding(row, field)
                if value and value not in entry[key]:
                    entry[key].append(value)
        items = sorted(entries.values(), key=lambda item: (item["classIri"] or "", item["label"] or ""))
        classes: dict[str, dict[str, Any]] = {}
        for entry in items:
            class_iri = entry["classIri"]
            if not class_iri:
                continue
            group = classes.setdefault(
                class_iri,
                {"iri": class_iri, "label": entry["classLabel"], "aliases": []},
            )
            group["aliases"].append(entry["label"])
        evidenced = sum(1 for item in items if item["status"] == "evidenced")
        inferred = sum(1 for item in items if item["status"] == "inferred")
        return {
            "pointer": runtime.ontology.current(),
            "entries": items,
            "classes": sorted(classes.values(), key=lambda item: item["label"] or ""),
            "counts": {
                "anchorClasses": len(classes),
                "altLabels": len(items),
                "evidenced": evidenced,
                "inferred": inferred,
            },
        }

    # ---- B-06 data dictionary ---------------------------------------------

    def _catalog_service() -> catalog_module.CatalogService:
        return catalog_module.CatalogService(runtime)

    @app.get("/catalog/dictionaries")
    def catalog_dictionaries(
        catalog: str | None = None,
        schema: str | None = None,
        table: str | None = None,
        column: str | None = None,
        sourceKind: str | None = None,
        bindingMethod: str | None = None,
        q: str | None = None,
        limit: int = Query(default=20, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        for value, allowed, code in (
            (sourceKind, catalog_module.SOURCE_KINDS, "E_DICT_FILTER_INVALID"),
            (bindingMethod, catalog_module.BINDING_METHODS, "E_DICT_FILTER_INVALID"),
        ):
            if value and value not in allowed:
                raise _browse_error(
                    code,
                    f"unsupported filter value: {value}",
                    {"value": value, "allowed": list(allowed)},
                )
        filters = {
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "column": column,
            "sourceKind": sourceKind,
            "bindingMethod": bindingMethod,
            "q": q,
        }
        return _catalog_service().list(filters, limit=limit, offset=offset)

    @app.get("/catalog/dictionaries/{table}")
    def catalog_dictionary_table(
        table: str,
        catalog: str = "platform",
        schema: str = "platform",
    ) -> dict[str, Any]:
        return _catalog_service().table(table, catalog=catalog, schema=schema)

    @app.post("/catalog/dictionaries/refresh")
    def catalog_dictionaries_refresh(
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        payload = body or {}
        sources = payload.get("sources")
        if sources is not None and not isinstance(sources, list):
            raise _browse_error(
                "E_DICT_SOURCE_UNKNOWN",
                "sources must be a list of source kinds",
                {"allowed": list(catalog_module.SOURCE_KINDS)},
            )
        tables = payload.get("tables")
        if tables is not None and not isinstance(tables, list):
            raise _browse_error(
                "E_DICT_FILTER_INVALID",
                "tables must be a list of table names",
            )
        return _catalog_service().refresh(
            sources=sources,
            catalog=payload.get("catalog") or "platform",
            schema=payload.get("schema") or "platform",
            tables=tables,
        )

    # ---- S4 extraction ---------------------------------------------------

    @app.post("/documents/{document_id}/extract")
    def extract_document(
        document_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        mode = (body or {}).get("mode", "auto")
        if mode not in ("auto", "rules", "llm"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported extraction mode: {mode}",
                provider="platform",
                provider_code="E_EXTRACT_MODE",
                details={"mode": mode, "allowed": ["auto", "rules", "llm"]},
            )
        return runtime.extraction.extract_document(document_id, mode=mode)

    @app.get("/candidates")
    def list_candidates(
        state: str | None = Query(default=None),
        documentId: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        items = runtime.extraction.list_candidates(
            state=state, document_id=documentId, limit=limit
        )
        return {"candidates": items, "count": len(items)}

    @app.post("/candidates/{candidate_id}/approve")
    def approve_candidate(
        candidate_id: str,
        graph: str | None = Query(default=None),
    ) -> dict[str, Any]:
        return runtime.extraction.approve(candidate_id, graph=graph)

    @app.post("/candidates/{candidate_id}/reject")
    def reject_candidate(
        candidate_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        return runtime.extraction.reject(candidate_id, (body or {}).get("reason"))

    # ---- S8 fact governance ---------------------------------------------

    @app.get("/facts")
    def list_facts(
        state: str = Query(default="active"),
        subject: str | None = Query(default=None),
        predicate: str | None = Query(default=None),
        sourceDocumentId: str | None = Query(default=None),
        conflict: bool = Query(default=False),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        result = runtime.facts.list(
            state=state,
            subject=subject,
            predicate=predicate,
            source_document_id=sourceDocumentId,
            conflict_only=conflict,
            limit=limit,
        )
        result["conflicts"] = runtime.facts.conflicts()
        return result

    @app.get("/facts/conflicts")
    def fact_conflicts(includeAccepted: bool = Query(default=False)) -> dict[str, Any]:
        items = runtime.facts.conflicts(include_accepted=includeAccepted)
        for entry in items:
            for fact in entry.get("facts", []):
                candidate_id = (fact.get("source") or {}).get("candidateId")
                if not candidate_id:
                    continue
                rows = runtime.metadata.query(
                    """
                    SELECT e.chunk_id, c.text
                      FROM platform.extraction_candidate e
                      JOIN platform.document_chunk c ON c.chunk_id = e.chunk_id
                     WHERE e.candidate_id = %s
                    """,
                    (candidate_id,),
                )
                if rows:
                    fact["evidence"] = {
                        "chunkId": rows[0]["chunk_id"],
                        "text": rows[0]["text"][:240],
                    }
        pending = [item for item in items if item["pending"]]
        return {
            "conflicts": items, "count": len(items),
            "pending": len(pending), "includeAccepted": includeAccepted,
        }

    @app.post("/facts/conflicts/resolve")
    def resolve_conflict(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        missing = [
            key for key in ("subject", "predicate", "action")
            if not isinstance(body.get(key), str) or not body.get(key)
        ]
        if missing:
            raise PortError(
                code="InvalidArgument",
                message=f"missing adjudication fields: {missing}",
                provider="platform",
                provider_code="E_FACT_MISSING_FIELDS",
                details={"missing": missing},
            )
        return runtime.facts.resolve_conflict(
            subject=body["subject"],
            predicate=body["predicate"],
            action=body["action"],
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            keep=body.get("keep"),
            merged_object=body.get("mergedObject"),
            merged_object_kind=body.get("mergedObjectKind", "iri"),
            graph=body.get("graph"),
            source_document_id=body.get("sourceDocumentId"),
        )

    @app.post("/facts/conflicts/undo")
    def undo_conflict(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        return runtime.facts.undo_resolution(
            event_id=body.get("eventId"),
            subject=body.get("subject"),
            predicate=body.get("predicate"),
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            dry_run=bool(body.get("dryRun", False)),
        )

    @app.post("/facts/conflicts/unmerge")
    def unmerge_conflict(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        merge_event_id = body.get("eventId")
        if not isinstance(merge_event_id, int):
            raise PortError(
                code="InvalidArgument",
                message="unmerge requires an integer eventId",
                provider="platform",
                provider_code="E_FACT_UNDO_TARGET",
                details={"field": "eventId"},
            )
        return runtime.facts.unmerge(
            merge_event_id,
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            dry_run=bool(body.get("dryRun", False)),
        )

    @app.post("/facts/conflicts/batch")
    def batch_keep(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        return runtime.facts.batch_keep(
            keep=body.get("keep"),
            predicate=body.get("predicate"),
            subject=body.get("subject"),
            source_document_id=body.get("sourceDocumentId"),
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            dry_run=bool(body.get("dryRun", True)),
        )

    @app.post("/facts")
    def assert_fact(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        missing = [
            key for key in ("subject", "predicate", "object")
            if not isinstance(body.get(key), str) or not body.get(key)
        ]
        if missing:
            raise PortError(
                code="InvalidArgument",
                message=f"missing fact fields: {missing}",
                provider="platform",
                provider_code="E_FACT_MISSING_FIELDS",
                details={"missing": missing},
            )
        return runtime.facts.record(
            subject=body["subject"],
            predicate=body["predicate"],
            object_value=body["object"],
            object_kind=body.get("objectKind", "iri"),
            graph=body.get("graph", "urn:platform:graph:abox:main"),
            source_kind=body.get("sourceKind", "manual"),
            source_document_id=body.get("sourceDocumentId"),
            source_run_id=body.get("sourceRunId"),
            actor=body.get("actor", "api"),
        )

    @app.post("/facts/retract")
    def retract_facts(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        return runtime.facts.retract_by_source(
            document_id=body.get("sourceDocumentId"),
            run_id=body.get("sourceRunId"),
            reason=body.get("reason"),
            actor=body.get("actor", "api"),
        )

    @app.get("/facts/{fact_id}")
    def get_fact(fact_id: str) -> dict[str, Any]:
        fact = runtime.facts.get(fact_id)
        fact["events"] = runtime.facts.events(fact_id)
        return fact

    @app.post("/facts/{fact_id}/retract")
    def retract_fact(
        fact_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        return runtime.facts.retract(
            fact_id, (body or {}).get("reason"), (body or {}).get("actor", "api")
        )

    @app.post("/facts/{fact_id}/restore")
    def restore_fact(
        fact_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        return runtime.facts.restore(fact_id, (body or {}).get("actor", "api"))

    @app.get("/facts/{fact_id}/events")
    def fact_events(fact_id: str) -> dict[str, Any]:
        return {"factId": fact_id, "events": runtime.facts.events(fact_id)}

    @app.get("/facts/events/export")
    def export_fact_events(
        start: str | None = Query(default=None, alias="from"),
        end: str | None = Query(default=None, alias="to"),
        sourceDocumentId: str | None = Query(default=None),
    ) -> dict[str, Any]:
        from .fact_export import build_ndjson, export_meta, summarize

        data = runtime.facts.export_events(start, end, sourceDocumentId)
        conflicts = runtime.facts.conflicts(include_accepted=True)
        fact_ids = [
            item["factId"] for item in data["windowItems"] if item.get("factId")
        ]
        data["snapshot"] = runtime.facts.snapshot(fact_ids=fact_ids)
        meta = export_meta(
            data, data["snapshot"], runtime.facts.assertion_count(),
            {"from": start, "to": end, "sourceDocumentId": sourceDocumentId},
        )
        data["export"] = meta
        data["ndjson"] = build_ndjson(data["items"])
        data["snapshotNdjson"] = build_ndjson(data["snapshot"])
        data["markdown"] = summarize(data["items"], conflicts, meta)
        return data

    # ---- S11 T-Box change governance -------------------------------------

    @app.get("/ontology/versions")
    def ontology_versions(includeDeprecated: bool = False) -> dict[str, Any]:
        all_versions = runtime.ontology.list_versions()
        versions = all_versions if includeDeprecated else [
            item for item in all_versions if item["status"] != "deprecated"
        ]
        return {
            "items": versions,
            "count": len(versions),
            "total": len(all_versions),
            "deprecated": len(all_versions) - len(versions),
            "pointer": runtime.ontology.current(),
        }

    @app.get("/ontology/versions/{version_id}")
    def ontology_version(version_id: str) -> dict[str, Any]:
        result = runtime.ontology.get(version_id)
        result["graphTripleCount"] = runtime.ontology.graph_count(version_id)
        result["proposals"] = runtime.ontology.list_proposals(version_id)["items"]
        result["events"] = runtime.ontology.events(version_id)["items"]
        return result

    @app.get("/ontology/versions/{version_id}/diff")
    def ontology_diff(
        version_id: str,
        against: str | None = Query(default=None),
    ) -> dict[str, Any]:
        return runtime.ontology.diff(against, version_id)

    @app.get("/ontology/versions/{version_id}/export")
    def ontology_export(
        version_id: str,
        format: str = Query(default="turtle"),
    ) -> Response:
        exported = runtime.ontology.export_version(version_id, format)
        media = "text/turtle" if format == "turtle" else "application/n-quads"
        filename = f"{version_id}.{'ttl' if format == 'turtle' else 'nq'}"
        return Response(
            content=exported["content"],
            media_type=media,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/ontology/versions/{version_id}/propose")
    def ontology_propose(
        version_id: str,
        body: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        return runtime.ontology.propose(
            version_id,
            change_summary=body.get("changeSummary", ""),
            actor=body.get("actor", "operator"),
            against_version=body.get("againstVersion"),
        )

    @app.get("/ontology/proposals")
    def ontology_proposals(versionId: str | None = Query(default=None)) -> dict[str, Any]:
        return runtime.ontology.list_proposals(versionId)

    @app.post("/ontology/proposals/{proposal_id}/approve")
    def ontology_approve(
        proposal_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        payload = body or {}
        return runtime.ontology.approve(
            proposal_id, actor=payload.get("actor", "operator"), reason=payload.get("reason")
        )

    @app.post("/ontology/publish")
    def ontology_publish(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        version_id = body.get("versionId")
        if not isinstance(version_id, str) or not version_id:
            raise PortError(
                code="InvalidArgument",
                message="publish requires versionId",
                provider="platform",
                provider_code="E_ONTOLOGY_VERSION_REQUIRED",
            )
        return runtime.ontology.publish(
            version_id,
            proposal_id=body.get("proposalId"),
            acknowledge_breaking=bool(body.get("acknowledgeBreaking", False)),
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            expected_version_id=body.get("expectedVersionId"),
        )

    @app.post("/ontology/rollback")
    def ontology_rollback(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        version_id = body.get("versionId")
        if not isinstance(version_id, str) or not version_id:
            raise PortError(
                code="InvalidArgument",
                message="rollback requires versionId",
                provider="platform",
                provider_code="E_ONTOLOGY_VERSION_REQUIRED",
            )
        return runtime.ontology.rollback_to(
            version_id, actor=body.get("actor", "operator"), reason=body.get("reason"),
            expected_version_id=body.get("expectedVersionId"),
        )

    @app.get("/ontology/events")
    def ontology_events(
        versionId: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> dict[str, Any]:
        return runtime.ontology.events(versionId, limit=limit)

    @app.get("/ontology/verify")
    def ontology_verify() -> dict[str, Any]:
        result = runtime.ontology.verify_events()
        # B-02: same verification surface, second chain (prov_event).
        result["prov"] = runtime.prov.verify()
        return result

    # ---- governance console: controlled write endpoints -------------------
    # Every write reuses the ontology service method the CLI calls, so SHACL,
    # consistency, breaking and approval gates are unchanged. New code here is
    # limited to actor/reason validation and a read-only publish dry-run.

    @app.post("/governance/proposals")
    def governance_create_proposal(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        actor = _governance_actor(body)
        version_id = _governance_field(body, "versionId", "E_ONTOLOGY_VERSION_REQUIRED")
        summary = _governance_field(body, "changeSummary", "E_ONTOLOGY_SUMMARY_REQUIRED")
        against = body.get("againstVersion")
        if against is not None and not isinstance(against, str):
            raise _governance_rejection(
                "E_GOVERNANCE_BAD_FIELD", "againstVersion must be a string", "againstVersion"
            )
        result = runtime.ontology.propose(
            version_id, summary, actor=actor, against_version=against or None
        )
        return {**result, "current": runtime.ontology.current()}

    @app.get("/governance/proposals")
    def governance_list_proposals(
        versionId: str | None = Query(default=None),
        status: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> dict[str, Any]:
        data = runtime.ontology.list_proposals(versionId)
        statuses = {item["id"]: item["status"] for item in runtime.ontology.list_versions()}
        items = [
            {**item, "versionStatus": statuses.get(item["versionId"])}
            for item in data["items"]
            if status is None or item.get("status") == status
        ]
        return {
            "items": items[:limit],
            "count": len(items),
            "returned": len(items[:limit]),
            "current": runtime.ontology.current(),
        }

    @app.get("/governance/proposals/{proposal_id}")
    def governance_get_proposal(proposal_id: str) -> dict[str, Any]:
        proposal = runtime.ontology.get_proposal(proposal_id)
        version = runtime.ontology.get(proposal["versionId"])
        return {
            "proposal": proposal,
            "version": version,
            "versionStatus": version["status"],
            "current": runtime.ontology.current(),
            "diff": proposal.get("diff") or {},
            "impact": proposal.get("impact") or {},
        }

    @app.post("/governance/proposals/{proposal_id}/approve")
    def governance_approve_proposal(
        proposal_id: str, body: dict[str, Any] = Body(...)
    ) -> dict[str, Any]:
        actor = _governance_actor(body)
        reason = _governance_reason(body)
        return runtime.ontology.approve(proposal_id, actor=actor, reason=reason)

    @app.post("/governance/proposals/{proposal_id}/reject")
    def governance_reject_proposal(
        proposal_id: str, body: dict[str, Any] = Body(...)
    ) -> dict[str, Any]:
        actor = _governance_actor(body)
        reason = _governance_reason(body)
        proposal = runtime.ontology.get_proposal(proposal_id)
        status = proposal.get("status")
        if status == "published":
            raise PortError(
                code="Conflict",
                message=f"proposal {proposal_id} is already published",
                provider="platform",
                provider_code="E_ONTOLOGY_PROPOSAL_STATUS",
                details={"status": status},
            )
        if status != "proposed":
            raise PortError(
                code="Conflict",
                message=f"proposal {proposal_id} is {status}, not proposed",
                provider="platform",
                provider_code="E_ONTOLOGY_PROPOSAL_STATUS",
                details={"status": status},
            )
        version_id = proposal["versionId"]
        # Proposal.status admits only proposed/approved/published (V10), so a
        # rejection is recorded on the version (status='rejected') plus one
        # audit event. Re-approving the same proposal is the explicit recovery.
        with runtime.metadata.tx() as tx:
            tx.execute(
                "UPDATE platform.ontology_version SET status = 'rejected' "
                "WHERE version_id = %s AND status IN ('draft', 'proposed')",
                (version_id,),
            )
            runtime.ontology._append_event(
                tx, version_id, proposal_id, "rejected", actor, reason,
                {
                    "changeSummary": proposal.get("changeSummary"),
                    "previousStatus": status,
                },
            )
        return {
            "proposalId": proposal_id,
            "versionId": version_id,
            "status": "rejected",
            "versionStatus": "rejected",
            "rejectedBy": actor,
            "rejectedAt": datetime.now(timezone.utc).isoformat(),
        }

    @app.post("/governance/publish")
    def governance_publish(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        actor = _governance_actor(body)
        version_id = _governance_field(body, "versionId", "E_ONTOLOGY_VERSION_REQUIRED")
        proposal_id = body.get("proposalId") or None
        if proposal_id is not None and not isinstance(proposal_id, str):
            raise _governance_rejection(
                "E_GOVERNANCE_BAD_FIELD", "proposalId must be a string", "proposalId"
            )
        acknowledge = bool(body.get("acknowledgeBreaking", False))
        publish_existing = bool(body.get("publishExisting", False))
        if bool(body.get("dryRun", False)):
            return _governance_publish_dry_run(
                runtime, version_id, proposal_id, acknowledge, publish_existing
            )
        result = runtime.ontology.publish(
            version_id,
            proposal_id=proposal_id,
            acknowledge_breaking=acknowledge,
            actor=actor,
            reason=body.get("reason"),
            activate_existing=publish_existing,
            expected_version_id=body.get("expectedVersionId"),
        )
        return {"ok": True, **result}

    @app.get("/governance/rollback/plan")
    def governance_rollback_plan(versionId: str = Query(...)) -> dict[str, Any]:
        target = runtime.ontology.get(versionId)
        current = runtime.ontology.current()
        current_id = (current or {}).get("versionId")
        return {
            "target": target,
            "replacedVersion": current,
            "targetTriples": runtime.ontology.graph_count(versionId),
            "wouldChangePointer": bool(current_id and current_id != versionId),
        }

    @app.post("/governance/rollback-to")
    def governance_rollback_to(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        actor = _governance_actor(body)
        version_id = _governance_field(body, "versionId", "E_ONTOLOGY_VERSION_REQUIRED")
        before = runtime.ontology.current()
        result = runtime.ontology.rollback_to(
            version_id, actor=actor, reason=body.get("reason"),
            expected_version_id=body.get("expectedVersionId"),
        )
        return {
            "ok": True,
            "replacedVersionId": (before or {}).get("versionId"),
            "targetTriples": result.get("triples"),
            "publishedBy": actor,
            **result,
        }

    @app.post("/governance/rollback")
    def governance_rollback(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        actor = _governance_actor(body)
        version_id = _governance_field(body, "versionId", "E_ONTOLOGY_VERSION_REQUIRED")
        before = runtime.ontology.current()
        result = runtime.ontology.rollback(version_id)
        # Legacy rollback creates a new version and does not append audit
        # events; record the reason here so the console's audit view is complete.
        with runtime.metadata.tx() as tx:
            runtime.ontology._append_event(
                tx, result["id"], None, "rolled_back", actor, body.get("reason"),
                {
                    "mode": "new_version",
                    "rollbackOf": version_id,
                    "previous": (before or {}).get("versionId"),
                    "publishedBy": actor,
                },
            )
        return {
            "ok": True,
            "replacedVersionId": (before or {}).get("versionId"),
            "publishedBy": actor,
            **result,
        }

    @app.post("/governance/bundle/export")
    def governance_bundle_export(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        from .bundle import export_bundle

        actor = _governance_actor(body)
        out = _governance_field(body, "out", "E_BUNDLE_OUT_REQUIRED")
        tag = _governance_field(body, "tag", "E_BUNDLE_TAG_REQUIRED")
        result = export_bundle(runtime, out, tag, bool(body.get("includeBlobs", False)))
        return {"ok": True, "actor": actor, **result}

    @app.get("/governance/bundle/inspect")
    def governance_bundle_inspect(path: str = Query(...)) -> dict[str, Any]:
        from .bundle import verify_bundle

        manifest = verify_bundle(path)
        return {
            "ok": True,
            "path": path,
            "tag": manifest.get("tag"),
            "totals": manifest.get("totals") or {},
            "tbox": (manifest.get("source") or {}).get("tbox") or {},
            "files": len(manifest.get("files") or []),
        }

    @app.post("/governance/bundle/import")
    def governance_bundle_import(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        from .bundle import import_bundle

        actor = _governance_actor(body)
        path = _governance_field(body, "bundle", "E_BUNDLE_PATH_REQUIRED")
        database = body.get("database") or "platform_restore_test"
        if not isinstance(database, str) or not database.strip():
            raise _governance_rejection(
                "E_GOVERNANCE_BAD_FIELD", "database must be a non-empty string", "database"
            )
        result = import_bundle(
            runtime.bundle,
            path,
            database=database.strip(),
            replace=bool(body.get("replace", False)),
            keep_db_on_failure=bool(body.get("keepDbOnFailure", False)),
        )
        return {"actor": actor, **result}

    @app.get("/governance/events")
    def governance_events(
        versionId: str | None = Query(default=None),
        action: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> dict[str, Any]:
        data = runtime.ontology.events(versionId, limit=limit)
        categories = {"published": 0, "rolled_back": 0, "superseded": 0, "other": 0}
        items = []
        for item in data["items"]:
            category = (
                item["action"]
                if item["action"] in ("published", "rolled_back", "superseded")
                else "other"
            )
            if action is not None and item["action"] != action:
                continue
            items.append({**item, "category": category})
            categories[category] += 1
        return {
            "items": items,
            "count": len(items),
            "categories": categories,
            "filter": {"versionId": versionId, "action": action},
            "current": runtime.ontology.current(),
        }

    # ---- G-01: versioned TTL import --------------------------------------

    @app.post("/ontology/import")
    @app.post("/api/ontology/import")
    async def ontology_import(request: Request) -> dict[str, Any]:
        """G-01 first half: parse the uploaded ontology and return real counts.

        Boundary of this slice: no owl:imports closure, no SHACL, no publish.
        Every response therefore carries usable=false plus an explicit reason.
        Input: multipart `file` + `targetNamespace`/`changeSummary`/`author`,
        or JSON `{content|contentBase64, ...}`, or a raw TTL body.
        """
        ctype = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
        payload: dict[str, Any] = {}
        raw: bytes | None = None
        filename = ""
        if ctype == "multipart/form-data":
            form = await request.form()
            upload = form.get("file")
            if upload is None or not hasattr(upload, "read"):
                raise PortError(
                    code="InvalidArgument",
                    message="multipart import requires a `file` part",
                    provider="platform",
                    provider_code="E_ONTOLOGY_IMPORT_SOURCE",
                )
            filename = str(getattr(upload, "filename", "") or "")
            raw = await upload.read()
            payload = {
                key: form.get(key)
                for key in ("targetNamespace", "changeSummary", "author", "format")
                if form.get(key)
            }
        else:
            body = await request.body()
            if ctype == "application/json":
                try:
                    payload = json.loads(body.decode("utf-8") or "{}")
                except ValueError as exc:
                    raise PortError(
                        code="InvalidArgument",
                        message=f"import body is not valid JSON: {exc}",
                        provider="platform",
                        provider_code="E_ONTOLOGY_IMPORT_BODY",
                    ) from exc
            elif body:
                raw = body

        def _option(name: str, default: Any = None) -> Any:
            if name in payload:
                return payload[name]
            value = request.query_params.get(name)
            return default if value is None else value

        if raw is None and isinstance(payload.get("content"), str):
            raw = payload["content"].encode("utf-8")
        if raw is None and payload.get("contentBase64"):
            import base64

            try:
                raw = base64.b64decode(payload["contentBase64"])
            except ValueError as exc:
                raise PortError(
                    code="InvalidArgument",
                    message=f"contentBase64 is not valid base64: {exc}",
                    provider="platform",
                    provider_code="E_ONTOLOGY_IMPORT_BODY",
                ) from exc
        if raw is None:
            raise PortError(
                code="InvalidArgument",
                message="import requires a `file` upload or content in the body",
                provider="platform",
                provider_code="E_ONTOLOGY_IMPORT_SOURCE",
            )

        rdf_format = str(_option("format") or import_format_from_name(filename))
        result, merged = build_import_document(
            raw,
            rdf_format=rdf_format,
            target_namespace=_option("targetNamespace") or _option("namespace"),
            author=_option("author"),
            change_summary=_option("changeSummary"),
            shapes_dir=runtime.config.reasoning.shapes_dir,
            consistency_checker=runtime.reasoning.check_consistency,
            shapes_provider=runtime.shapes.load_deployed,
        )
        return persist_import(result, merged, raw, runtime.metadata, runtime.graph)

    @app.get("/ontology/imports/{import_id}")
    @app.get("/api/ontology/imports/{import_id}")
    def ontology_import_record(import_id: str) -> dict[str, Any]:
        record = get_import_record(runtime.metadata, import_id)
        if record is None:
            raise PortError(
                code="NotFound",
                message=f"import {import_id} not found",
                provider="platform",
                provider_code="E_ONTOLOGY_IMPORT_NOT_FOUND",
            )
        return record

    @app.post("/ontology/imports/{import_id}/publish")
    @app.post("/api/ontology/imports/{import_id}/publish")
    def ontology_import_publish(
        import_id: str, body: dict[str, Any] | None = Body(default=None)
    ) -> dict[str, Any]:
        payload = body or {}
        dry_run = payload.get("dryRun", True)
        if not isinstance(dry_run, bool):
            raise PortError(
                code="InvalidArgument",
                message=f"dryRun must be a boolean, got {type(dry_run).__name__}",
                provider="platform",
                provider_code="E_ONTOLOGY_IMPORT_BODY",
            )
        return publish_import(
            runtime.metadata,
            runtime.graph,
            runtime.objects,
            runtime.ontology,
            import_id,
            dry_run=dry_run,
            actor=str(payload.get("actor") or "operator"),
            change_summary=payload.get("changeSummary"),
            acknowledge_breaking=bool(payload.get("acknowledgeBreaking", False)),
            abox_graphs=runtime.config.reasoning.abox_graphs,
            publish_existing=bool(payload.get("publishExisting", False)),
        )

    @app.put("/ontology/shapes")
    @app.put("/api/ontology/shapes")
    async def ontology_shapes_deploy(
        request: Request,
        namespace: str = Query(...),
        shapesId: str | None = Query(default=None),
    ) -> dict[str, Any]:
        raw = await request.body()
        rdf_format = "turtle"
        actor = "operator"
        body_shapes_id: str | None = None
        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                payload = json.loads(raw or b"{}")
            except ValueError as exc:
                raise PortError(
                    code="InvalidArgument",
                    message=f"shapes body is not valid JSON: {exc}",
                    provider="platform",
                    provider_code="E_SHAPES_PARSE",
                ) from exc
            raw = str(payload.get("content") or "").encode("utf-8")
            rdf_format = str(payload.get("format") or "turtle")
            body_shapes_id = payload.get("shapesId")
            actor = str(payload.get("actor") or "operator")
        if not raw.strip():
            raise PortError(
                code="InvalidArgument",
                message="shapes deployment requires a TTL body",
                provider="platform",
                provider_code="E_SHAPES_SOURCE",
            )
        return runtime.shapes.deploy(
            namespace,
            raw,
            rdf_format=rdf_format,
            shapes_id=shapesId or body_shapes_id,
            actor=actor,
        )

    @app.get("/ontology/shapes")
    @app.get("/api/ontology/shapes")
    def ontology_shapes_list() -> dict[str, Any]:
        return runtime.shapes.list()

    # ---- GSP write guard (G-01: no GSP bypass) ---------------------------

    GSP_PROTECTED = (
        "urn:platform:graph:tbox:",
        "urn:fsldm:",
        "https://w3id.org/fsldm/",
    )

    @app.api_route("/store", methods=["PUT", "POST", "DELETE"])
    @app.api_route("/api/store", methods=["PUT", "POST", "DELETE"])
    def gsp_write(graph: str | None = Query(default=None)) -> JSONResponse:
        """Reject Graph Store Protocol writes.

        T-Box state must move through /ontology/import + publish gates. Allowing
        a write here would be a governance bypass, so every GSP write is refused
        with a stable code instead of being forwarded to Oxigraph.
        """
        target = graph or ""
        protected = any(target.startswith(prefix) for prefix in GSP_PROTECTED)
        raise PortError(
            code="PermissionDenied",
            message=(
                "GSP writes are disabled; ontology state must go through "
                "/ontology/import and the publish gates"
            ),
            provider="platform",
            provider_code="E_GSP_GOVERNANCE_REQUIRED",
            details={"graph": target or None, "protectedGraph": protected},
        )

    # ---- S5 reasoning + SHACL -------------------------------------------

    @app.post("/reasoning/materialize")
    def materialize(body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
        payload = body or {}
        profile = payload.get("profile")
        if profile is not None and profile not in ("EL", "OWL2EL"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported reasoning profile: {profile}",
                provider="platform",
                provider_code="E_REASONING_PROFILE",
                details={"profile": profile, "allowed": ["EL", "OWL2EL"]},
            )
        abox_graphs = payload.get("aboxGraphs")
        if abox_graphs is not None and (
            not isinstance(abox_graphs, list)
            or not abox_graphs
            or not all(isinstance(item, str) and item.startswith("urn:platform:") for item in abox_graphs)
        ):
            raise PortError(
                code="InvalidArgument",
                message="aboxGraphs must be a non-empty list of urn:platform: IRIs",
                provider="platform",
                provider_code="E_REASONING_ABOX_GRAPHS",
            )
        return runtime.reasoning.materialize(
            profile=profile, force=bool(payload.get("force", False)),
            abox_graphs=abox_graphs,
        )

    @app.get("/reasoning/status")
    def reasoning_status() -> dict[str, Any]:
        return runtime.reasoning.status()

    @app.post("/validation/run")
    def run_validation(body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
        target = (body or {}).get("graph", "abox")
        if not isinstance(target, str):
            raise PortError(
                code="InvalidArgument",
                message="validation graph must be a string",
                provider="platform",
                provider_code="E_VALIDATE_TARGET",
            )
        return runtime.reasoning.validate(target)

    @app.get("/validation/shapes")
    def validation_shapes() -> dict[str, Any]:
        try:
            return {
                "shapesDir": runtime.config.reasoning.shapes_dir,
                "files": [p.name for p in runtime.validator.shapes()],
                "shapesVersion": runtime.validator.shapes_version(),
                # G-03: which namespace, which shape set, which version.
                "namespaces": runtime.validator.registries(),
            }
        except OSError as exc:
            raise PortError(
                code="Unavailable",
                message=f"cannot read shapes directory: {exc}",
                provider="pyshacl",
                provider_code="E_SHACL_SHAPES_MISSING",
            ) from exc

    @app.post("/context/resolve")
    def context_resolve(body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
        return runtime.context.resolve(body or {})

    # ---- S7 Web UI views (read-only; no framework, no build chain) -------

    @app.get("/ui/api/overview")
    def ui_overview() -> dict[str, Any]:
        return webui.overview(runtime)

    @app.get("/ui/api/ontology")
    def ui_ontology() -> dict[str, Any]:
        return webui.ontology(runtime)

    @app.get("/ui/api/entities")
    def ui_entities(
        q: str = Query(default="", max_length=200),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, Any]:
        return webui.entities(runtime, q, limit=limit)

    @app.get("/ui/api/neighbors")
    def ui_neighbors(
        iri: str = Query(min_length=1, max_length=2000),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        return webui.neighbors(runtime, iri, limit=limit)

    @app.get("/ui/api/entity")
    def ui_entity(
        iri: str = Query(min_length=1, max_length=2048),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        """B-03 read-only entity detail: classes, required props, neighbours, badge."""
        return entity_view.entity_detail(runtime, iri, limit=limit)

    @app.get("/ui/api/candidates")
    def ui_candidates(
        state: str | None = Query(default="pending"),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        return webui.candidates_with_evidence(runtime, state=state, limit=limit)

    @app.get("/ui/api/search")
    def ui_search(
        q: str = Query(min_length=1, max_length=2000),
        topK: int = Query(default=10, ge=1, le=50),
        tokenBudget: int = Query(default=2048, ge=32, le=8192),
        strategy: str = Query(default="hybrid"),
    ) -> dict[str, Any]:
        if strategy not in ("hybrid", "vector", "lexical"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported strategy: {strategy}",
                provider="platform",
                provider_code="E_CONTEXT_STRATEGY",
                details={"strategy": strategy},
            )
        return runtime.context.resolve(
            {"query": q, "topK": topK, "tokenBudget": tokenBudget, "strategy": strategy}
        )

    @app.get("/")
    def ui_root() -> Any:
        if (WEB_DIR / "index.html").is_file():
            return RedirectResponse(url="/ui/")
        return {"status": "ok", "ui": "not bundled", "webDir": str(WEB_DIR)}

    if WEB_DIR.is_dir():
        app.mount("/ui", StaticFiles(directory=str(WEB_DIR), html=True), name="ui")

    @app.get("/status")
    def status() -> dict[str, Any]:
        disk: dict[str, Any] = {}
        try:
            usage = shutil.disk_usage(runtime.config.storage.root)
            disk = {
                "free_pct": round((usage.free / usage.total) * 100, 2) if usage.total else 0,
                "free_bytes": usage.free,
                "total_bytes": usage.total,
            }
        except OSError as exc:
            disk = {"error": str(exc)}

        counts: dict[str, Any] = {}
        try:
            counts["blobs"] = runtime.metadata.count_blobs()
            counts["refs"] = runtime.metadata.count_refs()
        except Exception as exc:
            counts["error"] = str(exc)

        ontology: dict[str, Any] = {}
        try:
            pointer = runtime.ontology.current()
            versions = runtime.ontology.list_versions()
            ontology = {
                "pointer": pointer,
                "versions": len(versions),
                "activeVersions": sum(1 for v in versions if v["status"] != "deprecated"),
                "statuses": {v["id"]: v["status"] for v in versions},
            }
        except Exception as exc:
            ontology = {"error": str(exc)}

        triples: int | None = None
        try:
            result = runtime.graph.query(
                "SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }"
            )
            if result["bindings"]:
                triples = int(result["bindings"][0]["values"]["n"]["value"])
        except PortError:
            triples = None

        documents_counts: dict[str, Any] = {}
        try:
            documents_counts = runtime.documents.counts()
        except Exception as exc:
            documents_counts = {"error": str(exc)}

        search_counts: dict[str, Any] = {}
        try:
            search_counts = runtime.search.counts()
        except Exception as exc:
            search_counts = {"error": str(exc)}

        extraction_counts: dict[str, Any] = {}
        try:
            extraction_counts = runtime.extraction.counts()
        except Exception as exc:
            extraction_counts = {"error": str(exc)}

        reasoning_status: dict[str, Any] = {}
        try:
            reasoning_status = runtime.reasoning.status()
        except Exception as exc:
            reasoning_status = {"error": str(exc)}

        return {
            "status": "ok",
            "version": __version__,
            "slice": "S13",
            "mode": runtime.config.mode,
            "runtime_mode": runtime.config.runtime.mode,
            "config_version": runtime.config.config_version,
            "config_file": str(runtime.bundle.path),
            "providers": {
                "metadata": runtime.metadata.manifest().__dict__,
                "graph": runtime.graph.manifest().__dict__,
                "object": runtime.objects.manifest().__dict__,
                "ontology": runtime.ontology.manifest().__dict__,
                "parser": runtime.parser.manifest().__dict__,
                "documents": runtime.documents.manifest().__dict__,
                "embedding": runtime.embedding.manifest().__dict__,
                "vectors": runtime.vectors.manifest().__dict__,
                "search_index": runtime.search_index.manifest().__dict__,
                "search": runtime.search.manifest().__dict__,
                "llm": runtime.llm.manifest().__dict__,
                "extraction": runtime.extraction.manifest().__dict__,
                "reasoner": runtime.reasoner.manifest().__dict__,
                "consistency_reasoner": (
                    runtime.consistency_reasoner.manifest().__dict__
                    if runtime.consistency_reasoner is not None
                    else None
                ),
                "validation": runtime.validator.manifest().__dict__ if hasattr(runtime.validator, "manifest") else {},
                "reasoning": runtime.reasoning.manifest().__dict__,
                "context": runtime.context.manifest().__dict__,
                "answerability": runtime.answerable.manifest().__dict__,
                "facts": runtime.facts.manifest().__dict__,
                "secrets": runtime.secrets.manifest().__dict__,
            },
            "not_implemented": {
                name: port.manifest().notes for name, port in runtime.placeholders.items()
            },
            "degraded": runtime.degraded,
            "storage": {"disk": disk, "counts": counts},
            "graph": {"triples": triples},
            "documents": documents_counts,
            "search": search_counts,
            "extraction": extraction_counts,
            "reasoning": reasoning_status,
            "self_check": [item.to_dict() for item in checks],
            "notes": [
                "no auth, no metrics/tracing, no job queue or event bus",
                "OCR is disabled; scanned PDFs are returned as degraded with NO_OCR_ENABLED",
                "embedding unavailable -> hybrid search returns lexical results with degraded=true",
                "extraction candidates are approval-gated: nothing is written to the graph before approval",
                "llm is OpenAI-compatible and optional: auto mode degrades to rules when unconfigured",
                "reasoning materializes into a separate graph; source graphs are never overwritten",
                "SHACL without shapes is an explicit Unsupported error, never a silent pass",
            ],
        }

    # --- G1 ontology routes ---
    # Ownership: ontology governance line (O-02..O-06). Append-only block: no
    # existing handler or module-level helper above is modified. Everything here
    # is additive and read/write-scoped to governance; publish semantics are
    # untouched except that publish now also writes lifecycle transitions.

    @app.post("/governance/proposals/{proposal_id}/review")
    def governance_proposal_review(
        proposal_id: str,
        body: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        """O-02: proposed -> review. Actor and reason are mandatory."""
        actor = _governance_actor(body)
        reason = _governance_reason(body)
        return runtime.ontology.review(proposal_id, actor=actor, reason=reason)

    @app.get("/governance/proposals/{proposal_id}/transitions")
    def governance_proposal_transitions(
        proposal_id: str,
        limit: int = Query(200, ge=1, le=2000),
    ) -> dict[str, Any]:
        return runtime.ontology.transitions(proposal_id=proposal_id, limit=limit)

    @app.get("/governance/versions/{version_id}/transitions")
    def governance_version_transitions(
        version_id: str,
        limit: int = Query(200, ge=1, le=2000),
    ) -> dict[str, Any]:
        return runtime.ontology.transitions(version_id=version_id, limit=limit)

    @app.get("/health/ontology-diff/flow")
    def health_ontology_diff_flow(
        versionId: str | None = Query(None),
        proposalId: str | None = Query(None),
        limit: int = Query(200, ge=1, le=2000),
    ) -> dict[str, Any]:
        """O-02: explicit lifecycle view. /health/ontology-diff also embeds
        the same block under `lifecycle`."""
        if proposalId:
            payload = runtime.ontology.transitions(proposal_id=proposalId, limit=limit)
            payload["filter"] = {"proposalId": proposalId, "versionId": versionId}
            return payload
        if not versionId:
            pointer = healthboard._pointer(runtime)
            versionId = (pointer or {}).get("versionId")
        if not versionId:
            return {
                "items": [],
                "count": 0,
                "empty": True,
                "emptyReason": "未指定 versionId，且 tbox/current 指针不存在",
                "readOnly": True,
            }
        from .ontology_lifecycle import flow

        payload = flow(runtime.metadata, versionId)
        payload["filter"] = {"proposalId": proposalId, "versionId": versionId}
        return payload

    # ---- O-03 change impact analysis (read-only) -------------------------

    @app.get("/ontology/impact")
    def ontology_impact(
        from_: str | None = Query(None, alias="from"),
        to: str | None = Query(None),
        sample: int = Query(5, ge=0, le=10),
    ) -> dict[str, Any]:
        from . import impact as impact_module

        return impact_module.analyze(runtime, from_, to, sample)

    @app.get("/ontology/impact/export")
    def ontology_impact_export(
        from_: str | None = Query(None, alias="from"),
        to: str | None = Query(None),
        sample: int = Query(5, ge=0, le=10),
        format: str = Query("markdown"),
    ) -> Response:
        from . import impact as impact_module

        report = impact_module.analyze(runtime, from_, to, sample)
        filename, media_type, body = impact_module.export(report, format)
        return Response(
            content=body,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # ---- O-04 publish gate evidence packs (read + download) -------------

    @app.get("/ontology/evidence")
    def ontology_evidence_list(
        versionId: str | None = Query(None),
        verdict: str | None = Query(None),
        limit: int = Query(50, ge=1, le=500),
    ) -> dict[str, Any]:
        from . import evidence as evidence_module

        return evidence_module.list_packs(
            runtime.metadata, version_id=versionId, verdict=verdict, limit=limit
        )

    @app.get("/ontology/evidence/{evidence_id}/download")
    def ontology_evidence_download(evidence_id: str) -> Response:
        from . import evidence as evidence_module
        import json as _json

        pack = evidence_module.fetch(runtime.metadata, evidence_id)
        evidence_module.check_download(pack)
        path = evidence_module.materialize(runtime.config.storage.root, pack)
        runtime.metadata.execute(
            "UPDATE platform.ontology_evidence SET path = %s WHERE evidence_id = %s",
            (str(path), evidence_id),
        )
        body = _json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True)
        return Response(
            content=body,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{evidence_id}.json"',
                "X-Evidence-SHA256": str(pack.get("sha256") or ""),
                "X-Evidence-Path": str(path),
            },
        )

    # ---- O-05 term-layer governance (coverage / diff / import check) -----

    @app.get("/ontology/terms/coverage")
    def ontology_terms_coverage(
        expectConcepts: int | None = Query(None, ge=0),
        expectAliases: int | None = Query(None, ge=0),
    ) -> dict[str, Any]:
        from . import termgov

        return termgov.graph_coverage(
            runtime, expect_concepts=expectConcepts, expect_aliases=expectAliases
        )

    @app.post("/ontology/terms/diff")
    def ontology_terms_diff(
        body: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        from . import termgov

        content = str(body.get("content") or "")
        if not content.strip():
            raise PortError(
                code="InvalidArgument", message="body.content is required (SKOS text)",
                provider="platform", provider_code="E_TERM_CONTENT_REQUIRED",
            )
        report = termgov.diff_against_graph(
            runtime, content, str(body.get("format") or "turtle"),
            source_name=body.get("sourceName"),
        )
        termgov.record_check(runtime.metadata, report, source_kind="import",
                             version_id=(body.get("versionId")), actor="operator")
        return report

    @app.post("/ontology/terms/import")
    def ontology_terms_import(
        body: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        from . import termgov

        content = str(body.get("content") or "")
        if not content.strip():
            raise PortError(
                code="InvalidArgument", message="body.content is required (SKOS text)",
                provider="platform", provider_code="E_TERM_CONTENT_REQUIRED",
            )
        report = termgov.diff_against_graph(
            runtime, content, str(body.get("format") or "turtle"),
            source_name=body.get("sourceName"),
        )
        termgov.record_check(runtime.metadata, report, source_kind="import",
                             version_id=body.get("versionId"), actor="operator")
        if bool(body.get("dryRun", True)):
            return {"dryRun": True, "diff": report}
        return termgov.record_import(runtime.metadata, report,
                                    source_name=body.get("sourceName"))

    @app.get("/ontology/terms/checks")
    def ontology_terms_checks(limit: int = Query(50, ge=1, le=500)) -> dict[str, Any]:
        from . import termgov

        return termgov.list_checks(runtime.metadata, limit=limit)

    # ---- O-06 health snapshot comparison --------------------------------

    @app.get("/health/ontology-snapshot")
    def health_ontology_snapshot(
        from_: str | None = Query(None, alias="from"),
        to: str | None = Query(None),
    ) -> dict[str, Any]:
        return healthboard.snapshot_compare(runtime, from_, to)
    # --- end G1 ---

    # --- G2 metrics-core routes ---
    @app.get("/metrics/{metric_id}/compute")
    def metric_compute(
        metric_id: str,
        internal: bool = False,
        as_of: date | None = Query(None, alias="asOf"),
        period_start: date | None = Query(None, alias="periodStart"),
        period_end: date | None = Query(None, alias="periodEnd"),
        data_source: str = Query("fixture", alias="dataSource"),
    ) -> dict[str, Any]:
        """Scheme-A compute: direct fact-table aggregation, no observation cache.

        Non-executable metrics return a stable provider code plus the missing
        reason (E_METRIC_NOT_STRUCTURALLY_COMPUTABLE / E_METRIC_BINDING_MISSING /
        E_METRIC_RULE_SET_ONLY / E_METRIC_WINDOW_INSUFFICIENT ...), never 0.
        """
        from .metric_compiler import MetricCompiler

        start, end = period_start, period_end
        if as_of is not None and start is None and end is None:
            start = end = as_of
        compiler = MetricCompiler(runtime.metadata)
        result = compiler.execute(
            metric_id, start=start, end=end, internal=internal, data_source=data_source
        )
        return {
            **result,
            "rowCount": len(result["rows"]),
            "computedAt": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/metrics-readiness")
    def metrics_readiness(
        status: str | None = None,
        kind: str | None = None,
        format: str = "json",
    ) -> Any:
        """M-06 ledger export. registered_only is never reported as executable."""
        if status is not None and status not in (
            "executed", "registered_only", "not_executable"
        ):
            raise _browse_error(
                "E_METRIC_READINESS_STATUS_INVALID",
                "status must be executed|registered_only|not_executable",
                {"status": status},
            )
        if kind is not None and kind not in ("partial", "rule"):
            raise _browse_error(
                "E_METRIC_READINESS_KIND_INVALID",
                "kind must be partial|rule",
                {"kind": kind},
            )
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            clauses.append("status = %s")
            params.append(status)
        if kind is not None:
            clauses.append("item_kind = %s")
            params.append(kind)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = runtime.metadata.query(
            "SELECT item_kind, metric_id, status, reason, detail, evidence_ref,"
            f" checked_at FROM platform.metric_readiness{where}"
            " ORDER BY item_kind, metric_id",
            tuple(params),
        )
        items = [
            {
                "itemKind": row["item_kind"],
                "metricId": row["metric_id"],
                "status": row["status"],
                "reason": row["reason"],
                "detail": row["detail"],
                "evidenceRef": row["evidence_ref"],
                "checkedAt": str(row["checked_at"]),
            }
            for row in rows
        ]
        counts_rows = runtime.metadata.query(
            "SELECT status, COUNT(*) AS n FROM platform.metric_readiness GROUP BY status"
        )
        counts = {row["status"]: int(row["n"]) for row in counts_rows}
        for key in ("executed", "registered_only", "not_executable"):
            counts.setdefault(key, 0)
        if format == "csv":
            import csv
            import io

            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(
                ["item_kind", "metric_id", "status", "reason", "evidence_ref", "checked_at"]
            )
            for item in items:
                writer.writerow(
                    [
                        item["itemKind"], item["metricId"], item["status"],
                        item["reason"], item["evidenceRef"], item["checkedAt"],
                    ]
                )
            suffix = status or kind or "all"
            return Response(
                content=buffer.getvalue(),
                media_type="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition":
                        f'attachment; filename="metric-readiness-{suffix}.csv"'
                },
            )
        return {
            "items": items,
            "count": len(items),
            "counts": counts,
            "filter": {"status": status, "kind": kind},
        }
    # --- end G2 ---

    # --- G3 metrics-report routes ---
    # M-02: 对外出数清单与 publishable 治理。清单 100% 来自 platform.metric_definition，
    # 不做手工维护；可算性直接采用库内 computability_tier，且“可算”不等于“已有观测值”。

    _G3_METRIC_SQL = """
        SELECT metric_id, name_zh, display_name, domain, evidence_basis, publishable, inference,
               formula_disabled, missing, evidence_status, note, definition_version, metric_kind,
               formula_expr, formula_text, numerator_agg, denominator_agg, window_kind,
               min_window_days, observation_period, grain, granularity, unit, effective_date,
               variant_of, output_mode, provenance_label, computability_tier
          FROM platform.metric_definition
         ORDER BY metric_id
    """

    _G3_TIER_LABELS = {
        "structurally_computable": "结构性可算（需事实与观测）",
        "blocked_semantics": "语义阻断",
        "blocked_external": "对外阻断",
    }
    _G3_TIER_TONES = {
        "structurally_computable": "ok",
        "blocked_semantics": "warn",
        "blocked_external": "bad",
    }
    _G3_GAP_LABELS = {
        "regulatory_source": "缺监管原文",
        "source": "缺事实来源",
        "entity": "缺实体绑定",
    }

    # M-05: E1 25 条行业公式（来源：doc/_fsldm/12-口径终裁-v9.md §1）。
    # 该清单只用于“声明核对”，不参与清单取数；清单仍逐条读库。
    _G3_E1_SOURCE = "doc/_fsldm/12-口径终裁-v9.md §1"
    _G3_INDUSTRY_NOTICE = "内部基线、不外报"
    _G3_E1_INDUSTRY_IDS = (
        "FIN-BANK-002",
        "FIN-BANK-005",
        "FIN-BANK-017",
        "FIN-BANK-018",
        "FIN-BANK-019",
        "FIN-BANK-033",
        "FIN-BANK-034",
        "FIN-BANK-006",
        "FIN-BANK-020",
        "FIN-BANK-021",
        "FIN-BANK-031",
        "FIN-BANK-032",
        "FIN-BANK-035",
        "FIN-BANK-036-v1",
        "FIN-INS-003",
        "FIN-INS-006",
        "FIN-INS-007",
        "FIN-INS-017",
        "FIN-INS-022-v1",
        "FIN-INS-023-v1",
        "FIN-INS-024",
        "FIN-INS-026",
        "CUST-005",
        "CUST-009",
        "CUST-010",
    )

    def _g3_text(value: Any) -> str:
        if value is None:
            return "口径未给出"
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        text = str(value).strip()
        return text or "口径未给出"

    def _g3_evidence(row: dict[str, Any]) -> dict[str, Any]:
        basis = (row.get("evidence_basis") or "none").strip() or "none"
        provenance = (row.get("provenance_label") or "").strip()
        if basis == "regulatory":
            return {
                "code": basis,
                "basisLabel": "监管原文",
                "source": provenance or "监管原文",
                "hasRegulatoryText": True,
            }
        if basis == "industry":
            return {
                "code": basis,
                "basisLabel": "行业通行（未获监管原文）",
                "source": provenance or "行业通行",
                "hasRegulatoryText": False,
                "notice": _G3_INDUSTRY_NOTICE,
            }
        return {
            "code": basis,
            "basisLabel": "无证据",
            "source": provenance or "未给出",
            "hasRegulatoryText": False,
        }

    def _g3_metric_row(row: dict[str, Any]) -> dict[str, Any]:
        metric_id = str(row.get("metric_id") or "")
        tier = (row.get("computability_tier") or "unknown").strip() or "unknown"
        evidence = _g3_evidence(row)
        publishable = bool(row.get("publishable"))
        formula = (row.get("formula_text") or "").strip() or (row.get("formula_expr") or "").strip()
        external_eligible = bool(
            publishable
            and evidence["code"] == "regulatory"
            and tier == "structurally_computable"
        )
        if external_eligible:
            external_status = "external_candidate"
            external_label = "对外可出数候选（需事实与观测）"
            external_reason = "证据为监管原文、publishable=true、口径结构性可算"
        elif evidence["code"] == "industry":
            external_status = "internal_baseline"
            external_label = _G3_INDUSTRY_NOTICE
            external_reason = f"行业公式未获监管原文：{_G3_INDUSTRY_NOTICE}"
        elif not publishable:
            external_status = "unpublishable"
            external_label = "不可发布"
            external_reason = "publishable=false"
        else:
            external_status = "blocked"
            external_label = "不可对外"
            external_reason = f"口径未达结构性可算：{tier}"

        missing = row.get("missing")
        if row.get("output_mode") == "index":
            gap = "族索引：需指定变体（E_METRIC_VARIANT_REQUIRED）"
            gap_code = "variant_required"
        elif missing:
            gap = _G3_GAP_LABELS.get(str(missing), _g3_text(missing))
            gap_code = str(missing)
        elif not formula:
            gap = "公式缺失"
            gap_code = "formula_missing"
        elif tier != "structurally_computable":
            gap = _G3_TIER_LABELS.get(tier, tier)
            gap_code = tier
        elif row.get("inference"):
            gap = "口径为推导，无成文原文"
            gap_code = "inference_only"
        else:
            gap = "—"
            gap_code = None

        return {
            "metricId": metric_id,
            "nameZh": row.get("name_zh"),
            "displayName": row.get("display_name"),
            "domain": row.get("domain"),
            "publishable": publishable,
            "evidenceBasis": evidence["code"],
            "evidenceBasisLabel": evidence["basisLabel"],
            "evidenceSource": evidence["source"],
            "hasRegulatoryText": evidence["hasRegulatoryText"],
            "industryBaseline": evidence["code"] == "industry",
            "internalNotice": evidence.get("notice"),
            "e1Baseline": metric_id in _G3_E1_INDUSTRY_IDS,
            "formula": formula or "口径未给出",
            "formulaExpr": row.get("formula_expr"),
            "computability": tier,
            "computabilityLabel": _G3_TIER_LABELS.get(tier, tier),
            "computabilityTone": _G3_TIER_TONES.get(tier, "muted"),
            "gap": gap,
            "gapCode": gap_code,
            "missing": missing,
            "externalEligible": external_eligible,
            "externalStatus": external_status,
            "externalLabel": external_label,
            "externalReason": external_reason,
            "variantOf": row.get("variant_of"),
            "outputMode": row.get("output_mode"),
            "formulaDisabled": bool(row.get("formula_disabled")),
            "inference": bool(row.get("inference")),
            "evidenceStatus": row.get("evidence_status"),
            "definitionVersion": row.get("definition_version"),
        }

    def _g3_manifest(
        scope: str,
        domain: str | None,
        evidence_basis: str | None,
        publishable: bool | None,
    ) -> dict[str, Any]:
        raw = runtime.metadata.query(_G3_METRIC_SQL)
        items = [_g3_metric_row(row) for row in raw]
        all_items = list(items)
        if domain:
            items = [item for item in items if item["domain"] == domain]
        if evidence_basis:
            items = [item for item in items if item["evidenceBasis"] == evidence_basis]
        if publishable is not None:
            items = [item for item in items if item["publishable"] is bool(publishable)]
        if scope == "external":
            items = [item for item in items if item["externalEligible"]]

        tiers: dict[str, int] = {}
        for item in items:
            tiers[item["computability"]] = tiers.get(item["computability"], 0) + 1
        external_count = sum(1 for item in items if item["externalEligible"])

        by_id = {item["metricId"]: item for item in all_items}
        e1_present = [mid for mid in _G3_E1_INDUSTRY_IDS if mid in by_id]
        e1_missing = [mid for mid in _G3_E1_INDUSTRY_IDS if mid not in by_id]
        e1_wrong = [mid for mid in e1_present if by_id[mid]["evidenceBasis"] != "industry"]
        e1_publishable = [mid for mid in e1_present if by_id[mid]["publishable"]]

        meta = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": "platform.metric_definition",
            "scope": scope,
            "total": len(items),
            "allTotal": len(all_items),
            "counts": {
                "publishableTrue": sum(1 for item in items if item["publishable"]),
                "industry": sum(1 for item in items if item["evidenceBasis"] == "industry"),
                "regulatory": sum(1 for item in items if item["evidenceBasis"] == "regulatory"),
                "externalEligible": external_count,
                "industryExcludedFromExternal": (
                    sum(1 for item in all_items if item["evidenceBasis"] == "industry")
                    if scope == "external"
                    else 0
                ),
                "computability": tiers,
            },
            "industryNotice": _G3_INDUSTRY_NOTICE,
            "e1Check": {
                "source": _G3_E1_SOURCE,
                "expected": len(_G3_E1_INDUSTRY_IDS),
                "found": len(e1_present),
                "allPresent": len(e1_missing) == 0,
                "missingIds": e1_missing,
                "allIndustry": len(e1_wrong) == 0 and len(e1_missing) == 0,
                "violations": e1_wrong,
                "publishableTrue": len(e1_publishable),
                "note": "以库为准；发现缺失或不一致时原样列出，不做补数、不改口径。",
            },
            "externalScopeRule": (
                "evidence_basis=regulatory 且 publishable=true 且 computability_tier=structurally_computable"
            ),
            "disclaimer": "可算性仅表示口径四元组与公式可编译，不代表已有观测值；本清单不承诺业务数值。",
        }
        return {
            "items": items,
            "count": len(items),
            "meta": meta,
            "filters": {
                "scope": scope,
                "domain": domain,
                "evidenceBasis": evidence_basis,
                "publishable": publishable,
            },
        }

    @app.get("/metrics/report/manifest")
    def metrics_report_manifest(
        scope: str = Query(default="all", pattern="^(all|external)$"),
        domain: str | None = None,
        evidenceBasis: str | None = None,
        publishable: bool | None = None,
    ) -> dict[str, Any]:
        return _g3_manifest(scope, domain, evidenceBasis, publishable)

    @app.get("/metrics/report/manifest.csv")
    def metrics_report_manifest_csv(
        scope: str = Query(default="all", pattern="^(all|external)$"),
        domain: str | None = None,
        evidenceBasis: str | None = None,
        publishable: bool | None = None,
    ) -> Response:
        import csv
        import io

        payload = _g3_manifest(scope, domain, evidenceBasis, publishable)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "metric_id",
                "名称",
                "域",
                "evidence_basis",
                "证据来源",
                "publishable",
                "可算性",
                "公式",
                "对外状态",
                "对外判定说明",
                "内部标注",
                "E1行业基线",
                "缺口",
                "variant_of",
                "output_mode",
                "definition_version",
            ]
        )
        for item in payload["items"]:
            writer.writerow(
                [
                    item["metricId"],
                    item["nameZh"] or "",
                    item["domain"] or "",
                    item["evidenceBasis"],
                    item["evidenceSource"],
                    str(item["publishable"]).lower(),
                    item["computabilityLabel"],
                    item["formula"],
                    item["externalLabel"],
                    item["externalReason"],
                    item["internalNotice"] or "",
                    "true" if item["e1Baseline"] else "false",
                    item["gap"],
                    item["variantOf"] or "",
                    item["outputMode"] or "",
                    item["definitionVersion"] or "",
                ]
            )
        body = "\ufeff" + buffer.getvalue()
        filename = f"metrics-manifest-{date.today():%Y%m%d}.csv"
        return Response(
            content=body.encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # M-03: 多口径并列与族索引。族索引本身不出数，出数前必须选择变体并回填 metric_id。

    _G3_FAMILY_SQL = """
        SELECT metric_id, name_zh, display_name, domain, evidence_basis, publishable, inference,
               formula_disabled, missing, evidence_status, definition_version, metric_kind,
               formula_expr, formula_text, numerator_agg, denominator_agg, window_kind,
               min_window_days, observation_period, grain, granularity, unit,
               variant_of, output_mode, provenance_label, computability_tier
          FROM platform.metric_definition
         WHERE output_mode = 'index' OR variant_of IS NOT NULL
         ORDER BY metric_id
    """
    _G3_VARIANT_GUIDANCE = {
        "code": "E_METRIC_VARIANT_REQUIRED",
        "message": "该指标是口径族索引，不直接出数；请先选择变体并回填 metric_id。",
        "howTo": [
            "在族索引详情中选择一个变体（窗口/分母/粒度会并排展示）",
            "前端将变体 metric_id 回填到详情与 URL",
            "再用该 metric_id 调用 /metrics/{metric_id}/output",
        ],
    }

    def _g3_variant(row: dict[str, Any]) -> dict[str, Any]:
        tier = (row.get("computability_tier") or "unknown").strip() or "unknown"
        evidence = _g3_evidence(row)
        publishable = bool(row.get("publishable"))
        formula = (row.get("formula_text") or "").strip() or (row.get("formula_expr") or "").strip()
        return {
            "metricId": str(row.get("metric_id") or ""),
            "nameZh": row.get("name_zh"),
            "displayName": row.get("display_name"),
            "publishable": publishable,
            "evidenceBasis": evidence["code"],
            "externalEligible": bool(
                publishable
                and evidence["code"] == "regulatory"
                and tier == "structurally_computable"
            ),
            "internalNotice": evidence.get("notice"),
            "formula": formula or "口径未给出",
            "formulaDisabled": bool(row.get("formula_disabled")),
            "computability": tier,
            "computabilityLabel": _G3_TIER_LABELS.get(tier, tier),
            "window": {
                "kind": row.get("window_kind"),
                "minWindowDays": row.get("min_window_days"),
                "text": _g3_text(row.get("observation_period")),
            },
            "denominator": _g3_text(row.get("denominator_text") or row.get("denominator_agg")),
            "denominatorText": row.get("denominator_text"),
            "grain": _g3_text(row.get("granularity") or row.get("grain")),
            "grainCode": row.get("grain"),
            "metricKind": row.get("metric_kind"),
            "unit": row.get("unit"),
        }

    def _g3_family_payload(
        family_id: str,
        index_row: dict[str, Any] | None,
        variant_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        variants = [_g3_variant(row) for row in variant_rows]

        def diff(field: str, label: str, getter) -> dict[str, Any]:
            values = {item["metricId"]: getter(item) for item in variants}
            return {
                "field": field,
                "label": label,
                "values": values,
                "different": len(set(values.values())) > 1,
            }

        return {
            "familyId": family_id,
            "indexMetricId": (
                index_row.get("metric_id") if index_row is not None else family_id
            ),
            "nameZh": (
                index_row.get("name_zh") if index_row is not None else family_id
            ),
            "selectionRequired": True,
            "guidance": _G3_VARIANT_GUIDANCE,
            "variantCount": len(variants),
            "variants": variants,
            "diffs": [
                diff(
                    "observationPeriod",
                    "观察窗口",
                    lambda item: "%s（%s 天）"
                    % (item["window"]["text"], item["window"]["minWindowDays"] or 0),
                ),
                diff("denominator", "分母", lambda item: item["denominator"]),
                diff("grain", "粒度", lambda item: item["grain"]),
                diff("formula", "公式", lambda item: item["formula"]),
            ],
            "source": "platform.metric_definition",
        }

    def _g3_families() -> list[dict[str, Any]]:
        rows = runtime.metadata.query(_G3_FAMILY_SQL)
        indexes = {
            str(row["metric_id"]): row
            for row in rows
            if row.get("output_mode") == "index"
        }
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            parent = row.get("variant_of")
            if not parent:
                continue
            grouped.setdefault(str(parent), []).append(row)
        family_ids = sorted(set(indexes) | set(grouped))
        return [
            _g3_family_payload(family_id, indexes.get(family_id), grouped.get(family_id, []))
            for family_id in family_ids
        ]

    @app.get("/metrics/report/families")
    def metrics_report_families() -> dict[str, Any]:
        families = _g3_families()
        return {
            "families": families,
            "count": len(families),
            "guidance": _G3_VARIANT_GUIDANCE,
            "source": "platform.metric_definition",
        }

    @app.get("/metrics/report/families/{family_id}")
    def metrics_report_family(family_id: str) -> dict[str, Any]:
        for family in _g3_families():
            if family["familyId"] == family_id:
                return {"family": family, "source": "platform.metric_definition"}
        raise PortError(
            code="NotFound",
            message=f"metric family not found: {family_id}",
            provider="platform",
            provider_code="E_METRIC_FAMILY_NOT_FOUND",
            details={"familyId": family_id},
        )

    # M-04: 口径卡可视化 + PROV 判定徽标。
    # 79 张主卡 = variant_of IS NULL 的行（与 doc/_fsldm/01-指标卡 的 79 个文件逐一对应）；
    # 6 条族变体没有独立卡，明确显示“未建卡”，不伪造卡内容。

    _G3_CARD_SQL = """
        SELECT metric_id, name_zh, display_name, domain, evidence_basis, publishable, inference,
               formula_disabled, missing, evidence_status, note, definition_version, metric_kind,
               formula_expr, formula_text, numerator_agg, denominator_agg, window_kind,
               min_window_days, observation_period, grain, granularity, unit, effective_date,
               variant_of, output_mode, provenance_label, computability_tier,
               definition, denominator_text
          FROM platform.metric_definition
         WHERE metric_id = %s
    """

    def _g3_tone_for_external(status: str) -> str:
        if status == "external_candidate":
            return "ok"
        if status == "internal_baseline":
            return "warn"
        return "bad"

    @app.get("/browse/metrics/{metric_id}/card")
    def browse_metric_card(metric_id: str) -> dict[str, Any]:
        rows = runtime.metadata.query(_G3_CARD_SQL, (metric_id,))
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"metric not found: {metric_id}",
                provider="platform",
                provider_code="E_METRIC_NOT_FOUND",
                details={"metricId": metric_id},
            )
        row = rows[0]
        base = _g3_metric_row(row)
        evidence = _g3_evidence(row)
        card_exists = row.get("variant_of") is None
        if card_exists:
            card_state = "built"
            card_state_label = "已建卡"
            doc_path = f"doc/_fsldm/01-指标卡/{metric_id}.md"
        else:
            card_state = "not_built"
            card_state_label = "未建卡（族变体，无独立口径卡）"
            doc_path = None

        badges = [
            {
                "key": "evidence",
                "label": evidence["basisLabel"]
                + (f" · {_G3_INDUSTRY_NOTICE}" if evidence.get("notice") else ""),
                "tone": (
                    "ok" if evidence["code"] == "regulatory"
                    else ("warn" if evidence["code"] == "industry" else "bad")
                ),
            },
            {
                "key": "publishable",
                "label": "可发布（内部）" if base["publishable"] else "不可发布",
                "tone": "ok" if base["publishable"] else "warn",
            },
            {
                "key": "external",
                "label": base["externalLabel"],
                "tone": _g3_tone_for_external(base["externalStatus"]),
            },
            {
                "key": "computability",
                "label": base["computabilityLabel"],
                "tone": base["computabilityTone"],
            },
        ]

        decision_count = None
        decision_label = "PROV 判定：运行时可无 PROV"
        prov = getattr(runtime, "prov", None)
        if prov is not None:
            try:
                history = prov.decision_history(metric_id, limit=20)
                decision_count = int(history.get("count", 0))
                decision_label = (
                    f"PROV 判定 {decision_count} 条" if decision_count else "PROV 判定：无记录"
                )
                badges.append(
                    {
                        "key": "prov",
                        "label": decision_label,
                        "tone": "ok" if decision_count else "muted",
                    }
                )
            except Exception as exc:  # PROV 不可用不应阻断口径卡
                decision_label = f"PROV 判定不可用：{type(exc).__name__}"

        sections = [
            {"key": "definition", "title": "定义", "text": _g3_text(row.get("definition"))},
            {"key": "formula", "title": "公式", "text": base["formula"]},
            {
                "key": "denominator",
                "title": "分母",
                "text": _g3_text(row.get("denominator_text") or row.get("denominator_agg")),
            },
            {"key": "window", "title": "观察期", "text": _g3_text(row.get("observation_period"))},
            {"key": "grain", "title": "粒度", "text": _g3_text(row.get("granularity") or row.get("grain"))},
            {
                "key": "evidence",
                "title": "证据",
                "text": "｜".join(
                    part for part in (
                        evidence["basisLabel"],
                        evidence["source"],
                        _g3_text(row.get("evidence_status")),
                        evidence.get("notice"),
                    ) if part
                ),
            },
            {"key": "pipeline", "title": "可算性", "text": base["computabilityLabel"]},
            {"key": "gap", "title": "缺口", "text": base["gap"]},
        ]

        return {
            "metricId": metric_id,
            "cardExists": card_exists,
            "cardState": card_state,
            "cardStateLabel": card_state_label,
            "cardSource": "platform.metric_definition",
            "docPath": doc_path,
            "card": {
                "metricId": metric_id,
                "nameZh": row.get("name_zh"),
                "displayName": row.get("display_name"),
                "domain": row.get("domain"),
                "metricKind": row.get("metric_kind"),
                "unit": row.get("unit"),
                "definitionVersion": row.get("definition_version"),
                "effectiveDate": row.get("effective_date"),
                "variantOf": row.get("variant_of"),
                "outputMode": row.get("output_mode"),
                "note": row.get("note"),
            },
            "badges": badges,
            "sections": sections,
            "prov": {
                "graph": "urn:platform:prov",
                "decisionsUrl": f"/prov/decisions?metricId={metric_id}&limit=20",
                "verifyUrl": "/prov/verify",
                "decisionCount": decision_count,
                "decisionLabel": decision_label,
            },
            "links": {
                "detailApi": f"/browse/metrics/{metric_id}",
                "output": f"/metrics/{metric_id}/output",
                "manifest": "/metrics/report/manifest",
                "families": "/metrics/report/families",
            },
            "source": "metric_definition + doc/_fsldm/01-指标卡",
        }

    # --- end G3 ---

    # --- G4 retrieval routes ---
    # The block is intentionally self-contained: helpers are nested so no
    # existing route/helper in this module is touched. Everything here is
    # read-only except the opt-in golden-set evaluation, which only reads.

    _G4_LAYERS = ("ontology", "terms", "metrics", "facts")
    _G4_LAYER_STATUSES = (
        "covered",
        "partial",
        "missing",
        "unavailable",
        "not_applicable",
    )
    _G4_CITATION_KINDS = {
        "ontology-version",
        "rdfs-term",
        "skos-term",
        "metric-definition",
        "formula",
        "rule-set",
        "fact-projection",
        "fact-table",
        "fact-table-field",
        "fact-observation",
        "value-source",
        "chunk",
    }
    # Frozen 24-query set from doc/_design/24 §5.2 and platform/tests/term_eval.py.
    # It is deliberately duplicated here so the panel does not import a test
    # module; the strings and expected classes must stay byte-identical.
    _G4_QUERY_SET = (
        {"id": "A1", "group": "A", "query": "她名下的存款帐户是怎么自动还房贷的？", "expectedClasses": ("https://w3id.org/fsldm/agreement#Account",)},
        {"id": "A2", "group": "A", "query": "授信合同里对个人贷款和企业贷款分别怎么约定？", "expectedClasses": ("https://w3id.org/fsldm/agreement#CreditAgreement",)},
        {"id": "A3", "group": "A", "query": "个贷系统自然人基本信息表包含哪些字段？", "expectedClasses": ("https://w3id.org/fsldm/party#Individual",)},
        {"id": "A4", "group": "A", "query": "当事人关系历史记录保留多久？", "expectedClasses": ("https://w3id.org/fsldm/party#PartyRelationship",)},
        {"id": "A5", "group": "A", "query": "抵押物价值发生巨大变化时银行如何处理？", "expectedClasses": ("https://w3id.org/fsldm/asset#CollateralItem",)},
        {"id": "A6", "group": "A", "query": "抵押合同的合同号数据质量是怎么控制的？", "expectedClasses": ("https://w3id.org/fsldm/banking#CollateralAgreement",)},
        {"id": "A7", "group": "A", "query": "客户的基本信息从哪些系统采集？", "expectedClasses": ("https://w3id.org/fsldm/core#Party",)},
        {"id": "A8", "group": "A", "query": "不良率是多少？", "expectedClasses": ("https://w3id.org/fsldm/core#Metric",)},
        {"id": "A9", "group": "A", "query": "集团客户的授信集中度如何计算？", "expectedClasses": ("https://w3id.org/fsldm/party#PartyGroup", "https://w3id.org/fsldm/agreement#CreditAgreement")},
        {"id": "A10", "group": "A", "query": "关联客户之间的风险传染怎么识别？", "expectedClasses": ("https://w3id.org/fsldm/party#PartyRelationship", "https://w3id.org/fsldm/party#PartyGroup")},
        {"id": "A11", "group": "A", "query": "这个险种对应哪些保险产品？", "expectedClasses": ("https://w3id.org/fsldm/insurance#InsuranceProduct",)},
        {"id": "A12", "group": "A", "query": "报案之后多久立案？", "expectedClasses": ("https://w3id.org/fsldm/event#ClaimEvent",)},
        {"id": "B1", "group": "B", "query": "这家客户在你们这有几个账户？", "expectedClasses": ("https://w3id.org/fsldm/core#Party", "https://w3id.org/fsldm/agreement#Account")},
        {"id": "B2", "group": "B", "query": "单一集团客户授信集中度是多少？", "expectedClasses": ("https://w3id.org/fsldm/party#PartyGroup", "https://w3id.org/fsldm/agreement#CreditAgreement")},
        {"id": "B3", "group": "B", "query": "今年报案立案率、案均已决金额多少？", "expectedClasses": ("https://w3id.org/fsldm/event#ClaimEvent", "https://w3id.org/fsldm/agreement#Claim")},
        {"id": "B4", "group": "B", "query": "不良率 / NPL ratio 是多少？", "expectedClasses": ("https://w3id.org/fsldm/core#Metric",)},
        {"id": "B5", "group": "B", "query": "查一下这张保单的保障项", "expectedClasses": ("https://w3id.org/fsldm/agreement#Policy", "https://w3id.org/fsldm/insurance#Coverage")},
        {"id": "C1", "group": "C", "query": "逾期贷款余额占比是多少？", "expectedClasses": ("https://w3id.org/fsldm/agreement#CreditAgreement", "https://w3id.org/fsldm/core#Metric")},
        {"id": "C2", "group": "C", "query": "单一客户贷款集中度是多少？", "expectedClasses": ("https://w3id.org/fsldm/core#Party", "https://w3id.org/fsldm/core#Metric")},
        {"id": "C3", "group": "C", "query": "今年报案立案率是多少？", "expectedClasses": ("https://w3id.org/fsldm/event#ClaimEvent", "https://w3id.org/fsldm/agreement#Claim")},
        {"id": "C4", "group": "C", "query": "今年案均赔款是多少？", "expectedClasses": ("https://w3id.org/fsldm/agreement#Claim", "https://w3id.org/fsldm/core#Metric")},
        {"id": "C5", "group": "C", "query": "今年保单继续率是多少？", "expectedClasses": ("https://w3id.org/fsldm/agreement#Policy", "https://w3id.org/fsldm/core#Metric")},
        {"id": "C6", "group": "C", "query": "今年退保率是多少？", "expectedClasses": ("https://w3id.org/fsldm/agreement#Policy", "https://w3id.org/fsldm/core#Metric")},
        {"id": "C7", "group": "C", "query": "本年客户AUM是多少？", "expectedClasses": ("https://w3id.org/fsldm/core#Party", "https://w3id.org/fsldm/core#Metric")},
    )
    # Ten golden cases: six already regression-tested in tests/test_answer_layers.py,
    # four refusal cases built from concepts absent in the published T-Box.
    _G4_GOLDEN_SET = (
        {
            "id": "G01",
            "query": "产品包的产品特性有哪些",
            "type": "definition",
            "expectRefused": False,
            "requiredCitationKinds": ("ontology-version",),
        },
        {
            "id": "G02",
            "query": "13个月继续率（有效保单件数）的口径是什么",
            "type": "definition",
            "expectRefused": False,
            "requiredCitationKinds": ("metric-definition", "formula"),
        },
        {
            "id": "G03",
            "query": "逾期分档（M0–M6）是什么",
            "type": "rule_set",
            "expectRefused": False,
            "requiredCitationKinds": ("rule-set",),
        },
        {
            "id": "G04",
            "query": "13个月继续率是多少",
            "type": "definition",
            "expectRefused": False,
            "requiredCitationKinds": ("metric-definition",),
            "allowDegraded": True,
        },
        {
            "id": "G05",
            "query": "当事人关系历史记录保留多久",
            "type": "definition",
            "expectRefused": False,
            "requiredCitationKinds": ("ontology-version",),
        },
        {
            "id": "G06",
            "query": "抵押物价值发生巨大变化时银行如何处理",
            "type": "definition",
            "expectRefused": False,
            "requiredCitationKinds": ("ontology-version",),
        },
        {
            "id": "G07",
            "query": "量子计算机的制冷功率是多少",
            "type": "value",
            "expectRefused": True,
            "expectedMissingLayers": ("ontology", "metrics"),
        },
        {
            "id": "G08",
            "query": "火星探测器电池功率是多少",
            "type": "value",
            "expectRefused": True,
            "expectedMissingLayers": ("ontology", "metrics"),
        },
        {
            "id": "G09",
            "query": "量子退火机的能耗是多少",
            "type": "value",
            "expectRefused": True,
            "expectedMissingLayers": ("ontology", "metrics"),
        },
        {
            "id": "G10",
            "query": "超导磁悬浮列车的时速是多少",
            "type": "value",
            "expectRefused": True,
            "expectedMissingLayers": ("ontology", "metrics"),
        },
    )
    _g4_term_cache: dict[str, Any] = {}

    def _g4_query_catalog() -> list[dict[str, Any]]:
        return [
            {
                "id": item["id"],
                "group": item["group"],
                "query": item["query"],
                "expectedClasses": list(item["expectedClasses"]),
            }
            for item in _G4_QUERY_SET
        ]

    def _g4_last_and_message(
        result: dict[str, Any],
    ) -> tuple[dict[str, str], list[dict[str, Any]]]:
        statuses = {
            str(layer.get("layer")): str(layer.get("status") or "missing")
            for layer in result.get("layers") or []
        }
        missing = list(result.get("missing") or [])
        return statuses, missing

    def _g4_verdict(result: dict[str, Any]) -> str:
        statuses, missing = _g4_last_and_message(result)
        blocking = any(
            statuses.get(name) in ("missing", "unavailable")
            for name in _G4_LAYERS
        )
        missing_layers = {str(item.get("layer") or "") for item in missing}
        if result.get("answerable") and (blocking or missing_layers):
            return "overclaim"
        if (
            not result.get("answerable")
            and not missing_layers
            and statuses.get("ontology") == "covered"
        ):
            return "underclaim"
        return "ok"

    def _g4_eval_answerable(query: str, item: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        try:
            payload = _qa_answerable(runtime, query, include_layers=True)
            payload = dict(payload)
            payload["_g4"] = {
                "id": item["id"],
                "group": item["group"],
                "query": query,
                "expectedClasses": item["expectedClasses"],
                "elapsedMs": int((time.monotonic() - started) * 1000),
                "error": None,
            }
            return payload
        except PortError as exc:
            return {
                "_g4": {
                    "id": item["id"],
                    "group": item["group"],
                    "query": query,
                    "expectedClasses": item["expectedClasses"],
                    "elapsedMs": int((time.monotonic() - started) * 1000),
                    "error": exc.provider_code or exc.code,
                    "message": exc.message,
                },
                "query": query,
                "answerable": False,
                "intent": "unknown",
                "layers": [],
                "missing": [],
                "candidates": [],
                "selectedMetrics": [],
            }
        except Exception as exc:  # a panel must never turn a bad row into 500
            return {
                "_g4": {
                    "id": item["id"],
                    "group": item["group"],
                    "query": query,
                    "expectedClasses": item["expectedClasses"],
                    "elapsedMs": int((time.monotonic() - started) * 1000),
                    "error": "E_G4_QUERY_FAILED",
                    "message": str(exc)[:200],
                },
                "query": query,
                "answerable": False,
                "intent": "unknown",
                "layers": [],
                "missing": [],
                "candidates": [],
                "selectedMetrics": [],
            }

    def _g4_term_misjudgment(catalog: list[dict[str, Any]]) -> dict[str, Any]:
        """Reproduce term_eval's expansion false-positive rate (currently 1/11)."""
        try:
            pointer = runtime.ontology.current()
            graph_iri = str(pointer.get("graph")) if pointer else ""
            if not graph_iri:
                return {
                    "status": "unavailable",
                    "reason": "no_ontology_pointer",
                    "evaluated": 0,
                    "misjudged": 0,
                    "rate": 0.0,
                    "items": [],
                    "source": "termlex.match",
                }
            lexicon = _g4_term_cache.get(graph_iri)
            if lexicon is None:
                from .termlex import TermLexicon  # local import: no top-level change

                lexicon = TermLexicon.build(runtime.graph, graph_iri)
                _g4_term_cache[graph_iri] = lexicon
            max_hits = int(
                getattr(
                    getattr(getattr(runtime, "config", None), "context", None),
                    "term_expand_max_hits",
                    5,
                )
            )
            expanded_total = 0
            wrong_total = 0
            items: list[dict[str, Any]] = []
            for entry in catalog:
                hits = lexicon.match(entry["query"], max_hits=max_hits)
                if not hits:
                    continue
                expanded = [str(getattr(hit, "canonical", "")) for hit in hits]
                wrong = [
                    iri for iri in expanded if iri not in set(entry["expectedClasses"])
                ]
                expanded_total += len(expanded)
                wrong_total += len(wrong)
                if wrong:
                    items.append(
                        {
                            "id": entry["id"],
                            "group": entry["group"],
                            "query": entry["query"],
                            "expanded": expanded,
                            "expected": entry["expectedClasses"],
                            "wrong": wrong,
                        }
                    )
            return {
                "status": "ok",
                "reason": None,
                "evaluated": expanded_total,
                "misjudged": wrong_total,
                "rate": round(wrong_total / expanded_total, 4) if expanded_total else 0.0,
                "items": items,
                "source": "termlex.match",
                "note": "24 条查询集的术语扩展误判率；当前基线 9.09% (1/11)",
            }
        except Exception as exc:
            return {
                "status": "unavailable",
                "reason": str(exc)[:200],
                "evaluated": 0,
                "misjudged": 0,
                "rate": 0.0,
                "items": [],
                "source": "termlex.match",
            }

    def _g4_layer_counts(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts = {
            layer: {status: 0 for status in _G4_LAYER_STATUSES}
            for layer in _G4_LAYERS
        }
        present = {layer: 0 for layer in _G4_LAYERS}
        for result in results:
            for layer in result.get("layers") or []:
                name = str(layer.get("layer") or "")
                if name not in counts:
                    continue
                status = str(layer.get("status") or "missing")
                if status not in counts[name]:
                    status = "missing"
                counts[name][status] += 1
                present[name] += 1
        payload = []
        for name in _G4_LAYERS:
            row = counts[name]
            denom = present[name] or 0
            payload.append(
                {
                    "layer": name,
                    "evaluated": denom,
                    **row,
                    "coverageRate": round(row["covered"] / denom, 4) if denom else 0.0,
                }
            )
        return payload

    def _g4_missing_distribution(results: list[dict[str, Any]]) -> dict[str, Any]:
        by_layer: dict[str, int] = {}
        by_code: dict[tuple[str, str], int] = {}
        items: list[dict[str, Any]] = []
        for result in results:
            info = result.get("_g4") or {}
            for item in result.get("missing") or []:
                layer = str(item.get("layer") or "unknown")
                code = str(item.get("code") or "UNSPECIFIED")
                by_layer[layer] = by_layer.get(layer, 0) + 1
                by_code[(layer, code)] = by_code.get((layer, code), 0) + 1
                if len(items) < 200:
                    items.append(
                        {
                            "queryId": info.get("id"),
                            "group": info.get("group"),
                            "query": info.get("query"),
                            "layer": layer,
                            "code": code,
                            "what": item.get("what") or item.get("text") or code,
                        }
                    )
        return {
            "total": sum(by_layer.values()),
            "byLayer": [
                {"layer": layer, "count": count}
                for layer, count in sorted(by_layer.items(), key=lambda pair: (-pair[1], pair[0]))
            ],
            "byCode": [
                {"layer": layer, "code": code, "count": count}
                for (layer, code), count in sorted(
                    by_code.items(), key=lambda pair: (-pair[1], pair[0])
                )
            ],
            "items": items,
        }

    def _g4_candidates(results: list[dict[str, Any]]) -> dict[str, Any]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for result in results:
            info = result.get("_g4") or {}
            for candidate in result.get("candidates") or []:
                layer = str(candidate.get("layer") or "unknown")
                candidate_id = str(candidate.get("id") or "")
                if not candidate_id:
                    continue
                key = (layer, candidate_id)
                entry = grouped.setdefault(
                    key,
                    {
                        "layer": layer,
                        "id": candidate_id,
                        "label": candidate.get("label"),
                        "reason": candidate.get("reason"),
                        "score": candidate.get("score"),
                        "count": 0,
                        "queries": [],
                    },
                )
                entry["count"] += 1
                if len(entry["queries"]) < 3 and info.get("query"):
                    entry["queries"].append(info["query"])
        items = sorted(
            grouped.values(),
            key=lambda entry: (-float(entry.get("count") or 0), entry["layer"], entry["id"]),
        )
        return {"total": len(items), "items": items[:100]}

    def _g4_trend(results: list[dict[str, Any]]) -> dict[str, Any]:
        groups: dict[str, dict[str, Any]] = {}
        intents: dict[str, dict[str, Any]] = {}
        for result in results:
            info = result.get("_g4") or {}
            group = str(info.get("group") or "?")
            intent = str(result.get("intent") or "unknown")
            statuses = {
                str(layer.get("layer")): str(layer.get("status") or "missing")
                for layer in result.get("layers") or []
            }
            for bucket, key in ((groups, group), (intents, intent)):
                entry = bucket.setdefault(
                    key,
                    {
                        "bucket": key,
                        "evaluated": 0,
                        "answerable": 0,
                        "layers": {name: {"covered": 0, "denominator": 0} for name in _G4_LAYERS},
                    },
                )
                entry["evaluated"] += 1
                entry["answerable"] += 1 if result.get("answerable") else 0
                for name in _G4_LAYERS:
                    status = statuses.get(name)
                    if status in (None, "not_applicable"):
                        continue
                    cell = entry["layers"][name]
                    cell["denominator"] += 1
                    cell["covered"] += 1 if status == "covered" else 0
        def _finish(bucket: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
            rows = []
            for key in sorted(bucket):
                entry = bucket[key]
                layers = {
                    name: {
                        "covered": cell["covered"],
                        "denominator": cell["denominator"],
                        "rate": round(cell["covered"] / cell["denominator"], 4)
                        if cell["denominator"]
                        else 0.0,
                    }
                    for name, cell in entry["layers"].items()
                }
                rows.append(
                    {
                        "bucket": key,
                        "evaluated": entry["evaluated"],
                        "answerable": entry["answerable"],
                        "layers": layers,
                    }
                )
            return rows
        return {"basis": "query-set groups / intent", "byGroup": _finish(groups), "byIntent": _finish(intents)}

    def _g4_misjudgments(results: list[dict[str, Any]]) -> dict[str, Any]:
        items = []
        for result in results:
            info = result.get("_g4") or {}
            verdict = _g4_verdict(result)
            if verdict == "ok":
                continue
            statuses = {
                str(layer.get("layer")): str(layer.get("status") or "missing")
                for layer in result.get("layers") or []
            }
            items.append(
                {
                    "id": info.get("id"),
                    "group": info.get("group"),
                    "query": info.get("query"),
                    "verdict": verdict,
                    "answerable": bool(result.get("answerable")),
                    "reasonCode": result.get("reasonCode"),
                    "layerStatuses": statuses,
                    "missingCodes": [
                        str(item.get("code") or "") for item in result.get("missing") or []
                    ],
                    "drillDownUrl": "/answerable/panel?queryId=" + str(info.get("id") or ""),
                }
            )
        evaluated = len(results)
        return {
            "evaluated": evaluated,
            "count": len(items),
            "rate": round(len(items) / evaluated, 4) if evaluated else 0.0,
            "items": items,
        }

    def _g4_citation_view(citation: dict[str, Any]) -> dict[str, Any]:
        from urllib.parse import quote

        kind = str(citation.get("kind") or "")
        ref = citation.get("ref")
        source = citation.get("sourceRef") or {}
        url = source.get("resolveUrl") if isinstance(source, dict) else None
        if not url:
            if kind == "ontology-version":
                url = "/ui/ontology.html"
            elif kind in ("rdfs-term", "skos-term"):
                url = "/ui/entity.html?iri=" + quote(str(citation.get("id") or ""), safe="")
            elif kind in ("metric-definition", "formula", "rule-set"):
                metric_id = citation.get("metricId")
                url = (
                    "/ui/browse.html?tab=metrics&metricId=" + quote(str(metric_id), safe="")
                    if metric_id
                    else "/ui/browse.html?tab=metrics"
                )
            elif kind == "fact-table":
                url = "/browse/facts?table=" + quote(str(ref or ""), safe="")
            elif kind in ("fact-table-field", "fact-projection"):
                url = "/ui/browse.html?tab=metrics"
            elif kind == "chunk":
                url = "/ui/search.html"
        resolvable = bool(url) or bool(kind in _G4_CITATION_KINDS and ref)
        return {
            **citation,
            "resolveUrl": url,
            "resolvable": resolvable,
        }

    def _g4_answer_quality_data(
        strategy: str, limit: int, case_id: str | None = None
    ) -> dict[str, Any]:
        golden = list(_G4_GOLDEN_SET)
        if case_id:
            golden = [item for item in golden if item["id"] == case_id]
        cases = []
        for case in golden[:limit]:
            try:
                result = _qa_answer(
                    runtime,
                    case["query"],
                    top_k=5,
                    strategy=strategy,
                    request_id="g4-golden-" + case["id"],
                )
            except PortError as exc:
                result = {
                    "refused": True,
                    "answerType": "error",
                    "answerMode": "none",
                    "reasonCode": exc.provider_code or exc.code,
                    "citations": [],
                    "missing": [],
                    "degraded": True,
                    "error": exc.message,
                }
            except Exception as exc:
                result = {
                    "refused": True,
                    "answerType": "error",
                    "answerMode": "none",
                    "reasonCode": "E_G4_ANSWER_FAILED",
                    "citations": [],
                    "missing": [],
                    "degraded": True,
                    "error": str(exc)[:200],
                }
            citations = [_g4_citation_view(item) for item in result.get("citations") or []]
            missing = list(result.get("missing") or [])
            missing_layers = sorted(
                {str(item.get("layer") or "unknown") for item in missing}
            )
            kinds = {str(item.get("kind") or "") for item in citations}
            failures = []
            if bool(result.get("refused")) != bool(case["expectRefused"]):
                failures.append(
                    "expected refused="
                    + str(bool(case["expectRefused"])).lower()
                    + ", got "
                    + str(bool(result.get("refused"))).lower()
                )
            if result.get("refused"):
                if not missing:
                    failures.append("refusal has no missing layer")
                for name in case.get("expectedMissingLayers") or ():
                    if name not in missing_layers:
                        failures.append("missing layer not reported: " + name)
            else:
                required = list(case.get("requiredCitationKinds") or ())
                absent = [kind for kind in required if kind not in kinds]
                if absent:
                    failures.append("missing citation kinds: " + ",".join(absent))
                if not citations:
                    failures.append("answer has no citation")
            if not case.get("allowDegraded") and result.get("degraded"):
                failures.append("unexpected degraded=true")
            unresolvable = [item for item in citations if not item.get("resolvable")]
            if unresolvable:
                failures.append("unresolvable citations: " + str(len(unresolvable)))
            cases.append(
                {
                    "id": case["id"],
                    "query": case["query"],
                    "type": case["type"],
                    "expectRefused": bool(case["expectRefused"]),
                    "actual": {
                        "refused": bool(result.get("refused")),
                        "answerType": result.get("answerType"),
                        "answerMode": result.get("answerMode"),
                        "reasonCode": result.get("reasonCode"),
                        "degraded": bool(result.get("degraded")),
                        "citations": citations,
                        "citationKinds": sorted(kinds),
                        "missingLayers": missing_layers,
                    },
                    "pass": not failures,
                    "failures": failures,
                    "drillDownUrl": (
                        "/answer/quality?caseId="
                        + case["id"]
                        + "&strategy="
                        + strategy
                    ),
                }
            )

        by_type: dict[str, dict[str, Any]] = {}
        by_reason: dict[tuple[str, str], int] = {}
        refusals_without_layers = []
        for item in cases:
            actual = item["actual"]
            entry = by_type.setdefault(
                item["type"],
                {
                    "type": item["type"],
                    "cases": 0,
                    "refused": 0,
                    "withCitations": 0,
                    "citations": 0,
                    "resolvable": 0,
                },
            )
            entry["cases"] += 1
            entry["refused"] += 1 if actual["refused"] else 0
            entry["citations"] += len(actual["citations"])
            entry["resolvable"] += sum(1 for c in actual["citations"] if c.get("resolvable"))
            entry["withCitations"] += 1 if actual["citations"] else 0
            if actual["refused"]:
                reason = str(actual.get("reasonCode") or "UNSPECIFIED")
                by_reason[(item["type"], reason)] = by_reason.get((item["type"], reason), 0) + 1
                if not actual["missingLayers"]:
                    refusals_without_layers.append(
                        {"id": item["id"], "query": item["query"], "type": item["type"]}
                    )

        cases_total = len(cases)
        citations_total = sum(len(item["actual"]["citations"]) for item in cases)
        citations_resolvable = sum(
            1 for item in cases for c in item["actual"]["citations"] if c.get("resolvable")
        )
        broken = [
            {"id": item["id"], "query": item["query"], "citation": c}
            for item in cases
            for c in item["actual"]["citations"]
            if not c.get("resolvable")
        ]
        by_type_rows = []
        for key in sorted(by_type):
            entry = by_type[key]
            by_type_rows.append(
                {
                    **entry,
                    "citationCoverageRate": round(entry["withCitations"] / entry["cases"], 4)
                    if entry["cases"]
                    else 0.0,
                    "resolvableRate": round(entry["resolvable"] / entry["citations"], 4)
                    if entry["citations"]
                    else 0.0,
                }
            )
        return {
            "strategy": strategy,
            "goldenSet": {
                "id": "r02-golden-10",
                "count": len(_G4_GOLDEN_SET),
                "evaluated": cases_total,
                "caseId": case_id,
            },
            "summary": {
                "cases": cases_total,
                "passed": sum(1 for item in cases if item["pass"]),
                "failed": sum(1 for item in cases if not item["pass"]),
                "passRate": round(
                    sum(1 for item in cases if item["pass"]) / cases_total, 4
                )
                if cases_total
                else 0.0,
                "casesWithCitations": sum(1 for item in cases if item["actual"]["citations"]),
                "citationCoverageRate": round(
                    sum(1 for item in cases if item["actual"]["citations"]) / cases_total, 4
                )
                if cases_total
                else 0.0,
                "citations": citations_total,
                "resolvableCitations": citations_resolvable,
                "citationResolvableRate": round(citations_resolvable / citations_total, 4)
                if citations_total
                else 0.0,
                "brokenLinkRate": round(len(broken) / citations_total, 4)
                if citations_total
                else 0.0,
                "baselineBrokenLinkRate": 0.0,
                "regression": bool(broken),
            },
            "citationCoverageByType": by_type_rows,
            "refusalsByReason": [
                {"type": type_name, "reasonCode": reason, "count": count}
                for (type_name, reason), count in sorted(by_reason.items())
            ],
            "refusalsByType": [
                {
                    "type": entry["type"],
                    "cases": entry["cases"],
                    "refused": entry["refused"],
                    "refusalRate": round(entry["refused"] / entry["cases"], 4)
                    if entry["cases"]
                    else 0.0,
                }
                for entry in by_type_rows
            ],
            "refusalsWithoutLayers": refusals_without_layers,
            "brokenLinks": broken,
            "cases": cases,
            "empty": cases_total == 0,
            "emptyReason": (
                "case_not_found"
                if cases_total == 0 and case_id
                else ("no_golden_cases" if cases_total == 0 else None)
            ),
            "readOnly": True,
        }

    def _g4_provenance_fields(detail: dict[str, Any], iri: str) -> dict[str, Any]:
        from urllib.parse import quote

        sources = list(detail.get("sources") or [])
        edges = list((detail.get("neighbors") or {}).get("edges") or [])
        related = list((detail.get("relatedMetrics") or {}).get("items") or [])
        bindings: dict[str, dict[str, Any]] = {}
        for metric in related:
            for binding in metric.get("bindings") or []:
                column = str(binding.get("entityColumn") or "").strip().lower()
                if column:
                    bindings[column] = {
                        "metricId": metric.get("metricId"),
                        "factTable": binding.get("factTable"),
                        "entityColumn": binding.get("entityColumn"),
                        "role": binding.get("role"),
                    }

        def _ref_url(ref: str) -> str:
            return "/source/resolve?ref=" + quote(str(ref), safe="")

        fields = []
        for prop in detail.get("properties") or []:
            property_iri = str(prop.get("property") or "")
            local = str(_local_name(property_iri) or property_iri).lower()
            values = list(prop.get("values") or [])
            asserted = any(
                edge.get("s") == iri
                and edge.get("p") == property_iri
                and not edge.get("inferred")
                for edge in edges
            )
            inferred_only = (
                any(
                    edge.get("s") == iri
                    and edge.get("p") == property_iri
                    and edge.get("inferred")
                    for edge in edges
                )
                and not asserted
            )
            links: list[dict[str, Any]] = []
            state = "none"
            basis = "无 sourceRef / PROV 溯源"
            has_source_ref = False
            has_prov = False
            value_text = ""
            for value in values:
                if isinstance(value, dict) and value.get("kind") == "literal":
                    value_text = str(value.get("value") or "")
                    break
            for source in sources:
                text = str(source.get("text") or "")
                if value_text and len(value_text) >= 2 and value_text in text:
                    links.append(
                        {
                            "kind": "source_ref",
                            "ref": source.get("ref"),
                            "url": source.get("resolveUrl") or _ref_url(str(source.get("ref"))),
                        }
                    )
                    state = "evidenced"
                    basis = "字段值命中 PROV/sourceRef 证据文本"
                    has_source_ref = True
                    has_prov = source.get("kind") in ("unparsed", "doc", "fact", "obs", "obs-set")
                    break
            if state == "none" and local in bindings:
                binding = bindings[local]
                table = binding.get("factTable")
                links.append(
                    {
                        "kind": "fact_binding",
                        "ref": table,
                        "url": "/browse/facts?table=" + quote(str(table or ""), safe=""),
                    }
                )
                links.append({"kind": "prov", "url": "/prov/verify"})
                state = "evidenced"
                basis = "指标事实字段绑定（可回溯到事实表/PROV 校验）"
                has_source_ref = True
                has_prov = True
            if state == "none" and property_iri in (
                "http://www.w3.org/2000/01/rdf-schema#seeAlso",
                "http://www.w3.org/ns/prov#wasDerivedFrom",
                "http://www.w3.org/ns/prov#wasGeneratedBy",
            ):
                state = "evidenced"
                basis = "该字段本身承载 sourceRef / PROV 关系"
                links.append({"kind": "prov", "url": "/prov/verify"})
                has_source_ref = True
                has_prov = True
            if state == "none" and inferred_only:
                state = "inferred"
                basis = "仅推理图出现，无断言 sourceRef / PROV"
                links.append({"kind": "prov", "url": "/prov/verify"})
                has_prov = True
            fields.append(
                {
                    "property": property_iri,
                    "label": prop.get("label") or _local_name(property_iri) or property_iri,
                    "values": values,
                    "valueText": value_text or None,
                    "asserted": asserted,
                    "inferredOnly": inferred_only,
                    "badge": {
                        "state": state,
                        "label": "有溯源" if state == "evidenced" else ("仅推理" if state == "inferred" else "无"),
                        "basis": basis,
                    },
                    "hasSourceRef": has_source_ref,
                    "hasProv": has_prov,
                    "links": links,
                }
            )
        summary = {
            "total": len(fields),
            "evidenced": sum(1 for item in fields if item["badge"]["state"] == "evidenced"),
            "inferred": sum(1 for item in fields if item["badge"]["state"] == "inferred"),
            "none": sum(1 for item in fields if item["badge"]["state"] == "none"),
            "withSourceRef": sum(1 for item in fields if item["hasSourceRef"]),
            "withProv": sum(1 for item in fields if item["hasProv"]),
            "coverageRate": round(
                sum(1 for item in fields if item["badge"]["state"] != "none") / len(fields), 4
            )
            if fields
            else 0.0,
        }
        return {
            "iri": iri,
            "label": detail.get("label"),
            "fields": fields,
            "summary": summary,
            "entitySources": sources,
            "evidenceBadge": detail.get("evidenceBadge"),
            "empty": len(fields) == 0,
            "emptyReason": "no_fields" if not fields else None,
            "note": "每个字段都有徽标；无溯源显式显示「无」",
            "readOnly": True,
            "source": "GET /entity/provenance",
        }

    def _g4_browse_links(
        iri: str | None = None,
        metric_id: str | None = None,
        class_iri: str | None = None,
        entity_iri: str | None = None,
        tab: str | None = None,
    ) -> dict[str, Any]:
        from urllib.parse import quote

        def _q(value: str | None) -> str:
            return quote(str(value or ""), safe="")

        templates = {
            "triples-to-entity": "/ui/entity.html?iri={iri}",
            "metrics-to-definition": "/ui/browse.html?tab=metrics&metricId={metricId}",
            "tree-to-entity": "/ui/entity.html?iri={iri}",
            "entity-to-tab": "/ui/browse.html?tab={tab}&entity={iri}",
        }
        paths = [
            {
                "id": "triples-to-entity",
                "label": "三元组 → 实体页",
                "from": "/browse/triples",
                "to": "entity.html",
                "template": templates["triples-to-entity"],
                "method": "GET",
                "href": "/ui/entity.html?iri=" + _q(iri) if iri else None,
            },
            {
                "id": "metrics-to-definition",
                "label": "口径卡 → 口径定义",
                "from": "/browse/metrics",
                "to": "/browse/metrics/{metricId} + browse metrics tab",
                "template": templates["metrics-to-definition"],
                "method": "GET",
                "href": (
                    "/ui/browse.html?tab=metrics&metricId=" + _q(metric_id)
                    if metric_id
                    else None
                ),
            },
            {
                "id": "tree-to-entity",
                "label": "类树 → 实体页",
                "from": "/browse/ontology/tree",
                "to": "entity.html",
                "template": templates["tree-to-entity"],
                "method": "GET",
                "href": "/ui/entity.html?iri=" + _q(class_iri) if class_iri else None,
            },
            {
                "id": "entity-to-tab",
                "label": "实体页 → 浏览 tab",
                "from": "/ui/entity.html",
                "to": "browse.html",
                "template": templates["entity-to-tab"],
                "method": "GET",
                "href": (
                    "/ui/browse.html?tab="
                    + _q(tab or "ontology")
                    + "&entity="
                    + _q(entity_iri)
                    if entity_iri
                    else None
                ),
            },
        ]
        return {
            "paths": paths,
            "templates": templates,
            "artifacts": {
                "triples": "/browse/triples?limit=20",
                "metrics": "/browse/metrics",
                "tree": "/browse/ontology/tree",
                "entity": "/ui/api/entity?iri={iri}",
            },
            "stable": True,
            "readOnly": True,
            "writeOperations": 0,
        }

    @app.get("/answerable/panel")
    def g4_answerable_panel(
        intent: str = Query(default="all"),
        group: str = Query(default="all"),
        layer: str = Query(default="all"),
        limit: int = Query(default=24, ge=1, le=24),
        queryId: str | None = Query(default=None, max_length=20),
    ) -> dict[str, Any]:
        catalog = _g4_query_catalog()
        if queryId:
            catalog = [item for item in catalog if item["id"] == queryId]
        catalog = catalog[:limit]
        results = [_g4_eval_answerable(item["query"], item) for item in catalog]
        if intent in ("value", "definition"):
            results = [item for item in results if str(item.get("intent")) == intent]
        if group in ("A", "B", "C"):
            results = [
                item for item in results if str((item.get("_g4") or {}).get("group")) == group
            ]
        if layer in _G4_LAYERS:
            for item in results:
                item["missing"] = [
                    entry for entry in item.get("missing") or [] if str(entry.get("layer")) == layer
                ]
        errors = [
            item for item in results if (item.get("_g4") or {}).get("error") is not None
        ]
        usable = [item for item in results if (item.get("_g4") or {}).get("error") is None]
        empty = len(results) == 0 or len(usable) == 0
        payload = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "readOnly": True,
            "querySet": {
                "id": "r01-24",
                "count": len(_G4_QUERY_SET),
                "evaluated": len(results),
                "groups": sorted({item["group"] for item in _G4_QUERY_SET}),
                "source": "doc/_design/24 §5.2 + platform/tests/term_eval.py",
            },
            "filters": {
                "intent": intent,
                "group": group,
                "layer": layer,
                "limit": limit,
                "queryId": queryId,
            },
            "layers": _g4_layer_counts(results),
            "missing": _g4_missing_distribution(results),
            "candidates": _g4_candidates(results),
            "trend": _g4_trend(results),
            "misjudgments": _g4_misjudgments(results),
            "termExpansion": _g4_term_misjudgment(
                [item for item in catalog if item["id"] in {r["_g4"]["id"] for r in results}]
            ),
            "errors": [
                {
                    "queryId": (item.get("_g4") or {}).get("id"),
                    "query": (item.get("_g4") or {}).get("query"),
                    "error": (item.get("_g4") or {}).get("error"),
                    "message": (item.get("_g4") or {}).get("message"),
                }
                for item in errors
            ],
            "empty": empty,
            "emptyReason": (
                "runtime_unavailable"
                if empty and len(results) > 0 and len(usable) == 0
                else (
                    "query_not_found"
                    if queryId and len(catalog) == 0
                    else (
                        "no_queries_matched_filters"
                        if len(results) == 0 and len(catalog) > 0
                        else ("no_query_set" if len(catalog) == 0 else None)
                    )
                )
            ),
            "notes": [
                "四层计数与 missing 分布来自 /answerable 的分层结果（只读）",
                "24 条查询集误判可下钻到单条 query 的 layerStatuses / missingCodes",
                "termExpansion 复现 term_eval 的术语扩展误判率（当前基线 9.09%）",
            ],
        }
        if payload["empty"] and errors and len(errors) == len(results):
            payload["emptyReason"] = "runtime_unavailable"
            payload["degraded"] = True
        return payload

    @app.get("/answer/quality")
    def g4_answer_quality(
        strategy: str = Query(default="lexical"),
        limit: int = Query(default=10, ge=1, le=10),
        caseId: str | None = Query(default=None, max_length=10),
    ) -> dict[str, Any]:
        if strategy not in ("lexical", "vector", "hybrid"):
            raise PortError(
                code="InvalidArgument",
                message="strategy must be lexical/vector/hybrid",
                provider="platform",
                provider_code="E_ANSWER_STRATEGY_INVALID",
            )
        return _g4_answer_quality_data(strategy, limit, caseId)

    @app.get("/entity/provenance")
    def g4_entity_provenance(
        iri: str = Query(min_length=1, max_length=2048),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        detail = entity_view.entity_detail(runtime, iri, limit=limit)
        return _g4_provenance_fields(detail, iri)

    @app.get("/browse/links")
    def g4_browse_links(
        iri: str | None = Query(default=None, max_length=2048),
        metricId: str | None = Query(default=None, max_length=200),
        classIri: str | None = Query(default=None, max_length=2048),
        entity: str | None = Query(default=None, max_length=2048),
        tab: str | None = Query(default=None, max_length=40),
    ) -> dict[str, Any]:
        return _g4_browse_links(
            iri=iri,
            metric_id=metricId,
            class_iri=classIri,
            entity_iri=entity,
            tab=tab,
        )

    # --- end G4 ---

    # --- G6 dict routes ---
    @app.get("/catalog/dictionaries/views/{view}")
    def catalog_dictionary_view(
        view: str,
        catalog: str | None = None,
        schema: str | None = None,
        table: str | None = None,
        column: str | None = None,
        sourceKind: str | None = None,
        q: str | None = None,
        limit: int = Query(default=20, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        if view not in catalog_module.DICT_VIEWS:
            raise _browse_error(
                catalog_module.VIEW_INVALID,
                f"unknown dictionary view: {view}",
                {"view": view, "allowed": list(catalog_module.DICT_VIEWS)},
            )
        if sourceKind and sourceKind not in catalog_module.SOURCE_KINDS:
            raise _browse_error(
                "E_DICT_FILTER_INVALID",
                f"unsupported filter value: {sourceKind}",
                {"value": sourceKind, "allowed": list(catalog_module.SOURCE_KINDS)},
            )
        filters = {
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "column": column,
            "sourceKind": sourceKind,
            "q": q,
        }
        if view == "missing_comment":
            filters["missingComment"] = True
        elif view == "unbound":
            filters["unbound"] = True
        elif view == "mappable_unbound":
            filters["mappableUnbound"] = True
        result = _catalog_service().list(filters, limit=limit, offset=offset)
        result["view"] = view
        return result

    @app.post("/catalog/dictionaries/bind")
    def catalog_dictionary_bind(
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        payload = body or {}
        return _catalog_service().record_manual_binding(
            table=payload.get("table") or "",
            column=payload.get("column") or "",
            property_iri=payload.get("propertyIri") or "",
            operator=payload.get("operator") or "",
            basis=payload.get("basis") or "",
            note=payload.get("note"),
            catalog=payload.get("catalog") or "platform",
            schema=payload.get("schema") or "platform",
        )

    # --- end G6 ---

    # --- G5 canvas routes ---

    def _canvas_iri(value: str, field: str) -> str:
        if not _BROWSE_IRI.match(value) or not value.startswith(("http://", "https://", "urn:")):
            raise _browse_error(
                "E_CANVAS_BAD_IRI",
                f"{field} is not a safe absolute IRI",
                {"field": field, "value": value},
            )
        return value

    @app.get("/browse/path")
    def browse_path(
        source: str = Query(alias="from", min_length=1, max_length=2000),
        target: str | None = Query(default=None, alias="to", max_length=2000),
        max_hops: int = Query(default=3, alias="maxHops", ge=1),
        max_nodes: int | None = Query(default=None, alias="maxNodes", ge=1, le=1000),
        max_edges: int | None = Query(default=None, alias="maxEdges", ge=1, le=2000),
        max_paths: int | None = Query(default=None, alias="maxPaths", ge=1, le=50),
        include_types: bool = Query(default=True, alias="includeTypes"),
        include_source: bool = Query(default=True, alias="includeSource"),
        graph: str | None = Query(default=None, max_length=2000),
    ) -> dict[str, Any]:
        """Read-only multi-hop canvas (design 53/55).

        ``to`` switches path mode; without it the result is the bounded
        neighbourhood of ``from``. The route only talks to ``runtime.canvas``,
        so switching simple/full/off never changes this signature.
        """
        _canvas_iri(source, "from")
        requested = None
        if graph:
            _canvas_iri(graph, "graph")
            requested = [graph]
        canvas_cfg = runtime.config.canvas
        nodes_cap = max_nodes or int(canvas_cfg.max_nodes)
        edges_cap = max_edges or int(canvas_cfg.max_edges)
        if target:
            _canvas_iri(target, "to")
            return runtime.canvas.path(
                source,
                target,
                max_hops=max_hops,
                max_paths=max_paths or int(canvas_cfg.max_paths),
                max_nodes=nodes_cap,
                include_types=include_types,
                include_source=include_source,
                graphs=requested,
            )
        return runtime.canvas.subgraph(
            source,
            hops=max_hops,
            max_nodes=nodes_cap,
            max_edges=edges_cap,
            include_types=include_types,
            include_source=include_source,
            graphs=requested,
        )

    # --- end G5 ---

    return app
