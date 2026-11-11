// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// A-Box browse reads used by the metric card and entity pages.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.4 rows F43-F47 and F92, and
// doc/coa-x/18-platform-core拆解.md §KERNEL browse routes. These are the
// kernel's cheap catalogue reads; they intentionally do not need an
// ontology-engine hop.
//
// These two operations stay on `ControlPlaneService` next to `FindLinks`,
// `FindGraphPath`, `GetCanvasSubgraph` and `GetCanvasManifest`. They are not
// the same capability as P15's `FindLinks`: that op expands neighbours of one
// IRI (nodes/edges/truncated), while `BrowseOntologyTree` returns the class
// hierarchy and `ListOntologyInstances` returns the instances of one class.
// None of them takes `entityUri`; the instance filter is the class IRI on the
// `class` query parameter.
$version: "2"

namespace com.amazon.semanticcontext.browse

use com.amazon.semanticcontext.common#StringList
use com.amazon.semanticcontext.ontologylifecycle#OntologyPointer

/// IRI of an ontology class, as passed on the `class` query parameter.
@length(min: 1, max: 2048)
string BrowseClassIri

/// One ontology class in the browse tree.
structure OntologyClassRef {
    /// Class IRI.
    @required
    iri: String

    /// Display label; the local name when the T-Box has no label.
    @required
    label: String

    /// Superclass IRIs; empty for a root class.
    @length(min: 0, max: 200)
    parents: StringList
}

/// One class node of the nested tree.
structure OntologyTreeNode {
    /// Class IRI.
    @required
    iri: String

    /// Display label.
    @required
    label: String

    /// Superclass IRIs; empty for a root class.
    @length(min: 0, max: 200)
    parents: StringList

    /// Child nodes, sorted by label.
    @length(min: 0, max: 5000)
    children: OntologyTreeNodeList
}

/// One property in the flat property list.
structure OntologyPropertyRef {
    /// Property IRI.
    @required
    iri: String

    /// Display label.
    @required
    label: String

    /// `ObjectProperty`, `DatatypeProperty`, or `AnnotationProperty`.
    @required
    kind: String
}

/// Counts returned with the tree.
structure OntologyBrowseCounts {
    /// Number of classes in the published T-Box.
    @required
    classes: Integer

    /// Number of properties in the published T-Box.
    @required
    properties: Integer
}

/// Class hierarchy, flat class list and property list of the current T-Box.
///
/// When nothing is published the server returns an empty `tree`, empty
/// `classes`/`properties`, zero counts and no `pointer`; it does not raise
/// `NotFoundError`.
structure OntologyTreeResult {
    /// Current pointer; absent when nothing is published.
    pointer: OntologyPointer

    /// Nested class tree, roots sorted by label.
    @required
    tree: OntologyTreeNodeList

    /// Flat class list, sorted by label.
    @required
    classes: OntologyClassRefList

    /// Flat property list, sorted by label.
    @required
    properties: OntologyPropertyRefList

    /// Counts for both flat lists.
    @required
    counts: OntologyBrowseCounts
}

/// One instance of a class.
structure OntologyInstanceRef {
    /// Instance IRI.
    @required
    iri: String

    /// Display label; the local name when the instance has no label.
    @required
    label: String

    /// Graph the instance was found in.
    @required
    graph: String
}

/// Instances of one class.
///
/// An unknown class, or an empty current graph, returns `items: []`,
/// `total: 0` and no `pointer`; it is an empty result, not an error.
structure OntologyInstanceList {
    /// Class IRI that was queried.
    @required
    class: String

    /// Instances in T-Box order, capped by `limit`.
    @required
    items: OntologyInstanceRefList

    /// Total instances of the class, before `limit` was applied.
    @required
    total: Integer

    /// Page size that was applied (server default 20).
    @required
    limit: Integer

    /// Offset that was applied (server default 0).
    @required
    offset: Integer

    /// Current pointer; absent when nothing is published.
    pointer: OntologyPointer
}

/// Flat class list in a browse response.
list OntologyClassRefList {
    member: OntologyClassRef
}

/// Nested class tree in a browse response.
list OntologyTreeNodeList {
    member: OntologyTreeNode
}

/// Flat property list in a browse response.
list OntologyPropertyRefList {
    member: OntologyPropertyRef
}

/// Instance list in a browse response.
list OntologyInstanceRefList {
    member: OntologyInstanceRef
}

/// Read the class hierarchy, flat class list and property list.
@readonly
@http(method: "GET", uri: "/browse/ontology/tree", code: 200)
@examples([
    {
        title: "Read the published class tree"
        output: {
            pointer: { name: "tbox/current", versionId: "ont-1a2b3c4d5e6f", semver: "1.0.0", graph: "urn:platform:graph:tbox:1a2b3c4d", updatedAt: "2026-10-02T09:30:00Z" }
            tree: [
                {
                    iri: "urn:coa:class:BusinessEntity"
                    label: "Business Entity"
                    parents: []
                    children: [
                        {
                            iri: "urn:coa:class:Contract"
                            label: "Contract"
                            parents: ["urn:coa:class:BusinessEntity"]
                            children: []
                        }
                    ]
                }
            ]
            classes: [
                {
                    iri: "urn:coa:class:BusinessEntity"
                    label: "Business Entity"
                    parents: []
                }
                {
                    iri: "urn:coa:class:Contract"
                    label: "Contract"
                    parents: ["urn:coa:class:BusinessEntity"]
                }
            ]
            properties: [
                {
                    iri: "urn:coa:property:belongs-to"
                    label: "belongs to"
                    kind: "ObjectProperty"
                }
            ]
            counts: { classes: 2, properties: 1 }
        }
    }
])
operation BrowseOntologyTree {
    output: OntologyTreeResult
}

/// List instances of one ontology class.
///
/// `limit` caps the returned page; `total` still reports the full instance
/// count so the caller can show "N of M".
@readonly
@http(method: "GET", uri: "/browse/ontology/instances", code: 200)
@examples([
    {
        title: "List instances of a class"
        input: { classIri: "urn:coa:class:BusinessEntity", limit: 5 }
        output: {
            class: "urn:coa:class:BusinessEntity"
            items: [
                {
                    iri: "urn:coa:entity:contract-ledger"
                    label: "Contract Ledger"
                    graph: "urn:platform:graph:abox"
                }
            ]
            total: 12
            limit: 5
            offset: 0
        }
    }
])
operation ListOntologyInstances {
    input := {
        /// Class whose instances are listed.
        @required
        @httpQuery("class")
        classIri: BrowseClassIri

        /// Maximum instances to return (1-100); server default 20.
        @httpQuery("limit")
        @range(min: 1, max: 100)
        limit: Integer

        /// Instances to skip (0 or greater); server default 0.
        @httpQuery("offset")
        @range(min: 0, max: 2147483647)
        offset: Integer
    }

    output: OntologyInstanceList
}
