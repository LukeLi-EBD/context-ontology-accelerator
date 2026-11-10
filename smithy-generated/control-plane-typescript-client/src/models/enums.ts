// smithy-typescript generated code
/**
 * @public
 * @enum
 */
export const FactCandidateStatus = {
  /**
   * Approved; a fact row and an A-Box triple exist.
   */
  APPROVED: "APPROVED",
  /**
   * Awaiting steward review.
   */
  PENDING: "PENDING",
  /**
   * Rejected; kept for audit, never projected into the A-Box.
   */
  REJECTED: "REJECTED",
} as const;
/**
 * @public
 */
export type FactCandidateStatus = (typeof FactCandidateStatus)[keyof typeof FactCandidateStatus];

/**
 * @public
 * @enum
 */
export const DocumentStatus = {
  /**
   * Ingestion failed; the document row keeps the error reason.
   */
  FAILED: "FAILED",
  /**
   * Chunks, embeddings and fact candidates exist.
   */
  INDEXED: "INDEXED",
  /**
   * Ingestion (chunking/embedding/extraction) in progress.
   */
  PROCESSING: "PROCESSING",
  /**
   * Bytes stored, ingestion not started.
   */
  UPLOADED: "UPLOADED",
} as const;
/**
 * @public
 */
export type DocumentStatus = (typeof DocumentStatus)[keyof typeof DocumentStatus];

/**
 * @public
 * @enum
 */
export const FactObjectKind = {
  /**
   * Object is an IRI.
   */
  iri: "iri",
  /**
   * Object is a literal value.
   */
  literal: "literal",
} as const;
/**
 * @public
 */
export type FactObjectKind = (typeof FactObjectKind)[keyof typeof FactObjectKind];

/**
 * @public
 * @enum
 */
export const FactSourceKind = {
  /**
   * Extracted from a document.
   */
  document: "document",
  /**
   * Entered by an operator.
   */
  manual: "manual",
  /**
   * Written by a merge adjudication.
   */
  merge: "merge",
  /**
   * Loaded from a table.
   */
  table: "table",
} as const;
/**
 * @public
 */
export type FactSourceKind = (typeof FactSourceKind)[keyof typeof FactSourceKind];

/**
 * @public
 * @enum
 */
export const FactState = {
  /**
   * The row currently backs the A-Box graph.
   */
  active: "active",
  /**
   * The row was withdrawn; the assertion is no longer asserted.
   */
  retracted: "retracted",
  /**
   * A newer merged row replaced this one.
   */
  superseded: "superseded",
} as const;
/**
 * @public
 */
export type FactState = (typeof FactState)[keyof typeof FactState];

/**
 * @public
 * @enum
 */
export const FactEventFormat = {
  /**
   * Full event payload, including the stored JSON document.
   */
  full: "full",
  /**
   * Event header only: no payload document.
   */
  summary: "summary",
} as const;
/**
 * @public
 */
export type FactEventFormat = (typeof FactEventFormat)[keyof typeof FactEventFormat];

/**
 * @public
 * @enum
 */
export const FactStateFilter = {
  /**
   * Only active rows.
   */
  active: "active",
  /**
   * Rows in any state (the default).
   */
  all: "all",
  /**
   * Only retracted rows.
   */
  retracted: "retracted",
  /**
   * Only superseded rows.
   */
  superseded: "superseded",
} as const;
/**
 * @public
 */
export type FactStateFilter = (typeof FactStateFilter)[keyof typeof FactStateFilter];

/**
 * @public
 * @enum
 */
export const FactConflictAction = {
  /**
   * Apply one `keep` rule to every pending group inside the scope.
   */
  batch: "batch",
  /**
   * Keep one value, retire the others.
   */
  keep: "keep",
  /**
   * Accept the conflict: every value stays active.
   */
  keep_both: "keep_both",
  /**
   * Retire every conflicting value and record one merged value.
   */
  merge: "merge",
} as const;
/**
 * @public
 */
export type FactConflictAction = (typeof FactConflictAction)[keyof typeof FactConflictAction];

/**
 * @public
 * @enum
 */
export const PrincipalType = {
  /**
   * A non-human agent identity (e.g. a service or automation).
   */
  AGENT: "Agent",
  /**
   * A group of users; the grant applies to all members.
   */
  GROUP: "Group",
  /**
   * An individual user identity.
   */
  USER: "User",
} as const;
/**
 * @public
 */
export type PrincipalType = (typeof PrincipalType)[keyof typeof PrincipalType];

/**
 * @public
 * @enum
 */
export const IngestionRunKind = {
  /**
   * Directory imports recorded in platform.import_batch.
   */
  BATCH: "BATCH",
} as const;
/**
 * @public
 */
export type IngestionRunKind = (typeof IngestionRunKind)[keyof typeof IngestionRunKind];

/**
 * @public
 * @enum
 */
export const IngestionRunStatus = {
  /**
   * Every discovered item was processed (indexed or failed).
   */
  COMPLETED: "COMPLETED",
  /**
   * The run was stopped before finishing and can be resumed.
   */
  INTERRUPTED: "INTERRUPTED",
  /**
   * Import is currently writing items.
   */
  RUNNING: "RUNNING",
  /**
   * The run's lease expired and a recovery pass marked it stale.
   */
  STALE: "STALE",
} as const;
/**
 * @public
 */
