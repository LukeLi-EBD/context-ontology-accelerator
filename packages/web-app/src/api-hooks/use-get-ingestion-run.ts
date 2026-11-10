// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useQuery } from "@tanstack/react-query";
import { GetIngestionRunCommand } from "@coa/control-plane-client";
import type { GetIngestionRunOutput } from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

/**
 * F17: one import batch with its latest attempt and its per-item rows. Used by
 * the read-only run detail page; the list page keeps using
 * `useListIngestionRuns` for the summary counters.
 */
export function useGetIngestionRun(namespaceId: string, runId: string) {
  const client = useControlPlaneClient();

  return useQuery<GetIngestionRunOutput, Error>({
    queryKey: ["ingestion-run", namespaceId, runId],
    queryFn: () =>
      client.send(new GetIngestionRunCommand({ namespaceId, runId })),
    enabled: !!namespaceId && !!runId,
  });
}
