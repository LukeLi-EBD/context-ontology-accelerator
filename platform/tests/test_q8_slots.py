"""Q8-a: configuration opens every known provider, rejects only unknowns.

Run inside the platform container:
  docker compose exec -T -e PYTHONPATH=/app/src platform \
    python /tmp/hosttests/test_q8_slots.py
"""

import tempfile
import unittest
from pathlib import Path

import yaml

from platform_core.config import load_config
from platform_core.errors import EXIT_CONFIG, PlatformError, PortError
from platform_core.reasoning import ReasoningService

BASE = {"database": {"url": "postgresql://platform:platform_dev@postgres:5432/platform"}}


def load(overrides: dict, environ: dict | None = None):
    doc = dict(BASE)
    for key, value in overrides.items():
        if isinstance(value, dict):
            doc.setdefault(key, {}).update(value)
        else:
            doc[key] = value
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
        yaml.safe_dump(doc, handle)
        path = handle.name
    try:
        return load_config(path, environ=environ or {})
    finally:
        Path(path).unlink(missing_ok=True)


class SlotConfigTests(unittest.TestCase):
    def _assert_error(self, overrides: dict, code: str, key: str) -> None:
        with self.assertRaises(PlatformError) as ctx:
            load(overrides)
        self.assertEqual(ctx.exception.code, code, ctx.exception.detail)
        self.assertEqual(ctx.exception.key, key)
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFIG)

    # ---- graph.provider ------------------------------------------------
    def test_1_graph_provider_distinguishes_unknown_from_missing(self):
        self._assert_error({"graph": {"provider": "nope"}}, "E_PROVIDER_INVALID", "graph.provider")
        self._assert_error(
            {"graph": {"provider": "pyoxigraph"}},
            "E_PROVIDER_NOT_IMPLEMENTED",
            "graph.provider",
        )
        self._assert_error(
            {"graph": {"provider": "age"}},
            "E_PROVIDER_NOT_IMPLEMENTED",
            "graph.provider",
        )

    def test_2_graph_provider_accepts_implemented_backends(self):
        bundle = load({"graph": {"provider": "oxigraph-http"}})
        self.assertEqual(bundle.config.graph.provider, "oxigraph-http")
        bundle = load({"graph": {"provider": "oxigraph"}})
        self.assertEqual(bundle.config.graph.provider, "oxigraph-http")
        self.assertTrue(any("alias" in item for item in bundle.warnings), bundle.warnings)
        bundle = load({"graph": {"provider": "fuseki"}})
        self.assertEqual(bundle.config.graph.provider, "fuseki")

    # ---- reasoning.engine / mode ---------------------------------------
    def test_3_reasoning_engine_opens_enum_and_flags_missing(self):
        self._assert_error(
            {"reasoning": {"engine": "konclude"}},
            "E_PROVIDER_NOT_IMPLEMENTED",
            "reasoning.engine",
        )
        self._assert_error(
            {"reasoning": {"engine": "elk"}},
            "E_PROVIDER_NOT_IMPLEMENTED",
            "reasoning.engine",
        )
        self._assert_error(
            {"reasoning": {"engine": "mystery"}},
            "E_PROVIDER_INVALID",
            "reasoning.engine",
        )
        bundle = load(
            {
                "reasoning": {
                    "engine": "hermit",
                    "mode": "validate",
                    "profile": "OWL2DL",
                }
            }
        )
        self.assertEqual(bundle.config.reasoning.engine, "hermit")

    def test_4_reasoning_mode_on_demand_is_recognised_but_not_implemented(self):
        bundle = load({"reasoning": {"mode": "on-demand"}})
        self.assertEqual(bundle.config.reasoning.mode, "on-demand")
        self.assertTrue(
            any("on-demand" in item for item in bundle.warnings), bundle.warnings
        )
        service = ReasoningService(bundle.config.reasoning, None, None, None, None, None)
        with self.assertRaises(PortError) as ctx:
            service.materialize()
        self.assertEqual(
            ctx.exception.provider_code, "E_REASONING_ON_DEMAND_NOT_IMPLEMENTED"
        )

    # ---- storage --------------------------------------------------------
    def test_5_large_object_provider_reports_missing_implementation(self):
        self._assert_error(
            {"storage": {"large_object_provider": "pg"}},
            "E_PROVIDER_NOT_IMPLEMENTED",
            "storage.large_object_provider",
        )
        self._assert_error(
            {"storage": {"large_object_provider": "silo"}},
            "E_PROVIDER_NOT_IMPLEMENTED",
            "storage.large_object_provider",
        )
        self._assert_error(
            {"storage": {"provider": "silo"}},
            "E_PROVIDER_NOT_IMPLEMENTED",
            "storage.provider",
        )

    # ---- llm.preset -----------------------------------------------------
    def test_6_llm_preset_fills_defaults_and_explicit_wins(self):
        bundle = load({"llm": {"preset": "deepseek"}})
        self.assertEqual(bundle.config.llm.base_url, "https://api.deepseek.com/v1")
        self.assertEqual(bundle.config.llm.model, "deepseek-chat")
        self.assertEqual(bundle.config.llm.api_key_env, "DEEPSEEK_API_KEY")
        self.assertTrue(any("preset=deepseek" in item for item in bundle.warnings))

        bundle = load(
            {
                "llm": {
                    "preset": "volcano-ark",
                    "base_url": "https://my-ark.example/coding/v3",
                    "model": "ep-real",
                }
            }
        )
        self.assertEqual(bundle.config.llm.base_url, "https://my-ark.example/coding/v3")
        self.assertEqual(bundle.config.llm.model, "ep-real")


if __name__ == "__main__":
    unittest.main(verbosity=2)
