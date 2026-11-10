// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// A-Box entity reads served by the local bridge.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.4 rows F90-F98, F101-F102, F143,
// and doc/coa-x/18-platform-core拆解.md §KERNEL entity routes. Both reads are
// namespace-independent: the entity IRI carries its own identity, matching the
// contract paths `GET /entities/{iri}` and `GET /entities/{iri}/provenance`.
$version: "2"

namespace com.amazon.semanticcontext.entity

use com.amazon.semanticcontext.common#NotFoundError

/// Percent-encoded IRI of an A-Box entity.
@length(min: 1, max: 2048)
string EntityRef

/// One RDF term: IRI or literal (with optional datatype and language).
structure EntityTerm {
    /// `iri` or `literal`.
    @required
    kind: String

    /// Lexical value of the term.
    @required
    value: String

    /// IRI form; present when `kind` is `iri`.
    iri: String

    /// Datatype IRI for typed literals.
    datatype: String

    /// BCP-47 language tag for language-tagged literals.
    lang: String
}

list EntityTermList {
    member: EntityTerm
}

/// One node in the immediate neighbourhood.
structure EntityNode {
    /// Node IRI.
    @required
    iri: String

    /// Display label; falls back to the local name when unlabeled.
    @required
    label: String

    /// True when the node exists only in the inferred graph.
    @required
    inferred: Boolean
}

list EntityNodeList {
    member: EntityNode
}

/// One edge in the immediate neighbourhood.
structure EntityEdge {
    /// Subject IRI.
    @required
    s: String

    /// Predicate IRI.
    @required
    p: String

    /// Object IRI or lexical value.
    @required
    o: String

    /// Named graph the edge came from.
    @required
    graph: String

    /// True when the edge exists only in the inferred graph.
    @required
    inferred: Boolean
}

list EntityEdgeList {
    member: EntityEdge
}

/// Immediate neighbourhood of an entity.
structure EntityNeighbors {
    /// Neighbour nodes.
    @required
    nodes: EntityNodeList

    /// Edges connecting them.
    @required
    edges: EntityEdgeList

    /// True when the neighbourhood was capped by the request limit.
    @required
    truncated: Boolean
}

/// One superclass link in a class chain.
structure EntityClassLink {
    /// Class IRI.
    @required
    iri: String

    /// Class label.
    @required
    label: String
}

list EntityClassLinkList {
    member: EntityClassLink
}

/// One class asserted or inferred for the entity.
structure EntityClass {
    /// Class IRI.
    @required
    iri: String

    /// Class label.
    @required
    label: String

    /// True when the class has a label in the T-Box.
    @required
    labeled: Boolean

    /// True when the membership exists only in the inferred graph.
    @required
    inferredOnly: Boolean

    /// Number of instances of this class.
    @required
    instanceCount: Integer

    /// Superclass chain, nearest first.
    @required
    chain: EntityClassLinkList
}

list EntityClassList {
    member: EntityClass
}

/// One property and its values on the entity.
structure EntityProperty {
    /// Property IRI.
    @required
    property: String

    /// Property label.
    @required
    label: String

    /// Values asserted for the property.
    @required
    values: EntityTermList
}

list EntityPropertyList {
    member: EntityProperty
}

/// One property required by a class of the entity.
structure EntityRequired {
    /// Property IRI.
    @required
    property: String

    /// Property label.
    @required
    label: String

    /// Minimum cardinality the class declares.
    @required
    minCount: Integer

    /// Classes that declare the requirement.
    @required
    declaredOn: StringList

    /// Values present on the entity.
    @required
    values: EntityTermList

    /// Number of values present.
    @required
    valueCount: Integer

    /// True when `valueCount` meets `minCount`.
    @required
    satisfied: Boolean
}

list EntityRequiredList {
    member: EntityRequired
}

/// Strings in an entity read response.
list StringList {
    member: String
}

/// One evidence source for the entity.
structure EntitySource {
    /// Source family.
    @required
    kind: String

    /// Source reference.
    @required
    ref: String

    /// Text span, when the source is a document chunk.
    text: String

    /// Console URL that resolves the reference.
    @required
    resolveUrl: String

    /// Link intended for direct rendering.
    @required
    href: String
}

