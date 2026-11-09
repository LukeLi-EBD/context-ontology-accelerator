// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * T-Box lifecycle console: register a version, open a proposal, review it,
 * publish, and roll back. This page exists to exercise the chain end to end
 * (09 §5.6) — each action records the response it got, so a reviewer can see
 * what the backend returned without opening devtools.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Container from "@cloudscape-design/components/container";
import FormField from "@cloudscape-design/components/form-field";
import Header from "@cloudscape-design/components/header";
import Input from "@cloudscape-design/components/input";
import KeyValuePairs from "@cloudscape-design/components/key-value-pairs";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import Textarea from "@cloudscape-design/components/textarea";
import {
  useApiClient,
  ApiError,
} from "@components/ApiClientProvider";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import {
  diffOntologyVersions,
  exportOntologyVersion,
  getOntologyVersion,
  listOntologyProposals,
  listOntologyVersions,
  proposeOntologyVersion,
  publishOntologyVersion,
  registerOntologyVersion,
  reviewOntologyProposal,
  rollbackOntology,
  type OntologyDiff,
  type OntologyProposal,
  type OntologyVersion,
  type OntologyVersionDetail,
} from "../../services/ontology-lifecycle";

const SAMPLE_TTL = `@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://coa.local/ont/chain> a owl:Ontology .
<https://coa.local/ont/chain#Loan> a owl:Class ; rdfs:label "Loan" .
`;

interface StepLog {
  id: string;
  step: string;
  detail: string;
  ok: boolean;
  at: string;
}

function statusType(status: string) {
  if (status === "published") return "success" as const;
  if (status === "approved") return "in-progress" as const;
  if (status === "superseded" || status === "deprecated") return "stopped" as const;
  return "pending" as const;
}

// The kernel's proposal state machine starts at "proposed"; the contract also
// calls it "pending". Accept both so the review buttons stay live.
const OPEN_PROPOSAL = new Set(["proposed", "pending", "open"]);

function errorText(err: unknown): string {
  if (err instanceof ApiError) return `${err.status} ${err.code}: ${err.message}`;
  return err instanceof Error ? err.message : String(err);
}

