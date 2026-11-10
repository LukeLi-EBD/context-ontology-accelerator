# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Namespace-scoped graph vertex lookup router.

Endpoints:

  GET /graph/class/{class_uri:path}?namespace=<ns>
  GET /graph/object-property/{prop_uri:path}?namespace=<ns>
  GET /graph/datatype-property/{prop_uri:path}?namespace=<ns>

All three return a {@link GraphVertex} — the source vertex's
descriptive fields plus its outgoing edges, where each edge carries
just the destination's URI / label / kind. The query covers every
named graph in the namespace, so a vertex from an induced ontology
can include edges that reach into foundational ontologies registered
in the same namespace.

Labels follow the namespace's immutable language (namespace-language LLD
§2.2.5): each resource is named with the label ranked first by
:func:`~coa_ontology.catalog.namespace_language.label_preference_for`, and a
vertex's ``labels`` list is ordered best first. A language never hides a
resource.

Vertex-kind validation is enforced server-side: hitting
``/graph/class/{uri}`` for a URI that exists in the namespace but is
typed as an ``owl:ObjectProperty`` returns 404 with a hint, since
mismatched routes usually indicate a UI bug.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from coa_control_plane_server.models import (
    GetOntologyOverviewResponseContent as _OntologyOverview,
)
from coa_control_plane_server.models import (
    GraphVertexKind as _GraphVertexKind,
)
from coa_control_plane_server.models import (
    OntologyClassSummary as _OntologyClassSummary,
)
from coa_control_plane_server.models import (
    OntologyPropertySummary as _OntologyPropertySummary,
)
from fastapi import APIRouter, HTTPException, Query

from coa_ontology.catalog.graph_schemas import (
    CanvasLimits,
    CanvasManifest,
    CanvasSubgraphPage,
    GraphPathResult,
    GraphSearchHit,
    GraphSearchResult,
    GraphStatementPage,
    GraphVertex,
    OntologyDiff,
    OntologySnapshot,
    QualityValidation,
    ReasoningStatus,
)
from coa_ontology.catalog.namespace_language import label_preference_for
from coa_ontology.query_params import require_enum_value
from coa_ontology.stores import build_stores
from coa_ontology.stores.base import GraphStore

router = APIRouter()
log = logging.getLogger(__name__)

# Map the URL-segment kind to the rdf:type the vertex must carry.
_OWL = "http://www.w3.org/2002/07/owl#"
_RDFS = "http://www.w3.org/2000/01/rdf-schema#"
_KIND_TO_REQUIRED_TYPES: dict[str, set[str]] = {
    # Some sources mark classes as ``rdfs:Class`` rather than
    # ``owl:Class``; accept either.
    "class": {_OWL + "Class", _RDFS + "Class"},
    "object-property": {_OWL + "ObjectProperty"},
    "datatype-property": {_OWL + "DatatypeProperty"},
}


# Page-size bounds for /graph/search. ``limit`` is interpolated straight into
# the SPARQL LIMIT clause, so an unbounded value is an unbounded Neptune scan
# and a negative one is invalid SPARQL (surfacing as a 500). Reject out-of-range
# values at the edge with a 400, mirroring the sources layer's ``maxResults``
# clamp. The ceiling is above the largest limit any caller sends today (the
# Explorer's 100-class fetch chunk).
_DEFAULT_SEARCH_LIMIT = 50
_MAX_SEARCH_LIMIT = 500
# ``offset`` is interpolated into the SPARQL OFFSET clause; bounded so an absurd
# value is a 400, not a query the store has to walk. Generous on purpose: the
# class browser pages through every class of an ontology, and induced ontologies
# reach tens of thousands of classes. Equals the Smithy GraphSearch ``offset``
# @range max (and GetOntologyOverview's).
_MAX_SEARCH_OFFSET = 1_000_000
# GraphSearch ``q`` @length max. ``q`` is escaped into a SPARQL CONTAINS filter;
# the bound keeps that query (and the request) a sane size. No minimum: the UI
# sends an empty or ``*`` query to list a namespace's entities.
_MAX_SEARCH_QUERY_LENGTH = 4000
# GetOntologyOverview ``limit`` / ``offset`` @range bounds. Without them a
# negative ``limit`` slices the last items off the page (``items[0:-1]``) and a
# negative ``offset`` reads as 0.
_MAX_OVERVIEW_LIMIT = 10_000
_MAX_OVERVIEW_OFFSET = 1_000_000

