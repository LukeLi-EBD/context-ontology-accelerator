// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import {
  Box,
  Button,
  Container,
  Header,
  SpaceBetween,
  StatusIndicator,
} from "@cloudscape-design/components";
import { useApiClient } from "@components/ApiClientProvider";
import { useAppI18n } from "../../i18n/LocaleProvider";
import type { AppMessage } from "../../i18n/appMessages";
import {
  checkAnswerable,
  type CheckAnswerableResponse,
  type CoverageLayer,
  type MissingGap,
} from "../../services/answerable";

const LAYER_LABEL: Record<string, AppMessage> = {
  ontology: "Ontology",
  terms: "Terms",
  metrics: "Metrics",
  facts: "Facts",
};

const STATUS_LABEL: Record<string, AppMessage> = {
  covered: "Covered",
  partial: "Partial",
  missing: "Missing",
  degraded: "Degraded",
  unavailable: "Unavailable",
  not_applicable: "Not applicable",
};

const STATUS_COLOR: Record<string, string> = {
  covered: "#037f0c",
  partial: "#b08200",
  missing: "#d13212",
  degraded: "#b08200",
  unavailable: "#687078",
  not_applicable: "#687078",
};

type IndicatorType = "success" | "error" | "warning" | "info" | "stopped";

function indicatorType(status: string): IndicatorType {
  switch (status) {
    case "covered":
      return "success";
    case "partial":
    case "degraded":
      return "warning";
    case "missing":
      return "error";
    case "unavailable":
      return "stopped";
    default:
      return "info";
  }
}

/** Percent text for a layer, or null when the layer cannot be computed. */
export function layerPercent(layer: CoverageLayer): string | null {
  if (layer.coverage === undefined || layer.coverage === null) return null;
  return `${Math.round(Math.max(0, Math.min(1, layer.coverage)) * 100)}%`;
}

function LayerBar({ layer }: { layer: CoverageLayer }) {
  const { t } = useAppI18n();
  const percent = layerPercent(layer);
  const value = percent ? Number(percent.replace("%", "")) : 0;
  return (
    <div data-testid={`answerable-layer-${layer.layer}`}>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          gap: "8px",
          marginBottom: "4px",
        }}
      >
        <span style={{ fontWeight: 600 }}>
          {t(LAYER_LABEL[layer.layer] ?? "Ontology")}
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            style={{ fontVariantNumeric: "tabular-nums", minWidth: "40px" }}
            data-testid={`answerable-layer-${layer.layer}-value`}
          >
            {percent ?? t("Unavailable")}
          </span>
          <StatusIndicator type={indicatorType(layer.status)}>
            {STATUS_LABEL[layer.status]
              ? t(STATUS_LABEL[layer.status])
              : layer.status}
          </StatusIndicator>
        </span>
      </div>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent ? value : undefined}
        aria-label={t(LAYER_LABEL[layer.layer] ?? "Ontology")}
        style={{
          height: "8px",
          borderRadius: "4px",
          background: "#e9ebed",
          overflow: "hidden",
        }}
      >
        {percent && (
          <div
            style={{
              width: `${value}%`,
              height: "100%",
              borderRadius: "4px",
              background: STATUS_COLOR[layer.status] ?? "#687078",
            }}
          />
        )}
      </div>
      {layer.missing.length > 0 && (
        <div style={{ marginTop: "4px", color: "#5f6b7a", fontSize: "12px" }}>
          {layer.missing.join("、")}
        </div>
      )}
    </div>
  );
}

