#!/usr/bin/env python3
"""Static guard: forbid the Oxigraph-hanging SPARQL shapes.

Root causes measured against a live endpoint (E-01 / D1-2, 2026-11-06):
- ``VALUES ?g {...} GRAPH ?g { { ... } UNION { ... } }`` hangs (>25s, 504).
- a grouped subquery wrapping ``BIND`` inside a variable graph (same risk class).
- ``GRAPH ?g { ... OPTIONAL { ... } ... }`` hangs: 50 subjects under
  ``VALUES ?s`` did not return within 35s. Replacing the variable graph with
  one constant ``GRAPH <g>`` per readable graph answered in ~3ms per batch
  (variable graph was ~35x slower even when it returned).

This case scans every SPARQL template assembled in ``platform/src`` and fails
when a variable graph (``GRAPH ?var``) co-occurs with ``UNION``, when a grouped
``{ BIND(...) }`` block sits directly inside a variable graph, or when
``OPTIONAL`` appears anywhere inside a variable-graph block.

Capability boundary: SPARQL is assembled as Python strings. We do NOT parse
SPARQL; we extract string templates per function/module with ``ast`` and apply
regexes plus a balanced-brace scan for the graph body. Dynamic query
construction that hides the pattern from static string literals cannot be
detected. Fixed-graph UNION (``GRAPH <iri>`` or ``FROM <iri>``) is out of scope
by design and is never flagged.

Baseline: this file mirrors ``platform/tests/test_sparql_query_shape.py`` from
branch ``luke`` (commit 45ae42c, 2026-11-06) and adds the third rule
(``variable-graph+optional``). Set ``SPARQL_GUARD_SRC`` to scan another tree.

Whitelist entries must state the reason and the measured timing; do not add an
entry without hitting the endpoint.
"""
from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path
from typing import Iterable

SRC_ROOT = Path(
    os.environ.get("SPARQL_GUARD_SRC")
    or (Path(__file__).resolve().parents[1] / "src")
)

GRAPH_VAR = re.compile(r"GRAPH\s+\?[A-Za-z_]\w*", re.IGNORECASE)
UNION = re.compile(r"\bUNION\b", re.IGNORECASE)
OPTIONAL = re.compile(r"\bOPTIONAL\b", re.IGNORECASE)
QUERY_KEYWORD = re.compile(r"\b(SELECT|ASK|CONSTRUCT|DESCRIBE)\b", re.IGNORECASE)
# A nested group `{ { BIND(...) } }` directly inside a variable graph.
NESTED_BIND = re.compile(
    r"GRAPH\s+\?[A-Za-z_]\w*\s*\{\s*(?:\{\s*)+BIND\s*\(",
    re.IGNORECASE | re.DOTALL,
)
DIRECT_BIND = re.compile(r"GRAPH\s+\?[A-Za-z_]\w*\s*\{\s*BIND\s*\(", re.IGNORECASE)

# (relative path, scope, kind) -> reason + measured timing.
# Keep empty unless a real exemption has been verified against a live endpoint.
WHITELIST: dict[tuple[str, str, str], str] = {
    (
        "platform_core/api.py",
        "browse_ontology_instances",
        "variable-graph+optional",
    ): (
        "pre-existing baseline debt (not D1-2): GRAPH ?g over all graphs + OPTIONAL label, "
        "ORDER BY + LIMIT 20. Measured 265.9ms, rows=20, on tbox+abox:main+abox:synthetic "
        "(agent-platform-oxigraph, 2026-11-07). Owner follow-up: move the label lookup out "
        "of the variable graph."
    ),
    (
        "platform_core/webui.py",
        "ontology",
        "variable-graph+optional",
    ): (
        "pre-existing baseline debt (not D1-2): VALUES ?g + GRAPH ?g with two OPTIONAL "
        "branches (label/subClassOf), no LIMIT. Measured 51.6ms, rows=224, on "
        "tbox+abox:main+abox:synthetic (agent-platform-oxigraph, 2026-11-07). "
        "Owner follow-up: split OPTIONAL lookups per constant graph."
    ),
    (
        "platform_core/webui.py",
        "entities",
        "variable-graph+optional",
    ): (
        "pre-existing baseline debt (not D1-2): VALUES ?g + GRAPH ?g { ?s a ?type . "
        "OPTIONAL label } LIMIT 20. Measured 1.9ms, rows=20 (filtered variant 2.1ms), on "
        "tbox+abox:main+abox:synthetic (agent-platform-oxigraph, 2026-11-07). The 35s hang "
        "required a 50-subject VALUES ?s list plus OPTIONAL. Owner follow-up: drop OPTIONAL "
        "or split the label lookup."
    ),
}


