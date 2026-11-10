// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Graph context section showing entity relationships from the knowledge graph.
 */
import React from "react";
import {
  Box,
  Button,
  SpaceBetween,
  StatusIndicator,
} from "@cloudscape-design/components";
import type {
  GraphContextItem,
  LegacyGraphContextRelationship,
} from "@app-types";
import { useAppI18n } from "../../../i18n/LocaleProvider";
import { useApiClient } from "../../ApiClientProvider";
import {
  getEntityProvenance,
  type EntityProvenanceReport,
} from "../../../services/entities";

export interface GraphContextSectionProps {
  context: GraphContextItem;
  /** When set, each entity gets an inline Provenance lookup button. */
  namespaceId?: string;
}

interface RenderedRelationship {
  sourceUri: string;
  predicate: string;
  targetUri: string;
  targetLabel?: string;
}

const MAX_RENDERED_STATEMENTS = 20;

const graphSupportingStatements = (
  properties: Record<string, unknown> | undefined,
): string[] => {
  const raw =
    properties?.supportingStatements ?? properties?.supporting_statements;
  if (Array.isArray(raw)) {
    return raw
      .filter(
        (statement): statement is string =>
          typeof statement === "string" && statement.trim().length > 0,
      )
      .slice(0, MAX_RENDERED_STATEMENTS);
  }
  if (typeof raw !== "string" || raw.trim().length === 0) return [];

  try {
    const parsed: unknown = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed
        .filter(
          (statement): statement is string =>
            typeof statement === "string" && statement.trim().length > 0,
        )
        .slice(0, MAX_RENDERED_STATEMENTS);
    }
  } catch {
    // Restored legacy sessions may store one plain-text statement.
  }
  return [raw];
};

const legacyRelationship = (
  entityUri: string,
  relationship: LegacyGraphContextRelationship,
): RenderedRelationship | null => {
  const sourceUri =
    relationship.sourceUri ?? relationship.source_uri ?? entityUri;
  const predicate =
    relationship.predicateLabel ??
    relationship.predicate_label ??
    relationship.predicateUri ??
    relationship.predicate_uri ??
    relationship.predicate;
  const targetUri =
    relationship.targetUri ?? relationship.target_uri ?? relationship.target;
  if (!sourceUri || !predicate || !targetUri) return null;
  return {
    sourceUri,
    predicate,
    targetUri,
    targetLabel: relationship.targetLabel ?? relationship.target_label,
  };
};

/**
 * Inline provenance lookup for one entity in an answer (F93). Rendered only
 * when a namespace is known, so it never reaches for the API client in contexts
 * that only render static graph evidence.
 */
const InlineProvenance: React.FC<{ uri: string }> = ({ uri }) => {
  const { t } = useAppI18n();
  const api = useApiClient();
  const [phase, setPhase] = React.useState<
    "idle" | "loading" | "done" | "error"
  >("idle");
  const [report, setReport] = React.useState<EntityProvenanceReport | null>(
    null,
  );
  const [error, setError] = React.useState<string | null>(null);

  const load = async () => {
    setPhase("loading");
    setError(null);
    try {
      setReport(await getEntityProvenance(api, uri, 20));
      setPhase("done");
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : t("Failed to load provenance"),
      );
      setPhase("error");
    }
  };

  return (
    <div>
      <Button
        variant="inline-link"
        loading={phase === "loading"}
        onClick={() => void load()}
      >
        {t("Provenance")}
      </Button>
      {phase === "done" && report && (
        <div style={{ marginTop: "2px" }}>
          <SpaceBetween direction="horizontal" size="xs">
            <StatusIndicator type="success">
              {t("Evidenced {count}", { count: report.summary.evidenced })}
            </StatusIndicator>
            <StatusIndicator type="pending">
              {t("Inferred {count}", { count: report.summary.inferred })}
            </StatusIndicator>
            <StatusIndicator type="stopped">
              {t("None {count}", { count: report.summary.none })}
            </StatusIndicator>
            <Box variant="small" color="text-body-secondary">
              {t("of {total} fields/statements", {
                total: report.summary.total,
              })}
            </Box>
          </SpaceBetween>
          {report.empty && report.emptyReason ? (
            <Box variant="small" color="text-body-secondary">
              {report.emptyReason}
            </Box>
          ) : null}
        </div>
      )}
      {phase === "error" && error ? (
        <Box variant="small" color="text-status-error">
          {error}
        </Box>
      ) : null}
    </div>
  );
};

export const GraphContextSection: React.FC<GraphContextSectionProps> = ({
  context,
  namespaceId,
}) => {
  const { t } = useAppI18n();
  const entities = context.entities ?? [];
  const relationships: RenderedRelationship[] = [
    ...(context.relationships ?? []).map((relationship) => ({
      sourceUri: relationship.sourceUri,
      predicate: relationship.predicateLabel ?? relationship.predicateUri,
      targetUri: relationship.targetUri,
    })),
    ...entities.flatMap((entity) =>
      (entity.relationships ?? [])
        .map((relationship) => legacyRelationship(entity.uri, relationship))
        .filter(
          (relationship): relationship is RenderedRelationship =>
            relationship !== null,
        ),
    ),
  ];
  if (entities.length === 0 && relationships.length === 0) return null;

  const entityLabels = new Map(
    entities.map((entity) => [entity.uri, entity.label || entity.uri]),
  );

  return (
    <div style={{ borderTop: "1px solid #e9ebed", paddingTop: "8px" }}>
      <Box variant="span" fontSize="body-s" fontWeight="bold">
        {t("Graph context")}
      </Box>
      {entities.length > 0 && (
        <div style={{ marginTop: "4px" }}>
          {entities.map((entity) => {
            const statements = graphSupportingStatements(entity.properties);
            return (
              <React.Fragment key={entity.uri}>
                <Box variant="span" fontSize="body-s" display="block">
                  {entity.label || entity.uri}
                  {entity.type && (
                    <Box variant="span" color="text-body-secondary">
                      {" "}
                      ({entity.type})
                    </Box>
                  )}
                </Box>
                {namespaceId && entity.uri ? (
                  <InlineProvenance uri={entity.uri} />
                ) : null}
                {statements.map((statement, index) => (
                  <Box
                    key={`${entity.uri}|statement|${index}`}
                    variant="span"
                    fontSize="body-s"
                    color="text-body-secondary"
                    display="block"
                  >
                    ↳ {statement}
                  </Box>
                ))}
              </React.Fragment>
            );
          })}
        </div>
      )}
      {relationships.length > 0 && (
        <div style={{ marginTop: "4px" }}>
          {relationships.map((relationship, index) => (
            <Box
              key={`${relationship.sourceUri}|${relationship.predicate}|${relationship.targetUri}|${index}`}
              variant="span"
              fontSize="body-s"
              display="block"
            >
              {entityLabels.get(relationship.sourceUri) ??
                relationship.sourceUri}{" "}
              → {relationship.predicate} →{" "}
              {entityLabels.get(relationship.targetUri) ??
                relationship.targetLabel ??
                relationship.targetUri}
            </Box>
          ))}
        </div>
      )}
    </div>
  );
};
