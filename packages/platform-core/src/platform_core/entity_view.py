"""B-03 read-only entity view: classes, required properties, neighbours, metrics, badge.

Everything here is a read: the only ports touched are ``ontology.current``,
``graph.query``, ``reasoning.status`` and ``metadata.query``. The evidence badge
is decided in the backend so the UI never guesses.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from . import source_ref
from .datagen_abox import SYNTHETIC_GRAPH
from .errors import PortError

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
PROV = "http://www.w3.org/ns/prov#"
PROV_GRAPH = "urn:platform:prov"

RDF_TYPE = RDF + "type"
RDFS_LABEL = RDFS + "label"
RDFS_SUBCLASS = RDFS + "subClassOf"
RDFS_SEE_ALSO = RDFS + "seeAlso"
SKOS_PREF = SKOS + "prefLabel"
OWL_CLASS = OWL + "Class"
OWL_RESTRICTION = OWL + "Restriction"
OWL_ON_PROPERTY = OWL + "onProperty"
OWL_MIN_CARD = OWL + "minCardinality"
OWL_MIN_Q_CARD = OWL + "minQualifiedCardinality"
PROV_USED = PROV + "used"
PROV_VALUE = PROV + "value"

SAFE_IRI = re.compile(r"^[^<>\"{}|^`\\\s]{1,2048}$")
MAX_EDGES = 200
EXAMPLE_LIMIT = 5

EVIDENCED = "evidenced"
INFERRED = "inferred"
NO_SOURCE = "no-source"

BADGE_LABELS = {
    EVIDENCED: "有原文/事实",
    INFERRED: "推测",
    NO_SOURCE: "无依据",
}

# Weak, documented class -> metric grain/entity_column aliases. Matching is by
# substring of the normalized class local name, and every hit is reported with
# its match basis. Unmatched classes return "unbound" instead of a guess.
CLASS_ALIASES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("account", ("account_id", "account_no", "account_number"), ("account",)),
    ("creditagreement", ("agreement_id", "loan_no"), ("agreement",)),
    ("loanagreement", ("agreement_id", "loan_no"), ("agreement",)),
    ("agreement", ("agreement_id",), ("agreement",)),
    ("policy", ("policy_no",), ("agreement",)),
    ("individual", ("customer_no",), ("customer",)),
    ("organization", ("customer_no",), ("customer",)),
    ("party", ("customer_no",), ("customer",)),
    ("customer", ("customer_no",), ("customer",)),
    ("product", ("product", "product_type"), ("product",)),
    ("institution", ("institution",), ("institution",)),
    ("asset", ("asset_id",), ("asset",)),
    ("event", ("event_id",), ("event",)),
)


def _err(code: str, message: str, **details: Any) -> PortError:
    return PortError(
        code="InvalidArgument",
        message=message,
        provider="platform",
        provider_code=code,
        details=details or None,
    )


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
    kind = term.get("kind")
    if kind == "iri":
        return {"kind": "iri", "value": term.get("iri")}
    if kind == "bnode":
        return {"kind": "bnode", "value": term.get("label")}
    payload: dict[str, Any] = {"kind": "literal", "value": term.get("value")}
    if term.get("datatype"):
        payload["datatype"] = term.get("datatype")
    return payload


def _local_name(iri: str | None) -> str:
    if not iri:
        return "—"
    for sep in ("#", "/", ":"):
        if sep in iri:
            return iri.rsplit(sep, 1)[-1]
    return iri


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _graphs(runtime: Any) -> list[str]:
    graphs: list[str] = []
    pointer = _safe_current(runtime)
    if pointer and pointer.get("graph"):
        graphs.append(str(pointer["graph"]))
    status = _reasoning_status(runtime)
    abox = status.get("aboxGraphs")
    if not abox:
        config = getattr(runtime, "config", None)
        reasoning_cfg = getattr(config, "reasoning", None)
        abox = getattr(reasoning_cfg, "abox_graphs", ()) or ()
    for graph in abox:
        if graph and graph not in graphs:
            graphs.append(str(graph))
    # The datagen A-Box is a real named instance graph; expose it read-only so
    # the entity page can resolve those IRIs even though reasoning.abox_graphs
    # (which also feeds materialization) deliberately stays on the fact graph.
    if SYNTHETIC_GRAPH not in graphs and _graph_exists(runtime, SYNTHETIC_GRAPH):
        graphs.append(SYNTHETIC_GRAPH)
    return graphs


def _graph_exists(runtime: Any, graph: str) -> bool:
    try:
        return bool(runtime.graph.ask(f"ASK {{ GRAPH <{graph}> {{ ?s ?p ?o }} }}"))
    except Exception:
        return False


def _safe_current(runtime: Any) -> dict[str, Any] | None:
    try:
        pointer = runtime.ontology.current()
    except Exception:
        return None
    return pointer if isinstance(pointer, dict) else None


def _reasoning_status(runtime: Any) -> dict[str, Any]:
    fn = getattr(runtime, "reasoning", None)
    if fn is None:
        return {}
    try:
        status = fn.status()
    except Exception:
        return {}
    return status if isinstance(status, dict) else {}


def _inferred_graph(runtime: Any) -> str | None:
    status = _reasoning_status(runtime)
    pointer = status.get("pointer") or {}
    if not isinstance(pointer, dict):
        return None
    graph = pointer.get("targetGraph") or pointer.get("graph")
    return str(graph) if graph else None


def _ignored_types(runtime: Any) -> set[str]:
    """Meta-level types hidden by the entity view (config entity_view.ignore_types)."""
    config = getattr(runtime, "config", None)
    view = getattr(config, "entity_view", None)
    values = getattr(view, "ignore_types", None) or ()
    return {str(value) for value in values}


def _outgoing_triples_query(graphs: list[str], iri: str) -> str:
    values = " ".join(f"<{g}>" for g in graphs)
    return (
        "SELECT ?g ?s ?p ?o WHERE { "
        f"VALUES ?g {{ {values} }} "
        f"GRAPH ?g {{ BIND(<{iri}> AS ?s) ?s ?p ?o }} "
        f"}} LIMIT {MAX_EDGES}"
    )


def _incoming_triples_query(graphs: list[str], iri: str) -> str:
    values = " ".join(f"<{g}>" for g in graphs)
    return (
        "SELECT ?g ?s ?p ?o WHERE { "
        f"VALUES ?g {{ {values} }} "
        f"GRAPH ?g {{ BIND(<{iri}> AS ?o) ?s ?p ?o }} "
        f"}} LIMIT {MAX_EDGES}"
    )


def _edges(result: dict[str, Any]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for row in result.get("bindings") or []:
        subject = _term(row, "s")
        predicate = _term(row, "p")
        obj = _term_json(row, "o")
        if not subject or not predicate or not obj or not obj.get("value"):
            continue
        edges.append(
            {
                "graph": _term(row, "g"),
                "s": subject,
                "p": predicate,
                "o": obj,
            }
        )
    return edges


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Outgoing/incoming lookups are disjoint except self-loops; keep one row."""
    seen: set[tuple[Any, ...]] = set()
    unique: list[dict[str, Any]] = []
    for edge in edges:
        key = (edge["graph"], edge["s"], edge["p"], edge["o"].get("value"))
        if key not in seen:
            seen.add(key)
            unique.append(edge)
    return unique


