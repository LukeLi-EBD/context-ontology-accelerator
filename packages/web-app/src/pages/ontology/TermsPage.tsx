// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Terms and aliases (F58/F59).
 *
 * F58: anchor-class counts and the alias entries read from the published
 *      T-Box.
 * F59: the seven-column alias table (class, label, status, confidence, guard
 *      regex, canonical-for, suppressed surfaces).
 *
 * Read-only. Everything shown comes from `ListTerms`; an empty published graph
 * renders an explicit empty state rather than placeholder rows.
 */
import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import Alert from "@cloudscape-design/components/alert";
import Badge from "@cloudscape-design/components/badge";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Container from "@cloudscape-design/components/container";
import FormField from "@cloudscape-design/components/form-field";
import Header from "@cloudscape-design/components/header";
import Input from "@cloudscape-design/components/input";
import Pagination from "@cloudscape-design/components/pagination";
import Select from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import { useApiClient } from "@components/ApiClientProvider";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import {
  listTerms,
  type ListTermsResponse,
  type TermEntry,
} from "../../services/dictionary";

const PAGE_SIZE = 50;

const STATUS_OPTIONS = [
  { label: "全部状态", value: "all" },
  { label: "证据支持 (evidenced)", value: "evidenced" },
  { label: "推理生成 (inferred)", value: "inferred" },
];

function statusIndicator(status: string) {
  if (status === "evidenced") {
    return <StatusIndicator type="success">evidenced</StatusIndicator>;
  }
  if (status === "inferred") {
    return <StatusIndicator type="info">inferred</StatusIndicator>;
  }
  return <Badge>{status || "unknown"}</Badge>;
}

export function TermsPage() {
  const { namespaceId = "" } = useParams();
  const apiClient = useApiClient();

  useBreadcrumbTrail(
    namespaceId
      ? [
          {
            text: "Ontology",
            href: `/namespaces/${namespaceId}/ontology`,
            namespaceId,
          },
          { text: "术语与别名" },
        ]
      : [],
  );

  const [data, setData] = useState<ListTermsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queryText, setQueryText] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [status, setStatus] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    if (!namespaceId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    listTerms(apiClient, namespaceId, {
      q: appliedQuery || undefined,
      status: status === "all" ? undefined : status,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    })
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [apiClient, namespaceId, appliedQuery, status, page, refreshToken]);

  const pagesCount = useMemo(() => {
    if (!data || data.total === 0) return 1;
    return Math.max(1, Math.ceil(data.total / data.limit));
  }, [data]);

  const counts = data?.counts;
  const rows = data?.entries ?? [];

  const columnDefinitions = [
    {
      id: "class",
      header: "类（锚点）",
      cell: (item: TermEntry) => (
        <SpaceBetween size="xxs">
          <Box fontWeight="bold">{item.classLabel || "（无标签）"}</Box>
          <Box fontSize="body-s" color="text-body-secondary">
            {item.classIri || "—"}
          </Box>
        </SpaceBetween>
      ),
    },
    {
      id: "label",
      header: "别名表层",
      cell: (item: TermEntry) => item.label,
    },
    {
      id: "status",
      header: "状态",
      cell: (item: TermEntry) => statusIndicator(item.status),
    },
    {
      id: "confidence",
      header: "置信度",
      cell: (item: TermEntry) =>
        item.confidence === undefined || item.confidence === null
          ? "—"
          : item.confidence.toFixed(2),
    },
    {
      id: "guard",
      header: "守护正则",
      cell: (item: TermEntry) =>
        item.guardRegex ? <code>{item.guardRegex}</code> : "—",
    },
    {
      id: "canonicalFor",
      header: "归一目标",
      cell: (item: TermEntry) =>
        item.canonicalFor.length ? item.canonicalFor.join("、") : "—",
    },
    {
      id: "suppressed",
      header: "抑制表层",
      cell: (item: TermEntry) =>
        item.suppressedSurface.length ? item.suppressedSurface.join("、") : "—",
    },
  ];

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="读取当前命名空间已发布 T-Box 中的 term:TermEntry；锚点类计数对应 F58，七列别名表对应 F59。"
        actions={
          <Button
            iconName="refresh"
            onClick={() => setRefreshToken((value) => value + 1)}
          >
            刷新
          </Button>
        }
      >
        术语与别名
      </Header>

      {error && (
        <Alert type="error" header="术语加载失败">
          {error}
        </Alert>
      )}

      {data && !data.graph && (
        <Alert type="info" header="当前命名空间没有已发布的本体">
          发布一版 T-Box 后，term:TermEntry 会出现在这里。
        </Alert>
      )}

      <Container header={<Header variant="h2">锚点类与条目计数</Header>}>
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">锚点类（F58）</Box>
            <Box variant="awsui-value-large">{counts?.anchorClasses ?? 0}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">别名条目（F59）</Box>
            <Box variant="awsui-value-large">{counts?.termEntries ?? 0}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">证据支持</Box>
            <Box variant="awsui-value-large">{counts?.evidenced ?? 0}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">推理生成</Box>
            <Box variant="awsui-value-large">{counts?.inferred ?? 0}</Box>
          </div>
        </ColumnLayout>
        {data?.graph && (
          <Box margin={{ top: "s" }} fontSize="body-s" color="text-body-secondary">
            来源图：{data.graph}
          </Box>
        )}
      </Container>

      <Table
        columnDefinitions={columnDefinitions}
        items={rows}
        loading={loading}
        loadingText="正在读取术语…"
        trackBy="entry"
        resizableColumns
        header={
          <Header
            variant="h2"
            counter={data ? `(${data.total})` : undefined}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <FormField label="状态筛选">
                  <Select
                    selectedOption={
                      STATUS_OPTIONS.find((option) => option.value === status) ??
                      STATUS_OPTIONS[0]
                    }
                    onChange={({ detail }) => {
                      setStatus(detail.selectedOption.value ?? "all");
                      setPage(1);
                    }}
                    options={STATUS_OPTIONS}
                  />
                </FormField>
                <FormField label="搜索（类名 / 别名 / IRI）">
                  <Input
                    value={queryText}
                    placeholder="输入关键字后回车"
                    onChange={({ detail }) => setQueryText(detail.value)}
                    onKeyDown={({ detail }) => {
                      if (detail.key === "Enter") {
                        setAppliedQuery(queryText.trim());
                        setPage(1);
                      }
                    }}
                  />
                </FormField>
                <Button
                  onClick={() => {
                    setAppliedQuery(queryText.trim());
                    setPage(1);
                  }}
                >
                  查询
                </Button>
              </SpaceBetween>
            }
          >
            七列别名表
          </Header>
        }
        empty={
          <Box textAlign="center" color="inherit">
            <Box variant="strong">
              {appliedQuery || status !== "all"
                ? "没有符合筛选条件的别名"
                : "当前图里没有 term:TermEntry"}
            </Box>
          </Box>
        }
        pagination={
          <Pagination
            currentPageIndex={page}
            pagesCount={pagesCount}
            onChange={({ detail }) => setPage(detail.currentPageIndex)}
          />
        }
      />
    </SpaceBetween>
  );
}

export default TermsPage;
