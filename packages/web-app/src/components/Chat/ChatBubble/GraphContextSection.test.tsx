// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GraphContextSection } from "./GraphContextSection";

const getEntityProvenance = vi.fn();

vi.mock("../../ApiClientProvider", () => ({
  useApiClient: () => ({ get: vi.fn() }),
}));

vi.mock("../../../services/entities", () => ({
  getEntityProvenance: (...args: unknown[]) => getEntityProvenance(...args),
}));

describe("GraphContextSection", () => {
  it("renders canonical graph-only supporting statements", () => {
    render(
      <GraphContextSection
        context={{
          entities: [
            {
              uri: "urn:acme",
              label: "Acme",
              type: "Company",
              properties: {
                supportingStatements: JSON.stringify([
                  "Acme acquired Example Corp.",
                  "Acme operates in retail.",
                ]),
              },
            },
          ],
        }}
      />,
    );

    expect(
      screen.getByText(/Acme acquired Example Corp\./),
    ).toBeInTheDocument();
    expect(screen.getByText(/Acme operates in retail\./)).toBeInTheDocument();
  });

  it("handles legacy array and plain-text supporting statements safely", () => {
    const { rerender } = render(
      <GraphContextSection
        context={{
          entities: [
            {
              uri: "urn:legacy",
              label: "Legacy entity",
              properties: {
                supporting_statements: ["Legacy graph statement.", 42, null],
              },
            },
          ],
        }}
      />,
    );

    expect(screen.getByText(/Legacy graph statement\./)).toBeInTheDocument();
    expect(screen.queryByText("42")).not.toBeInTheDocument();

    rerender(
      <GraphContextSection
        context={{
          entities: [
            {
              uri: "urn:plain",
              label: "Plain entity",
              properties: {
                supportingStatements: "One restored plain-text statement.",
              },
            },
          ],
        }}
      />,
    );

    expect(
      screen.getByText(/One restored plain-text statement\./),
    ).toBeInTheDocument();
  });

  it("looks up provenance inline and shows the three-state summary (F93)", async () => {
    getEntityProvenance.mockResolvedValue({
      summary: { evidenced: 2, inferred: 1, none: 3, total: 6 },
      empty: false,
      emptyReason: null,
    });

    render(
      <GraphContextSection
        namespaceId="ns-1"
        context={{
          entities: [{ uri: "urn:acme", label: "Acme" }],
        }}
      />,
    );

    await userEvent.click(screen.getByText("Provenance"));

    await waitFor(() =>
      expect(screen.getByText("Evidenced 2")).toBeInTheDocument(),
    );
    expect(screen.getByText("Inferred 1")).toBeInTheDocument();
    expect(screen.getByText("None 3")).toBeInTheDocument();
    expect(getEntityProvenance).toHaveBeenCalledWith(
      expect.anything(),
      "urn:acme",
      20,
    );
  });
});
