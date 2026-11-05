"""S6 acceptance: context assembly, citations/traceability, budget truncation,
graph/search degradation, structured empty results, HTTP route and config fail-fast.
"""

from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path

import httpx

from .assembly import Runtime, assemble
from .config import load_config
from .errors import PlatformError, PortError

RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RISK_PHRASE = "海岸带监测"


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def _overrides(values: dict[str, str]) -> dict[str, str]:
    return {f"PLATFORM__{key.replace('.', '__').upper()}": value for key, value in values.items()}


def _tbox(prefix: str) -> str:
    return f"""
@prefix owl: <{OWL}> .
@prefix rdfs: <{RDFS}> .
@prefix rdf: <{RDF}> .
<urn:platform:smoke:onto:{prefix}> a owl:Ontology .
<urn:platform:smoke:{prefix}:Thing> a owl:Class .
<urn:platform:smoke:{prefix}:Person> a owl:Class ;
    rdfs:subClassOf <urn:platform:smoke:{prefix}:Thing> .
<urn:platform:smoke:{prefix}:Student> a owl:Class ;
    rdfs:subClassOf <urn:platform:smoke:{prefix}:Person> .
"""


def _write(tmp_dir: Path, name: str, text: str) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / name
    path.write_text(text, encoding="utf-8")
    return path


