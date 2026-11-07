# -*- coding: utf-8 -*-
"""第二遍只读分析：术语基线 + 属性/类逐条清单（可核对）。"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

BASE = "http://127.0.0.1:8080"
GRAPH = "urn:platform:graph:tbox:ont-11f92ebb3326"
TZ = timezone(timedelta(hours=8))
PFX = """
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX term: <https://w3id.org/fsldm/terms#>
"""


def q(query):
    full = PFX + query.replace(" WHERE", f" FROM <{GRAPH}> WHERE", 1)
    url = f"{BASE}/browse/sparql?query=" + urllib.parse.quote(full, safe="")
    return json.loads(urllib.request.urlopen(url, timeout=60).read().decode("utf-8"))


def val(v):
    return v.get("value") if v.get("value") is not None else v.get("iri")


def rows(query):
    d = q(query)
    return [{k: val(v) for k, v in b["values"].items()} for b in d.get("bindings", [])]


def count(query):
    return int(val(q(query)["bindings"][0]["values"]["n"]))


out = {}
docs = {}

# 1) MetricScheme 基线
docs["metricSchemeConcepts"] = count(
    "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s skos:inScheme term:MetricScheme }")
docs["termNsConcepts"] = count(
    'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a skos:Concept . FILTER(STRSTARTS(STR(?s), "https://w3id.org/fsldm/terms#")) }')
docs["termNsNotInMetricScheme"] = count(
    'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a skos:Concept . FILTER(STRSTARTS(STR(?s), "https://w3id.org/fsldm/terms#")) FILTER NOT EXISTS { ?s skos:inScheme term:MetricScheme } }')
docs["metricSchemeVariants"] = count(
    "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s skos:inScheme term:MetricScheme ; term:variantOf ?v }")
docs["metricConceptsWithUnit"] = count(
    "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s skos:inScheme term:MetricScheme ; term:unit ?u }")
docs["conceptSchemes"] = count("SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a skos:ConceptScheme }")

schemes = rows("SELECT ?s ?l WHERE { ?s a skos:ConceptScheme . OPTIONAL { ?s skos:prefLabel ?l } }")
docs["schemeList"] = [{"iri": r["s"], "label": r.get("l")} for r in schemes]

# 2) 术语门禁锚点与词条基线
docs["anchorClasses"] = count("SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s term:termBatch ?b }")
anchors = rows("SELECT ?s ?l ?b WHERE { ?s term:termBatch ?b OPTIONAL { ?s skos:prefLabel ?l } }")
docs["anchorList"] = sorted([{"iri": r["s"], "label": r.get("l"), "batch": r.get("b")} for r in anchors],
                            key=lambda x: x["iri"])
docs["termEntries"] = count("SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a term:TermEntry }")
docs["entriesByStatus"] = {r["st"]: int(r["n"]) for r in rows(
    "SELECT ?st (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a term:TermEntry ; term:status ?st } GROUP BY ?st")}
docs["altLabelZhOnAnchors"] = count(
    'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s term:termBatch ?b ; skos:altLabel ?a . FILTER(lang(?a)="zh") }')
docs["prefLabelZhOnAnchors"] = count(
    'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s term:termBatch ?b ; skos:prefLabel ?l . FILTER(lang(?l)="zh") }')

# 3) 类与属性逐条清单（label/comment/domain/range）
classes = rows("""
SELECT ?s ?label ?comment WHERE {
  ?s a owl:Class .
  OPTIONAL { ?s rdfs:label ?label }
  OPTIONAL { ?s rdfs:comment ?comment }
}""")
props = rows("""
SELECT DISTINCT ?s ?label ?comment ?dom ?range WHERE {
  { ?s a owl:ObjectProperty } UNION { ?s a owl:DatatypeProperty }
  OPTIONAL { ?s rdfs:label ?label }
  OPTIONAL { ?s rdfs:comment ?comment }
  OPTIONAL { ?s rdfs:domain ?dom }
  OPTIONAL { ?s rdfs:range ?range }
}""")

def local(iri):
    import re
    return re.split(r"[#/]", iri.rstrip("#/"))[-1]

# 4) 精确分类：只看 label（+ IRI 本地名），不看 comment（comment 只是说明）
KW = {
    "时间事实字段": ["日期", "时间", "时点", "日", "date", "time", "timestamp", "day"],
    "时效制度": ["期限", "有效期", "保留", "留存", "时效", "存续期", "retention", "retain", "tenor", "validity"],
    "流程制度": ["处置", "处理", "流程", "步骤", "环节", "审批", "程序", "工单", "workflow", "procedure", "process", "disposal"],
    "阈值制度": ["阈值", "限额", "上限", "下限", "临界", "封顶", "threshold", "limit", "cap", "floor"],
    "政策约束": ["必须", "应当", "不得", "禁止", "规则", "制度", "约束", "policy", "constraint", "rule"],
}


def classify(items, is_prop):
    res = {}
    for cat, kws in KW.items():
        hit = []
        for r in items:
            lab = (r.get("label") or "")
            loc = local(r["s"])
            t = (lab + " " + loc).lower()
            if any(k.lower() in t for k in kws):
                hit.append({"iri": r["s"], "local": loc, "label": lab, "domain": r.get("dom"), "range": r.get("range")})
        res[cat] = hit
    return res


out["classCount"] = len({c["s"] for c in classes})
out["propCount"] = len({p["s"] for p in props})
out["classClassify"] = {k: len(v) for k, v in classify(classes, False).items()}
out["propClassify"] = {k: len(v) for k, v in classify(props, True).items()}
out["classHits"] = {k: [i["local"] + "|" + (i["label"] or "") for i in v]
                    for k, v in classify(classes, False).items()}
out["propHits"] = {k: [i["local"] + "|" + (i["label"] or "") for i in v]
                   for k, v in classify(props, True).items()}

# 5) 全量属性清单（可核对，写 TSV）
ts = datetime.now(TZ).strftime("%Y%m%dT%H%M%S")
tsv = f"D:/agentABC/wt/r-qa-integration/doc/_design/knowledge-gap/properties_{ts}.tsv"
with open(tsv, "w", encoding="utf-8") as f:
    f.write("iri\tlocal\tlabel\tdomain\trange\n")
    for p in sorted(props, key=lambda x: x["s"]):
        f.write("\t".join([p["s"], local(p["s"]), (p.get("label") or "").replace("\t", " "),
                           p.get("dom") or "", p.get("range") or ""]) + "\n")
out["propertiesTsv"] = tsv

json.dump({"collectedAt": datetime.now(TZ).isoformat(), "baseline": docs, "classify": out},
          open(f"D:/agentABC/wt/r-qa-integration/doc/_design/knowledge-gap/baseline_{ts}.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(json.dumps({"baseline": docs, "classify": {k: out[k] for k in ("classCount", "propCount", "classClassify", "propClassify", "classHits", "propHits")}},
                 ensure_ascii=False, indent=2))
