import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
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

import { ApiError, useApiClient } from "../../components/ApiClientProvider";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import {
  getEntity,
  getEntityProvenance,
  type EntityClass,
  type EntityDetail,
  type EntityEdge,
  type EntityProperty,
  type EntityProvenanceItem,
  type EntityProvenanceReport,
  type EntityRequired,
  type EntitySource,
  type ProvenanceField,
  type RelatedMetric,
} from "../../services/entities";

const errorText = (err: unknown): string => {
  if (err instanceof ApiError) {
    if (err.status === 404) return "该 IRI 在当前命名图中不存在（404）";
    return `${err.status} ${err.code}: ${err.message}`;
  }
  return err instanceof Error ? err.message : String(err);
};

const shorten = (value: string, max = 120): string =>
  value.length > max ? `${value.slice(0, max)}…` : value;

/** Percent-encoded Chinese ids are exact but unreadable; decode for display only. */
const pretty = (value: string): string => {
  if (!value.includes("%")) return value;
  try {
    const decoded = decodeURIComponent(value);
    return decoded === value ? value : decoded;
  } catch {
    return value;
  }
};

const badgeType = (state: string): "success" | "warning" | "error" | "info" => {
  if (state === "evidenced") return "success";
  if (state === "inferred") return "warning";
  if (state === "no-source") return "error";
  return "info";
};

const fieldBadgeType = (
  state: string,
): "success" | "warning" | "info" => {
  if (state === "evidenced") return "success";
  if (state === "inferred") return "warning";
  return "info";
};

