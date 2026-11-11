// smithy-typescript generated code
import type { DocumentType as __DocumentType } from "@smithy/types";

import type {
  DocumentStatus,
  ExportFormat,
  FactCandidateStatus,
  FactConflictAction,
  FactEventFormat,
  FactObjectKind,
  FactSourceKind,
  FactState,
  FactStateFilter,
  GraphVertexKind,
  ImportJobStatus,
  IncludeMode,
  InductionJobStatus,
  InductionSourceType,
  IngestionRunKind,
  IngestionRunStatus,
  IngestJobState,
  LinkDirection,
  MatchType,
  NamespaceStatus,
  OntologyFileFormat,
  OntologyType,
  PrincipalType,
  ProposalStatus,
  ProposalValidationJobStatus,
  ProposalValidationSeverity,
  ProposalValidationTier,
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
 * Compares the schema version this build expects with the one the database reports.
 * @public
 */
export interface SystemSchemaVersion {
  /**
   * Highest migration version this build ships.
   * @public
   */
  codeVersion: number | undefined;

  /**
   * Highest applied migration version recorded by the database; null when unreadable.
   * @public
   */
  dbVersion?: number | undefined;

  /**
   * True only when both versions are known and equal.
   * @public
   */
  consistent?: boolean | undefined;

  /**
   * Human-readable provenance for the two numbers.
   * @public
   */
  source: string | undefined;
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

  /**
   * Code/database schema consistency (migration state); absent when the
   * deployment cannot read the schema version table.
   * @public
   */
  schemaVersion?: SystemSchemaVersion | undefined;
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
 * One ontology class in the browse tree.
 * @public
 */
export interface OntologyClassRef {
  /**
   * Class IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label; the local name when the T-Box has no label.
   * @public
   */
  label: string | undefined;

  /**
   * Superclass IRIs; empty for a root class.
   * @public
   */
  parents?: string[] | undefined;
}

/**
 * Counts returned with the tree.
 * @public
 */
export interface OntologyBrowseCounts {
  /**
   * Number of classes in the published T-Box.
   * @public
   */
  classes: number | undefined;

  /**
   * Number of properties in the published T-Box.
   * @public
   */
  properties: number | undefined;
}

/**
 * The `tbox/current` pointer row.
 * @public
 */
export interface OntologyPointer {
  /**
   * Pointer name, always `tbox/current` in this deployment.
   * @public
   */
  name?: string | undefined;

  /**
   * Version the pointer currently selects.
   * @public
   */
  versionId: string | undefined;

  /**
   * Semver of the selected version.
   * @public
   */
  semver?: string | undefined;

  /**
   * Canonical hash of the selected version.
   * @public
   */
  contentHash?: string | undefined;

  /**
   * Graph IRI of the selected version.
   * @public
   */
  graph?: string | undefined;

  /**
   * Last pointer move (ISO-8601).
   * @public
   */
  updatedAt?: string | undefined;
}

/**
 * One property in the flat property list.
 * @public
 */
export interface OntologyPropertyRef {
  /**
   * Property IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label.
   * @public
   */
  label: string | undefined;

  /**
   * `ObjectProperty`, `DatatypeProperty`, or `AnnotationProperty`.
   * @public
   */
  kind: string | undefined;
}

/**
 * @public
 */
export interface ListOntologyInstancesInput {
  /**
   * Class whose instances are listed.
   * @public
   */
  classIri: string | undefined;

  /**
   * Maximum instances to return (1-100); server default 20.
   * @public
   */
  limit?: number | undefined;

  /**
   * Instances to skip (0 or greater); server default 0.
   * @public
   */
  offset?: number | undefined;
}

/**
 * One instance of a class.
 * @public
 */
export interface OntologyInstanceRef {
  /**
   * Instance IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label; the local name when the instance has no label.
   * @public
   */
  label: string | undefined;

  /**
   * Graph the instance was found in.
   * @public
   */
  graph: string | undefined;
}

/**
 * Instances of one class.
 *
 * An unknown class, or an empty current graph, returns `items: []`,
 * `total: 0` and no `pointer`; it is an empty result, not an error.
 * @public
 */
export interface OntologyInstanceList {
  /**
   * Class IRI that was queried.
   * @public
   */
  class: string | undefined;

  /**
   * Instances in T-Box order, capped by `limit`.
   * @public
   */
  items: OntologyInstanceRef[] | undefined;

  /**
   * Total instances of the class, before `limit` was applied.
   * @public
   */
  total: number | undefined;

  /**
   * Page size that was applied (server default 20).
   * @public
   */
  limit: number | undefined;

  /**
   * Offset that was applied (server default 0).
   * @public
   */
  offset: number | undefined;

  /**
   * Current pointer; absent when nothing is published.
   * @public
   */
  pointer?: OntologyPointer | undefined;
}

/**
 * @public
 */
export interface GetDictionaryInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Source whose dictionary is read or refreshed.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Restrict the table rollups to one table.
   * @public
   */
  table?: string | undefined;
}

/**
 * Lifecycle of one dictionary introspection pass.
 * @public
 */
export interface DictionaryRefreshRun {
  /**
   * Server-minted identifier of this introspection pass.
   * @public
   */
  runId: string | undefined;

  /**
   * Source whose dictionary was introspected.
   * @public
   */
  sourceId: string | undefined;

  /**
   * `running`, `succeeded` or `failed`.
   * @public
   */
  status: string | undefined;

  /**
   * Caller-supplied key that makes the refresh replayable.
   * @public
   */
  idempotencyKey?: string | undefined;

  /**
   * Principal that requested the refresh, when recorded.
   * @public
   */
  requestedBy?: string | undefined;

  /**
   * ISO-8601 start time.
   * @public
   */
  startedAt?: string | undefined;

  /**
   * ISO-8601 finish time; absent while still running.
   * @public
   */
  finishedAt?: string | undefined;

  /**
   * Column rows read from the source.
   * @public
   */
  processed?: number | undefined;

  /**
   * Column rows newly inserted into the snapshot.
   * @public
   */
  inserted?: number | undefined;

  /**
   * Column rows updated in the snapshot.
   * @public
   */
  updated?: number | undefined;

  /**
   * Column rows that were already identical.
   * @public
   */
  unchanged?: number | undefined;

  /**
   * Column rows dropped because the source no longer exposes them.
   * @public
   */
  removed?: number | undefined;

  /**
   * Failure message when `status` is `failed`; absent otherwise.
   * @public
   */
  error?: string | undefined;
}

/**
 * Per-table rollup on the source dictionary page.
 * @public
 */
export interface DictionaryTableSummary {
  /**
   * Table name.
   * @public
   */
  table: string | undefined;

  /**
   * Column count in the table.
   * @public
   */
  columns: number | undefined;

  /**
   * Columns carrying a source comment.
   * @public
   */
  commented: number | undefined;

  /**
   * Columns bound to an ontology property.
   * @public
   */
  bound: number | undefined;

  /**
   * Columns with no source comment.
   * @public
   */
  missingComment: number | undefined;

  /**
   * Columns not bound to any ontology property.
   * @public
   */
  unbound: number | undefined;
}

/**
 * Comment coverage rollup (F66). `ratio` is absent when there are no rows.
 * @public
 */
export interface CommentCoverage {
  /**
   * Rows considered.
   * @public
   */
  total: number | undefined;

  /**
   * Rows carrying a comment.
   * @public
   */
  commented: number | undefined;

  /**
   * Rows with no comment.
   * @public
   */
  missing: number | undefined;

  /**
   * Commented rows divided by total, 0..1.
   * @public
   */
  ratio?: number | undefined;
}

/**
 * @public
 */
export interface GetDictionaryOutput {
  /**
   * Source the dictionary belongs to.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Source engine kind, e.g. `postgresql` or `snowflake`.
   * @public
   */
  sourceKind?: string | undefined;

  /**
   * Catalog the source exposes tables under.
   * @public
   */
  catalog?: string | undefined;

  /**
   * Schema the source exposes tables under.
   * @public
   */
  schema?: string | undefined;

  /**
   * Per-table rollups.
   * @public
   */
  tables: DictionaryTableSummary[] | undefined;

  /**
   * Comment coverage for the whole source.
   * @public
   */
  totals: CommentCoverage | undefined;

  /**
   * Bindings already resolved (`binding_method` != `none`).
   * @public
   */
  boundColumns: number | undefined;

  /**
   * Lifecycle of one dictionary introspection pass.
   * @public
   */
  latestRun?: DictionaryRefreshRun | undefined;
}

/**
 * @public
 */
export interface GetDictionaryCommentCoverageInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Source whose dictionary is read or refreshed.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Restrict the coverage rollup to one table.
   * @public
   */
  table?: string | undefined;
}

/**
 * @public
 */
export interface GetDictionaryCommentCoverageOutput {
  /**
   * Source the coverage applies to.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Comment coverage for the whole source.
   * @public
   */
  coverage: CommentCoverage | undefined;

  /**
   * Per-table coverage rollups.
   * @public
   */
  tables: DictionaryTableSummary[] | undefined;
}

/**
 * @public
 */
export interface GetDictionaryViewInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Source whose dictionary is read or refreshed.
   * @public
   */
  sourceId: string | undefined;

  /**
   * `all`, `missing_comment`, `unbound` or `mappable_unbound`.
   * @public
   */
  view?: string | undefined;

  /**
   * Restrict to one table name.
   * @public
   */
  table?: string | undefined;

  /**
   * Restrict to one column name.
   * @public
   */
  column?: string | undefined;

  /**
   * `explicit`, `name_match`, `manual` or `none`.
   * @public
   */
  bindingMethod?: string | undefined;

  /**
   * `postgresql`, `mysql`, `redshift`, `sqlserver`, `snowflake`,
   * `glue` or `duckdb`.
   * @public
   */
  sourceKind?: string | undefined;

  /**
   * Case-insensitive substring match on table, column or comment.
   * @public
   */
  query?: string | undefined;

  /**
   * Page size (default 50, max 200).
   * @public
   */
  limit?: number | undefined;

  /**
   * Rows to skip (default 0).
   * @public
   */
  offset?: number | undefined;
}

/**
 * One column row in the dictionary (ten-column view, F63).
 * @public
 */
export interface DictionaryColumn {
  /**
   * Source this column snapshot belongs to.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Catalog the source exposes the table under.
   * @public
   */
  catalog: string | undefined;

  /**
   * Schema the source exposes the table under.
   * @public
   */
  schema: string | undefined;

  /**
   * Table name.
   * @public
   */
  table: string | undefined;

  /**
   * Column name.
   * @public
   */
  column: string | undefined;

  /**
   * Column data type as reported by the source.
   * @public
   */
  dataType: string | undefined;

  /**
   * Whether the column admits NULL.
   * @public
   */
  isNullable: boolean | undefined;

  /**
   * Source engine kind, e.g. `postgresql` or `snowflake`.
   * @public
   */
  sourceKind: string | undefined;

  /**
   * How the binding was resolved: `explicit`, `name_match`, `manual` or `none`.
   * @public
   */
  bindingMethod: string | undefined;

  /**
   * Column comment captured from the source, when present.
   * @public
   */
  comment?: string | undefined;

  /**
   * Ontology property this column is bound to, when bound.
   * @public
   */
  propertyIri?: string | undefined;

  /**
   * Confidence of a `name_match` binding, 0..1.
   * @public
   */
  confidence?: number | undefined;

  /**
   * Human note attached to a `manual` binding.
   * @public
   */
  bindingNote?: string | undefined;

  /**
   * ISO-8601 time the snapshot observed this column.
   * @public
   */
  observedAt?: string | undefined;

  /**
   * Refresh run that last wrote this row.
   * @public
   */
  lastRefreshRunId?: string | undefined;
}

/**
 * @public
 */
export interface GetDictionaryViewOutput {
  /**
   * Column rows for this page.
   * @public
   */
  items: DictionaryColumn[] | undefined;

  /**
   * Number of rows after filtering.
   * @public
   */
  total: number | undefined;

  /**
   * Number of rows skipped.
   * @public
   */
  offset: number | undefined;

  /**
   * Page size actually applied.
   * @public
   */
  limit: number | undefined;

  /**
   * The filter view that was applied.
   * @public
   */
  view: string | undefined;

  /**
   * Comment coverage rollup (F66). `ratio` is absent when there are no rows.
   * @public
   */
  coverage: CommentCoverage | undefined;

  /**
   * Non-fatal notes, e.g. an empty mappable set. Never silent.
   * @public
   */
  warnings?: string[] | undefined;
}

