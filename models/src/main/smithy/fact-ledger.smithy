// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// A-Box fact-ledger read and lifecycle operations.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.1 rows F28, F32, F35-F38, and
// doc/coa-x/18-platform-core拆解.md §KERNEL facts routes. The adjudication
// write (`ResolveFactConflicts`, including `batch`) lives in facts.smithy; this
// file adds the reads and the two lifecycle writes the bridge already serves so
// they do not disappear when platform-core is split out of coa_api_local.py.
$version: "2"

namespace com.amazon.semanticcontext.facts

use com.amazon.semanticcontext.common#ConflictError
use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#Uuid

/// Lifecycle state of one assertion row.
enum FactState {
    /// The row currently backs the A-Box graph.
    active

    /// The row was withdrawn; the assertion is no longer asserted.
    retracted

    /// A newer merged row replaced this one.
    superseded
}

/// Filter for `ListFacts.state`.
enum FactStateFilter {
    /// Only active rows.
    active

    /// Only retracted rows.
    retracted

    /// Only superseded rows.
    superseded

    /// Rows in any state (the default).
    all
}

/// Level of detail for `ListFactEvents`.
enum FactEventFormat {
    /// Full event payload, including the stored JSON document.
    full

    /// Event header only: no payload document.
    summary
}

/// Kind of RDF term in the object position.
enum FactObjectKind {
    /// Object is an IRI.
    iri

    /// Object is a literal value.
    literal
}

/// Source family recorded on an assertion row.
enum FactSourceKind {
    /// Extracted from a document.
    document

    /// Loaded from a table.
    table

    /// Entered by an operator.
    manual

    /// Written by a merge adjudication.
    merge
}

/// RDF object of an assertion row.
structure FactObject {
    /// `iri` or `literal`.
    @required
    kind: String

    /// Lexical value of the object.
    @required
    value: String

    /// IRI form of the object; present when `kind` is `iri`.
    iri: String
}

/// Provenance attached to an assertion row.
structure FactSource {
    /// Source family: `document`, `table`, `manual`, or `merge`.
    kind: String

    /// Document that produced the row, when any.
    documentId: Uuid

    /// Ingestion run that produced the row, when any.
    runId: String

    /// Extraction candidate that produced the row, when any.
    candidateId: String
}

/// One entry in a fact's hash-chained event history.
structure FactEvent {
    /// Monotonic event identifier within the ledger.
    @required
    eventId: Integer

    /// Fact the event belongs to.
    @required
    factId: FactId

    /// Event name, e.g. `assert`, `retract`, `restore`, `merge`, `undo`.
    @required
    action: String

    /// Identity that performed the action.
    actor: String

    /// Why the action was taken.
    reason: String

    /// Batch identifier shared by a bulk operation.
    batchId: String

    /// Event-specific payload written by the ledger.
    payload: Document

    /// Previous event in the hash chain; absent for the first event.
    prevEvent: Integer

    /// Hash of this event, chained from `prevEvent`.
    hash: String

    /// When the event was written (ISO-8601).
    createdAt: String
}

list FactEventList {
    member: FactEvent
}

/// One assertion row as returned by the ledger.
structure FactRecord {
    /// Stable assertion-row identifier.
    @required
    factId: FactId

    /// Subject IRI.
    @required
    subject: FactIri

    /// Predicate IRI.
    @required
    predicate: FactIri

    /// Object of the assertion.
    @required
    object: FactObject

    /// Named graph the assertion belongs to.
    @required
    graph: FactIri

    /// Lifecycle state of the row.
    @required
    state: FactState

    /// Where the row came from.
    source: FactSource

    /// When the row was first asserted (ISO-8601).
    assertedAt: String

    /// When the row was retracted (ISO-8601); absent while active.
    retractedAt: String

    /// Reason recorded on retraction.
    retractReason: String

    /// True when the caller accepted the conflict without picking a value.
    acceptedConflict: Boolean

    /// Adjudication applied to the row: `keep`, `keep_both`, or `merge`.
    resolution: String

    /// Identity that adjudicated the conflict.
    resolvedBy: String

    /// When the conflict was adjudicated (ISO-8601).
    resolvedAt: String

    /// Row that superseded this one after a merge.
    supersededBy: String

    /// Rows merged into this one.
    @length(min: 0, max: 500)
    mergedFrom: FactIdList

    /// True when the (subject, predicate) group currently has a conflict.
    conflict: Boolean

    /// True when an identical assertion row already existed and was reused by
    /// `AssertFact`; absent on reads.
    duplicate: Boolean

    /// Event history, present only on `GetFact` with events requested.
    events: FactEventList
}

