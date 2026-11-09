// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useMutation } from "@tanstack/react-query";
import { useApiClient } from "@components/ApiClientProvider";

/** One embedding row returned by the ontology engine, vector included. */
export interface ChunkEmbedding {
  id: string;
  ontology_id: string;
  entity_uri: string;
  entity_type: string;
  embedding_type: string;
  model_id: string;
  dimensions: number;
  created_at: string;
  vector: number[];
  metadata?: Record<string, unknown> | null;
}

export interface ChunkVectorSearchResult {
  embedding: ChunkEmbedding;
  hits: ChunkEmbedding[];
}

function chunkEntityUri(chunkId: string): string {
  return `urn:coa:chunk:${chunkId}`;
}

/**
 * Reads the stored vector of one chunk and uses it as the query for a real
 * k-NN search. Both calls go through the existing ontology embeddings routes;
 * no client-side embedding or fake hit list is involved.
 */
export function useChunkVectorSearch(namespaceId: string) {
  const apiClient = useApiClient();

  return useMutation<ChunkVectorSearchResult, Error, string>({
    mutationFn: async (chunkId) => {
      const entityUri = encodeURIComponent(chunkEntityUri(chunkId));
      const rows = await apiClient.get<ChunkEmbedding[]>(
        `/namespaces/${encodeURIComponent(namespaceId)}/embeddings/by-entity/${entityUri}?entity_type=chunk&embedding_type=chunk`,
      );
      const embedding = rows[0];
      if (!embedding || !embedding.vector?.length) {
        throw new Error("CHUNK_VECTOR_NOT_FOUND");
      }
      const hits = await apiClient.post<ChunkEmbedding[]>(
        `/namespaces/${encodeURIComponent(namespaceId)}/embeddings/search`,
        {
          vector: embedding.vector,
          entity_type: "chunk",
          embedding_type: "chunk",
          model_id: embedding.model_id,
          top_k: 5,
        },
      );
      return { embedding, hits };
    },
  });
}
