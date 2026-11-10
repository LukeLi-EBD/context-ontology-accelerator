// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  BulkDeleteMetricsCommand,
  CreateMetricCommand,
  DeleteMetricCommand,
  ExportOsiCommand,
  GetImportJobCommand,
  GetMetricCommand,
  GetOsiUploadUrlCommand,
  ImportOsiCommand,
  ListMetricsCommand,
  UpdateMetricCommand,
} from "@coa/control-plane-client";
import type {
  ImportOsiCommandOutput,
  MetricDefinition as _MetricDefinition,
  MetricDialect as _MetricDialect,
  MetricAiContext as _MetricAiContext,
  CreateMetricInput as _CreateMetricInput,
} from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";
import { useApiClient } from "@components/ApiClientProvider";

// Re-export Smithy types with required fields narrowed for UI usage.
// The generated types mark @required output fields as T | undefined
// because the OpenAPI generator is conservative. We know the API always
// returns these fields, so we narrow them here for ergonomic UI code.

export type MetricDialect = Required<_MetricDialect>;
export type MetricAiContext = _MetricAiContext;

export interface MetricDefinition extends Required<
  Pick<
    _MetricDefinition,
    "name" | "description" | "expression" | "dataSourceId" | "sourceTable"
  >
> {
  /** Display-only label; absent when the metric has none. */
  label?: string;
  defaultTimeGrain?: string;
  unit?: string;
  returnType?: string;
  aiContext?: MetricAiContext;
  ontologyConcepts?: string[];
  definedBy?: string;
  effectiveFrom?: string;
  // COA-private provenance, carried through OSI custom_extensions. Absent means
  // unknown; never coalesce it to false or an empty string.
  domain?: string;
  evidenceBasis?: string;
  publishable?: boolean;
}

/** Input for create/update — excludes namespaceId (passed via URL). */
export type CreateMetricInput = Omit<_CreateMetricInput, "namespaceId">;

export interface CreateMetricOutput {
  metric: MetricDefinition;
  warnings?: Array<{ field: string; message: string; severity: string }>;
}

export interface ListMetricsOutput {
  metrics: MetricDefinition[];
  nextToken?: string;
}

export interface ImportOsiOutput {
  datasetsResolved: number;
  metricsCreated: number;
  metricsUpdated: number;
  warnings?: string[];
  jobId?: string;
  status?: "COMPLETED" | "IN_PROGRESS" | "FAILED";
}

/** Fill the generated output's optional counters before handing it to the UI. */
function narrowImportOutput(out: ImportOsiCommandOutput): ImportOsiOutput {
  return {
    datasetsResolved: out.datasetsResolved ?? 0,
    metricsCreated: out.metricsCreated ?? 0,
    metricsUpdated: out.metricsUpdated ?? 0,
    warnings: out.warnings,
    jobId: out.jobId,
    status: out.status,
  };
}

export interface ImportJobOutput {
  jobId: string;
  status: "IN_PROGRESS" | "COMPLETED" | "FAILED";
  metricsTotal: number;
  metricsProcessed: number;
  metricsCreated: number;
  metricsUpdated: number;
  errors?: string[];
  warnings?: string[];
}

export interface ExportOsiOutput {
  content: string;
}

export function useListMetrics(namespaceId: string, maxResults = 50) {
  const client = useControlPlaneClient();

  return useInfiniteQuery<ListMetricsOutput, Error>({
    queryKey: ["metrics", namespaceId],
    queryFn: async ({ pageParam }) => {
      const out = await client.send(
        new ListMetricsCommand({
          namespaceId,
          maxResults,
          nextToken: pageParam as string | undefined,
        }),
      );
      return {
        metrics: (out.metrics ?? []) as MetricDefinition[],
        nextToken: out.nextToken,
      };
    },
    getNextPageParam: (lastPage) => lastPage.nextToken,
    initialPageParam: undefined as string | undefined,
    enabled: !!namespaceId,
  });
}