def _string_value(node: ast.AST) -> str:
    """Best-effort string template for Constant / JoinedStr / Add chains."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("{expr}")
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _string_value(node.left) + _string_value(node.right)
    return ""


def _scope_strings(scope: ast.AST) -> list[str]:
    """Collect SPARQL string templates owned by one function/module.

    Docstrings and nested defs are skipped; only chunks that contain a SPARQL
    query keyword are kept, so prose that merely mentions the shapes cannot
    trip the guard.
    """
    chunks: list[str] = []
    body = getattr(scope, "body", [])
    docstring = None
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        if isinstance(body[0].value.value, str):
            docstring = body[0]

    def walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child is not scope:
                continue
            if child is docstring:
                continue
            if isinstance(child, (ast.Constant, ast.JoinedStr, ast.BinOp)):
                text = _string_value(child)
                if text and QUERY_KEYWORD.search(text):
                    chunks.append(text)
                    if isinstance(child, (ast.Constant, ast.JoinedStr)):
                        continue
            walk(child)

    walk(scope)
    return chunks


def _scopes(module: ast.Module) -> Iterable[tuple[str, ast.AST]]:
    yield "<module>", module
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield getattr(node, "name", "<lambda>"), node


def _variable_graph_bodies(text: str) -> list[str]:
    """Return the brace-balanced body after each ``GRAPH ?var``.

    A plain regex cannot tell whether an ``OPTIONAL`` sits inside the graph
    block or after it, so this walks the text and counts braces.
    """
    bodies: list[str] = []
    for match in GRAPH_VAR.finditer(text):
        opening = text.find("{", match.end())
        if opening < 0:
            continue
        depth = 0
        for index in range(opening, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    bodies.append(text[opening + 1 : index])
                    break
    return bodies


def scan_file(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:  # pragma: no cover - defensive
        print(f"SKIP (syntax error) {path}: {exc}")
        return [], []
    relative = path.relative_to(SRC_ROOT).as_posix()
    candidates: list[dict[str, object]] = []
    hits: list[dict[str, object]] = []
    for scope_name, scope in _scopes(tree):
        text = "\n".join(_scope_strings(scope))
        if not GRAPH_VAR.search(text):
            continue
        has_union = bool(UNION.search(text))
        has_nested_bind = bool(NESTED_BIND.search(text))
        direct_bind = bool(DIRECT_BIND.search(text))
        has_optional = any(OPTIONAL.search(body) for body in _variable_graph_bodies(text))
        line = min(
            (getattr(node, "lineno", 10**9) for node in ast.walk(scope)),
            default=0,
        )
        candidate = {
            "file": relative,
            "scope": scope_name,
            "line": line,
            "union": has_union,
            "nestedBind": has_nested_bind,
            "directBind": direct_bind,
            "optional": has_optional,
        }
        candidates.append(candidate)
        if not (has_union or has_nested_bind or has_optional):
            continue
        if has_union:
            kind = "variable-graph+union"
        elif has_nested_bind:
            kind = "variable-graph+nested-bind-group"
        else:
            kind = "variable-graph+optional"
        hits.append(
            {
                "file": relative,
                "scope": scope_name,
                "line": line,
                "kind": kind,
                "directBind": direct_bind,
                "optional": has_optional,
                "whitelisted": (relative, scope_name, kind) in WHITELIST,
            }
        )
    return candidates, hits


def main() -> int:
    candidates: list[dict[str, object]] = []
    hits: list[dict[str, object]] = []
    scanned = 0
    for path in sorted(SRC_ROOT.rglob("*.py")):
        scanned += 1
        file_candidates, file_hits = scan_file(path)
        candidates.extend(file_candidates)
        hits.extend(file_hits)

    print(f"scanned files: {scanned} under {SRC_ROOT}")
    print(f"variable-graph templates: {len(candidates)}")
    for item in candidates:
        if item["union"]:
            risk = "RISK(union)"
        elif item["nestedBind"]:
            risk = "RISK(nested-bind)"
        elif item["optional"]:
            risk = "RISK(optional)"
        else:
            risk = "safe"
        print(
            f"  [{risk}] {item['file']}:{item['line']} scope={item['scope']} "
            f"directBind={item['directBind']} optional={item['optional']}"
        )
    print(f"violations: {len([h for h in hits if not h['whitelisted']])}")
    violations: list[dict[str, object]] = []
    for hit in hits:
        status = "WHITELISTED" if hit["whitelisted"] else "FAIL"
        print(
            f"  [{status}] {hit['file']}:{hit['line']} scope={hit['scope']} "
            f"kind={hit['kind']} directBind={hit['directBind']} optional={hit['optional']}"
        )
        if hit["whitelisted"]:
            print(f"      reason: {WHITELIST[(hit['file'], hit['scope'], hit['kind'])]}")
        else:
            violations.append(hit)

    assert not violations, (
        "variable-graph + UNION/nested-BIND/OPTIONAL SPARQL templates found: "
        + ", ".join(f"{h['file']}:{h['line']} {h['scope']} ({h['kind']})" for h in violations)
    )
    print("OK: no unwhitelisted variable-graph + UNION/nested-BIND/OPTIONAL template")
    return 0


if __name__ == "__main__":
    sys.exit(main())