export type IngestionRunStatus = (typeof IngestionRunStatus)[keyof typeof IngestionRunStatus];

/**
 * @public
 * @enum
 */
export const TimeGrain = {
  /**
   * Daily granularity.
   */
  DAY: "DAY",
  /**
   * Monthly granularity.
   */
  MONTH: "MONTH",
  /**
   * Quarterly granularity.
   */
  QUARTER: "QUARTER",
  /**
   * Weekly granularity.
   */
  WEEK: "WEEK",
  /**
   * Yearly granularity.
   */
  YEAR: "YEAR",
} as const;
/**
 * @public
 */
export type TimeGrain = (typeof TimeGrain)[keyof typeof TimeGrain];

/**
 * @public
 * @enum
 */
export const SqlDialect = {
  /**
   * Databricks SQL dialect.
   */
  DATABRICKS: "DATABRICKS",
  /**
   * MySQL SQL dialect.
   */
  MYSQL: "MYSQL",
  /**
   * PostgreSQL SQL dialect.
   */
  POSTGRESQL: "POSTGRESQL",
  /**
   * Amazon Redshift SQL dialect.
   */
  REDSHIFT: "REDSHIFT",
  /**
   * Snowflake SQL dialect.
   */
  SNOWFLAKE: "SNOWFLAKE",
  /**
   * Trino SQL dialect.
   */
  TRINO: "TRINO",
} as const;
/**
 * @public
 */
export type SqlDialect = (typeof SqlDialect)[keyof typeof SqlDialect];

/**
 * @public
 * @enum
 */
export const WarningSeverity = {
  /**
   * Blocking issue: the metric is rejected at create/update. This includes
   * SQL accepted by neither the persistence gate nor serve-time firewall,
   * an unapproved source, and a provably absent declared source table.
   */
  ERROR: "ERROR",
  /**
   * Informational, non-blocking notice.
   */
  INFO: "INFO",
  /**
   * Warning-level issue; non-fatal but should be reviewed.
   */
  WARNING: "WARNING",
} as const;
/**
 * @public
 */
export type WarningSeverity = (typeof WarningSeverity)[keyof typeof WarningSeverity];

/**
 * @public
 * @enum
 */
export const ExportFormat = {
  INLINE: "inline",
  S3: "s3",
} as const;
/**
 * @public
 */
export type ExportFormat = (typeof ExportFormat)[keyof typeof ExportFormat];

/**
 * @public
 * @enum
 */
export const ImportJobStatus = {
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
  IN_PROGRESS: "IN_PROGRESS",
} as const;
/**
 * @public
 */
export type ImportJobStatus = (typeof ImportJobStatus)[keyof typeof ImportJobStatus];

/**
 * @public
 * @enum
 */
export const NamespaceStatus = {
  /**
   * The namespace is active and accepting reads and writes.
   */
  ACTIVE: "ACTIVE",
  /**
   * The namespace is archived and read-only; mutations are rejected.
   */
  ARCHIVED: "ARCHIVED",
  /**
   * The namespace and its resources have been fully deleted.
   */
  DELETED: "DELETED",
  /**
   * The deletion pipeline failed; the namespace may be partially deleted.
   */
  DELETE_FAILED: "DELETE_FAILED",
  /**
   * Deletion pipeline is running (async cleanup of child resources in
   * progress). Set immediately when DELETE /namespaces/{id} is accepted;
   * cleared to DELETED on success or DELETE_FAILED on error.
   */
  DELETING: "DELETING",
} as const;
/**
 * @public
 */
export type NamespaceStatus = (typeof NamespaceStatus)[keyof typeof NamespaceStatus];

/**
 * @public
 * @enum
 */
export const VkgHealthStatus = {
  /**
   * A task is running but its container health check is failing, so the
   * service cannot answer queries (e.g. the published R2RML/schema could not
   * be loaded). Distinct from UNAVAILABLE, which means no task is running.
   */
  DEGRADED: "DEGRADED",
  /**
   * Running and able to translate queries.
   */
  HEALTHY: "HEALTHY",
  /**
   * The service is starting up (deployment in progress); expected to become HEALTHY shortly.
   */
  PROVISIONING: "PROVISIONING",
  /**
   * The service exists but is not currently serving (no running task).
   */
  UNAVAILABLE: "UNAVAILABLE",
  /**
   * Not deployed yet, or the state could not be determined.
   */
  UNKNOWN: "UNKNOWN",
} as const;
/**
 * @public
 */
export type VkgHealthStatus = (typeof VkgHealthStatus)[keyof typeof VkgHealthStatus];

/**
 * @public
 * @enum
 */
export const LinkDirection = {
  /**
   * Follow edges in both directions.
   */
  BOTH: "both",
  /**
   * Follow object -> subject edges into the seed IRI.
   */
  INCOMING: "incoming",
  /**
   * Follow subject -> object edges out of the seed IRI.
   */
  OUTGOING: "outgoing",
} as const;
/**
 * @public
 */
export type LinkDirection = (typeof LinkDirection)[keyof typeof LinkDirection];

/**
 * @public
 * @enum
 */
