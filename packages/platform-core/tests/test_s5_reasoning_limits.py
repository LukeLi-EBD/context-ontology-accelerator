"""Split of reasoning.max_input_bytes into source/assembly thresholds.

The two limits must be independently configurable while both default to 50MiB,
and each overrun must name the layer it guards.
"""

import unittest

from platform_core.adapters.reasoner_robot import ReasonerClient
from platform_core.config import ReasoningConfig
from platform_core.errors import PortError

MiB = 1024 * 1024


class ReasoningLimitSplitTest(unittest.TestCase):
    def test_defaults_are_both_50mib(self):
        config = ReasoningConfig()
        self.assertEqual(config.max_source_bytes, 50 * MiB)
        self.assertEqual(config.max_assembly_bytes, 50 * MiB)

    def test_manifest_exposes_both_limits(self):
        limits = ReasonerClient(ReasoningConfig()).manifest().limits
        self.assertEqual(limits["max_source_bytes"], 50 * MiB)
        self.assertEqual(limits["max_assembly_bytes"], 50 * MiB)
        self.assertNotIn("max_input_bytes", limits)

    def test_rdfs_overrun_names_source_layer(self):
        config = ReasoningConfig(max_source_bytes=1024, max_assembly_bytes=50 * MiB)
        client = ReasonerClient(config)
        with self.assertRaises(PortError) as caught:
            client.rdfs_closure(b"x" * 4096, b"")
        error = caught.exception
        self.assertEqual(error.provider_code, "E_REASONING_INPUT_TOO_LARGE")
        self.assertIn("RDFS source input", error.message)
        self.assertIn("reasoning.max_source_bytes=1024", error.message)
        self.assertEqual(error.details["layer"], "source")
        self.assertEqual(error.details["limit"], 1024)

    def test_reason_overrun_names_assembly_layer(self):
        config = ReasoningConfig(
            max_source_bytes=50 * MiB, max_assembly_bytes=2048
        )
        client = ReasonerClient(config)
        with self.assertRaises(PortError) as caught:
            client.reason(b"t" * 1024, b"a" * 4096)
        error = caught.exception
        self.assertEqual(error.provider_code, "E_REASONING_INPUT_TOO_LARGE")
        self.assertIn("reasoning assembly input", error.message)
        self.assertIn("reasoning.max_assembly_bytes=2048", error.message)
        self.assertEqual(error.details["layer"], "assembly")
        self.assertEqual(error.details["limit"], 2048)

    def test_the_two_limits_are_independent(self):
        # Source fits under max_assembly but not under max_source: stage 1 must
        # reject while stage 2's own limit is unaffected.
        config = ReasoningConfig(max_source_bytes=1024, max_assembly_bytes=8192)
        client = ReasonerClient(config)
        with self.assertRaises(PortError):
            client.rdfs_closure(b"x" * 4096, b"")
        self.assertLessEqual(len(b"x" * 4096), config.max_assembly_bytes)

    def test_legacy_key_is_rejected(self):
        with self.assertRaises(ValueError):
            ReasoningConfig(max_input_bytes=50 * MiB)


if __name__ == "__main__":
    unittest.main()
