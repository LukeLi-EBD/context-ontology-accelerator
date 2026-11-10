// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// Platform metric card served by the local bridge.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.4 row F100 and
// doc/coa-x/18-platform-core拆解.md §KERNEL `/metrics/{metricId}`.
//
// Do not confuse this with `GetMetric` in metric-service.smithy: that op reads
// the namespaced metric registry (Dynamo-backed, wire shape `MetricDetail`).
// This op reads `platform.metric_definition` (Postgres-backed) and adds field
// bindings plus the external-evidence verdict, so it is a different resource
// with a different state machine and must stay a separate operation.
$version: "2"

namespace com.amazon.semanticcontext.platformmetric

use com.amazon.semanticcontext.common#NotFoundError

/// Stable metric identifier.
@length(min: 1, max: 128)
string PlatformMetricId

/// One physical binding of a metric to a fact-table column.
structure MetricFieldBinding {
    /// Role in the formula: `numerator`, `denominator`, or `index`.
    role: String

    /// Fact table the binding reads.
    factTable: String

    /// Column that holds the entity key.
    entityColumn: String

    /// SQL expression that produces the value.
    valueExpr: String

    /// Aggregate applied inside the window.
    agg: String

    /// Additional SQL predicate.
    filterSql: String

    /// Column used as the observation window.
    windowColumn: String

    /// Window mode (e.g. `calendar`, `rolling`).
    windowMode: String
}

list MetricFieldBindingList {
    member: MetricFieldBinding
}

/// One governed metric definition with bindings and external-evidence status.
structure MetricCard {
    /// Stable metric identifier.
    @required
    metricId: String

    /// Chinese metric name.
    name: String

    /// Metric domain.
    domain: String

    /// What kind of evidence backs the definition.
    evidenceBasis: String

    /// Whether the metric may be published.
    publishable: Boolean

    /// True when the metric is derived by inference rather than measured.
    inference: Boolean

    /// True when the formula is intentionally disabled.
    formulaDisabled: Boolean

    /// What is missing before the metric can be computed.
    missing: String

    /// Evidence status recorded on the definition.
    evidenceStatus: String

    /// Operator note attached to the definition.
    note: String

    /// Effective date of the definition (ISO-8601 date).
    effectiveDate: String

    /// Family index this metric is a variant of.
    variantOf: String

    /// Output mode: `single`, `index`, or `rule_set`.
    outputMode: String

    /// Rule-set payload; present only when `outputMode` is `rule_set`.
    ruleSet: Document

    /// Full prose definition.
    definition: String

    /// Formula as display text.
    formulaText: String

    /// Denominator as display text.
    denominatorText: String

    /// Observation period as display text.
    observationPeriodText: String

    /// Granularity as display text.
    granularityText: String

    /// Grain code matched against ontology class local names.
    grain: String

    /// Provenance label.
    provenanceLabel: String

    /// Unit of measure.
    unit: String

    /// Definition version.
    definitionVersion: String

    /// `bound` when at least one field binding exists, `unbound` otherwise.
    @required
    bindingStatus: String

    /// Physical bindings for this definition version.
    @required
    fieldBindings: MetricFieldBindingList

    /// True when the metric passes the external-evidence gate.
    externalEligible: Boolean

    /// External-evidence status code.
    externalStatus: String

    /// External-evidence status label.
    externalLabel: String

    /// Why the metric is (not) external-eligible.
    externalReason: String

    /// Family index this metric belongs to, when any.
    familyId: String

    /// Variant metric identifiers of the family.
    @required
    variantMetricIds: StringList
}

list StringList {
    member: String
}

/// Read the platform metric card.
///
/// `bindingStatus` is first-class: an unbound metric reports `unbound` and an
/// empty `fieldBindings` list. The source table is never invented to hide it.
@readonly
@http(method: "GET", uri: "/metrics/{metricId}", code: 200)
@examples([
    {
        title: "Read one metric card"
        input: { metricId: "M-001" }
        output: {
            metricId: "M-001"
            name: "合同金额"
            domain: "contract"
            evidenceBasis: "system"
            publishable: true
            inference: false
            formulaDisabled: false
            missing: ""
            evidenceStatus: "complete"
            note: ""
            effectiveDate: "2026-01-01"
            outputMode: "single"
            grain: "contract"
            definitionVersion: "v3"
            bindingStatus: "bound"
            fieldBindings: [
                { role: "numerator", factTable: "fact_contract", entityColumn: "contract_id", valueExpr: "amount", agg: "sum", windowMode: "calendar" }
            ]
            externalEligible: true
            externalStatus: "external_candidate"
            externalLabel: "可对外"
            externalReason: "证据链完整"
            variantMetricIds: []
        }
    }
])
operation GetMetricCard {
    input := {
        /// Stable metric identifier.
        @required
        @httpLabel
        metricId: PlatformMetricId
    }

    output: MetricCard

    errors: [
        NotFoundError
    ]
}