/**
 * @public
 */
export interface ListDictionariesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Page size (default 50, max 200).
   * @public
   */
  limit?: number | undefined;

  /**
   * Rows to skip (default 0).
   * @public
   */
  offset?: number | undefined;
}

/**
 * Per-source rollup shown in the source list.
 * @public
 */
export interface DictionarySummary {
  /**
   * Source the snapshot belongs to.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Source engine kind, e.g. `postgresql` or `snowflake`.
   * @public
   */
  sourceKind: string | undefined;

  /**
   * Distinct tables in the snapshot.
   * @public
   */
  tables: number | undefined;

  /**
   * Column count in the snapshot.
   * @public
   */
  columns: number | undefined;

  /**
   * Columns carrying a source comment.
   * @public
   */
  commented: number | undefined;

  /**
   * Columns bound to an ontology property.
   * @public
   */
  bound: number | undefined;

  /**
   * ISO-8601 time the snapshot was last observed.
   * @public
   */
  observedAt?: string | undefined;

  /**
   * Most recent refresh run for this source.
   * @public
   */
  lastRun?: DictionaryRefreshRun | undefined;
}

/**
 * @public
 */
export interface ListDictionariesOutput {
  /**
   * Per-source dictionary rollups for this page.
   * @public
   */
  items: DictionarySummary[] | undefined;

  /**
   * Number of sources that have a snapshot.
   * @public
   */
  total: number | undefined;

  /**
   * Number of rows skipped.
   * @public
   */
  offset: number | undefined;

  /**
   * Page size actually applied.
   * @public
   */
  limit: number | undefined;
}

/**
 * @public
 */
export interface ListTermsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Case-insensitive substring match on label, class label or class IRI.
   * @public
   */
  query?: string | undefined;

  /**
   * Filter by entry status: `evidenced` or `inferred`.
   * @public
   */
  status?: string | undefined;

  /**
   * Page size (default 100, max 500).
   * @public
   */
  limit?: number | undefined;

  /**
   * Rows to skip (default 0).
   * @public
   */
  offset?: number | undefined;
}

/**
 * Anchor-class and alias counts for the namespace's published T-Box.
 * @public
 */
export interface TermCounts {
  /**
   * Distinct owl:Class nodes that an alias entry points at (F58).
   * @public
   */
  anchorClasses: number | undefined;

  /**
   * Number of skos:Concept / term:TermEntry alias entries (F59).
   * @public
   */
  termEntries: number | undefined;

  /**
   * Entries whose status is `evidenced`.
   * @public
   */
  evidenced: number | undefined;

  /**
   * Entries whose status is `inferred`.
   * @public
   */
  inferred: number | undefined;
}

/**
 * One alias row. The seven data columns are class, label, status,
 * confidence, guard regex, canonical-for targets and suppressed surfaces.
 * @public
 */
export interface TermEntry {
  /**
   * IRI of the skos:Concept / term:TermEntry node.
   * @public
   */
  entry: string | undefined;

  /**
   * IRI of the anchored class.
   * @public
   */
  classIri?: string | undefined;

  /**
   * rdfs:label of the anchored class, when the graph carries one.
   * @public
   */
  classLabel?: string | undefined;

  /**
   * The alias surface form (skos:prefLabel or term:label).
   * @public
   */
  label: string | undefined;

  /**
   * `evidenced` or `inferred`.
   * @public
   */
  status: string | undefined;

  /**
   * Term confidence, 0..1, when recorded.
   * @public
   */
  confidence?: number | undefined;

  /**
   * Guard regular expression that must pass before the alias is used.
   * @public
   */
  guardRegex?: string | undefined;

  /**
   * Concepts this surface is the canonical label for.
   * @public
   */
  canonicalFor?: string[] | undefined;

  /**
   * Surface forms suppressed in favour of this entry.
   * @public
   */
  suppressedSurface?: string[] | undefined;
}

/**
 * @public
 */
export interface ListTermsOutput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * IRI of the graph the entries were read from; absent when the
   * namespace has no lexicon graph.
   * @public
   */
  graph?: string | undefined;

  /**
   * Anchor-class and alias counts for the namespace's published T-Box.
   * @public
   */
  counts: TermCounts | undefined;

  /**
   * The alias rows for this page.
   * @public
   */
  entries: TermEntry[] | undefined;

  /**
   * Number of entries after filtering.
   * @public
   */
  total: number | undefined;

  /**
   * Number of rows skipped.
   * @public
   */
  offset: number | undefined;

  /**
   * Page size actually applied.
   * @public
   */
  limit: number | undefined;
}

/**
 * @public
 */
export interface RefreshDictionariesInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Source whose dictionary is read or refreshed.
   * @public
   */
  sourceId: string | undefined;

  /**
   * Caller-supplied key; generated per request when absent.
   * @public
   */
  idempotencyKey?: string | undefined;

  /**
   * Principal requesting the refresh, when the caller supplies one.
   * @public
   */
  requestedBy?: string | undefined;
}

/**
 * @public
 */
export interface RefreshDictionariesOutput {
  /**
   * Lifecycle of one dictionary introspection pass.
   * @public
   */
  run: DictionaryRefreshRun | undefined;

  /**
   * How bindings were resolved: `published-ontology`,
   * `published-ontology-empty`, or `replay` when an already-succeeded
   * idempotency key returned its prior run.
   * @public
   */
  bindingBasis: string | undefined;

  /**
   * Non-fatal notes (e.g. a source with zero columns). Never silent.
   * @public
   */
  warnings?: string[] | undefined;
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
 * One superclass link in a class chain.
 * @public
 */
export interface EntityClassLink {
  /**
   * Class IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Class label.
   * @public
   */
  label: string | undefined;
}

/**
 * One class asserted or inferred for the entity.
 * @public
 */
export interface EntityClass {
  /**
   * Class IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Class label.
   * @public
   */
  label: string | undefined;

  /**
   * True when the class has a label in the T-Box.
   * @public
   */
  labeled: boolean | undefined;

  /**
   * True when the membership exists only in the inferred graph.
   * @public
   */
  inferredOnly: boolean | undefined;

  /**
   * Number of instances of this class.
   * @public
   */
  instanceCount: number | undefined;

  /**
   * Superclass chain, nearest first.
   * @public
   */
  chain: EntityClassLink[] | undefined;
}

/**
 * Three-state evidence badge for the entity or one field.
 * @public
 */
export interface EntityBadge {
  /**
   * `evidenced`, `inferred`, or `none`.
   * @public
   */
  state: string | undefined;

  /**
   * Human-readable badge label.
   * @public
   */
  label: string | undefined;

  /**
   * Why the badge has this state.
   * @public
   */
  basis: string | undefined;

  /**
   * Judge that produced the verdict, when one was used.
   * @public
   */
  judge?: string | undefined;
}

/**
 * One edge in the immediate neighbourhood.
 * @public
 */
export interface EntityEdge {
  /**
   * Subject IRI.
   * @public
   */
  s: string | undefined;

  /**
   * Predicate IRI.
   * @public
   */
  p: string | undefined;

  /**
   * Object IRI or lexical value.
   * @public
   */
  o: string | undefined;

  /**
   * Named graph the edge came from.
   * @public
   */
  graph: string | undefined;

  /**
   * True when the edge exists only in the inferred graph.
   * @public
   */
  inferred: boolean | undefined;
}

/**
 * One node in the immediate neighbourhood.
 * @public
 */
export interface EntityNode {
  /**
   * Node IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label; falls back to the local name when unlabeled.
   * @public
   */
  label: string | undefined;

  /**
   * True when the node exists only in the inferred graph.
   * @public
   */
  inferred: boolean | undefined;
}

/**
 * Immediate neighbourhood of an entity.
 * @public
 */
export interface EntityNeighbors {
  /**
   * Neighbour nodes.
   * @public
   */
  nodes: EntityNode[] | undefined;

  /**
   * Edges connecting them.
   * @public
   */
  edges: EntityEdge[] | undefined;

  /**
   * True when the neighbourhood was capped by the request limit.
   * @public
   */
  truncated: boolean | undefined;
}

/**
 * One RDF term: IRI or literal (with optional datatype and language).
 * @public
 */
export interface EntityTerm {
  /**
   * `iri` or `literal`.
   * @public
   */
  kind: string | undefined;

  /**
   * Lexical value of the term.
   * @public
   */
  value: string | undefined;

  /**
   * IRI form; present when `kind` is `iri`.
   * @public
   */
  iri?: string | undefined;

  /**
   * Datatype IRI for typed literals.
   * @public
   */
  datatype?: string | undefined;

  /**
   * BCP-47 language tag for language-tagged literals.
   * @public
   */
  lang?: string | undefined;
}

/**
 * One property and its values on the entity.
 * @public
 */
export interface EntityProperty {
  /**
   * Property IRI.
   * @public
   */
  property: string | undefined;

  /**
   * Property label.
   * @public
   */
  label: string | undefined;

  /**
   * Values asserted for the property.
   * @public
   */
  values: EntityTerm[] | undefined;
}

/**
 * One fact-ledger row backing a statement on the entity.
 * @public
 */
export interface EntityProvenanceItem {
  /**
   * Assertion-row identifier.
   * @public
   */
  factId: string | undefined;

  /**
   * Predicate IRI.
   * @public
   */
  predicate: string | undefined;

  /**
   * Object of the assertion.
   * @public
   */
  object: EntityTerm | undefined;

  /**
   * Ledger state of the row.
   * @public
   */
  state: string | undefined;

  /**
   * Source family recorded on the row.
   * @public
   */
  sourceKind?: string | undefined;

  /**
   * Document that produced the row.
   * @public
   */
  documentId?: string | undefined;

  /**
   * Extraction candidate that produced the row.
   * @public
   */
  candidateId?: string | undefined;

  /**
   * When the row was asserted (ISO-8601).
   * @public
   */
  assertedAt: string | undefined;

  /**
   * True when the row belongs to a conflict group.
   * @public
   */
  conflict: boolean | undefined;
}

/**
 * Fact-ledger provenance for the entity's subject.
 * @public
 */
export interface EntityProvenance {
  /**
   * Number of rows returned.
   * @public
   */
  count: number | undefined;

  /**
   * Ledger rows.
   * @public
   */
  items: EntityProvenanceItem[] | undefined;

  /**
   * True when the ledger could not be read.
   * @public
   */
  unavailable?: boolean | undefined;
}

/**
 * One metric field binding relevant to the entity.
 * @public
 */
export interface RelatedMetricBinding {
  /**
   * Binding role.
   * @public
   */
  role?: string | undefined;

  /**
   * Fact table the metric reads.
   * @public
   */
  factTable?: string | undefined;

  /**
   * Column that holds the entity key.
   * @public
   */
  entityColumn?: string | undefined;
}

/**
 * One metric related to the entity.
 * @public
 */
export interface RelatedMetric {
  /**
   * Metric identifier.
   * @public
   */
  metricId: string | undefined;

  /**
   * Chinese metric name.
   * @public
   */
  nameZh?: string | undefined;

  /**
   * Metric domain.
   * @public
   */
  domain?: string | undefined;

  /**
   * Metric grain.
   * @public
   */
  grain?: string | undefined;

  /**
   * Whether the metric is publishable.
   * @public
   */
  publishable?: boolean | undefined;

  /**
   * Field bindings that connect the metric to the entity.
   * @public
   */
  bindings: RelatedMetricBinding[] | undefined;

  /**
   * Why the metric matched the entity.
   * @public
   */
  matchBasis: string[] | undefined;
}

/**
 * Metrics related to the entity, with the match verdict.
 * @public
 */
export interface EntityRelatedMetrics {
  /**
   * `matched`, `empty`, or `unavailable`.
   * @public
   */
  status: string | undefined;

  /**
   * Why no metrics matched, when status is `empty` or `unavailable`.
   * @public
   */
  reason?: string | undefined;

  /**
   * Related metrics.
   * @public
   */
  items: RelatedMetric[] | undefined;

  /**
   * Bases used to match metrics.
   * @public
   */
  matchBasis: string[] | undefined;
}

/**
 * One property required by a class of the entity.
 * @public
 */
export interface EntityRequired {
  /**
   * Property IRI.
   * @public
   */
  property: string | undefined;

  /**
   * Property label.
   * @public
   */
  label: string | undefined;

  /**
   * Minimum cardinality the class declares.
   * @public
   */
  minCount: number | undefined;