export function useGetMetric(namespaceId: string, name: string) {
  const client = useControlPlaneClient();

  return useQuery<{ metric: MetricDefinition }, Error>({
    queryKey: ["metrics", namespaceId, name],
    queryFn: async () => {
      const out = await client.send(
        new GetMetricCommand({ namespaceId, name }),
      );
      return { metric: out.metric as MetricDefinition };
    },
    enabled: !!namespaceId && !!name,
  });
}

export function useCreateMetric(namespaceId: string) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  return useMutation<CreateMetricOutput, Error, CreateMetricInput>({
    mutationFn: async (input) => {
      const out = await client.send(
        new CreateMetricCommand({ ...input, namespaceId }),
      );
      return {
        metric: out.metric as MetricDefinition,
        warnings: out.warnings as CreateMetricOutput["warnings"],
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["metrics", namespaceId] });
    },
  });
}

export function useUpdateMetric(namespaceId: string, name: string) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  return useMutation<CreateMetricOutput, Error, CreateMetricInput>({
    mutationFn: async (input) => {
      const out = await client.send(
        new UpdateMetricCommand({ ...input, namespaceId, name }),
      );
      return {
        metric: out.metric as MetricDefinition,
        warnings: out.warnings as CreateMetricOutput["warnings"],
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["metrics", namespaceId] });
      queryClient.invalidateQueries({
        queryKey: ["metrics", namespaceId, name],
      });
    },
  });
}

export function useDeleteMetric(namespaceId: string) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (metricName) => {
      await client.send(
        new DeleteMetricCommand({ namespaceId, name: metricName }),
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["metrics", namespaceId] });
    },
  });
}

export interface BulkDeleteOutput {
  deleted: number;
  notFound?: string[];
}

/**
 * Most names one BulkDeleteMetrics request may carry: the `@length(max: 2000)`
 * on `BulkDeleteMetrics.names` in metric-service.smithy (enforced server-side as
 * `BULK_DELETE_NAMES_MAX_ITEMS` in the metric-service contract). Larger name
 * lists are sent as consecutive requests of at most this many names.
 */
export const BULK_DELETE_NAMES_MAX_ITEMS = 2000;

export interface BulkDeleteInput {
  names?: string[];
  filter?: {
    dataSourceId?: string;
    sourceTable?: string;
    namePrefix?: string;
  };
}

/**
 * Deletes `input.names` in requests of at most {@link BULK_DELETE_NAMES_MAX_ITEMS}
 * names, sent one after another, and sums the results. A failing request stops
 * the run; its error says how many metrics earlier requests already deleted.
 */
export async function bulkDeleteInBatches(
  input: BulkDeleteInput,
  post: (body: BulkDeleteInput) => Promise<BulkDeleteOutput>,
): Promise<BulkDeleteOutput> {
  const names = input.names;
  if (!names || names.length <= BULK_DELETE_NAMES_MAX_ITEMS) {
    return post(input);
  }
  let deleted = 0;
  const notFound: string[] = [];
  for (let i = 0; i < names.length; i += BULK_DELETE_NAMES_MAX_ITEMS) {
    const batch = names.slice(i, i + BULK_DELETE_NAMES_MAX_ITEMS);
    let result: BulkDeleteOutput;
    try {
      result = await post({ ...input, names: batch });
    } catch (err) {
      if (deleted === 0) throw err;
      const reason = err instanceof Error ? err.message : String(err);
      throw new Error(
        `${reason} (${deleted} metrics were already deleted; the remaining ${names.length - i} were not confirmed deleted)`,
        { cause: err },
      );
    }
    deleted += result.deleted;
    notFound.push(...(result.notFound ?? []));
  }
  return notFound.length ? { deleted, notFound } : { deleted };
}

