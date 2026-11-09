// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ControlPlaneServiceServiceException,
  UploadDocumentCommand,
} from "@coa/control-plane-client";
import type {
  UploadDocumentInput,
  UploadDocumentOutput,
} from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

/**
 * Uploads one document through the generated client. The server writes the
 * document row and schedules ingestion; nothing is derived client-side.
 */
export function useUploadDocument() {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  return useMutation<
    UploadDocumentOutput,
    ControlPlaneServiceServiceException,
    UploadDocumentInput
  >({
    mutationFn: async (input) => {
      return client.send(new UploadDocumentCommand(input));
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["documents", variables.namespaceId],
      });
    },
  });
}