  /**
   * Classes that declare the requirement.
   * @public
   */
  declaredOn: string[] | undefined;

  /**
   * Values present on the entity.
   * @public
   */
  values: EntityTerm[] | undefined;

  /**
   * Number of values present.
   * @public
   */
  valueCount: number | undefined;

  /**
   * True when `valueCount` meets `minCount`.
   * @public
   */
  satisfied: boolean | undefined;
}

/**
 * One evidence source for the entity.
 * @public
 */
export interface EntitySource {
  /**
   * Source family.
   * @public
   */
  kind: string | undefined;

  /**
   * Source reference.
   * @public
   */
  ref: string | undefined;

  /**
   * Text span, when the source is a document chunk.
   * @public
   */
  text?: string | undefined;

  /**
   * Console URL that resolves the reference.
   * @public
   */
  resolveUrl: string | undefined;

  /**
   * Link intended for direct rendering.
   * @public
   */
  href: string | undefined;
}

/**
 * T-Box snapshot the read was evaluated against.
 * @public
 */
export interface EntityTbox {
  /**
   * Published version identifier.
   * @public
   */
  versionId?: string | undefined;

  /**
   * Published semantic version.
   * @public
   */
  semver?: string | undefined;

  /**
   * Named graph that holds the T-Box.
   * @public
   */
  graph?: string | undefined;
}

/**
 * One A-Box entity with its class, property, neighbourhood and metric view.
 * @public
 */
export interface EntityDetail {
  /**
   * Entity IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label.
   * @public
   */
  label: string | undefined;

  /**
   * Classes asserted or inferred for the entity.
   * @public
   */
  classes: EntityClass[] | undefined;

  /**
   * Properties required by those classes.
   * @public
   */
  requiredProperties: EntityRequired[] | undefined;

  /**
   * Overall verdict for required properties.
   * @public
   */
  requiredStatus: string | undefined;

  /**
   * All properties and values on the entity.
   * @public
   */
  properties: EntityProperty[] | undefined;

  /**
   * Immediate neighbourhood.
   * @public
   */
  neighbors: EntityNeighbors | undefined;

  /**
   * Number of instances of the entity's first class.
   * @public
   */
  instanceCount: number | undefined;

  /**
   * Metrics that reference the entity.
   * @public
   */
  relatedMetrics: EntityRelatedMetrics | undefined;

  /**
   * Evidence sources.
   * @public
   */
  sources: EntitySource[] | undefined;

  /**
   * Evidence badge for the entity as a whole.
   * @public
   */
  evidenceBadge: EntityBadge | undefined;

  /**
   * T-Box snapshot used for the read; absent when no T-Box is published.
   * @public
   */
  tbox?: EntityTbox | undefined;

  /**
   * When the sample was taken (ISO-8601).
   * @public
   */
  sampledAt: string | undefined;

  /**
   * Named graphs that supplied the returned statements.
   * @public
   */
  namedGraphs: string[] | undefined;

  /**
   * Fact-ledger rows for this subject.
   * @public
   */
  provenance: EntityProvenance | undefined;
}

/**
 * @public
 */
export interface GetEntityInput {
  /**
   * Percent-encoded IRI of the entity.
   * @public
   */
  entityId: string | undefined;

  /**
   * Maximum neighbours and properties to sample (1-200).
   * @public
   */
  limit?: number | undefined;
}

/**
 * One PROV activity related to the entity.
 * @public
 */
export interface ProvenanceActivity {
  /**
   * Activity IRI.
   * @public
   */
  activityId: string | undefined;

  /**
   * Relation between the entity and the activity.
   * @public
   */
  relation: string | undefined;

  /**
   * Object of the relation, when any.
   * @public
   */
  object?: string | undefined;

  /**
   * Named graph that holds the relation.
   * @public
   */
  graph?: string | undefined;
}

/**
 * One citation that resolves a field value.
 * @public
 */
export interface ProvenanceCitation {
  /**
   * Citation kind.
   * @public
   */
  kind: string | undefined;

  /**
   * Citation reference.
   * @public
   */
  ref?: string | undefined;

  /**
   * Text span of the citation.
   * @public
   */
  text?: string | undefined;

  /**
   * Document that contains the citation.
   * @public
   */
  documentId?: string | undefined;

  /**
   * Console URL for the citation.
   * @public
   */
  url?: string | undefined;
}

/**
 * One resolution link attached to a provenance field.
 * @public
 */
export interface ProvenanceLink {
  /**
   * Link kind: `source_ref`, `fact`, `fact_binding`, or `prov`.
   * @public
   */
  kind: string | undefined;

  /**
   * Referenced identifier.
   * @public
   */
  ref?: string | undefined;

  /**
   * Console URL for the reference.
   * @public
   */
  url?: string | undefined;

  /**
   * Document that owns the reference, when any.
   * @public
   */
  documentId?: string | undefined;
}

/**
 * One field with its three-state evidence badge.
 * @public
 */
export interface ProvenanceField {
  /**
   * Property IRI.
   * @public
   */
  property: string | undefined;

  /**
   * Property label.
   * @public
   */
  label: string | undefined;

  /**
   * Values asserted for the property.
   * @public
   */
  values: EntityTerm[] | undefined;

  /**
   * Lexical form of the first literal value.
   * @public
   */
  valueText?: string | undefined;

  /**
   * True when the triple is asserted in the A-Box.
   * @public
   */
  asserted: boolean | undefined;

  /**
   * True when the triple exists only in the inferred graph.
   * @public
   */
  inferredOnly: boolean | undefined;

  /**
   * Three-state evidence badge.
   * @public
   */
  badge: EntityBadge | undefined;

  /**
   * True when a source reference resolves the value.
   * @public
   */
  hasSourceRef: boolean | undefined;

  /**
   * True when a PROV activity or source reference backs the value.
   * @public
   */
  hasProv: boolean | undefined;

  /**
   * Resolved evidence links.
   * @public
   */
  links: ProvenanceLink[] | undefined;
}

/**
 * Aggregate coverage of the three evidence states.
 * @public
 */
export interface ProvenanceSummary {
  /**
   * Number of fields.
   * @public
   */
  total: number | undefined;

  /**
   * Fields with resolved evidence.
   * @public
   */
  evidenced: number | undefined;

  /**
   * Fields backed only by inference.
   * @public
   */
  inferred: number | undefined;

  /**
   * Fields with no evidence.
   * @public
   */
  none: number | undefined;

  /**
   * Fields with a source reference.
   * @public
   */
  withSourceRef: number | undefined;

  /**
   * Fields with a PROV link.
   * @public
   */
  withProv: number | undefined;

  /**
   * Share of fields that are not `none` (0-1).
   * @public
   */
  coverageRate: number | undefined;
}

/**
 * Per-field provenance report for one entity.
 * @public
 */
export interface EntityProvenanceReport {
  /**
   * Entity IRI.
   * @public
   */
  iri: string | undefined;

  /**
   * Display label.
   * @public
   */
  label: string | undefined;

  /**
   * Fields with evidence badges.
   * @public
   */
  fields: ProvenanceField[] | undefined;

  /**
   * Statement view; mirrors `fields` for the statement table.
   * @public
   */
  statements: ProvenanceField[] | undefined;

  /**
   * PROV activities related to the entity.
   * @public
   */
  activities: ProvenanceActivity[] | undefined;

  /**
   * Citations that resolve field values.
   * @public
   */
  citations: ProvenanceCitation[] | undefined;

  /**
   * Aggregate coverage.
   * @public
   */
  summary: ProvenanceSummary | undefined;

  /**
   * Evidence badge for the entity as a whole.
   * @public
   */
  evidenceBadge: EntityBadge | undefined;

  /**
   * Named graphs that supplied the returned statements.
   * @public
   */
  namedGraphs: string[] | undefined;

  /**
   * Fact-ledger rows for this subject.
   * @public
   */
  provenance: EntityProvenance | undefined;

  /**
   * True when the entity has no properties.
   * @public
   */
  empty: boolean | undefined;

  /**
   * Why the report is empty, when it is.
   * @public
   */
  emptyReason?: string | undefined;

  /**
   * Fixed note explaining the badge semantics.
   * @public
   */
  note: string | undefined;
}

/**
 * @public
 */
export interface GetEntityProvenanceInput {
  /**
   * Percent-encoded IRI of the entity.
   * @public
   */
  entityId: string | undefined;

  /**
   * Maximum fields and neighbours to sample (1-200).
   * @public
   */
  limit?: number | undefined;
}

/**
 * @public
 */
export interface AssertFactInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

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
   * Object value; an IRI when `objectKind` is `iri`.
   * @public
   */
  object: string | undefined;

  /**
   * `iri` or `literal`.
   * @public
   */
  objectKind: FactObjectKind | undefined;

  /**
   * Named graph the assertion belongs to.
   * @public
   */
  graph?: string | undefined;

  /**
   * Source family recorded on the row.
   * @public
   */
  sourceKind?: FactSourceKind | undefined;

  /**
   * Document that produced the row, when any.
   * @public
   */
  sourceDocumentId?: string | undefined;

  /**
   * Ingestion run that produced the row, when any.
   * @public
   */
  sourceRunId?: string | undefined;

  /**
   * Identity recorded on the assert event.
   * @public
   */
  actor?: string | undefined;
}

/**
 * One entry in a fact's hash-chained event history.
 * @public
 */
export interface FactEvent {
  /**
   * Monotonic event identifier within the ledger.
   * @public
   */
  eventId: number | undefined;

  /**
   * Fact the event belongs to.
   * @public
   */
  factId: string | undefined;

  /**
   * Event name, e.g. `assert`, `retract`, `restore`, `merge`, `undo`.
   * @public
   */
  action: string | undefined;

  /**
   * Identity that performed the action.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the action was taken.
   * @public
   */
  reason?: string | undefined;

  /**
   * Batch identifier shared by a bulk operation.
   * @public
   */
  batchId?: string | undefined;

  /**
   * Event-specific payload written by the ledger.
   * @public
   */
  payload?: __DocumentType | undefined;

  /**
   * Previous event in the hash chain; absent for the first event.
   * @public
   */
  prevEvent?: number | undefined;

  /**
   * Hash of this event, chained from `prevEvent`.
   * @public
   */
  hash?: string | undefined;

  /**
   * When the event was written (ISO-8601).
   * @public
   */
  createdAt?: string | undefined;
}

/**
 * RDF object of an assertion row.
 * @public
 */
export interface FactObject {
  /**
   * `iri` or `literal`.
   * @public
   */
  kind: string | undefined;

  /**
   * Lexical value of the object.
   * @public
   */
  value: string | undefined;

  /**
   * IRI form of the object; present when `kind` is `iri`.
   * @public
   */
  iri?: string | undefined;
}

/**
 * Provenance attached to an assertion row.
 * @public
 */
export interface FactSource {
  /**
   * Source family: `document`, `table`, `manual`, or `merge`.
   * @public
   */
  kind?: string | undefined;

  /**
   * Document that produced the row, when any.
   * @public
   */
  documentId?: string | undefined;

  /**
   * Ingestion run that produced the row, when any.
   * @public
   */
  runId?: string | undefined;

  /**
   * Extraction candidate that produced the row, when any.
   * @public
   */
  candidateId?: string | undefined;
}

/**
 * One assertion row as returned by the ledger.
 * @public
 */
export interface FactRecord {
  /**
   * Stable assertion-row identifier.
   * @public
   */
  factId: string | undefined;

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
   * Object of the assertion.
   * @public
   */
  object: FactObject | undefined;

  /**
   * Named graph the assertion belongs to.
   * @public
   */
  graph: string | undefined;

  /**
   * Lifecycle state of the row.
   * @public
   */
  state: FactState | undefined;

  /**
   * Where the row came from.
   * @public
   */
  source?: FactSource | undefined;

  /**
   * When the row was first asserted (ISO-8601).
   * @public
   */
  assertedAt?: string | undefined;

  /**
   * When the row was retracted (ISO-8601); absent while active.
   * @public
   */
  retractedAt?: string | undefined;

  /**
   * Reason recorded on retraction.
   * @public
   */
  retractReason?: string | undefined;

  /**
   * True when the caller accepted the conflict without picking a value.
   * @public
   */
  acceptedConflict?: boolean | undefined;

  /**
   * Adjudication applied to the row: `keep`, `keep_both`, or `merge`.
   * @public
   */
  resolution?: string | undefined;

  /**
   * Identity that adjudicated the conflict.
   * @public
   */
  resolvedBy?: string | undefined;