list FactRecordList {
    member: FactRecord
}

/// One fact backing a conflicting value.
structure FactConflictFact {
    /// Assertion-row identifier.
    @required
    factId: FactId

    /// Object value this row asserts.
    @required
    object: String

    /// `iri` or `literal`.
    @required
    objectKind: String

    /// Where the row came from.
    source: FactSource

    /// When the row was asserted (ISO-8601).
    assertedAt: String

    /// Text evidence that produced the row.
    evidence: FactConflictEvidence
}

/// Text evidence attached to a conflicting row.
structure FactConflictEvidence {
    /// Chunk identifier inside the source document.
    chunkId: String

    /// Text span that produced the value.
    text: String
}

list FactConflictFactList {
    member: FactConflictFact
}

/// One (subject, predicate) group with more than one active value.
structure FactConflict {
    /// Subject IRI shared by the group.
    @required
    subject: FactIri

    /// Predicate IRI shared by the group.
    @required
    predicate: FactIri

    /// Distinct values in the group.
    @required
    @length(min: 0, max: 500)
    values: FactIriList

    /// True when the group was accepted as a conflict without a single winner.
    @required
    accepted: Boolean

    /// True when the group still needs a decision.
    @required
    pending: Boolean

    /// Rows backing the group.
    @required
    facts: FactConflictFactList
}

list FactConflictItemList {
    member: FactConflict
}

/// One event in an adjudication's history.
structure FactAdjudicationEvent {
    /// Monotonic event identifier.
    @required
    eventId: Integer

    /// Event name (`keep`, `keep_both`, `merge`, `undo`).
    @required
    action: String

    /// Identity that performed the action.
    actor: String

    /// Why the action was taken.
    reason: String

    /// When the event was written (ISO-8601).
    @required
    at: String

    /// Event-specific payload.
    payload: Document
}

list FactAdjudicationEventList {
    member: FactAdjudicationEvent
}

/// The decision that a subsequent undo reverted.
structure FactUndoReference {
    /// Event identifier of the undo.
    @required
    eventId: Integer

    /// Identity that performed the undo.
    actor: String

    /// Why the decision was undone.
    reason: String

    /// When the undo was written (ISO-8601).
    @required
    at: String
}

/// Effective state of a conflict group after replaying its adjudications.
structure FactAdjudicationEffective {
    /// Number of active rows in the group.
    @required
    activeCount: Integer

    /// Values still active.
    @required
    @length(min: 0, max: 500)
    values: FactIriList

    /// True when the active values still conflict.
    @required
    conflict: Boolean

    /// True when the conflict was explicitly accepted.
    @required
    acceptedConflict: Boolean
}

/// Adjudication summary for one conflict group.
structure FactAdjudication {
    /// Subject IRI.
    @required
    subject: FactIri

    /// Predicate IRI.
    @required
    predicate: FactIri

    /// Event identifier of the effective decision; absent before any decision.
    eventId: Integer

    /// Action of the effective decision; absent before any decision.
    action: String

    /// Identity that made the effective decision.
    actor: String

    /// Why the effective decision was made.
    reason: String

    /// When the effective decision was made (ISO-8601).
    @required
    at: String

    /// `in_effect` when the decision still applies, `undone` after an undo.
    @required
    status: String

    /// Value kept by a `keep` decision.
    kept: String

    /// Values the group had when the decision was made.
    @required
    @length(min: 0, max: 500)
    values: FactIriList

    /// Merged value written by a `merge` decision.
    object: String

    /// Undo that reverted this decision, when status is `undone`.
    undoneBy: FactUndoReference

    /// Full adjudication history, oldest first.
    @required
    history: FactAdjudicationEventList

    /// State recomputed from the surviving rows.
    @required
    effective: FactAdjudicationEffective
}

