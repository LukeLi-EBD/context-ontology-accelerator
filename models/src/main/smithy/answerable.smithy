// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
//
// ========================= MERGE HOOK — READ ME =========================
// Answerability pre-check (F76 four-layer coverage / F79 gaps and fixes).
//
// This operation is INTENTIONALLY NOT bound to DataLayerService in this
// branch. Four parallel P7 tracks add operations to the same service list, so
// editing it here would guarantee merge conflicts.
//
// Before merging this branch, add ONE line to the operations list in
// models/src/main/smithy/data-layer.smithy:
//
//     operations: [
//         Query
//         TranslateSPARQL
//         KBSearch
//         GraphTraverse
//         DescribeSchema
//         CheckAnswerable        <-- add exactly this line
//     ]
//
// Then regenerate (models/gradlew build) on the integration line and commit
// smithy-generated/ there. Without that line the model still validates, but
// the operation is missing from OpenAPI and from every generated client.
//
// All shapes for CheckAnswerable live in this file; nothing else needs to move.
// The local bridge (doc/coa-x/tools/coa_api_local.py) already serves the route.
// =========================================================================
$version: "2"

namespace com.amazon.semanticcontext.datalayer

use com.amazon.semanticcontext.common#AccessDeniedError
use com.amazon.semanticcontext.common#InternalServerError
use com.amazon.semanticcontext.common#ServiceUnavailableError
use com.amazon.semanticcontext.common#StringList
use com.amazon.semanticcontext.common#Uuid
use com.amazon.semanticcontext.common#ValidationError

