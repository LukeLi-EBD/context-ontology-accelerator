"""Scheme A: minimal single-dialect (PostgreSQL) metric formula compiler.

Input is the governed definition (`metric_kind`, `formula_expr`) plus the field
bindings registered in `platform.metric_field_binding`. Output is an executable
SQL template that aggregates one row per entity and evaluates the formula in
PostgreSQL itself. No dbt/MetricFlow dependency and no YAML second source.

Boundaries:
* only the arithmetic grammar already accepted by `metrics._eval_formula`
  (numerator / denominator / numbers / + - * / parentheses) is compiled;
* the calculator gate is repeated here: a non-publishable metric is rejected
  for external callers and a rule-set metric is routed to `/metrics/{id}/rules`;
* missing bindings or unsupported syntax return explicit error codes instead of
  silently degrading to 0 or a definition card.
"""

from __future__ import annotations

import ast
import re
from datetime import date
from decimal import Decimal
from typing import Any

from .adapters.metadata_pg import MetadataPg
from .errors import PortError

EXPR_UNSUPPORTED = "E_METRIC_EXPR_UNSUPPORTED"
BINDING_MISSING = "E_METRIC_BINDING_MISSING"
BINDING_INVALID = "E_METRIC_BINDING_INVALID"
RULE_SET_ONLY = "E_METRIC_RULE_SET_ONLY"
NOT_COMPUTABLE = "E_METRIC_NOT_STRUCTURALLY_COMPUTABLE"

NOT_FOUND = "E_METRIC_NOT_FOUND"
PUBLISH = "E_METRIC_NOT_PUBLISHABLE"
DISABLED = "E_METRIC_FORMULA_DISABLED"
EVIDENCE = "E_METRIC_EVIDENCE_MISSING"
WINDOW = "E_METRIC_WINDOW_INSUFFICIENT"
DENOM = "E_METRIC_DENOM_ZERO"

_AGG_SQL = {
    "sum": "SUM({})",
    "max": "MAX({})",
    "min": "MIN({})",
    "avg": "AVG({})",
    "count": "COUNT({})",
    "count_distinct": "COUNT(DISTINCT {})",
}
_TABLE_RE = re.compile(r"^platform\.[a-z0-9_]+$")
_COL_RE = re.compile(r"^[a-z0-9_]+$")
_FILTER_FORBIDDEN = (";", "--", "/*", "*/")


def _err(metric_id: str, code: str, message: str, **details: Any) -> PortError:
    return PortError(
        code="InvalidArgument",
        message=message,
        provider="platform",
        provider_code=code,
        details={"metricId": metric_id, **details},
    )