list FactAdjudicationList {
    member: FactAdjudication
}

/// Facts matching a `ListFacts` query.
structure FactList {
    /// State filter that produced this page; `all` when not narrowed.
    @required
    state: String

    /// Rows in ledger order.
    @required
    items: FactRecordList

    /// Number of rows in this page.
    @required
    count: Integer

    /// Conflict groups touching the returned rows.
    conflicts: FactConflictItemList
}

/// Conflict groups and their adjudication state.
structure FactConflictList {
    /// Groups in ledger order.
    @required
    conflicts: FactConflictItemList

    /// Number of groups in this page.
    @required
    count: Integer

    /// Groups that still need a decision.
    @required
    pending: Integer

    /// True when accepted conflicts were included.
    includeAccepted: Boolean

    /// Adjudication summary for every returned group.
    adjudications: FactAdjudicationList
}

/// Result of undoing an adjudication.
///
/// `keep` and `keep_both` undo restore the retired rows and return them under
/// `restoredFactIds`; `merge` undo removes the merged row and restores the
/// originals under `restoredFactIds`. `dryRun` fills the same members without
/// writing anything.
structure FactUndoResult {
    /// True when the call only previewed the undo.
    @required
    dryRun: Boolean

    /// Event identifier written by the undo; absent on a dry run.
    eventId: Integer

    /// Subject IRI of the undone group.
    @required
    subject: FactIri

    /// Predicate IRI of the undone group.
    @required
    predicate: FactIri

    /// Action that was undone.
    @required
    undoneAction: String

    /// Rows restored by the undo.
    @length(min: 0, max: 500)
    restoredFactIds: FactIdList

    /// Merged row removed by the undo (`merge` only).
    mergedFactId: String

    /// Active values after the undo.
    @length(min: 0, max: 500)
    values: FactIriList

    /// True when the group conflicts again after the undo.
    conflict: Boolean
}

/// One fact selected by a batch retract.
structure FactRetractItem {
    /// Assertion-row identifier.
    @required
    factId: FactId

    /// Subject IRI.
    @required
    subject: FactIri

    /// Predicate IRI.
    @required
    predicate: FactIri

    /// Object value.
    @required
    object: String

    /// `iri` or `literal`.
    @required
    objectKind: String

    /// Named graph.
    @required
    graph: FactIri

    /// Extraction candidate that produced the row, when any.
    candidateId: String
}

list FactRetractItemList {
    member: FactRetractItem
}

/// One fact skipped by a batch retract.
structure FactRetractSkipped {
    /// Assertion-row identifier.
    @required
    factId: FactId

    /// Why the row was skipped.
    @required
    reason: String
}

list FactRetractSkippedList {
    member: FactRetractSkipped
}

/// Result of a batch retract.
///
/// `dryRun` defaults to true: an omitted flag can only preview. When `dryRun`
/// is false, `batchId` is set and every retracted row shares it.
structure FactBatchRetractResult {
    /// True when the call only previewed the retract.
    @required
    dryRun: Boolean

    /// Batch identifier written by the retract; absent on a dry run.
    batchId: String

    /// Number of rows that are (or would be) retracted.
    @required
    count: Integer

    /// Rows that are (or would be) retracted.
    @required
    items: FactRetractItemList

    /// Rows filtered out of the selection.
    @required
    skipped: FactRetractSkippedList

    /// Identity recorded on the audit events.
    @required
    actor: String

    /// Why the rows were retracted.
    reason: String

    /// Identifiers of the retracted rows; absent on a dry run.
    @length(min: 0, max: 500)
    retracted: FactIdList
}

