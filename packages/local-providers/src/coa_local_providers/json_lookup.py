"""A file-backed :class:`DataSourceLookup` for the COA metric validator.

The implementation consumes a JSON catalog snapshot exported read-only from the
running platform (``GET /catalog/dictionaries``) and answers the seven methods
``coa_metrics.validator`` asks for. It never opens a database connection and
never calls the platform API at validation time — the snapshot is the only
input.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from coa_metrics.lookups import ColumnMetadata, DataSourceLookup


class JsonDataSourceLookup(DataSourceLookup):
    """Answer catalog questions from a JSON snapshot.

    Snapshot shape::

        {
          "data_sources": {
            "platform": {
              "catalog_available": true,
              "rejection_reasons": {"schema.table": "unapproved"},
              "tables": {
                "platform.bank_loan_account": [
                  {"name": "institution", "data_type": "text"}
                ]
              }
            }
          }
        }

    Table names are resolved case-insensitively. A qualified name
    (``schema.table``) matches its exact entry; a bare name matches the single
    entry ending in ``.name``. Ambiguous bare names are *not* answered, mirroring
    ``SmusCatalogDataSourceLookup``'s refusal to guess between assets.
    """

    def __init__(self, snapshot: Mapping[str, Any]) -> None:
        sources = snapshot.get("data_sources", {})
        self._catalog_available: dict[str, bool] = {}
        self._tables: dict[str, dict[str, list[ColumnMetadata]]] = {}
        self._rejections: dict[str, dict[str, str]] = {}

        for data_source_id, entry in sources.items():
            tables = entry.get("tables", {})
            self._catalog_available[data_source_id] = bool(entry.get("catalog_available", True))
            self._tables[data_source_id] = {
                name.lower(): [
                    ColumnMetadata(name=str(col["name"]), data_type=str(col["data_type"]))
                    for col in columns
                ]
                for name, columns in tables.items()
            }
            self._rejections[data_source_id] = {
                name.lower(): reason for name, reason in entry.get("rejection_reasons", {}).items()
            }

    @classmethod
    def from_path(cls, path: str | Path) -> JsonDataSourceLookup:
        """Load a snapshot from a JSON file."""
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    # -- resolution ----------------------------------------------------
    def _resolve(self, data_source_id: str, table_name: str) -> str | None:
        tables = self._tables.get(data_source_id)
        if not tables:
            return None
        declared = table_name.strip().lower()
        if declared in tables:
            return declared
        bare = declared.rsplit(".", 1)[-1]
        matches = [name for name in tables if name.rsplit(".", 1)[-1] == bare]
        return matches[0] if len(matches) == 1 else None

    # -- DataSourceLookup ----------------------------------------------
    def data_source_exists(self, data_source_id: str) -> bool:
        return data_source_id in self._tables

    def table_exists(self, data_source_id: str, table_name: str) -> bool:
        return self._resolve(data_source_id, table_name) is not None

    def get_table_columns(self, data_source_id: str, table_name: str) -> list[ColumnMetadata] | None:
        resolved = self._resolve(data_source_id, table_name)
        if resolved is None:
            return None
        return list(self._tables[data_source_id][resolved])

    def catalog_available(self, data_source_id: str) -> bool:
        return self._catalog_available.get(data_source_id, False)

    def known_tables(self, data_source_id: str) -> set[str]:
        tables = self._tables.get(data_source_id)
        if not tables:
            return set()
        names = set(tables)
        names.update(name.rsplit(".", 1)[-1] for name in tables)
        return names

    def table_rejection_reason(self, data_source_id: str, table_name: str) -> str | None:
        return self._rejections.get(data_source_id, {}).get(table_name.strip().lower())

    def get_column_type(self, data_source_id: str, table_name: str, column_name: str) -> str | None:
        return super().get_column_type(data_source_id, table_name, column_name)


__all__ = ["JsonDataSourceLookup"]
