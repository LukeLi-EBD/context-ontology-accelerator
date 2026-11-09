"""N6 MemoryStore: turns written here must show up in N5 get_history."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coa_gateway.conversation_store import SessionNotFound, SqliteConversationStore
from coa_gateway.memory_store import SEARCH_MODE, SqliteMemoryStore


class MemoryStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "sessions.db"
        self.conversation = SqliteConversationStore(self.path)
        self.memory = SqliteMemoryStore(self.path)
        self.session = self.conversation.create("u-1", "ns-1", "roundtrip")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_append_turn_makes_history_non_empty(self) -> None:
        self.assertEqual(self.conversation.get_history(self.session.session_id), [])
        first = self.memory.append_turn(
            self.session.session_id, {"role": "user", "content": "第一轮问题"}
        )
        second = self.memory.append_turn(
            self.session.session_id, {"role": "assistant", "content": "第一轮回答"}
        )
        self.assertGreater(second.turn_id, first.turn_id)
        history = self.conversation.get_history(self.session.session_id, limit=10)
        self.assertEqual([turn["role"] for turn in history], ["user", "assistant"])
        self.assertEqual([turn["content"] for turn in history], ["第一轮问题", "第一轮回答"])

    def test_get_window_returns_last_turns_oldest_first(self) -> None:
        for index in range(4):
            self.memory.append_turn(
                self.session.session_id, {"role": "user", "content": f"turn-{index}"}
            )
        window = self.memory.get_window(self.session.session_id, turns=2)
        self.assertEqual([turn.content for turn in window], ["turn-2", "turn-3"])

    def test_search_is_lexical_and_namespaced(self) -> None:
        self.memory.append_turn(
            self.session.session_id, {"role": "user", "content": "会话历史真的落盘了吗"}
        )
        other = self.conversation.create("u-1", "ns-2", "other")
        self.memory.append_turn(other.session_id, {"role": "user", "content": "落盘"})

        hits = self.memory.search("ns-1", "落盘", top_k=5)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["session_id"], self.session.session_id)
        self.assertEqual(hits[0]["mode"], SEARCH_MODE)
        self.assertEqual(SEARCH_MODE, "lexical-approx")

    def test_search_escapes_like_wildcards(self) -> None:
        self.memory.append_turn(
            self.session.session_id, {"role": "user", "content": "coverage 100% done"}
        )
        self.memory.append_turn(
            self.session.session_id, {"role": "user", "content": "plain text"}
        )
        self.assertEqual(len(self.memory.search("ns-1", "100%", top_k=5)), 1)
        percent_hits = self.memory.search("ns-1", "%", top_k=5)
        self.assertEqual([hit["content"] for hit in percent_hits], ["coverage 100% done"])

    def test_delete_session_and_gc(self) -> None:
        self.memory.append_turn(
            self.session.session_id, {"role": "user", "content": "old"}, at="2020-01-01T00:00:00+00:00"
        )
        self.memory.append_turn(
            self.session.session_id, {"role": "user", "content": "new"}, at="2026-01-01T00:00:00+00:00"
        )
        self.assertEqual(self.memory.gc("2021-01-01T00:00:00+00:00"), 1)
        self.assertEqual(len(self.memory.get_window(self.session.session_id, turns=10)), 1)
        self.assertEqual(self.memory.delete_session(self.session.session_id), 1)
        self.assertEqual(self.conversation.get_history(self.session.session_id), [])

    def test_append_to_missing_session_raises(self) -> None:
        with self.assertRaises(SessionNotFound):
            self.memory.append_turn("no-such-session", {"role": "user", "content": "x"})

    def test_turns_survive_new_store_instance(self) -> None:
        self.memory.append_turn(self.session.session_id, {"role": "user", "content": "persisted"})
        reopened = SqliteConversationStore(self.path)
        history = reopened.get_history(self.session.session_id)
        self.assertEqual([turn["content"] for turn in history], ["persisted"])


if __name__ == "__main__":
    unittest.main()
