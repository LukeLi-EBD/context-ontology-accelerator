# -*- coding: utf-8 -*-
"""只读：用 GET /answerable 取 G05/G06 的覆盖度拆分（不写库）。"""
import json
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8080"
CASES = {
    "G05": "当事人关系历史记录保留多久",
    "G06": "抵押物价值发生巨大变化时银行如何处理",
}

out = {}
for cid, q in CASES.items():
    url = f"{BASE}/answerable?q=" + urllib.parse.quote(q, safe="") + "&layers=true"
    d = json.loads(urllib.request.urlopen(url, timeout=30).read().decode("utf-8"))
    out[cid] = {
        "query": q,
        "answerable": d.get("answerable"),
        "coverage": d.get("coverage"),
        "coverageChars": d.get("coverageChars"),
        "threshold": d.get("threshold"),
        "matchedTerms": [t.get("label") if isinstance(t, dict) else t for t in (d.get("matchedTerms") or [])],
        "missing": d.get("missing"),
        "version": d.get("ontologyVersion"),
    }

print(json.dumps(out, ensure_ascii=False, indent=2))
