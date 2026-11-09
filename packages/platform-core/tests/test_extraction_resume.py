"""S14H-04: extraction batch checkpoint / resume check.

Needs a live platform DB, so it runs inside the API container:

    platform-check?  no - use:
    docker compose exec -T platform python /app/tests/test_extraction_resume.py

It uses a stub LLM (no network, no GPU) and a synthetic corpus, so every
number here is a test fixture, not a business result.
"""

from __future__ import annotations

import re
import sys
import uuid
from io import BytesIO

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError

CONFIG_PATH = sys.argv[1] if len(sys.argv) > 1 else "/data/platform.yaml"
OVERRIDES = {
    "documents.chunk_max_chars": "200",
    "documents.chunk_overlap_chars": "0",
    # Force one chunk per LLM batch so several batches (and checkpoints) exist.
    "extraction.max_chunks": "1",
}
CORPUS = (
    "{nonce} " + "".join(
        f"第{i}条记录：单位甲位于城市{i}，金额为{i}万元，编号 RESUME-{i:03d}。\n"
        for i in range(1, 19)
    )
)


class StubLlm:
    """Deterministic LLM stand-in that can fail on a chosen call number."""

    def __init__(self, fail_on_call: int | None = None) -> None:
        self.calls = 0
        self.fail_on_call = fail_on_call

    def configured(self) -> bool:
        return True

    def complete_json(self, system: str, user: str) -> dict:
        self.calls += 1
        if self.fail_on_call is not None and self.calls >= self.fail_on_call:
            raise PortError(
                code="Unavailable",
                message="stub llm is down",
                provider="stub",
                provider_code="E_LLM_UNAVAILABLE",
            )
        chunk_numbers = user.count("[chunk ")
        # Stable per-chunk tag so a cached batch and a re-run batch produce the
        # same triple (otherwise dedupe across resume would look broken).
        found = re.search(r"RESUME-\d{3}", user)
        tag = found.group(0) if found else f"B{self.calls}"
        triples = [
            {
                # Same triple in every batch: must be merged away, not re-created.
                "chunk": 0,
                "subject": "urn:platform:entity:resume-shared",
                "predicate": "urn:platform:rel:locatedIn",
                "object": "urn:platform:entity:resume-city",
                "objectKind": "iri",
            },
            {
                # Unique per chunk, so each batch contributes one new candidate.
                "chunk": max(0, chunk_numbers - 1),
                "subject": f"urn:platform:entity:resume-{tag}",
                "predicate": "urn:platform:rel:hasCode",
                "object": f"RESUME-{tag}",
                "objectKind": "literal",
            },
        ]
        return {"triples": triples}


def main() -> int:
    bundle = load_config(CONFIG_PATH, environ={
        f"PLATFORM__{key.replace('.', '__').upper()}": value for key, value in OVERRIDES.items()
    })
    runtime = assemble(bundle)
    runtime.metadata.open(retry_seconds=10.0)
    runtime.metadata.migrate()

    nonce = uuid.uuid4().hex[:8]
    ingested = runtime.documents.ingest_stream(
        BytesIO(CORPUS.format(nonce=nonce).encode("utf-8")), f"s14h04-resume-{nonce}.txt"
    )
    document_id = ingested["documentId"]
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))
        print(f"{'PASS' if ok else 'FAIL'} {name} {detail}")

    batches = runtime.extraction.llm_batch_size(ingested["chunkCount"])
    expected_batches = -(-ingested["chunkCount"] // batches)
    print(f"document={document_id[:8]} chunks={ingested['chunkCount']} batchSize={batches} "
          f"batches={expected_batches}")

    # ---- interrupted run: 2 completed batches, 1 failed -----------------
    failing = StubLlm(fail_on_call=3)
    runtime.extraction._llm = failing
    try:
        runtime.extraction.extract_document(document_id, mode="llm")
        check("interrupt.raises", False, "extraction did not fail")
    except PortError as exc:
        check("interrupt.raises", exc.provider_code == "E_LLM_UNAVAILABLE",
              f"calls={failing.calls} code={exc.provider_code}")

    rows = runtime.metadata.query(
        """
        SELECT status, COUNT(*) AS n FROM platform.extraction_progress
         WHERE document_id = %s GROUP BY status
        """, (document_id,))
    state = {row["status"]: int(row["n"]) for row in rows}
    check(
        "interrupt.checkpoint_written",
        state.get("completed", 0) >= 2 and state.get("failed", 0) == 1,
        f"completed={state.get('completed', 0)} failed={state.get('failed', 0)}",
    )

    # ---- resumed run: skips stored batches, retries the failed one ------
    def candidate_count() -> int:
        rows = runtime.metadata.query(
            "SELECT COUNT(*) AS n FROM platform.extraction_candidate WHERE document_id = %s",
            (document_id,))
        return int(rows[0]["n"]) if rows else -1

    before_candidates = candidate_count()
    print(f"candidates_before_resume={before_candidates}")
    check("interrupt.no_partial_insert", before_candidates == 0,
          f"candidates={before_candidates}")

    resumed = StubLlm()
    runtime.extraction._llm = resumed
    result = runtime.extraction.extract_document(document_id, mode="llm")
    llm = result["llm"] or {}
    check(
        "resume.skips_completed_batches",
        llm.get("resumedBatches", 0) >= 2 and resumed.calls == expected_batches - 2,
        f"resumedBatches={llm.get('resumedBatches')} llmCalls={resumed.calls} "
        f"expectedCalls={expected_batches - 2}",
    )
    check(
        "resume.merge_dedupe",
        llm.get("candidates") == expected_batches + 1
        and llm.get("dedupDropped") == expected_batches - 1,
        f"candidates={llm.get('candidates')} raw={llm.get('candidatesRaw')} "
        f"dedupDropped={llm.get('dedupDropped')}",
    )
    check("resume.inserted", result["inserted"] == llm.get("candidates"),
          f"inserted={result['inserted']} candidates={llm.get('candidates')} "
          f"rows={candidate_count()}")

    rows = runtime.metadata.query(
        "SELECT COUNT(*) AS n FROM platform.extraction_progress WHERE document_id = %s",
        (document_id,))
    left = int(rows[0]["n"]) if rows else -1
    check("resume.checkpoint_cleared", left == 0, f"remainingRows={left}")

    failed = [name for name, ok, _ in checks if not ok]
    print(f"SUMMARY passed={len(checks) - len(failed)} failed={len(failed)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
