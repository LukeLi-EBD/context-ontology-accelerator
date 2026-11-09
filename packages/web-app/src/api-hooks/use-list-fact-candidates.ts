// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { ListFactCandidatesCommand } from "@coa/control-plane-client";
import type {
  FactCandidateStatus,
  ListFactCandidatesOutput,
} from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

export interface FactCandidateFilters {
  status?: FactCandidateStatus;
  documentId?: string;
}

export function useListFactCandidates(
  namespaceId: string,
  filters: FactCandidateFilters = {},
) {
  const client = useControlPlaneClient();
  const { status, documentId } = filters;

  const query = useInfiniteQuery<ListFactCandidatesOutput, Error>({
    queryKey: [
      "fact-candidates",
      namespaceId,
      status ?? "all",
      documentId ?? "all",
    ],
    queryFn: async ({ pageParam }) => {
      return client.send(
        new ListFactCandidatesCommand({
          namespaceId,
          status,
          documentId,
          maxResults: 100,
          nextToken: pageParam as string | undefined,
        }),
      );
    },
    getNextPageParam: (lastPage) => lastPage.nextToken,
    initialPageParam: undefined as string | undefined,
    enabled: !!namespaceId,
  });

  const { hasNextPage, isFetchingNextPage, fetchNextPage } = query;
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  return query;
}