def formula_to_sql(expr: str) -> str:
    """Translate the declared formula into a PostgreSQL expression.

    Raises E_METRIC_EXPR_UNSUPPORTED for any node outside the arithmetic
    grammar. Division is NULLIF-guarded so a zero denominator never yields
    Infinity; the executor turns that into E_METRIC_DENOM_ZERO.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise _err("", EXPR_UNSUPPORTED, f"formula is not parseable: {exc.msg}") from exc

    def walk(node: ast.AST) -> str:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return repr(node.value)
        if isinstance(node, ast.Name):
            if node.id == "numerator":
                # Cast counts to numeric: PostgreSQL integer division would turn
                # 1/2 into 0 before the ratio is scaled. COALESCE keeps the
                # formula consistent with the selected ``numerator`` column:
                # an entity that only appears in the denominator CTE has no
                # numerator row, and that must evaluate as 0, not NULL.
                return "COALESCE(num.numerator, 0)::numeric"
            if node.id == "denominator":
                return "(den.denominator)::numeric"
            raise _err("", EXPR_UNSUPPORTED, f"unknown identifier {node.id!r}")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            op = "-" if isinstance(node.op, ast.USub) else "+"
            return f"({op}{walk(node.operand)})"
        if isinstance(node, ast.BinOp):
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add):
                return f"({left} + {right})"
            if isinstance(node.op, ast.Sub):
                return f"({left} - {right})"
            if isinstance(node.op, ast.Mult):
                return f"({left} * {right})"
            if isinstance(node.op, ast.Div):
                return f"({left} / NULLIF({right}, 0))"
        raise _err(
            "", EXPR_UNSUPPORTED,
            f"unsupported expression node {type(node).__name__}",
        )

    return walk(tree)


class MetricCompiler:
    """Compile and execute one metric against a bound fact table."""

    def __init__(self, metadata: MetadataPg) -> None:
        self.metadata = metadata

    # ------------------------------------------------------------------ load
    def _definition(self, metric_id: str) -> dict[str, Any]:
        rows = self.metadata.query(
            "SELECT metric_id, definition_version, name_zh, publishable, inference, "
            "formula_disabled, evidence_basis, output_mode, rule_set_json, metric_kind, "
            "formula_expr, window_kind, numerator_agg, denominator_agg, min_window_days, "
            "computability_tier "
            "FROM platform.metric_definition WHERE metric_id = %s",
            (metric_id,),
        )
        if not rows:
            raise _err(metric_id, NOT_FOUND, f"metric {metric_id} not found")
        return rows[0]

    def _bindings(self, metric_id: str, version: str) -> dict[str, dict[str, Any]]:
        rows = self.metadata.query(
            "SELECT role, fact_table, entity_column, value_expr, agg, filter_sql, "
            "window_column, window_mode FROM platform.metric_field_binding "
            "WHERE metric_id = %s AND definition_version = %s",
            (metric_id, version),
        )
        return {r["role"]: r for r in rows}

    def _gate(self, metric_id: str, d: dict[str, Any], internal: bool) -> None:
        if d["formula_disabled"]:
            raise _err(metric_id, DISABLED, "metric formula is disabled by governance")
        if d["output_mode"] == "rule_set" or d["metric_kind"] == "rule_set":
            raise _err(metric_id, RULE_SET_ONLY,
                       "rule-set metric must be evaluated through /metrics/{id}/rules")
        if not internal and not d["publishable"]:
            raise _err(metric_id, PUBLISH,
                       "metric is not publishable; external call refused")
        if d["evidence_basis"] == "none" and not internal:
            raise _err(metric_id, EVIDENCE, "metric has no acceptable evidence basis")

    # --------------------------------------------------------------- compile
    def compile(
        self,
        metric_id: str,
        *,
        start: date | str | None = None,
        end: date | str | None = None,
        internal: bool = False,
        data_source: str = "fixture",
    ) -> dict[str, Any]:
        d = self._definition(metric_id)
        self._gate(metric_id, d, internal)

        if not d["formula_expr"] or not d["window_kind"] or not d["numerator_agg"]:
            raise _err(metric_id, NOT_COMPUTABLE,
                       "quartet incomplete: formula_expr/window_kind/numerator_agg required")

        formula = d["formula_expr"]
        value_sql = formula_to_sql(formula)
        needs_den = "denominator" in formula
        bindings = self._bindings(metric_id, d["definition_version"])
        if "numerator" not in bindings:
            raise _err(metric_id, BINDING_MISSING, "numerator field binding missing")
        if needs_den and "denominator" not in bindings:
            raise _err(metric_id, BINDING_MISSING, "denominator field binding missing")

        window_mode = bindings["numerator"]["window_mode"]
        if window_mode == "instant":
            if start is None and end is None:
                raise _err(metric_id, BINDING_INVALID, "instant metric requires asOf")
            as_of = str(start or end)
            win_start = win_end = as_of
        else:
            if start is None or end is None:
                raise _err(metric_id, BINDING_INVALID, "period metric requires start and end")
            win_start, win_end = str(start), str(end)
            # Inclusive days, matching the legacy calculator (end - start + 1).
            span = (date.fromisoformat(win_end) - date.fromisoformat(win_start)).days + 1
            if span < int(d["min_window_days"] or 0):
                raise _err(metric_id, WINDOW, f"window {span}d below min {d['min_window_days']}d")

        entity = bindings["numerator"]["entity_column"]
        parts: list[str] = []
        params: list[Any] = []

        def cte(role: str, alias: str) -> str:
            b = bindings[role]
            fact_table = b["fact_table"]
            if not _TABLE_RE.match(fact_table):
                raise _err(metric_id, BINDING_INVALID, f"invalid fact table {fact_table!r}")
            for col in (b["entity_column"], b["window_column"]):
                if not _COL_RE.match(col):
                    raise _err(metric_id, BINDING_INVALID, f"invalid column {col!r}")
            agg_sql = _AGG_SQL.get(b["agg"])
            if not agg_sql:
                raise _err(metric_id, BINDING_INVALID, f"invalid agg {b['agg']!r}")
            if not _TABLE_RE.match(fact_table) or fact_table not in self._known_tables():
                raise _err(metric_id, BINDING_INVALID, f"fact table {fact_table!r} not found")
            where = []
            if b["window_mode"] == "instant":
                where.append(f"{b['window_column']} = %s")
                params.append(win_end)
            else:
                where.append(f"{b['window_column']} >= %s AND {b['window_column']} <= %s")
                params.extend([win_start, win_end])
            filt = b["filter_sql"]
            if filt:
                for token in _FILTER_FORBIDDEN:
                    if token in filt:
                        raise _err(metric_id, BINDING_INVALID, "filter contains forbidden token")
                for key, val in (("{start}", win_start), ("{end}", win_end)):
                    if key in filt:
                        filt = filt.replace(key, "%s")
                        params.append(val)
                where.append(f"({filt})")
            where.append("data_source = %s")
            params.append(data_source)
            return (
                f"{alias} AS (SELECT {b['entity_column']} AS entity_key, "
                f"{agg_sql.format(b['value_expr'])} AS {role} "
                f"FROM {fact_table} WHERE " + " AND ".join(where) +
                f" GROUP BY {b['entity_column']})"
            )

        parts.append(cte("numerator", "num"))
        if needs_den:
            if bindings["denominator"]["entity_column"] != entity:
                raise _err(metric_id, BINDING_INVALID,
                           "numerator/denominator entity columns differ")
            parts.append(cte("denominator", "den"))

        if needs_den:
            select = (
                "SELECT COALESCE(num.entity_key, den.entity_key) AS entity_key, "
                "COALESCE(num.numerator, 0) AS numerator, "
                "den.denominator AS denominator, "
                f"({value_sql}) AS metric_value FROM num "
                "FULL OUTER JOIN den USING (entity_key) ORDER BY 1"
            )
        else:
            select = (
                "SELECT num.entity_key AS entity_key, num.numerator AS numerator, "
                "NULL::numeric AS denominator, "
                f"({value_sql}) AS metric_value FROM num ORDER BY 1"
            )
        sql = "WITH " + ",\n".join(parts) + "\n" + select
        return {
            "metricId": metric_id,
            "definitionVersion": d["definition_version"],
            "metricKind": d["metric_kind"],
            "windowKind": d["window_kind"],
            "window": {"start": win_start, "end": win_end},
            "dataSource": data_source,
            "sql": sql,
            "params": params,
            "bindings": sorted(bindings),
            "_factTables": sorted({bindings[role]["fact_table"] for role in bindings}),
        }

    def _known_tables(self) -> set[str]:
        if not hasattr(self, "_tables_cache"):
            rows = self.metadata.query(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'platform'"
            )
            self._tables_cache = {f"platform.{r['tablename']}" for r in rows}
        return self._tables_cache

    # --------------------------------------------------------------- execute
    def execute(
        self,
        metric_id: str,
        *,
        start: date | str | None = None,
        end: date | str | None = None,
        internal: bool = False,
        data_source: str = "fixture",
    ) -> dict[str, Any]:
        plan = self.compile(
            metric_id, start=start, end=end, internal=internal, data_source=data_source
        )
        rows = self.metadata.query(plan["sql"], tuple(plan["params"]))
        out: list[dict[str, Any]] = []
        for r in rows:
            numerator = _num(r["numerator"])
            denominator = _num(r["denominator"])
            if "denominator" in plan["bindings"] and is_zero(denominator):
                raise _err(metric_id, DENOM, "denominator is zero; value undefined")
            out.append({
                "entityKey": r["entity_key"],
                "numerator": numerator,
                "denominator": denominator,
                "value": _num(r["metric_value"]),
            })
        result: dict[str, Any] = {
            "metricId": metric_id,
            "window": plan["window"],
            "dataSource": plan["dataSource"],
            "rows": out,
            "noData": len(out) == 0,
        }
        if not out:
            # An empty result from a data source that does not exist in the fact
            # table is not "no data" — it is a wrong-source request. Say so
            # explicitly instead of returning a silent empty payload.
            available = self._data_sources(plan["_factTables"])
            if data_source not in available:
                result.update({
                    "reason": "E_METRIC_DATASOURCE_MISMATCH",
                    "reasonText": (
                        f"dataSource={data_source} has no rows in "
                        f"{', '.join(plan['_factTables'])}; "
                        f"available dataSource: {', '.join(available) or 'none'}"
                        f" (requested {data_source}, found "
                        f"{', '.join(available) or 'none'})"
                    ),
                    "requestedDataSource": data_source,
                    "availableDataSources": available,
                })
        return result

    def _data_sources(self, fact_tables: list[str]) -> list[str]:
        sources: set[str] = set()
        for table in fact_tables:
            if not _TABLE_RE.match(table):
                continue
            rows = self.metadata.query(
                f"SELECT DISTINCT data_source FROM {table}"
            )
            sources.update(str(r["data_source"]) for r in rows)
        return sorted(sources)


def _num(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def is_zero(value: float | None) -> bool:
    return value is not None and abs(value) < 1e-12
