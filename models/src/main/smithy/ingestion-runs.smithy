// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// P8 / D-group F17+F18: namespace-scoped ingestion run listing.
//
// ── Merge instructions (this file is branch-local; main is untouched) ──
// 1) In models/src/main/smithy/control-plane.smithy, add one line to the
//    `use com.amazon.semanticcontext.common#...` block:
//
//        use com.amazon.semanticcontext.ingestion#ListIngestionRuns
//
// 2) In the same file, inside `service ControlPlaneService { operations: [ ... ] }`,
//    add one line immediately after `ListDocumentChunks`:
//
//        ListIngestionRuns
//
// Nothing else in control-plane.smithy changes. The operation, its IO shapes,
// and the enums all live in this file under their own namespace.
//
// ── Scope note ──
// The task names this op `ListIngestionRuns(kind=BATCH)`. Only the BATCH family
// is defined here (one row per `platform import` root directory). `kind` is
// accepted as an explicit discriminator and defaults to BATCH; any other wire
// value is rejected by the server with ValidationError rather than silently
// treated as BATCH. No ITEM-kind enum value is declared in this batch, so the
// generated client cannot request an unimplemented family.
$version: "2"

namespace com.amazon.semanticcontext.ingestion

use com.amazon.semanticcontext.common#PaginatedOutput
use com.amazon.semanticcontext.common#PaginationToken
use com.amazon.semanticcontext.common#Uuid
use com.amazon.semanticcontext.common#ValidationError

/// Lifecycle state of one ingestion run, mirroring platform.import_batch.status.
enum IngestionRunStatus {
    /// Import is currently writing items.
    RUNNING

    /// Every discovered item was processed (indexed or failed).
    COMPLETED

    /// The run was stopped before finishing and can be resumed.
    INTERRUPTED

    /// The run's lease expired and a recovery pass marked it stale.
    STALE
}

/// Which ingestion run family to list.
enum IngestionRunKind {
    /// Directory imports recorded in platform.import_batch.
    BATCH
}

/// One import batch and its per-item counters.
structure IngestionRun {
    /// Stable batch identifier (platform.import_batch.batch_id).
    @required
    runId: Uuid

    /// Filesystem root that was imported.
    @required
    root: String

    /// Current lifecycle state.
    @required
    status: IngestionRunStatus

    /// True when status is STALE.
    @required
    stale: Boolean

    /// Machine-readable stale reason; present only when stale is true.
    staleReason: String

    /// Discovered items in this batch.
    @required
    total: Long

    /// Items that reached a terminal state (indexed or failed).
    @required
    completed: Long

    /// Items indexed successfully.
    @required
    indexed: Long

    /// Items that ended in failure.
    @required
    failed: Long

    /// Items indexed with degraded quality (for example missing embeddings).
    @required
    degraded: Long

    /// When the batch row was created.
    @required
    createdAt: Timestamp

    /// When the batch row last changed.
    @required
    updatedAt: Timestamp

    /// When the batch finished; absent while running.
    finishedAt: Timestamp

    /// Most recent invocation of `platform import` for this batch
    /// (platform.import_run). Absent for batches imported before the ledger.
    lastRun: IngestionRunAttempt
}

/// Final state of one import invocation.
enum IngestionAttemptStatus {
    /// The process was still working when the snapshot was taken.
    RUNNING

    /// The invocation returned normally (items may still have failed).
    COMPLETED

    /// Stopped by the operator; the next invocation resumes.
    INTERRUPTED

    /// The invocation raised before it could finish.
    FAILED
}

/// Scan buckets that never became import items.
structure IngestionRunSkipped {
    /// Dotfiles and other paths ignored by the scanner.
    @required
    hidden: Long

    /// Files whose extension is outside ALLOWED_EXTENSIONS.
    @required
    unsupported: Long

    /// Zero-byte files.
    @required
    empty: Long

    /// Files above documents.max_upload_bytes.
    @required
    tooLarge: Long

    /// Files that could not be stat'ed or hashed.
    @required
    unreadable: Long
}

