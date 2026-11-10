// smithy-typescript generated code
import type { ReviewDecision, ReviewStatus, SourceStatus } from "./enums";
import type {
  CustomConnectorConfiguration,
  EventRescanConfig,
  GlueConfiguration,
  JdbcConfiguration,
  RescanSchedule,
} from "./models_0";

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
