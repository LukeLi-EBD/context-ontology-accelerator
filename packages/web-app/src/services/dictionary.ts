// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Terms + data-dictionary API client (P4, F58-F66).
 *
 * All requests go through API Gateway via ApiClient. The wire shapes mirror
 * `models/src/main/smithy/ontology-dictionary.smithy`; the generated client is
 * refreshed on the main line, so the types are declared here to keep this
 * branch buildable without generated artefacts.
 */
import type { ApiClient } from "../components/ApiClientProvider";

export type DictionaryView =
  | "all"
  | "missing_comment"
  | "unbound"
  | "mappable_unbound";

export type BindingMethod = "explicit" | "name_match" | "manual" | "none";

export type SourceKind =
  | "postgresql"
  | "mysql"
  | "redshift"
  | "sqlserver"
  | "snowflake"
  | "glue"
  | "duckdb";

export interface TermCounts {
  anchorClasses: number;
  termEntries: number;
  evidenced: number;
  inferred: number;
}

export interface TermEntry {
  entry: string;
  classIri?: string;
  classLabel?: string;
  label: string;
  status: string;
  confidence?: number;
  guardRegex?: string;
  canonicalFor: string[];
  suppressedSurface: string[];
}

export interface ListTermsResponse {
  namespaceId: string;
  graph?: string;
  counts: TermCounts;
  entries: TermEntry[];
  total: number;
  offset: number;
  limit: number;
}

export interface DictionaryRefreshRun {
  runId: string;
  sourceId: string;
  status: string;
  idempotencyKey?: string;
  requestedBy?: string;
  startedAt?: string;
  finishedAt?: string;
  processed?: number;
  inserted?: number;
  updated?: number;
  unchanged?: number;
  removed?: number;
  error?: string;
}

export interface DictionarySummary {
  sourceId: string;
  sourceKind: string;
  tables: number;
  columns: number;
  commented: number;
  bound: number;
  observedAt?: string;
  lastRun?: DictionaryRefreshRun;
}

export interface DictionaryColumn {
  sourceId: string;
  catalog: string;
  schema: string;
  table: string;
  column: string;
  dataType: string;
  isNullable: boolean;
  sourceKind: string;
  bindingMethod: BindingMethod;
  comment?: string;
  propertyIri?: string;
  confidence?: number;
  bindingNote?: string;
  observedAt?: string;
  lastRefreshRunId?: string;
}

export interface DictionaryTableSummary {
  table: string;
  columns: number;
  commented: number;
  bound: number;
  missingComment: number;
  unbound: number;
}

export interface CommentCoverage {
  total: number;
  commented: number;
  missing: number;
  ratio?: number;
}

export interface ListDictionariesResponse {
  items: DictionarySummary[];
  total: number;
  offset: number;
  limit: number;
}

export interface GetDictionaryResponse {
  sourceId: string;
  sourceKind?: string;
  catalog?: string;
  schema?: string;
  tables: DictionaryTableSummary[];
  totals: CommentCoverage;
  boundColumns: number;
  latestRun?: DictionaryRefreshRun;
}

export interface GetDictionaryViewResponse {
  items: DictionaryColumn[];
  total: number;
  offset: number;
  limit: number;
  view: DictionaryView;
  coverage: CommentCoverage;
  warnings?: string[];
}

export interface GetDictionaryCommentCoverageResponse {
  sourceId: string;
  coverage: CommentCoverage;
  tables: DictionaryTableSummary[];
}

export interface RefreshDictionariesResponse {
  run: DictionaryRefreshRun;
  bindingBasis: string;
  warnings?: string[];
}

const qs = (params: Record<string, string | number | undefined | null>): string => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    search.set(key, String(value));
  });
  const text = search.toString();
  return text ? `?${text}` : "";
};

export async function listTerms(
  apiClient: ApiClient,
  namespaceId: string,
  params: { q?: string; status?: string; limit?: number; offset?: number } = {},
): Promise<ListTermsResponse> {
  return apiClient.get<ListTermsResponse>(
    `/namespaces/${encodeURIComponent(namespaceId)}/terms${qs(params)}`,
  );
}

export async function listDictionaries(
  apiClient: ApiClient,
  namespaceId: string,
  params: { limit?: number; offset?: number } = {},
): Promise<ListDictionariesResponse> {
  return apiClient.get<ListDictionariesResponse>(
    `/namespaces/${encodeURIComponent(namespaceId)}/dictionaries${qs(params)}`,
  );
}

export async function getDictionary(
  apiClient: ApiClient,
  namespaceId: string,
  sourceId: string,
  params: { table?: string } = {},
): Promise<GetDictionaryResponse> {
  return apiClient.get<GetDictionaryResponse>(
    `/namespaces/${encodeURIComponent(namespaceId)}/dictionaries/${encodeURIComponent(sourceId)}${qs(params)}`,
  );
}

export async function getDictionaryView(
  apiClient: ApiClient,
  namespaceId: string,
  sourceId: string,
  params: {
    view?: DictionaryView;
    table?: string;
    column?: string;
    bindingMethod?: BindingMethod;
    sourceKind?: SourceKind;
    q?: string;
    limit?: number;
    offset?: number;
  } = {},
): Promise<GetDictionaryViewResponse> {
  return apiClient.get<GetDictionaryViewResponse>(
    `/namespaces/${encodeURIComponent(namespaceId)}/dictionaries/${encodeURIComponent(sourceId)}/view${qs(params)}`,
  );
}

export async function getDictionaryCommentCoverage(
  apiClient: ApiClient,
  namespaceId: string,
  sourceId: string,
  params: { table?: string } = {},
): Promise<GetDictionaryCommentCoverageResponse> {
  return apiClient.get<GetDictionaryCommentCoverageResponse>(
    `/namespaces/${encodeURIComponent(namespaceId)}/dictionaries/${encodeURIComponent(sourceId)}/comment-coverage${qs(params)}`,
  );
}

export async function refreshDictionaries(
  apiClient: ApiClient,
  namespaceId: string,
  sourceId: string,
  body: { idempotencyKey?: string; requestedBy?: string } = {},
): Promise<RefreshDictionariesResponse> {
  return apiClient.post<RefreshDictionariesResponse>(
    `/namespaces/${encodeURIComponent(namespaceId)}/dictionaries/${encodeURIComponent(sourceId)}/refresh`,
    body,
  );
}
