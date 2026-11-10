// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
//
// ========================= MERGE HOOK — READ ME =========================
// P5 metric catalog reads: GetMetricFamily (F55) and GetMetricReportManifest
// (F57).
//
// These two operations are INTENTIONALLY NOT bound to ControlPlaneService in
// this branch. The P4 second half, P5 and P7 batches all add operations to the
// same service list, so editing it here would guarantee merge conflicts.
//
// Before merging this branch, add TWO `use` lines next to the other metric
// imports in models/src/main/smithy/control-plane.smithy:
//
//     use com.amazon.semanticcontext.metriccatalog#GetMetricFamily
//     use com.amazon.semanticcontext.metriccatalog#GetMetricReportManifest
//
// and TWO lines to the operations list, at the end of the "Metric service"
// block:
//
//         // ── Metric service ──────────────────────────────────────────────
//         CreateMetric
//         GetMetric
//         ListMetrics
//         UpdateMetric
//         DeleteMetric
//         ValidateMetric
//         BulkDeleteMetrics
//         ImportOsi
//         ExportOsi
//         GetOsiUploadUrl
//         GetImportJob
//         GetMetricFamily                <-- add exactly this line
//         GetMetricReportManifest        <-- add exactly this line
//
// Then regenerate (models/gradlew build) on the integration line and commit
// smithy-generated/ there. Without those lines the model still validates, but
// both operations are missing from OpenAPI and from every generated client.
//
// All shapes for both operations live in this file; nothing else needs to move.
// The local bridge (doc/coa-x/tools/coa_api_local.py) already serves both
// routes, and the web app reads them through the plain ApiClient.
// =========================================================================
$version: "2"

namespace com.amazon.semanticcontext.metriccatalog

use com.amazon.semanticcontext.common#AccessDeniedError
use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#Uuid
use com.amazon.semanticcontext.common#ValidationError

// ──────────────────────────────────────────────
// GetMetricFamily (F55)
// ──────────────────────────────────────────────
/// Read one metric family: the index metric and its variants side by side.
/// The family index never yields a value; callers must pick a variant and use
/// the variant's metricId for output.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/metrics/families/{familyId}")
@examples([
    {
        title: "Insurance continuation-rate family"
        input: { namespaceId: "ed70a15c-2d42-4dc9-8c61-33b2584f05fd", familyId: "FIN-INS-022" }
        output: {
            family: {
                familyId: "FIN-INS-022"
                indexMetricId: "FIN-INS-022"
                nameZh: "13 个月保费继续率"
                selectionRequired: true
                guidance: {
                    code: "E_METRIC_VARIANT_REQUIRED"
                    message: "该指标是口径族索引，不直接出数；请先选择变体并回填 metric_id。"
                    howTo: ["在族索引详情中选择一个变体（窗口/分母/粒度会并排展示）", "前端将变体 metric_id 回填到详情与 URL", "再用该 metric_id 调用 /metrics/{metric_id}/output"]
                }
                variantCount: 2
                variants: [
                    {
                        metricId: "FIN-INS-022-v1"
                        nameZh: "13 个月保费继续率（宽限期口径）"
                        publishable: true
                        evidenceBasis: "regulatory"
                        externalEligible: true
                        formula: "13 个月继续率 = 期初后第 13 个月仍有效保单 / 期初保单"
                        formulaDisabled: false
                        computability: "structurally_computable"
                        computabilityLabel: "结构性可算（需事实与观测）"
                    }
                    {
                        metricId: "FIN-INS-022-v2"
                        nameZh: "13 个月保费继续率（自然月口径）"
                        publishable: true
                        evidenceBasis: "regulatory"
                        externalEligible: true
                        formula: "13 个月继续率 = 期初后第 13 个月仍有效保单 / 期初保单"
                        formulaDisabled: false
                        computability: "structurally_computable"
                        computabilityLabel: "结构性可算（需事实与观测）"
                    }
                ]
                diffs: [
                    {
                        field: "observationPeriod"
                        label: "观察窗口"
                        values: { "FIN-INS-022-v1": "13 个月（390 天）", "FIN-INS-022-v2": "13 个月（390 天）" }
                        different: false
                    }
                ]
                source: "platform.metric_definition"
            }
        }
    }
])
operation GetMetricFamily {
    input := {
        /// Namespace that owns the metric family.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Family identifier: the metric id of the family index.
        @required
        @httpLabel
        familyId: MetricFamilyId
    }

    output := {
        /// The family index plus every variant and their differences.
        @required
        family: MetricFamily
    }

    errors: [
        NotFoundError
        AccessDeniedError
        ValidationError
    ]
}

