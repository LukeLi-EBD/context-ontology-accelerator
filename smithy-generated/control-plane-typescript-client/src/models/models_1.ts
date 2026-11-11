// smithy-typescript generated code
import type { DocumentType as __DocumentType } from "@smithy/types";

import type {
  AnswerQualityStrategy,
  DatabaseEngine,
  ExtractionMode,
  GlueExecutionEngine,
  GroundingMode,
  InductionJobStatus,
  InductionSourceType,
  InductionStrategy,
  OntologyExportFormat,
  OntologyImpactChange,
  OntologyImportFormat,
  OntologyProposalDecision,
  OntologyProposalStatus,
  OntologyRollbackMode,
  OntologyValidationJobStatus,
  OntologyValidationSeverity,
  OntologyValidationTier,
  OntologyVersionStatus,
  PreprocessingIssueType,
  ProposalStatus,
  ProposalValidationJobStatus,
  ProposalValidationTier,
  QueryEngine,
  RescanChangeKind,
  RescanColumnChangeStatus,
  ReviewDecision,
  ReviewStatus,
  RoleScope,
  ScanJobEventType,
  ScanTrigger,
  SourceScanJobStatus,
  SourceStatus,
  SourceSubType,
  SourceType,
  SparqlAuthMode,
  SparqlStore,
} from "./enums";
import type {
  OntologyBrowseCounts,
  OntologyClassRef,
  OntologyPointer,
  OntologyPropertyRef,
  ProposalMetadata,
} from "./models_0";

/**
 * Summary of an inducted data source.
 * @public
 */
export interface InducedDatasource {
  /**
   * Data source identifier reference.
   * @public
   */
  datasourceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId?: string | undefined;

  /**
   * Ontology ID produced for this data source.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * Human-readable label for the induction run.
   * @public
   */
  label?: string | undefined;

  /**
   * Number of tables processed during induction.
   * @public
   */
  tablesProcessed?: number | undefined;

  /**
   * Number of columns processed during induction.
   * @public
   */
  columnsProcessed?: number | undefined;

  /**
   * Number of novel classes created (not grounded to existing concepts).
   * @public
   */
  novelClassesCreated?: number | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListInducedDatasourcesOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Data sources that have been successfully inducted.
   * @public
   */
  datasources: InducedDatasource[] | undefined;
}

/**
 * @public
 */
export interface ListInductionJobsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Filter by job status. Also accepts `ingested` (the job's proposal
   * was accepted) and `cancelled`, which the service stores but this
   * enum does not list. Any other value returns 400 listing the allowed
   * values.
   * @public
   */
  status?: InductionJobStatus | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of jobs to return in one page (default 50).
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * Summary of an induction job (for list views).
 * @public
 */
export interface InductionJobSummary {
  /**
   * UUID v4 identifier.
   * @public
   */
  jobId: string | undefined;

  /**
   * Induction job status.
   *
   * The first group of stages (PENDING through FAILED) covers the structured
   * induction pipeline (induce_catalog). The second group covers the
   * unstructured induction pipeline stage progression
   * (querying_neptune → sampling → generating_descriptions → resolving_iris →
   * applying_rules → entailment → serializing → storing → completed | failed).
   * @public
   */
  status: InductionJobStatus | undefined;

  /**
   * Timestamp when the induction job was created.
   * @public
   */
  createdAt: Date | undefined;

  /**
   * Origin of this induction run — STRUCTURED for table-to-ontology runs,
   * UNSTRUCTURED for knowledge-graph-to-ontology runs. Items lacking this
   * attribute on read SHALL be treated as STRUCTURED for backward compatibility.
   * @public
   */
  sourceType?: InductionSourceType | undefined;

  /**
   * Number of tables processed (populated after completion).
   * @public
   */
  tablesProcessed?: number | undefined;

  /**
   * Number of novel classes created.
   * @public
   */
  novelClassesCreated?: number | undefined;

  /**
   * Error message if failed.
   * @public
   */
  error?: string | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListInductionJobsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Induction jobs matching the query.
   * @public
   */
  jobs: InductionJobSummary[] | undefined;
}

/**
 * @public
 */
export interface ListProposalsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Filter by proposal status.
   * @public
   */
  status?: ProposalStatus | undefined;

  /**
   * Filter by target ontology ID. The server also accepts the legacy
   * spelling `ontology_id`; this one wins when both are sent.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * Filter by induction origin. `STRUCTURED` also matches proposals
   * recorded before the attribute existed.
   * @public
   */
  sourceType?: InductionSourceType | undefined;

  /**
   * Filter by proposal type (e.g. `induction`), exact match.
   * @public
   */
  proposalType?: string | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of proposals to return in one page (default 50). The
   * server also accepts the legacy spelling `limit`; this one wins.
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * Summary of a proposal (for list views).
 * @public
 */
export interface ProposalSummary {
  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Proposal status.
   *
   * ``inducing`` is the FIRST in-flight state: the induction was triggered and
   * a background worker is building the ontology. A stub proposal row is written
   * at trigger time (so the run is visible in the proposals list immediately and
   * survives a browser refresh); the same row is upserted to ``pending`` when the
   * worker finishes, or to ``failed`` if it errors. Clients poll ``ListProposals``
   * to observe the transition.
   *
   * ``accepting`` is a later in-flight state: the user submitted ``AcceptProposal``
   * and a background worker is merging the ontology. It is followed by
   * ``embeddingsSync`` while the just-written embeddings become searchable in the
   * (eventually-consistent) vector index. The status then flips to ``accepted``
   * on success, or to ``acceptFailed`` with ``acceptError`` naming the pipeline
   * step that failed. An ``acceptFailed`` proposal is re-acceptable — the accept
   * pipeline is idempotent on re-run — so the client may submit
   * ``AcceptProposal`` again once the cause is resolved. Clients poll
   * ``GetProposal`` to observe the transitions.
   * @public
   */
  status: ProposalStatus | undefined;

  /**
   * Ontology ID this proposal targets.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Origin of this proposal — STRUCTURED for table-to-ontology induction,
   * UNSTRUCTURED for knowledge-graph-to-ontology induction. Items lacking
   * this attribute on read SHALL be treated as STRUCTURED for backward
   * compatibility.
   * @public
   */
  sourceType?: InductionSourceType | undefined;

  /**
   * Proposal metadata.
   * @public
   */
  metadata?: ProposalMetadata | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListProposalsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Proposals matching the query.
   * @public
   */
  proposals: ProposalSummary[] | undefined;
}

/**
 * @public
 */
export interface LoadFoundationalOntologyInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Catalog key of the foundational ontology to load.
   * @public
   */
  key: string | undefined;

  /**
   * Optional idempotency token. A retry with the same token within 24
   * hours returns the original job handle instead of starting a second
   * load; reusing the token for a different key is rejected with a 409.
   * @public
   */
  clientToken?: string | undefined;
}

/**
 * @public
 */
export interface LoadFoundationalOntologyOutput {
  /**
   * Load status for the foundational ontology.
   * @public
   */
  status: string | undefined;

  /**
   * Ontology ID assigned to the loaded foundational ontology.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * Number of classes loaded.
   * @public
   */
  classCount?: number | undefined;

  /**
   * Number of embeddings generated.
   * @public
   */
  embeddingCount?: number | undefined;
}

/**
 * @public
 */
export interface RejectProposalsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * IDs of the proposals to reject.
   * @public
   */
  proposalIds: string[] | undefined;

  /**
   * Reason for rejecting the proposals.
   * @public
   */
  reason: string | undefined;
}

/**
 * @public
 */
export interface RejectProposalsOutput {
  /**
   * Number of proposals rejected.
   * @public
   */
  rejected: number | undefined;
}

/**
 * @public
 */
export interface RepairProposalDatatypesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * When true, preview the repairs (return the change list) without
   * persisting anything or changing the proposal's status. Defaults false.
   * @public
   */
  dryRun?: boolean | undefined;
}

/**
 * A single datatype-token rewrite applied by RepairProposalDatatypes.
 * @public
 */
export interface DatatypeRepairChange {
  /**
   * The malformed datatype IRI that was found.
   * @public
   */
  found: string | undefined;

  /**
   * The canonical XSD datatype IRI it was rewritten to.
   * @public
   */
  canonical: string | undefined;
}

/**
 * @public
 */
export interface RepairProposalDatatypesOutput {
  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Number of datatype tokens rewritten (0 when already clean). On a
   * dry run this is the number that WOULD be rewritten.
   * @public
   */
  repairedCount: number | undefined;

  /**
   * The (before → after) rewrites applied (or, on a dry run, that would
   * be applied), for the preview / post-repair summary.
   * @public
   */
  changes: DatatypeRepairChange[] | undefined;

  /**
   * Echoes the request mode: true when this was a non-persisting preview.
   * @public
   */
  dryRun?: boolean | undefined;
}

/**
 * Switches for one document-to-table bridge run. Every member is optional;
 * an omitted member takes the default named in its description. An unknown
 * member is rejected. The run makes one LLM call per batch of up to 25
 * columns of each table that has document evidence, plus grounding and
 * embedding calls; `maxTables` caps that one-off cost.
 * @public
 */
export interface BridgeOptions {
  /**
   * Most table classes considered in one run. Default 60.
   * @public
   */
  maxTables?: number | undefined;

  /**
   * Tables processed in parallel. Default 6.
   * @public
   */
  concurrency?: number | undefined;

  /**
   * Compute and report the plan without creating a proposal. Default false.
   * @public
   */
  dryRun?: boolean | undefined;
}

/**
 * @public
 */
export interface StartInductionInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Data source IDs to induct from. The table-based strategies
   * (`table_to_ontology`, `rigor_ontology`) need at least one; an empty
   * list is rejected with a 400. `unstructured_lexical_graph` reads the
   * lexical graph instead and accepts an empty list. `bridge_to_tables`
   * runs on an accepted ontology and ignores the list; send an empty one.
   * @public
   */
  datasourceIds: string[] | undefined;

  /**
   * URI prefix for generated ontology classes and properties. For the
   * `bridge_to_tables` strategy, the ID of the accepted ontology to
   * bridge (404 if the namespace has no such ontology).
   * @public
   */
  ontologyUriPrefix: string | undefined;

  /**
   * Human-readable label for this induction run.
   * @public
   */
  label?: string | undefined;

  /**
   * Confidence threshold for matching against existing ontologies.
   * @public
   */
  confidenceThreshold?: number | undefined;

  /**
   * Output-token cap for the ENHANCED-mode LLM grounding rerank.
   * Raise it when a reasoning model truncates its JSON answer (the
   * rerank fails loud naming this knob). Omitted → server default (1000).
   * @public
   */
  rerankMaxTokens?: number | undefined;

  /**
   * Induction strategy to use.
   * @public
   */
  strategy?: InductionStrategy | undefined;

  /**
   * Options for the `bridge_to_tables` strategy. Omitted → every
   * option takes its default. Set on another strategy it returns 400.
   * @public
   */
  bridgeOptions?: BridgeOptions | undefined;

  /**
   * Existing ontology IDs to ground against (reuse existing concepts).
   * @public
   */
  groundingOntologyIds?: string[] | undefined;

  /**
   * How aggressively to ground induced classes against existing ontologies.
   * Defaults to ENHANCED when omitted.
   * @public
   */
  groundingMode?: GroundingMode | undefined;

  /**
   * Caller-selected lexical sources are not supported. A Neptune Analytics
   * graph ARN or graph id returns HTTP 422 with ``detail.code`` set to
   * ``UNSUPPORTED_SOURCE``; the ``neptune-db`` sentinel names the
   * deployment-configured lexical source, the same as omitting the field.
   *
   * @deprecated (since 2026-10-01) Caller-selected lexical sources are not supported; omit this field.
   * @public
   */
  graphArn?: string | undefined;

  /**
   * Optional idempotency token. A retry with the same token and the same
   * parameters within 24 hours returns the original result instead of creating
   * a duplicate; reusing the token with different parameters is rejected with
   * ConflictError (409).
   * @public
   */
  clientToken?: string | undefined;
}

/**
 * @public
 */
export interface StartInductionOutput {
  /**
   * Unique job identifier for tracking progress.
   * @public
   */
  jobId: string | undefined;
}

/**
 * @public
 */
export interface UpdateProposalInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Revised OWL ontology in Turtle format.
   * @public
   */
  ontologyTurtle?: string | undefined;

  /**
   * Revised R2RML mappings in Turtle format.
   * @public
   */
  r2rmlTurtle?: string | undefined;

  /**
   * Class-level grounding choices keyed by the match's
   * sourceTableIdentity, or by its bare sourceTable when that name is
   * unique in the proposal. A bare sourceTable that several class-level
   * matches share is rejected with ConflictError and nothing is saved.
   * Values must be one of the candidates returned with the proposal.
   * Grounding choices cannot be combined with Turtle/R2RML edits in the
   * same request.
   * @public
   */
  groundingOverrides?: Record<string, string> | undefined;

  /**
   * Source tables whose grounding should be cleared so they remain
   * novel, keyed like groundingOverrides. Kept separate from
   * groundingOverrides because OpenAPI map values cannot faithfully
   * preserve Smithy sparse-map nulls.
   * @public
   */
  novelTables?: string[] | undefined;

  /**
   * Set true when the revised OWL ontology was uploaded directly to S3
   * via a presigned PUT (see GetProposalUploadUrls) instead of being sent
   * inline in `ontologyTurtle` — for large proposals exceeding the API
   * payload cap. Defaults to false (inline).
   * @public
   */
  ontologyUploaded?: boolean | undefined;

  /**
   * Set true when the revised R2RML was uploaded via presigned PUT
   * instead of inline `r2rmlTurtle`. Defaults to false (inline).
   * @public
   */
  r2rmlUploaded?: boolean | undefined;

  /**
   * Immutable revision returned by GetProposalUploadUrls. Required when
   * either uploaded flag is true so an upload cannot overwrite the
   * proposal's currently active artifacts before validation succeeds.
   * @public
   */
  uploadRevisionId?: string | undefined;
}

/**
 * @public
 */
export interface UpdateProposalOutput {
  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Proposal status.
   *
   * ``inducing`` is the FIRST in-flight state: the induction was triggered and
   * a background worker is building the ontology. A stub proposal row is written
   * at trigger time (so the run is visible in the proposals list immediately and
   * survives a browser refresh); the same row is upserted to ``pending`` when the
   * worker finishes, or to ``failed`` if it errors. Clients poll ``ListProposals``
   * to observe the transition.
   *
   * ``accepting`` is a later in-flight state: the user submitted ``AcceptProposal``
   * and a background worker is merging the ontology. It is followed by
   * ``embeddingsSync`` while the just-written embeddings become searchable in the
   * (eventually-consistent) vector index. The status then flips to ``accepted``
   * on success, or to ``acceptFailed`` with ``acceptError`` naming the pipeline
   * step that failed. An ``acceptFailed`` proposal is re-acceptable — the accept
   * pipeline is idempotent on re-run — so the client may submit
   * ``AcceptProposal`` again once the cause is resolved. Clients poll
   * ``GetProposal`` to observe the transitions.
   * @public
   */
  status: ProposalStatus | undefined;
}

/**
 * @public
 */
export interface ValidateProposalInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Validator tiers to run (defaults to all three tiers if omitted).
   * @public
   */
  tiers?: ProposalValidationTier[] | undefined;

  /**
   * Optional SHACL shapes Turtle for tier-1 SHACL validation.
   * @public
   */
  shaclShapesTurtle?: string | undefined;

  /**
   * Optional competency-question prompts for tier-3 LLM validators.
   * @public
   */
  competencyQuestions?: string[] | undefined;

  /**
   * Optional idempotency token. A retry with the same token and the same
   * parameters within 24 hours returns the original job handle instead of
   * starting a second validation job; reusing the token with different
   * parameters is rejected with a 409.
   * @public
   */
  clientToken?: string | undefined;
}

/**
 * @public
 */
export interface ValidateProposalOutput {
  /**
   * UUID v4 identifier.
   * @public
   */
  jobId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Status of a proposal validation job.
   * @public
   */
  status: ProposalValidationJobStatus | undefined;

  /**
   * Timestamp when the validation job was created.
   * @public
   */
  createdAt: string | undefined;
}

/**
 * @public
 */
export interface DiffOntologyVersionsInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Target version.
   * @public
   */
  versionId: string | undefined;

  /**
   * Baseline version; the current pointer when omitted.
   * @public
   */
  against?: string | undefined;
}

/**
 * One element that makes a diff breaking.
 * @public
 */
export interface OntologyBreakingItem {
  /**
   * Kind: `class_removed`, `property_removed`, `domain_narrowed`,
   * `range_narrowed`, or `property_became_required`.
   * @public
   */
  kind: string | undefined;

  /**
   * IRI of the affected class or property; absent for domain/range changes.
   * @public
   */
  iri?: string | undefined;

  /**
   * Property IRI for domain/range changes.
   * @public
   */
  property?: string | undefined;

  /**
   * Values before the change.
   * @public
   */
  from?: string[] | undefined;

  /**
   * Values after the change.
   * @public
   */
  to?: string[] | undefined;
}

/**
 * Domain or range values before and after one property change.
 * @public
 */
export interface OntologyDomainChange {
  /**
   * Property IRI.
   * @public
   */
  property: string | undefined;

  /**
   * Values before the change.
   * @public
   */
  from: string[] | undefined;

  /**
   * Values after the change.
   * @public
   */
  to: string[] | undefined;
}

/**
 * A class whose instances would disappear.
 * @public
 */
export interface OntologyClassInstance {
  /**
   * Class IRI.
   * @public
   */
  class: string | undefined;

  /**
   * Current instance count of that class.
   * @public
   */
  instances: number | undefined;
}

/**
 * Structural summary of a diff.
 * @public
 */
export interface OntologyDiffSummary {
  /**
   * Triples added by the target version.
   * @public
   */
  addedTriples: number | undefined;

  /**
   * Triples removed by the target version.
   * @public
   */
  removedTriples: number | undefined;

  /**
   * Class IRIs added.
   * @public
   */
  addedClasses: string[] | undefined;

  /**
   * Class IRIs removed.
   * @public
   */
  removedClasses: string[] | undefined;

  /**
   * Property IRIs added.
   * @public
   */
  addedProperties: string[] | undefined;

  /**
   * Property IRIs removed.
   * @public
   */
  removedProperties: string[] | undefined;

  /**
   * Domain changes per property.
   * @public
   */
  domainChanges: OntologyDomainChange[] | undefined;

