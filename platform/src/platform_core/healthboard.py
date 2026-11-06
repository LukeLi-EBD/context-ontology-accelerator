"""B-04 read-only health dashboard and T-Box diff aggregation.

No write path exists here. Every number is either queried live or reported as
``None`` with an explicit reason; the dashboard never substitutes a guess.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters.metadata_pg import SUPPORTED_SCHEMA_VERSION
from .errors import PortError
from .ontology_lifecycle import summarize as _lifecycle_summary

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
RDF_TYPE = RDF + "type"
RDFS_LABEL = RDFS + "label"
SKOS_PREF = SKOS + "prefLabel"

EXAMPLE_LIMIT = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _term(binding: dict[str, Any], name: str) -> str | None:
    term = (binding.get("values") or {}).get(name)
    if not isinstance(term, dict):
        return None
    if term.get("kind") == "iri":
        return term.get("iri")
    if term.get("kind") == "bnode":
        return term.get("label")
    return term.get("value")


def _term_json(binding: dict[str, Any], name: str) -> dict[str, Any] | None:
    term = (binding.get("values") or {}).get(name)
    if not isinstance(term, dict):
        return None
    if term.get("kind") == "iri":
        return {"kind": "iri", "value": term.get("iri")}
    if term.get("kind") == "bnode":
        return {"kind": "bnode", "value": term.get("label")}
    payload: dict[str, Any] = {"kind": "literal", "value": term.get("value")}
    if term.get("datatype"):
        payload["datatype"] = term.get("datatype")
    return payload


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _pointer(runtime: Any) -> dict[str, Any] | None:
    try:
        pointer = runtime.ontology.current()
    except Exception:
        return None
    return pointer if isinstance(pointer, dict) else None


def _abox_graphs(runtime: Any) -> list[str]:
    try:
        status = runtime.reasoning.status()
    except Exception:
        status = {}
    graphs = (status or {}).get("aboxGraphs")
    if not graphs:
        reasoning = getattr(getattr(runtime, "config", None), "reasoning", None)
        graphs = getattr(reasoning, "abox_graphs", ()) or ()
    return [str(graph) for graph in graphs if graph]


def _values(graphs: list[str]) -> str:
    return " ".join(f"<{graph}>" for graph in graphs)


def _classes(runtime: Any, graph: str) -> dict[str, Any]:
    query = (
        "SELECT ?c ?label ?pref WHERE { "
        f"GRAPH <{graph}> {{ "
        f"{{ ?c a <{OWL}Class> }} UNION {{ ?c a <{RDFS}Class> }} "
        f"OPTIONAL {{ ?c <{RDFS_LABEL}> ?label }} "
        f"OPTIONAL {{ ?c <{SKOS_PREF}> ?pref }} "
        "} } LIMIT 5000"
    )
    result = runtime.graph.query(query)
    entries: dict[str, bool] = {}
    for row in result.get("bindings") or []:
        cls = _term(row, "c")
        if not cls:
            continue
        labeled = bool(_term(row, "pref") or _term(row, "label"))
        entries[cls] = entries.get(cls, False) or labeled
    return {
        "total": len(entries),
        "unlabeled": sum(1 for labeled in entries.values() if not labeled),
        "iris": sorted(entries),
        "source": (
            f"SPARQL GRAPH <{graph}>：owl:Class/rdfs:Class；label=skos:prefLabel|rdfs:label"
        ),
    }


def _properties(runtime: Any, graph: str) -> dict[str, Any]:
    query = (
        "SELECT DISTINCT ?p WHERE { "
        f"GRAPH <{graph}> {{ "
        f"?p a ?t . VALUES ?t {{ <{OWL}ObjectProperty> <{OWL}DatatypeProperty> "
        f"<{OWL}AnnotationProperty> }} "
        "} } LIMIT 5000"
    )
    result = runtime.graph.query(query)
    iris = sorted(
        iris
        for iris in (_term(row, "p") for row in result.get("bindings") or [])
        if iris
    )
    return {
        "total": len(iris),
        "iris": iris,
        "source": f"SPARQL GRAPH <{graph}>：owl:ObjectProperty/DatatypeProperty/AnnotationProperty",
    }


def _instance_classes(runtime: Any, graphs: list[str]) -> dict[str, int]:
    query = (
        "SELECT ?c (COUNT(DISTINCT ?s) AS ?n) WHERE { "
        f"VALUES ?g {{ {_values(graphs)} }} "
        "GRAPH ?g { ?s a ?c } "
        "} GROUP BY ?c"
    )
    result = runtime.graph.query(query)
    counts: dict[str, int] = {}
    for row in result.get("bindings") or []:
        cls = _term(row, "c")
        if cls:
            counts[cls] = _as_int(_term(row, "n"))
    return counts


def _instance_total(runtime: Any, graphs: list[str]) -> int:
    query = (
        "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { "
        f"VALUES ?g {{ {_values(graphs)} }} "
        "GRAPH ?g { ?s a ?t } "
        "}"
    )
    result = runtime.graph.query(query)
    rows = result.get("bindings") or []
    return _as_int(_term(rows[0], "n")) if rows else 0


def _used_predicates(runtime: Any, graphs: list[str]) -> set[str]:
    query = (
        "SELECT DISTINCT ?p WHERE { "
        f"VALUES ?g {{ {_values(graphs)} }} "
        "GRAPH ?g { ?s ?p ?o } "
        "} LIMIT 5000"
    )
    result = runtime.graph.query(query)
    return {
        predicate
        for predicate in (_term(row, "p") for row in result.get("bindings") or [])
        if predicate
    }


def _orphans(runtime: Any, graphs: list[str]) -> int:
    query = (
        "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { "
        f"VALUES ?g {{ {_values(graphs)} }} "
        "GRAPH ?g { ?s a ?t } "
        "FILTER NOT EXISTS { "
        "GRAPH ?g2 { ?s ?p ?o . "
        f"FILTER(?p != <{RDF_TYPE}> && ?p != <{RDFS_LABEL}>) }} "
        "FILTER NOT EXISTS { GRAPH ?g3 { ?x ?q ?s } } "
        "}"
    )
    result = runtime.graph.query(query)
    rows = result.get("bindings") or []
    return _as_int(_term(rows[0], "n")) if rows else 0


def _readyz(runtime: Any) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    try:
        runtime.metadata.health()
        checks["database"] = {"status": "ok"}
    except Exception as exc:
        checks["database"] = {"status": "fail", "detail": str(exc)}

    try:
        runtime.graph.ask("ASK {}")
        checks["graph"] = {"status": "ok"}
    except Exception as exc:
        checks["graph"] = {"status": "fail", "detail": str(exc)}

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
        checks["storage"] = {"status": "ok", "disk_free_pct": round(free_pct, 2)}
    except Exception as exc:
        checks["storage"] = {"status": "fail", "detail": str(exc)}

    healthy = all(item["status"] == "ok" for item in checks.values())
    return {
        "status": "ok" if healthy else "degraded",
        "checks": checks,
        "source": "GET /readyz 判定逻辑（database / graph / storage）",
    }


def _latest_import(runtime: Any) -> dict[str, Any]:
    rows = runtime.metadata.query(
        "SELECT import_id, version_id, conforms, violation_count, created_at "
        "FROM platform.ontology_import ORDER BY created_at DESC LIMIT 1"
    )
    if not rows:
        return {
            "count": None,
            "conforms": None,
            "sampledAt": None,
            "source": "platform.ontology_import（最新导入记录）",
            "note": "无导入记录，未以 0 代替",
        }
    row = rows[0]
    created = row.get("created_at")
    raw_count = row.get("violation_count")
    return {
        "count": None if raw_count is None else _as_int(raw_count),
        "conforms": row.get("conforms"),
        "importId": row.get("import_id"),
        "versionId": row.get("version_id"),
        "sampledAt": created.isoformat() if hasattr(created, "isoformat") else created,
        "source": "platform.ontology_import（最新导入记录，非实时重跑）",
        "note": None,
    }


def _inference_failures(runtime: Any) -> dict[str, Any]:
    rows = runtime.metadata.query(
        "SELECT COUNT(*) AS n FROM platform.reasoning_job "
        "WHERE kind='materialize' AND state='failed'"
    )
    count = _as_int(rows[0].get("n")) if rows else 0
    last_job = None
    try:
        last_job = runtime.reasoning.last_job()
    except Exception:
        last_job = None
    return {
        "count": count,
        "lastJob": last_job,
        "source": "platform.reasoning_job（kind=materialize, state=failed）+ GET /reasoning/status",
    }


def _migration(runtime: Any) -> dict[str, Any]:
    rows = runtime.metadata.query("SELECT MAX(version) AS v FROM platform.schema_version")
    raw_version = rows[0].get("v") if rows else None
    db_version = None if raw_version is None else _as_int(raw_version)
    return {
        "codeVersion": SUPPORTED_SCHEMA_VERSION,
        "dbVersion": db_version,
        "consistent": None if db_version is None else db_version == SUPPORTED_SCHEMA_VERSION,
        "source": "platform.schema_version MAX(version) vs SUPPORTED_SCHEMA_VERSION",
    }


def _version(runtime: Any, version_id: str) -> dict[str, Any]:
    try:
        row = runtime.ontology.get(version_id)
    except PortError as exc:
        raise PortError(
            code="NotFound",
            message=f"ontology version not found: {version_id}",
            provider="platform",
            provider_code="E_DIFF_VERSION_NOT_FOUND",
            details={"version": version_id, "cause": exc.provider_code},
            retryable=False,
        ) from exc
    if not isinstance(row, dict) or not row.get("graph"):
        raise PortError(
            code="NotFound",
            message=f"ontology version has no graph: {version_id}",
            provider="platform",
            provider_code="E_DIFF_VERSION_NOT_FOUND",
            details={"version": version_id},
            retryable=False,
        )
    return row


def _triple_examples(
    runtime: Any, from_graph: str | None, to_graph: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    def _rows(query: str) -> list[dict[str, Any]]:
        result = runtime.graph.query(query)
        items: list[dict[str, Any]] = []
        for row in result.get("bindings") or []:
            subject = _term_json(row, "s")
            predicate = _term_json(row, "p")
            obj = _term_json(row, "o")
            if subject and predicate and obj:
                items.append({"s": subject, "p": predicate, "o": obj})
        return items

    added_query = (
        "SELECT ?s ?p ?o WHERE { "
        f"GRAPH <{to_graph}> {{ ?s ?p ?o }} "
        + (f"MINUS {{ GRAPH <{from_graph}> {{ ?s ?p ?o }} }} " if from_graph else "")
        + f"}} LIMIT {EXAMPLE_LIMIT}"
    )
    removed_query = (
        "SELECT ?s ?p ?o WHERE { "
        + (f"GRAPH <{from_graph}> {{ ?s ?p ?o }} " if from_graph else "")
        + (f"MINUS {{ GRAPH <{to_graph}> {{ ?s ?p ?o }} }} " if from_graph else "")
        + f"}} LIMIT {EXAMPLE_LIMIT}"
    )
    added = _rows(added_query) if from_graph else _rows(
        f"SELECT ?s ?p ?o WHERE {{ GRAPH <{to_graph}> {{ ?s ?p ?o }} }} LIMIT {EXAMPLE_LIMIT}"
    )
    removed = _rows(removed_query) if from_graph else []
    return added, removed


def ontology_diff(
    runtime: Any, from_version: str | None, to_version: str | None
) -> dict[str, Any]:
    sampled_at = _now()
    pointer = _pointer(runtime)

    if not to_version:
        if not pointer or not pointer.get("versionId"):
            raise PortError(
                code="Conflict",
                message="no tbox/current pointer; pass ?to=<version>",
                provider="platform",
                provider_code="E_DIFF_NO_CURRENT",
                retryable=False,
            )
        to_version = str(pointer["versionId"])

    to_row = _version(runtime, to_version)

    if not from_version:
        versions = [
            item
            for item in runtime.ontology.list_versions()
            if item.get("status") != "deprecated"
        ]
        ids = [str(item.get("id")) for item in versions]
        if to_version not in ids:
            raise PortError(
                code="Conflict",
                message="current version is not in the version list",
                provider="platform",
                provider_code="E_DIFF_NO_PREVIOUS_BASELINE",
                details={"to": to_version},
                retryable=False,
            )
        index = ids.index(to_version)
        if index == 0:
            raise PortError(
                code="Conflict",
                message="current version has no previous baseline",
                provider="platform",
                provider_code="E_DIFF_NO_PREVIOUS_BASELINE",
                details={"to": to_version},
                retryable=False,
            )
        from_version = ids[index - 1]

    from_row = _version(runtime, from_version)

    summary = runtime.ontology.diff(from_version, to_version)
    detail = summary.get("summary") or {}

    added_classes = [str(item) for item in detail.get("addedClasses") or []]
    removed_classes = [str(item) for item in detail.get("removedClasses") or []]
    added_properties = [str(item) for item in detail.get("addedProperties") or []]
    removed_properties = [str(item) for item in detail.get("removedProperties") or []]

    from_graph = from_row.get("graph")
    to_graph = to_row.get("graph")
    added_triples, removed_triples = _triple_examples(runtime, from_graph, to_graph)

    examples = {
        "addedClasses": added_classes[:EXAMPLE_LIMIT],
        "removedClasses": removed_classes[:EXAMPLE_LIMIT],
        "addedProperties": added_properties[:EXAMPLE_LIMIT],
        "removedProperties": removed_properties[:EXAMPLE_LIMIT],
        "addedTriples": added_triples[:EXAMPLE_LIMIT],
        "removedTriples": removed_triples[:EXAMPLE_LIMIT],
    }

    return {
        "from": from_version,
        "to": to_version,
        "resolved": {
            "from": {
                "versionId": from_row.get("versionId") or from_row.get("id"),
                "semver": from_row.get("semver"),
                "graph": from_graph,
            },
            "to": {
                "versionId": to_row.get("versionId") or to_row.get("id"),
                "semver": to_row.get("semver"),
                "graph": to_graph,
            },
        },
        "counts": {
            "addedTriples": _as_int(detail.get("addedTriples")),
            "removedTriples": _as_int(detail.get("removedTriples")),
            "addedClasses": len(added_classes),
            "removedClasses": len(removed_classes),
            "addedProperties": len(added_properties),
            "removedProperties": len(removed_properties),
        },
        "addedClasses": added_classes[:500],
        "removedClasses": removed_classes[:500],
        "addedProperties": added_properties[:500],
        "removedProperties": removed_properties[:500],
        "examples": examples,
        "exampleLimit": EXAMPLE_LIMIT,
        "breaking": bool(summary.get("breaking")),
        "breakingItems": summary.get("breakingItems") or summary.get("impacts") or [],
        # O-02: the diff response carries the proposal/version flow so
        # /health/ontology-diff can answer "who moved this version, when, why".
        "lifecycle": _lifecycle_block(runtime, [from_version, to_version]),
        # O-06: changes aggregated by class/property plus an explicit
        # two-version snapshot comparison.
        "aggregations": _aggregate_block(runtime, from_graph, to_graph),
        "snapshots": _safe_snapshot_block(runtime, from_row, to_row),
        "sampledAt": sampled_at,
        "source": "GET /health/ontology-diff（runtime.ontology.diff + 图差异示例查询）",
        "readOnly": True,
    }


def _aggregate_block(runtime: Any, from_graph: str | None, to_graph: str | None) -> dict[str, Any]:
    """O-06: class/property aggregation; never fails the diff itself."""
    try:
        from .impact import _aggregate

        return _aggregate(runtime, from_graph, to_graph)
    except Exception as exc:
        return {
            "byClass": [], "byProperty": [],
            "unclassified": {"addedTriples": 0, "removedTriples": 0},
            "empty": True,
            "emptyReason": f"聚合不可算：{exc}",
            "method": "SPARQL GROUP BY ?s ?p over (to MINUS from)",
            "readOnly": True,
        }


def _safe_snapshot_block(runtime: Any, from_row: dict[str, Any],
                         to_row: dict[str, Any]) -> dict[str, Any]:
    try:
        return _snapshot_block(runtime, from_row, to_row)
    except Exception as exc:
        return {
            "from": None, "to": None, "delta": {}, "empty": True,
            "emptyReason": f"快照不可算：{exc}", "readOnly": True,
        }


def snapshot(runtime: Any, version_id: str) -> dict[str, Any]:
    """O-06: one version's class/property/instance snapshot with explicit gaps."""
    try:
        row = _version(runtime, version_id)
    except Exception as exc:
        return {
            "versionId": version_id, "empty": True,
            "emptyReason": f"版本不存在或不可读：{exc}", "readOnly": True,
        }
    graph = row.get("graph")
    if not graph:
        return {
            "versionId": version_id, "semver": row.get("semver"),
            "status": row.get("status"), "empty": True,
            "emptyReason": "版本没有关联图（graph 为空）", "readOnly": True,
        }
    classes = _classes(runtime, graph)
    properties = _properties(runtime, graph)
    graphs = _abox_graphs(runtime)
    instances = _instance_total(runtime, graphs) if graphs else None
    return {
        "versionId": row.get("versionId") or row.get("id"),
        "semver": row.get("semver"),
        "status": row.get("status"),
        "graph": graph,
        "triples": _as_int(row.get("tripleCount")),
        "triplesSource": "version.tripleCount（内容指纹三元组数）",
        "classes": classes["total"],
        "classesSource": classes["source"],
        "properties": properties["total"],
        "propertiesSource": properties["source"],
        "instances": instances,
        "instancesSource": "SPARQL COUNT(DISTINCT ?s) over A-Box graphs" if graphs
        else "A-Box 未配置",
        "instancesNote": None if graphs else "没有 A-Box 图，实例数不可算（未以 0 代替）",
        "empty": False,
        "readOnly": True,
    }


