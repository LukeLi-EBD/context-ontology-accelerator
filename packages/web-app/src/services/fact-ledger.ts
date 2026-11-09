// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * A-Box fact ledger client (09 §4.7): list, detail, conflicts, retract/restore.
 *
 * Paths are namespace-scoped contract shapes served by the local bridge (8099);
 * the kernel keeps a single ledger, so the namespace segment does not partition
 * rows. Every call goes through `ApiClient` like the other services.
 */
import type { ApiClient } from "../components/ApiClientProvider";

export interface FactObject {
  kind: string;
  value: string;
  iri?: string;
}

export interface FactSource {
  kind?: string;
  documentId?: string | null;
  runId?: string | null;
  candidateId?: string | null;
}

export interface FactEvent {
  eventId: number;
  factId: string;
  action: string;
  actor?: string | null;
  reason?: string | null;
  batchId?: string | null;
  payload?: Record<string, unknown>;
  prevEvent?: number | null;
  hash?: string;
  createdAt?: string;
}

export interface FactRecord {
  factId: string;
  subject: string;
  predicate: string;
  object: FactObject;
  graph: string;
  state: "active" | "retracted" | "superseded" | string;
  source?: FactSource;
  assertedAt?: string;
  retractedAt?: string | null;
  retractReason?: string | null;
  acceptedConflict?: boolean;
  resolution?: string | null;
  resolvedBy?: string | null;
  resolvedAt?: string | null;
  supersededBy?: string | null;
  mergedFrom?: string[] | null;
  conflict?: boolean;
  events?: FactEvent[];
}

export interface FactList {
  state: string;
  items: FactRecord[];
  count: number;
  conflicts?: FactConflict[];
}

export interface FactConflictFact {
  factId: string;
  object: string;
  objectKind: string;
  source?: FactSource;
  assertedAt?: string;
  evidence?: { chunkId?: string; text?: string };
}

export interface FactConflict {
  subject: string;
  predicate: string;
  values: string[];
  accepted: boolean;
  pending: boolean;
  facts: FactConflictFact[];
}

export interface FactConflictList {
  conflicts: FactConflict[];
  count: number;
  pending: number;
  includeAccepted?: boolean;
  /** Latest adjudication per (s,p), including the ones `keep`/`merge` removed from `conflicts`. */
  adjudications?: FactAdjudication[];
}

export interface FactAdjudicationEvent {
  eventId: number;
  action: string;
  actor?: string | null;
  reason?: string | null;
  at: string;
  payload?: Record<string, unknown>;
}

export interface FactAdjudication {
  subject: string;
  predicate: string;
  eventId: number | null;
  action: string | null;
  actor?: string | null;
  reason?: string | null;
  at: string;
  status: "in_effect" | "undone" | string;
  kept?: string | null;
  values: string[];
  object?: string | null;
  undoneBy?: {
    eventId: number;
    actor?: string | null;
    reason?: string | null;
    at: string;
  } | null;
  history: FactAdjudicationEvent[];
  effective: {
    activeCount: number;
    values: string[];
    conflict: boolean;
    acceptedConflict: boolean;
  };
}

export interface FactListQuery {
  state?: string;
  subject?: string;
  predicate?: string;
  sourceDocumentId?: string;
  conflict?: boolean;
  limit?: number;
}

function root(namespace: string): string {
  return `/namespaces/${encodeURIComponent(namespace)}/facts`;
}

export async function listFacts(
  client: ApiClient,
  namespace: string,
  query: FactListQuery = {},
): Promise<FactList> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === "" || value === false) continue;
    params.set(key, String(value));
  }
  const suffix = params.size > 0 ? `?${params.toString()}` : "";
  return client.get<FactList>(`${root(namespace)}${suffix}`);
}

export async function getFact(
  client: ApiClient,
  namespace: string,
  factId: string,
): Promise<FactRecord> {
  return client.get<FactRecord>(`${root(namespace)}/${encodeURIComponent(factId)}`);
}

export async function listFactConflicts(
  client: ApiClient,
  namespace: string,
  includeAccepted = false,
): Promise<FactConflictList> {
  const suffix = includeAccepted ? "?includeAccepted=true" : "";
  return client.get<FactConflictList>(`${root(namespace)}/conflicts${suffix}`);
}

export interface FactActionInput {
  actor: string;
  reason?: string;
}

export async function retractFact(
  client: ApiClient,
  namespace: string,
  factId: string,
  input: FactActionInput,
): Promise<FactRecord> {
  return client.post<FactRecord>(
    `${root(namespace)}/${encodeURIComponent(factId)}/retract`,
    { actor: input.actor, reason: input.reason },
  );
}

export async function restoreFact(
  client: ApiClient,
  namespace: string,
  factId: string,
  input: FactActionInput,
): Promise<FactRecord> {
  return client.post<FactRecord>(
    `${root(namespace)}/${encodeURIComponent(factId)}/restore`,
    { actor: input.actor, reason: input.reason },
  );
}

export interface ResolveConflictInput {
  subject: string;
  predicate: string;
  action: "keep" | "keep_both" | "merge";
  actor: string;
  reason?: string;
  keep?: string;
  mergedObject?: string;
  mergedObjectKind?: string;
  graph?: string;
}

export async function resolveFactConflict(
  client: ApiClient,
  namespace: string,
  input: ResolveConflictInput,
): Promise<Record<string, unknown>> {
  return client.post<Record<string, unknown>>(`${root(namespace)}/conflicts/resolve`, input);
}

export interface UndoConflictInput {
  eventId?: number;
  subject?: string;
  predicate?: string;
  actor: string;
  reason?: string;
  dryRun?: boolean;
}

export async function undoFactConflict(
  client: ApiClient,
  namespace: string,
  input: UndoConflictInput,
): Promise<Record<string, unknown>> {
  return client.post<Record<string, unknown>>(`${root(namespace)}/conflicts/undo`, input);
}
