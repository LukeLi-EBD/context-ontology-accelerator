"""Run S1: parse the exported OSI corpus with COA and reconcile with the platform.

The validation call chain is deliberately in-process:

``run_s1`` → ``coa_metrics.osi_parser.parse_osi_yaml`` →
``coa_metrics.validator.validate_metric`` → ``JsonDataSourceLookup``.

The platform API is not called here; the snapshot exported in step 1 is the
only input.
"""

from __future__ import annotations

import argparse
import inspect
import json
import platform as platform_module
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from coa_local_providers import JsonDataSourceLookup
from coa_local_providers.osi_bridge import metric_body_from_osi
from coa_local_providers.win_compat import ensure_resource_module

ensure_resource_module()

from coa_metrics.osi_parser import OsiDocument, OsiMetric, parse_osi_yaml, serialize_osi_yaml  # noqa: E402
from coa_metrics.validator import BLOCKING_CHECKS, validate_metric  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
SQL_BLOCKING = set(BLOCKING_CHECKS)


class RecordingLookup(JsonDataSourceLookup):
    """JsonDataSourceLookup that records who asked it and from where."""

    def __init__(self, snapshot: dict[str, Any]) -> None:
        super().__init__(snapshot)
        self.calls: list[dict[str, Any]] = []
        self.stacks: dict[str, list[traceback.FrameSummary]] = {}

    def _record(self, method: str, data_source_id: str, table: str | None) -> None:
        self.calls.append({"method": method, "dataSourceId": data_source_id, "table": table})
        if method not in self.stacks:
            self.stacks[method] = traceback.extract_stack()[:-2]

    def data_source_exists(self, data_source_id: str) -> bool:
        self._record("data_source_exists", data_source_id, None)
        return super().data_source_exists(data_source_id)

    def table_exists(self, data_source_id: str, table_name: str) -> bool:
        self._record("table_exists", data_source_id, table_name)
        return super().table_exists(data_source_id, table_name)

    def get_table_columns(self, data_source_id: str, table_name: str):  # type: ignore[override]
        self._record("get_table_columns", data_source_id, table_name)
        return super().get_table_columns(data_source_id, table_name)

    def known_tables(self, data_source_id: str) -> set[str]:
        self._record("known_tables", data_source_id, None)
        return super().known_tables(data_source_id)

    def catalog_available(self, data_source_id: str) -> bool:
        self._record("catalog_available", data_source_id, None)
        return super().catalog_available(data_source_id)

    def table_rejection_reason(self, data_source_id: str, table_name: str) -> str | None:
        self._record("table_rejection_reason", data_source_id, table_name)
        return super().table_rejection_reason(data_source_id, table_name)


def canonical(metric: OsiMetric) -> dict[str, Any]:
    extension = metric.custom_extensions
    return {
        "name": metric.name,
        "description": metric.description,
        "expression": [[item.dialect, item.expression] for item in metric.expression],
        "ai_context": None
        if metric.ai_context is None
        else [
            metric.ai_context.synonyms,
            metric.ai_context.instructions,
            metric.ai_context.examples,
        ],
        "extension": None
        if extension is None
        else [
            extension.data_source_id,
            extension.source_table,
            extension.unit,
            extension.return_type,
            extension.time_dimension,
            extension.ontology_concepts,
            extension.defined_by,
            extension.effective_from,
            extension.label,
        ],
    }


