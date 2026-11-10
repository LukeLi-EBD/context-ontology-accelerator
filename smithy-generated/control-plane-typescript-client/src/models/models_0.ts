// smithy-typescript generated code
import type { DocumentType as __DocumentType } from "@smithy/types";

import type {
  DatabaseEngine,
  DocumentStatus,
  ExportFormat,
  ExtractionMode,
  FactCandidateStatus,
  GlueExecutionEngine,
  GraphVertexKind,
  GroundingMode,
  ImportJobStatus,
  IncludeMode,
  InductionJobStatus,
  InductionSourceType,
  InductionStrategy,
  IngestJobState,
  MatchType,
  NamespaceStatus,
  OntologyFileFormat,
  OntologyType,
  PreprocessingIssueType,
  PrincipalType,
  ProposalStatus,
  ProposalValidationJobStatus,
  ProposalValidationSeverity,
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
  SqlDialect,
  TimeGrain,
  VkgHealthStatus,
  WarningSeverity,
} from "./enums";

/**
 * Health of the ontology-induction subsystem's dependencies: the graph store (Neptune Analytics),
 * vector store (OpenSearch), Bedrock embeddings backend, and description LLM (Bedrock Converse).
 * @public
 */
export interface OntologyInductionHealth {
  /**
   * Graph store (Neptune Analytics) status
   * @public
   */
  graphStore?: string | undefined;

  /**
   * Vector store (OpenSearch) status
   * @public
   */
  vectorStore?: string | undefined;

  /**
   * Bedrock embeddings backend status
   * @public
   */
  bedrockEmbeddings?: string | undefined;

  /**
   * Description LLM (Bedrock Converse) status
   * @public
   */
  descriptionLlm?: string | undefined;
}

/**
 * @public
 */
export interface GetSystemHealthOutput {
  /**
   * Overall system status: "ok" or "degraded"
   * @public
   */
  status: string | undefined;

  /**
   * Ontology induction subsystem health (graph store, vector store, Bedrock)
   * @public
   */
  ontologyInduction?: OntologyInductionHealth | undefined;

  /**
   * DynamoDB sources table status
   * @public
   */
  dynamodb?: string | undefined;

  /**
   * Neptune KG (GraphRAG) status
   * @public
   */
  neptuneKg?: string | undefined;

  /**
   * OpenSearch Serverless collection status
   * @public
   */
  opensearch?: string | undefined;
}

/**
 * @public
 */
export interface HealthCheckOutput {
  /**
   * Liveness status; "ok" when the service is up.
   * @public
   */
  status: string | undefined;
}

/**
 * @public
 */
export interface ApproveFactCandidateInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  candidateId: string | undefined;

  /**
   * Identity of the approving principal; defaults to the caller.
   * @public
   */
  actor?: string | undefined;

  /**
   * Values overriding the extracted subject/predicate/object.
   * @public
   */
  factOverrides?: Record<string, string> | undefined;
}

/**
 * @public
 */
export interface ApproveFactCandidateOutput {
  /**
   * Identifier of the written fact.
   * @public
   */
  factId: string | undefined;

  /**
   * Candidate status after the call (`APPROVED`).
   * @public
   */
  status: FactCandidateStatus | undefined;
}

/**
 * @public
 */
export interface ListDocumentChunksInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Document whose chunks to list.
   * @public
   */
  documentId: string | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum chunks per page (default and maximum 200).
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * One text chunk of a document.
 * @public
 */
export interface DocumentChunk {
  /**
   * Identifier of the chunk; also the entity URI suffix used by its embedding.
   * @public
   */
  chunkId: string | undefined;

  /**
   * 1-based page number the chunk came from (1 for plain-text sources).
   * @public
   */
  page: number | undefined;

  /**
   * Chunk text exactly as indexed.
   * @public
   */
  text: string | undefined;

  /**
   * Inclusive character offset of the chunk in the normalised document text.
   * @public
   */
  charStart: number | undefined;

  /**
   * Exclusive character offset of the chunk in the normalised document text.
   * @public
   */
  charEnd: number | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListDocumentChunksOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Page of chunks, ordered by `charStart`.
   * @public
   */
  items: DocumentChunk[] | undefined;
}

/**
 * @public
 */
export interface ListDocumentsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Optional lifecycle-status filter.
   * @public
   */
  status?: DocumentStatus | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum documents per page (default and maximum 100).
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * One document in the namespace's ingestion registry.
 * @public
 */
export interface DocumentSummary {
  /**
   * Identifier assigned by UploadDocument.
   * @public
   */
  documentId: string | undefined;

  /**
   * Display title (caller-supplied, else the filename).
   * @public
   */
  title: string | undefined;

  /**
   * Current lifecycle status.
   * @public
   */
  status: DocumentStatus | undefined;

  /**
   * Number of chunks written for this document.
   * @public
   */
  chunkCount: number | undefined;

  /**
   * Timestamp of the last status change (RFC 3339).
   *
   * Declared as a string, like the other summary types in this service, so
   * the wire value is the stored RFC 3339 text rather than an epoch number.
   * @public
   */
  updatedAt: string | undefined;

  /**
   * Why ingestion failed. Present only when `status` is `FAILED`.
   * @public
   */
  errorMessage?: string | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListDocumentsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Page of document summaries.
   * @public
   */
  items: DocumentSummary[] | undefined;
}

/**
 * @public
 */
export interface ListFactCandidatesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Only candidates extracted from this document.
   * @public
   */
  documentId?: string | undefined;

  /**
   * Only candidates in this review status (default: all).
   * @public
   */
  status?: FactCandidateStatus | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum candidates per page (default and maximum 200).
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * One subject-predicate-object candidate extracted from a document chunk.
 * @public
 */
export interface FactCandidate {
  /**
   * Identifier assigned at extraction time.
   * @public
   */
  candidateId: string | undefined;

  /**
   * Subject IRI or literal label as extracted.
   * @public
   */
  subject: string | undefined;

  /**
   * Predicate IRI or label as extracted.
   * @public
   */
  predicate: string | undefined;

  /**
   * Object IRI or literal label as extracted.
   * @public
   */
  object: string | undefined;

  /**
   * Extractor confidence in [0, 1].
   * @public
   */
  confidence: number | undefined;

  /**
   * Review status.
   * @public
   */
  status: FactCandidateStatus | undefined;

  /**
   * Document the candidate was extracted from.
   * @public
   */
  documentId?: string | undefined;

  /**
   * Chunk the candidate was extracted from.
   * @public
   */
  chunkId?: string | undefined;

  /**
   * Source sentence the candidate was extracted from.
   * @public
   */
  evidence?: string | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListFactCandidatesOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Page of candidates, newest first.
   * @public
   */
  items: FactCandidate[] | undefined;
}

/**
 * @public
 */
export interface RejectFactCandidateInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  candidateId: string | undefined;

  /**
   * Identity of the rejecting principal; defaults to the caller.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the candidate was rejected.
   * @public
   */
  reason: string | undefined;
}

/**
 * @public
 */
export interface RejectFactCandidateOutput {
  /**
   * Candidate status after the call (`REJECTED`).
   * @public
   */
  status: FactCandidateStatus | undefined;
}

/**
 * @public
 */
export interface UploadDocumentInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Original filename, including extension.
   * @public
   */
  filename: string | undefined;

  /**
   * MIME type of the uploaded bytes, e.g. `text/plain`.
   * @public
   */
  contentType: string | undefined;

  /**
   * Base64-encoded document content.
   * @public
   */
  contentBase64?: string | undefined;

  /**
   * SHA-256 of the content (lowercase hex). Optional when
   * `contentBase64` is supplied — if present it must match the decoded
   * bytes, and is rejected rather than ignored when it does not.
   * @public
   */
  contentSha256?: string | undefined;

  /**
   * Display title; defaults to `filename`.
   * @public
   */
  title?: string | undefined;

  /**
   * Caller metadata stored on the document row.
   * @public
   */
  metadata?: Record<string, string> | undefined;
}

/**
 * @public
 */
export interface UploadDocumentOutput {
  /**
   * Identifier of the stored document.
   * @public
   */
  documentId: string | undefined;

  /**
   * Document version (1 for the first upload of these bytes).
   * @public
   */
  version: number | undefined;

  /**
   * SHA-256 of the stored bytes, lowercase hex.
   * @public
   */
  contentHash: string | undefined;

  /**
   * Lifecycle status at response time (`UPLOADED` or `PROCESSING`).
   * @public
   */
  status: DocumentStatus | undefined;
}

/**
 * One stored embedding, vector included.
 *
 * Member names mirror the engine's snake_case JSON through `@jsonName`; the
 * camelCase names here are the contract's own spelling.
 * @public
 */
export interface EmbeddingRecord {
  /**
   * Row identity. Empty for k-NN hits, which carry no stable external id.
   * @public
   */
  id: string | undefined;

  /**
   * Ontology (or A-Box/namespace) the vector belongs to.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * URI of the embedded entity.
   * @public
   */
  entityUri: string | undefined;

  /**
   * Entity type the row was written for.
   * @public
   */
  entityType: string | undefined;

  /**
   * Kind of vector in this row.
   * @public
   */
  embeddingType: string | undefined;

  /**
   * Model that produced the vector.
   * @public
   */
  modelId: string | undefined;

  /**
   * Vector length.
   * @public
   */
  dimensions: number | undefined;

  /**
   * Source text, when the row was written from text (chunk rows carry it).
   * @public
   */
  text?: string | undefined;

  /**
   * Row creation timestamp (RFC 3339); empty for k-NN hits.
   * @public
   */
  createdAt?: string | undefined;

