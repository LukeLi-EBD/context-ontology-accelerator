// SPDX-License-Identifier: Apache-2.0
// P13 / F107 — T-Box version-proposal detail with the impact checklist.
//
// ── Why a separate op, and why it is named this way ────────────────────────
//
// The contract already has `GetProposal` (ontology-induction.smithy, already
// registered in control-plane.smithy), so extending it was checked first.
// Reconciled item by item against base 9a36752c:
//
//   GetProposal today                              F107 needs
//   ---------------------------------------------  ----------------------------
//   input: namespaceId + proposalId: Uuid          namespaceId + ontologyId
//   (no ontologyId label)                          + proposalId: String
//   URI /namespaces/{ns}/proposals/{pid}           /namespaces/{ns}/ontologies/
//                                                  {oid}/proposals/{pid}
//   output: induction artifacts (ontologyTurtle,   versionId / versionStatus /
//   r2rmlTurtle, presigned URLs, metadata,         current pointer / stored diff
//   acceptError)                                   / impact analysis
//   status: ProposalStatus = inducing | pending |  status: proposed | approved |
//   accepting | accepted | ...                     published | superseded | ...
//   served by the ontology-engine Lambda, store    served by the platform kernel,
//   coa_ontology proposals (DynamoDB-shaped)       store platform.ontology_proposal
//
// These are two different resources on two different backends. The existing op
// addresses an *induction* proposal (document/table -> ontology) whose id is a
// Uuid; F107's proposal is a *version lifecycle* proposal whose id looks like
// `prop-32e6cc1834cd` (not a Uuid) and whose row lives in
// platform.ontology_proposal keyed by version. Adding `impact` to `GetProposal`
// is therefore not an additive change: it would need a new path label, a new id
// shape, a second status enum, a second backend, and version pairs that the
// induction record does not carry. Decision: keep a separate operation, renamed
// `GetOntologyVersionProposal` so it can never be read as a duplicate of
// `GetProposal`.
//
// Note: doc/coa-x/12-剩余51条批量排期.md (P13) says "无新 op；
// GetOntologyProposal 响应补 impact 字段", but no such op exists in any .smithy
// file at 9a36752c — nor on main 1c066384. The only proposal-detail op in the
// model is the induction `GetProposal` above. The plan text assumed an op that
// was never registered.
//
// ── Merge steps (shared model untouched) ───────────────────────────────────
//
//   1. models/src/main/smithy/control-plane.smithy — inside the `use` block,
//      next to the other ontology uses, add exactly:
//
//          use com.amazon.semanticcontext.ontologylifecycle#GetOntologyVersionProposal
//
//   2. models/src/main/smithy/control-plane.smithy — inside
//      `service ControlPlaneService { operations: [ ... ] }`, directly after
//      `GetOntologyOverview`, add exactly:
//
//          // ── Ontology version lifecycle (F107) ───────────────────────────
//          GetOntologyVersionProposal
//
// After both lines are merged, regenerate with the normal pipeline; do not
// hand-write the client.
//
// The backend that serves this path is the platform kernel
// (`packages/platform-core/src/platform_core/api.py`,
// `GET /governance/proposals/{proposal_id}`), exposed to the web app through
// the local bridge as `/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals/{proposalId}`.
//
// Nullability rule (deliberate): every instance count is a sparse member.
// An absent member means "not computable" and must be rendered as null; it is
// NOT zero. A value of 0 always means the count really is zero.
$version: "2"

namespace com.amazon.semanticcontext.ontologylifecycle

use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#OntologyId
use com.amazon.semanticcontext.common#Uuid
use com.amazon.semanticcontext.common#ValidationError

/// Read one T-Box version proposal together with its stored diff and the O-03
/// impact checklist. Read-only: nothing is written, no gate is run.
///
/// Not the same operation as the induction `GetProposal`
/// (`/namespaces/{namespaceId}/proposals/{proposalId}`): that one addresses a
/// Uuid-keyed induction proposal served by the ontology engine; this one
/// addresses a version-lifecycle proposal nested under its ontology and served
/// by the platform kernel. See the file header for the full comparison.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals/{proposalId}", code: 200)
operation GetOntologyVersionProposal {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Identifier of the ontology the proposal belongs to.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Proposal identifier returned by ProposeOntologyVersion.
        @required
        @httpLabel
        @length(min: 1, max: 128)
        proposalId: String
    }

    output := {
        /// The proposal row, including the diff stored at propose time.
        @required
        proposal: Document

        /// The version row the proposal points at.
        @required
        version: Document

        /// Current status of that version.
        @required
        versionStatus: String

        /// Current tbox/current pointer, when one exists.
        current: Document

        /// Diff stored on the proposal (`from` -> `to`).
        @required
        diff: Document

        /// Change impact: stored counts plus the full O-03 analysis.
        @required
        impact: OntologyImpact
    }

    errors: [
        ValidationError
        NotFoundError
    ]
}

