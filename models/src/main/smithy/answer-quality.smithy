// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// Answer-quality run served by the local bridge.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.5 rows F86-F89 and
// doc/coa-x/18-platform-core拆解.md §KERNEL `/answer/quality`. Each call
// re-runs the fixed golden set and returns one run; there is deliberately no
// history or trend endpoint (results are persisted once, not sampled).
$version: "2"

namespace com.amazon.semanticcontext.quality

/// Retrieval strategy used for the run.
enum AnswerQualityStrategy {
    /// Lexical retrieval only.
    lexical

    /// Hybrid lexical + vector retrieval.
    hybrid
}

/// One citation attached to an answer.
structure AnswerQualityCitation {
    /// Citation identifier.
    @required
    id: String

    /// Citation kind, e.g. `document` or `fact`.
    @required
    kind: String

    /// Referenced identifier.
    @required
    ref: String

    /// Ontology or document version the citation resolved against.
    versionId: String

    /// Console URL that resolves the citation.
    resolveUrl: String

    /// True when the reference still resolves.
    @required
    resolvable: Boolean
}

list AnswerQualityCitationList {
    member: AnswerQualityCitation
}

/// Actual answer produced for one golden-set case.
structure AnswerQualityActual {
    /// True when the answer was refused.
    @required
    refused: Boolean

    /// Answer type chosen by the pipeline.
    @required
    answerType: String

    /// Answer mode chosen by the pipeline.
    @required
    answerMode: String

    /// Refusal reason code; absent when the answer was not refused.
    reasonCode: String

    /// True when the answer was served degraded.
    @required
    degraded: Boolean

    /// Citations attached to the answer.
    @required
    citations: AnswerQualityCitationList

    /// Distinct citation kinds.
    @required
    citationKinds: StringList

    /// Retrieval layers that produced nothing.
    @required
    missingLayers: StringList
}

/// One golden-set case and its verdict.
structure AnswerQualityCase {
    /// Case identifier.
    @required
    id: String

    /// Query executed for the case.
    @required
    query: String

    /// Case type used for grouping.
    @required
    type: String

    /// True when the case expects a refusal.
    @required
    expectRefused: Boolean

    /// Actual answer.
    @required
    actual: AnswerQualityActual

    /// True when the case passed.
    @required
    pass: Boolean

    /// Failure codes recorded for the case.
    @required
    failures: StringList

    /// Console URL for the underlying answer.
    drillDownUrl: String
}

list AnswerQualityCaseList {
    member: AnswerQualityCase
}

/// Aggregate rates over the run.
structure AnswerQualitySummary {
    /// Number of cases in the run.
    @required
    cases: Integer

    /// Number of passing cases.
    @required
    passed: Integer

    /// Number of failing cases.
    @required
    failed: Integer

    /// Share of passing cases (0-1).
    @required
    passRate: Double

    /// Number of cases with at least one citation.
    @required
    casesWithCitations: Integer

    /// Share of cases with at least one citation (0-1).
    @required
    citationCoverageRate: Double

    /// Total citations across the run.
    @required
    citations: Integer

    /// Citations whose reference resolves.
    @required
    resolvableCitations: Integer

    /// Share of citations that resolve (0-1).
    @required
    citationResolvableRate: Double

    /// Share of citations that do not resolve (0-1).
    @required
    brokenLinkRate: Double

    /// Broken-link rate recorded on the baseline.
    @required
    baselineBrokenLinkRate: Double

    /// True when the broken-link rate regressed against the baseline.
    @required
    regression: Boolean
}

/// Per-type aggregate used by the coverage and refusal breakdowns.
structure AnswerQualityByType {
    /// Case or answer type.
    @required
    type: String

    /// Number of cases of this type.
    @required
    cases: Integer

    /// Number of refused answers of this type.
    @required
    refused: Integer

    /// Number of answers with citations, when applicable.
    withCitations: Integer

    /// Total citations of this type.
    @required
    citations: Integer

    /// Citations that resolve, when computed.
    resolvable: Integer

    /// Share of cases with citations (0-1).
    @required
    citationCoverageRate: Double

    /// Share of citations that resolve (0-1), when computed.
    resolvableRate: Double

    /// Share of answers refused (0-1), when computed.
    refusalRate: Double
}