export function OntologyVersionsPage() {
  const { namespaceId } = useParams();
  const api = useApiClient();
  const [ontologyId, setOntologyId] = useState("fsldm-local");
  const [appliedOntologyId, setAppliedOntologyId] = useState("fsldm-local");
  const [ttl, setTtl] = useState(SAMPLE_TTL);
  const [versions, setVersions] = useState<OntologyVersion[]>([]);
  const [proposals, setProposals] = useState<OntologyProposal[]>([]);
  const [pointer, setPointer] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [log, setLog] = useState<StepLog[]>([]);
  const [detail, setDetail] = useState<OntologyVersionDetail | null>(null);
  const [diff, setDiff] = useState<OntologyDiff | null>(null);
  const [detailBusy, setDetailBusy] = useState<string | null>(null);

  useBreadcrumbTrail(
    namespaceId
      ? [
          { text: "Ontology", href: `/namespaces/${namespaceId}/ontology`, namespaceId },
          { text: "版本与发布" },
        ]
      : undefined,
  );

  const record = useCallback((step: string, detail: string, ok: boolean) => {
    setLog((prev) => [
      {
        id: `${Date.now()}-${prev.length}`,
        step,
        detail,
        ok,
        at: new Date().toLocaleTimeString(),
      },
      ...prev,
    ]);
  }, []);

  const refresh = useCallback(async () => {
    if (!namespaceId) return;
    setLoading(true);
    setError(null);
    try {
      const [versionList, proposalList] = await Promise.all([
        listOntologyVersions(api, namespaceId, appliedOntologyId),
        listOntologyProposals(api, namespaceId, appliedOntologyId),
      ]);
      setVersions(versionList.items ?? []);
      setPointer(versionList.pointer?.versionId);
      setProposals(proposalList.items ?? []);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setLoading(false);
    }
  }, [api, namespaceId, appliedOntologyId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const run = useCallback(
    async (key: string, step: string, fn: () => Promise<string>) => {
      setBusy(key);
      setError(null);
      try {
        const detail = await fn();
        record(step, detail, true);
        await refresh();
      } catch (err) {
        const message = errorText(err);
        setError(`${step} 失败：${message}`);
        record(step, message, false);
      } finally {
        setBusy(null);
      }
    },
    [record, refresh],
  );

  const register = () =>
    run("register", "① 注册版本", async () => {
      const created = await registerOntologyVersion(api, namespaceId!, appliedOntologyId, {
        content: ttl,
        changeSummary: `UI register ${new Date().toISOString()}`,
      });
      return `versionId=${created.versionId} semver=${created.semver} status=${created.status} triples=${created.triples ?? "?"}`;
    });

  const propose = (version: OntologyVersion) =>
    run(`propose-${version.id}`, "② 创建提案", async () => {
      const created = await proposeOntologyVersion(api, namespaceId!, appliedOntologyId, {
        versionId: version.id,
        rationale: `UI proposal for ${version.semver}`,
        againstVersion: pointer,
      });
      return `proposalId=${created.proposalId ?? (created as unknown as { id: string }).id} against=${pointer ?? "(none)"}`;
    });

  const review = (proposal: OntologyProposal, decision: "APPROVE" | "REJECT") =>
    run(`review-${proposal.proposalId}-${decision}`, `③ 评审 ${decision}`, async () => {
      const res = await reviewOntologyProposal(
        api,
        namespaceId!,
        appliedOntologyId,
        proposal.proposalId,
        decision,
        `UI ${decision.toLowerCase()}`,
      );
      return `proposalId=${res.proposalId} result=${JSON.stringify(res)}`;
    });

  const publish = (version: OntologyVersion) =>
    run(`publish-${version.id}`, "④ 发布", async () => {
      const approved = proposals.find(
        (p) => p.versionId === version.id && p.status === "approved",
      );
      if (!approved) {
        throw new Error("该版本还没有已通过的提案，先执行 ②③");
      }
      const res = await publishOntologyVersion(api, namespaceId!, appliedOntologyId, {
        versionId: version.id,
        proposalId: approved.proposalId,
        expectedVersionId: pointer,
        reason: "UI publish",
      });
      return `publishedVersion=${res.publishedVersion} semver=${res.semver}`;
    });

  const rollback = (version: OntologyVersion) =>
    run(`rollback-${version.id}`, "⑤ 回滚", async () => {
      const res = await rollbackOntology(api, namespaceId!, appliedOntologyId, {
        targetVersionId: version.id,
        reason: "UI rollback",
      });
      return `publishedVersion=${res.publishedVersion} replaced=${res.replacedVersionId}`;
    });

  const openDetail = useCallback(
    async (version: OntologyVersion) => {
      if (!namespaceId) return;
      setDetailBusy(`detail-${version.id}`);
      setError(null);
      try {
        const against = version.id === pointer ? undefined : pointer;
        const [loaded, compared] = await Promise.all([
          getOntologyVersion(api, namespaceId, appliedOntologyId, version.id),
          diffOntologyVersions(
            api,
            namespaceId,
            appliedOntologyId,
            version.id,
            against,
          ),
        ]);
        setDetail(loaded);
        setDiff(compared);
        record(
          "⑥ 版本详情 / 差异",
          `versionId=${loaded.versionId} against=${against ?? "(auto)"} ` +
            `+${compared.summary?.addedTriples ?? "?"}/-${compared.summary?.removedTriples ?? "?"} ` +
            `breaking=${String(compared.breaking ?? false)}`,
          true,
        );
      } catch (err) {
        setDetail(null);
        setDiff(null);
        setError(`查看详情失败：${errorText(err)}`);
      } finally {
        setDetailBusy(null);
      }
    },
    [api, namespaceId, appliedOntologyId, pointer, record],
  );

  const download = useCallback(async () => {
    if (!namespaceId || !detail) return;
    setDetailBusy("export");
    setError(null);
    try {
      const text = await exportOntologyVersion(
        api,
        namespaceId,
        appliedOntologyId,
        detail.versionId,
      );
      const blob = new Blob([text], { type: "text/turtle" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${detail.versionId}.ttl`;
      link.click();
      URL.revokeObjectURL(url);
      record("⑦ 导出", `versionId=${detail.versionId} bytes=${text.length}`, true);
    } catch (err) {
      setError(`导出失败：${errorText(err)}`);
      record("⑦ 导出", errorText(err), false);
    } finally {
      setDetailBusy(null);
    }
  }, [api, namespaceId, appliedOntologyId, detail, record]);

  const iriList = (title: string, values?: string[]) => (
    <Box>
      <Box variant="awsui-key-label">{title}</Box>
      {values && values.length > 0 ? (
        <SpaceBetween size="xxs">
          {values.slice(0, 12).map((iri) => (
            <Box key={iri} variant="code">
              {iri}
            </Box>
          ))}
        </SpaceBetween>
      ) : (
        <Box color="text-status-inactive">无</Box>
      )}
    </Box>
  );

  const logColumns = useMemo(
    () => [
      { id: "time", header: "时间", cell: (item: StepLog) => item.at },
      { id: "step", header: "步骤", cell: (item: StepLog) => item.step },
      { id: "result", header: "服务端返回", cell: (item: StepLog) => item.detail },
      {
        id: "ok",
        header: "结果",
        cell: (item: StepLog) => (
          <StatusIndicator type={item.ok ? "success" : "error"}>
            {item.ok ? "2xx" : "失败"}
          </StatusIndicator>
        ),
      },
    ],
    [],
  );

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="本体 T-Box 从「提案」到「生效」的完整链路。每一步都会把后端响应留在下方操作记录里。"
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={() => void refresh()} loading={loading}>
              刷新
            </Button>
          </SpaceBetween>
        }
      >
        版本与发布
      </Header>

      {error && (
        <Alert type="error" header="请求失败">
          {error}
        </Alert>
      )}

      <Container header={<Header variant="h2">当前发布版本</Header>}>
        <Box>{pointer ?? "尚未发布任何版本"}</Box>
      </Container>

      <Container
        header={
          <Header
            variant="h2"
            description="ontologyId 作为目标命名空间传给注册接口；默认 fsldm-local。"
          >
            ① 注册版本（导入 TTL 生成草稿）
          </Header>
        }
      >
        <SpaceBetween size="m">
          <FormField label="ontologyId">
            <Input value={ontologyId} onChange={({ detail }) => setOntologyId(detail.value)} />
          </FormField>
          <FormField label="Turtle 内容">
            <Textarea
              value={ttl}
              onChange={({ detail }) => setTtl(detail.value)}
              rows={8}
            />
          </FormField>
          <SpaceBetween direction="horizontal" size="xs">
            <Button
              variant="primary"
              loading={busy === "register"}
              onClick={() => {
                setAppliedOntologyId(ontologyId);
                register();
              }}
            >
              注册草稿版本
            </Button>
          </SpaceBetween>
        </SpaceBetween>
      </Container>

      <Table
        header={
          <Header
            variant="h2"
            counter={`(${versions.length})`}
            description="② 为草稿发起提案 → ③ 评审 → ④ 发布 → ⑤ 回滚到任意版本"
          >
            版本
          </Header>
        }
        loading={loading}
        loadingText="加载版本"
        items={versions}
        columnDefinitions={[
          { id: "semver", header: "semver", cell: (v: OntologyVersion) => v.semver },
          { id: "id", header: "versionId", cell: (v: OntologyVersion) => v.id },
          {
            id: "status",
            header: "状态",
            cell: (v: OntologyVersion) => (
              <StatusIndicator type={statusType(v.status)}>{v.status}</StatusIndicator>
            ),
          },
          { id: "triples", header: "三元组", cell: (v: OntologyVersion) => v.tripleCount ?? "-" },
          {
            id: "created",
            header: "创建时间",
            cell: (v: OntologyVersion) => v.createdAt ?? "-",
          },
          {
            id: "detail",
            header: "⑥ 详情",
            cell: (v: OntologyVersion) => (
              <Button
                loading={detailBusy === `detail-${v.id}`}
                onClick={() => void openDetail(v)}
              >
                详情 / 差异
              </Button>
            ),
          },
          {
            id: "actions",
            header: "操作",
            cell: (v: OntologyVersion) => (
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  disabled={v.status !== "draft"}
                  loading={busy === `propose-${v.id}`}
                  onClick={() => void propose(v)}
                >
                  ② 发起提案
                </Button>
                <Button
                  disabled={v.status !== "approved"}
                  loading={busy === `publish-${v.id}`}
                  onClick={() => void publish(v)}
                >
                  ④ 发布
                </Button>
                <Button
                  disabled={v.id === pointer}
                  loading={busy === `rollback-${v.id}`}
                  onClick={() => void rollback(v)}
                >
                  ⑤ 回滚到此版本
                </Button>
              </SpaceBetween>
            ),
          },
        ]}
        empty={
          <Box textAlign="center" color="inherit">
            还没有版本，先在上方注册一个。
          </Box>
        }
      />

      <Table
        header={
          <Header variant="h2" counter={`(${proposals.length})`}>
            提案
          </Header>
        }
        loading={loading}
        loadingText="加载提案"
        items={proposals}
        columnDefinitions={[
          { id: "id", header: "proposalId", cell: (p: OntologyProposal) => p.proposalId },
          { id: "version", header: "versionId", cell: (p: OntologyProposal) => p.versionId },
          {
            id: "status",
            header: "状态",
            cell: (p: OntologyProposal) => (
              <StatusIndicator type={statusType(p.status)}>{p.status}</StatusIndicator>
            ),
          },
          { id: "summary", header: "变更摘要", cell: (p: OntologyProposal) => p.changeSummary ?? "-" },
          {
            id: "actions",
            header: "③ 评审",
            cell: (p: OntologyProposal) => (
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  variant="primary"
                  disabled={!OPEN_PROPOSAL.has(p.status)}
                  loading={busy === `review-${p.proposalId}-APPROVE`}
                  onClick={() => void review(p, "APPROVE")}
                >
                  通过
                </Button>
                <Button
                  disabled={!OPEN_PROPOSAL.has(p.status)}
                  loading={busy === `review-${p.proposalId}-REJECT`}
                  onClick={() => void review(p, "REJECT")}
                >
                  驳回
                </Button>
              </SpaceBetween>
            ),
          },
        ]}
        empty={<Box textAlign="center" color="inherit">还没有提案。</Box>}
      />

      {detail && (
        <Container
          header={
            <Header
              variant="h2"
              actions={
                <Button loading={detailBusy === "export"} onClick={() => void download()}>
                  ⑦ 导出 TTL
                </Button>
              }
            >
              版本详情
            </Header>
          }
        >
          <KeyValuePairs
            columns={3}
            items={[
              { label: "versionId", value: detail.versionId },
              { label: "semver", value: detail.semver },
              {
                label: "状态",
                value: <StatusIndicator type={statusType(detail.status)}>{detail.status}</StatusIndicator>,
              },
              { label: "contentHash", value: detail.contentHash ?? "-" },
              { label: "三元组", value: String(detail.statementCount ?? detail.tripleCount ?? "-") },
              { label: "图三元组", value: String(detail.graphTripleCount ?? "-") },
              { label: "graphUri", value: detail.graphUri ?? detail.graph ?? "-" },
              { label: "创建时间", value: detail.createdAt ?? "-" },
              { label: "发布时间", value: detail.publishedAt ?? "-" },
            ]}
          />
        </Container>
      )}

      {diff && (
        <Container
          header={
            <Header
              variant="h2"
              description={`from ${diff.from ?? "(none)"} → to ${diff.to ?? "?"}`}
            >
              版本差异
            </Header>
          }
        >
          <SpaceBetween size="m">
            {diff.breaking && (
              <Alert type="warning" header="包含破坏性变更">
                发布该版本必须显式确认（`acknowledgeBreaking`），否则会被
                `E_ONTOLOGY_BREAKING` 拦住。
                {(diff.breakingItems ?? []).map((item) => (
                  <Box key={`${item.kind}:${item.iri}`} variant="code">
                    {item.kind} {item.iri}
                  </Box>
                ))}
              </Alert>
            )}
            <KeyValuePairs
              columns={2}
              items={[
                { label: "新增三元组", value: String(diff.summary?.addedTriples ?? "-") },
                { label: "删除三元组", value: String(diff.summary?.removedTriples ?? "-") },
              ]}
            />
            {iriList("新增类", diff.summary?.addedClasses)}
            {iriList("删除类", diff.summary?.removedClasses)}
            {iriList("新增属性", diff.summary?.addedProperties)}
            {iriList("删除属性", diff.summary?.removedProperties)}
            {(diff.summary?.domainChanges ?? []).length > 0 && (
              <Box>
                <Box variant="awsui-key-label">domain 变更</Box>
                {(diff.summary?.domainChanges ?? []).map((change) => (
                  <Box key={change.property} variant="code">
                    {change.property}: [{change.from.join(", ")}] → [{change.to.join(", ")}]
                  </Box>
                ))}
              </Box>
            )}
            {(diff.summary?.rangeChanges ?? []).length > 0 && (
              <Box>
                <Box variant="awsui-key-label">range 变更</Box>
                {(diff.summary?.rangeChanges ?? []).map((change) => (
                  <Box key={change.property} variant="code">
                    {change.property}: [{change.from.join(", ")}] → [{change.to.join(", ")}]
                  </Box>
                ))}
              </Box>
            )}
          </SpaceBetween>
        </Container>
      )}

      <Table
        header={<Header variant="h2">操作记录（本页最近 20 条）</Header>}
        items={log.slice(0, 20)}
        columnDefinitions={logColumns}
        empty={<Box textAlign="center" color="inherit">还没有操作。</Box>}
      />
    </SpaceBetween>
  );
}

export default OntologyVersionsPage;
