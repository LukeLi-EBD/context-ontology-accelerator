// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import { useNamespace } from "@api-hooks/use-namespace";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Box from "@cloudscape-design/components/box";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Table from "@cloudscape-design/components/table";
import Badge from "@cloudscape-design/components/badge";
import Alert from "@cloudscape-design/components/alert";
import Modal from "@cloudscape-design/components/modal";
import Input from "@cloudscape-design/components/input";
import FormField from "@cloudscape-design/components/form-field";
import Spinner from "@cloudscape-design/components/spinner";
import Link from "@cloudscape-design/components/link";
import {
  useGetMetric,
  useDeleteMetric,
  useGetMetricCard,
  useGetMetricFamily,
  useOntologyClasses,
} from "../api-hooks/use-metrics";
import type { MetricFieldBinding } from "../api-hooks/use-metrics";
import { useSourceNameById } from "../api-hooks/use-source-name-by-id";
import { useAppI18n } from "../i18n/LocaleProvider";

export const MetricDetail: React.FC = () => {
  const { t } = useAppI18n();
  const navigate = useNavigate();
  const { namespaceId, metricName } = useParams<{
    namespaceId: string;
    metricName: string;
  }>();

  const { data, isLoading, error } = useGetMetric(
    namespaceId ?? "",
    metricName ?? "",
  );
  const deleteMutation = useDeleteMetric(namespaceId ?? "");

  const { name: nsName } = useNamespace(namespaceId);
  useBreadcrumbTrail([
    { text: nsName, href: `/namespaces/${namespaceId}`, namespaceId },
    { text: t("Ontology") },
    {
      text: t("Metrics"),
      href: `/namespaces/${namespaceId}/metrics`,
      namespaceId,
    },
    { text: metricName ?? "" },
  ]);

  // Resolve dataSourceId -> human-readable source name
  const sourceNameById = useSourceNameById(namespaceId ?? "");

  // F54/F56: platform card (bindings + external status) and F55: the family
  // this metric belongs to, if it is a variant (or the family index itself).
  const { data: card } = useGetMetricCard(metricName ?? "");
  const { data: familyData } = useGetMetricFamily(
    namespaceId ?? "",
    card?.familyId ?? undefined,
  );
  const family = familyData?.family;
  const { data: classData } = useOntologyClasses(namespaceId ?? "");

  // F54 deliberately keeps this a weak association: metric_field_binding has no
  // entity IRI, only a column name, so there is no real column -> class mapping
  // to follow. We match the bound column / grain against the ontology class
  // local name instead. When more than one class shares that local name the
  // match is ambiguous and we show no link at all: a wrong entity page is worse
  // than no entity page.
  const classesByLocalName = useMemo(() => {
    const map = new Map<string, Array<{ iri: string; label?: string }>>();
    for (const cls of classData?.classes ?? []) {
      const local = cls.iri.split(/[#/]/).filter(Boolean).pop() ?? "";
      if (!local) continue;
      const key = local.toLowerCase();
      map.set(key, [...(map.get(key) ?? []), cls]);
    }
    return map;
  }, [classData?.classes]);

  const uniqueClassFor = (name?: string) => {
    if (!name) return undefined;
    const matches = classesByLocalName.get(name.toLowerCase()) ?? [];
    return matches.length === 1 ? matches[0] : undefined;
  };

  const entityHref = (iri: string) =>
    `/namespaces/${namespaceId}/ontology/entities/${encodeURIComponent(iri)}`;
  const openEntity = (iri: string) => (event: CustomEvent) => {
    event.preventDefault();
    navigate(entityHref(iri));
  };
  const classForColumn = (column?: string) => uniqueClassFor(column);
  const grainClass = uniqueClassFor(card?.grain ?? undefined);
  const externalBadgeColor = (status?: string) => {
    switch (status) {
      case "external_candidate":
        return "green" as const;
      case "blocked":
        return "red" as const;
      case "unpublishable":
        return "grey" as const;
      default:
        return "blue" as const;
    }
  };

  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");

  const metric = data?.metric;

  const handleDelete = () => {
    if (!metricName) return;
    deleteMutation.mutate(metricName, {
      onSuccess: () => {
        navigate(`/namespaces/${namespaceId}/metrics`, {
          state: {
            flash: {
              type: "success",
              content: t("Metric “{name}” deleted.", { name: metricName }),
            },
          },
        });
      },
    });
  };

  if (isLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert type="error">
        {t("Failed to load metric: {message}", { message: error.message })}
      </Alert>
    );
  }

  if (!metric) {
    return <Alert type="warning">{t("Metric not found.")}</Alert>;
  }

  // Three-state provenance: absent is "unknown", and must stay visually distinct
  // from an explicit false ("No").
  const provenanceText = (value: string | boolean | undefined) => {
    if (value === undefined) return t("Unknown");
    if (typeof value === "boolean") return value ? t("Yes") : t("No");
    return value;
  };

  return (
    <SpaceBetween size="l">
      {/* Overview */}
      <Container
        header={
          <Header
            variant="h1"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  onClick={() =>
                    navigate(
                      `/namespaces/${namespaceId}/metrics/${metricName}/edit`,
                    )
                  }
                >
                  {t("Edit")}
                </Button>
                <Button
                  variant="normal"
                  onClick={() => setDeleteModalVisible(true)}
                >
                  {t("Delete")}
                </Button>
              </SpaceBetween>
            }
          >
            {metric.label || metric.name}
          </Header>
        }
      >
        {/* F56: binding + external status, straight off the platform card. */}
        {card && (
          <div style={{ marginBottom: "16px" }}>
            <SpaceBetween direction="horizontal" size="xs">
              <Badge color={card.bindingStatus === "bound" ? "green" : "grey"}>
                {card.bindingStatus === "bound" ? t("Bound") : t("Unbound")}
              </Badge>
              {card.externalStatus && (
                <Badge color={externalBadgeColor(card.externalStatus)}>
                  {card.externalLabel ?? card.externalStatus}
                </Badge>
              )}
              {card.externalReason && (
                <Box color="text-body-secondary" variant="small">
                  {card.externalReason}
                </Box>
              )}
            </SpaceBetween>
          </div>
        )}
        <ColumnLayout columns={3} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">{t("Name")}</Box>
            <div>{metric.name}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Display label")}</Box>
            <div>{metric.label || "—"}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Description")}</Box>
            <div>{metric.description}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Unit")}</Box>
            <div>{metric.unit ?? "—"}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Return type")}</Box>
            <div>{metric.returnType ?? "—"}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Defined by")}</Box>
            <div>{metric.definedBy ?? "—"}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Effective from")}</Box>
            <div>{metric.effectiveFrom ?? "—"}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Default time grain")}</Box>
            <div>{metric.defaultTimeGrain ?? "—"}</div>
          </div>
        </ColumnLayout>
      </Container>

      {/* F55: family view — switch between variants that share an index. */}
      {family && family.variants.length > 0 && (
        <Container
          header={
            <Header
              variant="h2"
              description={t(
                "Variants answer the same business question with a different formula, window or denominator.",
              )}
            >
              {t("Family variants")}
            </Header>
          }
        >
          <SpaceBetween size="m">
            <SpaceBetween direction="horizontal" size="xs">
              {family.variants.map((variant) => (
                <Button
                  key={variant.metricId}
                  variant={
                    variant.metricId === metricName ? "primary" : "normal"
                  }
                  onClick={() =>
                    navigate(
                      `/namespaces/${namespaceId}/metrics/${variant.metricId}`,
                    )
                  }
                >
                  {variant.grain
                    ? `${variant.metricId} · ${variant.grain}`
                    : variant.metricId}
                </Button>
              ))}
            </SpaceBetween>
            {family.diffs.length > 0 && (
              <Table
                variant="embedded"
                items={family.diffs}
                columnDefinitions={[
                  {
                    id: "field",
                    header: t("Field"),
                    cell: (diff) => diff.label ?? diff.field,
                    width: 180,
                  },
                  ...family.variants.map((variant) => ({
                    id: variant.metricId,
                    header: variant.grain ?? variant.metricId,
                    cell: (diff: (typeof family.diffs)[number]) =>
                      diff.values[variant.metricId] ?? "—",
                  })),
                  {
                    id: "different",
                    header: t("Differs"),
                    cell: (diff) =>
                      diff.different ? (
                        <Badge color="red">{t("Yes")}</Badge>
                      ) : (
                        <Box color="text-status-inactive">{t("No")}</Box>
                      ),
                    width: 90,
                  },
                ]}
              />
            )}
          </SpaceBetween>
        </Container>
      )}

      {/* Governance — COA-private provenance from the bundle's custom_extensions */}
      <Container header={<Header variant="h2">{t("Governance")}</Header>}>
        <ColumnLayout columns={3} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">{t("Domain")}</Box>
            <div>{provenanceText(metric.domain)}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Evidence basis")}</Box>
            <div>{provenanceText(metric.evidenceBasis)}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Publishable")}</Box>
            <div>{provenanceText(metric.publishable)}</div>
          </div>
        </ColumnLayout>
      </Container>

      {/* Source */}
      <Container header={<Header variant="h2">{t("Source")}</Header>}>
        <ColumnLayout columns={3} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">{t("Data source")}</Box>
            <div>
              {metric.dataSourceId
                ? (sourceNameById.get(metric.dataSourceId) ??
                  metric.dataSourceId)
                : "—"}
            </div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Source table")}</Box>
            <div>{metric.sourceTable}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Time grain")}</Box>
            <div>{metric.defaultTimeGrain ?? "—"}</div>
          </div>
        </ColumnLayout>
      </Container>

      {/* F54: class + field bindings, with an entity-page hop per binding. */}
      <Container
        header={
          <Header
            variant="h2"
            description={t(
              "Field bindings come from the metric's physical binding. Bindings carry a column name, not an IRI, so the entity-page link resolves that column against an ontology class of the same name.",
            )}
          >
            {t("Class and field bindings")}
          </Header>
        }
      >
        <SpaceBetween size="m">
          <div>
            <Box variant="awsui-key-label">{t("Class binding")}</Box>
            {grainClass ? (
              <SpaceBetween direction="horizontal" size="xs">
                <Link
                  href={entityHref(grainClass.iri)}
                  onFollow={openEntity(grainClass.iri)}
                >
                  {grainClass.label || grainClass.iri}
                </Link>
                <Box color="text-body-secondary" variant="small">
                  {card?.grain}
                </Box>
              </SpaceBetween>
            ) : (
              <Box color="text-status-inactive">
                {t(
                  "No ontology class matches this metric's grain ({grain}).",
                  { grain: card?.grain ?? "—" },
                )}
              </Box>
            )}
          </div>
          <div>
            <Box variant="awsui-key-label">{t("Field bindings")}</Box>
            {card?.fieldBindings && card.fieldBindings.length > 0 ? (
              <Table
                variant="embedded"
                items={card.fieldBindings}
                columnDefinitions={[
                  {
                    id: "role",
                    header: t("Role"),
                    cell: (binding: MetricFieldBinding) =>
                      binding.role ? <Badge>{binding.role}</Badge> : "—",
                    width: 120,
                  },
                  {
                    id: "factTable",
                    header: t("Fact table"),
                    cell: (binding: MetricFieldBinding) =>
                      binding.factTable ?? "—",
                  },
                  {
                    id: "entityColumn",
                    header: t("Entity column"),
                    cell: (binding: MetricFieldBinding) =>
                      binding.entityColumn ?? "—",
                  },
                  {
                    id: "valueExpr",
                    header: t("Value expression"),
                    cell: (binding: MetricFieldBinding) =>
                      binding.valueExpr ?? "—",
                  },
                  {
                    id: "agg",
                    header: t("Aggregate"),
                    cell: (binding: MetricFieldBinding) => binding.agg ?? "—",
                    width: 110,
                  },
                  {
                    id: "filter",
                    header: t("Filter"),
                    cell: (binding: MetricFieldBinding) =>
                      binding.filterSql ?? "—",
                  },
                  {
                    id: "window",
                    header: t("Window"),
                    cell: (binding: MetricFieldBinding) =>
                      binding.windowColumn
                        ? `${binding.windowColumn} / ${binding.windowMode ?? "—"}`
                        : "—",
                  },
                  {
                    id: "entity",
                    header: t("Entity page"),
                    cell: (binding: MetricFieldBinding) => {
                      const cls = classForColumn(binding.entityColumn);
                      return cls ? (
                        <Link
                          href={entityHref(cls.iri)}
                          onFollow={openEntity(cls.iri)}
                        >
                          {t("Open")}
                        </Link>
                      ) : (
                        <Box color="text-status-inactive">—</Box>
                      );
                    },
                    width: 110,
                  },
                ]}
              />
            ) : (
              <Box color="text-status-inactive">
                {t("No field bindings recorded for this metric version.")}
              </Box>
            )}
          </div>
        </SpaceBetween>
      </Container>

      {/* Expressions */}
      <Container header={<Header variant="h2">{t("Expressions")}</Header>}>
        <Table
          items={metric.expression?.dialects ?? []}
          columnDefinitions={[
            {
              id: "dialect",
              header: t("Dialect"),
              cell: (item) => <Badge>{item.dialect}</Badge>,
              width: 150,
            },
            {
              id: "expression",
              header: t("SQL Expression"),
              cell: (item) => (
                <code
                  style={{
                    fontFamily: "monospace",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {item.expression}
                </code>
              ),
            },
          ]}
          variant="embedded"
        />
      </Container>

      {/* AI Context */}
      {metric.aiContext && (
        <Container header={<Header variant="h2">{t("AI Context")}</Header>}>
          <SpaceBetween size="m">
            {metric.aiContext.synonyms &&
              metric.aiContext.synonyms.length > 0 && (
                <div>
                  <Box variant="awsui-key-label">{t("Synonyms")}</Box>
                  <SpaceBetween direction="horizontal" size="xs">
                    {metric.aiContext.synonyms.map((s) => (
                      <Badge key={s} color="blue">
                        {s}
                      </Badge>
                    ))}
                  </SpaceBetween>
                </div>
              )}
            {metric.aiContext.instructions && (
              <div>
                <Box variant="awsui-key-label">{t("Instructions")}</Box>
                <div>{metric.aiContext.instructions}</div>
              </div>
            )}
            {metric.aiContext.examples &&
              metric.aiContext.examples.length > 0 && (
                <div>
                  <Box variant="awsui-key-label">{t("Examples")}</Box>
                  <ul>
                    {metric.aiContext.examples.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </div>
              )}
          </SpaceBetween>
        </Container>
      )}

      {/* Ontology Links */}
      <Container header={<Header variant="h2">{t("Ontology Links")}</Header>}>
        {metric.ontologyConcepts && metric.ontologyConcepts.length > 0 ? (
          <SpaceBetween direction="horizontal" size="xs">
            {metric.ontologyConcepts.map((c) => (
              <Link key={c} href={entityHref(c)} onFollow={openEntity(c)}>
                {c}
              </Link>
            ))}
          </SpaceBetween>
        ) : (
          <Box color="text-status-inactive">
            {t(
              "No ontology classes linked. Edit this metric to associate it with classes from your ontology.",
            )}
          </Box>
        )}
      </Container>

      {/* Delete Modal */}
      <Modal
        visible={deleteModalVisible}
        onDismiss={() => {
          setDeleteModalVisible(false);
          setDeleteConfirmText("");
          deleteMutation.reset();
        }}
        header={t("Delete metric")}
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                variant="link"
                onClick={() => {
                  setDeleteModalVisible(false);
                  setDeleteConfirmText("");
                }}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="primary"
                onClick={handleDelete}
                loading={deleteMutation.isPending}
                disabled={deleteConfirmText !== metricName}
              >
                {t("Delete")}
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Box>
            {t("Permanently delete metric {name}?", {
              name: metricName ?? "",
            })}{" "}
            {t(
              "This action cannot be undone. The metric will be removed from the ontology graph and will no longer be discoverable.",
            )}
          </Box>
          <FormField
            label={t("Type “{name}” to confirm", { name: metricName ?? "" })}
          >
            <Input
              value={deleteConfirmText}
              onChange={({ detail }) => setDeleteConfirmText(detail.value)}
              placeholder={metricName}
            />
          </FormField>
          {deleteMutation.isError && (
            <Alert type="error">
              {deleteMutation.error?.message ?? t("Delete failed")}
            </Alert>
          )}
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
};