list AnswerQualityByTypeList {
    member: AnswerQualityByType
}

/// Refusal count grouped by case type and reason code.
structure AnswerQualityRefusalReason {
    /// Case type.
    @required
    type: String

    /// Refusal reason code.
    @required
    reasonCode: String

    /// Number of refusals.
    @required
    count: Integer
}

list AnswerQualityRefusalReasonList {
    member: AnswerQualityRefusalReason
}

/// The golden set that was evaluated.
structure AnswerQualityGoldenSet {
    /// Golden-set identifier.
    @required
    id: String

    /// Number of cases in the set.
    @required
    count: Integer

    /// Number of cases evaluated in this run.
    @required
    evaluated: Integer

    /// Identifier of the single case, when the run was narrowed to one case.
    caseId: String
}

list StringList {
    member: String
}

/// Free-form JSON documents in an answer-quality response.
list DocumentList {
    member: Document
}

/// One answer-quality run over the fixed golden set.
structure AnswerQualityResponse {
    /// Retrieval strategy used for the run.
    @required
    strategy: String

    /// Golden set that was evaluated.
    @required
    goldenSet: AnswerQualityGoldenSet

    /// Aggregate rates.
    @required
    summary: AnswerQualitySummary

    /// Citation coverage grouped by case type.
    citationCoverageByType: AnswerQualityByTypeList

    /// Refusal counts grouped by reason.
    refusalsByReason: AnswerQualityRefusalReasonList

    /// Refusal counts grouped by type.
    refusalsByType: AnswerQualityByTypeList

    /// Refusals that carried no layer diagnostics.
    refusalsWithoutLayers: DocumentList

    /// Citations that no longer resolve.
    brokenLinks: DocumentList

    /// Per-case verdicts.
    @required
    cases: AnswerQualityCaseList

    /// True when the run evaluated no cases.
    @required
    empty: Boolean

    /// Why the run is empty, when it is.
    emptyReason: String

    /// Always true: the endpoint never writes.
    @required
    readOnly: Boolean
}

/// Run the answer-quality golden set.
///
/// The endpoint is read-only. `limit` caps the number of per-case details
/// returned; rates are still computed over the whole set.
@readonly
@http(method: "GET", uri: "/answer/quality", code: 200)
@examples([
    {
        title: "Run the lexical golden set"
        input: { strategy: "lexical", limit: 10 }
        output: {
            strategy: "lexical"
            goldenSet: { id: "golden-v1", count: 12, evaluated: 12 }
            summary: {
                cases: 12
                passed: 11
                failed: 1
                passRate: 0.9167
                casesWithCitations: 10
                citationCoverageRate: 0.8333
                citations: 18
                resolvableCitations: 17
                citationResolvableRate: 0.9444
                brokenLinkRate: 0.0556
                baselineBrokenLinkRate: 0.06
                regression: false
            }
            citationCoverageByType: [
                { type: "entity", cases: 4, refused: 0, withCitations: 4, citations: 6, resolvable: 6, citationCoverageRate: 1.0, resolvableRate: 1.0 }
            ]
            refusalsByReason: [
                { type: "out-of-scope", reasonCode: "E_NO_EVIDENCE", count: 1 }
            ]
            refusalsByType: []
            refusalsWithoutLayers: []
            brokenLinks: [{ citationId: "cit-9", ref: "doc-missing" }]
            cases: [
                {
                    id: "case-001"
                    query: "Contract Ledger 属于哪个域？"
                    type: "entity"
                    expectRefused: false
                    actual: {
                        refused: false
                        answerType: "graph"
                        answerMode: "strict"
                        degraded: false
                        citations: [{ id: "cit-1", kind: "fact", ref: "fact-1a2b3c4d5e6f", resolvable: true }]
                        citationKinds: ["fact"]
                        missingLayers: []
                    }
                    pass: true
                    failures: []
                    drillDownUrl: "/answer?q=case-001"
                }
            ]
            empty: false
            readOnly: true
        }
    }
])
operation GetAnswerQuality {
    input := {
        /// Retrieval strategy for the run.
        @required
        @httpQuery("strategy")
        strategy: AnswerQualityStrategy

        /// Maximum per-case details to return (1-50).
        @httpQuery("limit")
        @range(min: 1, max: 50)
        limit: Integer
    }

    output: AnswerQualityResponse
}
