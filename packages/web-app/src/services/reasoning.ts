// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * MaterializeReasoning (P3): RDFS closure -> ELK -> SHACL gate.
 *
 * The namespace-scoped path is served by the local bridge (8099), which
 * forwards it to the kernel; the kernel writes `platform.reasoning_job` and
 * the inferred triples, so the result is the job, not a fire-and-forget ack.
 */
import type { ApiClient } from "../components/ApiClientProvider";

export interface MaterializationStage {
  triples?: number;
  ms?: number;
  conforms?: boolean;
  violations?: number;
}

export interface MaterializationResult {
  jobId: string;
  targetGraph: string;
  inferred: number;
  skipped: boolean;
  consistent: boolean;
  inputHash?: string;
  ms?: number;
  ontologyVersion?: string;
  profile?: string;
  mode?: string;
  stages: Record<string, MaterializationStage>;
  warnings?: string[];
}

export async function materializeReasoning(
  client: ApiClient,
  namespace: string,
  options: { force?: boolean } = {},
): Promise<MaterializationResult> {
  return client.post<MaterializationResult>(
    `/namespaces/${encodeURIComponent(namespace)}/graph/reasoning/materialize`,
    options.force === undefined ? {} : { force: options.force },
  );
}
