// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// Namespace-level ontology validation jobs.
//
// Two operations, deliberately. The engine also exposes `GET /validate/jobs`,
// but that list is process-local memory with no caller in the web app: putting
// it in the contract would advertise a history that does not survive a restart.
//
// This family is not `RunValidation` (`/graph/validate`). That one is a
// synchronous, kernel-side quality read used by the health board. These two are
// asynchronous, multi-tier SHACL/structural/review jobs whose result is polled
// by id.
$version: "2"

namespace com.amazon.semanticcontext.ontologyvalidation

use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#Uuid

/// Which validation tier a job runs.
enum OntologyValidationTier {
    /// Blocking checks: SHACL conformance, fatal structural errors.
    tier1_blocking

    /// Scoring checks: OntoQA-style structural metrics.
    tier2_scoring

    /// Review checks: findings surfaced for a human, not blocking.
    tier3_review
}

/// Lifecycle state of an asynchronous validation job.
enum OntologyValidationJobStatus {
    /// Accepted and queued; no work has started.
    pending

    /// The worker is running the requested tiers.
    running

    /// All requested tiers finished; `report` is present.
    completed

    /// The job aborted; `error` carries the reason and there is no report.
    failed
}

/// Severity of one finding, mirroring the tier that produced it.
enum OntologyValidationSeverity {
    /// Blocking finding; any `error` makes the report fail.
    error

    /// Non-blocking scoring warning.
    warning

    /// Informational, flagged for review.
    info
}

/// Identifier of a document or ontology the validation reads.
@length(min: 1, max: 2048)
string ValidationOntologyId

/// Identifier of an asynchronous validation job.
@length(min: 1, max: 128)
string OntologyValidationJobId

/// Turtle payload supplied inline instead of fetched from the catalog.
@length(min: 1, max: 1000000)
string ValidationTurtle

/// One natural-language competency question the ontology should answer.
///
/// Namespaced because `ontologyinduction` already defines `CompetencyQuestion`;
/// a service closure requires shape names to be unique case-insensitively
/// across namespaces.
@length(min: 1, max: 1024)
string OntologyValidationCompetencyQuestion

/// Tiers requested for one job, in the order they run.
@length(min: 1, max: 3)
list OntologyValidationTierList {
    member: OntologyValidationTier
}

/// Competency questions the Tier-3 review checks against.
@length(min: 0, max: 50)
list OntologyValidationQuestionList {
    member: OntologyValidationCompetencyQuestion
}

/// Findings produced by one job, in tier order.
@length(min: 0, max: 5000)
list OntologyValidationFindingList {
    member: OntologyValidationFinding
}

/// One validation finding.
structure OntologyValidationFinding {
    /// Validator that produced the finding, e.g. `shacl` or `structural`.
    @required
    validator: String

    /// Tier the finding belongs to.
    @required
    tier: OntologyValidationTier

    /// Severity; `error` blocks, the other two do not.
    @required
    severity: OntologyValidationSeverity

    /// Machine-readable finding code.
    @required
    code: String

    /// Human-readable description.
    @required
    message: String

    /// URI of the offending element, when the finding names one.
    subject: String

    /// Validator-specific detail (SHACL path, metric values). Shape is not
    /// pinned because it varies per validator.
    details: Document
}

/// OntoQA-style structural metrics produced by the Tier-2 pass.
///
/// Absent members mean the metric could not be computed. This is distinct from
/// zero: `connectedComponents: 0` would claim the graph is empty.
structure OntologyValidationMetrics {
    /// Declared classes.
    classCount: Integer

    /// Declared object properties.
    objectPropertyCount: Integer

    /// Declared datatype properties.
    datatypePropertyCount: Integer

    /// Non-inheritance relations divided by total relations.
    relationshipRichness: Double

    /// Datatype properties divided by classes.
    attributeRichness: Double

    /// Subclass relations divided by classes.
    inheritanceRichness: Double

    /// Deepest subclass chain.
    maxDepth: Integer

    /// Number of subgraphs not joined by any relation.
    connectedComponents: Integer
}

/// Result of a completed job.
structure OntologyValidationReport {
    /// Job this report belongs to.
    @required
    jobId: OntologyValidationJobId

    /// Ontology the job validated.
    ontologyId: ValidationOntologyId

    /// True only when no finding has severity `error`.
    @required
    passed: Boolean

    /// Every finding across the requested tiers.
    @required
    findings: OntologyValidationFindingList

    /// Structural metrics; absent when Tier 2 did not run.
    metrics: OntologyValidationMetrics

    /// Tiers that actually ran.
    @required
    tiersRun: OntologyValidationTierList

    /// When the report was produced (ISO-8601).
    @required
    createdAt: String
}