list EntitySourceList {
    member: EntitySource
}

/// Three-state evidence badge for the entity or one field.
structure EntityBadge {
    /// `evidenced`, `inferred`, or `none`.
    @required
    state: String

    /// Human-readable badge label.
    @required
    label: String

    /// Why the badge has this state.
    @required
    basis: String

    /// Judge that produced the verdict, when one was used.
    judge: String
}

/// One fact-ledger row backing a statement on the entity.
structure EntityProvenanceItem {
    /// Assertion-row identifier.
    @required
    factId: String

    /// Predicate IRI.
    @required
    predicate: String

    /// Object of the assertion.
    @required
    object: EntityTerm

    /// Ledger state of the row.
    @required
    state: String

    /// Source family recorded on the row.
    sourceKind: String

    /// Document that produced the row.
    documentId: String

    /// Extraction candidate that produced the row.
    candidateId: String

    /// When the row was asserted (ISO-8601).
    @required
    assertedAt: String

    /// True when the row belongs to a conflict group.
    @required
    conflict: Boolean
}

list EntityProvenanceItemList {
    member: EntityProvenanceItem
}

/// Fact-ledger provenance for the entity's subject.
structure EntityProvenance {
    /// Number of rows returned.
    @required
    count: Integer

    /// Ledger rows.
    @required
    items: EntityProvenanceItemList

    /// True when the ledger could not be read.
    unavailable: Boolean
}

/// One metric field binding relevant to the entity.
structure RelatedMetricBinding {
    /// Binding role.
    role: String

    /// Fact table the metric reads.
    factTable: String

    /// Column that holds the entity key.
    entityColumn: String
}

list RelatedMetricBindingList {
    member: RelatedMetricBinding
}

/// One metric related to the entity.
structure RelatedMetric {
    /// Metric identifier.
    @required
    metricId: String

    /// Chinese metric name.
    nameZh: String

    /// Metric domain.
    domain: String

    /// Metric grain.
    grain: String

    /// Whether the metric is publishable.
    publishable: Boolean

    /// Field bindings that connect the metric to the entity.
    @required
    bindings: RelatedMetricBindingList

    /// Why the metric matched the entity.
    @required
    matchBasis: StringList
}

list RelatedMetricList {
    member: RelatedMetric
}

/// Metrics related to the entity, with the match verdict.
structure EntityRelatedMetrics {
    /// `matched`, `empty`, or `unavailable`.
    @required
    status: String

    /// Why no metrics matched, when status is `empty` or `unavailable`.
    reason: String

    /// Related metrics.
    @required
    items: RelatedMetricList

    /// Bases used to match metrics.
    @required
    matchBasis: StringList
}

/// T-Box snapshot the read was evaluated against.
structure EntityTbox {
    /// Published version identifier.
    versionId: String

    /// Published semantic version.
    semver: String

    /// Named graph that holds the T-Box.
    graph: String
}

/// One A-Box entity with its class, property, neighbourhood and metric view.
structure EntityDetail {
    /// Entity IRI.
    @required
    iri: String

    /// Display label.
    @required
    label: String

    /// Classes asserted or inferred for the entity.
    @required
    classes: EntityClassList

    /// Properties required by those classes.
    @required
    requiredProperties: EntityRequiredList

    /// Overall verdict for required properties.
    @required
    requiredStatus: String

    /// All properties and values on the entity.
    @required
    properties: EntityPropertyList

    /// Immediate neighbourhood.
    @required
    neighbors: EntityNeighbors

    /// Number of instances of the entity's first class.
    @required
    instanceCount: Integer

    /// Metrics that reference the entity.
    @required
    relatedMetrics: EntityRelatedMetrics

    /// Evidence sources.
    @required
    sources: EntitySourceList

    /// Evidence badge for the entity as a whole.
    @required
    evidenceBadge: EntityBadge

    /// T-Box snapshot used for the read; absent when no T-Box is published.
    tbox: EntityTbox

    /// When the sample was taken (ISO-8601).
    @required
    sampledAt: String

    /// Named graphs that supplied the returned statements.
    @required
    namedGraphs: StringList

    /// Fact-ledger rows for this subject.
    @required
    provenance: EntityProvenance
}

