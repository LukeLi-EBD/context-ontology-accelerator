// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// Ontology graph + catalog query operations.
//
// Read-only namespace-scoped queries against the ontology graph and
// catalog registry. Used by the web UI's Graph Search and Catalog views.
// Backend FastAPI routers live under packages/ontology-engine/.../catalog/.
$version: "2"

namespace com.amazon.semanticcontext.ontologygraph

use com.amazon.semanticcontext.common#ClientToken
use com.amazon.semanticcontext.common#ConflictError
use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#OntologyId
use com.amazon.semanticcontext.common#PaginatedOutput
use com.amazon.semanticcontext.common#PaginationToken
use com.amazon.semanticcontext.common#PresignedUrl
use com.amazon.semanticcontext.common#StringList
use com.amazon.semanticcontext.common#Uuid
use com.amazon.semanticcontext.common#ValidationError

// ── Catalog ─────────────────────────────────────────────────────────
/// Coarse-grained ontology category for filtering the catalog.
enum OntologyType {
    /// A foundational (upper / reference) ontology.
    FOUNDATIONAL = "foundational"

    /// An ontology induced from data sources (e.g. tables).
    INDUCED = "induced"

    /// An ontology created manually by a user.
    USER_CREATED = "user_created"

    /// An ontology file a user uploaded (the web app's upload flow).
    USER_UPLOADED = "user_uploaded"
}

/// Serialization format of an ontology file, as accepted by
/// IngestOntologyFromS3. Several spellings name the same format.
enum OntologyFileFormat {
    /// Turtle.
    TURTLE = "turtle"

    /// Turtle (file-extension spelling).
    TTL = "ttl"

    /// RDF/XML.
    RDF_XML = "rdf-xml"

    /// RDF/XML (media-type spelling).
    RDF_PLUS_XML = "rdf+xml"

    /// OWL in RDF/XML.
    OWL_XML = "owl-xml"

    /// RDF/XML (short spelling).
    XML = "xml"

    /// JSON-LD.
    JSON_LD = "json-ld"

    /// JSON-LD (file-extension spelling).
    JSONLD = "jsonld"
}

/// Key of an object in the ontology upload bucket, as issued by
/// GetOntologyUploadUrl: relative (no leading `/`), with no `..` path segment
/// and no backslash.
@length(min: 1, max: 1024)
@pattern("^(?!/)(?!(?:.*/)?\\.\\.(?:/|$))[^\\\\]+$")
string OntologyUploadKey

/// IRI of a graph vertex: an `http(s)://` IRI with a host, or a `urn:`, with
/// no whitespace or characters forbidden in a SPARQL IRI reference.
@length(min: 1, max: 2048)
@pattern("^(?:https?://[^/\\s<>\"{}|\\\\^`]|urn:)[^\\s<>\"{}|\\\\^`]*$")
string VertexIri

/// Summary of an ontology in the namespace registry.
structure OntologyRecord {
    /// Unique identifier of the ontology within the namespace.
    @required
    ontologyId: String

    /// Canonical IRI of the ontology.
    @required
    uri: String

    /// Human-readable display title.
    title: String

    /// Human-readable description of the ontology.
    description: String

    /// Category of the ontology (foundational, induced, or user_created).
    ontologyType: String

    /// Ingest lifecycle marker set by the async parse/embed worker: "pending"
    /// while ingesting, "ok" once parsed, "parse_error" on failure. Absent on
    /// legacy rows persisted before this field existed, for which a positive
    /// embeddingCount means the ingest completed.
    parseStatus: String

    /// Lifecycle status of the registry row. Set to "deleting" while an async
    /// ontology delete tears down its graph + embeddings (the row stays listed
    /// as "Delete in progress" until teardown completes, then is removed).
    /// Absent for normal, fully-materialized ontologies.
    status: String

    /// Set when an async delete's teardown failed (graph/embedding hard gate),
    /// leaving the row in status "deleting". Lets a client distinguish a stuck
    /// delete (re-issue DELETE to retry) from one still in progress. Cleared
    /// when a fresh delete starts; absent otherwise.
    deleteError: String

    /// Serialization format of the source file (e.g. turtle, rdfxml, jsonld).
    format: String

    /// Domain tags used to categorize and filter the ontology.
    domainTags: StringList

    /// Number of classes in the ontology.
    classCount: Integer

    /// Number of properties in the ontology.
    propertyCount: Integer

    /// Number of axioms in the ontology.
    axiomCount: Integer

    /// Number of vector embeddings generated for the ontology.
    embeddingCount: Integer

    /// IRI of the named graph holding the ontology's triples.
    graphUri: String

    /// Creation timestamp of the registry row.
    createdAt: String

    /// Last-updated timestamp of the registry row.
    updatedAt: String
}

list OntologyRecordList {
    member: OntologyRecord
}

/// IRI of a `urn:platform:` named graph (the only graphs a namespace may ask
/// the reasoner to read).
@length(min: 1, max: 2048)
string PlatformGraphIri

list PlatformGraphIriList {
    member: PlatformGraphIri
}