# Canvas manifest (F13). ``nodeKinds`` / ``graphFilter`` / ``offsetPaging`` are
# the controls the canvas actually implements today; anything else must stay
# hidden. Limits match what GetCanvasSubgraph will enforce, and are published
# here so the UI stops paging at the boundary instead of learning it from a 400.
_CANVAS_CAPABILITIES: tuple[str, ...] = ("nodeKinds", "graphFilter", "offsetPaging")
_CANVAS_LIMITS: dict[str, int] = {"max_nodes": 200, "max_edges": 400, "max_page_size": 100}
# The three node kinds GetCanvasSubgraph accepts. Anything else is a client bug,
# not a filter that silently matches nothing.
_CANVAS_KINDS: tuple[str, ...] = ("class", "object-property", "datatype-property")
_CANVAS_PATH_MAX_HOPS = 6
_CANVAS_PATH_MAX_LIMIT = 20
_DEFAULT_CANVAS_PAGE_SIZE = 50

# Fixed client-facing messages: backend exception text (store class names,
# endpoints) is logged, never returned, and the caller's own URI is not echoed.
_MSG_LOOKUP_UNSUPPORTED = "Graph lookup is not supported on this backend."
_MSG_INVALID_VERTEX_URI = "Invalid vertex URI."
_MSG_VERTEX_NOT_FOUND = "No triples found for this URI in the namespace."
_MSG_INVALID_STATEMENT_FILTER = "Invalid statement filter."

# ListStatements bounds. ``limit`` / ``offset`` reach SPARQL LIMIT/OFFSET, and
# the term length equals the Smithy ``objectValue`` @length max; all are
# rejected at the edge rather than clamped.
_DEFAULT_STATEMENT_LIMIT = 20
_MAX_STATEMENT_LIMIT = 200
_MAX_STATEMENT_OFFSET = 1_000_000
_MAX_STATEMENT_TERM_LENGTH = 2048


def _graph(namespace: str | None) -> GraphStore:
    return build_stores(namespace)[0]


def _now_iso() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# Provenance strings the health board renders verbatim, so a number on the page
# can be traced back to the query shape that produced it.
_HEALTH_SNAPSHOT_SOURCE = (
    "SPARQL aggregation over the namespace named graphs: owl:Class / owl:ObjectProperty / "
    "owl:DatatypeProperty declarations joined to rdf:type usage"
)
_HEALTH_VALIDATE_SOURCE = (
    "SPARQL over the namespace named graphs (outgoing edges and inbound references); "
    "SHACL shapes are not configured in this deployment"
)
_REASONING_SOURCE = "ontology-engine capability check (no reasoner wired up)"
_DIFF_SOURCE = "SPARQL MINUS between the two named graphs"
_MAX_DIFF_LIMIT = 200


