// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";

/** A single sample prompt shown on the empty playground. */
export interface ExampleQuestion {
  /** Short chip label. Falls back to `question` when omitted. */
  label?: string;
  /** Full natural-language query sent to the serve layer on click. */
  question: string;
  /** Optional tier hint (e.g. "T1", "T2", "T3") — display only. */
  tier?: string;
  /** Optional execution-path hint (e.g. "jdbc", "athena-federation") — display only. */
  path?: string;
}

interface QuestionsFile {
  questions?: ExampleQuestion[];
}

/**
 * `missing` means the namespace has no published questions file (404) — a
 * legitimate state the UI renders as an explicit hint, not as "no prompts
 * exist anywhere". `error` means the file exists but could not be read or
 * parsed; the UI says so instead of showing an empty list.
 */
export type ExampleQuestionsStatus = "loading" | "ready" | "missing" | "error";

export interface ExampleQuestionsState {
  questions: ExampleQuestion[];
  status: ExampleQuestionsStatus;
}

async function loadQuestions(
  namespaceId: string,
): Promise<ExampleQuestionsState> {
  try {
    const res = await fetch(`/questions/${encodeURIComponent(namespaceId)}.json`, {
      headers: { Accept: "application/json" },
    });
    if (res.status === 404) return { questions: [], status: "missing" };
    if (!res.ok) return { questions: [], status: "error" };
    const data = (await res.json()) as QuestionsFile | null;
    if (!data || !Array.isArray(data.questions)) {
      return { questions: [], status: "error" };
    }
    return {
      questions: data.questions.filter(
        (q): q is ExampleQuestion =>
          typeof q?.question === "string" && q.question.length > 0,
      ),
      status: "ready",
    };
  } catch {
    return { questions: [], status: "error" };
  }
}

/**
 * Remounting the Playground (React StrictMode double-invokes effects in
 * development) must not fetch the same file twice, so a request already in
 * flight is shared until it settles.
 */
const inFlight = new Map<string, Promise<ExampleQuestionsState>>();

function questionsRequest(namespaceId: string): Promise<ExampleQuestionsState> {
  const pending = inFlight.get(namespaceId);
  if (pending) return pending;
  const request = loadQuestions(namespaceId);
  inFlight.set(namespaceId, request);
  void request.then(
    () => inFlight.delete(namespaceId),
    () => inFlight.delete(namespaceId),
  );
  return request;
}

/**
 * Loads per-namespace sample prompts published to the UI origin at
 * `/questions/{namespaceId}.json` (same origin that serves
 * `runtime-config.json`).
 */
export function useExampleQuestions(namespaceId: string): ExampleQuestionsState {
  const [state, setState] = useState<ExampleQuestionsState>({
    questions: [],
    status: "loading",
  });

  useEffect(() => {
    if (!namespaceId) {
      setState({ questions: [], status: "loading" });
      return;
    }
    let cancelled = false;
    void questionsRequest(namespaceId).then((result) => {
      if (!cancelled) setState(result);
    });
    return () => {
      cancelled = true;
    };
  }, [namespaceId]);

  return state;
}
