"""Migration idempotency gate (P1-03): apply the real registry twice on an empty
database and assert the schema is complete, repeatable and gap-free.

The connection is supplied by scripts/ci/migration-idempotency.sh through
MIGRATION_GATE_PG_DSN; this module only owns the assertions.
"""

from __future__ import annotations

import os
import sys

import psycopg
from psycopg.rows import dict_row

from coa_control_plane.platform_db.registry import (
    MIGRATIONS,
    SUPPORTED_SCHEMA_VERSION,
    migration_gap_versions,
)
from coa_control_plane.platform_db.runner import apply_migrations

DSN = os.environ["MIGRATION_GATE_PG_DSN"]

# V52 adds these three columns to each ontology table; V53 adds the pointer index.
OWNED_TABLES = ("ontology_version", "ontology_proposal", "ontology_event")
OWNED_COLUMNS = ("ontology_id", "namespace_id", "attribution_source")
POINTER_INDEX = "graph_pointer_version_idx"

checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, ok, detail))


with psycopg.connect(DSN, row_factory=dict_row) as conn:
    # 1. empty database -> full registry in one run
    first = apply_migrations(conn)
    conn.commit()
    expected = [f"V{version}" for version, _, _ in MIGRATIONS]
    check(
        "first-run-applies-registry",
        first == expected,
        f"applied={len(first)} expected={len(expected)}",
    )
    # 2. the last applied migration is V53
    last = first[-1] if first else None
    check("last-applied-is-V53", last == "V53", f"last={last}")
    # 3. recorded high-water mark equals the code version
    row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) AS v FROM platform.schema_version"
    ).fetchone()
    current = int(row["v"])
    check(
        "max-schema-version",
        current == SUPPORTED_SCHEMA_VERSION == 53,
        f"max={current} supported={SUPPORTED_SCHEMA_VERSION}",
    )
    # 4. second run is a no-op
    second = apply_migrations(conn)
    conn.commit()
    check("second-run-applies-nothing", second == [], f"applied={second}")
    # 5. every registered version at or below the mark has its own row
    history = {
        int(r["version"]) for r in conn.execute("SELECT version FROM platform.schema_version")
    }
    gaps = migration_gap_versions(current, history)
    check("no-migration-gaps", gaps == [], f"gaps={gaps}")

    # 6-8. the nine V52 columns: present, nullable, no default
    cols = {
        (r["table_name"], r["column_name"]): r
        for r in conn.execute(
            "SELECT table_name, column_name, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema='platform' AND table_name = ANY(%s) "
            "AND column_name = ANY(%s)",
            (list(OWNED_TABLES), list(OWNED_COLUMNS)),
        )
    }
    missing = [
        f"{t}.{c}" for t in OWNED_TABLES for c in OWNED_COLUMNS if (t, c) not in cols
    ]
    check("v52-nine-columns-exist", not missing, f"missing={missing}")

    not_nullable = [
        f"{t}.{c}" for t in OWNED_TABLES for c in OWNED_COLUMNS
        if (t, c) in cols and cols[(t, c)]["is_nullable"] != "YES"
    ]
    check("v52-nine-columns-nullable", not not_nullable, f"not_nullable={not_nullable}")

    with_default = [
        f"{t}.{c}" for t in OWNED_TABLES for c in OWNED_COLUMNS
        if (t, c) in cols and cols[(t, c)]["column_default"] is not None
    ]
    check("v52-nine-columns-no-default", not with_default, f"with_default={with_default}")

    # 9. V53 pointer index exists
    index = conn.execute(
        "SELECT 1 FROM pg_indexes WHERE schemaname='platform' AND indexname=%s",
        (POINTER_INDEX,),
    ).fetchone()
    check("v53-pointer-index-exists", index is not None, f"index={POINTER_INDEX}")

failed = [(n, d) for n, ok, d in checks if not ok]
for name, ok, detail in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))

print(f"RESULT: {len(checks) - len(failed)} passed, {len(failed)} failed")
sys.exit(0 if not failed else 1)