export function useBulkDeleteMetrics(namespaceId: string) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  return useMutation<BulkDeleteOutput, Error, BulkDeleteInput>({
    mutationFn: (input) =>
      bulkDeleteInBatches(input, async (body) => {
        const out = await client.send(
          new BulkDeleteMetricsCommand({ ...body, namespaceId }),
        );
        return { deleted: out.deleted ?? 0, notFound: out.notFound };
      }),
    // Settled, not success: a batched delete that fails part-way has still
    // removed the metrics in its earlier batches.
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["metrics", namespaceId] });
    },
  });
}

export function useImportOsi(namespaceId: string) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  return useMutation<ImportOsiOutput, Error, string>({
    mutationFn: async (content: string) =>
      narrowImportOutput(
        await client.send(new ImportOsiCommand({ namespaceId, content })),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["metrics", namespaceId] });
    },
  });
}

/** Upload file to S3 via pre-signed URL, then call import with s3Key. */
export function useImportOsiViaS3(namespaceId: string) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  return useMutation<ImportOsiOutput, Error, File>({
    mutationFn: async (file: File) => {
      // Step 1: Get pre-signed upload URL
      const presigned = await client.send(
        new GetOsiUploadUrlCommand({ namespaceId, filename: file.name }),
      );
      const uploadUrl = presigned.uploadUrl as string;
      const s3Key = presigned.s3Key as string;

      // Step 2: Upload file to S3
      const uploadResponse = await fetch(uploadUrl, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": "application/x-yaml" },
      });
      if (!uploadResponse.ok) {
        throw new Error(`S3 upload failed: ${uploadResponse.status}`);
      }

      // Step 3: Call import with s3Key
      return narrowImportOutput(
        await client.send(new ImportOsiCommand({ namespaceId, s3Key })),
      );
    },
    onSuccess: (result) => {
      if (result.status === "COMPLETED") {
        queryClient.invalidateQueries({ queryKey: ["metrics", namespaceId] });
      }
    },
  });
}

/** Import an OSI file through the pre-signed S3 upload flow.
 *
 *  Always routes via S3 (upload-url → browser PUT → import by `s3Key`), never an
 *  inline `{content}` POST. The inline path went through API Gateway, whose WAF
 *  (`AWSManagedRulesCommonRuleSet`, `SizeRestrictions_BODY`) rejects any request
 *  body over 8 KB — so a typical metrics YAML (~10-15 KB) failed with 403
 *  (issue 103). The S3 object bypasses the WAF; only a small `{s3Key}` reaches
 *  the API.
 *
 *  Requires the browser→S3 PUT to be permitted: the OSI bucket's CORS allows it
 *  and the SPA's CSP `connect-src` includes the region's S3 origin (see
 *  `public-ui-construct.ts`). The backend still accepts an inline `{content}`
 *  body for non-UI callers under the 8 KB limit — only the UI stopped using it. */
export function useImportOsiFile(namespaceId: string) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  return useMutation<ImportOsiOutput, Error, File>({
    mutationFn: async (file: File) => {
      const presigned = await client.send(
        new GetOsiUploadUrlCommand({ namespaceId, filename: file.name }),
      );
      const uploadUrl = presigned.uploadUrl as string;
      const s3Key = presigned.s3Key as string;
      const uploadResponse = await fetch(uploadUrl, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": "application/x-yaml" },
      });
      if (!uploadResponse.ok) {
        throw new Error(`S3 upload failed: ${uploadResponse.status}`);
      }
      return narrowImportOutput(
        await client.send(new ImportOsiCommand({ namespaceId, s3Key })),
      );
    },
    onSuccess: (result) => {
      if (result.status === "COMPLETED") {
        queryClient.invalidateQueries({ queryKey: ["metrics", namespaceId] });
      }
    },
  });
}

