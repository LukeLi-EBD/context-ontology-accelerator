// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Ontology canvas: draw a namespace's graph and find paths between IRIs.
 *
 * Feature points (12 §P1):
 *   F13 manifest   — capabilities + limits are read before the first page.
 *   F08 filters    — node kind, named graph, page size.
 *   F09 load more  — offset paging, disabled at the manifest boundary.
 *   F10 clear      — drops the accumulated page.
 *   F11 stats      — loaded counts and the truncated flag, never a silent cap.
 *   F12 tables     — node and edge tables for what is drawn.
 *   F04–F07 paths  — form, path table, edge table, SVG.
 *
 * Everything here is read-only; the canvas never writes to the graph.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import Multiselect, {
  type MultiselectProps,
} from "@cloudscape-design/components/multiselect";
import Select from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Table from "@cloudscape-design/components/table";
import { useApiClient } from "@components/ApiClientProvider";
import { useBreadcrumbTrail } from "@api-hooks/use-breadcrumb-trail";
import {
  findGraphPath,
  getCanvasManifest,
  getCanvasSubgraph,
  type CanvasEdge,
  type CanvasManifest,
  type CanvasNode,
  type GraphPath,
} from "../../services/ontology-engine";

const KIND_OPTIONS: MultiselectProps.Option[] = [
  { label: "Class", value: "class" },
  { label: "Object property", value: "object-property" },
  { label: "Datatype property", value: "datatype-property" },
];

const KIND_COLOURS: Record<string, string> = {
  class: "#0972d3",
  "object-property": "#037f0c",
  "datatype-property": "#b2911b",
  resource: "#687078",
};

