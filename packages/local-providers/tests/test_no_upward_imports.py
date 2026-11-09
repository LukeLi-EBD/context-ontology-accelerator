"""Architecture guard: ``local-providers`` must not import a service package.

The reported defect was ``query_pg.py`` importing ``coa_serve.clients.base``.
The fix moved the four legacy contracts into ``coa_local_providers.contracts``;
this test keeps the direction from flipping back. It parses imports instead of
grepping text so docstrings that mention the old path do not fail it.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "coa_local_providers"
UPWARD = ("coa_serve",)


def _modules(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.module, node.lineno))
        elif isinstance(node, ast.Import):
            found.extend((alias.name, node.lineno) for alias in node.names)
    return found


def test_no_upward_service_imports() -> None:
    offenders = [
        f"{path.relative_to(PACKAGE)}:{line} imports {module}"
        for path in PACKAGE.rglob("*.py")
        for module, line in _modules(path)
        if module.split(".")[0] in UPWARD
    ]
    assert offenders == [], "local-providers 反向依赖服务包: " + ", ".join(offenders)
