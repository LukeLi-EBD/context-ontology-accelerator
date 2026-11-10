// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useQuery } from "@tanstack/react-query";
import { ListIngestionRunsCommand } from "@coa/control-plane-client";
import type {
  IngestionRunStatus,
  ListIngestionRunsOutput,
} from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

/**
 * F17/F18: namespace-scoped import batches. One page is enough for the console
 * view (the op caps a page at 50); `refetch` is what the Refresh button uses so
 * the per-item counters follow the importer without a page reload.
 */
export function useListIngestionRuns(
  namespaceId: string,
  status?: IngestionRunStatus,
) {
  const client = useControlPlaneClient();

  return useQuery<ListIngestionRunsOutput, Error>({
    queryKey: ["ingestion-runs", namespaceId, status ?? "all"],
    queryFn: () =>
      client.send(
        new ListIngestionRunsCommand({
          namespaceId,
          kind: "BATCH",
          status,
          maxResults: 50,
        }),
      ),
    enabled: !!namespaceId,
  });
}
