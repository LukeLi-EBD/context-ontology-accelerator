"""Coverage audit for the synthetic fact data.

Four lenses requested by the product owner:
1. ontology: classes / properties with no instance values;
2. bindings: every metric_field_binding row, its table/column data presence;
3. metrics: all structurally executable definitions, run + classify;
4. cases: declared boundary cases, their row counts and single-row cases.

The module is read-only. It returns JSON so the CLI can print and the design doc
can cite exact numbers.
"""

from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal
from typing import Any

import rdflib
from rdflib import OWL, RDF

from .adapters.metadata_pg import MetadataPg
from .datagen import (
    AS_OF,
    SYNTHETIC,
    _metric_definition,
    build_rule_facts,
    discover_tables,
)
from .errors import PortError
from .metric_compiler import MetricCompiler
from .rules import RuleExecutor

WINDOW_START = "2024-12-01"
WINDOW_END = "2025-12-31"

CLASS_ALIASES = {
    "customer": "cust_master",
    "party": "cust_master",
    "institution": None,
    "product": None,
    "region": None,
    "industry": None,
}

_STOP_TOKENS = {
    "bank", "banking", "ins", "insurance", "cust", "customer", "party", "financial",
    "services", "service", "data", "model", "record", "stat", "snapshot", "item",
    "detail", "information", "number", "identifier", "id", "type", "role", "code",
    "of", "for", "has", "is", "the",
}


def _tokens(name: str) -> set[str]:
    snake = _snake(name)
    return {t for t in snake.split("_") if t and t not in _STOP_TOKENS}


def _match_table(name: str, tables: list[str]) -> str | None:
    snake = _snake(name)
    if snake in CLASS_ALIASES:
        return CLASS_ALIASES[snake]
    tokens = _tokens(name)
    if not tokens:
        return None
    best: tuple[int, int, str] | None = None
    for table in tables:
        overlap = len(tokens & _tokens(table))
        if overlap >= 2 or (overlap == 1 and len(tokens) == 1):
            score = (overlap, -len(table), table)
            if best is None or score > best:
                best = score
    return best[2] if best else None


def _match_columns(name: str, columns: dict[str, dict[str, str]]) -> list[tuple[str, str]]:
    tokens = _tokens(name)
    if not tokens:
        return []
    hits: list[tuple[str, str]] = []
    for table, cols in columns.items():
        for column in cols:
            overlap = len(tokens & _tokens(column))
            if overlap >= 2 or (overlap == 1 and len(tokens) == 1 and _snake(column) == _snake(name)):
                hits.append((table, column))
    return hits


_SQL_WORDS = {
    "sum", "max", "min", "avg", "count", "distinct", "null", "case", "when",
    "then", "else", "end", "and", "or", "cast", "numeric", "as", "coalesce",
    "abs", "round", "greatest", "least", "filter", "where", "over", "partition",
}


def _snake(name: str) -> str:
    name = name.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return re.sub(r"__+", "_", name)


def _columns(meta: MetadataPg, schema: str) -> dict[str, dict[str, str]]:
    rows = meta.query(
        "SELECT table_name, column_name, is_nullable FROM information_schema.columns "
        "WHERE table_schema = %s ORDER BY table_name, ordinal_position",
        (schema,),
    )
    out: dict[str, dict[str, str]] = defaultdict(dict)
    for r in rows:
        out[r["table_name"]][r["column_name"]] = r["is_nullable"]
    return out