/// Counters exactly as reported by one invocation.
structure IngestionRunCounters {
    /// Items discovered by this scan.
    @required
    total: Long

    /// Items that were already embedded before this invocation.
    @required
    alreadyDone: Long

    /// Items this invocation reached a terminal state for.
    @required
    processed: Long

    /// Items successfully parsed.
    @required
    parsed: Long

    /// Items that resumed from a previous chunking step.
    @required
    resumedChunked: Long

    /// Items indexed with vectors in the active model partition.
    @required
    indexed: Long

    /// Document rows created by this invocation.
    @required
    documentsAdded: Long

    /// Items that failed during this invocation.
    @required
    failedThisRun: Long

    /// Items still marked failed at the end of this invocation.
    @required
    failedTotal: Long

    /// Items left pending, parsing or chunked when the invocation stopped.
    @required
    remainingFiles: Long

    /// True when the invocation stopped at a segment boundary and can resume.
    @required
    interrupted: Boolean

    /// Scan buckets that never became items.
    @required
    skipped: IngestionRunSkipped

    /// Wall-clock duration of the invocation.
    @required
    elapsedSeconds: Double
}

/// One invocation of `platform import` (platform.import_run).
structure IngestionRunAttempt {
    /// Invocation identifier (platform.import_run.run_id), not the batch id.
    @required
    runId: Uuid

    @required
    status: IngestionAttemptStatus

    /// When the invocation opened its ledger row.
    @required
    startedAt: Timestamp

    /// When the invocation closed its ledger row; absent while running.
    finishedAt: Timestamp

    /// Process exit code reported by the CLI.
    exitCode: Integer

    /// Machine-readable failure code when status is FAILED.
    errorCode: String

    /// Human-readable failure message when status is FAILED.
    errorMessage: String

    /// Counters are absent when the invocation failed before counting.
    counters: IngestionRunCounters
}

/// A page of ingestion runs.
list IngestionRunList {
    /// The runs in this page.
    member: IngestionRun
}

/// One failed item surfaced in the inline failure feed.
structure IngestionFailure {
    /// Batch the failed item belongs to.
    @required
    runId: Uuid

    /// Item path relative to the batch root.
    @required
    relPath: String

    /// Number of processing attempts so far.
    @required
    attempts: Integer

    /// Machine-readable failure code, when the importer recorded one.
    code: String

    /// Human-readable failure message, when the importer recorded one.
    message: String

    /// When the item last changed.
    @required
    updatedAt: Timestamp
}

/// Ordered failed items across the returned runs.
list IngestionFailureList {
    /// One failed item.
    member: IngestionFailure
}

/// List namespace-scoped ingestion runs (F17) with counters that refresh on
/// each call (F18), newest first.
@http(method: "GET", uri: "/namespaces/{namespaceId}/ingestion-runs")
@readonly
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "maxResults", items: "items")
@examples([
    {
        title: "List one namespace's import batches"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", kind: "BATCH" }
        output: {
            items: [
                {
                    runId: "9a7c2b40-6d1e-4b9f-8a3c-2f4d5e6a7b8c"
                    root: "/data/corpus/handbook"
                    status: "COMPLETED"
                    stale: false
                    total: 120
                    completed: 120
                    indexed: 118
                    failed: 2
                    degraded: 1
                    createdAt: 1762732800
                    updatedAt: 1762819200
                    finishedAt: 1762819200
                }
            ]
            totalCount: 1
            failures: [
                {
                    runId: "9a7c2b40-6d1e-4b9f-8a3c-2f4d5e6a7b8c"
                    relPath: "appendix/legacy.docx"
                    attempts: 3
                    code: "E_PARSE_UNSUPPORTED"
                    message: "unsupported legacy document format"
                    updatedAt: 1762819200
                }
            ]
        }
    }
])
operation ListIngestionRuns {
    input := {
        /// Namespace whose runs are listed.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Run family; defaults to BATCH and only BATCH is implemented.
        @httpQuery("kind")
        kind: IngestionRunKind

        /// Optional lifecycle-status filter.
        @httpQuery("status")
        status: IngestionRunStatus

        /// Pagination token from a previous response.
        @httpQuery("nextToken")
        nextToken: PaginationToken

        /// Maximum runs per page (default and maximum 50).
        @httpQuery("maxResults")
        @range(min: 1, max: 50)
        maxResults: Integer
    }

    output := with [PaginatedOutput] {
        /// Page of ingestion runs.
        @required
        items: IngestionRunList

        /// Number of runs matching the filter across all pages.
        @required
        totalCount: Long

        /// Most recent failed items across the returned page (at most 20).
        @required
        failures: IngestionFailureList
    }

    errors: [
        ValidationError
    ]
}