export const IngestJobState = {
  /**
   * The ingest job finished successfully.
   */
  COMPLETED: "completed",
  /**
   * Ingest finished writing; waiting for the just-written embeddings to
   * become searchable in the (eventually-consistent) vector index before
   * the job is reported COMPLETED.
   */
  EMBEDDINGS_SYNC: "embeddings_sync",
  /**
   * The ingest job failed.
   */
  FAILED: "failed",
  /**
   * The ingest job is queued and has not started yet.
   */
  PENDING: "pending",
  /**
   * The ingest job is currently running.
   */
  RUNNING: "running",
} as const;
/**
 * @public
 */
export type IngestJobState = (typeof IngestJobState)[keyof typeof IngestJobState];

/**
 * @public
 * @enum
 */
export const GraphVertexKind = {
  /**
   * An annotation property (metadata such as labels or comments).
   */
  ANNOTATION_PROPERTY: "annotation-property",
  /**
   * A blank (anonymous) node.
   */
  BLANK_NODE: "blank-node",
  /**
   * An OWL/RDFS class.
   */
  CLASS: "class",
  /**
   * A datatype property (relates individuals to literal values).
   */
  DATATYPE_PROPERTY: "datatype-property",
  /**
   * A literal value node.
   */
  LITERAL: "literal",
  /**
   * An object property (relates individuals to individuals).
   */
  OBJECT_PROPERTY: "object-property",
  /**
   * The ontology header node itself.
   */
  ONTOLOGY: "ontology",
  /**
   * A property of unspecified kind.
   */
  PROPERTY: "property",
  /**
   * A vertex whose kind could not be determined.
   */
  UNKNOWN: "unknown",
} as const;
/**
 * @public
 */
export type GraphVertexKind = (typeof GraphVertexKind)[keyof typeof GraphVertexKind];

/**
 * @public
 * @enum
 */
export const OntologyFileFormat = {
  /**
   * JSON-LD (file-extension spelling).
   */
  JSONLD: "jsonld",
  /**
   * JSON-LD.
   */
  JSON_LD: "json-ld",
  /**
   * OWL in RDF/XML.
   */
  OWL_XML: "owl-xml",
  /**
   * RDF/XML (media-type spelling).
   */
  RDF_PLUS_XML: "rdf+xml",
  /**
   * RDF/XML.
   */
  RDF_XML: "rdf-xml",
  /**
   * Turtle (file-extension spelling).
   */
  TTL: "ttl",
  /**
   * Turtle.
   */
  TURTLE: "turtle",
  /**
   * RDF/XML (short spelling).
   */
  XML: "xml",
} as const;
/**
 * @public
 */
export type OntologyFileFormat = (typeof OntologyFileFormat)[keyof typeof OntologyFileFormat];

/**
 * @public
 * @enum
 */
export const OntologyType = {
  /**
   * A foundational (upper / reference) ontology.
   */
  FOUNDATIONAL: "foundational",
  /**
   * An ontology induced from data sources (e.g. tables).
   */
  INDUCED: "induced",
  /**
   * An ontology created manually by a user.
   */
  USER_CREATED: "user_created",
  /**
   * An ontology file a user uploaded (the web app's upload flow).
   */
  USER_UPLOADED: "user_uploaded",
} as const;
/**
 * @public
 */
export type OntologyType = (typeof OntologyType)[keyof typeof OntologyType];

/**
 * @public
 * @enum
 */
export const ProposalStatus = {
  /**
   * The proposal was accepted and merged successfully.
   */
  ACCEPTED: "accepted",
  /**
   * In-flight state: a worker is merging the accepted ontology into the namespace.
   */
  ACCEPTING: "accepting",
  /**
   * An accept ran but a pipeline step exhausted its retries. ``acceptError``
   * names the failing step. Terminal for that attempt, but the proposal stays
   * re-acceptable: the pipeline is idempotent, so re-submitting
   * ``AcceptProposal`` after fixing the cause converges.
   */
  ACCEPT_FAILED: "accept_failed",
  /**
   * The proposal was cancelled.
   */
  CANCELLED: "cancelled",
  /**
   * In-flight state following ``accepting``: the ontology is merged and the
   * worker is waiting for the embeddings it wrote to become searchable in the
   * eventually-consistent vector index.
   */
  EMBEDDINGS_SYNC: "embeddings_sync",
  /**
   * Induction or acceptance failed.
   */
  FAILED: "failed",
  /**
   * First in-flight state: induction triggered, a worker is building the ontology.
   */
  INDUCING: "inducing",
  /**
   * The ontology finished building and the proposal awaits review.
   */
  PENDING: "pending",
  /**
   * The proposal was rejected by a reviewer.
   */
  REJECTED: "rejected",
  /**
   * The proposal's Turtle/R2RML content was revised by the user.
   */
  UPDATED: "updated",
} as const;
/**
 * @public
 */
export type ProposalStatus = (typeof ProposalStatus)[keyof typeof ProposalStatus];

/**
 * @public
 * @enum
 */
export const IncludeMode = {
  /**
   * Synonym for `report`.
   */
  FULL: "full",
  /**
   * Return the full induction report including every entry in `report.matches`.
   * May exceed the 6MB response cap on large inductions — intended for
   * debugging, not for polling.
   */
  REPORT: "report",
} as const;
/**
 * @public
 */
export type IncludeMode = (typeof IncludeMode)[keyof typeof IncludeMode];