  /**
   * When the conflict was adjudicated (ISO-8601).
   * @public
   */
  resolvedAt?: string | undefined;

  /**
   * Row that superseded this one after a merge.
   * @public
   */
  supersededBy?: string | undefined;

  /**
   * Rows merged into this one.
   * @public
   */
  mergedFrom?: string[] | undefined;

  /**
   * True when the (subject, predicate) group currently has a conflict.
   * @public
   */
  conflict?: boolean | undefined;

  /**
   * True when an identical assertion row already existed and was reused by
   * `AssertFact`; absent on reads.
   * @public
   */
  duplicate?: boolean | undefined;

  /**
   * Event history, present only on `GetFact` with events requested.
   * @public
   */
  events?: FactEvent[] | undefined;
}

/**
 * @public
 */
export interface BatchKeepFactConflictsInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Value to keep in every matched group; required.
   * @public
   */
  keep: string | undefined;

  /**
   * Only groups with this predicate.
   * @public
   */
  predicate?: string | undefined;

  /**
   * Only groups with this subject.
   * @public
   */
  subject?: string | undefined;

  /**
   * Only groups that contain a row from this document.
   * @public
   */
  sourceDocumentId?: string | undefined;

  /**
   * Identity recorded on every adjudication event; defaults to
   * `operator`.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the rule is applied.
   * @public
   */
  reason?: string | undefined;

  /**
   * Preview only; defaults to true.
   * @public
   */
  dryRun?: boolean | undefined;
}

/**
 * One group of a batch keep. `status` is one of `would_keep` (dry run),
 * `kept`, or `skipped`.
 * @public
 */
export interface FactBatchKeepRow {
  /**
   * IRI of a subject, predicate or object in the namespace A-Box.
   * @public
   */
  subject: string | undefined;

  /**
   * IRI of a subject, predicate or object in the namespace A-Box.
   * @public
   */
  predicate: string | undefined;

  /**
   * One of `would_keep` (dry run), `kept`, or `skipped`.
   * @public
   */
  status: string | undefined;

  /**
   * Facts retired by this row (0 for a skipped group).
   * @public
   */
  retired?: number | undefined;

  /**
   * Why the group was skipped.
   * @public
   */
  reason?: string | undefined;

  /**
   * Values the group had before the decision.
   * @public
   */
  values?: string[] | undefined;

  /**
   * Assertion rows kept by a `kept` row; absent on a dry run.
   * @public
   */
  keptFactIds?: string[] | undefined;

  /**
   * Assertion rows retired by a `kept` row; absent on a dry run.
   * @public
   */
  retiredFactIds?: string[] | undefined;
}

/**
 * Result of `batch`: the scope that was applied and what it touched.
 * @public
 */
export interface FactBatchKeepResult {
  /**
   * Identifier shared by every event this batch wrote.
   * @public
   */
  batchId: string | undefined;

  /**
   * True when nothing was written (the default).
   * @public
   */
  dryRun: boolean | undefined;

  /**
   * Value the rule keeps.
   * @public
   */
  keep: string | undefined;

  /**
   * Pending groups inside the scope.
   * @public
   */
  matched: number | undefined;

  /**
   * Groups kept (or that would be kept, on a dry run).
   * @public
   */
  kept: number | undefined;

  /**
   * Groups where `keep` is not one of the values.
   * @public
   */
  skipped: number | undefined;

  /**
   * Facts retired across the matched groups.
   * @public
   */
  affectedFacts: number | undefined;

  /**
   * Scope the caller supplied; absent members did not narrow it.
   * @public
   */
  subject?: string | undefined;

  /**
   * IRI of a subject, predicate or object in the namespace A-Box.
   * @public
   */
  predicate?: string | undefined;

  /**
   * UUID v4 identifier.
   * @public
   */
  sourceDocumentId?: string | undefined;

  /**
   * Per-group outcome, in ledger order.
   * @public
   */
  results?: FactBatchKeepRow[] | undefined;
}

/**
 * @public
 */
export interface GetFactInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Assertion-row identifier.
   * @public
   */
  factId: string | undefined;
}

/**
 * Effective state of a conflict group after replaying its adjudications.
 * @public
 */
export interface FactAdjudicationEffective {
  /**
   * Number of active rows in the group.
   * @public
   */
  activeCount: number | undefined;

  /**
   * Values still active.
   * @public
   */
  values: string[] | undefined;

  /**
   * True when the active values still conflict.
   * @public
   */
  conflict: boolean | undefined;

  /**
   * True when the conflict was explicitly accepted.
   * @public
   */
  acceptedConflict: boolean | undefined;
}

/**
 * One event in an adjudication's history.
 * @public
 */
export interface FactAdjudicationEvent {
  /**
   * Monotonic event identifier.
   * @public
   */
  eventId: number | undefined;

  /**
   * Event name (`keep`, `keep_both`, `merge`, `undo`).
   * @public
   */
  action: string | undefined;

  /**
   * Identity that performed the action.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the action was taken.
   * @public
   */
  reason?: string | undefined;

  /**
   * When the event was written (ISO-8601).
   * @public
   */
  at: string | undefined;

  /**
   * Event-specific payload.
   * @public
   */
  payload?: __DocumentType | undefined;
}

/**
 * The decision that a subsequent undo reverted.
 * @public
 */
export interface FactUndoReference {
  /**
   * Event identifier of the undo.
   * @public
   */
  eventId: number | undefined;

  /**
   * Identity that performed the undo.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the decision was undone.
   * @public
   */
  reason?: string | undefined;

  /**
   * When the undo was written (ISO-8601).
   * @public
   */
  at: string | undefined;
}

/**
 * Adjudication summary for one conflict group.
 * @public
 */
export interface FactAdjudication {
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
   * Event identifier of the effective decision; absent before any decision.
   * @public
   */
  eventId?: number | undefined;

  /**
   * Action of the effective decision; absent before any decision.
   * @public
   */
  action?: string | undefined;

  /**
   * Identity that made the effective decision.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the effective decision was made.
   * @public
   */
  reason?: string | undefined;

  /**
   * When the effective decision was made (ISO-8601).
   * @public
   */
  at: string | undefined;

  /**
   * `in_effect` when the decision still applies, `undone` after an undo.
   * @public
   */
  status: string | undefined;

  /**
   * Value kept by a `keep` decision.
   * @public
   */
  kept?: string | undefined;

  /**
   * Values the group had when the decision was made.
   * @public
   */
  values: string[] | undefined;

  /**
   * Merged value written by a `merge` decision.
   * @public
   */
  object?: string | undefined;

  /**
   * Undo that reverted this decision, when status is `undone`.
   * @public
   */
  undoneBy?: FactUndoReference | undefined;

  /**
   * Full adjudication history, oldest first.
   * @public
   */
  history: FactAdjudicationEvent[] | undefined;

  /**
   * State recomputed from the surviving rows.
   * @public
   */
  effective: FactAdjudicationEffective | undefined;
}

/**
 * Text evidence attached to a conflicting row.
 * @public
 */
export interface FactConflictEvidence {
  /**
   * Chunk identifier inside the source document.
   * @public
   */
  chunkId?: string | undefined;

  /**
   * Text span that produced the value.
   * @public
   */
  text?: string | undefined;
}

/**
 * One fact backing a conflicting value.
 * @public
 */
export interface FactConflictFact {
  /**
   * Assertion-row identifier.
   * @public
   */
  factId: string | undefined;

  /**
   * Object value this row asserts.
   * @public
   */
  object: string | undefined;

  /**
   * `iri` or `literal`.
   * @public
   */
  objectKind: string | undefined;

  /**
   * Where the row came from.
   * @public
   */
  source?: FactSource | undefined;

  /**
   * When the row was asserted (ISO-8601).
   * @public
   */
  assertedAt?: string | undefined;

  /**
   * Text evidence that produced the row.
   * @public
   */
  evidence?: FactConflictEvidence | undefined;
}

/**
 * One (subject, predicate) group with more than one active value.
 * @public
 */
export interface FactConflict {
  /**
   * Subject IRI shared by the group.
   * @public
   */
  subject: string | undefined;

  /**
   * Predicate IRI shared by the group.
   * @public
   */
  predicate: string | undefined;

  /**
   * Distinct values in the group.
   * @public
   */
  values: string[] | undefined;

  /**
   * True when the group was accepted as a conflict without a single winner.
   * @public
   */
  accepted: boolean | undefined;

  /**
   * True when the group still needs a decision.
   * @public
   */
  pending: boolean | undefined;

  /**
   * Rows backing the group.
   * @public
   */
  facts: FactConflictFact[] | undefined;
}

/**
 * Conflict groups and their adjudication state.
 * @public
 */
export interface FactConflictList {
  /**
   * Groups in ledger order.
   * @public
   */
  conflicts: FactConflict[] | undefined;

  /**
   * Number of groups in this page.
   * @public
   */
  count: number | undefined;

  /**
   * Groups that still need a decision.
   * @public
   */
  pending: number | undefined;

  /**
   * True when accepted conflicts were included.
   * @public
   */
  includeAccepted?: boolean | undefined;

  /**
   * Adjudication summary for every returned group.
   * @public
   */
  adjudications?: FactAdjudication[] | undefined;
}

/**
 * @public
 */
export interface ListFactConflictsInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Include groups the caller already accepted; false by default.
   * @public
   */
  includeAccepted?: boolean | undefined;
}

/**
 * One page of a fact's event chain.
 * @public
 */
export interface FactEventPage {
  /**
   * Fact the page belongs to.
   * @public
   */
  factId: string | undefined;

  /**
   * Number of events in this page.
   * @public
   */
  count: number | undefined;

  /**
   * Total number of events on the chain.
   * @public
   */
  total: number | undefined;

  /**
   * Events, newest first.
   * @public
   */
  items: FactEvent[] | undefined;

  /**
   * Pass back as `before` to page further back; absent at the start.
   * @public
   */
  nextBefore?: number | undefined;
}

/**
 * @public
 */
export interface ListFactEventsInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Assertion-row identifier.
   * @public
   */
  factId: string | undefined;

  /**
   * Maximum events to return (1-200).
   * @public
   */
  limit?: number | undefined;

  /**
   * Return events strictly older than this event identifier.
   * @public
   */
  before?: number | undefined;

  /**
   * `full` includes the payload document; `summary` omits it.
   * @public
   */
  format?: FactEventFormat | undefined;
}

/**
 * Facts matching a `ListFacts` query.
 * @public
 */
export interface FactList {
  /**
   * State filter that produced this page; `all` when not narrowed.
   * @public
   */
  state: string | undefined;

  /**
   * Rows in ledger order.
   * @public
   */
  items: FactRecord[] | undefined;

  /**
   * Number of rows in this page.
   * @public
   */
  count: number | undefined;

  /**
   * Conflict groups touching the returned rows.
   * @public
   */
  conflicts?: FactConflict[] | undefined;
}

/**
 * @public
 */
export interface ListFactsInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Only rows in this state; `all` when omitted.
   * @public
   */
  state?: FactStateFilter | undefined;

  /**
   * Only rows with this subject.
   * @public
   */
  subject?: string | undefined;

  /**
   * Only rows with this predicate.
   * @public
   */
  predicate?: string | undefined;

  /**
   * Only rows produced by this document.
   * @public
   */
  sourceDocumentId?: string | undefined;

  /**
   * When true, only rows in a conflicting group; when false, only rows
   * outside a conflict.
   * @public
   */
  conflict?: boolean | undefined;

  /**
   * Maximum rows to return (1-500).
   * @public
   */
  limit?: number | undefined;
}

/**
 * Outcome of one adjudication. Only the members for the chosen `action` are
 * populated: `keep` fills kept/retired, `keep_both` fills acceptedFactIds,
 * `merge` fills mergedFactId/originalFactIds, `batch` fills batch.
 * @public
 */
export interface FactConflictResolutionOutcome {
  /**
   * Adjudication applied to a conflict group. Wire values stay lowercase
   * because the ledger and the console have used them since the first
   * release; the model follows the wire rather than renaming it.
   * @public
   */
  action: FactConflictAction | undefined;

  /**
   * Conflict group subject; absent on `batch` when the scope did not
   * narrow by subject.
   * @public
   */
  subject?: string | undefined;

  /**
   * Conflict group predicate; absent on `batch` when the scope did not
   * narrow by predicate.
   * @public
   */
  predicate?: string | undefined;

  /**
   * Value kept by `keep`.
   * @public
   */
  kept?: string | undefined;