def _lookup(vertex_uri: str, namespace: str, kind: str) -> GraphVertex:
    graph = _graph(namespace)
    preference = label_preference_for(namespace)
    try:
        record = graph.get_vertex(vertex_uri, namespace=namespace, label_preference=preference)
    except NotImplementedError as e:
        log.warning("graph lookup unsupported by backend: %s", e)
        raise HTTPException(501, _MSG_LOOKUP_UNSUPPORTED) from e
    except ValueError as e:
        # _iri() raises ValueError for malformed URIs; its text echoes the URI.
        raise HTTPException(400, _MSG_INVALID_VERTEX_URI) from e
    if record is None:
        # Backend may also return None when the call is unsupported
        # (e.g. Neptune Analytics today).
        if not getattr(graph, "get_vertex", None) or graph.__class__.__name__ == "NeptuneAnalyticsGraphStore":
            raise HTTPException(501, "Vertex lookup is not supported on this backend.")
        raise HTTPException(404, _MSG_VERTEX_NOT_FOUND)

    required = _KIND_TO_REQUIRED_TYPES[kind]
    if not (set(record.get("types") or []) & required):
        raise HTTPException(
            404,
            (
                f"The vertex exists in this namespace but is not a "
                f"{kind.replace('-', ' ')} (rdf:type = {record.get('types') or []})."
            ),
        )

    return GraphVertex(
        uri=record["uri"],
        kind=kind,
        namespace=namespace,
        types=record.get("types", []),
        labels=record.get("labels", []),
        comments=record.get("comments", []),
        alt_labels=record.get("alt_labels", []),
        superseded=record.get("superseded", {}),
        graph_uris=record.get("graph_uris", []),
        is_mapped=record.get("is_mapped", False),
        edges=record.get("edges", []),
    )


@router.get("/search", response_model=GraphSearchResult)
def search_entities(
    q: str,
    namespace: str = "default",
    kind: str | None = None,
    ontology_id: str | None = None,
    exclude_ontology_id: str | None = None,
    limit: int = _DEFAULT_SEARCH_LIMIT,
    offset: int = 0,
):
    """Substring search over entity IRIs and labels in a namespace.

    Searches all named graphs under the namespace for subjects whose
    IRI or ``rdfs:label`` contains the query string (case-insensitive).
    Optionally filter by ``kind`` (``class``, ``object-property``,
    ``datatype-property``) and/or ``ontology_id`` (restricts to a
    single named graph). Use ``exclude_ontology_id`` to omit results
    from a specific ontology (e.g., governed-metrics).

    Returns a ``{hits, total_count}`` envelope: ``hits`` is the ``limit`` /
    ``offset`` page window (in a deterministic order) with URI, label, kind,
    and graph_uris (all named graphs the entity is defined in); ``total_count``
    is the number of distinct matches across all pages so the client can render
    a known page count.
    """
    if len(q) > _MAX_SEARCH_QUERY_LENGTH:
        raise HTTPException(400, f"q must be at most {_MAX_SEARCH_QUERY_LENGTH} characters")
    require_enum_value("kind", kind, _GraphVertexKind)
    if ontology_id and exclude_ontology_id:
        raise HTTPException(400, "Cannot use both ontology_id and exclude_ontology_id")
    if exclude_ontology_id is not None and not exclude_ontology_id.strip():
        raise HTTPException(400, "exclude_ontology_id cannot be empty")
    if not 0 <= offset <= _MAX_SEARCH_OFFSET:
        raise HTTPException(400, f"offset must be between 0 and {_MAX_SEARCH_OFFSET}")
    if not 1 <= limit <= _MAX_SEARCH_LIMIT:
        raise HTTPException(400, f"limit must be between 1 and {_MAX_SEARCH_LIMIT}")

    graph = _graph(namespace)
    preference = label_preference_for(namespace)
    try:
        results = graph.search_entities(
            query=q,
            namespace=namespace,
            kind=kind,
            ontology_id=ontology_id,
            exclude_ontology_id=exclude_ontology_id,
            limit=limit,
            offset=offset,
            label_preference=preference,
        )
        # Recomputed per page by design: ``total_count`` is part of every page's
        # envelope contract (clients use it as the paging stop condition), so it
        # must stay identical across pages rather than be derived from the window.
        total = graph.count_entities(
            query=q,
            namespace=namespace,
            kind=kind,
            ontology_id=ontology_id,
            exclude_ontology_id=exclude_ontology_id,
        )
    except (NotImplementedError, AttributeError) as e:
        log.warning("entity search unsupported by backend: %s", e)
        raise HTTPException(501, "Entity search is not supported on this backend.") from e
    return GraphSearchResult(hits=[GraphSearchHit(**r) for r in results], total_count=total)


