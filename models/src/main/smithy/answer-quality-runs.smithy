// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// P14 / F86: read the stored answer-quality run history.
//
// ── Merge instructions (this file is branch-local; main is untouched) ──
// 1) In models/src/main/smithy/control-plane.smithy, add one line to the
//    `use com.amazon.semanticcontext...` block (alphabetical, after the
//    metriccatalog imports and before the namespace imports):
//
//        use com.amazon.semanticcontext.quality#ListAnswerQualityRuns
//
// 2) In the same file, inside `service ControlPlaneService { operations: [ ... ] }`,
//    add one line immediately after `ListIngestionRuns`:
//
//        ListAnswerQualityRuns
//
// Nothing else in control-plane.smithy changes. The operation, its IO shapes
// and the strategy enum all live in this file under their own namespace.
//
// ── Scope note ──
// `GetAnswerQuality` is a local platform-core rerun endpoint and has never been
// modelled. This op only covers the read half added by P14: the rows that
// `_record_answer_quality_run` already writes into
// `platform.answer_quality_run` (V45). No migration is added; the table and its
// `ran_at` index already exist.
$version: "2"

namespace com.amazon.semanticcontext.quality

use com.amazon.semanticcontext.common#ValidationError

/// Retrieval strategy used for a golden-set run, mirroring
/// `platform.answer_quality_run.strategy`.
enum AnswerQualityStrategy {
    /// Lexical (term/token) retrieval.
    lexical

    /// Dense-vector retrieval.
    vector

    /// Lexical plus vector retrieval.
    hybrid
}

/// Citation coverage of one retrieval layer across a single run.
///
/// A case counts as covered for a layer when at least one of its citations
/// belongs to that layer's citation kinds. The four layers are `ontology`,
/// `terms`, `metrics` and `facts`; a `chunk` citation is a document hit and is
/// not attributed to any of them.
structure QualityLayerCoverage {
    /// Layer name: `ontology`, `terms`, `metrics` or `facts`.
    @required
    layer: String

    /// Cases in the run with at least one citation from this layer.
    @required
    covered: Integer

    /// Cases evaluated in the run.
    @required
    evaluated: Integer

    /// `covered / evaluated`, 0..1.
    @required
    rate: Float
}

/// Four-layer coverage entries, in layer order (ontology, terms, metrics,
/// facts).
list QualityLayerCoverageList {
    /// One layer's coverage.
    member: QualityLayerCoverage
}

/// One stored golden-set run. Every field is read from
/// `platform.answer_quality_run`; nothing is recomputed at read time.
structure AnswerQualityRun {
    /// Stored run id (`platform.answer_quality_run.run_id`), the same value the
    /// quality response returned when the run was recorded.
    @required
    runId: String

    /// When the run finished, from `platform.answer_quality_run.ran_at`.
    @required
    @timestampFormat("date-time")
    ranAt: Timestamp

    /// Retrieval strategy of the run.
    @required
    strategy: AnswerQualityStrategy

    /// Golden-set identifier, e.g. `r02-golden-10`.
    @required
    goldenSet: String

    /// Cases evaluated in the run.
    @required
    evaluated: Integer

    /// Cases that passed.
    @required
    passed: Integer

    /// Cases that failed.
    @required
    failed: Integer

    /// `passed / evaluated`, 0..1.
    @required
    passRate: Float

    /// Share of cases with at least one citation, 0..1 (the run's overall
    /// coverage).
    @required
    citationCoverageRate: Float

    /// Share of citations that resolve to a reachable target, 0..1.
    @required
    citationResolvableRate: Float

    /// Share of citations that do not resolve, 0..1.
    @required
    brokenLinkRate: Float

    /// True when the run recorded at least one broken citation.
    @required
    regression: Boolean

    /// Per-layer coverage. Absent for rows written before P14 started storing
    /// the aggregation in `detail`; absent means "not recorded", never zero.
    layerCoverage: QualityLayerCoverageList
}

/// Stored runs for one page, newest first.
list AnswerQualityRunList {
    /// One stored run.
    member: AnswerQualityRun
}

/// List stored golden-set runs, newest first by `ran_at`.
@readonly
@http(method: "GET", uri: "/answer/quality/runs")
@examples([
    {
        title: "Two stored runs with layer coverage"
        input: { limit: 2, strategy: "lexical" }
        output: {
            items: [
                {
                    runId: "aq-3f9c2b7d1e4a"
                    ranAt: "2026-11-10T12:40:00Z"
                    strategy: "lexical"
                    goldenSet: "r02-golden-10"
                    evaluated: 10
                    passed: 7
                    failed: 3
                    passRate: 0.7
                    citationCoverageRate: 1.0
                    citationResolvableRate: 1.0
                    brokenLinkRate: 0.0
                    regression: false
                    layerCoverage: [
                        { layer: "ontology", covered: 10, evaluated: 10, rate: 1.0 }
                        { layer: "terms", covered: 8, evaluated: 10, rate: 0.8 }
                        { layer: "metrics", covered: 6, evaluated: 10, rate: 0.6 }
                        { layer: "facts", covered: 2, evaluated: 10, rate: 0.2 }
                    ]
                }
                {
                    runId: "aq-1a2b3c4d5e6f"
                    ranAt: "2026-11-10T12:20:00Z"
                    strategy: "lexical"
                    goldenSet: "r02-golden-10"
                    evaluated: 10
                    passed: 7
                    failed: 3
                    passRate: 0.7
                    citationCoverageRate: 1.0
                    citationResolvableRate: 1.0
                    brokenLinkRate: 0.0
                    regression: false
                }
            ]
            totalCount: 2
            limit: 2
            readOnly: true
        }
    }
])
operation ListAnswerQualityRuns {
    input := {
        /// Maximum runs to return (1..200, default 20).
        @httpQuery("limit")
        @range(min: 1, max: 200)
        limit: Integer

        /// Only return runs produced with this strategy.
        @httpQuery("strategy")
        strategy: AnswerQualityStrategy

        /// Only return runs at or after this instant (inclusive).
        @httpQuery("since")
        @timestampFormat("date-time")
        since: Timestamp
    }

    output := {
        /// Stored runs, newest first.
        @required
        items: AnswerQualityRunList

        /// Number of runs matching the filter, across all pages.
        @required
        totalCount: Long

        /// Page size used for this response.
        @required
        limit: Integer

        /// Strategy filter echoed back; absent when unfiltered.
        strategy: AnswerQualityStrategy

        /// Time-window lower bound echoed back; absent when unfiltered.
        @timestampFormat("date-time")
        since: Timestamp

        /// Always true: this operation never writes.
        @required
        readOnly: Boolean
    }

    errors: [
        ValidationError
    ]
}
