# -*- coding: utf-8 -*-
"""近邻盘点：与 G05/G06 语义相邻的类，确认"有实体、无规则"。"""
import json
import re
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8080"
GRAPH = "urn:platform:graph:tbox:ont-11f92ebb3326"
TOKENS = ["history", "历史", "rule", "规则", "policy", "制度", "threshold", "thresholds",
          "limit", "限额", "procedure", "流程", "process", "处置", "retention", "保留",
          "inspection", "查勘", "value", "估值", "quote", "报价", "salvage", "残值", "revalu"]

q = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s ?l FROM <%s> WHERE {
  ?s a owl:Class .
  OPTIONAL { ?s rdfs:label ?l }
}""" % GRAPH
url = f"{BASE}/browse/sparql?query=" + urllib.parse.quote(q, safe="")
data = json.loads(urllib.request.urlopen(url, timeout=60).read().decode("utf-8"))

def val(v):
    return v.get("value") if v.get("value") is not None else v.get("iri")

rows = [{k: val(v) for k, v in b["values"].items()} for b in data["bindings"]]
for tok in TOKENS:
    hits = [r for r in rows if tok.lower() in ((r.get("l") or "") + " " + re.split(r"[#/]", r["s"])[-1]).lower()]
    print(f"{tok}: {len(hits)} -> " + ", ".join(sorted({(r.get('l') or '') + '(' + re.split(r'[#/]', r['s'])[-1] + ')' for r in hits})))