/// List ontologies registered in a namespace, one page at a time.
///
/// A page can hold fewer than `maxResults` ontologies, or none, while
/// `nextToken` is present: each request reads a bounded slice of the registry.
/// Keep paging until `nextToken` is absent.
///
/// The server also binds a legacy `skip` query parameter (an offset applied
/// before the page, up to 10000). It predates `nextToken`, is kept for existing
/// callers, and is deliberately not modelled: use `nextToken`.
@readonly
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "maxResults", items: "ontologies")
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies", code: 200)
operation ListOntologies {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        @httpQuery("ontology_type")
        ontologyType: OntologyType

        /// Filters the listing to ontologies carrying this domain tag.
        @httpQuery("domain_tag")
        @length(min: 1, max: 256)
        domainTag: String

        /// Filters the listing to the ontology with exactly this canonical IRI.
        @httpQuery("uri")
        uri: OntologyId

        /// Filters the listing to ontologies from this source registry (e.g.
        /// `induced`, `document`), exact match.
        @httpQuery("source_registry")
        @length(min: 1, max: 256)
        sourceRegistry: String

        /// Filters the listing to ontologies with this license tier (e.g.
        /// `restricted`), exact match.
        @httpQuery("license_tier")
        @length(min: 1, max: 256)
        licenseTier: String

        /// Legacy spelling of `maxResults`; `maxResults` wins when both are sent.
        @httpQuery("limit")
        @range(min: 1, max: 1000)
        limit: Integer

        /// Pagination token from a previous response.
        @httpQuery("nextToken")
        nextToken: PaginationToken

        /// Maximum number of ontologies to return in one page (default 50).
        @httpQuery("maxResults")
        @range(min: 1, max: 1000)
        maxResults: Integer
    }

    output := with [PaginatedOutput] {
        /// The ontologies registered in the namespace.
        @required
        ontologies: OntologyRecordList
    }
}

/// Get a single ontology by ID.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}", code: 200)
operation GetOntology {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Identifier of the ontology to fetch.
        @required
        @httpLabel
        ontologyId: OntologyId
    }

    output := {
        /// The requested ontology record.
        @required
        ontology: Document
    }
}

/// Delete an induced ontology and all its artifacts (graph triples,
/// vector embeddings, and registry entry) from a namespace.
///
/// Async — returns **202** immediately: the registry entry is removed
/// synchronously (so ``ListOntologies`` no longer lists it — the client-visible
/// status), then the slower Neptune named-graph DROP and per-embedding AOSS
/// teardown run in the background. Clients poll ``ListOntologies`` until the id
/// is gone. This mirrors the async accept flow and avoids the API Gateway 29s
/// integration timeout (504) on large ontologies.
///
/// The ontology id is a full IRI (contains ``://`` and ``#``), so it is passed
/// as a query parameter rather than a path label — API Gateway mangles a
/// URL-encoded ``#`` in a path segment (falls through to IAM auth → 403). This
/// mirrors the graph vertex-lookup endpoints (``/graph/class?uri=``).
@idempotent
@http(method: "DELETE", uri: "/namespaces/{namespaceId}/ontologies", code: 202)
operation DeleteOntology {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Full IRI of the ontology to delete (passed as a query parameter).
        @required
        @httpQuery("ontology_id")
        ontologyId: OntologyId
    }
}

/// Upload an ontology file (Turtle, RDF/XML, or JSON-LD).
///
/// Not served: the API answers 501 for this path. Uploads go through
/// GetOntologyUploadUrl + IngestOntologyFromS3, which take a `clientToken`;
/// this operation therefore has none.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/upload", code: 200)
operation UploadOntology {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Identifier of the ontology the file belongs to.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Raw ontology file contents (Turtle, RDF/XML, or JSON-LD).
        @required
        @httpPayload
        @length(max: 6000000)
        body: Blob
    }

    output := {
        /// Result of the upload operation.
        @required
        result: Document
    }
}

/// Download an ontology as Turtle.
///
/// Returns 404 when the ontology does not exist or its graph holds no triples
/// and no cached file is available; nothing is written to the artifacts bucket
/// in that case.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/download", code: 200)
operation DownloadOntology {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Identifier of the ontology to download.
        @required
        @httpLabel
        ontologyId: OntologyId
    }

    output := {
        /// Presigned S3 GET URL for the ontology serialized as Turtle. The
        /// ontology is written to the artifacts bucket and served out-of-band
        /// rather than inlined, because a large induced ontology (6+ MB) would
        /// exceed the API Gateway / Lambda response limit and 502 the call.
        @required
        downloadUrl: PresignedUrl

        /// Seconds until the presigned URL expires.
        expiresInSeconds: Integer
    }
}

/// Fetch an ontology from its source URL and ingest it.
///
/// Naturally idempotent, so there is no `clientToken`: it refreshes an ontology
/// that must already be registered under `ontologyId` (404 otherwise), and a
/// repeat re-fetches into the same registry row instead of creating another.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/fetch", code: 200)
operation FetchOntology {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Identifier to register the fetched ontology under.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Source URL to fetch the ontology from. HTTPS only.
        @length(min: 1, max: 2048)
        @pattern("^https://")
        sourceUrl: String
    }

    output := {
        /// Result of the fetch-and-ingest operation.
        @required
        result: Document
    }
}

/// Generate a presigned S3 URL for ontology file upload.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/upload-url", code: 200)
operation GetOntologyUploadUrl {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Name of the file to be uploaded. The server sanitizes it and keeps the
        /// first 200 characters, so the bound is generous: clients derive the
        /// name from the ontology identifier, which may itself be a long IRI.
        @required
        @length(max: 4096)
        filename: String

        /// MIME content type of the file to be uploaded.
        @length(max: 256)
        contentType: String

        /// Identifier to register the uploaded ontology under.
        ontologyId: OntologyId

        /// Human-readable display title for the ontology.
        @length(max: 1024)
        title: String
    }

    output := {
        /// Presigned S3 URL to PUT the file to.
        @required
        uploadUrl: PresignedUrl

        /// S3 object key where the file will be stored.
        @required
        s3Key: String

        /// Identifier assigned to the ontology.
        @required
        ontologyId: String
    }
}

