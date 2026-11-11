// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// FindLinks — bounded neighbourhood ("Links" tab) for the ontology graph.
//
// WHY THIS FILE IS SEPARATE
// -------------------------
// This operation was authored on its own branch while the shared graph model
// was under concurrent edit. It deliberately does NOT touch control-plane.smithy
// or ontology-graph.smithy. When merging, make exactly these two additions to
// models/src/main/smithy/control-plane.smithy (copy the lines verbatim):
//
//   1) In the `use` block, between the FindGraphPath and GetCanvasManifest
//      imports, add:
//
//          use com.amazon.semanticcontext.ontologygraph#FindLinks
//
//   2) In `service ControlPlaneService { operations: [ ... ] }`, immediately
//      after the `FindGraphPath` entry, add:
//
//          FindLinks
//
// Until step 1+2 land, the operation is defined but not bound to the service,
// so no route is generated. Nothing else in this file needs to change.
//
// SETTLED DECISIONS (do not re-litigate on merge)
// -----------------------------------------------
// 1) Service: ControlPlaneService, NOT DataLayerService. FindLinks belongs to
//    the same family as FindGraphPath / GetCanvasSubgraph / GetCanvasManifest,
//    which already live in ControlPlaneService; the older note in
//    doc/coa-x/09-platform整合评估.md that filed it under DataLayerService is
//    superseded.
// 2) Input name: `uri`, not `entityUri` (same document, older draft).
// 3) "No neighbours" is a successful empty answer: nodes: [], edges: [],
//    truncated: false. Do NOT model or return a 404 / NotFoundError for a
//    well-formed IRI with no adjacency.
$version: "2"

namespace com.amazon.semanticcontext.ontologygraph

use com.amazon.semanticcontext.common#Uuid

/// Direction in which a neighbourhood expands from the seed IRI.
enum LinkDirection {
    /// Follow subject -> object edges out of the seed IRI.
    OUTGOING = "outgoing"

    /// Follow object -> subject edges into the seed IRI.
    INCOMING = "incoming"

    /// Follow edges in both directions.
    BOTH = "both"
}

/// One neighbour reached from the seed IRI.
structure GraphLinkNode {
    /// Full IRI of the neighbour.
    @required
    uri: String

    /// ``rdfs:label`` when the namespace carries one.
    label: String

    /// ``class``, ``object-property``, ``datatype-property`` or ``resource``.
    kind: String

    /// Shortest hop distance from the seed IRI (1–3).
    @required
    hops: Integer
}

/// One adjacency edge, tagged with the hop that discovered it.
structure GraphLinkEdge {
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

    /// How expansion traversed the edge: ``outgoing`` or ``incoming``.
    direction: String

    /// Hop at which expansion discovered this edge (1–3).
    @required
    hops: Integer
}

/// Neighbours reached within the hop limit, one entry per node.
list GraphLinkNodeList {
    member: GraphLinkNode
}

/// Adjacency edges within the hop limit, deduplicated across named graphs.
list GraphLinkEdgeList {
    member: GraphLinkEdge
}

/// The bounded neighbourhood around one IRI, up to three hops away.
///
/// Read-only: the graph is never written. Nodes and edges both carry the hop
/// that reached them, so a caller can group by distance and verify the cap.
/// ``maxHops`` above the contractual 3 is rejected by the backend rather than
/// clamped, and a seed with no adjacency returns empty lists — an empty
/// neighbourhood is a valid answer, not an error. When ``limit`` cuts the
/// answer, ``truncated`` says so instead of returning a partial result that
/// looks complete.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/graph/links", code: 200)
operation FindLinks {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// IRI to expand from.
        @required
        @httpQuery("uri")
        @length(max: 2048)
        uri: String

        /// Direction to expand; defaults to ``both``.
        @httpQuery("direction")
        direction: LinkDirection

        /// Maximum hops to expand (1–3); defaults to 3.
        @httpQuery("max_hops")
        @range(min: 1, max: 3)
        maxHops: Integer

        /// Maximum edges returned (1–500); defaults to 200.
        @httpQuery("limit")
        @range(min: 1, max: 500)
        limit: Integer
    }

    output := {
        /// Neighbours within the hop limit, nearest first; the seed is omitted.
        @required
        nodes: GraphLinkNodeList

        /// Adjacency edges within the hop limit, deduplicated by triple + graph.
        @required
        edges: GraphLinkEdgeList

        /// True when the edge limit ended the expansion before it was complete.
        @required
        truncated: Boolean
    }
}

apply FindLinks @examples([
    {
        title: "Two-hop neighbourhood around a class"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", uri: "http://example.com/onto#Claim", direction: "both", maxHops: 2, limit: 10 }
        output: {
            nodes: [
                {
                    uri: "http://example.com/onto#Policy"
                    label: "Policy"
                    kind: "class"
                    hops: 1
                }
                {
                    uri: "http://example.com/onto#Customer"
                    label: "Customer"
                    kind: "class"
                    hops: 2
                }
            ]
            edges: [
                {
                    source: "http://example.com/onto#Claim"
                    predicate: "http://www.w3.org/2000/01/rdf-schema#subClassOf"
                    predicateLabel: "subClassOf"
                    target: "http://example.com/onto#Policy"
                    graph: "https://coa.local/graph/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d/http%3A%2F%2Fexample.com%2Fonto"
                    direction: "outgoing"
                    hops: 1
                }
                {
                    source: "http://example.com/onto#Policy"
                    predicate: "http://example.com/onto#heldBy"
                    predicateLabel: "heldBy"
                    target: "http://example.com/onto#Customer"
                    graph: "https://coa.local/graph/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d/http%3A%2F%2Fexample.com%2Fonto"
                    direction: "outgoing"
                    hops: 2
                }
            ]
            truncated: false
        }
    }
    {
        title: "An IRI with no adjacency is an empty, successful answer"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", uri: "http://example.com/onto#UnusedClass", maxHops: 3 }
        output: {
            nodes: []
            edges: []
            truncated: false
        }
    }
])
