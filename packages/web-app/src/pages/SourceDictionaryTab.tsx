// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Data dictionary tab on the source detail page (F60-F66).
 *
 * F60 table filter, F61 column filter, F62 refresh/introspection, F63 the
 * ten-column dictionary view, F64 binding-tier filter, F65 paging, F66 comment
 * coverage and the four view modes.
 *
 * The tab never invents rows: before the first refresh the tables are empty and
 * the page says so. A failed refresh surfaces the server's message and the
 * failed run id.
 */
import React, { useEffect, useMemo, useState } from "react";
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
import ProgressBar from "@cloudscape-design/components/progress-bar";
import Select from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import { useApiClient } from "@components/ApiClientProvider";
import {
  getDictionary,
  getDictionaryView,
  refreshDictionaries,
  type DictionaryColumn,
  type DictionaryView,
  type GetDictionaryResponse,
  type GetDictionaryViewResponse,
} from "../services/dictionary";

const PAGE_SIZE = 20;

const VIEW_OPTIONS: { label: string; value: DictionaryView }[] = [
  { label: "全部列", value: "all" },
  { label: "缺注释", value: "missing_comment" },
  { label: "未绑定", value: "unbound" },
  { label: "可映射未绑定", value: "mappable_unbound" },
];

const BINDING_OPTIONS = [
  { label: "全部档位", value: "all" },
  { label: "显式规则 (explicit)", value: "explicit" },
  { label: "同名匹配 (name_match)", value: "name_match" },
  { label: "人工绑定 (manual)", value: "manual" },
  { label: "未绑定 (none)", value: "none" },
];

function bindingBadge(method: string) {
  if (method === "manual") return <Badge color="blue">manual</Badge>;
  if (method === "explicit") return <Badge color="green">explicit</Badge>;
  if (method === "name_match") return <Badge>name_match</Badge>;
  return <Badge color="red">none</Badge>;
}

function percent(ratio: number | undefined): number {
  if (ratio === undefined || ratio === null) return 0;
  return Math.round(ratio * 100);
}

