// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryCommand, QueryMode } from "@coa/data-layer-client";
import { usePlaygroundChatLocal } from "./use-playground-chat-local";

const mockSend = vi.fn();

vi.mock("@components/DataLayerClientProvider", () => ({
  useDataLayerClient: () => ({ send: mockSend }),
}));

let uuidCounter = 0;
vi.stubGlobal("crypto", {
  randomUUID: () => `uuid-${++uuidCounter}`,
});

const NS_ID = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd";

function localResponse(answer: string) {
  return {
    requestId: "req-1",
    result: {
      tier: 2,
      confidence: { score: 0.82, rationale: "chunks answered it" },
      synthesizedAnswer: answer,
      trace: [
        { step: "retrieve", status: "done", durationMs: 12 },
        { step: "synthesize", status: "done", durationMs: 30 },
      ],
      supportingContent: [
        {
          chunkId: "phase3-chunk-1",
          text: "协议的具体形态",
          sourceDocumentId: "572e1140f6055a0083a7be9e4118eec0",
          relevanceScore: 0.55,
        },
      ],
      guardrailBlocked: false,
      partial: false,
    },
  };
}

describe("usePlaygroundChatLocal", () => {
  beforeEach(() => {
    mockSend.mockReset();
    uuidCounter = 0;
  });

  it("sends the query to the local bridge as a single non-streaming request", async () => {
    mockSend.mockResolvedValueOnce(localResponse("协议形态是账户、保单、贷款合同等。"));

    const { result } = renderHook(() =>
      usePlaygroundChatLocal({ namespaceId: NS_ID, enabled: true }),
    );

    act(() => {
      result.current.sendQuery("Agreement 有哪些形态？", "standard");
    });

    const command = mockSend.mock.calls[0][0];
    expect(command).toBeInstanceOf(QueryCommand);
    expect(command.input).toEqual({
      namespaceId: NS_ID,
      query: "Agreement 有哪些形态？",
      mode: QueryMode.STANDARD,
      includeSupporting: true,
    });

    await waitFor(() =>
      expect(result.current.state.messages[1]?.response).toBeDefined(),
    );
    expect(result.current.state.messages[1].content).toContain("账户");
    expect(result.current.state.messages[1].response?.result.trace).toHaveLength(
      2,
    );
    expect(
      result.current.state.messages[1].response?.result.supportingContent?.[0]
        ?.chunkId,
    ).toBe("phase3-chunk-1");
    expect(result.current.isStreaming).toBe(false);
  });

  it("maps deep-reasoning to the wire enum", async () => {
    mockSend.mockResolvedValueOnce(localResponse("deep"));

    const { result } = renderHook(() =>
      usePlaygroundChatLocal({ namespaceId: NS_ID, enabled: true }),
    );

    act(() => {
      result.current.sendQuery("为什么统一建模为 PARTY？", "deep-reasoning");
    });

    expect(mockSend.mock.calls[0][0].input.mode).toBe(QueryMode.DEEP_REASONING);
    await waitFor(() =>
      expect(result.current.state.messages[1]?.response).toBeDefined(),
    );
  });

  it("surfaces a bridge failure as an assistant error bubble", async () => {
    mockSend.mockRejectedValueOnce(new Error("bridge unavailable"));

    const { result } = renderHook(() =>
      usePlaygroundChatLocal({ namespaceId: NS_ID, enabled: true }),
    );

    act(() => {
      result.current.sendQuery("任意问题");
    });

    await waitFor(() =>
      expect(result.current.state.messages[1]?.error).toBeDefined(),
    );
    expect(result.current.state.messages[1].error?.error).toBe(
      "LocalQueryFailed",
    );
    expect(result.current.state.messages[1].content).toBe("bridge unavailable");
    expect(result.current.isStreaming).toBe(false);
  });

  it("does not send when the streaming branch owns the page", async () => {
    const { result } = renderHook(() =>
      usePlaygroundChatLocal({ namespaceId: NS_ID, enabled: false }),
    );

    act(() => {
      result.current.sendQuery("不应发送");
    });

    expect(mockSend).not.toHaveBeenCalled();
    expect(result.current.state.messages).toHaveLength(0);
  });

  it("clears the transcript on new chat without creating a serve session", async () => {
    mockSend.mockResolvedValueOnce(localResponse("answer"));

    const { result } = renderHook(() =>
      usePlaygroundChatLocal({ namespaceId: NS_ID, enabled: true }),
    );

    act(() => {
      result.current.sendQuery("问题");
    });
    await waitFor(() =>
      expect(result.current.state.messages).toHaveLength(2),
    );

    act(() => {
      result.current.newChat();
    });
    expect(result.current.state.messages).toHaveLength(0);
    // Only the query itself hit the bridge — no session action.
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
