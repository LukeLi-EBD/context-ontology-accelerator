// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * T-Box lifecycle client (09 §5.6): version registration, proposals,
 * review, publish and rollback.
 *
 * These paths are served by the local API bridge (8099), which forwards the
 * lifecycle half to the platform kernel. All requests go through `ApiClient`
 * like every other service here.
 */
import type { ApiClient } from "../components/ApiClientProvider";

export interface OntologyVersion {
  id: string;
  semver: string;
  status: "draft" | "approved" | "published" | "superseded" | "deprecated" | string;
  contentHash?: string;
  tripleCount?: number;
  format?: string;
  graph?: string;
  rollbackOf?: string | null;
  label?: string | null;
  createdAt?: string;
  publishedAt?: string | null;
}

export interface VersionList {
  items: OntologyVersion[];
  count: number;
  total: number;
  deprecated: number;
  pointer?: { versionId: string; semver: string; graph: string; updatedAt: string };
}

export interface OntologyProposal {
  proposalId: string;
  versionId: string;
  againstVersion?: string | null;
  changeSummary?: string;
  status: string;
  breaking?: boolean;
  createdBy?: string;
  createdAt?: string;
  approvedBy?: string | null;
  approvedAt?: string | null;
  publishedAt?: string | null;
  versionStatus?: string;
}

export interface ProposalList {
  items: OntologyProposal[];
  count: number;
  returned: number;
  current?: VersionList["pointer"];
}

export interface RegisterVersionInput {
  content: string;
  format?: string;
  changeSummary?: string;
}

/** GetOntologyVersion: the version row plus its proposals and events. */
export interface OntologyVersionDetail extends OntologyVersion {
  versionId: string;
  graphUri?: string;
  statementCount?: number;
  graphTripleCount?: number;
  proposals?: OntologyProposal[];
  events?: { action?: string; at?: string; actor?: string }[];
}

/** DiffOntologyVersions: what changed between `from` and `to`. */
export interface OntologyDiff {
  from?: string | null;
  to?: string;
  breaking?: boolean;
  breakingItems?: { iri: string; kind: string }[];
  summary?: {
    addedClasses?: string[];
    removedClasses?: string[];
    addedProperties?: string[];
    removedProperties?: string[];
    addedTriples?: number;
    removedTriples?: number;
    domainChanges?: { property: string; from: string[]; to: string[] }[];
    rangeChanges?: { property: string; from: string[]; to: string[] }[];
  };
}

/** GetOntologyProposal: the proposal, its version, and the stored diff. */
export interface OntologyProposalDetail {
  proposal: OntologyProposal & {
    diff?: OntologyDiff;
    impact?: Record<string, unknown>;
    acknowledgedBreaking?: boolean;
  };
  version: OntologyVersion;
  versionStatus: string;
  diff: OntologyDiff;
  impact?: Record<string, unknown>;
}

/** ListOntologyEvents: one row of the hash-chained audit log. */
export interface OntologyEvent {
  eventId: number;
  versionId?: string | null;
  proposalId?: string | null;
  action: string;
  actor: string;
  reason?: string | null;
  payload?: Record<string, unknown>;
  createdAt: string;
  type?: string;
  at?: string;
}

export interface OntologyEventList {
  items: OntologyEvent[];
  count: number;
  categories?: Record<string, number>;
}

export interface BundleExportResult {
  ok?: boolean;
  bundleDir: string;
  tag: string;
  schemaVersion?: number;
  generatedAt?: string;
  totals?: Record<string, number>;
  bytes?: number;
  files?: number;
}

export interface BundleInspectResult {
  ok?: boolean;
  path: string;
  tag?: string;
  totals?: Record<string, number>;
  tbox?: Record<string, unknown>;
  files?: number;
}

export interface BundleImportResult {
  ok?: boolean;
  database?: string;
  bundle?: string;
  tbox?: Record<string, unknown>;
  checks?: { name?: string; ok?: boolean }[];
  failedStep?: string;
  error?: string;
  providerCode?: string;
}

/** What ImportOntology answers: the draft row it just created. */
export interface RegisteredVersion {
  versionId: string;
  importId?: string;
  semver: string;
  status: string;
  targetNamespace?: string;
  triples?: number;
  contentHash?: string;
  skipped?: boolean;
  conflicts?: unknown[];
}

function root(namespace: string, ontologyId: string): string {
  return `/namespaces/${encodeURIComponent(namespace)}/ontologies/${encodeURIComponent(ontologyId)}`;
}

export async function listOntologyVersions(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
): Promise<VersionList> {
  return client.get<VersionList>(`${root(namespace, ontologyId)}/versions`);
}

