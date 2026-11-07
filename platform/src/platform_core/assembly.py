"""Single assembly point: config -> concrete adapters (replace provider in one file)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .adapters.canvas_disabled import DisabledCanvas
from .adapters.canvas_full import FullCanvas
from .adapters.canvas_simple import SimpleCanvas
from .adapters.embedding import EmbeddingClient
from .adapters.graph_fuseki import FusekiHttpStore
from .adapters.graph_oxigraph import OxigraphHttpStore
from .adapters.reasoner_hermit import HermitReasoner
from .adapters.llm_openai import LlmClient
from .adapters.metadata_pg import MetadataPg
from .adapters.object_fs import FsCasBackend
from .adapters.object_layered import LayeredObjectStore
from .adapters.object_pg import PgByteaBackend
from .adapters.ontology_pg import OntologyRegistry
from .adapters.reasoner_robot import ReasonerClient
from .adapters.search_pg import PgSearchIndex
from .adapters.vector_pg import PgVectorStore
from .answerable import AnswerabilityService
from .config import ConfigBundle
from .context import ContextResolver
from .documents import DocumentService
from .extraction import ExtractionService
from .facts import FactLedger
from .metrics import MetricService
from .rules import RuleExecutor
from .parsers import LocalDocumentParser
from .ports import EnvSecretProvider, UnsupportedPort
from .prov import ProvService
from .reasoning import ReasoningService
from .search import SearchService
from .shapes import ShapesRegistry
from .validation import ShaclValidator


@dataclass
class Runtime:
    bundle: ConfigBundle
    metadata: MetadataPg
    graph: Any
    objects: LayeredObjectStore
    ontology: OntologyRegistry
    shapes: ShapesRegistry
    parser: LocalDocumentParser
    documents: DocumentService
    secrets: EnvSecretProvider
    embedding: EmbeddingClient
    vectors: PgVectorStore
    search_index: PgSearchIndex
    search: SearchService
    metrics: MetricService
    rules: RuleExecutor
    prov: ProvService
    llm: LlmClient
    facts: FactLedger
    extraction: ExtractionService
    reasoner: ReasonerClient
    consistency_reasoner: HermitReasoner | None
    validator: ShaclValidator
    reasoning: ReasoningService
    context: ContextResolver
    answerable: AnswerabilityService
    canvas: Any = None
    placeholders: dict[str, UnsupportedPort] = field(default_factory=dict)
    degraded: list[str] = field(default_factory=list)

    @property
    def config(self) -> Any:
        return self.bundle.config

    def close(self) -> None:
        self.embedding.close()
        self.llm.close()
        self.reasoner.close()
        if self.consistency_reasoner is not None:
            self.consistency_reasoner.close()
        self.metadata.close()
        self.graph.close()


def assemble(bundle: ConfigBundle) -> Runtime:
    cfg = bundle.config
    metadata = MetadataPg(
        url=cfg.database.url,
        pool_max=cfg.database.pool_max,
        statement_timeout_ms=cfg.database.statement_timeout_ms,
        # S16: keep the pg_trgm operator threshold aligned with search.min_similarity
        # so `q.raw <% c.text` can use the trigram GIN index.
        trgm_word_similarity_threshold=cfg.search.min_similarity,
    )
    # Q8-a: graph.provider selects the assembled adapter; config rejected any
    # known-but-missing provider before we get here.
    if cfg.graph.provider == "fuseki":
        graph: Any = FusekiHttpStore(
            endpoint=cfg.graph.endpoint,
            timeout_ms=cfg.graph.timeout_ms,
            max_rows=cfg.graph.max_rows,
        )
    else:
        graph = OxigraphHttpStore(
            endpoint=cfg.graph.endpoint,
            timeout_ms=cfg.graph.timeout_ms,
            max_rows=cfg.graph.max_rows,
        )
    fs_backend = FsCasBackend(root=cfg.storage.root, tmp_dir=cfg.storage.tmp_dir)
    pg_backend = PgByteaBackend(metadata)
    objects = LayeredObjectStore(cfg.storage, metadata, fs_backend, pg_backend)
    ontology = OntologyRegistry(metadata, graph, objects, cfg.ontology)
    shapes = ShapesRegistry(metadata)
    parser = LocalDocumentParser(cfg.documents, cfg.ocr, cfg.storage.tmp_dir, objects)
    documents = DocumentService(
        cfg.documents, metadata, objects, parser, cfg.storage.tmp_dir
    )
    secrets = EnvSecretProvider()
    embedding = EmbeddingClient(cfg.embedding, secrets)
    vectors = PgVectorStore(metadata, cfg.embedding)
    search_index = PgSearchIndex(metadata, cfg.search)
    search = SearchService(cfg.search, metadata, embedding, vectors, search_index)
    metrics = MetricService(metadata)
    rules = RuleExecutor(metadata)
    prov = ProvService(metadata, graph)
    llm = LlmClient(cfg.llm, secrets)
    facts = FactLedger(metadata, graph)
    extraction = ExtractionService(cfg.extraction, metadata, graph, llm, facts)
    reasoner = ReasonerClient(cfg.reasoning)
    validator = ShaclValidator(cfg.reasoning)
    # Q8-b: engine=hermit adds a DL consistency/classify client; materialize
    # stays on reasoner (ROBOT/ELK) so the default path is unchanged.
    consistency_reasoner = (
        HermitReasoner(cfg.reasoning.endpoint, cfg.reasoning.timeout_ms)
        if cfg.reasoning.engine == "hermit"
        else None
    )
    reasoning = ReasoningService(
        cfg.reasoning,
        metadata,
        graph,
        reasoner,
        validator,
        ontology,
        consistency_reasoner=consistency_reasoner,
    )
    # S11: governed publish runs SHACL + consistency + breaking gates, then
    # materializes the RDFS->OWL->SHACL chain. Legacy direct publish (bootstrap
    # and S1 scripts) intentionally stays dependency-free.
    # The hook honours reasoning.materialize_online: with the default false a
    # publish records a deferred materialization instead of starting full
    # A-Box inference on the online path.
    ontology.set_governance(
        validator=validator,
        reasoner=reasoner,
        materializer=reasoning.publish_materializer,
        abox_graphs=cfg.reasoning.abox_graphs,
        reason_profile=cfg.reasoning.profile,
    )
    # --- G8 terms gate ---
    ontology.set_terms_gate(cfg.terms)
    # --- end G8 terms gate ---
    context = ContextResolver(cfg.context, ontology, reasoning, search, graph, facts)
    # Q4: pre-retrieval coverage gate over T-Box terms (SKOS when present).
    answerable = AnswerabilityService(cfg.context, ontology, graph)

    # D1 (design 53 §5.3): one port, three switch values. Config already split
    # unknown (E_PROVIDER_INVALID) from known-but-missing (E_PROVIDER_NOT_IMPLEMENTED).
    if cfg.canvas.provider == "simple":
        canvas: Any = SimpleCanvas(cfg, graph, ontology, reasoning)
    elif cfg.canvas.provider == "full":
        canvas = FullCanvas()
    else:
        canvas = DisabledCanvas("canvas.provider=off")

    placeholders = {
        "Cache": UnsupportedPort("Cache", "S3"),
    }

    degraded: list[str] = []
    if cfg.runtime.mode == "learn" and not cfg.reasoning.service_enabled:
        degraded.append("reasoner:offline_only(learn)")
    if cfg.embedding.provider == "disabled":
        degraded.append("embedding:disabled(SEMANTIC_SEARCH=false)")
    if cfg.embedding.provider == "fake":
        degraded.append("embedding:fake(test_only)")
    if not cfg.extraction.enabled:
        degraded.append("extraction:disabled")
    if not llm.configured():
        degraded.append("llm:unconfigured(rules_only)")
    degraded.append("ocr:disabled")
    degraded.extend(bundle.warnings)

    return Runtime(
        bundle=bundle,
        metadata=metadata,
        graph=graph,
        objects=objects,
        ontology=ontology,
        shapes=shapes,
        parser=parser,
        documents=documents,
        secrets=secrets,
        embedding=embedding,
        vectors=vectors,
        search_index=search_index,
        search=search,
        metrics=metrics,
        rules=rules,
        prov=prov,
        llm=llm,
        facts=facts,
        extraction=extraction,
        reasoner=reasoner,
        consistency_reasoner=consistency_reasoner,
        validator=validator,
        reasoning=reasoning,
        context=context,
        answerable=answerable,
        canvas=canvas,
        placeholders=placeholders,
        degraded=degraded,
    )
