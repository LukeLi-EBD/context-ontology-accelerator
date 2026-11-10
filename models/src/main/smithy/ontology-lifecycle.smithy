// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// T-Box lifecycle: version registry, proposals, publish, rollback and the
// hash-chained audit log.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.6 rows F104, F111-F123 and
// doc/coa-x/18-platform-core拆解.md §KERNEL lifecycle routes. Every operation
// below is already served by the local bridge (`coa_api_local.py`, KERNEL) and
// answered by `platform_core.adapters.ontology_pg`; this file is the contract
// that keeps them alive when platform-core is split out of the bridge.
//
// Names matter here. The induction proposal family (`GetProposal`,
// `AcceptProposal`, ...) is a different resource with a different state
// machine and is not reused by `ProposeOntologyVersion`. `VerifyOntology` is
// the lifecycle/audit hash-chain check; it is not `RunValidation` (the
// namespace-level SHACL quality check) and cannot be folded into it.
$version: "2"

namespace com.amazon.semanticcontext.ontologylifecycle

use com.amazon.semanticcontext.common#ConflictError
use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#OntologyId
use com.amazon.semanticcontext.common#Uuid
use com.amazon.semanticcontext.common#ValidationError

/// Lifecycle state of one T-Box version row.
enum OntologyVersionStatus {
    /// Imported, not yet proposed.
    draft

    /// A proposal was submitted and waits for review.
    proposed

    /// The proposal is being reviewed.
    review

    /// The proposal (and the version) is approved for publish.
    approved

    /// The version backs the `tbox/current` pointer.
    published

    /// A newer version replaced it at the pointer.
    superseded

    /// Review rejected the proposal.
    rejected

    /// Archived read-only baseline; cannot be published or rolled back to.
    deprecated
}

/// State of one lifecycle proposal.
enum OntologyProposalStatus {
    /// Submitted and waiting for review.
    proposed

    /// Under review.
    review

    /// Approved; publish may proceed.
    approved

    /// The proposal's version was published.
    published

    /// Review rejected the proposal. The proposal row itself only stores
    /// proposed/approved/published; rejection is reported here on the review
    /// response while the version row carries `rejected`.
    rejected
}

/// Review decision accepted by `ReviewOntologyProposal`.
enum OntologyProposalDecision {
    /// Approve the proposal and move the version to `approved`.
    APPROVE

    /// Reject the proposal and mark the version `rejected`.
    REJECT
}

/// Rollback strategy accepted by `RollbackOntology`.
enum OntologyRollbackMode {
    /// Move the `tbox/current` pointer back to an existing version.
    POINTER_ONLY

    /// Copy the target version into a new version, then move the pointer.
    NEW_VERSION
}

/// Serialisation format of an exported version.
enum OntologyExportFormat {
    /// Turtle (`.ttl`).
    turtle

    /// N-Quads (`.nq`).
    nquads
}

/// Serialisation format accepted by `ImportOntology`.
enum OntologyImportFormat {
    /// Turtle.
    turtle

    /// N-Triples.
    nt
}

/// Version identifier minted by the registry, e.g. `ont-draft-1a2b3c4d5e6f`.
@length(min: 1, max: 128)
string OntologyVersionId

/// Proposal identifier minted by the registry, e.g. `prop-1a2b3c4d5e6f`.
@length(min: 1, max: 128)
string OntologyProposalId

/// Free-text summary of what a version changes.
@length(min: 0, max: 8192)
string OntologyChangeSummary

/// Identity performing a lifecycle write.
@length(min: 1, max: 256)
string OntologyActor

/// Optional reason recorded on a lifecycle write.
@length(min: 0, max: 2048)
string OntologyReason

/// Source ontology text uploaded to `ImportOntology`.
@length(min: 1, max: 52428800)
string OntologySourceContent

/// One T-Box version row, as the registry stores it.
structure OntologyVersion {
    /// Version identifier.
    @required
    id: OntologyVersionId

    /// Semantic version, e.g. `1.2.0` or `1.2.0+rollback.1`.
    @required
    semver: String

    /// Lifecycle state.
    @required
    status: OntologyVersionStatus

    /// SHA-256 of the canonical graph.
    contentHash: String

    /// Declared triple count of the version.
    tripleCount: Integer

    /// Source serialisation (`turtle` or `nt`).
    format: String

    /// Graph IRI holding the version's triples.
    graph: String

    /// When set, the version was created by rolling back to this version.
    rollbackOf: OntologyVersionId

    /// Human-readable label.
    label: String

    /// Creation time (ISO-8601).
    createdAt: String

    /// First publish time (ISO-8601); absent while never published.
    publishedAt: String
}

