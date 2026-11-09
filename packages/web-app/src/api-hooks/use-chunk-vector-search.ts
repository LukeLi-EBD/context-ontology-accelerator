// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useMutation } from "@tanstack/react-query";
import {
  GetEntityEmbeddingsCommand,
  SearchEmbeddingsCommand,
} from "@coa/control-plane-client";
import type { EmbeddingRecord } from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

export interface ChunkVectorSearchResult {
  embedding: EmbeddingRecord;
  hits: EmbeddingRecord[];
}

function chunkEntityUri(chunkId: string): string {
  return `urn:coa:chunk:${chunkId}`;
}

/**
 * Reads the stored vector of one chunk and uses it as the query for a real
 * k-NN search. Both calls go through the generated control-plane client
 * (GetEntityEmbeddings / SearchEmbeddings); no client-side embedding or fake
 * hit list is involved.
 */
export function useChunkVectorSearch(namespaceId: string) {
  const client = useControlPlaneClient();

  return useMutation<ChunkVectorSearchResult, Error, string>({
    mutationFn: async (chunkId) => {
      const stored = await client.send(
        new GetEntityEmbeddingsCommand({
          namespaceId,
          entityUri: chunkEntityUri(chunkId),
          entityType: "chunk",
          embeddingType: "chunk",
        }),
      );
      const embedding = stored.embeddings?.[0];
      if (!embedding || !embedding.vector?.length) {
        throw new Error("CHUNK_VECTOR_NOT_FOUND");
      }
      const nearest = await client.send(
        new SearchEmbeddingsCommand({
          namespaceId,
          vector: embedding.vector,
          entityType: "chunk",
          embeddingType: "chunk",
          modelId: embedding.modelId,
          topK: 5,
        }),
      );
      return { embedding, hits: nearest.embeddings ?? [] };
    },
  });
}