  /**
   * Assertion rows kept by `keep`.
   * @public
   */
  keptFactIds?: string[] | undefined;

  /**
   * Assertion rows retired by `keep`.
   * @public
   */
  retiredFactIds?: string[] | undefined;

  /**
   * Number of retired rows (`keep`).
   * @public
   */
  retired?: number | undefined;

  /**
   * Values the group had before the decision.
   * @public
   */
  values?: string[] | undefined;

  /**
   * Assertion rows accepted by `keep_both`.
   * @public
   */
  acceptedFactIds?: string[] | undefined;

  /**
   * New assertion row written by `merge`.
   * @public
   */
  mergedFactId?: string | undefined;

  /**
   * Rows `merge` retired, in ledger order.
   * @public
   */
  originalFactIds?: string[] | undefined;

  /**
   * Batch outcome (`batch` only).
   * @public
   */
  batch?: FactBatchKeepResult | undefined;
}

/**
 * @public
 */
export interface ResolveFactConflictsInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Conflict group subject. Required unless `action` is `batch`.
   * @public
   */
  subject?: string | undefined;

  /**
   * Conflict group predicate. Required unless `action` is `batch`.
   * @public
   */
  predicate?: string | undefined;

  /**
   * Adjudication applied to a conflict group. Wire values stay lowercase
   * because the ledger and the console have used them since the first
   * release; the model follows the wire rather than renaming it.
   * @public
   */
  action: FactConflictAction | undefined;

  /**
   * Value to keep (`batch` only; `keep` takes it from `keep` on the
   * console path, which sends the chosen value here too).
   * @public
   */
  keep?: string | undefined;

  /**
   * Value that replaces the conflicting ones (`merge`).
   * @public
   */
  mergedObject?: string | undefined;

  /**
   * `iri` (default) or `literal`.
   * @public
   */
  mergedObjectKind?: string | undefined;

  /**
   * Graph for the merged fact; defaults to the group's graph.
   * @public
   */
  graph?: string | undefined;

  /**
   * Scope by source document (`batch`).
   * @public
   */
  sourceDocumentId?: string | undefined;

  /**
   * Preview only (`batch`); defaults to true.
   * @public
   */
  dryRun?: boolean | undefined;

  /**
   * Identity recorded on the audit event; defaults to `operator`.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the decision was taken.
   * @public
   */
  reason?: string | undefined;
}

/**
 * @public
 */
export interface RestoreFactInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Assertion-row identifier.
   * @public
   */
  factId: string | undefined;

  /**
   * Identity recorded on the restore event; defaults to `api`.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the row is restored.
   * @public
   */
  reason?: string | undefined;
}

/**
 * @public
 */
export interface RetractFactInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Assertion-row identifier.
   * @public
   */
  factId: string | undefined;

  /**
   * Identity recorded on the retract event; defaults to `api`.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the row is withdrawn.
   * @public
   */
  reason?: string | undefined;
}

/**
 * One fact selected by a batch retract.
 * @public
 */
export interface FactRetractItem {
  /**
   * Assertion-row identifier.
   * @public
   */
  factId: string | undefined;

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
   * Object value.
   * @public
   */
  object: string | undefined;

  /**
   * `iri` or `literal`.
   * @public
   */
  objectKind: string | undefined;

  /**
   * Named graph.
   * @public
   */
  graph: string | undefined;

  /**
   * Extraction candidate that produced the row, when any.
   * @public
   */
  candidateId?: string | undefined;
}

/**
 * One fact skipped by a batch retract.
 * @public
 */
export interface FactRetractSkipped {
  /**
   * Assertion-row identifier.
   * @public
   */
  factId: string | undefined;

  /**
   * Why the row was skipped.
   * @public
   */
  reason: string | undefined;
}

/**
 * Result of a batch retract.
 *
 * `dryRun` defaults to true: an omitted flag can only preview. When `dryRun`
 * is false, `batchId` is set and every retracted row shares it.
 * @public
 */
export interface FactBatchRetractResult {
  /**
   * True when the call only previewed the retract.
   * @public
   */
  dryRun: boolean | undefined;

  /**
   * Batch identifier written by the retract; absent on a dry run.
   * @public
   */
  batchId?: string | undefined;

  /**
   * Number of rows that are (or would be) retracted.
   * @public
   */
  count: number | undefined;

  /**
   * Rows that are (or would be) retracted.
   * @public
   */
  items: FactRetractItem[] | undefined;

  /**
   * Rows filtered out of the selection.
   * @public
   */
  skipped: FactRetractSkipped[] | undefined;

  /**
   * Identity recorded on the audit events.
   * @public
   */
  actor: string | undefined;

  /**
   * Why the rows were retracted.
   * @public
   */
  reason?: string | undefined;

  /**
   * Identifiers of the retracted rows; absent on a dry run.
   * @public
   */
  retracted?: string[] | undefined;
}

/**
 * @public
 */
export interface RetractFactsInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Explicit rows to retract (1-500); wins over the filters.
   * @public
   */
  factIds?: string[] | undefined;

  /**
   * Filter: only rows with this subject.
   * @public
   */
  subject?: string | undefined;

  /**
   * Filter: only rows with this predicate.
   * @public
   */
  predicate?: string | undefined;

  /**
   * Filter: only rows in this named graph.
   * @public
   */
  graph?: string | undefined;

  /**
   * Filter: only rows produced by this document.
   * @public
   */
  sourceDocumentId?: string | undefined;

  /**
   * Identity recorded on every retract event; defaults to `operator`.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the rows are withdrawn.
   * @public
   */
  reason?: string | undefined;

  /**
   * Preview only; defaults to true.
   * @public
   */
  dryRun?: boolean | undefined;
}

/**
 * Result of undoing an adjudication.
 *
 * `keep` and `keep_both` undo restore the retired rows and return them under
 * `restoredFactIds`; `merge` undo removes the merged row and restores the
 * originals under `restoredFactIds`. `dryRun` fills the same members without
 * writing anything.
 * @public
 */
export interface FactUndoResult {
  /**
   * True when the call only previewed the undo.
   * @public
   */
  dryRun: boolean | undefined;

  /**
   * Event identifier written by the undo; absent on a dry run.
   * @public
   */
  eventId?: number | undefined;

  /**
   * Subject IRI of the undone group.
   * @public
   */
  subject: string | undefined;

  /**
   * Predicate IRI of the undone group.
   * @public
   */
  predicate: string | undefined;

  /**
   * Action that was undone.
   * @public
   */
  undoneAction: string | undefined;

  /**
   * Rows restored by the undo.
   * @public
   */
  restoredFactIds?: string[] | undefined;

  /**
   * Merged row removed by the undo (`merge` only).
   * @public
   */
  mergedFactId?: string | undefined;

  /**
   * Active values after the undo.
   * @public
   */
  values?: string[] | undefined;

  /**
   * True when the group conflicts again after the undo.
   * @public
   */
  conflict?: boolean | undefined;
}

/**
 * @public
 */
export interface UndoFactConflictResolutionInput {
  /**
   * Namespace that owns the ledger partition.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Adjudication event to undo; alternative to subject + predicate.
   * @public
   */
  eventId?: number | undefined;

  /**
   * Subject of the group; required when `eventId` is absent.
   * @public
   */
  subject?: string | undefined;

  /**
   * Predicate of the group; required when `eventId` is absent.
   * @public
   */
  predicate?: string | undefined;

  /**
   * Identity recorded on the undo event; defaults to `operator`.
   * @public
   */
  actor?: string | undefined;

  /**
   * Why the decision is being undone.
   * @public
   */
  reason?: string | undefined;

  /**
   * Preview only; defaults to true.
   * @public
   */
  dryRun?: boolean | undefined;
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
 * @public
 */
export interface ListIngestionRunsInput {
  /**
   * Namespace whose runs are listed.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Run family; defaults to BATCH and only BATCH is implemented.
   * @public
   */
  kind?: IngestionRunKind | undefined;

  /**
   * Optional lifecycle-status filter.
   * @public
   */
  status?: IngestionRunStatus | undefined;

  /**
   * Pagination token from a previous response.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Maximum runs per page (default and maximum 50).
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * One failed item surfaced in the inline failure feed.
 * @public
 */
export interface IngestionFailure {
  /**
   * Batch the failed item belongs to.
   * @public
   */
  runId: string | undefined;

  /**
   * Item path relative to the batch root.
   * @public
   */
  relPath: string | undefined;

  /**
   * Number of processing attempts so far.
   * @public
   */
  attempts: number | undefined;

  /**
   * Machine-readable failure code, when the importer recorded one.
   * @public
   */
  code?: string | undefined;

  /**
   * Human-readable failure message, when the importer recorded one.
   * @public
   */
  message?: string | undefined;

  /**
   * When the item last changed.
   * @public
   */
  updatedAt: Date | undefined;
}

/**
 * One import batch and its per-item counters.
 * @public
 */
export interface IngestionRun {
  /**
   * Stable batch identifier (platform.import_batch.batch_id).
   * @public
   */
  runId: string | undefined;

  /**
   * Filesystem root that was imported.
   * @public
   */
  root: string | undefined;

  /**
   * Current lifecycle state.
   * @public
   */
  status: IngestionRunStatus | undefined;

  /**
   * True when status is STALE.
   * @public
   */
  stale: boolean | undefined;

  /**
   * Machine-readable stale reason; present only when stale is true.
   * @public
   */
  staleReason?: string | undefined;

  /**
   * Discovered items in this batch.
   * @public
   */
  total: number | undefined;

  /**
   * Items that reached a terminal state (indexed or failed).
   * @public
   */
  completed: number | undefined;

  /**
   * Items indexed successfully.
   * @public
   */
  indexed: number | undefined;

  /**
   * Items that ended in failure.
   * @public
   */
  failed: number | undefined;

  /**
   * Items indexed with degraded quality (for example missing embeddings).
   * @public
   */
  degraded: number | undefined;

  /**
   * When the batch row was created.
   * @public
   */
  createdAt: Date | undefined;

  /**
   * When the batch row last changed.
   * @public
   */
  updatedAt: Date | undefined;

  /**
   * When the batch finished; absent while running.
   * @public
   */
  finishedAt?: Date | undefined;
}

/**
 * Standard pagination output
 * @public
 */
export interface ListIngestionRunsOutput {
  /**
   * Opaque token for fetching the next page; absent when there are no more results.
   * @public
   */
  nextToken?: string | undefined;

  /**
   * Page of ingestion runs.
   * @public
   */
  items: IngestionRun[] | undefined;

  /**
   * Number of runs matching the filter across all pages.
   * @public
   */
  totalCount: number | undefined;

  /**
   * Most recent failed items across the returned page (at most 20).
   * @public
   */
  failures: IngestionFailure[] | undefined;
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
export interface GetMetricFamilyInput {
  /**
   * Namespace that owns the metric family.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Family identifier: the metric id of the family index.
   * @public
   */
  familyId: string | undefined;
}

/**
 * One field that differs (or does not differ) across variants.
 * @public
 */
export interface MetricFamilyDiff {
  /**
   * Field name used for the comparison.
   * @public
   */
  field: string | undefined;

  /**
   * Display label of the field.
   * @public
   */
  label: string | undefined;

  /**
   * metricId -> rendered value.
   * @public
   */
  values: Record<string, string> | undefined;

  /**
   * True when the values are not all equal.
   * @public
   */
  different: boolean | undefined;
}

/**
 * Instruction shown when a family index is opened instead of a variant.
 * @public
 */
export interface MetricFamilyGuidance {
  /**
   * Stable machine code (for example E_METRIC_VARIANT_REQUIRED).
   * @public
   */
  code: string | undefined;

  /**
   * Human-readable explanation.
   * @public
   */
  message: string | undefined;

  /**
   * Ordered steps that resolve the selection.
   * @public
   */
  howTo: string[] | undefined;
}

/**
 * Observation window declared by a variant.
 * @public
 */
export interface MetricFamilyVariantWindow {
  /**
   * Window kind (instant, period, rolling).
   * @public
   */
  kind?: string | undefined;

  /**
   * Minimum window length in days.
   * @public
   */
  minWindowDays?: number | undefined;

  /**
   * Rendered window description.
   * @public
   */
  text?: string | undefined;
}

/**
 * One variant of a metric family.
 * @public
 */
export interface MetricFamilyVariant {
  /**
   * Variant metric id; use this for output calls.
   * @public
   */
  metricId: string | undefined;

