// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import { useNamespace } from "@api-hooks/use-namespace";
import { useGetIngestionRun } from "@api-hooks";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import KeyValuePairs from "@cloudscape-design/components/key-value-pairs";
import Link from "@cloudscape-design/components/link";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Spinner from "@cloudscape-design/components/spinner";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import type {
  IngestionRunItem,
  IngestionRunStatus,
} from "@coa/control-plane-client";
import { formatTimestamp } from "@utils/helpers";
import { useAppI18n } from "../i18n/LocaleProvider";
import type { AppMessage } from "../i18n/appMessages";

const RUN_STATUS_META: Record<
  IngestionRunStatus,
  {
    type: "in-progress" | "success" | "warning" | "error";
    label: AppMessage;
  }
> = {
  RUNNING: { type: "in-progress", label: "Running" },
  COMPLETED: { type: "success", label: "Completed" },
  INTERRUPTED: { type: "warning", label: "Interrupted" },
  STALE: { type: "error", label: "Stale" },
};

/**
 * F17 read-only detail: one import batch, its latest invocation, and the
 * per-file rows. Every field the API does not return renders as "—"; nothing
 * here invents a default.
 */
export default function IngestionRunDetailPage() {
  const { namespaceId = "", runId = "" } = useParams();
  const navigate = useNavigate();
  const { t } = useAppI18n();
  const { name } = useNamespace(namespaceId);
  const runQuery = useGetIngestionRun(namespaceId, runId);

  const run = runQuery.data?.run;
  const attempt = run?.lastRun;
  const counters = attempt?.counters;
  const items = run?.items ?? [];
  const statusMeta = run?.status ? RUN_STATUS_META[run.status] : undefined;

  useBreadcrumbTrail([
    { text: name, href: `/namespaces/${namespaceId}`, namespaceId },
    {
      text: t("Documents"),
      href: `/namespaces/${namespaceId}/documents`,
      namespaceId,
    },
    { text: run?.root || runId },
  ]);

  return (
    <SpaceBetween size="l">
      {runQuery.isError ? (
        <Alert type="error" header={t("Failed to load run")}>
          {runQuery.error.message}
        </Alert>
      ) : null}

      <Container
        header={
          <Header
            variant="h2"
            description={
              <SpaceBetween direction="horizontal" size="xs">
                {statusMeta ? (
                  <StatusIndicator type={statusMeta.type}>
                    {t(statusMeta.label)}
                  </StatusIndicator>
                ) : (
                  <Box color="text-body-secondary">—</Box>
                )}
                <Box variant="small" color="text-body-secondary">
                  {t("Run ID")}: {run?.runId ?? runId}
                </Box>
              </SpaceBetween>
            }
            actions={
              <Button
                iconName="refresh"
                ariaLabel={t("Refresh")}
                loading={runQuery.isFetching}
                onClick={() => void runQuery.refetch()}
              />
            }
          >
            {run?.root || runId}
          </Header>
        }
      >
        {runQuery.isLoading ? (
          <Box textAlign="center" padding="l">
            <Spinner size="large" />
          </Box>
        ) : (
          <KeyValuePairs
            columns={3}
            items={[
              {
                label: t("Status"),
                value: statusMeta ? t(statusMeta.label) : "—",
              },
              {
                label: t("Exit code"),
                value: attempt?.exitCode ?? "—",
              },
              {
                label: t("Error code"),
                value: attempt?.errorCode ?? "—",
              },
              {
                label: t("Started"),
                value: formatTimestamp(attempt?.startedAt),
              },
              {
                label: t("Finished"),
                value: formatTimestamp(attempt?.finishedAt ?? run?.finishedAt),
              },
              {
                label: t("Total"),
                value: counters?.total ?? "—",
              },
              {
                label: t("Indexed"),
                value: counters?.indexed ?? "—",
              },
              {
                label: t("Failed this run"),
                value: counters?.failedThisRun ?? "—",
              },
              {
                label: t("Updated"),
                value: formatTimestamp(run?.updatedAt),
              },
            ]}
          />
        )}
      </Container>

      <Table<IngestionRunItem>
        variant="embedded"
        stripedRows
        loading={runQuery.isLoading}
        loadingText={t("Loading run")}
        items={items}
        header={
          <Header variant="h3" counter={`(${items.length})`}>
            {t("Items")}
          </Header>
        }
        columnDefinitions={[
          {
            id: "relPath",
            header: t("File"),
            cell: (item) => item.relPath || "—",
            minWidth: 240,
          },
          {
            id: "status",
            header: t("Status"),
            cell: (item) => item.status || "—",
            width: 120,
          },
          {
            id: "attempts",
            header: t("Attempts"),
            cell: (item) => item.attempts ?? "—",
            width: 110,
          },
          {
            id: "failureCode",
            header: t("Failure code"),
            cell: (item) => item.failureCode || "—",
            minWidth: 160,
          },
          {
            id: "failureMessage",
            header: t("Failure message"),
            cell: (item) => item.failureMessage || "—",
            minWidth: 220,
          },
          {
            id: "updatedAt",
            header: t("Updated"),
            cell: (item) => formatTimestamp(item.updatedAt),
            minWidth: 170,
          },
        ]}
        empty={
          <Box textAlign="center" color="inherit">
            <b>{t("No items")}</b>
          </Box>
        }
      />

      <Box variant="p" color="text-body-secondary">
        <Link
          href={`/namespaces/${namespaceId}/documents`}
          onFollow={(event) => {
            event.preventDefault();
            navigate(`/namespaces/${namespaceId}/documents`);
          }}
        >
          {t("Back to documents")}
        </Link>
      </Box>
    </SpaceBetween>
  );
}