  /**
   * Provenance metadata, e.g. chunk/document ids for chunk vectors.
   * @public
   */
  metadata?: __DocumentType | undefined;

  /**
   * The raw vector.
   * @public
   */
  vector: number[] | undefined;
}

/**
 * Envelope for the embedding reads. The engine returns a bare array; the
 * gateway wraps it in this structure to give the contract a typed output.
 * @public
 */
export interface EmbeddingListOutput {
  /**
   * Matching embedding rows.
   * @public
   */
  embeddings: EmbeddingRecord[] | undefined;
}

/**
 * @public
 */
export interface GetEntityEmbeddingsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Entity URI whose vectors to read.
   * @public
   */
  entityUri: string | undefined;

  /**
   * Only rows written for this entity type.
   * @public
   */
  entityType?: string | undefined;

  /**
   * Only rows of this vector kind.
   * @public
   */
  embeddingType?: string | undefined;

  /**
   * Only rows produced by this model.
   * @public
   */
  modelId?: string | undefined;
}

/**
 * @public
 */
export interface SearchEmbeddingsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Query vector. Must have the same dimensionality as the stored rows.
   * @public
   */
  vector: number[] | undefined;

  /**
   * Restrict the search to this vector kind.
   * @public
   */
  embeddingType: string | undefined;

  /**
   * Restrict the search to vectors from this model.
   * @public
   */
  modelId: string | undefined;

  /**
   * Restrict the search to this entity type (engine default: `class`).
   * @public
   */
  entityType?: string | undefined;

  /**
   * Restrict the search to one ontology's named graph.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * Number of nearest rows to return (engine default: 10).
   * @public
   */
  topK?: number | undefined;
}

/**
 * The request body for creating a namespace-scoped grant, binding a principal to
 * a role and optionally scoping data access via a table allowlist, column denylist, and allowed-metrics list.
 * @public
 */
export interface CreateGrantRequest {
  /**
   * Whether the principal is a user, group, or agent.
   * @public
   */
  principalType: PrincipalType | undefined;

  /**
   * Identifier of the principal to bind to the role.
   * @public
   */
  principalId: string | undefined;

  /**
   * Name of the role to assign to the principal.
   * @public
   */
  role: string | undefined;

  /**
   * Optional list of tables to restrict data access to.
   * @public
   */
  tableAllowlist?: string[] | undefined;

  /**
   * Optional per-table columns to deny access to.
   * @public
   */
  columnDenylist?: Record<string, string[]> | undefined;

  /**
   * Optional list of metrics to permit access to.
   * @public
   */
  allowedMetrics?: string[] | undefined;

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
export interface CreateGrantInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * The request body for creating a namespace-scoped grant, binding a principal to
   * a role and optionally scoping data access via a table allowlist, column denylist, and allowed-metrics list.
   * @public
   */
  body: CreateGrantRequest | undefined;
}

/**
 * A namespace grant record returned in responses, describing the principal, the
 * role assigned to it, and any table allowlist, column denylist, or allowed-metrics scoping within the namespace.
 * @public
 */
export interface GrantSummary {
  /**
   * Unique identifier of the grant.
   * @public
   */
  grantId: string | undefined;

  /**
   * Identifier of the namespace the grant applies to.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Whether the principal is a user, group, or agent.
   * @public
   */
  principalType: PrincipalType | undefined;

  /**
   * Identifier of the principal the grant is bound to.
   * @public
   */
  principalId: string | undefined;

  /**
   * Name of the role assigned to the principal.
   * @public
   */
  role: string | undefined;

  /**
   * Identifier of the principal that created the grant.
   * @public
   */
  grantedBy: string | undefined;

  /**
   * Timestamp when the grant was created.
   * @public
   */
  grantedAt: string | undefined;

  /**
   * Optional list of tables the grant restricts data access to.
   * @public
   */
  tableAllowlist?: string[] | undefined;

  /**
   * Optional per-table columns the grant denies access to.
   * @public
   */
  columnDenylist?: Record<string, string[]> | undefined;

  /**
   * Optional list of metrics the grant permits access to.
   * @public
   */
  allowedMetrics?: string[] | undefined;
}

/**
 * @public
 */
export interface CreateGrantOutput {
  /**
   * A namespace grant record returned in responses, describing the principal, the
   * role assigned to it, and any table allowlist, column denylist, or allowed-metrics scoping within the namespace.
   * @public
   */
  grant: GrantSummary | undefined;
}

/**
 * The request body for creating a platform-scoped grant, binding a principal to a
 * platform role that applies across all namespaces.
 * @public
 */
export interface CreatePlatformGrantRequest {
  /**
   * Whether the principal is a user, group, or agent.
   * @public
   */
  principalType: PrincipalType | undefined;

  /**
   * Identifier of the principal to bind to the platform role.
   * @public
   */
  principalId: string | undefined;

  /**
   * Name of the platform role to assign to the principal.
   * @public
   */
  role: string | undefined;

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
export interface CreatePlatformGrantInput {
  /**
   * The request body for creating a platform-scoped grant, binding a principal to a
   * platform role that applies across all namespaces.
   * @public
   */
  body: CreatePlatformGrantRequest | undefined;
}

/**
 * A platform-scoped grant record returned in responses, binding a principal to a
 * platform role that applies across all namespaces (no namespaceId or per-namespace data-access scoping).
 * @public
 */
export interface PlatformGrantSummary {
  /**
   * Unique identifier of the platform grant.
   * @public
   */
  grantId: string | undefined;

  /**
   * Whether the principal is a user, group, or agent.
   * @public
   */
  principalType: PrincipalType | undefined;

  /**
   * Identifier of the principal the grant is bound to.
   * @public
   */
  principalId: string | undefined;

  /**
   * Name of the platform role assigned to the principal.
   * @public
   */
  role: string | undefined;

  /**
   * Identifier of the principal that created the grant.
   * @public
   */
  grantedBy: string | undefined;

  /**
   * Timestamp when the grant was created.
   * @public
   */
  grantedAt: string | undefined;
}

/**
 * @public
 */
export interface CreatePlatformGrantOutput {
  /**
   * A platform-scoped grant record returned in responses, binding a principal to a
   * platform role that applies across all namespaces (no namespaceId or per-namespace data-access scoping).
   * @public
   */
  grant: PlatformGrantSummary | undefined;
}

/**
 * @public
 */
export interface DeleteGrantInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the grant to revoke.
   * @public
   */
  grantId: string | undefined;
}

/**
 * @public
 */
export interface DeleteGrantOutput {}

/**
 * @public
 */
export interface DeletePlatformGrantInput {
  /**
   * Identifier of the platform grant to revoke.
   * @public
   */
  grantId: string | undefined;
}

/**
 * @public
 */
export interface DeletePlatformGrantOutput {}

/**
 * Standard pagination input
 * @public
 */
export interface ListNamespaceGrantsInput {
  /**
   * Pagination cursor from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of grants to return per page.
   * @public
   */
  maxResults?: number | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Optional principal identifier to filter the grants by.
   * @public
   */
  principal?: string | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListNamespaceGrantsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * The page of namespace grants.
   * @public
   */
  grants: GrantSummary[] | undefined;
}

/**
 * Standard pagination input
 * @public
 */
export interface ListPlatformGrantsInput {
  /**
   * Pagination cursor from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of grants to return per page.
   * @public
   */
  maxResults?: number | undefined;

  /**
   * Optional principal identifier to filter the grants by.
   * @public
   */
  principal?: string | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListPlatformGrantsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * The page of platform grants.
   * @public
   */
  grants: PlatformGrantSummary[] | undefined;
}

/**
 * @public
 */
export interface ListPrincipalGrantsInput {
  /**
   * Identifier of the principal whose grants to list (`me`).
   * @public
   */
  principalId: string | undefined;

  /**
   * Pagination cursor from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of grants to return per page (default 1000).
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListPrincipalGrantsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * The page of namespace grants held by the principal.
   * @public
   */
  grants: GrantSummary[] | undefined;
}

/**
 * Filter criteria selecting which metrics a bulk delete should remove.
 * @public
 */
export interface BulkDeleteFilter {
  /**
   * Delete all metrics with this data source ID.
   * @public
   */
  dataSourceId?: string | undefined;

  /**
   * Delete all metrics with this source table.
   * @public
   */
  sourceTable?: string | undefined;

  /**
   * Delete all metrics whose name matches this prefix.
   * @public
   */
  namePrefix?: string | undefined;
}

/**
 * @public
 */
export interface BulkDeleteMetricsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Explicit list of metric names to delete. Mutually exclusive with filter.
   * @public
   */
  names?: string[] | undefined;

  /**
   * Filter criteria — deletes all metrics matching the filter.
   * Mutually exclusive with names.
   * @public
   */
  filter?: BulkDeleteFilter | undefined;

  /**
   * Delete every metric in the namespace (used by namespace deletion).
   * Mutually exclusive with names and filter.
   * @public
   */
  deleteAll?: boolean | undefined;
}

/**
 * @public
 */
export interface BulkDeleteMetricsOutput {
  /**
   * Number of metrics deleted.
   * @public
   */
  deleted: number | undefined;

  /**
   * Metric names that were not found (from names list).
   * @public
   */
  notFound?: string[] | undefined;
}

/**
 * AI context for metric discoverability.
 * @public
 */
export interface MetricAiContext {
  /**
   * Alternative names the metric may be referred to by.
   * @public
   */
  synonyms?: string[] | undefined;

  /**
   * Free-text guidance for how to use or interpret the metric.
   * @public
   */
  instructions?: string | undefined;