def run_smoke_s6(runtime: Runtime, base_url: str, bad_config: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    config_path = str(runtime.bundle.path)
    tmp_dir = Path(runtime.config.storage.tmp_dir)
    nonce = uuid.uuid4().hex[:8]
    abox = f"urn:platform:test:{uuid.uuid4().hex[:10]}:s6"
    graphless: Runtime | None = None
    searchless: Runtime | None = None

    try:
        runtime.metadata.open(retry_seconds=10.0)
        runtime.metadata.migrate()

        # 1. corpus + index
        text = (
            f"海岸带监测周报{nonce}。本周完成了潮间带沉积物采样与近岸水质连续观测，"
            "岸线侵蚀监测点位新增三处，卫星遥感反演与现场巡检结果完成交叉校验。"
            "监测数据已入库，异常值由人工复核后回填。"
        )
        ingested = runtime.documents.ingest_stream(
            BytesIO(text.encode("utf-8")), f"s6-coast-{nonce}.txt"
        )
        indexed = runtime.search.index_document(ingested["documentId"])
        suite.check(
            "corpus.index",
            ingested["chunkCount"] > 0,
            f"document={ingested['documentId'][:10]} chunks={ingested['chunkCount']} "
            f"embedded={indexed['embedded']}",
        )

        # 2. ontology v1 + individual + materialize (facts source)
        v1 = runtime.ontology.import_source(
            str(_write(tmp_dir, f"s6-{nonce}-v1.ttl", _tbox(nonce))), "1.0.0"
        )
        runtime.ontology.publish(v1["versionId"], acknowledge_breaking=True)
        alice = f"urn:platform:smoke:{nonce}:alice"
        runtime.graph.update(
            f"INSERT DATA {{ GRAPH <{abox}> {{ <{alice}> a <urn:platform:smoke:{nonce}:Student> . }} }}"
        )
        materialized = runtime.reasoning.materialize(abox_graphs=[abox])
        target = f"urn:platform:inferred:{v1['versionId']}"
        suite.check(
            "ontology.materialize",
            materialized["consistent"] is True and materialized["targetGraph"] == target,
            f"version={v1['versionId']} inferred={materialized['inferred']}",
        )

        # 3. chunks are assembled with citations
        pack = runtime.context.resolve({"query": RISK_PHRASE, "topK": 5})
        suite.check(
            "context.chunks",
            len(pack["chunks"]) >= 1 and pack["tokenEstimate"] > 0,
            f"chunks={len(pack['chunks'])} tokens={pack['tokenEstimate']}",
        )
        suite.check(
            "context.citations",
            all(
                item["citationId"] == f"doc:{item['docId']}#{item['chunkId']}"
                for item in pack["chunks"]
            )
            and any(c["kind"] == "chunk" for c in pack["citations"]),
            f"citations={len(pack['citations'])}",
        )

        # 4. every chunk citation resolves to a stored document chunk
        traceable = True
        for chunk in pack["chunks"]:
            rows = runtime.metadata.query(
                "SELECT 1 FROM platform.document_chunk WHERE chunk_id = %s", (chunk["chunkId"],)
            )
            traceable = traceable and bool(rows)
        suite.check(
            "context.traceable_chunks", traceable, f"checked={len(pack['chunks'])}"
        )

        # 5. graph facts with version/graph provenance
        facts = runtime.context.resolve({"query": RISK_PHRASE, "entityHints": [alice], "topK": 3})
        person = f"urn:platform:smoke:{nonce}:Person"
        subject_facts = [f for f in facts["facts"] if f["subject"] == alice]
        suite.check(
            "context.facts",
            any(f["predicate"] == RDF + "type" and f["object"].get("iri") == person for f in subject_facts)
            and all(f["graph"] == target for f in subject_facts),
            f"facts={len(subject_facts)} graph={target}",
        )
        fact_citations = [c for c in facts["citations"] if c["kind"] == "triple"]
        bad_citations = [
            c
            for c in fact_citations
            if not (c["ontologyVersion"] == v1["versionId"] and c["graph"])
        ]
        suite.check(
            "context.fact_citations",
            bool(fact_citations) and not bad_citations,
            f"triple_citations={len(fact_citations)} bad={bad_citations[:1]}",
        )

        # 6. budget truncation
        tight = runtime.context.resolve({"query": RISK_PHRASE, "topK": 5, "tokenBudget": 64})
        suite.check(
            "context.budget_truncated",
            tight["truncated"] is True
            and tight["tokenEstimate"] <= 64
            and tight["omitted"]["chunks"] >= 1,
            f"tokens={tight['tokenEstimate']} omitted={tight['omitted']}",
        )

        # 7. structured empty (lexical, no exact match) is 200-shaped, not an error.
        # S14H-P0: a fixed short token shares trigrams with real corpus rows
        # (measured: 5 hits), so use a per-run random token. Lexical recall may
        # still return trigram-adjacent chunks (e.g. an ingested note that literally
        # contains "zzzqqqxxxjjj"), so the assertion is "no chunk contains this
        # token", not "no chunks at all" — that keeps it deterministic without
        # weakening the no-fabricated-content guarantee.
        empty_token = f"zzz{uuid.uuid4().hex}"
        empty = runtime.context.resolve(
            {"query": empty_token, "strategy": "lexical", "topK": 5}
        )
        token_hits = [
            item for item in empty["chunks"]
            if empty_token in str(item.get("text") or "")
        ]
        suite.check(
            "context.empty",
            token_hits == [] and empty["facts"] == [] and empty["degraded"] is False,
            f"chunks={len(empty['chunks'])} tokenHits={len(token_hits)} "
            f"facts={len(empty['facts'])}",
        )

        # 8. graph outage -> chunks only, degraded but not crashed
        graphless = assemble(
            load_config(config_path, environ=_overrides({"graph.endpoint": "http://127.0.0.1:9"}))
        )
        graphless.metadata.open(retry_seconds=10.0)
        graphless.metadata.migrate()
        degraded_pack = graphless.context.resolve({"query": RISK_PHRASE, "topK": 5})
        suite.check(
            "context.graph_down",
            degraded_pack["degraded"] is True
            and degraded_pack["facts"] == []
            and len(degraded_pack["chunks"]) >= 1
            and "E_GRAPH_UNAVAILABLE" in degraded_pack["warnings"],
            f"degraded={degraded_pack['degraded']} chunks={len(degraded_pack['chunks'])} "
            f"warnings={degraded_pack['warnings']}",
        )

        # 9. search disabled -> facts only, degraded
        searchless = assemble(
            load_config(config_path, environ=_overrides({"search.enabled": "false"}))
        )
        searchless.metadata.open(retry_seconds=10.0)
        searchless.metadata.migrate()
        facts_only = searchless.context.resolve({"query": RISK_PHRASE, "entityHints": [alice]})
        suite.check(
            "context.search_disabled",
            facts_only["degraded"] is True
            and facts_only["chunks"] == []
            and len(facts_only["facts"]) >= 1
            and "E_SEARCH_DISABLED" in facts_only["warnings"],
            f"degraded={facts_only['degraded']} facts={len(facts_only['facts'])} "
            f"warnings={facts_only['warnings']}",
        )

        # 10. request validation
        for name, payload, code in (
            ("context.bad_query", {"query": ""}, "E_CONTEXT_QUERY_EMPTY"),
            ("context.bad_budget", {"query": "x", "tokenBudget": 0}, "E_CONTEXT_BUDGET"),
            ("context.bad_graph", {"query": "x", "graphs": ["bogus"]}, "E_CONTEXT_GRAPH"),
        ):
            try:
                runtime.context.resolve(payload)
                suite.fail(name, f"{code} was not raised")
            except PortError as exc:
                suite.check(name, exc.provider_code == code, f"{exc.code}/{exc.provider_code}")

        # 11. explicit version read-back
        old = runtime.context.resolve({"query": RISK_PHRASE, "ontologyVersion": v1["versionId"]})
        suite.check(
            "context.version",
            old["ontologyVersion"] == v1["versionId"]
            and old["graphs"][0] == runtime.ontology.get(v1["versionId"])["graph"],
            f"version={old['ontologyVersion']} graph={old['graphs'][0]}",
        )

        # 12. HTTP route + status slice
        with httpx.Client(base_url=base, timeout=30.0) as client:
            status = client.get("/status")
            suite.check(
                "http.status",
                status.status_code == 200
                and status.json().get("slice") in {"S6", "S7", "S8", "S9", "S10", "S11", "S12", "S13"}
                and "context" in status.json().get("providers", {}),
                f"http={status.status_code} slice={status.json().get('slice')}",
            )
            response = client.post("/context/resolve", json={"query": RISK_PHRASE})
            suite.check(
                "http.context_resolve",
                response.status_code == 200
                and response.json().get("citations") is not None,
                f"http={response.status_code} chunks={len(response.json().get('chunks', []))}",
            )
            bad = client.post("/context/resolve", json={"query": ""})
            suite.check(
                "http.context_bad_request",
                bad.status_code == 400
                and bad.json().get("error", {}).get("providerCode") == "E_CONTEXT_QUERY_EMPTY",
                f"http={bad.status_code}",
            )

        # 13. bad context budget config fails fast
        try:
            load_config(bad_config)
            suite.fail("config.failfast", "invalid context budget was accepted")
        except PlatformError as exc:
            suite.check(
                "config.failfast",
                exc.code == "E_CONFIG_CONTEXT" and exc.exit_code == 78,
                f"{exc.code} exit={exc.exit_code}",
            )

    finally:
        if graphless is not None:
            graphless.close()
        if searchless is not None:
            searchless.close()
        # SILENT: an aborted run may never have created the abox; a plain DROP
        # would turn cleanup into an Oxigraph HTTP 500 and hide the real error.
        runtime.graph.update(f"DROP SILENT GRAPH <{abox}>")
        runtime.facts.purge_test(abox)

    total = len(suite.results)
    passed = sum(1 for _, ok, _ in suite.results if ok)
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print(f"S6 SMOKE {passed}/{total}")
    return 0 if passed == total else 1