@router.get("/canvas/manifest", response_model=CanvasManifest)
def get_canvas_manifest():
    """What the canvas can render, and the limits it must page within.

    Served from constants rather than derived from a scan: the point is to let
    the UI disable controls the backend cannot honour *before* it draws, so a
    wrong guess here would surface as a button that always fails. When a
    capability or limit changes, it changes here and in ``GetCanvasSubgraph``
    together — the manifest is the declared contract, not a probe result.
    """
    return CanvasManifest(capabilities=list(_CANVAS_CAPABILITIES), limits=CanvasLimits(**_CANVAS_LIMITS))


@router.get("/canvas", response_model=CanvasSubgraphPage)
def get_canvas_subgraph(
    namespace: str = "default",
    kinds: str | None = None,
    graph: str | None = None,
    limit: int = _DEFAULT_CANVAS_PAGE_SIZE,
    offset: int = 0,
):
    """One page of drawable canvas nodes and edges.

    Paging is offset-based on the backend's index order (no global sort), so
    ``nextOffset`` from the previous page is the continuation token. A node-kind
    filter keeps only subjects typed as that kind; the page is still a full page
    because the type test runs inside the query, not after it.
    """
    max_page = _CANVAS_LIMITS["max_page_size"]
    if not 1 <= limit <= max_page:
        raise HTTPException(400, f"limit must be between 1 and {max_page}")
    if not 0 <= offset <= _MAX_SEARCH_OFFSET:
        raise HTTPException(400, f"offset must be between 0 and {_MAX_SEARCH_OFFSET}")
    if graph is not None and (not graph or len(graph) > _MAX_STATEMENT_TERM_LENGTH):
        raise HTTPException(400, _MSG_INVALID_STATEMENT_FILTER)

    parsed_kinds: list[str] | None = None
    if kinds:
        parsed_kinds = [k.strip() for k in kinds.split(",") if k.strip()]
        unknown = [k for k in parsed_kinds if k not in _CANVAS_KINDS]
        if unknown:
            raise HTTPException(400, "Unknown node kind(s): " + ", ".join(unknown))

    graph_store = _graph(namespace)
    try:
        page = graph_store.get_canvas_subgraph(
            namespace,
            kinds=parsed_kinds,
            graph_uri=graph,
            limit=limit,
            offset=offset,
        )
    except (NotImplementedError, AttributeError) as e:
        log.warning("canvas subgraph unsupported by backend: %s", e)
        raise HTTPException(501, "Canvas subgraph is not supported on this backend.") from e
    except ValueError as e:
        log.warning("invalid canvas filter: %s", e)
        raise HTTPException(400, _MSG_INVALID_STATEMENT_FILTER) from e
    return CanvasSubgraphPage(**page)


@router.get("/path", response_model=GraphPathResult)
def find_graph_path(
    namespace: str = "default",
    start: str = Query(...),
    end: str = Query(...),
    max_hops: int = 3,
    limit: int = 5,
):
    """Simple paths between ``start`` and ``end``, shortest first.

    ``max_hops`` and ``limit`` are clamped to the canvas limits rather than
    rejected so a UI slider can never turn a click into a 400; ``truncated``
    carries the fact that more paths exist.
    """
    for label, value in (("start", start), ("end", end)):
        if not value or len(value) > _MAX_STATEMENT_TERM_LENGTH:
            raise HTTPException(400, f"Invalid {label} IRI.")
        if not value.startswith(("http://", "https://", "urn:")):
            raise HTTPException(400, f"Invalid {label} IRI.")

    if not 1 <= max_hops <= _CANVAS_PATH_MAX_HOPS:
        raise HTTPException(400, f"max_hops must be between 1 and {_CANVAS_PATH_MAX_HOPS}")
    if not 1 <= limit <= _CANVAS_PATH_MAX_LIMIT:
        raise HTTPException(400, f"limit must be between 1 and {_CANVAS_PATH_MAX_LIMIT}")

    graph_store = _graph(namespace)
    try:
        result = graph_store.find_graph_path(
            namespace,
            start=start,
            end=end,
            max_hops=max_hops,
            limit=limit,
        )
    except (NotImplementedError, AttributeError) as e:
        log.warning("graph path unsupported by backend: %s", e)
        raise HTTPException(501, "Graph path search is not supported on this backend.") from e
    except ValueError as e:
        log.warning("invalid graph path IRI: %s", e)
        raise HTTPException(400, "Invalid graph path IRI.") from e
    return GraphPathResult(**result)


