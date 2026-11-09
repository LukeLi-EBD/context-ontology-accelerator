// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useMutation } from "@tanstack/react-query";
import { GraphSearchCommand } from "@coa/control-plane-client";
import type { ControlPlaneServiceServiceException } from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

/**
 * Named graph the approval path projects an accepted fact into
 * (`urn:coa:abox:documents`, see the sources candidate routes). Searching this
 * one graph keeps the request cheap: the namespace also carries large synthetic
 * A-Box graphs that an unscoped search would have to scan.
 */
export const DOCUMENT_ABOX_ONTOLOGY_ID = "urn:coa:abox:documents";

export interface AboxFactVerification {
  /** The IRI the approval path derives from the candidate subject. */
  entityUri: string;
  /** True when the entity is present in the documents A-Box graph. */
  found: boolean;
  /** Named graphs the matching entity was seen in (empty when not found). */
  graphUris: string[];
}

/**
 * Read the A-Box back through GraphSearch to confirm an approved candidate was
 * materialised. This is a real query against the ontology engine (via the
 * generated control-plane client), not a cached local flag: after a stack
 * restart it still answers from the graph.
 */
export function useVerifyAboxFact(namespaceId: string) {
  const client = useControlPlaneClient();

  return useMutation<
    AboxFactVerification,
    ControlPlaneServiceServiceException,
    { subject: string }
  >({
    mutationFn: async ({ subject }) => {
      const entityUri = `urn:coa:entity:${encodeURIComponent(subject)}`;
      const output = await client.send(
        new GraphSearchCommand({
          namespaceId,
          q: entityUri,
          ontologyId: DOCUMENT_ABOX_ONTOLOGY_ID,
          limit: 10,
        }),
      );
      const hit = (output.hits ?? []).find(
        (candidate) =>
          decodeURIComponent(candidate.uri ?? "") ===
          decodeURIComponent(entityUri),
      );
      return {
        entityUri,
        found: Boolean(hit),
        graphUris: hit?.graphUris ?? [],
      };
    },
  });
}
