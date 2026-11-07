"""Offline-window guard for A-Box materialization (design 70).

The online path (publish/rollback) must not start a full materialization when
``reasoning.materialize_online`` is false (the default); status must not run a
full graph COUNT to report the inferred size.
"""

import unittest
from datetime import datetime, timezone

from platform_core.config import ReasoningConfig
from platform_core.reasoning import ReasoningService


class _FakeMeta:
    def __init__(self, pointer_row=None):
        self._pointer_row = pointer_row

    def query(self, sql, params=None):
        if "inferred_pointer" in sql:
            return [self._pointer_row] if self._pointer_row else []
        return []


class _FakeGraph:
    def count_graph(self, graph_iri):
        raise AssertionError("status must not COUNT the inferred graph")


class _FakeReasoner:
    def health(self):
        return {"available": True, "robotVersion": "stub", "engine": "robot"}


def _service(config, pointer_row=None):
    return ReasoningService(
        config,
        _FakeMeta(pointer_row),
        _FakeGraph(),
        _FakeReasoner(),
        None,
        None,
    )


class OfflineMaterializeTest(unittest.TestCase):
    def test_online_materialize_defaults_to_false(self):
        self.assertFalse(ReasoningConfig().materialize_online)

    def test_publish_hook_defers_when_offline(self):
        service = _service(ReasoningConfig())
        result = service.publish_materializer()
        self.assertTrue(result["skipped"])
        self.assertEqual(result["deferred"], "offline_only")
        self.assertEqual(result["inferred"], 0)
        self.assertIsNone(result["jobId"])

    def test_publish_hook_delegates_when_enabled(self):
        service = _service(ReasoningConfig(materialize_online=True))
        service.materialize = lambda: {"jobId": "rsn-stub", "inferred": 7, "skipped": False}
        result = service.publish_materializer()
        self.assertEqual(result["jobId"], "rsn-stub")
        self.assertEqual(result["inferred"], 7)
        self.assertNotIn("deferred", result)

    def test_status_reads_stored_count_without_counting(self):
        row = {
            "name": "default",
            "ontology_version": "ont-1",
            "target_graph": "urn:platform:inferred:ont-1",
            "input_hash": "0" * 64,
            "inferred": 322021,
            "job_id": "rsn-stub",
            "updated_at": datetime.now(timezone.utc),
        }
        status = _service(ReasoningConfig(), row).status()
        self.assertEqual(status["inferredTriples"], 322021)


if __name__ == "__main__":
    unittest.main()
