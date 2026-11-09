"""Postgres QueryExecutor: registry wiring, clear config errors, non-raising health."""

from __future__ import annotations

import unittest

from coa_serve.clients.base import QueryExecutor

from coa_gateway import PostgresQueryExecutor, ProviderNotConfigured, ProviderSettings, build_client, build_gateway

_UNREACHABLE = "host=127.0.0.1 port=1 dbname=platform connect_timeout=1"


class PostgresQueryExecutorTest(unittest.IsolatedAsyncioTestCase):
    def test_contract_conformance(self) -> None:
        self.assertTrue(isinstance(PostgresQueryExecutor(_UNREACHABLE), QueryExecutor))

    def test_registry_builds_from_dsn(self) -> None:
        executor = build_client(
            "query_executor",
            ProviderSettings.from_mapping(
                {"COA_PROVIDER_QUERY_EXECUTOR": "postgres", "COA_EXECUTOR_POSTGRES_DSN": _UNREACHABLE}
            ),
        )
        self.assertIsInstance(executor, PostgresQueryExecutor)

    def test_missing_dsn_is_a_clear_error(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("query_executor", ProviderSettings.from_mapping({"COA_PROVIDER_QUERY_EXECUTOR": "postgres"}))
        self.assertIn("COA_EXECUTOR_POSTGRES_DSN", str(caught.exception))

    def test_athena_is_declared_but_unwired(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("query_executor", ProviderSettings.from_mapping({"COA_PROVIDER_QUERY_EXECUTOR": "athena"}))
        self.assertIn("not wired", str(caught.exception))

    async def test_health_check_never_raises(self) -> None:
        health = await PostgresQueryExecutor(_UNREACHABLE).health_check()
        self.assertFalse(health["ok"])
        self.assertEqual(health["backend"], "postgres")
        self.assertIn("error", health)

    def test_disabled_interface_raises_on_access(self) -> None:
        gateway = build_gateway(
            ProviderSettings.from_mapping({"COA_PROVIDER_VECTOR": "none", "COA_PROVIDER_GRAPH": "none"})
        )
        self.assertFalse(gateway.capabilities()["query_executor"])
        with self.assertRaises(ProviderNotConfigured):
            _ = gateway.query_executor


if __name__ == "__main__":
    unittest.main()
