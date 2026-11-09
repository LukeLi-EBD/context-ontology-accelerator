"""T1/T2 landing checks + the frozen 24-query metric (before/after, same process).

Run inside the platform container:
  python /tmp/hosttests/term_eval.py

It asserts the L1-01 gap (exactly 146 legacy untagged altLabels), the term-layer
counts, then measures the 24-query set twice on the same SearchService:
term_expand/lexical_expand = false (baseline) and true (candidate).
MRR@10 is reported over the 6 gold queries only; seedHit@1 over all 24.
Every number is Provisional per _design/24 section 5.6 (gold 6/24).
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "/app/src")

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, SKOS

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.termlex import TermLexicon

CONFIG = "/data/platform.yaml"
BUNDLE = "/data/ontology/fsldm-tbox-v1.1.ttl"
SHAPES = "/data/shapes/fsldm/terms.ttl"

CORE = "https://w3id.org/fsldm/core#"
PARTY = "https://w3id.org/fsldm/party#"
AGMT = "https://w3id.org/fsldm/agreement#"
EVT = "https://w3id.org/fsldm/event#"
ASSET = "https://w3id.org/fsldm/asset#"
BANK = "https://w3id.org/fsldm/banking#"
INS = "https://w3id.org/fsldm/insurance#"

TERM = "https://w3id.org/fsldm/terms#"
PROV = "http://www.w3.org/ns/prov#"

QUERIES = [
    # A1-A6: the six A-tier aliases with evidence; only these carry a gold chunk.
    {"q": "她名下的存款帐户是怎么自动还房贷的？", "exp": [AGMT + "Account"], "doc": "08b15dc6c1fcac79603efa96716b305e4e4328b34190b27f90e4883623cdae5a", "term": "帐户", "note": "A1 帐户"},
    {"q": "授信合同里对个人贷款和企业贷款分别怎么约定？", "exp": [AGMT + "CreditAgreement"], "doc": "2c99ce56ddd8b9fd1b4fdd1575258cc355c55f92950dd79549374ca76d40b541", "term": "授信合同", "note": "A2 授信合同"},
    {"q": "个贷系统自然人基本信息表包含哪些字段？", "exp": [PARTY + "Individual"], "doc": "2c99ce56ddd8b9fd1b4fdd1575258cc355c55f92950dd79549374ca76d40b541", "term": "自然人", "note": "A3 自然人"},
    {"q": "当事人关系历史记录保留多久？", "exp": [PARTY + "PartyRelationship"], "doc": "22c84924a40eedad4a0b6eb5766954b362c3c26d31c3fde12ca74f66a2143334", "term": "当事人关系", "note": "A4 当事人关系"},
    {"q": "抵押物价值发生巨大变化时银行如何处理？", "exp": [ASSET + "CollateralItem"], "doc": "2c99ce56ddd8b9fd1b4fdd1575258cc355c55f92950dd79549374ca76d40b541", "term": "抵押物", "note": "A5 抵押物"},
    {"q": "抵押合同的合同号数据质量是怎么控制的？", "exp": [BANK + "CollateralAgreement"], "doc": "2c99ce56ddd8b9fd1b4fdd1575258cc355c55f92950dd79549374ca76d40b541", "term": "抵押合同", "note": "A6 抵押合同"},
    # A7-A12: the remaining failure surfaces from 05 section 1.1.
    {"q": "客户的基本信息从哪些系统采集？", "exp": [CORE + "Party"], "note": "A7 客户"},
    {"q": "不良率是多少？", "exp": [CORE + "Metric"], "note": "A8 不良率"},
    {"q": "集团客户的授信集中度如何计算？", "exp": [PARTY + "PartyGroup", AGMT + "CreditAgreement"], "note": "A9 集团客户"},
    {"q": "关联客户之间的风险传染怎么识别？", "exp": [PARTY + "PartyRelationship", PARTY + "PartyGroup"], "note": "A10 关联客户"},
    {"q": "这个险种对应哪些保险产品？", "exp": [INS + "InsuranceProduct"], "note": "A11 险种"},
    {"q": "报案之后多久立案？", "exp": [EVT + "ClaimEvent"], "note": "A12 报案"},
    # B: the five scenario sentences from 05 section 1.2.
    {"q": "这家客户在你们这有几个账户？", "exp": [CORE + "Party", AGMT + "Account"], "note": "B1 多概念短句"},
    {"q": "单一集团客户授信集中度是多少？", "exp": [PARTY + "PartyGroup", AGMT + "CreditAgreement"], "note": "B2 集团授信"},
    {"q": "今年报案立案率、案均已决金额多少？", "exp": [EVT + "ClaimEvent", AGMT + "Claim"], "note": "B3 复合指标"},
    {"q": "不良率 / NPL ratio 是多少？", "exp": [CORE + "Metric"], "note": "B4 中英混写"},
    {"q": "查一下这张保单的保障项", "exp": [AGMT + "Policy", INS + "Coverage"], "note": "B5 口语化"},
    # C: seven regulatory metric names (bank 2 / insurance 4 / customer 1).
    {"q": "逾期贷款余额占比是多少？", "exp": [AGMT + "CreditAgreement", CORE + "Metric"], "note": "C1 银行"},
    {"q": "单一客户贷款集中度是多少？", "exp": [CORE + "Party", CORE + "Metric"], "note": "C2 银行"},
    {"q": "今年报案立案率是多少？", "exp": [EVT + "ClaimEvent", AGMT + "Claim"], "note": "C3 保险"},
    {"q": "今年案均赔款是多少？", "exp": [AGMT + "Claim", CORE + "Metric"], "note": "C4 保险"},
    {"q": "今年保单继续率是多少？", "exp": [AGMT + "Policy", CORE + "Metric"], "note": "C5 保险"},
    {"q": "今年退保率是多少？", "exp": [AGMT + "Policy", CORE + "Metric"], "note": "C6 保险"},
    {"q": "本年客户AUM是多少？", "exp": [CORE + "Party", CORE + "Metric"], "note": "C7 客户经营"},
]


def counts(graph: Graph) -> dict[str, int]:
    untagged = sum(
        1
        for _, obj in graph.subject_objects(SKOS.altLabel)
        if isinstance(obj, Literal) and not obj.language
    )
    return {
        "untaggedAltLabels": untagged,
        "taggedAltLabels": sum(
            1
            for _, obj in graph.subject_objects(SKOS.altLabel)
            if isinstance(obj, Literal) and obj.language
        ),
        "anchorClasses": sum(1 for _ in graph.subjects(URIRef(TERM + "termBatch"), None)),
        "termEntries": sum(
            1 for _ in graph.subjects(RDF.type, URIRef(TERM + "TermEntry"))
        ),
        "activities": sum(1 for _ in graph.subjects(RDF.type, URIRef(PROV + "Activity"))),
        "canonicalFor": sum(1 for _ in graph.subject_objects(URIRef(TERM + "canonicalFor"))),
        "suppressedSurface": sum(
            1 for _ in graph.subject_objects(URIRef(TERM + "suppressedSurface"))
        ),
    }


def resolve_gold(runtime) -> None:
    for item in QUERIES:
        if not item.get("doc"):
            continue
        rows = runtime.metadata.query(
            "SELECT chunk_id FROM platform.document_chunk "
            "WHERE document_id = %s AND text ILIKE %s "
            "ORDER BY page_from, chunk_id LIMIT 1",
            (item["doc"], f"%{item['term']}%"),
        )
        item["gold"] = rows[0]["chunk_id"] if rows else None


def run_search(runtime, item: dict, expansions: list[str]) -> dict:
    return runtime.search.hybrid_search(
        item["q"], limit=10, mode="hybrid", expansions=expansions
    )


def main() -> int:
    graph = Graph()
    graph.parse(BUNDLE, format="turtle")
    stats = counts(graph)
    print("term-layer counts:", json.dumps(stats, ensure_ascii=False))

    failures = []
    if stats["untaggedAltLabels"] != 146:
        failures.append("L1-01: legacy untagged altLabels must stay 146")
    if stats["anchorClasses"] != 15:
        failures.append("anchor classes must be 15")
    if stats["taggedAltLabels"] != 18:
        failures.append("tagged altLabels must be 18")
    if stats["activities"] != 4:
        failures.append("prov Activities must be 4")
    if stats["canonicalFor"] != 1 or stats["suppressedSurface"] != 1:
        failures.append("T6 decisions must be exactly 1 canonicalFor + 1 suppressedSurface")
    if failures:
        print("FAIL:", "; ".join(failures))
        return 1

    bundle = load_config(CONFIG, None)
    runtime = assemble(bundle)
    runtime.metadata.open(retry_seconds=10.0)
    try:
        current = runtime.ontology.current()
        tbox_graph = current["graph"]
        resolve_gold(runtime)
        gold_items = [item for item in QUERIES if item.get("gold")]
        print(f"gold coverage: {len(gold_items)}/24")
        if len(gold_items) != 6:
            print("FAIL: gold coverage must be 6/24")
            return 1

        lexicon = TermLexicon.build(runtime.graph, tbox_graph)
        config = runtime.config

        # ---- baseline (both toggles off) ----
        config.context.term_expand = False
        config.search.lexical_expand = False
        baseline_rr = []
        baseline_seed = 0
        baseline_top1 = []
        for item in QUERIES:
            result = run_search(runtime, item, [])
            ranks = [row["chunkId"] for row in result["results"]]
            baseline_top1.append(ranks[0] if ranks else None)
            if item.get("gold"):
                rank = ranks.index(item["gold"]) + 1 if item["gold"] in ranks else 0
                baseline_rr.append(1.0 / rank if rank else 0.0)
            seeds, _ = runtime.context._seeds(item["q"], [], [tbox_graph])
            baseline_seed += 1 if seeds and seeds[0] in item["exp"] else 0

        # ---- candidate (both toggles on) ----
        config.context.term_expand = True
        config.search.lexical_expand = True
        cand_rr = []
        cand_seed = 0
        cand_top1 = []
        expanded_total = 0
        expanded_wrong = 0
        retention = 0
        for index, item in enumerate(QUERIES):
            hits = lexicon.match(item["q"], max_hits=config.context.term_expand_max_hits)
            expansions = lexicon.lexical_queries(hits, limit=10)
            if hits:
                expanded_total += len(hits)
                expanded_wrong += sum(1 for hit in hits if hit.canonical not in item["exp"])
            result = run_search(runtime, item, expansions)
            ranks = [row["chunkId"] for row in result["results"]]
            cand_top1.append(ranks[0] if ranks else None)
            if baseline_top1[index] and baseline_top1[index] in ranks:
                retention += 1
            if item.get("gold"):
                rank = ranks.index(item["gold"]) + 1 if item["gold"] in ranks else 0
                cand_rr.append(1.0 / rank if rank else 0.0)
            seeds = lexicon.canonical_seeds(
                lexicon.match(item["q"], max_hits=config.context.term_expand_max_hits)
            ) or runtime.context._seeds(item["q"], [], [tbox_graph])[0]
            cand_seed += 1 if seeds and seeds[0] in item["exp"] else 0

        # ---- report ----
        def mrr(values: list[float]) -> float:
            return sum(values) / len(values) if values else 0.0

        summary = {
            "queries": len(QUERIES),
            "gold": len(gold_items),
            "mrr10_gold_before": round(mrr(baseline_rr), 4),
            "mrr10_gold_after": round(mrr(cand_rr), 4),
            "seedHit1_before": f"{baseline_seed}/{len(QUERIES)}",
            "seedHit1_after": f"{cand_seed}/{len(QUERIES)}",
            "queriesWithHit10_before": f"{sum(1 for v in baseline_top1 if v)}/{len(QUERIES)}",
            "queriesWithHit10_after": f"{sum(1 for v in cand_top1 if v)}/{len(QUERIES)}",
            "expandedAliases": expanded_total,
            "fpRate": round(expanded_wrong / expanded_total, 4) if expanded_total else 0.0,
            "baselineTop1RetentionAt10": f"{retention}/{len(QUERIES)}",
            "provisional": "gold 6/24 < 18/24; all numbers are Provisional",
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        for item in QUERIES:
            hits = lexicon.match(item["q"], max_hits=5)
            print(
                f"  {item['note']}\t{','.join(hit.canonical.rsplit('#', 1)[-1] for hit in hits) or '-'}"
            )
    finally:
        runtime.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