  /**
   * Display name of the variant.
   * @public
   */
  nameZh?: string | undefined;

  /**
   * Display label override, when the definition carries one.
   * @public
   */
  displayName?: string | undefined;

  /**
   * Whether the variant may be published at all.
   * @public
   */
  publishable?: boolean | undefined;

  /**
   * Evidence basis (regulatory, industry, none).
   * @public
   */
  evidenceBasis?: string | undefined;

  /**
   * Whether the variant passes the external-eligibility rule.
   * @public
   */
  externalEligible?: boolean | undefined;

  /**
   * Notice shown when the variant is an internal baseline.
   * @public
   */
  internalNotice?: string | undefined;

  /**
   * Formula text as declared by the definition.
   * @public
   */
  formula?: string | undefined;

  /**
   * True when the formula is present but execution is disabled.
   * @public
   */
  formulaDisabled?: boolean | undefined;

  /**
   * Computability tier code.
   * @public
   */
  computability?: string | undefined;

  /**
   * Computability tier label.
   * @public
   */
  computabilityLabel?: string | undefined;

  /**
   * Observation window declared by the variant.
   * @public
   */
  window?: MetricFamilyVariantWindow | undefined;

  /**
   * Denominator expression text, when the definition declares one.
   * @public
   */
  denominator?: string | undefined;

  /**
   * Human-readable denominator description.
   * @public
   */
  denominatorText?: string | undefined;

  /**
   * Grain label (for example policy or agreement).
   * @public
   */
  grain?: string | undefined;

  /**
   * Grain code as stored in the definition.
   * @public
   */
  grainCode?: string | undefined;

  /**
   * Metric kind (ratio, duration, sum, ...).
   * @public
   */
  metricKind?: string | undefined;

  /**
   * Unit of the produced value.
   * @public
   */
  unit?: string | undefined;
}

/**
 * One metric family (a family index plus its variants).
 * @public
 */
export interface MetricFamily {
  /**
   * Family identifier, equal to the index metric id.
   * @public
   */
  familyId: string | undefined;

  /**
   * The metric a caller lands on before choosing a variant.
   * @public
   */
  indexMetricId: string | undefined;

  /**
   * Display name of the family index.
   * @public
   */
  nameZh?: string | undefined;

  /**
   * Always true for a family index: output needs a variant metricId.
   * @public
   */
  selectionRequired: boolean | undefined;

  /**
   * How the caller must choose a variant before producing a value.
   * @public
   */
  guidance: MetricFamilyGuidance | undefined;

  /**
   * Number of variants in this family.
   * @public
   */
  variantCount: number | undefined;

  /**
   * Variants of this family, in metric id order.
   * @public
   */
  variants: MetricFamilyVariant[] | undefined;

  /**
   * Field-by-field differences across variants.
   * @public
   */
  diffs: MetricFamilyDiff[] | undefined;

  /**
   * Store the family was read from.
   * @public
   */
  source: string | undefined;
}

/**
 * @public
 */
export interface GetMetricFamilyOutput {
  /**
   * The family index plus every variant and their differences.
   * @public
   */
  family: MetricFamily | undefined;
}

/**
 * @public
 */
export interface GetMetricReportManifestInput {
  /**
   * Namespace that owns the governed metrics.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * "all" (everything) or "external" (external-eligible candidates only).
   * @public
   */
  scope?: string | undefined;

  /**
   * Optional domain filter.
   * @public
   */
  domain?: string | undefined;

  /**
   * Optional evidence-basis filter.
   * @public
   */
  evidenceBasis?: string | undefined;

  /**
   * Optional publishable filter.
   * @public
   */
  publishable?: boolean | undefined;
}

/**
 * Filters applied to a manifest response.
 * @public
 */
export interface MetricReportFilters {
  /**
   * Applied scope.
   * @public
   */
  scope?: string | undefined;

  /**
   * Applied domain filter.
   * @public
   */
  domain?: string | undefined;

  /**
   * Applied evidence-basis filter.
   * @public
   */
  evidenceBasis?: string | undefined;

  /**
   * Applied publishable filter.
   * @public
   */
  publishable?: boolean | undefined;
}

/**
 * One governed metric row as it appears in the report manifest. Fields left
 * absent were not applicable for that metric; they are never coerced to false.
 * @public
 */
export interface MetricReportItem {
  /**
   * Governed metric id (also the identifier used by /metrics/\{metric_id\}).
   * @public
   */
  metricId: string | undefined;

  /**
   * Display name in Chinese.
   * @public
   */
  nameZh?: string | undefined;

  /**
   * Display label override, when the definition carries one.
   * @public
   */
  displayName?: string | undefined;

  /**
   * Business domain.
   * @public
   */
  domain?: string | undefined;

  /**
   * Whether the metric may be published.
   * @public
   */
  publishable?: boolean | undefined;

  /**
   * Evidence basis (regulatory, industry, none).
   * @public
   */
  evidenceBasis?: string | undefined;

  /**
   * Rendered evidence-basis label.
   * @public
   */
  evidenceBasisLabel?: string | undefined;

  /**
   * Provenance label of the evidence.
   * @public
   */
  evidenceSource?: string | undefined;

  /**
   * True when regulatory text is attached.
   * @public
   */
  hasRegulatoryText?: boolean | undefined;

  /**
   * True when the metric is an industry formula (internal baseline only).
   * @public
   */
  industryBaseline?: boolean | undefined;

  /**
   * Internal-baseline notice, when applicable.
   * @public
   */
  internalNotice?: string | undefined;

  /**
   * True when the metric is flagged as an E1 baseline.
   * @public
   */
  e1Baseline?: boolean | undefined;

  /**
   * Formula text as declared by the definition.
   * @public
   */
  formula?: string | undefined;

  /**
   * Formula expression used for execution, when declared.
   * @public
   */
  formulaExpr?: string | undefined;

  /**
   * Computability tier code.
   * @public
   */
  computability?: string | undefined;

  /**
   * Computability tier label.
   * @public
   */
  computabilityLabel?: string | undefined;

  /**
   * Computability tone used by the UI (ok, warn, blocked).
   * @public
   */
  computabilityTone?: string | undefined;

  /**
   * Short computability gap description.
   * @public
   */
  gap?: string | undefined;

  /**
   * Stable gap code.
   * @public
   */
  gapCode?: string | undefined;

  /**
   * Missing component description, when the metric cannot be computed.
   * @public
   */
  missing?: string | undefined;

  /**
   * Whether the metric passes the external-eligibility rule.
   * @public
   */
  externalEligible?: boolean | undefined;

  /**
   * Stable external status code.
   * @public
   */
  externalStatus?: string | undefined;

  /**
   * Rendered external status label.
   * @public
   */
  externalLabel?: string | undefined;

  /**
   * Why the metric has this external status.
   * @public
   */
  externalReason?: string | undefined;

  /**
   * Execution path code (unavailable, rule_set_only, executable).
   * @public
   */
  executionPath?: string | undefined;

  /**
   * True when the metric can be executed right now.
   * @public
   */
  executable?: boolean | undefined;

  /**
   * Human-readable execution blocker.
   * @public
   */
  executionReason?: string | undefined;

  /**
   * Stable execution blocker code.
   * @public
   */
  executionReasonCode?: string | undefined;

  /**
   * Number of observation rows available.
   * @public
   */
  observationCount?: number | undefined;

  /**
   * Observation window currently available, in days.
   * @public
   */
  availableWindowDays?: number | undefined;

  /**
   * Observation window required by the definition, in days.
   * @public
   */
  minWindowDays?: number | undefined;

  /**
   * True when the available window covers the required window.
   * @public
   */
  windowSufficient?: boolean | undefined;

  /**
   * Window warning shown to the reporter, when applicable.
   * @public
   */
  windowWarning?: string | undefined;

  /**
   * Family index id for a variant metric.
   * @public
   */
  variantOf?: string | undefined;

  /**
   * Output mode (index, rule_set, value).
   * @public
   */
  outputMode?: string | undefined;

  /**
   * True when the formula exists but execution is disabled.
   * @public
   */
  formulaDisabled?: boolean | undefined;

  /**
   * True when the definition is inferred rather than provided.
   * @public
   */
  inference?: boolean | undefined;

  /**
   * Evidence verification status.
   * @public
   */
  evidenceStatus?: string | undefined;

  /**
   * Definition version the row was read from.
   * @public
   */
  definitionVersion?: string | undefined;
}

/**
 * Counter breakdown of the manifest.
 * @public
 */
export interface MetricReportCounts {
  /**
   * Rows with publishable=true.
   * @public
   */
  publishableTrue?: number | undefined;

  /**
   * Rows whose evidence basis is industry.
   * @public
   */
  industry?: number | undefined;

  /**
   * Rows whose evidence basis is regulatory.
   * @public
   */
  regulatory?: number | undefined;

  /**
   * Rows that pass the external-eligibility rule.
   * @public
   */
  externalEligible?: number | undefined;

  /**
   * Rows with external status external_candidate.
   * @public
   */
  externalCandidates?: number | undefined;

  /**
   * Rows executable right now.
   * @public
   */
  executableNow?: number | undefined;

  /**
   * Industry rows excluded from external output.
   * @public
   */
  industryExcludedFromExternal?: number | undefined;

  /**
   * Row count per computability tier.
   * @public
   */
  computability?: Record<string, number> | undefined;
}

/**
 * Execution-path breakdown of the manifest.
 * @public
 */
export interface MetricReportExecution {
  /**
   * Rows with external status external_candidate.
   * @public
   */
  externalCandidates?: number | undefined;

  /**
   * Rows executable right now.
   * @public
   */
  executableNow?: number | undefined;

  /**
   * Rows executable from a rule set only.
   * @public
   */
  ruleSetOnly?: number | undefined;

  /**
   * Rows that cannot be executed yet.
   * @public
   */
  unavailable?: number | undefined;

  /**
   * Unavailable rows counted by reason code.
   * @public
   */
  byReason?: Record<string, number> | undefined;

  /**
   * Basis used by the execution judgement.
   * @public
   */
  basis?: string | undefined;

  /**
   * Explanatory note for the execution judgement.
   * @public
   */
  note?: string | undefined;
}

/**
 * Counters and provenance for the whole manifest.
 * @public
 */
export interface MetricReportMeta {
  /**
   * Generation timestamp (ISO-8601).
   * @public
   */
  generatedAt: string | undefined;

  /**
   * Store the manifest was read from.
   * @public
   */
  source?: string | undefined;

  /**
   * Scope this manifest was generated for.
   * @public
   */
  scope?: string | undefined;

  /**
   * Number of rows in this response.
   * @public
   */
  total?: number | undefined;

  /**
   * Number of rows in the namespace before filtering.
   * @public
   */
  allTotal?: number | undefined;

  /**
   * Counter breakdown.
   * @public
   */
  counts?: MetricReportCounts | undefined;

  /**
   * Execution-path breakdown.
   * @public
   */
  execution?: MetricReportExecution | undefined;

  /**
   * Industry-baseline notice shared by all industry rows.
   * @public
   */
  industryNotice?: string | undefined;

  /**
   * Rule that decides external eligibility.
   * @public
   */
  externalScopeRule?: string | undefined;

  /**
   * Statement that computability does not imply business values exist.
   * @public
   */
  disclaimer?: string | undefined;
}

/**
 * @public
 */
export interface GetMetricReportManifestOutput {
  /**
   * Manifest rows after filtering.
   * @public
   */
  items: MetricReportItem[] | undefined;

  /**
   * Number of rows in items.
   * @public
   */
  count: number | undefined;

  /**
   * Counters and provenance for the whole manifest.
   * @public
   */
  meta: MetricReportMeta | undefined;

  /**
   * Filters that were applied to this response.
   * @public
   */
  filters: MetricReportFilters | undefined;
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
export interface ExportOntologyBundleInput {
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
   * Output directory; the server default when omitted.
   * @public
   */
  out?: string | undefined;

  /**
   * Bundle tag; a generated tag when omitted.
   * @public
   */
  tag?: string | undefined;

  /**
   * Include the A-Box blob store in the bundle.
   * @public
   */
  includeBlobs?: boolean | undefined;

  /**
   * Who runs the export.
   * @public
   */
  actor?: string | undefined;
}

/**
 * Result of `ExportOntologyBundle`.
 * @public
 */
export interface OntologyBundleExportResult {
  /**
   * Always true on success.
   * @public
   */
  ok: boolean | undefined;

  /**
   * Absolute directory the bundle was written to.
   * @public
   */
  bundleDir: string | undefined;

