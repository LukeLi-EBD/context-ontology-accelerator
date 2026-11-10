"""Metric definition registry (basis v3) with the publishability guard.

The platform has no metric fact store, so "output" here is the governed
definition card: the v3 fields plus the provenance envelope. A metric that
cannot be released never reaches the caller, regardless of whether a value
happens to exist elsewhere.
"""

from __future__ import annotations

import ast
import json
from datetime import date, datetime, timezone
from typing import Any

from .adapters.metadata_pg import MetadataPg
from .errors import PortError
from . import metric_external, source_ref

PUBLISH_CODE = "E_METRIC_NOT_PUBLISHABLE"
DISABLED_CODE = "E_METRIC_FORMULA_DISABLED"
NOT_FOUND_CODE = "E_METRIC_NOT_FOUND"
EVIDENCE_CODE = "E_METRIC_EVIDENCE_MISSING"
DRIVABLE_CODE = "E_METRIC_NOT_DRIVABLE"
WINDOW_CODE = "E_METRIC_WINDOW_INSUFFICIENT"
DENOM_CODE = "E_METRIC_DENOM_ZERO"
NO_DATA_CODE = "E_METRIC_NO_DATA"
VARIANT_CODE = "E_METRIC_VARIANT_REQUIRED"

_COLUMNS = (
    "metric_id, name_zh, domain, evidence_basis, publishable, inference, "
    "formula_disabled, missing, evidence_status, note, "
    "effective_date, variant_of, output_mode, rule_set_json"
)

_COMPUTE_COLUMNS = _COLUMNS + (
    ", definition_version, metric_kind, formula_expr, numerator_agg, "
    "denominator_agg, window_kind, min_window_days, grain, unit"
)

_DETAIL_COLUMNS = _COLUMNS + (
    ", definition, formula_text, denominator_text, observation_period, "
    "granularity, grain, provenance_label, unit, definition_version, "
    "computability_tier"
)

_AGGREGATES = {"sum", "max", "min", "avg", "count", "count_distinct"}

# metric_kind 只决定卡片分类；真正能否计算由 formula/window/aggregate 四元组决定。
# band（分档标签）与 index/rule_set 仍由各自专用读取路径处理，不进数值直算。
DRIVABLE_KINDS = ("ratio", "duration", "sum", "count", "amount", "period_value")


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
    # 观测行已经是“按实体/窗口”聚合后的分子、分母；这里是对观测做跨实体合成，
    # 不能再套一遍原始聚合。count / count_distinct 在事实层已完成去重，跨实体
    # 合成必须相加，否则会变成“对每实体计数的去重计数”。
    if agg.lower() in ("sum", "count", "count_distinct"):
        return f"SUM({column})"
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


