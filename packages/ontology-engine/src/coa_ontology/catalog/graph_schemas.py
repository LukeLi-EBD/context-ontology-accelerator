# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Schemas for the namespace-scoped graph vertex lookup endpoints.

Kept in a separate module from ``catalog/schemas.py`` so the existing
ontology / embedding payloads remain isolated from this newer surface.
"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class GraphNeighbor(BaseModel):
    """A destination of an outgoing edge from the source vertex.

    Only minimal identifying information is included — by design, this
    endpoint does not recursively expand neighbors; clients are expected
    to issue follow-up requests for full neighbor data.
    """

    uri: str = Field(..., description="Full IRI of the destination, or lexical form for literals.")
    label: str | None = Field(
        default=None,
        description=(
            "Human-readable name. For URI neighbors this is the first "
            "``rdfs:label`` found in any namespace graph; for literals "
            "this is the literal value itself."
        ),
    )
    kind: str = Field(
        ...,
        description=(
            "Coarse category — one of: ``class``, ``object-property``, "
            "``datatype-property``, ``annotation-property``, ``ontology``, "
            "``property``, ``literal``, ``blank-node``, ``unknown``."
        ),
    )


class GraphEdge(BaseModel):
    """One outgoing edge from the source vertex."""

    predicate: str = Field(..., description="Full IRI of the predicate.")
    predicate_label: str | None = Field(
        default=None,
        description="Local name of the predicate (e.g. ``subClassOf``) for display.",
    )
    direction: str = Field(
        default="outgoing",
        description="``outgoing`` if source→neighbor, ``incoming`` if neighbor→source.",
    )
    neighbor: GraphNeighbor


class GraphVertex(BaseModel):
    """The source vertex with its outgoing edges and minimal neighbors."""

    uri: str = Field(..., description="Full IRI of the source vertex.")
    kind: str = Field(
        ...,
        description=(
            "The vertex kind requested by the client — one of ``class``, ``object-property``, ``datatype-property``."
        ),
    )
    namespace: str = Field(..., description="Namespace whose graphs were searched.")
    types: list[str] = Field(
        default_factory=list,
        description="All ``rdf:type`` values declared on the vertex.",
    )
    labels: list[str] = Field(
        default_factory=list,
        description="All ``rdfs:label`` literals on the vertex.",
    )
    comments: list[str] = Field(
        default_factory=list,
        description="All ``rdfs:comment`` literals on the vertex.",
    )
    alt_labels: list[str] = Field(
        default_factory=list,
        description=(
            "All ``skos:altLabel`` literals — source synonyms curated during "
            "enrichment and emitted onto the induced class/property."
        ),
    )
    superseded: dict[str, list[str]] = Field(
        default_factory=dict,
        description=(
            "Previous generations of this vertex's annotations, retired when a "
            "re-induced proposal was accepted into the same ontology. Keys "
            "are ``comments`` / ``definitions`` / ``altLabels`` / ``glossaryTerms`` / ``tags``; values are the "
            "literals that used to be live (typically the AI-generated text a "
            "steward's curation replaced). Read from the ``coa:superseded*`` "
            "history predicates; NOT live content and excluded from ``edges``."
        ),
    )
    graph_uris: list[str] = Field(
        default_factory=list,
        description=(
            "Named graphs in which the vertex appears as subject. "
            "Useful for surfacing 'this class is defined in ontology X "
            "but referenced from ontology Y' in a UI."
        ),
    )
    is_mapped: bool = Field(
        default=False,
        description=(
            "Whether this vertex carries the ``coa:isMapped`` marker — i.e. it "
            "is backed by an R2RML mapping and therefore answerable by the "
            "structured Tier-2 (NL→SPARQL/NL→SQL) path. Structured/table-backed "
            "classes are True; unstructured-induced and foundational classes are "
            "False (the marker is absent). Pulled from the top-level "
            "``coa:isMapped`` triple and excluded from ``edges``."
        ),
    )
    edges: list[GraphEdge] = Field(
        default_factory=list,
        description=(
            "Outgoing edges. ``rdf:type``, ``rdfs:label``, ``rdfs:comment``, and "
            "``coa:isMapped`` are pulled into the top-level ``types``, "
            "``labels``, ``comments``, and ``is_mapped`` fields and excluded from "
            "this list to keep it focused on schema relationships."
        ),
    )