/// One page of a fact's event chain.
structure FactEventPage {
    /// Fact the page belongs to.
    @required
    factId: FactId

    /// Number of events in this page.
    @required
    count: Integer

    /// Total number of events on the chain.
    @required
    total: Integer

    /// Events, newest first.
    @required
    items: FactEventList

    /// Pass back as `before` to page further back; absent at the start.
    nextBefore: Integer
}

/// List assertion rows in this namespace.
///
/// All filters are optional and combine with AND. `limit` is capped by the
/// ledger at 500 rows.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/facts", code: 200)
@examples([
    {
        title: "List active facts for one subject"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", subject: "urn:coa:entity:contract-ledger", state: "active", limit: 50 }
        output: {
            state: "active"
            count: 1
            items: [
                {
                    factId: "fact-1a2b3c4d5e6f"
                    subject: "urn:coa:entity:contract-ledger"
                    predicate: "urn:coa:predicate:belongs-to"
                    object: { kind: "iri", value: "urn:coa:entity:archive", iri: "urn:coa:entity:archive" }
                    graph: "urn:coa:graph:asserted"
                    state: "active"
                    assertedAt: "2026-10-01T08:00:00Z"
                    conflict: false
                }
            ]
        }
    }
])
operation ListFacts {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Only rows in this state; `all` when omitted.
        @httpQuery("state")
        state: FactStateFilter

        /// Only rows with this subject.
        @httpQuery("subject")
        subject: FactIri

        /// Only rows with this predicate.
        @httpQuery("predicate")
        predicate: FactIri

        /// Only rows produced by this document.
        @httpQuery("sourceDocumentId")
        sourceDocumentId: Uuid

        /// When true, only rows in a conflicting group; when false, only rows
        /// outside a conflict.
        @httpQuery("conflict")
        conflict: Boolean

        /// Maximum rows to return (1-500).
        @httpQuery("limit")
        @range(min: 1, max: 500)
        limit: Integer
    }

    output: FactList

    errors: [
        NotFoundError
    ]
}

/// Read one assertion row by identifier.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/facts/{factId}", code: 200)
@examples([
    {
        title: "Read one fact"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", factId: "fact-1a2b3c4d5e6f" }
        output: {
            factId: "fact-1a2b3c4d5e6f"
            subject: "urn:coa:entity:contract-ledger"
            predicate: "urn:coa:predicate:belongs-to"
            object: { kind: "literal", value: "contract-ledger" }
            graph: "urn:coa:graph:asserted"
            state: "active"
            assertedAt: "2026-10-01T08:00:00Z"
            conflict: false
        }
    }
])
operation GetFact {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Assertion-row identifier.
        @required
        @httpLabel
        factId: FactId
    }

    output: FactRecord

    errors: [
        NotFoundError
    ]
}

/// List (subject, predicate) groups that hold more than one active value.
///
/// Accepted conflicts are omitted unless `includeAccepted` is true. Each group
/// carries its full adjudication history so the console can render undo.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/facts/conflicts", code: 200)
@examples([
    {
        title: "List pending conflicts"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", includeAccepted: false }
        output: {
            count: 1
            pending: 1
            includeAccepted: false
            conflicts: [
                {
                    subject: "urn:coa:entity:contract-ledger"
                    predicate: "urn:coa:predicate:belongs-to"
                    values: ["urn:coa:entity:archive", "urn:coa:entity:legal"]
                    accepted: false
                    pending: true
                    facts: [
                        { factId: "fact-1a2b3c4d5e6f", object: "urn:coa:entity:archive", objectKind: "iri" }
                        { factId: "fact-0f1e2d3c4b5a", object: "urn:coa:entity:legal", objectKind: "iri" }
                    ]
                }
            ]
            adjudications: [
                {
                    subject: "urn:coa:entity:contract-ledger"
                    predicate: "urn:coa:predicate:belongs-to"
                    at: "2026-10-01T08:00:00Z"
                    status: "in_effect"
                    values: ["urn:coa:entity:archive", "urn:coa:entity:legal"]
                    history: []
                    effective: { activeCount: 2, values: ["urn:coa:entity:archive", "urn:coa:entity:legal"], conflict: true, acceptedConflict: false }
                }
            ]
        }
    }
])
operation ListFactConflicts {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Include groups the caller already accepted; false by default.
        @httpQuery("includeAccepted")
        includeAccepted: Boolean
    }

    output: FactConflictList

    errors: [
        NotFoundError
    ]
}