def audit_ontology(ttl: str | None, meta: MetadataPg, schema: str, tables: list[str]) -> dict[str, Any]:
    classes: list[str] = []
    properties: list[str] = []
    if ttl:
        graph = rdflib.Graph()
        graph.parse(data=ttl, format="turtle")
        classes = sorted({str(s) for s in graph.subjects(RDF.type, OWL.Class)})
        prop_types = (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.FunctionalProperty)
        for ptype in prop_types:
            properties.extend(str(s) for s in graph.subjects(RDF.type, ptype))
        properties = sorted(set(properties))

    cols = _columns(meta, schema)
    rows_by_table = {
        t: int(meta.query(f"SELECT count(*) AS n FROM {schema}.{t}")[0]["n"]) for t in tables
    }

    class_rows: dict[str, int] = {}
    class_values: dict[str, int] = {}
    class_unmapped: dict[str, str] = {}
    uncovered_classes: list[str] = []
    for iri in classes:
        table = _match_table(iri, tables)
        if table and rows_by_table.get(table, 0) > 0:
            class_rows[iri] = rows_by_table[table]
            continue
        # Fall back to distinct non-null values of matching value columns.
        total = 0
        for t, column in _match_columns(iri, {k: v for k, v in cols.items() if k in tables}):
            n = meta.query(
                f"SELECT count(DISTINCT {column}) AS n FROM {schema}.{t} "
                f"WHERE {column} IS NOT NULL AND data_source = %s",
                (SYNTHETIC,),
            )[0]["n"]
            total += int(n or 0)
        class_values[iri] = total
        if table:
            class_unmapped[iri] = table
        if total == 0:
            uncovered_classes.append(iri)

    prop_tables: dict[str, list[str]] = {}
    uncovered_properties: list[str] = []
    null_only_properties: list[str] = []
    for iri in properties:
        hits: list[str] = []
        nonnull_total = 0
        for table, column in _match_columns(iri, {k: v for k, v in cols.items() if k in tables}):
            hits.append(f"{table}.{column}")
            n = meta.query(
                f"SELECT count(*) AS n FROM {schema}.{table} "
                f"WHERE {column} IS NOT NULL AND data_source = %s",
                (SYNTHETIC,),
            )[0]["n"]
            nonnull_total += int(n or 0)
        prop_tables[iri] = sorted(set(hits))
        if not hits:
            uncovered_properties.append(iri)
        elif nonnull_total == 0:
            null_only_properties.append(iri)

    return {
        "classesTotal": len(classes),
        "classesWithRows": len(class_rows),
        "classesWithColumnValues": sum(1 for v in class_values.values() if v > 0),
        "classesUncovered": len(uncovered_classes),
        "uncoveredClasses": uncovered_classes,
        "emptyMappedTables": sorted(class_unmapped.values()),
        "propertiesTotal": len(properties),
        "propertiesUncovered": len(uncovered_properties),
        "uncoveredProperties": uncovered_properties,
        "propertiesAllNull": len(null_only_properties),
        "allNullProperties": null_only_properties,
        "mappedPropertyColumns": {k: v for k, v in prop_tables.items() if v},
    }


def audit_bindings(meta: MetadataPg, schema: str) -> dict[str, Any]:
    bindings = meta.query(
        "SELECT metric_id, definition_version, role, fact_table, entity_column, "
        "value_expr, agg, window_column FROM platform.metric_field_binding "
        "ORDER BY metric_id, role"
    )
    cols = _columns(meta, schema)
    missing_tables: set[str] = set()
    missing_columns: set[str] = set()
    all_null: set[str] = set()
    single_row: set[str] = set()
    checked: set[str] = set()
    detail: list[dict[str, Any]] = []
    for b in bindings:
        table = (b["fact_table"] or "").split(".")[-1]
        refs: list[str] = []
        for key in ("entity_column", "value_expr", "window_column"):
            raw = b[key] or ""
            refs.extend(
                ident for ident in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", raw)
                if ident.lower() not in _SQL_WORDS
            )
        refs = sorted({r for r in refs if r in cols.get(table, {})})
        if not table or table not in cols:
            missing_tables.add(f"{b['metric_id']}:{table}")
            continue
        if not refs:
            continue
        total = int(meta.query(f"SELECT count(*) AS n FROM {schema}.{table}")[0]["n"])
        for column in refs:
            key = f"{table}.{column}"
            checked.add(key)
            if column in missing_columns or key in all_null or key in single_row:
                continue
            nonnull = int(meta.query(
                f"SELECT count(*) AS n FROM {schema}.{table} WHERE {column} IS NOT NULL"
            )[0]["n"])
            if total == 1:
                single_row.add(key)
            if nonnull == 0:
                all_null.add(key)
        detail.append({"metricId": b["metric_id"], "role": b["role"], "table": table, "columns": refs})
    return {
        "bindings": len(bindings),
        "metrics": len({b["metric_id"] for b in bindings}),
        "columnsChecked": len(checked),
        "missingTables": sorted(missing_tables),
        "missingColumns": sorted(missing_columns),
        "allNullColumns": sorted(all_null),
        "singleRowColumns": sorted(single_row),
        "detail": detail,
    }


