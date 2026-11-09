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

export async function proposeOntologyVersion(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  input: { versionId: string; rationale?: string; againstVersion?: string },
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
): Promise<{ ok?: boolean; proposalId: string; status?: string }> {
  return client.post(
    `${root(namespace, ontologyId)}/proposals/${encodeURIComponent(proposalId)}/review`,
    { decision, comment },
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
    reason?: string;
  },
): Promise<{ ok?: boolean; publishedVersion?: string; semver?: string; graph?: string }> {
  return client.post(`${root(namespace, ontologyId)}/publish`, input);
}

export async function rollbackOntology(
  client: ApiClient,
  namespace: string,
  ontologyId: string,
  input: { targetVersionId: string; planOnly?: boolean; reason?: string },
): Promise<{ ok?: boolean; publishedVersion?: string; replacedVersionId?: string }> {
  return client.post(`${root(namespace, ontologyId)}/rollback`, input);
}
