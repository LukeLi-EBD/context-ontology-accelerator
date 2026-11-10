// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * SparqlConsoleView — the SPARQL tab of the Explorer (F72–F74).
 *
 * F72: run one SELECT/ASK through the contract's `RunSparql` operation against
 * the current namespace's graphs. F73: render the provider's variables as
 * columns and show the row count, including an explicit truncation notice. F74:
 * show the API's status and codes verbatim (`code`, `providerCode`,
 * `providerMessage`) instead of collapsing them into a generic message.
 */
import { useMemo, useState } from "react";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Header from "@cloudscape-design/components/header";
import KeyValuePairs from "@cloudscape-design/components/key-value-pairs";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Table from "@cloudscape-design/components/table";
import Textarea from "@cloudscape-design/components/textarea";
import { RunSparqlCommand } from "@coa/data-layer-client";
import { useDataLayerClient } from "@components/DataLayerClientProvider";
import { useAppI18n } from "../../../i18n/LocaleProvider";

const DEFAULT_QUERY = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 100";
const ROW_LIMIT = 5_000;

interface ConsoleResult {
  form?: string;
  answer?: boolean;
  variables?: string[];
  rows?: string[][];
  rowCount?: number;
  returnedRows?: number;
  truncated?: boolean;
  graphCount?: number;
  elapsedMs?: number;
}

interface ConsoleError {
  status?: number;
  code?: string;
  providerCode?: string;
  providerMessage?: string;
  message: string;
}

function toConsoleError(error: unknown): ConsoleError {
  const candidate = error as {
    $metadata?: { httpStatusCode?: number };
    code?: unknown;
    name?: unknown;
    providerCode?: unknown;
    providerMessage?: unknown;
    message?: unknown;
  };
  return {
    status: candidate?.$metadata?.httpStatusCode,
    code:
      typeof candidate?.code === "string"
        ? candidate.code
        : typeof candidate?.name === "string"
          ? candidate.name
          : undefined,
    providerCode:
      typeof candidate?.providerCode === "string"
        ? candidate.providerCode
        : undefined,
    providerMessage:
      typeof candidate?.providerMessage === "string"
        ? candidate.providerMessage
        : undefined,
    message:
      typeof candidate?.message === "string"
        ? candidate.message
        : String(error),
  };
}

export function SparqlConsoleView({ namespace }: { namespace?: string }) {
  const { t } = useAppI18n();
  const client = useDataLayerClient();
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ConsoleResult | null>(null);
  const [error, setError] = useState<ConsoleError | null>(null);

  const canRun = Boolean(namespace) && query.trim().length > 0 && !running;

  const run = async () => {
    if (!namespace || !query.trim()) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const output = await client.send(
        new RunSparqlCommand({ namespaceId: namespace, sparql: query }),
      );
      setResult(output as ConsoleResult);
    } catch (caught) {
      setError(toConsoleError(caught));
    } finally {
      setRunning(false);
    }
  };

  const columns = useMemo(() => {
    const variables = result?.variables ?? [];
    return variables.map((variable) => ({
      id: variable,
      header: variable,
      cell: (item: Record<string, string>) => item[variable] ?? "",
    }));
  }, [result]);

  const items = useMemo(() => {
    const variables = result?.variables ?? [];
    return (result?.rows ?? []).map((row, index) => {
      const item: Record<string, string> = { key: String(index) };
      variables.forEach((variable, at) => {
        item[variable] = row[at] ?? "";
      });
      return item;
    });
  }, [result]);

  const errorItems = useMemo(() => {
    if (!error) return [];
    const rows: { label: string; value: string }[] = [];
    if (error.status !== undefined) {
      rows.push({ label: t("HTTP status"), value: String(error.status) });
    }
    if (error.code) {
      rows.push({ label: t("Error code"), value: error.code });
    }
    if (error.providerCode) {
      rows.push({ label: t("Provider code"), value: error.providerCode });
    }
    if (error.providerMessage) {
      rows.push({
        label: t("Provider message"),
        value: error.providerMessage,
      });
    }
    rows.push({ label: t("Message"), value: error.message });
    return rows;
  }, [error, t]);

  return (
    <SpaceBetween size="m">
      <Header
        variant="h2"
        description={t(
          "Run one SPARQL SELECT or ASK against this namespace's graphs. FROM, SERVICE and LOAD are refused; results stop at 5,000 rows or 10 seconds.",
        )}
      >
        {t("SPARQL console")}
      </Header>

      <Textarea
        value={query}
        rows={10}
        disabled={running}
        onChange={({ detail }) => setQuery(detail.value)}
        onKeyDown={({ detail }) => {
          if (
            detail.key === "Enter" &&
            (detail.ctrlKey || detail.metaKey) &&
            canRun
          ) {
            void run();
          }
        }}
        spellcheck={false}
        ariaLabel={t("SPARQL query")}
      />

      <SpaceBetween size="s" direction="horizontal">
        <Button variant="primary" loading={running} disabled={!canRun} onClick={() => void run()}>
          {running ? t("Running query…") : t("Run query")}
        </Button>
        <Box color="text-body-secondary" fontSize="body-s">
          {t("Ctrl+Enter also runs the query.")}
        </Box>
      </SpaceBetween>

      <Box color="text-body-secondary" fontSize="body-s">
        {t(
          "Only the graphs of this namespace are readable. The T-Box and inferred graphs are out of scope in this version.",
        )}
      </Box>

      {error && (
        <Alert type="error" header={t("Query rejected")}>
          <SpaceBetween size="s">
            <KeyValuePairs columns={1} items={errorItems} />
          </SpaceBetween>
        </Alert>
      )}

      {result?.form === "ASK" && (
        <Box>
          <Box variant="awsui-key-label">{t("ASK answer")}</Box>
          <Box>{result.answer ? t("true") : t("false")}</Box>
          <Box color="text-body-secondary" fontSize="body-s">
            {t("Namespace graphs in scope: {count}", {
              count: result.graphCount ?? 0,
            })}
            {" · "}
            {t("Executed in {ms} ms", { ms: result.elapsedMs ?? 0 })}
          </Box>
        </Box>
      )}

      {result?.form === "SELECT" && (
        <SpaceBetween size="s">
          <SpaceBetween size="xs" direction="horizontal">
            <Box variant="awsui-key-label">{t("Rows")}</Box>
            <Box>{result.rowCount ?? 0}</Box>
            <Box color="text-body-secondary" fontSize="body-s">
              {t("Namespace graphs in scope: {count}", {
                count: result.graphCount ?? 0,
              })}
              {" · "}
              {t("Executed in {ms} ms", { ms: result.elapsedMs ?? 0 })}
            </Box>
          </SpaceBetween>
          {result.truncated && (
            <Alert type="warning" header={t("Result truncated")}>
              {t(
                "The provider produced {total} rows. Only the first {limit} are shown; narrow the query to see the rest.",
                {
                  total: result.rowCount ?? 0,
                  limit: ROW_LIMIT,
                },
              )}
            </Alert>
          )}
          <Table
            variant="embedded"
            items={items}
            columnDefinitions={columns}
            trackBy="key"
            header={
              <Header
                variant="h3"
                counter={`(${result.returnedRows ?? 0})`}
                description={t(
                  "Returned {returned} of {total} rows.",
                  {
                    returned: result.returnedRows ?? 0,
                    total: result.rowCount ?? 0,
                  },
                )}
              >
                {t("Result")}
              </Header>
            }
            empty={
              <Box textAlign="center" color="inherit">
                {t("No rows returned.")}
              </Box>
            }
          />
        </SpaceBetween>
      )}
    </SpaceBetween>
  );
}
