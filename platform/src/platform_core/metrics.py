"""Metric definition registry (basis v3) with the publishability guard.

The platform has no metric fact store, so "output" here is the governed
definition card: the v3 fields plus the provenance envelope. A metric that
cannot be released never reaches the caller, regardless of whether a value
happens to exist elsewhere.
"""

from __future__ import annotations

import ast
from datetime import date, datetime, timezone
from typing import Any

from .adapters.metadata_pg import MetadataPg
from .errors import PortError

PUBLISH_CODE = "E_METRIC_NOT_PUBLISHABLE"
DISABLED_CODE = "E_METRIC_FORMULA_DISABLED"
NOT_FOUND_CODE = "E_METRIC_NOT_FOUND"
EVIDENCE_CODE = "E_METRIC_EVIDENCE_MISSING"
DRIVABLE_CODE = "E_METRIC_NOT_DRIVABLE"
WINDOW_CODE = "E_METRIC_WINDOW_INSUFFICIENT"
DENOM_CODE = "E_METRIC_DENOM_ZERO"
NO_DATA_CODE = "E_METRIC_NO_DATA"

_COLUMNS = (
    "metric_id, name_zh, domain, evidence_basis, publishable, inference, "
    "formula_disabled, missing, evidence_status, note"
)

_COMPUTE_COLUMNS = _COLUMNS + (
    ", definition_version, metric_kind, formula_expr, numerator_agg, "
    "denominator_agg, window_kind, min_window_days, grain, unit"
)

_AGGREGATES = {"sum", "max", "min", "avg"}


def _bad(metric_id: str, provider_code: str, message: str, missing: str | None = None) -> PortError:
    details = {"metricId": metric_id}
    if missing is not None:
        details["missing"] = missing
    return PortError(
        code="InvalidArgument",
        message=message,
        provider="platform",
        provider_code=provider_code,
        details=details,
    )


def _agg(agg: str | None, column: str) -> str | None:
    if agg is None or agg.lower() not in _AGGREGATES:
        return None
    return f"{agg.upper()}({column})"


