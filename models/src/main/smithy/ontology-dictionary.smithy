// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// Ontology terms + data dictionary operations (P4, F58-F66).
//
// Read-mostly namespace-scoped surface backed by the namespace lexicon graph
// (terms) and platform.dictionary_column / platform.dictionary_refresh_run
// (dictionary). Kept in its own file so parallel contract work does not touch
// this set.
$version: "2"

namespace com.amazon.semanticcontext.dictionary

use com.amazon.semanticcontext.common#InternalServerError
use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#ServiceUnavailableError
use com.amazon.semanticcontext.common#StringList
use com.amazon.semanticcontext.common#Uuid
use com.amazon.semanticcontext.common#ValidationError

// ---------------------------------------------------------------------------
// Terms (F58/F59)
// ---------------------------------------------------------------------------
/// Anchor-class and alias counts for the namespace's published T-Box.
structure TermCounts {
    /// Distinct owl:Class nodes that an alias entry points at (F58).
    @required
    anchorClasses: Integer

    /// Number of skos:Concept / term:TermEntry alias entries (F59).
    @required
    termEntries: Integer

    /// Entries whose status is `evidenced`.
    @required
    evidenced: Integer

    /// Entries whose status is `inferred`.
    @required
    inferred: Integer
}

/// One alias row. The seven data columns are class, label, status,
/// confidence, guard regex, canonical-for targets and suppressed surfaces.
structure TermEntry {
    /// IRI of the skos:Concept / term:TermEntry node.
    @required
    entry: String

    /// IRI of the anchored class.
    classIri: String

    /// rdfs:label of the anchored class, when the graph carries one.
    classLabel: String

    /// The alias surface form (skos:prefLabel or term:label).
    @required
    label: String

    /// `evidenced` or `inferred`.
    @required
    status: String

    /// Term confidence, 0..1, when recorded.
    confidence: Double

    /// Guard regular expression that must pass before the alias is used.
    guardRegex: String

    /// Concepts this surface is the canonical label for.
    canonicalFor: StringList

    /// Surface forms suppressed in favour of this entry.
    suppressedSurface: StringList
}

list TermEntryList {
    member: TermEntry
}

/// List the namespace's alias entries with anchor-class counts (F58/F59).
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/terms", code: 200)
operation ListTerms {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Case-insensitive substring match on label, class label or class IRI.
        @httpQuery("q")
        @length(min: 1, max: 256)
        query: String

        /// Filter by entry status: `evidenced` or `inferred`.
        @httpQuery("status")
        @length(min: 1, max: 32)
        status: String

        /// Page size (default 100, max 500).
        @httpQuery("limit")
        @range(min: 1, max: 500)
        limit: Integer

        /// Rows to skip (default 0).
        @httpQuery("offset")
        @range(min: 0, max: 100000)
        offset: Integer
    }

    output := {
        @required
        namespaceId: Uuid

        /// IRI of the graph the entries were read from; absent when the
        /// namespace has no lexicon graph.
        graph: String

        @required
        counts: TermCounts

        /// The alias rows for this page.
        @required
        entries: TermEntryList

        /// Number of entries after filtering.
        @required
        total: Integer

        /// Number of rows skipped.
        @required
        offset: Integer

        /// Page size actually applied.
        @required
        limit: Integer
    }

    errors: [
        ValidationError
        InternalServerError
        ServiceUnavailableError
    ]
}

// ---------------------------------------------------------------------------
// Data dictionary (F60-F66)
// ---------------------------------------------------------------------------
/// Lifecycle of one dictionary introspection pass.
structure DictionaryRefreshRun {
    /// Server-minted identifier of this introspection pass.
    @required
    runId: String

    /// Source whose dictionary was introspected.
    @required
    sourceId: String

    /// `running`, `succeeded` or `failed`.
    @required
    status: String

    /// Caller-supplied key that makes the refresh replayable.
    idempotencyKey: String

    /// Principal that requested the refresh, when recorded.
    requestedBy: String

    /// ISO-8601 start time.
    startedAt: String

    /// ISO-8601 finish time; absent while still running.
    finishedAt: String

    /// Column rows read from the source.
    processed: Integer

    /// Column rows newly inserted into the snapshot.
    inserted: Integer

    /// Column rows updated in the snapshot.
    updated: Integer

    /// Column rows that were already identical.
    unchanged: Integer

    /// Column rows dropped because the source no longer exposes them.
    removed: Integer

    /// Failure message when `status` is `failed`; absent otherwise.
    error: String
}