/**
 * @public
 * @enum
 */
export const MatchType = {
  /**
   * An ambiguous match requiring review.
   */
  AMBIGUOUS: "ambiguous",
  /**
   * An exact match to an existing concept.
   */
  EXACT: "exact",
  /**
   * A high-confidence match to an existing concept.
   */
  HIGH_CONFIDENCE: "high_confidence",
  /**
   * No match found — a novel concept was created.
   */
  NOVEL: "novel",
} as const;
/**
 * @public
 */
export type MatchType = (typeof MatchType)[keyof typeof MatchType];

/**
 * @public
 * @enum
 */
export const InductionSourceType = {
  /**
   * A document-to-table bridge run (`bridge_to_tables` strategy) over an
   * accepted ontology. Its result is a pending proposal (or none on a dry
   * run); `bridgeReport.proposalId` names it.
   */
  BRIDGE: "BRIDGE",
  /**
   * A structured (table-to-ontology) induction run.
   */
  STRUCTURED: "STRUCTURED",
  /**
   * An unstructured (knowledge-graph-to-ontology) induction run.
   */
  UNSTRUCTURED: "UNSTRUCTURED",
} as const;
/**
 * @public
 */
export type InductionSourceType = (typeof InductionSourceType)[keyof typeof InductionSourceType];

/**
 * @public
 * @enum
 */
export const InductionJobStatus = {
  /**
   * Unstructured stage: applying induction rules.
   */
  APPLYING_RULES: "applying_rules",
  /**
   * Building the induced ontology.
   */
  BUILDING_ONTOLOGY: "building_ontology",
  /**
   * The induction job finished successfully.
   */
  COMPLETED: "completed",
  /**
   * Unstructured stage: running entailment/reasoning.
   */
  ENTAILMENT: "entailment",
  /**
   * The induction job failed.
   */
  FAILED: "failed",
  /**
   * Fetching data source metadata (schema, constraints, relationships).
   */
  FETCHING_METADATA: "fetching_metadata",
  /**
   * Unstructured stage: generating concept descriptions.
   */
  GENERATING_DESCRIPTIONS: "generating_descriptions",
  /**
   * Generating embeddings for matching.
   */
  GENERATING_EMBEDDINGS: "generating_embeddings",
  /**
   * Loading the existing ontologies to ground against.
   */
  LOADING_GROUNDING_ONTOLOGIES: "loading_grounding_ontologies",
  /**
   * Matching induced concepts against grounding ontologies.
   */
  MATCHING: "matching",
  /**
   * The job is queued and has not started.
   */
  PENDING: "pending",
  /**
   * Unstructured stage: querying the Neptune knowledge graph.
   */
  QUERYING_NEPTUNE: "querying_neptune",
  /**
   * Unstructured stage: resolving concept IRIs.
   */
  RESOLVING_IRIS: "resolving_iris",
  /**
   * Bridge job (`bridge_to_tables` strategy) in progress. The current step
   * is in the job's `progress` field. A bridge job goes
   * pending → running → completed | failed.
   */
  RUNNING: "running",
  /**
   * Unstructured stage: sampling graph data.
   */
  SAMPLING: "sampling",
  /**
   * Unstructured stage: serializing the induced ontology.
   */
  SERIALIZING: "serializing",
  /**
   * Persisting the induced ontology and proposal.
   */
  STORING: "storing",
} as const;
/**
 * @public
 */
export type InductionJobStatus = (typeof InductionJobStatus)[keyof typeof InductionJobStatus];

/**
 * @public
 * @enum
 */
export const ProposalValidationSeverity = {
  /**
   * An error-level finding.
   */
  ERROR: "error",
  /**
   * An informational finding.
   */
  INFO: "info",
  /**
   * A warning-level finding.
   */
  WARNING: "warning",
} as const;
/**
 * @public
 */
export type ProposalValidationSeverity = (typeof ProposalValidationSeverity)[keyof typeof ProposalValidationSeverity];

/**
 * @public
 * @enum
 */
export const ProposalValidationTier = {
  /**
   * Tier 1: blocking validators (findings block acceptance).
   */
  TIER1_BLOCKING: "tier1_blocking",
  /**
   * Tier 2: scoring validators (findings contribute to a quality score).
   */
  TIER2_SCORING: "tier2_scoring",
  /**
   * Tier 3: review validators (findings surfaced for human review).
   */
  TIER3_REVIEW: "tier3_review",
} as const;
/**
 * @public
 */
export type ProposalValidationTier = (typeof ProposalValidationTier)[keyof typeof ProposalValidationTier];

/**
 * @public
 * @enum
 */
export const ProposalValidationJobStatus = {
  /**
   * The validation job finished successfully.
   */
  COMPLETED: "completed",
  /**
   * The validation job failed.
   */
  FAILED: "failed",
  /**
   * The validation job is queued and has not started.
   */
  PENDING: "pending",
  /**
   * The validation job is running.
   */
  RUNNING: "running",
} as const;
/**
 * @public
 */
export type ProposalValidationJobStatus =
  (typeof ProposalValidationJobStatus)[keyof typeof ProposalValidationJobStatus];

/**
 * @public
 * @enum
 */