/// The `tbox/current` pointer row.
structure OntologyPointer {
    /// Pointer name, always `tbox/current` in this deployment.
    name: String

    /// Version the pointer currently selects.
    @required
    versionId: OntologyVersionId

    /// Semver of the selected version.
    semver: String

    /// Canonical hash of the selected version.
    contentHash: String

    /// Graph IRI of the selected version.
    graph: String

    /// Last pointer move (ISO-8601).
    updatedAt: String
}

/// Page of versions for one ontology.
structure OntologyVersionPage {
    /// Versions in creation order.
    @required
    items: OntologyVersionList

    /// Number of versions returned.
    @required
    count: Integer

    /// Number of versions before the deprecated filter.
    @required
    total: Integer

    /// Deprecated versions filtered out of `items`.
    @required
    deprecated: Integer

    /// Current pointer; absent when nothing is published.
    pointer: OntologyPointer
}

/// A version row plus its proposals and audit events.
structure OntologyVersionDetail {
    /// Version identifier.
    @required
    id: OntologyVersionId

    /// Contract alias of `id`.
    @required
    versionId: OntologyVersionId

    /// Semantic version.
    @required
    semver: String

    /// Lifecycle state.
    @required
    status: OntologyVersionStatus

    /// SHA-256 of the canonical graph.
    contentHash: String

    /// Declared triple count.
    tripleCount: Integer

    /// Source serialisation.
    format: String

    /// Graph IRI holding the triples.
    graph: String

    /// Contract alias of `graph`.
    graphUri: String

    /// Contract alias of `tripleCount`.
    statementCount: Integer

    /// Triples actually present in the graph store.
    graphTripleCount: Integer

    /// Version this one rolled back to, when applicable.
    rollbackOf: OntologyVersionId

    /// Human-readable label.
    label: String

    /// Creation time (ISO-8601).
    createdAt: String

    /// Publish time (ISO-8601).
    publishedAt: String

    /// Proposals filed against this version.
    proposals: OntologyProposalList

    /// Audit events recorded for this version.
    events: OntologyEventList
}

/// One element that makes a diff breaking.
structure OntologyBreakingItem {
    /// Kind: `class_removed`, `property_removed`, `domain_narrowed`,
    /// `range_narrowed`, or `property_became_required`.
    @required
    kind: String

    /// IRI of the affected class or property; absent for domain/range changes.
    iri: String

    /// Property IRI for domain/range changes.
    property: String

    /// Values before the change.
    @length(min: 0, max: 200)
    from: OntologyStringList

    /// Values after the change.
    @length(min: 0, max: 200)
    to: OntologyStringList
}

/// A class whose instances would disappear.
structure OntologyClassInstance {
    /// Class IRI.
    @required
    class: String

    /// Current instance count of that class.
    @required
    instances: Integer
}

/// Domain or range values before and after one property change.
structure OntologyDomainChange {
    /// Property IRI.
    @required
    property: String

    /// Values before the change.
    @required
    @length(min: 0, max: 200)
    from: OntologyStringList

    /// Values after the change.
    @required
    @length(min: 0, max: 200)
    to: OntologyStringList
}

/// Structural summary of a diff.
structure OntologyDiffSummary {
    /// Triples added by the target version.
    @required
    addedTriples: Integer

    /// Triples removed by the target version.
    @required
    removedTriples: Integer

    /// Class IRIs added.
    @required
    @length(min: 0, max: 5000)
    addedClasses: OntologyStringList

    /// Class IRIs removed.
    @required
    @length(min: 0, max: 5000)
    removedClasses: OntologyStringList

    /// Property IRIs added.
    @required
    @length(min: 0, max: 5000)
    addedProperties: OntologyStringList

    /// Property IRIs removed.
    @required
    @length(min: 0, max: 5000)
    removedProperties: OntologyStringList

    /// Domain changes per property.
    @required
    @length(min: 0, max: 5000)
    domainChanges: OntologyDomainChangeList

    /// Range changes per property.
    @required
    @length(min: 0, max: 5000)
    rangeChanges: OntologyDomainChangeList

    /// Removed classes with their instance counts.
    @required
    @length(min: 0, max: 5000)
    removedClassInstances: OntologyClassInstanceList
}

/// What changed between two versions.
structure OntologyDiff {
    /// Baseline version; absent when the target is the first version.
    from: OntologyVersionId

    /// Target version.
    @required
    to: OntologyVersionId

    /// True when at least one breaking item exists.
    @required
    breaking: Boolean

    /// Elements that make the diff breaking.
    @required
    @length(min: 0, max: 5000)
    breakingItems: OntologyBreakingItemList

    /// Structural summary.
    @required
    summary: OntologyDiffSummary

    /// Pre-rendered Markdown description of the diff.
    markdown: String
}

