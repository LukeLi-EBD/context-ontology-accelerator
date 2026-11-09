// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ApproveFactCandidateCommand,
  ControlPlaneServiceServiceException,
  RejectFactCandidateCommand,
} from "@coa/control-plane-client";
import type {
  ApproveFactCandidateInput,
  ApproveFactCandidateOutput,
  RejectFactCandidateInput,
  RejectFactCandidateOutput,
} from "@coa/control-plane-client";
import { useControlPlaneClient } from "@components/ControlPlaneClientProvider";

/**
 * Approve or reject one extracted candidate. Both operations are idempotent on
 * the server; the list is invalidated so the new status comes from the API,
 * never from optimistic local state.
 */
export function useReviewFactCandidate(namespaceId: string) {
  const client = useControlPlaneClient();
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({
      queryKey: ["fact-candidates", namespaceId],
    });
    // Approving also materialises a fact row, so the document counters and the
    // candidate lists for other filters are stale too.
    queryClient.invalidateQueries({ queryKey: ["documents", namespaceId] });
  };

  const approve = useMutation<
    ApproveFactCandidateOutput,
    ControlPlaneServiceServiceException,
    Omit<ApproveFactCandidateInput, "namespaceId">
  >({
    mutationFn: async (input) => {
      return client.send(
        new ApproveFactCandidateCommand({ namespaceId, ...input }),
      );
    },
    onSuccess: invalidate,
  });

  const reject = useMutation<
    RejectFactCandidateOutput,
    ControlPlaneServiceServiceException,
    Omit<RejectFactCandidateInput, "namespaceId">
  >({
    mutationFn: async (input) => {
      return client.send(
        new RejectFactCandidateCommand({ namespaceId, ...input }),
      );
    },
    onSuccess: invalidate,
  });

  return { approve, reject };
}
