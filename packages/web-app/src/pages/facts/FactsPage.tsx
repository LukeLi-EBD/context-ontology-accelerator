import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Checkbox from "@cloudscape-design/components/checkbox";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Container from "@cloudscape-design/components/container";
import FormField from "@cloudscape-design/components/form-field";
import Header from "@cloudscape-design/components/header";
import Input from "@cloudscape-design/components/input";
import Select from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Table from "@cloudscape-design/components/table";

import { ApiError, useApiClient } from "../../components/ApiClientProvider";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import {
  getFact,
  listFactConflicts,
  listFacts,
  restoreFact,
  retractFact,
  type FactConflict,
  type FactRecord,
} from "../../services/fact-ledger";

const STATE_OPTIONS = [
  { label: "生效中（active）", value: "active" },
  { label: "已撤回（retracted）", value: "retracted" },
  { label: "已取代（superseded）", value: "superseded" },
  { label: "全部状态", value: "all" },
];

function errorText(err: unknown): string {
  if (err instanceof ApiError) return `${err.status} ${err.code}: ${err.message}`;
  return err instanceof Error ? err.message : String(err);
}

function objectText(fact: FactRecord): string {
  return fact.object?.value ?? "-";
}

function sourceText(fact: FactRecord): string {
  const source = fact.source ?? {};
  return [source.kind, source.documentId, source.candidateId].filter(Boolean).join(" / ") || "-";
}