/// Lifecycle states of an async ontology-ingest job.
enum IngestJobState {
    /// The ingest job is queued and has not started yet.
    PENDING = "pending"

    /// The ingest job is currently running.
    RUNNING = "running"

    /// Ingest finished writing; waiting for the just-written embeddings to
    /// become searchable in the (eventually-consistent) vector index before
    /// the job is reported COMPLETED.
    EMBEDDINGS_SYNC = "embeddings_sync"

    /// The ingest job finished successfully.
    COMPLETED = "completed"

    /// The ingest job failed.
    FAILED = "failed"
}

/// Counts produced once an ingest job completes.
structure IngestJobResult {
    /// Identifier of the ingested ontology.
    ontologyId: String

    /// Number of classes ingested.
    classCount: Integer

    /// Number of embeddings generated.
    embeddingCount: Integer
}

/// Async ingest job handle / status — returned by ingest-from-s3 (202) and
/// the ingest-status poll. Typed so FE/BE share one contract.
structure IngestJob {
    /// Identifier of the async ingest job.
    @required
    jobId: String

    /// Identifier of the ontology being ingested.
    @required
    ontologyId: String

    @required
    status: IngestJobState

    /// Error message when the job failed; absent otherwise.
    error: String

    result: IngestJobResult
}

/// Ingest an ontology file from S3 (async — returns 202, poll ingest-status).
///
/// Each call starts a new ingest job; send a `clientToken` to make a retry safe.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/ingest-from-s3", code: 202)
operation IngestOntologyFromS3 {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Identifier to register the ingested ontology under.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// S3 object key of the uploaded ontology file, as returned by
        /// GetOntologyUploadUrl.
        @required
        s3Key: OntologyUploadKey

        /// Serialization format of the file. Inferred from the key's file
        /// extension when omitted.
        format: OntologyFileFormat

        /// Human-readable display title for the ontology.
        @length(max: 1024)
        title: String

        /// Category of the ontology. Defaults to `user_created`.
        ontologyType: OntologyType

        /// Optional idempotency token. A retry with the same token and the same
        /// parameters within 24 hours returns the original result instead of
        /// starting a second ingest job; reusing the token with different
        /// parameters is rejected with a 409.
        @idempotencyToken
        clientToken: ClientToken
    }

    output := {
        @required
        result: IngestJob
    }
}

/// Poll ingest job status.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/ingest-status/{jobId}", code: 200)
operation GetIngestStatus {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Identifier of the ontology whose ingest job is being polled.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Identifier of the ingest job to poll.
        @required
        @httpLabel
        @length(min: 1, max: 128)
        jobId: String
    }

    output := {
        @required
        result: IngestJob
    }
}

// ── Graph ───────────────────────────────────────────────────────────
/// Vertex kind discriminator.
enum GraphVertexKind {
    /// An OWL/RDFS class.
    CLASS = "class"

    /// An object property (relates individuals to individuals).
    OBJECT_PROPERTY = "object-property"

    /// A datatype property (relates individuals to literal values).
    DATATYPE_PROPERTY = "datatype-property"

    /// An annotation property (metadata such as labels or comments).
    ANNOTATION_PROPERTY = "annotation-property"

    /// The ontology header node itself.
    ONTOLOGY = "ontology"

    /// A property of unspecified kind.
    PROPERTY = "property"

    /// A literal value node.
    LITERAL = "literal"

    /// A blank (anonymous) node.
    BLANK_NODE = "blank-node"

    /// A vertex whose kind could not be determined.
    UNKNOWN = "unknown"
}

/// A single result from a graph search query, identifying a matched vertex
/// by its IRI, label, kind, and the named graph it lives in.
structure GraphSearchHit {
    /// IRI of the matched vertex.
    @required
    uri: String

    /// Human-readable label of the matched vertex.
    label: String

    /// Vertex kind (class, object-property, datatype-property, etc.).
    @required
    kind: String

    /// IRIs of the named graphs the vertex is defined in. A class IRI asserted
    /// in more than one ontology (e.g. a shared IRI referenced by both
    /// schema.org and FIBO) lists every source graph, not just one.
    @jsonName("graph_uris")
    graphUris: StringList
}

list GraphSearchHitList {
    member: GraphSearchHit
}

/// A neighboring vertex reached by traversing an edge, identified by its IRI,
/// label, and kind.
structure GraphNeighbor {
    /// IRI of the neighboring vertex.
    @required
    uri: String

    /// Human-readable label of the neighboring vertex.
    label: String

    /// Vertex kind of the neighbor.
    @required
    kind: String
}

/// A relationship edge between two graph vertices, carrying the connecting
/// predicate, its direction, and the neighboring vertex on the other end.
structure GraphEdge {
    /// IRI of the connecting predicate.
    @required
    predicate: String

    /// Human-readable label of the predicate.
    @jsonName("predicate_label")
    predicateLabel: String

    /// Direction of the edge relative to the source vertex (incoming/outgoing).
    @required
    direction: String

    @required
    neighbor: GraphNeighbor
}

list GraphEdgeList {
    member: GraphEdge
}

