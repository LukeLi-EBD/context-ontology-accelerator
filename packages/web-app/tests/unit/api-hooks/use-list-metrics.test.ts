// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { ListMetricsCommand } from "@coa/control-plane-client";
import { useListMetrics } from "../../../src/api-hooks/use-metrics";

const mockSend = vi.fn();
vi.mock("../../../src/components/ControlPlaneClientProvider", () => ({
  useControlPlaneClient: () => ({ send: mockSend }),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return React.createElement(
    QueryClientProvider,
    { client: queryClient },
    children,
  );
}

describe("useListMetrics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns metrics on success", async () => {
    mockSend.mockResolvedValueOnce({
      metrics: [
        {
          name: "revenue",
          description: "Total revenue",
          expression: { dialects: [{ dialect: "POSTGRESQL", sql: "SELECT 1" }] },
          dataSourceId: "ds-1",
          sourceTable: "orders",
        },
      ],
      nextToken: undefined,
    });

    const { result } = renderHook(() => useListMetrics("ns-1"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].metrics).toHaveLength(1);
    expect(result.current.data?.pages[0].metrics[0].name).toBe("revenue");
  });

  it("passes maxResults and the namespace through the ListMetrics command", async () => {
    mockSend.mockResolvedValueOnce({ metrics: [], nextToken: undefined });

    const { result } = renderHook(() => useListMetrics("ns-1", 100), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const command = mockSend.mock.calls[0][0];
    expect(command).toBeInstanceOf(ListMetricsCommand);
    expect(command.input).toEqual({
      namespaceId: "ns-1",
      maxResults: 100,
      nextToken: undefined,
    });
  });

  it("reports hasNextPage when nextToken is present", async () => {
    mockSend.mockResolvedValueOnce({
      metrics: [
        {
          name: "m1",
          description: "d",
          expression: { dialects: [] },
          dataSourceId: "ds-1",
          sourceTable: "t",
        },
      ],
      nextToken: "50",
    });

    const { result } = renderHook(() => useListMetrics("ns-1"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.hasNextPage).toBe(true);
  });

  it("reports no next page when nextToken is absent", async () => {
    mockSend.mockResolvedValueOnce({
      metrics: [
        {
          name: "m1",
          description: "d",
          expression: { dialects: [] },
          dataSourceId: "ds-1",
          sourceTable: "t",
        },
      ],
    });

    const { result } = renderHook(() => useListMetrics("ns-1"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.hasNextPage).toBe(false);
  });

  it("does not fetch when namespaceId is empty", async () => {
    const { result } = renderHook(() => useListMetrics(""), { wrapper });

    // Should stay in idle/pending state without calling the API
    expect(mockSend).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  it("sets error when query fails", async () => {
    mockSend.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useListMetrics("ns-1"), { wrapper });

    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error?.message).toBe("Network error");
  });
});
