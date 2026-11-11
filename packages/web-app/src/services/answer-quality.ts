import type { ApiClient } from "../components/ApiClientProvider";

/**
 * GetAnswerQuality (F86–F89). The endpoint re-runs the fixed golden set on
 * every call: it reports a single run, not a stored history, so the panel can
 * show rates and per-case detail but not a trend line.
 */
export interface AnswerQualityCitation {
  id: string;
  kind: string;
  ref: string;
  versionId?: string;
  resolveUrl?: string;
  resolvable: boolean;
}

export interface AnswerQualityCase {
  id: string;
  query: string;
  type: string;
  expectRefused: boolean;
  actual: {
    refused: boolean;
    answerType: string;
    answerMode: string;
    reasonCode: string | null;
    degraded: boolean;
    citations: AnswerQualityCitation[];
    citationKinds: string[];
    missingLayers: string[];
  };
  pass: boolean;
  failures: string[];
  drillDownUrl?: string;
}

export interface AnswerQualitySummary {
  cases: number;
  passed: number;
  failed: number;
  passRate: number;
  casesWithCitations: number;
  citationCoverageRate: number;
  citations: number;
  resolvableCitations: number;
  citationResolvableRate: number;
  brokenLinkRate: number;
  baselineBrokenLinkRate: number;
  regression: boolean;
}

export interface AnswerQualityByType {
  type: string;
  cases: number;
  refused: number;
  withCitations?: number;
  citations: number;
  resolvable?: number;
  citationCoverageRate: number;
  resolvableRate?: number;
  refusalRate?: number;
}

export interface AnswerQualityResponse {
  strategy: string;
  goldenSet: {
    id: string;
    count: number;
    evaluated: number;
    caseId?: string | null;
  };
  summary: AnswerQualitySummary;
  citationCoverageByType?: AnswerQualityByType[];
  refusalsByReason?: Array<{ type: string; reasonCode: string; count: number }>;
  refusalsByType?: AnswerQualityByType[];
  refusalsWithoutLayers?: unknown[];
  brokenLinks?: unknown[];
  cases: AnswerQualityCase[];
  empty: boolean;
  emptyReason: string | null;
  readOnly: boolean;
}

export type AnswerQualityStrategy = "lexical" | "hybrid";

export function getAnswerQuality(
  client: ApiClient,
  strategy: AnswerQualityStrategy,
  limit = 10,
): Promise<AnswerQualityResponse> {
  return client.get<AnswerQualityResponse>(
    `/answer/quality?strategy=${encodeURIComponent(strategy)}&limit=${limit}`,
  );
}

/**
 * ListAnswerQualityRuns (F86). Reads the rows written to
 * `platform.answer_quality_run`, newest first. `layerCoverage` is absent on
 * rows recorded before P14 stored the aggregation, which means "not recorded",
 * not zero.
 */
export interface AnswerQualityLayerCoverage {
  layer: string;
  covered: number;
  evaluated: number;
  rate: number;
}

export interface AnswerQualityRun {
  runId: string;
  ranAt: string;
  strategy: string;
  goldenSet: string;
  evaluated: number;
  passed: number;
  failed: number;
  passRate: number;
  citationCoverageRate: number;
  citationResolvableRate: number;
  brokenLinkRate: number;
  regression: boolean;
  layerCoverage?: AnswerQualityLayerCoverage[] | null;
}

export interface AnswerQualityRunListResponse {
  items: AnswerQualityRun[];
  totalCount: number;
  limit: number;
  strategy?: string | null;
  since?: string | null;
  readOnly: boolean;
}

export function listAnswerQualityRuns(
  client: ApiClient,
  limit = 20,
): Promise<AnswerQualityRunListResponse> {
  return client.get<AnswerQualityRunListResponse>(
    `/answer/quality/runs?limit=${limit}`,
  );
}