/// A node in the ontology graph — a class, property, or individual — with its
/// IRI, kind, namespace, associated labels/comments, and outgoing edges.
structure GraphVertex {
    /// IRI of the vertex.
    @required
    uri: String

    /// Vertex kind (class, object-property, datatype-property, etc.).
    @required
    kind: String

    /// Namespace the vertex belongs to.
    @required
    namespace: String

    /// RDF types (rdf:type) declared on the vertex.
    types: StringList

    /// Human-readable labels (rdfs:label) of the vertex.
    labels: StringList

    /// Descriptive comments (rdfs:comment) on the vertex.
    comments: StringList

    /// Alternative labels (skos:altLabel) — carries source synonyms curated
    /// during enrichment and emitted onto the induced class/property.
    @jsonName("alt_labels")
    altLabels: StringList

    /// IRIs of the named graphs the vertex appears in.
    @jsonName("graph_uris")
    graphUris: StringList

    /// Whether this vertex carries the ``coa:isMapped`` marker — i.e. it is
    /// backed by an R2RML mapping and therefore answerable by the structured
    /// Tier-2 (NL→SPARQL / NL→SQL) path. Structured / table-backed classes are
    /// true; unstructured-induced and foundational classes are false (the marker
    /// is absent). Derived from the top-level ``coa:isMapped`` triple and
    /// excluded from ``edges``.
    @jsonName("is_mapped")
    isMapped: Boolean

    /// Previous generations of this vertex's annotations, retired when a
    /// re-induced proposal was accepted into the same ontology. Keys are
    /// ``comments`` / ``definitions`` / ``altLabels`` / ``glossaryTerms`` /
    /// ``tags``; values are the literals
    /// that used to be live — typically the AI-generated text a steward's
    /// curation replaced. Read from the ``coa:superseded*`` history predicates.
    /// History only: NOT live content (serve and embeddings ignore it) and
    /// excluded from ``edges``. Empty when nothing has been superseded.
    superseded: SupersededAnnotations

    /// Outgoing relationship edges from this vertex.
    edges: GraphEdgeList
}

/// Retired annotation literals keyed by kind (``comments`` / ``definitions`` /
/// ``altLabels`` / ``glossaryTerms`` / ``tags``). See ``GraphVertex.superseded``.
map SupersededAnnotations {
    key: String
    value: StringList
}

/// Substring search over entity IRIs and labels in a namespace's graphs.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/search", code: 200)
operation GraphSearch {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Substring search term matched against entity IRIs and labels. An
        /// empty value or `*` lists the namespace's entities; a value over 4000
        /// characters returns 400.
        @required
        @httpQuery("q")
        @length(max: 4000)
        q: String

        @httpQuery("kind")
        kind: GraphVertexKind

        /// Restricts results to the specified ontology's named graph.
        @httpQuery("ontology_id")
        ontologyId: OntologyId

        /// Excludes results from the specified ontology's named graph
        /// (e.g., to filter out governed metrics classes).
        @httpQuery("exclude_ontology_id")
        excludeOntologyId: OntologyId

        /// Maximum number of hits to return (the page size). Bounded because the
        /// value drives the underlying query's LIMIT clause; out-of-range values
        /// are rejected with a 400.
        @httpQuery("limit")
        @range(min: 1, max: 500)
        limit: Integer

        /// Number of leading hits to skip, for pagination. Combined with
        /// ``limit`` this yields a stable page window over the full,
        /// deterministically-ordered result set. Bounded like
        /// GetOntologyOverview's ``offset`` (the class browser pages through
        /// every class of large induced ontologies); out-of-range values are
        /// rejected with a 400.
        @httpQuery("offset")
        @range(min: 0, max: 1000000)
        offset: Integer
    }

    output := {
        /// The matching graph search hits (the requested page window).
        @required
        hits: GraphSearchHitList

        /// Total number of hits matching the query across all pages, so a
        /// client can render a known page count. Independent of ``limit`` /
        /// ``offset``.
        @jsonName("total_count")
        totalCount: Integer
    }
}

/// One RDF statement (triple) in a namespace's named graphs.
structure GraphStatement {
    /// Named graph the statement lives in.
    @required
    graph: String

    /// Subject IRI.
    @required
    subject: String

    /// Predicate IRI.
    @required
    predicate: String

    /// Object term: an IRI, or the lexical form of a literal.
    @required
    object: String
}

list GraphStatementList {
    member: GraphStatement
}

/// Enumerate the statements in a namespace's named graphs.
///
/// Read-only and namespace-scoped: the query only ever sees graphs under the
/// namespace's prefix, and each filter narrows that set (they combine with
/// AND). Subject / predicate are IRIs; object is an IRI when it starts with
/// ``http://``, ``https://`` or ``urn:`` and a literal lexical form otherwise.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/statements", code: 200)
operation ListStatements {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Restrict to one subject IRI.
        @httpQuery("subject")
        subject: VertexIri

        /// Restrict to one predicate IRI.
        @httpQuery("predicate")
        predicate: VertexIri

        /// Restrict to one object: an IRI, or a literal's lexical form.
        @httpQuery("object")
        @length(max: 2048)
        objectValue: String

        /// Restrict to one named graph IRI in the namespace.
        @httpQuery("graph")
        graph: VertexIri

        /// Maximum number of statements to return (the page size).
        @httpQuery("limit")
        @range(min: 1, max: 200)
        limit: Integer

        /// Number of leading statements to skip, for pagination.
        @httpQuery("offset")
        @range(min: 0, max: 1000000)
        offset: Integer
    }

    output := {
        /// The page of matching statements, in the backend's named-graph
        /// index order (stable for a static graph, not a sorted order).
        @required
        statements: GraphStatementList

        /// True when the page was capped at ``limit`` and more statements
        /// exist beyond this window.
        truncated: Boolean
    }
}

