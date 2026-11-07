# -*- coding: utf-8 -*-
"""注释层核查：rdfs:comment / skos:definition 里是否有规则性语句（避免只看 label 而漏判）。"""
import json
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8080"
GRAPH = "urn:platform:graph:tbox:ont-11f92ebb3326"
KW = ["必须", "应当", "不得", "禁止", "保留", "留存", "处置", "流程", "审批", "阈值", "限额", "重估"]

q = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?s ?p ?l FROM <%s> WHERE {
  ?s ?p ?l .
  FILTER(?p IN (rdfs:comment, skos:definition))
}""" % GRAPH
url = f"{BASE}/browse/sparql?query=" + urllib.parse.quote(q, safe="")
d = json.loads(urllib.request.urlopen(url, timeout=60).read().decode("utf-8"))
def val(v):
    return v.get("value") if v.get("value") is not None else v.get("iri")
rows = [{k: val(v) for k, v in b["values"].items()} for b in d["bindings"]]
print("comment/definition 行数:", len(rows))
for k in KW:
    hits = [r for r in rows if k in (r.get("l") or "")]
    print(f"{k}: {len(hits)}")
    for h in hits[:5]:
        txt = (h.get("l") or "").replace("\n", " ")
        print("   ", h["s"].rsplit("#", 1)[-1], "|", txt[:110])