/// Metric id of a family index; allows the ids used by governed metrics.
@pattern("^[A-Za-z][A-Za-z0-9._-]{0,127}$")
@length(min: 1, max: 128)
string MetricFamilyId

/// One metric family (a family index plus its variants).
structure MetricFamily {
    /// Family identifier, equal to the index metric id.
    @required
    familyId: String

    /// The metric a caller lands on before choosing a variant.
    @required
    indexMetricId: String

    /// Display name of the family index.
    nameZh: String

    /// Always true for a family index: output needs a variant metricId.
    @required
    selectionRequired: Boolean

    /// How the caller must choose a variant before producing a value.
    @required
    guidance: MetricFamilyGuidance

    /// Number of variants in this family.
    @required
    variantCount: Integer

    /// Variants of this family, in metric id order.
    @required
    variants: MetricFamilyVariantList

    /// Field-by-field differences across variants.
    @required
    diffs: MetricFamilyDiffList

    /// Store the family was read from.
    @required
    source: String
}

/// Instruction shown when a family index is opened instead of a variant.
structure MetricFamilyGuidance {
    /// Stable machine code (for example E_METRIC_VARIANT_REQUIRED).
    @required
    code: String

    /// Human-readable explanation.
    @required
    message: String

    /// Ordered steps that resolve the selection.
    @required
    howTo: MetricFamilyHowToList
}

/// Ordered guidance steps.
list MetricFamilyHowToList {
    /// One step of the guidance.
    member: String
}

/// One variant of a metric family.
structure MetricFamilyVariant {
    /// Variant metric id; use this for output calls.
    @required
    metricId: String

    /// Display name of the variant.
    nameZh: String

    /// Display label override, when the definition carries one.
    displayName: String

    /// Whether the variant may be published at all.
    publishable: Boolean

    /// Evidence basis (regulatory, industry, none).
    evidenceBasis: String

    /// Whether the variant passes the external-eligibility rule.
    externalEligible: Boolean

    /// Notice shown when the variant is an internal baseline.
    internalNotice: String

    /// Formula text as declared by the definition.
    formula: String

    /// True when the formula is present but execution is disabled.
    formulaDisabled: Boolean

    /// Computability tier code.
    computability: String

    /// Computability tier label.
    computabilityLabel: String

    /// Observation window declared by the variant.
    window: MetricFamilyVariantWindow

    /// Denominator expression text, when the definition declares one.
    denominator: String

    /// Human-readable denominator description.
    denominatorText: String

    /// Grain label (for example policy or agreement).
    grain: String

    /// Grain code as stored in the definition.
    grainCode: String

    /// Metric kind (ratio, duration, sum, ...).
    metricKind: String

    /// Unit of the produced value.
    unit: String
}

/// Variants of one family.
list MetricFamilyVariantList {
    /// One variant.
    member: MetricFamilyVariant
}

/// Observation window declared by a variant.
structure MetricFamilyVariantWindow {
    /// Window kind (instant, period, rolling).
    kind: String

    /// Minimum window length in days.
    minWindowDays: Integer

    /// Rendered window description.
    text: String
}

/// One field that differs (or does not differ) across variants.
structure MetricFamilyDiff {
    /// Field name used for the comparison.
    @required
    field: String

    /// Display label of the field.
    @required
    label: String

    /// metricId -> rendered value.
    @required
    values: MetricFamilyDiffValues

    /// True when the values are not all equal.
    @required
    different: Boolean
}

/// Rendered values of one diff field, keyed by variant metric id.
map MetricFamilyDiffValues {
    /// Variant metric id.
    key: String

    /// Rendered value for that variant.
    value: String
}

/// Field differences across the variants of a family.
list MetricFamilyDiffList {
    /// One compared field.
    member: MetricFamilyDiff
}