/// One lifecycle proposal.
structure OntologyProposal {
    /// Proposal identifier.
    @required
    proposalId: OntologyProposalId

    /// Version the proposal is about.
    @required
    versionId: OntologyVersionId

    /// Version the diff was computed against.
    againstVersion: OntologyVersionId

    /// What the proposal changes.
    changeSummary: OntologyChangeSummary

    /// Proposal state.
    @required
    status: OntologyProposalStatus

    /// True when the diff contains breaking items.
    @required
    breaking: Boolean

    /// True when a caller acknowledged the breaking items.
    acknowledgedBreaking: Boolean

    /// Diff stored at propose time.
    diff: OntologyDiff

    /// Counts derived from the diff, as the kernel emits them.
    impact: Document

    /// Who created the proposal.
    createdBy: String

    /// Creation time (ISO-8601).
    createdAt: String

    /// Who approved the proposal.
    approvedBy: String

    /// Approval time (ISO-8601).
    approvedAt: String

    /// Publish time of the proposal (ISO-8601).
    publishedAt: String

    /// State of the underlying version, present on list and detail reads.
    versionStatus: OntologyVersionStatus
}

/// Page of proposals for one ontology.
structure OntologyProposalPage {
    /// Proposals in creation order (newest first).
    @required
    items: OntologyProposalList

    /// Number of proposals after filtering.
    @required
    count: Integer

    /// Number of proposals actually returned.
    @required
    returned: Integer

    /// Current pointer; absent when nothing is published.
    current: OntologyPointer
}

/// A proposal plus its version and the diff stored at propose time.
structure OntologyProposalDetail {
    /// The proposal itself.
    @required
    proposal: OntologyProposal

    /// Version the proposal targets.
    @required
    version: OntologyVersion

    /// State of that version.
    @required
    versionStatus: OntologyVersionStatus

    /// Diff stored at propose time.
    @required
    diff: OntologyDiff

    /// Counts derived from the diff.
    impact: Document

    /// Current pointer; absent when nothing is published.
    current: OntologyPointer
}

/// One row of the hash-chained lifecycle audit log.
structure OntologyEvent {
    /// Monotonic event identifier.
    @required
    eventId: Long

    /// Version the event belongs to.
    versionId: OntologyVersionId

    /// Proposal the event belongs to.
    proposalId: OntologyProposalId

    /// Action recorded, e.g. `published`, `rolled_back`, `approved`.
    @required
    action: String

    /// Who performed the action.
    @required
    actor: String

    /// Optional reason recorded with the action.
    reason: String

    /// Action payload, as the kernel stored it.
    payload: Document

    /// Previous event identifier in the chain.
    prevEvent: Long

    /// Hash of this event.
    hash: String

    /// Event time (ISO-8601).
    @required
    createdAt: String

    /// Alias of `action`, kept for older callers.
    type: String

    /// Alias of `createdAt`, kept for older callers.
    at: String

    /// `published`, `rolled_back`, `superseded`, or `other`.
    category: String
}

/// Audit page for one ontology.
structure OntologyEventPage {
    /// Events, newest first.
    @required
    items: OntologyEventList

    /// Number of events returned.
    @required
    count: Integer

    /// Counts per category.
    categories: OntologyCategoryCounts

    /// Filters echoed back by the server.
    filter: OntologyEventFilter

    /// Current pointer at read time; absent when nothing is published.
    current: OntologyPointer
}

/// Counts per audit category.
map OntologyCategoryCounts {
    /// Category name.
    key: String

    /// Number of events in that category.
    value: Integer
}

/// Filters accepted by `ListOntologyEvents`.
structure OntologyEventFilter {
    /// Version filter that was applied.
    versionId: OntologyVersionId

    /// Action filter that was applied.
    action: String
}

/// One gate verdict inside a publish plan.
map OntologyGateMap {
    /// Gate name, e.g. `integrity`, `breaking`, `shacl`.
    key: String

    /// Gate verdict object; shape differs per gate.
    value: Document
}

/// One reason a publish plan would refuse to publish.
structure PublishBlocker {
    /// Gate that produced the blocker.
    @required
    gate: String

    /// Provider error code.
    @required
    code: String

    /// Human-readable explanation.
    @required
    message: String

    /// Gate-specific detail.
    details: Document
}

