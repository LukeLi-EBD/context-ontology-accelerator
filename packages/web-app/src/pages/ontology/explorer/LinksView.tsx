// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * LinksView — the Explorer's "Links" tab.
 *
 * Read-only neighbourhood around one IRI (FindLinks): nodes plus the edges
 * that connect them, each tagged with the hop that reached it. The hop
 * ceiling is contractual (3) and the backend rejects a deeper request rather
 * than clamping, so the selector max and the table's hop column are the same
 * fact. No adjacency is a successful empty answer, not an error.
 */
import { useState } from "react";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import FormField from "@cloudscape-design/components/form-field";
import Header from "@cloudscape-design/components/header";
import Input from "@cloudscape-design/components/input";
import Select, { type SelectProps } from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Table from "@cloudscape-design/components/table";
import type { ApiClient } from "@components/ApiClientProvider";
import {
  findGraphLinks,
  type GraphLinkEdge,
  type GraphLinkNode,
  type GraphLinksResult,
  type LinkDirection,
} from "../../../services/ontology-engine";
import { useAppI18n } from "../../../i18n/LocaleProvider";

const MAX_HOPS_CEILING = 3;
const MAX_LINK_LIMIT = 500;

export function LinksView({
  apiClient,
  namespace,
}: {
  apiClient: ApiClient;
  namespace?: string;
}) {
  const { t } = useAppI18n();
  const [uri, setUri] = useState("");
  const [direction, setDirection] = useState<LinkDirection>("both");
  const [maxHops, setMaxHops] = useState(3);
  const [limit, setLimit] = useState(200);
  const [result, setResult] = useState<GraphLinksResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const directionOptions: SelectProps.Option[] = [
    { value: "both", label: t("Both directions") },
    { value: "outgoing", label: t("Outgoing") },
    { value: "incoming", label: t("Incoming") },
  ];

  const run = async () => {
    if (!namespace) return;
    setLoading(true);
    setError(null);
    try {
      const found = await findGraphLinks(apiClient, namespace, uri.trim(), {
        direction,
        max_hops: maxHops,
        limit,
      });
      setResult(found);
    } catch (e) {
      setError((e as Error).message);
      setResult(null);
    } finally {
      setLoading(false);
      setSearched(true);
    }
  };

  const clear = () => {
    setUri("");
    setResult(null);
    setError(null);
    setSearched(false);
  };

  const nodes: GraphLinkNode[] = [...(result?.nodes ?? [])].sort(
    (a, b) => a.hops - b.hops || a.uri.localeCompare(b.uri),
  );
  const edges: GraphLinkEdge[] = [...(result?.edges ?? [])].sort(
    (a, b) => a.hops - b.hops || a.source.localeCompare(b.source),
  );
  const isEmpty = searched && !loading && !error && nodes.length === 0 && edges.length === 0;

  const nodeColumns = [
    { id: "hops", header: t("Hops"), cell: (n: GraphLinkNode) => n.hops },
    {
      id: "label",
      header: t("Label"),
      cell: (n: GraphLinkNode) => n.label || "—",
    },
    {
      id: "kind",
      header: t("Kind"),
      cell: (n: GraphLinkNode) => n.kind ?? "resource",
    },
    {
      id: "uri",
      header: t("IRI"),
      cell: (n: GraphLinkNode) => (
        <Box variant="code" fontSize="body-s">
          {n.uri}
        </Box>
      ),
    },
  ];

  const edgeColumns = [
    { id: "hops", header: t("Hops"), cell: (e: GraphLinkEdge) => e.hops },
    {
      id: "direction",
      header: t("Direction"),
      cell: (e: GraphLinkEdge) =>
        e.direction === "incoming" ? t("Incoming") : t("Outgoing"),
    },
    {
      id: "source",
      header: t("Source"),
      cell: (e: GraphLinkEdge) => (
        <Box variant="code" fontSize="body-s">
          {e.source}
        </Box>
      ),
    },
    {
      id: "predicate",
      header: t("Predicate"),
      cell: (e: GraphLinkEdge) => e.predicateLabel || e.predicate,
    },
    {
      id: "target",
      header: t("Target"),
      cell: (e: GraphLinkEdge) => (
        <Box variant="code" fontSize="body-s">
          {e.target}
        </Box>
      ),
    },
    {
      id: "graph",
      header: t("Named graph"),
      cell: (e: GraphLinkEdge) => (
        <Box variant="code" fontSize="body-s">
          {e.graph || "—"}
        </Box>
      ),
    },
  ];

  return (
    <SpaceBetween size="m">
      <Box color="text-body-secondary">
        {t(
          "Neighbourhood expansion: every hop re-scans the whole frontier, so cost grows per hop and the cap is 3 hops. (Paths allows 6 because it searches between two IRIs.)",
        )}
      </Box>

      <ColumnLayout columns={4}>
        <FormField label={t("Seed IRI")}>
          <Input
            value={uri}
            onChange={({ detail }) => setUri(detail.value)}
            placeholder="https://…"
            data-testid="explorer-link-uri"
          />
        </FormField>
        <FormField label={t("Direction to expand")}>
          <Select
            selectedOption={
              directionOptions.find((o) => o.value === direction) ?? null
            }
            options={directionOptions}
            onChange={({ detail }) =>
              setDirection((detail.selectedOption.value as LinkDirection) ?? "both")
            }
            data-testid="explorer-link-direction"
          />
        </FormField>
        <FormField
          label={t("Max hops")}
          constraintText={t("Up to 3 hops — frontier expansion, cost grows per hop.")}
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
            data-testid="explorer-link-hops"
          />
        </FormField>
        <FormField label={t("Link limit")}>
          <Input
            type="number"
            value={String(limit)}
            onChange={({ detail }) => {
              const parsed = Number(detail.value);
              if (Number.isFinite(parsed) && parsed > 0) {
                setLimit(Math.min(parsed, MAX_LINK_LIMIT));
              }
            }}
            data-testid="explorer-link-limit"
          />
        </FormField>
      </ColumnLayout>

      <SpaceBetween direction="horizontal" size="xs">
        <Button
          variant="primary"
          onClick={run}
          loading={loading}
          disabled={!namespace || !uri.trim()}
          data-testid="explorer-link-find"
        >
          {t("Find links")}
        </Button>
        <Button onClick={clear} data-testid="explorer-link-clear">
          {t("Clear")}
        </Button>
      </SpaceBetween>

      {error && (
        <Alert type="error" header={t("Link search failed")} data-testid="explorer-link-error">
          {error}
        </Alert>
      )}

      {isEmpty && (
        <Alert
          type="info"
          header={t("No links found for this IRI.")}
          data-testid="explorer-link-empty"
        />
      )}

      {!isEmpty && result && (
        <>
          <Box data-testid="explorer-link-count">
            {t("Neighbours: {nodes} · Edges: {edges}", {
              nodes: nodes.length,
              edges: edges.length,
            })}
            {" — "}
            {t("Expanded {hops} hop(s); nodes beyond that are not included.", {
              hops: maxHops,
            })}
          </Box>
          {result.truncated && (
            <Alert type="info" data-testid="explorer-link-truncated">
              {t("More edges exist than returned; lower the limit or narrow the direction.")}
            </Alert>
          )}

          <Header variant="h3">{t("Neighbours")}</Header>
          <Table
            items={nodes}
            columnDefinitions={nodeColumns}
            trackBy={(n) => n.uri}
            empty={t("No neighbours")}
            data-testid="explorer-link-nodes"
          />

          <Header variant="h3">{t("Adjacency edges")}</Header>
          <Table
            items={edges}
            columnDefinitions={edgeColumns}
            trackBy={(e) => `${e.graph}|${e.source}|${e.predicate}|${e.target}|${e.direction}`}
            empty={t("No edges")}
            data-testid="explorer-link-edges"
          />
        </>
      )}
    </SpaceBetween>
  );
}