  /**
   * Range changes per property.
   * @public
   */
  rangeChanges: OntologyDomainChange[] | undefined;

  /**
   * Removed classes with their instance counts.
   * @public
   */
  removedClassInstances: OntologyClassInstance[] | undefined;
}

/**
 * What changed between two versions.
 * @public
 */
export interface OntologyDiff {
  /**
   * Baseline version; absent when the target is the first version.
   * @public
   */
  from?: string | undefined;

  /**
   * Target version.
   * @public
   */
  to: string | undefined;

  /**
   * True when at least one breaking item exists.
   * @public
   */
  breaking: boolean | undefined;

  /**
   * Elements that make the diff breaking.
   * @public
   */
  breakingItems: OntologyBreakingItem[] | undefined;

  /**
   * Structural summary.
   * @public
   */
  summary: OntologyDiffSummary | undefined;

  /**
   * Pre-rendered Markdown description of the diff.
   * @public
   */
  markdown?: string | undefined;
}

/**
 * @public
 */
export interface ExportOntologyVersionInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Version to export.
   * @public
   */
  versionId: string | undefined;

  /**
   * Serialisation; Turtle when omitted.
   * @public
   */
  format?: OntologyExportFormat | undefined;
}

/**
 * @public
 */
export interface ExportOntologyVersionOutput {
  /**
   * Serialised ontology text, with the media type the server chose
   * (`text/turtle` or `application/n-quads`).
   * @public
   */
  content: string | undefined;
}

/**
 * @public
 */
export interface GetOntologyVersionInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Version to read.
   * @public
   */
  versionId: string | undefined;
}

/**
 * One row of the hash-chained lifecycle audit log.
 * @public
 */
export interface OntologyEvent {
  /**
   * Monotonic event identifier.
   * @public
   */
  eventId: number | undefined;

  /**
   * Version the event belongs to.
   * @public
   */
  versionId?: string | undefined;

  /**
   * Proposal the event belongs to.
   * @public
   */
  proposalId?: string | undefined;

  /**
   * Action recorded, e.g. `published`, `rolled_back`, `approved`.
   * @public
   */
  action: string | undefined;

  /**
   * Who performed the action.
   * @public
   */
  actor: string | undefined;

  /**
   * Optional reason recorded with the action.
   * @public
   */
  reason?: string | undefined;

  /**
   * Action payload, as the kernel stored it.
   * @public
   */
  payload?: __DocumentType | undefined;

  /**
   * Previous event identifier in the chain.
   * @public
   */
  prevEvent?: number | undefined;

  /**
   * Hash of this event.
   * @public
   */
  hash?: string | undefined;

  /**
   * Event time (ISO-8601).
   * @public
   */
  createdAt: string | undefined;

  /**
   * Alias of `action`, kept for older callers.
   * @public
   */
  type?: string | undefined;

  /**
   * Alias of `createdAt`, kept for older callers.
   * @public
   */
  at?: string | undefined;

  /**
   * `published`, `rolled_back`, `superseded`, or `other`.
   * @public
   */
  category?: string | undefined;
}

/**
 * One affected class.
 * @public
 */
export interface OntologyImpactClass {
  /**
   * Class IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label; the IRI's local name when the T-Box has no label.
   * @public
   */
  label: string | undefined;

  /**
   * How the class changed.
   * @public
   */
  change: OntologyImpactChange | undefined;

  /**
   * Triples added under this class.
   * @public
   */
  addedTriples: number | undefined;

  /**
   * Triples removed under this class.
   * @public
   */
  removedTriples: number | undefined;
}

/**
 * Instance count of one affected class.
 * @public
 */
export interface OntologyImpactClassInstances {
  /**
   * Class IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label.
   * @public
   */
  label: string | undefined;

  /**
   * Instances of the class across the A-Box graphs.
   *
   * Not computable when no A-Box graph is configured. Both an absent member
   * and an explicit `null` mean exactly that, and the kernel sends `null`;
   * neither is `0`. A configured A-Box that genuinely holds no instance
   * reports `0`. Client generators model this as an optional member
   * (`?: number`), so treat `null` as a value the field can actually hold
   * at runtime.
   * @public
   */
  instances?: number | undefined;
}

/**
 * Instance impact of the change.
 * @public
 */
export interface OntologyImpactInstances {
  /**
   * Instances across every A-Box graph.
   *
   * Not computable when no A-Box graph is configured. Both an absent member
   * and an explicit `null` mean exactly that, and the kernel sends `null`;
   * neither is `0`. A configured A-Box with no instances reports `0`.
   * Client generators model this as an optional member (`?: number`), so
   * treat `null` as a value the field can actually hold at runtime.
   * @public
   */
  total?: number | undefined;

  /**
   * Per-class counts, one entry per affected class.
   * @public
   */
  byClass: OntologyImpactClassInstances[] | undefined;

  /**
   * Where the counts came from.
   * @public
   */
  source?: string | undefined;

  /**
   * Why a count is absent, e.g. `没有 A-Box 图，实例数不可算；未以 0 代替`.
   * @public
   */
  note?: string | undefined;

  /**
   * Sum of `byClass[].instances` over the affected classes; A-Box only, so
   * absent whenever `total` is absent.
   * @public
   */
  affectedInstances?: number | undefined;

  /**
   * A-Box graph IRIs that were scanned; absent when none is configured.
   * @public
   */
  graphs?: string[] | undefined;
}

/**
 * One affected property.
 * @public
 */
export interface OntologyImpactProperty {
  /**
   * Property IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label; the IRI's local name when the T-Box has no label.
   * @public
   */
  label: string | undefined;

  /**
   * How the property changed.
   * @public
   */
  change: OntologyImpactChange | undefined;

  /**
   * Triples added under this property.
   * @public
   */
  addedTriples: number | undefined;

  /**
   * Triples removed under this property.
   * @public
   */
  removedTriples: number | undefined;

  /**
   * `rdfs:domain` changes recorded for this property.
   * @public
   */
  domainChanges: OntologyDomainChange[] | undefined;

  /**
   * `rdfs:range` changes recorded for this property.
   * @public
   */
  rangeChanges: OntologyDomainChange[] | undefined;
}

/**
 * What the change affects, as computed at read time.
 * @public
 */
export interface OntologyImpactAffected {
  /**
   * Affected classes.
   * @public
   */
  classes: OntologyImpactClass[] | undefined;

  /**
   * Affected properties.
   * @public
   */
  properties: OntologyImpactProperty[] | undefined;

  /**
   * Instance impact.
   * @public
   */
  instances: OntologyImpactInstances | undefined;
}

/**
 * One class or property in the aggregation view.
 * @public
 */
export interface OntologyImpactAggregation {
  /**
   * Class or property IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label.
   * @public
   */
  label: string | undefined;

  /**
   * Triples added under this IRI.
   * @public
   */
  addedTriples: number | undefined;

  /**
   * Triples removed under this IRI.
   * @public
   */
  removedTriples: number | undefined;
}

/**
 * Triple counts that could not be attributed to a class or property.
 * @public
 */
export interface OntologyImpactTripleCount {
  /**
   * Triples added.
   * @public
   */
  addedTriples: number | undefined;

  /**
   * Triples removed.
   * @public
   */
  removedTriples: number | undefined;
}

/**
 * Changed triples grouped by subject class and predicate property.
 * @public
 */
export interface OntologyImpactAggregations {
  /**
   * Changes grouped by subject class.
   * @public
   */
  byClass: OntologyImpactAggregation[] | undefined;

  /**
   * Changes grouped by predicate property.
   * @public
   */
  byProperty: OntologyImpactAggregation[] | undefined;

  /**
   * Triples whose subject and predicate are neither a known class nor a
   * known property.
   * @public
   */
  unclassified: OntologyImpactTripleCount | undefined;

  /**
   * True when the two versions have no triple difference.
   * @public
   */
  empty: boolean | undefined;

  /**
   * Why `byClass`/`byProperty` are empty.
   * @public
   */
  emptyReason?: string | undefined;

  /**
   * Aggregation method, e.g. `SPARQL GROUP BY ?s ?p over (to MINUS from)`.
   * @public
   */
  method?: string | undefined;

  /**
   * Row cap applied to the aggregation query.
   * @public
   */
  rowLimit?: number | undefined;
}

/**
 * Stored diff counts kept on a proposal row.
 * @public
 */
export interface OntologyImpactCounts {
  /**
   * Triples the target version adds.
   * @public
   */
  addedTriples: number | undefined;

  /**
   * Triples the target version removes.
   * @public
   */
  removedTriples: number | undefined;

  /**
   * Number of class IRIs added.
   * @public
   */
  addedClasses: number | undefined;

  /**
   * Number of class IRIs removed.
   * @public
   */
  removedClasses: number | undefined;

  /**
   * Number of property IRIs added.
   * @public
   */
  addedProperties: number | undefined;

  /**
   * Number of property IRIs removed.
   * @public
   */
  removedProperties: number | undefined;

  /**
   * Number of properties whose `rdfs:domain` changed.
   * @public
   */
  domainChanges: number | undefined;

  /**
   * Number of properties whose `rdfs:range` changed.
   * @public
   */
  rangeChanges: number | undefined;
}

/**
 * The change set the analysis was computed from.
 * @public
 */
export interface OntologyImpactChangeSet {
  /**
   * Counts derived from the stored diff.
   * @public
   */
  counts: OntologyImpactCounts | undefined;

  /**
   * Class IRIs added by the target version.
   * @public
   */
  addedClasses: string[] | undefined;

  /**
   * Class IRIs removed by the target version.
   * @public
   */
  removedClasses: string[] | undefined;

  /**
   * Property IRIs added by the target version.
   * @public
   */
  addedProperties: string[] | undefined;

  /**
   * Property IRIs removed by the target version.
   * @public
   */
  removedProperties: string[] | undefined;

  /**
   * Domain changes per property.
   * @public
   */
  domainChanges: OntologyDomainChange[] | undefined;

  /**
   * Range changes per property.
   * @public
   */
  rangeChanges: OntologyDomainChange[] | undefined;

  /**
   * True when at least one breaking item exists.
   * @public
   */
  breaking: boolean | undefined;

  /**
   * Elements that make the change breaking.
   * @public
   */
  breakingItems: OntologyBreakingItem[] | undefined;
}

/**
 * One metric that depends on the affected classes or properties.
 * @public
 */
export interface OntologyImpactMetric {
  /**
   * Metric identifier.
   * @public
   */
  metricId: string | undefined;

  /**
   * Metric display name.
   * @public
   */
  name?: string | undefined;

  /**
   * Tokens or binding paths that matched, e.g. `text:invoice` or
   * `binding:fact_x.invoice_no`.
   * @public
   */
  matchedBy: string[] | undefined;

  /**
   * Registries the match came from.
   * @public
   */
  source: string | undefined;
}

/**
 * A registry that could not be read while computing the dependencies.
 * @public
 */
export interface OntologyImpactNote {
  /**
   * Registry name, e.g. `metric_definition`.
   * @public
   */
  source: string | undefined;

  /**
   * Provider error raised while reading that registry.
   * @public
   */
  error: string | undefined;
}

/**
 * One metric rule that depends on the affected classes or properties.
 * @public
 */
export interface OntologyImpactRule {
  /**
   * Metric that owns the rule.
   * @public
   */
  metricId: string | undefined;

  /**
   * Rule identifier inside the metric's rule set.
   * @public
   */
  ruleId?: string | undefined;

  /**
   * Rule severity, as the rule set declares it.
   * @public
   */
  level?: string | undefined;

  /**
   * `rule_set_text` or `dependent_metric`.
   * @public
   */
  matchedBy: string | undefined;

  /**
   * Where the rule was read from.
   * @public
   */
  source: string | undefined;
}

/**
 * One dictionary term whose canonical IRI is affected.
 * @public
 */
export interface OntologyImpactTerm {
  /**
   * Surface form the term is written as.
   * @public
   */
  surface?: string | undefined;

  /**
   * Canonical IRI the surface form resolves to.
   * @public
   */
  canonical?: string | undefined;

  /**
   * Language tag, e.g. `zh`.
   * @public
   */
  lang?: string | undefined;

  /**
   * Where the term entry came from.
   * @public
   */
  source?: string | undefined;

  /**
   * Local name of `canonical`, for display.
   * @public
   */
  canonicalLabel?: string | undefined;
}

/**
 * Metrics, rules and terms that depend on the affected IRIs.
 * @public
 */
export interface OntologyImpactDependencies {
  /**
   * Metrics whose definitions or bindings mention an affected IRI.
   * @public
   */
  metrics: OntologyImpactMetric[] | undefined;

  /**
   * Metric rules that mention an affected IRI, or belong to a hit metric.
   * @public
   */
  rules: OntologyImpactRule[] | undefined;

  /**
   * Dictionary terms whose canonical IRI is affected.
   * @public
   */
  terms: OntologyImpactTerm[] | undefined;

  /**
   * Registries that could not be read; the analysis still returns.
   * @public
   */
  notes: OntologyImpactNote[] | undefined;

  /**
   * True when no metric and no rule matched.
   * @public
   */
  empty: boolean | undefined;

  /**
   * Why nothing matched.
   * @public
   */
  emptyReason?: string | undefined;

  /**
   * How the dependencies were matched.
   * @public
   */
  method?: string | undefined;
}

/**
 * One version the analysis read.
 * @public
 */
export interface OntologyImpactVersionRef {
  /**
   * Version identifier.
   * @public
   */
  versionId?: string | undefined;

  /**
   * Semantic version.
   * @public
   */
  semver?: string | undefined;

  /**
   * Canonical hash of the version.
   * @public
   */
  contentHash?: string | undefined;

  /**
   * Declared triple count.
   * @public
   */
  tripleCount?: number | undefined;
}

/**
 * Versions the analysis read.
 * @public
 */
export interface OntologyImpactInputs {
  /**
   * Baseline version; absent when the analysis had no baseline.
   * @public
   */
  from?: OntologyImpactVersionRef | undefined;

  /**
   * Target version.
   * @public
   */
  to?: OntologyImpactVersionRef | undefined;
}

/**
 * One class whose instance count was independently recounted.
 * @public
 */
export interface OntologyImpactSample {
  /**
   * Class IRI that was sampled.
   * @public
   */
  iri: string | undefined;

  /**
   * Count reported by the main pass.
   * @public
   */
  listed: number | undefined;

  /**
   * Count the independent recount returned.
   * @public
   */
  recounted: number | undefined;

  /**
   * True when `listed` and `recounted` agree.
   * @public
   */
  consistent: boolean | undefined;
}

/**
 * Independent recount of a sample of the affected class counts.
 * @public
 */
export interface OntologyImpactVerification {
  /**
   * Classes that were recounted.
   * @public
   */
  sampled: OntologyImpactSample[] | undefined;

  /**
   * True when every sampled class agreed.
   *
   * Not computable when there is no A-Box graph, or when nothing was
   * sampled. Both an absent member and an explicit `null` mean "cannot be
   * computed", and the kernel sends `null`; neither is `false`. Client
   * generators model this as an optional member (`?: boolean`), so treat
   * `null` as a value the field can actually hold at runtime.
   * @public
   */
  consistent?: boolean | undefined;

  /**
   * Why no sample was taken, or which class disagreed.
   * @public
   */
  reason?: string | undefined;

  /**
   * Recount method, e.g. `独立 SPARQL 重算（逐类 COUNT DISTINCT）`.
   * @public
   */
  source?: string | undefined;
}

/**
 * Read-only change impact analysis of one proposal.
 *
 * `readOnly` is always true: the analysis runs SPARQL reads and registry
 * queries and writes nothing.
 * @public
 */
export interface OntologyImpactAnalysis {
  /**
   * Baseline version; absent when the target has no previous version.
   * @public
   */
  from?: string | undefined;

  /**
   * Target version.
   * @public
   */
  to: string | undefined;

  /**
   * The change set that was analysed.
   * @public
   */
  changeSet: OntologyImpactChangeSet | undefined;

  /**
   * Classes, properties and instances the change touches.
   * @public
   */
  affected: OntologyImpactAffected | undefined;

  /**
   * Changed triples grouped by class and property.
   * @public
   */
  aggregations: OntologyImpactAggregations | undefined;

  /**
   * Metrics, rules and terms that depend on the affected IRIs.
   * @public
   */
  dependencies: OntologyImpactDependencies | undefined;

  /**
   * Independent recount of a sample of the class counts.
   * @public
   */
  verification: OntologyImpactVerification | undefined;

  /**
   * Versions the analysis read, when it had both endpoints.
   * @public
   */
  inputs?: OntologyImpactInputs | undefined;

  /**
   * SHA-256 over both content hashes and the diff.
   * @public
   */
  inputsFingerprint?: string | undefined;

  /**
   * True when classes, properties, metrics and rules are all empty.
   * @public
   */
  empty: boolean | undefined;

  /**
   * Why the analysis is empty.
   * @public
   */
  emptyReason?: string | undefined;

  /**
   * When the analysis ran (ISO-8601).
   * @public
   */
  computedAt: string | undefined;

  /**
   * Data the analysis was computed from.
   * @public
   */
  source: string | undefined;

  /**
   * Always true; the analysis never writes.
   * @public
   */
  readOnly: boolean | undefined;
}

/**
 * Why the impact analysis could not be produced.
 * @public
 */
export interface OntologyImpactError {
  /**
   * Stable provider code.
   * @public
   */
  code: string | undefined;

  /**
   * Human-readable explanation.
   * @public
   */
  message: string | undefined;

  /**
   * Code-specific detail, e.g. the version that could not be read.
   * @public
   */
  details?: __DocumentType | undefined;
}

/**
 * Impact of a proposal.
 *
 * The counts are written when the proposal is filed. `analysis` and
 * `analysisError` are mutually exclusive: exactly one of them is present on
 * every read, so a caller can always tell "analysed" from "analysis failed".
 * @public
 */
export interface OntologyImpact {
  /**
   * Triples the target version adds.
   * @public
   */
  addedTriples?: number | undefined;

  /**
   * Triples the target version removes.
   * @public
   */
  removedTriples?: number | undefined;

  /**
   * Number of class IRIs added.
   * @public
   */
  addedClasses?: number | undefined;

  /**
   * Number of class IRIs removed.
   * @public
   */
  removedClasses?: number | undefined;

  /**
   * Number of property IRIs added.
   * @public
   */
  addedProperties?: number | undefined;

  /**
   * Number of property IRIs removed.
   * @public
   */
  removedProperties?: number | undefined;

