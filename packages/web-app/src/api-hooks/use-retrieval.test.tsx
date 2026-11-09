// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  KBSearchCommand,
  QueryCommand,
} from "@coa/data-layer-client";
import { useAskNamespace, useKbSearch } from "./use-retrieval";

const mockSend = vi.fn();

vi.mock("@components/DataLayerClientProvider", () => ({
  useDataLayerClient: () => ({ send: mockSend }),
}));

const NS_ID = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd";

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>
      {children}
    </QueryClientProvider>
  );
}

describe("use-retrieval", () => {
  beforeEach(() => {
    mockSend.mockReset();
  });

  it("sends KBSearch with the namespace, query and a bounded topK", async () => {
    mockSend.mockResolvedValueOnce({
      chunks: [
        {
          chunkId: "c1",
          text: "采购票据的金额为 1200",
          sourceDocumentName: "采购合同.pdf",
          relevanceScore: 0.83,
        },
      ],
      trace: [],
    });

    const { result } = renderHook(() => useKbSearch(NS_ID), { wrapper });
    await result.current.mutateAsync("采购票据 的金额是多少");

    const command = mockSend.mock.calls[0][0];
    expect(command).toBeInstanceOf(KBSearchCommand);
    expect(command.input).toEqual({
      namespaceId: NS_ID,
      query: "采购票据 的金额是多少",
      topK: 5,
    });
    await waitFor(() =>
      expect(result.current.data?.chunks?.[0]?.chunkId).toBe("c1"),
    );
  });

  it("pins Query to standard mode and asks for supporting content", async () => {
    mockSend.mockResolvedValueOnce({
      result: { tier: 3, confidence: { score: 0.7 }, trace: [], synthesizedAnswer: "1200" },
    });

    const { result } = renderHook(() => useAskNamespace(NS_ID), { wrapper });
    await result.current.mutateAsync("当事人和协议之间是什么关系？");

    const command = mockSend.mock.calls[0][0];
    expect(command).toBeInstanceOf(QueryCommand);
    expect(command.input).toEqual({
      namespaceId: NS_ID,
      query: "当事人和协议之间是什么关系？",
      mode: "standard",
      includeSupporting: true,
    });
    await waitFor(() =>
      expect(result.current.data?.result.synthesizedAnswer).toBe("1200"),
    );
  });
});
