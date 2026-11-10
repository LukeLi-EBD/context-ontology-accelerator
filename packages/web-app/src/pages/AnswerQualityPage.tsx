import React, { useCallback, useEffect, useState } from "react";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import Select from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import { useApiClient } from "@components";
import {
  getAnswerQuality,
  type AnswerQualityCase,
  type AnswerQualityCitation,
  type AnswerQualityResponse,
  type AnswerQualityStrategy,
} from "../services/answer-quality";

const STRATEGY_OPTIONS = [
  { label: "词法（lexical）", value: "lexical" },
  { label: "混合（hybrid）", value: "hybrid" },
];

function percent(value: number | undefined): string {
  if (value === undefined || value === null) return "—";
  return `${Math.round(value * 1000) / 10}%`;
}

/**
 * /playground/quality — quality panel for the fixed golden set (F86/F87/F89)
 * with per-case drill-down (F88).
 *
 * The endpoint re-runs the golden set on every call and stores nothing, so the
 * panel reports one run. A trend line is deliberately absent: there is no run
 * history to draw it from, and inventing one would be a scoreboard, not a check.
 */
export default function AnswerQualityPage() {
  const client = useApiClient();
  const [strategy, setStrategy] = useState<AnswerQualityStrategy>("lexical");
  const [data, setData] = useState<AnswerQualityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AnswerQualityCase | null>(null);

  const load = useCallback(
    async (next: AnswerQualityStrategy) => {
      setLoading(true);
      setError(null);
      try {
        setData(await getAnswerQuality(client, next, 10));
        setSelected(null);
      } catch (e) {
        setData(null);
        setError(e instanceof Error ? e.message : "加载问答质量失败");
      } finally {
        setLoading(false);
      }
    },
    [client],
  );

  useEffect(() => {
    load(strategy);
  }, [load, strategy]);

  const summary = data?.summary;
  const cases = data?.cases ?? [];

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="固定题集重跑，逐题对比「该答 / 该拒」。只读，不写库。"
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Select
              selectedOption={
                STRATEGY_OPTIONS.find((o) => o.value === strategy) ?? null
              }
              onChange={({ detail }) => {
                setStrategy(detail.selectedOption.value as AnswerQualityStrategy);
              }}
              options={STRATEGY_OPTIONS}
              ariaLabel="检索策略"
            />
            <Button
              iconName="refresh"
              loading={loading}
              onClick={() => load(strategy)}
            >
              重新跑
            </Button>
          </SpaceBetween>
        }
      >
        问答质量
      </Header>

      {error && (
        <Alert type="error" header="加载失败">
          {error}
        </Alert>
      )}

      <Alert type="info" header="没有趋势">
        每次打开都用固定题集现场重跑，结果不落库，因此这里只有「本次运行」。要做趋势得先加运行记录表，不在本轮。
      </Alert>

      <Container
        header={
          <Header
            variant="h2"
            description={
              data
                ? `题集 ${data.goldenSet.id}，共 ${data.goldenSet.count} 题，已评估 ${data.goldenSet.evaluated} 题`
                : undefined
            }
          >
            本次总览
          </Header>
        }
      >
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">通过率</Box>
            <Box>
              {summary
                ? `${summary.passed}/${summary.cases}（${percent(summary.passRate)}）`
                : "—"}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">引用覆盖率</Box>
            <Box>{percent(summary?.citationCoverageRate)}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">引用可解析率</Box>
            <Box>
              {percent(summary?.citationResolvableRate)}
              {summary ? `（${summary.resolvableCitations}/${summary.citations}）` : ""}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">断链率</Box>
            <Box>
              <StatusIndicator
                type={
                  (summary?.brokenLinkRate ?? 0) > 0 ? "warning" : "success"
                }
              >
                {percent(summary?.brokenLinkRate)}
              </StatusIndicator>
            </Box>
          </div>
        </ColumnLayout>
      </Container>

      <Container header={<Header variant="h2">按题型的引用与拒答（F89）</Header>}>
        <Table
          items={data?.citationCoverageByType ?? []}
          columnDefinitions={[
            { id: "type", header: "题型", cell: (item) => item.type },
            { id: "cases", header: "题数", cell: (item) => item.cases },
            { id: "refused", header: "拒答", cell: (item) => item.refused },
            {
              id: "coverage",
              header: "引用覆盖率",
              cell: (item) => percent(item.citationCoverageRate),
            },
            {
              id: "resolvable",
              header: "可解析率",
              cell: (item) => percent(item.resolvableRate),
            },
            {
              id: "citations",
              header: "引用数",
              cell: (item) => item.citations,
            },
          ]}
          empty={<Box textAlign="center">没有题型数据</Box>}
        />
      </Container>

      <Container header={<Header variant="h2">拒答原因</Header>}>
        <Table
          items={data?.refusalsByReason ?? []}
          columnDefinitions={[
            { id: "type", header: "题型", cell: (item) => item.type },
            { id: "reason", header: "原因码", cell: (item) => item.reasonCode },
            { id: "count", header: "题数", cell: (item) => item.count },
          ]}
          empty={<Box textAlign="center">本次没有拒答</Box>}
        />
      </Container>

      <Table<AnswerQualityCase>
        header={
          <Header variant="h2" description="点一行看判定明细与引用">
            逐题结果（F88）
          </Header>
        }
        items={cases}
        loading={loading}
        columnDefinitions={[
          {
            id: "id",
            header: "题号",
            cell: (item) => (
              <Button variant="inline-link" onClick={() => setSelected(item)}>
                {item.id}
              </Button>
            ),
          },
          { id: "query", header: "问题", cell: (item) => item.query },
          { id: "type", header: "题型", cell: (item) => item.type },
          {
            id: "expect",
            header: "期望",
            cell: (item) => (item.expectRefused ? "拒答" : "作答"),
          },
          {
            id: "actual",
            header: "实际",
            cell: (item) =>
              item.actual.refused
                ? `拒答${item.actual.reasonCode ? `（${item.actual.reasonCode}）` : ""}`
                : "作答",
          },
          {
            id: "citations",
            header: "引用",
            cell: (item) => item.actual.citations.length,
          },
          {
            id: "pass",
            header: "判定",
            cell: (item) => (
              <StatusIndicator type={item.pass ? "success" : "error"}>
                {item.pass ? "通过" : "不通过"}
              </StatusIndicator>
            ),
          },
        ]}
        empty={<Box textAlign="center">题集为空</Box>}
      />

      {selected && (
        <Container
          header={
            <Header variant="h2" description={selected.query}>
              {selected.id} 明细
            </Header>
          }
        >
          <SpaceBetween size="m">
            {selected.failures.length > 0 && (
              <Alert type="warning" header="不通过原因">
                <SpaceBetween size="xxs">
                  {selected.failures.map((failure) => (
                    <Box key={failure}>{failure}</Box>
                  ))}
                </SpaceBetween>
              </Alert>
            )}
            <div>
              <Box variant="awsui-key-label">缺失层</Box>
              <Box>
                {selected.actual.missingLayers.length > 0
                  ? selected.actual.missingLayers.join("、")
                  : "无"}
              </Box>
            </div>
            <Table<AnswerQualityCitation>
              items={selected.actual.citations}
              columnDefinitions={[
                { id: "kind", header: "类型", cell: (item) => item.kind },
                { id: "ref", header: "引用", cell: (item) => item.ref },
                {
                  id: "resolvable",
                  header: "可解析",
                  cell: (item) => (
                    <StatusIndicator
                      type={item.resolvable ? "success" : "error"}
                    >
                      {item.resolvable ? "是" : "否"}
                    </StatusIndicator>
                  ),
                },
                {
                  id: "url",
                  header: "跳转",
                  cell: (item) =>
                    item.resolveUrl ? (
                      <a href={item.resolveUrl}>{item.resolveUrl}</a>
                    ) : (
                      "—"
                    ),
                },
              ]}
              empty={<Box textAlign="center">本题没有引用</Box>}
            />
          </SpaceBetween>
        </Container>
      )}
    </SpaceBetween>
  );
}
