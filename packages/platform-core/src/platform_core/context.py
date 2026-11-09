"""S6 context assembly (04 section 5.3).

Boundary (D18): this service only composes SPARQL text, dataset clauses and
parameters. Graph evaluation stays in Oxigraph, recall/fusion stays in
SearchService (fixed RRF k=60). Nothing here merges or re-ranks result sets.
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from typing import Any

from .adapters.graph_oxigraph import IRI_RE
from .adapters.ontology_pg import OntologyRegistry
from .config import ContextConfig
from .errors import PortError
from .ports import Manifest
from .reasoning import ReasoningService
from .search import SearchService

log = logging.getLogger(__name__)

TASK_TYPES = ("answer", "extract", "classify", "plan")
STRATEGIES = ("hybrid", "vector", "lexical")
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _term_text(term: dict[str, Any]) -> str:
    if term.get("kind") == "iri":
        return str(term.get("iri"))
    if term.get("kind") == "bnode":
        return f"_:{term.get('label')}"
    return f'"{_escape(str(term.get("value", "")))}"'


class ContextResolver:
    port = "ContextResolver"

    def __init__(
        self,
        config: ContextConfig,
        ontology: OntologyRegistry,
        reasoning: ReasoningService,
        search: SearchService,
        graph: Any,
        facts: Any | None = None,
        termlex: Any | None = None,
    ) -> None:
        self._config = config
        self._ontology = ontology
        self._reasoning = reasoning
        self._search = search
        self._graph = graph
        self._ledger = facts
        self._termlex = termlex
        self._lexicon_cache: tuple[str, Any] | None = None

    def manifest(self) -> Manifest:
        return Manifest(
            provider="platform",
            port=self.port,
            provider_version="s6.1",
            capabilities=["context.resolve"],
            limits={
                "defaultTokenBudget": self._config.default_token_budget,
                "maxTokenBudget": self._config.max_token_budget,
                "topK": self._config.default_top_k,
                "graphLimit": self._config.graph_limit,
            },
            notes={
                "slice": "S6",
                "fusion": "rrf-k60 (delegated to SearchService)",
                "degrade": "graph down -> chunks only; search down -> facts only",
            },
        )

    # ---- resolve ---------------------------------------------------------

    def resolve(self, request: dict[str, Any]) -> dict[str, Any]:
        if not self._config.enabled:
            raise PortError(
                code="Unsupported",
                message="context.enabled=false: context assembly is disabled",
                provider="platform",
                provider_code="E_CONTEXT_DISABLED",
                details={"key": "context.enabled"},
            )
        started = time.monotonic()
        query = str(request.get("query") or "").strip()
        if not query:
            raise PortError(
                code="InvalidArgument",
                message="context query must not be empty",
                provider="platform",
                provider_code="E_CONTEXT_QUERY_EMPTY",
            )
        task_type = str(request.get("taskType") or "answer")
        if task_type not in TASK_TYPES:
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported taskType: {task_type}",
                provider="platform",
                provider_code="E_CONTEXT_TASK",
                details={"allowed": list(TASK_TYPES)},
            )
        strategy = str(request.get("strategy") or "hybrid")
        if strategy not in STRATEGIES:
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported strategy: {strategy}",
                provider="platform",
                provider_code="E_CONTEXT_ARG",
                details={"allowed": list(STRATEGIES)},
            )

        top_k = request.get("topK")
        top_k = self._config.default_top_k if top_k is None else int(top_k)
        if top_k < 1 or top_k > 50:
            raise PortError(
                code="InvalidArgument",
                message=f"topK must be within 1..50, got {top_k}",
                provider="platform",
                provider_code="E_CONTEXT_ARG",
                details={"topK": top_k},
            )

        budget = request.get("tokenBudget")
        budget = self._config.default_token_budget if budget is None else int(budget)
        if budget < 1 or budget > self._config.max_token_budget:
            raise PortError(
                code="InvalidArgument",
                message=f"tokenBudget must be within 1..{self._config.max_token_budget}, got {budget}",
                provider="platform",
                provider_code="E_CONTEXT_BUDGET",
                details={"tokenBudget": budget, "max": self._config.max_token_budget},
            )

        # Default version = the one the inferred pointer was materialized from,
        # so facts and their ontologyVersion stay consistent. Fall back to the
        # published T-Box pointer when nothing has been materialized yet.
        pointer = self._pointer()
        requested_version = request.get("ontologyVersion")
        if not requested_version and pointer:
            requested_version = pointer.get("ontologyVersion")
        version = self._version(requested_version)
        version_id = str(version["versionId"])
        tbox_graph = str(version["graph"])
        if pointer and pointer.get("ontologyVersion") != version_id:
            # An explicitly requested version has no inferred graph of its own.
            pointer = None
        graphs = self._graphs(request.get("graphs"), tbox_graph, pointer)
        inferred_graph = pointer["targetGraph"] if pointer else None

        steps: list[dict[str, Any]] = []
        warnings: list[str] = []
        degraded = False

        lexicon = None
        if self._config.term_expand:
            try:
                lexicon = self._lexicon(version_id, tbox_graph)
            except PortError as exc:
                warnings.append(exc.provider_code or exc.code)
                log.warning(
                    "context term lexicon unavailable",
                    extra={"event": {"event": "context_degraded", "code": exc.provider_code}},
                )
        guard_before = lexicon.guard_rejected if lexicon else 0
        query_hits = lexicon.match(query, max_hits=self._config.term_expand_max_hits) if lexicon else []
        expansions = lexicon.lexical_queries(query_hits, limit=10) if lexicon else []

        hints = [str(item) for item in (request.get("entityHints") or [])]
        for hint in hints:
            if not (":" in hint and IRI_RE.match(hint)):
                raise PortError(
                    code="InvalidArgument",
                    message=f"entityHints must be IRIs, got {hint!r}",
                    provider="platform",
                    provider_code="E_CONTEXT_ARG",
                    details={"entityHints": hints},
                )

        try:
            seeds, seed_ms = self._seeds(query, hints, graphs, query_hits)
        except PortError as exc:
            degraded = True
            warnings.append(exc.provider_code or exc.code)
            log.warning(
                "context graph route degraded",
                extra={"event": {"event": "context_degraded", "code": exc.provider_code}},
            )
            seeds, seed_ms = [], 0
        steps.append(
            {
                "name": "graph.seed",
                "durationMs": seed_ms,
                "output": {
                    "seeds": len(seeds),
                    "termExpand": bool(self._config.term_expand),
                    "termHits": len(query_hits),
                    "guardRejected": (lexicon.guard_rejected - guard_before) if lexicon else 0,
                },
            }
        )

        facts: list[dict[str, Any]] = []
        entities: list[dict[str, Any]] = []
        terms: list[dict[str, Any]] = []
        fact_ms = 0
        if seeds:
            try:
                facts, entities, terms, fact_ms = self._facts(seeds, graphs, version_id, inferred_graph)
            except PortError as exc:
                degraded = True
                warnings.append(exc.provider_code or exc.code)
                log.warning(
                    "context graph route degraded",
                    extra={"event": {"event": "context_degraded", "code": exc.provider_code}},
                )
        steps.append(
            {"name": "graph.facts", "durationMs": fact_ms, "output": {"facts": len(facts)}}
        )

        chunks: list[dict[str, Any]] = []
        search_ms = 0
        lexical_only = False
        result: dict[str, Any] = {}
        try:
            search_started = time.monotonic()
            result = self._search.hybrid_search(
                query, limit=top_k, mode=strategy, expansions=expansions
            )
            search_ms = int((time.monotonic() - search_started) * 1000)
            lexical_only = bool(result.get("lexicalOnly"))
            if result.get("degraded"):
                warnings.extend(result.get("reasons") or [])
            chunks = list(result.get("results") or [])
        except PortError as exc:
            degraded = True
            warnings.append(exc.provider_code or exc.code)
            log.warning(
                "context search route degraded",
                extra={"event": {"event": "context_degraded", "code": exc.provider_code}},
            )
        steps.append(
            {
                "name": "search.hybrid",
                "durationMs": search_ms,
                "output": {
                    "hits": len(chunks),
                    "timingMs": result.get("timingMs"),
                    "embeddingCache": result.get("embeddingCache"),
                },
            }
        )

        cut_started = time.monotonic()
        used_chunks, used_facts, tokens, omitted_chunks, omitted_facts = self._cut(chunks, facts, budget)
        steps.append(
            {
                "name": "budget.cut",
                "durationMs": int((time.monotonic() - cut_started) * 1000),
                "output": {
                    "tokens": tokens,
                    "omittedChunks": omitted_chunks,
                    "omittedFacts": omitted_facts,
                },
            }
        )
        truncated = omitted_chunks > 0 or omitted_facts > 0

        citations = self._citations(used_chunks, used_facts)
        pack = {
            "id": f"pack-{uuid.uuid4().hex[:12]}",
            "taskType": task_type,
            "ontologyVersion": version_id,
            "graphs": graphs,
            "terms": terms,
            "entities": entities,
            "facts": used_facts,
            "chunks": [
                {
                    "docId": item["documentId"],
                    "chunkId": item["chunkId"],
                    "text": item["text"],
                    "score": item["score"],
                    "pageFrom": item.get("pageFrom"),
                    "pageTo": item.get("pageTo"),
                    "citationId": f"doc:{item['documentId']}#{item['chunkId']}",
                }
                for item in used_chunks
            ],
            "citations": citations,
            "tokenEstimate": tokens,
            "tokenBudget": budget,
            "truncated": truncated,
            "omitted": {"chunks": omitted_chunks, "facts": omitted_facts},
            "strategy": strategy,
            "lexicalOnly": lexical_only,
            "degraded": degraded or bool(warnings),
            "warnings": list(dict.fromkeys(warnings)),
            "steps": steps,
        }
        log.info(
            "context resolve",
            extra={
                "event": {
                    "event": "context.resolve",
                    "packId": pack["id"],
                    "version": version_id,
                    "chunks": len(used_chunks),
                    "facts": len(used_facts),
                    "tokens": tokens,
                    "degraded": pack["degraded"],
                    "ms": int((time.monotonic() - started) * 1000),
                }
            },
        )
        return pack

    # ---- helpers ---------------------------------------------------------

    def _pointer(self) -> dict[str, Any] | None:
        try:
            return self._reasoning.status().get("pointer")
        except PortError:
            return None

    def _version(self, version_id: str | None) -> dict[str, Any]:
        """Normalize to {"versionId", "graph"}: get() returns id, current() versionId."""
        try:
            if version_id:
                row = self._ontology.get(str(version_id))
                return {"versionId": row["id"], "graph": row["graph"]}
            current = self._ontology.current()
        except PortError as exc:
            if exc.code == "NotFound":
                raise PortError(
                    code="NotFound",
                    message=f"ontology version not found: {version_id}",
                    provider="platform",
                    provider_code="E_CONTEXT_VERSION",
                    details={"ontologyVersion": version_id},
                ) from exc
            raise
        if not current:
            raise PortError(
                code="NotFound",
                message="no published ontology version to build context from",
                provider="platform",
                provider_code="E_CONTEXT_VERSION",
            )
        return current

    def _graphs(
        self, requested: Any, tbox_graph: str, pointer: dict[str, Any] | None
    ) -> list[str]:
        if requested:
            graphs = [str(item) for item in requested]
            for graph in graphs:
                if not (":" in graph and IRI_RE.match(graph)):
                    raise PortError(
                        code="InvalidArgument",
                        message=f"graphs must be IRIs, got {graph!r}",
                        provider="platform",
                        provider_code="E_CONTEXT_GRAPH",
                        details={"graphs": graphs},
                    )
            return list(dict.fromkeys(graphs))
        graphs = [tbox_graph]
        if pointer and pointer.get("targetGraph"):
            graphs.append(str(pointer["targetGraph"]))
        return graphs

    def _lexicon(self, version_id: str, tbox_graph: str) -> Any:
        """Build the SKOS alias lexicon once per published T-Box version."""
        if self._termlex is not None:
            return self._termlex
        if self._lexicon_cache and self._lexicon_cache[0] == version_id:
            return self._lexicon_cache[1]
        from .termlex import TermLexicon

        lexicon = TermLexicon.build(self._graph, tbox_graph)
        self._lexicon_cache = (version_id, lexicon)
        return lexicon

    def _seeds(
        self,
        query: str,
        hints: list[str],
        graphs: list[str],
        term_hits: list[Any] | None = None,
    ) -> tuple[list[str], int]:
        if hints:
            return list(dict.fromkeys(hints)), 0
        if term_hits:
            # T1: an alias hit names the canonical class directly; the CONTAINS
            # scan is skipped so before/after share one deterministic path.
            seeds = list(dict.fromkeys(str(hit.canonical) for hit in term_hits))
            return seeds[: self._config.seed_limit], 0
        started = time.monotonic()
        from_clause = " ".join(f"FROM <{graph}>" for graph in graphs)
        sparql = (
            f"SELECT DISTINCT ?s {from_clause} WHERE {{ "
            f"?s <{RDFS_LABEL}> ?l . "
            f'FILTER(isLiteral(?l) && CONTAINS(STR(?l), "{_escape(query)}")) '
            f"}} LIMIT {self._config.seed_limit}"
        )
        result = self._graph.query(sparql)
        seeds = []
        for row in result.get("bindings", []):
            subject = row["values"].get("s")
            if subject and subject.get("kind") == "iri":
                seeds.append(str(subject["iri"]))
        return seeds, int((time.monotonic() - started) * 1000)

    def _facts(
        self,
        seeds: list[str],
        graphs: list[str],
        version_id: str,
        inferred_graph: str | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
        started = time.monotonic()
        values = " ".join(f"<{seed}>" for seed in seeds)
        graph_values = " ".join(f"<{graph}>" for graph in graphs)
        sparql = (
            "SELECT ?s ?p ?o ?g WHERE { "
            f"VALUES ?g {{ {graph_values} }} "
            f"GRAPH ?g {{ VALUES ?s {{ {values} }} ?s ?p ?o }} "
            f"}} LIMIT {self._config.graph_limit}"
        )
        result = self._graph.query(sparql)
        raw_facts: list[dict[str, Any]] = []
        for row in result.get("bindings", []):
            values_map = row["values"]
            subject, predicate, obj, graph_term = (
                values_map.get("s"),
                values_map.get("p"),
                values_map.get("o"),
                values_map.get("g"),
            )
            if not (subject and predicate and obj and graph_term):
                continue
            subject_iri = str(subject.get("iri"))
            graph_iri = str(graph_term.get("iri"))
            citation = self._triple_citation(subject, predicate, obj, graph_iri)
            raw_facts.append(
                {
                    "subject": subject_iri,
                    "predicate": str(predicate.get("iri")),
                    "object": obj,
                    "graph": graph_iri,
                    "ontologyVersion": version_id,
                    "citationId": citation["id"],
                }
            )
        # S8: a retracted assertion must not be recalled, even from an inferred
        # graph that has not been re-materialized yet.
        facts = (
            self._ledger.filter_retracted(raw_facts)
            if self._ledger is not None
            else raw_facts
        )
        entities: dict[str, dict[str, Any]] = {}
        terms: list[dict[str, Any]] = []
        for fact in facts:
            subject_iri = fact["subject"]
            obj = fact["object"]
            graph_iri = fact["graph"]
            entity = entities.setdefault(
                subject_iri,
                {"id": subject_iri, "types": [], "label": None},
            )
            predicate_iri = fact["predicate"]
            if predicate_iri == RDF_TYPE and obj.get("kind") == "iri":
                entity["types"].append(str(obj["iri"]))
            elif predicate_iri == RDFS_LABEL and obj.get("kind") == "literal":
                entity["label"] = str(obj.get("value") or "")
                terms.append(
                    {
                        "term": subject_iri,
                        "label": entity["label"],
                        "sourceGraph": graph_iri,
                        "ontologyVersion": version_id,
                    }
                )
        # Inferred facts belong to the same version; keep the caller's marker.
        if inferred_graph:
            for fact in facts:
                fact["inferred"] = fact["graph"] == inferred_graph
        if self._ledger is not None and facts:
            try:
                self._ledger.annotate(facts)
            except Exception as exc:  # never drop retrieval because governance is down
                log.warning(
                    "fact annotation failed",
                    extra={"event": {"event": "context_fact_annotate_failed", "error": str(exc)}},
                )
        return facts, list(entities.values()), terms, int((time.monotonic() - started) * 1000)

    @staticmethod
    def _triple_citation(
        subject: dict[str, Any], predicate: dict[str, Any], obj: dict[str, Any], graph: str
    ) -> dict[str, Any]:
        ref = f"{_term_text(subject)} {_term_text(predicate)} {_term_text(obj)}"
        digest = hashlib.sha1(f"{ref} {graph}".encode("utf-8")).hexdigest()
        return {"id": f"triple:{digest}", "ref": ref, "graph": graph}

    def _citations(
        self, chunks: list[dict[str, Any]], facts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        citations = []
        for item in chunks:
            citations.append(
                {
                    "id": f"doc:{item['documentId']}#{item['chunkId']}",
                    "kind": "chunk",
                    "ref": item["chunkId"],
                    "documentId": item["documentId"],
                    "locator": f"p{item.get('pageFrom')}-{item.get('pageTo')}",
                }
            )
        for fact in facts:
            citations.append(
                {
                    "id": fact["citationId"],
                    "kind": "triple",
                    "ref": f"{fact['subject']} {fact['predicate']} {_term_text(fact['object'])}",
                    "graph": fact["graph"],
                    "ontologyVersion": fact["ontologyVersion"],
                }
            )
        return citations

    def _cut(
        self, chunks: list[dict[str, Any]], facts: list[dict[str, Any]], budget: int
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int, int]:
        """Deterministic truncation: facts first, then chunks take the remainder.

        Facts are the governed, compact output of the platform and must survive
        a tight budget; before this change the RRF-ranked chunks were packed
        first and could consume the whole budget (measured 2026-11-05: a 512
        token request returned 0 facts because two chunks fitted first).
        """
        used_facts: list[dict[str, Any]] = []
        tokens = 0
        for fact in sorted(facts, key=lambda item: item["citationId"]):
            cost = self._estimate(
                f"{fact['subject']} {fact['predicate']} {_term_text(fact['object'])}"
            ) + 4
            if tokens + cost > budget:
                break
            used_facts.append(fact)
            tokens += cost
        used_chunks: list[dict[str, Any]] = []
        for item in chunks:
            cost = self._estimate(str(item.get("text") or "")) + 8
            if tokens + cost > budget:
                break
            used_chunks.append(item)
            tokens += cost
        return (
            used_chunks,
            used_facts,
            tokens,
            len(chunks) - len(used_chunks),
            len(facts) - len(used_facts),
        )

    @staticmethod
    def _estimate(text: str) -> int:
        cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        return cjk + (len(text) - cjk) // 4 + 1