/// Undo the effective adjudication of one conflict group.
///
/// Identify the group either by `eventId` (the adjudication event) or by
/// `subject` + `predicate`. `dryRun` is the safe default: it reports the rows
/// and values the undo would change without writing.
@http(method: "POST", uri: "/namespaces/{namespaceId}/facts/conflicts/undo", code: 200)
@examples([
    {
        title: "Preview undoing a keep decision"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", eventId: 41, actor: "operator", reason: "wrong value kept", dryRun: true }
        output: {
            dryRun: true
            subject: "urn:coa:entity:contract-ledger"
            predicate: "urn:coa:predicate:belongs-to"
            undoneAction: "keep"
            restoredFactIds: ["fact-0f1e2d3c4b5a"]
            values: ["urn:coa:entity:archive", "urn:coa:entity:legal"]
            conflict: true
        }
    }
])
operation UndoFactConflictResolution {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Adjudication event to undo; alternative to subject + predicate.
        @range(min: 1, max: 2147483647)
        eventId: Integer

        /// Subject of the group; required when `eventId` is absent.
        subject: FactIri

        /// Predicate of the group; required when `eventId` is absent.
        predicate: FactIri

        /// Identity recorded on the undo event; defaults to `operator`.
        @length(min: 1, max: 256)
        actor: String

        /// Why the decision is being undone.
        @length(min: 0, max: 1024)
        reason: String

        /// Preview only; defaults to true.
        dryRun: Boolean
    }

    output: FactUndoResult

    errors: [
        ConflictError
        NotFoundError
    ]
}

/// Withdraw one assertion row.
///
/// Retracting an already retracted row is a no-op that returns its current
/// state. The event chain records the actor and reason.
@http(method: "POST", uri: "/namespaces/{namespaceId}/facts/{factId}/retract", code: 200)
@examples([
    {
        title: "Retract one fact"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", factId: "fact-1a2b3c4d5e6f", actor: "operator", reason: "superseded by source" }
        output: {
            factId: "fact-1a2b3c4d5e6f"
            subject: "urn:coa:entity:contract-ledger"
            predicate: "urn:coa:predicate:belongs-to"
            object: { kind: "iri", value: "urn:coa:entity:archive", iri: "urn:coa:entity:archive" }
            graph: "urn:coa:graph:asserted"
            state: "retracted"
            retractedAt: "2026-10-02T09:00:00Z"
            retractReason: "superseded by source"
        }
    }
])
operation RetractFact {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Assertion-row identifier.
        @required
        @httpLabel
        factId: FactId

        /// Identity recorded on the retract event; defaults to `api`.
        @length(min: 1, max: 256)
        actor: String

        /// Why the row is withdrawn.
        @length(min: 0, max: 1024)
        reason: String
    }

    output: FactRecord

    errors: [
        ConflictError
        NotFoundError
    ]
}

