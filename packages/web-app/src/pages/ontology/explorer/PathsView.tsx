// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * PathsView — the Explorer's "Paths" tab.
 *
 * Same read-only path search the Canvas page exposes (FindGraphPath, F04–F07),
 * lifted onto /ontology/graph so it can be deep-linked with ?tab=paths. The
 * form, result table and empty state mirror CanvasPage; the API call is the
 * shared `findGraphPath` service function, not a second client.
 */
import { useState } from "react";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import FormField from "@cloudscape-design/components/form-field";
import Header from "@cloudscape-design/components/header";
import Input from "@cloudscape-design/components/input";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Table from "@cloudscape-design/components/table";
import type { ApiClient } from "@components/ApiClientProvider";
import {
  findGraphPath,
  type CanvasEdge,
  type CanvasNode,
  type GraphPath,
} from "../../../services/ontology-engine";
import { useAppI18n } from "../../../i18n/LocaleProvider";

const MAX_HOPS_CEILING = 6;
const MAX_PATH_LIMIT = 20;

function nodeLabel(node: CanvasNode | undefined): string {
  return node?.label || node?.uri || "—";
}

export function PathsView({
  apiClient,
  namespace,
}: {
  apiClient: ApiClient;
  namespace?: string;
}) {
  const { t } = useAppI18n();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [maxHops, setMaxHops] = useState(3);
  const [pathLimit, setPathLimit] = useState(5);
  const [paths, setPaths] = useState<GraphPath[]>([]);
  const [truncated, setTruncated] = useState(false);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const run = async () => {
    if (!namespace) return;
    setLoading(true);
    setError(null);
    try {
      const result = await findGraphPath(
        apiClient,
        namespace,
        start.trim(),
        end.trim(),
        { max_hops: maxHops, limit: pathLimit },
      );
      setPaths(result.paths ?? []);
      setTruncated(Boolean(result.truncated));
      setSelected(0);
    } catch (e) {
      setError((e as Error).message);
      setPaths([]);
      setTruncated(false);
    } finally {
      setLoading(false);
      setSearched(true);
    }
  };

  const clear = () => {
    setStart("");
    setEnd("");
    setPaths([]);
    setTruncated(false);
    setSelected(0);
    setError(null);
    setSearched(false);
  };

  const current = paths[selected];

  const nodeColumns = [
    {
      id: "label",
      header: t("Label"),
      cell: (n: CanvasNode) => nodeLabel(n),
    },
    {
      id: "kind",
      header: t("Kind"),
      cell: (n: CanvasNode) => n.kind ?? "resource",
    },
    {
      id: "uri",
      header: t("IRI"),
      cell: (n: CanvasNode) => (
        <Box variant="code" fontSize="body-s">
          {n.uri}
        </Box>
      ),
    },
  ];

  const edgeColumns = [
    {
      id: "source",
      header: t("Source"),
      cell: (e: CanvasEdge) => (
        <Box variant="code" fontSize="body-s">
          {e.source}
        </Box>
      ),
    },
    {
      id: "predicate",
      header: t("Predicate"),
      cell: (e: CanvasEdge) => e.predicateLabel || e.predicate,
    },
    {
      id: "target",
      header: t("Target"),
      cell: (e: CanvasEdge) => (
        <Box variant="code" fontSize="body-s">
          {e.target}
        </Box>
      ),
    },
    {
      id: "direction",
      header: t("Direction"),
      cell: (e: CanvasEdge) =>
        e.direction === "incoming" ? t("Incoming") : t("Outgoing"),
    },
  ];

  return (
    <SpaceBetween size="m">
      <Box color="text-body-secondary">
        {t(
          "Point-to-point path search: the engine follows one route at a time, so it can afford 6 hops. (Links is capped at 3 because it expands the whole frontier.)",
        )}
      </Box>

      <ColumnLayout columns={4}>
        <FormField label={t("Start IRI")}>
          <Input
            value={start}
            onChange={({ detail }) => setStart(detail.value)}
            placeholder="https://…"
            data-testid="explorer-path-start"
          />
        </FormField>
        <FormField label={t("End IRI")}>
          <Input
            value={end}
            onChange={({ detail }) => setEnd(detail.value)}
            placeholder="https://…"
            data-testid="explorer-path-end"
          />
        </FormField>
        <FormField
          label={t("Max hops")}
          constraintText={t("Up to 6 hops — point-to-point search.")}
        >
          <Input
            type="number"
            value={String(maxHops)}
            onChange={({ detail }) => {
              const parsed = Number(detail.value);
              if (Number.isFinite(parsed) && parsed > 0) {
                setMaxHops(Math.min(parsed, MAX_HOPS_CEILING));
              }
            }}
            data-testid="explorer-path-hops"
          />
        </FormField>
        <FormField label={t("Path limit")}>
          <Input
            type="number"
            value={String(pathLimit)}
            onChange={({ detail }) => {
              const parsed = Number(detail.value);
              if (Number.isFinite(parsed) && parsed > 0) {
                setPathLimit(Math.min(parsed, MAX_PATH_LIMIT));
              }
            }}
            data-testid="explorer-path-limit"
          />
        </FormField>
      </ColumnLayout>

      <SpaceBetween direction="horizontal" size="xs">
        <Button
          variant="primary"
          onClick={run}
          loading={loading}
          disabled={!namespace || !start.trim() || !end.trim()}
          data-testid="explorer-path-find"
        >
          {t("Find paths")}
        </Button>
        <Button onClick={clear} data-testid="explorer-path-clear">
          {t("Clear")}
        </Button>
      </SpaceBetween>

      {error && (
        <Alert type="error" header={t("Path search failed")} data-testid="explorer-path-error">
          {error}
        </Alert>
      )}

      {searched && !loading && !error && paths.length === 0 && (
        <Alert
          type="info"
          header={t("No path found within {hops} hop(s).", { hops: maxHops })}
          data-testid="explorer-path-empty"
        />
      )}

      {paths.length > 0 && (
        <>
          <Box data-testid="explorer-path-count">
            {t("Paths found: {count}", { count: paths.length })}
          </Box>
          {truncated && (
            <Alert type="info" data-testid="explorer-path-truncated">
              {t("More paths exist than returned; raise the limit to see them.")}
            </Alert>
          )}
          <Table
            items={paths}
            columnDefinitions={[
              {
                id: "index",
                header: "#",
                cell: (_p: GraphPath, i?: number) => (i ?? 0) + 1,
              },
              { id: "hops", header: t("Hops"), cell: (p: GraphPath) => p.hops },
              {
                id: "nodes",
                header: t("Nodes"),
                cell: (p: GraphPath) => p.nodes.length,
              },
              {
                id: "edges",
                header: t("Edges"),
                cell: (p: GraphPath) => p.edges.length,
              },
              {
                id: "route",
                header: t("Route"),
                cell: (p: GraphPath) => p.nodes.map(nodeLabel).join(" → "),
              },
            ]}
            selectionType="single"
            selectedItems={current ? [current] : []}
            onSelectionChange={({ detail }) => {
              const picked = detail.selectedItems[0];
              if (picked) setSelected(paths.indexOf(picked));
            }}
            trackBy={(p) =>
              p.nodes.map((n) => n.uri).join("|") +
              "#" +
              p.edges.map((e) => `${e.source}>${e.predicate}>${e.target}`).join("|")
            }
            empty={t("No paths yet")}
            header={<Header variant="h2">{t("Path results")}</Header>}
            data-testid="explorer-path-table"
          />

          {current && (
            <>
              <Header variant="h3">
                {t("Showing path {index} of {total}", {
                  index: selected + 1,
                  total: paths.length,
                })}
              </Header>
              <Header variant="h3">{t("Path nodes")}</Header>
              <Table
                items={current.nodes}
                columnDefinitions={nodeColumns}
                trackBy={(n) => n.uri}
                empty={t("No nodes")}
                data-testid="explorer-path-nodes"
              />
              <Header variant="h3">{t("Path edges")}</Header>
              <Table
                items={current.edges}
                columnDefinitions={edgeColumns}
                trackBy={(e) => `${e.source}|${e.predicate}|${e.target}`}
                empty={t("No edges")}
                data-testid="explorer-path-edges"
              />
            </>
          )}
        </>
      )}
    </SpaceBetween>
  );
}
