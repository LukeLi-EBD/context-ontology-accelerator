"""``python -m coa_runtime matrix`` prints the config matrix; not a service.

Exit code 0 when every interface resolves, 1 when any row is not ``ok``.
This is the command referenced by plan §2 D5 ("配置矩阵可查").
"""

from __future__ import annotations

import sys

from .registry import MISSING, NOT_AVAILABLE, OK, UNKNOWN, default_registry
from .settings import Settings

_BAD = {MISSING, UNKNOWN, NOT_AVAILABLE}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else "matrix"
    if command != "matrix":
        print(f"unknown command {command!r}; usage: python -m coa_runtime matrix", file=sys.stderr)
        return 2

    registry = default_registry()
    rows = registry.matrix(Settings.from_environ())
    width = max(len(row.interface) for row in rows)
    for row in rows:
        key_width = max(len(row.key) for row in rows)
        print(
            f"{row.interface:<{width}}  {row.key:<{key_width}}  {row.status:<13}  "
            f"{row.provider or '-':<18}  {row.context}  {row.detail if row.status != OK else ''}".rstrip()
        )
    bad = sum(1 for row in rows if row.status in _BAD)
    print(f"\n{len(rows) - bad}/{len(rows)} ok, {bad} not resolvable")
    return 0 if bad == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