/** Poll an import job until it completes. */
export function useGetImportJob(namespaceId: string, jobId: string | null) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();
  const hasInvalidated = React.useRef(false);

  // Reset ref when jobId changes
  React.useEffect(() => {
    hasInvalidated.current = false;
  }, [jobId]);

  return useQuery<ImportJobOutput, Error>({
    queryKey: ["importJob", namespaceId, jobId],
    queryFn: async () => {
      const out = await client.send(
        new GetImportJobCommand({ namespaceId, jobId: jobId! }),
      );
      return {
        jobId: out.jobId ?? jobId!,
        status: out.status as ImportJobOutput["status"],
        metricsTotal: out.metricsTotal ?? 0,
        metricsProcessed: out.metricsProcessed ?? 0,
        metricsCreated: out.metricsCreated ?? 0,
        metricsUpdated: out.metricsUpdated ?? 0,
        errors: out.errors,
        warnings: out.warnings,
      };
    },
    enabled: !!namespaceId && !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "IN_PROGRESS") return 5000;
      // Job finished — invalidate metrics list once
      if (
        (status === "COMPLETED" || status === "FAILED") &&
        !hasInvalidated.current
      ) {
        hasInvalidated.current = true;
        queryClient.invalidateQueries({ queryKey: ["metrics", namespaceId] });
      }
      return false;
    },
  });
}

export interface ExportOsiInput {
  /** Optional subset of metric names to export. Omit to export every metric
   *  in the namespace (default, unchanged behavior). */
  names?: string[];
}

export function useExportOsi(namespaceId: string) {
  const client = useControlPlaneClient();

  return useMutation<ExportOsiOutput, Error, ExportOsiInput | void>({
    mutationFn: async (input) => {
      const names = input?.names?.length ? input.names : undefined;
      const out = await client.send(
        new ExportOsiCommand({ namespaceId, names }),
      );
      return { content: out.content as string };
    },
  });
}

// ---------------------------------------------------------------------------
// P5 metric card (F54/F55/F56/F57)
//
// These reads are served by the platform kernel, not by the metric contract:
// F54/F56 extend the "GetMetric (F100)" platform card (`/metrics/{metricId}`),
// and F55/F57 add the family and report-manifest reads defined in
// models/src/main/smithy/metric-catalog.smithy. The generated client predates
// all three, so they go through the plain ApiClient.
// ---------------------------------------------------------------------------

/** One physical binding of a metric to a fact table column. */
export interface MetricFieldBinding {
  /** numerator / denominator / index. */
  role?: string;
  factTable?: string;
  entityColumn?: string;
  valueExpr?: string;
  agg?: string;
  filterSql?: string;
  windowColumn?: string;
  windowMode?: string;
}

/** Platform metric card: the detail fields plus bindings and external status. */
export interface MetricCard {
  metricId: string;
  name?: string | null;
  domain?: string | null;
  evidenceBasis?: string | null;
  publishable?: boolean | null;
  variantOf?: string | null;
  outputMode?: string | null;
  /** Grain code (e.g. `customer`); matched against ontology class local names. */
  grain?: string | null;
  granularityText?: string | null;
  unit?: string | null;
  definitionVersion?: string | null;
  bindingStatus: "bound" | "unbound";
  fieldBindings: MetricFieldBinding[];
  externalEligible?: boolean;
  externalStatus?: string;
  externalLabel?: string;
  externalReason?: string;
  familyId?: string | null;
  variantMetricIds?: string[];
}

export function useGetMetricCard(metricId: string) {
  const apiClient = useApiClient();

  return useQuery<MetricCard, Error>({
    queryKey: ["metric-card", metricId],
    queryFn: () =>
      apiClient.get<MetricCard>(`/metrics/${encodeURIComponent(metricId)}`),
    enabled: !!metricId,
  });
}

export interface MetricFamilyVariant {
  metricId: string;
  nameZh?: string;
  displayName?: string;
  grain?: string;
  grainCode?: string;
  computability?: string;
  computabilityLabel?: string;
  denominator?: number | null;
  denominatorText?: string | null;
  formula?: string | null;
  unit?: string | null;
  publishable?: boolean;
  externalEligible?: boolean;
  evidenceBasis?: string;
  window?: { kind?: string; minWindowDays?: number | null; text?: string };
}

