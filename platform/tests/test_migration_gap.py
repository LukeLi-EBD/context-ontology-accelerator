"""迁移断档守卫（E_DB_MIGRATION_GAP）单元测试。

不连接数据库：用一个按 SQL 文本分派的最小假连接模拟 platform.schema_version，
只验证 migrate() 的版本判定分支，不执行任何真实 DDL。
"""

from __future__ import annotations

import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, "/app/src")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_core.adapters import metadata_pg
from platform_core.adapters.metadata_pg import (
    MIGRATION_GAP_HINT,
    RETIRED_MIGRATION_VERSIONS,
    MetadataPg,
    migration_gap_versions,
)
from platform_core.errors import PlatformError


class _FakeCursor:
    def __init__(self, rows: list[dict] | None = None, rowcount: int = 1) -> None:
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self) -> dict | None:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list[dict]:
        return list(self._rows)


class _FakeTx:
    def __enter__(self) -> "_FakeTx":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


class _FakeConn:
    """仅实现 migrate() 用到的 execute/transaction 调用。"""

    def __init__(self, current: int, versions: list[int]) -> None:
        self._current = current
        self._versions = versions

    def transaction(self) -> _FakeTx:
        return _FakeTx()

    def execute(self, sql: str, params: tuple | list = ()) -> _FakeCursor:
        if "pg_advisory_xact_lock" in sql:
            return _FakeCursor()
        if "to_regclass" in sql:
            if "schema_version" in sql:
                return _FakeCursor([{"reg": "platform.schema_version"}])
            return _FakeCursor([{"reg": None}])
        if "SELECT version FROM" in sql:
            return _FakeCursor([{"version": v} for v in self._versions])
        if "COALESCE(MAX(version)" in sql:
            return _FakeCursor([{"v": self._current}])
        return _FakeCursor()


class _FakePool:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    @contextmanager
    def connection(self):
        yield self._conn


def _meta(current: int, versions: list[int]) -> MetadataPg:
    meta = MetadataPg("postgresql://fake/db")
    meta._pool = _FakePool(_FakeConn(current, versions))
    return meta


REGISTERED = [row[0] for row in metadata_pg.MIGRATIONS]


class MigrationGapTest(unittest.TestCase):
    def test_registered_versions_are_unique_and_exclude_retired(self) -> None:
        self.assertEqual(len(REGISTERED), len(set(REGISTERED)))
        for version in RETIRED_MIGRATION_VERSIONS:
            self.assertNotIn(version, REGISTERED)

    def test_normal_ascending_upgrade_does_not_raise(self) -> None:
        meta = _meta(current=34, versions=[v for v in REGISTERED if v <= 34])
        result = meta.migrate()
        self.assertEqual(result["applied"], ["V37", "V38", "V39", "V40"])

    def test_lower_version_inserted_into_registry_raises_gap(self) -> None:
        # 人为向注册表插入一个低于当前版本的未退休迁移，且历史表没有它的记录。
        patched = list(metadata_pg.MIGRATIONS) + [
            (33, "V33__late_fix.sql", "late registry fix")
        ]
        history = [v for v in REGISTERED if v <= 37 and v != 33]
        with mock.patch.object(metadata_pg, "MIGRATIONS", patched):
            meta = _meta(current=37, versions=history)
            with self.assertRaises(PlatformError) as ctx:
                meta.migrate()
        error = ctx.exception
        self.assertEqual(error.code, "E_DB_MIGRATION_GAP")
        self.assertIn("33", error.detail)
        self.assertIn("37", error.detail)
        self.assertIn("35", error.detail)
        self.assertIn("36", error.detail)
        self.assertIn(MIGRATION_GAP_HINT, error.detail)

    def test_retired_versions_do_not_raise(self) -> None:
        # 注册表里保留 35/36 的空号位，历史表没有对应行，也不应报缺口。
        patched = list(metadata_pg.MIGRATIONS) + [
            (35, "V35__c2_quota.sql", "withdrawn C2 branch"),
            (36, "V36__unused.sql", "never used"),
        ]
        history = [v for v in REGISTERED if v <= 34] + [37, 38, 39, 40]
        with mock.patch.object(metadata_pg, "MIGRATIONS", patched):
            meta = _meta(current=40, versions=history)
            result = meta.migrate()
        self.assertEqual(result["applied"], [])

    def test_newer_database_still_reports_mismatch(self) -> None:
        meta = _meta(current=99, versions=[v for v in REGISTERED if v <= 37])
        with self.assertRaises(PlatformError) as ctx:
            meta.migrate()
        self.assertEqual(ctx.exception.code, "E_DB_MIGRATION_MISMATCH")
        self.assertIn("99", ctx.exception.detail)

    def test_gap_helper_without_history_on_fresh_database(self) -> None:
        # 能力边界：历史表不存在时全新库 current=0，无法判定缺口。
        self.assertEqual(migration_gap_versions(0, None), [])

    def test_gap_helper_ignores_retired_and_applied(self) -> None:
        registry = [(1, "a", ""), (2, "b", ""), (35, "c", ""), (36, "d", ""), (37, "e", "")]
        self.assertEqual(migration_gap_versions(37, {1, 2, 37}, registry), [])


if __name__ == "__main__":
    unittest.main()
