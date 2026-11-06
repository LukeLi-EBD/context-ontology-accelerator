# -*- coding: utf-8 -*-
"""只读推演：在不发布的前提下，用与 answerable.py 相同的算法预测
候选知识词面对 G05/G06 覆盖度的影响。

算法镜像自 platform_core/answerable.py：
- STOPWORDS 原样复制
- 覆盖 = 被任一 label 子串命中的内容字符 / 内容字符总数
- 长词优先、不重叠占用
"""
import json
import re
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8080"
GRAPH = "urn:platform:graph:tbox:ont-11f92ebb3326"

STOPWORDS = (
    "为什么", "怎么样", "怎么", "如何", "什么", "哪些", "哪个", "哪里", "多少",
    "几个", "是否", "有没有", "能否", "请问", "告诉我", "一下", "以及", "关于",
    "根据", "的", "了", "是", "在", "和", "与", "及", "并", "或", "有", "吗",
    "呢", "啊", "请", "帮", "我", "你", "它", "都", "也", "还", "就", "很",
)
PUNCT = set(" \t\r\n，。？！、；：\"'“”‘’（）《》〈〉…—,.;:?!()[]{}<>-_/\\|@#$%^&*+=~`")
MIN_TERM_CHARS = 2


def fetch_terms():
    q = (
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
        "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> "
        f"SELECT ?s ?p ?l FROM <{GRAPH}> WHERE {{ "
        "?s ?p ?l . FILTER(?p IN (skos:prefLabel, skos:altLabel, rdfs:label)) }"
    )
    url = f"{BASE}/browse/sparql?query=" + urllib.parse.quote(q, safe="")
    d = json.loads(urllib.request.urlopen(url, timeout=60).read().decode("utf-8"))
    out = []
    for b in d["bindings"]:
        v = b["values"]
        lab = v.get("l", {}).get("value")
        if lab:
            out.append(lab)
    return out


def content_mask(normalized):
    mask = [ch not in PUNCT for ch in normalized]
    for sw in sorted(STOPWORDS, key=len, reverse=True):
        start = normalized.find(sw)
        while start != -1:
            for i in range(start, start + len(sw)):
                mask[i] = False
            start = normalized.find(sw, start + 1)
    return mask, sum(1 for f in mask if f)


def coverage(query, labels):
    normalized = re.sub(r"\s+", "", query.lower())
    mask, total = content_mask(normalized)
    taken = [False] * len(normalized)
    hits = []
    for lab in sorted({re.sub(r"\s+", "", l.lower()) for l in labels}, key=len, reverse=True):
        if len(lab) < MIN_TERM_CHARS:
            continue
        start = normalized.find(lab)
        while start != -1:
            end = start + len(lab)
            if not any(taken[start:end]):
                for i in range(start, end):
                    taken[i] = True
                hits.append(lab)
            start = normalized.find(lab, start + 1)
    covered = sum(1 for i, f in enumerate(mask) if f and taken[i])
    return {"coverage": round(covered / total, 4), "covered": covered, "total": total,
            "hits": sorted(set(hits)), "answerable": covered / total >= 0.6}


CASES = {
    "G05": "当事人关系历史记录保留多久",
    "G06": "抵押物价值发生巨大变化时银行如何处理",
}
# 候选词面分两类：业务自然词 vs 题面片段（后者不建议进术语层）
SCENARIOS = {
    "G05": {
        "基线（现有本体）": [],
        "业务自然词 保留期/留存期": ["保留期", "留存期"],
        "业务自然词 记录保留": ["记录保留"],
        "题面片段 保留多久": ["保留多久"],
    },
    "G06": {
        "基线（现有本体）": [],
        "业务自然词 价值重估/处置流程": ["价值重估", "处置流程", "押品处置"],
        "业务自然词 巨大变化": ["巨大变化"],
        "题面片段 价值发生巨大变化": ["价值发生巨大变化"],
        "题面片段 银行处理": ["银行处理"],
    },
}

existing = fetch_terms()
print("graph label rows:", len(existing))
report = {}
for cid, q in CASES.items():
    report[cid] = {"query": q, "existing": coverage(q, existing), "scenarios": {}}
    for name, extra in SCENARIOS[cid].items():
        report[cid]["scenarios"][name] = coverage(q, existing + extra)

print(json.dumps(report, ensure_ascii=False, indent=2))