/// Result of `PublishOntology`; a dry run fills the plan view, a real publish
/// fills the version view.
structure PublishResult {
    /// Always true on a successful real publish; absent on a dry run.
    ok: Boolean

    /// True when the call only ran the gates.
    dryRun: Boolean

    /// Version being published.
    versionId: OntologyVersionId

    /// State of that version at call time.
    versionStatus: OntologyVersionStatus

    /// Version the pointer would replace.
    currentVersionId: OntologyVersionId

    /// Whether an already registered version was re-activated.
    publishExisting: Boolean

    /// Dry-run verdict: true when the publish would succeed.
    wouldPublish: Boolean

    /// Dry-run verdict: true when the publish would change the pointer.
    changed: Boolean

    /// Kernel alias of the published version.
    id: OntologyVersionId

    /// Contract name of the published version, added by the bridge.
    publishedVersion: OntologyVersionId

    /// Semver of the published version.
    semver: String

    /// Graph IRI of the published version.
    graph: String

    /// Declared triple count.
    tripleCount: Integer

    /// Triples present in the graph store.
    triples: Integer

    /// Version the pointer replaced.
    previousVersionId: OntologyVersionId

    /// Proposal that authorised the publish.
    proposalId: OntologyProposalId

    /// Who published.
    publishedBy: String

    /// Publish time (ISO-8601).
    publishedAt: String

    /// True when the pointer already selected this version.
    unchanged: Boolean

    /// True when a repeat publish returned the earlier result.
    idempotent: Boolean

    /// True when an approved proposal authorised the publish.
    governed: Boolean

    /// True when the publish created an implicit proposal.
    implicit: Boolean

    /// Kernel alias of `implicit`.
    implicitProposal: Boolean

    /// `publish`, `activate_existing`, `implicit`, or `governed`.
    mode: String

    /// True when the diff contains breaking items.
    breaking: Boolean

    /// Whether the caller acknowledged breaking items.
    acknowledgeBreaking: Boolean

    /// Counts derived from the diff.
    impact: Document

    /// Per-gate verdicts.
    gates: OntologyGateMap

    /// Reasons the publish would fail.
    blockers: OntologyBlockerList
}

/// Result of `RollbackOntology`; a plan-only call fills the plan view, a real
/// rollback fills the version view.
structure OntologyRollbackResult {
    /// Always true on a successful real rollback; absent on a plan.
    ok: Boolean

    /// Rollback strategy that was applied.
    mode: OntologyRollbackMode

    /// Version the rollback restores; plan view.
    target: OntologyVersion

    /// Version the pointer currently selects; plan view.
    replacedVersion: OntologyVersion

    /// Identifier of the target version.
    targetVersionId: OntologyVersionId

    /// Triple count of the target version.
    targetTriples: Integer

    /// Version the pointer replaced.
    replacedVersionId: OntologyVersionId

    /// Kernel alias of the published version.
    id: OntologyVersionId

    /// Contract name of the published version, added by the bridge.
    publishedVersion: OntologyVersionId

    /// For `NEW_VERSION`, the version that was copied.
    rollbackOf: OntologyVersionId

    /// Semver of the resulting version.
    semver: String

    /// State of the resulting version.
    status: OntologyVersionStatus

    /// Graph IRI of the resulting version.
    graph: String

    /// Canonical hash of the resulting version.
    contentHash: String

    /// Triples of the resulting version.
    triples: Integer

    /// Previous pointer value.
    previous: OntologyVersionId

    /// Plan verdict: true when the pointer would move.
    wouldChangePointer: Boolean

    /// True when the pointer already selected the target.
    unchanged: Boolean

    /// Who rolled back.
    publishedBy: String

    /// Publish time of the resulting version (ISO-8601).
    publishedAt: String

    /// Rollback time (ISO-8601).
    rolledBackAt: String

    /// Who rolled back.
    rolledBackBy: String

    /// Reason recorded on the rollback.
    reason: String

    /// Reasons a rollback would fail.
    blockers: OntologyBlockerList
}

/// Result of `ReviewOntologyProposal`.
structure OntologyProposalReviewResult {
    /// Always true on a successful review.
    ok: Boolean

    /// Proposal that was reviewed.
    @required
    proposalId: OntologyProposalId

    /// Version the proposal targets.
    versionId: OntologyVersionId

    /// New proposal state.
    status: OntologyProposalStatus

    /// New version state.
    versionStatus: OntologyVersionStatus

    /// Who approved, when the decision was `APPROVE`.
    approvedBy: String

    /// Approval time (ISO-8601).
    approvedAt: String

    /// True when `proposed` was approved without a separate review step.
    reviewedImplicitly: Boolean

    /// Who rejected, when the decision was `REJECT`.
    rejectedBy: String

    /// Rejection time (ISO-8601).
    rejectedAt: String

    /// Reason recorded with the decision.
    reason: String

    /// True when the proposal was already in the requested state.
    unchanged: Boolean
}