def _delta(before: Any, after: Any) -> int | None:
    if before is None or after is None:
        return None
    return int(after) - int(before)


def _snapshot_block(runtime: Any, from_row: dict[str, Any],
                    to_row: dict[str, Any]) -> dict[str, Any]:
    before = snapshot(runtime, from_row.get("versionId") or from_row.get("id"))
    after = snapshot(runtime, to_row.get("versionId") or to_row.get("id"))
    delta = {
        "triples": _delta(before.get("triples"), after.get("triples")),
        "classes": _delta(before.get("classes"), after.get("classes")),
        "properties": _delta(before.get("properties"), after.get("properties")),
        "instances": _delta(before.get("instances"), after.get("instances")),
    }
    same = before.get("versionId") == after.get("versionId")
    unchanged = same or all(value in (0, None) for value in delta.values())
    return {
        "from": before,
        "to": after,
        "delta": delta,
        "empty": unchanged,
        "emptyReason": (
            "两版本相同，无快照差异" if same
            else "快照无可比指标（实例数不可算或数据缺失）" if all(
                value is None for value in delta.values())
            else None
        ),
        "source": "各版本类/属性/实例计数 + 内容指纹三元组数",
        "readOnly": True,
    }


def snapshot_compare(runtime: Any, from_version: str | None = None,
                     to_version: str | None = None) -> dict[str, Any]:
    """O-06 endpoint payload: two explicit versions, or current vs previous."""
    pointer = _pointer(runtime)
    if not to_version:
        to_version = (pointer or {}).get("versionId")
    if not to_version:
        return {
            "from": None, "to": None, "delta": {},
            "empty": True,
            "emptyReason": "tbox/current 指针不存在，且未指定 to 版本",
            "source": "各版本类/属性/实例计数 + 内容指纹三元组数",
            "readOnly": True,
        }
    if not from_version:
        versions = [item for item in runtime.ontology.list_versions()
                    if item.get("status") != "deprecated"]
        ids = [str(item.get("id")) for item in versions]
        if to_version in ids:
            index = ids.index(to_version)
            if index == 0:
                return {
                    "from": None, "to": snapshot(runtime, to_version), "delta": {},
                    "empty": True,
                    "emptyReason": "当前版本没有基线版本，无法做快照对比",
                    "source": "各版本类/属性/实例计数 + 内容指纹三元组数",
                    "readOnly": True,
                }
            from_version = ids[index - 1]
        else:
            return {
                "from": None, "to": snapshot(runtime, to_version), "delta": {},
                "empty": True,
                "emptyReason": "当前版本不在版本列表中，无法确定基线",
                "readOnly": True,
            }
    before = snapshot(runtime, from_version)
    after = snapshot(runtime, to_version)
    block = {
        "from": before, "to": after,
        "delta": {
            "triples": _delta(before.get("triples"), after.get("triples")),
            "classes": _delta(before.get("classes"), after.get("classes")),
            "properties": _delta(before.get("properties"), after.get("properties")),
            "instances": _delta(before.get("instances"), after.get("instances")),
        },
    }
    if before.get("versionId") == after.get("versionId"):
        block.update({"empty": True, "emptyReason": "两版本相同，无快照差异"})
    elif all(value is None for value in block["delta"].values()):
        block.update({"empty": True,
                      "emptyReason": "快照无可比指标（实例数不可算或数据缺失）"})
    else:
        block.update({"empty": False, "emptyReason": None})
    block["source"] = "各版本类/属性/实例计数 + 内容指纹三元组数"
    block["readOnly"] = True
    return block


