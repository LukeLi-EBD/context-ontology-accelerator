# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Abstract interfaces for the graph store and the vector store.

These are thin, typed Protocols that both backends implement. They cover
the subset of operations the induction pipeline and the catalog routers
actually use — they are NOT meant to reproduce every Neptune Analytics
feature or every OpenSearch feature.

Two golden rules:
  1. If a caller needs backend-specific behaviour, it talks to the
     concrete backend, not through these Protocols.
  2. Method names match the legacy ``na_store`` surface so the refactor
     is mechanical.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from coa_common.label_language import LabelPreference


class SearchScopeTooLarge(RuntimeError):
    """An entity search would scan more than the backend's row budget.

    Raised *before* the scan starts, from a cheap aggregate pre-check, so the
    caller can answer with an explicit, actionable error instead of letting a
    whole-namespace substring scan time out into a bare 500.
    """

    def __init__(self, quads: int, limit: int, namespace: str | None = None):
        self.quads = quads
        self.limit = limit
        self.namespace = namespace or ""
        super().__init__(
            f"unfiltered search over namespace {self.namespace or '(default)'} "
            f"would scan {quads} quads, above the {limit}-quad budget"
        )


class FilteredSearchTooLarge(RuntimeError):
    """A ``kind``-filtered search would evaluate more entities than budgeted.

    The ``kind`` filter bounds the subject set to one type, but the substring
    match and the ``ORDER BY`` still run over every subject of that type, so a
    namespace with a very large class count outruns the transport timeout just
    like an unfiltered search does. Measured before the scan from the type
    triples, which are an index scan rather than a label scan.
    """

    def __init__(self, entities: int, limit: int, kind: str, namespace: str | None = None):
        self.entities = entities
        self.limit = limit
        self.kind = kind
        self.namespace = namespace or ""
        super().__init__(
            f"search over {entities} {kind} entities in namespace "
            f"{self.namespace or '(default)'} exceeds the {limit}-entity budget"
        )


class GraphScanTooLarge(RuntimeError):
    """A whole-namespace graph read (canvas page, path walk) exceeds its budget.

    Both routes scan or expand over the namespace's full triple set, so their
    cost is not bounded by the response page size. Refused up front rather than
    left to the transport timeout, which would burn the graph store's CPU after
    the caller has already given up.
    """

    def __init__(self, quads: int, limit: int, operation: str, namespace: str | None = None):
        self.quads = quads
        self.limit = limit
        self.operation = operation
        self.namespace = namespace or ""
        super().__init__(
            f"{operation} over namespace {self.namespace or '(default)'} would scan {quads} quads, "
            f"above the {limit}-quad budget"
        )


class GraphQueryCancelled(RuntimeError):
    """The graph store aborted the query at its own server-side deadline.

    Distinct from a client timeout: the store has already stopped evaluating, so
    the caller can answer 504 without leaving a query burning CPU behind it. The
    local Oxigraph transport raises this from the store's cancellation notice,
    which arrives as a truncated 200 response rather than an HTTP error.
    """


# ── Vector store ────────────────────────────────────────────────────────


@dataclass
class EmbeddingHit:
    """One nearest-neighbour result."""

    entity_uri: str
    embedding_type: str
    model_id: str
    vector: list[float]
    ontology_id: str | None = None
    entity_type: str | None = None
    score: float | None = None
    text: str | None = None
    metadata: dict[str, Any] | None = None