  /**
   * Number of properties whose `rdfs:domain` changed.
   * @public
   */
  domainChanges?: number | undefined;

  /**
   * Number of properties whose `rdfs:range` changed.
   * @public
   */
  rangeChanges?: number | undefined;

  /**
   * Total instances belonging to removed classes.
   * @public
   */
  removedClassInstances?: number | undefined;

  /**
   * Number of breaking items recorded in the diff.
   * @public
   */
  breakingItems?: number | undefined;

  /**
   * Read-only analysis; present when the analysis succeeded.
   * @public
   */
  analysis?: OntologyImpactAnalysis | undefined;

  /**
   * Why the analysis failed; present when `analysis` is absent.
   * @public
   */
  analysisError?: OntologyImpactError | undefined;
}

/**
 * One lifecycle proposal.
 * @public
 */
export interface OntologyProposal {
  /**
   * Proposal identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Version the proposal is about.
   * @public
   */
  versionId: string | undefined;

  /**
   * Version the diff was computed against.
   * @public
   */
  againstVersion?: string | undefined;

  /**
   * What the proposal changes.
   * @public
   */
  changeSummary?: string | undefined;

  /**
   * Proposal state.
   * @public
   */
  status: OntologyProposalStatus | undefined;

  /**
   * True when the diff contains breaking items.
   * @public
   */
  breaking: boolean | undefined;

  /**
   * True when a caller acknowledged the breaking items.
   * @public
   */
  acknowledgedBreaking?: boolean | undefined;

  /**
   * Diff stored at propose time.
   * @public
   */
  diff?: OntologyDiff | undefined;

  /**
   * Counts derived from the diff, plus the read-only impact analysis.
   * @public
   */
  impact?: OntologyImpact | undefined;

  /**
   * Who created the proposal.
   * @public
   */
  createdBy?: string | undefined;

  /**
   * Creation time (ISO-8601).
   * @public
   */
  createdAt?: string | undefined;

  /**
   * Who approved the proposal.
   * @public
   */
  approvedBy?: string | undefined;

  /**
   * Approval time (ISO-8601).
   * @public
   */
  approvedAt?: string | undefined;

  /**
   * Publish time of the proposal (ISO-8601).
   * @public
   */
  publishedAt?: string | undefined;

  /**
   * State of the underlying version, present on list and detail reads.
   * @public
   */
  versionStatus?: OntologyVersionStatus | undefined;
}

/**
 * A version row plus its proposals and audit events.
 * @public
 */
export interface OntologyVersionDetail {
  /**
   * Version identifier.
   * @public
   */
  id: string | undefined;

  /**
   * Contract alias of `id`.
   * @public
   */
  versionId: string | undefined;

  /**
   * Semantic version.
   * @public
   */
  semver: string | undefined;

  /**
   * Lifecycle state.
   * @public
   */
  status: OntologyVersionStatus | undefined;

  /**
   * SHA-256 of the canonical graph.
   * @public
   */
  contentHash?: string | undefined;

  /**
   * Declared triple count.
   * @public
   */
  tripleCount?: number | undefined;

  /**
   * Source serialisation.
   * @public
   */
  format?: string | undefined;

  /**
   * Graph IRI holding the triples.
   * @public
   */
  graph?: string | undefined;

  /**
   * Contract alias of `graph`.
   * @public
   */
  graphUri?: string | undefined;

  /**
   * Contract alias of `tripleCount`.
   * @public
   */
  statementCount?: number | undefined;

  /**
   * Triples actually present in the graph store.
   * @public
   */
  graphTripleCount?: number | undefined;

  /**
   * Version this one rolled back to, when applicable.
   * @public
   */
  rollbackOf?: string | undefined;

  /**
   * Human-readable label.
   * @public
   */
  label?: string | undefined;

  /**
   * Creation time (ISO-8601).
   * @public
   */
  createdAt?: string | undefined;

  /**
   * Publish time (ISO-8601).
   * @public
   */
  publishedAt?: string | undefined;

  /**
   * Proposals filed against this version.
   * @public
   */
  proposals?: OntologyProposal[] | undefined;

  /**
   * Audit events recorded for this version.
   * @public
   */
  events?: OntologyEvent[] | undefined;
}

/**
 * @public
 */
export interface GetOntologyVersionProposalInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Proposal to read.
   * @public
   */
  proposalId: string | undefined;
}

/**
 * One T-Box version row, as the registry stores it.
 * @public
 */
export interface OntologyVersion {
  /**
   * Version identifier.
   * @public
   */
  id: string | undefined;

  /**
   * Semantic version, e.g. `1.2.0` or `1.2.0+rollback.1`.
   * @public
   */
  semver: string | undefined;

  /**
   * Lifecycle state.
   * @public
   */
  status: OntologyVersionStatus | undefined;

  /**
   * SHA-256 of the canonical graph.
   * @public
   */
  contentHash?: string | undefined;

  /**
   * Declared triple count of the version.
   * @public
   */
  tripleCount?: number | undefined;

  /**
   * Source serialisation (`turtle` or `nt`).
   * @public
   */
  format?: string | undefined;

  /**
   * Graph IRI holding the version's triples.
   * @public
   */
  graph?: string | undefined;

  /**
   * When set, the version was created by rolling back to this version.
   * @public
   */
  rollbackOf?: string | undefined;

  /**
   * Human-readable label.
   * @public
   */
  label?: string | undefined;

  /**
   * Creation time (ISO-8601).
   * @public
   */
  createdAt?: string | undefined;

  /**
   * First publish time (ISO-8601); absent while never published.
   * @public
   */
  publishedAt?: string | undefined;
}

/**
 * A proposal plus its version and the diff stored at propose time.
 * @public
 */
export interface OntologyProposalDetail {
  /**
   * The proposal itself.
   * @public
   */
  proposal: OntologyProposal | undefined;

  /**
   * Version the proposal targets.
   * @public
   */
  version: OntologyVersion | undefined;

  /**
   * State of that version.
   * @public
   */
  versionStatus: OntologyVersionStatus | undefined;

  /**
   * Diff stored at propose time.
   * @public
   */
  diff: OntologyDiff | undefined;

  /**
   * Counts derived from the diff, plus the read-only impact analysis.
   * @public
   */
  impact?: OntologyImpact | undefined;

  /**
   * Current pointer; absent when nothing is published.
   * @public
   */
  current?: OntologyPointer | undefined;
}

/**
 * @public
 */
export interface ImportOntologyInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier; also the default target namespace.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Ontology text to parse.
   * @public
   */
  content: string | undefined;

  /**
   * Serialisation of `content`; Turtle when omitted.
   * @public
   */
  format?: OntologyImportFormat | undefined;

  /**
   * Summary of what the upload changes.
   * @public
   */
  changeSummary?: string | undefined;

  /**
   * Author recorded on the import record.
   * @public
   */
  author?: string | undefined;
}

/**
 * SHACL outcome recorded by an import.
 * @public
 */
export interface OntologyShaclResult {
  /**
   * Identifier of the deployed shapes graph.
   * @public
   */
  shapesId?: string | undefined;

  /**
   * Version of the deployed shapes graph.
   * @public
   */
  shapesVersion?: string | undefined;

  /**
   * True when the shapes conform; null when no shapes were configured.
   * @public
   */
  conforms?: boolean | undefined;

  /**
   * Number of violations reported by the validator.
   * @public
   */
  violationCount?: number | undefined;

  /**
   * `validated` or `error`.
   * @public
   */
  status?: string | undefined;

  /**
   * Validator engine, e.g. `pyshacl`.
   * @public
   */
  engine?: string | undefined;

  /**
   * Validation error, when `status` is `error`.
   * @public
   */
  error?: string | undefined;

  /**
   * Violations reported by the validator.
   * @public
   */
  violations?: __DocumentType[] | undefined;
}

/**
 * Result of `ImportOntology`: the draft row the registry created.
 * @public
 */
export interface OntologyImportResult {
  /**
   * Import record identifier.
   * @public
   */
  importId: string | undefined;

  /**
   * Draft version identifier.
   * @public
   */
  versionId: string | undefined;

  /**
   * Namespace the draft targets.
   * @public
   */
  targetNamespace?: string | undefined;

  /**
   * Author recorded on the import.
   * @public
   */
  author?: string | undefined;

  /**
   * Change summary recorded on the import.
   * @public
   */
  changeSummary?: string | undefined;

  /**
   * Serialisation the content was parsed as.
   * @public
   */
  format?: string | undefined;

  /**
   * Triples already in the baseline.
   * @public
   */
  triples?: number | undefined;

  /**
   * Triples in the imported graph.
   * @public
   */
  totalTriples?: number | undefined;

  /**
   * Distinct OWL classes.
   * @public
   */
  classes?: number | undefined;

  /**
   * Distinct object properties.
   * @public
   */
  objectProperties?: number | undefined;

  /**
   * Distinct datatype properties.
   * @public
   */
  dataProperties?: number | undefined;

  /**
   * `owl:imports` IRIs declared by the source.
   * @public
   */
  importsDeclared?: string[] | undefined;

  /**
   * Imports that resolved against the search path.
   * @public
   */
  importsResolved?: __DocumentType[] | undefined;

  /**
   * Imports that did not resolve.
   * @public
   */
  unresolvedImports?: __DocumentType[] | undefined;

  /**
   * SHACL outcome.
   * @public
   */
  shacl?: OntologyShaclResult | undefined;

  /**
   * Consistency check outcome, as the reasoner reported it.
   * @public
   */
  consistency?: __DocumentType | undefined;

  /**
   * True when nothing blocks the draft from being proposed.
   * @public
   */
  usable?: boolean | undefined;

  /**
   * Provider code explaining why the draft is not usable.
   * @public
   */
  reason?: string | undefined;

  /**
   * Every blocker that made the draft unusable.
   * @public
   */
  usableReasons?: __DocumentType[] | undefined;

  /**
   * True when the import was published; always false at this boundary.
   * @public
   */
  published?: boolean | undefined;

  /**
   * True when the import record was written.
   * @public
   */
  persisted?: boolean | undefined;

  /**
   * Implementation slice that produced the result.
   * @public
   */
  slice?: string | undefined;

  /**
   * Staging graph written by the import.
   * @public
   */
  stagingGraph?: string | undefined;

  /**
   * SHA-256 of the uploaded source.
   * @public
   */
  sourceSha256?: string | undefined;

  /**
   * Import creation time (ISO-8601).
   * @public
   */
  createdAt?: string | undefined;
}

/**
 * @public
 */
export interface ListOntologyEventsInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Only events for this version.
   * @public
   */
  versionId?: string | undefined;

  /**
   * Only events with this action.
   * @public
   */
  action?: string | undefined;

  /**
   * Maximum events to return (1-1000).
   * @public
   */
  limit?: number | undefined;
}

/**
 * Filters accepted by `ListOntologyEvents`.
 * @public
 */
export interface OntologyEventFilter {
  /**
   * Version filter that was applied.
   * @public
   */
  versionId?: string | undefined;

  /**
   * Action filter that was applied.
   * @public
   */
  action?: string | undefined;
}

/**
 * Audit page for one ontology.
 * @public
 */
export interface OntologyEventPage {
  /**
   * Events, newest first.
   * @public
   */
  items: OntologyEvent[] | undefined;

  /**
   * Number of events returned.
   * @public
   */
  count: number | undefined;

  /**
   * Counts per category.
   * @public
   */
  categories?: Record<string, number> | undefined;

  /**
   * Filters echoed back by the server.
   * @public
   */
  filter?: OntologyEventFilter | undefined;

  /**
   * Current pointer at read time; absent when nothing is published.
   * @public
   */
  current?: OntologyPointer | undefined;
}

/**
 * @public
 */
export interface ListOntologyProposalsInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;
}

/**
 * Page of proposals for one ontology.
 * @public
 */
export interface OntologyProposalPage {
  /**
   * Proposals in creation order (newest first).
   * @public
   */
  items: OntologyProposal[] | undefined;

  /**
   * Number of proposals after filtering.
   * @public
   */
  count: number | undefined;

  /**
   * Number of proposals actually returned.
   * @public
   */
  returned: number | undefined;

  /**
   * Current pointer; absent when nothing is published.
   * @public
   */
  current?: OntologyPointer | undefined;
}

/**
 * @public
 */
export interface ListOntologyVersionsInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;
}

/**
 * Page of versions for one ontology.
 * @public
 */
export interface OntologyVersionPage {
  /**
   * Versions in creation order.
   * @public
   */
  items: OntologyVersion[] | undefined;

  /**
   * Number of versions returned.
   * @public
   */
  count: number | undefined;

  /**
   * Number of versions before the deprecated filter.
   * @public
   */
  total: number | undefined;

  /**
   * Deprecated versions filtered out of `items`.
   * @public
   */
  deprecated: number | undefined;

  /**
   * Current pointer; absent when nothing is published.
   * @public
   */
  pointer?: OntologyPointer | undefined;
}

/**
 * @public
 */
export interface ProposeOntologyVersionInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Draft version the proposal is about.
   * @public
   */
  versionId: string | undefined;

  /**
   * Why the draft should be published; also used as the change summary.
   * @public
   */
  rationale: string | undefined;

  /**
   * Baseline to diff against; the current pointer when omitted.
   * @public
   */
  againstVersion?: string | undefined;

  /**
   * Who files the proposal.
   * @public
   */
  actor?: string | undefined;
}

/**
 * @public
 */
export interface PublishOntologyInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Version to publish.
   * @public
   */
  versionId: string | undefined;

  /**
   * Proposal that authorises this publish.
   * @public
   */
  proposalId?: string | undefined;

  /**
   * Optimistic-concurrency guard: the pointer must still select this
   * version, otherwise the publish fails closed.
   * @public
   */
  expectedVersionId?: string | undefined;

  /**
   * Accept breaking changes recorded in the diff.
   * @public
   */
  acknowledgeBreaking?: boolean | undefined;

  /**
   * Re-activate an already registered version instead of staging a new
   * one.
   * @public
   */
  publishExisting?: boolean | undefined;

  /**
   * Run the gates and return the plan without writing anything.
   * @public
   */
  planOnly?: boolean | undefined;

  /**
   * Who publishes.
   * @public
   */
  actor?: string | undefined;

  /**
   * Reason recorded on the publish.
   * @public
   */
  reason?: string | undefined;
}

/**
 * One reason a publish plan would refuse to publish.
 * @public
 */
export interface PublishBlocker {
  /**
   * Gate that produced the blocker.
   * @public
   */
  gate: string | undefined;

  /**
   * Provider error code.
   * @public
   */
  code: string | undefined;

  /**
   * Human-readable explanation.
   * @public
   */
  message: string | undefined;

  /**
   * Gate-specific detail.
   * @public
   */
  details?: __DocumentType | undefined;
}

/**
 * Result of `PublishOntology`; a dry run fills the plan view, a real publish
 * fills the version view.
 * @public
 */
export interface PublishResult {
  /**
   * Always true on a successful real publish; absent on a dry run.
   * @public
   */
  ok?: boolean | undefined;

  /**
   * True when the call only ran the gates.
   * @public
   */
  dryRun?: boolean | undefined;

  /**
   * Version being published.
   * @public
   */
  versionId?: string | undefined;

  /**
   * State of that version at call time.
   * @public
   */
  versionStatus?: OntologyVersionStatus | undefined;

  /**
   * Version the pointer would replace.
   * @public
   */
  currentVersionId?: string | undefined;

  /**
   * Whether an already registered version was re-activated.
   * @public
   */
  publishExisting?: boolean | undefined;

  /**
   * Dry-run verdict: true when the publish would succeed.
   * @public
   */
  wouldPublish?: boolean | undefined;

  /**
   * Dry-run verdict: true when the publish would change the pointer.
   * @public
   */
  changed?: boolean | undefined;

  /**
   * Kernel alias of the published version.
   * @public
   */
  id?: string | undefined;

  /**
   * Contract name of the published version, added by the bridge.
   * @public
   */
  publishedVersion?: string | undefined;

  /**
   * Semver of the published version.
   * @public
   */
  semver?: string | undefined;

  /**
   * Graph IRI of the published version.
   * @public
   */
  graph?: string | undefined;

  /**
   * Declared triple count.
   * @public
   */
  tripleCount?: number | undefined;

  /**
   * Triples present in the graph store.
   * @public
   */
  triples?: number | undefined;

  /**
   * Version the pointer replaced.
   * @public
   */
  previousVersionId?: string | undefined;

  /**
   * Proposal that authorised the publish.
   * @public
   */
  proposalId?: string | undefined;

  /**
   * Who published.
   * @public
   */
  publishedBy?: string | undefined;

  /**
   * Publish time (ISO-8601).
   * @public
   */
  publishedAt?: string | undefined;

  /**
   * True when the pointer already selected this version.
   * @public
   */
  unchanged?: boolean | undefined;

  /**
   * True when a repeat publish returned the earlier result.
   * @public
   */
  idempotent?: boolean | undefined;

  /**
   * True when an approved proposal authorised the publish.
   * @public
   */
  governed?: boolean | undefined;

  /**
   * True when the publish created an implicit proposal.
   * @public
   */
  implicit?: boolean | undefined;

  /**
   * Kernel alias of `implicit`.
   * @public
   */
  implicitProposal?: boolean | undefined;

  /**
   * `publish`, `activate_existing`, `implicit`, or `governed`.
   * @public
   */
  mode?: string | undefined;

  /**
   * True when the diff contains breaking items.
   * @public
   */
  breaking?: boolean | undefined;

  /**
   * Whether the caller acknowledged breaking items.
   * @public
   */
  acknowledgeBreaking?: boolean | undefined;

  /**
   * Counts derived from the diff, plus the read-only impact analysis.
   * @public
   */
  impact?: OntologyImpact | undefined;

  /**
   * Per-gate verdicts.
   * @public
   */
  gates?: Record<string, __DocumentType> | undefined;

  /**
   * Reasons the publish would fail.
   * @public
   */
  blockers?: PublishBlocker[] | undefined;
}

/**
 * Result of `ReviewOntologyProposal`.
 * @public
 */
export interface OntologyProposalReviewResult {
  /**
   * Always true on a successful review.
   * @public
   */
  ok?: boolean | undefined;

  /**
   * Proposal that was reviewed.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Version the proposal targets.
   * @public
   */
  versionId?: string | undefined;

  /**
   * New proposal state.
   * @public
   */
  status?: OntologyProposalStatus | undefined;

  /**
   * New version state.
   * @public
   */
  versionStatus?: OntologyVersionStatus | undefined;

