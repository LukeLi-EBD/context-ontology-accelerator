// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * StatementBrowserView — raw triple browsing for the Explorer.
 *
 * Read-only: lists the namespace's statements one page at a time with
 * optional subject / predicate / object / graph filters (combined with AND).
 * Paging is server-side (deterministic order), so a row's position never
 * shifts when a filter changes. Clicking a subject opens its entity page.
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import FormField from "@cloudscape-design/components/form-field";
import Grid from "@cloudscape-design/components/grid";
import Header from "@cloudscape-design/components/header";
import Input from "@cloudscape-design/components/input";
import Link from "@cloudscape-design/components/link";
import Select, { type SelectProps } from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Table from "@cloudscape-design/components/table";
import type { ApiClient } from "@components/ApiClientProvider";
import {
  listStatements,
  type GraphStatement,
} from "../../../services/ontology-engine";
import { useAppI18n } from "../../../i18n/LocaleProvider";

const LIMIT_OPTIONS: SelectProps.Option[] = [20, 50, 100].map((n) => ({
  value: String(n),
  label: String(n),
}));

interface DraftFilters {
  subject: string;
  predicate: string;
  object: string;
  graph: string;
}

const EMPTY_FILTERS: DraftFilters = {
  subject: "",
  predicate: "",
  object: "",
  graph: "",
};

function applied(filters: DraftFilters): DraftFilters {
  return {
    subject: filters.subject.trim(),
    predicate: filters.predicate.trim(),
    object: filters.object.trim(),
    graph: filters.graph.trim(),
  };
}

export function StatementBrowserView({
  apiClient,
  namespace,
}: {
  apiClient: ApiClient;
  namespace?: string;
}) {
  const { t } = useAppI18n();
  const navigate = useNavigate();
  const [draft, setDraft] = useState<DraftFilters>(EMPTY_FILTERS);
  // The filters the current page was fetched with. A new object identity is
  // also what triggers the fetch, so "Clear" refreshes even when already empty.
  const [filters, setFilters] = useState<DraftFilters>(EMPTY_FILTERS);
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [items, setItems] = useState<GraphStatement[]>([]);
  const [truncated, setTruncated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!namespace) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    listStatements(apiClient, namespace, {
      subject: filters.subject || undefined,
      predicate: filters.predicate || undefined,
      object: filters.object || undefined,
      graph: filters.graph || undefined,
      limit,
      offset,
    })
      .then((page) => {
        if (cancelled) return;
        setItems(page.statements ?? []);
        setTruncated(Boolean(page.truncated));
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [apiClient, namespace, filters, limit, offset]);

  const applyFilters = () => {
    setOffset(0);
    setFilters(applied(draft));
  };

  const clearFilters = () => {
    setDraft(EMPTY_FILTERS);
    setOffset(0);
    setFilters({ ...EMPTY_FILTERS });
  };

  const first = items.length === 0 ? 0 : offset + 1;
  const last = offset + items.length;

  return (
    <SpaceBetween size="m">
      {error && (
        <Alert
          type="warning"
          dismissible
          onDismiss={() => setError(null)}
          header={t("Could not load statements")}
        >
          {error}
        </Alert>
      )}

      <Grid gridDefinition={[{ colspan: 3 }, { colspan: 3 }, { colspan: 2 }, { colspan: 2 }, { colspan: 2 }]}>
        <FormField label={t("Subject")}>
          <Input
            value={draft.subject}
            placeholder="https://…"
            onChange={({ detail }) =>
              setDraft((d) => ({ ...d, subject: detail.value }))
            }
          />
        </FormField>
        <FormField label={t("Predicate")}>
          <Input
            value={draft.predicate}
            placeholder="https://…"
            onChange={({ detail }) =>
              setDraft((d) => ({ ...d, predicate: detail.value }))
            }
          />
        </FormField>
        <FormField label={t("Object")}>
          <Input
            value={draft.object}
            onChange={({ detail }) =>
              setDraft((d) => ({ ...d, object: detail.value }))
            }
          />
        </FormField>
        <FormField label={t("Named graph")}>
          <Input
            value={draft.graph}
            placeholder="https://…"
            onChange={({ detail }) =>
              setDraft((d) => ({ ...d, graph: detail.value }))
            }
          />
        </FormField>
        <FormField label={t("Limit")}>
          <Select
            selectedOption={
              LIMIT_OPTIONS.find((o) => o.value === String(limit)) ?? null
            }
            options={LIMIT_OPTIONS}
            onChange={({ detail }) => {
              setOffset(0);
              setLimit(Number(detail.selectedOption.value ?? 20));
            }}
          />
        </FormField>
      </Grid>

      <SpaceBetween direction="horizontal" size="xs">
        <Button variant="primary" onClick={applyFilters} loading={loading}>
          {t("Search")}
        </Button>
        <Button onClick={clearFilters}>{t("Clear")}</Button>
        <Box color="text-body-secondary" padding={{ top: "xs" }}>
          {t("Filters combine with AND.")}
        </Box>
      </SpaceBetween>

      <Table
        loading={loading}
        loadingText={t("Loading statements")}
        items={items}
        trackBy={(s) => `${s.graph}|${s.subject}|${s.predicate}|${s.object}`}
        columnDefinitions={[
          {
            id: "graph",
            header: t("Named graph"),
            cell: (s) => (
              <Box variant="code" fontSize="body-s">
                {s.graph}
              </Box>
            ),
          },
          {
            id: "subject",
            header: t("Subject"),
            isRowHeader: true,
            cell: (s) =>
              namespace ? (
                <Link
                  href={`/namespaces/${namespace}/ontology/entities/${encodeURIComponent(s.subject)}`}
                  onFollow={(e) => {
                    e.preventDefault();
                    navigate(
                      `/namespaces/${namespace}/ontology/entities/${encodeURIComponent(s.subject)}`,
                    );
                  }}
                >
                  {s.subject}
                </Link>
              ) : (
                s.subject
              ),
          },
          {
            id: "predicate",
            header: t("Predicate"),
            cell: (s) => (
              <Box variant="code" fontSize="body-s">
                {s.predicate}
              </Box>
            ),
          },
          {
            id: "object",
            header: t("Object"),
            cell: (s) => (
              <Box variant="code" fontSize="body-s">
                {s.object}
              </Box>
            ),
          },
        ]}
        empty={t("No statements match these filters.")}
        header={
          <Header
            variant="h2"
            counter={items.length > 0 ? `(${first}–${last})` : undefined}
            description={t(
              "Statements are paged in the graph store's index order.",
            )}
          >
            {t("Statements")}
          </Header>
        }
        footer={
          <SpaceBetween direction="horizontal" size="xs">
            <Button
              disabled={offset === 0 || loading}
              onClick={() => setOffset(Math.max(0, offset - limit))}
            >
              {t("Previous")}
            </Button>
            <Button
              disabled={!truncated || loading}
              onClick={() => setOffset(offset + limit)}
            >
              {t("Next")}
            </Button>
          </SpaceBetween>
        }
      />
    </SpaceBetween>
  );
}
