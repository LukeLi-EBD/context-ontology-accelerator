"""Unit tests for the migration-statement splitter (no database required).

Run from ``_impl``: ``python -m unittest discover -s tests -p "test_*.py"``
with ``PYTHONPATH=src``.
"""

from __future__ import annotations

import unittest

from platform_core.sqlsplit import split_sql_statements


class SplitSqlStatementsTest(unittest.TestCase):
    def test_line_comment_with_semicolon_is_not_a_split_point(self):
        sql = (
            "-- 迁移说明: 这里的分号; 不是语句分隔符\n"
            "CREATE TABLE demo_line (id int);\n"
            "SELECT 1;\n"
        )
        statements = split_sql_statements(sql)
        self.assertEqual(len(statements), 2, statements)
        self.assertIn("-- 迁移说明: 这里的分号; 不是语句分隔符", statements[0])
        self.assertTrue(statements[0].endswith("CREATE TABLE demo_line (id int)"))

    def test_string_literal_with_semicolon_is_not_a_split_point(self):
        sql = (
            "INSERT INTO demo_str (v) VALUES ('a;b');\n"
            "UPDATE demo_str SET v = 'c;d' WHERE v = 'a;b';\n"
        )
        statements = split_sql_statements(sql)
        self.assertEqual(len(statements), 2, statements)
        self.assertIn("'a;b'", statements[0])
        self.assertIn("'c;d'", statements[1])

    def test_block_comment_and_quoted_identifier(self):
        sql = (
            "/* 块注释; 内含分号 */\n"
            'CREATE TABLE "odd;name" (id int);\n'
            "SELECT 1;\n"
        )
        statements = split_sql_statements(sql)
        self.assertEqual(len(statements), 2, statements)
        self.assertIn("/* 块注释; 内含分号 */", statements[0])
        self.assertIn('"odd;name"', statements[0])

    def test_dollar_quoted_body_with_semicolons(self):
        sql = (
            "CREATE FUNCTION demo_fn() RETURNS int AS $body$ BEGIN; RETURN 1; END; $body$ "
            "LANGUAGE plpgsql;\n"
            "SELECT demo_fn();\n"
        )
        statements = split_sql_statements(sql)
        self.assertEqual(len(statements), 2, statements)
        self.assertIn("$body$ BEGIN; RETURN 1; END; $body$", statements[0])

    def test_empty_and_trailing_statements(self):
        self.assertEqual(split_sql_statements(";;  ;\n-- 只有注释\n"), [])
        self.assertEqual(split_sql_statements("SELECT 1"), ["SELECT 1"])


if __name__ == "__main__":
    unittest.main()