/// Discover what the canvas can render, and its hard limits.
///
/// The canvas reads this before requesting a subgraph so it can disable the
/// controls the backend cannot honour and label a capped result honestly,
/// instead of guessing the limits on the client.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/canvas/manifest", code: 200)
operation GetCanvasManifest {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid
    }

    output := {
        /// Capabilities the canvas may rely on (e.g. ``nodeKinds``,
        /// ``graphFilter``, ``cursorPaging``). Clients must ignore values
        /// they do not recognise, so a capability can be added without
        /// breaking older frontends.
        @required
        capabilities: CanvasCapabilityList

        /// Hard limits enforced by the backend.
        @required
        limits: CanvasLimits
    }
}

list CanvasCapabilityList {
    member: String
}

/// Hard ceilings the canvas subgraph endpoint enforces. Published so the UI
/// stops paging at the boundary instead of learning it from a 400.
structure CanvasLimits {
    /// Maximum nodes returned by one canvas subgraph page.
    @required
    maxNodes: Integer

    /// Maximum edges returned alongside those nodes.
    @required
    maxEdges: Integer

    /// Maximum page size accepted by ``maxResults``.
    @required
    maxPageSize: Integer
}

/// One page of canvas nodes and edges, optionally filtered.
///
/// Unlike the vertex lookup, this does not start from a single IRI: it scans
/// the namespace's named graphs in backend index order and shapes the triples
/// into drawable nodes and edges. Paging is offset-based; pass the previous
/// page's ``nextOffset`` back to continue. ``truncated`` says whether another
/// page exists, so the UI can stop without guessing.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/canvas", code: 200)
operation GetCanvasSubgraph {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Comma-separated node kinds to keep: ``class``,
        /// ``object-property``, ``datatype-property``. Omit for every kind.
        @httpQuery("kinds")
        @length(max: 120)
        kinds: String

        /// Only read triples from this named graph (an IRI inside the
        /// namespace). Omit to read every graph in the namespace.
        @httpQuery("graph")
        @length(max: 2048)
        graph: String

        /// Page size. The manifest's ``maxPageSize`` is the ceiling.
        @httpQuery("limit")
        @range(min: 1, max: 100)
        limit: Integer

        /// Backend index offset. Pass the previous page's ``nextOffset``.
        @httpQuery("offset")
        @range(min: 0, max: 1000000)
        offset: Integer
    }

    output := {
        /// Nodes touched by this page's triples.
        @required
        nodes: CanvasNodeList

        /// Edges whose object is an IRI (literals are kept as node labels,
        /// never drawn as edges).
        @required
        edges: CanvasEdgeList

        /// True when another page exists beyond this window.
        @required
        truncated: Boolean

        /// Number of nodes in this page (not the whole graph).
        @required
        nodeCount: Integer

        /// Number of edges in this page (not the whole graph).
        @required
        edgeCount: Integer

        /// Offset of the next page; present only when ``truncated`` is true.
        nextOffset: Integer
    }
}

/// A drawable node: an IRI with an optional label and coarse kind.
structure CanvasNode {
    /// Full IRI of the node.
    @required
    uri: String

    /// ``rdfs:label`` when one appears in the scanned page.
    label: String

    /// ``class``, ``object-property``, ``datatype-property``, or ``resource``
    /// when the page's ``rdf:type`` triple does not name one of those.
    kind: String
}

list CanvasNodeList {
    member: CanvasNode
}

/// A drawable edge. ``direction`` is ``outgoing`` for canvas pages and may be
/// ``incoming`` on a path, where an edge is traversed against its assertion.
structure CanvasEdge {
    /// Subject IRI.
    @required
    source: String

    /// Predicate IRI.
    @required
    predicate: String

    /// Local name of the predicate, for display.
    predicateLabel: String

    /// Object IRI.
    @required
    target: String

    /// Named graph the triple lives in.
    graph: String

    /// ``outgoing`` or ``incoming``.
    direction: String
}

list CanvasEdgeList {
    member: CanvasEdge
}

/// Find simple paths between two IRIs, up to a bounded hop count.
///
/// Read-only: the graph is never written. ``maxHops`` and ``limit`` are
/// clamped by the backend's published canvas limits; when the enumeration
/// hits the cap, ``truncated`` says so rather than silently returning a
/// partial answer as if it were complete.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/path", code: 200)
operation FindGraphPath {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// IRI to start from.
        @required
        @httpQuery("start")
        @length(max: 2048)
        start: String

        /// IRI to reach.
        @required
        @httpQuery("end")
        @length(max: 2048)
        end: String

        /// Maximum edges in a path (1–6).
        @httpQuery("max_hops")
        @range(min: 1, max: 6)
        maxHops: Integer

        /// Maximum number of paths returned (1–20).
        @httpQuery("limit")
        @range(min: 1, max: 20)
        limit: Integer
    }

    output := {
        /// Shortest paths first; each carries the nodes and edges to draw it.
        @required
        paths: GraphPathList

        /// True when more paths exist than ``limit`` (or the search cap hit).
        @required
        truncated: Boolean
    }
}

/// One simple path: no node repeats, ``hops == edges.size()``.
structure GraphPath {
    /// Nodes visited by the path, in traversal order.
    @required
    nodes: CanvasNodeList

    /// Edges followed, one per hop; direction records assertion vs traversal.
    @required
    edges: CanvasEdgeList

    /// Number of edges in the path.
    @required
    hops: Integer
}

list GraphPathList {
    member: GraphPath
}