@router.get("/snapshot", response_model=OntologySnapshot, response_model_by_alias=True)
def get_ontology_snapshot(namespace: str = "default"):
    """T-Box/A-Box coverage for the health board.

    Class coverage is ``classesWithInstances / tbox.classes``: a real fraction,
    so a namespace whose ontology declares 156 classes but only instantiates 4
    shows 2.6%, not "green".
    """
    graph_store = _graph(namespace)
    try:
        snapshot = graph_store.get_health_snapshot(namespace)
    except (NotImplementedError, AttributeError) as e:
        log.warning("health snapshot unsupported by backend: %s", e)
        raise HTTPException(501, "Ontology snapshot is not supported on this backend.") from e
    except ValueError as e:
        log.warning("invalid namespace for health snapshot: %s", e)
        raise HTTPException(400, "Invalid namespace.") from e
    return OntologySnapshot(**snapshot, source=_HEALTH_SNAPSHOT_SOURCE, sampled_at=_now_iso())


@router.post("/validate", response_model=QualityValidation, response_model_by_alias=True)
def run_validation(namespace: str = "default"):
    """Read-only quality checks: orphan instances, unlabeled classes, SHACL.

    Checks that cannot run report ``skipped``/null with a reason. SHACL never
    degrades into "0 violations" just because no shapes are loaded.
    """
    graph_store = _graph(namespace)
    try:
        validation = graph_store.run_quality_validation(namespace)
    except (NotImplementedError, AttributeError) as e:
        log.warning("quality validation unsupported by backend: %s", e)
        raise HTTPException(501, "Quality validation is not supported on this backend.") from e
    except ValueError as e:
        log.warning("invalid namespace for quality validation: %s", e)
        raise HTTPException(400, "Invalid namespace.") from e
    return QualityValidation(**validation, source=_HEALTH_VALIDATE_SOURCE, sampled_at=_now_iso())


@router.get("/reasoning", response_model=ReasoningStatus, response_model_by_alias=True)
def get_reasoning_status(namespace: str = "default"):
    """Whether a reasoner is wired up in this deployment.

    Served from capability constants: this service materialises nothing, so
    the honest answer is ``available: false`` with the reason, not a zero
    failure count that implies reasoning ran and succeeded.
    """
    return ReasoningStatus(
        available=False,
        engine=None,
        failures={
            "count": None,
            "detail": "inference jobs are not observable from this service",
        },
        detail="This deployment serves asserted triples only; no reasoner is configured.",
        source=_REASONING_SOURCE,
        sampled_at=_now_iso(),
    )