  /**
   * Example questions or usages illustrating the metric.
   * @public
   */
  examples?: string[] | undefined;
}

/**
 * A single dialect + expression pair.
 * @public
 */
export interface MetricDialect {
  /**
   * SQL dialect identifier.
   * @public
   */
  dialect: SqlDialect | undefined;

  /**
   * SQL expression. Must be a full SELECT statement (or set operation) —
   * e.g. "SELECT COUNT(*) AS total FROM orders". Bare aggregate fragments
   * like "COUNT(*)" are rejected: the serve-time SQL firewall only executes
   * top-level SELECT statements, and onboarding validates the same shape.
   * @public
   */
  expression: string | undefined;
}

/**
 * Expression container with multi-dialect support.
 * @public
 */
export interface MetricExpression {
  /**
   * Per-dialect SQL expressions for the metric.
   * @public
   */
  dialects: MetricDialect[] | undefined;
}

/**
 * @public
 */
export interface CreateMetricInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Metric name: alphanumeric + underscores, 1-128 chars.
   * @public
   */
  name: string | undefined;

  /**
   * Display-only label for the metric. Omit (or send null) for no label.
   * @public
   */
  label?: string | undefined;

  /**
   * Human-readable description of what the metric measures.
   * @public
   */
  description: string | undefined;

  /**
   * Expression container with multi-dialect support.
   * @public
   */
  expression: MetricExpression | undefined;

  /**
   * Data source identifier reference.
   * @public
   */
  dataSourceId: string | undefined;

  /**
   * Source table name reference.
   * @public
   */
  sourceTable: string | undefined;

  /**
   * Default time aggregation granularity for a metric.
   * @public
   */
  defaultTimeGrain?: TimeGrain | undefined;

  /**
   * Unit of measure for the metric value (e.g. "USD", "count").
   * @public
   */
  unit?: string | undefined;

  /**
   * Data type of the value the metric returns (e.g. "integer", "decimal").
   * @public
   */
  returnType?: string | undefined;

  /**
   * AI context for metric discoverability.
   * @public
   */
  aiContext?: MetricAiContext | undefined;

  /**
   * Ontology concept URIs this metric is associated with.
   * @public
   */
  ontologyConcepts?: string[] | undefined;

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
 * Full metric definition.
 * @public
 */
export interface MetricDefinition {
  /**
   * Server-assigned unique identifier.
   * @public
   */
  metricId?: string | undefined;

  /**
   * Namespace this metric belongs to.
   * @public
   */
  namespaceId?: string | undefined;

  /**
   * Metric name: alphanumeric + underscores, 1-128 chars.
   * @public
   */
  name: string | undefined;

  /**
   * Display-only label for the metric. Absent when the metric has none.
   * @public
   */
  label?: string | undefined;

  /**
   * Human-readable description of what the metric measures.
   * @public
   */
  description: string | undefined;

  /**
   * Expression container with multi-dialect support.
   * @public
   */
  expression: MetricExpression | undefined;

  /**
   * Data source identifier reference.
   * @public
   */
  dataSourceId: string | undefined;

  /**
   * Source table name reference.
   * @public
   */
  sourceTable: string | undefined;

  /**
   * Default time aggregation granularity for a metric.
   * @public
   */
  defaultTimeGrain?: TimeGrain | undefined;

  /**
   * Unit of measure for the metric value (e.g. "USD", "count").
   * @public
   */
  unit?: string | undefined;

  /**
   * Data type of the value the metric returns (e.g. "integer", "decimal").
   * @public
   */
  returnType?: string | undefined;

  /**
   * AI context for metric discoverability.
   * @public
   */
  aiContext?: MetricAiContext | undefined;

  /**
   * Ontology concept URIs this metric is associated with.
   * @public
   */
  ontologyConcepts?: string[] | undefined;

  /**
   * Set by server — principal who created/updated the metric.
   * @public
   */
  definedBy?: string | undefined;

  /**
   * Set by server — date the metric became effective.
   * @public
   */
  effectiveFrom?: string | undefined;

  /**
   * COA-private provenance: business domain. Absent means unknown.
   * Not an OSI standard field; migrate when OSI standardises an equivalent.
   * @public
   */
  domain?: string | undefined;

  /**
   * COA-private provenance: evidence basis. Absent means unknown.
   * Not an OSI standard field; migrate when OSI standardises an equivalent.
   * @public
   */
  evidenceBasis?: string | undefined;

  /**
   * COA-private provenance: publishable. Absent means unknown; an explicit
   * false is "not publishable", not a missing value.
   * Not an OSI standard field; migrate when OSI standardises an equivalent.
   * @public
   */
  publishable?: boolean | undefined;
}

/**
 * Validation warning returned alongside successful create/update.
 * @public
 */
export interface ValidationWarning {
  /**
   * Name of the field the warning applies to.
   * @public
   */
  field: string | undefined;

  /**
   * Human-readable description of the warning.
   * @public
   */
  message: string | undefined;

  /**
   * Severity level attached to a validation warning.
   * @public
   */
  severity: WarningSeverity | undefined;
}

/**
 * Result of creating a metric, including the persisted definition and any warnings.
 * @public
 */
export interface CreateMetricOutput {
  /**
   * Full metric definition.
   * @public
   */
  metric: MetricDefinition | undefined;

  /**
   * Non-fatal validation warnings raised during creation.
   * @public
   */
  warnings?: ValidationWarning[] | undefined;
}

/**
 * @public
 */
export interface DeleteMetricInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Metric name: alphanumeric + underscores, 1-128 chars.
   * @public
   */
  name: string | undefined;
}

/**
 * @public
 */
export interface ExportOsiInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Response format: "inline" (default) returns content in body,
   * "s3" writes to S3 and returns a pre-signed download URL.
   * @public
   */
  format?: ExportFormat | undefined;

  /**
   * Optional subset of metric names to export (repeated query param,
   * e.g. ?names=a&names=b). Omit to export every metric in the
   * namespace (default, unchanged behavior).
   * @public
   */
  names?: string[] | undefined;
}

/**
 * Result of an OSI export, either inline YAML content or a pre-signed download URL.
 * @public
 */
export interface ExportOsiOutput {
  /**
   * OSI YAML content (populated when format=inline or omitted).
   * @public
   */
  content?: string | undefined;

  /**
   * Pre-signed S3 GET URL for downloading the export (populated when format=s3).
   * @public
   */
  downloadUrl?: string | undefined;

  /**
   * Seconds until the download URL expires (populated when format=s3).
   * @public
   */
  expiresIn?: number | undefined;
}

/**
 * @public
 */
export interface GetImportJobInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the async import job to poll.
   * @public
   */
  jobId: string | undefined;
}

/**
 * Current status and progress counters for an asynchronous OSI import job.
 * @public
 */
export interface ImportJobOutput {
  /**
   * Identifier of the import job.
   * @public
   */
  jobId: string | undefined;

  /**
   * Status of an asynchronous import job.
   * @public
   */
  status: ImportJobStatus | undefined;

  /**
   * Total number of metrics in the import.
   * @public
   */
  metricsTotal: number | undefined;

  /**
   * Number of metrics processed so far.
   * @public
   */
  metricsProcessed: number | undefined;

  /**
   * Number of new metrics created so far.
   * @public
   */
  metricsCreated: number | undefined;

  /**
   * Number of existing metrics updated so far.
   * @public
   */
  metricsUpdated: number | undefined;

  /**
   * Fatal errors encountered during the import.
   * @public
   */
  errors?: string[] | undefined;

  /**
   * Non-fatal warnings raised during the import.
   * @public
   */
  warnings?: string[] | undefined;
}

/**
 * @public
 */
export interface GetMetricInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Metric name: alphanumeric + underscores, 1-128 chars.
   * @public
   */
  name: string | undefined;
}

/**
 * Result of retrieving a single metric definition.
 * @public
 */
export interface GetMetricOutput {
  /**
   * Full metric definition.
   * @public
   */
  metric: MetricDefinition | undefined;
}

/**
 * @public
 */
export interface GetOsiUploadUrlInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Original filename (used for content-type validation).
   * @public
   */
  filename: string | undefined;
}

/**
 * @public
 */
export interface GetOsiUploadUrlOutput {
  /**
   * Pre-signed S3 PUT URL. Upload the YAML file here with Content-Type: application/x-yaml.
   * @public
   */
  uploadUrl: string | undefined;

  /**
   * S3 key to pass to ImportOsi after upload completes.
   * @public
   */
  s3Key: string | undefined;

  /**
   * Seconds until the pre-signed URL expires.
   * @public
   */
  expiresIn: number | undefined;
}

/**
 * @public
 */
export interface ImportOsiInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * OSI YAML content as a string (inline). Mutually exclusive with s3Key.
   * Maximum 5MB for inline content; use GetOsiUploadUrl + s3Key for larger files.
   * @public
   */
  content?: string | undefined;

  /**
   * S3 object key containing the OSI YAML (for large files uploaded via GetOsiUploadUrl).
   * Mutually exclusive with content.
   * @public
   */
  s3Key?: string | undefined;

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
 * Result of an OSI import, summarizing resolved datasets and metric changes.
 * @public
 */
export interface ImportOsiOutput {
  /**
   * Number of datasets resolved from the OSI document.
   * @public
   */
  datasetsResolved: number | undefined;

  /**
   * Number of new metrics created by the import.
   * @public
   */
  metricsCreated: number | undefined;

  /**
   * Number of existing metrics updated by the import.
   * @public
   */
  metricsUpdated: number | undefined;

  /**
   * Non-fatal warnings raised during the import.
   * @public
   */
  warnings?: string[] | undefined;

