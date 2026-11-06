# -*- coding: utf-8 -*-
"""只读量化：当前 T-Box 知识供给面的可核对数字。

约束：只发 GET /browse/sparql（SELECT），不写库、不发布、不改指针。
输出：stdout 摘要 + 同目录 quantify_<ts>.json 证据。
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

BASE = "http://127.0.0.1:8080"
TZ = timezone(timedelta(hours=8))

PREFIXES = """
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX sh:   <http://www.w3.org/ns/shacl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX term: <https://w3id.org/fsldm/terms#>
PREFIX fsldm: <https://w3id.org/fsldm/>
"""


GRAPH_IRI: str = ""


def sparql(query: str) -> dict:
    q = PREFIXES + query
    if GRAPH_IRI:
        # T-Box 是命名图；/browse/sparql 不带 FROM 时默认图为空
        q = q.replace(" WHERE", f" FROM <{GRAPH_IRI}> WHERE", 1)
    url = f"{BASE}/browse/sparql?query=" + urllib.parse.quote(q, safe="")
    with urllib.request.urlopen(url, timeout=60) as r:
        raw = r.read().decode("utf-8")
    return json.loads(raw)


def _val(v: dict):
    if not v:
        return None
    return v.get("value") if v.get("value") is not None else v.get("iri")


def rows(query: str, var: str = "s") -> list[str]:
    d = sparql(query)
    out = []
    for b in d.get("bindings", []):
        v = _val(b.get("values", {}).get(var, {}))
        if v is not None:
            out.append(v)
    return out


def bindings(query: str) -> list[dict]:
    d = sparql(query)
    out = []
    for b in d.get("bindings", []):
        row = {k: _val(v) for k, v in b.get("values", {}).items()}
        if any(v is None for v in row.values()):
            row = {k: v for k, v in row.items() if v is not None}
        out.append(row)
    return out


def main() -> int:
    ev: dict = {"collectedAt": datetime.now(TZ).isoformat()}

    # ---- 0) 指针与图 ----
    with urllib.request.urlopen(f"{BASE}/browse/terms?limit=1", timeout=30) as r:
        terms_head = json.loads(r.read().decode("utf-8"))
    ev["pointer"] = terms_head.get("pointer")
    global GRAPH_IRI
    GRAPH_IRI = (ev["pointer"] or {}).get("graph") or ""

    # ---- 1) 类 / 属性计数 ----
    quant = [
        ("classes", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a owl:Class }"),
        ("objectProperties", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a owl:ObjectProperty }"),
        ("datatypeProperties", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a owl:DatatypeProperty }"),
        ("annotationProperties", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a owl:AnnotationProperty }"),
        ("functionalProps", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a owl:FunctionalProperty }"),
        ("allPropsRDF", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a rdf:Property }"),
        ("restrictions", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a owl:Restriction }"),
        ("namedIndividuals", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a owl:NamedIndividual }"),
        ("metricScheme", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a term:MetricScheme }"),
        ("termEntries", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a term:TermEntry }"),
        ("termBatchAnchors", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s term:termBatch ?b }"),
        ("skosConcepts", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a skos:Concept }"),
        ("prefLabelZh", 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s skos:prefLabel ?l . FILTER(lang(?l)="zh") }'),
        ("prefLabelEn", 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s skos:prefLabel ?l . FILTER(lang(?l)="en") }'),
        ("altLabelZh", 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s skos:altLabel ?l . FILTER(lang(?l)="zh") }'),
        ("altLabelNoLang", 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s skos:altLabel ?l . FILTER(lang(?l)="") }'),
        ("definitions", 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s skos:definition ?l . FILTER(lang(?l)="zh") }'),
        ("classesNoLabel", 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a owl:Class . FILTER NOT EXISTS { ?s rdfs:label ?l } }'),
        ("propsNoLabel", 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { { ?s a owl:ObjectProperty } UNION { ?s a owl:DatatypeProperty } FILTER NOT EXISTS { ?s rdfs:label ?l } }'),
    ]
    counts = {}
    for name, q in quant:
        d = sparql(q)
        counts[name] = int(_val(d["bindings"][0]["values"]["n"]))
    ev["counts"] = counts

    # ---- 2) 约束细化（owl:Restriction 的具体种类）----
    restr = bindings("""
        SELECT ?p (COUNT(DISTINCT ?s) AS ?n) WHERE {
          ?s a owl:Restriction ; ?p ?v .
          FILTER(?p IN (owl:allValuesFrom, owl:someValuesFrom, owl:hasValue, owl:cardinality,
                        owl:minCardinality, owl:maxCardinality, owl:qualifiedCardinality,
                        owl:minQualifiedCardinality, owl:maxQualifiedCardinality, owl:onClass, owl:onProperty))
        } GROUP BY ?p ORDER BY DESC(?n)
    """)
    ev["restrictionKinds"] = {b["p"].rsplit("#", 1)[-1]: int(b["n"]) for b in restr}

    # ---- 3) 全量属性（IRI/label/comment）用于语义分类 ----
    props = bindings("""
        SELECT DISTINCT ?s ?label ?comment ?dom ?range WHERE {
          { ?s a owl:ObjectProperty } UNION { ?s a owl:DatatypeProperty } UNION { ?s a rdf:Property }
          OPTIONAL { ?s rdfs:label ?label }
          OPTIONAL { ?s rdfs:comment ?comment }
          OPTIONAL { ?s rdfs:domain ?dom }
          OPTIONAL { ?s rdfs:range ?range }
        }
    """)
    ev["propertyRowCount"] = len(props)
    ev["propertyIRIs"] = sorted({p["s"] for p in props})

    # ---- 4) 全部类（IRI/label）用于语义分类 ----
    classes = bindings("""
        SELECT DISTINCT ?s ?label ?comment WHERE {
          ?s a owl:Class .
          OPTIONAL { ?s rdfs:label ?label }
          OPTIONAL { ?s rdfs:comment ?comment }
        }
    """)
    ev["classRowCount"] = len(classes)

    def local(iri: str) -> str:
        return re.split(r"[#/]", iri.rstrip("#/"))[-1]

    def ns(iri: str) -> str:
        parts = re.split(r"(#|/)", iri.rstrip("#/"))
        return "".join(parts[:-1]).rstrip("#/")

    ev["classesByNamespace"] = dict(Counter(ns(c["s"]) for c in classes).most_common())
    ev["propsByNamespace"] = dict(Counter(ns(p["s"]) for p in props).most_common())

    def text_of(r: dict) -> str:
        return " ".join(x for x in (local(r["s"]), r.get("label") or "", r.get("comment") or "") if x).lower()

    CAT = {
        "时效": ["date", "time", "effective", "expiry", "expire", "duration", "period", "term", "tenor",
                 "maturity", "retention", "retain", "asof", "as_of", "day", "days", "date", "日期", "时间",
                 "期限", "有效期", "到期", "存续", "保留", "留存", "时效", "天数", "时点"],
        "流程": ["process", "procedure", "step", "stage", "workflow", "transition", "status", "state",
                 "event", "action", "operation", "process", "流程", "步骤", "状态", "环节", "处置", "处理",
                 "审批", "事件", "动作"],
        "约束": ["must", "shall", "require", "constraint", "rule", "policy", "restriction", "mandatory",
                 "不允许", "必须", "应当", "约束", "规则", "制度", "政策", "限制", "禁止"],
        "阈值": ["threshold", "limit", "max", "min", "ratio", "rate", "percent", "quota", "cap", "floor",
                 "ceil", "阈值", "限额", "上限", "下限", "比例", "比例", "比率", "临界"],
    }

    def classify(rs: list[dict]) -> dict:
        hits = defaultdict(list)
        for r in rs:
            t = text_of(r)
            for cat, kws in CAT.items():
                if any(k in t for k in kws):
                    hits[cat].append({"iri": r["s"], "label": r.get("label"), "local": local(r["s"])})
        return {k: v for k, v in hits.items()}

    prop_hits = classify(props)
    class_hits = classify(classes)
    ev["propertyClassified"] = {k: {"count": len(v), "items": v} for k, v in prop_hits.items()}
    ev["classClassified"] = {k: {"count": len(v), "items": v} for k, v in class_hits.items()}

    # ---- 5) 关键词直查：G05/G06 所需知识是否存在 ----
    probes = {
        "retention_any": ["保留", "留存", "retention", "retain"],
        "disposal_any": ["处置", "处理", "disposal", "dispose", "handling"],
        "revaluation_any": ["重估", "价值变化", "估值", "revalu", "valuation"],
        "threshold_any": ["阈值", "限额", "上限", "threshold", "limit"],
        "policy_any": ["制度", "政策", "办法", "policy", "regulation"],
    }
    probe_result = {}
    all_nodes = [{"iri": c["s"], "label": c.get("label"), "comment": c.get("comment")} for c in classes] + \
                [{"iri": p["s"], "label": p.get("label"), "comment": p.get("comment")} for p in props]
    for name, kws in probes.items():
        hit = []
        for r in all_nodes:
            t = text_of({"s": r["iri"], "label": r.get("label") or "", "comment": r.get("comment") or ""})
            if any(k.lower() in t for k in kws):
                hit.append({"iri": r["iri"], "label": r.get("label"), "local": local(r["iri"])})
        probe_result[name] = hit
    ev["keywordProbes"] = {k: {"count": len(v), "items": v[:20]} for k, v in probe_result.items()}

    # ---- 6) MetricScheme 明细：命名空间与 variantOf ----
    ms = bindings("""
        SELECT ?s ?label ?variantOf WHERE {
          ?s a term:MetricScheme .
          OPTIONAL { ?s skos:prefLabel ?label }
          OPTIONAL { ?s term:variantOf ?variantOf }
        }
    """)
    ev["metricSchemeRows"] = len(ms)
    ev["metricSchemeVariants"] = len([m for m in ms if m.get("variantOf")])
    ev["metricSchemeSample"] = ms[:3]

    # ---- 7) term: 命名空间概念（高水位判据基线）----
    term_concepts = bindings("""
        SELECT ?s ?status WHERE {
          ?s a skos:Concept . FILTER(STRSTARTS(STR(?s), "https://w3id.org/fsldm/terms#"))
          OPTIONAL { ?s term:termStatus ?status }
        }
    """)
    ev["termConceptCount"] = len(term_concepts)
    ev["termConceptByStatus"] = dict(Counter(t.get("status") or "none" for t in term_concepts))

    # ---- 输出 ----
    ts = datetime.now(TZ).strftime("%Y%m%dT%H%M%S")
    out = f"D:/agentABC/wt/r-qa-integration/doc/_qa/knowledge-gap/quantify_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(ev, f, ensure_ascii=False, indent=2)

    print(json.dumps({k: ev[k] for k in ("pointer", "counts", "restrictionKinds", "propertyRowCount",
                                        "classRowCount", "classesByNamespace", "propsByNamespace",
                                        "metricSchemeRows", "metricSchemeVariants",
                                        "termConceptCount", "termConceptByStatus")},
                     ensure_ascii=False, indent=2))
    print("\n--- 语义分类计数 ---")
    for k, v in ev["propertyClassified"].items():
        print(f"property {k}: {v['count']}")
        for it in v["items"][:15]:
            print("   ", it["local"], "|", it["label"])
    for k, v in ev["classClassified"].items():
        print(f"class {k}: {v['count']}")
        for it in v["items"][:15]:
            print("   ", it["local"], "|", it["label"])
    print("\n--- 关键词直查 ---")
    for k, v in ev["keywordProbes"].items():
        print(f"{k}: {v['count']} -> {[i['local'] for i in v['items']]}")
    print(f"\nEVIDENCE: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
