"""In-memory vector adapter: real cosine ranking + contract filters."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coa_gateway.vector_memory import InMemoryVectorClient

_ENTRIES = [
    {
        "id": "e1",
        "text": "逾期 指标 定义",
        "vector": [1.0, 0.0, 0.0],
        "metadata": {"namespace": "ns1", "entity_type": "Metric", "data_source_id": "ds1", "ontology_ids": ["ont-a"]},
    },
    {
        "id": "e2",
        "text": "逾期 率 计算",
        "vector": [0.0, 1.0, 0.0],
        "metadata": {"namespace": "ns2", "entity_type": "Metric"},
    },
    {
        "id": "e3",
        "text": "无关 文档",
        "vector": [0.7071, 0.7071, 0.0],
        "metadata": {"namespace": "ns1", "entity_type": "Document"},
    },
]


class InMemoryVectorClientTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "vectors.jsonl"
        with self.path.open("w", encoding="utf-8") as handle:
            for entry in _ENTRIES:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.client = InMemoryVectorClient(self.path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    async def test_search_orders_by_cosine(self) -> None:
        hits = await self.client.search([1.0, 0.0, 0.0], top_k=3)
        self.assertEqual([hit.id for hit in hits], ["e1", "e3", "e2"])
        self.assertAlmostEqual(hits[0].score, 1.0, places=6)
        self.assertAlmostEqual(hits[1].score, 0.7071, places=4)

    async def test_search_filters(self) -> None:
        self.assertEqual(
            [hit.id for hit in await self.client.search([1.0, 0.0, 0.0], namespace="ns2")],
            ["e2"],
        )
        self.assertEqual(
            [hit.id for hit in await self.client.search([1.0, 0.0, 0.0], require_mapped=True)],
            ["e1"],
        )
        self.assertEqual(
            [hit.id for hit in await self.client.search([1.0, 0.0, 0.0], entity_type="Document")],
            ["e3"],
        )
        self.assertEqual(
            [hit.id for hit in await self.client.search([1.0, 0.0, 0.0], ontology_ids=["ont-a"])],
            ["e1"],
        )

    async def test_hybrid_combines_lexical_and_vector(self) -> None:
        hits = await self.client.hybrid_search("逾期 指标", [0.0, 1.0, 0.0], top_k=3)
        # e2: cosine 1.0 + lexical 0.5 -> 0.75; e1: cosine 0.0 + lexical 1.0 -> 0.50
        self.assertEqual([hit.id for hit in hits], ["e2", "e1", "e3"])
        self.assertAlmostEqual(hits[0].score, 0.75, places=6)
        self.assertAlmostEqual(hits[1].score, 0.50, places=6)

    async def test_health_check_reports_entries_and_never_raises(self) -> None:
        health = await self.client.health_check()
        self.assertTrue(health["ok"])
        self.assertEqual(health["entries"], 3)
        self.assertEqual(health["backend"], "in-memory")

        missing = await InMemoryVectorClient(Path(self._tmp.name) / "absent.jsonl").health_check()
        self.assertFalse(missing["ok"])
        self.assertIn("FileNotFoundError", missing["error"])


if __name__ == "__main__":
    unittest.main()
