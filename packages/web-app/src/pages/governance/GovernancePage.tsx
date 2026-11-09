import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Checkbox from "@cloudscape-design/components/checkbox";
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
  exportOntologyBundle,
  importOntologyBundle,
  inspectOntologyBundle,
  listOntologyEvents,
  type OntologyEvent,
} from "../../services/ontology-lifecycle";

// The local kernel keeps one ontology registry; the namespace/ontology path
// segments are contract shape, not a partition key.
const DEFAULT_ONTOLOGY_ID = "fsldm-local";

const ACTION_OPTIONS = [
  { label: "全部动作", value: "" },
  { label: "imported", value: "imported" },
  { label: "proposed", value: "proposed" },
  { label: "approved", value: "approved" },
  { label: "rejected", value: "rejected" },
  { label: "published", value: "published" },
  { label: "breaking_acknowledged", value: "breaking_acknowledged" },
  { label: "superseded", value: "superseded" },
  { label: "rolled_back", value: "rolled_back" },
];

function errorText(err: unknown): string {
  if (err instanceof ApiError) return `${err.status} ${err.code}: ${err.message}`;
  return err instanceof Error ? err.message : String(err);
}

function eventDetail(event: OntologyEvent): string {
  const raw = event.payload?.breakingItems;
  if (Array.isArray(raw) && raw.length > 0) {
    const items = raw as { kind?: string; iri?: string }[];
    return `${items.length} 项：${items
      .map((item) => `${item.kind ?? "?"} ${item.iri ?? "?"}`)
      .join("；")}`;
  }
  const mode = event.payload?.mode;
  if (typeof mode === "string") return mode;
  return event.reason ?? "-";
}

function jsonBlock(value: unknown) {
  return (
    <Box variant="code">
      <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
        {JSON.stringify(value, null, 2)}
      </pre>
    </Box>
  );
}

