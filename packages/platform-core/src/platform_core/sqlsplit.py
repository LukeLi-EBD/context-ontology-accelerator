"""Compatibility shim: SQL splitting moved to the COA control-plane package.

R1 of the platform-core teardown moved the migration chain (registry, runner,
SQL files, splitter) to ``coa_control_plane.platform_db``. The implementation
is not duplicated here; this module only keeps the old import path working for
callers that have not moved yet. It is deleted together with platform-core.
"""

from __future__ import annotations

from coa_control_plane.platform_db.sqlsplit import split_sql_statements

__all__ = ["split_sql_statements"]
