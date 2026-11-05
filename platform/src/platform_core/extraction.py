"""ExtractionService (S4): rule regexes + optional LLM -> candidates -> approval -> A-Box.

Boundary (D18): this module orchestrates. Rule matching uses Python `re` on
configuration-provided patterns; triple serialization uses rdflib literals/IRIs;
the graph write goes through the S0/S1 GraphStore. No probabilistic entity
resolution, no self-written extraction algorithm.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from psycopg.types.json import Jsonb
from rdflib import Literal, URIRef

from .adapters.graph_oxigraph import IRI_RE, OxigraphHttpStore
from .adapters.llm_openai import LlmClient
from .adapters.metadata_pg import MetadataPg
from .config import ExtractionConfig, ExtractionRule
from .errors import PortError
from .ports import Manifest

log = logging.getLogger(__name__)

ABOX_GRAPH = "urn:platform:graph:abox:main"
LOCATED_IN = "urn:platform:rel:locatedIn"
HAS_LOCATION_LABEL = "urn:platform:rel:hasLocationLabel"
LOCATION_FALLBACK_CONFIDENCE = 0.4
RULES_VERSION = "s4-rules.1"
LLM_VERSION = "s4-llm.1"
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")

SYSTEM_PROMPT = (
    "You are a knowledge extraction engine. Input is a list of numbered text "
    "chunks, each introduced by [chunk <n>]. Output one JSON object only. "
    "Schema: {\"triples\":[{\"chunk\":<n>,\"subject\":\"<IRI>\",\"predicate\":\"<IRI>\","
    "\"object\":\"<IRI or literal>\",\"objectKind\":\"iri|literal\"}]}. "
    "Set chunk to the number of the chunk the fact came from. "
    "Write subjects and IRI objects as urn:platform:entity:<name without spaces> "
    "and predicates as urn:platform:rel:<lowerCamelCase>. Set objectKind=literal "
    "for values such as dates, amounts, counts and names, with the plain string "
    "in object. Extract every fact the text states. Never invent facts."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iri(value: str) -> bool:
    return bool(value) and bool(IRI_RE.match(value)) and bool(SCHEME_RE.match(value))


class ExtractionService:
    port = "ExtractionPipeline"

    def __init__(
        self,
        config: ExtractionConfig,
        metadata: MetadataPg,
        graph: OxigraphHttpStore,
        llm: LlmClient,
        facts: Any | None = None,
    ) -> None:
        self._config = config
        self._meta = metadata
        self._graph = graph
        self._llm = llm
        self._facts = facts
        self._rules: list[tuple[ExtractionRule, re.Pattern[str]]] = [
            (rule, re.compile(rule.pattern)) for rule in config.rules
        ]

    def manifest(self) -> Manifest:
        return Manifest(
            provider="rules+llm",
            port=self.port,
            provider_version="s4.1",
            capabilities=["extract.rules", "extract.llm", "candidate.approve"],
            limits={
                "rules": len(self._rules),
                "llm_max_chunks": self._config.llm_max_chunks,
                "llm_max_chunks_override": self._config.max_chunks,
                "llm_batch_rule": "max(llm_max_chunks, min(200, ceil(chunks/10)))",
                "abox_graph": ABOX_GRAPH,
            },
            notes={
                "slice": "S4",
                "llm_configured": self._llm.configured(),
                "write_policy": "approval-gated, pending -> graph",
            },
        )

    # ---- extraction ------------------------------------------------------

    def extract_document(
        self, document_id: str, mode: Literal["auto", "rules", "llm"] = "auto"
    ) -> dict[str, Any]:
        if mode not in ("auto", "rules", "llm"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported extraction mode: {mode}",
                provider="platform",
                provider_code="E_EXTRACT_MODE",
                details={"mode": mode, "allowed": ["auto", "rules", "llm"]},
            )
        if not self._config.enabled:
            raise PortError(
                code="Unsupported",
                message="extraction.enabled=false: extraction is disabled",
                provider="platform",
                provider_code="E_EXTRACTION_DISABLED",
                details={"key": "extraction.enabled"},
            )
        self._document(document_id)
        chunks = self._meta.query(
            """
            SELECT chunk_id, seq, text
              FROM platform.document_chunk
             WHERE document_id = %s
             ORDER BY seq
            """,
            (document_id,),
        )

        reasons: list[str] = []
        rules_matched = 0
        inserted = 0
        skipped = 0
        candidates: list[dict[str, Any]] = []

        if mode in ("auto", "rules"):
            for rule, pattern in self._rules:
                for chunk in chunks:
                    for match in pattern.finditer(chunk["text"]):
                        rules_matched += 1
                        candidate = self._rule_candidate(rule, match, document_id, chunk)
                        if candidate is None:
                            skipped += 1
                            continue
                        candidates.append(candidate)

        llm_stats: dict[str, Any] | None = None
        if mode == "llm" or (mode == "auto" and self._llm.configured()):
            try:
                produced, llm_stats = self._llm_candidates(document_id, chunks)
                candidates.extend(produced)
            except PortError as exc:
                if mode == "llm":
                    raise
                reasons.append(exc.provider_code or exc.code)
                log.warning(
                    "extraction degraded: llm unavailable",
                    extra={"event": {"event": "extract_degraded", "code": exc.provider_code}},
                )

        for candidate in candidates:
            if self._insert(candidate):
                inserted += 1

        # Only a completed document drops its batch checkpoints; an interrupted
        # or degraded run keeps them so the next call resumes where it stopped.
        if llm_stats is not None:
            self._clear_progress(document_id, llm_stats["batchSize"])

        result = {
            "documentId": document_id,
            "mode": mode,
            "chunks": len(chunks),
            "rulesMatched": rules_matched,
            "inserted": inserted,
            "skipped": skipped,
            "degraded": bool(reasons),
            "reasons": reasons,
            "llm": llm_stats,
        }
        log.info("extraction finished", extra={"event": {"event": "extract", **result}})
        return result

    def _rule_candidate(
        self,
        rule: ExtractionRule,
        match: re.Match[str],
        document_id: str,
        chunk: dict[str, Any],
    ) -> dict[str, Any] | None:
        groups = {key: (value or "").strip() for key, value in match.groupdict().items()}
        if not groups.get("subject") or not groups.get("object"):
            return None
        try:
            subject = rule.subject.format(**groups)
            obj = rule.object.format(**groups)
        except (KeyError, IndexError):
            return None
        if not _iri(subject) or not _iri(rule.predicate):
            return None
        predicate = rule.predicate
        kind = "iri"
        confidence = 0.9
        if not _iri(obj):
            # locatedIn must stay entity-level (SHACL: sh:nodeKind sh:IRI, OQ-35).
            # An unresolved place mention becomes a weak string annotation and
            # still goes through the human approval queue.
            if predicate != LOCATED_IN:
                return None
            predicate = HAS_LOCATION_LABEL
            kind = "literal"
            confidence = LOCATION_FALLBACK_CONFIDENCE
            obj = groups["object"]
        return {
            "documentId": document_id,
            "chunkId": chunk["chunk_id"],
            "extractor": "rules",
            "extractorVersion": RULES_VERSION,
            "subject": subject,
            "predicate": predicate,
            "objectKind": kind,
            "objectValue": obj,
            "confidence": confidence,
            "evidence": {
                "rule": rule.name,
                "chunkSeq": chunk["seq"],
                "match": match.group(0)[:200],
            },
        }

    def llm_batch_size(self, chunk_count: int) -> int:
        """Adaptive LLM batch size: explicit override wins, else scale with size.

        ``clamp(ceil(chunks/10), 20, 200)`` keeps small documents at one or two
        calls while large documents are processed in batches instead of silently
        dropping everything after the first 20 chunks.
        """
        if self._config.max_chunks is not None:
            return self._config.max_chunks
        floor = max(self._config.llm_max_chunks, 20)
        return max(min(floor, 200), min(200, math.ceil(chunk_count / 10)))

    def _llm_candidates(
        self, document_id: str, chunks: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        started = time.monotonic()
        total = len(chunks)
        cap = self.llm_batch_size(total)
        produced: list[dict[str, Any]] = []
        batches = 0
        reused = 0
        cached = self._load_progress(document_id, cap)
        for index, start in enumerate(range(0, total, cap)):
            batches += 1
            end = min(start + cap, total)
            if index in cached:
                # Resume: this batch finished in an earlier run; its candidates
                # were persisted with the checkpoint, so no LLM call is needed.
                produced.extend(cached[index])
                reused += 1
                continue
            try:
                items = self._llm_batch(document_id, chunks[start:end])
            except PortError as exc:
                self._save_progress(
                    document_id, cap, index, start, end, [],
                    failure_code=exc.provider_code or exc.code,
                )
                raise
            self._save_progress(document_id, cap, index, start, end, items)
            produced.extend(items)

        # Cross-batch merge: one triple may be stated in several chunks; keep the
        # first occurrence (it carries its own chunk evidence) and drop repeats.
        merged: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for item in produced:
            key = (item["subject"], item["predicate"], item["objectValue"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)

        stats = {
            "configured": self._llm.configured(),
            "chunks": total,
            "batchSize": cap,
            "batches": batches,
            "resumedBatches": reused,
            "candidatesRaw": len(produced),
            "candidates": len(merged),
            "dedupDropped": len(produced) - len(merged),
            "elapsedMs": int((time.monotonic() - started) * 1000),
        }
        log.info("llm extraction batches finished", extra={"event": {"event": "extract_llm", **stats}})
        return merged, stats

    def _llm_batch(
        self, document_id: str, batch: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        lines = [f"[chunk {index}]\n{chunk['text'][:2000]}" for index, chunk in enumerate(batch)]
        payload = self._llm.complete_json(
            SYSTEM_PROMPT,
            "Extract facts from these numbered chunks.\n\n" + "\n\n".join(lines),
        )
        triples = payload.get("triples")
        if not isinstance(triples, list):
            raise PortError(
                code="DataLoss",
                message="llm JSON does not contain a triples array",
                provider="openai-compatible",
                provider_code="E_LLM_BAD_RESPONSE",
            )
        produced: list[dict[str, Any]] = []
        for item in triples[: self._config.max_candidates_per_chunk * len(batch)]:
            if not isinstance(item, dict):
                continue
            chunk = self._batch_chunk(batch, item.get("chunk"))
            subject = str(item.get("subject", ""))
            predicate = str(item.get("predicate", ""))
            value = str(item.get("object", ""))
            kind = str(item.get("objectKind", "iri"))
            if kind not in ("iri", "literal"):
                continue
            if not _iri(subject) or not _iri(predicate):
                continue
            if kind == "iri" and not _iri(value):
                continue
            if kind == "literal" and not value:
                continue
            confidence = 0.55
            if predicate == LOCATED_IN and kind == "literal":
                # Keep the strong relation IRI-only; the raw label is a weak
                # annotation awaiting manual resolution (OQ-35).
                predicate = HAS_LOCATION_LABEL
                confidence = LOCATION_FALLBACK_CONFIDENCE
            produced.append(
                {
                    "documentId": document_id,
                    "chunkId": chunk["chunk_id"],
                    "extractor": "llm",
                    "extractorVersion": LLM_VERSION,
                    "subject": subject,
                    "predicate": predicate,
                    "objectKind": kind,
                    "objectValue": value,
                    "confidence": confidence,
                    "evidence": {"chunkSeq": chunk["seq"], "source": "llm"},
                }
            )
        return produced

    @staticmethod
    def _batch_chunk(batch: list[dict[str, Any]], raw_index: Any) -> dict[str, Any]:
        try:
            index = int(raw_index)
        except (TypeError, ValueError):
            index = 0
        if index < 0 or index >= len(batch):
            index = 0
        return batch[index]

    def _insert(self, candidate: dict[str, Any]) -> bool:
        dedupe = hashlib.sha256(
            "|".join(
                [
                    candidate["documentId"],
                    candidate["chunkId"],
                    candidate["extractorVersion"],
                    candidate["subject"],
                    candidate["predicate"],
                    candidate["objectKind"],
                    candidate["objectValue"],
                ]
            ).encode("utf-8")
        ).hexdigest()
        rowcount = self._meta.execute(
            """
            INSERT INTO platform.extraction_candidate (
              candidate_id, document_id, chunk_id, extractor, extractor_version,
              subject_iri, predicate_iri, object_kind, object_value, confidence,
              state, dedupe_key, evidence
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            ON CONFLICT (dedupe_key) DO NOTHING
            """,
            (
                "cand-" + uuid.uuid4().hex,
                candidate["documentId"],
                candidate["chunkId"],
                candidate["extractor"],
                candidate["extractorVersion"],
                candidate["subject"],
                candidate["predicate"],
                candidate["objectKind"],
                candidate["objectValue"],
                candidate["confidence"],
                dedupe,
                Jsonb(candidate["evidence"]),
            ),
        )
        return rowcount > 0

    # ---- candidate queue -------------------------------------------------

    def list_candidates(
        self,
        state: str | None = None,
        document_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if state is not None and state not in ("pending", "approved", "rejected"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported candidate state: {state}",
                provider="platform",
                provider_code="E_CANDIDATE_STATE",
                details={"state": state},
            )
        clauses: list[str] = []
        params: list[Any] = []
        if state:
            clauses.append("state = %s")
            params.append(state)
        if document_id:
            clauses.append("document_id = %s")
            params.append(document_id)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(max(1, min(limit, 500)))
        rows = self._meta.query(
            f"""
            SELECT candidate_id, document_id, chunk_id, extractor, subject_iri,
                   predicate_iri, object_kind, object_value, confidence, state,
                   graph_iri, created_at, decided_at, reject_reason
              FROM platform.extraction_candidate
              {where}
             ORDER BY created_at DESC, candidate_id
             LIMIT %s
            """,
            tuple(params),
        )
        return [self._candidate(row) for row in rows]

    def approve(self, candidate_id: str, graph: str | None = None,
                actor: str = "api") -> dict[str, Any]:
        self._require_pending(candidate_id)
        candidate = self._candidate_row(candidate_id)
        target = graph or ABOX_GRAPH
        if not _iri(target):
            raise PortError(
                code="InvalidArgument",
                message="target graph is not a valid IRI",
                provider="platform",
                provider_code="E_CANDIDATE_BAD_GRAPH",
                details={"graph": target},
            )
        subject = candidate["subject_iri"]
        predicate = candidate["predicate_iri"]
        value = candidate["object_value"]
        if not _iri(subject) or not _iri(predicate):
            raise PortError(
                code="InvalidArgument",
                message="candidate subject/predicate is not a valid IRI",
                provider="platform",
                provider_code="E_CANDIDATE_BAD_IRI",
                details={"candidateId": candidate_id},
            )
        if candidate["object_kind"] == "iri":
            if not _iri(value):
                raise PortError(
                    code="InvalidArgument",
                    message="candidate object is not a valid IRI",
                    provider="platform",
                    provider_code="E_CANDIDATE_BAD_IRI",
                    details={"candidateId": candidate_id},
                )
            obj_term = URIRef(value).n3()
        else:
            obj_term = Literal(value).n3()

        triple = f"{URIRef(subject).n3()} {URIRef(predicate).n3()} {obj_term} ."
        self._graph.update(f"INSERT DATA {{ GRAPH <{target}> {{ {triple} }} }}")

        with self._meta.tx() as tx:
            updated = tx.execute(
                """
                UPDATE platform.extraction_candidate
                   SET state = 'approved', decided_at = now(), graph_iri = %s
                 WHERE candidate_id = %s AND state = 'pending'
                """,
                (target, candidate_id),
            )
        if updated == 0:
            raise PortError(
                code="Conflict",
                message=f"candidate {candidate_id} is no longer pending",
                provider="postgres",
                provider_code="E_CANDIDATE_NOT_PENDING",
            )
        fact: dict[str, Any] | None = None
        if self._facts is not None:
            fact = self._facts.record(
                subject=subject,
                predicate=predicate,
                object_value=value,
                object_kind=candidate["object_kind"],
                graph=target,
                source_kind="extraction",
                source_document_id=candidate["document_id"],
                candidate_id=candidate_id,
                actor=actor,
            )
        log.info(
            "candidate approved",
            extra={"event": {"event": "candidate_approved", "candidateId": candidate_id}},
        )
        result = {
            "candidateId": candidate_id,
            "state": "approved",
            "graph": target,
            "triples": 1,
            "factId": fact["factId"] if fact else None,
            "conflict": bool(fact and fact.get("conflict")),
        }
        if fact and fact.get("conflictValues"):
            result["conflictValues"] = fact["conflictValues"]
        return result

    def reject(self, candidate_id: str, reason: str | None = None) -> dict[str, Any]:
        self._require_pending(candidate_id)
        with self._meta.tx() as tx:
            updated = tx.execute(
                """
                UPDATE platform.extraction_candidate
                   SET state = 'rejected', decided_at = now(), reject_reason = %s
                 WHERE candidate_id = %s AND state = 'pending'
                """,
                (reason, candidate_id),
            )
        if updated == 0:
            raise PortError(
                code="Conflict",
                message=f"candidate {candidate_id} is no longer pending",
                provider="postgres",
                provider_code="E_CANDIDATE_NOT_PENDING",
            )
        return {"candidateId": candidate_id, "state": "rejected"}

    def counts(self) -> dict[str, Any]:
        rows = self._meta.query(
            """
            SELECT state, COUNT(*) AS n
              FROM platform.extraction_candidate
             GROUP BY state
            """
        )
        result = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
        for row in rows:
            result[row["state"]] = int(row["n"])
            result["total"] += int(row["n"])
        result["rules"] = len(self._rules)
        result["llmConfigured"] = self._llm.configured()
        try:
            result["aboxTriples"] = self._graph.count_graph(ABOX_GRAPH)
        except PortError:
            result["aboxTriples"] = None
        return result

    # ---- helpers ---------------------------------------------------------

    def _load_progress(
        self, document_id: str, batch_size: int
    ) -> dict[int, list[dict[str, Any]]]:
        rows = self._meta.query(
            """
            SELECT batch_index, candidates
              FROM platform.extraction_progress
             WHERE document_id = %s AND extractor_version = %s
               AND batch_size = %s AND status = 'completed'
            """,
            (document_id, LLM_VERSION, batch_size),
        )
        return {int(row["batch_index"]): list(row["candidates"] or []) for row in rows}

    def _save_progress(
        self,
        document_id: str,
        batch_size: int,
        batch_index: int,
        chunk_start: int,
        chunk_end: int,
        candidates: list[dict[str, Any]],
        failure_code: str | None = None,
    ) -> None:
        self._meta.execute(
            """
            INSERT INTO platform.extraction_progress (
              document_id, extractor_version, batch_size, batch_index,
              chunk_start, chunk_end, candidate_count, candidates, status,
              failure_code, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (document_id, extractor_version, batch_size, batch_index)
            DO UPDATE SET chunk_start = EXCLUDED.chunk_start,
                          chunk_end = EXCLUDED.chunk_end,
                          candidate_count = EXCLUDED.candidate_count,
                          candidates = EXCLUDED.candidates,
                          status = EXCLUDED.status,
                          failure_code = EXCLUDED.failure_code,
                          updated_at = now()
            """,
            (
                document_id,
                LLM_VERSION,
                batch_size,
                batch_index,
                chunk_start,
                chunk_end,
                len(candidates),
                Jsonb(candidates),
                "failed" if failure_code else "completed",
                failure_code,
            ),
        )

    def _clear_progress(self, document_id: str, batch_size: int) -> None:
        self._meta.execute(
            """
            DELETE FROM platform.extraction_progress
             WHERE document_id = %s AND extractor_version = %s AND batch_size = %s
            """,
            (document_id, LLM_VERSION, batch_size),
        )

    def _document(self, document_id: str) -> None:
        rows = self._meta.query(
            "SELECT document_id FROM platform.document WHERE document_id = %s",
            (document_id,),
        )
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"document not found: {document_id}",
                provider="postgres",
                provider_code="E_DOC_NOT_FOUND",
            )

    def _candidate_row(self, candidate_id: str) -> dict[str, Any]:
        rows = self._meta.query(
            """
            SELECT candidate_id, document_id, chunk_id, extractor, subject_iri,
                   predicate_iri, object_kind, object_value, confidence, state,
                   graph_iri, created_at, decided_at, reject_reason
              FROM platform.extraction_candidate
             WHERE candidate_id = %s
            """,
            (candidate_id,),
        )
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"candidate not found: {candidate_id}",
                provider="postgres",
                provider_code="E_CANDIDATE_NOT_FOUND",
            )
        return rows[0]

    def _require_pending(self, candidate_id: str) -> None:
        row = self._candidate_row(candidate_id)
        if row["state"] != "pending":
            raise PortError(
                code="Conflict",
                message=f"candidate {candidate_id} is already {row['state']}",
                provider="postgres",
                provider_code="E_CANDIDATE_NOT_PENDING",
                details={"state": row["state"]},
            )

    @staticmethod
    def _candidate(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "candidateId": row["candidate_id"],
            "documentId": row["document_id"],
            "chunkId": row["chunk_id"],
            "extractor": row["extractor"],
            "subject": row["subject_iri"],
            "predicate": row["predicate_iri"],
            "objectKind": row["object_kind"],
            "object": row["object_value"],
            "confidence": float(row["confidence"]),
            "state": row["state"],
            "graph": row["graph_iri"],
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
            "decidedAt": row["decided_at"].isoformat() if row["decided_at"] else None,
            "rejectReason": row["reject_reason"],
        }