/// One resolution link attached to a provenance field.
structure ProvenanceLink {
    /// Link kind: `source_ref`, `fact`, `fact_binding`, or `prov`.
    @required
    kind: String

    /// Referenced identifier.
    ref: String

    /// Console URL for the reference.
    url: String

    /// Document that owns the reference, when any.
    documentId: String
}

list ProvenanceLinkList {
    member: ProvenanceLink
}

/// One field with its three-state evidence badge.
structure ProvenanceField {
    /// Property IRI.
    @required
    property: String

    /// Property label.
    @required
    label: String

    /// Values asserted for the property.
    @required
    values: EntityTermList

    /// Lexical form of the first literal value.
    valueText: String

    /// True when the triple is asserted in the A-Box.
    @required
    asserted: Boolean

    /// True when the triple exists only in the inferred graph.
    @required
    inferredOnly: Boolean

    /// Three-state evidence badge.
    @required
    badge: EntityBadge

    /// True when a source reference resolves the value.
    @required
    hasSourceRef: Boolean

    /// True when a PROV activity or source reference backs the value.
    @required
    hasProv: Boolean

    /// Resolved evidence links.
    @required
    links: ProvenanceLinkList
}

list ProvenanceFieldList {
    member: ProvenanceField
}

/// One PROV activity related to the entity.
structure ProvenanceActivity {
    /// Activity IRI.
    @required
    activityId: String

    /// Relation between the entity and the activity.
    @required
    relation: String

    /// Object of the relation, when any.
    object: String

    /// Named graph that holds the relation.
    graph: String
}

list ProvenanceActivityList {
    member: ProvenanceActivity
}

/// One citation that resolves a field value.
structure ProvenanceCitation {
    /// Citation kind.
    @required
    kind: String

    /// Citation reference.
    ref: String

    /// Text span of the citation.
    text: String

    /// Document that contains the citation.
    documentId: String

    /// Console URL for the citation.
    url: String
}

list ProvenanceCitationList {
    member: ProvenanceCitation
}

/// Aggregate coverage of the three evidence states.
structure ProvenanceSummary {
    /// Number of fields.
    @required
    total: Integer

    /// Fields with resolved evidence.
    @required
    evidenced: Integer

    /// Fields backed only by inference.
    @required
    inferred: Integer

    /// Fields with no evidence.
    @required
    none: Integer

    /// Fields with a source reference.
    @required
    withSourceRef: Integer

    /// Fields with a PROV link.
    @required
    withProv: Integer

    /// Share of fields that are not `none` (0-1).
    @required
    coverageRate: Double
}

/// Per-field provenance report for one entity.
structure EntityProvenanceReport {
    /// Entity IRI.
    @required
    iri: String

    /// Display label.
    @required
    label: String

    /// Fields with evidence badges.
    @required
    fields: ProvenanceFieldList

    /// Statement view; mirrors `fields` for the statement table.
    @required
    statements: ProvenanceFieldList

    /// PROV activities related to the entity.
    @required
    activities: ProvenanceActivityList

    /// Citations that resolve field values.
    @required
    citations: ProvenanceCitationList

    /// Aggregate coverage.
    @required
    summary: ProvenanceSummary

    /// Evidence badge for the entity as a whole.
    @required
    evidenceBadge: EntityBadge

    /// Named graphs that supplied the returned statements.
    @required
    namedGraphs: StringList

    /// Fact-ledger rows for this subject.
    @required
    provenance: EntityProvenance

    /// True when the entity has no properties.
    @required
    empty: Boolean

    /// Why the report is empty, when it is.
    emptyReason: String

    /// Fixed note explaining the badge semantics.
    @required
    note: String
}

