# -*- coding: utf-8 -*-
"""候选词面冲突检查：新 seed 想用的 zh 词面是否已被占用（只读）。"""
import json
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8080"
GRAPH = "urn:platform:graph:tbox:ont-11f92ebb3326"
CANDIDATES = ["保留期限", "留存期限", "记录保留", "留存期", "保留时长",
              "抵押物重估", "价值重估", "重估", "处置流程", "处置程序", "押品处置", "价值变化",
              "大额变动", "重估阈值", "处置时限"]

q = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s ?p ?l FROM <%s> WHERE {
  ?s ?p ?l .
  FILTER(?p IN (skos:prefLabel, skos:altLabel, rdfs:label))
}""" % GRAPH
url = f"{BASE}/browse/sparql?query=" + urllib.parse.quote(q, safe="")
data = json.loads(urllib.request.urlopen(url, timeout=60).read().decode("utf-8"))

def val(v):
    return v.get("value") if v.get("value") is not None else v.get("iri")

rows = [{k: val(v) for k, v in b["values"].items()} for b in data["bindings"]]
print("总词面行数:", len(rows))
for cand in CANDIDATES:
    hits = [r for r in rows if cand in (r.get("l") or "")]
    print(f"{cand}: {len(hits)}")
    for h in hits[:6]:
        print("   ", h["l"], "|", h["p"].rsplit("#", 1)[-1], "|", h["s"])