def audit_metrics(meta: MetadataPg) -> dict[str, Any]:
    definitions = meta.query(
        "SELECT metric_id, definition_version, name_zh, publishable, formula_disabled, "
        "output_mode, metric_kind, formula_expr, window_kind, min_window_days, fact_function "
        "FROM platform.metric_definition ORDER BY metric_id"
    )
    compiler = MetricCompiler(meta)
    executor = RuleExecutor(meta)
    facts = build_rule_facts(meta)
    counts = {"success": 0, "refusal": 0, "exception": 0, "notStructural": 0}
    failures: list[dict[str, Any]] = []
    not_structural: list[str] = []
    for d in definitions:
        structural = d["metric_kind"] != "rule_set" and (
            d["formula_expr"] or d["fact_function"]
        )
        if not structural and d["metric_kind"] != "rule_set":
            counts["notStructural"] += 1
            not_structural.append(d["metric_id"])
            continue
        if d["formula_disabled"]:
            counts["refusal"] += 1
            failures.append({"metricId": d["metric_id"], "category": "refusal", "code": "E_METRIC_FORMULA_DISABLED"})
            continue
        if not d["publishable"]:
            counts["refusal"] += 1
            failures.append({"metricId": d["metric_id"], "category": "refusal", "code": "E_METRIC_NOT_PUBLISHABLE"})
            continue
        try:
            if d["metric_kind"] == "rule_set":
                result = executor.execute(d["metric_id"], facts, as_of=AS_OF.isoformat())
                counts["success"] += 1
                failures.append({"metricId": d["metric_id"], "category": "success", "value": result["triggeredCount"]})
                continue
            probe = {"start": WINDOW_START, "end": WINDOW_END}
            if d["window_kind"] == "instant":
                probe = {"start": AS_OF.isoformat(), "end": None}
            result = compiler.execute(
                d["metric_id"], start=probe["start"], end=probe["end"],
                internal=False, data_source=SYNTHETIC,
            )
            if result["noData"]:
                counts["exception"] += 1
                failures.append({"metricId": d["metric_id"], "category": "exception", "code": "E_METRIC_NO_DATA"})
            else:
                counts["success"] += 1
                failures.append({"metricId": d["metric_id"], "category": "success", "entityRows": len(result["rows"])})
        except PortError as exc:
            code = exc.provider_code or "E_UNKNOWN"
            if code in ("E_METRIC_DENOM_ZERO", "E_METRIC_NO_DATA", "E_METRIC_WINDOW_INSUFFICIENT"):
                counts["exception"] += 1
                category = "exception"
            else:
                counts["refusal"] += 1
                category = "refusal"
            failures.append({"metricId": d["metric_id"], "category": category, "code": code})
    return {
        "definitions": len(definitions),
        "structural": len(definitions) - counts["notStructural"],
        "counts": counts,
        "notStructuralIds": not_structural,
        "failures": failures,
    }


def _count(meta: MetadataPg, sql: str, params: tuple = ()) -> int:
    return int(meta.query(sql, params)[0]["n"] or 0)


def audit_cases(meta: MetadataPg, schema: str) -> dict[str, Any]:
    p = "platform"
    cases = {
        "null_value": _count(meta, f"SELECT count(*) AS n FROM {p}.cust_master WHERE channel IS NULL OR segment IS NULL"),
        "zero_value": _count(meta, f"SELECT count(*) AS n FROM {p}.cust_aum_snapshot WHERE aum = 0"),
        "zero_denominator_snapshot": _count(meta, f"SELECT count(*) AS n FROM {p}.bank_provision_snapshot WHERE npl_balance = 0 AND loan_balance = 0"),
        "negative_value": 0,
        "super_large_value": _count(meta, f"SELECT count(*) AS n FROM {p}.cust_transaction WHERE amount >= 10000000"),
        "cross_period": _count(meta, f"SELECT count(*) AS n FROM {p}.cust_aum_snapshot WHERE as_of NOT BETWEEN DATE '2025-01-01' AND DATE '2025-12-31'"),
        "same_day_duplicate": _count(meta, f"SELECT count(*) AS n FROM {p}.cust_transaction t JOIN (SELECT customer_no, txn_date FROM {p}.cust_transaction GROUP BY 1,2 HAVING count(*) >= 2) d ON d.customer_no=t.customer_no AND d.txn_date=t.txn_date"),
        "status_transition_loan": _count(meta, f"SELECT count(*) AS n FROM {p}.bank_loan_account WHERE risk_class_start <> risk_class_end"),
        "status_transition_policy": _count(meta, f"SELECT count(*) AS n FROM {p}.ins_policy_event WHERE event_type <> 'reinstatement'"),
        "refund": _count(meta, f"SELECT count(*) AS n FROM {p}.cust_transaction WHERE txn_type = 'refund'"),
        "overdue_30": _count(meta, f"SELECT count(*) AS n FROM {p}.bank_loan_account WHERE dpd_end >= 30 AND dpd_end < 60"),
        "overdue_60": _count(meta, f"SELECT count(*) AS n FROM {p}.bank_loan_account WHERE dpd_end >= 60 AND dpd_end < 90"),
        "overdue_90": _count(meta, f"SELECT count(*) AS n FROM {p}.bank_loan_account WHERE dpd_end >= 90"),
        "lost_contact": 0,
    }
    single = sorted(k for k, v in cases.items() if v == 1)
    return {
        "cases": cases,
        "singleRowCases": single,
        "notConstructible": [
            "negative_value: 事实表数值列带 CHECK >= 0（如 cust_transaction.amount），负值会被数据库拒绝",
            "lost_contact: cust_master 无手机号/邮箱/联系方式列，无法表达失联客户",
        ],
    }


def audit_all(meta: MetadataPg, schema: str, ttl: str | None) -> dict[str, Any]:
    tables = discover_tables(meta, schema)
    return {
        "schema": schema,
        "tables": len(tables),
        "ontology": audit_ontology(ttl, meta, schema, tables),
        "bindings": audit_bindings(meta, schema),
        "metrics": audit_metrics(meta),
        "cases": audit_cases(meta, schema),
        "rowCounts": {t: int(meta.query(f"SELECT count(*) AS n FROM {schema}.{t}")[0]["n"]) for t in tables},
    }