  /**
   * Who approved, when the decision was `APPROVE`.
   * @public
   */
  approvedBy?: string | undefined;

  /**
   * Approval time (ISO-8601).
   * @public
   */
  approvedAt?: string | undefined;

  /**
   * True when `proposed` was approved without a separate review step.
   * @public
   */
  reviewedImplicitly?: boolean | undefined;

  /**
   * Who rejected, when the decision was `REJECT`.
   * @public
   */
  rejectedBy?: string | undefined;

  /**
   * Rejection time (ISO-8601).
   * @public
   */
  rejectedAt?: string | undefined;

  /**
   * Reason recorded with the decision.
   * @public
   */
  reason?: string | undefined;

  /**
   * True when the proposal was already in the requested state.
   * @public
   */
  unchanged?: boolean | undefined;
}

/**
 * @public
 */
export interface ReviewOntologyProposalInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Proposal to review.
   * @public
   */
  proposalId: string | undefined;

  /**
   * `APPROVE` or `REJECT`.
   * @public
   */
  decision: OntologyProposalDecision | undefined;

  /**
   * Reviewer comment recorded with the decision.
   * @public
   */
  comment?: string | undefined;

  /**
   * Who reviews.
   * @public
   */
  actor?: string | undefined;
}

/**
 * Result of `RollbackOntology`; a plan-only call fills the plan view, a real
 * rollback fills the version view.
 * @public
 */
export interface OntologyRollbackResult {
  /**
   * Always true on a successful real rollback; absent on a plan.
   * @public
   */
  ok?: boolean | undefined;

  /**
   * Rollback strategy that was applied.
   * @public
   */
  mode?: OntologyRollbackMode | undefined;

  /**
   * Version the rollback restores; plan view.
   * @public
   */
  target?: OntologyVersion | undefined;

  /**
   * Version the pointer currently selects; plan view.
   * @public
   */
  replacedVersion?: OntologyVersion | undefined;

  /**
   * Identifier of the target version.
   * @public
   */
  targetVersionId?: string | undefined;

  /**
   * Triple count of the target version.
   * @public
   */
  targetTriples?: number | undefined;

  /**
   * Version the pointer replaced.
   * @public
   */
  replacedVersionId?: string | undefined;

  /**
   * Kernel alias of the published version.
   * @public
   */
  id?: string | undefined;

  /**
   * Contract name of the published version, added by the bridge.
   * @public
   */
  publishedVersion?: string | undefined;

  /**
   * For `NEW_VERSION`, the version that was copied.
   * @public
   */
  rollbackOf?: string | undefined;

  /**
   * Semver of the resulting version.
   * @public
   */
  semver?: string | undefined;

  /**
   * State of the resulting version.
   * @public
   */
  status?: OntologyVersionStatus | undefined;

  /**
   * Graph IRI of the resulting version.
   * @public
   */
  graph?: string | undefined;

  /**
   * Canonical hash of the resulting version.
   * @public
   */
  contentHash?: string | undefined;

  /**
   * Triples of the resulting version.
   * @public
   */
  triples?: number | undefined;

  /**
   * Previous pointer value.
   * @public
   */
  previous?: string | undefined;

  /**
   * Plan verdict: true when the pointer would move.
   * @public
   */
  wouldChangePointer?: boolean | undefined;

  /**
   * True when the pointer already selected the target.
   * @public
   */
  unchanged?: boolean | undefined;

  /**
   * Who rolled back.
   * @public
   */
  publishedBy?: string | undefined;

  /**
   * Publish time of the resulting version (ISO-8601).
   * @public
   */
  publishedAt?: string | undefined;

  /**
   * Rollback time (ISO-8601).
   * @public
   */
  rolledBackAt?: string | undefined;

  /**
   * Who rolled back.
   * @public
   */
  rolledBackBy?: string | undefined;

  /**
   * Reason recorded on the rollback.
   * @public
   */
  reason?: string | undefined;

  /**
   * Reasons a rollback would fail.
   * @public
   */
  blockers?: PublishBlocker[] | undefined;
}

/**
 * @public
 */
export interface RollbackOntologyInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Version to restore.
   * @public
   */
  targetVersionId: string | undefined;

  /**
   * `POINTER_ONLY` or `NEW_VERSION`; required so the effect is explicit.
   * @public
   */
  mode: OntologyRollbackMode | undefined;

  /**
   * Optimistic-concurrency guard for `POINTER_ONLY`.
   * @public
   */
  expectedVersionId?: string | undefined;

  /**
   * Return the plan only; nothing is written.
   * @public
   */
  planOnly?: boolean | undefined;

  /**
   * Who rolls back.
   * @public
   */
  actor?: string | undefined;

  /**
   * Reason recorded on the rollback.
   * @public
   */
  reason?: string | undefined;
}

/**
 * PROV chain verification result.
 * @public
 */
export interface OntologyProvResult {
  /**
   * True when every PROV link verifies.
   * @public
   */
  ok: boolean | undefined;

  /**
   * Number of PROV events checked.
   * @public
   */
  checked: number | undefined;

  /**
   * First failure, when `ok` is false.
   * @public
   */
  error?: string | undefined;

  /**
   * Hash of the last verified event.
   * @public
   */
  lastHash?: string | undefined;

  /**
   * PROV graph IRI.
   * @public
   */
  graph?: string | undefined;
}

/**
 * T-Box / PROV zero-mixing check.
 * @public
 */
export interface OntologySeparationResult {
  /**
   * True when neither graph carries the other's nodes.
   * @public
   */
  ok: boolean | undefined;

  /**
   * PROV graph IRI.
   * @public
   */
  provGraph?: string | undefined;

  /**
   * T-Box graph IRI.
   * @public
   */
  tboxGraph?: string | undefined;

  /**
   * Triples in the PROV graph.
   * @public
   */
  provTriples?: number | undefined;

  /**
   * PROV triples found in the T-Box graph.
   * @public
   */
  tboxProvTriples?: number | undefined;

  /**
   * T-Box triples found in the PROV graph.
   * @public
   */
  provTboxTriples?: number | undefined;

  /**
   * Legacy `prov:` predicates already present in the T-Box.
   * @public
   */
  tboxLegacyProvPredicateTriples?: number | undefined;
}

/**
 * Result of `VerifyOntology`.
 * @public
 */
export interface OntologyVerifyResult {
  /**
   * True when every link in the lifecycle chain verifies.
   * @public
   */
  ok: boolean | undefined;

  /**
   * Number of events checked before the first failure or the end.
   * @public
   */
  checked: number | undefined;

  /**
   * First failure, when `ok` is false.
   * @public
   */
  error?: string | undefined;

  /**
   * PROV chain verification result.
   * @public
   */
  prov: OntologyProvResult | undefined;

  /**
   * T-Box/PROV separation check.
   * @public
   */
  separation?: OntologySeparationResult | undefined;
}

/**
 * @public
 */
export interface VerifyOntologyInput {
  /**
   * Namespace that owns the ontology.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology identifier.
   * @public
   */
  ontologyId: string | undefined;
}

/**
 * @public
 */
export interface GetOntologyValidationJobInput {
  /**
   * Namespace the job is scoped to.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Job to read.
   * @public
   */
  jobId: string | undefined;
}

/**
 * One validation finding.
 * @public
 */
export interface OntologyValidationFinding {
  /**
   * Validator that produced the finding, e.g. `shacl` or `structural`.
   * @public
   */
  validator: string | undefined;

  /**
   * Tier the finding belongs to.
   * @public
   */
  tier: OntologyValidationTier | undefined;

  /**
   * Severity; `error` blocks, the other two do not.
   * @public
   */
  severity: OntologyValidationSeverity | undefined;

  /**
   * Machine-readable finding code.
   * @public
   */
  code: string | undefined;

  /**
   * Human-readable description.
   * @public
   */
  message: string | undefined;

  /**
   * URI of the offending element, when the finding names one.
   * @public
   */
  subject?: string | undefined;

  /**
   * Validator-specific detail (SHACL path, metric values). Shape is not
   * pinned because it varies per validator.
   * @public
   */
  details?: __DocumentType | undefined;
}

/**
 * OntoQA-style structural metrics produced by the Tier-2 pass.
 *
 * Absent members mean the metric could not be computed. This is distinct from
 * zero: `connectedComponents: 0` would claim the graph is empty.
 * @public
 */
export interface OntologyValidationMetrics {
  /**
   * Declared classes.
   * @public
   */
  classCount?: number | undefined;

  /**
   * Declared object properties.
   * @public
   */
  objectPropertyCount?: number | undefined;

  /**
   * Declared datatype properties.
   * @public
   */
  datatypePropertyCount?: number | undefined;

  /**
   * Non-inheritance relations divided by total relations.
   * @public
   */
  relationshipRichness?: number | undefined;

  /**
   * Datatype properties divided by classes.
   * @public
   */
  attributeRichness?: number | undefined;

  /**
   * Subclass relations divided by classes.
   * @public
   */
  inheritanceRichness?: number | undefined;

  /**
   * Deepest subclass chain.
   * @public
   */
  maxDepth?: number | undefined;

  /**
   * Number of subgraphs not joined by any relation.
   * @public
   */
  connectedComponents?: number | undefined;
}

/**
 * Result of a completed job.
 * @public
 */
export interface OntologyValidationReport {
  /**
   * Job this report belongs to.
   * @public
   */
  jobId: string | undefined;

  /**
   * Ontology the job validated.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * True only when no finding has severity `error`.
   * @public
   */
  passed: boolean | undefined;

  /**
   * Every finding across the requested tiers.
   * @public
   */
  findings: OntologyValidationFinding[] | undefined;

  /**
   * Structural metrics; absent when Tier 2 did not run.
   * @public
   */
  metrics?: OntologyValidationMetrics | undefined;

  /**
   * Tiers that actually ran.
   * @public
   */
  tiersRun: OntologyValidationTier[] | undefined;

  /**
   * When the report was produced (ISO-8601).
   * @public
   */
  createdAt: string | undefined;
}

/**
 * One asynchronous validation job, as returned by start and by poll.
 * @public
 */
export interface OntologyValidationJob {
  /**
   * Server-assigned job identifier.
   * @public
   */
  jobId: string | undefined;

  /**
   * Current lifecycle state.
   * @public
   */
  status: OntologyValidationJobStatus | undefined;

  /**
   * When the job was accepted (ISO-8601).
   * @public
   */
  createdAt: string | undefined;

  /**
   * Result, present only when `status` is `completed`.
   * @public
   */
  report?: OntologyValidationReport | undefined;

  /**
   * Failure reason, present only when `status` is `failed`.
   * @public
   */
  error?: string | undefined;
}

/**
 * @public
 */
export interface StartOntologyValidationInput {
  /**
   * Namespace the job is scoped to.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Ontology to validate, resolved through the catalog.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Inline Turtle that overrides the catalog copy.
   * @public
   */
  ontologyTurtle?: string | undefined;

  /**
   * Tiers to run; all three when absent.
   * @public
   */
  tiers?: OntologyValidationTier[] | undefined;

  /**
   * Custom SHACL shapes applied by the Tier-1 pass.
   * @public
   */
  shaclShapesTurtle?: string | undefined;

  /**
   * Competency questions the Tier-3 review answers.
   * @public
   */
  competencyQuestions?: string[] | undefined;
}

/**
 * @public
 */
export interface GetMetricCardInput {
  /**
   * Stable metric identifier.
   * @public
   */
  metricId: string | undefined;
}

/**
 * One physical binding of a metric to a fact-table column.
 * @public
 */
export interface MetricFieldBinding {
  /**
   * Role in the formula: `numerator`, `denominator`, or `index`.
   * @public
   */
  role?: string | undefined;

  /**
   * Fact table the binding reads.
   * @public
   */
  factTable?: string | undefined;

  /**
   * Column that holds the entity key.
   * @public
   */
  entityColumn?: string | undefined;

  /**
   * SQL expression that produces the value.
   * @public
   */
  valueExpr?: string | undefined;

  /**
   * Aggregate applied inside the window.
   * @public
   */
  agg?: string | undefined;

  /**
   * Additional SQL predicate.
   * @public
   */
  filterSql?: string | undefined;

  /**
   * Column used as the observation window.
   * @public
   */
  windowColumn?: string | undefined;

  /**
   * Window mode (e.g. `calendar`, `rolling`).
   * @public
   */
  windowMode?: string | undefined;
}

/**
 * One governed metric definition with bindings and external-evidence status.
 * @public
 */
export interface MetricCard {
  /**
   * Stable metric identifier.
   * @public
   */
  metricId: string | undefined;

  /**
   * Chinese metric name.
   * @public
   */
  name?: string | undefined;

  /**
   * Metric domain.
   * @public
   */
  domain?: string | undefined;

  /**
   * What kind of evidence backs the definition.
   * @public
   */
  evidenceBasis?: string | undefined;

  /**
   * Whether the metric may be published.
   * @public
   */
  publishable?: boolean | undefined;

  /**
   * True when the metric is derived by inference rather than measured.
   * @public
   */
  inference?: boolean | undefined;

  /**
   * True when the formula is intentionally disabled.
   * @public
   */
  formulaDisabled?: boolean | undefined;

  /**
   * What is missing before the metric can be computed.
   * @public
   */
  missing?: string | undefined;

  /**
   * Evidence status recorded on the definition.
   * @public
   */
  evidenceStatus?: string | undefined;

  /**
   * Operator note attached to the definition.
   * @public
   */
  note?: string | undefined;

  /**
   * Effective date of the definition (ISO-8601 date).
   * @public
   */
  effectiveDate?: string | undefined;

  /**
   * Family index this metric is a variant of.
   * @public
   */
  variantOf?: string | undefined;

  /**
   * Output mode: `single`, `index`, or `rule_set`.
   * @public
   */
  outputMode?: string | undefined;

  /**
   * Rule-set payload; present only when `outputMode` is `rule_set`.
   * @public
   */
  ruleSet?: __DocumentType | undefined;

  /**
   * Full prose definition.
   * @public
   */
  definition?: string | undefined;

  /**
   * Formula as display text.
   * @public
   */
  formulaText?: string | undefined;

  /**
   * Denominator as display text.
   * @public
   */
  denominatorText?: string | undefined;

  /**
   * Observation period as display text.
   * @public
   */
  observationPeriodText?: string | undefined;

  /**
   * Granularity as display text.
   * @public
   */
  granularityText?: string | undefined;

  /**
   * Grain code matched against ontology class local names.
   * @public
   */
  grain?: string | undefined;

  /**
   * Provenance label.
   * @public
   */
  provenanceLabel?: string | undefined;

  /**
   * Unit of measure.
   * @public
   */
  unit?: string | undefined;

  /**
   * Definition version.
   * @public
   */
  definitionVersion?: string | undefined;

  /**
   * `bound` when at least one field binding exists, `unbound` otherwise.
   * @public
   */
  bindingStatus: string | undefined;

  /**
   * Physical bindings for this definition version.
   * @public
   */
  fieldBindings: MetricFieldBinding[] | undefined;

  /**
   * True when the metric passes the external-evidence gate.
   * @public
   */
  externalEligible?: boolean | undefined;

  /**
   * External-evidence status code.
   * @public
   */
  externalStatus?: string | undefined;

  /**
   * External-evidence status label.
   * @public
   */
  externalLabel?: string | undefined;

  /**
   * Why the metric is (not) external-eligible.
   * @public
   */
  externalReason?: string | undefined;

  /**
   * Family index this metric belongs to, when any.
   * @public
   */
  familyId?: string | undefined;

  /**
   * Variant metric identifiers of the family.
   * @public
   */
  variantMetricIds: string[] | undefined;
}

/**
 * One citation attached to an answer.
 * @public
 */
export interface AnswerQualityCitation {
  /**
   * Citation identifier.
   * @public
   */
  id: string | undefined;

  /**
   * Citation kind, e.g. `document` or `fact`.
   * @public
   */
  kind: string | undefined;

  /**
   * Referenced identifier.
   * @public
   */
  ref: string | undefined;

  /**
   * Ontology or document version the citation resolved against.
   * @public
   */
  versionId?: string | undefined;

  /**
   * Console URL that resolves the citation.
   * @public
   */
  resolveUrl?: string | undefined;

  /**
   * True when the reference still resolves.
   * @public
   */
  resolvable: boolean | undefined;
}

/**
 * Actual answer produced for one golden-set case.
 * @public
 */
export interface AnswerQualityActual {
  /**
   * True when the answer was refused.
   * @public
   */
  refused: boolean | undefined;

  /**
   * Answer type chosen by the pipeline.
   * @public
   */
  answerType: string | undefined;

  /**
   * Answer mode chosen by the pipeline.
   * @public
   */
  answerMode: string | undefined;

  /**
   * Refusal reason code; absent when the answer was not refused.
   * @public
   */
  reasonCode?: string | undefined;

  /**
   * True when the answer was served degraded.
   * @public
   */
  degraded: boolean | undefined;

  /**
   * Citations attached to the answer.
   * @public
   */
  citations: AnswerQualityCitation[] | undefined;

  /**
   * Distinct citation kinds.
   * @public
   */
  citationKinds: string[] | undefined;

  /**
   * Retrieval layers that produced nothing.
   * @public
   */
  missingLayers: string[] | undefined;
}

/**
 * One golden-set case and its verdict.
 * @public
 */
export interface AnswerQualityCase {
  /**
   * Case identifier.
   * @public
   */
  id: string | undefined;

  /**
   * Query executed for the case.
   * @public
   */
  query: string | undefined;

  /**
   * Case type used for grouping.
   * @public
   */
  type: string | undefined;

  /**
   * True when the case expects a refusal.
   * @public
   */
  expectRefused: boolean | undefined;

  /**
   * Actual answer.
   * @public
   */
  actual: AnswerQualityActual | undefined;

  /**
   * True when the case passed.
   * @public
   */
  pass: boolean | undefined;

  /**
   * Failure codes recorded for the case.
   * @public
   */
  failures: string[] | undefined;

  /**
   * Console URL for the underlying answer.
   * @public
   */
  drillDownUrl?: string | undefined;
}

/**
 * Per-type aggregate used by the coverage and refusal breakdowns.
 * @public
 */
export interface AnswerQualityByType {
  /**
   * Case or answer type.
   * @public
   */
  type: string | undefined;

  /**
   * Number of cases of this type.
   * @public
   */
  cases: number | undefined;

  /**
   * Number of refused answers of this type.
   * @public
   */
  refused: number | undefined;

  /**
   * Number of answers with citations, when applicable.
   * @public
   */
  withCitations?: number | undefined;

