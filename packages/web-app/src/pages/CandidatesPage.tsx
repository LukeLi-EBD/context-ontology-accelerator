// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useMemo, useState } from "react";
import { useSearchParams, useParams } from "react-router-dom";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import { useNamespace } from "@api-hooks/use-namespace";
import {
  DOCUMENT_ABOX_ONTOLOGY_ID,
  useListFactCandidates,
  useReviewFactCandidate,
  useVerifyAboxFact,
} from "@api-hooks";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Flashbar from "@cloudscape-design/components/flashbar";
import type { FlashbarProps } from "@cloudscape-design/components/flashbar";
import FormField from "@cloudscape-design/components/form-field";
import Header from "@cloudscape-design/components/header";
import Modal from "@cloudscape-design/components/modal";
import Select from "@cloudscape-design/components/select";
import type { SelectProps } from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import Textarea from "@cloudscape-design/components/textarea";
import { ControlPlaneServiceServiceException } from "@coa/control-plane-client";
import type {
  FactCandidate,
  FactCandidateStatus,
} from "@coa/control-plane-client";
import { useAppI18n } from "../i18n/LocaleProvider";
import type { AppMessage } from "../i18n/appMessages";

const STATUS_META: Record<
  FactCandidateStatus,
  {
    type: "pending" | "success" | "stopped" | "info";
    label: AppMessage;
  }
> = {
  PENDING: { type: "pending", label: "Pending" },
  APPROVED: { type: "success", label: "Approved" },
  REJECTED: { type: "stopped", label: "Rejected" },
};

