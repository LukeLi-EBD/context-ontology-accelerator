// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * System Health page — displays backend service health status.
 *
 * Route: /system-health
 *
 * Calls GET /system-health (proxied to ontology-engine /readiness) and
 * renders the status of each backend component with visual indicators.
 */
import React, { useCallback, useEffect, useState } from "react";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Container from "@cloudscape-design/components/container";
import FormField from "@cloudscape-design/components/form-field";
import Header from "@cloudscape-design/components/header";
import Input from "@cloudscape-design/components/input";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import type { StatusIndicatorProps } from "@cloudscape-design/components/status-indicator";

import { useApiClient, useCurrentNamespace } from "@components";
import { useAppI18n, type AppTranslate } from "../i18n/LocaleProvider";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import { verifyOntology } from "../services/ontology-lifecycle";

interface OntologyInductionHealth {
  graphStore?: string;
  vectorStore?: string;
  bedrockEmbeddings?: string;
  descriptionLlm?: string;
}

interface SystemHealthResponse {
  status: string;
  ontologyInduction?: OntologyInductionHealth;
  dynamodb?: string;
  neptuneKg?: string;
  opensearch?: string;
  /**
   * Local stack answers GetSystemHealth with real probes (PG / Oxigraph /
   * 8101 / 8091 / object store) instead of the AWS service names above.
   */
  components?: HealthComponent[];
  pointer?: {
    ok?: boolean;
    status?: string;
    versionId?: string | null;
    semver?: string | null;
    tripleCount?: number | null;
    warning?: string;
  } | null;
  namedGraphs?: number | null;
  schemaVersion?: SchemaVersion | null;
  checkedAt?: string;
}

interface SchemaVersion {
  codeVersion: number;
  dbVersion: number | null;
  consistent: boolean | null;
  source: string;
}

interface QualityCount {
  count: number | null;
  detail?: string | null;
}

interface ShaclReport {
  status: string;
  violations?: number | null;
  conforms?: boolean | null;
  detail?: string | null;
}

interface OntologySnapshot {
  tbox: { classes: number; objectProperties: number; datatypeProperties: number };
  abox: { instances: number; classesWithInstances: number };
  coverage: { classCoverage: number; unlabeledClasses: number };
  graphs: string[];
  source: string;
  sampledAt: string;
}

interface QualityValidation {
  orphanInstances: QualityCount;
  unlabeledClasses: QualityCount;
  shacl: ShaclReport;
  inferenceFailures: QualityCount;
  source: string;
  sampledAt: string;
}

interface ReasoningStatus {
  available: boolean;
  engine?: string | null;
  failures: QualityCount;
  detail?: string | null;
  source: string;
  sampledAt: string;
}

interface TripleExample {
  subject: string;
  predicate: string;
  object: string;
}

interface OntologyDiff {
  baselineGraph: string;
  targetGraph: string;
  counts: {
    addedTriples: number;
    removedTriples: number;
    addedClasses: number;
    removedClasses: number;
    addedProperties: number;
    removedProperties: number;
  };
  addedClasses: string[];
  removedClasses: string[];
  addedProperties: string[];
  removedProperties: string[];
  examples: { addedTriples: TripleExample[]; removedTriples: TripleExample[] };
  truncated: boolean;
  source: string;
  sampledAt: string;
}

interface HealthComponent {
  name: string;
  label?: string;
  status: string;
  detail?: string | null;
  url?: string;
}

type ComponentStatus = "ok" | "degraded" | "error" | "loading" | string;

function statusType(status: ComponentStatus): StatusIndicatorProps.Type {
  if (status === "ok") return "success";
  if (status === "loading") return "loading";
  if (status === "degraded") return "warning";
  return "error";
}

function statusLabel(status: ComponentStatus, t: AppTranslate): string {
  if (status === "ok") return t("Healthy");
  if (status === "loading") return t("Checking...");
  if (status === "degraded") return t("Degraded");
  if (status.startsWith("error:")) return status.replace("error: ", "");
  return status || t("Unknown");
}

interface HealthCardProps {
  title: string;
  description: string;
  status: ComponentStatus;
}

