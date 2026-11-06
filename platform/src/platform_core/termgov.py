"""O-05: term-layer governance (SKOS coverage, conflicts, import diff).

Two responsibilities, both read-only with respect to the published graph:

1. ``coverage``: how much of the documented term baseline is actually present
   (85 metric concepts, 18 class aliases from design docs 50/52), with field
   coverage, duplicate surfaces and pref/alt conflicts.
2. ``diff``: before a new SKOS file is imported, show added / removed /
   redefined (改义) concepts and aliases plus every conflict, and record the
   check in ``platform.term_check``. The check result is required before a term
   batch can be registered through ``/ontology/terms/import``; the existing
   T-Box ``/ontology/import`` path (SHA-256 + guard compilation) is untouched.

Nothing here invents numbers: when the baseline cannot be read, counts are
``None`` with an explicit reason instead of 0.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import rdflib
from rdflib import Literal, URIRef

from .errors import PortError
from .termlex import SKOS, TERM, TERM_ENTRY, compile_guard

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
OWL_CLASS = "http://www.w3.org/2002/07/owl#Class"
METRIC_SCHEME = f"{TERM}MetricScheme"

# Documented baselines: 85 metric concepts (design 50) and 18 class aliases
# (roadmap G-08 / design 52). Callers may override for other vocabularies.
EXPECTED_CONCEPTS = 85
EXPECTED_ALIASES = 18
BASELINE_SOURCE = "doc/_design/50-指标 SKOS 词表-v1.md（85 概念）+ doc/_design/52-后续路线图-v1.md（18 别名）"

E_TERM_CHECK_FAILED = "E_TERM_CHECK_FAILED"
E_TERM_CHECK_MISSING = "E_TERM_CHECK_MISSING"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _iri(value: Any) -> str:
    if isinstance(value, URIRef):
        return str(value)
    return str(value or "")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lang(value: Any) -> str:
    lang = getattr(value, "language", "") if isinstance(value, Literal) else ""
    return str(lang or "")


def _empty_snapshot() -> dict[str, Any]:
    return {"concepts": {}, "aliases": {}, "classes": {}}


# ---------------------------------------------------------------------------
# parsing / snapshot
# ---------------------------------------------------------------------------

def parse_skos(content: str, fmt: str = "turtle") -> dict[str, Any]:
    """Parse an uploaded SKOS/T-Box file into the governance snapshot shape."""
    fmt = (fmt or "turtle").lower()
    if fmt in ("ttl", "turtle"):
        fmt = "turtle"
    graph = rdflib.Graph()
    try:
        graph.parse(data=content, format=fmt)
    except Exception as exc:
        raise PortError(
            code="InvalidArgument", message=f"cannot parse SKOS content as {fmt}: {exc}",
            provider="platform", provider_code="E_TERM_PARSE_FAILED",
            details={"format": fmt},
        ) from exc
    return snapshot_from_rdflib(graph)


def snapshot_from_rdflib(graph: rdflib.Graph) -> dict[str, Any]:
    snapshot = _empty_snapshot()
    for subject in set(graph.subjects(rdflib.RDF.type, URIRef(f"{SKOS}Concept"))):
        iri = _iri(subject)
        node = snapshot["concepts"].setdefault(
            iri, {"pref": {}, "alt": [], "definition": None, "notation": None,
                  "broader": [], "inScheme": None}
        )
        for obj in graph.objects(subject, URIRef(f"{SKOS}prefLabel")):
            node["pref"][_lang(obj)] = _text(obj)
        for obj in graph.objects(subject, URIRef(f"{SKOS}altLabel")):
            node["alt"].append({"text": _text(obj), "lang": _lang(obj)})
        definition = next(iter(graph.objects(subject, URIRef(f"{SKOS}definition"))), None)
        if definition is not None:
            node["definition"] = _text(definition)
        notation = next(iter(graph.objects(subject, URIRef(f"{SKOS}notation"))), None)
        if notation is not None:
            node["notation"] = _text(notation)
        node["broader"] = sorted(_iri(item) for item in graph.objects(subject, URIRef(f"{SKOS}broader")))
        scheme = next(iter(graph.objects(subject, URIRef(f"{SKOS}inScheme"))), None)
        node["inScheme"] = _iri(scheme) if scheme is not None else None
    for subject in set(graph.subjects(rdflib.RDF.type, URIRef(TERM_ENTRY))):
        iri = _iri(subject)
        entry = snapshot["aliases"].setdefault(iri, {})
        for predicate, key in ((f"{TERM}forClass", "forClass"), (f"{TERM}label", "label"),
                               (f"{TERM}guardRegex", "guard"), (f"{TERM}status", "status"),
                               (f"{TERM}confidence", "confidence")):
            value = next(iter(graph.objects(subject, URIRef(predicate))), None)
            if value is not None:
                entry[key] = _text(value)
    for subject in set(graph.subjects(rdflib.RDF.type, URIRef(OWL_CLASS))):
        iri = _iri(subject)
        pref = {_lang(obj): _text(obj) for obj in graph.objects(subject, URIRef(f"{SKOS}prefLabel"))}
        alt = [{"text": _text(obj), "lang": _lang(obj)}
               for obj in graph.objects(subject, URIRef(f"{SKOS}altLabel"))]
        suppressed = [_text(obj) for obj in graph.objects(subject, URIRef(f"{TERM}suppressedSurface"))]
        label = {_lang(obj): _text(obj) for obj in graph.objects(subject, URIRef(RDFS_LABEL))}
        if pref or alt or label or suppressed:
            snapshot["classes"][iri] = {
                "pref": pref, "alt": alt, "label": label,
                "suppressed": sorted(set(suppressed)),
            }
    return snapshot


# ---------------------------------------------------------------------------
# coverage / conflicts
# ---------------------------------------------------------------------------

def _concept_surfaces(snapshot: dict[str, Any]) -> dict[tuple[str, str], set[str]]:
    surfaces: dict[tuple[str, str], set[str]] = {}
    for iri, node in snapshot["concepts"].items():
        for lang, text in (node.get("pref") or {}).items():
            if text:
                surfaces.setdefault((text, lang), set()).add(iri)
        for item in node.get("alt") or []:
            if item.get("text"):
                surfaces.setdefault((item["text"], item.get("lang") or ""), set()).add(iri)
    return surfaces


def _pref_owners(snapshot: dict[str, Any]) -> dict[tuple[str, str], set[str]]:
    owners: dict[tuple[str, str], set[str]] = {}
    for iri, node in snapshot["concepts"].items():
        for lang, text in (node.get("pref") or {}).items():
            if text:
                owners.setdefault((text, lang), set()).add(iri)
    return owners


def _alt_owners(snapshot: dict[str, Any]) -> dict[tuple[str, str], set[str]]:
    owners: dict[tuple[str, str], set[str]] = {}
    for iri, node in snapshot["concepts"].items():
        for item in node.get("alt") or []:
            if item.get("text"):
                owners.setdefault((item["text"], item.get("lang") or ""), set()).add(iri)
    return owners


def conflicts(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """All duplicate/alias/guard conflicts; ``blocking`` decides publishability."""
    findings: list[dict[str, Any]] = []
    concept_surfaces = _concept_surfaces(snapshot)
    pref_owners = _pref_owners(snapshot)
    alt_owners = _alt_owners(snapshot)
    alias_labels: dict[tuple[str, str], set[str]] = {}

    for (text, lang), owners in sorted(concept_surfaces.items()):
        if len(owners) > 1:
            findings.append({
                "code": "SURFACE_SHARED_BY_MULTIPLE_CONCEPTS",
                "severity": "blocking", "blocking": True,
                "surface": text, "lang": lang, "owners": sorted(owners),
                "message": f"surface {text!r} points to {len(owners)} concepts",
            })
    for key, owners in sorted(pref_owners.items()):
        if key in alt_owners and (owners | alt_owners[key]) - owners:
            others = sorted((owners | alt_owners[key]) - owners)
            findings.append({
                "code": "PREF_CONFLICTS_WITH_ALT_OF_OTHER_CONCEPT",
                "severity": "blocking", "blocking": True,
                "surface": key[0], "lang": key[1], "owners": others,
                "message": f"{key[0]!r} is prefLabel of one concept and altLabel of another",
            })
    for iri, node in sorted(snapshot["concepts"].items()):
        if not (node.get("pref") or {}):
            findings.append({"code": "CONCEPT_MISSING_PREF_LABEL", "severity": "blocking",
                             "blocking": True, "iri": iri,
                             "message": "concept has no skos:prefLabel"})
        if not node.get("definition"):
            findings.append({"code": "CONCEPT_MISSING_DEFINITION", "severity": "warning",
                             "blocking": False, "iri": iri,
                             "message": "concept has no skos:definition (coverage gap)"})
        if not node.get("notation"):
            findings.append({"code": "CONCEPT_MISSING_NOTATION", "severity": "warning",
                             "blocking": False, "iri": iri,
                             "message": "concept has no skos:notation (coverage gap)"})

    for iri, node in sorted(snapshot["classes"].items()):
        suppressed = set(node.get("suppressed") or [])
        for item in node.get("alt") or []:
            if item.get("text") and item["text"] in suppressed:
                findings.append({
                    "code": "SUPPRESSED_SURFACE_STILL_ALIAS",
                    "severity": "blocking", "blocking": True,
                    "iri": iri, "surface": item["text"],
                    "message": "term:suppressedSurface is still an skos:altLabel",
                })

    for iri, entry in sorted(snapshot["aliases"].items()):
        label = entry.get("label")
        owner = entry.get("forClass")
        if not label or not owner:
            findings.append({"code": "ALIAS_INCOMPLETE", "severity": "blocking",
                             "blocking": True, "entry": iri,
                             "message": "term:TermEntry needs both label and forClass"})
        elif owner not in snapshot["concepts"] and owner not in snapshot["classes"]:
            findings.append({"code": "ALIAS_TARGET_MISSING", "severity": "warning",
                             "blocking": False, "entry": iri, "owner": owner,
                             "message": "alias target is not in the imported concepts/classes"})
        if label:
            alias_labels.setdefault((label, owner or ""), set()).add(iri)
        guard = entry.get("guard")
        if guard:
            try:
                compile_guard(guard, iri)
            except PortError as exc:
                findings.append({"code": "GUARD_REGEX_INVALID", "severity": "blocking",
                                 "blocking": True, "entry": iri, "guard": guard,
                                 "message": exc.message})
    for (label, _owner), entries in sorted(alias_labels.items()):
        if len(entries) > 1:
            findings.append({
                "code": "ALIAS_LABEL_DUPLICATED", "severity": "warning", "blocking": False,
                "surface": label, "entries": sorted(entries),
                "message": "same alias label registered more than once",
            })
    return findings


def _field_coverage(snapshot: dict[str, Any]) -> dict[str, Any]:
    concepts = snapshot["concepts"]
    total = len(concepts)
    with_pref = sum(1 for node in concepts.values() if node.get("pref"))
    with_definition = sum(1 for node in concepts.values() if node.get("definition"))
    with_notation = sum(1 for node in concepts.values() if node.get("notation"))
    with_scheme = sum(1 for node in concepts.values()
                      if node.get("inScheme") == METRIC_SCHEME)
    aliases = snapshot["aliases"]
    alias_total = len(aliases)
    alias_with_target = sum(
        1 for entry in aliases.values()
        if (entry.get("forClass") in concepts) or (entry.get("forClass") in snapshot["classes"])
    )

    def _ratio(count: int) -> float | None:
        return round(count / total, 4) if total else None

    return {
        "concepts": total,
        "conceptsWithPrefLabel": with_pref,
        "conceptsWithDefinition": with_definition,
        "conceptsWithNotation": with_notation,
        "conceptsInMetricScheme": with_scheme,
        "conceptPrefCoverage": _ratio(with_pref),
        "conceptDefinitionCoverage": _ratio(with_definition),
        "conceptNotationCoverage": _ratio(with_notation),
        "aliases": alias_total,
        "aliasesWithTarget": alias_with_target,
        "aliasTargetCoverage": round(alias_with_target / alias_total, 4) if alias_total else None,
    }


def coverage(snapshot: dict[str, Any], *, expect_concepts: int | None = None,
             expect_aliases: int | None = None, source: str = "graph") -> dict[str, Any]:
    expect_concepts = EXPECTED_CONCEPTS if expect_concepts is None else expect_concepts
    expect_aliases = EXPECTED_ALIASES if expect_aliases is None else expect_aliases
    fields = _field_coverage(snapshot)
    findings = conflicts(snapshot)
    concept_gap = max(0, expect_concepts - fields["concepts"])
    alias_gap = max(0, expect_aliases - fields["aliases"])
    return {
        "source": source,
        "expected": {
            "concepts": expect_concepts,
            "aliases": expect_aliases,
            "baselineSource": BASELINE_SOURCE,
            "note": "基线来自设计文档；可用 expectConcepts/expectAliases 覆盖，不是推算值",
        },
        "actual": fields,
        "coverage": {
            "conceptRatio": round(fields["concepts"] / expect_concepts, 4)
            if expect_concepts else None,
            "aliasRatio": round(fields["aliases"] / expect_aliases, 4)
            if expect_aliases else None,
            "missingConcepts": concept_gap,
            "missingAliases": alias_gap,
        },
        "complete": concept_gap == 0 and alias_gap == 0,
        "conflicts": findings,
        "counts": {
            "blocking": sum(1 for item in findings if item["blocking"]),
            "warnings": sum(1 for item in findings if not item["blocking"]),
        },
        "generatedAt": _now(),
        "readOnly": True,
    }


# ---------------------------------------------------------------------------
# live graph snapshot (published T-Box)
# ---------------------------------------------------------------------------

def _binding_term(row: dict[str, Any], name: str) -> dict[str, Any]:
    return (row.get("values") or {}).get(name) or {}


def snapshot_from_graph(runtime: Any, graph_iri: str) -> dict[str, Any]:
    snapshot = _empty_snapshot()
    concept_rows = runtime.graph.query(
        f"""
        SELECT ?s ?p ?o FROM <{graph_iri}> WHERE {{
          ?s a <{SKOS}Concept> ;
             <{SKOS}inScheme> <{METRIC_SCHEME}> .
          VALUES ?p {{
            <{SKOS}prefLabel> <{SKOS}altLabel> <{SKOS}definition>
            <{SKOS}notation> <{SKOS}broader>
          }}
          ?s ?p ?o .
        }}
        """
    )
    for row in concept_rows.get("bindings") or []:
        subject = _iri(_binding_term(row, "s").get("iri"))
        predicate = _binding_term(row, "p").get("iri")
        obj = _binding_term(row, "o")
        node = snapshot["concepts"].setdefault(
            subject, {"pref": {}, "alt": [], "definition": None, "notation": None,
                      "broader": [], "inScheme": METRIC_SCHEME}
        )
        if predicate == f"{SKOS}prefLabel":
            node["pref"][str(obj.get("lang") or "")] = _text(obj.get("value"))
        elif predicate == f"{SKOS}altLabel":
            node["alt"].append({"text": _text(obj.get("value")),
                                "lang": str(obj.get("lang") or "")})
        elif predicate == f"{SKOS}definition":
            node["definition"] = _text(obj.get("value"))
        elif predicate == f"{SKOS}notation":
            node["notation"] = _text(obj.get("value"))
        elif predicate == f"{SKOS}broader":
            node["broader"].append(_iri(obj.get("iri")))

    entry_rows = runtime.graph.query(
        f"""
        SELECT ?e ?c ?l ?guard ?status FROM <{graph_iri}> WHERE {{
          ?e a <{TERM_ENTRY}> ; <{TERM}forClass> ?c ; <{TERM}label> ?l .
          OPTIONAL {{ ?e <{TERM}guardRegex> ?guard }}
          OPTIONAL {{ ?e <{TERM}status> ?status }}
        }}
        """
    )
    for row in entry_rows.get("bindings") or []:
        iri = _iri(_binding_term(row, "e").get("iri"))
        entry = snapshot["aliases"].setdefault(iri, {})
        entry["forClass"] = _iri(_binding_term(row, "c").get("iri"))
        entry["label"] = _text(_binding_term(row, "l").get("value"))
        guard = _binding_term(row, "guard")
        if guard:
            entry["guard"] = _text(guard.get("value"))
        status = _binding_term(row, "status")
        if status:
            entry["status"] = _text(status.get("value"))

    class_rows = runtime.graph.query(
        f"""
        SELECT ?s ?p ?o FROM <{graph_iri}> WHERE {{
          ?s <{TERM}termBatch> ?b .
          VALUES ?p {{
            <{SKOS}prefLabel> <{SKOS}altLabel> <{RDFS_LABEL}>
            <{TERM}suppressedSurface>
          }}
          ?s ?p ?o .
        }}
        """
    )
    for row in class_rows.get("bindings") or []:
        subject = _iri(_binding_term(row, "s").get("iri"))
        predicate = _binding_term(row, "p").get("iri")
        obj = _binding_term(row, "o")
        node = snapshot["classes"].setdefault(
            subject, {"pref": {}, "alt": [], "label": {}, "suppressed": []}
        )
        if predicate == f"{SKOS}prefLabel":
            node["pref"][str(obj.get("lang") or "")] = _text(obj.get("value"))
        elif predicate == f"{SKOS}altLabel":
            node["alt"].append({"text": _text(obj.get("value")),
                                "lang": str(obj.get("lang") or "")})
        elif predicate == RDFS_LABEL:
            node["label"][str(obj.get("lang") or "")] = _text(obj.get("value"))
        elif predicate == f"{TERM}suppressedSurface":
            node["suppressed"].append(_text(obj.get("value")))
    for node in snapshot["classes"].values():
        node["suppressed"] = sorted(set(node["suppressed"]))
    return snapshot


def current_graph(runtime: Any) -> str | None:
    try:
        pointer = runtime.ontology.current()
    except Exception:
        pointer = None
    version_id = (pointer or {}).get("versionId")
    if not version_id:
        return None
    try:
        return runtime.ontology.get(version_id).get("graph")
    except Exception:
        return None


def graph_coverage(runtime: Any, *, expect_concepts: int | None = None,
                   expect_aliases: int | None = None) -> dict[str, Any]:
    graph_iri = current_graph(runtime)
    if not graph_iri:
        return {
            "source": "graph",
            "empty": True,
            "emptyReason": "tbox/current 指针不存在或版本无图，术语覆盖率不可算",
            "expected": {"concepts": expect_concepts if expect_concepts is not None
                         else EXPECTED_CONCEPTS,
                         "aliases": expect_aliases if expect_aliases is not None
                         else EXPECTED_ALIASES,
                         "baselineSource": BASELINE_SOURCE},
            "actual": None,
            "conflicts": [],
            "generatedAt": _now(),
            "readOnly": True,
        }
    report = coverage(snapshot_from_graph(runtime, graph_iri),
                      expect_concepts=expect_concepts, expect_aliases=expect_aliases)
    report["graph"] = graph_iri
    report["empty"] = False
    return report


# ---------------------------------------------------------------------------
# diff (new SKOS vs published)
# ---------------------------------------------------------------------------

def _normalized_concept(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "pref": dict(sorted((node.get("pref") or {}).items())),
        "alt": sorted((item.get("text"), item.get("lang") or "")
                      for item in node.get("alt") or []),
        "definition": node.get("definition"),
        "notation": node.get("notation"),
        "broader": sorted(node.get("broader") or []),
    }


def _normalized_aliases(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        iri: {key: entry.get(key) for key in ("forClass", "label", "guard", "status")}
        for iri, entry in snapshot["aliases"].items()
    }


def diff_snapshots(current: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    current = current or _empty_snapshot()
    incoming = incoming or _empty_snapshot()
    cur_concepts = {iri: _normalized_concept(node) for iri, node in current["concepts"].items()}
    new_concepts = {iri: _normalized_concept(node) for iri, node in incoming["concepts"].items()}
    cur_aliases = _normalized_aliases(current)
    new_aliases = _normalized_aliases(incoming)

    added = {
        "concepts": sorted(set(new_concepts) - set(cur_concepts)),
        "aliases": sorted(set(new_aliases) - set(cur_aliases)),
    }
    removed = {
        "concepts": sorted(set(cur_concepts) - set(new_concepts)),
        "aliases": sorted(set(cur_aliases) - set(new_aliases)),
    }
    changed: list[dict[str, Any]] = []
    for iri in sorted(set(cur_concepts) & set(new_concepts)):
        fields = [key for key in cur_concepts[iri]
                  if cur_concepts[iri][key] != new_concepts[iri][key]]
        if fields:
            changed.append({
                "kind": "concept", "iri": iri, "fields": fields,
                "semanticChange": "definition" in fields or "pref" in fields
                or "broader" in fields,
                "from": {key: cur_concepts[iri][key] for key in fields},
                "to": {key: new_concepts[iri][key] for key in fields},
            })
    for iri in sorted(set(cur_aliases) & set(new_aliases)):
        fields = [key for key in cur_aliases[iri]
                  if cur_aliases[iri][key] != new_aliases[iri][key]]
        if fields:
            changed.append({
                "kind": "alias", "iri": iri, "fields": fields,
                "semanticChange": "forClass" in fields or "label" in fields,
                "from": {key: cur_aliases[iri][key] for key in fields},
                "to": {key: new_aliases[iri][key] for key in fields},
            })

    findings = conflicts(incoming)
    blocking = [item for item in findings if item["blocking"]]
    coverage_block = _field_coverage(incoming)
    report = {
        "from": {
            "concepts": len(cur_concepts), "aliases": len(cur_aliases),
            "source": "published T-Box",
        },
        "to": {
            "concepts": len(new_concepts), "aliases": len(new_aliases),
            "source": "uploaded SKOS",
        },
        "added": added,
        "removed": removed,
        "changed": changed,
        "redefined": [item for item in changed if item["semanticChange"]],
        "conflicts": findings,
        "coverage": coverage_block,
        "summary": {
            "addedConcepts": len(added["concepts"]),
            "removedConcepts": len(removed["concepts"]),
            "changedConcepts": sum(1 for item in changed if item["kind"] == "concept"),
            "redefinedConcepts": sum(1 for item in changed
                                    if item["kind"] == "concept" and item["semanticChange"]),
            "addedAliases": len(added["aliases"]),
            "removedAliases": len(removed["aliases"]),
            "changedAliases": sum(1 for item in changed if item["kind"] == "alias"),
            "blockingConflicts": len(blocking),
            "warnings": len(findings) - len(blocking),
        },
        "verdict": {
            "status": "fail" if blocking else "pass",
            "blockingCount": len(blocking),
            "mayPublish": not blocking and (coverage_block["concepts"] == 0
                                            or coverage_block["conceptPrefCoverage"] == 1.0),
            "rule": "存在 blocking 冲突或任一概念缺 prefLabel 时禁止登记为可发布词表",
        },
        "note": "本核对不写图；写入仍走 /ontology/import（SHA-256 校验 + guard 编译）",
        "generatedAt": _now(),
        "readOnly": True,
    }
    report["diffHash"] = _sha256({key: value for key, value in report.items()
                                  if key != "generatedAt"})
    return report


def diff_against_graph(runtime: Any, content: str, fmt: str = "turtle",
                       *, source_name: str | None = None) -> dict[str, Any]:
    graph_iri = current_graph(runtime)
    incoming = parse_skos(content, fmt)
    current = snapshot_from_graph(runtime, graph_iri) if graph_iri else _empty_snapshot()
    report = diff_snapshots(current, incoming)
    report["sourceName"] = source_name
    report["format"] = fmt
    report["contentHash"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    report["baseline"] = {
        "graph": graph_iri,
        "note": None if graph_iri else "无已发布版本，diff 视为全量新增",
    }
    return report


# ---------------------------------------------------------------------------
# check registry (V33)
# ---------------------------------------------------------------------------

def record_check(metadata: Any, report: dict[str, Any], *, source_kind: str = "import",
                 version_id: str | None = None, actor: str = "operator") -> dict[str, Any]:
    check_id = f"tc-{uuid.uuid4().hex[:12]}"
    status = "pass" if report["verdict"]["mayPublish"] else "fail"
    metadata.query(
        """
        INSERT INTO platform.term_check
          (check_id, source_kind, version_id, status, diff_hash, report, created_by)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
        RETURNING check_id
        """,
        (check_id, source_kind, version_id, status, report["diffHash"],
         _canonical(report), actor),
    )
    return {"checkId": check_id, "status": status, "diffHash": report["diffHash"]}


def record_import(metadata: Any, report: dict[str, Any], *, source_name: str | None,
                  actor: str = "operator") -> dict[str, Any]:
    if not report["verdict"]["mayPublish"]:
        raise PortError(
            code="Conflict",
            message="term diff has blocking conflicts; import is refused",
            provider="platform", provider_code=E_TERM_CHECK_FAILED,
            details={"blocking": report["verdict"]["blockingCount"],
                     "diffHash": report["diffHash"]},
        )
    import_id = f"ti-{uuid.uuid4().hex[:12]}"
    metadata.query(
        """
        INSERT INTO platform.term_import
          (import_id, source_name, content_hash, status, diff, created_by)
        VALUES (%s, %s, %s, 'checked', %s::jsonb, %s)
        RETURNING import_id
        """,
        (import_id, source_name, report["contentHash"], _canonical(report), actor),
    )
    return {
        "importId": import_id,
        "status": "checked",
        "diffHash": report["diffHash"],
        "next": "POST /ontology/import（T-Box 导入仍执行 SHA-256 校验与 guard 编译）",
        "note": "术语核对通过；本端点不写图",
    }


def list_checks(metadata: Any, limit: int = 50) -> dict[str, Any]:
    rows = metadata.query(
        "SELECT check_id, source_kind, version_id, status, diff_hash, created_at "
        "FROM platform.term_check ORDER BY created_at DESC, check_id LIMIT %s",
        (limit,),
    )
    items = [
        {
            "checkId": row["check_id"],
            "sourceKind": row["source_kind"],
            "versionId": row.get("version_id"),
            "status": row["status"],
            "diffHash": row["diff_hash"],
            "createdAt": row["created_at"].isoformat()
            if hasattr(row["created_at"], "isoformat") else row["created_at"],
        }
        for row in rows
    ]
    return {
        "items": items, "count": len(items),
        "empty": not items,
        "emptyReason": None if items else "尚无术语核对记录",
        "readOnly": True,
    }