export async function getOntologyVersion(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  versionId: string,
): Promise<OntologyVersionDetail> {
  return client.get<OntologyVersionDetail>(
    `${root(namespace, ontologyId)}/versions/${encodeURIComponent(versionId)}`,
  );
}

export async function diffOntologyVersions(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  versionId: string,
  against?: string,
): Promise<OntologyDiff> {
  const suffix = against ? `?against=${encodeURIComponent(against)}` : "";
  return client.get<OntologyDiff>(
    `${root(namespace, ontologyId)}/versions/${encodeURIComponent(versionId)}/diff${suffix}`,
  );
}

/** ExportOntologyVersion: raw Turtle/N-Quads text, not JSON. */
export async function exportOntologyVersion(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  versionId: string,
  format: "turtle" | "nquads" = "turtle",
): Promise<string> {
  const path = `${root(namespace, ontologyId)}/versions/${encodeURIComponent(versionId)}/export?format=${format}`;
  if (!client.getText) throw new Error("ApiClient.getText is not available");
  return client.getText(path);
}

export async function registerOntologyVersion(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  input: RegisterVersionInput,
): Promise<RegisteredVersion> {
  return client.post<RegisteredVersion>(`${root(namespace, ontologyId)}/import`, {
    format: input.format ?? "turtle",
    content: input.content,
    changeSummary: input.changeSummary,
  });
}

export async function listOntologyProposals(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
): Promise<ProposalList> {
  return client.get<ProposalList>(`${root(namespace, ontologyId)}/proposals`);
}

/** GetOntologyProposal: proposal detail, including the diff stored at propose time. */
export async function getOntologyProposal(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  proposalId: string,
): Promise<OntologyProposalDetail> {
  return client.get<OntologyProposalDetail>(
    `${root(namespace, ontologyId)}/proposals/${encodeURIComponent(proposalId)}`,
  );
}

export async function proposeOntologyVersion(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  input: { versionId: string; rationale?: string; againstVersion?: string; actor?: string },
): Promise<OntologyProposal> {
  return client.post<OntologyProposal>(
    `${root(namespace, ontologyId)}/proposals`,
    input,
  );
}

export async function reviewOntologyProposal(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  proposalId: string,
  decision: "APPROVE" | "REJECT",
  comment?: string,
  actor?: string,
): Promise<{ ok?: boolean; proposalId: string; status?: string }> {
  return client.post(
    `${root(namespace, ontologyId)}/proposals/${encodeURIComponent(proposalId)}/review`,
    { decision, comment, actor },
  );
}

export async function publishOntologyVersion(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  input: {
    versionId: string;
    proposalId?: string;
    expectedVersionId?: string;
    acknowledgeBreaking?: boolean;
    actor?: string;
    reason?: string;
  },
): Promise<{ ok?: boolean; publishedVersion?: string; semver?: string; graph?: string }> {
  return client.post(`${root(namespace, ontologyId)}/publish`, input);
}

export async function rollbackOntology(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  input: { targetVersionId: string; planOnly?: boolean; actor?: string; reason?: string },
): Promise<{ ok?: boolean; publishedVersion?: string; replacedVersionId?: string }> {
  return client.post(`${root(namespace, ontologyId)}/rollback`, input);
}

/** ListOntologyEvents: the hash-chained audit log, optionally per version/action. */
export async function listOntologyEvents(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  params: { versionId?: string; action?: string; limit?: number } = {},
): Promise<OntologyEventList> {
  const query = new URLSearchParams();
  if (params.versionId) query.set("versionId", params.versionId);
  if (params.action) query.set("action", params.action);
  if (params.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return client.get<OntologyEventList>(
    `${root(namespace, ontologyId)}/events${suffix}`,
  );
}

/** VerifyOntology: recompute the audit hash chains and report broken links. */
export async function verifyOntology(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
): Promise<Record<string, unknown>> {
  return client.post<Record<string, unknown>>(
    `${root(namespace, ontologyId)}/verify`,
    {},
  );
}

export async function exportOntologyBundle(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  input: { out?: string; tag?: string; includeBlobs?: boolean } = {},
): Promise<BundleExportResult> {
  return client.post<BundleExportResult>(
    `${root(namespace, ontologyId)}/bundles/export`,
    input,
  );
}

export async function inspectOntologyBundle(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  bundleRef: string,
): Promise<BundleInspectResult> {
  return client.get<BundleInspectResult>(
    `${root(namespace, ontologyId)}/bundles/inspect?bundleRef=${encodeURIComponent(bundleRef)}`,
  );
}

export async function importOntologyBundle(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  input: { bundleRef: string; database?: string; replace?: boolean; actor?: string },
): Promise<BundleImportResult> {
  return client.post<BundleImportResult>(
    `${root(namespace, ontologyId)}/bundles/import`,
    input,
  );
}