/// Read one A-Box entity by IRI.
///
/// The IRI is percent-encoded in the path so its slashes are not parsed as path
/// separators. `limit` caps the neighbourhood, not the property list.
@readonly
@http(method: "GET", uri: "/entities/{entityId}", code: 200)
@examples([
    {
        title: "Read one entity"
        input: { entityId: "urn:coa:entity:contract-ledger", limit: 50 }
        output: {
            iri: "urn:coa:entity:contract-ledger"
            label: "Contract Ledger"
            classes: [
                {
                    iri: "urn:coa:class:BusinessEntity"
                    label: "Business Entity"
                    labeled: true
                    inferredOnly: false
                    instanceCount: 12
                    chain: [{ iri: "urn:coa:class:Thing", label: "Thing" }]
                }
            ]
            requiredProperties: []
            requiredStatus: "satisfied"
            properties: [
                {
                    property: "urn:coa:predicate:belongs-to"
                    label: "belongs to"
                    values: [{ kind: "iri", value: "urn:coa:entity:archive", iri: "urn:coa:entity:archive" }]
                }
            ]
            neighbors: { nodes: [], edges: [], truncated: false }
            instanceCount: 12
            relatedMetrics: { status: "empty", reason: "no metric binding", items: [], matchBasis: [] }
            sources: []
            evidenceBadge: { state: "inferred", label: "仅推理", basis: "仅推理图出现，无断言 sourceRef / PROV" }
            tbox: { versionId: "8c7d6e5f-4a3b-4c2d-8e1f-0a9b8c7d6e5f", semver: "1.4.0", graph: "urn:coa:graph:tbox" }
            sampledAt: "2026-10-02T09:00:00Z"
            namedGraphs: ["urn:coa:graph:asserted"]
            provenance: { count: 1, items: [], unavailable: false }
        }
    }
])
operation GetEntity {
    input := {
        /// Percent-encoded IRI of the entity.
        @required
        @httpLabel
        entityId: EntityRef

        /// Maximum neighbours and properties to sample (1-200).
        @httpQuery("limit")
        @range(min: 1, max: 200)
        limit: Integer
    }

    output: EntityDetail

    errors: [
        NotFoundError
    ]
}

/// Read the per-field provenance report for one A-Box entity.
///
/// Every field carries an explicit three-state badge (`evidenced`, `inferred`,
/// `none`); a field without evidence is shown as `none`, never omitted.
@readonly
@http(method: "GET", uri: "/entities/{entityId}/provenance", code: 200)
@examples([
    {
        title: "Read entity provenance"
        input: { entityId: "urn:coa:entity:contract-ledger", limit: 50 }
        output: {
            iri: "urn:coa:entity:contract-ledger"
            label: "Contract Ledger"
            fields: [
                {
                    property: "urn:coa:predicate:belongs-to"
                    label: "belongs to"
                    values: [{ kind: "iri", value: "urn:coa:entity:archive", iri: "urn:coa:entity:archive" }]
                    asserted: true
                    inferredOnly: false
                    badge: { state: "evidenced", label: "有溯源", basis: "事实账本 fact-1a2b3c4d5e6f" }
                    hasSourceRef: true
                    hasProv: true
                    links: [{ kind: "fact", ref: "fact-1a2b3c4d5e6f", url: "/facts/fact-1a2b3c4d5e6f/events" }]
                }
            ]
            statements: []
            activities: []
            citations: [{ kind: "doc", ref: "doc-1", text: "Contract Ledger belongs to Archive", url: "/source/resolve?ref=doc-1" }]
            summary: { total: 1, evidenced: 1, inferred: 0, none: 0, withSourceRef: 1, withProv: 1, coverageRate: 1.0 }
            evidenceBadge: { state: "evidenced", label: "有溯源", basis: "字段值命中 PROV/sourceRef 证据文本" }
            namedGraphs: ["urn:coa:graph:asserted"]
            provenance: { count: 1, items: [], unavailable: false }
            empty: false
            note: "每个字段都有徽标；无溯源显式显示「无」"
        }
    }
])
operation GetEntityProvenance {
    input := {
        /// Percent-encoded IRI of the entity.
        @required
        @httpLabel
        entityId: EntityRef

        /// Maximum fields and neighbours to sample (1-200).
        @httpQuery("limit")
        @range(min: 1, max: 200)
        limit: Integer
    }

    output: EntityProvenanceReport

    errors: [
        NotFoundError
    ]
}