def _eval_formula(expr: str, numerator: float, denominator: float | None) -> float:
    """Evaluate only the tiny arithmetic grammar a definition may declare."""
    allowed_bin = (ast.Add, ast.Sub, ast.Mult, ast.Div)

    def walk(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id == "numerator":
                return numerator
            if node.id == "denominator" and denominator is not None:
                return denominator
            raise ValueError(node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = walk(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, allowed_bin):
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right == 0:
                raise ZeroDivisionError("division by zero")
            return left / right
        raise ValueError(type(node).__name__)

    return walk(ast.parse(expr, mode="eval"))


def _card(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "metricId": row["metric_id"],
        "name": row["name_zh"],
        "domain": row["domain"],
        "evidenceBasis": row["evidence_basis"],
        "publishable": row["publishable"],
        "inference": row["inference"],
        "formulaDisabled": row["formula_disabled"],
        "missing": row["missing"],
        "evidenceStatus": row["evidence_status"],
        "note": row["note"],
    }


def _reject(metric_id: str, missing: str | None, message: str) -> PortError:
    return PortError(
        code="PermissionDenied",
        message=message,
        provider="platform",
        provider_code=PUBLISH_CODE,
        details={"metricId": metric_id, "missing": missing or "source"},
    )


class MetricService:
    port = "MetricService"

    def __init__(self, metadata: MetadataPg) -> None:
        self._meta = metadata

    def list(self, domain: str | None = None) -> list[dict[str, Any]]:
        if domain is None:
            rows = self._meta.query(
                f"SELECT {_COLUMNS} FROM platform.metric_definition ORDER BY metric_id"
            )
        else:
            rows = self._meta.query(
                f"SELECT {_COLUMNS} FROM platform.metric_definition "
                "WHERE domain = %s ORDER BY metric_id",
                (domain,),
            )
        return [_card(row) for row in rows]

    def get(self, metric_id: str) -> dict[str, Any]:
        rows = self._meta.query(
            f"SELECT {_COLUMNS} FROM platform.metric_definition WHERE metric_id = %s",
            (metric_id,),
        )
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"unknown metric: {metric_id}",
                provider="platform",
                provider_code=NOT_FOUND_CODE,
                details={"metricId": metric_id},
            )
        return _card(rows[0])

    def output(self, metric_id: str, internal: bool = False) -> dict[str, Any]:
        """Return the governed definition card, or refuse with a typed error."""
        row = self.get(metric_id)
        if row["formulaDisabled"]:
            raise PortError(
                code="PolicyRejected",
                message=f"metric formula is disabled: {metric_id}",
                provider="platform",
                provider_code=DISABLED_CODE,
                details={"metricId": metric_id, "missing": "formula"},
            )
        if row["evidenceBasis"] == "none":
            raise _reject(metric_id, row["missing"], "metric has no evidence basis")
        if not row["publishable"] and not internal:
            raise _reject(
                metric_id,
                row["missing"] or "regulatory_source",
                "metric is not publishable externally",
            )
        payload = dict(row)
        payload["source"] = "INDUSTRY" if row["evidenceBasis"] == "industry" else "REGULATORY"
        payload["outputType"] = "definition"
        return payload

    # ---- definition-driven calculator -----------------------------------

    def _compute_row(self, metric_id: str) -> dict[str, Any]:
        rows = self._meta.query(
            f"SELECT {_COMPUTE_COLUMNS} FROM platform.metric_definition WHERE metric_id = %s",
            (metric_id,),
        )
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"unknown metric: {metric_id}",
                provider="platform",
                provider_code=NOT_FOUND_CODE,
                details={"metricId": metric_id},
            )
        return rows[0]

    def compute(
        self,
        metric_id: str,
        internal: bool = False,
        as_of: date | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
        entity_key: str | None = None,
        institution: str | None = None,
    ) -> dict[str, Any]:
        """Compute a metric from registered fields + observations, never per-ID code."""
        row = self._compute_row(metric_id)
        if row["formula_disabled"]:
            raise PortError(
                code="PolicyRejected",
                message=f"metric formula is disabled: {metric_id}",
                provider="platform",
                provider_code=DISABLED_CODE,
                details={"metricId": metric_id, "missing": "formula"},
            )
        if row["evidence_basis"] == "none":
            raise _reject(metric_id, row["missing"], "metric has no evidence basis")
        if not row["publishable"] and not internal:
            raise _reject(
                metric_id, row["missing"] or "regulatory_source",
                "metric is not publishable externally",
            )

        kind = row["metric_kind"]
        if kind not in ("ratio", "duration"):
            raise _bad(metric_id, DRIVABLE_CODE, "metric kind is not drivable", "metric_kind")
        if not row["formula_expr"] or not row["window_kind"] or not row["numerator_agg"]:
            raise _bad(
                metric_id, EVIDENCE_CODE,
                "definition quartet is incomplete (formula/window/aggregate)",
                "definition",
            )
        numerator_sql = _agg(row["numerator_agg"], "numerator")
        denominator_sql = _agg(row["denominator_agg"], "denominator") if kind == "ratio" else None
        if numerator_sql is None or (kind == "ratio" and denominator_sql is None):
            raise _bad(
                metric_id, EVIDENCE_CODE,
                "definition quartet is incomplete (aggregate/denominator)",
                "denominator" if kind == "ratio" else "numerator_agg",
            )
        if row["window_kind"] not in ("instant", "period"):
            raise _bad(metric_id, DRIVABLE_CODE, "unsupported window kind", "window_kind")
        try:
            _eval_formula(str(row["formula_expr"]), 0.0, 1.0)
        except (SyntaxError, ValueError) as exc:
            raise _bad(
                metric_id, DRIVABLE_CODE,
                f"formula is not drivable: {exc}", "formula",
            )

        window_sql = ""
        params: list[Any] = [metric_id, row["definition_version"]]
        if row["window_kind"] == "instant":
            if as_of is None:
                raise _bad(metric_id, WINDOW_CODE, "instant metric requires asOf", "window")
            window_sql = " AND as_of = %s"
            params.append(as_of)
            window = {"kind": "instant", "asOf": as_of.isoformat(),
                      "start": as_of.isoformat(), "end": as_of.isoformat()}
        else:
            if period_start is None or period_end is None:
                raise _bad(metric_id, WINDOW_CODE, "period metric requires a full window", "window")
            days = (period_end - period_start).days + 1
            if days < int(row["min_window_days"] or 0):
                raise _bad(
                    metric_id, WINDOW_CODE,
                    f"window has {days} days, needs {row['min_window_days']}",
                    "window",
                )
            if period_end < period_start:
                raise _bad(metric_id, WINDOW_CODE, "window end precedes start", "window")
            window_sql = " AND window_start >= %s AND window_end <= %s"
            params.extend([period_start, period_end])
            window = {"kind": "period", "start": period_start.isoformat(),
                      "end": period_end.isoformat()}
        if entity_key:
            window_sql += " AND entity_key = %s"
            params.append(entity_key)
        if institution:
            window_sql += " AND institution = %s"
            params.append(institution)

        select = f"{numerator_sql} AS numerator_value, "
        select += f"{denominator_sql} AS denominator_value, " if denominator_sql else "NULL AS denominator_value, "
        select += "COUNT(*) AS sample_count, BOOL_OR(fixture) AS has_fixture, "
        select += "MIN(window_start) AS window_start, MAX(window_end) AS window_end, "
        select += "MAX(computed_at) AS computed_at"
        rows = self._meta.query(
            f"SELECT {select} FROM platform.metric_observation "
            f"WHERE metric_id = %s AND definition_version = %s{window_sql}",
            tuple(params),
        )
        stats = rows[0]
        if int(stats["sample_count"]) == 0:
            raise _bad(metric_id, NO_DATA_CODE, "no observations in the requested window", "data")

        try:
            numerator = float(stats["numerator_value"] or 0)
            denominator = (
                float(stats["denominator_value"])
                if stats["denominator_value"] is not None else None
            )
        except (TypeError, ValueError):
            raise _bad(metric_id, DRIVABLE_CODE, "non-numeric observation payload", "numerator")
        if kind == "ratio" and denominator is None:
            raise _bad(metric_id, DENOM_CODE, "denominator is missing", "denominator")
        if kind == "ratio" and denominator == 0:
            raise _bad(metric_id, DENOM_CODE, "denominator is zero", "denominator")
        try:
            value = _eval_formula(str(row["formula_expr"]), numerator, denominator)
        except ZeroDivisionError:
            raise _bad(metric_id, DENOM_CODE, "denominator is zero", "denominator")
        except (SyntaxError, ValueError) as exc:
            raise _bad(
                metric_id, DRIVABLE_CODE,
                f"formula is not drivable: {exc}", "formula",
            )

        fixture = bool(stats["has_fixture"])
        return {
            "metricId": metric_id,
            "value": value,
            "unit": row["unit"],
            "definitionVersion": row["definition_version"],
            "formula": row["formula_expr"],
            "window": window,
            "observedWindow": {
                "start": stats["window_start"].isoformat() if stats["window_start"] else None,
                "end": stats["window_end"].isoformat() if stats["window_end"] else None,
            },
            "grain": row["grain"],
            "evidenceBasis": row["evidence_basis"],
            "source": "INDUSTRY" if row["evidence_basis"] == "industry" else "REGULATORY",
            "inference": row["inference"],
            "publishable": row["publishable"],
            "dataSource": "fixture" if fixture else "business",
            "fixture": fixture,
            "sampleCount": int(stats["sample_count"]),
            "computedAt": (stats["computed_at"].isoformat()
                           if stats["computed_at"] else datetime.now(timezone.utc).isoformat()),
            "outputType": "observation",
        }