  /**
   * Total citations of this type.
   * @public
   */
  citations: number | undefined;

  /**
   * Citations that resolve, when computed.
   * @public
   */
  resolvable?: number | undefined;

  /**
   * Share of cases with citations (0-1).
   * @public
   */
  citationCoverageRate: number | undefined;

  /**
   * Share of citations that resolve (0-1), when computed.
   * @public
   */
  resolvableRate?: number | undefined;

  /**
   * Share of answers refused (0-1), when computed.
   * @public
   */
  refusalRate?: number | undefined;
}

/**
 * The golden set that was evaluated.
 * @public
 */
export interface AnswerQualityGoldenSet {
  /**
   * Golden-set identifier.
   * @public
   */
  id: string | undefined;

  /**
   * Number of cases in the set.
   * @public
   */
  count: number | undefined;

  /**
   * Number of cases evaluated in this run.
   * @public
   */
  evaluated: number | undefined;

  /**
   * Identifier of the single case, when the run was narrowed to one case.
   * @public
   */
  caseId?: string | undefined;
}

/**
 * Refusal count grouped by case type and reason code.
 * @public
 */
export interface AnswerQualityRefusalReason {
  /**
   * Case type.
   * @public
   */
  type: string | undefined;

  /**
   * Refusal reason code.
   * @public
   */
  reasonCode: string | undefined;

  /**
   * Number of refusals.
   * @public
   */
  count: number | undefined;
}

/**
 * Aggregate rates over the run.
 * @public
 */
export interface AnswerQualitySummary {
  /**
   * Number of cases in the run.
   * @public
   */
  cases: number | undefined;

  /**
   * Number of passing cases.
   * @public
   */
  passed: number | undefined;

  /**
   * Number of failing cases.
   * @public
   */
  failed: number | undefined;

  /**
   * Share of passing cases (0-1).
   * @public
   */
  passRate: number | undefined;

  /**
   * Number of cases with at least one citation.
   * @public
   */
  casesWithCitations: number | undefined;

  /**
   * Share of cases with at least one citation (0-1).
   * @public
   */
  citationCoverageRate: number | undefined;

  /**
   * Total citations across the run.
   * @public
   */
  citations: number | undefined;

  /**
   * Citations whose reference resolves.
   * @public
   */
  resolvableCitations: number | undefined;

  /**
   * Share of citations that resolve (0-1).
   * @public
   */
  citationResolvableRate: number | undefined;

  /**
   * Share of citations that do not resolve (0-1).
   * @public
   */
  brokenLinkRate: number | undefined;

  /**
   * Broken-link rate recorded on the baseline.
   * @public
   */
  baselineBrokenLinkRate: number | undefined;

  /**
   * True when the broken-link rate regressed against the baseline.
   * @public
   */
  regression: boolean | undefined;
}

/**
 * One answer-quality run over the fixed golden set.
 * @public
 */
export interface AnswerQualityResponse {
  /**
   * Retrieval strategy used for the run.
   * @public
   */
  strategy: string | undefined;

  /**
   * Golden set that was evaluated.
   * @public
   */
  goldenSet: AnswerQualityGoldenSet | undefined;

  /**
   * Aggregate rates.
   * @public
   */
  summary: AnswerQualitySummary | undefined;

  /**
   * Citation coverage grouped by case type.
   * @public
   */
  citationCoverageByType?: AnswerQualityByType[] | undefined;

  /**
   * Refusal counts grouped by reason.
   * @public
   */
  refusalsByReason?: AnswerQualityRefusalReason[] | undefined;

  /**
   * Refusal counts grouped by type.
   * @public
   */
  refusalsByType?: AnswerQualityByType[] | undefined;

  /**
   * Refusals that carried no layer diagnostics.
   * @public
   */
  refusalsWithoutLayers?: __DocumentType[] | undefined;

  /**
   * Citations that no longer resolve.
   * @public
   */
  brokenLinks?: __DocumentType[] | undefined;

  /**
   * Per-case verdicts.
   * @public
   */
  cases: AnswerQualityCase[] | undefined;

  /**
   * True when the run evaluated no cases.
   * @public
   */
  empty: boolean | undefined;

  /**
   * Why the run is empty, when it is.
   * @public
   */
  emptyReason?: string | undefined;

  /**
   * Always true: the endpoint never writes.
   * @public
   */
  readOnly: boolean | undefined;
}

/**
 * @public
 */
export interface GetAnswerQualityInput {
  /**
   * Retrieval strategy for the run.
   * @public
   */
  strategy: AnswerQualityStrategy | undefined;

  /**
   * Maximum per-case details to return (1-50).
   * @public
   */
  limit?: number | undefined;
}

/**
 * @public
 */
export interface ListAnswerQualityRunsInput {
  /**
   * Maximum runs to return (1..200, default 20).
   * @public
   */
  limit?: number | undefined;

  /**
   * Only return runs produced with this strategy.
   * @public
   */
  strategy?: AnswerQualityStrategy | undefined;

  /**
   * Only return runs at or after this instant (inclusive).
   * @public
   */
  since?: Date | undefined;
}

/**
 * Citation coverage of one retrieval layer across a single run.
 *
 * A case counts as covered for a layer when at least one of its citations
 * belongs to that layer's citation kinds. The four layers are `ontology`,
 * `terms`, `metrics` and `facts`; a `chunk` citation is a document hit and is
 * not attributed to any of them.
 * @public
 */
export interface QualityLayerCoverage {
  /**
   * Layer name: `ontology`, `terms`, `metrics` or `facts`.
   * @public
   */
  layer: string | undefined;

  /**
   * Cases in the run with at least one citation from this layer.
   * @public
   */
  covered: number | undefined;

  /**
   * Cases evaluated in the run.
   * @public
   */
  evaluated: number | undefined;

  /**
   * `covered / evaluated`, 0..1.
   * @public
   */
  rate: number | undefined;
}

/**
 * One stored golden-set run. Every field is read from
 * `platform.answer_quality_run`; nothing is recomputed at read time.
 * @public
 */
export interface AnswerQualityRun {
  /**
   * Stored run id (`platform.answer_quality_run.run_id`), the same value the
   * quality response returned when the run was recorded.
   * @public
   */
  runId: string | undefined;

  /**
   * When the run finished, from `platform.answer_quality_run.ran_at`.
   * @public
   */
  ranAt: Date | undefined;

  /**
   * Retrieval strategy of the run.
   * @public
   */
  strategy: AnswerQualityStrategy | undefined;

  /**
   * Golden-set identifier, e.g. `r02-golden-10`.
   * @public
   */
  goldenSet: string | undefined;

  /**
   * Cases evaluated in the run.
   * @public
   */
  evaluated: number | undefined;

  /**
   * Cases that passed.
   * @public
   */
  passed: number | undefined;

  /**
   * Cases that failed.
   * @public
   */
  failed: number | undefined;

  /**
   * `passed / evaluated`, 0..1.
   * @public
   */
  passRate: number | undefined;

  /**
   * Share of cases with at least one citation, 0..1 (the run's overall
   * coverage).
   * @public
   */
  citationCoverageRate: number | undefined;

  /**
   * Share of citations that resolve to a reachable target, 0..1.
   * @public
   */
  citationResolvableRate: number | undefined;

  /**
   * Share of citations that do not resolve, 0..1.
   * @public
   */
  brokenLinkRate: number | undefined;

  /**
   * True when the run recorded at least one broken citation.
   * @public
   */
  regression: boolean | undefined;

  /**
   * Per-layer coverage. Absent for rows written before P14 started storing
   * the aggregation in `detail`; absent means "not recorded", never zero.
   * @public
   */
  layerCoverage?: QualityLayerCoverage[] | undefined;
}

/**
 * @public
 */
export interface ListAnswerQualityRunsOutput {
  /**
   * Stored runs, newest first.
   * @public
   */
  items: AnswerQualityRun[] | undefined;

  /**
   * Number of runs matching the filter, across all pages.
   * @public
   */
  totalCount: number | undefined;

  /**
   * Page size used for this response.
   * @public
   */
  limit: number | undefined;

  /**
   * Strategy filter echoed back; absent when unfiltered.
   * @public
   */
  strategy?: AnswerQualityStrategy | undefined;

  /**
   * Time-window lower bound echoed back; absent when unfiltered.
   * @public
   */
  since?: Date | undefined;

  /**
   * Always true: this operation never writes.
   * @public
   */
  readOnly: boolean | undefined;
}

/**
 * @public
 */
export interface GetNamespaceRoleInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Unique identifier of the role to retrieve.
   * @public
   */
  roleId: string | undefined;
}

/**
 * Full detail of a role, including its Cedar authorization policy.
 * @public
 */
export interface RoleDetail {
  /**
   * Unique identifier of the role.
   * @public
   */
  roleId: string | undefined;

  /**
   * Human-readable role name (lowercase alphanumeric and hyphens).
   * @public
   */
  name: string | undefined;

  /**
   * Role description.
   * @public
   */
  description?: string | undefined;

  /**
   * Scope at which a role applies: platform-wide or within a single namespace.
   * @public
   */
  scope: RoleScope | undefined;

  /**
   * Whether this is a built-in role (true) or a custom role (false).
   * @public
   */
  isBuiltIn: boolean | undefined;

  /**
   * The Cedar policy document defining the role's permissions.
   * @public
   */
  cedarPolicy?: string | undefined;
}

/**
 * Output containing the requested role's detail.
 * @public
 */
export interface GetNamespaceRoleOutput {
  /**
   * Full detail of a role, including its Cedar authorization policy.
   * @public
   */
  role: RoleDetail | undefined;
}

/**
 * @public
 */
export interface ListNamespaceRolesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;
}

/**
 * Summary view of a role, returned in role listings.
 * @public
 */
export interface RoleSummary {
  /**
   * Unique identifier of the role.
   * @public
   */
  roleId: string | undefined;

  /**
   * Human-readable role name (lowercase alphanumeric and hyphens).
   * @public
   */
  name: string | undefined;

  /**
   * Role description.
   * @public
   */
  description?: string | undefined;

  /**
   * Scope at which a role applies: platform-wide or within a single namespace.
   * @public
   */
  scope: RoleScope | undefined;

  /**
   * Whether this is a built-in role (true) or a custom role (false).
   * @public
   */
  isBuiltIn: boolean | undefined;
}

/**
 * Output containing the list of roles within a namespace.
 * @public
 */
export interface ListNamespaceRolesOutput {
  /**
   * The roles available within the namespace.
   * @public
   */
  roles: RoleSummary[] | undefined;
}

/**
 * @public
 */
export interface ListPlatformRolesInput {}

/**
 * Output containing the list of platform-scoped roles.
 * @public
 */
export interface ListPlatformRolesOutput {
  /**
   * The platform-scoped roles.
   * @public
   */
  roles: RoleSummary[] | undefined;
}

/**
 * @public
 */
export interface ApproveSourceInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source to approve.
   * @public
   */
  sourceId: string | undefined;
}

/**
 * @public
 */
export interface ApproveSourceOutput {
  /**
   * Identifier of the source being approved.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Unified lifecycle status for all source types.
   * @public
   */
  status: SourceStatus | undefined;
}

/**
 * Custom Athena Query Federation connector configuration — the
 * CUSTOM_CONNECTOR sub-type. The connector is a Lambda the customer authors
 * and deploys in their own account, which this service registers as a
 * Lambda-backed Athena data catalog in its own account; both discovery and
 * serve-time queries run through Athena against that catalog.
 *
 * Unlike GlueConfiguration there is no Glue database behind the source, so
 * there is no catalogId and no cross-account IAM role to assume: the customer
 * grants access on the connector Lambda's own resource policy instead. There
 * is also no region member — the connector must live in this deployment's
 * region (see connectorFunctionArn).
 * @public
 */
export interface CustomConnectorConfiguration {
  /**
   * ARN of the connector Lambda. ONE Lambda serves both metadata and record
   * requests — what Athena calls a composite handler. The ARN's region must
   * equal this deployment's own region, because Athena can only invoke a
   * data-source connector co-located with the query.
   *
   * Athena also accepts a split metadata/record PAIR of Lambdas, which this
   * member was once one half of. The pair is deliberately not modelled: the
   * reference connector and the CDK template customers are given both deploy a
   * single composite Lambda, so a second ARN asked every customer to reason
   * about a distinction almost none of them would make — and an ARN placed in
   * the wrong one of two adjacent members fails at query time rather than at
   * onboarding. Restoring it is purely additive (one optional member, plus the
   * record-function catalog parameter) if a customer ever needs the split form.
   * @public
   */
  connectorFunctionArn: string | undefined;

  /**
   * The single database inside the connector's catalog that this source
   * exposes. Exactly one database is resolved per source, so a connector
   * serving several databases is onboarded once per database.
   * @public
   */
  databaseName: string | undefined;

  /**
   * Include-filter applied to table names within databaseName. Omit to
   * discover every table.
   * @public
   */
  tableFilter?: string | undefined;

  /**
   * Exclude-filter applied to table names within databaseName, evaluated
   * after tableFilter.
   * @public
   */
  tableExcludeFilter?: string | undefined;
}

/**
 * Databricks SQL Warehouse source — the DATABRICKS_SQL_WAREHOUSE sub-type.
 * Discovery and queries both run through Athena against a connector Lambda this
 * service deploys, which resolves this configuration from the Athena catalog
 * name it is invoked under. Nothing here is deployed by the customer.
 *
 * Its own shape rather than an extra DatabaseEngine on JdbcConfiguration, whose
 * @required `host`/`port` have no meaning for a warehouse addressed by an HTTP
 * path and which has no place for the Unity Catalog catalog.
 * @public
 */
export interface DatabricksSqlWarehouseConfiguration {
  /**
   * Databricks workspace host, e.g. `dbc-a1b2345c-d6e7.cloud.databricks.com`.
   * A PrivateLink-only workspace is not reachable: the connector runs outside
   * any customer VPC.
   * @public
   */
  workspaceHostname: string | undefined;

  /**
   * SQL Warehouse HTTP path. The Databricks analogue of a port.
   * @public
   */
  httpPath: string | undefined;

  /**
   * Unity Catalog catalog pinned for this source. Lowercased at registration:
   * `information_schema` stores identifiers lowercase.
   * @public
   */
  databricksCatalog: string | undefined;

  /**
   * Unity Catalog schema this source exposes. Exactly one per source — the same
   * one-database-per-source model GlueConfiguration and
   * CustomConnectorConfiguration use. Lowercased at registration.
   * @public
   */
  databaseName: string | undefined;

  /**
   * Secret holding \{"token": ...\} for a personal access token, or
   * \{"client_id": ..., "client_secret": ...\} for OAuth machine-to-machine. The
   * shape selects the auth mode, so a customer cannot declare one mode and
   * store the other. Reachable only through crossAccountRoleArn, so its ACCOUNT
   * is unconstrained; it must be readable by that role and live in the
   * deployment region (Athena does not support cross-Region federated queries).
   *
   * Note an AWS constraint this service can neither impose nor relax: a secret
   * in a different account from the role must be encrypted with a
   * CUSTOMER-MANAGED key, because `aws/secretsmanager` cannot be shared across
   * accounts by any policy.
   * @public
   */
  credentialSecretArn: string | undefined;

  /**
   * Customer-owned IAM role the connector assumes to read
   * credentialSecretArn. Same member name, type and meaning as on
   * JdbcConfiguration and GlueConfiguration, and @required here rather than
   * optional: the connector holds no Secrets Manager permission of its own, so
   * there is no direct-read fallback.
   *
   * Its trust policy must name the connector role and condition on
   * NamespaceDetail$datasourceExternalId; its permission policy grants
   * GetSecretValue on that one secret, plus kms:Decrypt if the secret uses a
   * customer-managed key.
   *
   * The role MUST be named \{RESOURCE_PREFIX\}datasource-access-*, because this
   * deployment's assume grant is scoped to that prefix, so registration rejects
   * any other name explicitly rather than letting it fail as an opaque
   * AccessDenied at first scan. Its ACCOUNT is unconstrained.
   *
   * There is no externalId member: a caller-supplied ExternalId is the
   * vulnerability it was meant to close, so the value is derived from the
   * namespace.
   * @public
   */
  crossAccountRoleArn: string | undefined;

  /**
   * Include-filter applied to table names within databaseName. Omit to
   * discover every table.
   * @public
   */
  tableFilter?: string | undefined;

  /**
   * Exclude-filter applied to table names within databaseName, evaluated
   * after tableFilter.
   * @public
   */
  tableExcludeFilter?: string | undefined;
}

/**
 * Glue Data Catalog database connection configuration.
 * @public
 */
export interface GlueConfiguration {
  /**
   * Glue Data Catalog id: a 12-digit AWS account id (the account's root
   * catalog) or a nested catalog id of the form `account:catalogName`
   * (federated / S3 Tables / Redshift-backed / cross-account catalogs).
   * @public
   */
  catalogId: string | undefined;

  /**
   * AWS region identifier.
   * @public
   */
  region: string | undefined;

  /**
   * Database name.
   * @public
   */
  databaseName: string | undefined;

  /**
   * Passed to Glue `GetTables` as its native `Expression` (a regular
   * expression) — the one filter that is not a glob.
   * @public
   */
  tableFilter?: string | undefined;

  /**
   * Tables matching this glob filter are excluded.
   * @public
   */
  tableExcludeFilter?: string | undefined;

  /**
   * IAM role ARN for cross-account access.
   * @public
   */
  crossAccountRoleArn?: string | undefined;

  /**
   * IGNORED. The ExternalId presented on the cross-account assume is derived
   * from the namespace (`NamespaceDetail$datasourceExternalId`) and is no
   * longer accepted from the request: a caller-chosen value would hand back
   * control of what binds the assume to its namespace. Sources onboarded
   * before this change keep the value already stored on their record.
   *
   * @deprecated (since 2026-08-28) Ignored. Condition the role's trust policy on NamespaceDetail$datasourceExternalId instead.
   * @public
   */
  externalId?: string | undefined;

  /**
   * Nested Athena/Glue catalog name when the database lives in a federated or
   * other non-root catalog. When set, the source is queried as
   * `AwsDataCatalog.<athenaDataCatalogName>.<databaseName>.<table>`; when
   * omitted, as `AwsDataCatalog.<databaseName>.<table>`.
   * @public
   */
  athenaDataCatalogName?: string | undefined;

