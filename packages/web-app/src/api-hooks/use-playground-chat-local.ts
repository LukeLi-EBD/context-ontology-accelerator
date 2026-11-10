// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Local, non-streaming Playground chat.
 *
 * Used only when the deployment publishes no `serveRuntimeArn`: the browser then
 * calls the local bridge's `POST /namespaces/{namespaceId}/query` instead of
 * AgentCore's `/invocations`. The condition is one-way — when an ARN is
 * published the streaming path is used unchanged.
 *
 * An absent ARN is a legitimate local deployment, not a misconfiguration, so
 * nothing here raises a config error. The answer arrives in one response; the
 * page labels this mode explicitly and must not fake token-by-token output.
 */
import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import {
  QueryCommand,
  type QueryStrategy as WireQueryStrategy,
} from "@coa/data-layer-client";
import { QueryMode } from "@coa/data-layer-client";
import { useDataLayerClient } from "@components/DataLayerClientProvider";
import type {
  ChatMessage,
  ExecutionMode,
  PlaygroundResponse,
  QueryStrategy,
} from "@app-types/playground";
import { INITIAL_STATE, playgroundReducer } from "./playground-reducer";
import type { UsePlaygroundChatSSEReturn } from "./use-playground-chat-sse";

export interface UsePlaygroundChatLocalOptions {
  namespaceId: string;
  /** Only the local branch may send; the streaming branch owns the rest. */
  enabled: boolean;
}

function toWireMode(mode?: ExecutionMode): QueryMode {
  return mode === "deep-reasoning"
    ? QueryMode.DEEP_REASONING
    : QueryMode.STANDARD;
}

export function usePlaygroundChatLocal({
  namespaceId,
  enabled,
}: UsePlaygroundChatLocalOptions): UsePlaygroundChatSSEReturn {
  const client = useDataLayerClient();
  const [state, dispatch] = useReducer(playgroundReducer, INITIAL_STATE);
  const [isSending, setIsSending] = useState(false);

  const messagesRef = useRef(state.messages);
  useEffect(() => {
    messagesRef.current = state.messages;
  }, [state.messages]);

  const runQuery = useCallback(
    async (
      query: string,
      requestId: string,
      mode?: ExecutionMode,
      strategy?: QueryStrategy,
    ) => {
      try {
        const output = await client.send(
          new QueryCommand({
            namespaceId,
            query,
            mode: toWireMode(mode),
            ...(strategy && {
              strategy: strategy as WireQueryStrategy,
            }),
            includeSupporting: true,
          }),
        );
        // The bridge returns { result, requestId, ... }; the reducer normalizes
        // it exactly as it does for the streaming done event.
        dispatch({
          type: "DONE",
          requestId,
          response: output as unknown as PlaygroundResponse,
        });
      } catch (err) {
        dispatch({
          type: "ERROR",
          requestId,
          error: "LocalQueryFailed",
          message: err instanceof Error ? err.message : String(err),
        });
      } finally {
        setIsSending(false);
      }
    },
    [client, namespaceId],
  );

  const sendQuery = useCallback(
    (query: string, mode?: ExecutionMode, strategy?: QueryStrategy) => {
      if (!enabled || !namespaceId || isSending) return;

      const requestId = crypto.randomUUID();
      dispatch({
        type: "SEND_QUERY",
        id: crypto.randomUUID(),
        requestId,
        query,
      });
      setIsSending(true);
      void runQuery(query, requestId, mode, strategy);
    },
    [enabled, namespaceId, isSending, runQuery],
  );

  const retryQuery = useCallback(
    (message: ChatMessage, mode?: ExecutionMode, strategy?: QueryStrategy) => {
      if (!enabled || !namespaceId) return;
      if (message.role !== "assistant") return;
      if (message.isLoading || isSending) return;
      if (!message.replyToId) return;

      const userMsg = messagesRef.current.find(
        (m) => m.id === message.replyToId,
      );
      if (!userMsg || userMsg.role !== "user") return;

      const requestId = crypto.randomUUID();
      dispatch({ type: "RETRY", messageId: message.id, requestId });
      setIsSending(true);
      void runQuery(userMsg.content, requestId, mode, strategy);
    },
    [enabled, namespaceId, isSending, runQuery],
  );

  const newChat = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return {
    state,
    // The local bridge has no serve-side session store in this deployment.
    sessionId: null,
    isRestoring: false,
    showRestoreSpinner: false,
    restoreTimedOut: false,
    dismissRestoreWarning: () => {},
    // Reported as `isStreaming` to share the page's in-flight guard, but this
    // mode is a single request/response — the UI labels it non-streaming.
    isStreaming: isSending,
    sendQuery,
    retryQuery,
    newChat,
    hasMoreHistory: false,
    isLoadingOlderHistory: false,
    requestOlderHistory: () => {},
  };
}