@router.get("/diff", response_model=OntologyDiff, response_model_by_alias=True)
def get_ontology_diff(
    namespace: str = "default",
    from_graph: str = Query(..., alias="from"),
    to_graph: str = Query(..., alias="to"),
    limit: int = 20,
):
    """Compare two named graphs of this namespace with SPARQL ``MINUS``.

    Both IRIs must be named graphs of the namespace, so the diff cannot be used
    to read a graph outside it. Added means present in ``to``, absent from
    ``from``.
    """
    for label, value in (("from", from_graph), ("to", to_graph)):
        if not value or len(value) > _MAX_STATEMENT_TERM_LENGTH:
            raise HTTPException(400, f"Invalid {label} graph IRI.")
        if not value.startswith(("http://", "https://", "urn:")):
            raise HTTPException(400, f"Invalid {label} graph IRI.")
    if not 1 <= limit <= _MAX_DIFF_LIMIT:
        raise HTTPException(400, f"limit must be between 1 and {_MAX_DIFF_LIMIT}")

    graph_store = _graph(namespace)
    try:
        result = graph_store.diff_named_graphs(from_graph, to_graph, namespace=namespace, limit=limit)
    except (NotImplementedError, AttributeError) as e:
        log.warning("graph diff unsupported by backend: %s", e)
        raise HTTPException(501, "Graph diff is not supported on this backend.") from e
    except ValueError as e:
        log.warning("invalid graph for diff: %s", e)
        raise HTTPException(400, "Both graphs must be named graphs of this namespace.") from e
    return OntologyDiff(**result, source=_DIFF_SOURCE, sampled_at=_now_iso())


@router.get("/statements", response_model=GraphStatementPage)
def list_statements(
    namespace: str = "default",
    subject: str | None = None,
    predicate: str | None = None,
    object_value: str | None = Query(default=None, alias="object"),
    graph: str | None = None,
    limit: int = _DEFAULT_STATEMENT_LIMIT,
    offset: int = 0,
):
    """One page of the namespace's RDF statements, optionally filtered.

    Every filter is optional and they combine with AND. ``subject`` /
    ``predicate`` / ``graph`` are IRIs; ``object`` is an IRI when it starts
    with an IRI scheme and a literal lexical form otherwise. The page is
    namespace-scoped by the graph store, so a ``graph`` outside the namespace
    yields an empty page rather than leaking another namespace's triples.
    """
    if not 1 <= limit <= _MAX_STATEMENT_LIMIT:
        raise HTTPException(400, f"limit must be between 1 and {_MAX_STATEMENT_LIMIT}")
    if not 0 <= offset <= _MAX_STATEMENT_OFFSET:
        raise HTTPException(400, f"offset must be between 0 and {_MAX_STATEMENT_OFFSET}")

    for value in (subject, predicate, graph):
        if value is not None and (not value or len(value) > _MAX_STATEMENT_TERM_LENGTH):
            raise HTTPException(400, _MSG_INVALID_STATEMENT_FILTER)
        if value is not None and not value.startswith(("http://", "https://", "urn:")):
            raise HTTPException(400, _MSG_INVALID_STATEMENT_FILTER)
    if object_value is not None and len(object_value) > _MAX_STATEMENT_TERM_LENGTH:
        raise HTTPException(400, _MSG_INVALID_STATEMENT_FILTER)

    graph_store = _graph(namespace)
    try:
        result = graph_store.list_statements(
            namespace,
            subject=subject,
            predicate=predicate,
            object_value=object_value,
            graph_uri=graph,
            limit=limit,
            offset=offset,
        )
    except (NotImplementedError, AttributeError) as e:
        log.warning("statement listing unsupported by backend: %s", e)
        raise HTTPException(501, "Statement listing is not supported on this backend.") from e
    except ValueError as e:
        # ``_iri`` rejects malformed / injecting URIs; its text echoes them.
        log.warning("invalid statement filter: %s", e)
        raise HTTPException(400, _MSG_INVALID_STATEMENT_FILTER) from e
    return GraphStatementPage(**result)


