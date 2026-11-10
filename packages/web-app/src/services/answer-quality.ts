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
  goldenSet: { id: string; count: number; evaluated: number; caseId?: string | null };
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