  /**
   * Execution engine for this Glue/Iceberg source's serve-time queries.
   * Defaults to ATHENA when omitted. Set REDSHIFT to route queries through
   * Amazon Redshift Serverless (`awsdatacatalog` auto-mount); requires
   * `redshiftWorkgroup` to be set.
   * @public
   */
  executionEngine?: GlueExecutionEngine | undefined;

  /**
   * Redshift Serverless workgroup used to execute queries when
   * `executionEngine` is REDSHIFT. Ignored (and unnecessary) for ATHENA.
   * @public
   */
  redshiftWorkgroup?: string | undefined;
}

/**
 * JDBC database connection configuration.
 * @public
 */
export interface JdbcConfiguration {
  /**
   * Database engine type for JDBC connections.
   * @public
   */
  engine: DatabaseEngine | undefined;

  /**
   * Database hostname or endpoint.
   * @public
   */
  host: string | undefined;

  /**
   * Database port number.
   * @public
   */
  port: number | undefined;

  /**
   * Database name.
   * @public
   */
  databaseName: string | undefined;

  /**
   * Only schemas matching this glob filter are discovered.
   * @public
   */
  schemaFilter?: string | undefined;

  /**
   * Schemas matching this glob filter are excluded, IN ADDITION TO the
   * engine's system schemas (e.g. `pg_catalog`, `information_schema`), which
   * are always excluded.
   * @public
   */
  schemaExcludeFilter?: string | undefined;

  /**
   * Schema/table filter: one or more shell globs, separated by `|` or `,`, each
   * matched against the WHOLE name. `*` matches any characters, `?` one
   * character, `[abc]` one of a set. Examples: `sales_*`, `public|analytics`,
   * `constructor*,results`. Not a regular expression — `^`, `$` and `.*` are
   * matched literally. The one exception is a Glue Data Catalog source's
   * `tableFilter`, which is passed to Glue as its native expression syntax.
   * @public
   */
  tableFilter?: string | undefined;

  /**
   * Schema/table filter: one or more shell globs, separated by `|` or `,`, each
   * matched against the WHOLE name. `*` matches any characters, `?` one
   * character, `[abc]` one of a set. Examples: `sales_*`, `public|analytics`,
   * `constructor*,results`. Not a regular expression — `^`, `$` and `.*` are
   * matched literally. The one exception is a Glue Data Catalog source's
   * `tableFilter`, which is passed to Glue as its native expression syntax.
   * @public
   */
  tableExcludeFilter?: string | undefined;

  /**
   * Secrets Manager ARN for database credentials.
   * @public
   */
  credentialSecretArn?: string | undefined;

  /**
   * IAM role ARN for cross-account access.
   * @public
   */
  crossAccountRoleArn?: string | undefined;

  /**
   * IGNORED. The ExternalId presented on the cross-account assume is derived
   * from the namespace (`NamespaceDetail$datasourceExternalId`) and is no
   * longer accepted from the request: a caller-chosen value would hand back
   * control of what binds the assume to its namespace. Sources onboarded
   * before this change keep the value already stored on their record.
   *
   * @deprecated (since 2026-08-28) Ignored. Condition the role's trust policy on NamespaceDetail$datasourceExternalId instead.
   * @public
   */
  externalId?: string | undefined;

  /**
   * Snowflake only: the virtual warehouse used to run INFORMATION_SCHEMA
   * queries during discovery (Snowflake requires an active warehouse).
   * @public
   */
  warehouse?: string | undefined;

  /**
   * Snowflake only: optional Snowflake RBAC role name to assume for the
   * session (a Snowflake construct — not an AWS IAM role; see crossAccountRoleArn).
   * @public
   */
  role?: string | undefined;
}

/**
 * RDF/SPARQL graph source configuration — the RDF_SPARQL sub-type. Instance
 * data (A-Box) lives natively as triples in a SPARQL store and is answered at
 * serve time by NL→SPARQL executed directly against `dataEndpoint` (no Glue
 * catalog, no VKG/SQL). There is no schema discovery: the ontology (T-Box) is
 * imported separately and points its classes at this source by name.
 *
 * Registration only verifies the endpoint is reachable (no scan). Persisted as
 * the source `configuration` blob; serve and the verify Lambda both read it.
 * Cross-field rules enforced server-side: `store = neptune` requires
 * `authMode = sigv4` and forbids `credentialSecretArn`.
 * @public
 */
export interface SparqlConfiguration {
  /**
   * SPARQL engine. Defaults to `neptune` when omitted.
   * @public
   */
  store?: SparqlStore | undefined;

  /**
   * SPARQL endpoint for the A-Box (instance data) that serve executes against.
   * @public
   */
  dataEndpoint: string | undefined;

  /**
   * AWS region for SigV4 signing. Defaults to the deployment region.
   * @public
   */
  region?: string | undefined;

  /**
   * Endpoint port. Defaults to 8182 (Neptune).
   * @public
   */
  port?: number | undefined;

  /**
   * Named graph holding the A-Box. When set, generated queries are confined
   * to it; when absent, the store's default graph is queried.
   * @public
   */
  dataNamedGraph?: string | undefined;

  /**
   * Authentication mode. Defaults to `sigv4`.
   * @public
   */
  authMode?: SparqlAuthMode | undefined;

  /**
   * Credential for non-SigV4 auth modes. Rejected for `neptune`.
   * @public
   */
  credentialSecretArn?: string | undefined;
}

/**
 * Database source creation fields.
 * Exactly one of glueConfiguration, jdbcConfiguration, customConnectorConfiguration,
 * databricksSqlWarehouseConfiguration or sparqlConfiguration must be provided — it
 * selects the sub-type.
 * @public
 */
export interface CreateDatabaseSourceInput {
  /**
   * Human-readable display name. Allows spaces and punctuation. 1–128 chars.
   * @public
   */
  name: string | undefined;

  /**
   * Glue Data Catalog config. Required for GLUE_DATABASE sub-type.
   * @public
   */
  glueConfiguration?: GlueConfiguration | undefined;

  /**
   * JDBC connection config. Required for JDBC_DATABASE sub-type.
   * @public
   */
  jdbcConfiguration?: JdbcConfiguration | undefined;

  /**
   * Custom Athena federation connector config. Required for the
   * CUSTOM_CONNECTOR sub-type.
   * @public
   */
  customConnectorConfiguration?: CustomConnectorConfiguration | undefined;

  /**
   * Databricks SQL Warehouse config. Required for the
   * DATABRICKS_SQL_WAREHOUSE sub-type.
   * @public
   */
  databricksSqlWarehouseConfiguration?: DatabricksSqlWarehouseConfiguration | undefined;

  /**
   * RDF/SPARQL graph store config. Required for the RDF_SPARQL sub-type.
   * Registration verifies reachability only; enrichment does not apply.
   * @public
   */
  sparqlConfiguration?: SparqlConfiguration | undefined;

  /**
   * Enable AI-powered business metadata enrichment (descriptions,
   * synonyms, glossary terms, tags). Defaults to true. When false the
   * scan pipeline skips the enrichment step and the source transitions
   * directly from SCANNING to PENDING_REVIEW with discovered technical
   * metadata only.
   * @public
   */
  metadataEnrichmentEnabled?: boolean | undefined;
}

/**
 * Configuration for document extraction behaviour.
 * @public
 */
export interface ExtractionConfig {
  /**
   * Extraction mode — mirrors ExtractionMode in constants.py.
   * @public
   */
  extractionMode?: ExtractionMode | undefined;

  /**
   * Whether to use Bedrock batch inference for extraction.
   * @public
   */
  useBatchInference?: boolean | undefined;

  /**
   * Whether to version extracted documents.
   * @public
   */
  enableVersioning?: boolean | undefined;

  /**
   * Whether to extract propositions from chunks.
   * @public
   */
  enablePropositionExtraction?: boolean | undefined;

  /**
   * Explicit entity-class vocabulary handed to the extraction LLM. When
   * non-empty, overrides both graphrag's hardcoded news/finance defaults
   * AND the corpus-inferred fallback — the exact labels supplied here are
   * the ones the extractor uses to type entities. Case-sensitive, spaced
   * (e.g. "Policy", "Claim", "Loss Ratio"). Leave empty to fall back to
   * inferEntityClassifications.
   * @public
   */
  preferredEntityClassifications?: string[] | undefined;

  /**
   * Whether to derive the entity-class vocabulary from this corpus at ingest
   * start rather than inheriting graphrag's hardcoded news/finance defaults
   * ("Company", "Sports Team", "Creative Work", …). Ignored when
   * preferredEntityClassifications is set. Defaults to true.
   * @public
   */
  inferEntityClassifications?: boolean | undefined;

  /**
   * Explicit TOPIC vocabulary handed to the extraction LLM. Topics are the
   * thematic groupings chunks are assigned to — they become ``__Topic__``
   * nodes and are later induced as ``skos:Concept`` — as distinct from
   * preferredEntityClassifications, which types the entities themselves
   * (``__Entity__.class``, induced as ``owl:Class``).
   *
   * The extractor prefers a listed topic when one matches the content in
   * meaning and specificity, and invents a name otherwise, so this is a
   * steer rather than a closed set. Case-sensitive, spaces allowed
   * (e.g. "Black Tie Gala", "Everyday Elegance").
   *
   * Leave empty (the default) to let the extractor name every topic from the
   * chunk text. There is deliberately no ``inferTopics`` flag: the toolkit
   * has no topic equivalent of the entity-classification inference pass, so
   * an empty list already *is* "let the model decide".
   * @public
   */
  preferredTopics?: string[] | undefined;

  /**
   * Whether to route every PDF through Amazon Textract's AnalyzeDocument
   * with TABLES feature (instead of unstructured.partition_pdf strategy=
   * "fast", which does not detect tables). Preserves row/column structure
   * through preprocessing so a statistical table survives as facts, not
   * prose. Costs materially more per page than DetectDocumentText; leave
   * off for prose-dominant corpora. Defaults to false.
   * @public
   */
  enableTableExtraction?: boolean | undefined;

  /**
   * Chunk size (in tokens) for the SentenceSplitter that splits staged
   * documents into extraction/embedding units. Larger values keep more
   * context (a full table row + header, a full policy clause) in one
   * chunk. **`0` means "use the graphrag-toolkit default (256)"** — the
   * sentinel that survives the state-machine → ECS env-var pipe without
   * a special-cased missing-field state. Set a positive value (e.g. 1024
   * for dense/tabular corpora) to override.
   * @public
   */
  chunkSize?: number | undefined;

  /**
   * Overlap (in tokens) between consecutive chunks. **`0` means "use the
   * graphrag-toolkit default (25)"**. Ignored unless chunkSize > 0.
   * @public
   */
  chunkOverlap?: number | undefined;

  /**
   * Whether to delete previous document versions on re-ingest.
   * @public
   */
  deletePrevVersions?: boolean | undefined;

  /**
   * Bedrock inference profile or foundation model ARN.
   * @public
   */
  bedrockModelArn?: string | undefined;
}

/**
 * Document source creation fields.
 * For S3 sources: provide sourceBucketArn (and optionally s3Prefixes, roleArn).
 * For upload sources: provide uploadId from GetSourceUploadUrls; the ingest
 * prefix is derived server-side as \{namespaceId\}/raw/\{uploadId\}/ and any
 * caller-supplied s3Prefixes is ignored.
 * @public
 */
export interface CreateDocumentSourceInput {
  /**
   * Human-readable display name. Allows spaces and punctuation. 1–128 chars.
   * @public
   */
  name: string | undefined;

  /**
   * S3 key prefixes to ingest. Used only for the S3 sub-type, where they
   * point into the caller-owned sourceBucketArn. Ignored for upload sources,
   * whose prefix is derived server-side from uploadId.
   * @public
   */
  s3Prefixes?: string[] | undefined;

  /**
   * Server-issued upload session identifier returned by GetSourceUploadUrls.
   * Required for the upload sub-type; the ingest prefix is reconstructed as
   * \{namespaceId\}/raw/\{uploadId\}/ so a caller cannot redirect ingestion at
   * another namespace's objects.
   * @public
   */
  uploadId?: string | undefined;

  /**
   * ARN of the S3 bucket. Required for S3 sub-type.
   * @public
   */
  sourceBucketArn?: string | undefined;

  /**
   * IAM role for cross-account S3 access.
   * @public
   */
  roleArn?: string | undefined;

  /**
   * Configuration for document extraction behaviour.
   * @public
   */
  extractionConfig?: ExtractionConfig | undefined;
}

/**
 * Top-level create request. Exactly one of databaseSource or documentSource
 * must be set, matching the sourceType discriminator.
 * @public
 */
export interface CreateSourceInput {
  /**
   * Top-level category of a unified source.
   * @public
   */
  sourceType: SourceType | undefined;

  /**
   * Required when sourceType = DATABASE.
   * @public
   */
  databaseSource?: CreateDatabaseSourceInput | undefined;

  /**
   * Required when sourceType = DOCUMENTS.
   * @public
   */
  documentSource?: CreateDocumentSourceInput | undefined;

  /**
   * Optional idempotency token. A retry with the same token and the same
   * parameters within 24 hours returns the original result instead of creating
   * a duplicate; reusing the token with different parameters is rejected with
   * ConflictError (409).
   * @public
   */
  clientToken?: string | undefined;
}

/**
 * @public
 */
export interface CreateSourceOperationInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Top-level create request. Exactly one of databaseSource or documentSource
   * must be set, matching the sourceType discriminator.
   * @public
   */
  body: CreateSourceInput | undefined;
}

/**
 * Create source response.
 * @public
 */
export interface CreateSourceOutput {
  /**
   * Unique identifier of the newly created source.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Unified lifecycle status for all source types.
   * @public
   */
  status: SourceStatus | undefined;

  /**
   * Identifier of the scan job started for the source, if any.
   * @public
   */
  scanJobId?: string | undefined;

  /**
   * Timestamp when the source was created.
   * @public
   */
  createdAt: Date | undefined;
}

/**
 * @public
 */
export interface CreateSourceOperationOutput {
  /**
   * Create source response.
   * @public
   */
  body: CreateSourceOutput | undefined;
}

/**
 * @public
 */
export interface DeleteSourceInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source to delete.
   * @public
   */
  sourceId: string | undefined;
}

/**
 * @public
 */
export interface DeleteSourceOutput {
  /**
   * Identifier of the deleted source.
   * @public
   */
  sourceId?: string | undefined;

  /**
   * Unified lifecycle status for all source types.
   * @public
   */
  status?: SourceStatus | undefined;
}

/**
 * @public
 */
export interface GetSourceOperationInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source to fetch.
   * @public
   */
  sourceId: string | undefined;
}

/**
 * Event-driven rescan configuration for a DATABASE source. When enabled (Glue
 * sources only), upstream Glue Data Catalog changes to the source's database
 * automatically trigger an EVENT-trigger rescan; the schema-diff keeps it
 * non-destructive and repeated events are coalesced.
 * @public
 */
export interface EventRescanConfig {
  /**
   * Whether event-driven rescans are currently active.
   * @public
   */
  enabled: boolean | undefined;
}

/**
 * A recurring rescan cadence for a DATABASE source, backed by an EventBridge
 * schedule. When enabled, the source is automatically re-scanned on the given
 * cadence (a SCHEDULED-trigger rescan); the schema-diff keeps it
 * non-destructive.
 * @public
 */
export interface RescanSchedule {
  /**
   * Whether the recurring rescan is currently active.
   * @public
   */
  enabled: boolean | undefined;

  /**
   * EventBridge schedule expression, e.g. "rate(1 day)" or
   * "cron(0 3 * * ? *)". Required when enabled.
   * @public
   */
  scheduleExpression?: string | undefined;

  /**
   * IANA timezone the cron expression is evaluated in (e.g.
   * "America/New_York"). Defaults to UTC when omitted.
   * @public
   */
  timezone?: string | undefined;
}

/**
 * Type-specific detail for DATABASE sources.
 * @public
 */
export interface DatabaseSourceDetail {
  /**
   * Glue Data Catalog database connection configuration.
   * @public
   */
  glueConfiguration?: GlueConfiguration | undefined;

  /**
   * JDBC database connection configuration.
   * @public
   */
  jdbcConfiguration?: JdbcConfiguration | undefined;

  /**
   * Populated for the CUSTOM_CONNECTOR sub-type; absent otherwise.
   * @public
   */
  customConnectorConfiguration?: CustomConnectorConfiguration | undefined;

  /**
   * Populated for the DATABRICKS_SQL_WAREHOUSE sub-type; absent otherwise.
   * @public
   */
  databricksSqlWarehouseConfiguration?: DatabricksSqlWarehouseConfiguration | undefined;

  /**
   * Populated for the RDF_SPARQL sub-type; absent otherwise.
   * @public
   */
  sparqlConfiguration?: SparqlConfiguration | undefined;

  /**
   * Whether AI-powered business metadata enrichment runs for this source.
   * Set at creation time and persisted with the source record. When false
   * the scan pipeline skips the enrichment step and the source transitions
   * from SCANNING straight to PENDING_REVIEW.
   * @public
   */
  metadataEnrichmentEnabled?: boolean | undefined;

  /**
   * Preferred execution engine for single-source queries against this source.
   * Read-only and system-set at creation: `JDBC` for direct (low-latency)
   * execution, set only for engines with an implemented direct dialect
   * (PostgreSQL/Redshift today); otherwise `ATHENA` (native Glue, and JDBC
   * engines without a direct path yet). The consumption layer overrides this
   * to Athena for any query spanning multiple sources.
   * @public
   */
  queryEngine?: QueryEngine | undefined;

  /**
   * Number of tables discovered in the most recent scan.
   * @public
   */
  tablesDiscovered?: number | undefined;

  /**
   * Number of tables with reviewStatus=APPROVED.
   * @public
   */
  tablesApproved?: number | undefined;

  /**
   * Identifier of the most recent scan job.
   * @public
   */
  lastScanJobId?: string | undefined;

  /**
   * Timestamp of the most recent scan.
   * @public
   */
  lastScanAt?: Date | undefined;

  /**
   * Name of the Glue Connection that backs Athena federated queries
   * for this data source. Read-only and system-managed: populated
   * only for JDBC sub-types (PostgreSQL, MySQL, Redshift, Oracle, SQL
   * Server, Snowflake) on first scan and removed when the source is
   * deleted. Null for S3/Iceberg-backed Glue databases — those are
   * queried via Athena's native AwsDataCatalog.
   *
   * To query the source via Athena, pair this with the namespace's
   * `athenaWorkgroupName` and the `athenaDataCatalogName` below. See
   * the Athena Queryability section of `packages/sources/README.md`
   * for examples.
   * @public
   */
  glueConnectionName?: string | undefined;