// ──────────────────────────────────────────────
// GetMetricReportManifest (F57)
// ──────────────────────────────────────────────
/// Read the governed metrics report manifest. Every row carries its external
/// status, execution path and computability, all read from
/// platform.metric_definition; nothing is computed or invented here.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/metrics/report/manifest")
@examples([
    {
        title: "One manifest row"
        input: { namespaceId: "ed70a15c-2d42-4dc9-8c61-33b2584f05fd", scope: "all" }
        output: {
            items: [
                {
                    metricId: "FIN-INS-022"
                    nameZh: "13 个月保费继续率"
                    domain: "insurance"
                    publishable: true
                    evidenceBasis: "regulatory"
                    evidenceBasisLabel: "监管原文"
                    evidenceSource: "监管原文"
                    hasRegulatoryText: true
                    industryBaseline: false
                    e1Baseline: false
                    formula: "口径未给出"
                    computability: "structurally_computable"
                    computabilityLabel: "结构性可算（需事实与观测）"
                    computabilityTone: "ok"
                    gap: "族索引：需指定变体（E_METRIC_VARIANT_REQUIRED）"
                    gapCode: "variant_required"
                    externalEligible: true
                    externalStatus: "external_candidate"
                    externalLabel: "对外可出数候选（需事实与观测）"
                    externalReason: "证据为监管原文、publishable=true、口径结构性可算；资格判定未含观测与窗口，实际可执行性见 executionPath"
                    executionPath: "unavailable"
                    executable: false
                    executionReason: "该口径是族索引，需先选择变体"
                    executionReasonCode: "variant_required"
                    observationCount: 0
                    availableWindowDays: 0
                    minWindowDays: 390
                    windowSufficient: false
                    outputMode: "index"
                    formulaDisabled: false
                    inference: false
                    evidenceStatus: "regulatory_verified"
                    definitionVersion: "v3"
                }
            ]
            count: 1
            meta: {
                generatedAt: "2026-11-10T12:00:00+00:00"
                source: "platform.metric_definition"
                scope: "all"
                total: 85
                allTotal: 85
                counts: {
                    publishableTrue: 60
                    industry: 25
                    regulatory: 60
                    externalEligible: 35
                    externalCandidates: 35
                    executableNow: 0
                    industryExcludedFromExternal: 0
                    computability: { structurally_computable: 60, blocked_semantics: 25 }
                }
                externalScopeRule: "evidence_basis=regulatory 且 publishable=true 且 computability_tier=structurally_computable"
                disclaimer: "可算性仅表示口径四元组与公式可编译，不代表已有观测值；本清单不承诺业务数值。"
            }
            filters: { scope: "all" }
        }
    }
])
operation GetMetricReportManifest {
    input := {
        /// Namespace that owns the governed metrics.
        @required
        @httpLabel
        namespaceId: Uuid

        /// "all" (everything) or "external" (external-eligible candidates only).
        @httpQuery("scope")
        scope: MetricReportScope

        /// Optional domain filter.
        @httpQuery("domain")
        @length(min: 1, max: 64)
        domain: String

        /// Optional evidence-basis filter.
        @httpQuery("evidenceBasis")
        @length(min: 1, max: 64)
        evidenceBasis: String

        /// Optional publishable filter.
        @httpQuery("publishable")
        publishable: Boolean
    }

    output := {
        /// Manifest rows after filtering.
        @required
        items: MetricReportItemList

        /// Number of rows in items.
        @required
        count: Integer

        /// Counters and provenance for the whole manifest.
        @required
        meta: MetricReportMeta

        /// Filters that were applied to this response.
        @required
        filters: MetricReportFilters
    }

    errors: [
        AccessDeniedError
        ValidationError
    ]
}

/// Manifest scope: everything, or external-eligible candidates only.
@pattern("^(all|external)$")
@length(min: 3, max: 8)
string MetricReportScope

/// Manifest rows.
list MetricReportItemList {
    /// One governed metric row.
    member: MetricReportItem
}

