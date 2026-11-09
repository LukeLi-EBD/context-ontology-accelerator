"""Ledger graph acceptance: platform graphs always, A-Box graphs only when configured."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from platform_core.facts import _graph_ok

ABOX = "https://coa.local/graph/ns-1/urn%3Acoa%3Aabox%3Adocuments"


class LedgerGraphTest(unittest.TestCase):
    def test_platform_graph_always_accepted(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NDB_GRAPH_URI_BASE", None)
            self.assertTrue(_graph_ok("urn:platform:graph:abox:main"))

    def test_abox_graph_fails_closed_without_base(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NDB_GRAPH_URI_BASE", None)
            self.assertFalse(_graph_ok(ABOX))

    def test_abox_graph_accepted_with_base(self):
        with patch.dict(os.environ, {"NDB_GRAPH_URI_BASE": "https://coa.local/graph"}):
            self.assertTrue(_graph_ok(ABOX))

    def test_non_iri_and_foreign_graph_rejected(self):
        with patch.dict(os.environ, {"NDB_GRAPH_URI_BASE": "https://coa.local/graph"}):
            self.assertFalse(_graph_ok("not an iri"))
            self.assertFalse(_graph_ok("https://elsewhere.example/graph/x"))


if __name__ == "__main__":
    unittest.main()