/// Withdraw many assertion rows in one ledger transaction.
///
/// Selection is either an explicit `factIds` list or the `subject`,
/// `predicate`, `graph` and `sourceDocumentId` filters. `dryRun` defaults to
/// true so an omitted flag can only preview the change.
@http(method: "POST", uri: "/namespaces/{namespaceId}/facts/retract", code: 200)
@examples([
    {
        title: "Preview retracting one source's facts"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", sourceDocumentId: "8c7d6e5f-4a3b-4c2d-8e1f-0a9b8c7d6e5f", actor: "operator", reason: "source withdrawn", dryRun: true }
        output: {
            dryRun: true
            count: 1
            items: [
                {
                    factId: "fact-1a2b3c4d5e6f"
                    subject: "urn:coa:entity:contract-ledger"
                    predicate: "urn:coa:predicate:belongs-to"
                    object: "urn:coa:entity:archive"
                    objectKind: "iri"
                    graph: "urn:coa:graph:asserted"
                }
            ]
            skipped: []
            actor: "operator"
            reason: "source withdrawn"
        }
    }
])
operation RetractFacts {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Explicit rows to retract (1-500); wins over the filters.
        @length(min: 1, max: 500)
        factIds: FactIdList

        /// Filter: only rows with this subject.
        subject: FactIri

        /// Filter: only rows with this predicate.
        predicate: FactIri

        /// Filter: only rows in this named graph.
        graph: FactIri

        /// Filter: only rows produced by this document.
        sourceDocumentId: Uuid

        /// Identity recorded on every retract event; defaults to `operator`.
        @length(min: 1, max: 256)
        actor: String

        /// Why the rows are withdrawn.
        @length(min: 0, max: 1024)
        reason: String

        /// Preview only; defaults to true.
        dryRun: Boolean
    }

    output: FactBatchRetractResult

    errors: [
        ConflictError
        NotFoundError
    ]
}

/// Restore a retracted assertion row.
///
/// Restoring an active row is a no-op that returns its current state.
@http(method: "POST", uri: "/namespaces/{namespaceId}/facts/{factId}/restore", code: 200)
@examples([
    {
        title: "Restore a retracted fact"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", factId: "fact-1a2b3c4d5e6f", actor: "operator", reason: "retracted in error" }
        output: {
            factId: "fact-1a2b3c4d5e6f"
            subject: "urn:coa:entity:contract-ledger"
            predicate: "urn:coa:predicate:belongs-to"
            object: { kind: "iri", value: "urn:coa:entity:archive", iri: "urn:coa:entity:archive" }
            graph: "urn:coa:graph:asserted"
            state: "active"
            assertedAt: "2026-10-01T08:00:00Z"
            conflict: false
        }
    }
])
operation RestoreFact {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Assertion-row identifier.
        @required
        @httpLabel
        factId: FactId

        /// Identity recorded on the restore event; defaults to `api`.
        @length(min: 1, max: 256)
        actor: String
    }

    output: FactRecord

    errors: [
        ConflictError
        NotFoundError
    ]
}

/// Read one page of a fact's hash-chained event history.
///
/// Events are returned newest first. Pass `nextBefore` back as `before` to page
/// further back in the chain.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/facts/{factId}/events", code: 200)
@examples([
    {
        title: "Read a fact's event chain"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", factId: "fact-1a2b3c4d5e6f", limit: 20, format: "summary" }
        output: {
            factId: "fact-1a2b3c4d5e6f"
            count: 1
            total: 1
            items: [
                { eventId: 41, factId: "fact-1a2b3c4d5e6f", action: "assert", actor: "operator", createdAt: "2026-10-01T08:00:00Z" }
            ]
        }
    }
])
operation ListFactEvents {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Assertion-row identifier.
        @required
        @httpLabel
        factId: FactId

        /// Maximum events to return (1-200).
        @httpQuery("limit")
        @range(min: 1, max: 200)
        limit: Integer

        /// Return events strictly older than this event identifier.
        @httpQuery("before")
        @range(min: 0, max: 2147483647)
        before: Integer

        /// `full` includes the payload document; `summary` omits it.
        @httpQuery("format")
        format: FactEventFormat
    }

    output: FactEventPage

    errors: [
        NotFoundError
    ]
}

