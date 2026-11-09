"""O-03: T-Box change impact analysis.

Given a change set (``from`` version -> ``to`` version) this module answers the
review question "what does this touch?":

* affected classes / properties (added, removed, domain/range modified, or the
  subject of any changed T-Box triple);
* instance counts per affected class, read live from the A-Box; ``None`` with an
  explicit reason when no A-Box is configured (never guessed as 0);
* dependent metrics / rules (metric_definition + metric_field_binding +
  data_dictionary binding chain and text match) and term entries whose
  canonical class is affected;
* a verification block that recounts a sample of classes and reports whether
  the recount matches the listed numbers.

Everything is read-only and sorted deterministically, so the same versions
produce the same checklist byte-for-byte (except ``computedAt``).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from . import healthboard
from .errors import PortError
from .termlex import TermLexicon

SAMPLE_LIMIT = 10
MAX_AGGREGATE_ROWS = 2000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _local_name(iri: str) -> str:
    for sep in ("#", "/", ":"):
        if sep in iri:
            tail = iri.rsplit(sep, 1)[-1]
            if tail:
                return tail
    return iri


def _change_items(values: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in values or []:
        if isinstance(raw, dict):
            iri = raw.get("property") or raw.get("iri") or raw.get("classIri")
            items.append({
                "iri": str(iri) if iri else None,
                "from": raw.get("from") or raw.get("fromIri"),
                "to": raw.get("to") or raw.get("toIri"),
                "raw": raw,
            })
        else:
            items.append({"iri": str(raw), "from": None, "to": None, "raw": raw})
    return items


def _expand_iris(value: Any) -> list[str]:
    """domain/range 的 from/to 是 IRI 列表（多值），统一展开为字符串列表。"""
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item]
    return [str(value)] if value else []


def _change_iris(items: list[dict[str, Any]]) -> list[str]:
    iris: list[str] = []
    for item in items:
        iris.extend(_expand_iris(item.get("from")))
        iris.extend(_expand_iris(item.get("to")))
    return iris


def _aggregate(runtime: Any, from_graph: str | None, to_graph: str) -> dict[str, Any]:
    """Count changed triples grouped by subject (class) and predicate (property)."""
    if not from_graph:
        return {
            "byClass": [], "byProperty": [],
            "unclassified": {"addedTriples": 0, "removedTriples": 0},
            "empty": True, "emptyReason": "无基线版本，无法按类/属性聚合",
            "method": "SPARQL GROUP BY ?s ?p over (to MINUS from)",
        }
    classes = set(healthboard._classes(runtime, from_graph).get("iris") or [])
    classes.update(healthboard._classes(runtime, to_graph).get("iris") or [])
    properties = set(healthboard._properties(runtime, from_graph).get("iris") or [])
    properties.update(healthboard._properties(runtime, to_graph).get("iris") or [])

    def _rows(direction: str) -> list[dict[str, Any]]:
        if direction == "added":
            query = (
                f"SELECT ?s ?p (COUNT(*) AS ?n) WHERE {{ GRAPH <{to_graph}> {{ ?s ?p ?o }} "
                f"MINUS {{ GRAPH <{from_graph}> {{ ?s ?p ?o }} }} }} "
                f"GROUP BY ?s ?p LIMIT {MAX_AGGREGATE_ROWS}"
            )
        else:
            query = (
                f"SELECT ?s ?p (COUNT(*) AS ?n) WHERE {{ GRAPH <{from_graph}> {{ ?s ?p ?o }} "
                f"MINUS {{ GRAPH <{to_graph}> {{ ?s ?p ?o }} }} }} "
                f"GROUP BY ?s ?p LIMIT {MAX_AGGREGATE_ROWS}"
            )
        result = runtime.graph.query(query)
        rows: list[dict[str, Any]] = []
        for row in result.get("bindings") or []:
            subject = healthboard._term(row, "s")
            predicate = healthboard._term(row, "p")
            count = healthboard._as_int(healthboard._term(row, "n"))
            if subject and predicate:
                rows.append({"s": subject, "p": predicate, "n": count})
        return rows

    by_class: dict[str, dict[str, int]] = {}
    by_property: dict[str, dict[str, int]] = {}
    unclassified = {"addedTriples": 0, "removedTriples": 0}
    total_changes = 0

    def _bump(bucket: dict[str, dict[str, int]], key: str, field: str, count: int) -> None:
        entry = bucket.setdefault(key, {"addedTriples": 0, "removedTriples": 0})
        entry[field] += count

    for direction, field in (("added", "addedTriples"), ("removed", "removedTriples")):
        for row in _rows(direction):
            total_changes += row["n"]
            classified = False
            if row["s"] in classes:
                _bump(by_class, row["s"], field, row["n"])
                classified = True
            if row["p"] in properties:
                _bump(by_property, row["p"], field, row["n"])
                classified = True
            if not classified:
                unclassified[field] += row["n"]

    return {
        "byClass": [
            {"iri": key, "label": _local_name(key), **value}
            for key, value in sorted(by_class.items())
        ],
        "byProperty": [
            {"iri": key, "label": _local_name(key), **value}
            for key, value in sorted(by_property.items())
        ],
        "unclassified": unclassified,
        "empty": total_changes == 0,
        "emptyReason": "两版本无三元组差异" if total_changes == 0 else None,
        "method": "SPARQL GROUP BY ?s ?p over (to MINUS from)",
        "rowLimit": MAX_AGGREGATE_ROWS,
    }


def _instance_block(runtime: Any, class_iris: list[str]) -> dict[str, Any]:
    graphs = healthboard._abox_graphs(runtime)
    if not graphs:
        return {
            "total": None,
            "byClass": [{"iri": iri, "label": _local_name(iri), "instances": None}
                        for iri in class_iris],
            "source": "A-Box 未配置",
            "note": "没有 A-Box 图，实例数不可算；未以 0 代替",
        }
    counts = healthboard._instance_classes(runtime, graphs)
    by_class = [
        {"iri": iri, "label": _local_name(iri), "instances": int(counts.get(iri, 0))}
        for iri in class_iris
    ]
    affected_total = sum(item["instances"] for item in by_class)
    return {
        "total": healthboard._instance_total(runtime, graphs),
        "affectedInstances": affected_total,
        "byClass": by_class,
        "graphs": graphs,
        "source": "SPARQL COUNT(DISTINCT ?s) over A-Box graphs",
        "note": None,
    }


def _verify_sample(runtime: Any, instance_block: dict[str, Any], sample: int) -> dict[str, Any]:
    if instance_block.get("total") is None:
        return {
            "sampled": [],
            "consistent": None,
            "reason": "无 A-Box，实例数不可重算",
            "source": instance_block.get("source"),
        }
    graphs = instance_block.get("graphs") or []
    items = instance_block.get("byClass") or []
    picked = [item for item in items if item.get("iri") and ">" not in item["iri"]][:sample]
    sampled: list[dict[str, Any]] = []
    consistent = True
    for item in picked:
        query = (
            f"SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {{ VALUES ?g {{ {healthboard._values(graphs)} }} "
            f"GRAPH ?g {{ ?s a <{item['iri']}> }} }}"
        )
        result = runtime.graph.query(query)
        rows = result.get("bindings") or []
        recounted = healthboard._as_int(healthboard._term(rows[0], "n")) if rows else 0
        ok = recounted == item["instances"]
        consistent = consistent and ok
        sampled.append({
            "iri": item["iri"],
            "listed": item["instances"],
            "recounted": recounted,
            "consistent": ok,
        })
    return {
        "sampled": sampled,
        "consistent": consistent if sampled else None,
        "reason": None if sampled else "无受影响的类可抽样",
        "source": "独立 SPARQL 重算（逐类 COUNT DISTINCT）",
    }


def _metric_rows(metadata: Any) -> tuple[list, list, list, list[dict[str, Any]]]:
    notes: list[dict[str, Any]] = []
    try:
        metrics = metadata.query(
            "SELECT metric_id, name_zh, display_name, definition, formula_text, "
            "denominator_text, rule_set_json FROM platform.metric_definition "
            "ORDER BY metric_id"
        )
    except Exception as exc:
        metrics = []
        notes.append({"source": "metric_definition", "error": str(exc)})
    try:
        bindings = metadata.query(
            "SELECT metric_id, role, fact_table, entity_column, value_expr "
            "FROM platform.metric_field_binding"
        )
    except Exception as exc:
        bindings = []
        notes.append({"source": "metric_field_binding", "error": str(exc)})
    try:
        dictionary = metadata.query(
            "SELECT table_name, column_name, property_iri FROM platform.data_dictionary "
            "WHERE property_iri IS NOT NULL"
        )
    except Exception as exc:
        dictionary = []
        notes.append({"source": "data_dictionary", "error": str(exc)})
    return metrics, bindings, dictionary, notes


def _dependencies(
    metadata: Any, affected_classes: list[str], affected_properties: list[str], terms_block: dict[str, Any]
) -> dict[str, Any]:
    metrics, bindings, dictionary, notes = _metric_rows(metadata)
    tokens = {iri.lower() for iri in affected_classes + affected_properties}
    tokens.update(_local_name(iri).lower() for iri in affected_classes + affected_properties)

    columns: set[str] = set()
    for row in dictionary:
        prop = str(row.get("property_iri") or "")
        if prop in affected_properties:
            columns.add(str(row.get("column_name") or "").lower())

    metric_hits: dict[str, dict[str, Any]] = {}
    binding_by_metric: dict[str, list[dict[str, Any]]] = {}
    for row in bindings:
        binding_by_metric.setdefault(str(row.get("metric_id")), []).append(row)

    for row in metrics:
        metric_id = str(row.get("metric_id"))
        matched: list[str] = []
        haystack = " ".join(
            str(row.get(key) or "")
            for key in ("name_zh", "display_name", "definition", "formula_text", "denominator_text")
        ).lower()
        for token in tokens:
            if token and token in haystack:
                matched.append(f"text:{token}")
        for binding in binding_by_metric.get(metric_id, []):
            hay = " ".join(
                str(binding.get(key) or "")
                for key in ("fact_table", "entity_column", "value_expr")
            ).lower()
            if columns and any(col and col in hay for col in columns):
                matched.append(
                    "binding:"
                    + f"{binding.get('fact_table')}.{binding.get('entity_column')}"
                )
        if matched:
            metric_hits[metric_id] = {
                "metricId": metric_id,
                "name": row.get("name_zh") or row.get("display_name"),
                "matchedBy": sorted(set(matched)),
                "source": "metric_definition + metric_field_binding + data_dictionary",
            }

    rules: list[dict[str, Any]] = []
    for row in metrics:
        metric_id = str(row.get("metric_id"))
        raw_rules = row.get("rule_set_json")
        if isinstance(raw_rules, str):
            try:
                raw_rules = json.loads(raw_rules)
            except ValueError:
                raw_rules = None
        if not isinstance(raw_rules, list):
            continue
        serialized = json.dumps(raw_rules, ensure_ascii=False).lower()
        text_match = any(token and token in serialized for token in tokens)
        if not text_match and metric_id not in metric_hits:
            continue
        for rule in raw_rules:
            if not isinstance(rule, dict):
                continue
            rules.append({
                "metricId": metric_id,
                "ruleId": rule.get("ruleId") or rule.get("id") or rule.get("name"),
                "level": rule.get("level") or rule.get("severity"),
                "matchedBy": "rule_set_text" if text_match else "dependent_metric",
                "source": "metric_definition.rule_set_json",
            })

    return {
        "metrics": [metric_hits[key] for key in sorted(metric_hits)],
        "rules": sorted(rules, key=lambda item: (item["metricId"], str(item["ruleId"]))),
        "terms": terms_block.get("items") or [],
        "notes": notes,
        "empty": not metric_hits and not rules,
        "emptyReason": None if (metric_hits or rules) else "无指标或规则依赖命中",
        "method": (
            "metric_definition 文本字段（name_zh/display_name/definition/formula_text/"
            "denominator_text）token 命中 + data_dictionary.property_iri -> column -> "
            "metric_field_binding 字段链；规则来自 rule_set_json"
        ),
    }


def _term_block(runtime: Any, to_graph: str, affected: list[str]) -> dict[str, Any]:
    try:
        lexicon = TermLexicon.build(runtime.graph, to_graph)
        entries = lexicon.entries
    except Exception as exc:
        return {"items": [], "empty": True, "emptyReason": f"术语库不可读：{exc}",
                "source": "TermLexicon.build"}
    wanted = set(affected)
    items = [
        {
            "surface": entry.get("surface"),
            "canonical": entry.get("canonical"),
            "lang": entry.get("lang"),
            "source": entry.get("source"),
            "canonicalLabel": _local_name(str(entry.get("canonical") or "")),
        }
        for entry in entries
        if entry.get("canonical") in wanted
    ]
    items.sort(key=lambda item: (str(item["canonical"]), str(item["surface"]), str(item["lang"])))
    return {
        "items": items,
        "count": len(items),
        "empty": not items,
        "emptyReason": None if items else "受影响类/属性没有术语条目",
        "source": "TermLexicon（term:TermEntry / prefLabel / altLabel）",
    }


def analyze(
    runtime: Any, from_version: str | None = None, to_version: str | None = None,
    sample: int = 5,
) -> dict[str, Any]:
    """Read-only impact checklist for one change set."""
    pointer = healthboard._pointer(runtime)
    if not to_version:
        to_version = (pointer or {}).get("versionId")
    if not to_version:
        raise PortError(
            code="Conflict",
            message="no tbox/current pointer; pass ?to=<version>",
            provider="platform", provider_code="E_DIFF_NO_CURRENT", retryable=False,
        )
    to_row = healthboard._version(runtime, to_version)
    if not from_version:
        versions = [item for item in runtime.ontology.list_versions()
                    if item.get("status") != "deprecated"]
        ids = [str(item.get("id")) for item in versions]
        if to_version not in ids:
            raise PortError(
                code="Conflict", message="current version is not in the version list",
                provider="platform", provider_code="E_DIFF_NO_PREVIOUS_BASELINE",
                details={"to": to_version}, retryable=False,
            )
        baseline = healthboard._previous_version(versions, to_version)
        if baseline is None:
            return _empty_report(to_row, None, "当前版本没有基线版本，无法做影响分析")
        from_version = baseline
    from_row = healthboard._version(runtime, from_version)

    diff = runtime.ontology.diff(from_version, to_version)
    summary = diff.get("summary") or {}

    added_classes = [str(item) for item in summary.get("addedClasses") or []]
    removed_classes = [str(item) for item in summary.get("removedClasses") or []]
    added_props = [str(item) for item in summary.get("addedProperties") or []]
    removed_props = [str(item) for item in summary.get("removedProperties") or []]
    domain_changes = _change_items(summary.get("domainChanges"))
    range_changes = _change_items(summary.get("rangeChanges"))

    aggregates = _aggregate(runtime, from_row.get("graph"), to_row.get("graph"))
    aggregate_classes = [item["iri"] for item in aggregates["byClass"]]
    aggregate_props = [item["iri"] for item in aggregates["byProperty"]]

    class_iris = sorted(set(
        added_classes + removed_classes + aggregate_classes
        + _change_iris(domain_changes + range_changes)
    ))
    prop_iris = sorted(set(
        added_props + removed_props + aggregate_props
        + [item["iri"] for item in domain_changes + range_changes if item["iri"]]
    ))

    class_change: dict[str, str] = {}
    for iri in added_classes:
        class_change[iri] = "added"
    for iri in removed_classes:
        class_change.setdefault(iri, "removed")
    for iri in aggregate_classes:
        class_change.setdefault(iri, "modified")

    prop_change: dict[str, str] = {}
    for iri in added_props:
        prop_change[iri] = "added"
    for iri in removed_props:
        prop_change.setdefault(iri, "removed")
    for iri in aggregate_props:
        prop_change.setdefault(iri, "modified")

    by_class_counts = {item["iri"]: item for item in aggregates["byClass"]}
    affected_classes = [
        {
            "iri": iri,
            "label": _local_name(iri),
            "change": class_change.get(iri, "modified"),
            "addedTriples": by_class_counts.get(iri, {}).get("addedTriples", 0),
            "removedTriples": by_class_counts.get(iri, {}).get("removedTriples", 0),
        }
        for iri in class_iris
    ]
    by_prop_counts = {item["iri"]: item for item in aggregates["byProperty"]}
    affected_properties = [
        {
            "iri": iri,
            "label": _local_name(iri),
            "change": prop_change.get(iri, "modified"),
            "addedTriples": by_prop_counts.get(iri, {}).get("addedTriples", 0),
            "removedTriples": by_prop_counts.get(iri, {}).get("removedTriples", 0),
            "domainChanges": [item["raw"] for item in domain_changes if item["iri"] == iri],
            "rangeChanges": [item["raw"] for item in range_changes if item["iri"] == iri],
        }
        for iri in prop_iris
    ]

    instances = _instance_block(runtime, class_iris)
    verification = _verify_sample(runtime, instances, max(1, min(sample, SAMPLE_LIMIT)))
    terms_block = _term_block(runtime, to_row.get("graph"), class_iris + prop_iris)
    dependencies = _dependencies(runtime.metadata, class_iris, prop_iris, terms_block)

    inputs = {
        "from": {
            "versionId": from_row.get("id"),
            "semver": from_row.get("semver"),
            "contentHash": from_row.get("contentHash"),
            "tripleCount": from_row.get("tripleCount"),
        },
        "to": {
            "versionId": to_row.get("id"),
            "semver": to_row.get("semver"),
            "contentHash": to_row.get("contentHash"),
            "tripleCount": to_row.get("tripleCount"),
        },
    }
    return {
        "from": from_version,
        "to": to_version,
        "changeSet": {
            "counts": {
                "addedTriples": healthboard._as_int(summary.get("addedTriples")),
                "removedTriples": healthboard._as_int(summary.get("removedTriples")),
                "addedClasses": len(added_classes),
                "removedClasses": len(removed_classes),
                "addedProperties": len(added_props),
                "removedProperties": len(removed_props),
                "domainChanges": len(domain_changes),
                "rangeChanges": len(range_changes),
            },
            "addedClasses": added_classes,
            "removedClasses": removed_classes,
            "addedProperties": added_props,
            "removedProperties": removed_props,
            "domainChanges": [item["raw"] for item in domain_changes],
            "rangeChanges": [item["raw"] for item in range_changes],
            "breaking": bool(diff.get("breaking")),
            "breakingItems": diff.get("breakingItems") or diff.get("impacts") or [],
        },
        "affected": {
            "classes": affected_classes,
            "properties": affected_properties,
            "instances": instances,
        },
        "aggregations": aggregates,
        "dependencies": dependencies,
        "verification": verification,
        "inputs": inputs,
        "inputsFingerprint": _sha256({
            "from": inputs["from"]["contentHash"],
            "to": inputs["to"]["contentHash"],
            "diffFingerprint": _sha256(diff),
        }),
        "empty": not (class_iris or prop_iris or dependencies["metrics"] or dependencies["rules"]),
        "emptyReason": (
            None if (class_iris or prop_iris or dependencies["metrics"] or dependencies["rules"])
            else "两版本在类、属性、指标、规则上均无受影响项"
        ),
        "computedAt": _now(),
        "source": "runtime.ontology.diff + SPARQL + metric/term 注册表",
        "readOnly": True,
    }


def _empty_report(to_row: dict[str, Any], from_row: dict[str, Any] | None, reason: str) -> dict[str, Any]:
    return {
        "from": (from_row or {}).get("id"),
        "to": to_row.get("id"),
        "changeSet": {"counts": {}, "addedClasses": [], "removedClasses": [],
                      "addedProperties": [], "removedProperties": [],
                      "domainChanges": [], "rangeChanges": [],
                      "breaking": False, "breakingItems": []},
        "affected": {
            "classes": [], "properties": [],
            "instances": {"total": None, "byClass": [], "note": reason},
        },
        "aggregations": {"byClass": [], "byProperty": [],
                         "unclassified": {"addedTriples": 0, "removedTriples": 0},
                         "empty": True, "emptyReason": reason},
        "dependencies": {"metrics": [], "rules": [], "terms": [], "empty": True,
                         "emptyReason": reason, "notes": []},
        "verification": {"sampled": [], "consistent": None, "reason": reason},
        "inputs": {},
        "inputsFingerprint": None,
        "empty": True,
        "emptyReason": reason,
        "computedAt": _now(),
        "source": "runtime.ontology.diff + SPARQL + metric/term 注册表",
        "readOnly": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Exportable checklist (deterministic apart from the timestamp)."""
    lines = [
        f"# T-Box 变更影响清单 {report.get('from')} -> {report.get('to')}",
        "",
        f"- 输入指纹：`{report.get('inputsFingerprint')}`",
        f"- 差异：+{report['changeSet']['counts'].get('addedTriples', 0)} / "
        f"-{report['changeSet']['counts'].get('removedTriples', 0)} 三元组",
        f"- 破坏性变更：{'是' if report['changeSet'].get('breaking') else '否'}",
        "",
        "## 受影响类",
        "| 类 | 变更 | 新增三元组 | 删除三元组 | 实例数 |",
        "| --- | --- | --- | --- | --- |",
    ]
    instance_counts = {
        item["iri"]: item["instances"]
        for item in report["affected"]["instances"].get("byClass") or []
    }
    for item in report["affected"]["classes"]:
        lines.append(
            f"| {item['label']} | {item['change']} | {item['addedTriples']} | "
            f"{item['removedTriples']} | {instance_counts.get(item['iri'])} |"
        )
    if not report["affected"]["classes"]:
        lines.append("| （无） | - | - | - | - |")
    lines += [
        "",
        "## 受影响属性",
        "| 属性 | 变更 | 新增三元组 | 删除三元组 |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["affected"]["properties"]:
        lines.append(
            f"| {item['label']} | {item['change']} | {item['addedTriples']} | {item['removedTriples']} |"
        )
    if not report["affected"]["properties"]:
        lines.append("| （无） | - | - | - |")
    lines += ["", "## 依赖指标与规则", "| 指标 | 命中依据 | 规则 |", "| --- | --- | --- |"]
    rules_by_metric: dict[str, list[str]] = {}
    for rule in report["dependencies"].get("rules") or []:
        rules_by_metric.setdefault(rule["metricId"], []).append(str(rule["ruleId"]))
    for metric in report["dependencies"].get("metrics") or []:
        rules = ", ".join(sorted(rules_by_metric.get(metric["metricId"], []))) or "-"
        lines.append(f"| {metric['metricId']} {metric.get('name') or ''} | "
                     f"{', '.join(metric['matchedBy'])} | {rules} |")
    if not report["dependencies"].get("metrics"):
        lines.append("| （无） | - | - |")
    lines += ["", "## 术语", "| 术语 | 归属类 | 语言 |", "| --- | --- | --- |"]
    for term in report["dependencies"].get("terms") or []:
        lines.append(f"| {term['surface']} | {term.get('canonicalLabel')} | {term.get('lang')} |")
    if not report["dependencies"].get("terms"):
        lines.append("| （无） | - | - |")
    verification = report["verification"]
    lines += [
        "",
        "## 抽样重算",
        f"- 一致：{verification.get('consistent')}",
        f"- 说明：{verification.get('reason') or verification.get('source')}",
    ]
    for item in verification.get("sampled") or []:
        lines.append(
            f"- {item['iri']}：清单 {item['listed']} / 重算 {item['recounted']} "
            f"-> {'一致' if item['consistent'] else '不一致'}"
        )
    return "\n".join(lines) + "\n"


def export(report: dict[str, Any], fmt: str = "json") -> tuple[str, str, str]:
    """Return (filename, media_type, body)."""
    suffix = {"json": "json", "markdown": "md", "md": "md", "csv": "csv"}.get(fmt)
    if not suffix:
        raise PortError(
            code="InvalidArgument", message=f"unsupported export format: {fmt}",
            provider="platform", provider_code="E_IMPACT_EXPORT_FORMAT",
            details={"allowed": ["json", "markdown", "csv"]},
        )
    base = f"impact-{report.get('from') or 'none'}-to-{report.get('to')}"
    if suffix == "json":
        return f"{base}.json", "application/json", json.dumps(report, ensure_ascii=False, indent=2)
    if suffix == "md":
        return f"{base}.md", "text/markdown; charset=utf-8", render_markdown(report)
    instance_counts = {
        item["iri"]: item["instances"]
        for item in report["affected"]["instances"].get("byClass") or []
    }
    rows = ["kind,iri,change,addedTriples,removedTriples,instances"]
    for item in report["affected"]["classes"]:
        rows.append(f"class,{item['iri']},{item['change']},{item['addedTriples']},"
                    f"{item['removedTriples']},{instance_counts.get(item['iri'])}")
    for item in report["affected"]["properties"]:
        rows.append(f"property,{item['iri']},{item['change']},{item['addedTriples']},"
                    f"{item['removedTriples']},")
    return f"{base}.csv", "text/csv; charset=utf-8", "\n".join(rows) + "\n"