@router.get("/ontology-overview", response_model=_OntologyOverview, response_model_by_alias=True)
def get_ontology_overview(
    ontology_id: str,
    namespace: str = "default",
    sample: bool = False,
    limit: int | None = None,
    offset: int = 0,
):
    """Enumerate the classes + properties persisted in one ontology's graph.

    Reads directly from the graph store (not the Dynamo registry), so the
    result reflects the triples that actually landed in the knowledge
    graph for ``ontology_id``. Returns the ontology's classes, object
    properties (relationships between classes), and datatype properties.

    ``limit``/``offset`` page each of the three collections independently, and
    the response carries the un-paged totals (``total_classes`` etc.) so a
    client shows the true count while rendering one page. This bounds the
    response: a wide ontology (thousands of classes/properties) would otherwise
    exceed the API Gateway / Lambda response limit and 502 the call (#143).

    Set ``sample=true`` for a bounded taxonomy seed (a few largest-subtree
    root classes + a capped set of their descendants, no properties) instead
    of the full ontology. The Graph view uses this for its initial render so a
    multi-thousand-class ontology doesn't fan out one detail call per class;
    the rest of the taxonomy loads on demand as the user expands nodes.

    Returns 501 when the active backend cannot enumerate graphs (e.g.
    Neptune Analytics). An ontology that exists but has no schema triples
    yields a 200 with empty lists.

    ``limit`` (1-10000) and ``offset`` (0-1000000) out of range are a 400, as on
    ``/graph/search``.
    """
    if not 0 <= offset <= _MAX_OVERVIEW_OFFSET:
        raise HTTPException(400, f"offset must be between 0 and {_MAX_OVERVIEW_OFFSET}")
    if limit is not None and not 1 <= limit <= _MAX_OVERVIEW_LIMIT:
        raise HTTPException(400, f"limit must be between 1 and {_MAX_OVERVIEW_LIMIT}")
    graph = _graph(namespace)
    preference = label_preference_for(namespace)
    try:
        overview = graph.get_ontology_overview(
            ontology_id, namespace=namespace, sample=sample, label_preference=preference
        )
    except NotImplementedError as e:
        log.warning("ontology overview unsupported by backend: %s", e)
        raise HTTPException(501, "Ontology overview is not supported on this backend.") from e
    except ValueError as e:
        raise HTTPException(400, "Invalid ontology id.") from e
    except Exception as e:
        log.exception("get_ontology_overview failed for %s in %s", ontology_id, namespace)
        raise HTTPException(500, f"Internal error querying ontology graph: {type(e).__name__}") from e
    if overview is None:
        raise HTTPException(501, "Ontology overview is not supported on this backend.")

    all_classes = overview.get("classes", [])
    all_object_properties = overview.get("object_properties", [])
    all_datatype_properties = overview.get("datatype_properties", [])

    def _page(items: list) -> list:
        return items[offset : offset + limit] if limit is not None else items[offset:]

    # Construct the generated model. The store returns dicts with snake_case
    # keys; the generated model accepts them via populate_by_name=True. Each
    # collection is paged independently; totals reflect the full (un-paged) set.
    return _OntologyOverview(
        ontology_id=overview["ontology_id"],
        namespace=namespace,
        graph_uri=overview.get("graph_uri"),
        classes=[_OntologyClassSummary(**c) for c in _page(all_classes)],
        object_properties=[_OntologyPropertySummary(**p) for p in _page(all_object_properties)],
        datatype_properties=[_OntologyPropertySummary(**p) for p in _page(all_datatype_properties)],
        total_classes=len(all_classes),
        total_object_properties=len(all_object_properties),
        total_datatype_properties=len(all_datatype_properties),
    )


