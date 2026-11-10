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
    fetch(`/questions/${encodeURIComponent(namespaceId)}.json`, {
      headers: { Accept: "application/json" },
    })
      .then(async (res) => {
        if (cancelled) return;
        if (res.status === 404) {
          setState({ questions: [], status: "missing" });
          return;
        }
        if (!res.ok) {
          setState({ questions: [], status: "error" });
          return;
        }
        const data = (await res.json()) as QuestionsFile | null;
        if (cancelled) return;
        if (!data || !Array.isArray(data.questions)) {
          setState({ questions: [], status: "error" });
          return;
        }
        setState({
          questions: data.questions.filter(
            (q): q is ExampleQuestion =>
              typeof q?.question === "string" && q.question.length > 0,
          ),
          status: "ready",
        });
      })
      .catch(() => {
        if (!cancelled) setState({ questions: [], status: "error" });
      });
    return () => {
      cancelled = true;
    };
  }, [namespaceId]);

  return state;
}
