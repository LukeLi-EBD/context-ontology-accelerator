// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, fireEvent, waitFor, cleanup, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { StatementBrowserView } from "./StatementBrowserView";
import type { ApiClient } from "@components/ApiClientProvider";
import type { GraphStatement } from "../../../services/ontology-engine";

const listStatements = vi.fn();
vi.mock("../../../services/ontology-engine", () => ({
  listStatements: (...args: unknown[]) => listStatements(...args),
}));

const navigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual =
    await vi.importActual<typeof import("react-router-dom")>(
      "react-router-dom",
    );
  return { ...actual, useNavigate: () => navigate };
});

function statement(overrides: Partial<GraphStatement> = {}): GraphStatement {
  return {
    graph: "https://coa.local/graph/ns/g1",
    subject: "https://ex.org/loan#L1",
    predicate: "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    object: "https://ex.org/loan#Loan",
    ...overrides,
  };
}

// Minimal stub client — the component only forwards it to the (mocked) service
// call, so nothing is ever invoked on it.
const apiClient: ApiClient = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
};

function renderView(props: { namespace?: string } = { namespace: "ns" }) {
  // The view navigates via useNavigate only; MemoryRouter provides the context.
  const result = render(
    <MemoryRouter>
      <StatementBrowserView
        apiClient={apiClient}
        namespace={props.namespace}
      />
    </MemoryRouter>,
  );
  return within(result.container);
}

describe("StatementBrowserView", () => {
  beforeEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("lists the statement page with graph, subject, predicate and object", async () => {
    listStatements.mockResolvedValue({
      statements: [statement(), statement({ subject: "https://ex.org/loan#L2" })],
      truncated: false,
    });

    const view = renderView();

    await view.findByText("https://ex.org/loan#L1");
    expect(view.getByText("https://ex.org/loan#L2")).toBeInTheDocument();
    expect(
      view.getAllByText("https://coa.local/graph/ns/g1"),
    ).toHaveLength(2);
    expect(
      view.getAllByText("https://ex.org/loan#Loan").length,
    ).toBeGreaterThan(0);
    expect(listStatements).toHaveBeenCalledWith(apiClient, "ns", {
      subject: undefined,
      predicate: undefined,
      object: undefined,
      graph: undefined,
      limit: 20,
      offset: 0,
    });
  });

  it("sends every filter to the service and restarts paging at the first page", async () => {
    listStatements.mockResolvedValue({ statements: [], truncated: false });
    const view = renderView();
    await waitFor(() => expect(listStatements).toHaveBeenCalled());

    fireEvent.change(view.getByLabelText("Subject"), {
      target: { value: " https://ex.org/loan#L1 " },
    });
    fireEvent.change(view.getByLabelText("Predicate"), {
      target: { value: "https://ex.org/p" },
    });
    fireEvent.change(view.getByLabelText("Object"), {
      target: { value: "Loan" },
    });
    fireEvent.change(view.getByLabelText("Named graph"), {
      target: { value: "https://coa.local/graph/ns/g1" },
    });
    fireEvent.click(view.getByText("Search"));

    await waitFor(() =>
      expect(listStatements).toHaveBeenLastCalledWith(apiClient, "ns", {
        // Whitespace is trimmed before the request.
        subject: "https://ex.org/loan#L1",
        predicate: "https://ex.org/p",
        object: "Loan",
        graph: "https://coa.local/graph/ns/g1",
        limit: 20,
        offset: 0,
      }),
    );
  });

  it("clears the filters and refetches the unfiltered first page", async () => {
    listStatements.mockResolvedValue({ statements: [], truncated: false });
    const view = renderView();
    await waitFor(() => expect(listStatements).toHaveBeenCalled());

    fireEvent.change(view.getByLabelText("Subject"), {
      target: { value: "https://ex.org/loan#L1" },
    });
    fireEvent.click(view.getByText("Search"));
    await waitFor(() =>
      expect(listStatements).toHaveBeenLastCalledWith(
        apiClient,
        "ns",
        expect.objectContaining({ subject: "https://ex.org/loan#L1" }),
      ),
    );

    fireEvent.click(view.getByText("Clear"));

    await waitFor(() =>
      expect(listStatements).toHaveBeenLastCalledWith(apiClient, "ns", {
        subject: undefined,
        predicate: undefined,
        object: undefined,
        graph: undefined,
        limit: 20,
        offset: 0,
      }),
    );
  });

  it("pages forward only while more statements remain, and back to the start", async () => {
    listStatements
      .mockResolvedValueOnce({ statements: [statement()], truncated: true })
      .mockResolvedValue({ statements: [statement()], truncated: false });
    const view = renderView();
    await view.findByText("https://ex.org/loan#L1");

    const previous = view.getByText("Previous").closest("button");
    expect(previous).toBeDisabled();

    fireEvent.click(view.getByText("Next"));
    await waitFor(() =>
      expect(listStatements).toHaveBeenLastCalledWith(
        apiClient,
        "ns",
        expect.objectContaining({ offset: 20 }),
      ),
    );

    // The second page is the last one, so Next is off and Previous returns to 0.
    await waitFor(() =>
      expect(view.getByText("Next").closest("button")).toBeDisabled(),
    );
    fireEvent.click(view.getByText("Previous"));
    await waitFor(() =>
      expect(listStatements).toHaveBeenLastCalledWith(
        apiClient,
        "ns",
        expect.objectContaining({ offset: 0 }),
      ),
    );
  });

  it("links a subject to its entity page and navigates without a full reload", async () => {
    listStatements.mockResolvedValue({ statements: [statement()], truncated: false });
    const view = renderView();
    const link = await view.findByRole("link", {
      name: "https://ex.org/loan#L1",
    });

    expect(link).toHaveAttribute(
      "href",
      `/namespaces/ns/ontology/entities/${encodeURIComponent(
        "https://ex.org/loan#L1",
      )}`,
    );

    fireEvent.click(link);
    expect(navigate).toHaveBeenCalledWith(
      `/namespaces/ns/ontology/entities/${encodeURIComponent(
        "https://ex.org/loan#L1",
      )}`,
    );
  });

  it("surfaces a fetch failure in a dismissible warning Alert", async () => {
    listStatements.mockRejectedValue(new Error("graph unavailable"));
    const view = renderView();
    await view.findByText("Could not load statements");
    expect(view.getByText("graph unavailable")).toBeInTheDocument();
  });

  it("does not fetch at all until a namespace is known", () => {
    const view = renderView({});
    expect(listStatements).not.toHaveBeenCalled();
    expect(view.queryByText("Could not load statements")).toBeNull();
  });
});