  /**
   * Present when the import is processed asynchronously (metric count > threshold).
   * Poll GetImportJob with this ID to track progress.
   * @public
   */
  jobId?: string | undefined;

  /**
   * Import job status. "COMPLETED" for sync imports, "IN_PROGRESS" for async.
   * @public
   */
  status?: ImportJobStatus | undefined;
}

/**
 * Standard pagination input
 * @public
 */
export interface ListMetricsInput {
  /**
   * Pagination token from a previous response; omit for the first page.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of metrics to return in one page. For compatibility
   * with existing callers that page with larger values, the server
   * reduces a value above 200 to 200 rather than rejecting it.
   * @public
   */
  maxResults?: number | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Data source identifier reference.
   * @public
   */
  dataSourceId?: string | undefined;

  /**
   * Source table name reference.
   * @public
   */
  sourceTable?: string | undefined;
}

/**
 * Paginated list of metric definitions.
 * @public
 */
export interface ListMetricsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Metric definitions matching the request.
   * @public
   */
  metrics: MetricDefinition[] | undefined;
}

/**
 * @public
 */
export interface UpdateMetricInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Metric name: alphanumeric + underscores, 1-128 chars.
   * @public
   */
  name: string | undefined;

  /**
   * Display-only label for the metric. This is a full replace: omitting it
   * (or sending null) clears an existing label.
   * @public
   */
  label?: string | undefined;

  /**
   * Human-readable description of what the metric measures.
   * @public
   */
  description: string | undefined;

  /**
   * Expression container with multi-dialect support.
   * @public
   */
  expression: MetricExpression | undefined;

  /**
   * Data source identifier reference.
   * @public
   */
  dataSourceId: string | undefined;

  /**
   * Source table name reference.
   * @public
   */
  sourceTable: string | undefined;

  /**
   * Default time aggregation granularity for a metric.
   * @public
   */
  defaultTimeGrain?: TimeGrain | undefined;

  /**
   * Unit of measure for the metric value (e.g. "USD", "count").
   * @public
   */
  unit?: string | undefined;

  /**
   * Data type of the value the metric returns (e.g. "integer", "decimal").
   * @public
   */
  returnType?: string | undefined;

  /**
   * AI context for metric discoverability.
   * @public
   */
  aiContext?: MetricAiContext | undefined;

  /**
   * Ontology concept URIs this metric is associated with.
   * @public
   */
  ontologyConcepts?: string[] | undefined;
}

/**
 * Result of updating a metric, including the updated definition and any warnings.
 * @public
 */
export interface UpdateMetricOutput {
  /**
   * Full metric definition.
   * @public
   */
  metric: MetricDefinition | undefined;

  /**
   * Non-fatal validation warnings raised during the update.
   * @public
   */
  warnings?: ValidationWarning[] | undefined;
}

/**
 * @public
 */
export interface ValidateMetricInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Metric name: alphanumeric + underscores, 1-128 chars.
   * @public
   */
  name: string | undefined;

  /**
   * Display-only label for the metric. Omit (or send null) for no label.
   * @public
   */
  label?: string | undefined;

  /**
   * Human-readable description of what the metric measures.
   * @public
   */
  description: string | undefined;

  /**
   * Expression container with multi-dialect support.
   * @public
   */
  expression: MetricExpression | undefined;

  /**
   * Data source identifier reference.
   * @public
   */
  dataSourceId: string | undefined;

  /**
   * Source table name reference.
   * @public
   */
  sourceTable: string | undefined;

  /**
   * Default time aggregation granularity for a metric.
   * @public
   */
  defaultTimeGrain?: TimeGrain | undefined;

  /**
   * Unit of measure for the metric value (e.g. "USD", "count").
   * @public
   */
  unit?: string | undefined;

  /**
   * Data type of the value the metric returns (e.g. "integer", "decimal").
   * @public
   */
  returnType?: string | undefined;

  /**
   * AI context for metric discoverability.
   * @public
   */
  aiContext?: MetricAiContext | undefined;

  /**
   * Ontology concept URIs this metric is associated with.
   * @public
   */
  ontologyConcepts?: string[] | undefined;
}

/**
 * Result of validating a metric definition, listing blocking and advisory findings.
 * @public
 */
export interface ValidateMetricOutput {
  /**
   * Validation findings. Severity ERROR predicts create/update rejection;
   * INFO is advisory.
   * @public
   */
  warnings: ValidationWarning[] | undefined;
}

/**
 * @public
 */
export interface CreateNamespaceInput {
  /**
   * Namespace name: 3-64 lowercase alphanumeric or hyphens, must start/end with alphanumeric.
   * @public
   */
  name: string | undefined;

  /**
   * Display name for a namespace. Angle brackets and control characters are rejected.
   * @public
   */
  displayName?: string | undefined;

  /**
   * Namespace description. Angle brackets and control characters other than
   * tab and newline are rejected.
   * @public
   */
  description?: string | undefined;

  /**
   * Owner email address. The local part allows the RFC 5322 atext characters
   * except # | and backtick (the owner also becomes a grant principalId).
   * Personal information, so marked sensitive to keep it out of
   * generated-client logs.
   * @public
   */
  owner: string | undefined;

  /**
   * Language of the sources, ontology and knowledge graph this
   * namespace will hold. Defaults to `en` when omitted. Cannot be
   * changed after creation.
   * @public
   */
  language?: string | undefined;

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
 * Full detail view of a namespace, including owner, description, and system-managed fields.
 * @public
 */
export interface NamespaceDetail {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Namespace name: 3-64 lowercase alphanumeric or hyphens, must start/end with alphanumeric.
   * @public
   */
  name: string | undefined;

  /**
   * Display name for a namespace. Angle brackets and control characters are rejected.
   * @public
   */
  displayName?: string | undefined;

  /**
   * Namespace description. Angle brackets and control characters other than
   * tab and newline are rejected.
   * @public
   */
  description?: string | undefined;

  /**
   * Owner email address. The local part allows the RFC 5322 atext characters
   * except # | and backtick (the owner also becomes a grant principalId).
   * Personal information, so marked sensitive to keep it out of
   * generated-client logs.
   * @public
   */
  owner: string | undefined;

  /**
   * Lifecycle state of a namespace, from active use through the asynchronous deletion pipeline.
   * @public
   */
  status: NamespaceStatus | undefined;

  /**
   * Immutable namespace language (canonical BCP 47 tag), set at creation.
   * Namespaces created before the language field existed report `en`.
   * @public
   */
  language: string | undefined;

  /**
   * Amazon DataZone project ID linked to this namespace, when applicable.
   * @public
   */
  dataZoneProjectId?: string | undefined;

  /**
   * Number of data sources registered in the namespace.
   * @public
   */
  sourceCount?: number | undefined;

  /**
   * Creation timestamp (RFC 3339).
   * @public
   */
  createdAt: string | undefined;

  /**
   * Last-update timestamp (RFC 3339).
   * @public
   */
  updatedAt?: string | undefined;

  /**
   * Name of the Athena workgroup created for this namespace
   * (read-only, system-managed). Use this workgroup when querying
   * data sources via Athena federation. Format: `\{resource-prefix\}\{namespaceId\}`.
   * Null when workgroup provisioning could not be confirmed
   * (e.g., SSM parameter missing) — in that case Athena queries
   * against this namespace's federated catalogs are not yet supported
   * and a re-creation is required to enable them.
   * @public
   */
  athenaWorkgroupName?: string | undefined;

  /**
   * STS ExternalId the platform presents when assuming a cross-account role
   * onboarded into this namespace (read-only, system-derived). Format:
   * `\{resource-prefix\}\{namespaceId\}`, the same scheme as
   * `athenaWorkgroupName`.
   *
   * Any role supplied as `crossAccountRoleArn` MUST condition its trust policy
   * on this exact value (`sts:ExternalId`). The platform derives it server-side
   * and refuses to assume a role without presenting one, so this is what stops
   * a caller in one namespace from pointing a source at a role onboarded for
   * another. Surface it wherever a cross-account role is configured.
   * @public
   */
  datasourceExternalId?: string | undefined;

  /**
   * Health of this namespace's VKG translation service (read-time).
   * @public
   */
  vkgHealth?: VkgHealthStatus | undefined;

  /**
   * Human-readable explanation for a non-HEALTHY vkgHealth, when known
   * (e.g. "container health check failing", "no running task"). Absent when
   * HEALTHY. Coarse by design — the precise container-side cause is in the
   * VKG service /health response and its CloudWatch logs.
   * @public
   */
  vkgHealthReason?: string | undefined;
}

/**
 * Output of CreateNamespace, wrapping the newly created namespace detail.
 * @public
 */
export interface CreateNamespaceOutput {
  /**
   * Full detail view of a namespace, including owner, description, and system-managed fields.
   * @public
   */
  namespace: NamespaceDetail | undefined;
}

/**
 * @public
 */
export interface DeleteNamespaceInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;
}

/**
 * @public
 */
export interface DeleteNamespaceOutput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Lifecycle state of a namespace, from active use through the asynchronous deletion pipeline.
   * @public
   */
  status: NamespaceStatus | undefined;
}

/**
 * @public
 */
export interface GetNamespaceInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;
}

/**
 * Output of GetNamespace, wrapping the requested namespace detail.
 * @public
 */
export interface GetNamespaceOutput {
  /**
   * Full detail view of a namespace, including owner, description, and system-managed fields.
   * @public
   */
  namespace: NamespaceDetail | undefined;
}

/**
 * Standard pagination input
 * @public
 */