export const GroundingMode = {
  /**
   * Default — always defers to the LLM reranker for domain verification.
   */
  ENHANCED: "ENHANCED",
  /**
   * Grounding disabled — induced classes are never aligned to existing ontologies.
   */
  NONE: "NONE",
  /**
   * Auto-grounds exact-name matches against existing ontologies.
   */
  STANDARD: "STANDARD",
} as const;
/**
 * @public
 */
export type GroundingMode = (typeof GroundingMode)[keyof typeof GroundingMode];

/**
 * @public
 * @enum
 */
export const InductionStrategy = {
  /**
   * Document-to-table bridge, run on its own on the namespace's already
   * accepted ontology named by `ontologyUriPrefix`. Links document-induced
   * classes to table and column classes and proposes document-derived
   * definitions for those tables and columns. Needs an accepted table
   * ontology with R2RML mappings into which a document induction was also
   * accepted (the same ontology). Writes nothing itself: the completed job
   * names a pending proposal (`bridgeReport.proposalId`) holding the touched
   * tables with their new definitions, which is reviewed and accepted like
   * any other proposal. `datasourceIds` is ignored; send an empty list.
   * Returns a `jobId` to poll with GetInductionJob.
   */
  BRIDGE_TO_TABLES: "bridge_to_tables",
  /**
   * The RIGOR ontology induction strategy. Available only for namespaces
   * whose language has the primary subtag `en`; any other namespace is
   * rejected with a validation error before a job starts.
   */
  RIGOR_ONTOLOGY: "rigor_ontology",
  /**
   * Structured strategy: induce an ontology directly from relational table schemas.
   */
  TABLE_TO_ONTOLOGY: "table_to_ontology",
  /**
   * Unstructured strategy: induce an ontology from a lexical knowledge graph.
   */
  UNSTRUCTURED_LEXICAL_GRAPH: "unstructured_lexical_graph",
} as const;
/**
 * @public
 */
export type InductionStrategy = (typeof InductionStrategy)[keyof typeof InductionStrategy];

/**
 * @public
 * @enum
 */
export const OntologyExportFormat = {
  /**
   * N-Quads (`.nq`).
   */
  nquads: "nquads",
  /**
   * Turtle (`.ttl`).
   */
  turtle: "turtle",
} as const;
/**
 * @public
 */
export type OntologyExportFormat = (typeof OntologyExportFormat)[keyof typeof OntologyExportFormat];

/**
 * @public
 * @enum
 */
export const OntologyImpactChange = {
  /**
   * The class or property exists only in the target version.
   */
  added: "added",
  /**
   * The class or property exists in both; its triples changed.
   */
  modified: "modified",
  /**
   * The class or property exists only in the baseline.
   */
  removed: "removed",
} as const;
/**
 * @public
 */
export type OntologyImpactChange = (typeof OntologyImpactChange)[keyof typeof OntologyImpactChange];

/**
 * @public
 * @enum
 */
export const OntologyProposalStatus = {
  /**
   * Approved; publish may proceed.
   */
  approved: "approved",
  /**
   * Submitted and waiting for review.
   */
  proposed: "proposed",
  /**
   * The proposal's version was published.
   */
  published: "published",
  /**
   * Review rejected the proposal. The proposal row itself only stores
   * proposed/approved/published; rejection is reported here on the review
   * response while the version row carries `rejected`.
   */
  rejected: "rejected",
  /**
   * Under review.
   */
  review: "review",
} as const;
/**
 * @public
 */
export type OntologyProposalStatus = (typeof OntologyProposalStatus)[keyof typeof OntologyProposalStatus];

/**
 * @public
 * @enum
 */
export const OntologyVersionStatus = {
  /**
   * The proposal (and the version) is approved for publish.
   */
  approved: "approved",
  /**
   * Archived read-only baseline; cannot be published or rolled back to.
   */
  deprecated: "deprecated",
  /**
   * Imported, not yet proposed.
   */
  draft: "draft",
  /**
   * A proposal was submitted and waits for review.
   */
  proposed: "proposed",
  /**
   * The version backs the `tbox/current` pointer.
   */
  published: "published",
  /**
   * Review rejected the proposal.
   */
  rejected: "rejected",
  /**
   * The proposal is being reviewed.
   */
  review: "review",
  /**
   * A newer version replaced it at the pointer.
   */
  superseded: "superseded",
} as const;
/**
 * @public
 */
export type OntologyVersionStatus = (typeof OntologyVersionStatus)[keyof typeof OntologyVersionStatus];

/**
 * @public
 * @enum
 */
export const OntologyImportFormat = {
  /**
   * N-Triples.
   */
  nt: "nt",
  /**
   * Turtle.
   */
  turtle: "turtle",
} as const;
/**
 * @public
 */
export type OntologyImportFormat = (typeof OntologyImportFormat)[keyof typeof OntologyImportFormat];

/**
 * @public
 * @enum
 */
export const OntologyProposalDecision = {
  /**
   * Approve the proposal and move the version to `approved`.
   */
  APPROVE: "APPROVE",
  /**
   * Reject the proposal and mark the version `rejected`.
   */
  REJECT: "REJECT",
} as const;
/**
 * @public
 */
export type OntologyProposalDecision = (typeof OntologyProposalDecision)[keyof typeof OntologyProposalDecision];

/**
 * @public
 * @enum
 */
