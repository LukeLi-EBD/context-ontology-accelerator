// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Box, Button, SpaceBetween } from "@cloudscape-design/components";
import type {
  ExampleQuestion,
  ExampleQuestionsStatus,
} from "@api-hooks/use-example-questions";
import { useAppI18n } from "../../../i18n/LocaleProvider";

export interface SamplePromptsProps {
  questions: ExampleQuestion[];
  /**
   * Why the list may be empty. `missing` (no questions file for this namespace)
   * and `error` (file unreadable) each get their own hint so an absent file is
   * not silently rendered as "nothing to show".
   */
  status?: ExampleQuestionsStatus;
  onSelect: (question: string) => void;
  disabled?: boolean;
}

/**
 * Empty-state sample prompts for the playground. Renders one clickable chip per
 * example question; clicking sends the full question to the serve layer. Shown
 * only when the chat is empty and questions were published for the namespace.
 */
export const SamplePrompts: React.FC<SamplePromptsProps> = ({
  questions,
  status = "ready",
  onSelect,
  disabled = false,
}) => {
  const { t } = useAppI18n();

  if (status === "loading") {
    return null;
  }

  if (questions.length === 0) {
    const hint =
      status === "missing"
        ? t("No sample prompts are published for this namespace.")
        : status === "error"
          ? t("Could not load sample prompts.")
          : t("Ask a question against the governed surface...");
    return (
      <Box textAlign="center" color="text-body-secondary" padding="xl">
        {hint}
      </Box>
    );
  }

  return (
    <Box textAlign="center" padding="xl">
      <SpaceBetween size="m" alignItems="center">
        <Box color="text-body-secondary">
          {t("Try one of the sample prompts below, or type your own question.")}
        </Box>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "8px",
            justifyContent: "center",
            maxWidth: "760px",
          }}
        >
          {questions.map((q, i) => (
            <Button
              key={`${q.question}-${i}`}
              variant="normal"
              disabled={disabled}
              onClick={() => onSelect(q.question)}
              ariaLabel={q.question}
            >
              {q.label ?? q.question}
            </Button>
          ))}
        </div>
      </SpaceBetween>
    </Box>
  );
};