/// SHACL outcome recorded by an import.
structure OntologyShaclResult {
    /// Identifier of the deployed shapes graph.
    shapesId: String

    /// Version of the deployed shapes graph.
    shapesVersion: String

    /// True when the shapes conform; null when no shapes were configured.
    conforms: Boolean

    /// Number of violations reported by the validator.
    violationCount: Integer

    /// `validated` or `error`.
    status: String

    /// Validator engine, e.g. `pyshacl`.
    engine: String

    /// Validation error, when `status` is `error`.
    error: String

    /// Violations reported by the validator.
    @length(min: 0, max: 500)
    violations: DocumentList
}

/// Result of `ImportOntology`: the draft row the registry created.
structure OntologyImportResult {
    /// Import record identifier.
    @required
    importId: String

    /// Draft version identifier.
    @required
    versionId: OntologyVersionId

    /// Namespace the draft targets.
    targetNamespace: String

    /// Author recorded on the import.
    author: String

    /// Change summary recorded on the import.
    changeSummary: OntologyChangeSummary

    /// Serialisation the content was parsed as.
    format: String

    /// Triples already in the baseline.
    triples: Integer

    /// Triples in the imported graph.
    totalTriples: Integer

    /// Distinct OWL classes.
    classes: Integer

    /// Distinct object properties.
    objectProperties: Integer

    /// Distinct datatype properties.
    dataProperties: Integer

    /// `owl:imports` IRIs declared by the source.
    @length(min: 0, max: 500)
    importsDeclared: OntologyStringList

    /// Imports that resolved against the search path.
    @length(min: 0, max: 500)
    importsResolved: DocumentList

    /// Imports that did not resolve.
    @length(min: 0, max: 500)
    unresolvedImports: DocumentList

    /// SHACL outcome.
    shacl: OntologyShaclResult

    /// Consistency check outcome, as the reasoner reported it.
    consistency: Document

    /// True when nothing blocks the draft from being proposed.
    usable: Boolean

    /// Provider code explaining why the draft is not usable.
    reason: String

    /// Every blocker that made the draft unusable.
    @length(min: 0, max: 100)
    usableReasons: DocumentList

    /// True when the import was published; always false at this boundary.
    published: Boolean

    /// True when the import record was written.
    persisted: Boolean

    /// Implementation slice that produced the result.
    slice: String

    /// Staging graph written by the import.
    stagingGraph: String

    /// SHA-256 of the uploaded source.
    sourceSha256: String

    /// Import creation time (ISO-8601).
    createdAt: String
}

/// Result of `VerifyOntology`.
structure OntologyVerifyResult {
    /// True when every link in the lifecycle chain verifies.
    @required
    ok: Boolean

    /// Number of events checked before the first failure or the end.
    @required
    checked: Integer

    /// First failure, when `ok` is false.
    error: String

    /// PROV chain verification result.
    @required
    prov: OntologyProvResult

    /// T-Box/PROV separation check.
    separation: OntologySeparationResult
}

/// PROV chain verification result.
structure OntologyProvResult {
    /// True when every PROV link verifies.
    @required
    ok: Boolean

    /// Number of PROV events checked.
    @required
    checked: Integer

    /// First failure, when `ok` is false.
    error: String

    /// Hash of the last verified event.
    lastHash: String

    /// PROV graph IRI.
    graph: String
}

/// T-Box / PROV zero-mixing check.
structure OntologySeparationResult {
    /// True when neither graph carries the other's nodes.
    @required
    ok: Boolean

    /// PROV graph IRI.
    provGraph: String

    /// T-Box graph IRI.
    tboxGraph: String

    /// Triples in the PROV graph.
    provTriples: Integer

    /// PROV triples found in the T-Box graph.
    tboxProvTriples: Integer

    /// T-Box triples found in the PROV graph.
    provTboxTriples: Integer

    /// Legacy `prov:` predicates already present in the T-Box.
    tboxLegacyProvPredicateTriples: Integer
}

/// Strings in a lifecycle response.
list OntologyStringList {
    member: String
}

/// Versions in a lifecycle response.
list OntologyVersionList {
    member: OntologyVersion
}

/// Proposals in a lifecycle response.
list OntologyProposalList {
    member: OntologyProposal
}