/// Record one assertion row directly.
///
/// This is the operator-facing write path, separate from extraction candidates.
/// It is idempotent on (subject, predicate, object, graph, source document,
/// source run): an identical active row is returned with `duplicate: true`.
@http(method: "POST", uri: "/namespaces/{namespaceId}/facts", code: 200)
@examples([
    {
        title: "Record one fact"
        input: {
            namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
            subject: "urn:coa:entity:contract-ledger"
            predicate: "urn:coa:predicate:belongs-to"
            object: "urn:coa:entity:archive"
            objectKind: "iri"
            graph: "urn:coa:graph:asserted"
            actor: "operator"
        }
        output: {
            factId: "fact-1a2b3c4d5e6f"
            subject: "urn:coa:entity:contract-ledger"
            predicate: "urn:coa:predicate:belongs-to"
            object: { kind: "iri", value: "urn:coa:entity:archive", iri: "urn:coa:entity:archive" }
            graph: "urn:coa:graph:asserted"
            state: "active"
            assertedAt: "2026-10-01T08:00:00Z"
            conflict: false
            duplicate: false
        }
    }
])
operation AssertFact {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Subject IRI.
        @required
        subject: FactIri

        /// Predicate IRI.
        @required
        predicate: FactIri

        /// Object value; an IRI when `objectKind` is `iri`.
        @required
        @length(min: 1, max: 4096)
        object: String

        /// `iri` or `literal`.
        @required
        objectKind: FactObjectKind

        /// Named graph the assertion belongs to.
        graph: FactIri

        /// Source family recorded on the row.
        sourceKind: FactSourceKind

        /// Document that produced the row, when any.
        sourceDocumentId: Uuid

        /// Ingestion run that produced the row, when any.
        @length(min: 0, max: 256)
        sourceRunId: String

        /// Identity recorded on the assert event.
        @length(min: 1, max: 256)
        actor: String
    }

    output: FactRecord

    errors: [
        ConflictError
        NotFoundError
    ]
}

/// Apply one explicit `keep A` rule to every pending conflict in a scope.
///
/// This is the dedicated `/facts/conflicts/batch` route. It uses the same
/// ledger transaction as `ResolveFactConflicts` with `action: "batch"`; the
/// route is kept because early callers post here directly. `dryRun` defaults
/// to true, so an omitted flag can only preview.
@http(method: "POST", uri: "/namespaces/{namespaceId}/facts/conflicts/batch", code: 200)
@examples([
    {
        title: "Preview a batch keep"
        input: {
            namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
            keep: "urn:coa:entity:archive"
            predicate: "urn:coa:predicate:belongs-to"
            actor: "operator"
            reason: "archive is the canonical owner"
            dryRun: true
        }
        output: {
            batchId: "resolve-1a2b3c4d5e"
            dryRun: true
            keep: "urn:coa:entity:archive"
            matched: 1
            kept: 1
            skipped: 0
            affectedFacts: 0
            predicate: "urn:coa:predicate:belongs-to"
            results: [
                {
                    subject: "urn:coa:entity:contract-ledger"
                    predicate: "urn:coa:predicate:belongs-to"
                    status: "would_keep"
                    retired: 0
                    values: ["urn:coa:entity:archive", "urn:coa:entity:legal"]
                }
            ]
        }
    }
])
operation BatchKeepFactConflicts {
    input := {
        /// Namespace that owns the ledger partition.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Value to keep in every matched group; required.
        @required
        keep: FactIri

        /// Only groups with this predicate.
        predicate: FactIri

        /// Only groups with this subject.
        subject: FactIri

        /// Only groups that contain a row from this document.
        sourceDocumentId: Uuid

        /// Identity recorded on every adjudication event; defaults to
        /// `operator`.
        @length(min: 1, max: 256)
        actor: String

        /// Why the rule is applied.
        @length(min: 0, max: 1024)
        reason: String

        /// Preview only; defaults to true.
        dryRun: Boolean
    }

    output: FactBatchKeepResult

    errors: [
        ConflictError
        NotFoundError
    ]
}