class GraphSearchHit(BaseModel):
    """One result from a substring search over entity IRIs."""

    uri: str = Field(..., description="Full IRI of the matched entity.")
    label: str | None = Field(default=None, description="rdfs:label if available.")
    kind: str = Field(..., description="class | object-property | datatype-property | property | unknown")
    graph_uris: list[str] = Field(
        default_factory=list,
        description=(
            "Named graphs the entity is defined in. A class IRI asserted in more "
            "than one ontology (e.g. a shared IRI referenced by both schema.org "
            "and FIBO) lists every source graph, not just one."
        ),
    )


class GraphSearchResult(BaseModel):
    """A page of substring-search hits plus the total match count.

    ``hits`` is the requested ``limit``/``offset`` window (in a deterministic
    order); ``total_count`` is the number of distinct entities matching the
    query across all pages, so a client can render a known page count.
    """

    hits: list[GraphSearchHit] = Field(..., description="The page of matching hits.")
    total_count: int = Field(..., description="Total distinct matches across all pages.")


class GraphStatement(BaseModel):
    """One RDF statement (triple) from a namespace's named graphs."""

    graph: str = Field(..., description="Named graph the statement lives in.")
    subject: str = Field(..., description="Subject IRI.")
    predicate: str = Field(..., description="Predicate IRI.")
    object: str = Field(..., description="Object IRI, or the lexical form of a literal.")


class GraphStatementPage(BaseModel):
    """One page of statements.

    ``statements`` is the requested ``limit``/``offset`` window in a
    deterministic order; ``truncated`` is True when more statements remain
    beyond this window (the backend fetched one extra row to decide).
    """

    statements: list[GraphStatement] = Field(..., description="The page of statements.")
    truncated: bool = Field(default=False, description="True when more statements remain.")


class CanvasLimits(BaseModel):
    """Hard limits the canvas must honour when it asks for a subgraph."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    max_nodes: int = Field(..., description="Maximum nodes returned by one subgraph page.")
    max_edges: int = Field(..., description="Maximum edges returned alongside those nodes.")
    max_page_size: int = Field(..., description="Maximum page size accepted by maxResults.")


class CanvasManifest(BaseModel):
    """What the canvas can render, and where it must stop.

    ``capabilities`` is a list of identifiers; clients must ignore values they
    do not recognise so a capability can be added without breaking older
    frontends. ``limits`` is the same set the subgraph endpoint enforces, so the
    UI can disable "load more" at the boundary instead of failing on click.
    """

    capabilities: list[str] = Field(..., description="Capability identifiers this backend supports.")
    limits: CanvasLimits = Field(..., description="Hard limits enforced by the backend.")


class CanvasNode(BaseModel):
    """A drawable node: an IRI with an optional label and coarse kind."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    uri: str = Field(..., description="Full IRI of the node.")
    label: str | None = Field(default=None, description="``rdfs:label`` when the page carried one.")
    kind: str | None = Field(default=None, description="``class``, ``object-property``, ``datatype-property`` or ``resource``.")


class CanvasEdge(BaseModel):
    """A drawable edge, including how a path traversed it."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    source: str = Field(..., description="Subject IRI.")
    predicate: str = Field(..., description="Predicate IRI.")
    predicate_label: str | None = Field(default=None, description="Local name of the predicate.")
    target: str = Field(..., description="Object IRI.")
    graph: str | None = Field(default=None, description="Named graph the triple lives in.")
    direction: str | None = Field(default=None, description="``outgoing`` or ``incoming``.")


class CanvasSubgraphPage(BaseModel):
    """One page of the canvas, shaped from a triple window."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    nodes: list[CanvasNode] = Field(default_factory=list)
    edges: list[CanvasEdge] = Field(default_factory=list)
    truncated: bool = Field(default=False, description="True when another page exists.")
    node_count: int = Field(default=0, description="Nodes in this page.")
    edge_count: int = Field(default=0, description="Edges in this page.")
    next_offset: int | None = Field(default=None, description="Offset of the next page.")