/// Audit events in a lifecycle response.
list OntologyEventList {
    member: OntologyEvent
}

/// Breaking items in a diff.
list OntologyBreakingItemList {
    member: OntologyBreakingItem
}

/// Domain or range changes in a diff.
list OntologyDomainChangeList {
    member: OntologyDomainChange
}

/// Removed classes in a diff.
list OntologyClassInstanceList {
    member: OntologyClassInstance
}

/// Publish blockers.
list OntologyBlockerList {
    member: PublishBlocker
}

/// Free-form JSON documents in a lifecycle response.
list DocumentList {
    member: Document
}

/// List the versions of one ontology.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/versions", code: 200)
@examples([
    {
        title: "List versions with the current pointer"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core" }
        output: {
            items: [
                {
                    id: "ont-1a2b3c4d5e6f"
                    semver: "1.0.0"
                    status: "published"
                    tripleCount: 1280
                    graph: "urn:platform:graph:tbox:1a2b3c4d"
                    createdAt: "2026-10-01T08:00:00Z"
                    publishedAt: "2026-10-02T09:30:00Z"
                }
            ]
            count: 1
            total: 1
            deprecated: 0
            pointer: {
                name: "tbox/current"
                versionId: "ont-1a2b3c4d5e6f"
                semver: "1.0.0"
                graph: "urn:platform:graph:tbox:1a2b3c4d"
                updatedAt: "2026-10-02T09:30:00Z"
            }
        }
    }
])
operation ListOntologyVersions {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId
    }

    output: OntologyVersionPage

    errors: [
        NotFoundError
    ]
}

/// Read one version with its proposals and audit events.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}", code: 200)
@examples([
    {
        title: "Read one version"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", versionId: "ont-1a2b3c4d5e6f" }
        output: {
            id: "ont-1a2b3c4d5e6f"
            versionId: "ont-1a2b3c4d5e6f"
            semver: "1.0.0"
            status: "published"
            graph: "urn:platform:graph:tbox:1a2b3c4d"
            graphUri: "urn:platform:graph:tbox:1a2b3c4d"
            tripleCount: 1280
            statementCount: 1280
            graphTripleCount: 1280
            createdAt: "2026-10-01T08:00:00Z"
            proposals: []
            events: []
        }
    }
])
operation GetOntologyVersion {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Version to read.
        @required
        @httpLabel
        versionId: OntologyVersionId
    }

    output: OntologyVersionDetail

    errors: [
        NotFoundError
    ]
}

/// Diff one version against another (or against the publish baseline).
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}/diff", code: 200)
@examples([
    {
        title: "Diff a draft against the current version"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", versionId: "ont-draft-9f8e7d6c5b4a", against: "ont-1a2b3c4d5e6f" }
        output: {
            from: "ont-1a2b3c4d5e6f"
            to: "ont-draft-9f8e7d6c5b4a"
            breaking: false
            breakingItems: []
            summary: {
                addedTriples: 12
                removedTriples: 0
                addedClasses: [ "https://example.com/ontology/core#Invoice" ]
                removedClasses: []
                addedProperties: []
                removedProperties: []
                domainChanges: []
                rangeChanges: []
                removedClassInstances: []
            }
        }
    }
])
operation DiffOntologyVersions {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Target version.
        @required
        @httpLabel
        versionId: OntologyVersionId

        /// Baseline version; the current pointer when omitted.
        @httpQuery("against")
        against: OntologyVersionId
    }

    output: OntologyDiff

    errors: [
        NotFoundError
    ]
}

/// Export one version as Turtle or N-Quads text.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}/export", code: 200)
@examples([
    {
        title: "Export a version as Turtle"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", versionId: "ont-1a2b3c4d5e6f", format: "turtle" }
        output: { content: "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n<https://example.com/ontology/core#Invoice> a owl:Class .\n" }
    }
])
operation ExportOntologyVersion {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Version to export.
        @required
        @httpLabel
        versionId: OntologyVersionId

        /// Serialisation; Turtle when omitted.
        @httpQuery("format")
        format: OntologyExportFormat
    }

    output := {
        /// Serialised ontology text, with the media type the server chose
        /// (`text/turtle` or `application/n-quads`).
        @required
        @httpPayload
        content: String
    }

    errors: [
        NotFoundError
    ]
}

