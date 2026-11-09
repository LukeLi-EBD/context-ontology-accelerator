"""Read-only snapshot builders for the S1 slice.

Three inputs, all read-only:

* the running platform's ``GET /metrics/report/manifest``, ``GET /metrics/{id}``,
  ``GET /browse/metrics/{id}`` and ``GET /catalog/dictionaries`` (HTTP GET only);
* the platform's committed metric binding seeds under
  ``platform/src/platform_core/sql`` and ``metric_binding_overrides.py``;
* COA's ``coa_metrics.osi_parser`` models, used to build and serialize the OSI
  document so the corpus is expressed in COA's own format.

Nothing here opens a database connection or mutates the platform.
"""

from __future__ import annotations

import ast
import json
import re
import urllib.request
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

AS_OF = "2025-12-31"
PERIOD_START = "2025-01-01"
PERIOD_END = "2025-12-31"

_AGG_SQL = {
    "sum": "SUM({})",
    "max": "MAX({})",
    "min": "MIN({})",
    "avg": "AVG({})",
    "count": "COUNT({})",
    "count_distinct": "COUNT(DISTINCT {})",
}

_BINDING_TUPLE = re.compile(
    r"\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'(numerator|denominator)'\s*,\s*'([^']*)'"
    r"\s*,\s*'([^']*)'\s*,\s*'((?:[^']|'')*)'\s*,\s*'([^']*)'\s*,\s*(NULL|'((?:[^']|'')*)')"
    r"\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)",
    re.S,
)
_FACT_FUNCTION = re.compile(
    r"fact_function\s*=\s*'([^']+)'[\s\S]{0,200}?WHERE\s+metric_id\s*=\s*'([^']+)'"
)


def get_json(url: str, timeout: int = 30) -> Any:
    """HTTP GET a JSON document. The only network verb used in this slice."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_manifest(api: str) -> list[dict[str, Any]]:
    return get_json(f"{api}/metrics/report/manifest")["items"]


def fetch_metric(api: str, metric_id: str) -> dict[str, Any]:
    """Merge the API definition with the browse card (formula/version/aggregations)."""
    detail = get_json(f"{api}/metrics/{metric_id}")
    card = get_json(f"{api}/browse/metrics/{metric_id}")["metric"]
    merged = dict(detail)
    merged["browse"] = card
    return merged


def fetch_catalog_rows(api: str, page_size: int = 200) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = get_json(f"{api}/catalog/dictionaries?limit={page_size}&offset={offset}")
        items = page.get("items", [])
        rows.extend(items)
        if len(items) < page_size:
            return rows
        offset += page_size


def build_catalog_snapshot(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Turn flat dictionary rows into the ``JsonDataSourceLookup`` snapshot shape."""
    sources: dict[str, dict[str, Any]] = {}
    for row in rows:
        data_source_id = str(row.get("catalog") or "platform")
        qualified = f"{row.get('schema')}.{row.get('table')}"
        entry = sources.setdefault(
            data_source_id,
            {"catalog_available": True, "rejection_reasons": {}, "tables": {}},
        )
        entry["tables"].setdefault(qualified, []).append(
            {"name": str(row["column"]), "data_type": str(row.get("dataType") or "unknown")}
        )
    return {"data_sources": sources}


