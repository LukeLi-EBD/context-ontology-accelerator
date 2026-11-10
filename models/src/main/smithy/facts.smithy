// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// A-Box fact-ledger adjudication operations.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.1 rows F29–F33. One operation
// covers all four adjudications because the console treats them as one
// decision surface: `keep`, `keep_both`, `merge` act on one (subject,
// predicate) group, `batch` applies one `keep` rule to every pending group
// inside an explicit scope. The path is namespace-scoped like every other
// operation; the service definition lives in control-plane.smithy.
$version: "2"

namespace com.amazon.semanticcontext.facts

use com.amazon.semanticcontext.common#ConflictError
use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#Uuid

/// IRI of a subject, predicate or object in the namespace A-Box.
@length(min: 1, max: 2048)
string FactIri

/// Identifier of a fact assertion row.
@length(min: 1, max: 64)
string FactId

list FactIdList {
    member: FactId
}

list FactIriList {
    member: FactIri
}

/// Adjudication applied to a conflict group. Wire values stay lowercase
/// because the ledger and the console have used them since the first
/// release; the model follows the wire rather than renaming it.
enum FactConflictAction {
    /// Keep one value, retire the others.
    keep

    /// Accept the conflict: every value stays active.
    keep_both

    /// Retire every conflicting value and record one merged value.
    merge

    /// Apply one `keep` rule to every pending group inside the scope.
    batch
}

/// One group of a batch keep. `status` is one of `would_keep` (dry run),
/// `kept`, or `skipped`.
structure FactBatchKeepRow {
    @required
    subject: FactIri

    @required
    predicate: FactIri

    /// One of `would_keep` (dry run), `kept`, or `skipped`.
    @required
    status: String

    /// Facts retired by this row (0 for a skipped group).
    retired: Integer

    /// Why the group was skipped.
    reason: String

    /// Values the group had before the decision.
    values: FactIriList

    /// Assertion rows kept by a `kept` row; absent on a dry run.
    keptFactIds: FactIdList

    /// Assertion rows retired by a `kept` row; absent on a dry run.
    retiredFactIds: FactIdList
}

list FactBatchKeepRowList {
    member: FactBatchKeepRow
}

/// Result of `batch`: the scope that was applied and what it touched.
structure FactBatchKeepResult {
    /// Identifier shared by every event this batch wrote.
    @required
    batchId: String

    /// True when nothing was written (the default).
    @required
    dryRun: Boolean

    /// Value the rule keeps.
    @required
    keep: FactIri

    /// Pending groups inside the scope.
    @required
    matched: Integer

    /// Groups kept (or that would be kept, on a dry run).
    @required
    kept: Integer

    /// Groups where `keep` is not one of the values.
    @required
    skipped: Integer

    /// Facts retired across the matched groups.
    @required
    affectedFacts: Integer

    /// Scope the caller supplied; absent members did not narrow it.
    subject: FactIri

    predicate: FactIri

    sourceDocumentId: Uuid

    /// Per-group outcome, in ledger order.
    results: FactBatchKeepRowList
}

/// Outcome of one adjudication. Only the members for the chosen `action` are
/// populated: `keep` fills kept/retired, `keep_both` fills acceptedFactIds,
/// `merge` fills mergedFactId/originalFactIds, `batch` fills batch.
structure FactConflictResolutionOutcome {
    @required
    action: FactConflictAction

    /// Conflict group subject; absent on `batch` when the scope did not
    /// narrow by subject.
    subject: FactIri

    /// Conflict group predicate; absent on `batch` when the scope did not
    /// narrow by predicate.
    predicate: FactIri

    /// Value kept by `keep`.
    kept: FactIri

    /// Assertion rows kept by `keep`.
    keptFactIds: FactIdList

    /// Assertion rows retired by `keep`.
    retiredFactIds: FactIdList

    /// Number of retired rows (`keep`).
    retired: Integer

    /// Values the group had before the decision.
    values: FactIriList

    /// Assertion rows accepted by `keep_both`.
    acceptedFactIds: FactIdList

    /// New assertion row written by `merge`.
    mergedFactId: String

    /// Rows `merge` retired, in ledger order.
    originalFactIds: FactIdList

    /// Batch outcome (`batch` only).
    batch: FactBatchKeepResult
}

/// Adjudicate fact conflicts for this namespace.
///
/// `keep` and `keep_both` require `subject` + `predicate`. `merge` also
/// requires `mergedObject` (an IRI unless `mergedObjectKind` is `literal`).
/// `batch` requires `keep` plus at least one scope member
/// (`predicate`, `subject` or `sourceDocumentId`) and previews by default:
/// nothing is written unless `dryRun` is false.
@http(method: "POST", uri: "/namespaces/{namespaceId}/facts/conflicts/resolve", code: 200)
@examples([
    {
        title: "Merge two conflicting values"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", subject: "urn:coa:entity:contract-ledger", predicate: "urn:coa:predicate:belongs-to", action: "merge", mergedObject: "urn:coa:entity:archive" }
        output: {
            action: "merge"
            subject: "urn:coa:entity:contract-ledger"
            predicate: "urn:coa:predicate:belongs-to"
            mergedFactId: "fact-1a2b3c4d5e6f"
            originalFactIds: ["fact-0f1e2d3c4b5a", "fact-a9b8c7d6e5f4"]
        }
    }
    {
        title: "Preview a batch keep for one predicate"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", action: "batch", keep: "urn:coa:entity:archive", predicate: "urn:coa:predicate:belongs-to", dryRun: true }
        output: {
            action: "batch"
            predicate: "urn:coa:predicate:belongs-to"
            batch: { batchId: "resolve-1a2b3c4d5e", dryRun: true, keep: "urn:coa:entity:archive", matched: 3, kept: 3, skipped: 0, affectedFacts: 3 }
        }
    }
])
operation ResolveFactConflicts {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Conflict group subject. Required unless `action` is `batch`.
        subject: FactIri

        /// Conflict group predicate. Required unless `action` is `batch`.
        predicate: FactIri

        @required
        action: FactConflictAction

        /// Value to keep (`batch` only; `keep` takes it from `keep` on the
        /// console path, which sends the chosen value here too).
        keep: FactIri

        /// Value that replaces the conflicting ones (`merge`).
        mergedObject: FactIri

        /// `iri` (default) or `literal`.
        @length(min: 1, max: 16)
        mergedObjectKind: String

        /// Graph for the merged fact; defaults to the group's graph.
        graph: FactIri

        /// Scope by source document (`batch`).
        sourceDocumentId: Uuid

        /// Preview only (`batch`); defaults to true.
        dryRun: Boolean

        /// Identity recorded on the audit event; defaults to `operator`.
        @length(min: 1, max: 256)
        actor: String

        /// Why the decision was taken.
        @length(min: 0, max: 1024)
        reason: String
    }

    output: FactConflictResolutionOutcome

    errors: [
        ConflictError
        NotFoundError
    ]
}