class GraphPath(BaseModel):
    """One simple path: ``hops`` equals the number of edges."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    nodes: list[CanvasNode] = Field(default_factory=list)
    edges: list[CanvasEdge] = Field(default_factory=list)
    hops: int = 0


class GraphPathResult(BaseModel):
    """Every path found within the hop and result caps."""

    paths: list[GraphPath] = Field(default_factory=list)
    truncated: bool = Field(default=False, description="True when more paths exist than returned.")


class SnapshotTbox(BaseModel):
    """Declared schema objects (the T-Box)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    classes: int = 0
    object_properties: int = 0
    datatype_properties: int = 0


class SnapshotAbox(BaseModel):
    """Asserted instances using that schema (the A-Box)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    instances: int = 0
    classes_with_instances: int = 0


class SnapshotCoverage(BaseModel):
    """How much of the declared schema the data actually uses."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    class_coverage: float = Field(default=0.0, description="``classesWithInstances / classes`` in 0..1.")
    unlabeled_classes: int = 0


class OntologySnapshot(BaseModel):
    """T-Box/A-Box coverage plus the namespace graphs the diff form can offer."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tbox: SnapshotTbox = Field(default_factory=SnapshotTbox)
    abox: SnapshotAbox = Field(default_factory=SnapshotAbox)
    coverage: SnapshotCoverage = Field(default_factory=SnapshotCoverage)
    graphs: list[str] = Field(default_factory=list)
    source: str = ""
    sampled_at: str = ""


class QualityCount(BaseModel):
    """A measured count that may be unavailable."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    count: int | None = Field(default=None, description="Null when the check could not run.")
    detail: str | None = None


class ShaclReport(BaseModel):
    """SHACL gate outcome; ``skipped`` is explicit, never zero violations."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str = Field(..., description="One of ok, violations, skipped, error.")
    violations: int | None = None
    conforms: bool | None = None
    detail: str | None = None


class QualityValidation(BaseModel):
    """Read-only quality checks for the health board."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    orphan_instances: QualityCount = Field(default_factory=QualityCount)
    unlabeled_classes: QualityCount = Field(default_factory=QualityCount)
    shacl: ShaclReport
    inference_failures: QualityCount = Field(default_factory=QualityCount)
    source: str = ""
    sampled_at: str = ""


class ReasoningStatus(BaseModel):
    """Whether an inference engine is wired up, and why not when it is not."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    available: bool = False
    engine: str | None = None
    failures: QualityCount = Field(default_factory=QualityCount)
    detail: str | None = None
    source: str = ""
    sampled_at: str = ""


class OntologyDiffCounts(BaseModel):
    """Triple and schema delta counts."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    added_triples: int = 0
    removed_triples: int = 0
    added_classes: int = 0
    removed_classes: int = 0
    added_properties: int = 0
    removed_properties: int = 0


class TripleExample(BaseModel):
    """One sampled triple."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    subject: str
    predicate: str
    object: str


class OntologyDiffExamples(BaseModel):
    """Sample triples for each side of the diff."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    added_triples: list[TripleExample] = Field(default_factory=list)
    removed_triples: list[TripleExample] = Field(default_factory=list)


class OntologyDiff(BaseModel):
    """Result of comparing two named graphs of one namespace."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    baseline_graph: str
    target_graph: str
    counts: OntologyDiffCounts = Field(default_factory=OntologyDiffCounts)
    added_classes: list[str] = Field(default_factory=list)
    removed_classes: list[str] = Field(default_factory=list)
    added_properties: list[str] = Field(default_factory=list)
    removed_properties: list[str] = Field(default_factory=list)
    examples: OntologyDiffExamples = Field(default_factory=OntologyDiffExamples)
    truncated: bool = False
    source: str = ""
    sampled_at: str = ""

