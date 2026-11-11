// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import type { ApiClient } from "../components/ApiClientProvider";

/**
 * CheckAnswerable (F76 four-layer coverage / F79 gaps and fixes).
 *
 * The response mirrors models/src/main/smithy/answerable.smithy. `coverage` on
 * a layer is absent (null) when that layer cannot be computed — the UI must say
 * "unavailable" there instead of drawing a zero bar.
 */

export type CoverageLayerName = "ontology" | "terms" | "metrics" | "facts";

export interface CoverageChars {
  covered: number;
  total: number;
}

export interface MatchedTerm {
  term: string;
  label: string;
  span: number[];
}

export interface LayerMatch {
  id?: string;
  label?: string;
  predicate?: string;
  source?: string;
  score?: number;
  metricId?: string;
  status?: string;
  code?: string;
  observationRows?: number;
  factFunction?: string;
}

export interface CoverageLayer {
  layer: CoverageLayerName;
  status: string;
  coverage?: number | null;
  matched: LayerMatch[];
  missing: string[];
}

export interface NearbyTerm {
  term: string;
  label: string;
  similarity: number;
}

export interface GapCandidate {
  id: string;
  label: string;
  score: number;
}

export interface MissingGap {
  layer: string;
  code: string;
  text?: string;
  span?: number[];
  what?: string;
  howToFix?: string;
  metricId?: string;
  nearbyTerms?: NearbyTerm[];
  candidates?: GapCandidate[];
}

export interface AnswerCandidate {
  layer: string;
  id: string;
  label: string;
  reason: string;
  score: number;
}

export interface AnswerTimings {
  termsMs: number;
  metricMs: number;
  factsMs: number;
}

export interface CheckAnswerableResponse {
  query: string;
  answerable: boolean;
  valueAnswerable: boolean;
  answerMode: string;
  intent: string;
  degraded: boolean;
  coverage: number;
  threshold: number;
  coverageChars: CoverageChars;
  ontologyVersion: string;
  ontologyGraph: string;
  termSource: string;
  termCount: number;
  matchedTerms: MatchedTerm[];
  layers: CoverageLayer[];
  missing: MissingGap[];
  candidates: AnswerCandidate[];
  reasons: string[];
  reasonCode?: string | null;
  hint?: string | null;
  timings: AnswerTimings;
}

export interface CheckAnswerableOptions {
  ontologyVersion?: string;
  minCoverage?: number;
}

export function checkAnswerable(
  client: ApiClient,
  namespaceId: string,
  query: string,
  options: CheckAnswerableOptions = {},
): Promise<CheckAnswerableResponse> {
  return client.post<CheckAnswerableResponse>(
    `/namespaces/${encodeURIComponent(namespaceId)}/answerable`,
    { query, ...options },
  );
}