export interface ListNamespacesInput {
  /**
   * Opaque token from a prior response; pass it to fetch the next page.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of namespaces to return in a single page.
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * Condensed view of a namespace as returned in list responses.
 * @public
 */
export interface NamespaceSummary {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Namespace name: 3-64 lowercase alphanumeric or hyphens, must start/end with alphanumeric.
   * @public
   */
  name: string | undefined;

  /**
   * Display name for a namespace. Angle brackets and control characters are rejected.
   * @public
   */
  displayName?: string | undefined;

  /**
   * Lifecycle state of a namespace, from active use through the asynchronous deletion pipeline.
   * @public
   */
  status: NamespaceStatus | undefined;

  /**
   * Immutable namespace language (canonical BCP 47 tag). Namespaces created
   * before the language field existed report `en`.
   * @public
   */
  language: string | undefined;

  /**
   * Number of data sources registered in the namespace.
   * @public
   */
  sourceCount?: number | undefined;

  /**
   * Creation timestamp (RFC 3339).
   * @public
   */
  createdAt?: string | undefined;

  /**
   * Last-update timestamp (RFC 3339).
   * @public
   */
  updatedAt?: string | undefined;
}

/**
 * Output of ListNamespaces: a page of namespace summaries plus an optional pagination token.
 * @public
 */
export interface ListNamespacesOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * The page of namespace summaries.
   * @public
   */
  namespaces: NamespaceSummary[] | undefined;
}

/**
 * @public
 */
export interface UpdateNamespaceInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * New human-readable display name for the namespace. An empty string
   * clears it (the edit form sends "" for a cleared field).
   * @public
   */
  displayName?: string | undefined;

  /**
   * New description for the namespace. An empty string clears it.
   * @public
   */
  description?: string | undefined;
}

/**
 * Output of UpdateNamespace, wrapping the updated namespace detail.
 * @public
 */
export interface UpdateNamespaceOutput {
  /**
   * Full detail view of a namespace, including owner, description, and system-managed fields.
   * @public
   */
  namespace: NamespaceDetail | undefined;
}

/**
 * @public
 */
export interface UpdateNamespaceStatusInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Lifecycle state of a namespace, from active use through the asynchronous deletion pipeline.
   * @public
   */
  status: NamespaceStatus | undefined;
}

/**
 * Output of UpdateNamespaceStatus, wrapping the namespace detail with its new status.
 * @public
 */
export interface UpdateNamespaceStatusOutput {
  /**
   * Full detail view of a namespace, including owner, description, and system-managed fields.
   * @public
   */
  namespace: NamespaceDetail | undefined;
}

/**
 * @public
 */
export interface DeleteOntologyInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Full IRI of the ontology to delete (passed as a query parameter).
   * @public
   */
  ontologyId: string | undefined;
}

/**
 * @public
 */
export interface DownloadOntologyInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the ontology to download.
   * @public
   */
  ontologyId: string | undefined;
}

/**
 * @public
 */
export interface DownloadOntologyOutput {
  /**
   * Presigned S3 GET URL for the ontology serialized as Turtle. The
   * ontology is written to the artifacts bucket and served out-of-band
   * rather than inlined, because a large induced ontology (6+ MB) would
   * exceed the API Gateway / Lambda response limit and 502 the call.
   * @public
   */
  downloadUrl: string | undefined;

  /**
   * Seconds until the presigned URL expires.
   * @public
   */
  expiresInSeconds?: number | undefined;
}

/**
 * @public
 */
export interface FetchOntologyInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier to register the fetched ontology under.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Source URL to fetch the ontology from. HTTPS only.
   * @public
   */
  sourceUrl?: string | undefined;
}

/**
 * @public
 */
export interface FetchOntologyOutput {
  /**
   * Result of the fetch-and-ingest operation.
   * @public
   */
  result: __DocumentType | undefined;
}

/**
 * @public
 */
export interface GetGraphClassInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * IRI of the class vertex to look up.
   * @public
   */
  uri: string | undefined;
}

/**
 * A neighboring vertex reached by traversing an edge, identified by its IRI,
 * label, and kind.
 * @public
 */
export interface GraphNeighbor {
  /**
   * IRI of the neighboring vertex.
   * @public
   */
  uri: string | undefined;

  /**
   * Human-readable label of the neighboring vertex.
   * @public
   */
  label?: string | undefined;

  /**
   * Vertex kind of the neighbor.
   * @public
   */
  kind: string | undefined;
}

/**
 * A relationship edge between two graph vertices, carrying the connecting
 * predicate, its direction, and the neighboring vertex on the other end.
 * @public
 */
export interface GraphEdge {
  /**
   * IRI of the connecting predicate.
   * @public
   */
  predicate: string | undefined;

  /**
   * Human-readable label of the predicate.
   * @public
   */
  predicateLabel?: string | undefined;

  /**
   * Direction of the edge relative to the source vertex (incoming/outgoing).
   * @public
   */
  direction: string | undefined;

  /**
   * A neighboring vertex reached by traversing an edge, identified by its IRI,
   * label, and kind.
   * @public
   */
  neighbor: GraphNeighbor | undefined;
}

/**
 * A node in the ontology graph — a class, property, or individual — with its
 * IRI, kind, namespace, associated labels/comments, and outgoing edges.
 * @public
 */
export interface GraphVertex {
  /**
   * IRI of the vertex.
   * @public
   */
  uri: string | undefined;

  /**
   * Vertex kind (class, object-property, datatype-property, etc.).
   * @public
   */
  kind: string | undefined;

  /**
   * Namespace the vertex belongs to.
   * @public
   */
  namespace: string | undefined;

  /**
   * RDF types (rdf:type) declared on the vertex.
   * @public
   */
  types?: string[] | undefined;

  /**
   * Human-readable labels (rdfs:label) of the vertex.
   * @public
   */
  labels?: string[] | undefined;

  /**
   * Descriptive comments (rdfs:comment) on the vertex.
   * @public
   */
  comments?: string[] | undefined;

  /**
   * Alternative labels (skos:altLabel) — carries source synonyms curated
   * during enrichment and emitted onto the induced class/property.
   * @public
   */
  altLabels?: string[] | undefined;

  /**
   * IRIs of the named graphs the vertex appears in.
   * @public
   */
  graphUris?: string[] | undefined;

  /**
   * Whether this vertex carries the ``coa:isMapped`` marker — i.e. it is
   * backed by an R2RML mapping and therefore answerable by the structured
   * Tier-2 (NL→SPARQL / NL→SQL) path. Structured / table-backed classes are
   * true; unstructured-induced and foundational classes are false (the marker
   * is absent). Derived from the top-level ``coa:isMapped`` triple and
   * excluded from ``edges``.
   * @public
   */
  isMapped?: boolean | undefined;

  /**
   * Previous generations of this vertex's annotations, retired when a
   * re-induced proposal was accepted into the same ontology. Keys are
   * ``comments`` / ``definitions`` / ``altLabels`` / ``glossaryTerms`` /
   * ``tags``; values are the literals
   * that used to be live — typically the AI-generated text a steward's
   * curation replaced. Read from the ``coa:superseded*`` history predicates.
   * History only: NOT live content (serve and embeddings ignore it) and
   * excluded from ``edges``. Empty when nothing has been superseded.
   * @public
   */
  superseded?: Record<string, string[]> | undefined;

  /**
   * Outgoing relationship edges from this vertex.
   * @public
   */
  edges?: GraphEdge[] | undefined;
}

/**
 * @public
 */
export interface GetGraphDatatypePropertyInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * IRI of the datatype-property vertex to look up.
   * @public
   */
  uri: string | undefined;
}

/**
 * @public
 */
export interface GetGraphObjectPropertyInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * IRI of the object-property vertex to look up.
   * @public
   */
  uri: string | undefined;
}

/**
 * @public
 */
export interface GetIngestStatusInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the ontology whose ingest job is being polled.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Identifier of the ingest job to poll.
   * @public
   */
  jobId: string | undefined;
}

/**
 * Counts produced once an ingest job completes.
 * @public
 */
export interface IngestJobResult {
  /**
   * Identifier of the ingested ontology.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * Number of classes ingested.
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
 * Async ingest job handle / status — returned by ingest-from-s3 (202) and
 * the ingest-status poll. Typed so FE/BE share one contract.
 * @public
 */
export interface IngestJob {
  /**
   * Identifier of the async ingest job.
   * @public
   */
  jobId: string | undefined;

  /**
   * Identifier of the ontology being ingested.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Lifecycle states of an async ontology-ingest job.
   * @public
   */
  status: IngestJobState | undefined;

  /**
   * Error message when the job failed; absent otherwise.
   * @public
   */
  error?: string | undefined;

  /**
   * Counts produced once an ingest job completes.
   * @public
   */
  result?: IngestJobResult | undefined;
}

/**
 * @public
 */
export interface GetIngestStatusOutput {
  /**
   * Async ingest job handle / status — returned by ingest-from-s3 (202) and
   * the ingest-status poll. Typed so FE/BE share one contract.
   * @public
   */
  result: IngestJob | undefined;
}

/**
 * @public
 */
export interface GetOntologyInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the ontology to fetch.
   * @public
   */
  ontologyId: string | undefined;
}

/**
 * @public
 */
export interface GetOntologyOutput {
  /**
   * The requested ontology record.
   * @public
   */
  ontology: __DocumentType | undefined;
}

/**
 * @public
 */