export interface MetricFamilyDiff {
  field: string;
  label?: string;
  different: boolean;
  values: Record<string, string | null | undefined>;
}

export interface MetricFamily {
  familyId: string;
  indexMetricId?: string;
  nameZh?: string;
  variantCount: number;
  selectionRequired?: boolean;
  source?: string;
  guidance?: string | null;
  variants: MetricFamilyVariant[];
  diffs: MetricFamilyDiff[];
}

export function useGetMetricFamily(namespaceId: string, familyId?: string) {
  const apiClient = useApiClient();

  return useQuery<{ family: MetricFamily }, Error>({
    queryKey: ["metric-family", namespaceId, familyId ?? null],
    queryFn: () =>
      apiClient.get<{ family: MetricFamily }>(
        `/namespaces/${encodeURIComponent(namespaceId)}/metrics/families/${encodeURIComponent(familyId!)}`,
      ),
    enabled: !!namespaceId && !!familyId,
  });
}

/** One row of the governed-metric report manifest. */
export interface MetricReportItem {
  metricId: string;
  nameZh?: string;
  displayName?: string;
  domain?: string;
  publishable?: boolean;
  evidenceBasis?: string;
  evidenceBasisLabel?: string;
  formula?: string;
  computability?: string;
  computabilityLabel?: string;
  computabilityTone?: string;
  gap?: string;
  gapCode?: string | null;
  externalEligible?: boolean;
  externalStatus?: string;
  externalLabel?: string;
  externalReason?: string;
  executionPath?: string;
  executable?: boolean;
  executionReason?: string;
  variantOf?: string | null;
  outputMode?: string | null;
}

export interface MetricReportManifest {
  items: MetricReportItem[];
  count: number;
  meta?: {
    total?: number;
    counts?: {
      external?: number;
      externalCandidates?: number;
      executableNow?: number;
    };
    tiers?: Record<string, number>;
  };
  filters?: Record<string, unknown>;
}

export function useGetMetricReportManifest(
  namespaceId: string,
  scope: "all" | "external" = "all",
) {
  const apiClient = useApiClient();

  return useQuery<MetricReportManifest, Error>({
    queryKey: ["metric-report-manifest", namespaceId, scope],
    queryFn: () =>
      apiClient.get<MetricReportManifest>(
        `/namespaces/${encodeURIComponent(namespaceId)}/metrics/report/manifest?scope=${scope}`,
      ),
    enabled: !!namespaceId,
  });
}

export interface OntologyClassRef {
  iri: string;
  label?: string;
}

/**
 * Class list used to resolve a metric grain to the ontology class it counts.
 * Deliberately the kernel's browse read rather than graph search: it needs no
 * ontology-engine hop, and the card only needs iri + label.
 */
export function useOntologyClasses(namespaceId: string) {
  const apiClient = useApiClient();

  return useQuery<{ classes: OntologyClassRef[] }, Error>({
    queryKey: ["ontology-classes", namespaceId],
    queryFn: () =>
      apiClient.get<{ classes: OntologyClassRef[] }>("/browse/ontology/tree"),
    enabled: !!namespaceId,
  });
}

export interface OntologyInstanceRef {
  iri: string;
  label?: string;
}

export function useClassInstances(
  namespaceId: string,
  classIri: string | undefined,
  limit = 5,
) {
  const apiClient = useApiClient();

  return useQuery<{ items: OntologyInstanceRef[]; total: number }, Error>({
    queryKey: ["ontology-instances", namespaceId, classIri ?? null, limit],
    queryFn: () =>
      apiClient.get<{ items: OntologyInstanceRef[]; total: number }>(
        `/browse/ontology/instances?class=${encodeURIComponent(classIri!)}&limit=${limit}`,
      ),
    enabled: !!namespaceId && !!classIri,
  });
}
