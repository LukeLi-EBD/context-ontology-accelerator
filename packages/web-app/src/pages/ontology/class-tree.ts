// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/** One class row from an ontology-overview call, reduced to what the tree needs. */
export interface ClassTreeEntry {
  uri: string;
  label: string;
  /** `rdfs:subClassOf` parents, nearest first; absent for roots. */
  parents?: string[];
}

export interface ClassTreeNode {
  uri: string;
  label: string;
  children: ClassTreeNode[];
}

function labelOf(entries: Map<string, ClassTreeEntry>, uri: string): string {
  return entries.get(uri)?.label || uri;
}

function byLabel(
  entries: Map<string, ClassTreeEntry>,
): (a: string, b: string) => number {
  return (a, b) => labelOf(entries, a).localeCompare(labelOf(entries, b));
}

/**
 * Build the class hierarchy for the Explorer's Tree view from the same
 * ontology-overview rows the List view already loads.
 *
 * A class hangs under its first parent that is present in the set. Parents
 * outside the set (a foundational super-class such as `schema:Thing`) are
 * treated as roots, so their subtree stays reachable instead of disappearing.
 * Each class is placed exactly once, which also breaks a `subClassOf` cycle
 * (invalid RDF, but a broken graph must not blank the tree).
 */
export function buildClassTree(entries: ClassTreeEntry[]): ClassTreeNode[] {
  const byUri = new Map(entries.map((entry) => [entry.uri, entry]));
  const childrenOf = new Map<string, string[]>();
  const roots: string[] = [];

  for (const entry of entries) {
    const parent = (entry.parents ?? []).find(
      (uri) => uri !== entry.uri && byUri.has(uri),
    );
    if (parent) {
      const siblings = childrenOf.get(parent) ?? [];
      siblings.push(entry.uri);
      childrenOf.set(parent, siblings);
    } else {
      roots.push(entry.uri);
    }
  }

  const placed = new Set<string>();
  const build = (uri: string): ClassTreeNode | undefined => {
    if (placed.has(uri)) return undefined;
    placed.add(uri);
    const node: ClassTreeNode = {
      uri,
      label: labelOf(byUri, uri),
      children: [],
    };
    for (const child of (childrenOf.get(uri) ?? []).sort(byLabel(byUri))) {
      const built = build(child);
      if (built) node.children.push(built);
    }
    return node;
  };

  const nodes = roots
    .sort(byLabel(byUri))
    .map(build)
    .filter((node): node is ClassTreeNode => node !== undefined);

  // Anything still unplaced sits in a cycle with no root; surface it at the top
  // rather than dropping classes from the tree.
  for (const entry of [...entries].sort((a, b) => byLabel(byUri)(a.uri, b.uri))) {
    if (placed.has(entry.uri)) continue;
    const node = build(entry.uri);
    if (node) nodes.push(node);
  }
  return nodes;
}

/**
 * Ids to expand initially: every node with children up to the second level, so
 * the tree opens three levels deep — the depth promised for the class tree.
 */
export function defaultExpandedIds(nodes: ClassTreeNode[]): string[] {
  const ids: string[] = [];
  const walk = (node: ClassTreeNode, depth: number) => {
    if (node.children.length === 0 || depth >= 2) return;
    ids.push(node.uri);
    for (const child of node.children) walk(child, depth + 1);
  };
  for (const node of nodes) walk(node, 0);
  return ids;
}