/// Pre-check whether an ontology can answer a question, reporting coverage for
/// each of the four layers (ontology, terms, metrics, facts) and, for every
/// gap, what is missing and how to fix it.
///
/// Read-only. A layer whose inputs are not available reports status
/// `unavailable` (or `not_applicable`) and no coverage value; it is never
/// silently reported as zero coverage.
@idempotent
@http(method: "POST", uri: "/namespaces/{namespaceId}/answerable", code: 200)
@examples([
    {
        title: "A value question that is fully covered"
        input: { namespaceId: "ed70a15c-2d42-4dc9-8c61-33b2584f05fd", query: "上个月华东区的销售额是多少？" }
        output: {
            query: "上个月华东区的销售额是多少？"
            answerable: true
            valueAnswerable: true
            answerMode: "value"
            intent: "value"
            degraded: false
            coverage: 0.92
            threshold: 0.8
            coverageChars: { covered: 23, total: 25 }
            ontologyVersion: "v3"
            ontologyGraph: "https://coa.local/graph/ed70a15c-2d42-4dc9-8c61-33b2584f05fd/urn%3Acoa%3Aontology%3Av3"
            termSource: "skos(prefLabel/altLabel) when present + rdfs:label baseline"
            termCount: 148
            matchedTerms: [
                {
                    term: "urn:coa:metric:sales_amount"
                    label: "销售额"
                    span: [0, 3]
                }
            ]
            layers: [
                {
                    layer: "ontology"
                    status: "covered"
                    coverage: 0.92
                    matched: [
                        {
                            id: "urn:coa:metric:sales_amount"
                            label: "销售额"
                            source: "rdfs:label"
                        }
                    ]
                    missing: []
                }
                {
                    layer: "terms"
                    status: "covered"
                    coverage: 1.0
                    matched: [
                        {
                            id: "urn:coa:term:east_china"
                            label: "华东区"
                            source: "skos"
                        }
                    ]
                    missing: []
                }
                {
                    layer: "metrics"
                    status: "covered"
                    coverage: 1.0
                    matched: [
                        {
                            id: "sales_amount"
                            label: "销售额"
                            score: 0.98
                        }
                    ]
                    missing: []
                }
                {
                    layer: "facts"
                    status: "covered"
                    coverage: 1.0
                    matched: [
                        {
                            metricId: "sales_amount"
                            status: "covered"
                            code: "FACT_COVERED"
                            observationRows: 12
                        }
                    ]
                    missing: []
                }
            ]
            missing: []
            candidates: [
                {
                    layer: "metrics"
                    id: "sales_amount"
                    label: "销售额"
                    reason: "exact_name"
                    score: 0.98
                }
            ]
            reasons: []
            timings: { termsMs: 12, metricMs: 3, factsMs: 41 }
        }
    }
    {
        title: "A question with gaps in the ontology and facts layers"
        input: { namespaceId: "ed70a15c-2d42-4dc9-8c61-33b2584f05fd", query: "上个季度供应商交货及时率是多少？" }
        output: {
            query: "上个季度供应商交货及时率是多少？"
            answerable: false
            valueAnswerable: false
            answerMode: "none"
            intent: "value"
            degraded: true
            coverage: 0.55
            threshold: 0.8
            coverageChars: { covered: 11, total: 20 }
            ontologyVersion: "v3"
            ontologyGraph: "https://coa.local/graph/ed70a15c-2d42-4dc9-8c61-33b2584f05fd/urn%3Acoa%3Aontology%3Av3"
            termSource: "skos(prefLabel/altLabel) when present + rdfs:label baseline"
            termCount: 148
            matchedTerms: []
            layers: [
                {
                    layer: "ontology"
                    status: "partial"
                    coverage: 0.55
                    matched: []
                    missing: ["供应商"]
                }
                {
                    layer: "terms"
                    status: "missing"
                    coverage: 0.0
                    matched: []
                    missing: ["交货及时率"]
                }
                {
                    layer: "metrics"
                    status: "missing"
                    coverage: 0.0
                    matched: []
                    missing: ["on_time_delivery_rate"]
                }
                {
                    layer: "facts"
                    status: "not_applicable"
                    matched: []
                    missing: []
                }
            ]
            missing: [
                {
                    layer: "ontology"
                    code: "E_LAYER_ONTOLOGY_GAP"
                    text: "供应商"
                    span: [8, 11]
                    what: "本体未声明「供应商」"
                    howToFix: "补充 rdfs:label / skos:prefLabel，或收窄问题范围"
                    nearbyTerms: [
                        {
                            term: "urn:coa:party:supplier"
                            label: "供货方"
                            similarity: 0.67
                        }
                    ]
                }
                {
                    layer: "metrics"
                    code: "E_LAYER_METRICS_GAP"
                    what: "未匹配到可求值口径指标"
                    howToFix: "指定 metricId，或补充指标名称/别名"
                    candidates: [
                        {
                            id: "on_time_delivery_rate"
                            label: "交货及时率"
                            score: 0.71
                        }
                    ]
                }
            ]
            candidates: [
                {
                    layer: "metrics"
                    id: "on_time_delivery_rate"
                    label: "交货及时率"
                    reason: "fuzzy_name"
                    score: 0.71
                }
            ]
            reasons: ["facts layer has no metric to evaluate"]
            reasonCode: "E_ANSWER_METRIC_NOT_FOUND"
            hint: "本体未覆盖问题中的这些概念：供应商；请先补充术语（T-Box）或缩小问题范围"
            timings: { termsMs: 9, metricMs: 2, factsMs: 0 }
        }
    }
])
operation CheckAnswerable {
    input: CheckAnswerableInput
    output: CheckAnswerableOutput
    errors: [
        ValidationError
        AccessDeniedError
        InternalServerError
        ServiceUnavailableError
    ]
}

/// Input for CheckAnswerable.
structure CheckAnswerableInput {
    /// Namespace the question is asked in.
    @required
    @httpLabel
    namespaceId: Uuid

    /// The natural-language question to pre-check.
    @required
    @length(min: 1, max: 2000)
    query: String

    /// Ontology version to check against; defaults to the published current one.
    @length(min: 1, max: 128)
    ontologyVersion: String

    /// Minimum term coverage (0..1) required for `answerable: true`.
    @range(min: 0.0, max: 1.0)
    minCoverage: Float
}

