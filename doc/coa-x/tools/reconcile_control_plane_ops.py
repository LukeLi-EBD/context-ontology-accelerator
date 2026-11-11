#!/usr/bin/env python3
"""Reconcile the four views of an operation: model, service mount, generated
client command, and local bridge route.

P0-05 asked for a repeatable, machine-checkable table instead of prose.  The
four views live in four different artefacts and drift independently:

  1. model     : ``operation X`` + its ``@http`` trait in models/src/main/smithy
  2. mounted   : X appears in the ``operations: [...]`` of a ``service`` block
  3. command   : ``<X>Command.ts`` exists in the generated TypeScript client
  4. bridge    : the same method+path template is in ``ROUTES`` of the local
                 bridge (doc/coa-x/tools/coa_api_local.py)

The bridge dispatches on path only (it does not branch on the HTTP verb), so
the bridge column is matched on the path template alone.  That is recorded in
the summary and is the reason a bridge match never proves the verb too.

Usage:
    python doc/coa-x/tools/reconcile_control_plane_ops.py [--root PATH]
        [--csv PATH] [--quiet]

Exit code is 0 when every difference is either absent or registered in
``reconcile-known-gaps.json``, and 1 when at least one unregistered difference
exists. That makes it usable as a CI gate: a new drift without a named owner
turns the gate red, while the six currently registered gaps stay green.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SMITHY_DIR = Path("models/src/main/smithy")
CLIENT_DIRS = {
    "ControlPlaneService": Path("smithy-generated/control-plane-typescript-client/src/commands"),
    "DataLayerService": Path("smithy-generated/data-layer-typescript-client/src/commands"),
}
BRIDGE = Path("doc/coa-x/tools/coa_api_local.py")
KNOWN_GAPS = Path("doc/coa-x/tools/reconcile-known-gaps.json")

HTTP_RE = re.compile(
    r'@http\(\s*method:\s*"([A-Z]+)"\s*,?\s*uri:\s*"([^"]+)"', re.S
)
OPERATION_RE = re.compile(r"\boperation\s+([A-Za-z0-9_]+)\s*\{")
SERVICE_RE = re.compile(r"\bservice\s+([A-Za-z0-9_]+)\s*\{")


@dataclass
class Operation:
    name: str
    method: str
    uri: str
    file: str
    services: list[str] = field(default_factory=list)


def parse_model(root: Path) -> tuple[dict[str, Operation], dict[str, list[str]]]:
    ops: dict[str, Operation] = {}
    services: dict[str, list[str]] = {}
    for path in sorted((root / SMITHY_DIR).glob("*.smithy")):
        raw = path.read_text(encoding="utf-8")
        # Strip line comments so the trait/operation scan cannot pick a stray
        # identifier out of a comment.
        text = "\n".join(line.split("//", 1)[0] for line in raw.splitlines())

        for service in SERVICE_RE.finditer(text):
            name = service.group(1)
            depth = 0
            end = service.end() - 1
            for pos in range(end, len(text)):
                if text[pos] == "{":
                    depth += 1
                elif text[pos] == "}":
                    depth -= 1
                    if depth == 0:
                        end = pos
                        break
            block = text[service.end() : end]
            found = re.search(r"operations:\s*\[(.*?)\]", block, re.S)
            if found:
                services[name] = re.findall(r"[A-Za-z0-9_]+", found.group(1))

        cursor = 0
        for op in OPERATION_RE.finditer(text):
            name = op.group(1)
            if name in ops:
                raise SystemExit(
                    f"operation {name} defined twice ({ops[name].file} and {path.name})"
                )
            http = None
            for candidate in HTTP_RE.finditer(text[cursor : op.start()]):
                http = candidate
            if http is None:
                raise SystemExit(f"operation {name} in {path.name} has no preceding @http")
            ops[name] = Operation(
                name=name,
                method=http.group(1),
                uri=http.group(2),
                file=path.name,
            )
            cursor = op.end()

    for service, names in services.items():
        for name in names:
            if name not in ops:
                raise SystemExit(f"service {service} mounts unknown operation {name}")
            ops[name].services.append(service)
    return ops, services


def parse_commands(root: Path) -> dict[str, str]:
    commands: dict[str, str] = {}
    for service, rel in CLIENT_DIRS.items():
        directory = root / rel
        if not directory.is_dir():
            raise SystemExit(f"generated client directory missing: {rel}")
        for path in sorted(directory.glob("*Command.ts")):
            op = path.name[: -len("Command.ts")]
            commands.setdefault(op, service)
    return commands


def parse_bridge(root: Path) -> set[str]:
    """Return the path templates the local bridge can answer.

    Most routes live in ``ROUTES``; a few are special-cased before dispatch
    (``/health``) and therefore never appear in that list.
    """
    text = (root / BRIDGE).read_text(encoding="utf-8")
    tree = ast.parse(text)
    paths: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id != "ROUTES":
            continue
        for element in node.value.elts:
            first = element.elts[0]
            if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                raise SystemExit("ROUTES entry does not start with a string literal")
            paths.add(first.value)
        break
    else:
        raise SystemExit("ROUTES not found in the local bridge")
    for match in re.finditer(r'path\s*==\s*"([^"]+)"', text):
        paths.add(match.group(1))
    return paths


def load_known_gaps(root: Path) -> dict[str, dict[str, str]]:
    path = root / KNOWN_GAPS
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {entry["match"]: entry for entry in payload["entries"]}


def gap_and_owner(row: dict[str, str]) -> tuple[str, str]:
    if row["model"] == "no":
        return "bridge-only", "bridge"
    missing = []
    if row["mounted"] == "no":
        missing.append("not-mounted")
    if row["command"] == "no":
        missing.append("not-generated")
    if row["bridge"] == "no":
        missing.append("no-bridge-route")
    if not missing:
        return "", ""
    if len(missing) == 3:
        return "orphan", "contract"
    if row["bridge"] == "no":
        owner = "bridge"
    elif row["command"] == "no":
        owner = "contract-generation"
    else:
        owner = "contract"
    return "+".join(missing), owner


def build_rows(root: Path) -> tuple[list[dict[str, str]], dict[str, int]]:
    ops, _ = parse_model(root)
    commands = parse_commands(root)
    bridge = parse_bridge(root)
    known = load_known_gaps(root)

    rows: list[dict[str, str]] = []
    matched_bridge: set[str] = set()
    for op in sorted(ops.values(), key=lambda item: item.name):
        in_bridge_scope = "ControlPlaneService" in op.services
        bridge_hit = op.uri in bridge
        if bridge_hit:
            matched_bridge.add(op.uri)
        row = {
            "service": ",".join(op.services) or "-",
            "op": op.name,
            "http": f"{op.method} {op.uri}",
            "model": "yes",
            "mounted": "yes" if op.services else "no",
            "command": "yes" if op.name in commands else "no",
            "bridge": "yes" if bridge_hit else ("no" if in_bridge_scope else "n/a"),
        }
        row["gap"], row["owner"] = gap_and_owner(row)
        entry = known.get(f"op:{op.name}") or known.get(f"http:{row['http']}")
        row["registered"] = "yes" if row["gap"] and entry else ""
        row["due"] = entry.get("due", "") if row["gap"] and entry else ""
        row["reason"] = entry.get("reason", "") if row["gap"] and entry else ""
        if entry:
            row["owner"] = entry.get("owner", row["owner"])
        rows.append(row)

    for uri in sorted(
        path for path in bridge - matched_bridge if path.startswith("/namespaces/")
    ):
        row = {
            "service": "-",
            "op": "-",
            "http": f"? {uri}",
            "model": "no",
            "mounted": "no",
            "command": "no",
            "bridge": "yes",
        }
        row["gap"], row["owner"] = gap_and_owner(row)
        entry = known.get(f"http:? {uri}")
        row["registered"] = "yes" if entry else ""
        row["due"] = entry.get("due", "") if entry else ""
        row["reason"] = entry.get("reason", "") if entry else ""
        if entry:
            row["owner"] = entry.get("owner", row["owner"])
        rows.append(row)

    gaps = [row for row in rows if row["gap"]]
    summary = {
        "model_ops": len(ops),
        "control_plane_ops": sum(
            1 for op in ops.values() if "ControlPlaneService" in op.services
        ),
        "data_layer_ops": sum(
            1 for op in ops.values() if "DataLayerService" in op.services
        ),
        "mounted_ops": sum(1 for op in ops.values() if op.services),
        "commands": len(commands),
        "bridge_routes": len(bridge),
        "rows": len(rows),
        "gaps": len(gaps),
        "registered_gaps": sum(1 for row in gaps if row["registered"] == "yes"),
        "unregistered_gaps": sum(1 for row in gaps if row["registered"] != "yes"),
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--csv", type=Path, help="write the full table to this path")
    parser.add_argument("--quiet", action="store_true", help="only print the summary")
    args = parser.parse_args()

    rows, summary = build_rows(args.root)
    columns = [
        "service",
        "op",
        "http",
        "model",
        "mounted",
        "command",
        "bridge",
        "gap",
        "owner",
        "registered",
        "due",
        "reason",
    ]

    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    if not args.quiet:
        print("\t".join(columns))
        for row in rows:
            print("\t".join(row[name] for name in columns))

    print("\nsummary")
    for key, value in summary.items():
        print(f"  {key:16} {value}")
    print(
        "  bridge note      path-only match; the bridge dispatches on path, "
        "so a yes does not prove the HTTP verb. DataLayerService ops are n/a: "
        "the local bridge only fronts the control plane."
    )
    return 0 if summary["unregistered_gaps"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