/// One column row in the dictionary (ten-column view, F63).
structure DictionaryColumn {
    /// Source this column snapshot belongs to.
    @required
    sourceId: String

    /// Catalog the source exposes the table under.
    @required
    catalog: String

    /// Schema the source exposes the table under.
    @required
    schema: String

    /// Table name.
    @required
    table: String

    /// Column name.
    @required
    column: String

    /// Column data type as reported by the source.
    @required
    dataType: String

    /// Whether the column admits NULL.
    @required
    isNullable: Boolean

    /// Source engine kind, e.g. `postgresql` or `snowflake`.
    @required
    sourceKind: String

    /// How the binding was resolved: `explicit`, `name_match`, `manual` or `none`.
    @required
    bindingMethod: String

    /// Column comment captured from the source, when present.
    comment: String

    /// Ontology property this column is bound to, when bound.
    propertyIri: String

    /// Confidence of a `name_match` binding, 0..1.
    confidence: Double

    /// Human note attached to a `manual` binding.
    bindingNote: String

    /// ISO-8601 time the snapshot observed this column.
    observedAt: String

    /// Refresh run that last wrote this row.
    lastRefreshRunId: String
}

list DictionaryColumnList {
    member: DictionaryColumn
}

/// Per-source rollup shown in the source list.
structure DictionarySummary {
    /// Source the snapshot belongs to.
    @required
    sourceId: String

    /// Source engine kind, e.g. `postgresql` or `snowflake`.
    @required
    sourceKind: String

    /// Distinct tables in the snapshot.
    @required
    tables: Integer

    /// Column count in the snapshot.
    @required
    columns: Integer

    /// Columns carrying a source comment.
    @required
    commented: Integer

    /// Columns bound to an ontology property.
    @required
    bound: Integer

    /// ISO-8601 time the snapshot was last observed.
    observedAt: String

    /// Most recent refresh run for this source.
    lastRun: DictionaryRefreshRun
}

list DictionarySummaryList {
    member: DictionarySummary
}

/// Per-table rollup on the source dictionary page.
structure DictionaryTableSummary {
    /// Table name.
    @required
    table: String

    /// Column count in the table.
    @required
    columns: Integer

    /// Columns carrying a source comment.
    @required
    commented: Integer

    /// Columns bound to an ontology property.
    @required
    bound: Integer

    /// Columns with no source comment.
    @required
    missingComment: Integer

    /// Columns not bound to any ontology property.
    @required
    unbound: Integer
}

list DictionaryTableSummaryList {
    member: DictionaryTableSummary
}

/// Comment coverage rollup (F66). `ratio` is absent when there are no rows.
structure CommentCoverage {
    /// Rows considered.
    @required
    total: Integer

    /// Rows carrying a comment.
    @required
    commented: Integer

    /// Rows with no comment.
    @required
    missing: Integer

    /// Commented rows divided by total, 0..1.
    ratio: Double
}

/// List sources that have a dictionary snapshot.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/dictionaries", code: 200)
operation ListDictionaries {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Page size (default 50, max 200).
        @httpQuery("limit")
        @range(min: 1, max: 200)
        limit: Integer

        /// Rows to skip (default 0).
        @httpQuery("offset")
        @range(min: 0, max: 100000)
        offset: Integer
    }

    output := {
        /// Per-source dictionary rollups for this page.
        @required
        items: DictionarySummaryList

        /// Number of sources that have a snapshot.
        @required
        total: Integer

        /// Number of rows skipped.
        @required
        offset: Integer

        /// Page size actually applied.
        @required
        limit: Integer
    }

    errors: [
        ValidationError
        InternalServerError
        ServiceUnavailableError
    ]
}

/// Describe one source's dictionary: table rollups + exact comment coverage.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/dictionaries/{sourceId}", code: 200)
operation GetDictionary {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Source whose dictionary is read or refreshed.
        @required
        @httpLabel
        @length(min: 1, max: 128)
        sourceId: String

        /// Restrict the table rollups to one table.
        @httpQuery("table")
        @length(min: 1, max: 256)
        table: String
    }

    output := {
        /// Source the dictionary belongs to.
        @required
        sourceId: String

        /// Source engine kind, e.g. `postgresql` or `snowflake`.
        sourceKind: String

        /// Catalog the source exposes tables under.
        catalog: String

        /// Schema the source exposes tables under.
        schema: String

        /// Per-table rollups.
        @required
        tables: DictionaryTableSummaryList

        /// Comment coverage for the whole source.
        @required
        totals: CommentCoverage

        /// Bindings already resolved (`binding_method` != `none`).
        @required
        boundColumns: Integer

        latestRun: DictionaryRefreshRun
    }

    errors: [
        ValidationError
        NotFoundError
        InternalServerError
        ServiceUnavailableError
    ]
}