/// Read-only T-Box/A-Box coverage for the health board.
///
/// Counts are SPARQL aggregations over the namespace's named graphs: the
/// T-Box is every ``owl:Class``/``owl:*Property`` declared in any of them,
/// the A-Box is every distinct subject typed by one of those classes. Classes
/// with zero instances are real gaps here, not hidden by a synthetic sample.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/snapshot", code: 200)
operation GetOntologySnapshot {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid
    }

    output := {
        /// Declared schema objects.
        @required
        tbox: OntologySnapshotTbox

        /// Asserted data using that schema.
        @required
        abox: OntologySnapshotAbox

        /// How much of the schema the data actually uses.
        @required
        coverage: OntologyCoverage

        /// Named graphs in this namespace, so the diff form can offer real choices.
        @required
        graphs: GraphUriList

        /// Human-readable provenance for the numbers above.
        @required
        source: String

        /// When the aggregation ran (ISO-8601).
        @required
        sampledAt: String
    }
}

/// Counts of declared schema objects (the T-Box).
structure OntologySnapshotTbox {
    /// Distinct ``owl:Class`` IRIs.
    @required
    classes: Integer

    /// Distinct ``owl:ObjectProperty`` IRIs.
    @required
    objectProperties: Integer

    /// Distinct ``owl:DatatypeProperty`` IRIs.
    @required
    datatypeProperties: Integer
}

/// Counts of asserted instances (the A-Box).
structure OntologySnapshotAbox {
    /// Distinct subjects typed by a class declared in this namespace.
    @required
    instances: Integer

    /// Distinct declared classes that carry at least one instance.
    @required
    classesWithInstances: Integer
}

/// The share of declared classes that the data actually uses.
structure OntologyCoverage {
    /// ``classesWithInstances / tbox.classes`` in 0..1; 0 when no class is declared.
    @required
    classCoverage: Double

    /// Declared classes without ``rdfs:label`` or ``skos:prefLabel``.
    @required
    unlabeledClasses: Integer
}

/// A list of named graph IRIs.
list GraphUriList {
    member: String
}

/// Run the read-only quality checks the health board reports.
///
/// Despite the verb, nothing is written: the operation measures orphan
/// instances, unlabeled classes and SHACL conformance. Checks that cannot
/// run (no shapes, no reasoner) report a null count with a ``detail`` —
/// never a fabricated zero.
@http(method: "POST", uri: "/namespaces/{namespaceId}/graph/validate", code: 200)
operation RunValidation {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid
    }

    output := {
        /// Instances with no properties beyond ``rdf:type``/``rdfs:label``
        /// and no inbound references.
        @required
        orphanInstances: QualityCount

        /// Declared classes without any label.
        @required
        unlabeledClasses: QualityCount

        /// SHACL gate result, or an explicit "skipped" when no shapes exist.
        @required
        shacl: ShaclReport

        /// Failed inference jobs; null when this service cannot observe them.
        @required
        inferenceFailures: QualityCount

        /// Human-readable provenance for the checks above.
        @required
        source: String

        /// When the checks ran (ISO-8601).
        @required
        sampledAt: String
    }
}

/// A measured count that may be unavailable.
structure QualityCount {
    /// The measured count, or null when the check could not run.
    count: Integer

    /// How the count was measured, or why it is null.
    detail: String
}

/// Outcome of the SHACL gate.
structure ShaclReport {
    /// One of ``ok``, ``violations``, ``skipped``, ``error``.
    @required
    status: String

    /// Number of violations; null when the gate did not run.
    violations: Integer

    /// True only when the gate ran and produced no violations.
    conforms: Boolean

    /// Reason the gate was skipped or errored.
    detail: String
}

/// Report whether an inference engine is wired up and how its last job went.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/reasoning", code: 200)
operation GetReasoningStatus {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid
    }

    output := {
        /// True only when this deployment has a reasoner configured.
        @required
        available: Boolean

        /// Reasoner identifier (for example ``elk``); null when none is configured.
        engine: String

        /// Failed materialization jobs; null when not observable from here.
        failures: QualityCount

        /// Human-readable explanation of the state above.
        detail: String

        /// Where this status came from.
        @required
        source: String

        /// When the status was sampled (ISO-8601).
        @required
        sampledAt: String

        /// Triples the recorded pointer holds; null until the first run.
        inferredTriples: Integer

        /// Last materialization job, with its per-stage results. Null before
        /// the first run.
        lastJob: ReasoningJobSummary
    }
}

/// What the last materialization job left behind.
structure ReasoningJobSummary {
    /// Row identifier in `platform.reasoning_job`.
    @required
    jobId: String

    /// `queued`, `running`, `succeeded`, `skipped`, `failed` or `canceled`.
    @required
    state: String

    /// Triples the run added.
    inferred: Integer

    /// Consistency verdict; false fails the run.
    consistent: Boolean

    /// When the run finished (ISO-8601).
    finishedAt: String

    /// True when the run short-circuited because the inputs were unchanged.
    skipped: Boolean

    /// Per-stage results, empty when nothing ran.
    stages: ReasoningStages
}

/// One stage of a materialization run. Only the members the stage produces
/// are set: `rdfs`/`owl` report triples added, `shacl` reports the gate.
structure ReasoningStage {
    /// Triples this stage added to the inferred graph.
    triples: Integer

    /// True when the SHACL gate ran and found no violations.
    conforms: Boolean

    /// Violations found by the SHACL gate.
    violations: Integer

    /// Wall time for this stage.
    ms: Integer
}

/// Stages of a materialization run, in execution order.
structure ReasoningStages {
    /// RDFS closure (Jena `riot --rdfs`); skipped in `rdfs`-only mode.
    rdfs: ReasoningStage

    /// OWL EL materialization (ROBOT + ELK); absent in `rdfs`-only mode.
    owl: ReasoningStage

    /// SHACL gate; runs before any write, so a violation leaves the target
    /// graph untouched.
    shacl: ReasoningStage
}