export default function EntityPage() {
  const { namespaceId, entityId } = useParams<{
    namespaceId: string;
    entityId: string;
  }>();
  const api = useApiClient();
  const navigate = useNavigate();
  const [iriInput, setIriInput] = useState(entityId ?? "");
  const [detail, setDetail] = useState<EntityDetail | null>(null);
  const [prov, setProv] = useState<EntityProvenanceReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [provLoading, setProvLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useBreadcrumbTrail([{ text: "实体详情", href: "#" }]);

  const load = useCallback(
    async (iri: string) => {
      if (!iri) {
        setDetail(null);
        setProv(null);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const [nextDetail, nextProv] = await Promise.all([
          getEntity(api, iri),
          getEntityProvenance(api, iri).catch(() => null),
        ]);
        setDetail(nextDetail);
        setProv(nextProv);
      } catch (err) {
        setDetail(null);
        setProv(null);
        setError(errorText(err));
      } finally {
        setLoading(false);
      }
    },
    [api],
  );

  const reloadProvenance = useCallback(async () => {
    if (!detail) return;
    setProvLoading(true);
    try {
      setProv(await getEntityProvenance(api, detail.iri));
    } catch {
      setProv(null);
    } finally {
      setProvLoading(false);
    }
  }, [api, detail]);

  useEffect(() => {
    if (!entityId) {
      setDetail(null);
      return;
    }
    setIriInput(entityId);
    void load(entityId);
  }, [entityId, load]);

  const submit = () => {
    const iri = iriInput.trim();
    if (!namespaceId || !iri) return;
    navigate(
      `/namespaces/${namespaceId}/ontology/entities/${encodeURIComponent(iri)}`,
    );
  };

  const graphCount = useMemo(
    () => new Set(detail?.namedGraphs ?? []).size,
    [detail],
  );

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="GetEntity：按 IRI 读取一个 A-Box 实例；只读，不改账本"
      >
        实体详情
      </Header>

      <Container>
        <SpaceBetween size="m">
          <FormField
            label="实体 IRI"
            description="粘贴完整 IRI；中文名可用原样写法，后端会匹配已存在的编码形式"
          >
            <Input
              value={iriInput}
              onChange={({ detail: change }) => setIriInput(change.value)}
              placeholder="urn:coa:entity:…"
            />
          </FormField>
          <Button variant="primary" loading={loading} onClick={submit}>
            查询
          </Button>
        </SpaceBetween>
      </Container>

      {error && <Alert type="error">{error}</Alert>}

      {detail && (
        <>
          <Container
            header={
              <Header
                variant="h2"
                description={shorten(detail.iri, 200)}
                actions={
                  <StatusIndicator type={badgeType(detail.evidenceBadge.state)}>
                    {detail.evidenceBadge.label}
                  </StatusIndicator>
                }
              >
                {detail.label}
              </Header>
            }
          >
            <ColumnLayout columns={4} variant="text-grid">
              <div>
                <Box variant="awsui-key-label">所属命名图</Box>
                <Box>{graphCount} 个</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">直接类型</Box>
                <Box>{detail.classes.length} 个</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">事实条数</Box>
                <Box>{detail.provenance.count}</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">T-Box 版本</Box>
                <Box>
                  {detail.tbox
                    ? `${detail.tbox.semver ?? "-"}（${detail.tbox.versionId ?? "-"}` +
                      "）"
                    : "未绑定版本"}
                </Box>
              </div>
            </ColumnLayout>
            <Box margin={{ top: "m" }} variant="small" color="text-body-secondary">
              判定依据：{detail.evidenceBadge.basis || "-"}
              {detail.evidenceBadge.judge
                ? `；结论：${detail.evidenceBadge.judge}`
                : ""}
            </Box>
            {detail.namedGraphs.length > 0 && (
              <Box margin={{ top: "s" }}>
                <SpaceBetween size="xxs">
                  {detail.namedGraphs.map((graph) => (
                    <Box key={graph} variant="code">
                      {graph}
                    </Box>
                  ))}
                </SpaceBetween>
              </Box>
            )}
          </Container>

          <Table<EntityClass>
            items={detail.classes}
            header={
              <Header variant="h2" description="直接类型 + 父类链；推导标记为仅推理可见">
                类型
              </Header>
            }
            columnDefinitions={[
              { id: "label", header: "类", cell: (item) => item.label },
              {
                id: "iri",
                header: "IRI",
                cell: (item) => (
                  <Box variant="code">{shorten(pretty(item.iri), 80)}</Box>
                ),
              },
              {
                id: "chain",
                header: "父类链",
                cell: (item) =>
                  item.chain.length
                    ? item.chain.map((node) => node.label).join(" → ")
                    : "-",
              },
              {
                id: "instances",
                header: "实例数",
                cell: (item) => item.instanceCount,
              },
              {
                id: "inferred",
                header: "推导",
                cell: (item) => (item.inferredOnly ? "仅推理" : "显式"),
              },
            ]}
            empty={<Box textAlign="center">没有类型声明</Box>}
          />

          <Table<EntityProperty>
            items={detail.properties}
            header={
              <Header variant="h2" description="该实例上的取值；IRI 值可直接再查">
                属性
              </Header>
            }
            columnDefinitions={[
              { id: "label", header: "属性", cell: (item) => item.label },
              {
                id: "predicate",
                header: "IRI",
                cell: (item) => (
                  <Box variant="code">{shorten(pretty(item.property), 80)}</Box>
                ),
              },
              {
                id: "values",
                header: "值",
                cell: (item) =>
                  item.values.length === 0 ? (
                    "-"
                  ) : (
                    <SpaceBetween size="xxs">
                      {item.values.map((value, index) => (
                        <Box key={`${item.property}-${index}`}>
                          {value.kind === "iri" ? (
                            <Button
                              variant="inline-link"
                              onClick={() => {
                                if (!namespaceId) return;
                                navigate(
                                  `/namespaces/${namespaceId}/ontology/entities/${encodeURIComponent(
                                    value.iri ?? value.value,
                                  )}`,
                                );
                              }}
                            >
                              {shorten(pretty(value.iri ?? value.value), 80)}
                            </Button>
                          ) : (
                            shorten(value.value, 200)
                          )}
                        </Box>
                      ))}
                    </SpaceBetween>
                  ),
              },
            ]}
            empty={<Box textAlign="center">没有属性取值</Box>}
          />

          <Table<EntityRequired>
            items={detail.requiredProperties}
            header={
              <Header variant="h2" description="来自 T-Box 的 minCount 约束">
                必填属性
              </Header>
            }
            columnDefinitions={[
              { id: "label", header: "属性", cell: (item) => item.label },
              { id: "min", header: "minCount", cell: (item) => item.minCount },
              { id: "have", header: "实际", cell: (item) => item.valueCount },
              {
                id: "ok",
                header: "满足",
                cell: (item) => (
                  <StatusIndicator type={item.satisfied ? "success" : "error"}>
                    {item.satisfied ? "满足" : "缺失"}
                  </StatusIndicator>
                ),
              },
            ]}
            empty={<Box textAlign="center">该类型没有必填约束</Box>}
          />

          <Table<RelatedMetric>
            items={detail.relatedMetrics.items}
            header={
              <Header
                variant="h2"
                description={
                  detail.relatedMetrics.status === "bound"
                    ? `按绑定反查命中 ${detail.relatedMetrics.items.length} 个指标` +
                      (detail.relatedMetrics.matchBasis.length
                        ? `（${detail.relatedMetrics.matchBasis.join("、")}）`
                        : "")
                    : detail.relatedMetrics.reason ??
                      "类名未命中 metric_field_binding 的弱映射"
                }
              >
                相关指标
              </Header>
            }
            columnDefinitions={[
              {
                id: "metricId",
                header: "指标",
                cell: (item) => <Box variant="code">{item.metricId}</Box>,
              },
              { id: "name", header: "名称", cell: (item) => item.nameZh ?? "-" },
              { id: "domain", header: "领域", cell: (item) => item.domain ?? "-" },
              { id: "grain", header: "粒度", cell: (item) => item.grain ?? "-" },
              {
                id: "bindings",
                header: "字段绑定",
                cell: (item) =>
                  item.bindings.length === 0
                    ? "-"
                    : item.bindings
                        .map(
                          (binding) =>
                            `${binding.role ?? "-"}: ${
                              binding.factTable ?? "-"
                            }.${binding.entityColumn ?? "-"}`,
                        )
                        .join("；"),
              },
              {
                id: "publishable",
                header: "可发布",
                cell: (item) => (item.publishable ? "是" : "否"),
              },
            ]}
            empty={
              <Box textAlign="center">
                {detail.relatedMetrics.status === "bound"
                  ? "没有相关指标"
                  : "未绑定：需要先补类型的属性映射"}
              </Box>
            }
          />

          <Table<EntityProvenanceItem>
            items={detail.provenance.items}
            header={
              <Header
                variant="h2"
                description={
                  detail.provenance.unavailable
                    ? "事实账本读取不可用"
                    : "这些语句由哪条账本事实落图；带 documentId 的即原文来源"
                }
              >
                来源（事实账本）
              </Header>
            }
            columnDefinitions={[
              {
                id: "factId",
                header: "事实 ID",
                cell: (item) => <Box variant="code">{item.factId}</Box>,
              },
              {
                id: "predicate",
                header: "谓词",
                cell: (item) => (
                  <Box variant="code">{shorten(pretty(item.predicate), 60)}</Box>
                ),
              },
              {
                id: "object",
                header: "值",
                cell: (item) => shorten(pretty(item.object.value), 80),
              },
              { id: "state", header: "状态", cell: (item) => item.state },
              {
                id: "source",
                header: "来源",
                cell: (item) =>
                  item.documentId ? (
                    <Box variant="code">{shorten(item.documentId, 60)}</Box>
                  ) : (
                    `${item.sourceKind ?? "—"}（无文档）`
                  ),
              },
              {
                id: "conflict",
                header: "冲突",
                cell: (item) =>
                  item.conflict ? (
                    <StatusIndicator type="warning">待裁决</StatusIndicator>
                  ) : (
                    "-"
                  ),
              },
            ]}
            empty={<Box textAlign="center">账本里没有该主体的事实</Box>}
          />

          {prov && (
            <Table<ProvenanceField>
              items={prov.fields}
              header={
                <Header
                  variant="h2"
                  description={
                    `有溯源 ${prov.summary.evidenced} / 仅推理 ${prov.summary.inferred}` +
                    ` / 无 ${prov.summary.none}，覆盖率 ${Math.round(
                      prov.summary.coverageRate * 100,
                    )}%`
                  }
                  actions={
                    <Button
                      loading={provLoading}
                      onClick={() => void reloadProvenance()}
                    >
                      重新溯源
                    </Button>
                  }
                >
                  字段溯源
                </Header>
              }
              columnDefinitions={[
                { id: "label", header: "字段", cell: (item) => item.label },
                {
                  id: "value",
                  header: "值",
                  cell: (item) => shorten(pretty(item.valueText ?? "-"), 80),
                },
                {
                  id: "badge",
                  header: "徽标",
                  cell: (item) => (
                    <StatusIndicator
                      type={fieldBadgeType(item.badge.state)}
                    >
                      {item.badge.label}
                    </StatusIndicator>
                  ),
                },
                {
                  id: "basis",
                  header: "依据",
                  cell: (item) => shorten(item.badge.basis, 100),
                },
                {
                  id: "links",
                  header: "证据",
                  cell: (item) =>
                    item.links.length === 0
                      ? "-"
                      : item.links
                          .map((link) => link.documentId ?? link.ref ?? link.kind)
                          .join("、"),
                },
              ]}
              empty={<Box textAlign="center">没有可溯源的字段</Box>}
            />
          )}

          <Table<EntityEdge>
            items={detail.neighbors.edges}
            header={
              <Header
                variant="h2"
                description={
                  detail.neighbors.truncated
                    ? `已截断，仅显示前 ${detail.neighbors.edges.length} 条`
                    : `共 ${detail.neighbors.edges.length} 条`
                }
              >
                命名图与邻边
              </Header>
            }
            columnDefinitions={[
              {
                id: "s",
                header: "主语",
                cell: (item) => <Box variant="code">{shorten(pretty(item.s), 60)}</Box>,
              },
              {
                id: "p",
                header: "谓词",
                cell: (item) => <Box variant="code">{shorten(pretty(item.p), 60)}</Box>,
              },
              {
                id: "o",
                header: "宾语",
                cell: (item) => <Box variant="code">{shorten(pretty(item.o), 60)}</Box>,
              },
              { id: "graph", header: "命名图", cell: (item) => item.graph },
              {
                id: "inferred",
                header: "推导",
                cell: (item) => (item.inferred ? "是" : "否"),
              },
            ]}
            empty={<Box textAlign="center">没有邻边</Box>}
          />

          <Table<EntitySource>
            items={detail.sources}
            header={
              <Header variant="h2" description="图内 sourceRef / PROV 溯源链接">
                来源（图内）
              </Header>
            }
            columnDefinitions={[
              { id: "kind", header: "类型", cell: (item) => item.kind },
              {
                id: "ref",
                header: "引用",
                cell: (item) => <Box variant="code">{shorten(item.ref, 90)}</Box>,
              },
              {
                id: "text",
                header: "原文",
                cell: (item) => (item.text ? shorten(item.text, 160) : "-"),
              },
            ]}
            empty={<Box textAlign="center">图内没有 seeAlso / PROV 链接</Box>}
          />
        </>
      )}
    </SpaceBetween>
  );
}
