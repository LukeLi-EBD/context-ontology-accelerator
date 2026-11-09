// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import { useNamespace } from "@api-hooks/use-namespace";
import { useListDocuments, useUploadDocument } from "@api-hooks";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Container from "@cloudscape-design/components/container";
import FileUpload from "@cloudscape-design/components/file-upload";
import Flashbar from "@cloudscape-design/components/flashbar";
import type { FlashbarProps } from "@cloudscape-design/components/flashbar";
import FormField from "@cloudscape-design/components/form-field";
import Header from "@cloudscape-design/components/header";
import Input from "@cloudscape-design/components/input";
import Link from "@cloudscape-design/components/link";
import Modal from "@cloudscape-design/components/modal";
import Select from "@cloudscape-design/components/select";
import type { SelectProps } from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import Tabs from "@cloudscape-design/components/tabs";
import Textarea from "@cloudscape-design/components/textarea";
import { ControlPlaneServiceServiceException } from "@coa/control-plane-client";
import type {
  DocumentStatus,
  DocumentSummary,
} from "@coa/control-plane-client";
import { formatTimestamp } from "@utils/helpers";
import { useAppI18n } from "../i18n/LocaleProvider";
import type { AppMessage } from "../i18n/appMessages";

const STATUS_META: Record<
  DocumentStatus,
  {
    type: "pending" | "in-progress" | "success" | "error";
    label: AppMessage;
  }
> = {
  UPLOADED: { type: "pending", label: "Uploaded" },
  PROCESSING: { type: "in-progress", label: "Processing" },
  INDEXED: { type: "success", label: "Indexed" },
  FAILED: { type: "error", label: "Failed" },
};

// The local ingestion worker extracts text from these types only. PDF is part
// of the server whitelist but has no local extractor yet, so it is not offered.
const UPLOAD_ACCEPT = ".txt,.md,.docx";
const CONTENT_TYPES: Record<string, string> = {
  txt: "text/plain",
  md: "text/markdown",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
};

function contentTypeFor(filename: string): string {
  const extension = filename.split(".").pop()?.toLowerCase() ?? "";
  return CONTENT_TYPES[extension] ?? "text/plain";
}

function utf8ToBase64(text: string): string {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? "");
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.onerror = () => reject(reader.error ?? new Error("read failed"));
    reader.readAsDataURL(file);
  });
}