  /**
   * Tag recorded in the manifest.
   * @public
   */
  tag: string | undefined;

  /**
   * Manifest schema version.
   * @public
   */
  schemaVersion?: number | undefined;

  /**
   * Manifest generation time (ISO-8601).
   * @public
   */
  generatedAt?: string | undefined;

  /**
   * T-Box coordinates captured by the bundle.
   * @public
   */
  tbox?: __DocumentType | undefined;

  /**
   * Row counts captured by the bundle.
   * @public
   */
  totals?: Record<string, __DocumentType> | undefined;

  /**
   * Total bytes written.
   * @public
   */
  bytes?: number | undefined;

  /**
   * Number of files written.
   * @public
   */
  files?: number | undefined;

  /**
   * Identity that ran the export.
   * @public
   */
  actor?: string | undefined;
}

/**
 * @public
 */
export interface ImportBundleInput {
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
   * Bundle directory to restore.
   * @public
   */
  bundleRef: string | undefined;

  /**
   * Restore database; defaults to `platform_restore_test` when omitted.
   * @public
   */
  database?: string | undefined;

  /**
   * Drop and recreate the restore database before loading.
   * @public
   */
  replace?: boolean | undefined;

  /**
   * Keep the restore database when a step fails, for inspection.
   * @public
   */
  keepDbOnFailure?: boolean | undefined;

  /**
   * Who runs the restore.
   * @public
   */
  actor?: string | undefined;
}

/**
 * Blob-store outcome after an import.
 * @public
 */
export interface BundleBlobs {
  /**
   * True when the bundle carried blobs.
   * @public
   */
  included?: boolean | undefined;

  /**
   * Blobs present in the bundle.
   * @public
   */
  count?: number | undefined;

  /**
   * Total blob bytes.
   * @public
   */
  bytes?: number | undefined;

  /**
   * Blobs written into the restore target.
   * @public
   */
  written?: number | undefined;

  /**
   * Blobs that already existed in the target.
   * @public
   */
  existing?: number | undefined;
}

/**
 * One post-import consistency check.
 * @public
 */
export interface BundleCheck {
  /**
   * Check name, e.g. `documents` or `vectors`.
   * @public
   */
  name: string | undefined;

  /**
   * Value recorded in the manifest.
   * @public
   */
  exported?: __DocumentType | undefined;

  /**
   * Value observed in the restored database.
   * @public
   */
  imported?: __DocumentType | undefined;

  /**
   * True when the two values agree.
   * @public
   */
  ok: boolean | undefined;

  /**
   * Explanation when the check failed.
   * @public
   */
  detail?: string | undefined;
}

/**
 * Ledger counters and chain verdict after an import.
 * @public
 */
export interface BundleLedger {
  /**
   * Fact events restored.
   * @public
   */
  events?: number | undefined;

  /**
   * Fact assertions restored.
   * @public
   */
  facts?: number | undefined;

  /**
   * True when the restored fact-event chain verifies.
   * @public
   */
  chain?: boolean | undefined;
}

/**
 * T-Box coordinates recorded by an import.
 * @public
 */
export interface BundleTboxRestored {
  /**
   * Version the bundle registered.
   * @public
   */
  versionId?: string | undefined;

  /**
   * Canonical hash of the restored graph.
   * @public
   */
  contentHash?: string | undefined;

  /**
   * Graph IRI the bundle was loaded into.
   * @public
   */
  graph?: string | undefined;
}

/**
 * Result of `ImportBundle`.
 * @public
 */
export interface OntologyBundleImportResult {
  /**
   * True when every restored check agrees.
   * @public
   */
  ok?: boolean | undefined;

  /**
   * Restore database the bundle was loaded into.
   * @public
   */
  database?: string | undefined;

  /**
   * Bundle directory that was imported.
   * @public
   */
  bundle?: string | undefined;

  /**
   * T-Box coordinates registered by the import.
   * @public
   */
  tbox?: BundleTboxRestored | undefined;

  /**
   * Pointer state after the T-Box restore.
   * @public
   */
  tboxPointer?: OntologyPointer | undefined;

  /**
   * A-Box graph the bundle was loaded into.
   * @public
   */
  aboxGraph?: string | undefined;

  /**
   * Post-import consistency checks.
   * @public
   */
  checks?: BundleCheck[] | undefined;

  /**
   * Ledger counters and chain verdict.
   * @public
   */
  ledger?: BundleLedger | undefined;

  /**
   * Blob-store outcome.
   * @public
   */
  blobs?: BundleBlobs | undefined;

  /**
   * Expected row counts from the manifest.
   * @public
   */
  counts?: __DocumentType | undefined;

  /**
   * Step that failed, when `ok` is false.
   * @public
   */
  failedStep?: string | undefined;

  /**
   * Failure message, when `ok` is false.
   * @public
   */
  error?: string | undefined;

  /**
   * Provider error code, when `ok` is false.
   * @public
   */
  providerCode?: string | undefined;

  /**
   * Identity that ran the import.
   * @public
   */
  actor?: string | undefined;
}

/**
 * @public
 */
export interface InspectOntologyBundleInput {
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
   * Bundle directory to inspect.
   * @public
   */
  bundleRef: string | undefined;
}

/**
 * Result of `InspectOntologyBundle`.
 * @public
 */
export interface OntologyBundleInspectResult {
  /**
   * Always true when the manifest verifies.
   * @public
   */
  ok: boolean | undefined;

  /**
   * Path that was inspected.
   * @public
   */
  path: string | undefined;

  /**
   * Tag recorded in the manifest.
   * @public
   */
  tag?: string | undefined;

  /**
   * Row counts recorded in the manifest.
   * @public
   */
  totals?: Record<string, __DocumentType> | undefined;

  /**
   * T-Box coordinates recorded in the manifest.
   * @public
   */
  tbox?: __DocumentType | undefined;

  /**
   * Number of files in the bundle.
   * @public
   */
  files?: number | undefined;
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
export interface FindGraphPathInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * IRI to start from.
   * @public
   */
  start: string | undefined;

  /**
   * IRI to reach.
   * @public
   */
  end: string | undefined;

  /**
   * Maximum edges in a path (1–6).
   * @public
   */
  maxHops?: number | undefined;

  /**
   * Maximum number of paths returned (1–20).
   * @public
   */
  limit?: number | undefined;
}

/**
 * A drawable edge. ``direction`` is ``outgoing`` for canvas pages and may be
 * ``incoming`` on a path, where an edge is traversed against its assertion.
 * @public
 */
export interface CanvasEdge {
  /**
   * Subject IRI.
   * @public
   */
  source: string | undefined;

  /**
   * Predicate IRI.
   * @public
   */
  predicate: string | undefined;

  /**
   * Local name of the predicate, for display.
   * @public
   */
  predicateLabel?: string | undefined;

  /**
   * Object IRI.
   * @public
   */
  target: string | undefined;

  /**
   * Named graph the triple lives in.
   * @public
   */
  graph?: string | undefined;

  /**
   * ``outgoing`` or ``incoming``.
   * @public
   */
  direction?: string | undefined;
}

/**
 * A drawable node: an IRI with an optional label and coarse kind.
 * @public
 */
export interface CanvasNode {
  /**
   * Full IRI of the node.
   * @public
   */
  uri: string | undefined;

  /**
   * ``rdfs:label`` when one appears in the scanned page.
   * @public
   */
  label?: string | undefined;

  /**
   * ``class``, ``object-property``, ``datatype-property``, or ``resource``
   * when the page's ``rdf:type`` triple does not name one of those.
   * @public
   */
  kind?: string | undefined;
}

/**
 * One simple path: no node repeats, ``hops == edges.size()``.
 * @public
 */
export interface GraphPath {
  /**
   * Nodes visited by the path, in traversal order.
   * @public
   */
  nodes: CanvasNode[] | undefined;

  /**
   * Edges followed, one per hop; direction records assertion vs traversal.
   * @public
   */
  edges: CanvasEdge[] | undefined;

  /**
   * Number of edges in the path.
   * @public
   */
  hops: number | undefined;
}

/**
 * @public
 */
export interface FindGraphPathOutput {
  /**
   * Shortest paths first; each carries the nodes and edges to draw it.
   * @public
   */
  paths: GraphPath[] | undefined;

  /**
   * True when more paths exist than ``limit`` (or the search cap hit).
   * @public
   */
  truncated: boolean | undefined;
}

/**
 * @public
 */
export interface FindLinksInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * IRI to expand from.
   * @public
   */
  uri: string | undefined;

  /**
   * Direction to expand; defaults to ``both``.
   * @public
   */
  direction?: LinkDirection | undefined;

  /**
   * Maximum hops to expand (1–3); defaults to 3.
   * @public
   */
  maxHops?: number | undefined;

  /**
   * Maximum edges returned (1–500); defaults to 200.
   * @public
   */
  limit?: number | undefined;
}

/**
 * One adjacency edge, tagged with the hop that discovered it.
 * @public
 */
export interface GraphLinkEdge {
  /**
   * Subject IRI.
   * @public
   */
  source: string | undefined;

  /**
   * Predicate IRI.
   * @public
   */
  predicate: string | undefined;

  /**
   * Local name of the predicate, for display.
   * @public
   */
  predicateLabel?: string | undefined;

  /**
   * Object IRI.
   * @public
   */
  target: string | undefined;

  /**
   * Named graph the triple lives in.
   * @public
   */
  graph?: string | undefined;

  /**
   * How expansion traversed the edge: ``outgoing`` or ``incoming``.
   * @public
   */
  direction?: string | undefined;

  /**
   * Hop at which expansion discovered this edge (1–3).
   * @public
   */
  hops: number | undefined;
}

/**
 * One neighbour reached from the seed IRI.
 * @public
 */
export interface GraphLinkNode {
  /**
   * Full IRI of the neighbour.
   * @public
   */
  uri: string | undefined;

  /**
   * ``rdfs:label`` when the namespace carries one.
   * @public
   */
  label?: string | undefined;

  /**
   * ``class``, ``object-property``, ``datatype-property`` or ``resource``.
   * @public
   */
  kind?: string | undefined;

  /**
   * Shortest hop distance from the seed IRI (1–3).
   * @public
   */
  hops: number | undefined;
}

/**
 * @public
 */
export interface FindLinksOutput {
  /**
   * Neighbours within the hop limit, nearest first; the seed is omitted.
   * @public
   */
  nodes: GraphLinkNode[] | undefined;

  /**
   * Adjacency edges within the hop limit, deduplicated by triple + graph.
   * @public
   */
  edges: GraphLinkEdge[] | undefined;

  /**
   * True when the edge limit ended the expansion before it was complete.
   * @public
   */
  truncated: boolean | undefined;
}

/**
 * @public
 */
export interface GetCanvasManifestInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;
}

/**
 * Hard ceilings the canvas subgraph endpoint enforces. Published so the UI
 * stops paging at the boundary instead of learning it from a 400.
 * @public
 */
export interface CanvasLimits {
  /**
   * Maximum nodes returned by one canvas subgraph page.
   * @public
   */
  maxNodes: number | undefined;

  /**
   * Maximum edges returned alongside those nodes.
   * @public
   */
  maxEdges: number | undefined;

  /**
   * Maximum page size accepted by ``maxResults``.
   * @public
   */
  maxPageSize: number | undefined;
}

/**
 * @public
 */
export interface GetCanvasManifestOutput {
  /**
   * Capabilities the canvas may rely on (e.g. ``nodeKinds``,
   * ``graphFilter``, ``cursorPaging``). Clients must ignore values
   * they do not recognise, so a capability can be added without
   * breaking older frontends.
   * @public
   */
  capabilities: string[] | undefined;

  /**
   * Hard limits enforced by the backend.
   * @public
   */
  limits: CanvasLimits | undefined;
}

/**
 * @public
 */
export interface GetCanvasSubgraphInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Comma-separated node kinds to keep: ``class``,
   * ``object-property``, ``datatype-property``. Omit for every kind.
   * @public
   */
  kinds?: string | undefined;

  /**
   * Only read triples from this named graph (an IRI inside the
   * namespace). Omit to read every graph in the namespace.
   * @public
   */
  graph?: string | undefined;

  /**
   * Page size. The manifest's ``maxPageSize`` is the ceiling.
   * @public
   */
  limit?: number | undefined;