def canonical_document(document: OsiDocument) -> dict[str, Any]:
    return {
        "spec": document.osi_spec_version,
        "datasets": [
            [item.name, item.source, item.data_source_id, item.description, item.synonyms]
            for item in document.datasets
        ],
        "metrics": [canonical(metric) for metric in document.metrics],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        default=str(REPO_ROOT / "doc" / "_evidence-coa-integration" / "s1-2026-11-08" / "snapshot"),
    )
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT / "doc" / "_evidence-coa-integration" / "s1-2026-11-08"),
    )
    args = parser.parse_args()

    snapshot = Path(args.snapshot)
    out = Path(args.out)
    report_dir = out / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    yaml_text = (snapshot / "metrics.osi.yaml").read_text(encoding="utf-8")
    parsed = parse_osi_yaml(yaml_text)
    if parsed.document is None:
        print("PARSE_FAILED", [error.message for error in parsed.errors][:5])
        return 1

    metrics = parsed.document.metrics
    print(f"parse: metrics={len(metrics)} errors={len(parsed.errors)} warnings={len(parsed.warnings)}")

    # Round-trip: serialize with COA, parse again, compare canonical forms.
    reparsed = parse_osi_yaml(serialize_osi_yaml(parsed.document))
    roundtrip_ok = reparsed.document is not None and canonical_document(
        reparsed.document
    ) == canonical_document(parsed.document)
    print(f"round_trip: ok={roundtrip_ok} errors={len(reparsed.errors)}")

    catalog = json.loads((snapshot / "catalog.json").read_text(encoding="utf-8"))
    reconcile_inputs = json.loads(
        (snapshot / "reconcile_inputs.json").read_text(encoding="utf-8")
    )

    per_metric: dict[str, dict[str, Any]] = {}
    all_calls: list[dict[str, Any]] = []
    stacks: dict[str, list[traceback.FrameSummary]] = {}
    for metric in metrics:
        lookup = RecordingLookup(catalog)
        body = metric_body_from_osi(metric)
        result = validate_metric(body, data_sources_lookup=lookup)
        blocking = [error for error in result.errors if error["check"] in SQL_BLOCKING]
        per_metric[metric.name] = {
            "valid": result.valid,
            "coaSqlOk": len(blocking) == 0,
            "blockingChecks": sorted({error["check"] for error in blocking}),
            "errors": result.errors,
            "warnings": result.warnings,
            "lookupCalls": len(lookup.calls),
            "sqlSource": reconcile_inputs.get(metric.name, {}).get("sqlSource"),
            "sourceTable": body["sourceTable"],
        }
        all_calls.extend(
            {**call, "metricId": metric.name} for call in lookup.calls
        )
        for method, frames in lookup.stacks.items():
            stacks.setdefault(method, frames)

    manifest_counts = {
        "total": len(reconcile_inputs),
        "publishable": sum(1 for item in reconcile_inputs.values() if item["publishable"]),
        "executable": sum(1 for item in reconcile_inputs.values() if item["executable"]),
        "both": sum(
            1
            for item in reconcile_inputs.values()
            if item["publishable"] and item["executable"]
        ),
    }
    print(f"manifest: {manifest_counts}")

    diffs: list[dict[str, Any]] = []
    categories: Counter[str] = Counter()
    metric_categories: dict[str, str] = {}
    for metric_id, inputs in reconcile_inputs.items():
        result = per_metric[metric_id]
        executable = inputs["executable"]
        coa_sql_ok = result["coaSqlOk"]
        if executable and coa_sql_ok:
            category = "agree_executable"
        elif executable and not coa_sql_ok:
            category = "platform_executable_coa_rejected"
        elif not executable and coa_sql_ok:
            category = (
                "platform_not_executable_but_sql_present:"
                f"{inputs.get('executionReasonCode') or 'unknown'}"
            )
        else:
            category = "agree_not_executable"
        categories[category] += 1
        metric_categories[metric_id] = category
        if category.startswith(("platform_executable_coa_rejected", "platform_not_executable_but_sql_present")):
            diffs.append(
                {
                    "metricId": metric_id,
                    "category": category,
                    "executable": executable,
                    "publishable": inputs["publishable"],
                    "executionReasonCode": inputs.get("executionReasonCode"),
                    "executionReason": inputs.get("executionReason"),
                    "sqlSource": inputs.get("sqlSource"),
                    "coaSqlOk": coa_sql_ok,
                    "coaBlockingChecks": result["blockingChecks"],
                }
            )

    validation_payload = {
        "parse": {
            "metrics": len(metrics),
            "errors": [error.__dict__ for error in parsed.errors],
            "warnings": [warning.__dict__ for warning in parsed.warnings],
            "roundTripOk": roundtrip_ok,
            "roundTripErrors": [error.__dict__ for error in reparsed.errors],
        },
        "manifestCounts": manifest_counts,
        "coaCounts": {
            "sqlOk": sum(1 for item in per_metric.values() if item["coaSqlOk"]),
            "valid": sum(1 for item in per_metric.values() if item["valid"]),
            "sqlSources": dict(Counter(item["sqlSource"] for item in per_metric.values())),
        },
        "categories": dict(categories),
        "differences": diffs,
        "metrics": per_metric,
    }
    (report_dir / "validation.json").write_text(
        json.dumps(validation_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# S1 指标校验对账（COA validator → JsonDataSourceLookup）",
        "",
        f"- OSI 文档解析：{len(metrics)}/{manifest_counts['total']} 条，errors={len(parsed.errors)}",
        f"- round-trip 语义一致：{roundtrip_ok}",
        f"- 平台 manifest：total={manifest_counts['total']} publishable={manifest_counts['publishable']} "
        f"executable={manifest_counts['executable']} both={manifest_counts['both']}",
        f"- COA SQL 通过：{validation_payload['coaCounts']['sqlOk']}；COA 整体 valid："
        f"{validation_payload['coaCounts']['valid']}",
        "",
        "| 分类 | 条数 |",
        "| --- | --- |",
    ]
    lines += [f"| {name} | {count} |" for name, count in sorted(categories.items())]
    lines += [
        "",
        "## 差异逐条",
        "",
        "| metric | executable | publishable | sqlSource | COA SQL | 原因 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in diffs:
        reason = item["executionReason"] or item["executionReasonCode"] or ""
        lines.append(
            f"| {item['metricId']} | {item['executable']} | {item['publishable']} | "
            f"{item['sqlSource']} | {item['coaSqlOk']} | {reason[:80]} |"
        )
    lines += [
        "",
        "## 全量逐条（85 条）",
        "",
        "| metric | publishable | executable | sqlSource | COA SQL | 分类 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for metric_id in sorted(reconcile_inputs):
        inputs = reconcile_inputs[metric_id]
        result = per_metric[metric_id]
        lines.append(
            f"| {metric_id} | {inputs['publishable']} | {inputs['executable']} | "
            f"{result['sqlSource']} | {result['coaSqlOk']} | {metric_categories[metric_id]} |"
        )
    (report_dir / "reconcile.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    callchain = [
        "S1 调用链证据（全部在独立 venv 内、进程内完成；未调用 platform API）",
        "",
        f"validate_metric source: {inspect.getsourcefile(validate_metric)}",
        f"JsonDataSourceLookup source: {inspect.getsourcefile(JsonDataSourceLookup)}",
        f"lookup calls total: {len(all_calls)}",
        "",
        "## 方法级 stack（首次调用）",
    ]
    for method, frames in sorted(stacks.items()):
        callchain.append(f"\n### {method}")
        callchain += [
            f"  {frame.filename}:{frame.lineno} in {frame.name}" for frame in frames[-4:]
        ]
    callchain += ["", "## 调用样本（每个 method 取前 10 条）"]
    per_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for call in all_calls:
        per_method[call["method"]].append(call)
    for method in sorted(per_method):
        for call in per_method[method][:10]:
            callchain.append(
                f"  {method}: {call['metricId']} -> "
                f"table_exists/get_columns({call['dataSourceId']!r}, {call['table']!r})"
            )
    (report_dir / "callchain.txt").write_text("\n".join(callchain) + "\n", encoding="utf-8")

    env_lines = [
        f"python={sys.version.split()[0]}",
        f"platform={platform_module.platform()}",
        f"executable={sys.executable}",
        "PYTHONPATH entries:",
    ] + [f"  {entry}" for entry in sys.path if "coa" in entry.lower() or "agentABC" in entry]
    env_lines += [
        "",
        "AWS 环境变量存在性（本次不应连接 AWS）：",
    ]
    env_lines += [
        f"  {name}: {'set' if __import__('os').environ.get(name) else 'unset'}"
        for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_PROFILE", "AWS_REGION")
    ]
    (report_dir / "env.txt").write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    print(f"coa: sqlOk={validation_payload['coaCounts']['sqlOk']} "
          f"valid={validation_payload['coaCounts']['valid']} sources={validation_payload['coaCounts']['sqlSources']}")
    print(f"categories={dict(categories)}")
    print(f"lookup_calls={len(all_calls)}")
    print(f"reports={report_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
