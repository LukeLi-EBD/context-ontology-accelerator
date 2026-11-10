// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from "vitest";
import {
  buildClassTree,
  defaultExpandedIds,
  type ClassTreeEntry,
} from "./class-tree";

const entry = (
  uri: string,
  label: string,
  parents?: string[],
): ClassTreeEntry => ({ uri, label, parents });

describe("buildClassTree", () => {
  it("nests subClassOf parents under their children's parents, three levels deep", () => {
    const tree = buildClassTree([
      entry("urn:party", "Party"),
      entry("urn:org", "Organization", ["urn:party"]),
      entry("urn:bank", "Bank", ["urn:org"]),
      entry("urn:customer", "Customer", ["urn:party"]),
    ]);

    expect(tree).toHaveLength(1);
    expect(tree[0]!.uri).toBe("urn:party");
    expect(tree[0]!.children.map((c) => c.uri)).toEqual([
      "urn:customer",
      "urn:org",
    ]);
    expect(tree[0]!.children[1]!.children).toEqual([
      { uri: "urn:bank", label: "Bank", children: [] },
    ]);
  });

  it("keeps a class whose parent is outside the set at the top level", () => {
    const tree = buildClassTree([
      entry("urn:thing", "Thing", ["urn:external"]),
      entry("urn:org", "Organization", ["urn:thing"]),
    ]);

    expect(tree.map((n) => n.uri)).toEqual(["urn:thing"]);
    expect(tree[0]!.children[0]!.uri).toBe("urn:org");
  });

  it("places each class once when subClassOf points in a cycle", () => {
    const tree = buildClassTree([
      entry("urn:a", "A", ["urn:b"]),
      entry("urn:b", "B", ["urn:a"]),
    ]);

    const uris: string[] = [];
    const walk = (nodes: ReturnType<typeof buildClassTree>) => {
      for (const node of nodes) {
        uris.push(node.uri);
        walk(node.children);
      }
    };
    walk(tree);
    expect(uris.sort()).toEqual(["urn:a", "urn:b"]);
  });

  it("sorts siblings by label", () => {
    const tree = buildClassTree([
      entry("urn:root", "Root"),
      entry("urn:z", "Zeta", ["urn:root"]),
      entry("urn:a", "Alpha", ["urn:root"]),
    ]);
    expect(tree[0]!.children.map((c) => c.label)).toEqual(["Alpha", "Zeta"]);
  });
});

describe("defaultExpandedIds", () => {
  it("expands nodes with children down to the second level, so three levels show", () => {
    const tree = buildClassTree([
      entry("urn:a", "A"),
      entry("urn:b", "B", ["urn:a"]),
      entry("urn:c", "C", ["urn:b"]),
      entry("urn:d", "D", ["urn:c"]),
    ]);

    expect(defaultExpandedIds(tree)).toEqual(["urn:a", "urn:b"]);
  });
});