/// Run inference over the published T-Box plus this namespace's A-Box graphs
/// and replace the inferred graph for the published version.
///
/// The call is synchronous and can take a minute on a large A-Box. A second
/// concurrent call for the same target answers 409. When the inputs hash the
/// same as the recorded pointer and the target graph still holds exactly that
/// many triples, the run is reported as `skipped` without writing.
///
/// The reported `inferred` count is what this run added; it is not the size
/// of the inferred graph.
@http(method: "POST", uri: "/namespaces/{namespaceId}/graph/reasoning/materialize", code: 200)
@examples([
    {
        title: "Materialize with the default profile"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11" }
        output: {
            jobId: "rsn-1a2b3c4d5e6f"
            mode: "materialize"
            profile: "EL"
            ontologyVersion: "ont-7c6971e77b7d"
            targetGraph: "urn:platform:inferred:ont-7c6971e77b7d"
            inferred: 91052
            skipped: false
            consistent: true
            inputHash: "7ef8727158b43f4ae92054670a79a28aa8c3199f877d11f0a07679f83b6196de"
            ms: 72891
            stages: {
                rdfs: { triples: 53366, ms: 17342 }
                owl: { triples: 37686, ms: 26234 }
                shacl: { conforms: true, violations: 0, ms: 22484 }
            }
            warnings: []
        }
    }
])
operation MaterializeReasoning {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// `EL` (default) or `OWL2EL`.
        @length(min: 1, max: 32)
        profile: String

        /// Re-run even when the inputs are unchanged.
        force: Boolean

        /// A-Box graphs to reason over. Every IRI must be a `urn:platform:`
        /// graph, so a namespace cannot read another namespace's graph. When
        /// omitted the deployment's configured A-Box graphs are used.
        @length(max: 64)
        aboxGraphs: PlatformGraphIriList
    }

    output := {
        /// Identifier of the row in `platform.reasoning_job`.
        @required
        jobId: String

        /// `materialize` or `rdfs`.
        @required
        mode: String

        /// Reasoning profile that was used.
        @required
        profile: String

        /// Published ontology version the run read.
        @required
        ontologyVersion: String

        /// Graph the run would replace (and did replace unless skipped).
        @required
        targetGraph: String

        /// Triples this run added; 0 when skipped.
        @required
        inferred: Integer

        /// True when the inputs were unchanged and nothing was written.
        @required
        skipped: Boolean

        /// Consistency verdict from the reasoner. False fails the job and
        /// leaves the target graph untouched.
        @required
        consistent: Boolean

        /// Hash of (T-Box, A-Box, profile, mode) used to decide `skipped`.
        inputHash: String

        /// Wall time of the run.
        @required
        ms: Integer

        /// Per-stage results, in execution order.
        @required
        stages: ReasoningStages

        /// Non-fatal notes, for example axioms the EL profile ignores.
        @required
        warnings: StringList
    }

    errors: [
        ConflictError
        NotFoundError
    ]
}

/// Compare two named graphs in the same namespace, read-only.
///
/// ``from`` is the baseline and ``to`` the target; added means present in
/// ``to`` and absent from ``from``. Both IRIs must belong to this namespace,
/// so an arbitrary graph cannot be read through the diff.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/diff", code: 200)
operation GetOntologyDiff {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Baseline named graph IRI, inside this namespace.
        @required
        @httpQuery("from")
        @length(max: 2048)
        fromGraph: String

        /// Target named graph IRI, inside this namespace.
        @required
        @httpQuery("to")
        @length(max: 2048)
        toGraph: String

        /// Maximum sample rows per side (1–200).
        @httpQuery("limit")
        @range(min: 1, max: 200)
        limit: Integer
    }

    output := {
        /// Baseline graph that was compared.
        @required
        baselineGraph: String

        /// Target graph that was compared.
        @required
        targetGraph: String

        /// Triple and schema deltas.
        @required
        counts: OntologyDiffCounts

        /// Class IRIs only in the target (sample).
        @required
        addedClasses: OntologyDiffStringList

        /// Class IRIs only in the baseline (sample).
        @required
        removedClasses: OntologyDiffStringList

        /// Property IRIs only in the target (sample).
        @required
        addedProperties: OntologyDiffStringList

        /// Property IRIs only in the baseline (sample).
        @required
        removedProperties: OntologyDiffStringList

        /// Sample triples behind the counts.
        @required
        examples: OntologyDiffExamples

        /// True when a sample list or example set was cut at ``limit``.
        @required
        truncated: Boolean

        /// Human-readable provenance for the diff.
        @required
        source: String

        /// When the diff ran (ISO-8601).
        @required
        sampledAt: String
    }
}

/// Triple and schema delta counts.
structure OntologyDiffCounts {
    /// Triples present in the target and absent from the baseline.
    @required
    addedTriples: Integer

    /// Triples present in the baseline and absent from the target.
    @required
    removedTriples: Integer

    /// Classes added.
    @required
    addedClasses: Integer

    /// Classes removed.
    @required
    removedClasses: Integer

    /// Properties added (object or datatype).
    @required
    addedProperties: Integer

    /// Properties removed.
    @required
    removedProperties: Integer
}

/// Sample triples for each side of the diff.
structure OntologyDiffExamples {
    /// Sample of added triples.
    @required
    addedTriples: TripleExampleList

    /// Sample of removed triples.
    @required
    removedTriples: TripleExampleList
}