def _lifecycle_block(runtime: Any, version_ids: list[str]) -> dict[str, Any]:
    """Lifecycle block for /health/ontology-diff; never fails the diff itself."""
    try:
        return _lifecycle_summary(runtime.metadata, version_ids)
    except Exception as exc:  # pre-V32 database or fake metadata in tests
        return {
            "versions": {},
            "items": [],
            "empty": True,
            "emptyReason": f"流转表不可读：{exc}",
            "source": "platform.ontology_lifecycle_transition",
            "readOnly": True,
        }


def dashboard(runtime: Any) -> dict[str, Any]:
    sampled_at = _now()
    graphs = _abox_graphs(runtime)
    pointer = _pointer(runtime)
    tbox_graph = (pointer or {}).get("graph")

    coverage: dict[str, Any] = {
        "classes": {
            "total": None,
            "withInstances": None,
            "ratio": None,
            "error": None,
        },
        "properties": {
            "total": None,
            "withValues": None,
            "ratio": None,
            "error": None,
        },
        "instances": {"total": None, "error": None},
        "source": "T-Box 类/属性 + A-Box 实例（SPARQL 聚合）",
    }

    if not tbox_graph:
        coverage["classes"]["error"] = "tbox/current 指针不存在"
        coverage["properties"]["error"] = "tbox/current 指针不存在"
    else:
        try:
            classes = _classes(runtime, tbox_graph)
            instance_counts = _instance_classes(runtime, graphs) if graphs else {}
            declared = classes["iris"]
            with_instances = sum(
                1 for cls in declared if instance_counts.get(cls, 0) > 0
            )
            coverage["classes"] = {
                "total": classes["total"],
                "withInstances": with_instances,
                "ratio": round(with_instances / classes["total"], 4)
                if classes["total"]
                else None,
                "unlabeled": classes["unlabeled"],
                "error": None,
                "source": classes["source"],
            }
        except Exception as exc:
            coverage["classes"]["error"] = str(exc)

        try:
            properties = _properties(runtime, tbox_graph)
            used = _used_predicates(runtime, graphs) if graphs else set()
            declared = properties["iris"]
            with_values = sum(1 for prop in declared if prop in used)
            coverage["properties"] = {
                "total": properties["total"],
                "withValues": with_values,
                "ratio": round(with_values / properties["total"], 4)
                if properties["total"]
                else None,
                "error": None,
                "source": properties["source"],
            }
        except Exception as exc:
            coverage["properties"]["error"] = str(exc)

    try:
        coverage["instances"] = {
            "total": _instance_total(runtime, graphs) if graphs else 0,
            "graphs": graphs,
            "error": None,
            "source": "A-Box 命名图：COUNT(DISTINCT 有 rdf:type 的主体)",
        }
    except Exception as exc:
        coverage["instances"]["error"] = str(exc)

    try:
        orphan_count: int | None = _orphans(runtime, graphs) if graphs else 0
        orphan_error = None
    except Exception as exc:
        orphan_count = None
        orphan_error = str(exc)

    try:
        shacl = _latest_import(runtime)
    except Exception as exc:
        shacl = {
            "count": None,
            "conforms": None,
            "source": "platform.ontology_import（最新导入记录）",
            "error": str(exc),
        }

    try:
        inference = _inference_failures(runtime)
    except Exception as exc:
        inference = {
            "count": None,
            "lastJob": None,
            "source": "platform.reasoning_job",
            "error": str(exc),
        }

    try:
        migration = _migration(runtime)
    except Exception as exc:
        migration = {
            "codeVersion": SUPPORTED_SCHEMA_VERSION,
            "dbVersion": None,
            "consistent": None,
            "source": "platform.schema_version",
            "error": str(exc),
        }

    readiness = _readyz(runtime)

    return {
        "sampledAt": sampled_at,
        "coverage": coverage,
        "orphanInstances": {
            "count": orphan_count,
            "error": orphan_error,
            "source": "A-Box：无出边（除 rdf:type/rdfs:label）且无入边的实例",
        },
        "shaclViolations": shacl,
        "inferenceFailures": inference,
        "migration": migration,
        "readyz": readiness,
        "tbox": {
            "pointer": pointer,
            "versionId": (pointer or {}).get("versionId"),
            "semver": (pointer or {}).get("semver"),
            "graph": tbox_graph,
            "source": "GET /ontology/versions（tbox/current 指针）",
        },
        "ontologyDiff": "GET /health/ontology-diff",
        "dataSource": {
            "endpoints": [
                "GET /health/dashboard",
                "GET /browse/ontology/tree",
                "GET /browse/ontology/instances",
                "GET /reasoning/status",
                "GET /readyz",
                "GET /ontology/versions",
            ],
            "sampledAt": sampled_at,
            "note": "全部为只读聚合；每个区块的 source 字段标注具体出处，查询失败返回 null 与 error，不给猜测值",
        },
        "readOnly": True,
    }