function errorText(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

function nodeLabel(node: CanvasNode | undefined): string {
  if (!node) return "";
  const local = node.uri.split(/[#/]/).pop();
  return node.label || local || node.uri;
}

function mergeNodes(current: CanvasNode[], incoming: CanvasNode[]): CanvasNode[] {
  const byUri = new Map(current.map((n) => [n.uri, n]));
  for (const node of incoming) {
    if (!byUri.has(node.uri)) byUri.set(node.uri, node);
  }
  return [...byUri.values()];
}

function mergeEdges(current: CanvasEdge[], incoming: CanvasEdge[]): CanvasEdge[] {
  const seen = new Set(
    current.map((e) => `${e.source}\u0000${e.predicate}\u0000${e.target}\u0000${e.graph ?? ""}`),
  );
  const out = [...current];
  for (const edge of incoming) {
    const key = `${edge.source}\u0000${edge.predicate}\u0000${edge.target}\u0000${edge.graph ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(edge);
  }
  return out;
}

/** F07: a straight left-to-right rendering of one path. */
function PathDiagram({ path }: { path: GraphPath }) {
  const boxWidth = 150;
  const gap = 70;
  const height = 130;
  const width = Math.max(560, path.nodes.length * (boxWidth + gap) + 20);
  return (
    <svg
      width="100%"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Graph path"
      data-testid="canvas-path-svg"
      style={{ maxWidth: width }}
    >
      <defs>
        <marker
          id="canvas-arrow"
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="6"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#687078" />
        </marker>
      </defs>
      {path.nodes.map((node, index) => {
        const x = 10 + index * (boxWidth + gap);
        return (
          <g key={`${node.uri}-${index}`}>
            <rect
              x={x}
              y={45}
              width={boxWidth}
              height={44}
              rx={8}
              fill="#ffffff"
              stroke={KIND_COLOURS[node.kind ?? "resource"] ?? "#687078"}
              strokeWidth={2}
            />
            <text x={x + boxWidth / 2} y={70} textAnchor="middle" fontSize="13">
              {nodeLabel(node).slice(0, 22)}
            </text>
            {index < path.nodes.length - 1 && (
              <>
                <line
                  x1={x + boxWidth}
                  y1={67}
                  x2={x + boxWidth + gap - 4}
                  y2={67}
                  stroke="#687078"
                  strokeWidth={1.5}
                  markerEnd="url(#canvas-arrow)"
                />
                <text
                  x={x + boxWidth + gap / 2}
                  y={38}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#414d5c"
                >
                  {(path.edges[index]?.predicateLabel ?? "").slice(0, 20)}
                </text>
              </>
            )}
          </g>
        );
      })}
    </svg>
  );
}

export function CanvasPage() {
  const { namespaceId = "" } = useParams();
  const apiClient = useApiClient();

  useBreadcrumbTrail(
    namespaceId
      ? [
          { text: "Ontology", href: `/namespaces/${namespaceId}/ontology`, namespaceId },
          { text: "画布" },
        ]
      : [],
  );

  // F13: manifest state.
  const [manifest, setManifest] = useState<CanvasManifest | null>(null);
  const [manifestError, setManifestError] = useState<string | null>(null);

  // F08: filters.
  const [kinds, setKinds] = useState<MultiselectProps.Option[]>([]);
  const [graphUri, setGraphUri] = useState("");
  const [pageSize, setPageSize] = useState(50);

  // F09–F12: accumulated page.
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [edges, setEdges] = useState<CanvasEdge[]>([]);
  const [truncated, setTruncated] = useState(false);
  const [nextOffset, setNextOffset] = useState<number | undefined>();
  const [lastPage, setLastPage] = useState<{ nodes: number; edges: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // F04–F07: path state.
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [maxHops, setMaxHops] = useState(3);
  const [pathLimit, setPathLimit] = useState(5);
  const [paths, setPaths] = useState<GraphPath[]>([]);
  const [pathsTruncated, setPathsTruncated] = useState(false);
  const [pathError, setPathError] = useState<string | null>(null);
  const [pathBusy, setPathBusy] = useState(false);
  const [selectedPath, setSelectedPath] = useState(0);

  useEffect(() => {
    if (!namespaceId) return;
    let cancelled = false;
    getCanvasManifest(apiClient, namespaceId)
      .then((m) => {
        if (cancelled) return;
        setManifest(m);
        setManifestError(null);
        setPageSize((current) =>
          Math.max(1, Math.min(current, m.limits.maxPageSize)),
        );
      })
      .catch((e) => {
        if (!cancelled) setManifestError(errorText(e));
      });
    return () => {
      cancelled = true;
    };
  }, [apiClient, namespaceId]);

  const kindFilter = kinds.map((k) => k.value).join(",");

  const load = useCallback(
    async (reset: boolean) => {
      if (!namespaceId) return;
      setLoading(true);
      setLoadError(null);
      try {
        const page = await getCanvasSubgraph(apiClient, namespaceId, {
          kinds: kindFilter || undefined,
          graph: graphUri.trim() || undefined,
          limit: pageSize,
          offset: reset ? 0 : (nextOffset ?? 0),
        });
        setNodes((prev) => (reset ? page.nodes : mergeNodes(prev, page.nodes)));
        setEdges((prev) => (reset ? page.edges : mergeEdges(prev, page.edges)));
        setTruncated(page.truncated);
        setNextOffset(page.nextOffset);
        setLastPage({ nodes: page.nodeCount, edges: page.edgeCount });
      } catch (e) {
        setLoadError(errorText(e));
      } finally {
        setLoading(false);
      }
    },
    [apiClient, namespaceId, kindFilter, graphUri, pageSize, nextOffset],
  );

  // 首屏加载：每个命名空间只在挂载后自动取第一页，避免画布永远停在空态。
  // 用 ref 记住已加载的 namespace，只跑一次；后续分页仍由「Load more」按钮触发。
  const initialLoadFor = useRef<string | null>(null);
  useEffect(() => {
    if (!namespaceId || initialLoadFor.current === namespaceId) return;
    initialLoadFor.current = namespaceId;
    void load(true);
  }, [namespaceId, load]);

  const clearCanvas = () => {
    setNodes([]);
    setEdges([]);
    setTruncated(false);
    setNextOffset(undefined);
    setLastPage(null);
    setLoadError(null);
  };

  const runPathSearch = async () => {
    if (!namespaceId) return;
    setPathBusy(true);
    setPathError(null);
    try {
      const result = await findGraphPath(apiClient, namespaceId, start.trim(), end.trim(), {
        max_hops: maxHops,
        limit: pathLimit,
      });
      setPaths(result.paths);
      setPathsTruncated(result.truncated);
      setSelectedPath(0);
    } catch (e) {
      setPathError(errorText(e));
      setPaths([]);
    } finally {
      setPathBusy(false);
    }
  };

  const currentPath = paths[selectedPath];

  const nodeColumns = useMemo(
    () => [
      {
        id: "label",
        header: "Label",
        cell: (n: CanvasNode) => n.label || "—",
      },
      {
        id: "kind",
        header: "Kind",
        cell: (n: CanvasNode) => (
          <Badge color={n.kind === "class" ? "blue" : "grey"}>{n.kind ?? "resource"}</Badge>
        ),
      },
      { id: "uri", header: "IRI", cell: (n: CanvasNode) => n.uri },
    ],
    [],
  );

  const edgeColumns = useMemo(
    () => [
      { id: "source", header: "Source", cell: (e: CanvasEdge) => e.source },
      {
        id: "predicate",
        header: "Predicate",
        cell: (e: CanvasEdge) => e.predicateLabel || e.predicate,
      },
      { id: "target", header: "Target", cell: (e: CanvasEdge) => e.target },
      { id: "graph", header: "Graph", cell: (e: CanvasEdge) => e.graph ?? "—" },
    ],
    [],
  );

  const pathColumns = useMemo(
    () => [
      { id: "index", header: "#", cell: (_p: GraphPath, i?: number) => (i ?? 0) + 1 },
      { id: "hops", header: "Hops", cell: (p: GraphPath) => p.hops },
      { id: "nodes", header: "Nodes", cell: (p: GraphPath) => p.nodes.length },
      { id: "edges", header: "Edges", cell: (p: GraphPath) => p.edges.length },
      {
        id: "route",
        header: "Route",
        cell: (p: GraphPath) => p.nodes.map(nodeLabel).join(" → "),
      },
      {
        id: "action",
        header: "",
        cell: (p: GraphPath) => (
          <Button
            variant="inline-link"
            onClick={() => setSelectedPath(paths.indexOf(p))}
          >
            Draw
          </Button>
        ),
      },
    ],
    [paths],
  );

  const pathEdgeColumns = useMemo(
    () => [
      { id: "source", header: "Source", cell: (e: CanvasEdge) => e.source },
      {
        id: "predicate",
        header: "Predicate",
        cell: (e: CanvasEdge) => e.predicateLabel || e.predicate,
      },
      { id: "target", header: "Target", cell: (e: CanvasEdge) => e.target },
      {
        id: "direction",
        header: "Direction",
        cell: (e: CanvasEdge) => e.direction ?? "outgoing",
      },
    ],
    [],
  );

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Read-only canvas over the namespace's named graphs: filter a page, page through it, and find paths between two IRIs."
        actions={
          <Button
            onClick={() => load(true)}
            loading={loading}
            data-testid="canvas-load"
          >
            Load
          </Button>
        }
      >
        Canvas
      </Header>

      {/* F13: manifest must be read before the first page. */}
      <Container header={<Header variant="h2">Canvas manifest (F13)</Header>}>
        <SpaceBetween size="s">
          {manifestError && (
            <Alert type="error" header="Manifest unavailable" data-testid="canvas-manifest-error">
              {manifestError}
            </Alert>
          )}
          {!manifest && !manifestError && (
            <StatusIndicator type="loading">Reading manifest</StatusIndicator>
          )}
          {manifest && (
            <>
              <Box data-testid="canvas-manifest-status">
                <StatusIndicator type="success">Manifest loaded</StatusIndicator>
              </Box>
              <Box data-testid="canvas-manifest-capabilities">
                {manifest.capabilities.map((capability) => (
                  <Badge key={capability}>{capability}</Badge>
                ))}
              </Box>
              <Box data-testid="canvas-manifest-limits">
                Max nodes {manifest.limits.maxNodes} · max edges {manifest.limits.maxEdges} · max
                page size {manifest.limits.maxPageSize}
              </Box>
            </>
          )}
        </SpaceBetween>
      </Container>

      {/* F08: filters. */}
      <Container header={<Header variant="h2">Filters (F08)</Header>}>
        <ColumnLayout columns={3}>
          <FormField label="Node kinds">
            <Multiselect
              selectedOptions={kinds}
              onChange={({ detail }) => setKinds([...detail.selectedOptions])}
              options={KIND_OPTIONS}
              placeholder="All kinds"
              data-testid="canvas-kinds"
            />
          </FormField>
          <FormField label="Named graph (optional)">
            <Input
              value={graphUri}
              onChange={({ detail }) => setGraphUri(detail.value)}
              placeholder="https://coa.local/graph/..."
              data-testid="canvas-graph"
            />
          </FormField>
          <FormField label="Page size" description={manifest ? `Ceiling ${manifest.limits.maxPageSize}` : undefined}>
            <Input
              type="number"
              value={String(pageSize)}
              onChange={({ detail }) => {
                const parsed = Number(detail.value);
                if (Number.isFinite(parsed) && parsed > 0) {
                  setPageSize(
                    Math.min(parsed, manifest?.limits.maxPageSize ?? parsed),
                  );
                }
              }}
              data-testid="canvas-page-size"
            />
          </FormField>
        </ColumnLayout>
      </Container>

      {/* F09–F12: page, stats, tables. */}
      <Container header={<Header variant="h2">Subgraph (F09–F12)</Header>}>
        <SpaceBetween size="s">
          <SpaceBetween direction="horizontal" size="s">
            <Button
              onClick={() => load(false)}
              loading={loading}
              disabled={!truncated || nextOffset === undefined}
              data-testid="canvas-load-more"
            >
              Load more
            </Button>
            <Button onClick={clearCanvas} data-testid="canvas-clear">
              Clear
            </Button>
          </SpaceBetween>
          {loadError && (
            <Alert type="error" header="Subgraph request failed" data-testid="canvas-load-error">
              {loadError}
            </Alert>
          )}
          <Box data-testid="canvas-stats">
            Loaded {nodes.length} nodes / {edges.length} edges
            {lastPage ? ` · last page ${lastPage.nodes}/${lastPage.edges}` : ""} ·{" "}
            {truncated ? (
              <StatusIndicator type="warning">truncated — more pages exist</StatusIndicator>
            ) : (
              <StatusIndicator type="success">complete at this offset</StatusIndicator>
            )}
          </Box>
          <Header variant="h3" counter={`(${nodes.length})`}>
            Nodes
          </Header>
          <Table
            items={nodes}
            columnDefinitions={nodeColumns}
            empty="No nodes loaded"
            data-testid="canvas-nodes-table"
          />
          <Header variant="h3" counter={`(${edges.length})`}>
            Edges
          </Header>
          <Table
            items={edges}
            columnDefinitions={edgeColumns}
            empty="No edges loaded"
            data-testid="canvas-edges-table"
          />
        </SpaceBetween>
      </Container>

      {/* F04–F07: path search. */}
      <Container header={<Header variant="h2">Paths (F04–F07)</Header>}>
        <SpaceBetween size="m">
          <ColumnLayout columns={4}>
            <FormField label="Start IRI">
              <Input
                value={start}
                onChange={({ detail }) => setStart(detail.value)}
                placeholder="https://.../#Class"
                data-testid="canvas-path-start"
              />
            </FormField>
            <FormField label="End IRI">
              <Input
                value={end}
                onChange={({ detail }) => setEnd(detail.value)}
                placeholder="https://.../#Class"
                data-testid="canvas-path-end"
              />
            </FormField>
            <FormField label="Max hops">
              <Input
                type="number"
                value={String(maxHops)}
                onChange={({ detail }) => {
                  const parsed = Number(detail.value);
                  if (Number.isFinite(parsed) && parsed > 0) {
                    setMaxHops(Math.min(parsed, 6));
                  }
                }}
                data-testid="canvas-path-hops"
              />
            </FormField>
            <FormField label="Path limit">
              <Input
                type="number"
                value={String(pathLimit)}
                onChange={({ detail }) => {
                  const parsed = Number(detail.value);
                  if (Number.isFinite(parsed) && parsed > 0) {
                    setPathLimit(Math.min(parsed, 20));
                  }
                }}
                data-testid="canvas-path-limit"
              />
            </FormField>
          </ColumnLayout>
          <Button
            variant="primary"
            onClick={runPathSearch}
            loading={pathBusy}
            disabled={!start.trim() || !end.trim()}
            data-testid="canvas-path-find"
          >
            Find paths
          </Button>
          {pathError && (
            <Alert type="error" header="Path search failed" data-testid="canvas-path-error">
              {pathError}
            </Alert>
          )}
          <Box data-testid="canvas-path-count">
            {paths.length} path(s) ·{" "}
            {pathsTruncated ? "truncated — more paths exist" : "not truncated"}
          </Box>
          <Table
            items={paths}
            columnDefinitions={pathColumns}
            empty="No paths yet"
            data-testid="canvas-path-table"
          />
          {currentPath && (
            <>
              <Header variant="h3">Path diagram</Header>
              <PathDiagram path={currentPath} />
              <Header variant="h3">Path edges</Header>
              <Table
                items={currentPath.edges}
                columnDefinitions={pathEdgeColumns}
                empty="No edges"
                data-testid="canvas-path-edges-table"
              />
            </>
          )}
          {paths.length > 1 && (
            <FormField label="Diagram path">
              <Select
                selectedOption={{ label: `Path ${selectedPath + 1}`, value: String(selectedPath) }}
                onChange={({ detail }) => setSelectedPath(Number(detail.selectedOption.value))}
                options={paths.map((p, i) => ({
                  label: `Path ${i + 1} (${p.hops} hops)`,
                  value: String(i),
                }))}
                data-testid="canvas-path-select"
              />
            </FormField>
          )}
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
