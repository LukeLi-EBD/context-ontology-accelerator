"""Contract conformance: the local classes ARE the upstream COA protocols.

Imports the real ``coa_serve.clients.base`` module, so this runs where the COA
serve package is importable (the gateway verify image; see README).
"""

from __future__ import annotations

import unittest

from coa_local_providers.json_lookup import JsonDataSourceLookup
from coa_metrics.lookups import DataSourceLookup
from coa_serve.clients.base import GraphClient, QueryExecutor, VectorClient

from coa_gateway import FusekiGraphClient, InMemoryVectorClient, OxigraphGraphClient, PostgresQueryExecutor


class ContractConformanceTest(unittest.TestCase):
    def test_graph_implementations_satisfy_graph_client(self) -> None:
        self.assertTrue(isinstance(OxigraphGraphClient("http://oxigraph:7878"), GraphClient))
        self.assertTrue(isinstance(FusekiGraphClient("http://fuseki:3030"), GraphClient))

    def test_in_memory_vector_satisfies_vector_client(self) -> None:
        self.assertTrue(isinstance(InMemoryVectorClient("D:/tmp/vectors.jsonl"), VectorClient))

    def test_postgres_executor_satisfies_query_executor(self) -> None:
        self.assertTrue(isinstance(PostgresQueryExecutor("host=127.0.0.1 port=1 dbname=x"), QueryExecutor))

    def test_catalog_is_the_s1_lookup_class(self) -> None:
        # The gateway reuses S1's class; it does not define its own lookup.
        self.assertTrue(issubclass(JsonDataSourceLookup, DataSourceLookup))


if __name__ == "__main__":
    unittest.main()