function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `ui-${crypto.randomUUID()}`;
  }
  return `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export interface SourceDictionaryTabProps {
  namespaceId: string;
  sourceId: string;
}

export function SourceDictionaryTab({
  namespaceId,
  sourceId,
}: SourceDictionaryTabProps) {
  const apiClient = useApiClient();

  const [summary, setSummary] = useState<GetDictionaryResponse | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [viewData, setViewData] = useState<GetDictionaryViewResponse | null>(
    null,
  );
  const [viewError, setViewError] = useState<string | null>(null);
  const [loadingView, setLoadingView] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  const [view, setView] = useState<DictionaryView>("all");
  const [table, setTable] = useState("all");
  const [bindingMethod, setBindingMethod] = useState("all");
  const [queryText, setQueryText] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [page, setPage] = useState(1);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    if (!namespaceId || !sourceId) return;
    let cancelled = false;
    setSummaryError(null);
    getDictionary(apiClient, namespaceId, sourceId)
      .then((result) => {
        if (!cancelled) setSummary(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setSummaryError(err instanceof Error ? err.message : String(err));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [apiClient, namespaceId, sourceId, refreshToken]);

  useEffect(() => {
    if (!namespaceId || !sourceId) return;
    let cancelled = false;
    setLoadingView(true);
    setViewError(null);
    getDictionaryView(apiClient, namespaceId, sourceId, {
      view,
      table: table === "all" ? undefined : table,
      bindingMethod:
        bindingMethod === "all"
          ? undefined
          : (bindingMethod as DictionaryColumn["bindingMethod"]),
      q: appliedQuery || undefined,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    })
      .then((result) => {
        if (!cancelled) setViewData(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setViewError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingView(false);
      });
    return () => {
      cancelled = true;
    };
  }, [
    apiClient,
    namespaceId,
    sourceId,
    view,
    table,
    bindingMethod,
    appliedQuery,
    page,
    refreshToken,
  ]);

  const tableOptions = useMemo(() => {
    const options = [{ label: "全部表", value: "all" }];
    (summary?.tables ?? []).forEach((item) => {
      options.push({
        label: `${item.table} (${item.columns} 列)`,
        value: item.table,
      });
    });
    return options;
  }, [summary]);

  const totals = viewData?.coverage ?? summary?.totals;
  const pagesCount = viewData
    ? Math.max(1, Math.ceil(viewData.total / viewData.limit))
    : 1;

  const onRefresh = async () => {
    setRefreshing(true);
    setRefreshError(null);
    setRefreshMessage(null);
    try {
      const result = await refreshDictionaries(
        apiClient,
        namespaceId,
        sourceId,
        { idempotencyKey: newIdempotencyKey(), requestedBy: "web-app" },
      );
      const run = result.run;
      setRefreshMessage(
        `内省完成：处理 ${run.processed ?? 0} 列，新增 ${run.inserted ?? 0}，` +
          `更新 ${run.updated ?? 0}，未变 ${run.unchanged ?? 0}，` +
          `移除 ${run.removed ?? 0}；绑定依据 ${result.bindingBasis}` +
          (result.warnings?.length
            ? `；提示 ${result.warnings.join(", ")}`
            : ""),
      );
      setPage(1);
      setRefreshToken((value) => value + 1);
    } catch (err: unknown) {
      setRefreshError(err instanceof Error ? err.message : String(err));
    } finally {
      setRefreshing(false);
    }
  };

  const columnDefinitions = [
    { id: "table", header: "表", cell: (item: DictionaryColumn) => item.table },
    { id: "column", header: "列", cell: (item: DictionaryColumn) => item.column },
    {
      id: "dataType",
      header: "类型",
      cell: (item: DictionaryColumn) => item.dataType,
    },
    {
      id: "nullable",
      header: "可空",
      cell: (item: DictionaryColumn) => (item.isNullable ? "是" : "否"),
    },
    {
      id: "binding",
      header: "绑定档位",
      cell: (item: DictionaryColumn) => (
        <SpaceBetween size="xxs">
          {bindingBadge(item.bindingMethod)}
          {item.propertyIri && (
            <Box fontSize="body-s" color="text-body-secondary">
              {item.propertyIri}
            </Box>
          )}
        </SpaceBetween>
      ),
    },
    {
      id: "comment",
      header: "注释",
      cell: (item: DictionaryColumn) =>
        item.comment ? item.comment : "—",
    },
  ];

  const latestRun = summary?.latestRun;

  return (
    <SpaceBetween size="l">
      {refreshError && (
        <Alert type="error" header="字典刷新失败" dismissible onDismiss={() => setRefreshError(null)}>
          {refreshError}
        </Alert>
      )}
      {refreshMessage && (
        <Alert type="success" header="字典刷新完成" dismissible onDismiss={() => setRefreshMessage(null)}>
          {refreshMessage}
        </Alert>
      )}
      {summaryError && (
        <Alert type="error" header="字典摘要加载失败">
          {summaryError}
        </Alert>
      )}

      <Container
        header={
          <Header
            variant="h2"
            description="列快照来自数据源内省；manual 绑定不会被刷新覆盖。"
            actions={
              <Button
                variant="primary"
                iconName="refresh"
                loading={refreshing}
                onClick={onRefresh}
              >
                刷新字典
              </Button>
            }
          >
            字典概览
          </Header>
        }
      >
        <SpaceBetween size="m">
          <ColumnLayout columns={4} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">列总数</Box>
              <Box variant="awsui-value-large">{totals?.total ?? 0}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">已注释</Box>
              <Box variant="awsui-value-large">{totals?.commented ?? 0}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">已绑定</Box>
              <Box variant="awsui-value-large">
                {summary?.boundColumns ?? 0}
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">表数</Box>
              <Box variant="awsui-value-large">
                {summary?.tables.length ?? 0}
              </Box>
            </div>
          </ColumnLayout>

          <ProgressBar
            value={percent(totals?.ratio)}
            description="注释覆盖率（F66）"
            additionalInfo={`${totals?.commented ?? 0} / ${totals?.total ?? 0} 列有注释`}
          />

          {latestRun ? (
            <Box>
              <SpaceBetween direction="horizontal" size="xs">
                <span>最近一次内省：</span>
                {latestRun.status === "succeeded" ? (
                  <StatusIndicator type="success">succeeded</StatusIndicator>
                ) : latestRun.status === "failed" ? (
                  <StatusIndicator type="error">failed</StatusIndicator>
                ) : (
                  <StatusIndicator type="in-progress">{latestRun.status}</StatusIndicator>
                )}
                <span>
                  {latestRun.finishedAt ?? latestRun.startedAt ?? "—"} ·{" "}
                  {latestRun.runId}
                </span>
              </SpaceBetween>
              {latestRun.error && (
                <Box color="text-status-error" fontSize="body-s">
                  {latestRun.error}
                </Box>
              )}
            </Box>
          ) : (
            <Box color="text-body-secondary">
              尚未内省。点击“刷新字典”从数据源读取列。
            </Box>
          )}
        </SpaceBetween>
      </Container>

      {viewData?.warnings?.length ? (
        <Alert type="warning" header="视图提示">
          {viewData.warnings.join(", ")}
        </Alert>
      ) : null}

      {viewError && (
        <Alert type="error" header="字典列加载失败">
          {viewError}
        </Alert>
      )}

      <Table
        columnDefinitions={columnDefinitions}
        items={viewData?.items ?? []}
        loading={loadingView}
        loadingText="正在读取字典列…"
        trackBy={(item) => `${item.table}.${item.column}`}
        resizableColumns
        header={
          <Header
            variant="h2"
            counter={viewData ? `(${viewData.total})` : undefined}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <FormField label="视图">
                  <Select
                    selectedOption={
                      VIEW_OPTIONS.find((option) => option.value === view) ??
                      VIEW_OPTIONS[0]
                    }
                    onChange={({ detail }) => {
                      setView((detail.selectedOption.value as DictionaryView) ?? "all");
                      setPage(1);
                    }}
                    options={VIEW_OPTIONS}
                  />
                </FormField>
                <FormField label="表">
                  <Select
                    selectedOption={
                      tableOptions.find((option) => option.value === table) ??
                      tableOptions[0]
                    }
                    onChange={({ detail }) => {
                      setTable(detail.selectedOption.value ?? "all");
                      setPage(1);
                    }}
                    options={tableOptions}
                  />
                </FormField>
                <FormField label="绑定档位">
                  <Select
                    selectedOption={
                      BINDING_OPTIONS.find(
                        (option) => option.value === bindingMethod,
                      ) ?? BINDING_OPTIONS[0]
                    }
                    onChange={({ detail }) => {
                      setBindingMethod(detail.selectedOption.value ?? "all");
                      setPage(1);
                    }}
                    options={BINDING_OPTIONS}
                  />
                </FormField>
                <FormField label="查询">
                  <Input
                    value={queryText}
                    placeholder="表 / 列 / 注释，回车查询"
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
            数据字典列
          </Header>
        }
        empty={
          <Box textAlign="center" color="inherit">
            <Box variant="strong">
              {totals?.total
                ? "当前筛选下没有列"
                : "该数据源尚未生成字典快照"}
            </Box>
            <Box variant="p" color="inherit">
              {totals?.total
                ? "调整视图、表或查询条件。"
                : "点击“刷新字典”执行一次内省。"}
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

export default SourceDictionaryTab;
