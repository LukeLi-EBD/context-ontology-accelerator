import type { ApiClient } from "../components/ApiClientProvider";

/** One RDF term: IRI or literal (with optional datatype). */
export interface EntityTerm {
  kind: "iri" | "literal";
  value: string;
  iri?: string;
  datatype?: string | null;
  lang?: string | null;
}

export interface EntityNode {
  iri: string;
  label: string;
  inferred: boolean;
}

export interface EntityEdge {
  s: string;
  p: string;
  o: string;
  graph: string;
  inferred: boolean;
}

export interface EntityClass {
  iri: string;
  label: string;
  labeled: boolean;
  inferredOnly: boolean;
  instanceCount: number;
  chain: { iri: string; label: string }[];
}

export interface EntityProperty {
  property: string;
  label: string;
  values: EntityTerm[];
}

export interface EntityRequired {
  property: string;
  label: string;
  minCount: number;
  declaredOn: string[];
  values: EntityTerm[];
  valueCount: number;
  satisfied: boolean;
}

export interface EntitySource {
  kind: string;
  ref: string;
  text: string | null;
  resolveUrl: string;
  href: string;
}

export interface EntityBadge {
  state: string;
  label: string;
  basis: string;
  judge?: string | null;
}

/** One fact-ledger row that backs a statement on this entity (summary). */
export interface EntityProvenanceItem {
  factId: string;
  predicate: string;
  object: EntityTerm;
  state: string;
  sourceKind: string | null;
  documentId: string | null;
  candidateId: string | null;
  assertedAt: string;
  conflict: boolean;
}

export interface EntityProvenance {
  count: number;
  items: EntityProvenanceItem[];
  unavailable?: boolean;
}

export interface RelatedMetricBinding {
  role: string | null;
  factTable: string | null;
  entityColumn: string | null;
}

export interface RelatedMetric {
  metricId: string;
  nameZh: string | null;
  domain: string | null;
  grain: string | null;
  publishable: boolean | null;
  bindings: RelatedMetricBinding[];
  matchBasis: string[];
}

export interface EntityRelatedMetrics {
  status: string;
  reason: string | null;
  items: RelatedMetric[];
  matchBasis: string[];
}

export interface EntityDetail {
  iri: string;
  label: string;
  classes: EntityClass[];
  requiredProperties: EntityRequired[];
  requiredStatus: string;
  properties: EntityProperty[];
  neighbors: { nodes: EntityNode[]; edges: EntityEdge[]; truncated: boolean };
  instanceCount: number;
  relatedMetrics: EntityRelatedMetrics;
  sources: EntitySource[];
  evidenceBadge: EntityBadge;
  tbox: { versionId: string | null; semver: string | null; graph?: string | null } | null;
  sampledAt: string;
  /** Named graphs the returned statements came from (contract-level addition). */
  namedGraphs: string[];
  /** Fact-ledger rows for this subject (contract-level addition). */
  provenance: EntityProvenance;
}

/**
 * GetEntity: one A-Box instance by IRI. Read-only; the IRI is percent-encoded so
 * its slashes are not parsed as path separators.
 */
export async function getEntity(
  client: ApiClient,
  iri: string,
  limit = 50,
): Promise<EntityDetail> {
  return client.get<EntityDetail>(
    `/entities/${encodeURIComponent(iri)}?limit=${limit}`,
  );
}

export interface ProvenanceLink {
  kind: string;
  ref?: string | null;
  url?: string | null;
  documentId?: string | null;
}

/** Per-field evidence badge: 有溯源 / 仅推理 / 无. */
export interface ProvenanceField {
  property: string;
  label: string;
  values: EntityTerm[];
  valueText: string | null;
  asserted: boolean;
  inferredOnly: boolean;
  badge: { state: string; label: string; basis: string };
  hasSourceRef: boolean;
  hasProv: boolean;
  links: ProvenanceLink[];
}

export interface EntityProvenanceReport {
  iri: string;
  label: string;
  fields: ProvenanceField[];
  statements: ProvenanceField[];
  activities: {
    activityId: string;
    relation: string;
    object: string | null;
    graph: string | null;
  }[];
  citations: {
    kind: string;
    ref: string | null;
    text?: string | null;
    documentId?: string | null;
    url?: string | null;
  }[];
  summary: {
    total: number;
    evidenced: number;
    inferred: number;
    none: number;
    withSourceRef: number;
    withProv: number;
    coverageRate: number;
  };
  evidenceBadge: EntityBadge;
  namedGraphs: string[];
  provenance: EntityProvenance;
  empty: boolean;
  emptyReason: string | null;
  note: string;
}

/** GetEntityProvenance: per-field three-state badge plus citations, read-only. */
export async function getEntityProvenance(
  client: ApiClient,
  iri: string,
  limit = 50,
): Promise<EntityProvenanceReport> {
  return client.get<EntityProvenanceReport>(
    `/entities/${encodeURIComponent(iri)}/provenance?limit=${limit}`,
  );
}
