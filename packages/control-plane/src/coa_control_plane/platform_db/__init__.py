"""Platform database schema: migrations, version gate and the forward runner.

Why this package, and why inside ``coa_control_plane`` (R1 of the platform-core
teardown):

* The chain is live code. It is the only source of truth for the local
  ``platform`` / ``serve_local`` databases, and the local stack and its tools
  must be able to migrate without importing the package that R3 archives.
* ``coa_control_plane.metadata_store`` is not the home: it re-exports the SMUS
  metadata-store client, an unrelated concern.
* A new top-level package would add a distribution for a single table schema.

So placement is: registry (``registry.py``) + runner (``runner.py``) + SQL files
(``migrations/``) here; the ``MetadataPg`` adapter stays in ``platform-core``
until R2/R3 and delegates here, keeping one registry and one version gate.

The SQL files are byte-for-byte the committed platform-core files; migration
numbers never change (retired 35/36 stay empty, current head is 49).
"""

from coa_control_plane.platform_db.registry import (
    MIGRATION_GAP_HINT,
    MIGRATIONS,
    MIGRATIONS_DIR,
    MIGRATIONS_SUBDIR,
    RETIRED_MIGRATION_VERSIONS,
    SUPPORTED_SCHEMA_VERSION,
    migration_gap_versions,
    migration_text,
)
from coa_control_plane.platform_db.runner import MigrationGateError, apply_migrations

__all__ = [
    "MIGRATION_GAP_HINT",
    "MIGRATIONS",
    "MIGRATIONS_DIR",
    "MIGRATIONS_SUBDIR",
    "MigrationGateError",
    "RETIRED_MIGRATION_VERSIONS",
    "SUPPORTED_SCHEMA_VERSION",
    "apply_migrations",
    "migration_gap_versions",
    "migration_text",
]