@runtime_checkable
class VectorStore(Protocol):
    """Vector persistence + k-NN search.

    Implementations must embed normalized cosine vectors of dimension
    ``self.dimensions``. Vectors smaller than ``dimensions`` are padded
    with zeros by callers before being handed here.
    """

    dimensions: int

    def store_embedding(self, data: dict) -> dict:
        """Upsert a single embedding.

        ``data`` fields: entity_uri, ontology_id, entity_type,
        embedding_type, model_id, vector.
        """
        ...

    def store_embeddings_batch(self, items: list[dict]) -> list[dict]:
        """Upsert a batch of embeddings."""
        ...

    def get_embeddings_for_entity(
        self,
        entity_uri: str,
        entity_type: str | None = None,
        embedding_type: str | None = None,
        namespace: str | None = None,
    ) -> list[dict]:
        """Return all embeddings for one entity (optionally filtered)."""
        ...

    def list_embeddings_for_ontology(
        self,
        ontology_id: str,
        entity_type: str | None = None,
        embedding_type: str | None = None,
        namespace: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Return embeddings attached to an ontology.

        ``limit`` is an explicit caller-side ceiling. Implementations must
        honor it before transferring result rows so bounded metadata consumers
        do not accidentally enumerate an entire vector index.
        """
        ...

    def list_searchable_entity_uris(
        self,
        ontology_id: str,
        namespace: str | None = None,
    ) -> list[str]:
        """Return the ``entity_uri`` of every currently searchable embedding.

        Covers embeddings visible in the vector index right now for the
        ontology. A lightweight projection used by the embedding-readiness wait: it
        retrieves the actual URIs (so callers can compute an exact set
        intersection against what they wrote, which stays correct on
        append/re-accept) but deliberately excludes the embedding vector
        field so each poll transfers IDs only, not megabytes of vectors.
        """
        ...

    def search_nearest(
        self,
        vector: list[float],
        embedding_type: str,
        model_id: str,
        entity_type: str | None = None,
        ontology_id: str | None = None,
        top_k: int = 10,
        namespace: str | None = None,
    ) -> list[EmbeddingHit]:
        """k-NN search against stored vectors of the same model + type.

        ``EmbeddingHit.score`` MUST be **cosine similarity in ``[-1, 1]``**
        regardless of backend. Implementations are responsible for
        converting any backend-native score (e.g. squared L2 distance,
        OpenSearch's transformed cosine score) to raw cosine similarity
        before returning. This contract assumes the input vector and
        all stored vectors are unit-length (cosine-normalized at write
        time, which the ``BedrockEmbeddingClient`` enforces).

        Conversion identities for unit vectors:

        - From squared L2 distance: ``cos = 1 - (l2_squared / 2)``.
        - From OpenSearch ``cosinesimil`` ``_score``:
          ``cos = 2 * _score - 1``.
        - From raw cosine similarity (e.g. Neptune Analytics
          ``metric: "CosineSimilarity"``): no conversion needed.

        Conformance status (as of this writing):

        - ``NeptuneAnalyticsVectorStore`` — conforms (uses
          ``topK.byEmbedding`` with in-query L2² → cosine conversion).
        - ``OpenSearchVectorStore`` — **does NOT yet conform**: returns
          ``_score`` in ``[0, 1]`` (the raw OpenSearch ``cosinesimil``
          score) without converting. See the OPTIONAL Task 10A.1 in
          tasks.md for the rollout.
        """
        ...

    def delete_embeddings_for_ontology(self, ontology_id: str, namespace: str | None = None) -> int:
        """Drop all embeddings for an ontology. Returns deleted count."""
        ...

    def delete_embeddings_for_entities(
        self,
        entity_uris: Iterable[str],
        ontology_id: str,
        namespace: str | None = None,
    ) -> int:
        """Drop every embedding whose ``entity_uri`` is in ``entity_uris`` within a single ontology.

        Returns the deleted count. Raises when it cannot remove them all: append
        ingest relies on that to fail an accept instead of leaving the stale
        embedding searchable beside the new one.

        Used by append-mode ingest right before it re-embeds the subjects of an
        incoming proposal: a class whose description a steward replaced must not
        keep a stale embedding of the AI text in the index beside the new one,
        or recall keeps surfacing the superseded phrasing.

        The ``ontology_id`` scoping is load-bearing. A single namespace index
        can carry embeddings for multiple ontologies (foundational reloads with
        ``allow_append=True``, explicit-target merges), and different ontologies
        can carry the same IRI — an unscoped delete would take the OTHER
        ontology's embedding with it and re-create it under the wrong owner.
        Scoped to the given entities within the given ontology only; every
        other subject in the shared namespace index is untouched.
        """
        ...

    def delete_index(self, namespace: str | None = None) -> bool:
        """Delete the entire vector index for a namespace. Returns True if it existed."""
        ...

    def health_check(self) -> dict:
        """Cheap probe used by the FastAPI /health endpoint."""
        ...


# ── Graph store ─────────────────────────────────────────────────────────


@runtime_checkable
class GraphStore(Protocol):
    """Per-ontology graph store: metadata, classes, properties, raw Turtle.

    Each ontology lives in its own named graph inside a namespace; there
    is no cross-ontology catalog graph. The authoritative list of
    ontologies in a namespace lives in the Dynamo registry (see
    ``dynamo_store.list_ontologies_registry``); this Protocol only
    commits to the per-ontology operations the workbench calls.
    """

    # Ontology CRUD ----------------------------------------------------
    def create_ontology(self, data: dict) -> dict:
        """Create a new ontology from its attribute dict."""
        ...

    def get_ontology(self, oid: str) -> dict | None:
        """Fetch an ontology by id, or None if absent."""
        ...

    def get_ontology_by_uri(self, uri: str) -> dict | None:
        """Fetch an ontology by URI, or None if absent."""
        ...

    def update_ontology(self, uri: str, updates: dict) -> dict | None:
        """Apply updates to the ontology with the given URI."""
        ...

    def delete_ontology(self, uri: str) -> bool:
        """Delete the ontology with the given URI, returning whether it existed."""
        ...

    # Schema elements --------------------------------------------------
    def store_class(
        self,
        ontology_uri: str,
        class_uri: str,
        labels: list[str] | None = None,
        comments: list[str] | None = None,
        super_classes: list[str] | None = None,
        is_mapped: bool = False,
        query_backend: str | None = None,
        data_source_id: str | None = None,
    ) -> dict:
        """Persist a class into an ontology's named graph.

        Args:
            ontology_uri: URI of the owning ontology.
            class_uri: URI of the class to store.
            labels: Human-readable labels for the class.
            comments: Definitions/comments for the class.
            super_classes: Parent class URIs (``rdfs:subClassOf`` targets).
            is_mapped: Whether the class is structured-answerable (Tier-2): the
                ``rr:class`` of an R2RML TriplesMap, or a class bound to a graph source.
            query_backend: Which structured backend answers it (``"RDF_SPARQL"`` for a
                graph class). ``None`` for SQL — absence is read as SQL by serve.
            data_source_id: The source backing a graph class, for serve routing.

        Returns:
            The stored class as a dict.
        """
        ...

    def store_property(
        self,
        ontology_uri: str,
        prop_uri: str,
        label: str = "",
        comment: str = "",
        domains: list[str] | None = None,
        ranges: list[str] | None = None,
    ) -> dict:
        """Persist a property into an ontology's named graph.

        Args:
            ontology_uri: URI of the owning ontology.
            prop_uri: URI of the property to store.
            label: Human-readable label for the property.
            comment: Definition/comment for the property.
            domains: Domain class URIs for the property.
            ranges: Range URIs (class IRIs for object properties, datatypes otherwise).

        Returns:
            The stored property as a dict.
        """
        ...

    # Annotation supersession (append-mode re-ingest) ------------------
    def supersede_annotations(
        self,
        ontology_uri: str,
        subject_uris: Iterable[str],
        predicates: Mapping[str, str | None],
    ) -> int:
        """Retire the existing ``predicates`` values of ``subject_uris`` in one ontology graph.

        Called by append-mode ingest immediately before the incoming payload is
        written, so the incoming values for those (subject, predicate) pairs
        REPLACE what is live instead of accumulating beside it — a steward's
        re-induced description must not sit next to the earlier AI-generated
        one. ``predicates`` maps each annotation predicate to the history
        predicate its displaced values are moved to, or ``None`` to drop them;
        the previous generation stays inspectable without being live content.
        Scoped strictly to the given subjects — other subjects in the same
        graph (e.g. co-merged proposals) are untouched.

        Returns the number of live triples retired, or ``0`` when the backend
        has nothing to supersede (property-graph backends whose ``store_class``
        / ``store_property`` already overwrite return ``0`` without I/O).
        """
        ...

    # Bulk Turtle ingest -----------------------------------------------
    def load_turtle(
        self,
        ontology_uri: str,
        turtle: str,
        graph_uri: str | None = None,
    ) -> dict:
        """Load a raw Turtle document into the graph.

        Implementations SHOULD insert the triples into a named graph
        derived from ``graph_uri`` (or ``ontology_uri`` as a fallback)
        so subsequent deletes/re-ingests can target the ontology
        without affecting others.

        Returns a dict with at minimum ``graph_uri`` and
        ``bytes_loaded``; backends that cannot bulk-load raw Turtle
        (e.g. Neptune Analytics) return ``{"status": "skipped",
        "reason": ...}`` rather than raising.
        """
        ...

    # Bulk Turtle export -----------------------------------------------
    def get_graph_turtle(self, ontology_id: str) -> str | None:
        """Return the entire named graph for one ontology, serialized as Turtle.

        Implementations SHOULD read from the same named graph that
        :meth:`load_turtle` writes to (i.e. ``ontology_id`` must
        round-trip cleanly between load + get). Returns ``None`` when
        no such graph exists or the backend doesn't support raw RDF
        round-trip; the caller decides whether to fall back to other
        sources or surface a 404.
        """
        ...

    # Aggregate counts -------------------------------------------------
    def count_classes_and_properties(self, ontology_id: str) -> dict | None:
        """Count distinct ``owl:Class`` and property instances in one graph.

        Counts are computed over the ontology's named graph.
        Returns ``{"classes": int, "properties": int}`` or ``None`` when
        the backend cannot compute the counts (e.g. the graph does not
        exist, or the backend doesn't support the query). Callers treat
        ``None`` as "leave existing counts unchanged".
        """
        ...

    # Vertex lookup ----------------------------------------------------
    def get_vertex(
        self,
        vertex_uri: str,
        namespace: str | None = None,
        *,
        label_preference: LabelPreference | None = None,
    ) -> dict | None:
        """Return ``vertex_uri``'s outgoing triples + neighbor metadata.

        Implementations MUST search every named graph that lives under
        the namespace prefix, so a vertex from one ontology can carry
        edges that resolve to neighbors from another (e.g., an induced
        class with ``rdfs:subClassOf`` pointing into a foundational
        ontology in the same namespace).

        Returns ``None`` when the vertex has no outgoing triples in any
        of the namespace's graphs. Otherwise returns a dict::

            {
                "uri": str,
                "graph_uris": list[str],  # graphs the subject appears in
                "types": list[str],
                "labels": list[str],
                "comments": list[str],
                "edges": list[{
                    "predicate": str,
                    "predicate_label": str | None,
                    "neighbor": {
                        "uri": str,
                        "label": str | None,
                        "kind": str,  # 'class' | 'object-property' | …
                    },
                }],
            }
        """
        ...

    # Entity search ----------------------------------------------------
    def search_entities(
        self,
        query: str,
        namespace: str | None = None,
        kind: str | None = None,
        ontology_id: str | None = None,
        exclude_ontology_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        *,
        label_preference: LabelPreference | None = None,
    ) -> list[dict]:
        """Substring search over entity IRIs and labels in a namespace.

        Returns a list of dicts with keys: uri, label, kind, graph_uris (all
        named graphs the entity is defined in), in a deterministic total order
        so ``limit`` / ``offset`` yield stable page windows. Pair with
        :meth:`count_entities` for the total match count.
        """
        ...

    def count_entities(
        self,
        query: str,
        namespace: str | None = None,
        kind: str | None = None,
        ontology_id: str | None = None,
        exclude_ontology_id: str | None = None,
    ) -> int:
        """Total number of distinct entities matching a substring search.

        Same match set as :meth:`search_entities`, independent of pagination,
        so a client can render a known page count.
        """
        ...

    # Statement listing ------------------------------------------------
    def list_statements(
        self,
        namespace: str | None = None,
        *,
        subject: str | None = None,
        predicate: str | None = None,
        object_value: str | None = None,
        graph_uri: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """One page of RDF statements from the namespace's named graphs.

        Filters combine with AND; each is optional. ``subject`` / ``predicate``
        are IRIs. ``object_value`` is an IRI when it starts with an IRI scheme
        and a literal lexical form otherwise. ``graph_uri`` pins the page to one
        named graph of the namespace; a graph outside the namespace yields an
        empty page.

        Returns ``{"statements": [{"graph", "subject", "predicate", "object"}],
        "truncated": bool}``. Rows come back in the backend's named-graph index
        order, stable for a static graph, so ``limit`` / ``offset`` yield
        repeatable page windows without a global sort.
        """
        ...

    # Canvas subgraph / path -------------------------------------------
    def get_canvas_subgraph(
        self,
        namespace: str | None = None,
        *,
        kinds: Iterable[str] | None = None,
        graph_uri: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """One page of drawable nodes and edges, shaped from a triple page.

        ``kinds`` keeps only subjects typed as ``class``, ``object-property``
        or ``datatype-property``. Literal objects never become edges; they are
        used as node labels. Returns ``{"nodes", "edges", "truncated",
        "nodeCount", "edgeCount", "nextOffset"}``.
        """
        ...

    def find_graph_path(
        self,
        namespace: str | None = None,
        *,
        start: str,
        end: str,
        max_hops: int = 3,
        limit: int = 5,
    ) -> dict:
        """Simple paths between two IRIs, shortest first, within ``max_hops``.

        Returns ``{"paths": [{"nodes", "edges", "hops"}], "truncated": bool}``.
        """
        ...

    # Health board (coverage, quality, diff) ---------------------------
    def get_health_snapshot(self, namespace: str | None = None) -> dict:
        """T-Box/A-Box coverage: declared classes/properties vs instances.

        Returns ``{"tbox", "abox", "coverage", "graphs"}`` where ``coverage``
        carries ``classCoverage`` (0..1) and ``unlabeledClasses``.
        """
        ...

    def run_quality_validation(self, namespace: str | None = None) -> dict:
        """Read-only quality checks: orphan instances, unlabeled classes, SHACL.

        Returns ``{"orphanInstances", "unlabeledClasses", "shacl",
        "inferenceFailures"}``; each count is a ``{"count", "detail"}`` pair
        whose ``count`` is null when the check cannot run.
        """
        ...

    def diff_named_graphs(
        self, from_graph: str, to_graph: str, namespace: str | None = None, limit: int = 20
    ) -> dict:
        """Compare two named graphs of one namespace, read-only.

        Returns counts plus sampled added/removed classes, properties and
        triples. Raises ``ValueError`` when either graph is not a named graph
        of the namespace.
        """
        ...

    # Ontology overview ------------------------------------------------
    def get_ontology_overview(
        self,
        ontology_id: str,
        namespace: str | None = None,
        *,
        sample: bool = False,
        label_preference: LabelPreference | None = None,
    ) -> dict | None:
        """Return every class and property persisted in one ontology's graph.

        Enumerates the ontology's named graph and groups its schema
        elements for display::

            {
                "ontology_id": str,
                "graph_uri": str,
                "classes": [{"uri", "label", "comment"}],
                "object_properties": [{"uri", "label", "domain", "range"}],
                "datatype_properties": [{"uri", "label", "domain", "range"}],
            }

        Object properties are relationships between classes (range is a
        class IRI); datatype properties have a literal range. Returns
        ``None`` when the backend cannot enumerate the graph (e.g.
        Neptune Analytics has no SPARQL surface); the caller maps that to
        a 501. An existing-but-empty ontology returns a dict with empty
        lists, not ``None``.

        When ``sample`` is set, return only a bounded taxonomy seed (a few
        largest-subtree roots + a capped set of their descendants, no
        properties) instead of the full ontology. Backs the Graph view's
        initial render so large ontologies don't fan out one detail call per
        class. Backends that cannot enumerate graphs ignore the flag.
        """
        ...

    # Namespace schema (bulk) ------------------------------------------
    def get_namespace_schema(
        self,
        namespace: str,
        *,
        max_results: int = 100,
        include_properties: bool = True,
        label_preference: LabelPreference | None = None,
        class_prefix: str | None = None,
    ) -> dict:
        """List all classes and properties across all ontologies in a namespace.

        ``class_prefix`` keeps only classes whose IRI equals it or sits under it
        as an IRI namespace (``#`` / ``/``), applied before ``max_results``
        truncates the page.

        Returns::
            {
                "classes": [{"uri", "label", "description", "parentClass", "properties": [...]}],
                "namespace": str,
                "ontologyVersion": "",
            }
        """
        ...

    # Health -----------------------------------------------------------
    def health_check(self) -> dict:
        """Cheap probe used by the FastAPI /health endpoint."""
        ...