/// One sampled triple.
structure TripleExample {
    /// Subject IRI.
    @required
    subject: String

    /// Predicate IRI.
    @required
    predicate: String

    /// Object IRI or lexical literal form.
    @required
    object: String
}

/// A list of sampled triples.
list TripleExampleList {
    member: TripleExample
}

/// A list of IRIs or short strings.
list OntologyDiffStringList {
    member: String
}

/// Look up a class vertex by IRI.
///
/// The IRI is passed as a query parameter (``?uri=…``) rather than a
/// path label to avoid double-encoding issues with slashes and hash
/// fragments common in OWL IRIs (e.g. ``http://example.org/ont#Foo``).
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/class", code: 200)
operation GetGraphClass {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// IRI of the class vertex to look up.
        @required
        @httpQuery("uri")
        uri: VertexIri
    }

    output: GraphVertex

    errors: [
        NotFoundError
        ValidationError
    ]
}

/// Look up an object-property vertex by IRI (query param).
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/object-property", code: 200)
operation GetGraphObjectProperty {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// IRI of the object-property vertex to look up.
        @required
        @httpQuery("uri")
        uri: VertexIri
    }

    output: GraphVertex

    errors: [
        NotFoundError
        ValidationError
    ]
}

/// Look up a datatype-property vertex by IRI (query param).
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/datatype-property", code: 200)
operation GetGraphDatatypeProperty {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// IRI of the datatype-property vertex to look up.
        @required
        @httpQuery("uri")
        uri: VertexIri
    }

    output: GraphVertex

    errors: [
        NotFoundError
        ValidationError
    ]
}

// ── Ontology overview ───────────────────────────────────────────────
/// One class persisted in an ontology's named graph.
structure OntologyClassSummary {
    /// IRI of the class.
    @required
    uri: String

    /// Human-readable label (rdfs:label) of the class.
    label: String

    /// Descriptive comment (rdfs:comment) on the class.
    comment: String

    /// IRI of the previously-loaded class this class was grounded to
    /// (coa:groundedTo / skos:exactMatch / skos:closeMatch). Absent when the
    /// class is novel (net-new this induction).
    groundedTo: String

    /// "exact" or "close" when grounded via a SKOS mapping; otherwise absent.
    matchType: String

    /// IRIs of this class's direct super-classes (``rdfs:subClassOf``). Lets a
    /// caller reconstruct the taxonomy (roots + parent/child edges) from the
    /// overview alone, without an N-per-class vertex fan-out. Empty/absent for
    /// a top-level class with no loaded parent.
    subClassOf: StringList
}

list OntologyClassSummaryList {
    member: OntologyClassSummary
}

/// One property persisted in an ontology's named graph. Object properties
/// carry a class IRI in ``range`` (a relationship); datatype properties carry
/// a datatype IRI (e.g. xsd:string).
structure OntologyPropertySummary {
    /// IRI of the property.
    @required
    uri: String

    /// Human-readable label (rdfs:label) of the property.
    label: String

    /// IRI of the property's domain class.
    domain: String

    /// IRI of the property's range (a class IRI for object properties, a
    /// datatype IRI for datatype properties).
    range: String
}

list OntologyPropertySummaryList {
    member: OntologyPropertySummary
}

/// Everything persisted in one ontology's named graph, grouped for display.
/// Read from the graph store (not the registry), so it reflects the triples
/// that actually landed in the knowledge graph.
structure OntologyOverview {
    /// Identifier of the ontology.
    @required
    ontologyId: String

    /// Namespace the ontology belongs to.
    @required
    namespace: String

    /// IRI of the named graph holding the ontology's triples.
    graphUri: String

    /// Classes persisted in the ontology's named graph.
    classes: OntologyClassSummaryList

    /// Object properties — relationships between classes (domain → range class).
    objectProperties: OntologyPropertySummaryList

    /// Datatype properties — attributes of a class with a literal range.
    datatypeProperties: OntologyPropertySummaryList

    /// Total number of classes in the ontology (independent of limit/offset),
    /// so a client can show the true count while rendering one page.
    totalClasses: Integer

    /// Total number of object properties in the ontology (independent of limit/offset).
    totalObjectProperties: Integer

    /// Total number of datatype properties in the ontology (independent of limit/offset).
    totalDatatypeProperties: Integer
}

/// Enumerate the classes + properties persisted in one ontology's graph.
///
/// Reads the ontology's named graph directly, returning its classes,
/// object properties (relationships), and datatype properties. Used by the
/// web UI's induced-ontology detail view.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/ontology-overview", code: 200)
operation GetOntologyOverview {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Identifier of the ontology to summarize.
        @required
        @httpQuery("ontology_id")
        ontologyId: OntologyId

        /// Max entities to return per collection (classes, object properties,
        /// datatype properties are each capped independently). Bounds the
        /// response so a large ontology does not exceed the API Gateway / Lambda
        /// response limit. Omit for the server default.
        @httpQuery("limit")
        @range(min: 1, max: 10000)
        limit: Integer

        /// Zero-based offset into each collection, for paging. Combined with
        /// ``limit`` this yields a stable page window over the full ontology.
        @httpQuery("offset")
        @range(min: 0, max: 1000000)
        offset: Integer

        /// When true, return a bounded taxonomy seed instead of the full
        /// ontology: a few root classes with the largest subtrees plus a capped
        /// set of their descendants, and no properties. For a first render of a
        /// very large ontology; the rest loads on demand.
        @httpQuery("sample")
        sample: Boolean
    }

    output: OntologyOverview

    errors: [
        ValidationError
    ]
}
