"""Materialize metric observations from the existing fact tables.

This is an operational backfill, not a new calculation engine:

* metrics with field bindings are executed by :class:`MetricCompiler`;
* metrics with a ``fact_function`` are projected by :class:`MetricProjector`;
* rule-set metrics are executed by :class:`RuleExecutor` and produce no
  observation rows by design.

Only per-entity ``numerator`` / ``denominator`` values are written to
``platform.metric_observation``.  The metric value stays a read-time product of
``formula_expr`` (see ``metrics.MetricService.compute``).

Run it with an explicit ``--apply``; the default is a dry run.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from .adapters.metadata_pg import MetadataPg
from .assembly import assemble
from .config import load_config
from .errors import PortError
from .metric_compiler import MetricCompiler
from .metric_facts import MetricProjector, _OBS_UPSERT
from .metrics import MetricService

# datagen writes its snapshots with a single AS_OF date.  Backfill probes use the
# same anchor so a value is computed "as of the dataset's declared snapshot",
# never against a future-dated row that accidentally exists in a table.
CANONICAL_AS_OF = date(2025, 12, 31)

# Definitions only declare a minimum window.  Annual metrics get a full year;
# metrics with a longer minimum get exactly their minimum.
MIN_SPAN_DAYS = 365

_REASON_ZH = {
    "E_METRIC_BINDING_MISSING": "缺字段绑定",
    "E_METRIC_BINDING_INVALID": "字段绑定非法",
    "E_METRIC_NOT_STRUCTURALLY_COMPUTABLE": "定义四元组不完整",
    "E_METRIC_EXPR_UNSUPPORTED": "公式语法不支持",
    "E_METRIC_NOT_DRIVABLE": "指标类型不可直算",
    "E_METRIC_WINDOW_INSUFFICIENT": "窗口不足",
    "E_METRIC_DENOM_ZERO": "分母为零",
    "E_METRIC_NO_DATA": "无数据行",
    "E_METRIC_EVIDENCE_MISSING": "四元组不完整（分母聚合缺失）",
    "E_METRIC_FORMULA_DISABLED": "公式被治理禁用",
    "E_METRIC_RULE_SET_ONLY": "规则型指标须走 /rules",
    "E_METRIC_FACT_SOURCE_MISSING": "无事实函数",
    "E_METRIC_FACT_SOURCE_INVALID": "事实函数返回非法数据",
    "E_FACT_SOURCE_INVALID": "数据源不合法",
}


class MetricBackfill:
    port = "MetricBackfill"

    def __init__(self, metadata: MetadataPg) -> None:
        self._meta = metadata
        self._compiler = MetricCompiler(metadata)
        self._projector = MetricProjector(metadata)
        self._service = MetricService(metadata)

    # ------------------------------------------------------------- definitions
    def _definitions(self, metric_ids: list[str] | None) -> list[dict[str, Any]]:
        rows = self._meta.query(
            "SELECT metric_id, definition_version, metric_kind, output_mode, "
            "window_kind, min_window_days, numerator_agg, denominator_agg, "
            "formula_expr, fact_function, publishable, computability_tier "
            "FROM platform.metric_definition "
            "WHERE computability_tier = 'structurally_computable' "
            "ORDER BY metric_id"
        )
        if metric_ids:
            wanted = set(metric_ids)
            rows = [r for r in rows if r["metric_id"] in wanted]
        return rows

    def _has_binding(self, metric_id: str, version: str) -> bool:
        rows = self._meta.query(
            "SELECT 1 AS ok FROM platform.metric_field_binding "
            "WHERE metric_id = %s AND definition_version = %s AND role = 'numerator'",
            (metric_id, version),
        )
        return bool(rows)

    def _binding_window_mode(self, metric_id: str, version: str) -> str | None:
        rows = self._meta.query(
            "SELECT window_mode FROM platform.metric_field_binding "
            "WHERE metric_id = %s AND definition_version = %s AND role = 'numerator'",
            (metric_id, version),
        )
        return str(rows[0]["window_mode"]) if rows else None

    def _window(
        self, d: dict[str, Any], as_of: date, *, mode: str | None = None
    ) -> tuple[date, date]:
        # 绑定的 window_mode 优先于 definition.window_kind：v7 允许 period
        # 指标绑定 instant 事实（如 FIN-BANK-013），编译器按绑定的 instant 取数。
        mode = mode or d["window_kind"]
        if mode == "instant":
            return as_of, as_of
        span = max(int(d["min_window_days"] or 0), MIN_SPAN_DAYS)
        return as_of - timedelta(days=span - 1), as_of

    # ------------------------------------------------------------------ writes
    def _write_compiled(
        self,
        d: dict[str, Any],
        start: date,
        end: date,
        rows: list[dict[str, Any]],
        data_source: str,
        *,
        instant: bool,
    ) -> int:
        fixture = data_source == "fixture"
        params = [
            (
                d["metric_id"],
                d["definition_version"],
                None,
                None,
                row["entityKey"],
                start if instant else None,
                None if instant else start,
                None if instant else end,
                Decimal(str(row["numerator"])) if row["numerator"] is not None else None,
                Decimal(str(row["denominator"])) if row["denominator"] is not None else None,
                start,
                end,
                data_source,
                fixture,
            )
            for row in rows
        ]
        with self._meta.tx() as tx:
            tx.executemany(_OBS_UPSERT, params)
        return len(params)

    def _read_value(self, d: dict[str, Any], start: date, end: date) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"metric_id": d["metric_id"], "internal": True}
        if d["window_kind"] == "instant":
            kwargs["as_of"] = start
        else:
            kwargs["period_start"] = start
            kwargs["period_end"] = end
        return self._service.compute(**kwargs)

    # ------------------------------------------------------------------ routes
    def _compile_route(
        self,
        d: dict[str, Any],
        start: date,
        end: date,
        *,
        apply: bool,
        data_source: str,
        instant: bool,
    ) -> dict[str, Any]:
        item: dict[str, Any] = {"route": "compile"}
        try:
            result = self._compiler.execute(
                d["metric_id"],
                start=start,
                end=end,
                internal=True,
                data_source=data_source,
            )
        except PortError as exc:
            return _failure(item, exc.provider_code, exc.message, stage="compile")
        rows = result["rows"]
        item["rows"] = len(rows)
        if not rows:
            return _failure(item, "E_METRIC_NO_DATA", "compiler returned no entity rows", stage="compile")
        item["sample"] = rows[0]
        item["entityCount"] = len(rows)
        if apply:
            item["rowsWritten"] = self._write_compiled(
                d, start, end, rows, data_source, instant=instant
            )
            try:
                card = self._read_value(d, start, end)
            except PortError as exc:
                item["rowsWrittenNote"] = "观测行已落库，但读取路径仍拒绝出数"
                return _failure(item, exc.provider_code, exc.message, stage="read")
            item["value"] = card["value"]
            item["sampleCount"] = card["sampleCount"]
            item["dataSource"] = card["dataSource"]
            item["definitionVersion"] = card["definitionVersion"]
        return _success(item)

    def _project_route(
        self,
        d: dict[str, Any],
        start: date,
        end: date,
        *,
        apply: bool,
        data_source: str,
    ) -> dict[str, Any]:
        item: dict[str, Any] = {"route": "project"}
        result = self._projector.project(
            metric_id=d["metric_id"],
            window_start=start,
            window_end=end,
            data_source=data_source,
            apply=apply,
        )
        item["rows"] = int(result.get("rowsValid") or 0)
        if not result.get("ok"):
            return _failure(
                item,
                str(result.get("errorCode") or "E_FACT_SOURCE_INVALID"),
                str(result.get("message") or "projector refused the metric"),
                stage="project",
            )
        if item["rows"] == 0:
            return _failure(item, "E_METRIC_NO_DATA", "fact function returned no rows", stage="project")
        if apply:
            item["rowsWritten"] = int(result.get("rowsProjected") or 0)
            try:
                card = self._read_value(d, start, end)
            except PortError as exc:
                item["rowsWrittenNote"] = "观测行已落库，但读取路径仍拒绝出数"
                return _failure(item, exc.provider_code, exc.message, stage="read")
            item["value"] = card["value"]
            item["sampleCount"] = card["sampleCount"]
            item["dataSource"] = card["dataSource"]
            item["definitionVersion"] = card["definitionVersion"]
        return _success(item)

    def _rule_route(self, d: dict[str, Any], as_of: date, *, apply: bool) -> dict[str, Any]:
        # Rule sets have no observation table by design; their output is the
        # triggered rule count returned by /metrics/{id}/rules.
        from .datagen import build_rule_facts
        from .rules import RuleExecutor

        item: dict[str, Any] = {"route": "rule", "rows": 0, "rowsWritten": 0}
        facts = build_rule_facts(self._meta)
        try:
            result = RuleExecutor(self._meta).execute(
                d["metric_id"], facts, as_of=as_of.isoformat()
            )
        except PortError as exc:
            return _failure(item, exc.provider_code, exc.message, stage="rule")
        item["rows"] = int(result.get("factsEvaluated") or 0)
        item["value"] = int(result.get("triggeredCount") or 0)
        item["unevaluatedRules"] = result.get("unevaluatedRules") or []
        return _success(item)

    # -------------------------------------------------------------------- run
    def run(
        self,
        metric_ids: list[str] | None = None,
        *,
        apply: bool = False,
        data_source: str = "synthetic",
        as_of: date = CANONICAL_AS_OF,
    ) -> dict[str, Any]:
        if data_source not in ("fixture", "business", "synthetic"):
            raise ValueError("dataSource must be fixture, business or synthetic")
        definitions = self._definitions(metric_ids)
        results: list[dict[str, Any]] = []
        for d in definitions:
            has_binding = self._has_binding(d["metric_id"], d["definition_version"])
            binding_mode = (
                self._binding_window_mode(d["metric_id"], d["definition_version"])
                if has_binding
                else None
            )
            start, end = self._window(
                d, as_of, mode=binding_mode if not d["fact_function"] else None
            )
            item: dict[str, Any] = {
                "metricId": d["metric_id"],
                "definitionVersion": d["definition_version"],
                "metricKind": d["metric_kind"],
                "outputMode": d["output_mode"],
                "windowKind": d["window_kind"],
                "publishable": bool(d["publishable"]),
                "window": {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "asOf": start.isoformat() if d["window_kind"] == "instant" else None,
                },
            }
            if d["output_mode"] == "rule_set" or d["metric_kind"] == "rule_set":
                item.update(self._rule_route(d, as_of, apply=apply))
            elif d["fact_function"]:
                item.update(
                    self._project_route(d, start, end, apply=apply, data_source=data_source)
                )
            elif self._has_binding(d["metric_id"], d["definition_version"]):
                item.update(
                    self._compile_route(
                        d,
                        start,
                        end,
                        apply=apply,
                        data_source=data_source,
                        instant=binding_mode == "instant",
                    )
                )
            else:
                item.update(
                    _failure(
                        item,
                        "E_METRIC_BINDING_MISSING",
                        "no numerator field binding and no fact_function",
                        stage="route",
                    )
                )
            results.append(item)

        totals = {
            "structurallyComputable": len(results),
            "numeric": sum(1 for r in results if r["outputMode"] != "rule_set"
                           and r["metricKind"] != "rule_set"),
            "ruleSet": sum(1 for r in results if r["outputMode"] == "rule_set"
                          or r["metricKind"] == "rule_set"),
            "succeeded": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "rowsWritten": sum(int(r.get("rowsWritten") or 0) for r in results),
        }
        return {
            "ok": totals["failed"] == 0,
            "apply": apply,
            "dataSource": data_source,
            "asOf": as_of.isoformat(),
            "totals": totals,
            "metrics": results,
        }


def _failure(item: dict[str, Any], code: str, message: str, *, stage: str) -> dict[str, Any]:
    item["status"] = "failed"
    item["stage"] = stage
    item["errorCode"] = code
    item["message"] = message
    item["reasonZh"] = _REASON_ZH.get(code, message)
    return item


def _success(item: dict[str, Any]) -> dict[str, Any]:
    item["status"] = "success"
    return item


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="materialize metric observations")
    parser.add_argument("--config", default="/data/platform.yaml")
    parser.add_argument("--metric", action="append", default=None)
    parser.add_argument("--metric-ids", default=None, help="comma-separated metric ids")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--data-source",
        default="synthetic",
        choices=["fixture", "business", "synthetic"],
    )
    parser.add_argument("--as-of", default=CANONICAL_AS_OF.isoformat())
    args = parser.parse_args(argv)

    ids = list(args.metric or [])
    if args.metric_ids:
        ids.extend(part.strip() for part in args.metric_ids.split(",") if part.strip())
    ids = ids or None

    runtime = assemble(load_config(args.config, None))
    runtime.metadata.open(retry_seconds=10.0)
    report = MetricBackfill(runtime.metadata).run(
        ids,
        apply=args.apply,
        data_source=args.data_source,
        as_of=date.fromisoformat(args.as_of),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0 if report["ok"] or not args.apply else 1


if __name__ == "__main__":
    sys.exit(_main())