export function FactsPage() {
  const { namespaceId } = useParams<{ namespaceId: string }>();
  const api = useApiClient();
  useBreadcrumbTrail(
    namespaceId
      ? [
          { text: "Ontology", href: `/namespaces/${namespaceId}/ontology`, namespaceId },
          { text: "事实账本" },
        ]
      : undefined,
  );

  const [state, setState] = useState("active");
  const [subject, setSubject] = useState("");
  const [predicate, setPredicate] = useState("");
  const [conflictOnly, setConflictOnly] = useState(false);
  const [facts, setFacts] = useState<FactRecord[]>([]);
  const [conflicts, setConflicts] = useState<FactConflict[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<FactRecord | null>(null);
  const [actor, setActor] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [listBusy, setListBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadFacts = useCallback(async () => {
    if (!namespaceId) return;
    setListBusy(true);
    setError(null);
    try {
      const data = await listFacts(api, namespaceId, {
        state,
        subject: subject || undefined,
        predicate: predicate || undefined,
        conflict: conflictOnly,
        limit: 100,
      });
      setFacts(data.items ?? []);
      const groups = await listFactConflicts(api, namespaceId, false);
      setConflicts(groups.conflicts ?? []);
    } catch (err) {
      setError(`读取事实账本失败：${errorText(err)}`);
    } finally {
      setListBusy(false);
    }
  }, [api, namespaceId, state, subject, predicate, conflictOnly]);

  useEffect(() => {
    void loadFacts();
    // 只在筛选条件变化时自动重拉；「查询」按钮用于同条件下强制刷新。
  }, [state, conflictOnly, namespaceId]);

  const loadDetail = useCallback(
    async (factId: string) => {
      if (!namespaceId) return;
      setSelectedId(factId);
      setError(null);
      try {
        setDetail(await getFact(api, namespaceId, factId));
      } catch (err) {
        setDetail(null);
        setError(`读取事实详情失败：${errorText(err)}`);
      }
    },
    [api, namespaceId],
  );

  const requireActor = (): string => {
    const value = actor.trim();
    if (!value) {
      throw new Error("操作人（actor）必填：撤回/恢复必须留痕，不能留空");
    }
    return value;
  };

  const act = async (kind: "retract" | "restore", fact: FactRecord) => {
    if (!namespaceId) return;
    const key = `${kind}:${fact.factId}`;
    setBusy(key);
    setError(null);
    setNotice(null);
    try {
      const who = requireActor();
      const updated =
        kind === "retract"
          ? await retractFact(api, namespaceId, fact.factId, { actor: who, reason: reason || undefined })
          : await restoreFact(api, namespaceId, fact.factId, { actor: who, reason: reason || undefined });
      setDetail(await getFact(api, namespaceId, fact.factId));
      setNotice(
        `${kind === "retract" ? "已撤回" : "已恢复"} ${fact.factId}（actor=${who}，当前状态 ${
          updated.state ?? "-"
        }）`,
      );
      await loadFacts();
    } catch (err) {
      setError(
        `${kind === "retract" ? "撤回" : "恢复"}失败：${errorText(err)}`,
      );
    } finally {
      setBusy(null);
    }
  };

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="A-Box 断言账本：列表、详情、冲突与撤回/恢复。写入动作必须填写操作人并进入审计链。"
        actions={
          <Button iconName="refresh" onClick={() => void loadFacts()} loading={listBusy}>
            刷新
          </Button>
        }
      >
        事实账本
      </Header>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}
      {notice && (
        <Alert type="success" dismissible onDismiss={() => setNotice(null)}>
          {notice}
        </Alert>
      )}

      <Container header={<Header variant="h2">筛选</Header>}>
        <SpaceBetween size="m">
          <ColumnLayout columns={4}>
            <FormField label="状态">
              <Select
                selectedOption={STATE_OPTIONS.find((item) => item.value === state) ?? STATE_OPTIONS[0]}
                onChange={({ detail: change }) =>
                  setState(change.selectedOption?.value ?? "active")
                }
                options={STATE_OPTIONS}
              />
            </FormField>
            <FormField label="主语 IRI">
              <Input
                value={subject}
                onChange={({ detail: change }) => setSubject(change.value)}
                placeholder="https://coa.local/..."
              />
            </FormField>
            <FormField label="谓词 IRI">
              <Input
                value={predicate}
                onChange={({ detail: change }) => setPredicate(change.value)}
                placeholder="https://coa.local/ont/..."
              />
            </FormField>
            <FormField label="操作人（actor，写入必填）">
              <Input
                value={actor}
                onChange={({ detail: change }) => setActor(change.value)}
                placeholder="填写操作人"
              />
            </FormField>
          </ColumnLayout>
          <SpaceBetween direction="horizontal" size="m">
            <Button variant="primary" onClick={() => void loadFacts()} loading={listBusy}>
              查询
            </Button>
            <Checkbox
              checked={conflictOnly}
              onChange={({ detail: change }) => setConflictOnly(change.checked)}
            >
              只看有冲突的事实
            </Checkbox>
          </SpaceBetween>
        </SpaceBetween>
      </Container>

      <Container
        header={
          <Header variant="h2" description={`共 ${facts.length} 条`}>
            事实列表
          </Header>
        }
      >
        <Table
          items={facts}
          loading={listBusy}
          loadingText="读取事实账本"
          columnDefinitions={[
            { id: "factId", header: "factId", cell: (item) => item.factId, width: 220 },
            { id: "subject", header: "主语", cell: (item) => item.subject },
            { id: "predicate", header: "谓词", cell: (item) => item.predicate },
            { id: "object", header: "宾语", cell: objectText },
            {
              id: "state",
              header: "状态",
              cell: (item) => item.state,
              width: 110,
            },
            {
              id: "conflict",
              header: "冲突",
              cell: (item) => (item.conflict ? "是" : "-"),
              width: 70,
            },
            { id: "source", header: "来源", cell: sourceText },
            {
              id: "actions",
              header: "查看",
              cell: (item) => (
                <Button
                  variant="link"
                  onClick={() => void loadDetail(item.factId)}
                  loading={selectedId === item.factId && busy === null && detail === null}
                >
                  详情
                </Button>
              ),
              width: 90,
            },
          ]}
          empty={
            <Box textAlign="center" color="inherit">
              当前筛选下没有事实
            </Box>
          }
        />
      </Container>

      <Container
        header={
          <Header variant="h2" description="单条断言及其事件链">
            事实详情
          </Header>
        }
      >
        {detail ? (
          <SpaceBetween size="m">
            <ColumnLayout columns={3}>
              <Box>
                <b>factId</b>
                <div>{detail.factId}</div>
              </Box>
              <Box>
                <b>状态</b>
                <div>{detail.state}</div>
              </Box>
              <Box>
                <b>图</b>
                <div>{detail.graph}</div>
              </Box>
              <Box>
                <b>主语</b>
                <div>{detail.subject}</div>
              </Box>
              <Box>
                <b>谓词</b>
                <div>{detail.predicate}</div>
              </Box>
              <Box>
                <b>宾语</b>
                <div>
                  {objectText(detail)}（{detail.object?.kind ?? "-"}）
                </div>
              </Box>
              <Box>
                <b>来源</b>
                <div>{sourceText(detail)}</div>
              </Box>
              <Box>
                <b>断言时间</b>
                <div>{detail.assertedAt ?? "-"}</div>
              </Box>
              <Box>
                <b>撤回/解决</b>
                <div>
                  {detail.retractReason ??
                    detail.resolution ??
                    (detail.acceptedConflict ? "冲突已接受" : "-")}
                </div>
              </Box>
            </ColumnLayout>
            <SpaceBetween direction="horizontal" size="m">
              <FormField label="原因（可选，写入审计）">
                <Input
                  value={reason}
                  onChange={({ detail: change }) => setReason(change.value)}
                  placeholder="说明为什么撤回/恢复"
                />
              </FormField>
              <Button
                disabled={detail.state !== "active"}
                loading={busy === `retract:${detail.factId}`}
                onClick={() => void act("retract", detail)}
              >
                撤回这条事实
              </Button>
              <Button
                disabled={detail.state === "active" || detail.state === "superseded"}
                loading={busy === `restore:${detail.factId}`}
                onClick={() => void act("restore", detail)}
              >
                恢复这条事实
              </Button>
            </SpaceBetween>
            <Table
              items={detail.events ?? []}
              header={<Header variant="h3">事件链（{(detail.events ?? []).length} 条）</Header>}
              columnDefinitions={[
                { id: "createdAt", header: "时间", cell: (item) => item.createdAt ?? "-" },
                { id: "action", header: "动作", cell: (item) => item.action },
                { id: "actor", header: "actor", cell: (item) => item.actor ?? "-" },
                { id: "reason", header: "原因", cell: (item) => item.reason ?? "-" },
                {
                  id: "payload",
                  header: "载荷",
                  cell: (item) => (
                    <Box variant="code">
                      <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                        {JSON.stringify(item.payload ?? {}, null, 0)}
                      </pre>
                    </Box>
                  ),
                },
                { id: "hash", header: "hash", cell: (item) => (item.hash ?? "").slice(0, 12) },
              ]}
              empty={<Box textAlign="center">没有事件</Box>}
            />
          </SpaceBetween>
        ) : (
          <Box color="inherit">在列表里点「详情」查看单条事实与事件链。</Box>
        )}
      </Container>

      <Container
        header={
          <Header variant="h2" description="同一主语+谓词下出现多个不同宾语即视为冲突">
            冲突分组（{conflicts.length}）
          </Header>
        }
      >
        <Table
          items={conflicts}
          columnDefinitions={[
            { id: "subject", header: "主语", cell: (item) => item.subject },
            { id: "predicate", header: "谓词", cell: (item) => item.predicate },
            {
              id: "values",
              header: "宾语取值",
              cell: (item) => (item.values ?? []).join(" | ") || "-",
            },
            {
              id: "facts",
              header: "断言数",
              cell: (item) => (item.facts ?? []).length,
              width: 90,
            },
            {
              id: "pending",
              header: "待裁决",
              cell: (item) => (item.pending ? "是" : "已接受"),
              width: 90,
            },
          ]}
          empty={<Box textAlign="center">当前没有未裁决冲突</Box>}
        />
      </Container>
    </SpaceBetween>
  );
}
