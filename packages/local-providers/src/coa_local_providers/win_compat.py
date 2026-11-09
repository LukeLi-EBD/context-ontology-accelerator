"""Windows import shim for COA's ``coa_common`` package.

``coa_common/__init__.py`` eagerly imports ``coa_common.embeddings`` →
``coa_common.bedrock_metrics``, which does ``import resource`` (Unix-only) and
later calls ``resource.getrusage(resource.RUSAGE_SELF).ru_maxrss``. On Windows
that import fails before ``coa_metrics.validator`` can be loaded.

Installing a minimal stand-in in ``sys.modules`` lets the upstream parser and
validator be imported unchanged. Nothing in this slice measures process
memory, so the stand-in is never exercised.
"""

from __future__ import annotations

import sys
import types


def ensure_resource_module() -> None:
    """Install a no-op ``resource`` module when the platform has none."""
    if "resource" in sys.modules:
        return

    module = types.ModuleType("resource")
    module.RUSAGE_SELF = 0  # type: ignore[attr-defined]
    module.RUSAGE_CHILDREN = -1  # type: ignore[attr-defined]

    class _Usage:
        ru_maxrss = 0

    module.getrusage = lambda who: _Usage()  # type: ignore[attr-defined]

    sys.modules["resource"] = module


__all__ = ["ensure_resource_module"]