/// One asynchronous validation job, as returned by start and by poll.
structure OntologyValidationJob {
    /// Server-assigned job identifier.
    @required
    jobId: OntologyValidationJobId

    /// Current lifecycle state.
    @required
    status: OntologyValidationJobStatus

    /// When the job was accepted (ISO-8601).
    @required
    createdAt: String

    /// Result, present only when `status` is `completed`.
    report: OntologyValidationReport

    /// Failure reason, present only when `status` is `failed`.
    error: String
}

/// Start an asynchronous multi-tier validation of one ontology.
///
/// Returns as soon as the job is queued (HTTP 202); poll
/// `GetOntologyValidationJob` with the returned `jobId`. The ontology is read
/// from the catalog by id unless `ontologyTurtle` supplies it inline.
@examples([
    {
        title: "Queue a three-tier validation of a catalog ontology"
        input: {
            namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
            ontologyId: "urn:acme:ontology:supply-chain"
        }
        output: {
            jobId: "b7c9e2a1-4d3f-4a6b-9c8d-0e1f2a3b4c5d"
            status: "pending"
            createdAt: "2026-11-10T09:12:44Z"
        }
    }
])
@http(method: "POST", uri: "/namespaces/{namespaceId}/validate", code: 202)
operation StartOntologyValidation {
    input := {
        /// Namespace the job is scoped to.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology to validate, resolved through the catalog.
        @required
        ontologyId: ValidationOntologyId

        /// Inline Turtle that overrides the catalog copy.
        ontologyTurtle: ValidationTurtle

        /// Tiers to run; all three when absent.
        tiers: OntologyValidationTierList

        /// Custom SHACL shapes applied by the Tier-1 pass.
        shaclShapesTurtle: ValidationTurtle

        /// Competency questions the Tier-3 review answers.
        competencyQuestions: OntologyValidationQuestionList
    }

    output: OntologyValidationJob
}

/// Read the current state of one validation job.
///
/// Poll this after `StartOntologyValidation`. Unknown ids, and jobs belonging
/// to another namespace, both answer `NotFoundError` — the two are not
/// distinguished so a caller cannot probe for foreign job ids.
@readonly
@examples([
    {
        title: "Read a completed job with two findings"
        input: {
            namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
            jobId: "b7c9e2a1-4d3f-4a6b-9c8d-0e1f2a3b4c5d"
        }
        output: {
            jobId: "b7c9e2a1-4d3f-4a6b-9c8d-0e1f2a3b4c5d"
            status: "completed"
            createdAt: "2026-11-10T09:12:44Z"
            report: {
                jobId: "b7c9e2a1-4d3f-4a6b-9c8d-0e1f2a3b4c5d"
                ontologyId: "urn:acme:ontology:supply-chain"
                passed: false
                tiersRun: ["tier1_blocking", "tier2_scoring"]
                createdAt: "2026-11-10T09:12:51Z"
                findings: [
                    {
                        validator: "shacl"
                        tier: "tier1_blocking"
                        severity: "error"
                        code: "SHACL_VALIDATION_FAILED"
                        message: "Property ex:supplier is required but missing on 3 instances."
                        subject: "urn:acme:entity:shipment-42"
                    }
                    {
                        validator: "structural"
                        tier: "tier2_scoring"
                        severity: "warning"
                        code: "LOW_RELATIONSHIP_RICHNESS"
                        message: "Only 0.21 of relations are non-inheritance."
                    }
                ]
                metrics: {
                    classCount: 42
                    objectPropertyCount: 18
                    datatypePropertyCount: 27
                    relationshipRichness: 0.21
                    maxDepth: 4
                    connectedComponents: 1
                }
            }
        }
    }
])
@http(method: "GET", uri: "/namespaces/{namespaceId}/validate/jobs/{jobId}", code: 200)
operation GetOntologyValidationJob {
    input := {
        /// Namespace the job is scoped to.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Job to read.
        @required
        @httpLabel
        jobId: OntologyValidationJobId
    }

    output: OntologyValidationJob

    errors: [
        NotFoundError
    ]
}