def _class_map(runtime: Any, graph: str) -> dict[str, dict[str, Any]]:
    query = (
        "SELECT ?c ?label ?pref ?parent WHERE { "
        f"GRAPH <{graph}> {{ "
        f"{{ ?c a <{OWL_CLASS}> }} UNION {{ ?c a <{RDFS}Class> }} "
        f"OPTIONAL {{ ?c <{RDFS_LABEL}> ?label }} "
        f"OPTIONAL {{ ?c <{SKOS_PREF}> ?pref }} "
        f"OPTIONAL {{ ?c <{RDFS_SUBCLASS}> ?parent }} "
        "} } LIMIT 5000"
    )
    try:
        result = runtime.graph.query(query)
    except Exception:
        return {}
    classes: dict[str, dict[str, Any]] = {}
    for row in result.get("bindings") or []:
        iri = _term(row, "c")
        if not iri:
            continue
        entry = classes.setdefault(
            iri,
            {
                "iri": iri,
                "label": None,
                "labeled": False,
                "parents": [],
            },
        )
        label = _term(row, "pref") or _term(row, "label")
        if label:
            entry["label"] = label
            entry["labeled"] = True
        parent = _term(row, "parent")
        if parent and parent not in entry["parents"]:
            entry["parents"].append(parent)
    return classes