export interface GetOntologyOverviewInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the ontology to summarize.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Max entities to return per collection (classes, object properties,
   * datatype properties are each capped independently). Bounds the
   * response so a large ontology does not exceed the API Gateway / Lambda
   * response limit. Omit for the server default.
   * @public
   */
  limit?: number | undefined;

  /**
   * Zero-based offset into each collection, for paging. Combined with
   * ``limit`` this yields a stable page window over the full ontology.
   * @public
   */
  offset?: number | undefined;

  /**
   * When true, return a bounded taxonomy seed instead of the full
   * ontology: a few root classes with the largest subtrees plus a capped
   * set of their descendants, and no properties. For a first render of a
   * very large ontology; the rest loads on demand.
   * @public
   */
  sample?: boolean | undefined;
}

/**
 * One class persisted in an ontology's named graph.
 * @public
 */
export interface OntologyClassSummary {
  /**
   * IRI of the class.
   * @public
   */
  uri: string | undefined;

  /**
   * Human-readable label (rdfs:label) of the class.
   * @public
   */
  label?: string | undefined;

  /**
   * Descriptive comment (rdfs:comment) on the class.
   * @public
   */
  comment?: string | undefined;

  /**
   * IRI of the previously-loaded class this class was grounded to
   * (coa:groundedTo / skos:exactMatch / skos:closeMatch). Absent when the
   * class is novel (net-new this induction).
   * @public
   */
  groundedTo?: string | undefined;

  /**
   * "exact" or "close" when grounded via a SKOS mapping; otherwise absent.
   * @public
   */
  matchType?: string | undefined;

  /**
   * IRIs of this class's direct super-classes (``rdfs:subClassOf``). Lets a
   * caller reconstruct the taxonomy (roots + parent/child edges) from the
   * overview alone, without an N-per-class vertex fan-out. Empty/absent for
   * a top-level class with no loaded parent.
   * @public
   */
  subClassOf?: string[] | undefined;
}

/**
 * One property persisted in an ontology's named graph. Object properties
 * carry a class IRI in ``range`` (a relationship); datatype properties carry
 * a datatype IRI (e.g. xsd:string).
 * @public
 */
export interface OntologyPropertySummary {
  /**
   * IRI of the property.
   * @public
   */
  uri: string | undefined;

  /**
   * Human-readable label (rdfs:label) of the property.
   * @public
   */
  label?: string | undefined;

  /**
   * IRI of the property's domain class.
   * @public
   */
  domain?: string | undefined;

  /**
   * IRI of the property's range (a class IRI for object properties, a
   * datatype IRI for datatype properties).
   * @public
   */
  range?: string | undefined;
}

/**
 * Everything persisted in one ontology's named graph, grouped for display.
 * Read from the graph store (not the registry), so it reflects the triples
 * that actually landed in the knowledge graph.
 * @public
 */
export interface OntologyOverview {
  /**
   * Identifier of the ontology.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Namespace the ontology belongs to.
   * @public
   */
  namespace: string | undefined;

  /**
   * IRI of the named graph holding the ontology's triples.
   * @public
   */
  graphUri?: string | undefined;

  /**
   * Classes persisted in the ontology's named graph.
   * @public
   */
  classes?: OntologyClassSummary[] | undefined;

  /**
   * Object properties — relationships between classes (domain → range class).
   * @public
   */
  objectProperties?: OntologyPropertySummary[] | undefined;

  /**
   * Datatype properties — attributes of a class with a literal range.
   * @public
   */
  datatypeProperties?: OntologyPropertySummary[] | undefined;

  /**
   * Total number of classes in the ontology (independent of limit/offset),
   * so a client can show the true count while rendering one page.
   * @public
   */
  totalClasses?: number | undefined;

  /**
   * Total number of object properties in the ontology (independent of limit/offset).
   * @public
   */
  totalObjectProperties?: number | undefined;

  /**
   * Total number of datatype properties in the ontology (independent of limit/offset).
   * @public
   */
  totalDatatypeProperties?: number | undefined;
}

/**
 * @public
 */
export interface GetOntologyUploadUrlInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Name of the file to be uploaded. The server sanitizes it and keeps the
   * first 200 characters, so the bound is generous: clients derive the
   * name from the ontology identifier, which may itself be a long IRI.
   * @public
   */
  filename: string | undefined;

  /**
   * MIME content type of the file to be uploaded.
   * @public
   */
  contentType?: string | undefined;

  /**
   * Identifier to register the uploaded ontology under.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * Human-readable display title for the ontology.
   * @public
   */
  title?: string | undefined;
}

/**
 * @public
 */
export interface GetOntologyUploadUrlOutput {
  /**
   * Presigned S3 URL to PUT the file to.
   * @public
   */
  uploadUrl: string | undefined;

  /**
   * S3 object key where the file will be stored.
   * @public
   */
  s3Key: string | undefined;

  /**
   * Identifier assigned to the ontology.
   * @public
   */
  ontologyId: string | undefined;
}

/**
 * @public
 */
export interface GraphSearchInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Substring search term matched against entity IRIs and labels. An
   * empty value or `*` lists the namespace's entities; a value over 4000
   * characters returns 400.
   * @public
   */
  q: string | undefined;

  /**
   * Vertex kind discriminator.
   * @public
   */
  kind?: GraphVertexKind | undefined;

  /**
   * Restricts results to the specified ontology's named graph.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * Excludes results from the specified ontology's named graph
   * (e.g., to filter out governed metrics classes).
   * @public
   */
  excludeOntologyId?: string | undefined;

  /**
   * Maximum number of hits to return (the page size). Bounded because the
   * value drives the underlying query's LIMIT clause; out-of-range values
   * are rejected with a 400.
   * @public
   */
  limit?: number | undefined;

  /**
   * Number of leading hits to skip, for pagination. Combined with
   * ``limit`` this yields a stable page window over the full,
   * deterministically-ordered result set. Bounded like
   * GetOntologyOverview's ``offset`` (the class browser pages through
   * every class of large induced ontologies); out-of-range values are
   * rejected with a 400.
   * @public
   */
  offset?: number | undefined;
}

/**
 * A single result from a graph search query, identifying a matched vertex
 * by its IRI, label, kind, and the named graph it lives in.
 * @public
 */
export interface GraphSearchHit {
  /**
   * IRI of the matched vertex.
   * @public
   */
  uri: string | undefined;

  /**
   * Human-readable label of the matched vertex.
   * @public
   */
  label?: string | undefined;

  /**
   * Vertex kind (class, object-property, datatype-property, etc.).
   * @public
   */
  kind: string | undefined;

  /**
   * IRIs of the named graphs the vertex is defined in. A class IRI asserted
   * in more than one ontology (e.g. a shared IRI referenced by both
   * schema.org and FIBO) lists every source graph, not just one.
   * @public
   */
  graphUris?: string[] | undefined;
}

/**
 * @public
 */
export interface GraphSearchOutput {
  /**
   * The matching graph search hits (the requested page window).
   * @public
   */
  hits: GraphSearchHit[] | undefined;

  /**
   * Total number of hits matching the query across all pages, so a
   * client can render a known page count. Independent of ``limit`` /
   * ``offset``.
   * @public
   */
  totalCount?: number | undefined;
}

/**
 * @public
 */
export interface IngestOntologyFromS3Input {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier to register the ingested ontology under.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * S3 object key of the uploaded ontology file, as returned by
   * GetOntologyUploadUrl.
   * @public
   */
  s3Key: string | undefined;

  /**
   * Serialization format of the file. Inferred from the key's file
   * extension when omitted.
   * @public
   */
  format?: OntologyFileFormat | undefined;

  /**
   * Human-readable display title for the ontology.
   * @public
   */
  title?: string | undefined;

  /**
   * Category of the ontology. Defaults to `user_created`.
   * @public
   */
  ontologyType?: OntologyType | undefined;

  /**
   * Optional idempotency token. A retry with the same token and the same
   * parameters within 24 hours returns the original result instead of
   * starting a second ingest job; reusing the token with different
   * parameters is rejected with a 409.
   * @public
   */
  clientToken?: string | undefined;
}

/**
 * @public
 */
export interface IngestOntologyFromS3Output {
  /**
   * Async ingest job handle / status — returned by ingest-from-s3 (202) and
   * the ingest-status poll. Typed so FE/BE share one contract.
   * @public
   */
  result: IngestJob | undefined;
}

/**
 * @public
 */
export interface ListOntologiesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Coarse-grained ontology category for filtering the catalog.
   * @public
   */
  ontologyType?: OntologyType | undefined;

  /**
   * Filters the listing to ontologies carrying this domain tag.
   * @public
   */
  domainTag?: string | undefined;

  /**
   * Filters the listing to the ontology with exactly this canonical IRI.
   * @public
   */
  uri?: string | undefined;

  /**
   * Filters the listing to ontologies from this source registry (e.g.
   * `induced`, `document`), exact match.
   * @public
   */
  sourceRegistry?: string | undefined;

  /**
   * Filters the listing to ontologies with this license tier (e.g.
   * `restricted`), exact match.
   * @public
   */
  licenseTier?: string | undefined;

  /**
   * Legacy spelling of `maxResults`; `maxResults` wins when both are sent.
   * @public
   */
  limit?: number | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of ontologies to return in one page (default 50).
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * Summary of an ontology in the namespace registry.
 * @public
 */
export interface OntologyRecord {
  /**
   * Unique identifier of the ontology within the namespace.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Canonical IRI of the ontology.
   * @public
   */
  uri: string | undefined;

  /**
   * Human-readable display title.
   * @public
   */
  title?: string | undefined;

  /**
   * Human-readable description of the ontology.
   * @public
   */
  description?: string | undefined;

  /**
   * Category of the ontology (foundational, induced, or user_created).
   * @public
   */
  ontologyType?: string | undefined;