function GapItem({ gap }: { gap: MissingGap }) {
  const { t } = useAppI18n();
  const heading = gap.what || gap.text || gap.code;
  const nearby = (gap.nearbyTerms ?? []).map((item) => item.label);
  const candidates = (gap.candidates ?? []).map((item) => item.label);
  return (
    <li style={{ marginBottom: "8px" }}>
      <span
        style={{
          display: "inline-block",
          marginRight: "6px",
          padding: "0 6px",
          borderRadius: "4px",
          background: "#f2f3f3",
          color: "#16191f",
          fontSize: "12px",
        }}
      >
        {t(LAYER_LABEL[gap.layer] ?? "Ontology")}
      </span>
      <span>{heading}</span>
      {gap.text && gap.what && !gap.what.includes(gap.text) && (
        <span style={{ color: "#5f6b7a" }}>（{gap.text}）</span>
      )}
      {gap.howToFix && (
        <div style={{ color: "#5f6b7a", fontSize: "13px" }}>
          {t("Fix")}: {gap.howToFix}
        </div>
      )}
      {nearby.length > 0 && (
        <div style={{ color: "#5f6b7a", fontSize: "13px" }}>
          {t("Nearby terms")}: {nearby.join("、")}
        </div>
      )}
      {candidates.length > 0 && (
        <div style={{ color: "#5f6b7a", fontSize: "13px" }}>
          {t("Candidates")}: {candidates.join("、")}
        </div>
      )}
    </li>
  );
}

export interface AnswerableCoverageProps {
  namespaceId: string;
  /** Question to pre-check, normally the current playground input. */
  query: string;
}

/**
 * F76/F79: four-layer coverage bars plus the gap list with fixes, rendered in
 * the playground above the chat. The check is explicit (button), so typing a
 * question does not fire a request on every keystroke.
 */
export const AnswerableCoverage: React.FC<AnswerableCoverageProps> = ({
  namespaceId,
  query,
}) => {
  const { t } = useAppI18n();
  const client = useApiClient();
  const [result, setResult] = useState<CheckAnswerableResponse | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const canCheck = Boolean(namespaceId && query.trim()) && !loading;

  const runCheck = async () => {
    if (!canCheck) return;
    setLoading(true);
    setError(undefined);
    try {
      setResult(await checkAnswerable(client, namespaceId, query.trim()));
    } catch (err) {
      setResult(undefined);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description={t(
            "Checks the ontology, terms, metrics and facts layers for the current question.",
          )}
          actions={
            <Button
              variant="normal"
              onClick={runCheck}
              loading={loading}
              disabled={!namespaceId || !query.trim()}
            >
              {t("Check coverage")}
            </Button>
          }
        >
          {t("Answer coverage")}
        </Header>
      }
    >
      {!namespaceId && (
        <Box color="text-status-inactive">{t("No namespace selected.")}</Box>
      )}
      {namespaceId && !query.trim() && !result && (
        <Box color="text-body-secondary">
          {t("Enter a question to check coverage.")}
        </Box>
      )}
      {error && (
        <Box color="text-status-error">
          {t("Coverage check failed")}: {error}
        </Box>
      )}
      {result && (
        <SpaceBetween size="m">
          <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
            <StatusIndicator type={result.answerable ? "success" : "warning"}>
              {result.answerable ? t("Answerable") : t("Not answerable")}
            </StatusIndicator>
            <span style={{ color: "#5f6b7a" }}>
              {t("Layer coverage")}: {Math.round(result.coverage * 100)}% /{" "}
              {t("threshold")} {Math.round(result.threshold * 100)}%
            </span>
            {result.degraded && (
              <StatusIndicator type="warning">{t("Degraded")}</StatusIndicator>
            )}
          </div>
          {result.hint && <Box color="text-body-secondary">{result.hint}</Box>}
          <div
            style={{
              display: "grid",
              gap: "14px",
            }}
            data-testid="answerable-layers"
          >
            {result.layers.map((layer) => (
              <LayerBar key={layer.layer} layer={layer} />
            ))}
          </div>
          <div>
            <Box variant="h3">{t("Gaps and fixes")}</Box>
            {result.missing.length === 0 ? (
              <StatusIndicator type="success">
                {t("No gaps found.")}
              </StatusIndicator>
            ) : (
              <ul style={{ margin: "8px 0 0", paddingLeft: "20px" }}>
                {result.missing.map((gap, index) => (
                  <GapItem
                    key={`${gap.layer}-${gap.code}-${gap.metricId ?? gap.text ?? index}`}
                    gap={gap}
                  />
                ))}
              </ul>
            )}
          </div>
        </SpaceBetween>
      )}
    </Container>
  );
};