def _restrictions(runtime: Any, graph: str) -> dict[str, list[dict[str, Any]]]:
    query = (
        "SELECT ?c ?p ?n WHERE { "
        f"GRAPH <{graph}> {{ "
        f"?c <{RDFS_SUBCLASS}> ?r . "
        f"?r a <{OWL_RESTRICTION}> ; <{OWL_ON_PROPERTY}> ?p . "
        f"{{ ?r <{OWL_MIN_CARD}> ?n }} UNION {{ ?r <{OWL_MIN_Q_CARD}> ?n }} "
        "} } LIMIT 5000"
    )
    try:
        result = runtime.graph.query(query)
    except Exception:
        return {}
    restrictions: dict[str, list[dict[str, Any]]] = {}
    for row in result.get("bindings") or []:
        cls = _term(row, "c")
        prop = _term(row, "p")
        count = _as_int(_term(row, "n"))
        if not cls or not prop:
            continue
        restrictions.setdefault(cls, []).append({"property": prop, "minCount": count})
    return restrictions


def _property_labels(runtime: Any, graph: str) -> dict[str, str]:
    query = (
        "SELECT ?p ?label WHERE { "
        f"GRAPH <{graph}> {{ ?p <{RDFS_LABEL}> ?label }} "
        "} LIMIT 5000"
    )
    try:
        result = runtime.graph.query(query)
    except Exception:
        return {}
    labels: dict[str, str] = {}
    for row in result.get("bindings") or []:
        prop = _term(row, "p")
        label = _term(row, "label")
        if prop and label:
            labels[prop] = label
    return labels


def _instance_counts(runtime: Any, graphs: list[str], classes: list[str]) -> dict[str, int]:
    if not graphs or not classes:
        return {}
    values = " ".join(f"<{g}>" for g in graphs)
    class_values = " ".join(f"<{c}>" for c in classes)
    query = (
        "SELECT ?c (COUNT(DISTINCT ?s) AS ?n) WHERE { "
        f"VALUES ?g {{ {values} }} "
        f"GRAPH ?g {{ ?s a ?c }} "
        f"VALUES ?c {{ {class_values} }} "
        "} GROUP BY ?c"
    )
    try:
        result = runtime.graph.query(query)
    except Exception:
        return {}
    counts: dict[str, int] = {}
    for row in result.get("bindings") or []:
        cls = _term(row, "c")
        if cls:
            counts[cls] = _as_int(_term(row, "n"))
    return counts


