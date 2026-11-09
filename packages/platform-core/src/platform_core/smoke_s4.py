"""S4 acceptance: rule extraction, approval queue, A-Box write, LLM degradation,
graph outage, bad IRIs, config fail-fast and the HTTP extraction routes.
"""

from __future__ import annotations

import hashlib
import uuid
from io import BytesIO
from typing import Any

import httpx

from .assembly import Runtime, assemble
from .config import load_config
from .errors import EXIT_INTERNAL, PlatformError, PortError
from .extraction import ABOX_GRAPH

CORPUS_NAME = "s4-extraction.txt"
CORPUS_BASE = "北京位于中国。上海位于中国。北京是中国的首都。广州位于中国。"
# The nonce must land in the *object* group so case 6 can pick this run's candidate.
NONCE_SENTENCE = "测试点位于库{nonce}。"


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


def _error_code(response: httpx.Response) -> str:
    try:
        return response.json()["error"]["providerCode"]
    except Exception:  # noqa: BLE001
        return ""


def run_smoke_s4(runtime: Runtime, base_url: str, bad_config: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    test_graph = f"urn:platform:test:{uuid.uuid4().hex[:10]}:s4"
    config_path = str(runtime.bundle.path)
    degraded_runtime: Runtime | None = None
    graphless_runtime: Runtime | None = None
    unconfigured_runtime: Runtime | None = None

    try:
        runtime.metadata.open(retry_seconds=10.0)
        runtime.metadata.migrate()

        # 1. corpus ingest (per-run nonce keeps approvals/rejections repeatable)
        nonce = uuid.uuid4().hex[:8]
        corpus_text = CORPUS_BASE + NONCE_SENTENCE.format(nonce=nonce)
        ingested = runtime.documents.ingest_stream(
            BytesIO(corpus_text.encode("utf-8")), CORPUS_NAME
        )
        document_id = ingested["documentId"]
        suite.check(
            "corpus.ingest",
            ingested["chunkCount"] > 0,
            f"document={document_id[:8]} chunks={ingested['chunkCount']} nonce={nonce}",
        )

        # 2. rule extraction creates pending candidates
        before_total = runtime.extraction.counts()["total"]
        rules = runtime.extraction.extract_document(document_id, mode="rules")
        suite.check(
            "extract.rules",
            rules["inserted"] >= 5 and rules["rulesMatched"] >= 5,
            f"matched={rules['rulesMatched']} inserted={rules['inserted']} skipped={rules['skipped']}",
        )
        pending = [
            item
            for item in runtime.extraction.list_candidates(
                state="pending", document_id=document_id
            )
            if item["subject"].startswith("urn:")
        ]
        suite.check(
            "extract.pending",
            len(pending) >= 5 and all(item["state"] == "pending" for item in pending),
            f"pending={len(pending)}",
        )

        # 3. idempotent re-extraction
        again = runtime.extraction.extract_document(document_id, mode="rules")
        after_total = runtime.extraction.counts()["total"]
        suite.check(
            "extract.idempotent",
            again["inserted"] == 0 and after_total == before_total + rules["inserted"],
            f"inserted={again['inserted']} total={before_total + rules['inserted']}->{after_total}",
        )

        # 4. llm mode with an unconfigured client must not pretend to work
        #    (ambient env may configure a provider, so override it away explicitly)
        unconfigured_bundle = load_config(
            config_path,
            environ=_overrides({"llm.provider": "disabled"}),
        )
        unconfigured_runtime = assemble(unconfigured_bundle)
        unconfigured_runtime.metadata.open(retry_seconds=10.0)
        try:
            unconfigured_runtime.extraction.extract_document(document_id, mode="llm")
            suite.fail("extract.llm_unconfigured", "llm mode succeeded without config")
        except PortError as exc:
            suite.check(
                "extract.llm_unconfigured",
                exc.code == "Unsupported" and exc.provider_code == "E_LLM_NOT_CONFIGURED",
                f"{exc.code}/{exc.provider_code}",
            )

        # 5. auto mode with an unreachable LLM -> rules still apply, degraded
        degraded_bundle = load_config(
            config_path,
            environ=_overrides(
                {
                    "llm.base_url": "http://127.0.0.1:9/v1",
                    "llm.model": "s4-test-model",
                    "llm.timeout_ms": "2000",
                    "llm.api_key_env": "S4_EMPTY_KEY",
                }
            ),
        )
        degraded_runtime = assemble(degraded_bundle)
        degraded_runtime.metadata.open(retry_seconds=10.0)
        lowered = degraded_runtime.extraction.extract_document(document_id, mode="auto")
        suite.check(
            "extract.auto_degraded",
            lowered["degraded"] is True
            and "E_LLM_UNAVAILABLE" in lowered["reasons"]
            and lowered["rulesMatched"] >= 2,
            f"degraded={lowered['degraded']} reasons={lowered['reasons']} "
            f"matched={lowered['rulesMatched']}",
        )
        try:
            degraded_runtime.extraction.extract_document(document_id, mode="llm")
            suite.fail("extract.llm_unreachable", "llm mode succeeded against a dead endpoint")
        except PortError as exc:
            suite.check(
                "extract.llm_unreachable",
                exc.code == "Unavailable" and exc.provider_code == "E_LLM_UNAVAILABLE",
                f"{exc.code}/{exc.provider_code}",
            )

        # 6. approval writes exactly one triple to the A-Box graph
        candidate = next((item for item in pending if nonce in item["object"]), None)
        if candidate is None:
            suite.fail("approve.graph_write", f"nonce candidate not found (nonce={nonce})")
            raise PlatformError(
                code="E_SMOKE_NONCE",
                detail=f"nonce candidate not found in pending list (nonce={nonce})",
                stage="smoke-s4",
                exit_code=EXIT_INTERNAL,
            )
        before_triples = runtime.graph.count_graph(test_graph)
        approved = runtime.extraction.approve(candidate["candidateId"], graph=test_graph)
        after_triples = runtime.graph.count_graph(test_graph)
        suite.check(
            "approve.graph_write",
            approved["state"] == "approved"
            and approved["graph"] == test_graph
            and after_triples == before_triples + 1,
            f"triples={before_triples}->{after_triples} graph={approved['graph']}",
        )

        # 7. queue states
        still_pending = [
            item["candidateId"]
            for item in runtime.extraction.list_candidates(state="pending", document_id=document_id)
        ]
        approved_list = runtime.extraction.list_candidates(state="approved", document_id=document_id)
        suite.check(
            "candidates.state_filter",
            candidate["candidateId"] not in still_pending
            and any(item["candidateId"] == candidate["candidateId"] for item in approved_list),
            f"pending={len(still_pending)} approved={len(approved_list)}",
        )

        # 8. double approval conflicts
        try:
            runtime.extraction.approve(candidate["candidateId"])
            suite.fail("approve.conflict", "second approval succeeded")
        except PortError as exc:
            suite.check(
                "approve.conflict",
                exc.code == "Conflict" and exc.provider_code == "E_CANDIDATE_NOT_PENDING",
                f"{exc.code}/{exc.provider_code}",
            )

        # 9. rejection never writes the graph
        rejected_target = [
            item for item in pending if item["candidateId"] != candidate["candidateId"]
        ][0]
        graph_before = runtime.graph.count_graph(test_graph)
        runtime.extraction.reject(rejected_target["candidateId"], reason="acceptance")
        suite.check(
            "reject.no_graph_write",
            runtime.graph.count_graph(test_graph) == graph_before
            and runtime.extraction.list_candidates(state="rejected", document_id=document_id),
            f"triples={graph_before}",
        )

        # 10. invalid IRI stays pending
        bad_id = "cand-" + uuid.uuid4().hex
        bad_dedupe = hashlib.sha256(bad_id.encode("utf-8")).hexdigest()
        runtime.metadata.execute(
            """
            INSERT INTO platform.extraction_candidate (
              candidate_id, document_id, chunk_id, extractor, extractor_version,
              subject_iri, predicate_iri, object_kind, object_value, confidence,
              state, dedupe_key, evidence
            ) VALUES (%s, %s, %s, 'rules', 's4-test', 'bad iri', 'urn:platform:rel:test',
                      'iri', 'urn:platform:entity:test', 0.5, 'pending', %s, '{}'::jsonb)
            """,
            (bad_id, document_id, pending[0]["chunkId"], bad_dedupe),
        )
        try:
            runtime.extraction.approve(bad_id)
            suite.fail("approve.bad_iri", "invalid IRI was written")
        except PortError as exc:
            state = runtime.extraction.list_candidates(document_id=document_id)
            row = [item for item in state if item["candidateId"] == bad_id]
            suite.check(
                "approve.bad_iri",
                exc.code == "InvalidArgument"
                and exc.provider_code == "E_CANDIDATE_BAD_IRI"
                and bool(row)
                and row[0]["state"] == "pending",
                f"{exc.code}/{exc.provider_code} state={row[0]['state'] if row else None}",
            )
        runtime.metadata.execute(
            "DELETE FROM platform.extraction_candidate WHERE candidate_id = %s", (bad_id,)
        )

        # 11. graph outage leaves the candidate pending
        graphless_bundle = load_config(
            config_path,
            environ=_overrides(
                {"graph.endpoint": "http://127.0.0.1:9", "graph.timeout_ms": "2000"}
            ),
        )
        graphless_runtime = assemble(graphless_bundle)
        graphless_runtime.metadata.open(retry_seconds=10.0)
        extra = runtime.extraction.extract_document(document_id, mode="rules")
        graph_pending = [
            item
            for item in graphless_runtime.extraction.list_candidates(
                state="pending", document_id=document_id
            )
            if item["subject"].startswith("urn:")
        ]
        try:
            graphless_runtime.extraction.approve(graph_pending[0]["candidateId"])
            suite.fail("approve.graph_down", "approval succeeded with the graph down")
        except PortError as exc:
            state_after = graphless_runtime.extraction.list_candidates(document_id=document_id)
            row = [item for item in state_after if item["candidateId"] == graph_pending[0]["candidateId"]]
            suite.check(
                "approve.graph_down",
                exc.code in ("Unavailable", "DeadlineExceeded")
                and bool(row)
                and row[0]["state"] == "pending",
                f"{exc.code}/{exc.provider_code} state={row[0]['state'] if row else None}",
            )
        suite.check("extract.extra", extra["inserted"] >= 0, f"inserted={extra['inserted']}")

        # 12/13. not-found paths
        try:
            runtime.extraction.approve("cand-missing")
            suite.fail("approve.not_found", "missing candidate approved")
        except PortError as exc:
            suite.check(
                "approve.not_found",
                exc.code == "NotFound" and exc.provider_code == "E_CANDIDATE_NOT_FOUND",
                f"{exc.code}/{exc.provider_code}",
            )
        try:
            runtime.extraction.extract_document("doc-missing", mode="rules")
            suite.fail("extract.not_found", "missing document extracted")
        except PortError as exc:
            suite.check(
                "extract.not_found",
                exc.code == "NotFound" and exc.provider_code == "E_DOC_NOT_FOUND",
                f"{exc.code}/{exc.provider_code}",
            )

        # 14/15. HTTP routes
        with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
            extract_response = client.post(
                f"{base}/documents/{document_id}/extract", json={"mode": "rules"}
            )
            suite.check(
                "http.extract",
                extract_response.status_code == 200
                and extract_response.json().get("documentId") == document_id,
                f"http={extract_response.status_code} inserted={extract_response.json().get('inserted')}",
            )
            candidates_response = client.get(f"{base}/candidates", params={"state": "pending"})
            suite.check(
                "http.candidates",
                candidates_response.status_code == 200
                and isinstance(candidates_response.json().get("candidates"), list),
                f"http={candidates_response.status_code} count={candidates_response.json().get('count')}",
            )
            target = next(
                item
                for item in candidates_response.json()["candidates"]
                if item["subject"].startswith("urn:")
            )
            approve_response = client.post(
                f"{base}/candidates/{target['candidateId']}/approve",
                params={"graph": test_graph},
            )
            suite.check(
                "http.approve",
                approve_response.status_code == 200
                and approve_response.json().get("state") == "approved",
                f"http={approve_response.status_code} state={approve_response.json().get('state')}",
            )
            bad_mode = client.post(
                f"{base}/documents/{document_id}/extract", json={"mode": "bogus"}
            )
            suite.check(
                "http.bad_mode",
                bad_mode.status_code == 400 and _error_code(bad_mode) == "E_EXTRACT_MODE",
                f"http={bad_mode.status_code} code={_error_code(bad_mode)}",
            )
            status = client.get(f"{base}/status")
            suite.check(
                "http.status",
                status.status_code == 200
                and status.json().get("slice") in {"S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12", "S13"}
                and status.json().get("extraction", {}).get("total", -1) >= 0,
                f"http={status.status_code} slice={status.json().get('slice')} "
                f"total={status.json().get('extraction', {}).get('total')}",
            )

        # 16. bad rule config fails fast
        try:
            load_config(bad_config)
            suite.fail("config.failfast", "invalid extraction rule was accepted")
        except PlatformError as exc:
            suite.check(
                "config.failfast",
                exc.code == "E_CONFIG_EXTRACTION_RULE" and exc.exit_code == 78,
                f"{exc.code} exit={exc.exit_code}",
            )

    finally:
        if unconfigured_runtime is not None:
            unconfigured_runtime.close()
        if degraded_runtime is not None:
            degraded_runtime.close()
        if graphless_runtime is not None:
            graphless_runtime.close()
        try:
            runtime.graph.update(f"DROP GRAPH <{test_graph}>")
        except PortError:
            pass  # graph never created -> nothing to drop; must not mask the real failure
        runtime.facts.purge_test(test_graph)

    total = len(suite.results)
    passed = sum(1 for _, ok, _ in suite.results if ok)
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print(f"S4 SMOKE {passed}/{total}")
    return 0 if passed == total else 1
