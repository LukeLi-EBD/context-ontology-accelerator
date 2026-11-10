// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { HomePage } from "./HomePage";

const navigate = vi.fn();

// Namespace list decides whether the first-use guide (F03) is shown.
const namespaceState: {
  isSuccess: boolean;
  data?: { pages: Array<{ namespaces: Array<{ namespaceId: string }> }> };
} = { isSuccess: true, data: { pages: [{ namespaces: [{ namespaceId: "ns-1" }] }] } };

vi.mock("../api-hooks/use-list-namespaces", () => ({
  useListNamespaces: () => namespaceState,
}));

// Home overview card (F01) reads GET /system-health through the API client.
// The client must be referentially stable, like the real memoized provider.
const mockGet = vi.fn();
const mockClient = { get: mockGet };

vi.mock("@components", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@components")>();
  return {
    ...actual,
    useApiClient: () => mockClient,
  };
});

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => navigate };
});

vi.mock("../auth", () => ({
  useUser: () => ({
    user: {
      userid: "u1",
      name: "Ada Lovelace",
      email: "ada@example.com",
      groups: [],
    },
    logout: vi.fn(),
  }),
}));

const renderHome = () =>
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

describe("HomePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    namespaceState.data = { pages: [{ namespaces: [{ namespaceId: "ns-1" }] }] };
    mockGet.mockResolvedValue({
      status: "ok",
      pointer: { semver: "0.7.0", status: "published" },
      namedGraphs: 27,
      components: [{ status: "ok" }, { status: "ok" }],
    });
  });

  it("renders the Context Ontology Accelerator hero and tagline", () => {
    renderHome();
    expect(
      screen.getByText("Context Ontology Accelerator"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("The governed context layer for enterprise AI."),
    ).toBeInTheDocument();
  });

  it("greets the signed-in user by name", () => {
    renderHome();
    expect(screen.getByText(/Welcome, Ada Lovelace\./)).toBeInTheDocument();
  });

  it("renders the Scan / Ontology / Serve overview", () => {
    renderHome();
    expect(screen.getByText("Scan")).toBeInTheDocument();
    expect(screen.getByText("Ontology")).toBeInTheDocument();
    expect(screen.getByText("Serve")).toBeInTheDocument();
  });

  it("routes to namespace creation from Get started", async () => {
    renderHome();
    await userEvent.click(screen.getByRole("button", { name: /get started/i }));
    expect(navigate).toHaveBeenCalledWith("/namespaces/create");
  });

  it("routes to the namespace list from View namespaces", async () => {
    renderHome();
    await userEvent.click(
      screen.getByRole("button", { name: /view namespaces/i }),
    );
    expect(navigate).toHaveBeenCalledWith("/namespaces");
  });

  it("hides the first-use guide once a namespace exists", () => {
    renderHome();
    expect(screen.queryByText("下一步")).not.toBeInTheDocument();
  });

  it("shows the first-use guide in an empty environment", async () => {
    namespaceState.data = { pages: [{ namespaces: [] }] };
    renderHome();
    expect(screen.getByText("下一步")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "建命名空间" }));
    expect(navigate).toHaveBeenCalledWith("/namespaces/create");
  });

  it("shows the version pointer and named-graph count (F01)", async () => {
    renderHome();
    expect(await screen.findByText("0.7.0（published）")).toBeInTheDocument();
    expect(screen.getByText("27")).toBeInTheDocument();
    expect(screen.getByText("2/2 正常")).toBeInTheDocument();
  });

  it("refetches the overview on refresh (F02)", async () => {
    renderHome();
    await screen.findByText("0.7.0（published）");
    await userEvent.click(screen.getByRole("button", { name: "刷新" }));
    expect(mockGet).toHaveBeenCalledTimes(2);
  });
});
