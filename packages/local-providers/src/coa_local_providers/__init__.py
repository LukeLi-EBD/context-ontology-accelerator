"""Local, file-backed providers for COA packages.

This package is intentionally *not* a workspace member yet: the root
``pyproject.toml`` cannot resolve until ``smithy-generated/`` exists, so the
package is consumed through ``PYTHONPATH`` instead. See
``doc/_design/80-platform整合进COA可行性-2026-11-08.md`` §5.
"""

from coa_local_providers.win_compat import ensure_resource_module

# Must run before ``coa_metrics`` (and therefore ``coa_common``) is imported.
ensure_resource_module()

from coa_local_providers.json_lookup import JsonDataSourceLookup  # noqa: E402

__all__ = ["JsonDataSourceLookup"]