/// Proposal impact view.
///
/// `analysis` and `analysisError` are mutually exclusive: exactly one is
/// present. A caller that sees neither must treat the impact as unavailable.
structure OntologyImpact {
    /// Triples added by the change set, as stored at propose time.
    addedTriples: Long

    /// Triples removed by the change set, as stored at propose time.
    removedTriples: Long

    /// Number of added classes, as stored at propose time.
    addedClasses: Long

    /// Number of removed classes, as stored at propose time.
    removedClasses: Long

    /// Number of added properties, as stored at propose time.
    addedProperties: Long

    /// Number of removed properties, as stored at propose time.
    removedProperties: Long

    /// Number of domain changes, as stored at propose time.
    domainChanges: Long

    /// Number of range changes, as stored at propose time.
    rangeChanges: Long

    /// Instance rows removed together with their class, as stored at propose
    /// time. This is a T-Box diff counter, not a live A-Box count.
    removedClassInstances: Long

    /// Breaking item count recorded by the diff.
    breakingItems: Long

    /// Full O-03 impact checklist. Absent when `analysisError` is present.
    analysis: OntologyImpactAnalysis

    /// Why the checklist could not be produced. Absent on success; when
    /// present the UI must show this reason instead of an empty table.
    analysisError: OntologyImpactError
}

/// One read-only O-03 checklist for the proposal's change set.
@examples([
    {
        title: "A-Box 未配置：实例数不可算（null，不是 0）"
        document: {
            from: "00000000-0000-0000-0000-000000000001"
            to: "00000000-0000-0000-0000-000000000002"
            changeSet: {
                counts: {
                    addedTriples: 3
                    removedTriples: 0
                    addedClasses: 1
                    removedClasses: 0
                    addedProperties: 0
                    removedProperties: 0
                    domainChanges: 0
                    rangeChanges: 0
                }
                addedClasses: []
                removedClasses: []
                addedProperties: []
                removedProperties: []
                domainChanges: []
                rangeChanges: []
                breaking: false
                breakingItems: []
            }
            affected: {
                classes: [],
                properties: [],
                instances: {
                    byClass: []
                    source: "A-Box 未配置"
                    note: "没有 A-Box 图，实例数不可算；未以 0 代替"
                }
            }
            dependencies: {
                metrics: []
                rules: []
                terms: []
                notes: []
                empty: true
                emptyReason: "无指标或规则依赖命中"
                method: "metric_definition 文本字段 token 命中"
            }
            // `consistent` is omitted on purpose: Smithy IDL has no null, and
            // an absent member on the wire *is* null (not computable).
            verification: {
                sampled: []
                reason: "无 A-Box，实例数不可重算"
                source: "A-Box 未配置"
            }
            empty: false
            computedAt: "2026-11-10T00:00:00+00:00"
            source: "runtime.ontology.diff + SPARQL + metric/term 注册表"
            readOnly: true
        }
    }
])
structure OntologyImpactAnalysis {
    /// Baseline version id; absent for a first version with no baseline.
    from: String

    /// Target version id.
    @required
    to: String

    /// Triple / class / property deltas behind this checklist.
    @required
    changeSet: OntologyImpactChangeSet

    /// Classes, properties and live instance counts.
    @required
    affected: OntologyImpactAffected

    /// Metrics, rules and terms that depend on the affected IRIs.
    @required
    dependencies: OntologyImpactDependencies

    /// Independent recount of a sample of affected classes.
    @required
    verification: OntologyImpactVerification

    /// True when no class, property, metric or rule is affected.
    @required
    empty: Boolean

    /// Human-readable reason for an empty checklist.
    emptyReason: String

    /// When the checklist was computed (ISO-8601).
    @required
    computedAt: String

    /// Version rows (semver, contentHash, tripleCount) the diff ran on.
    inputs: Document

    /// Hash of (from contentHash, to contentHash, diff) for reproducibility.
    inputsFingerprint: String

    /// Raw per-class / per-property aggregation, including `unclassified`.
    aggregations: Document

    /// Human-readable provenance.
    @required
    source: String

    /// Always true: the analysis never writes.
    @required
    readOnly: Boolean
}

/// Triple and schema deltas of the change set.
structure OntologyImpactChangeSet {
    @required
    counts: OntologyImpactCounts

    @required
    addedClasses: OntologyImpactStringList

    @required
    removedClasses: OntologyImpactStringList

    @required
    addedProperties: OntologyImpactStringList

    @required
    removedProperties: OntologyImpactStringList

    /// Raw domain change rows (`property`, `from`, `to`).
    @required
    domainChanges: OntologyImpactDocumentList

    /// Raw range change rows (`property`, `from`, `to`).
    @required
    rangeChanges: OntologyImpactDocumentList

    /// True when the diff contains breaking changes.
    @required
    breaking: Boolean

    /// Breaking items emitted by the diff.
    @required
    breakingItems: OntologyImpactDocumentList
}

/// Aggregate delta counts.
structure OntologyImpactCounts {
    @required
    addedTriples: Long

    @required
    removedTriples: Long

    @required
    addedClasses: Long

    @required
    removedClasses: Long

    @required
    addedProperties: Long

    @required
    removedProperties: Long

    @required
    domainChanges: Long

    @required
    rangeChanges: Long
}

