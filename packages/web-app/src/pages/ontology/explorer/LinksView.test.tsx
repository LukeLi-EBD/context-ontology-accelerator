// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, fireEvent, waitFor, cleanup, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { LinksView } from "./LinksView";
import type { ApiClient } from "@components/ApiClientProvider";

const findGraphLinks = vi.fn();
vi.mock("../../../services/ontology-engine", () => ({
  findGraphLinks: (...args: unknown[]) => findGraphLinks(...args),
}));

const apiClient: ApiClient = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
};

const HOPPER = "https://example.org/p15#";

function result() {
  return {
    nodes: [
      { uri: `${HOPPER}B`, label: "B", kind: "resource", hops: 1 },
      { uri: `${HOPPER}C`, label: "C", kind: "resource", hops: 2 },
      { uri: `${HOPPER}D`, label: "D", kind: "resource", hops: 3 },
    ],
    edges: [1, 2, 3].map((hops) => ({
      source: `${HOPPER}${String.fromCharCode(64 + hops)}`,
      predicate: "https://example.org/p15#next",
      predicateLabel: "next",
      target: `${HOPPER}${String.fromCharCode(65 + hops)}`,
      graph: "g",
      direction: "outgoing",
      hops,
    })),
    truncated: false,
  };
}

function renderView() {
  const rendered = render(<LinksView apiClient={apiClient} namespace="ns" />);
  return within(rendered.container);
}

async function search(view: ReturnType<typeof renderView>, uri: string) {
  fireEvent.change(view.getByLabelText("Seed IRI"), { target: { value: uri } });
  fireEvent.click(view.getByRole("button", { name: "Find links" }));
}

describe("LinksView", () => {
  beforeEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the returned neighbourhood with its hop for every node and edge", async () => {
    findGraphLinks.mockResolvedValue(result());
    const view = renderView();

    await search(view, `${HOPPER}A`);

    await waitFor(() =>
      expect(findGraphLinks).toHaveBeenCalledWith(apiClient, "ns", `${HOPPER}A`, {
        direction: "both",
        max_hops: 3,
        limit: 200,
      }),
    );
    await view.findByText("Adjacency edges");
    // Hop 3 is visible, and nothing from a fourth hop leaked in.
    expect(view.getAllByText(`${HOPPER}D`).length).toBeGreaterThan(0);
    expect(view.queryByText(`${HOPPER}E`)).toBeNull();
    // Both tables carry the hop column, so the 3-hop ceiling is inspectable.
    expect(view.getAllByText("Hops").length).toBeGreaterThanOrEqual(2);
  });

  it("shows an explicit empty state when the IRI has no adjacency", async () => {
    findGraphLinks.mockResolvedValue({ nodes: [], edges: [], truncated: false });
    const view = renderView();

    await search(view, `${HOPPER}Isolated`);

    expect(
      await view.findByText("No links found for this IRI."),
    ).toBeInTheDocument();
  });

  it("never lets max hops exceed the contractual three", async () => {
    const view = renderView();
    const hops = view.getByLabelText("Max hops") as HTMLInputElement;

    fireEvent.change(hops, { target: { value: "9" } });

    expect(hops.value).toBe("3");
  });
});