  /**
   * Name of the Athena data catalog registered for this source. Read-only
   * and system-managed, derived from `\{resource-prefix\}ds_\{sourceId\}`. Null
   * for S3/Iceberg-backed Glue databases, which are queried through Athena's
   * native `AwsDataCatalog`.
   *
   * The addressing differs by sub-type, because the two catalogs are not the
   * same kind of object:
   *
   * - JDBC sub-types: a managed Glue federated catalog, NESTED under
   *   `AwsDataCatalog`, and equal to `glueConnectionName`. Query it as
   *   `AwsDataCatalog.<athenaDataCatalogName>.<schema>.<table>`.
   * - CUSTOM_CONNECTOR: a LAMBDA-type Athena catalog bound to the customer's
   *   connector Lambda. It is a TOP-LEVEL catalog, not nested, so query it as
   *   `<athenaDataCatalogName>.<databaseName>.<table>`.
   * - DATABRICKS_SQL_WAREHOUSE: also a TOP-LEVEL LAMBDA-type catalog, addressed
   *   the same way, but bound to the ONE connector Lambda this deployment
   *   operates — every such catalog in the environment shares that handler ARN,
   *   and the catalog name is what selects the source's workspace and
   *   credential. `databaseName` is the Unity Catalog schema.
   *
   * Run the query inside the namespace's Athena workgroup (see
   * NamespaceDetail.athenaWorkgroupName).
   * @public
   */
  athenaDataCatalogName?: string | undefined;

  /**
   * Recurring rescan schedule for this source, if configured. Absent when no
   * schedule has been set.
   * @public
   */
  rescanSchedule?: RescanSchedule | undefined;

  /**
   * Event-driven rescan configuration for this source, if configured. Absent
   * when event-driven rescans have never been set.
   * @public
   */
  eventRescan?: EventRescanConfig | undefined;
}

/**
 * A single file-level preprocessing issue recorded during ingestion.
 * @public
 */
export interface PreprocessingIssue {
  /**
   * Name of the file the issue applies to.
   * @public
   */
  filename: string | undefined;

  /**
   * Type of per-file preprocessing issue.
   * @public
   */
  type: PreprocessingIssueType | undefined;

  /**
   * Human-readable explanation of the issue.
   * @public
   */
  reason: string | undefined;
}

/**
 * Type-specific detail for DOCUMENTS sources.
 * @public
 */
export interface DocumentSourceDetail {
  /**
   * S3 key prefixes ingested for this source.
   * @public
   */
  s3Prefixes?: string[] | undefined;

  /**
   * S3 bucket ARN. Format: arn:aws:s3:::\{bucket-name\}
   * @public
   */
  sourceBucketArn?: string | undefined;

  /**
   * IAM role ARN for cross-account access.
   * @public
   */
  roleArn?: string | undefined;

  /**
   * Configuration for document extraction behaviour.
   * @public
   */
  extractionConfig?: ExtractionConfig | undefined;

  /**
   * Total number of files considered for ingestion.
   * @public
   */
  filesTotal?: number | undefined;

  /**
   * Number of files skipped during preprocessing.
   * @public
   */
  filesSkipped?: number | undefined;

  /**
   * Number of files that errored during preprocessing.
   * @public
   */
  filesErrored?: number | undefined;

  /**
   * Error message if processing failed.
   * @public
   */
  errorMessage?: string | undefined;

  /**
   * Per-file preprocessing issues recorded during ingestion.
   * @public
   */
  preprocessingIssues?: PreprocessingIssue[] | undefined;

  /**
   * Distinct source documents opened for chunk extraction by the KG build,
   * read from the per-source metrics record (PK=METRICS#\{ns\}, SK=KGBUILD#\{ds\}).
   * Null until the KG build has run and written metrics.
   * @public
   */
  documentsProcessed?: number | undefined;

  /**
   * Count of LLM extraction prompts run on chunks (topic + proposition each
   * fire once per chunk, so this is ~= extractors x chunks; NOT distinct).
   * Null until the KG build has run.
   * @public
   */
  chunksLLM?: number | undefined;

  /**
   * Distinct chunks whose embeddings were written to the OSS chunk vector
   * index. Bounded by the true chunk count. Null until the KG build has run.
   * @public
   */
  chunksEmbed?: number | undefined;

  /**
   * Distinct chunk nodes inserted into the Neptune graph. Bounded by the true
   * chunk count. Null until the KG build has run.
   * @public
   */
  chunksGraph?: number | undefined;
}

/**
 * Full source record returned by GetSource.
 * Uses sourceType as a discriminator — branch on it to access type-specific detail:
 *   DATABASE  → databaseDetails is populated; documentDetails is absent.
 *   DOCUMENTS → documentDetails is populated; databaseDetails is absent.
 * @public
 */
export interface GetSourceOutput {
  /**
   * Unique source identifier.
   * @public
   */
  sourceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Display name of the source.
   * @public
   */
  name: string | undefined;

  /**
   * Top-level category of a unified source.
   * @public
   */
  sourceType: SourceType | undefined;

  /**
   * Specific connector sub-type within a source category.
   * @public
   */
  sourceSubType: SourceSubType | undefined;

  /**
   * Unified lifecycle status for all source types.
   * @public
   */
  status: SourceStatus | undefined;

  /**
   * Timestamp when the source was created.
   * @public
   */
  createdAt: Date | undefined;

  /**
   * Timestamp when the source was last updated.
   * @public
   */
  updatedAt?: Date | undefined;

  /**
   * Populated when sourceType = DATABASE. Absent for DOCUMENTS sources.
   * @public
   */
  databaseDetails?: DatabaseSourceDetail | undefined;

  /**
   * Populated when sourceType = DOCUMENTS. Absent for DATABASE sources.
   * @public
   */
  documentDetails?: DocumentSourceDetail | undefined;
}

/**
 * @public
 */
export interface GetSourceOperationOutput {
  /**
   * Full source record returned by GetSource.
   * Uses sourceType as a discriminator — branch on it to access type-specific detail:
   *   DATABASE  → databaseDetails is populated; documentDetails is absent.
   *   DOCUMENTS → documentDetails is populated; databaseDetails is absent.
   * @public
   */
  body: GetSourceOutput | undefined;
}

/**
 * @public
 */
export interface GetSourceScanJobInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source the scan job belongs to.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Identifier of the scan job to fetch.
   * @public
   */
  jobId: string | undefined;
}

/**
 * @public
 */
export interface GetSourceScanJobOutput {
  /**
   * Unique scan job identifier.
   * @public
   */
  jobId: string | undefined;

  /**
   * Identifier of the source scanned.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Status of a database scan job execution.
   * @public
   */
  status: SourceScanJobStatus | undefined;

  /**
   * Number of tables discovered by the scan.
   * @public
   */
  tablesDiscovered?: number | undefined;

  /**
   * Tables processed so far, counting both unchanged-on-inspection and
   * enriched. Published as the job advances, so it lags by a few seconds.
   * @public
   */
  tablesProcessed?: number | undefined;

  /**
   * Denominator for `tablesProcessed`. Falls back to the previous scan's
   * table count until this scan's discovery has finished enumerating.
   * @public
   */
  tablesTotal?: number | undefined;

  /**
   * Number of tables added since the previous scan.
   * @public
   */
  tablesAdded?: number | undefined;

  /**
   * Number of tables removed since the previous scan.
   * @public
   */
  tablesRemoved?: number | undefined;

  /**
   * Number of tables modified since the previous scan.
   * @public
   */
  tablesModified?: number | undefined;

  /**
   * Timestamp when the scan job started.
   * @public
   */
  startedAt: Date | undefined;

  /**
   * Timestamp when the scan job completed.
   * @public
   */
  completedAt?: Date | undefined;

  /**
   * Error message if the scan job failed.
   * @public
   */
  errorMessage?: string | undefined;

  /**
   * Number of tables the scan listed but could not read.
   *
   * Absent when none failed, rather than zero, so it can be used directly to
   * filter for degraded scans. A non-zero value means the scan SUCCEEDED but
   * is incomplete: those tables carry no columns, no comments, and no declared
   * keys, and AI enrichment will have generated descriptions over the gap — so
   * a reviewer must not read the result as complete. Only connectors that read
   * each table separately can report this; one that returns a table's schema in
   * the same call that lists it cannot partially fail.
   * @public
   */
  tablesFailed?: number | undefined;

  /**
   * The unreadable tables as `database.table`, capped in length.
   *
   * A signal for diagnosis, not an inventory — `tablesFailed` is the exact
   * figure and this list may be shorter than it.
   * @public
   */
  failedTables?: string[] | undefined;

  /**
   * Warnings about the source's filters, absent when none. Set when a filter
   * that looks like a regular expression matched nothing — filters are globs,
   * so the scan succeeded without the intended filtering.
   * @public
   */
  filterWarnings?: string[] | undefined;
}

/**
 * @public
 */
export interface GetSourceTableInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source containing the table.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Identifier of the table to fetch.
   * @public
   */
  tableId: string | undefined;
}

/**
 * Business-facing metadata for a table or column returned in responses:
 * description, synonyms, glossary terms, tags, enrichment source, review
 * status, and AI-inference confidence.
 * @public
 */
export interface BusinessMetadataOutput {
  /**
   * Human-readable description of the table or column.
   * @public
   */
  description?: string | undefined;

  /**
   * Alternative names or aliases.
   * @public
   */
  synonyms?: string[] | undefined;

  /**
   * Associated business glossary terms.
   * @public
   */
  glossaryTerms?: string[] | undefined;

  /**
   * Free-form classification tags.
   * @public
   */
  tags?: string[] | undefined;

  /**
   * Origin of this metadata (e.g. AI-inferred, steward-specified, catalog-existing).
   * @public
   */
  enrichmentSource?: string | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus?: ReviewStatus | undefined;

  /**
   * AI-inference confidence (0.0-1.0) for AI-generated metadata; absent or 0
   * for steward-specified or catalog-existing metadata.
   * @public
   */
  confidence?: number | undefined;
}

/**
 * Metadata describing a single column of a source table: its name, data type,
 * nullability, partition-key flag, description, business metadata, and any
 * sampled distinct values.
 * @public
 */
export interface ColumnMetadata {
  /**
   * Column name.
   * @public
   */
  name: string | undefined;

  /**
   * Column data type (source-native type string).
   * @public
   */
  dataType: string | undefined;

  /**
   * Whether the column permits null values.
   * @public
   */
  nullable?: boolean | undefined;

  /**
   * Whether the column is a partition key.
   * @public
   */
  isPartitionKey?: boolean | undefined;

  /**
   * Human-readable description of the column.
   * @public
   */
  description?: string | undefined;

  /**
   * Business-facing metadata for a table or column returned in responses:
   * description, synonyms, glossary terms, tags, enrichment source, review
   * status, and AI-inference confidence.
   * @public
   */
  businessMetadata?: BusinessMetadataOutput | undefined;

  /**
   * Sampled distinct values for low-cardinality categorical columns
   * (capped, best-effort). Empty for high-cardinality, non-string, or
   * unsampled columns. Used by the serve NL→SQL layer to hint the LLM
   * with correct enum literals for WHERE clauses, and shown in the UI.
   * @public
   */
  distinctValues?: string[] | undefined;

  /**
   * True when a re-scan found this column removed from the source; it is
   * deleted on approve unless the steward keeps it. Absent/false otherwise.
   * @public
   */
  pendingDeletion?: boolean | undefined;
}

/**
 * A foreign-key relationship reported for a table: the local column and the
 * target table/column it references, with the source and inference confidence.
 * @public
 */
export interface ForeignKeyOutput {
  /**
   * Local column holding the foreign-key reference.
   * @public
   */
  column?: string | undefined;

  /**
   * Referenced table.
   * @public
   */
  targetTable?: string | undefined;

  /**
   * Referenced column in the target table.
   * @public
   */
  targetColumn?: string | undefined;

  /**
   * Origin of the key (e.g. discovered vs. steward-specified).
   * @public
   */
  source?: string | undefined;

  /**
   * Inference confidence (0.0-1.0) for AI-inferred keys.
   * @public
   */
  confidence?: number | undefined;

  /**
   * Steward review state for an inferred relationship (#1088): PENDING_REVIEW,
   * APPROVED, or REJECTED. Empty for authoritative keys (deterministic/steward)
   * and keys predating review. Only APPROVED/authoritative keys reach the ontology.
   * @public
   */
  reviewStatus?: string | undefined;

  /**
   * Datasource id of the target table when the relationship crosses a source
   * boundary (#1088). Empty for a within-source key.
   * @public
   */
  targetDatasourceId?: string | undefined;

  /**
   * Human-readable note of what an inferred relationship was inferred from,
   * shown to the steward at review time (#1088).
   * @public
   */
  provenance?: string | undefined;
}

/**
 * The primary-key definition reported for a table: its key columns plus the
 * source (e.g. discovered vs. steward-specified) and inference confidence.
 * @public
 */
export interface PrimaryKeyOutput {
  /**
   * Ordered column names composing the primary key.
   * @public
   */
  columns?: string[] | undefined;

  /**
   * Origin of the key (e.g. discovered vs. steward-specified).
   * @public
   */
  source?: string | undefined;

  /**
   * Inference confidence (0.0-1.0) for AI-inferred keys.
   * @public
   */
  confidence?: number | undefined;
}

/**
 * One source-owned field that a re-scan changed vs. the last approved scan,
 * carrying both the old and new values for the steward's before/after view.
 * @public
 */
export interface RescanFieldChange {
  /**
   * Field name (e.g. "description", "data_type", "primary_key").
   * @public
   */
  field: string | undefined;

  /**
   * Which category of change this is.
   * @public
   */
  kind: RescanChangeKind | undefined;

  /**
   * Value at the last approved scan.
   * @public
   */
  old?: string | undefined;

  /**
   * Value the latest re-scan discovered.
   * @public
   */
  new?: string | undefined;
}

/**
 * A column a re-scan added, removed, or modified, with its changed fields.
 * @public
 */
export interface RescanColumnChange {
  /**
   * Column name.
   * @public
   */
  name: string | undefined;

  /**
   * Whether the column was added, removed, or modified.
   * @public
   */
  status: RescanColumnChangeStatus | undefined;

  /**
   * Changed source-owned fields (populated for MODIFIED).
   * @public
   */
  fields?: RescanFieldChange[] | undefined;
}

/**
 * The old-vs-new breakdown of what a re-scan changed for a table, so a Data
 * Steward can compare against the last approved scan before approving. Present
 * only while the source is in RESCAN_REVIEW and this table actually changed.
 * @public
 */
export interface RescanTableDiff {
  /**
   * Changed table-level source-owned fields (description, keys, format, ...).
   * @public
   */
  tableFields?: RescanFieldChange[] | undefined;

  /**
   * Per-column added / removed / modified breakdown.
   * @public
   */
  columns?: RescanColumnChange[] | undefined;
}

/**
 * Technical metadata for a table: column count, partition keys, storage
 * format, and physical location.
 * @public
 */
export interface TechnicalMetadataOutput {
  /**
   * Number of columns in the table.
   * @public
   */
  columnCount?: number | undefined;

  /**
   * Names of the table's partition-key columns.
   * @public
   */
  partitionKeys?: string[] | undefined;

  /**
   * Storage/serialization format.
   * @public
   */
  format?: string | undefined;

  /**
   * Physical storage location (e.g. S3 URI).
   * @public
   */
  location?: string | undefined;
}

/**
 * @public
 */
export interface GetSourceTableOutput {
  /**
   * Unique table identifier (database.table format).
   * @public
   */
  tableId: string | undefined;

  /**
   * Table name.
   * @public
   */
  name: string | undefined;

  /**
   * Database the table belongs to.
   * @public
   */
  database: string | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus: ReviewStatus | undefined;

  /**
   * Metadata for every column in the table.
   * @public
   */
  columns: ColumnMetadata[] | undefined;

  /**
   * Business-facing metadata for a table or column returned in responses:
   * description, synonyms, glossary terms, tags, enrichment source, review
   * status, and AI-inference confidence.
   * @public
   */
  businessMetadata?: BusinessMetadataOutput | undefined;

  /**
   * The primary-key definition reported for a table: its key columns plus the
   * source (e.g. discovered vs. steward-specified) and inference confidence.
   * @public
   */
  primaryKey?: PrimaryKeyOutput | undefined;

  /**
   * Foreign-key relationships reported for the table.
   * @public
   */
  foreignKeys?: ForeignKeyOutput[] | undefined;

  /**
   * Technical metadata for a table: column count, partition keys, storage
   * format, and physical location.
   * @public
   */
  technicalMetadata?: TechnicalMetadataOutput | undefined;

  /**
   * True when a re-scan found this table removed from the source; it is
   * deleted on approve unless the steward keeps it. Absent/false otherwise.
   * @public
   */
  pendingDeletion?: boolean | undefined;

  /**
   * Old-vs-new breakdown of what the current re-scan changed for this table,
   * for the steward's before/after review. Present only while the source is
   * in RESCAN_REVIEW and this table changed; absent otherwise.
   * @public
   */
  rescanDiff?: RescanTableDiff | undefined;

  /**
   * True when the current re-scan discovered this table for the first time
   * (it did not exist in the last approved scan). It therefore has no
   * old-vs-new diff — the whole table is new. Absent/false otherwise.
   * @public
   */
  added?: boolean | undefined;
}

/**
 * A single file to upload, identified by filename and MIME content type.
 * @public
 */
export interface UploadFileRequest {
  /**
   * Name of the file to upload.
   * @public
   */
  filename: string | undefined;

  /**
   * MIME content type of the file.
   * @public
   */
  contentType: string | undefined;
}

/**
 * @public
 */
export interface GetSourceUploadUrlsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Files to generate pre-signed upload URLs for.
   * @public
   */
  files: UploadFileRequest[] | undefined;
}

/**
 * A pre-signed S3 PUT URL for a single file.
 * @public
 */
export interface UploadUrl {
  /**
   * Name of the file this URL is for.
   * @public
   */
  filename: string | undefined;

  /**
   * Pre-signed S3 PUT URL for uploading the file.
   * @public
   */
  uploadUrl: string | undefined;
}

/**
 * @public
 */
export interface GetSourceUploadUrlsOutput {
  /**
   * UUID v4 identifier.
   * @public
   */
  uploadId: string | undefined;

  /**
   * Relative S3 key prefix — no leading slash, no ".." traversal, no s3:// URI.
   * Examples: "documents/", "data/reports/2024/"
   * @public
   */
  s3Prefix: string | undefined;