  /**
   * Backend index offset. Pass the previous page's ``nextOffset``.
   * @public
   */
  offset?: number | undefined;
}

/**
 * @public
 */
export interface GetCanvasSubgraphOutput {
  /**
   * Nodes touched by this page's triples.
   * @public
   */
  nodes: CanvasNode[] | undefined;

  /**
   * Edges whose object is an IRI (literals are kept as node labels,
   * never drawn as edges).
   * @public
   */
  edges: CanvasEdge[] | undefined;

  /**
   * True when another page exists beyond this window.
   * @public
   */
  truncated: boolean | undefined;

  /**
   * Number of nodes in this page (not the whole graph).
   * @public
   */
  nodeCount: number | undefined;

  /**
   * Number of edges in this page (not the whole graph).
   * @public
   */
  edgeCount: number | undefined;

  /**
   * Offset of the next page; present only when ``truncated`` is true.
   * @public
   */
  nextOffset?: number | undefined;
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
export interface GetOntologyDiffInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Baseline named graph IRI, inside this namespace.
   * @public
   */
  fromGraph: string | undefined;

  /**
   * Target named graph IRI, inside this namespace.
   * @public
   */
  toGraph: string | undefined;

  /**
   * Maximum sample rows per side (1–200).
   * @public
   */
  limit?: number | undefined;
}

/**
 * Triple and schema delta counts.
 * @public
 */
export interface OntologyDiffCounts {
  /**
   * Triples present in the target and absent from the baseline.
   * @public
   */
  addedTriples: number | undefined;

  /**
   * Triples present in the baseline and absent from the target.
   * @public
   */
  removedTriples: number | undefined;

  /**
   * Classes added.
   * @public
   */
  addedClasses: number | undefined;

  /**
   * Classes removed.
   * @public
   */
  removedClasses: number | undefined;

  /**
   * Properties added (object or datatype).
   * @public
   */
  addedProperties: number | undefined;

  /**
   * Properties removed.
   * @public
   */
  removedProperties: number | undefined;
}

/**
 * One sampled triple.
 * @public
 */
export interface TripleExample {
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
   * Object IRI or lexical literal form.
   * @public
   */
  object: string | undefined;
}

/**
 * Sample triples for each side of the diff.
 * @public
 */
export interface OntologyDiffExamples {
  /**
   * Sample of added triples.
   * @public
   */
  addedTriples: TripleExample[] | undefined;

  /**
   * Sample of removed triples.
   * @public
   */
  removedTriples: TripleExample[] | undefined;
}

/**
 * @public
 */
export interface GetOntologyDiffOutput {
  /**
   * Baseline graph that was compared.
   * @public
   */
  baselineGraph: string | undefined;

  /**
   * Target graph that was compared.
   * @public
   */
  targetGraph: string | undefined;

  /**
   * Triple and schema deltas.
   * @public
   */
  counts: OntologyDiffCounts | undefined;

  /**
   * Class IRIs only in the target (sample).
   * @public
   */
  addedClasses: string[] | undefined;

  /**
   * Class IRIs only in the baseline (sample).
   * @public
   */
  removedClasses: string[] | undefined;

  /**
   * Property IRIs only in the target (sample).
   * @public
   */
  addedProperties: string[] | undefined;

  /**
   * Property IRIs only in the baseline (sample).
   * @public
   */
  removedProperties: string[] | undefined;

  /**
   * Sample triples behind the counts.
   * @public
   */
  examples: OntologyDiffExamples | undefined;

  /**
   * True when a sample list or example set was cut at ``limit``.
   * @public
   */
  truncated: boolean | undefined;

  /**
   * Human-readable provenance for the diff.
   * @public
   */
  source: string | undefined;

  /**
   * When the diff ran (ISO-8601).
   * @public
   */
  sampledAt: string | undefined;
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
export interface GetOntologySnapshotInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;
}

/**
 * Counts of asserted instances (the A-Box).
 * @public
 */
export interface OntologySnapshotAbox {
  /**
   * Distinct subjects typed by a class declared in this namespace.
   * @public
   */
  instances: number | undefined;

  /**
   * Distinct declared classes that carry at least one instance.
   * @public
   */
  classesWithInstances: number | undefined;
}

/**
 * The share of declared classes that the data actually uses.
 * @public
 */
export interface OntologyCoverage {
  /**
   * ``classesWithInstances / tbox.classes`` in 0..1; 0 when no class is declared.
   * @public
   */
  classCoverage: number | undefined;

  /**
   * Declared classes without ``rdfs:label`` or ``skos:prefLabel``.
   * @public
   */
  unlabeledClasses: number | undefined;
}

/**
 * Counts of declared schema objects (the T-Box).
 * @public
 */
export interface OntologySnapshotTbox {
  /**
   * Distinct ``owl:Class`` IRIs.
   * @public
   */
  classes: number | undefined;

  /**
   * Distinct ``owl:ObjectProperty`` IRIs.
   * @public
   */
  objectProperties: number | undefined;

  /**
   * Distinct ``owl:DatatypeProperty`` IRIs.
   * @public
   */
  datatypeProperties: number | undefined;
}

/**
 * @public
 */
export interface GetOntologySnapshotOutput {
  /**
   * Declared schema objects.
   * @public
   */
  tbox: OntologySnapshotTbox | undefined;

  /**
   * Asserted data using that schema.
   * @public
   */
  abox: OntologySnapshotAbox | undefined;

  /**
   * How much of the schema the data actually uses.
   * @public
   */
  coverage: OntologyCoverage | undefined;

  /**
   * Named graphs in this namespace, so the diff form can offer real choices.
   * @public
   */
  graphs: string[] | undefined;

  /**
   * Human-readable provenance for the numbers above.
   * @public
   */
  source: string | undefined;

  /**
   * When the aggregation ran (ISO-8601).
   * @public
   */
  sampledAt: string | undefined;
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
export interface GetReasoningStatusInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;
}

/**
 * A measured count that may be unavailable.
 * @public
 */
export interface QualityCount {
  /**
   * The measured count, or null when the check could not run.
   * @public
   */
  count?: number | undefined;

  /**
   * How the count was measured, or why it is null.
   * @public
   */
  detail?: string | undefined;
}

/**
 * One stage of a materialization run. Only the members the stage produces
 * are set: `rdfs`/`owl` report triples added, `shacl` reports the gate.
 * @public
 */
export interface ReasoningStage {
  /**
   * Triples this stage added to the inferred graph.
   * @public
   */
  triples?: number | undefined;

  /**
   * True when the SHACL gate ran and found no violations.
   * @public
   */
  conforms?: boolean | undefined;

  /**
   * Violations found by the SHACL gate.
   * @public
   */
  violations?: number | undefined;

  /**
   * Wall time for this stage.
   * @public
   */
  ms?: number | undefined;
}

/**
 * Stages of a materialization run, in execution order.
 * @public
 */
export interface ReasoningStages {
  /**
   * RDFS closure (Jena `riot --rdfs`); skipped in `rdfs`-only mode.
   * @public
   */
  rdfs?: ReasoningStage | undefined;

  /**
   * OWL EL materialization (ROBOT + ELK); absent in `rdfs`-only mode.
   * @public
   */
  owl?: ReasoningStage | undefined;

  /**
   * SHACL gate; runs before any write, so a violation leaves the target
   * graph untouched.
   * @public
   */
  shacl?: ReasoningStage | undefined;
}

/**
 * What the last materialization job left behind.
 * @public
 */
export interface ReasoningJobSummary {
  /**
   * Row identifier in `platform.reasoning_job`.
   * @public
   */
  jobId: string | undefined;

  /**
   * `queued`, `running`, `succeeded`, `skipped`, `failed` or `canceled`.
   * @public
   */
  state: string | undefined;

  /**
   * Triples the run added.
   * @public
   */
  inferred?: number | undefined;

  /**
   * Consistency verdict; false fails the run.
   * @public
   */
  consistent?: boolean | undefined;

  /**
   * When the run finished (ISO-8601).
   * @public
   */
  finishedAt?: string | undefined;

  /**
   * True when the run short-circuited because the inputs were unchanged.
   * @public
   */
  skipped?: boolean | undefined;

  /**
   * Per-stage results, empty when nothing ran.
   * @public
   */
  stages?: ReasoningStages | undefined;
}

/**
 * @public
 */
export interface GetReasoningStatusOutput {
  /**
   * True only when this deployment has a reasoner configured.
   * @public
   */
  available: boolean | undefined;

  /**
   * Reasoner identifier (for example ``elk``); null when none is configured.
   * @public
   */
  engine?: string | undefined;

  /**
   * Failed materialization jobs; null when not observable from here.
   * @public
   */
  failures?: QualityCount | undefined;

  /**
   * Human-readable explanation of the state above.
   * @public
   */
  detail?: string | undefined;

  /**
   * Where this status came from.
   * @public
   */
  source: string | undefined;

  /**
   * When the status was sampled (ISO-8601).
   * @public
   */
  sampledAt: string | undefined;

  /**
   * Triples the recorded pointer holds; null until the first run.
   * @public
   */
  inferredTriples?: number | undefined;

  /**
   * Last materialization job, with its per-stage results. Null before
   * the first run.
   * @public
   */
  lastJob?: ReasoningJobSummary | undefined;
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
export interface MaterializeReasoningInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * `EL` (default) or `OWL2EL`.
   * @public
   */
  profile?: string | undefined;

  /**
   * Re-run even when the inputs are unchanged.
   * @public
   */
  force?: boolean | undefined;

  /**
   * A-Box graphs to reason over. Every IRI must be a `urn:platform:`
   * graph, so a namespace cannot read another namespace's graph. When
   * omitted the deployment's configured A-Box graphs are used.
   * @public
   */
  aboxGraphs?: string[] | undefined;
}

/**
 * @public
 */
export interface MaterializeReasoningOutput {
  /**
   * Identifier of the row in `platform.reasoning_job`.
   * @public
   */
  jobId: string | undefined;

  /**
   * `materialize` or `rdfs`.
   * @public
   */
  mode: string | undefined;

  /**
   * Reasoning profile that was used.
   * @public
   */
  profile: string | undefined;

  /**
   * Published ontology version the run read.
   * @public
   */
  ontologyVersion: string | undefined;

  /**
   * Graph the run would replace (and did replace unless skipped).
   * @public
   */
  targetGraph: string | undefined;

  /**
   * Triples this run added; 0 when skipped.
   * @public
   */
  inferred: number | undefined;

  /**
   * True when the inputs were unchanged and nothing was written.
   * @public
   */
  skipped: boolean | undefined;

  /**
   * Consistency verdict from the reasoner. False fails the job and
   * leaves the target graph untouched.
   * @public
   */
  consistent: boolean | undefined;

  /**
   * Hash of (T-Box, A-Box, profile, mode) used to decide `skipped`.
   * @public
   */
  inputHash?: string | undefined;

  /**
   * Wall time of the run.
   * @public
   */
  ms: number | undefined;

  /**
   * Per-stage results, in execution order.
   * @public
   */
  stages: ReasoningStages | undefined;

  /**
   * Non-fatal notes, for example axioms the EL profile ignores.
   * @public
   */
  warnings: string[] | undefined;
}

/**
 * @public
 */
export interface RunValidationInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;
}

/**
 * Outcome of the SHACL gate.
 * @public
 */
export interface ShaclReport {
  /**
   * One of ``ok``, ``violations``, ``skipped``, ``error``.
   * @public
   */
  status: string | undefined;

  /**
   * Number of violations; null when the gate did not run.
   * @public
   */
  violations?: number | undefined;

  /**
   * True only when the gate ran and produced no violations.
   * @public
   */
  conforms?: boolean | undefined;

  /**
   * Reason the gate was skipped or errored.
   * @public
   */
  detail?: string | undefined;
}

/**
 * @public
 */
export interface RunValidationOutput {
  /**
   * Instances with no properties beyond ``rdf:type``/``rdfs:label``
   * and no inbound references.
   * @public
   */
  orphanInstances: QualityCount | undefined;

  /**
   * Declared classes without any label.
   * @public
   */
  unlabeledClasses: QualityCount | undefined;

  /**
   * SHACL gate result, or an explicit "skipped" when no shapes exist.
   * @public
   */
  shacl: ShaclReport | undefined;

  /**
   * Failed inference jobs; null when this service cannot observe them.
   * @public
   */
  inferenceFailures: QualityCount | undefined;

  /**
   * Human-readable provenance for the checks above.
   * @public
   */
  source: string | undefined;

  /**
   * When the checks ran (ISO-8601).
   * @public
   */
  sampledAt: string | undefined;
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
