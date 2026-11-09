// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { ListDocumentChunksCommand } from "@coa/control-plane-client";
import type { ListDocumentChunksOutput } from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

export function useListDocumentChunks(namespaceId: string, documentId: string) {
  const client = useControlPlaneClient();

  const query = useInfiniteQuery<ListDocumentChunksOutput, Error>({
    queryKey: ["document-chunks", namespaceId, documentId],
    queryFn: async ({ pageParam }) => {
      return client.send(
        new ListDocumentChunksCommand({
          namespaceId,
          documentId,
          maxResults: 200,
          nextToken: pageParam as string | undefined,
        }),
      );
    },
    getNextPageParam: (lastPage) => lastPage.nextToken,
    initialPageParam: undefined as string | undefined,
    enabled: !!namespaceId && !!documentId,
  });

  const { hasNextPage, isFetchingNextPage, fetchNextPage } = query;
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  return query;
}