/// One governed metric row as it appears in the report manifest. Fields left
/// absent were not applicable for that metric; they are never coerced to false.
structure MetricReportItem {
    /// Governed metric id (also the identifier used by /metrics/{metric_id}).
    @required
    metricId: String

    /// Display name in Chinese.
    nameZh: String

    /// Display label override, when the definition carries one.
    displayName: String

    /// Business domain.
    domain: String

    /// Whether the metric may be published.
    publishable: Boolean

    /// Evidence basis (regulatory, industry, none).
    evidenceBasis: String

    /// Rendered evidence-basis label.
    evidenceBasisLabel: String

    /// Provenance label of the evidence.
    evidenceSource: String

    /// True when regulatory text is attached.
    hasRegulatoryText: Boolean

    /// True when the metric is an industry formula (internal baseline only).
    industryBaseline: Boolean

    /// Internal-baseline notice, when applicable.
    internalNotice: String

    /// True when the metric is flagged as an E1 baseline.
    e1Baseline: Boolean

    /// Formula text as declared by the definition.
    formula: String

    /// Formula expression used for execution, when declared.
    formulaExpr: String

    /// Computability tier code.
    computability: String

    /// Computability tier label.
    computabilityLabel: String

    /// Computability tone used by the UI (ok, warn, blocked).
    computabilityTone: String

    /// Short computability gap description.
    gap: String

    /// Stable gap code.
    gapCode: String

    /// Missing component description, when the metric cannot be computed.
    missing: String

    /// Whether the metric passes the external-eligibility rule.
    externalEligible: Boolean

    /// Stable external status code.
    externalStatus: String

    /// Rendered external status label.
    externalLabel: String

    /// Why the metric has this external status.
    externalReason: String

    /// Execution path code (unavailable, rule_set_only, executable).
    executionPath: String

    /// True when the metric can be executed right now.
    executable: Boolean

    /// Human-readable execution blocker.
    executionReason: String

    /// Stable execution blocker code.
    executionReasonCode: String

    /// Number of observation rows available.
    observationCount: Integer

    /// Observation window currently available, in days.
    availableWindowDays: Integer

    /// Observation window required by the definition, in days.
    minWindowDays: Integer

    /// True when the available window covers the required window.
    windowSufficient: Boolean

    /// Window warning shown to the reporter, when applicable.
    windowWarning: String

    /// Family index id for a variant metric.
    variantOf: String

    /// Output mode (index, rule_set, value).
    outputMode: String

    /// True when the formula exists but execution is disabled.
    formulaDisabled: Boolean

    /// True when the definition is inferred rather than provided.
    inference: Boolean

    /// Evidence verification status.
    evidenceStatus: String

    /// Definition version the row was read from.
    definitionVersion: String
}

/// Counters and provenance for the whole manifest.
structure MetricReportMeta {
    /// Generation timestamp (ISO-8601).
    @required
    generatedAt: String

    /// Store the manifest was read from.
    source: String

    /// Scope this manifest was generated for.
    scope: String

    /// Number of rows in this response.
    total: Integer

    /// Number of rows in the namespace before filtering.
    allTotal: Integer

    /// Counter breakdown.
    counts: MetricReportCounts

    /// Execution-path breakdown.
    execution: MetricReportExecution

    /// Industry-baseline notice shared by all industry rows.
    industryNotice: String

    /// Rule that decides external eligibility.
    externalScopeRule: String

    /// Statement that computability does not imply business values exist.
    disclaimer: String
}

/// Counter breakdown of the manifest.
structure MetricReportCounts {
    /// Rows with publishable=true.
    publishableTrue: Integer

    /// Rows whose evidence basis is industry.
    industry: Integer

    /// Rows whose evidence basis is regulatory.
    regulatory: Integer

    /// Rows that pass the external-eligibility rule.
    externalEligible: Integer

    /// Rows with external status external_candidate.
    externalCandidates: Integer

    /// Rows executable right now.
    executableNow: Integer

    /// Industry rows excluded from external output.
    industryExcludedFromExternal: Integer

    /// Row count per computability tier.
    computability: MetricReportComputabilityCounts
}

/// Row count per computability tier.
map MetricReportComputabilityCounts {
    /// Computability tier code.
    key: String

    /// Number of rows in that tier.
    value: Integer
}

/// Execution-path breakdown of the manifest.
structure MetricReportExecution {
    /// Rows with external status external_candidate.
    externalCandidates: Integer

    /// Rows executable right now.
    executableNow: Integer

    /// Rows executable from a rule set only.
    ruleSetOnly: Integer

    /// Rows that cannot be executed yet.
    unavailable: Integer

    /// Unavailable rows counted by reason code.
    byReason: MetricReportExecutionReasons

    /// Basis used by the execution judgement.
    basis: String

    /// Explanatory note for the execution judgement.
    note: String
}

/// Unavailable rows counted by reason code.
map MetricReportExecutionReasons {
    /// Stable reason code.
    key: String

    /// Number of rows with that reason.
    value: Integer
}

/// Filters applied to a manifest response.
structure MetricReportFilters {
    /// Applied scope.
    scope: String

    /// Applied domain filter.
    domain: String

    /// Applied evidence-basis filter.
    evidenceBasis: String

    /// Applied publishable filter.
    publishable: Boolean
}
// The two operations above are intentionally NOT appended to
// ControlPlaneService here; see the MERGE HOOK at the top of this file for the
// exact lines to add on the integration line.
