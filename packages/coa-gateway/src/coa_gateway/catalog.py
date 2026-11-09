"""``DataSourceLookup`` wired from S1's ``JsonDataSourceLookup`` — not a rewrite.

The class stays in :mod:`coa_local_providers.json_lookup`; the gateway only
resolves it from ``COA_PROVIDER_SOURCE_CATALOG=json`` + ``COA_SOURCE_CATALOG_JSON_PATH``.
The import is lazy because that module pulls in ``coa_metrics`` (and, through it,
the AWS SDK); graph-only deployments should not pay for it.

N4 ``SourceCatalog`` (list/describe extensions) is **not** implemented: only the
seven ``DataSourceLookup`` methods the validator actually calls exist.
"""

from __future__ import annotations

from typing import Any


def build_json_source_catalog(path: str) -> Any:
    """Return the S1 class itself, loaded from a catalog snapshot."""
    from coa_local_providers.json_lookup import JsonDataSourceLookup

    return JsonDataSourceLookup.from_path(path)
