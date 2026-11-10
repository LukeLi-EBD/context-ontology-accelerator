"""Migration-chain invariants for ``coa_control_plane.platform_db``.

R1 moved the chain out of platform-core; these tests guard the two properties
that must survive the move: the registered head equals the gate constant, and
the registry and the committed SQL files agree in both directions.
"""

from __future__ import annotations

from pathlib import Path

from coa_control_plane.platform_db import (
    MIGRATIONS,
    MIGRATIONS_DIR,
    RETIRED_MIGRATION_VERSIONS,
    SUPPORTED_SCHEMA_VERSION,
    migration_gap_versions,
)


def test_head_matches_version_gate() -> None:
    assert MIGRATIONS[-1][0] == SUPPORTED_SCHEMA_VERSION == 52


def test_registered_versions_are_ordered_unique_and_exclude_retired() -> None:
    versions = [row[0] for row in MIGRATIONS]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions))
    assert not set(versions) & set(RETIRED_MIGRATION_VERSIONS)


def test_gap_helper_accepts_a_fully_migrated_database() -> None:
    applied = {version for version, _filename, _description in MIGRATIONS}
    assert migration_gap_versions(SUPPORTED_SCHEMA_VERSION, applied) == []


def test_registry_and_files_agree() -> None:
    sql_dir = Path(str(MIGRATIONS_DIR))
    registered = {filename for _version, filename, _description in MIGRATIONS}
    on_disk = {path.name for path in sql_dir.glob("V*.sql")}
    assert registered == on_disk
