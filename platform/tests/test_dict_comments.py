"""O-01b: dictionary column comment migration (V42) and coverage display.

Static checks run everywhere: they parse the migration SQL and the frozen
pre-migration baseline, so they prove the 283/375 split and that the 92
existing comments are not touched.

Live checks are opt-in: set ``DICT_COMMENTS_DSN`` to a postgres DSN and they
apply the migration twice, assert 375/375 coverage and byte-identical reruns.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, "/app/src")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

SQL_PATH = Path(__file__).resolve().parents[1] / "src/platform_core/sql/V42__dict_column_comments.sql"
BINDING_SQL_PATH = Path(__file__).resolve().parents[1] / "src/platform_core/sql/V39__dict_bindings.sql"
BASELINE_PATH = Path(__file__).resolve().parent / "data/dict_comments_baseline.json"
BINDINGS_PATH = Path(__file__).resolve().parent / "data/dict_comments_bindings.json"
DOC_PATH = Path(__file__).resolve().parents[2] / "doc/_design/61-字典列注释补齐.md"

STATEMENT = re.compile(
    r"^COMMENT ON COLUMN platform\.([a-z0-9_]+)\.([a-z0-9_]+) IS '(.+)';$"
)
BINDING_ROW = re.compile(
    r"\('([a-z0-9_]+)', '([a-z0-9_]+)', '(https://[^']+)', '(explicit|name_match)', "
    r"([0-9]+(?:\.[0-9]+)?), '([^']*)'\)"
)
CJK = re.compile(r"[\u4e00-\u9fff]")


def load_binding_rows() -> list[tuple[str, str, str, str, float, str]]:
    """Parse the VALUES rows of V39 (they appear twice: INSERT and UPDATE)."""
    text = BINDING_SQL_PATH.read_text(encoding="utf-8")
    rows: list[tuple[str, str, str, str, float, str]] = []
    seen: set[tuple[str, str, str, str, float, str]] = set()
    for line in text.splitlines():
        match = BINDING_ROW.search(line)
        if not match:
            continue
        row = (
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
            float(match.group(5)),
            match.group(6),
        )
        if row not in seen:
            seen.add(row)
            rows.append(row)
    return rows


def load_statements() -> list[tuple[str, str, str]]:
    text = SQL_PATH.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("--"):
            continue
        match = STATEMENT.match(line)
        if not match:
            raise AssertionError(f"unparseable migration line: {line[:80]}")
        rows.append((match.group(1), match.group(2), match.group(3).replace("''", "'")))
    return rows


def load_baseline() -> list[dict]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


class DictCommentStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.statements = load_statements()
        cls.baseline = load_baseline()
        cls.bindings = json.loads(BINDINGS_PATH.read_text(encoding="utf-8"))
        cls.bound = {(r["table"], r["column"]) for r in cls.bindings}
        cls.targets = {(t, c) for t, c, _ in cls.statements}
        cls.old = {(r["table"], r["column"]): r["comment"] for r in cls.baseline if r["comment"]}
        cls.append_only = cls.bound & set(cls.old)
        cls.text = {(t, c): s for t, c, s in cls.statements}

    def test_01_migration_targets_the_283_gaps_plus_14_bound_append_only_columns(self) -> None:
        missing = {(r["table"], r["column"]) for r in self.baseline if not r["comment"]}
        self.assertEqual(len(self.baseline), 375)
        self.assertEqual(len(missing), 283)
        self.assertEqual(len(self.append_only), 14)
        self.assertEqual(self.targets, missing | self.append_only)
        self.assertEqual(len(self.statements), 297)

    def test_02_existing_92_comments_keep_their_meaning(self) -> None:
        self.assertEqual(len(self.old), 92)
        self.assertEqual(self.targets & set(self.old), self.append_only)
        self.assertEqual(len(self.append_only), 14)
        for key in self.append_only:
            old = self.old[key]
            self.assertTrue(
                self.text[key].startswith(old),
                f"{key}: original comment text must be preserved verbatim",
            )
            self.assertIn("https://w3id.org/fsldm/", self.text[key])

    def test_03_coverage_is_375_of_375_after_apply(self) -> None:
        self.assertEqual(len(self.old) + len(set(self.targets) - self.append_only), 375)
        tables = {r["table"] for r in self.baseline}
        self.assertEqual(len(tables), 28)
        self.assertEqual({t for t, _ in self.targets} | {t for t, _ in self.old}, tables)

    def test_04_every_comment_is_chinese_and_non_trivial(self) -> None:
        for table, column, text in self.statements:
            self.assertGreaterEqual(len(text), 8, f"{table}.{column} comment too short")
            self.assertTrue(CJK.search(text), f"{table}.{column} must be Chinese")
            self.assertNotEqual(text.strip(), column, f"{table}.{column} repeats the column name")

    def test_05_statements_are_idempotent_comment_only(self) -> None:
        for table, column, _ in self.statements:
            self.assertTrue(table and column)
        self.assertEqual(len(self.targets), len(self.statements), "duplicate target in V42")
        sql = SQL_PATH.read_text(encoding="utf-8").upper()
        for forbidden in ("INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ", "DROP "):
            self.assertNotIn(forbidden, sql)

    def test_06_bound_columns_carry_property_iri(self) -> None:
        self.assertEqual(len(self.bindings), 79)
        for row in self.bindings:
            key = (row["table"], row["column"])
            self.assertIn(key, self.text)
            self.assertIn(row["propertyIri"], self.text[key], f"{key} must name {row['propertyIri']}")

    def test_07_speculation_markers_match_the_documented_list(self) -> None:
        speculated = sorted(
            f"{t}.{c}" for t, c, text in self.statements if "（推测）" in text
        )
        self.assertEqual(
            speculated,
            sorted(
                [
                    "bank_credit_application.duplicate_group_id",
                    "bank_credit_application.first_flag",
                    "bank_credit_application.internal_flag",
                    "bank_credit_application.test_flag",
                    "bank_credit_facility.internal_flag",
                    "bank_credit_facility.test_flag",
                    "bank_ews_signal.consecutive_partial_count",
                    "bank_ews_signal.other_facility_dpd_90plus",
                    "bank_ews_signal.rating_notch_curr",
                    "bank_ews_signal.rating_notch_prev",
                    "ins_claim_case.claim_amount",
                ]
            ),
        )
        if DOC_PATH.exists():
            doc = DOC_PATH.read_text(encoding="utf-8")
            for item in speculated:
                self.assertIn(item, doc, f"{item} missing from the speculation list")

    def test_08_comment_coverage_helper(self) -> None:
        try:
            from platform_core.catalog import comment_coverage
        except Exception as exc:  # pragma: no cover - import path differs per runner
            self.skipTest(f"platform_core import unavailable: {exc}")
        rows = [
            {"table": "t_a", "column": "c1", "comment": "有注释"},
            {"table": "t_a", "column": "c2", "comment": None},
            {"table": "t_b", "column": "c3", "comment": "有注释"},
        ]
        report = comment_coverage(rows)
        self.assertEqual(report["totals"]["columns"], 3)
        self.assertEqual(report["totals"]["commented"], 2)
        self.assertEqual(report["totals"]["missing"], 1)
        self.assertEqual(report["totals"]["ratePercent"], 66.67)
        self.assertFalse(report["complete"])


class DictBindingStaticTest(unittest.TestCase):
    """V39 must persist exactly the 79 bindings the runtime refresh produced."""

    @classmethod
    def setUpClass(cls) -> None:
        from platform_core.catalog import STATIC_PROPERTIES, is_mappable

        cls.rows = load_binding_rows()
        cls.baseline = load_baseline()
        cls.snapshot = json.loads(BINDINGS_PATH.read_text(encoding="utf-8"))
        cls.published_iris = {iri for _name, iri in STATIC_PROPERTIES}
        cls.is_mappable = staticmethod(is_mappable)

    def test_01_79_unique_rows_cover_real_columns(self) -> None:
        self.assertEqual(len(self.rows), 79)
        keys = {(r[0], r[1]) for r in self.rows}
        self.assertEqual(len(keys), 79, "V39 must not bind the same column twice")
        baseline_keys = {(r["table"], r["column"]) for r in self.baseline}
        missing = sorted(keys - baseline_keys)
        self.assertEqual(missing, [], f"V39 binds columns absent from the 375-column baseline: {missing}")

    def test_02_method_split_is_69_explicit_10_name_match(self) -> None:
        explicit = sum(1 for r in self.rows if r[3] == "explicit")
        name_match = sum(1 for r in self.rows if r[3] == "name_match")
        self.assertEqual((explicit, name_match), (69, 10))

    def test_03_every_iri_is_in_the_published_tbox_mirror(self) -> None:
        unknown = sorted({r[2] for r in self.rows} - self.published_iris)
        self.assertEqual(unknown, [], f"V39 binds IRIs absent from the published T-Box: {unknown}")

    def test_04_matches_the_frozen_refresh_snapshot(self) -> None:
        expected = {
            (r["table"], r["column"], r["propertyIri"], r["bindingMethod"])
            for r in self.snapshot
        }
        actual = {(r[0], r[1], r[2], r[3]) for r in self.rows}
        self.assertEqual(actual, expected, "V39 drifted from the verified refresh snapshot")

    def test_05_mappable_81_and_bound_79(self) -> None:
        mappable = [
            (r["table"], r["column"])
            for r in self.baseline
            if self.is_mappable(r["table"], r["column"])
        ]
        bound = {(r[0], r[1]) for r in self.rows}
        outside = sorted(bound - set(mappable))
        unbound = sorted(set(mappable) - bound)
        self.assertEqual(outside, [], f"V39 bound a column outside the mappable rule: {outside}")
        self.assertEqual(len(mappable), 81)
        self.assertEqual(len(bound), 79)
        self.assertEqual(
            unbound,
            [
                ("bank_loan_account", "period_start"),
                ("cust_master", "registration_date"),
            ],
            "the two weak mappable candidates must stay unbound for manual review",
        )


@unittest.skipUnless(os.environ.get("DICT_COMMENTS_DSN"), "set DICT_COMMENTS_DSN for live checks")
class DictCommentLiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import psycopg

        cls.connect = psycopg.connect
        cls.dsn = os.environ["DICT_COMMENTS_DSN"]
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.baseline = load_baseline()

    def _run_migration(self) -> None:
        with self.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(self.sql)

    def _run_binding_migration(self) -> None:
        sql_text = BINDING_SQL_PATH.read_text(encoding="utf-8")
        with self.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_text)

    def _dictionary_counts(self) -> tuple[int, int, int, int]:
        from platform_core.catalog import MAPPABLE_SQL

        query = f"""
            SELECT count(*) AS rows,
                   count(*) FILTER (
                       WHERE comment IS NOT NULL AND btrim(comment) <> ''
                   ) AS commented,
                   count(*) FILTER (
                       WHERE binding_method <> 'none' OR {MAPPABLE_SQL}
                   ) AS mappable,
                   count(*) FILTER (WHERE binding_method <> 'none') AS bound
              FROM platform.data_dictionary
             WHERE catalog_name = 'platform' AND schema_name = 'platform'
        """
        with self.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return tuple(cur.fetchone())

    def test_live_375_rows_92_comments_81_mappable_79_bound(self) -> None:
        self._run_migration()
        self._run_binding_migration()
        rows, commented, mappable, bound = self._dictionary_counts()
        self.assertEqual(rows, 375, f"dictionary rows actual={rows}, expected 375")
        self.assertEqual(commented, 92, f"dictionary comments actual={commented}, expected 92")
        self.assertEqual(mappable, 81, f"mappable columns actual={mappable}, expected 81")
        self.assertEqual(bound, 79, f"bound columns actual={bound}, expected 79")
        self._run_binding_migration()
        self.assertEqual(
            self._dictionary_counts(),
            (375, 92, 81, 79),
            "V39 must be idempotent",
        )

    def _snapshot(self) -> tuple[int, int, str, dict]:
        query = """
            SELECT c.relname, a.attname, col_description(c.oid, a.attnum)
              FROM pg_class c
              JOIN pg_namespace n ON n.oid = c.relnamespace
              JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
             WHERE n.nspname = 'platform' AND c.relkind = 'r'
               AND c.relname IN (
                   SELECT DISTINCT table_name FROM platform.data_dictionary WHERE source_kind = 'pg'
               )
             ORDER BY c.relname, a.attnum
        """
        with self.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
        digest = hashlib.md5(
            "\n".join(f"{t}.{c}={d}" for t, c, d in rows).encode("utf-8")
        ).hexdigest()
        return len(rows), sum(1 for _, _, d in rows if d), digest, {(t, c): d for t, c, d in rows}

    def test_live_375_of_375_and_rerun_is_stable(self) -> None:
        self._run_migration()
        columns, commented, digest, _ = self._snapshot()
        self.assertEqual(columns, 375)
        self.assertEqual(commented, 375)
        self._run_migration()
        self.assertEqual(self._snapshot()[2], digest, "V42 must be idempotent")

    def test_live_existing_comments_keep_their_text(self) -> None:
        self._run_migration()
        _, _, _, snapshot = self._snapshot()
        bound = {(r["table"], r["column"]) for r in json.loads(BINDINGS_PATH.read_text(encoding="utf-8"))}
        for row in self.baseline:
            if not row["comment"]:
                continue
            key = (row["table"], row["column"])
            current = snapshot.get(key) or ""
            if key in bound:
                self.assertTrue(current.startswith(row["comment"]), f"{key} lost its original text")
            else:
                self.assertEqual(current, row["comment"], f"{key} was overwritten")


if __name__ == "__main__":
    unittest.main(verbosity=2)
