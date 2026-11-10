// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "../../../i18n/LocaleProvider";
import { SamplePrompts } from "./SamplePrompts";

function renderPrompts(
  props: Partial<React.ComponentProps<typeof SamplePrompts>> = {},
) {
  window.localStorage.setItem("scl.locale", "en");
  const onSelect = vi.fn();
  render(
    <LocaleProvider>
      <SamplePrompts
        questions={[]}
        onSelect={onSelect}
        {...props}
      />
    </LocaleProvider>,
  );
  return { onSelect };
}

describe("SamplePrompts", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("tells the user the namespace has no published questions on a 404", () => {
    renderPrompts({ status: "missing" });
    expect(
      screen.getByText("No sample prompts are published for this namespace."),
    ).toBeInTheDocument();
  });

  it("distinguishes an unreadable file from an absent one", () => {
    renderPrompts({ status: "error" });
    expect(screen.getByText("Could not load sample prompts.")).toBeInTheDocument();
  });

  it("keeps the generic prompt when the file exists but is empty", () => {
    renderPrompts({ status: "ready" });
    expect(
      screen.getByText("Ask a question against the governed surface..."),
    ).toBeInTheDocument();
  });

  it("sends the full question when a chip is clicked", () => {
    const { onSelect } = renderPrompts({
      status: "ready",
      questions: [{ label: "Agreement", question: "Agreement 有哪些形态？" }],
    });
    fireEvent.click(screen.getByRole("button", { name: "Agreement 有哪些形态？" }));
    expect(onSelect).toHaveBeenCalledWith("Agreement 有哪些形态？");
  });

  it("renders nothing while the questions file is still loading", () => {
    renderPrompts({ status: "loading" });
    expect(
      screen.queryByText("Ask a question against the governed surface..."),
    ).toBeNull();
  });
});
