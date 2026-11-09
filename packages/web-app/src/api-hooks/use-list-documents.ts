// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { ListDocumentsCommand } from "@coa/control-plane-client";
import type {
  DocumentStatus,
  ListDocumentsOutput,
} from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

// Ingestion is asynchronous in the local stack too: the upload handler writes
// the document row as PROCESSING and a worker flips it to INDEXED/FAILED.
const ACTIVE_STATUSES = new Set<string>(["UPLOADED", "PROCESSING"]);
const POLL_INTERVAL_MS = 2_000;

export function useListDocuments(namespaceId: string, status?: DocumentStatus) {
  const client = useControlPlaneClient();

  const query = useInfiniteQuery<ListDocumentsOutput, Error>({
    queryKey: ["documents", namespaceId, status ?? "all"],
    queryFn: async ({ pageParam }) => {
      return client.send(
        new ListDocumentsCommand({
          namespaceId,
          status,
          maxResults: 100,
          nextToken: pageParam as string | undefined,
        }),
      );
    },
    getNextPageParam: (lastPage) => lastPage.nextToken,
    initialPageParam: undefined as string | undefined,
    refetchInterval: (q) => {
      const pages = q.state.data?.pages ?? [];
      const hasActive = pages.some((page) =>
        (page.items ?? []).some((item) =>
          ACTIVE_STATUSES.has(item.status ?? ""),
        ),
      );
      return hasActive ? POLL_INTERVAL_MS : false;
    },
    enabled: !!namespaceId,
  });

  // Load every page so the list is complete (the summary counters rely on it).
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = query;
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  return query;
}