/// Register an uploaded ontology as a draft version.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/import", code: 200)
@examples([
    {
        title: "Register a Turtle draft"
        input: {
            namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
            ontologyId: "https://example.com/ontology/core"
            content: "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n<https://example.com/ontology/core#Invoice> a owl:Class .\n"
            format: "turtle"
            changeSummary: "add Invoice class"
        }
        output: {
            importId: "imp-1a2b3c4d5e6f"
            versionId: "ont-draft-9f8e7d6c5b4a"
            targetNamespace: "https://example.com/ontology/core"
            format: "turtle"
            totalTriples: 1
            classes: 1
            objectProperties: 0
            dataProperties: 0
            importsDeclared: []
            importsResolved: []
            unresolvedImports: []
            usable: true
            published: false
            persisted: true
        }
    }
])
operation ImportOntology {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier; also the default target namespace.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Ontology text to parse.
        @required
        content: OntologySourceContent

        /// Serialisation of `content`; Turtle when omitted.
        format: OntologyImportFormat

        /// Summary of what the upload changes.
        changeSummary: OntologyChangeSummary

        /// Author recorded on the import record.
        @length(min: 1, max: 256)
        author: String
    }

    output: OntologyImportResult

    errors: [
        ValidationError
        NotFoundError
    ]
}

/// File a proposal for a registered draft version.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals", code: 200)
@examples([
    {
        title: "Propose a draft against the current version"
        input: {
            namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
            ontologyId: "https://example.com/ontology/core"
            versionId: "ont-draft-9f8e7d6c5b4a"
            rationale: "add Invoice class"
            againstVersion: "ont-1a2b3c4d5e6f"
            actor: "operator"
        }
        output: {
            proposalId: "prop-1a2b3c4d5e6f"
            versionId: "ont-draft-9f8e7d6c5b4a"
            againstVersion: "ont-1a2b3c4d5e6f"
            changeSummary: "add Invoice class"
            status: "proposed"
            breaking: false
        }
    }
])
operation ProposeOntologyVersion {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Draft version the proposal is about.
        @required
        versionId: OntologyVersionId

        /// Why the draft should be published; also used as the change summary.
        @required
        rationale: OntologyChangeSummary

        /// Baseline to diff against; the current pointer when omitted.
        againstVersion: OntologyVersionId

        /// Who files the proposal.
        actor: OntologyActor
    }

    output: OntologyProposal

    errors: [
        ValidationError
        ConflictError
        NotFoundError
    ]
}

/// List the proposals filed for one ontology.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals", code: 200)
@examples([
    {
        title: "List proposals"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core" }
        output: {
            items: [
                {
                    proposalId: "prop-1a2b3c4d5e6f"
                    versionId: "ont-draft-9f8e7d6c5b4a"
                    againstVersion: "ont-1a2b3c4d5e6f"
                    changeSummary: "add Invoice class"
                    status: "proposed"
                    breaking: false
                    versionStatus: "proposed"
                }
            ]
            count: 1
            returned: 1
        }
    }
])
operation ListOntologyProposals {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId
    }

    output: OntologyProposalPage

    errors: [
        NotFoundError
    ]
}

/// Read one proposal with its version and stored diff.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals/{proposalId}", code: 200)
@examples([
    {
        title: "Read one proposal"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", proposalId: "prop-1a2b3c4d5e6f" }
        output: {
            proposal: {
                proposalId: "prop-1a2b3c4d5e6f"
                versionId: "ont-draft-9f8e7d6c5b4a"
                againstVersion: "ont-1a2b3c4d5e6f"
                changeSummary: "add Invoice class"
                status: "proposed"
                breaking: false
            }
            version: {
                id: "ont-draft-9f8e7d6c5b4a"
                semver: "1.1.0"
                status: "proposed"
            }
            versionStatus: "proposed"
            diff: {
                from: "ont-1a2b3c4d5e6f"
                to: "ont-draft-9f8e7d6c5b4a"
                breaking: false
                breakingItems: []
                summary: {
                    addedTriples: 12
                    removedTriples: 0
                    addedClasses: []
                    removedClasses: []
                    addedProperties: []
                    removedProperties: []
                    domainChanges: []
                    rangeChanges: []
                    removedClassInstances: []
                }
            }
        }
    }
])
operation GetOntologyVersionProposal {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Proposal to read.
        @required
        @httpLabel
        proposalId: OntologyProposalId
    }

    output: OntologyProposalDetail

    errors: [
        NotFoundError
    ]
}