/// Result of an answerability pre-check.
structure CheckAnswerableOutput {
    /// Echo of the checked question.
    @required
    query: String

    /// True when the question can be answered: entity coverage meets the
    /// threshold, or an exact metric match supports a definition answer even
    /// when no fact rows are available.
    @required
    answerable: Boolean

    /// True when a concrete numeric value can be produced (facts layer covered).
    @required
    valueAnswerable: Boolean

    /// How the question can be answered: `value`, `definition` or `none`.
    @required
    answerMode: String

    /// Detected question intent: `value` or `definition`.
    @required
    intent: String

    /// True when any layer is degraded or unavailable.
    @required
    degraded: Boolean

    /// Character coverage of the ontology/term layer (0..1).
    @required
    coverage: Float

    /// Threshold used to decide `answerable`.
    @required
    threshold: Float

    /// Covered / total content characters behind `coverage`.
    @required
    coverageChars: CoverageChars

    /// Entity-level coverage (0..1): distinct matched ontology entities divided
    /// by distinct entity mentions in the question (1/n semantics). This drives
    /// `answerable`; `coverage` above remains the character-level diagnostic.
    entityCoverage: Float

    /// Number of distinct entity mentions the question involves (matched plus
    /// unresolved). Question meta words such as 口径/处理 are not entities.
    entityCount: Integer

    /// Number of distinct ontology entities among `entityCount`.
    matchedEntityCount: Integer

    /// Entity mentions in question order, both matched and unresolved.
    entityMentions: EntityMentionList

    /// True when entity coverage could not be evaluated against the ontology
    /// (no entity recognised). `entityCoverage` is then 0, never 1.
    entityDegraded: Boolean

    /// Why entity coverage degraded: `no_ontology_entity` (content exists but
    /// nothing matched) or `no_entity_mention` (only meta words).
    entityDegradeReason: String

    /// Ontology version the check ran against.
    @required
    ontologyVersion: String

    /// Named graph URI of that version.
    @required
    ontologyGraph: String

    /// Human-readable description of the term source used.
    @required
    termSource: String

    /// Number of distinct terms considered.
    @required
    termCount: Integer

    /// Terms that matched the question.
    @required
    matchedTerms: MatchedTermList

    /// Exactly four layers, in order: ontology, terms, metrics, facts.
    @required
    layers: CoverageLayerList

    /// One entry per gap, each carrying what is missing and how to fix it (F79).
    @required
    missing: MissingGapList

    /// Ranked candidates that could close the gaps.
    @required
    candidates: AnswerCandidateList

    /// Machine-readable reasons collected while evaluating.
    @required
    reasons: StringList

    /// Machine-readable reason when `answerable` is false.
    reasonCode: String

    /// Operator-facing next step when `answerable` is false.
    hint: String

    /// Per-layer evaluation timings in milliseconds.
    @required
    timings: AnswerTimings
}

/// Character accounting behind the ontology/term coverage ratio.
structure CoverageChars {
    /// Number of content characters covered by a matched term.
    @required
    covered: Integer

    /// Number of content characters in the question (stopwords/punctuation removed).
    @required
    total: Integer
}

/// A term that matched part of the question.
structure MatchedTerm {
    /// Term IRI.
    @required
    term: String

    /// Human-readable label.
    @required
    label: String

    /// Inclusive-exclusive [start, end) character span in the normalized question.
    @required
    span: Span

    /// Surface that actually matched when it is an alias extracted from a
    /// bracketed label ("保单" from "保险合同（保单）"); absent when the whole
    /// label matched.
    alias: String

    /// Every concept that declares the matched surface when more than one
    /// does. `term` is then the deterministic primary (a real label outranks a
    /// derived alias, ties by IRI order); the others are not dropped silently.
    candidates: StringList
}

/// Terms that matched the question.
list MatchedTermList {
    member: MatchedTerm
}

/// One entity mention in the question: a matched ontology entity or an
/// unresolved content fragment counted as one missing entity.
structure EntityMention {
    /// Surface text as it appears in the normalized question (known entities
    /// use the matched label).
    @required
    text: String

    /// Inclusive-exclusive [start, end) character span in the normalized question.
    @required
    span: Span

    /// `ontology` when the mention matched a term, `unknown` otherwise.
    @required
    kind: String

    /// Matched term IRI (ontology mentions only).
    term: String

    /// Matched label (ontology mentions only).
    label: String

    /// Label source of the match: `skos` or `rdfs:label`.
    source: String

    /// Every concept that declares the matched surface when more than one
    /// does; `term` is the deterministic primary. Absent when unambiguous.
    candidates: StringList
}