/// Classes, properties and live instance counts touched by the change set.
structure OntologyImpactAffected {
    @required
    classes: OntologyImpactClassList

    @required
    properties: OntologyImpactPropertyList

    /// Instance counts. `instances.total` is null (absent) when no A-Box is
    /// configured; null means "not computable", never "zero".
    @required
    instances: OntologyImpactInstances
}

/// One affected class.
structure OntologyImpactClass {
    /// Class IRI.
    @required
    iri: String

    /// Local name of the IRI, for display.
    @required
    label: String

    /// `added`, `removed` or `modified`.
    @required
    change: String

    /// Triples added on this class as subject.
    @required
    addedTriples: Long

    /// Triples removed on this class as subject.
    @required
    removedTriples: Long
}

/// One affected property.
structure OntologyImpactProperty {
    @required
    iri: String

    @required
    label: String

    /// `added`, `removed` or `modified`.
    @required
    change: String

    @required
    addedTriples: Long

    @required
    removedTriples: Long

    /// Raw domain change rows for this property.
    @required
    domainChanges: OntologyImpactDocumentList

    /// Raw range change rows for this property.
    @required
    rangeChanges: OntologyImpactDocumentList
}

/// Live instance counts over the configured A-Box graphs.
@examples([
    {
        title: "A-Box 未配置"
        document: {
            byClass: []
            source: "A-Box 未配置"
            note: "没有 A-Box 图，实例数不可算；未以 0 代替"
        }
    }
])
structure OntologyImpactInstances {
    /// Distinct subjects across all A-Box graphs. Absent when no A-Box is
    /// configured — display null, not 0.
    total: Long

    /// Sum of instances over the affected classes. Absent for the same reason.
    affectedInstances: Long

    /// Instance count per affected class; each `instances` member follows the
    /// same null-means-unknown rule.
    @required
    byClass: OntologyImpactInstanceClassList

    /// A-Box graph IRIs the counts were read from. Absent when none is
    /// configured.
    graphs: OntologyImpactStringList

    /// How the numbers were produced.
    @required
    source: String

    /// Why the numbers are unavailable; set when `total` is absent.
    note: String
}

/// Instance count for one affected class.
structure OntologyImpactInstanceClass {
    @required
    iri: String

    @required
    label: String

    /// Absent when no A-Box is configured. Never read as zero.
    instances: Long
}

/// Metrics, rules and terms that depend on the affected IRIs.
structure OntologyImpactDependencies {
    /// Metrics whose definition or binding chain matches an affected IRI.
    @required
    metrics: OntologyImpactMetricList

    /// Rules carried by those metrics.
    @required
    rules: OntologyImpactRuleList

    /// Term entries whose canonical class is affected.
    @required
    terms: OntologyImpactDocumentList

    /// True when no metric and no rule matched.
    @required
    empty: Boolean

    /// Reason for an empty dependency block.
    emptyReason: String

    /// Per-source read problems (for example a missing registry table).
    @required
    notes: OntologyImpactDocumentList

    /// Human-readable matching method.
    @required
    method: String
}

/// One dependent metric.
structure OntologyImpactMetric {
    @required
    metricId: String

    /// Display name, when the registry has one.
    name: String

    /// How the metric matched: `text:<token>` and/or `binding:<table>.<column>`.
    @required
    matchedBy: OntologyImpactStringList

    @required
    source: String
}

/// One dependent rule.
structure OntologyImpactRule {
    @required
    metricId: String

    /// Rule identifier from the metric's rule set.
    ruleId: String

    /// Rule severity / level, when present.
    level: String

    /// `rule_set_text` or `dependent_metric`.
    @required
    matchedBy: String

    @required
    source: String
}

/// Independent recount of a sample of affected classes.
structure OntologyImpactVerification {
    @required
    sampled: OntologyImpactVerificationSampleList

    /// True when every sampled class matched. Absent when nothing could be
    /// sampled (no A-Box, or no affected class).
    consistent: Boolean

    /// Why sampling produced no verdict.
    reason: String

    @required
    source: String
}

/// One sampled class: listed count vs independent recount.
structure OntologyImpactVerificationSample {
    @required
    iri: String

    @required
    listed: Long

    @required
    recounted: Long

    @required
    consistent: Boolean
}

/// Why the impact checklist could not be produced.
structure OntologyImpactError {
    /// Stable provider code, e.g. `E_DIFF_NO_PREVIOUS_BASELINE`.
    @required
    code: String

    /// Human-readable message.
    @required
    message: String

    /// Extra structured context.
    details: Document
}

list OntologyImpactStringList {
    member: String
}

list OntologyImpactDocumentList {
    member: Document
}

list OntologyImpactClassList {
    member: OntologyImpactClass
}

list OntologyImpactPropertyList {
    member: OntologyImpactProperty
}

list OntologyImpactInstanceClassList {
    member: OntologyImpactInstanceClass
}

list OntologyImpactMetricList {
    member: OntologyImpactMetric
}

list OntologyImpactRuleList {
    member: OntologyImpactRule
}

list OntologyImpactVerificationSampleList {
    member: OntologyImpactVerificationSample
}