  /**
   * Ingest lifecycle marker set by the async parse/embed worker: "pending"
   * while ingesting, "ok" once parsed, "parse_error" on failure. Absent on
   * legacy rows persisted before this field existed, for which a positive
   * embeddingCount means the ingest completed.
   * @public
   */
  parseStatus?: string | undefined;

  /**
   * Lifecycle status of the registry row. Set to "deleting" while an async
   * ontology delete tears down its graph + embeddings (the row stays listed
   * as "Delete in progress" until teardown completes, then is removed).
   * Absent for normal, fully-materialized ontologies.
   * @public
   */
  status?: string | undefined;

  /**
   * Set when an async delete's teardown failed (graph/embedding hard gate),
   * leaving the row in status "deleting". Lets a client distinguish a stuck
   * delete (re-issue DELETE to retry) from one still in progress. Cleared
   * when a fresh delete starts; absent otherwise.
   * @public
   */
  deleteError?: string | undefined;

  /**
   * Serialization format of the source file (e.g. turtle, rdfxml, jsonld).
   * @public
   */
  format?: string | undefined;

  /**
   * Domain tags used to categorize and filter the ontology.
   * @public
   */
  domainTags?: string[] | undefined;

  /**
   * Number of classes in the ontology.
   * @public
   */
  classCount?: number | undefined;

  /**
   * Number of properties in the ontology.
   * @public
   */
  propertyCount?: number | undefined;

  /**
   * Number of axioms in the ontology.
   * @public
   */
  axiomCount?: number | undefined;

  /**
   * Number of vector embeddings generated for the ontology.
   * @public
   */
  embeddingCount?: number | undefined;

  /**
   * IRI of the named graph holding the ontology's triples.
   * @public
   */
  graphUri?: string | undefined;

  /**
   * Creation timestamp of the registry row.
   * @public
   */
  createdAt?: string | undefined;

  /**
   * Last-updated timestamp of the registry row.
   * @public
   */
  updatedAt?: string | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListOntologiesOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * The ontologies registered in the namespace.
   * @public
   */
  ontologies: OntologyRecord[] | undefined;
}

/**
 * @public
 */
export interface ListStatementsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Restrict to one subject IRI.
   * @public
   */
  subject?: string | undefined;

  /**
   * Restrict to one predicate IRI.
   * @public
   */
  predicate?: string | undefined;

  /**
   * Restrict to one object: an IRI, or a literal's lexical form.
   * @public
   */
  objectValue?: string | undefined;

  /**
   * Restrict to one named graph IRI in the namespace.
   * @public
   */
  graph?: string | undefined;

  /**
   * Maximum number of statements to return (the page size).
   * @public
   */
  limit?: number | undefined;

  /**
   * Number of leading statements to skip, for pagination.
   * @public
   */
  offset?: number | undefined;
}

/**
 * One RDF statement (triple) in a namespace's named graphs.
 * @public
 */
export interface GraphStatement {
  /**
   * Named graph the statement lives in.
   * @public
   */
  graph: string | undefined;

  /**
   * Subject IRI.
   * @public
   */
  subject: string | undefined;

  /**
   * Predicate IRI.
   * @public
   */
  predicate: string | undefined;

  /**
   * Object term: an IRI, or the lexical form of a literal.
   * @public
   */
  object: string | undefined;
}

/**
 * @public
 */
export interface ListStatementsOutput {
  /**
   * The page of matching statements, in the backend's named-graph
   * index order (stable for a static graph, not a sorted order).
   * @public
   */
  statements: GraphStatement[] | undefined;

  /**
   * True when the page was capped at ``limit`` and more statements
   * exist beyond this window.
   * @public
   */
  truncated?: boolean | undefined;
}

/**
 * @public
 */
export interface UploadOntologyInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Identifier of the ontology the file belongs to.
   * @public
   */
  ontologyId: string | undefined;

  /**
   * Raw ontology file contents (Turtle, RDF/XML, or JSON-LD).
   * @public
   */
  body: Uint8Array | undefined;
}

/**
 * @public
 */
export interface UploadOntologyOutput {
  /**
   * Result of the upload operation.
   * @public
   */
  result: __DocumentType | undefined;
}

/**
 * @public
 */
export interface AcceptProposalInput {
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
   * Target ontology ID to merge into. If omitted, uses the proposal's own ontology ID.
   * @public
   */
  ontologyId?: string | undefined;
}

/**
 * @public
 */
export interface AcceptProposalOutput {
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
export interface CancelProposalInput {
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
}

/**
 * @public
 */
export interface CancelProposalOutput {
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
export interface CompileConstraintsInput {
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
   * Reviewed ConstraintConfig to compile into SHACL. At most 65536 bytes
   * once serialized as JSON; larger configs are rejected with a 400.
   * @public
   */
  constraint_config: __DocumentType | undefined;

  /**
   * Optional custom SHACL Turtle to merge with the compiled shapes.
   * @public
   */
  custom_turtle?: string | undefined;
}

/**
 * @public
 */
export interface CompileConstraintsOutput {
  /**
   * UUID v4 identifier.
   * @public
   */
  proposalId: string | undefined;

  /**
   * Compiled SHACL shapes in Turtle format.
   * @public
   */
  shapes_turtle: string | undefined;
}

/**
 * @public
 */
export interface GetInductionJobInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  jobId: string | undefined;

  /**
   * Omitted (default) returns a slim poll shape with `report.matches`
   * emptied so the response stays under the API-proxy Lambda's 6MB
   * response cap at scale (avoids 413 RequestEntityTooLarge). `report`
   * or `full` returns the full report including every concept match,
   * which may exceed that cap on large inductions. See #807.
   * @public
   */
  include?: IncludeMode | undefined;
}

/**
 * Outcome of a document-to-table bridge run, on a completed bridge job.
 * Name lists are capped; counts are not. Additional diagnostic counters
 * may appear.
 * @public
 */
export interface BridgeReport {
  /**
   * Ontology the bridge ran on.
   * @public
   */
  ontologyId?: string | undefined;

  /**
   * Whether this was a dry run (no proposal created).
   * @public
   */
  dryRun?: boolean | undefined;

  /**
   * The pending proposal holding the planned changes (absent on a dry run
   * or when nothing would change). Accept it to write them.
   * @public
   */
  proposalId?: string | undefined;

  /**
   * Table classes considered.
   * @public
   */
  tablesConsidered?: number | undefined;

  /**
   * Tables that had any document evidence and were sent to the LLM.
   * @public
   */
  tablesWithEvidence?: number | undefined;

  /**
   * Tables with no document evidence (left unchanged).
   * @public
   */
  tablesWithoutEvidence?: string[] | undefined;

  /**
   * Definitions proposed for tables.
   * @public
   */
  tableDefinitions?: number | undefined;

  /**
   * Definitions proposed for columns.
   * @public
   */
  columnDefinitions?: number | undefined;

  /**
   * Definitions that replaced a placeholder description (the old text is
   * kept in the description history).
   * @public
   */
  replacedBoilerplate?: number | undefined;

  /**
   * Replacements decided by the word-based placeholder check.
   * @public
   */
  replacedByRule?: number | undefined;

  /**
   * Replacements decided only by the model judging the existing description
   * a placeholder: the ones to review before accepting.
   * @public
   */
  replacedByModel?: number | undefined;

  /**
   * Tables and columns whose description the model alone judged a
   * placeholder (capped).
   * @public
   */
  replacedByModelSubjects?: string[] | undefined;

  /**
   * Definitions appended after an informative existing description.
   * @public
   */
  appendedToExisting?: number | undefined;

  /**
   * `skos:closeMatch` / `skos:relatedMatch` links from tables to document classes.
   * @public
   */
  tableLinks?: number | undefined;

  /**
   * `skos:closeMatch` / `skos:relatedMatch` links from columns to document classes.
   * @public
   */
  columnLinks?: number | undefined;

  /**
   * Names of the tables given a definition (capped).
   * @public
   */
  definedTables?: string[] | undefined;

  /**
   * Names of the columns given a definition (capped).
   * @public
   */
  definedColumns?: string[] | undefined;

  /**
   * The links proposed, one per entry as "<table or table.column>
   * <closeMatch|relatedMatch> <document class label>" (capped).
   * @public
   */
  links?: string[] | undefined;

  /**
   * Definition LLM calls made.
   * @public
   */
  llmCalls?: number | undefined;

  /**
   * Definition LLM calls that failed after retries.
   * @public
   */
  llmFailures?: number | undefined;

  /**
   * First LLM error seen, if any.
   * @public
   */
  firstLlmError?: string | undefined;

  /**
   * Tables whose definition calls all failed.
   * @public
   */
  failedTables?: string[] | undefined;

  /**
   * Run notes (missing evidence sources, search failures).
   * @public
   */
  notes?: string[] | undefined;

  /**
   * Wall-clock run time in seconds.
   * @public
   */
  elapsedSeconds?: number | undefined;
}

/**
 * A table that could not be processed during induction.
 * @public
 */
export interface DroppedTable {
  /**
   * Name of the table that was dropped.
   * @public
   */
  tableName: string | undefined;

  /**
   * Short failure category, e.g. "gen_llm_empty" or "parse_failed".
   * @public
   */
  reason: string | undefined;
}

/**
 * A single concept match result.
 * @public
 */
export interface ConceptMatch {
  /**
   * Source table the match originates from.
   * @public
   */
  sourceTable: string | undefined;

  /**
   * Stable data-source-qualified identity for the source table. New
   * structured inductions populate this so same-named tables remain
   * distinguishable; absent on legacy and unstructured matches.
   * @public
   */
  sourceTableIdentity?: string | undefined;