export default function DocumentsPage() {
  const { namespaceId = "" } = useParams();
  const navigate = useNavigate();
  const { t } = useAppI18n();
  const { name } = useNamespace(namespaceId);

  useBreadcrumbTrail([
    { text: name, href: `/namespaces/${namespaceId}`, namespaceId },
    { text: t("Documents") },
  ]);

  const [statusFilter, setStatusFilter] = useState<
    DocumentStatus | undefined
  >();
  const [uploadVisible, setUploadVisible] = useState(false);
  const [uploadMode, setUploadMode] = useState<"file" | "text">("file");
  const [files, setFiles] = useState<File[]>([]);
  const [pasteName, setPasteName] = useState("");
  const [pasteText, setPasteText] = useState("");
  const [title, setTitle] = useState("");
  const [flashItems, setFlashItems] = useState<
    FlashbarProps.MessageDefinition[]
  >([]);

  const documentsQuery = useListDocuments(namespaceId, statusFilter);
  const upload = useUploadDocument();

  const statusOptions: SelectProps.Options = [
    { label: t("All statuses"), value: "all" },
    { label: t("Uploaded"), value: "UPLOADED" },
    { label: t("Processing"), value: "PROCESSING" },
    { label: t("Indexed"), value: "INDEXED" },
    { label: t("Failed"), value: "FAILED" },
  ];

  const items = useMemo<DocumentSummary[]>(() => {
    const rows =
      documentsQuery.data?.pages.flatMap((page) => page.items ?? []) ?? [];
    return [...rows].sort((a, b) =>
      (b.updatedAt ?? "").localeCompare(a.updatedAt ?? ""),
    );
  }, [documentsQuery.data]);

  const busy = upload.isPending;
  const hasContent =
    uploadMode === "file" ? files.length > 0 : pasteText.trim().length > 0;

  async function submitUpload() {
    let filename: string;
    let contentBase64: string;
    try {
      if (uploadMode === "text") {
        filename = pasteName.trim() || "pasted-document.txt";
        contentBase64 = utf8ToBase64(pasteText);
      } else {
        const file = files[0];
        if (!file) return;
        filename = file.name;
        contentBase64 = await readFileAsBase64(file);
      }
    } catch (error) {
      setFlashItems([
        {
          type: "error",
          content: t("Failed to upload document: {message}", {
            message: String(error),
          }),
          dismissible: true,
          id: "upload-error",
        },
      ]);
      return;
    }

    upload.mutate(
      {
        namespaceId,
        filename,
        contentType: contentTypeFor(filename),
        contentBase64,
        title: title.trim() || undefined,
      },
      {
        onSuccess: (output) => {
          setUploadVisible(false);
          setFiles([]);
          setPasteName("");
          setPasteText("");
          setTitle("");
          setFlashItems([
            {
              type: "success",
              content: t("Document uploaded: {documentId}", {
                documentId: output.documentId ?? "",
              }),
              dismissible: true,
              id: "upload-ok",
            },
          ]);
        },
        onError: (error) => {
          const conflict =
            error instanceof ControlPlaneServiceServiceException &&
            error.name === "ConflictError";
          setFlashItems([
            {
              type: "error",
              content: conflict
                ? t("This document already exists in this namespace.")
                : t("Failed to upload document: {message}", {
                    message: error.message,
                  }),
              dismissible: true,
              id: "upload-error",
            },
          ]);
        },
      },
    );
  }

  return (
    <SpaceBetween size="l">
      <Flashbar items={flashItems} />
      <Table<DocumentSummary>
        variant="full-page"
        stickyHeader
        loading={documentsQuery.isLoading}
        loadingText={t("Loading documents")}
        header={
          <Header
            variant="awsui-h1-sticky"
            counter={`(${items.length})`}
            description={t(
              "Upload a document and follow its ingestion: chunks, extraction, and review.",
            )}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Select
                  ariaLabel={t("Filter by status")}
                  options={statusOptions}
                  selectedOption={
                    statusOptions.find(
                      (option) => option.value === (statusFilter ?? "all"),
                    ) ?? null
                  }
                  onChange={({ detail }) => {
                    const value = detail.selectedOption.value;
                    setStatusFilter(
                      value && value !== "all"
                        ? (value as DocumentStatus)
                        : undefined,
                    );
                  }}
                />
                <Button
                  iconName="refresh"
                  ariaLabel={t("Refresh")}
                  onClick={() => documentsQuery.refetch()}
                />
                <Button
                  variant="primary"
                  onClick={() => setUploadVisible(true)}
                >
                  {t("Upload document")}
                </Button>
              </SpaceBetween>
            }
          >
            {t("Documents")}
          </Header>
        }
        columnDefinitions={[
          {
            id: "title",
            header: t("Title"),
            cell: (item) => (
              <Link
                href={`/namespaces/${namespaceId}/documents/${item.documentId}`}
                onFollow={(event) => {
                  event.preventDefault();
                  navigate(
                    `/namespaces/${namespaceId}/documents/${item.documentId}`,
                  );
                }}
              >
                {item.title || item.documentId || "—"}
              </Link>
            ),
            minWidth: 220,
          },
          {
            id: "status",
            header: t("Status"),
            cell: (item) => {
              const meta = STATUS_META[item.status ?? "UPLOADED"];
              return (
                <SpaceBetween size="xxs">
                  <StatusIndicator type={meta.type}>
                    {t(meta.label)}
                  </StatusIndicator>
                  {item.status === "FAILED" && item.errorMessage ? (
                    <Box variant="small" color="text-status-error">
                      {item.errorMessage}
                    </Box>
                  ) : null}
                </SpaceBetween>
              );
            },
            minWidth: 200,
          },
          {
            id: "chunkCount",
            header: t("Chunks"),
            cell: (item) => item.chunkCount ?? 0,
            width: 100,
          },
          {
            id: "updatedAt",
            header: t("Last updated"),
            cell: (item) => formatTimestamp(item.updatedAt),
            minWidth: 170,
          },
        ]}
        items={items}
        empty={
          <Box textAlign="center" color="inherit">
            <b>{t("No documents")}</b>
            <Box padding={{ bottom: "s" }} variant="p" color="inherit">
              {t("Upload a document to start ingestion.")}
            </Box>
          </Box>
        }
      />

      <Modal
        visible={uploadVisible}
        onDismiss={() => setUploadVisible(false)}
        header={t("Upload document")}
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                variant="link"
                onClick={() => setUploadVisible(false)}
                disabled={busy}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="primary"
                loading={busy}
                disabled={!hasContent}
                onClick={() => void submitUpload()}
              >
                {t("Upload")}
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Tabs
            activeTabId={uploadMode}
            onChange={({ detail }) =>
              setUploadMode(detail.activeTabId as "file" | "text")
            }
            tabs={[
              {
                id: "file",
                label: t("Upload file"),
                content: (
                  <Container>
                    <FileUpload
                      value={files}
                      onChange={({ detail }) => setFiles(detail.value)}
                      accept={UPLOAD_ACCEPT}
                      multiple={false}
                      i18nStrings={{
                        uploadButtonText: () => t("Choose file"),
                        dropzoneText: () => t("Drop file to upload"),
                        removeFileAriaLabel: (index) =>
                          t("Remove file {index}", {
                            index: index + 1,
                          }),
                        limitShowFewer: t("Show fewer files"),
                        limitShowMore: t("Show more files"),
                        errorIconAriaLabel: t("Error"),
                      }}
                    />
                  </Container>
                ),
              },
              {
                id: "text",
                label: t("Paste text"),
                content: (
                  <SpaceBetween size="m">
                    <FormField label={t("File name")}>
                      <Input
                        value={pasteName}
                        onChange={({ detail }) => setPasteName(detail.value)}
                        placeholder="pasted-document.txt"
                      />
                    </FormField>
                    <FormField
                      label={t("Content")}
                      description={t("Paste the document text here.")}
                    >
                      <Textarea
                        value={pasteText}
                        onChange={({ detail }) => setPasteText(detail.value)}
                        rows={10}
                      />
                    </FormField>
                  </SpaceBetween>
                ),
              },
            ]}
          />
          <FormField
            label={t("Document title")}
            description={t(
              "Title is optional; the filename is used when empty.",
            )}
          >
            <Input
              value={title}
              onChange={({ detail }) => setTitle(detail.value)}
              placeholder={files[0]?.name ?? ""}
            />
          </FormField>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
}