export const OntologyRollbackMode = {
  /**
   * Copy the target version into a new version, then move the pointer.
   */
  NEW_VERSION: "NEW_VERSION",
  /**
   * Move the `tbox/current` pointer back to an existing version.
   */
  POINTER_ONLY: "POINTER_ONLY",
} as const;
/**
 * @public
 */
export type OntologyRollbackMode = (typeof OntologyRollbackMode)[keyof typeof OntologyRollbackMode];

/**
 * @public
 * @enum
 */
export const OntologyValidationSeverity = {
  /**
   * Blocking finding; any `error` makes the report fail.
   */
  error: "error",
  /**
   * Informational, flagged for review.
   */
  info: "info",
  /**
   * Non-blocking scoring warning.
   */
  warning: "warning",
} as const;
/**
 * @public
 */
export type OntologyValidationSeverity = (typeof OntologyValidationSeverity)[keyof typeof OntologyValidationSeverity];

/**
 * @public
 * @enum
 */
export const OntologyValidationTier = {
  /**
   * Blocking checks: SHACL conformance, fatal structural errors.
   */
  tier1_blocking: "tier1_blocking",
  /**
   * Scoring checks: OntoQA-style structural metrics.
   */
  tier2_scoring: "tier2_scoring",
  /**
   * Review checks: findings surfaced for a human, not blocking.
   */
  tier3_review: "tier3_review",
} as const;
/**
 * @public
 */
export type OntologyValidationTier = (typeof OntologyValidationTier)[keyof typeof OntologyValidationTier];

/**
 * @public
 * @enum
 */
export const OntologyValidationJobStatus = {
  /**
   * All requested tiers finished; `report` is present.
   */
  completed: "completed",
  /**
   * The job aborted; `error` carries the reason and there is no report.
   */
  failed: "failed",
  /**
   * Accepted and queued; no work has started.
   */
  pending: "pending",
  /**
   * The worker is running the requested tiers.
   */
  running: "running",
} as const;
/**
 * @public
 */
export type OntologyValidationJobStatus =
  (typeof OntologyValidationJobStatus)[keyof typeof OntologyValidationJobStatus];

/**
 * @public
 * @enum
 */
export const AnswerQualityStrategy = {
  /**
   * Hybrid lexical + vector retrieval.
   */
  hybrid: "hybrid",
  /**
   * Lexical retrieval only.
   */
  lexical: "lexical",
  /**
   * Vector (embedding) retrieval only.
   */
  vector: "vector",
} as const;
/**
 * @public
 */
export type AnswerQualityStrategy = (typeof AnswerQualityStrategy)[keyof typeof AnswerQualityStrategy];

/**
 * @public
 * @enum
 */
export const RoleScope = {
  /**
   * The role applies within a single namespace.
   */
  NAMESPACE: "NAMESPACE",
  /**
   * The role applies platform-wide, across all namespaces.
   */
  PLATFORM: "PLATFORM",
} as const;
/**
 * @public
 */
export type RoleScope = (typeof RoleScope)[keyof typeof RoleScope];

/**
 * @public
 * @enum
 */
export const SourceStatus = {
  /**
   * Async bulk approve worker failed; client may retry by calling
   * ApproveSource again (database sources only)
   */
  APPROVAL_FAILED: "APPROVAL_FAILED",
  /**
   * All tables reviewed and approved (database sources only)
   */
  APPROVED: "APPROVED",
  /**
   * Bulk approve in progress — async worker is writing DataZone revisions
   * (database sources only)
   */
  APPROVING: "APPROVING",
  /**
   * Processing completed successfully (document sources)
   */
  COMPLETED: "COMPLETED",
  /**
   * Fully deleted
   */
  DELETED: "DELETED",
  /**
   * Deletion failed
   */
  DELETE_FAILED: "DELETE_FAILED",
  /**
   * Deletion in progress
   */
  DELETING: "DELETING",
  /**
   * AI metadata enrichment in progress (database sources only)
   */
  ENRICHING: "ENRICHING",
  /**
   * Enrichment complete, awaiting human review (database sources only)
   */
  PENDING_REVIEW: "PENDING_REVIEW",
  /**
   * Source registered, pipeline not yet started
   */
  REGISTERED: "REGISTERED",
  /**
   * Bulk reject completed — the source and all its tables/columns are
   * rejected. Terminal: no further review transitions are allowed; the
   * steward must re-onboard a new source (database sources only)
   */
  REJECTED: "REJECTED",
  /**
   * Bulk reject in progress — async worker is writing DataZone revisions
   * (database sources only)
   */
  REJECTING: "REJECTING",
  /**
   * Async bulk reject worker failed; client may retry by calling
   * RejectSource again (database sources only)
   */
  REJECTION_FAILED: "REJECTION_FAILED",
  /**
   * A re-scan of an already-APPROVED source detected changes that are
   * awaiting steward review. Distinct from PENDING_REVIEW (initial
   * enrichment) so the UI can show "approved source, N changes to review"
   * and so downstream consumers that gate on APPROVED treat the source as
   * not-currently-approved while its drift is under review. On approve the
   * source returns to APPROVED; on reject it returns to APPROVED unchanged.
   * (database sources only)
   */
  RESCAN_REVIEW: "RESCAN_REVIEW",
  /**
   * Pipeline is running (schema discovery or document ingestion)
   */
  SCANNING: "SCANNING",
  /**
   * LLM entity extraction in progress (document sources only)
   */
  SCANNING_ENTITY_EXTRACTION: "SCANNING_ENTITY_EXTRACTION",
  /**
   * Knowledge graph build in progress (document sources only)
   */
  SCANNING_KG_BUILD: "SCANNING_KG_BUILD",
  /**
   * Processing failed
   */
  SCAN_FAILED: "SCAN_FAILED",
} as const;
/**
 * @public
 */
