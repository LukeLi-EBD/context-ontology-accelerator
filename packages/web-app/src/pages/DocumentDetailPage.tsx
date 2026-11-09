// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import { useNamespace } from "@api-hooks/use-namespace";
import { useListDocumentChunks, useListDocuments } from "@api-hooks";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Header from "@cloudscape-design/components/header";
import Link from "@cloudscape-design/components/link";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import type { DocumentChunk, DocumentSummary } from "@coa/control-plane-client";
import { formatTimestamp } from "@utils/helpers";
import { useAppI18n } from "../i18n/LocaleProvider";

const STATUS_LABELS: Record<
  string,
  {
    type: "pending" | "in-progress" | "success" | "error";
    label: Parameters<ReturnType<typeof useAppI18n>["t"]>[0];
  }
> = {
  UPLOADED: { type: "pending", label: "Uploaded" },
  PROCESSING: { type: "in-progress", label: "Processing" },
  INDEXED: { type: "success", label: "Indexed" },
  FAILED: { type: "error", label: "Failed" },
};

export default function DocumentDetailPage() {
  const { namespaceId = "", documentId = "" } = useParams();
  const navigate = useNavigate();
  const { t } = useAppI18n();
  const { name } = useNamespace(namespaceId);

  const documentsQuery = useListDocuments(namespaceId);
  const chunksQuery = useListDocumentChunks(namespaceId, documentId);
  const [selected, setSelected] = useState<DocumentChunk[]>([]);

  const document = useMemo<DocumentSummary | undefined>(() => {
    return documentsQuery.data?.pages
      .flatMap((page) => page.items ?? [])
      .find((item) => item.documentId === documentId);
  }, [documentsQuery.data, documentId]);

  useBreadcrumbTrail([
    { text: name, href: `/namespaces/${namespaceId}`, namespaceId },
    {
      text: t("Documents"),
      href: `/namespaces/${namespaceId}/documents`,
      namespaceId,
    },
    { text: document?.title || documentId },
  ]);

  const chunks = useMemo<DocumentChunk[]>(() => {
    return chunksQuery.data?.pages.flatMap((page) => page.items ?? []) ?? [];
  }, [chunksQuery.data]);

  const status = document?.status ?? "PROCESSING";
  const statusMeta = STATUS_LABELS[status] ?? STATUS_LABELS.PROCESSING;

  return (
    <SpaceBetween size="l">
      {document?.status === "FAILED" && document.errorMessage ? (
        <Alert type="error" header={t("Ingestion failed")}>
          {document.errorMessage}
        </Alert>
      ) : null}

      <Table<DocumentChunk>
        variant="full-page"
        stickyHeader
        selectionType="multi"
        selectedItems={selected}
        onSelectionChange={({ detail }) => setSelected(detail.selectedItems)}
        loading={chunksQuery.isLoading}
        loadingText={t("Loading chunks")}
        header={
          <Header
            variant="awsui-h1-sticky"
            counter={`(${chunks.length})`}
            description={
              <SpaceBetween direction="horizontal" size="xs">
                <StatusIndicator type={statusMeta.type}>
                  {t(statusMeta.label)}
                </StatusIndicator>
                {document?.updatedAt ? (
                  <Box variant="small" color="text-body-secondary">
                    {t("Last updated")}: {formatTimestamp(document.updatedAt)}
                  </Box>
                ) : null}
              </SpaceBetween>
            }
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  iconName="refresh"
                  ariaLabel={t("Refresh")}
                  onClick={() => {
                    void documentsQuery.refetch();
                    void chunksQuery.refetch();
                  }}
                />
                <Button
                  onClick={() =>
                    navigate(
                      `/namespaces/${namespaceId}/retrieval?documentId=${documentId}`,
                    )
                  }
                >
                  {t("Open in retrieval")}
                </Button>
              </SpaceBetween>
            }
          >
            {document?.title || documentId}
          </Header>
        }
        columnDefinitions={[
          {
            id: "index",
            header: t("Chunk"),
            cell: (item) => chunks.indexOf(item) + 1,
            width: 90,
          },
          {
            id: "page",
            header: t("Page"),
            cell: (item) => item.page ?? "—",
            width: 90,
          },
          {
            id: "range",
            header: t("Characters"),
            cell: (item) => `${item.charStart ?? 0}–${item.charEnd ?? 0}`,
            width: 130,
          },
          {
            id: "text",
            header: t("Chunk text"),
            cell: (item) => item.text ?? "",
            minWidth: 400,
          },
        ]}
        items={chunks}
        wrapLines
        empty={
          <Box textAlign="center" color="inherit">
            <b>{t("No chunks yet")}</b>
            <Box padding={{ bottom: "s" }} variant="p" color="inherit">
              {t("Chunks appear here once ingestion has finished.")}
            </Box>
          </Box>
        }
        footer={
          chunksQuery.hasNextPage ? (
            <Box textAlign="center">
              <Button
                loading={chunksQuery.isFetchingNextPage}
                onClick={() => void chunksQuery.fetchNextPage()}
              >
                {t("Load more chunks")}
              </Button>
            </Box>
          ) : null
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