/// Entity mentions in question order.
list EntityMentionList {
    member: EntityMention
}

/// A character span in the normalized question.
list Span {
    member: Integer
}

/// The four answerability layers.
list CoverageLayerList {
    member: CoverageLayer
}

/// One of the four answerability layers.
structure CoverageLayer {
    /// Layer name: `ontology` | `terms` | `metrics` | `facts`.
    @required
    layer: String

    /// `covered` | `partial` | `missing` | `degraded` | `unavailable` | `not_applicable`.
    @required
    status: String

    /// Layer coverage in 0..1. Absent when the layer cannot be computed;
    /// clients must render that as "unavailable", never as 0.
    coverage: Float

    /// Evidence that matched in this layer. Fields are layer-specific: ontology
    /// and term matches carry id/label/predicate/source, metrics carry
    /// id/label/score, facts carry metricId/status/code/observationRows.
    @required
    matched: LayerMatchList

    /// Short human-readable descriptions of what this layer lacks.
    @required
    missing: StringList
}

/// Evidence matched in one layer.
list LayerMatchList {
    member: LayerMatch
}

/// Layer-specific evidence for one match.
structure LayerMatch {
    /// Matched identifier (term IRI or metric id).
    id: String

    /// Human-readable label.
    label: String

    /// Predicate that produced the match (ontology layer).
    predicate: String

    /// Source of the label: `rdfs:label` or `skos`.
    source: String

    /// Match score (metrics layer).
    score: Float

    /// Metric this evidence belongs to (facts layer).
    metricId: String

    /// Fact coverage status for that metric.
    status: String

    /// Stable machine-readable status code.
    code: String

    /// Number of fact rows backing the metric.
    observationRows: Integer

    /// Fact function declared by the metric.
    factFunction: String
}

/// Gaps found while pre-checking, each with a fix.
list MissingGapList {
    member: MissingGap
}

/// A gap: what is missing, in which layer, and how to fix it (F79).
structure MissingGap {
    /// Layer the gap belongs to: `ontology` | `terms` | `metrics` | `facts`.
    @required
    layer: String

    /// Stable machine-readable code, e.g. `E_LAYER_ONTOLOGY_GAP`.
    @required
    code: String

    /// The question fragment that could not be covered (ontology layer).
    text: String

    /// Inclusive-exclusive [start, end) span of that fragment, when known.
    span: Span

    /// What exactly is missing, phrased as an operator action target.
    what: String

    /// How to close the gap.
    howToFix: String

    /// Metric this gap belongs to (facts layer).
    metricId: String

    /// Lexically nearby terms that may be the intended concept.
    nearbyTerms: NearbyTermList

    /// Ranked candidates that may close this gap.
    candidates: GapCandidateList
}

/// A lexically similar term offered for an uncovered fragment.
structure NearbyTerm {
    /// Term IRI.
    @required
    term: String

    /// Human-readable label.
    @required
    label: String

    /// Lexical similarity in 0..1.
    @required
    similarity: Float
}

/// Nearby terms for one gap.
list NearbyTermList {
    member: NearbyTerm
}

/// A ranked candidate that may close a gap.
structure GapCandidate {
    /// Candidate identifier (metric id).
    @required
    id: String

    /// Human-readable label.
    @required
    label: String

    /// Match score in 0..1.
    @required
    score: Float
}

/// Candidates for one gap.
list GapCandidateList {
    member: GapCandidate
}

/// A ranked candidate for the question as a whole.
structure AnswerCandidate {
    /// Layer the candidate belongs to.
    @required
    layer: String

    /// Candidate identifier.
    @required
    id: String

    /// Human-readable label.
    @required
    label: String

    /// Why the candidate matched.
    @required
    reason: String

    /// Match score in 0..1.
    @required
    score: Float
}

/// Ranked candidates for the question.
list AnswerCandidateList {
    member: AnswerCandidate
}

/// Per-layer evaluation timings.
structure AnswerTimings {
    /// Ontology/term layer duration in milliseconds.
    @required
    termsMs: Integer

    /// Metric matching duration in milliseconds.
    @required
    metricMs: Integer

    /// Fact layer duration in milliseconds.
    @required
    factsMs: Integer
}
