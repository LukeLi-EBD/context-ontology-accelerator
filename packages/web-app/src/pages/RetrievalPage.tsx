// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import { useNamespace } from "@api-hooks/use-namespace";
import {
  useChunkVectorSearch,
  useListDocumentChunks,
  useListDocuments,
} from "@api-hooks";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Container from "@cloudscape-design/components/container";
import Flashbar from "@cloudscape-design/components/flashbar";
import type { FlashbarProps } from "@cloudscape-design/components/flashbar";
import Header from "@cloudscape-design/components/header";
import Select from "@cloudscape-design/components/select";
import type { SelectProps } from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import type {
  DocumentChunk,
  DocumentSummary,
  EmbeddingRecord,
} from "@coa/control-plane-client";
import { useAppI18n } from "../i18n/LocaleProvider";

function metadataString(metadata: unknown, key: string): string {
  if (!metadata || typeof metadata !== "object") return "";
  const value = (metadata as Record<string, unknown>)[key];
  return value === undefined || value === null ? "" : String(value);
}

export default function RetrievalPage() {
  const { namespaceId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { t } = useAppI18n();
  const { name } = useNamespace(namespaceId);

  const documentsQuery = useListDocuments(namespaceId);
  const documentId = searchParams.get("documentId") ?? "";
  const chunksQuery = useListDocumentChunks(namespaceId, documentId);
  const search = useChunkVectorSearch(namespaceId);

  const [searchedChunkId, setSearchedChunkId] = useState<string | undefined>();
  const [flashItems, setFlashItems] = useState<
    FlashbarProps.MessageDefinition[]
  >([]);

  useBreadcrumbTrail([
    { text: name, href: `/namespaces/${namespaceId}`, namespaceId },
    { text: t("Retrieval") },
  ]);

  const documents = useMemo<DocumentSummary[]>(() => {
    return documentsQuery.data?.pages.flatMap((page) => page.items ?? []) ?? [];
  }, [documentsQuery.data]);

  const chunks = useMemo<DocumentChunk[]>(() => {
    return chunksQuery.data?.pages.flatMap((page) => page.items ?? []) ?? [];
  }, [chunksQuery.data]);

  const chunksById = useMemo(() => {
    const map = new Map<string, DocumentChunk>();
    for (const chunk of chunks) {
      if (chunk.chunkId) map.set(chunk.chunkId, chunk);
    }
    return map;
  }, [chunks]);

  const documentOptions: SelectProps.Options = documents.map((document) => ({
    label: document.title || document.documentId || "—",
    value: document.documentId,
    description: document.status,
  }));

  function selectDocument(value: string | undefined) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set("documentId", value);
    else next.delete("documentId");
    setSearchParams(next, { replace: true });
    search.reset();
    setSearchedChunkId(undefined);
  }

  function runSearch(chunk: DocumentChunk) {
    const chunkId = chunk.chunkId ?? "";
    setSearchedChunkId(chunkId);
    search.mutate(chunkId, {
      onError: (error) => {
        setFlashItems([
          {
            type: "error",
            content:
              error.message === "CHUNK_VECTOR_NOT_FOUND"
                ? t("Chunk vector is not indexed yet.")
                : t("Failed to run retrieval: {message}", {
                    message: error.message,
                  }),
            dismissible: true,
            id: "retrieval-error",
          },
        ]);
      },
    });
  }

  const hits: EmbeddingRecord[] = search.data?.hits ?? [];

  return (
    <SpaceBetween size="l">
      <Flashbar items={flashItems} />
      <Container
        header={
          <Header
            variant="h2"
            description={t(
              "Reads a chunk's stored embedding and runs a real k-NN search with it. The query vector and the hits both come from the vector store.",
            )}
          >
            {t("Vector retrieval")}
          </Header>
        }
      >
        <SpaceBetween size="m">
          <Select
            ariaLabel={t("Document")}
            placeholder={t("Select a document")}
            options={documentOptions}
            selectedOption={
              documentOptions.find((option) => option.value === documentId) ??
              null
            }
            onChange={({ detail }) =>
              selectDocument(detail.selectedOption.value)
            }
            statusType={documentsQuery.isLoading ? "loading" : "finished"}
          />
          {documentId ? (
            <Table<DocumentChunk>
              variant="embedded"
              loading={chunksQuery.isLoading}
              loadingText={t("Loading chunks")}
              header={
                <Header counter={`(${chunks.length})`}>{t("Chunks")}</Header>
              }
              columnDefinitions={[
                {
                  id: "index",
                  header: t("Chunk"),
                  cell: (item) => chunks.indexOf(item) + 1,
                  width: 80,
                },
                {
                  id: "page",
                  header: t("Page"),
                  cell: (item) => item.page ?? "—",
                  width: 80,
                },
                {
                  id: "range",
                  header: t("Characters"),
                  cell: (item) => `${item.charStart ?? 0}–${item.charEnd ?? 0}`,
                  width: 120,
                },
                {
                  id: "text",
                  header: t("Chunk text"),
                  cell: (item) => item.text ?? "",
                  minWidth: 360,
                },
                {
                  id: "actions",
                  header: t("Actions"),
                  cell: (item) => (
                    <Button
                      loading={
                        search.isPending && searchedChunkId === item.chunkId
                      }
                      onClick={() => runSearch(item)}
                    >
                      {t("Search this vector")}
                    </Button>
                  ),
                  minWidth: 170,
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
            />
          ) : (
            <Box variant="p" color="text-body-secondary">
              {t("Select a document to inspect")}
            </Box>
          )}
        </SpaceBetween>
      </Container>

      {search.data ? (
        <Table<EmbeddingRecord>
          variant="container"
          header={
            <Header
              variant="h2"
              counter={`(${hits.length})`}
              description={t("Query vector: {uri} ({dimensions} dimensions)", {
                uri: search.data.embedding.entityUri ?? "",
                dimensions: search.data.embedding.dimensions ?? 0,
              })}
            >
              {t("Top matches")}
            </Header>
          }
          columnDefinitions={[
            {
              id: "rank",
              header: t("Rank"),
              cell: (item) => hits.indexOf(item) + 1,
              width: 80,
            },
            {
              id: "match",
              header: t("Match"),
              cell: (item) => {
                const hitChunkId = metadataString(item.metadata, "chunk_id");
                return hitChunkId === searchedChunkId ? (
                  <StatusIndicator type="success">
                    {t("Matched this chunk")}
                  </StatusIndicator>
                ) : (
                  <StatusIndicator type="info">
                    {t("Other chunk")}
                  </StatusIndicator>
                );
              },
              minWidth: 180,
            },
            {
              id: "page",
              header: t("Page"),
              cell: (item) => metadataString(item.metadata, "page") || "—",
              width: 80,
            },
            {
              id: "text",
              header: t("Chunk text"),
              cell: (item) => {
                const hitChunkId = metadataString(item.metadata, "chunk_id");
                return chunksById.get(hitChunkId)?.text ?? item.entityUri ?? "";
              },
              minWidth: 400,
            },
          ]}
          items={hits}
          wrapLines
          empty={
            <Box textAlign="center" color="inherit">
              <b>{t("No matches")}</b>
            </Box>
          }
        />
      ) : (
        <Alert type="info">{t("Run a search to see the hits.")}</Alert>
      )}
    </SpaceBetween>
  );
}