export function GovernancePage() {
  const { namespaceId } = useParams<{ namespaceId: string }>();
  const api = useApiClient();
  useBreadcrumbTrail(
    namespaceId
      ? [
          { text: "Ontology", href: `/namespaces/${namespaceId}/ontology`, namespaceId },
          { text: "治理" },
        ]
      : undefined,
  );

  const [action, setAction] = useState("");
  const [events, setEvents] = useState<OntologyEvent[]>([]);
  const [eventsBusy, setEventsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [actor, setActor] = useState("");
  const [out, setOut] = useState("");
  const [tag, setTag] = useState(`ui-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "")}`);
  const [includeBlobs, setIncludeBlobs] = useState(false);
  const [bundleRef, setBundleRef] = useState("");
  const [database, setDatabase] = useState("platform_restore_test");
  const [replace, setReplace] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [exportResult, setExportResult] = useState<Record<string, unknown> | null>(null);
  const [inspectResult, setInspectResult] = useState<Record<string, unknown> | null>(null);
  const [importResult, setImportResult] = useState<Record<string, unknown> | null>(null);

  const loadEvents = useCallback(async () => {
    if (!namespaceId) return;
    setEventsBusy(true);
    setError(null);
    try {
      const data = await listOntologyEvents(api, namespaceId, DEFAULT_ONTOLOGY_ID, {
        action: action || undefined,
        limit: 100,
      });
      setEvents(data.items ?? []);
    } catch (err) {
      setError(`读取审计事件失败：${errorText(err)}`);
    } finally {
      setEventsBusy(false);
    }
  }, [api, namespaceId, action]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  const run = async (key: string, label: string, fn: () => Promise<string>) => {
    setBusy(key);
    setError(null);
    setNotice(null);
    try {
      setNotice(await fn());
    } catch (err) {
      setError(`${label}失败：${errorText(err)}`);
    } finally {
      setBusy(null);
    }
  };

  const doExport = () =>
    run("export", "导出 bundle", async () => {
      const result = await exportOntologyBundle(api, namespaceId!, DEFAULT_ONTOLOGY_ID, {
        out: out.trim() || undefined,
        tag: tag.trim() || undefined,
        includeBlobs,
      });
      setExportResult(result as unknown as Record<string, unknown>);
      if (result.bundleDir) {
        setBundleRef(result.bundleDir);
      }
      return `bundleDir=${result.bundleDir} tag=${result.tag} files=${result.files ?? "?"}`;
    });

  const doInspect = () =>
    run("inspect", "检查 bundle", async () => {
      if (!bundleRef.trim()) throw new Error("请先填写 bundle 路径（或先导出）");
      const result = await inspectOntologyBundle(
        api,
        namespaceId!,
        DEFAULT_ONTOLOGY_ID,
        bundleRef.trim(),
      );
      setInspectResult(result as unknown as Record<string, unknown>);
      return `path=${result.path} tag=${result.tag ?? "-"} files=${result.files ?? "?"}`;
    });

  const doImport = () =>
    run("import", "导入 bundle", async () => {
      if (!bundleRef.trim()) throw new Error("请先填写 bundle 路径（或先导出）");
      const result = await importOntologyBundle(api, namespaceId!, DEFAULT_ONTOLOGY_ID, {
        bundleRef: bundleRef.trim(),
        database: database.trim() || "platform_restore_test",
        replace,
        actor: actor.trim() || "operator",
      });
      setImportResult(result as unknown as Record<string, unknown>);
      if (result.ok === false) {
        // 写库已经发生，但校验没过时不能报成功；把失败项直接摆到提示里。
        const failed = (result.checks ?? []).find((check) => check.ok === false);
        throw new Error(
          `写库已执行，但校验未通过：step=${result.failedStep ?? "-"} check=${
            failed?.name ?? "-"
          }${result.error ? ` error=${result.error}` : ""}`,
        );
      }
      return `database=${result.database ?? database} ok=${String(result.ok)} failedStep=${result.failedStep ?? "-"}`;
    });

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="事件审计与 bundle 迁移。审计读取不写库；bundle 导出写文件系统，导入会新建数据库。"
      >
        治理
      </Header>

      {error && (
        <Alert type="error" header="请求失败">
          {error}
        </Alert>
      )}
      {notice && <Alert type="success">{notice}</Alert>}

      <Container
        header={
          <Header
            variant="h2"
            description="来自 GET /ontology/events 的哈希链审计；action 过滤在服务端生效。"
            actions={
              <Button loading={eventsBusy} onClick={() => void loadEvents()}>
                刷新
              </Button>
            }
          >
            事件审计
          </Header>
        }
      >
        <SpaceBetween size="m">
          <FormField label="动作过滤">
            <Select
              selectedOption={
                ACTION_OPTIONS.find((o) => o.value === action) ?? ACTION_OPTIONS[0]
              }
              onChange={({ detail }) => setAction(detail.selectedOption.value ?? "")}
              options={ACTION_OPTIONS}
            />
          </FormField>
          <Table
            loading={eventsBusy}
            loadingText="加载审计事件"
            items={events}
            columnDefinitions={[
              { id: "at", header: "时间", cell: (e: OntologyEvent) => e.createdAt ?? e.at ?? "-" },
              { id: "action", header: "动作", cell: (e: OntologyEvent) => e.action ?? e.type ?? "-" },
              { id: "actor", header: "actor", cell: (e: OntologyEvent) => e.actor ?? "-" },
              { id: "version", header: "versionId", cell: (e: OntologyEvent) => e.versionId ?? "-" },
              { id: "proposal", header: "proposalId", cell: (e: OntologyEvent) => e.proposalId ?? "-" },
              { id: "detail", header: "详情", cell: (e: OntologyEvent) => eventDetail(e) },
            ]}
            empty={<Box textAlign="center" color="inherit">当前过滤条件下没有事件。</Box>}
          />
        </SpaceBetween>
      </Container>

      <Container
        header={
          <Header
            variant="h2"
            description="导出当前发布版本；检查只读；导入会写入一个新的 PostgreSQL 数据库。"
          >
            bundle 迁移
          </Header>
        }
      >
        <SpaceBetween size="l">
          <SpaceBetween size="m">
            <FormField label="操作人（actor）" description="写入导入审计，可留空（默认 operator）">
              <Input value={actor} onChange={({ detail }) => setActor(detail.value)} />
            </FormField>
            <FormField label="输出目录（out）" description="留空由本地 kernel 用临时目录">
              <Input value={out} onChange={({ detail }) => setOut(detail.value)} />
            </FormField>
            <FormField label="tag">
              <Input value={tag} onChange={({ detail }) => setTag(detail.value)} />
            </FormField>
            <Checkbox
              checked={includeBlobs}
              onChange={({ detail }) => setIncludeBlobs(detail.checked)}
            >
              includeBlobs（同时导出 A-Box / blobs）
            </Checkbox>
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="primary" loading={busy === "export"} onClick={doExport}>
                导出 bundle
              </Button>
              <Button loading={busy === "inspect"} onClick={doInspect}>
                检查 bundle
              </Button>
            </SpaceBetween>
            {exportResult && (
              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">导出结果</Box>
                {jsonBlock(exportResult)}
              </SpaceBetween>
            )}
            {inspectResult && (
              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">检查结果</Box>
                {jsonBlock(inspectResult)}
              </SpaceBetween>
            )}
          </SpaceBetween>

          <SpaceBetween size="m">
            <FormField label="bundle 路径（bundleRef）" description="导出成功后自动填入">
              <Input value={bundleRef} onChange={({ detail }) => setBundleRef(detail.value)} />
            </FormField>
            <FormField label="目标数据库" description="本地导入总是新建数据库，不覆盖 platform">
              <Input value={database} onChange={({ detail }) => setDatabase(detail.value)} />
            </FormField>
            <Checkbox checked={replace} onChange={({ detail }) => setReplace(detail.checked)}>
              replace（目标库已存在时替换；默认 false）
            </Checkbox>
            <Alert type="warning" header="导入是写入操作">
              会在 PostgreSQL 新建 <code>{database || "platform_restore_test"}</code> 并写入
              bundle 内容，不会改动 <code>platform</code> 库。
            </Alert>
            <Button loading={busy === "import"} onClick={doImport}>
              导入 bundle
            </Button>
            {importResult && (
              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">导入结果</Box>
                {jsonBlock(importResult)}
              </SpaceBetween>
            )}
          </SpaceBetween>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
