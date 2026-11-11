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
import Modal from "@cloudscape-design/components/modal";
import Select from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Table from "@cloudscape-design/components/table";

import { ApiError, useApiClient } from "../../components/ApiClientProvider";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import {
  batchKeepFactConflicts,
  batchRetractFacts,
  getFact,
  listFactConflicts,
  listFactEvents,
  listFacts,
  resolveFactConflict,
  restoreFact,
  retractFact,
  undoFactConflict,
  type BatchKeepConflictResult,
  type BatchRetractResult,
  type FactAdjudication,
  type FactConflict,
  type FactEventPage,
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

function conflictKey(item: { subject: string; predicate: string }): string {
  return `${item.subject}|${item.predicate}`;
}

function actionText(action: string | null): string {
  if (action === "keep") return "保留一方";
  if (action === "keep_both") return "都保留";
  if (action === "merge") return "合并";
  return action ?? "-";
}

function shortTime(value: string): string {
  return value.length >= 19 ? value.slice(0, 19).replace("T", " ") : value;
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
  const [adjudications, setAdjudications] = useState<FactAdjudication[]>([]);
  const [keepChoice, setKeepChoice] = useState<Record<string, string>>({});
  const [mergeValue, setMergeValue] = useState<Record<string, string>>({});
  const [batchOpen, setBatchOpen] = useState(false);
  const [batchActor, setBatchActor] = useState("");
  const [batchPredicate, setBatchPredicate] = useState("");
  const [batchKeepValue, setBatchKeepValue] = useState("");
  const [batchPreview, setBatchPreview] = useState<BatchKeepConflictResult | null>(null);
  const [batchPreviewBusy, setBatchPreviewBusy] = useState(false);
  const [batchApplyBusy, setBatchApplyBusy] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<FactRecord | null>(null);
  const [chain, setChain] = useState<FactEventPage | null>(null);
  const [chainBusy, setChainBusy] = useState(false);
  const [selectedFacts, setSelectedFacts] = useState<FactRecord[]>([]);
  const [preview, setPreview] = useState<BatchRetractResult | null>(null);
  const [batchBusy, setBatchBusy] = useState(false);
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
      const groups = await listFactConflicts(api, namespaceId, true);
      setConflicts(groups.conflicts ?? []);
      setAdjudications(groups.adjudications ?? []);
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
        const [row, page] = await Promise.all([
          getFact(api, namespaceId, factId),
          listFactEvents(api, namespaceId, factId, { limit: 100 }),
        ]);
        setDetail(row);
        setChain(page);
      } catch (err) {
        setDetail(null);
        setChain(null);
        setError(`读取事实详情失败：${errorText(err)}`);
      }
    },
    [api, namespaceId],
  );

  const loadEarlier = async () => {
    if (!namespaceId || !chain || chain.nextBefore === null) return;
    setChainBusy(true);
    setError(null);
    try {
      const page = await listFactEvents(api, namespaceId, chain.factId, {
        limit: 100,
        before: chain.nextBefore,
      });
      // Pages walk backwards; merge so the chain stays in eventId order.
      setChain({
        ...page,
        count: page.count + chain.count,
        total: page.total,
        items: [...page.items, ...chain.items],
      });
    } catch (err) {
      setError(`读取更早事件失败：${errorText(err)}`);
    } finally {
      setChainBusy(false);
    }
  };

  const requireActor = (): string => {
    const value = actor.trim();
    if (!value) {
      throw new Error("操作人（actor）必填：裁决/撤销/撤回/恢复必须留痕，不能留空");
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
      setChain(
        await listFactEvents(api, namespaceId, fact.factId, { limit: 100 }),
      );
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

  const previewBatch = async () => {
    if (!namespaceId) return;
    setError(null);
    setNotice(null);
    try {
      const who = requireActor();
      const factIds = selectedFacts.map((item) => item.factId);
      const result = await batchRetractFacts(api, namespaceId, {
        factIds,
        actor: who,
        reason: reason || undefined,
        dryRun: true,
      });
      setPreview(result);
    } catch (err) {
      setError(`批量撤回预览失败：${errorText(err)}`);
    }
  };

  const confirmBatch = async () => {
    if (!namespaceId || !preview) return;
    setBatchBusy(true);
    setError(null);
    setNotice(null);
    try {
      const result = await batchRetractFacts(api, namespaceId, {
        factIds: preview.items.map((item) => item.factId),
        actor: preview.actor,
        reason: preview.reason ?? undefined,
        dryRun: false,
      });
      const skipped = result.skipped ?? [];
      setNotice(
        `批量撤回完成：${result.count} 条，批次 ${result.batchId ?? "-"}，actor=${result.actor}` +
          (result.reason ? `，理由=${result.reason}` : "，未填理由") +
          (skipped.length
            ? `；跳过 ${skipped.length} 条（${skipped
                .map((item) => `${item.factId}:${item.reason}`)
                .join("，")}）`
            : ""),
      );
      setPreview(null);
      setSelectedFacts([]);
      if (detail && result.retracted?.includes(detail.factId)) {
        await loadDetail(detail.factId);
      }
      await loadFacts();
    } catch (err) {
      setError(`批量撤回失败：${errorText(err)}`);
    } finally {
      setBatchBusy(false);
    }
  };

  const decide = async (kind: "keep" | "keep_both", conflict: FactConflict) => {
    if (!namespaceId) return;
    const key = `decide:${conflictKey(conflict)}`;
    setBusy(key);
    setError(null);
    setNotice(null);
    try {
      const who = requireActor();
      const keepValue =
        keepChoice[conflictKey(conflict)] ?? conflict.values?.[0] ?? undefined;
      if (kind === "keep" && !keepValue) {
        throw new Error("这条冲突没有可选宾语，无法「保留一方」");
      }
      await resolveFactConflict(api, namespaceId, {
        subject: conflict.subject,
        predicate: conflict.predicate,
        action: kind,
        actor: who,
        reason: reason || undefined,
        keep: kind === "keep" ? keepValue : undefined,
      });
      setNotice(
        kind === "keep"
          ? `已保留 ${keepValue}（actor=${who}），可撤销`
          : `已接受冲突（都保留，actor=${who}），可撤销`,
      );
      await loadFacts();
    } catch (err) {
      setError(`裁决失败：${errorText(err)}`);
    } finally {
      setBusy(null);
    }
  };

  // F31: merge retires every value of the group and writes one merged value.
  // The target comes from the per-row input, falling back to the value already
  // chosen in the keep picker so "these two are the same thing, keep this one"
  // does not require typing.
  const mergeConflict = async (conflict: FactConflict) => {
    if (!namespaceId) return;
    const key = `merge:${conflictKey(conflict)}`;
    setBusy(key);
    setError(null);
    setNotice(null);
    try {
      const who = requireActor();
      const mergedObject =
        (mergeValue[conflictKey(conflict)] ?? "").trim() ||
        keepChoice[conflictKey(conflict)] ||
        "";
      if (!mergedObject) {
        throw new Error("合并需要一个目标值：填「合并为」，或先在左侧选一个取值");
      }
      await resolveFactConflict(api, namespaceId, {
        subject: conflict.subject,
        predicate: conflict.predicate,
        action: "merge",
        mergedObject,
        actor: who,
        reason: reason || undefined,
      });
      setMergeValue((prev) => ({ ...prev, [conflictKey(conflict)]: "" }));
      setNotice(`已合并为 ${mergedObject}（actor=${who}），原断言已撤回，可撤销`);
      await loadFacts();
    } catch (err) {
      setError(`合并失败：${errorText(err)}`);
    } finally {
      setBusy(null);
    }
  };

  const previewBatchKeep = async () => {
    if (!namespaceId) return;
    setBatchPreviewBusy(true);
    setError(null);
    try {
      const who = batchActor.trim();
      if (!who) throw new Error("批量保留必须填写操作人");
      const keep = batchKeepValue.trim();
      if (!keep) throw new Error("批量保留需要填写要保留的取值");
      if (!batchPredicate) throw new Error("批量保留需要一个明确的谓词范围");
      setBatchPreview(
        await batchKeepFactConflicts(api, namespaceId, {
          keep,
          predicate: batchPredicate,
          actor: who,
          reason: reason || undefined,
          dryRun: true,
        }),
      );
    } catch (err) {
      setBatchPreview(null);
      setError(`批量保留预览失败：${errorText(err)}`);
    } finally {
      setBatchPreviewBusy(false);
    }
  };

  const applyBatchKeep = async () => {
    if (!namespaceId || !batchPreview) return;
    setBatchApplyBusy(true);
    setError(null);
    try {
      const who = batchActor.trim();
      if (!who) throw new Error("批量保留必须填写操作人");
      const result = await batchKeepFactConflicts(api, namespaceId, {
        keep: batchPreview.keep,
        predicate: batchPredicate,
        actor: who,
        reason: reason || undefined,
        dryRun: false,
      });
      setBatchOpen(false);
      setBatchPreview(null);
      setActor(who);
      setNotice(
        `批量保留完成：命中 ${result.matched} 组，保留 ${result.kept} 组，跳过 ${result.skipped} 组，撤回 ${result.affectedFacts} 条（batchId=${result.batchId}）`,
      );
      await loadFacts();
    } catch (err) {
      setError(`批量保留失败：${errorText(err)}`);
    } finally {
      setBatchApplyBusy(false);
    }
  };

  const undoAdjudication = async (entry: FactAdjudication) => {
    if (!namespaceId) return;
    setBusy(`undo:${entry.eventId}`);
    setError(null);
    setNotice(null);
    try {
      const who = requireActor();
      await undoFactConflict(api, namespaceId, {
        eventId: entry.eventId ?? undefined,
        subject: entry.subject,
        predicate: entry.predicate,
        actor: who,
        reason: reason || undefined,
      });
      setNotice(`已撤销裁决（${actionText(entry.action)}，actor=${who}）：冲突回到待裁决`);
      await loadFacts();
    } catch (err) {
      setError(`撤销裁决失败：${errorText(err)}`);
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
          <FormField
            label="理由（写入时进入审计）"
            description="裁决与撤销都会把这段文字写进账本事件链"
          >
            <Input
              value={reason}
              onChange={({ detail: change }) => setReason(change.value)}
              placeholder="为什么这样裁决 / 撤销"
            />
          </FormField>
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
          <Header
            variant="h2"
            description={`共 ${facts.length} 条；已选 ${selectedFacts.length} 条`}
            actions={
              <Button
                disabled={selectedFacts.length === 0}
                onClick={() => void previewBatch()}
              >
                批量撤回（预览）
              </Button>
            }
          >
            事实列表
          </Header>
        }
      >
        <Table
          items={facts}
          loading={listBusy}
          loadingText="读取事实账本"
          selectionType="multi"
          selectedItems={selectedFacts}
          onSelectionChange={({ detail: change }) =>
            setSelectedFacts(change.selectedItems)
          }
          trackBy="factId"
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
              items={chain?.items ?? []}
              loading={chainBusy}
              header={
                <Header
                  variant="h3"
                  description="独立读：GET /facts/{factId}/events，不依赖事实行；撤销入口只持有 eventId 时也走这条链"
                  actions={
                    chain?.nextBefore != null ? (
                      <Button loading={chainBusy} onClick={() => void loadEarlier()}>
                        加载更早
                      </Button>
                    ) : undefined
                  }
                >
                  事件链（已载 {chain?.count ?? 0} / 共 {chain?.total ?? 0} 条）
                </Header>
              }
              columnDefinitions={[
                { id: "createdAt", header: "时间", cell: (item) => item.createdAt ?? "-" },
                { id: "action", header: "动作", cell: (item) => item.action },
                { id: "actor", header: "actor", cell: (item) => item.actor ?? "-" },
                { id: "reason", header: "原因", cell: (item) => item.reason ?? "-" },
                { id: "batchId", header: "批次", cell: (item) => item.batchId ?? "-" },
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
          <Header
            variant="h2"
            description="同一主语+谓词下出现多个不同宾语即视为冲突"
            actions={
              <Button
                disabled={conflicts.length === 0}
                onClick={() => {
                  setBatchPreview(null);
                  // Default to the first group's predicate: the scope stays
                  // explicit (it is shown and editable) but most runs have one.
                  setBatchPredicate(conflicts[0]?.predicate ?? "");
                  setBatchKeepValue("");
                  setBatchActor(actor);
                  setError(null);
                  setBatchOpen(true);
                }}
              >
                按谓词批量保留
              </Button>
            }
          >
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
              width: 100,
            },
            {
              id: "keep",
              header: "保留哪一方",
              cell: (item) => {
                const chosen = keepChoice[conflictKey(item)] ?? item.values?.[0] ?? "";
                return (
                  <Select
                    ariaLabel={`保留取值 ${conflictKey(item)}`}
                    selectedOption={
                      item.values?.includes(chosen)
                        ? { label: chosen, value: chosen }
                        : null
                    }
                    onChange={({ detail: change }) =>
                      setKeepChoice((prev) => ({
                        ...prev,
                        [conflictKey(item)]: change.selectedOption?.value ?? "",
                      }))
                    }
                    options={(item.values ?? []).map((value) => ({ label: value, value }))}
                    placeholder="选择要保留的值"
                  />
                );
              },
            },
            {
              id: "actions",
              header: "裁决",
              cell: (item) => (
                <SpaceBetween size="xs">
                  <SpaceBetween direction="horizontal" size="xs">
                    <Input
                      ariaLabel={`合并为 ${conflictKey(item)}`}
                      placeholder="合并为（IRI，留空则用左侧所选）"
                      value={mergeValue[conflictKey(item)] ?? ""}
                      onChange={({ detail: change }) =>
                        setMergeValue((prev) => ({
                          ...prev,
                          [conflictKey(item)]: change.value,
                        }))
                      }
                    />
                    <Button
                      disabled={!item.pending}
                      loading={busy === `merge:${conflictKey(item)}`}
                      onClick={() => void mergeConflict(item)}
                    >
                      合并
                    </Button>
                  </SpaceBetween>
                  <SpaceBetween direction="horizontal" size="xs">
                    <Button
                      disabled={!item.pending}
                      loading={busy === `decide:${conflictKey(item)}`}
                      onClick={() => void decide("keep", item)}
                    >
                      保留所选
                    </Button>
                    <Button
                      disabled={!item.pending}
                      loading={busy === `decide:${conflictKey(item)}`}
                      onClick={() => void decide("keep_both", item)}
                    >
                      都保留
                    </Button>
                  </SpaceBetween>
                </SpaceBetween>
              ),
            },
          ]}
          empty={<Box textAlign="center">当前没有冲突</Box>}
        />
      </Container>

      <Container
        header={
          <Header
            variant="h2"
            description="来自账本事件链：判成什么、谁判的、什么时候，以及是否仍生效"
          >
            最近裁决（{adjudications.length}）
          </Header>
        }
      >
        <Table
          items={adjudications}
          columnDefinitions={[
            { id: "subject", header: "主语", cell: (item) => item.subject },
            { id: "predicate", header: "谓词", cell: (item) => item.predicate },
            {
              id: "action",
              header: "判定",
              cell: (item) => actionText(item.action),
              width: 110,
            },
            {
              id: "result",
              header: "判定结果",
              cell: (item) =>
                item.object ?? item.kept ?? ((item.values ?? []).join(" | ") || "-"),
            },
            { id: "actor", header: "操作人", cell: (item) => item.actor ?? "-", width: 120 },
            { id: "reason", header: "理由", cell: (item) => item.reason ?? "-" },
            { id: "at", header: "时间", cell: (item) => shortTime(item.at), width: 180 },
            {
              id: "status",
              header: "状态",
              cell: (item) =>
                item.status === "in_effect"
                  ? "生效中"
                  : `已撤销（${item.undoneBy?.actor ?? "-"} @ ${shortTime(
                      item.undoneBy?.at ?? "",
                    )}${item.undoneBy?.reason ? `：${item.undoneBy.reason}` : ""}）`,
              width: 240,
            },
            {
              id: "history",
              header: "事件链",
              cell: (item) =>
                (item.history ?? [])
                  .map((event) => `${event.action}@${shortTime(event.at)} by ${event.actor ?? "-"}`)
                  .join(" → ") || "-",
            },
            {
              id: "undo",
              header: "撤销",
              cell: (item) => (
                <Button
                  disabled={item.status !== "in_effect"}
                  loading={busy === `undo:${item.eventId}`}
                  onClick={() => void undoAdjudication(item)}
                >
                  撤销裁决
                </Button>
              ),
              width: 120,
            },
          ]}
          empty={<Box textAlign="center">还没有裁决记录</Box>}
        />
      </Container>

      <Modal
        visible={batchOpen}
        onDismiss={() => setBatchOpen(false)}
        size="medium"
        header="按谓词批量保留"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={() => setBatchOpen(false)} disabled={batchApplyBusy}>
                取消
              </Button>
              <Button loading={batchPreviewBusy} onClick={() => void previewBatchKeep()}>
                预览影响
              </Button>
              <Button
                variant="primary"
                loading={batchApplyBusy}
                disabled={!batchPreview || batchPreview.matched === 0}
                onClick={() => void applyBatchKeep()}
              >
                确认执行
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Box color="text-body-secondary">
            一条规则作用在一个明确的谓词范围内：命中的待裁决分组保留该取值，其余断言撤回。
            预览是默认行为，只有「确认执行」才会写账本。
          </Box>
          <FormField label="操作人（必填）">
            <Input
              ariaLabel="批量保留的操作人"
              placeholder="operator"
              value={batchActor}
              onChange={({ detail: change }) => {
                setBatchActor(change.value);
                setBatchPreview(null);
              }}
            />
          </FormField>
          <FormField label="谓词范围（必填）">
            <Select
              ariaLabel="批量保留的谓词范围"
              placeholder="选择谓词"
              selectedOption={
                batchPredicate ? { label: batchPredicate, value: batchPredicate } : null
              }
              options={Array.from(new Set(conflicts.map((item) => item.predicate)))
                .sort()
                .map((value) => ({ label: value, value }))}
              onChange={({ detail: change }) => {
                setBatchPredicate(change.selectedOption?.value ?? "");
                setBatchPreview(null);
              }}
            />
          </FormField>
          <FormField label="要保留的取值（必填）">
            <Input
              ariaLabel="批量保留的取值"
              placeholder="urn:coa:entity:…"
              value={batchKeepValue}
              onChange={({ detail: change }) => {
                setBatchKeepValue(change.value);
                setBatchPreview(null);
              }}
            />
          </FormField>
          {batchPreview ? (
            <Alert type={batchPreview.matched === 0 ? "warning" : "info"}>
              {`预览（dryRun=${batchPreview.dryRun}）：命中 ${batchPreview.matched} 组，保留 ${batchPreview.kept} 组，跳过 ${batchPreview.skipped} 组，将撤回 ${batchPreview.affectedFacts} 条断言。`}
            </Alert>
          ) : null}
        </SpaceBetween>
      </Modal>

      <Modal
        visible={preview !== null}
        onDismiss={() => setPreview(null)}
        size="large"
        header="批量撤回预览"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={() => setPreview(null)} disabled={batchBusy}>
                取消
              </Button>
              <Button
                variant="primary"
                loading={batchBusy}
                disabled={(preview?.count ?? 0) === 0}
                onClick={() => void confirmBatch()}
              >
                确认撤回 {preview?.count ?? 0} 条
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        {preview && (
          <SpaceBetween size="m">
            <Alert type="warning">
              将把 <b>{preview.count}</b> 条生效事实改为 retracted；actor=
              <b>{preview.actor}</b>，理由=
              <b>{preview.reason ? preview.reason : "（未填）"}</b>
              ，每条都会写 `batch_retracted` 事件并带上同一批次号。确认前不会写入任何东西。
            </Alert>
            {preview.skipped.length > 0 && (
              <Alert type="info">
                跳过 {preview.skipped.length} 条：
                {preview.skipped.map((item) => `${item.factId}（${item.reason}）`).join("，")}
              </Alert>
            )}
            <Table
              items={preview.items}
              trackBy="factId"
              columnDefinitions={[
                { id: "factId", header: "factId", cell: (item) => item.factId, width: 220 },
                { id: "subject", header: "主语", cell: (item) => item.subject },
                { id: "predicate", header: "谓词", cell: (item) => item.predicate },
                { id: "object", header: "宾语", cell: (item) => item.object },
                { id: "graph", header: "图", cell: (item) => item.graph },
              ]}
              empty={<Box textAlign="center">没有可撤回的事实</Box>}
            />
          </SpaceBetween>
        )}
      </Modal>
    </SpaceBetween>
  );
}