export type SourceStatus = (typeof SourceStatus)[keyof typeof SourceStatus];

/**
 * @public
 * @enum
 */
export const GlueExecutionEngine = {
  /**
   * Execute via Amazon Athena (default).
   */
  ATHENA: "ATHENA",
  /**
   * Execute via Amazon Redshift Serverless `awsdatacatalog` auto-mount.
   */
  REDSHIFT: "REDSHIFT",
} as const;
/**
 * @public
 */
export type GlueExecutionEngine = (typeof GlueExecutionEngine)[keyof typeof GlueExecutionEngine];

/**
 * @public
 * @enum
 */
export const DatabaseEngine = {
  /**
   * MySQL database engine.
   */
  MYSQL: "MYSQL",
  /**
   * Oracle database engine.
   */
  ORACLE: "ORACLE",
  /**
   * PostgreSQL database engine.
   */
  POSTGRESQL: "POSTGRESQL",
  /**
   * Amazon Redshift database engine.
   */
  REDSHIFT: "REDSHIFT",
  /**
   * Snowflake database engine.
   */
  SNOWFLAKE: "SNOWFLAKE",
  /**
   * Microsoft SQL Server database engine.
   */
  SQLSERVER: "SQLSERVER",
} as const;
/**
 * @public
 */
export type DatabaseEngine = (typeof DatabaseEngine)[keyof typeof DatabaseEngine];

/**
 * @public
 * @enum
 */
export const SparqlAuthMode = {
  /**
   * AWS Signature V4 with the caller's IAM role. No credential secret.
   */
  SIGV4: "sigv4",
} as const;
/**
 * @public
 */
export type SparqlAuthMode = (typeof SparqlAuthMode)[keyof typeof SparqlAuthMode];

/**
 * @public
 * @enum
 */
export const SparqlStore = {
  /**
   * Amazon Neptune (SPARQL 1.1 over HTTPS, SigV4/IAM auth).
   */
  NEPTUNE: "neptune",
} as const;
/**
 * @public
 */
export type SparqlStore = (typeof SparqlStore)[keyof typeof SparqlStore];

/**
 * @public
 * @enum
 */
export const ExtractionMode = {
  /**
   * Extract documents in a single continuous pass.
   */
  CONTINUOUS: "continuous",
  /**
   * Extract documents as separated units.
   */
  SEPARATED: "separated",
} as const;
/**
 * @public
 */
export type ExtractionMode = (typeof ExtractionMode)[keyof typeof ExtractionMode];

/**
 * @public
 * @enum
 */
export const SourceType = {
  /**
   * A structured database source.
   */
  DATABASE: "DATABASE",
  /**
   * An unstructured documents source.
   */
  DOCUMENTS: "DOCUMENTS",
} as const;
/**
 * @public
 */
export type SourceType = (typeof SourceType)[keyof typeof SourceType];

/**
 * @public
 * @enum
 */
export const QueryEngine = {
  /**
   * Query via Amazon Athena — native Glue catalog, or a JDBC federated catalog.
   */
  ATHENA: "ATHENA",
  /**
   * Query the database directly over JDBC (no Athena).
   */
  JDBC: "JDBC",
  /**
   * Query Glue/Iceberg tables via Amazon Redshift Serverless using the
   * `awsdatacatalog` auto-mount (an alternative execution engine to Athena
   * for Glue-backed sources; opt-in per source via
   * GlueConfiguration.executionEngine).
   */
  REDSHIFT: "REDSHIFT",
} as const;
/**
 * @public
 */
export type QueryEngine = (typeof QueryEngine)[keyof typeof QueryEngine];

/**
 * @public
 * @enum
 */
export const PreprocessingIssueType = {
  /**
   * The file errored during preprocessing.
   */
  ERROR: "error",
  /**
   * The file was skipped during preprocessing.
   */
  SKIPPED: "skipped",
} as const;
/**
 * @public
 */
export type PreprocessingIssueType = (typeof PreprocessingIssueType)[keyof typeof PreprocessingIssueType];

/**
 * @public
 * @enum
 */