function HealthCard({ title, description, status }: HealthCardProps) {
  const { t } = useAppI18n();
  return (
    <Container>
      <SpaceBetween size="xs">
        <Box variant="h3">{title}</Box>
        <Box variant="small" color="text-body-secondary">
          {description}
        </Box>
        <StatusIndicator type={statusType(status)}>
          {statusLabel(status, t)}
        </StatusIndicator>
      </SpaceBetween>
    </Container>
  );
}

export function SystemHealthPage() {
  const { locale, t } = useAppI18n();
  useBreadcrumbTrail([
    { text: t("Administration") },
    { text: t("System Health") },
  ]);
  const apiClient = useApiClient();
  const { namespaceId: currentNamespaceId } = useCurrentNamespace();
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [verifyNamespace, setVerifyNamespace] = useState(currentNamespaceId ?? "");
  const [verifyOntologyId, setVerifyOntologyId] = useState("fsldm-local");
  const [verifyBusy, setVerifyBusy] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<Record<string, unknown> | null>(null);

  // Health-board blocks (F126–F131). Each one reports its own error so a
  // missing check does not blank the whole page.
  const [snapshot, setSnapshot] = useState<OntologySnapshot | null>(null);
  const [snapshotError, setSnapshotError] = useState<string | null>(null);
  const [quality, setQuality] = useState<QualityValidation | null>(null);
  const [qualityError, setQualityError] = useState<string | null>(null);
  const [reasoning, setReasoning] = useState<ReasoningStatus | null>(null);
  const [diffFrom, setDiffFrom] = useState("");
  const [diffTo, setDiffTo] = useState("");
  const [diffBusy, setDiffBusy] = useState(false);
  const [diffError, setDiffError] = useState<string | null>(null);
  const [diff, setDiff] = useState<OntologyDiff | null>(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<SystemHealthResponse>("/system-health");
      setHealth(data);
      setLastChecked(new Date());
    } catch (e) {
      setError(
        e instanceof Error ? e.message : t("Failed to fetch system health"),
      );
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, [apiClient, t]);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  const fetchHealthBoard = useCallback(async () => {
    if (!currentNamespaceId) {
      return;
    }
    const base = `/namespaces/${encodeURIComponent(currentNamespaceId)}/graph`;
    setSnapshotError(null);
    setQualityError(null);

    const [snapshotResult, qualityResult, reasoningResult] = await Promise.allSettled([
      apiClient.get<OntologySnapshot>(`${base}/snapshot`),
      apiClient.post<QualityValidation>(`${base}/validate`, {}),
      apiClient.get<ReasoningStatus>(`${base}/reasoning`),
    ]);

    if (snapshotResult.status === "fulfilled") {
      setSnapshot(snapshotResult.value);
      const graphs = snapshotResult.value.graphs;
      setDiffFrom((prev) => prev || graphs[0] || "");
      setDiffTo((prev) => prev || graphs[graphs.length - 1] || graphs[0] || "");
    } else {
      setSnapshot(null);
      setSnapshotError(String(snapshotResult.reason));
    }

    if (qualityResult.status === "fulfilled") {
      setQuality(qualityResult.value);
    } else {
      setQuality(null);
      setQualityError(String(qualityResult.reason));
    }

    setReasoning(reasoningResult.status === "fulfilled" ? reasoningResult.value : null);
  }, [apiClient, currentNamespaceId]);

  useEffect(() => {
    void fetchHealthBoard();
  }, [fetchHealthBoard]);

  const runDiff = async () => {
    if (!currentNamespaceId) {
      return;
    }
    if (!diffFrom.trim() || !diffTo.trim()) {
      setDiffError("from 与 to 都必须填写（填写命名图 IRI）");
      return;
    }
    setDiffBusy(true);
    setDiffError(null);
    try {
      const query = new URLSearchParams({ from: diffFrom.trim(), to: diffTo.trim(), limit: "20" });
      const result = await apiClient.get<OntologyDiff>(
        `/namespaces/${encodeURIComponent(currentNamespaceId)}/graph/diff?${query.toString()}`,
      );
      setDiff(result);
    } catch (e) {
      setDiff(null);
      setDiffError(e instanceof Error ? e.message : String(e));
    } finally {
      setDiffBusy(false);
    }
  };

  useEffect(() => {
    if (!verifyNamespace && currentNamespaceId) {
      setVerifyNamespace(currentNamespaceId);
    }
  }, [currentNamespaceId, verifyNamespace]);

  const doVerifyOntology = async () => {
    if (!verifyNamespace.trim() || !verifyOntologyId.trim()) {
      setVerifyError("namespaceId 与 ontologyId 都必须填写");
      return;
    }
    setVerifyBusy(true);
    setVerifyError(null);
    try {
      const result = await verifyOntology(
        apiClient,
        verifyNamespace.trim(),
        verifyOntologyId.trim(),
      );
      setVerifyResult(result);
    } catch (e) {
      setVerifyResult(null);
      setVerifyError(e instanceof Error ? e.message : String(e));
    } finally {
      setVerifyBusy(false);
    }
  };

  const overallStatus: ComponentStatus = loading
    ? "loading"
    : error
      ? "error"
      : (health?.status ?? "error");

  // Local stack reports probed components; AWS deployments report fixed names.
  const localComponents = health?.components ?? [];

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description={t(
          "Real-time health status of all backend storage and AI services",
        )}
        actions={
          <Button iconName="refresh" onClick={fetchHealth} loading={loading}>
            {t("Refresh")}
          </Button>
        }
      >
        {t("System Health")}
      </Header>

      <Container
        header={
          <Header
            variant="h2"
            description={
              lastChecked
                ? t("Last checked: {time}", {
                    time: lastChecked.toLocaleTimeString(locale),
                  })
                : undefined
            }
          >
            {t("Overall Status")}
          </Header>
        }
      >
        <StatusIndicator type={statusType(overallStatus)}>
          {overallStatus === "ok"
            ? t("All systems operational")
            : overallStatus === "loading"
              ? t("Checking backend health...")
              : error
                ? t("Unreachable: {error}", { error })
                : t("One or more systems degraded")}
        </StatusIndicator>
      </Container>

      {localComponents.length > 0 ? (
        <>
          <Header
            variant="h2"
            description="本地栈逐项探活：哪一项不可用会在详情列写明原因"
          >
            组件探活
          </Header>

          <Table<HealthComponent>
            items={localComponents}
            columnDefinitions={[
              {
                id: "label",
                header: "组件",
                cell: (item) => item.label ?? item.name,
              },
              {
                id: "status",
                header: "状态",
                cell: (item) => (
                  <StatusIndicator type={statusType(item.status)}>
                    {statusLabel(item.status, t)}
                  </StatusIndicator>
                ),
              },
              {
                id: "detail",
                header: "详情",
                cell: (item) => item.detail ?? item.url ?? "-",
              },
            ]}
            empty={<Box textAlign="center">没有探活项</Box>}
          />

          <Container
            header={
              <Header variant="h2" description="tbox/current 指针与图规模">
                本体状态
              </Header>
            }
          >
            <ColumnLayout columns={3}>
              <div>
                <Box variant="awsui-key-label">T-Box 版本</Box>
                <Box>
                  {health?.pointer?.semver ?? "—"}
                  {health?.pointer?.status ? `（${health.pointer.status}）` : ""}
                </Box>
              </div>
              <div>
                <Box variant="awsui-key-label">命名图</Box>
                <Box>{health?.namedGraphs ?? "—"}</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">检查时间</Box>
                <Box>
                  {health?.checkedAt
                    ? new Date(health.checkedAt).toLocaleString(locale)
                    : "—"}
                </Box>
              </div>
            </ColumnLayout>
          </Container>
        </>
      ) : (
        <>
      <Header variant="h2">{t("Storage Backends")}</Header>

      <ColumnLayout columns={3}>
        <HealthCard
          title="DynamoDB"
          description={t("Sources and metadata table")}
          status={loading ? "loading" : (health?.dynamodb ?? "unknown")}
        />
        <HealthCard
          title="Neptune KG"
          description={t("GraphRAG knowledge graph (Gremlin/openCypher)")}
          status={loading ? "loading" : (health?.neptuneKg ?? "unknown")}
        />
        <HealthCard
          title="OpenSearch Serverless"
          description={t("Vector embeddings collection (AOSS)")}
          status={loading ? "loading" : (health?.opensearch ?? "unknown")}
        />
      </ColumnLayout>

      <Header variant="h2">{t("Ontology Induction")}</Header>

      <ColumnLayout columns={2}>
        <HealthCard
          title={t("Ontology Graph Store")}
          description={t("Neptune DB — RDF/OWL ontology triples")}
          status={
            loading
              ? "loading"
              : (health?.ontologyInduction?.graphStore ?? "unknown")
          }
        />
        <HealthCard
          title={t("Ontology Vector Store")}
          description={t(
            "OpenSearch — ontology embeddings and semantic search",
          )}
          status={
            loading
              ? "loading"
              : (health?.ontologyInduction?.vectorStore ?? "unknown")
          }
        />
        <HealthCard
          title={t("Bedrock Embeddings")}
          description={t(
            "Amazon Bedrock — text embedding model for vector generation",
          )}
          status={
            loading
              ? "loading"
              : (health?.ontologyInduction?.bedrockEmbeddings ?? "unknown")
          }
        />
        <HealthCard
          title={t("Description LLM")}
          description={t(
            "Amazon Bedrock Converse — LLM for entity descriptions and induction",
          )}
          status={
            loading
              ? "loading"
              : (health?.ontologyInduction?.descriptionLlm ?? "unknown")
          }
        />
      </ColumnLayout>
        </>
      )}

      <Header variant="h2" description="T-Box 声明与实际被使用的比例；不做采样，按命名图聚合">
        覆盖与质量
      </Header>

      {!currentNamespaceId && (
        <Alert type="warning" header="未选择命名空间">
          覆盖、质量与 diff 都按命名空间读取，请先在顶部选择命名空间。
        </Alert>
      )}

      <Container
        header={
          <Header variant="h3" description="覆盖率 = 有实例的类 / 已声明的类">
            F126 覆盖率（T-Box vs A-Box）
          </Header>
        }
      >
        {snapshotError ? (
          <Alert type="error" header="覆盖率读取失败">
            {snapshotError}
          </Alert>
        ) : (
          <SpaceBetween size="m">
            <ColumnLayout columns={4}>
              <div>
                <Box variant="awsui-key-label">已声明类</Box>
                <Box>{snapshot ? snapshot.tbox.classes : "—"}</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">对象属性 / 数据类型属性</Box>
                <Box>
                  {snapshot
                    ? `${snapshot.tbox.objectProperties} / ${snapshot.tbox.datatypeProperties}`
                    : "—"}
                </Box>
              </div>
              <div>
                <Box variant="awsui-key-label">有实例的类</Box>
                <Box>
                  {snapshot
                    ? `${snapshot.abox.classesWithInstances}（覆盖 ${(snapshot.coverage.classCoverage * 100).toFixed(1)}%）`
                    : "—"}
                </Box>
              </div>
              <div>
                <Box variant="awsui-key-label">A-Box 实例数</Box>
                <Box>{snapshot ? snapshot.abox.instances : "—"}</Box>
              </div>
            </ColumnLayout>
            {snapshot && (
              <Box variant="small" color="text-body-secondary">
                来源：{snapshot.source}；抽样 {snapshot.sampledAt}
              </Box>
            )}
          </SpaceBetween>
        )}
      </Container>

      <Container
        header={
          <Header variant="h3" description="产品有、本地没接的能力标「待本地化」，不折算成 0，也不记成「不适用」">
            F127 质量与推理
          </Header>
        }
      >
        <SpaceBetween size="m">
          {qualityError && (
            <Alert type="error" header="质量检查失败">
              {qualityError}
            </Alert>
          )}
          <Table
            items={
              quality
                ? [
                    {
                      name: "孤实例",
                      value: quality.orphanInstances.count,
                      detail: quality.orphanInstances.detail ?? "",
                    },
                    {
                      name: "无标签类",
                      value: quality.unlabeledClasses.count,
                      detail: quality.unlabeledClasses.detail ?? "",
                    },
                    {
                      name: "SHACL",
                      value:
                        quality.shacl.status === "skipped"
                          ? "待本地化（本地无 shapes）"
                          : quality.shacl.status,
                      detail: quality.shacl.detail ?? "",
                    },
                    {
                      name: "推理失败",
                      value: quality.inferenceFailures.count,
                      detail: !reasoning
                        ? (quality.inferenceFailures.detail ?? "推理状态不可读")
                        : reasoning.available
                          ? `推理引擎 ${reasoning.engine ?? "unknown"}`
                          : "待本地化（本地未接 reasoner）",
                    },
                  ]
                : []
            }
            columnDefinitions={[
              { id: "name", header: "检查项", cell: (item) => item.name },
              {
                id: "value",
                header: "结果",
                cell: (item) => (item.value === null || item.value === undefined ? "—" : item.value),
              },
              { id: "detail", header: "口径 / 原因", cell: (item) => item.detail || "—" },
            ]}
            empty={
              <Box textAlign="center">
                {currentNamespaceId ? "暂无可展示的质量指标" : "未选择命名空间"}
              </Box>
            }
          />
          {quality && (
            <Box variant="small" color="text-body-secondary">
              来源：{quality.source}；抽样 {quality.sampledAt}
            </Box>
          )}
          {reasoning && (
            <Box variant="small" color="text-body-secondary">
              推理状态：{reasoning.available ? `可用（${reasoning.engine}）` : "不可用"}。
              {reasoning.detail ?? ""} 来源：{reasoning.source}
            </Box>
          )}
        </SpaceBetween>
      </Container>

      <Container
        header={
          <Header variant="h3" description="代码期待的迁移版本与数据库实际版本">
            F128 迁移与 schema 一致性
          </Header>
        }
      >
        <ColumnLayout columns={3}>
          <div>
            <Box variant="awsui-key-label">代码版本</Box>
            <Box>{health?.schemaVersion?.codeVersion ?? "—"}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">数据库版本</Box>
            <Box>{health?.schemaVersion?.dbVersion ?? "—"}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">一致性</Box>
            <Box>
              {health?.schemaVersion?.consistent === true
                ? "一致"
                : health?.schemaVersion?.consistent === false
                  ? "不一致"
                  : "—"}
            </Box>
          </div>
        </ColumnLayout>
      </Container>

      <Container
        header={
          <Header variant="h3" description="两个命名图 IRI，from 为基线，to 为目标">
            F129 / F130 本体 diff
          </Header>
        }
      >
        <SpaceBetween size="m">
          <FormField label="from（基线命名图 IRI）">
            <Input
              value={diffFrom}
              onChange={({ detail }) => setDiffFrom(detail.value)}
              placeholder="https://coa.local/graph/<namespaceId>/..."
            />
          </FormField>
          <FormField label="to（目标命名图 IRI）">
            <Input
              value={diffTo}
              onChange={({ detail }) => setDiffTo(detail.value)}
              placeholder="https://coa.local/graph/<namespaceId>/..."
            />
          </FormField>
          {snapshot && snapshot.graphs.length > 0 && (
            <Box variant="small" color="text-body-secondary">
              本命名图可选值：{snapshot.graphs.join("、")}
            </Box>
          )}
          <Button variant="primary" loading={diffBusy} onClick={() => void runDiff()}>
            计算 diff
          </Button>
          {diffError && (
            <Alert type="error" header="diff 失败">
              {diffError}
            </Alert>
          )}
          {diff && (
            <SpaceBetween size="m">
              <ColumnLayout columns={6}>
                <div>
                  <Box variant="awsui-key-label">新增三元组</Box>
                  <Box>{diff.counts.addedTriples}</Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">删除三元组</Box>
                  <Box>{diff.counts.removedTriples}</Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">新增类</Box>
                  <Box>{diff.counts.addedClasses}</Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">删除类</Box>
                  <Box>{diff.counts.removedClasses}</Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">新增属性</Box>
                  <Box>{diff.counts.addedProperties}</Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">删除属性</Box>
                  <Box>{diff.counts.removedProperties}</Box>
                </div>
              </ColumnLayout>
              {diff.truncated && (
                <Alert type="info">
                  样本已按 limit 截断，计数仍是全量（未截断）。
                </Alert>
              )}
              <Table
                items={Array.from(
                  {
                    length: Math.max(diff.addedClasses.length, diff.removedClasses.length),
                  },
                  (_, index) => ({
                    added: diff.addedClasses[index] ?? "—",
                    removed: diff.removedClasses[index] ?? "—",
                  }),
                )}
                columnDefinitions={[
                  { id: "added", header: "新增类（样本）", cell: (item) => item.added },
                  { id: "removed", header: "删除类（样本）", cell: (item) => item.removed },
                ]}
                empty={<Box textAlign="center">类没有增删</Box>}
              />
              <Table
                items={Array.from(
                  {
                    length: Math.max(diff.addedProperties.length, diff.removedProperties.length),
                  },
                  (_, index) => ({
                    added: diff.addedProperties[index] ?? "—",
                    removed: diff.removedProperties[index] ?? "—",
                  }),
                )}
                columnDefinitions={[
                  { id: "added", header: "新增属性（样本）", cell: (item) => item.added },
                  { id: "removed", header: "删除属性（样本）", cell: (item) => item.removed },
                ]}
                empty={<Box textAlign="center">属性没有增删</Box>}
              />
              <Table
                items={[
                  ...diff.examples.addedTriples.map((item) => ({ side: "新增", ...item })),
                  ...diff.examples.removedTriples.map((item) => ({ side: "删除", ...item })),
                ]}
                columnDefinitions={[
                  { id: "side", header: "方向", cell: (item) => item.side },
                  { id: "subject", header: "subject", cell: (item) => item.subject },
                  { id: "predicate", header: "predicate", cell: (item) => item.predicate },
                  { id: "object", header: "object", cell: (item) => item.object },
                ]}
                empty={<Box textAlign="center">没有三元组样本</Box>}
              />
              <Box variant="small" color="text-body-secondary">
                来源：{diff.source}；抽样 {diff.sampledAt}
              </Box>
            </SpaceBetween>
          )}
        </SpaceBetween>
      </Container>

      <Container
        header={
          <Header variant="h3" description="每个区块的数据从哪来，跳转排查时按这张表找">
            F131 数据来源说明
          </Header>
        }
      >
        <Table
          items={[
            { block: "组件探活", source: "GetSystemHealth：8099 逐项探活（PG / Oxigraph / 8101 / 8091 / 对象存储）" },
            { block: "覆盖率", source: snapshot?.source ?? "—" },
            { block: "质量与推理", source: quality?.source ?? "—" },
            { block: "推理状态", source: reasoning?.source ?? "—" },
            { block: "迁移一致性", source: health?.schemaVersion?.source ?? "—" },
            {
              block: "本体 diff",
              source: diff?.source ?? "GetOntologyDiff：SPARQL MINUS（未计算时无结果）",
            },
          ]}
          columnDefinitions={[
            { id: "block", header: "区块", cell: (item) => item.block },
            { id: "source", header: "数据来源", cell: (item) => item.source },
          ]}
        />
      </Container>

      <Header variant="h2">本体质量</Header>

      <Container
        header={
          <Header
            variant="h2"
            description="VerifyOntology：重算 audit 哈希链，报告断链或缺失事件"
          >
            审计链校验
          </Header>
        }
      >
        <SpaceBetween size="m">
          <FormField label="namespaceId">
            <Input
              value={verifyNamespace}
              onChange={({ detail }) => setVerifyNamespace(detail.value)}
            />
          </FormField>
          <FormField label="ontologyId">
            <Input
              value={verifyOntologyId}
              onChange={({ detail }) => setVerifyOntologyId(detail.value)}
            />
          </FormField>
          <Button variant="primary" loading={verifyBusy} onClick={() => void doVerifyOntology()}>
            校验审计链
          </Button>
          {verifyError && (
            <Alert type="error" header="校验失败">
              {verifyError}
            </Alert>
          )}
          {verifyResult && (
            <Box variant="code">
              <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                {JSON.stringify(verifyResult, null, 2)}
              </pre>
            </Box>
          )}
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
