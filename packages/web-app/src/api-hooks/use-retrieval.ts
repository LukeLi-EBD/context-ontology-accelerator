// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useMutation } from "@tanstack/react-query";
import {
  KBSearchCommand,
  QueryCommand,
  QueryMode,
  type KBSearchOutput,
  type QueryOutput,
} from "@coa/data-layer-client";
import { useDataLayerClient } from "@components/DataLayerClientProvider";

/**
 * Knowledge-base search (`KBSearch` op, `POST /namespaces/{ns}/kb/search`).
 * Returns ranked chunks with provenance — the retrieval primitive behind the
 * Retrieval page's "Knowledge-base search" panel.
 */
export function useKbSearch(namespaceId: string) {
  const client = useDataLayerClient();

  return useMutation<KBSearchOutput, Error, string>({
    mutationFn: (query) =>
      client.send(
        new KBSearchCommand({ namespaceId, query, topK: 5 }),
      ),
  });
}

/**
 * Natural-language query (`Query` op, `POST /namespaces/{ns}/query`). Pinned
 * to `standard` mode: the service's `deep-reasoning` mode has a p50 of ~90 s,
 * which no browser request should wait on.
 */
export function useAskNamespace(namespaceId: string) {
  const client = useDataLayerClient();

  return useMutation<QueryOutput, Error, string>({
    mutationFn: (query) =>
      client.send(
        new QueryCommand({
          namespaceId,
          query,
          mode: QueryMode.STANDARD,
          includeSupporting: true,
        }),
      ),
  });
}