  /**
   * Source column the match originates from.
   * @public
   */
  sourceColumn: string | undefined;

  /**
   * Matched class URI (null if novel).
   * @public
   */
  matchedClassUri?: string | undefined;

  /**
   * Ontology ID containing the matched class.
   * @public
   */
  matchedOntologyId?: string | undefined;

  /**
   * Similarity score (0.0 to 1.0).
   * @public
   */
  similarity?: number | undefined;

  /**
   * Concept match type.
   * @public
   */
  matchType: MatchType | undefined;
}

/**
 * Report generated after a successful induction run.
 * @public
 */
export interface InductionReport {
  /**
   * Number of tables processed during induction.
   * @public
   */
  tablesProcessed: number | undefined;

  /**
   * Number of columns processed during induction.
   * @public
   */
  columnsProcessed: number | undefined;

  /**
   * Number of novel classes created (not grounded to existing concepts).
   * @public
   */
  novelClassesCreated: number | undefined;

  /**
   * Concept match results produced by induction.
   * @public
   */
  matches: ConceptMatch[] | undefined;

  /**
   * Ontology IDs used for grounding.
   * @public
   */
  groundingOntologiesUsed?: string[] | undefined;

  /**
   * Proposal ID generated by this induction.
   * @public
   */
  inducedOntologyId?: string | undefined;

  /**
   * Tables excluded from the induced ontology because they could not be
   * processed (e.g. the generation LLM returned nothing, or its output
   * failed to parse). Empty for strategies that never drop tables.
   * @public
   */
  droppedTables?: DroppedTable[] | undefined;
}

/**
 * @public
 */
export interface GetInductionJobOutput {
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
   * Induction report (populated when status is COMPLETED).
   * @public
   */
  report?: InductionReport | undefined;

  /**
   * Origin of this run; `BRIDGE` for a `bridge_to_tables` job. Items
   * lacking it are STRUCTURED.
   * @public
   */
  sourceType?: InductionSourceType | undefined;

  /**
   * Current step of a running bridge job, as short free text
   * (e.g. "writing definitions for 12 tables").
   * @public
   */
  progress?: string | undefined;

  /**
   * Bridge outcome (populated when a `bridge_to_tables` job is COMPLETED).
   * @public
   */
  bridgeReport?: BridgeReport | undefined;

  /**
   * Error message (populated when status is FAILED).
   * @public
   */
  error?: string | undefined;
}

/**
 * @public
 */
export interface GetInferConstraintsJobInput {
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
   * UUID v4 identifier.
   * @public
   */
  jobId: string | undefined;
}

/**
 * @public
 */
export interface GetInferConstraintsJobOutput {
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
   * Job status (pending | running | completed | failed).
   * @public
   */
  status: string | undefined;

  /**
   * Error message if status is failed.
   * @public
   */
  error?: string | undefined;

  /**
   * Inferred ConstraintConfig (present once status is completed).
   * @public
   */
  inferred_constraints?: __DocumentType | undefined;
}

/**
 * @public
 */
export interface GetProposalInput {
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
}

/**
 * Metadata about a proposal.
 * @public
 */
export interface ProposalMetadata {
  /**
   * Data source IDs this proposal was induced from.
   * @public
   */
  datasourceIds?: string[] | undefined;

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
 * @public
 */
export interface GetProposalOutput {
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
   * OWL ontology in Turtle format. Omitted for large proposals that are
   * served out-of-band via `ontologyUrl` (a presigned S3 GET URL).
   * @public
   */
  ontologyTurtle?: string | undefined;

  /**
   * R2RML mappings in Turtle format. Omitted when served via `r2rmlUrl`.
   * @public
   */
  r2rmlTurtle?: string | undefined;

  /**
   * Presigned S3 GET URL for the OWL ontology Turtle when it is served
   * out-of-band (proposals exceeding the API payload cap). Null when
   * `ontologyTurtle` is inlined.
   * @public
   */
  ontologyUrl?: string | undefined;

  /**
   * Presigned S3 GET URL for the R2RML Turtle when served out-of-band.
   * @public
   */
  r2rmlUrl?: string | undefined;

  /**
   * Presigned S3 GET URL for the grounding-match list (`matches.json`)
   * when it is served out-of-band. Null when the match list is small
   * enough to be returned inline.
   * @public
   */
  matchesUrl?: string | undefined;

  /**
   * Presigned S3 GET URL for the SHACL constraint config
   * (`constraints.ttl`) when it is served out-of-band. Null when no
   * constraints artifact exists, in which case any small inline
   * `constraintConfig` in `metadata` is returned instead.
   * @public
   */
  constraintsUrl?: string | undefined;

  /**
   * Proposal metadata (tables processed, classes created, etc.).
   * @public
   */
  metadata?: ProposalMetadata | undefined;

  /**
   * Error message from the most recent failed accept attempt.
   * Populated when an ``accepting`` → ``pending`` rollback occurred;
   * cleared on the next ``AcceptProposal`` call.
   * @public
   */
  acceptError?: string | undefined;
}

/**
 * @public
 */
export interface GetProposalUploadUrlsInput {
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
}

/**
 * @public
 */
export interface GetProposalUploadUrlsOutput {
  /**
   * Revision containing both create-only upload targets. Pass this value
   * to UpdateProposal as uploadRevisionId only after every requested PUT
   * succeeds.
   * @public
   */
  revisionId: string | undefined;

  /**
   * Create-only S3 PUT URL for the revised OWL ontology Turtle. Send
   * `If-None-Match: *`; after 409, 412, or an ambiguous outcome, request
   * a fresh revision rather than reusing this URL.
   * @public
   */
  ontologyPutUrl: string | undefined;

  /**
   * Create-only S3 PUT URL for the revised R2RML Turtle. Send
   * `If-None-Match: *`; after 409, 412, or an ambiguous outcome, request
   * a fresh revision rather than reusing this URL.
   * @public
   */
  r2rmlPutUrl: string | undefined;
}

/**
 * @public
 */
export interface GetProposalValidationJobInput {
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
   * UUID v4 identifier.
   * @public
   */
  jobId: string | undefined;
}

/**
 * One validation finding (e.g. a HermiT inconsistency, OoPS pitfall).
 * @public
 */
export interface ProposalValidationFinding {
  /**
   * Name of the validator that produced this finding.
   * @public
   */
  validator: string | undefined;

  /**
   * Validation tier identifier — selects which validators to run.
   * @public
   */
  tier: ProposalValidationTier | undefined;

  /**
   * Severity of a single validation finding.
   * @public
   */
  severity: ProposalValidationSeverity | undefined;

  /**
   * Machine-readable code identifying the finding.
   * @public
   */
  code: string | undefined;

  /**
   * Human-readable description of the finding.
   * @public
   */
  message: string | undefined;

  /**
   * Subject IRI the finding refers to (a class/property URI).
   * @public
   */
  subject?: string | undefined;

  /**
   * Structured, finding-specific payload. For MALFORMED_DATATYPE_TOKENS this
   * carries `offenders` (a list of `\{subject, predicate, found, canonical\}`),
   * `count`, and `element_count` so the UI can preview the proposed repair.
   * @public
   */
  details?: __DocumentType | undefined;
}

/**
 * Aggregated validation report.
 * @public
 */
export interface ProposalValidationReport {
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
   * Whether the proposal passed validation (no blocking findings).
   * @public
   */
  passed: boolean | undefined;

  /**
   * All findings produced across the validation tiers.
   * @public
   */
  findings: ProposalValidationFinding[] | undefined;

  /**
   * Validation tiers that were run.
   * @public
   */
  tiersRun: ProposalValidationTier[] | undefined;

  /**
   * Timestamp when the validation report was created.
   * @public
   */
  createdAt: string | undefined;
}

/**
 * @public
 */
export interface GetProposalValidationJobOutput {
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

  /**
   * Error message if status is FAILED.
   * @public
   */
  error?: string | undefined;

  /**
   * Validation report (present once status is COMPLETED).
   * @public
   */
  report?: ProposalValidationReport | undefined;
}

/**
 * @public
 */
export interface InferConstraintsInput {
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
   * Optional idempotency token. A retry with the same token and the same
   * parameters within 24 hours returns the original job handle instead of
   * starting a second job; reusing the token with different parameters is
   * rejected with a 409.
   * @public
   */
  clientToken?: string | undefined;
}

/**
 * @public
 */
export interface InferConstraintsOutput {
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
   * Initial job status (pending).
   * @public
   */
  status: string | undefined;
}

/**
 * @public
 */
export interface ListFoundationalOntologiesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;
}

/**
 * A foundational (reference) ontology available to ground induction against,
 * identified by its key and title, with an optional description, URI, and
 * domain tags.
 * @public
 */
export interface FoundationalOntologySummary {
  /**
   * Catalog key identifying the foundational ontology.
   * @public
   */
  key: string | undefined;

  /**
   * Display title of the foundational ontology.
   * @public
   */
  title: string | undefined;

  /**
   * Short description of the ontology's scope.
   * @public
   */
  description?: string | undefined;

  /**
   * Canonical URI of the foundational ontology.
   * @public
   */
  uri?: string | undefined;

  /**
   * Domain tags categorizing the ontology.
   * @public
   */
  domainTags?: string[] | undefined;
}

/**
 * @public
 */
export interface ListFoundationalOntologiesOutput {
  /**
   * Catalog of foundational ontologies available for grounding.
   * @public
   */
  items: FoundationalOntologySummary[] | undefined;
}

/**
 * @public
 */
export interface ListInducedDatasourcesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum number of data sources to return in one page (default 1000).
   * @public
   */
  maxResults?: number | undefined;
}

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