/// Approve or reject a proposal.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals/{proposalId}/review", code: 200)
@examples([
    {
        title: "Approve a proposal"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", proposalId: "prop-1a2b3c4d5e6f", decision: "APPROVE", comment: "looks good", actor: "reviewer" }
        output: { ok: true, proposalId: "prop-1a2b3c4d5e6f", versionId: "ont-draft-9f8e7d6c5b4a", status: "approved", versionStatus: "approved", approvedBy: "reviewer" }
    }
])
operation ReviewOntologyProposal {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Proposal to review.
        @required
        @httpLabel
        proposalId: OntologyProposalId

        /// `APPROVE` or `REJECT`.
        @required
        decision: OntologyProposalDecision

        /// Reviewer comment recorded with the decision.
        comment: OntologyReason

        /// Who reviews.
        actor: OntologyActor
    }

    output: OntologyProposalReviewResult

    errors: [
        ValidationError
        ConflictError
        NotFoundError
    ]
}

/// Publish a version, moving the `tbox/current` pointer.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/publish", code: 200)
@examples([
    {
        title: "Plan a publish"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", versionId: "ont-draft-9f8e7d6c5b4a", planOnly: true }
        output: { dryRun: true, versionId: "ont-draft-9f8e7d6c5b4a", versionStatus: "approved", wouldPublish: true, breaking: false, gates: { integrity: { ok: true, triples: 1292, declared: 1292 } }, blockers: [] }
    }
])
operation PublishOntology {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Version to publish.
        @required
        versionId: OntologyVersionId

        /// Proposal that authorises this publish.
        proposalId: OntologyProposalId

        /// Optimistic-concurrency guard: the pointer must still select this
        /// version, otherwise the publish fails closed.
        expectedVersionId: OntologyVersionId

        /// Accept breaking changes recorded in the diff.
        acknowledgeBreaking: Boolean

        /// Re-activate an already registered version instead of staging a new
        /// one.
        publishExisting: Boolean

        /// Run the gates and return the plan without writing anything.
        planOnly: Boolean

        /// Who publishes.
        actor: OntologyActor

        /// Reason recorded on the publish.
        reason: OntologyReason
    }

    output: PublishResult

    errors: [
        ValidationError
        ConflictError
        NotFoundError
    ]
}

/// Roll the `tbox/current` pointer back to an earlier version.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/rollback", code: 200)
@examples([
    {
        title: "Plan a pointer-only rollback"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", targetVersionId: "ont-1a2b3c4d5e6f", mode: "POINTER_ONLY", planOnly: true }
        output: {
            mode: "POINTER_ONLY"
            target: { id: "ont-1a2b3c4d5e6f", semver: "1.0.0", status: "superseded" }
            targetVersionId: "ont-1a2b3c4d5e6f"
            targetTriples: 1280
            wouldChangePointer: true
        }
    }
])
operation RollbackOntology {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Version to restore.
        @required
        targetVersionId: OntologyVersionId

        /// `POINTER_ONLY` or `NEW_VERSION`; required so the effect is explicit.
        @required
        mode: OntologyRollbackMode

        /// Optimistic-concurrency guard for `POINTER_ONLY`.
        expectedVersionId: OntologyVersionId

        /// Return the plan only; nothing is written.
        planOnly: Boolean

        /// Who rolls back.
        actor: OntologyActor

        /// Reason recorded on the rollback.
        reason: OntologyReason
    }

    output: OntologyRollbackResult

    errors: [
        ValidationError
        ConflictError
        NotFoundError
    ]
}

/// List the hash-chained lifecycle audit events for one ontology.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/events", code: 200)
@examples([
    {
        title: "List publish and rollback events"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", limit: 50 }
        output: {
            items: [
                {
                    eventId: 41
                    versionId: "ont-1a2b3c4d5e6f"
                    action: "published"
                    actor: "operator"
                    createdAt: "2026-10-02T09:30:00Z"
                    type: "published"
                    at: "2026-10-02T09:30:00Z"
                    category: "published"
                }
            ]
            count: 1
            categories: { published: 1, rolled_back: 0, superseded: 0, other: 0 }
        }
    }
])
operation ListOntologyEvents {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Only events for this version.
        @httpQuery("versionId")
        versionId: OntologyVersionId

        /// Only events with this action.
        @httpQuery("action")
        @length(min: 1, max: 64)
        action: String

        /// Maximum events to return (1-1000).
        @httpQuery("limit")
        @range(min: 1, max: 1000)
        limit: Integer
    }

    output: OntologyEventPage

    errors: [
        NotFoundError
    ]
}

/// Recompute the lifecycle and PROV hash chains and report broken links.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/verify", code: 200)
@examples([
    {
        title: "Verify both audit chains"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core" }
        output: { ok: true, checked: 41, prov: { ok: true, checked: 12, graph: "urn:platform:graph:prov" } }
    }
])
operation VerifyOntology {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId
    }

    output: OntologyVerifyResult
}