def parse_bindings(sql_dir: str | Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Parse ``metric_field_binding`` rows from the committed migrations.

    Files are read in lexical order so a ``DELETE`` resets accumulated rows the
    same way a forward migration run would.
    """
    bindings: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in sorted(Path(sql_dir).glob("V*.sql")):
        content = path.read_text(encoding="utf-8", errors="replace")
        if "metric_field_binding" not in content:
            continue
        if re.search(r"DELETE\s+FROM\s+platform\.metric_field_binding", content, re.I):
            bindings.clear()
        for match in _BINDING_TUPLE.finditer(content):
            metric_id, version, role = match.group(1), match.group(2), match.group(3)
            bindings[(metric_id, version, role)] = {
                "metric_id": metric_id,
                "definition_version": version,
                "role": role,
                "fact_table": match.group(4),
                "entity_column": match.group(5),
                "value_expr": (match.group(6) or "").replace("''", "'"),
                "agg": match.group(7),
                "filter_sql": (match.group(9) or "").replace("''", "'"),
                "window_column": match.group(10),
                "window_mode": match.group(11),
            }
    return bindings


def load_binding_overrides(path: str | Path) -> list[dict[str, Any]]:
    """Read ``BINDING_OVERRIDES`` without importing the platform package."""
    source = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "BINDING_OVERRIDES":
            return list(ast.literal_eval(node.value))
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "BINDING_OVERRIDES":
            return list(ast.literal_eval(node.value))
    return []


def apply_overrides(
    bindings: dict[tuple[str, str, str], dict[str, Any]], overrides: Iterable[Mapping[str, Any]]
) -> None:
    for override in overrides:
        metric_id = override["metric_id"]
        version = override.get("definition_version", "")
        role = override["role"]
        target = bindings.get((metric_id, version, role))
        if target is None:
            continue
        for key, value in override.items():
            if key in {"metric_id", "definition_version", "role"} or value is None:
                continue
            target[key] = value


def parse_fact_functions(sql_dir: str | Path) -> dict[str, str]:
    """Map metrics whose SQL lives in a ``platform.metric_fact_*`` function."""
    functions: dict[str, str] = {}
    for path in sorted(Path(sql_dir).glob("V*.sql")):
        content = path.read_text(encoding="utf-8", errors="replace")
        for match in _FACT_FUNCTION.finditer(content):
            functions[match.group(2)] = match.group(1)
    return functions


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version)) or (0,)


def resolve_binding(
    bindings: Mapping[tuple[str, str, str], Mapping[str, Any]], metric_id: str, version: str
) -> dict[str, Mapping[str, Any]]:
    """Pick the binding rows for the definition version the platform reports."""
    by_role = {
        role: row
        for (row_metric, row_version, role), row in bindings.items()
        if row_metric == metric_id and row_version == version
    }
    if by_role:
        return by_role
    versions = sorted(
        {row_version for (row_metric, row_version, _role) in bindings if row_metric == metric_id},
        key=_version_key,
    )
    if not versions:
        return {}
    return {
        role: row
        for (row_metric, row_version, role), row in bindings.items()
        if row_metric == metric_id and row_version == versions[-1]
    }


def _substitute(text: str) -> str:
    return text.replace("{start}", f"'{PERIOD_START}'").replace("{end}", f"'{AS_OF}'")


def formula_to_sql(expr: str, numerator_expr: str, denominator_expr: str) -> str:
    """Mirror ``platform_core.metric_compiler.formula_to_sql`` exactly."""
    tree = ast.parse(expr, mode="eval")

    def walk(node: ast.AST) -> str:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return repr(node.value)
        if isinstance(node, ast.Name):
            if node.id == "numerator":
                return numerator_expr
            if node.id == "denominator":
                return denominator_expr
            raise ValueError(f"unknown identifier {node.id!r}")
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
        raise ValueError(f"unsupported expression node {type(node).__name__}")

    return walk(tree)


def _window_predicate(binding: Mapping[str, Any]) -> str:
    column = binding["window_column"]
    if str(binding["window_mode"]).lower() in {"instant", "as_of", "snapshot"}:
        return f"{column} = '{AS_OF}'"
    return f"{column} >= '{PERIOD_START}' AND {column} <= '{PERIOD_END}'"


def _cte(alias: str, role: str, binding: Mapping[str, Any], columns: Mapping[str, set[str]]) -> str:
    aggregate = _AGG_SQL[binding["agg"]].format(_substitute(binding["value_expr"]))
    table = binding["fact_table"]
    predicate = _window_predicate(binding)
    filter_sql = _substitute(binding["filter_sql"]).strip()
    if filter_sql:
        predicate += f" AND ({filter_sql})"
    if "data_source" in columns.get(table.lower(), set()):
        predicate += " AND data_source = 'synthetic'"
    return (
        f"{alias} AS (SELECT {binding['entity_column']} AS entity_key, "
        f"{aggregate} AS {role} FROM {table} WHERE {predicate} "
        f"GROUP BY {binding['entity_column']})"
    )


def compile_metric_sql(
    metric: Mapping[str, Any],
    binding_by_role: Mapping[str, Mapping[str, Any]],
    fact_function: str | None,
    catalog_columns: Mapping[str, set[str]],
) -> tuple[str | None, str]:
    """Build the metric expression and say where it came from.

    Returns ``(expression, source)`` where source is one of
    ``binding`` / ``fact_function`` / ``formula_text_fallback`` (the last one
    means the platform has no executable binding, so the platform formula text
    is carried verbatim and COA is expected to reject it as non-SQL).
    """
    formula = str(metric["browse"].get("formula") or metric.get("formulaText") or "").strip()
    if not formula:
        return None, "formula_text_fallback"

    if fact_function:
        numerator_expr = "COALESCE(f.numerator, 0)::numeric"
        denominator_expr = "(f.denominator)::numeric"
        try:
            value_sql = formula_to_sql(formula, numerator_expr, denominator_expr)
        except ValueError:
            return None, "formula_text_fallback"
        sql = (
            "SELECT f.entity_key AS entity_key, f.numerator AS numerator, "
            "f.denominator AS denominator, "
            f"({value_sql}) AS metric_value "
            f"FROM {fact_function}('{PERIOD_START}', '{PERIOD_END}', 'synthetic') AS f"
        )
        return sql, "fact_function"

    needed_roles = ["numerator"]
    if "denominator" in formula:
        needed_roles.append("denominator")
    if not all(role in binding_by_role for role in needed_roles):
        return None, "formula_text_fallback"

    ctes = [_cte("num", "numerator", binding_by_role["numerator"], catalog_columns)]
    if "denominator" in needed_roles:
        ctes.append(_cte("den", "denominator", binding_by_role["denominator"], catalog_columns))

    numerator_expr = "COALESCE(num.numerator, 0)::numeric"
    denominator_expr = "(den.denominator)::numeric"
    try:
        value_sql = formula_to_sql(formula, numerator_expr, denominator_expr)
    except ValueError:
        return None, "formula_text_fallback"

    if "denominator" in needed_roles:
        select = (
            "SELECT COALESCE(num.entity_key, den.entity_key) AS entity_key, "
            "COALESCE(num.numerator, 0) AS numerator, den.denominator AS denominator, "
            f"({value_sql}) AS metric_value "
            "FROM num FULL OUTER JOIN den USING (entity_key)"
        )
    else:
        select = (
            "SELECT num.entity_key AS entity_key, num.numerator AS numerator, "
            "NULL::numeric AS denominator, "
            f"({value_sql}) AS metric_value FROM num"
        )
    return "WITH " + ",\n".join(ctes) + "\n" + select, "binding"


def metric_description(metric: Mapping[str, Any]) -> str:
    for key in ("definition", "note", "formulaText"):
        value = metric.get(key)
        if value and str(value).strip():
            return str(value).strip()
    return str(metric.get("name") or metric["metricId"])