export const SourceSubType = {
  /**
   * Structured: customer-authored AWS Athena Query Federation SDK connector
   * (a Lambda in the customer's account), registered as a Lambda-backed
   * Athena data catalog and queried through Athena
   */
  CUSTOM_CONNECTOR: "CUSTOM_CONNECTOR",
  /**
   * Structured: a Databricks SQL Warehouse, reached through the connector
   * this service deploys and operates itself. Like CUSTOM_CONNECTOR it is a
   * Lambda-backed Athena data catalog, but the connector is ours rather than
   * the customer's: one Lambda per deployment serves every such source,
   * selecting each source's workspace and credential from the Athena catalog
   * name it is invoked under.
   */
  DATABRICKS_SQL_WAREHOUSE: "DATABRICKS_SQL_WAREHOUSE",
  /**
   * Structured: AWS Glue Data Catalog database
   */
  GLUE_DATABASE: "GLUE_DATABASE",
  /**
   * Structured: JDBC-connected relational database
   */
  JDBC_DATABASE: "JDBC_DATABASE",
  /**
   * Unstructured: direct file upload
   */
  LOCAL_UPLOAD: "LOCAL_UPLOAD",
  /**
   * Structured: an RDF graph store queried natively over SPARQL 1.1 (e.g.
   * Amazon Neptune). NL→SPARQL executes directly against the source endpoint;
   * no Glue catalog and no schema scan — the ontology is imported separately.
   * The engine is `SparqlConfiguration.store`, not a further sub-type.
   */
  RDF_SPARQL: "RDF_SPARQL",
  /**
   * Unstructured: S3 bucket prefix
   */
  S3: "S3",
} as const;
/**
 * @public
 */
export type SourceSubType = (typeof SourceSubType)[keyof typeof SourceSubType];

/**
 * @public
 * @enum
 */
export const SourceScanJobStatus = {
  /**
   * Scan job was cancelled.
   */
  CANCELLED: "CANCELLED",
  /**
   * Scan job completed successfully.
   */
  COMPLETED: "COMPLETED",
  /**
   * Scan job is discovering tables and schema.
   */
  DISCOVERING: "DISCOVERING",
  /**
   * Scan job is enriching metadata.
   */
  ENRICHING: "ENRICHING",
  /**
   * Scan job failed.
   */
  FAILED: "FAILED",
  /**
   * Scan job is running.
   */
  IN_PROGRESS: "IN_PROGRESS",
} as const;
/**
 * @public
 */
export type SourceScanJobStatus = (typeof SourceScanJobStatus)[keyof typeof SourceScanJobStatus];

/**
 * @public
 * @enum
 */
export const ReviewStatus = {
  /**
   * Reviewed and approved.
   */
  APPROVED: "APPROVED",
  /**
   * Awaiting steward review.
   */
  PENDING_REVIEW: "PENDING_REVIEW",
  /**
   * Reviewed and rejected.
   */
  REJECTED: "REJECTED",
} as const;
/**
 * @public
 */
export type ReviewStatus = (typeof ReviewStatus)[keyof typeof ReviewStatus];

/**
 * @public
 * @enum
 */
export const RescanChangeKind = {
  /**
   * Primary key or foreign keys.
   */
  CONSTRAINT: "CONSTRAINT",
  /**
   * Source-derived comment on the table or column.
   */
  DESCRIPTION: "DESCRIPTION",
  /**
   * Column distinct-value sample. Reserved: sampled values are data churn
   * rather than a schema change, so the diff does not emit this today. Kept
   * for a planned re-induction signal.
   */
  SAMPLED_VALUES: "SAMPLED_VALUES",
  /**
   * Physical shape: data type, nullability, partition flag, storage format,
   * location, or partition keys.
   */
  SCHEMA: "SCHEMA",
} as const;
/**
 * @public
 */
export type RescanChangeKind = (typeof RescanChangeKind)[keyof typeof RescanChangeKind];

/**
 * @public
 * @enum
 */
export const RescanColumnChangeStatus = {
  /**
   * Present in the fresh scan, absent from the last approved scan.
   */
  ADDED: "added",
  /**
   * Present in both, but one or more source-owned fields differ.
   */
  MODIFIED: "modified",
  /**
   * Present in the last approved scan, gone from the source. Deleted on
   * approve unless the steward keeps it.
   */
  REMOVED: "removed",
} as const;
/**
 * @public
 */
export type RescanColumnChangeStatus = (typeof RescanColumnChangeStatus)[keyof typeof RescanColumnChangeStatus];

/**
 * @public
 * @enum
 */
export const ReviewDecision = {
  /**
   * Approve the metadata.
   */
  APPROVED: "APPROVED",
  /**
   * Reject the metadata.
   */
  REJECTED: "REJECTED",
} as const;
/**
 * @public
 */
export type ReviewDecision = (typeof ReviewDecision)[keyof typeof ReviewDecision];

/**
 * @public
 * @enum
 */
export const ScanJobEventType = {
  /**
   * A steward approve/reject decision (including re-scan approve/reject).
   */
  REVIEW: "REVIEW",
  /**
   * A discovery/enrichment scan of the source.
   */
  SCAN: "SCAN",
} as const;
/**
 * @public
 */
export type ScanJobEventType = (typeof ScanJobEventType)[keyof typeof ScanJobEventType];

/**
 * @public
 * @enum
 */
export const ScanTrigger = {
  /**
   * Rescan fired by a matched upstream event rule.
   */
  EVENT: "EVENT",
  /**
   * First scan, run when the source was connected.
   */
  INITIAL: "INITIAL",
  /**
   * User-initiated rescan (UI or API).
   */
  MANUAL: "MANUAL",
  /**
   * Rescan fired by a configured recurring schedule.
   */
  SCHEDULED: "SCHEDULED",
} as const;
/**
 * @public
 */
export type ScanTrigger = (typeof ScanTrigger)[keyof typeof ScanTrigger];