def _ancestors(cls: str, classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    current: str | None = cls
    while current and current not in seen:
        seen.add(current)
        entry = classes.get(current)
        chain.append(
            {
                "iri": current,
                "label": (entry or {}).get("label") or _local_name(current),
            }
        )
        parents = (entry or {}).get("parents") or []
        known = [parent for parent in parents if parent in classes]
        current = known[0] if known else None
    return chain


def _class_aliases(classes: list[dict[str, Any]]) -> tuple[set[str], set[str], list[str]]:
    columns: set[str] = set()
    grains: set[str] = set()
    basis: list[str] = []
    for cls in classes:
        key = re.sub(r"[^a-z0-9]", "", (_local_name(cls["iri"]) or "").lower())
        if not key:
            continue
        for alias, alias_columns, alias_grains in CLASS_ALIASES:
            if alias in key:
                columns.update(alias_columns)
                grains.update(alias_grains)
                basis.append(
                    f"{_local_name(cls['iri'])} ≈ entity_column[{','.join(alias_columns)}] / grain[{','.join(alias_grains)}]"
                )
                break
    return columns, grains, basis


def _related_metrics(runtime: Any, classes: list[dict[str, Any]]) -> dict[str, Any]:
    columns, grains, basis = _class_aliases(classes)
    if not columns and not grains:
        return {
            "status": "unbound",
            "reason": "类名未命中 metric_field_binding 的 entity_column/grain 弱映射",
            "items": [],
            "matchBasis": [],
        }
    sql = (
        "SELECT DISTINCT b.metric_id, b.role, b.fact_table, b.entity_column, "
        "d.name_zh, d.domain, d.grain, d.publishable "
        "FROM platform.metric_field_binding b "
        "LEFT JOIN platform.metric_definition d ON d.metric_id = b.metric_id "
        "WHERE b.entity_column = ANY(%s) OR d.grain = ANY(%s) "
        "ORDER BY b.metric_id, b.role"
    )
    rows = runtime.metadata.query(sql, [sorted(columns), sorted(grains)])
    items: dict[str, dict[str, Any]] = {}
    for row in rows:
        metric_id = row.get("metric_id")
        if not metric_id:
            continue
        item = items.setdefault(
            metric_id,
            {
                "metricId": metric_id,
                "nameZh": row.get("name_zh"),
                "domain": row.get("domain"),
                "grain": row.get("grain"),
                "publishable": row.get("publishable"),
                "bindings": [],
                "matchBasis": [],
            },
        )
        if row.get("entity_column") in columns:
            item["matchBasis"].append(f"entity_column={row.get('entity_column')}")
        elif row.get("grain") in grains:
            item["matchBasis"].append(f"grain={row.get('grain')}")
        item["bindings"].append(
            {
                "role": row.get("role"),
                "factTable": row.get("fact_table"),
                "entityColumn": row.get("entity_column"),
            }
        )
    for item in items.values():
        item["matchBasis"] = sorted(set(item["matchBasis"]))
    return {
        "status": "bound" if items else "unbound",
        "reason": None if items else "metric_field_binding 无匹配行",
        "items": list(items.values()),
        "matchBasis": sorted(set(basis)),
    }


def _source_descriptor(ref: str, text: str | None) -> dict[str, Any]:
    try:
        parsed = source_ref.parse_ref(ref)
    except PortError:
        return {
            "kind": "unparsed",
            "ref": ref,
            "text": text,
            "resolveUrl": "/source/resolve?ref=" + quote(ref, safe=""),
            "href": "/source/resolve?ref=" + quote(ref, safe=""),
        }
    resolve_url = "/source/resolve?ref=" + quote(ref, safe="")
    href = resolve_url
    if parsed.get("kind") == "fact":
        table = parsed.get("table") or ""
        href = f"/browse/facts?table={quote(str(table), safe='')}&limit=5"
    return {
        "kind": parsed.get("kind"),
        "ref": ref,
        "text": text,
        "resolveUrl": resolve_url,
        "href": href,
    }


def _sources(
    runtime: Any, iri: str, asserted_edges: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    refs: list[tuple[str, str | None]] = []
    for edge in asserted_edges:
        predicate = edge["p"]
        obj = edge["o"]
        if predicate == RDFS_SEE_ALSO and obj.get("kind") == "literal":
            refs.append((str(obj["value"]), None))
        elif predicate in (PROV + "wasDerivedFrom", PROV + "wasGeneratedBy") and obj.get(
            "kind"
        ) == "literal":
            refs.append((str(obj["value"]), None))
    try:
        result = runtime.graph.query(
            "SELECT ?ref ?text WHERE { "
            f"GRAPH <{PROV_GRAPH}> {{ "
            f"?activity <{PROV_USED}> <{iri}> . "
            f"?activity <{PROV_USED}> ?evidence . "
            f"?evidence <{RDFS_SEE_ALSO}> ?ref . "
            f"OPTIONAL {{ ?evidence <{PROV_VALUE}> ?text }} "
            "} } LIMIT 50"
        )
        for row in result.get("bindings") or []:
            ref = _term(row, "ref")
            text = _term(row, "text")
            if ref:
                refs.append((ref, text))
    except Exception:
        pass
    seen: set[str] = set()
    sources: list[dict[str, Any]] = []
    for ref, text in refs:
        if ref in seen:
            continue
        seen.add(ref)
        sources.append(_source_descriptor(ref, text))
    return sources


def _badge(
    runtime: Any,
    sources: list[dict[str, Any]],
    asserted_edges: list[dict[str, Any]],
    inferred_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    if sources:
        return {
            "state": EVIDENCED,
            "label": BADGE_LABELS[EVIDENCED],
            "basis": f"{len(sources)} 条可解析 sourceRef / PROV 溯源链接",
            "judge": None,
        }
    if inferred_edges and not asserted_edges:
        status = _reasoning_status(runtime)
        pointer = status.get("pointer") or {}
        pointer = pointer if isinstance(pointer, dict) else {}
        profile = pointer.get("profile") or status.get("profile") or "unknown"
        job_id = pointer.get("jobId") or "—"
        return {
            "state": INFERRED,
            "label": BADGE_LABELS[INFERRED],
            "basis": (
                f"仅在推理图 <{_inferred_graph(runtime) or '—'}> 出现；"
                f"profile={profile}，推理作业 {job_id}"
            ),
            "judge": f"system:reasoning/{profile}",
        }
    return {
        "state": NO_SOURCE,
        "label": BADGE_LABELS[NO_SOURCE],
        "basis": (
            "存在断言三元组，但未找到 sourceRef / PROV 溯源链接"
            if asserted_edges
            else "该 IRI 在当前图与推理图中均无三元组"
        ),
        "judge": None,
    }


def entity_detail(runtime: Any, iri: str, limit: int = 50) -> dict[str, Any]:
    if not SAFE_IRI.match(iri or ""):
        raise _err("E_ENTITY_BAD_IRI", "iri is not a safe absolute IRI", iri=iri)

    graphs = _graphs(runtime)
    asserted: list[dict[str, Any]] = []
    if graphs:
        try:
            # Two plain one-hop lookups instead of `GRAPH ?g { ... UNION ... }`:
            # Oxigraph hangs on union-under-variable-graph (measured >25s), while
            # the split queries answer in milliseconds on the same graphs.
            asserted = _edges(runtime.graph.query(_outgoing_triples_query(graphs, iri)))
            asserted += _edges(runtime.graph.query(_incoming_triples_query(graphs, iri)))
        except Exception as exc:
            raise PortError(
                code="Unavailable",
                message=f"graph query failed: {exc}",
                provider="platform",
                provider_code="E_ENTITY_GRAPH_UNAVAILABLE",
                retryable=True,
            ) from exc

    inferred_graph = _inferred_graph(runtime)
    inferred: list[dict[str, Any]] = []
    if inferred_graph:
        try:
            inferred = _edges(
                runtime.graph.query(_outgoing_triples_query([inferred_graph], iri))
            )
            inferred += _edges(
                runtime.graph.query(_incoming_triples_query([inferred_graph], iri))
            )
        except Exception:
            inferred = []

    # An inferred graph may also be listed in abox_graphs; keep the two views disjoint.
    inferred = _dedupe_edges(inferred)
    asserted = _dedupe_edges(asserted)
    inferred_edges = [edge for edge in inferred if edge["graph"] == inferred_graph]
    asserted_edges = [edge for edge in asserted if edge["graph"] != inferred_graph]

    if not asserted_edges and not inferred_edges:
        raise PortError(
            code="NotFound",
            message="entity not found in any configured graph",
            provider="platform",
            provider_code="E_ENTITY_NOT_FOUND",
            details={"iri": iri, "graphs": graphs},
        )

    all_edges = asserted_edges + inferred_edges
    # Presentation filter: meta-level type edges (owl:Thing / owl:NamedIndividual
    # by default) carry no business meaning. This only trims the read-only
    # payload; the graphs, the inferred graph and /browse/sparql keep every triple.
    ignored_types = _ignored_types(runtime)
    display_edges = [
        edge
        for edge in all_edges
        if not (edge["p"] == RDF_TYPE and edge["o"].get("value") in ignored_types)
    ]
    type_edges = [edge for edge in display_edges if edge["p"] == RDF_TYPE and edge["s"] == iri]
    class_iris: list[str] = []
    for edge in type_edges:
        obj = edge["o"]
        if obj.get("kind") == "iri" and obj["value"] not in class_iris:
            class_iris.append(obj["value"])

    current = _safe_current(runtime)
    tbox = current.get("graph") if current else None
    classes_map = _class_map(runtime, tbox) if tbox else {}
    restrictions = _restrictions(runtime, tbox) if tbox else {}
    property_labels = _property_labels(runtime, tbox) if tbox else {}

    counts = _instance_counts(runtime, graphs, class_iris) if class_iris else {}

    classes_payload: list[dict[str, Any]] = []
    for cls in class_iris:
        entry = classes_map.get(cls) or {}
        inferred_only = not any(
            edge["p"] == RDF_TYPE and edge["s"] == iri and edge["o"].get("value") == cls
            for edge in asserted_edges
        )
        classes_payload.append(
            {
                "iri": cls,
                "label": entry.get("label") or _local_name(cls),
                "labeled": bool(entry.get("labeled")),
                "chain": _ancestors(cls, classes_map),
                "instanceCount": counts.get(cls, 0),
                "inferredOnly": inferred_only,
            }
        )

    # Required properties from owl:Restriction min cardinality, including ancestors.
    seen_props: dict[str, dict[str, Any]] = {}
    for cls in class_iris:
        for item in _ancestors(cls, classes_map):
            for restriction in restrictions.get(item["iri"], []):
                prop = restriction["property"]
                record = seen_props.setdefault(
                    prop,
                    {
                        "property": prop,
                        "label": property_labels.get(prop) or _local_name(prop),
                        "minCount": 0,
                        "declaredOn": [],
                    },
                )
                record["minCount"] = max(record["minCount"], restriction["minCount"])
                if item["iri"] not in record["declaredOn"]:
                    record["declaredOn"].append(item["iri"])

    values_by_prop: dict[str, list[dict[str, Any]]] = {}
    for edge in display_edges:
        if edge["s"] != iri:
            continue
        values_by_prop.setdefault(edge["p"], []).append(edge["o"])

    required: list[dict[str, Any]] = []
    for prop, record in sorted(seen_props.items(), key=lambda item: item[0]):
        values = values_by_prop.get(prop, [])
        required.append(
            {
                **record,
                "values": values,
                "valueCount": len(values),
                "satisfied": len(values) >= max(record["minCount"], 1),
            }
        )
    required.sort(key=lambda item: (item["satisfied"], item["property"]))
    required_status = "no-restrictions" if not required else "ok"

    properties_payload: list[dict[str, Any]] = []
    for prop, values in sorted(values_by_prop.items(), key=lambda item: item[0]):
        if prop == RDF_TYPE:
            continue
        properties_payload.append(
            {
                "property": prop,
                "label": property_labels.get(prop) or _local_name(prop),
                "values": values,
            }
        )

    label = None
    for edge in asserted_edges:
        if edge["s"] == iri and edge["p"] == RDFS_LABEL and edge["o"].get("kind") == "literal":
            label = str(edge["o"]["value"])
            break
    if label is None:
        for edge in inferred_edges:
            if edge["s"] == iri and edge["p"] == RDFS_LABEL and edge["o"].get("kind") == "literal":
                label = str(edge["o"]["value"])
                break
    if label is None:
        label = _local_name(iri)

    nodes: dict[str, dict[str, Any]] = {
        iri: {
            "iri": iri,
            "label": label,
            "inferred": not asserted_edges and bool(inferred_edges),
        }
    }
    edge_rows: list[dict[str, Any]] = []
    for edge in display_edges[:limit]:
        for term in (edge["s"], edge["o"].get("value")):
            if term and term.startswith(("http://", "https://", "urn:")):
                nodes.setdefault(
                    term,
                    {
                        "iri": term,
                        "label": _local_name(term),
                        "inferred": edge["graph"] == inferred_graph,
                    },
                )
        edge_rows.append(
            {
                "s": edge["s"],
                "p": edge["p"],
                "o": edge["o"]["value"],
                "graph": edge["graph"],
                "inferred": edge["graph"] == inferred_graph,
            }
        )
    for edge in display_edges:
        if edge["p"] == RDFS_LABEL and edge["s"] in nodes and edge["o"].get("kind") == "literal":
            nodes[edge["s"]]["label"] = str(edge["o"]["value"])

    asserted_own = [edge for edge in asserted_edges if edge["s"] == iri]
    inferred_own = [edge for edge in inferred_edges if edge["s"] == iri]
    sources = _sources(runtime, iri, asserted_own)
    badge = _badge(runtime, sources, asserted_own, inferred_own)

    return {
        "iri": iri,
        "label": label,
        "classes": classes_payload,
        "requiredProperties": required,
        "requiredStatus": required_status,
        "properties": properties_payload,
        "neighbors": {
            "nodes": list(nodes.values()),
            "edges": edge_rows,
            "truncated": len(display_edges) > len(edge_rows),
        },
        "instanceCount": classes_payload[0]["instanceCount"] if classes_payload else 0,
        "relatedMetrics": _related_metrics(runtime, classes_payload),
        "sources": sources,
        "evidenceBadge": badge,
        "tbox": {
            "versionId": (current or {}).get("versionId"),
            "semver": (current or {}).get("semver"),
            "graph": tbox,
        },
        "sampledAt": datetime.now(timezone.utc).isoformat(),
        "source": "GET /ui/api/entity",
        "readOnly": True,
    }