export default function CandidatesPage() {
  const { namespaceId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { t } = useAppI18n();
  const { name } = useNamespace(namespaceId);

  const statusParam = searchParams.get("status") as FactCandidateStatus | null;
  const documentId = searchParams.get("documentId") ?? undefined;
  const [statusFilter, setStatusFilter] = useState<FactCandidateStatus | null>(
    statusParam,
  );
  const [flashItems, setFlashItems] = useState<
    FlashbarProps.MessageDefinition[]
  >([]);
  const [rejecting, setRejecting] = useState<FactCandidate | undefined>();
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState(false);
  const [busyId, setBusyId] = useState<string | undefined>();
  const [verifyingId, setVerifyingId] = useState<string | undefined>();

  useBreadcrumbTrail([
    { text: name, href: `/namespaces/${namespaceId}`, namespaceId },
    { text: t("Candidates") },
  ]);

  const candidatesQuery = useListFactCandidates(namespaceId, {
    status: statusFilter ?? undefined,
    documentId,
  });
  const { approve, reject } = useReviewFactCandidate(namespaceId);
  const verifyAbox = useVerifyAboxFact(namespaceId);

  const statusOptions: SelectProps.Options = [
    { label: t("All statuses"), value: "all" },
    { label: t("Pending"), value: "PENDING" },
    { label: t("Approved"), value: "APPROVED" },
    { label: t("Rejected"), value: "REJECTED" },
  ];

  const items = useMemo<FactCandidate[]>(() => {
    return (
      candidatesQuery.data?.pages.flatMap((page) => page.items ?? []) ?? []
    );
  }, [candidatesQuery.data]);

  function updateStatusFilter(value: FactCandidateStatus | null) {
    setStatusFilter(value);
    const next = new URLSearchParams(searchParams);
    if (value) next.set("status", value);
    else next.delete("status");
    setSearchParams(next, { replace: true });
  }

  function onError(error: ControlPlaneServiceServiceException) {
    const conflict =
      error instanceof ControlPlaneServiceServiceException &&
      error.name === "ConflictError";
    setFlashItems([
      {
        type: "error",
        content: conflict
          ? t("This candidate is no longer pending.")
          : t("Failed to review candidate: {message}", {
              message: error.message,
            }),
        dismissible: true,
        id: "review-error",
      },
    ]);
  }

  function approveCandidate(candidate: FactCandidate) {
    const candidateId = candidate.candidateId ?? "";
    setBusyId(candidateId);
    approve.mutate(
      { candidateId },
      {
        onSuccess: (output) => {
          setFlashItems([
            {
              type: "success",
              content: t("Candidate approved: {factId}", {
                factId: output.factId ?? "",
              }),
              dismissible: true,
              id: "approve-ok",
            },
          ]);
        },
        onError,
        onSettled: () => setBusyId(undefined),
      },
    );
  }

  function verifyCandidate(candidate: FactCandidate) {
    const candidateId = candidate.candidateId ?? "";
    setVerifyingId(candidateId);
    verifyAbox.mutate(
      { subject: candidate.subject ?? "" },
      {
        onSuccess: (result) => {
          setFlashItems([
            {
              type: result.found ? "success" : "warning",
              content: result.found
                ? t("A-Box triple verified: {uri} in {graph}.", {
                    uri: result.entityUri,
                    // The search is scoped to this graph, so a hit is proof of
                    // membership even when the wire omits graphUris.
                    graph: result.graphUris[0] ?? DOCUMENT_ABOX_ONTOLOGY_ID,
                  })
                : t("No A-Box triple found for this fact yet."),
              dismissible: true,
              id: `abox-${candidateId}`,
            },
          ]);
        },
        onError: (error) => {
          setFlashItems([
            {
              type: "error",
              content: t("A-Box verification failed: {message}", {
                message: error.message,
              }),
              dismissible: true,
              id: `abox-error-${candidateId}`,
            },
          ]);
        },
        onSettled: () => setVerifyingId(undefined),
      },
    );
  }

  function submitReject() {
    if (!rejecting) return;
    if (!reason.trim()) {
      setReasonError(true);
      return;
    }
    const candidateId = rejecting.candidateId ?? "";
    setBusyId(candidateId);
    reject.mutate(
      { candidateId, reason: reason.trim() },
      {
        onSuccess: () => {
          setRejecting(undefined);
          setReason("");
          setReasonError(false);
          setFlashItems([
            {
              type: "success",
              content: t("Candidate rejected."),
              dismissible: true,
              id: "reject-ok",
            },
          ]);
        },
        onError,
        onSettled: () => setBusyId(undefined),
      },
    );
  }

  return (
    <SpaceBetween size="l">
      <Flashbar items={flashItems} />
      <Table<FactCandidate>
        variant="full-page"
        stickyHeader
        loading={candidatesQuery.isLoading}
        loadingText={t("Loading candidates")}
        header={
          <Header
            variant="awsui-h1-sticky"
            counter={`(${items.length})`}
            description={t(
              "Candidates extracted from this namespace's documents. Approving one writes the fact and projects it into the graph.",
            )}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  iconName="refresh"
                  ariaLabel={t("Refresh")}
                  onClick={() => candidatesQuery.refetch()}
                />
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
                    updateStatusFilter(
                      value && value !== "all"
                        ? (value as FactCandidateStatus)
                        : null,
                    );
                  }}
                />
              </SpaceBetween>
            }
          >
            {t("Candidates")}
          </Header>
        }
        columnDefinitions={[
          {
            id: "subject",
            header: t("Subject"),
            cell: (item) => item.subject ?? "—",
            minWidth: 180,
          },
          {
            id: "predicate",
            header: t("Predicate"),
            cell: (item) => item.predicate ?? "—",
            minWidth: 150,
          },
          {
            id: "object",
            header: t("Object"),
            cell: (item) => item.object ?? "—",
            minWidth: 160,
          },
          {
            id: "confidence",
            header: t("Confidence"),
            cell: (item) =>
              item.confidence === undefined ? "—" : item.confidence.toFixed(2),
            width: 120,
          },
          {
            id: "document",
            header: t("Document"),
            cell: (item) => <Box variant="small">{item.documentId ?? "—"}</Box>,
            minWidth: 220,
          },
          {
            id: "status",
            header: t("Status"),
            cell: (item) => {
              const meta = STATUS_META[item.status ?? "PENDING"];
              return (
                <StatusIndicator type={meta.type}>
                  {t(meta.label)}
                </StatusIndicator>
              );
            },
            width: 130,
          },
          {
            id: "actions",
            header: t("Actions"),
            cell: (item) => {
              const pending =
                item.status === "PENDING" || item.status === undefined;
              if (item.status === "APPROVED") {
                return (
                  <Button
                    loading={verifyingId === item.candidateId}
                    onClick={() => verifyCandidate(item)}
                  >
                    {t("Verify A-Box")}
                  </Button>
                );
              }
              return (
                <SpaceBetween direction="horizontal" size="xs">
                  <Button
                    variant="primary"
                    disabled={!pending}
                    loading={busyId === item.candidateId && approve.isPending}
                    onClick={() => approveCandidate(item)}
                  >
                    {t("Approve")}
                  </Button>
                  <Button
                    disabled={!pending}
                    loading={busyId === item.candidateId && reject.isPending}
                    onClick={() => {
                      setRejecting(item);
                      setReason("");
                      setReasonError(false);
                    }}
                  >
                    {t("Reject")}
                  </Button>
                </SpaceBetween>
              );
            },
            minWidth: 190,
          },
        ]}
        items={items}
        empty={
          <Box textAlign="center" color="inherit">
            <b>{t("No candidates")}</b>
            <Box padding={{ bottom: "s" }} variant="p" color="inherit">
              {t("Candidates appear here after a document has been ingested.")}
            </Box>
          </Box>
        }
        footer={
          candidatesQuery.hasNextPage ? (
            <Box textAlign="center">
              <Button
                loading={candidatesQuery.isFetchingNextPage}
                onClick={() => void candidatesQuery.fetchNextPage()}
              >
                {t("Load more candidates")}
              </Button>
            </Box>
          ) : null
        }
      />

      <Modal
        visible={!!rejecting}
        onDismiss={() => setRejecting(undefined)}
        header={t("Reject candidate")}
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                variant="link"
                onClick={() => setRejecting(undefined)}
                disabled={reject.isPending}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="primary"
                loading={reject.isPending}
                onClick={submitReject}
              >
                {t("Reject")}
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Box variant="p">
            {rejecting?.subject} · {rejecting?.predicate} · {rejecting?.object}
          </Box>
          <FormField
            label={t("Reason for rejection")}
            errorText={reasonError ? t("A reason is required.") : undefined}
          >
            <Textarea
              value={reason}
              onChange={({ detail }) => {
                setReason(detail.value);
                if (detail.value.trim()) setReasonError(false);
              }}
              rows={3}
            />
          </FormField>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
}