/// Page the column view with the four dashboard filters (F60/F61/F64/F65).
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/dictionaries/{sourceId}/view", code: 200)
operation GetDictionaryView {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Source whose dictionary is read or refreshed.
        @required
        @httpLabel
        @length(min: 1, max: 128)
        sourceId: String

        /// `all`, `missing_comment`, `unbound` or `mappable_unbound`.
        @httpQuery("view")
        @length(min: 1, max: 32)
        view: String

        /// Restrict to one table name.
        @httpQuery("table")
        @length(min: 1, max: 256)
        table: String

        /// Restrict to one column name.
        @httpQuery("column")
        @length(min: 1, max: 256)
        column: String

        /// `explicit`, `name_match`, `manual` or `none`.
        @httpQuery("bindingMethod")
        @length(min: 1, max: 32)
        bindingMethod: String

        /// `postgresql`, `mysql`, `redshift`, `sqlserver`, `snowflake`,
        /// `glue` or `duckdb`.
        @httpQuery("sourceKind")
        @length(min: 1, max: 32)
        sourceKind: String

        /// Case-insensitive substring match on table, column or comment.
        @httpQuery("q")
        @length(min: 1, max: 256)
        query: String

        /// Page size (default 50, max 200).
        @httpQuery("limit")
        @range(min: 1, max: 200)
        limit: Integer

        /// Rows to skip (default 0).
        @httpQuery("offset")
        @range(min: 0, max: 100000)
        offset: Integer
    }

    output := {
        /// Column rows for this page.
        @required
        items: DictionaryColumnList

        /// Number of rows after filtering.
        @required
        total: Integer

        /// Number of rows skipped.
        @required
        offset: Integer

        /// Page size actually applied.
        @required
        limit: Integer

        /// The filter view that was applied.
        @required
        view: String

        @required
        coverage: CommentCoverage

        /// Non-fatal notes, e.g. an empty mappable set. Never silent.
        warnings: StringList
    }

    errors: [
        ValidationError
        NotFoundError
        InternalServerError
        ServiceUnavailableError
    ]
}

/// Comment coverage for one source (F66).
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/dictionaries/{sourceId}/comment-coverage", code: 200)
operation GetDictionaryCommentCoverage {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Source whose dictionary is read or refreshed.
        @required
        @httpLabel
        @length(min: 1, max: 128)
        sourceId: String

        /// Restrict the coverage rollup to one table.
        @httpQuery("table")
        @length(min: 1, max: 256)
        table: String
    }

    output := {
        /// Source the coverage applies to.
        @required
        sourceId: String

        /// Comment coverage for the whole source.
        @required
        coverage: CommentCoverage

        /// Per-table coverage rollups.
        @required
        tables: DictionaryTableSummaryList
    }

    errors: [
        ValidationError
        NotFoundError
        InternalServerError
        ServiceUnavailableError
    ]
}

/// Introspect a source and replace its dictionary snapshot.
///
/// A repeated `idempotencyKey` for a succeeded run returns that run instead of
/// introspecting again. A still-running duplicate is a conflict. Columns whose
/// stored `binding_method` is `manual` are never overwritten.
@http(method: "POST", uri: "/namespaces/{namespaceId}/dictionaries/{sourceId}/refresh", code: 200)
operation RefreshDictionaries {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Source whose dictionary is read or refreshed.
        @required
        @httpLabel
        @length(min: 1, max: 128)
        sourceId: String

        /// Caller-supplied key; generated per request when absent.
        @length(min: 1, max: 128)
        idempotencyKey: String

        /// Principal requesting the refresh, when the caller supplies one.
        @length(min: 1, max: 128)
        requestedBy: String
    }

    output := {
        @required
        run: DictionaryRefreshRun

        /// How bindings were resolved: `published-ontology`,
        /// `published-ontology-empty`, or `replay` when an already-succeeded
        /// idempotency key returned its prior run.
        @required
        bindingBasis: String

        /// Non-fatal notes (e.g. a source with zero columns). Never silent.
        warnings: StringList
    }

    errors: [
        ValidationError
        NotFoundError
        InternalServerError
        ServiceUnavailableError
    ]
}
