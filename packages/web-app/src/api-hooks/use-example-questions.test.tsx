// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useExampleQuestions } from "./use-example-questions";

const NS_ID = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd";

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response;
}

describe("useExampleQuestions", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads and filters the published questions file", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse({
        questions: [
          { label: "Agreement", question: "Agreement 有哪些形态？" },
          { label: "broken", question: "" },
        ],
      }),
    );

    const { result } = renderHook(() => useExampleQuestions(NS_ID));

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.questions).toEqual([
      { label: "Agreement", question: "Agreement 有哪些形态？" },
    ]);
    expect(fetch).toHaveBeenCalledWith(
      `/questions/${NS_ID}.json`,
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
  });

  it("reports a missing file as `missing` (not as an empty list)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(null, 404));

    const { result } = renderHook(() => useExampleQuestions(NS_ID));

    await waitFor(() => expect(result.current.status).toBe("missing"));
    expect(result.current.questions).toEqual([]);
  });

  it("reports an unreadable file as `error`", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({}, 500));

    const { result } = renderHook(() => useExampleQuestions(NS_ID));

    await waitFor(() => expect(result.current.status).toBe("error"));
  });

  it("reports malformed JSON as `error` instead of showing nothing", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ questions: "nope" }));

    const { result } = renderHook(() => useExampleQuestions(NS_ID));

    await waitFor(() => expect(result.current.status).toBe("error"));
  });

  it("reports a network failure as `error`", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("offline"));

    const { result } = renderHook(() => useExampleQuestions(NS_ID));

    await waitFor(() => expect(result.current.status).toBe("error"));
  });
});