  /**
   * Pre-signed S3 PUT URLs, one per requested file.
   * @public
   */
  uploadUrls: UploadUrl[] | undefined;

  /**
   * Seconds until the generated URLs expire.
   * @public
   */
  expiresIn: number | undefined;
}

/**
 * @public
 */
export interface KeepRescanRemovalInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source containing the flagged table.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Table identifier (database.table format).
   * @public
   */
  tableId: string | undefined;

  /**
   * If set, keep only this removed column of the table. Omit to keep the
   * whole removed table.
   * @public
   */
  columnName?: string | undefined;
}

/**
 * @public
 */
export interface KeepRescanRemovalOutput {
  /**
   * Identifier of the table the kept item belongs to.
   * @public
   */
  tableId: string | undefined;

  /**
   * The kept column, echoed back only when keeping a single column.
   * @public
   */
  columnName?: string | undefined;

  /**
   * The item's removal state after the keep. Always false — the item is
   * no longer pending deletion.
   * @public
   */
  pendingDeletion: boolean | undefined;
}

/**
 * @public
 */
export interface ListSourcesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Filter by source type (DATABASE or DOCUMENTS).
   * @public
   */
  sourceType?: SourceType | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of items to return per page.
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * Summary representation of a unified source (used in list responses).
 * Contains only the fields common to all source types.
 * @public
 */
export interface SourceSummary {
  /**
   * Unique source identifier.
   * @public
   */
  sourceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Display name of the source.
   * @public
   */
  name: string | undefined;

  /**
   * Top-level category of a unified source.
   * @public
   */
  sourceType: SourceType | undefined;

  /**
   * Specific connector sub-type within a source category.
   * @public
   */
  sourceSubType: SourceSubType | undefined;

  /**
   * Unified lifecycle status for all source types.
   * @public
   */
  status: SourceStatus | undefined;

  /**
   * Timestamp when the source was created.
   * @public
   */
  createdAt: Date | undefined;

  /**
   * Timestamp when the source was last updated.
   * @public
   */
  updatedAt?: Date | undefined;

  /**
   * Number of tables discovered in the most recent scan (DATABASE sources only).
   * @public
   */
  tablesDiscovered?: number | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListSourcesOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Page of source summaries.
   * @public
   */
  items: SourceSummary[] | undefined;
}

/**
 * @public
 */
export interface ListSourceScanJobsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source whose history to list.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of entries to return per page. Defaults to 1000, so a
   * caller that does not follow `nextToken` still sees the whole history
   * of all but the busiest sources.
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * One row in a source's scan history.
 * @public
 */
export interface ScanJobEntry {
  /**
   * When the entry occurred (scan start, or the moment the review resolved).
   * @public
   */
  at: Date | undefined;

  /**
   * Whether this row is a scan or a review event. Absent on legacy scan-job
   * rows written before review events existed — treat a missing value as SCAN.
   * @public
   */
  eventType?: ScanJobEventType | undefined;

  /**
   * Status of the row. For a SCAN this is the scan-job status
   * (IN_PROGRESS/DISCOVERING/ENRICHING/COMPLETED/FAILED/CANCELLED); for a
   * REVIEW it is the terminal source status the decision produced
   * (e.g. APPROVED, REJECTED, APPROVAL_FAILED). Free-form because the two
   * event kinds draw from different status vocabularies.
   * @public
   */
  status?: string | undefined;

  /**
   * For a SCAN row: whether it was a full or incremental (re-scan) run.
   * @public
   */
  scanType?: string | undefined;

  /**
   * What triggered a SCAN row: the first scan on connect, a user-initiated
   * re-scan, or an automated one from a schedule or a matched event. Absent
   * on rows written before triggers were recorded.
   * @public
   */
  triggerType?: ScanTrigger | undefined;

  /**
   * Number of tables discovered by the scan (SCAN rows).
   * @public
   */
  tablesDiscovered?: number | undefined;

  /**
   * Number of tables approved as of this review (REVIEW rows).
   * @public
   */
  tablesApproved?: number | undefined;

  /**
   * Timestamp when the scan job completed (SCAN rows).
   * @public
   */
  completedAt?: Date | undefined;

  /**
   * Error message if the scan job failed (SCAN rows).
   * @public
   */
  errorMessage?: string | undefined;

  /**
   * The steward's decision for a REVIEW row.
   * @public
   */
  decision?: ReviewDecision | undefined;

  /**
   * True when this event resolved a re-scan review (rather than an initial
   * approve/reject). REVIEW rows only.
   * @public
   */
  isRescan?: boolean | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListSourceScanJobsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * History entries, newest first.
   * @public
   */
  items: ScanJobEntry[] | undefined;
}

/**
 * Standard pagination input
 * @public
 */
export interface ListSourceTablesInput {
  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of items to return per page (default and maximum 50,
   * the catalog search page limit). For compatibility with clients
   * written against the earlier 1000 bound, the server still reduces a
   * value from 51 to 1000 to 50 rather than rejecting it.
   * @public
   */
  maxResults?: number | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source whose tables to list.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus?: ReviewStatus | undefined;
}

/**
 * A summary record for a source table in list/get responses: identifiers,
 * database, column and approved-column counts, review status, and enrichment
 * source.
 * @public
 */
export interface TableSummary {
  /**
   * Unique table identifier (database.table format).
   * @public
   */
  tableId: string | undefined;

  /**
   * Table name.
   * @public
   */
  name: string | undefined;

  /**
   * Database the table belongs to.
   * @public
   */
  database: string | undefined;

  /**
   * Number of columns in the table.
   * @public
   */
  columnCount?: number | undefined;

  /**
   * Number of columns with reviewStatus=APPROVED. Allows the UI to show
   * approval progress (columnsApproved / columnCount) without fetching
   * per-column detail.
   * @public
   */
  columnsApproved?: number | undefined;

  /**
   * Number of columns the re-scan found removed from the source (retained,
   * pending deletion on approval). Lets the list surface column-level removals
   * in the Review status column.
   * @public
   */
  columnsPendingDeletion?: number | undefined;

  /**
   * Number of inferred foreign keys on this table with
   * ``reviewStatus=PENDING_REVIEW`` — relationships that a cross-source
   * inference pass has proposed and a steward has not yet decided on.
   * Non-zero on tables whose parent source is already ``APPROVED``
   * signals that the source's Approve button has already been clicked
   * but a later cross-source pass has since found new relationships to
   * review; the steward can drill in per-table and use per-relationship
   * review (``PATCH /keys``) or per-table Approve to settle them.
   * Absent when zero to keep response bodies small.
   * @public
   */
  pendingRelationships?: number | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus: ReviewStatus | undefined;

  /**
   * Origin of the table's business metadata.
   * @public
   */
  enrichmentSource?: string | undefined;

  /**
   * True when a re-scan found this table removed from the source; it is
   * deleted on approve unless the steward keeps it. Absent/false otherwise.
   * @public
   */
  pendingDeletion?: boolean | undefined;

  /**
   * True when this table was created by the re-scan under review (net-new
   * since the last approved scan). Derived from the re-scan backup; not
   * persisted; absent outside RESCAN_REVIEW.
   * @public
   */
  added?: boolean | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListSourceTablesOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Page of table summaries.
   * @public
   */
  items: TableSummary[] | undefined;

  /**
   * Number of assets skipped due to retrieval or parsing failures.
   * Present only when one or more assets could not be loaded, indicating
   * a degraded (partial) response.
   * @public
   */
  skippedAssets?: number | undefined;
}

/**
 * @public
 */
export interface PutSourceEventRescanInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source to configure.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Whether event-driven rescans should be active.
   * @public
   */
  enabled: boolean | undefined;
}

/**
 * @public
 */
export interface PutSourceEventRescanOutput {
  /**
   * Identifier of the source.
   * @public
   */
  sourceId: string | undefined;

  /**
   * The resulting event-driven rescan configuration.
   * @public
   */
  eventRescan: EventRescanConfig | undefined;
}

/**
 * @public
 */
export interface PutSourceRescanScheduleInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source to schedule rescans for.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Whether the recurring rescan should be active.
   * @public
   */
  enabled: boolean | undefined;

  /**
   * EventBridge schedule expression (e.g. "rate(1 day)" or
   * "cron(0 3 * * ? *)"). Required when enabled=true.
   *
   * The cadence is floored, because every tick is a full discovery plus
   * enrichment pass. A `rate()` below the floor is rejected with 400, a
   * `cron()` must name a single minute so it cannot fire sub-hourly, and
   * one-time `at()` expressions are not accepted.
   * @public
   */
  scheduleExpression?: string | undefined;

  /**
   * IANA timezone for cron evaluation. Defaults to UTC.
   * @public
   */
  timezone?: string | undefined;
}

/**
 * @public
 */
export interface PutSourceRescanScheduleOutput {
  /**
   * Identifier of the source.
   * @public
   */
  sourceId: string | undefined;

  /**
   * The resulting schedule configuration.
   * @public
   */
  rescanSchedule: RescanSchedule | undefined;
}

/**
 * @public
 */
export interface RejectSourceInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source to reject.
   * @public
   */
  sourceId: string | undefined;
}

/**
 * @public
 */
export interface RejectSourceOutput {
  /**
   * Identifier of the source being rejected.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Unified lifecycle status for all source types.
   * @public
   */
  status: SourceStatus | undefined;
}

/**
 * @public
 */
export interface RescanSourceInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source to rescan.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Acknowledge that starting this re-scan discards an open re-scan
   * review. Required only when the source is in RESCAN_REVIEW: a fresh
   * re-scan re-diffs against the last APPROVED state, so any review
   * decisions or edits made inside the open review window are lost.
   * Omitting it in that state returns 409 rather than silently
   * discarding the review. Ignored from every other status, where a
   * re-scan discards nothing.
   * @public
   */
  confirmDiscardOpenReview?: boolean | undefined;

  /**
   * Optional idempotency token. A retry with the same token and the same
   * parameters within 24 hours returns the original result instead of
   * starting another scan; reusing the token with different parameters
   * is rejected with ConflictError (409).
   * @public
   */
  clientToken?: string | undefined;
}

/**
 * @public
 */
export interface RescanSourceOutput {
  /**
   * Identifier of the rescanned source.
   * @public
   */
  sourceId?: string | undefined;

  /**
   * Unified lifecycle status for all source types.
   * @public
   */
  status?: SourceStatus | undefined;
}

/**
 * @public
 */
export interface ReviewSourceColumnInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source containing the column.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Table identifier (database.table format).
   * @public
   */
  tableId: string | undefined;

  /**
   * Column name identifier.
   * @public
   */
  columnName: string | undefined;

  /**
   * Decision a steward can make on enriched metadata.
   * @public
   */
  decision: ReviewDecision | undefined;
}

/**
 * @public
 */
export interface ReviewSourceColumnOutput {
  /**
   * Identifier of the table containing the column.
   * @public
   */
  tableId: string | undefined;

  /**
   * Name of the reviewed column.
   * @public
   */
  columnName: string | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus: ReviewStatus | undefined;
}

/**
 * @public
 */
export interface ReviewSourceTableInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source containing the table.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Table identifier (database.table format).
   * @public
   */
  tableId: string | undefined;

  /**
   * Decision a steward can make on enriched metadata.
   * @public
   */
  decision: ReviewDecision | undefined;
}

/**
 * @public
 */
export interface ReviewSourceTableOutput {
  /**
   * Identifier of the reviewed table.
   * @public
   */
  tableId: string | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus: ReviewStatus | undefined;
}

/**
 * Steward-supplied overrides applied to discovered metadata: description,
 * synonyms, glossary terms, and tags.
 * @public
 */
export interface MetadataOverrides {
  /**
   * Override description for the table or column.
   * @public
   */
  description?: string | undefined;

  /**
   * Override synonyms or aliases.
   * @public
   */
  synonyms?: string[] | undefined;

  /**
   * Override business glossary terms.
   * @public
   */
  glossaryTerms?: string[] | undefined;

  /**
   * Override classification tags.
   * @public
   */
  tags?: string[] | undefined;
}

/**
 * @public
 */
export interface UpdateSourceColumnMetadataInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source containing the column.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Table identifier (database.table format).
   * @public
   */
  tableId: string | undefined;

  /**
   * Column name identifier.
   * @public
   */
  columnName: string | undefined;

  /**
   * Steward-supplied overrides applied to discovered metadata: description,
   * synonyms, glossary terms, and tags.
   * @public
   */
  overrides: MetadataOverrides | undefined;
}

/**
 * @public
 */
export interface UpdateSourceColumnMetadataOutput {
  /**
   * Identifier of the table containing the column.
   * @public
   */
  tableId: string | undefined;

  /**
   * Name of the updated column.
   * @public
   */
  columnName: string | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus: ReviewStatus | undefined;
}

/**
 * @public
 */
export interface UpdateSourceMetadataInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source to update.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Human-readable display name. Allows spaces and punctuation. 1–128 chars.
   * @public
   */
  name?: string | undefined;

  /**
   * Glue Data Catalog database connection configuration.
   * @public
   */
  glueConfiguration?: GlueConfiguration | undefined;

  /**
   * JDBC database connection configuration.
   * @public
   */
  jdbcConfiguration?: JdbcConfiguration | undefined;

  /**
   * Custom Athena Query Federation connector configuration — the
   * CUSTOM_CONNECTOR sub-type. The connector is a Lambda the customer authors
   * and deploys in their own account, which this service registers as a
   * Lambda-backed Athena data catalog in its own account; both discovery and
   * serve-time queries run through Athena against that catalog.
   *
   * Unlike GlueConfiguration there is no Glue database behind the source, so
   * there is no catalogId and no cross-account IAM role to assume: the customer
   * grants access on the connector Lambda's own resource policy instead. There
   * is also no region member — the connector must live in this deployment's
   * region (see connectorFunctionArn).
   * @public
   */
  customConnectorConfiguration?: CustomConnectorConfiguration | undefined;

  /**
   * Whether AI-powered metadata enrichment runs for this source.
   * @public
   */
  metadataEnrichmentEnabled?: boolean | undefined;
}

/**
 * @public
 */
export interface UpdateSourceMetadataOutput {
  /**
   * Identifier of the updated source.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Unified lifecycle status for all source types.
   * @public
   */
  status: SourceStatus | undefined;

  /**
   * Timestamp when the source was last updated.
   * @public
   */
  updatedAt: Date | undefined;
}

/**
 * Steward-supplied foreign key relationship. Stored with
 * source = STEWARD_SPECIFIED.
 * @public
 */
export interface ForeignKeyInput {
  /**
   * Column name identifier.
   * @public
   */
  column: string | undefined;

  /**
   * Referenced table.
   * @public
   */
  targetTable: string | undefined;

  /**
   * Referenced column in the target table.
   * @public
   */
  targetColumn?: string | undefined;

  /**
   * Origin of the key. Preserved on a steward review so an approved inferred
   * relationship keeps its AI_INFERRED provenance (#1088).
   * @public
   */
  source?: string | undefined;

  /**
   * Steward review decision for an inferred relationship (#1088): APPROVED or
   * REJECTED. Omitted for a plain steward-authored edit (treated as approved).
   * @public
   */
  reviewStatus?: string | undefined;

  /**
   * Datasource id of the target table for a cross-source relationship (#1088).
   * @public
   */
  targetDatasourceId?: string | undefined;

  /**
   * Provenance note, preserved across a review round-trip (#1088).
   * @public
   */
  provenance?: string | undefined;
}

/**
 * Steward-supplied primary key. Replaces the table's primary key; an empty
 * columns list clears it. Stored with source = STEWARD_SPECIFIED.
 * @public
 */
export interface PrimaryKeyInput {
  /**
   * Column names composing the primary key; empty list clears it.
   * @public
   */
  columns: string[] | undefined;
}

/**
 * @public
 */
export interface UpdateSourceTableKeysInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source containing the table.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Table identifier (database.table format).
   * @public
   */
  tableId: string | undefined;

  /**
   * Steward-supplied primary key. Replaces the table's primary key; an empty
   * columns list clears it. Stored with source = STEWARD_SPECIFIED.
   * @public
   */
  primaryKey?: PrimaryKeyInput | undefined;

  /**
   * Foreign-key relationships to set for the table.
   * @public
   */
  foreignKeys?: ForeignKeyInput[] | undefined;
}

/**
 * @public
 */
export interface UpdateSourceTableKeysOutput {
  /**
   * Identifier of the updated table.
   * @public
   */
  tableId: string | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus: ReviewStatus | undefined;
}

/**
 * @public
 */
export interface UpdateSourceTableMetadataInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the source containing the table.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Table identifier (database.table format).
   * @public
   */
  tableId: string | undefined;

  /**
   * Steward-supplied overrides applied to discovered metadata: description,
   * synonyms, glossary terms, and tags.
   * @public
   */
  overrides: MetadataOverrides | undefined;
}

/**
 * @public
 */
export interface UpdateSourceTableMetadataOutput {
  /**
   * Identifier of the updated table.
   * @public
   */
  tableId: string | undefined;

  /**
   * Review status for enriched metadata.
   * @public
   */
  reviewStatus: ReviewStatus | undefined;
}

/**
 * One class node of the nested tree.
 * @public
 */
export interface OntologyTreeNode {
  /**
   * Class IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label.
   * @public
   */
  label: string | undefined;

  /**
   * Superclass IRIs; empty for a root class.
   * @public
   */
  parents?: string[] | undefined;

  /**
   * Child nodes, sorted by label.
   * @public
   */
  children?: OntologyTreeNode[] | undefined;
}

/**
 * Class hierarchy, flat class list and property list of the current T-Box.
 *
 * When nothing is published the server returns an empty `tree`, empty
 * `classes`/`properties`, zero counts and no `pointer`; it does not raise
 * `NotFoundError`.
 * @public
 */
export interface OntologyTreeResult {
  /**
   * Current pointer; absent when nothing is published.
   * @public
   */
  pointer?: OntologyPointer | undefined;

  /**
   * Nested class tree, roots sorted by label.
   * @public
   */
  tree: OntologyTreeNode[] | undefined;

  /**
   * Flat class list, sorted by label.
   * @public
   */
  classes: OntologyClassRef[] | undefined;

  /**
   * Flat property list, sorted by label.
   * @public
   */
  properties: OntologyPropertyRef[] | undefined;

  /**
   * Counts for both flat lists.
   * @public
   */
  counts: OntologyBrowseCounts | undefined;
}