def _rule_set(value: Any, output_mode: Any) -> Any:
    """jsonb comes back parsed from psycopg; tolerate a text payload too."""
    if value is None or output_mode != "rule_set":
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def _card(row: dict[str, Any], detail: bool = False) -> dict[str, Any]:
    effective = row.get("effective_date")
    card = {
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
        "effectiveDate": effective.isoformat() if effective else None,
        "variantOf": row.get("variant_of"),
        "outputMode": row.get("output_mode"),
        "ruleSet": _rule_set(row.get("rule_set_json"), row.get("output_mode")),
    }
    if detail:
        card.update(
            {
                "definition": row.get("definition"),
                "formulaText": row.get("formula_text"),
                "denominatorText": row.get("denominator_text"),
                "observationPeriodText": row.get("observation_period"),
                "granularityText": row.get("granularity"),
                # F54: the grain code is what the console matches against the
                # ontology class local name; the prose text is display-only.
                "grain": row.get("grain"),
                "provenanceLabel": row.get("provenance_label"),
                "unit": row.get("unit"),
                "definitionVersion": row.get("definition_version"),
            }
        )
    return card


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
            f"SELECT {_DETAIL_COLUMNS} FROM platform.metric_definition WHERE metric_id = %s",
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
        row = rows[0]
        card = _card(row, detail=True)
        # Field bindings let the metric page answer "which entity/column does
        # this metric bind to?" — the reverse of the entity page's lookup.
        bindings = self._field_bindings(metric_id, row.get("definition_version"))
        card["fieldBindings"] = bindings
        # Unbound is a first-class state here: 32 of the 85 governed metrics
        # have no field binding yet, and an empty sourceTable must never be
        # invented to hide that.
        card["bindingStatus"] = "bound" if bindings else "unbound"
        judgement = metric_external.judgement(row)
        card["externalEligible"] = judgement["eligible"]
        card["externalStatus"] = judgement["status"]
        card["externalLabel"] = judgement["label"]
        card["externalReason"] = judgement["reason"]
        family_id = row.get("variant_of") or (
            metric_id if row.get("output_mode") == "index" else None
        )
        card["familyId"] = family_id
        card["variantMetricIds"] = self.variants(family_id) if family_id else []
        return card

    def _field_bindings(
        self, metric_id: str, version: str | None
    ) -> list[dict[str, Any]]:
        if not version:
            return []
        rows = self._meta.query(
            "SELECT role, fact_table, entity_column, value_expr, agg, filter_sql, "
            "window_column, window_mode FROM platform.metric_field_binding "
            "WHERE metric_id = %s AND definition_version = %s ORDER BY role",
            (metric_id, version),
        )
        return [
            {
                "role": row.get("role"),
                "factTable": row.get("fact_table"),
                "entityColumn": row.get("entity_column"),
                "valueExpr": row.get("value_expr"),
                "agg": row.get("agg"),
                "filterSql": row.get("filter_sql"),
                "windowColumn": row.get("window_column"),
                "windowMode": row.get("window_mode"),
            }
            for row in rows
        ]

    def variants(self, metric_id: str) -> list[str]:
        rows = self._meta.query(
            "SELECT metric_id FROM platform.metric_definition "
            "WHERE variant_of = %s ORDER BY metric_id",
            (metric_id,),
        )
        return [row["metric_id"] for row in rows]

    def _reject_family_index(self, metric_id: str) -> PortError:
        variants = self.variants(metric_id)
        return PortError(
            code="InvalidArgument",
            message=(
                f"metric {metric_id} is a family index and has no single formula; "
                "specify a variant: " + (", ".join(variants) or "(none registered)")
            ),
            provider="platform",
            provider_code=VARIANT_CODE,
            details={"metricId": metric_id, "variants": variants, "missing": "variant"},
        )

    def output(self, metric_id: str, internal: bool = False) -> dict[str, Any]:
        """Return the governed definition card, or refuse with a typed error."""
        row = self.get(metric_id)
        if row["outputMode"] == "index":
            raise self._reject_family_index(metric_id)
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
        payload["outputType"] = (
            "rule_set" if row["outputMode"] == "rule_set" else "definition"
        )
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
        data_source: str | None = None,
    ) -> dict[str, Any]:
        """Compute a metric from registered fields + observations, never per-ID code."""
        row = self._compute_row(metric_id)
        if row["output_mode"] == "index":
            raise self._reject_family_index(metric_id)
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
        if kind not in DRIVABLE_KINDS:
            raise _bad(metric_id, DRIVABLE_CODE, "metric kind is not drivable", "metric_kind")
        if not row["formula_expr"] or not row["window_kind"] or not row["numerator_agg"]:
            raise _bad(
                metric_id, EVIDENCE_CODE,
                "definition quartet is incomplete (formula/window/aggregate)",
                "definition",
            )
        needs_denominator = "denominator" in str(row["formula_expr"])
        numerator_sql = _agg(row["numerator_agg"], "numerator")
        denominator_sql = (
            _agg(row["denominator_agg"], "denominator")
            if needs_denominator
            else None
        )
        if numerator_sql is None or (needs_denominator and denominator_sql is None):
            raise _bad(
                metric_id, EVIDENCE_CODE,
                "definition quartet is incomplete (aggregate/denominator)",
                "denominator" if needs_denominator else "numerator_agg",
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
            if (
                period_start is None
                or period_end is None
                or period_start == period_end
            ):
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
        if data_source:
            window_sql += " AND data_source = %s"
            params.append(data_source)

        select = f"{numerator_sql} AS numerator_value, "
        select += f"{denominator_sql} AS denominator_value, " if denominator_sql else "NULL AS denominator_value, "
        select += "COUNT(*) AS sample_count, BOOL_OR(fixture) AS has_fixture, "
        select += "MIN(data_source) AS data_source, "
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
        try:
            provenance = source_ref.metric_source_payload(
                self._meta,
                metric_id=metric_id,
                definition_version=row["definition_version"],
                as_of=as_of.isoformat() if row["window_kind"] == "instant" else None,
                period_start=(
                    period_start.isoformat() if row["window_kind"] == "period" else None
                ),
                period_end=(
                    period_end.isoformat() if row["window_kind"] == "period" else None
                ),
                entity_key=entity_key,
                institution=institution,
                fixture=fixture,
                row_count=int(stats["sample_count"]),
            )
        except Exception as exc:  # noqa: BLE001 - provenance never blocks a value
            source_ref.log.warning("metric source_ref unavailable: %s", exc)
            provenance = {"sourceRef": None, "sourceRefs": []}
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
            "dataSource": stats["data_source"] or None,
            "fixture": fixture,
            "sampleCount": int(stats["sample_count"]),
            "computedAt": (stats["computed_at"].isoformat()
                           if stats["computed_at"] else datetime.now(timezone.utc).isoformat()),
            "outputType": "observation",
            "sourceRef": provenance["sourceRef"],
            "sourceRefs": provenance["sourceRefs"],
        }
