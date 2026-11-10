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
  listAnswerQualityRuns,
  type AnswerQualityCase,
  type AnswerQualityCitation,
  type AnswerQualityResponse,
  type AnswerQualityRun,
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

function formatRanAt(value: string): string {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return value;
  return new Date(timestamp).toLocaleString("zh-CN", {
    hour12: false,
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function layerSummary(run: AnswerQualityRun): string {
  if (!run.layerCoverage || run.layerCoverage.length === 0) {
    return "—（该行未记录分层覆盖）";
  }
  return run.layerCoverage
    .map((entry) => `${entry.layer} ${entry.covered}/${entry.evaluated}`)
    .join("；");
}

/**
 * Multi-point trend for stored runs. A single run is not a trend, so it is
 * reported as "历史不足" instead of being drawn as one point.
 */
function TrendChart({ runs }: { runs: AnswerQualityRun[] }) {
  if (runs.length < 2) {
    return (
      <Box textAlign="center" color="text-body-secondary">
        {runs.length === 0
          ? "历史不足：还没有运行记录"
          : "历史不足：只有 1 次运行，单点不画线"}
      </Box>
    );
  }
  const ordered = [...runs].sort(
    (a, b) => Date.parse(a.ranAt) - Date.parse(b.ranAt),
  );
  const width = 720;
  const height = 200;
  const padX = 56;
  const padY = 28;
  const x = (index: number) =>
    padX + (index * (width - padX * 2)) / (ordered.length - 1);
  const y = (rate: number) =>
    height - padY - Math.max(0, Math.min(1, rate)) * (height - padY * 2);
  const polyline = ordered
    .map((run, index) => `${x(index)},${y(run.passRate)}`)
    .join(" ");
  return (
    <SpaceBetween size="xs">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="通过率趋势"
        style={{ width: "100%", height: "auto", display: "block" }}
      >
        {[0, 0.5, 1].map((tick) => (
          <g key={tick}>
            <line
              x1={padX}
              x2={width - padX}
              y1={y(tick)}
              y2={y(tick)}
              stroke="#e9ebed"
              strokeWidth="1"
            />
            <text
              x={padX - 8}
              y={y(tick) + 4}
              textAnchor="end"
              fontSize="11"
              fill="#687078"
            >
              {Math.round(tick * 100)}%
            </text>
          </g>
        ))}
        <polyline
          points={polyline}
          fill="none"
          stroke="#0972d3"
          strokeWidth="2"
        />
        {ordered.map((run, index) => (
          <circle
            key={run.runId}
            cx={x(index)}
            cy={y(run.passRate)}
            r="4"
            fill="#0972d3"
          >
            <title>
              {`${formatRanAt(run.ranAt)} · 通过率 ${percent(run.passRate)} · ${run.runId}`}
            </title>
          </circle>
        ))}
        <text x={padX} y={height - 8} fontSize="11" fill="#687078">
          {formatRanAt(ordered[0].ranAt)}
        </text>
        <text
          x={width - padX}
          y={height - 8}
          textAnchor="end"
          fontSize="11"
          fill="#687078"
        >
          {formatRanAt(ordered[ordered.length - 1].ranAt)}
        </text>
      </svg>
      <Box variant="small" color="text-body-secondary">
        蓝线为通过率（passed / evaluated），共 {ordered.length} 次运行；数据来自
        platform.answer_quality_run。
      </Box>
    </SpaceBetween>
  );
}

/**
 * /playground/quality — quality panel for the fixed golden set (F86/F87/F89)
 * with per-case drill-down (F88).
 *
 * Each call still re-runs the golden set, but a full run is recorded in
 * `platform.answer_quality_run`. The trend reads those stored rows through
 * ListAnswerQualityRuns; it never synthesises a history that does not exist.
 */
export default function AnswerQualityPage() {
  const client = useApiClient();
  const [strategy, setStrategy] = useState<AnswerQualityStrategy>("lexical");
  const [data, setData] = useState<AnswerQualityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AnswerQualityCase | null>(null);
  const [runs, setRuns] = useState<AnswerQualityRun[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await listAnswerQualityRuns(client, 20);
      setRuns(response.items);
    } catch (e) {
      setRuns([]);
      setHistoryError(e instanceof Error ? e.message : "加载运行历史失败");
    } finally {
      setHistoryLoading(false);
    }
  }, [client]);

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
        // A full run just wrote a row, so read the stored history back rather
        // than appending an in-memory point. Runs on failure too: older rows
        // are still real history.
        await loadHistory();
        setLoading(false);
      }
    },
    [client, loadHistory],
  );

  // Runs are explicit: opening the page only reads history. A full run writes a
  // row now, so auto-running on mount (which StrictMode would double) would
  // create phantom history.
  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const summary = data?.summary;
  const cases = data?.cases ?? [];

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="固定题集重跑，逐题对比「该答 / 该拒」；每次完整运行落一条历史。"
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Select
              selectedOption={
                STRATEGY_OPTIONS.find((o) => o.value === strategy) ?? null
              }
              onChange={({ detail }) => {
                setStrategy(
                  detail.selectedOption.value as AnswerQualityStrategy,
                );
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
        {!data && !loading && !error && (
          <Box color="text-body-secondary" padding={{ bottom: "s" }}>
            尚未运行；点击右上角「重新跑」执行一次固定题集评估（会写一条历史）。
          </Box>
        )}
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
              {summary
                ? `（${summary.resolvableCitations}/${summary.citations}）`
                : ""}
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

      <Container
        header={
          <Header
            variant="h2"
            description={`已落库运行 ${runs.length} 条，按 ran_at 倒序（最多 20 条）`}
          >
            运行历史与趋势（F86）
          </Header>
        }
      >
        <SpaceBetween size="m">
          {historyError && (
            <Alert type="error" header="运行历史加载失败">
              {historyError}
            </Alert>
          )}
          {historyLoading && runs.length === 0 ? (
            <Box textAlign="center" color="text-body-secondary">
              正在读取运行历史…
            </Box>
          ) : (
            <>
              <TrendChart runs={runs} />
              <Table
                items={runs}
                columnDefinitions={[
                  {
                    id: "runId",
                    header: "runId",
                    cell: (item) => item.runId,
                  },
                  {
                    id: "ranAt",
                    header: "时间",
                    cell: (item) => formatRanAt(item.ranAt),
                  },
                  {
                    id: "strategy",
                    header: "策略",
                    cell: (item) => item.strategy,
                  },
                  {
                    id: "result",
                    header: "通过 / 失败",
                    cell: (item) =>
                      `${item.passed} / ${item.failed}（${percent(item.passRate)}）`,
                  },
                  {
                    id: "coverage",
                    header: "总覆盖率",
                    cell: (item) => percent(item.citationCoverageRate),
                  },
                  {
                    id: "layers",
                    header: "各层覆盖（ontology / terms / metrics / facts）",
                    cell: (item) => layerSummary(item),
                  },
                ]}
                empty={
                  <Box textAlign="center" color="text-body-secondary">
                    还没有落库的运行记录
                  </Box>
                }
              />
            </>
          )}
        </SpaceBetween>
      </Container>

      <Container
        header={<Header variant="h2">按题型的引用与拒答（F89）</Header>}
      >
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