@router.get("/schema")
def get_namespace_schema(
    namespace: str = "default",
    max_results: int = 100,
    include_properties: bool = True,
    class_filter: str | None = None,
):
    """List all OWL classes (and optionally properties) across all ontologies in a namespace.

    Returns a bulk schema summary for MCP discovery tools and UI schema views.
    Queries all named graphs under the namespace prefix.

    ``class_filter`` restricts the response to classes whose IRI equals the
    given value or starts with it (treating a trailing ``#``/``/`` as a
    prefix). Matches the Smithy ``DescribeSchema.classFilter`` input; a
    non-matching filter returns an empty ``classes`` list.

    When ``class_filter`` is set it is passed to the store as ``class_prefix``
    (the same exact or IRI-namespace match), which the store applies before its
    LIMIT, so a class outside the first page of the whole namespace is still
    found. The backend is queried with the 500-class ceiling and the match above
    is re-applied here, for stores that ignore ``class_prefix``; ``max_results``
    still bounds the FINAL response.
    """
    graph = _graph(namespace)
    preference = label_preference_for(namespace)
    backend_limit = 500 if class_filter else min(max_results, 500)
    try:
        result = graph.get_namespace_schema(
            namespace,
            max_results=backend_limit,
            include_properties=include_properties,
            label_preference=preference,
            class_prefix=class_filter,
        )
    except NotImplementedError as e:
        log.warning("namespace schema unsupported by backend: %s", e)
        raise HTTPException(501, "Namespace schema is not supported on this backend.") from e
    except Exception as e:
        log.exception("get_namespace_schema failed for %s", namespace)
        raise HTTPException(500, f"Internal error querying schema: {type(e).__name__}") from e

    if class_filter:
        prefix = class_filter
        classes = result.get("classes") if isinstance(result, dict) else None
        if isinstance(classes, list):
            filtered = [c for c in classes if isinstance(c, dict) and _matches_class_filter(c.get("uri", ""), prefix)]
            # Re-apply the caller's cap AFTER filtering so callers get at most
            # ``max_results`` matches (not the raw 500 from the backend).
            result["classes"] = filtered[: min(max_results, 500)]
    return result


def _matches_class_filter(uri: str, prefix: str) -> bool:
    """True if ``uri`` equals ``prefix`` or begins with it as an IRI prefix.

    Treats ``prefix`` as either an exact IRI or a namespace-style prefix.
    A trailing ``#`` or ``/`` on ``prefix`` is honored verbatim; otherwise
    the match tolerates a following ``#`` or ``/`` before any local name so
    ``https://schema.org/`` matches ``https://schema.org/Order``.
    """
    if not uri:
        return False
    if uri == prefix:
        return True
    if prefix.endswith(("#", "/")):
        return uri.startswith(prefix)
    return uri.startswith(prefix + "#") or uri.startswith(prefix + "/")


@router.get("/vertex", response_model=GraphVertex)
def get_vertex(uri: str, namespace: str = "default"):
    """Look up any vertex by IRI — no kind validation."""
    graph = _graph(namespace)
    preference = label_preference_for(namespace)
    try:
        record = graph.get_vertex(uri, namespace=namespace, label_preference=preference)
    except NotImplementedError as e:
        log.warning("graph lookup unsupported by backend: %s", e)
        raise HTTPException(501, _MSG_LOOKUP_UNSUPPORTED) from e
    except ValueError as e:
        raise HTTPException(400, _MSG_INVALID_VERTEX_URI) from e
    if record is None:
        raise HTTPException(404, _MSG_VERTEX_NOT_FOUND)
    record.setdefault("kind", "unknown")
    record.setdefault("namespace", namespace)
    return GraphVertex(**record)


# Vertex lookups take the IRI as ``?uri=`` query param. OWL IRIs frequently
# contain slashes and ``#`` fragments which double-encode poorly through
# API Gateway path templates and through some HTTP clients.
@router.get("/class/", response_model=GraphVertex)
def get_class(uri: str, namespace: str = "default"):
    """Look up an ``owl:Class`` vertex (URI in ``?uri=`` query param)."""
    return _lookup(uri, namespace, "class")


@router.get("/object-property/", response_model=GraphVertex)
def get_object_property(uri: str, namespace: str = "default"):
    """Look up an ``owl:ObjectProperty`` vertex (URI in ``?uri=`` query param)."""
    return _lookup(uri, namespace, "object-property")


@router.get("/datatype-property/", response_model=GraphVertex)
def get_datatype_property(uri: str, namespace: str = "default"):
    """Look up an ``owl:DatatypeProperty`` vertex (URI in ``?uri=`` query param)."""
    return _lookup(uri, namespace, "datatype-property")
