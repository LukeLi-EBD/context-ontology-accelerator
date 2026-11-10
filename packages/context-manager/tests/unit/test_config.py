# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for configuration loading."""

from unittest.mock import MagicMock, patch

import pytest
import structlog.testing
from coa_ports import PortError, PortErrorCode
from coa_serve.config import ServiceConfig, load_config


class _FakeConfigProvider:
    """Stands in for the ``ConfigProvider`` port resolved by ``_config_provider``."""

    def __init__(self, value: str = "gr-12345") -> None:
        self.value = value
        self.calls: list[str] = []
        self.error: Exception | None = None

    def get(self, name: str) -> str:
        self.calls.append(name)
        if self.error is not None:
            raise self.error
        return self.value


@pytest.fixture(autouse=True)
def fake_ssm(monkeypatch):
    """Replace the config port with an in-memory fake for every test in this module."""
    provider = _FakeConfigProvider()
    monkeypatch.setattr("coa_serve.config._config_provider", lambda: provider)
    return provider


@pytest.mark.unit
class TestLoadConfig:
    def test_loads_config_with_ssm(self, fake_ssm):
        config = load_config()

        assert isinstance(config, ServiceConfig)
        assert config.guardrail_id == "gr-12345"
        assert config.retrieval_guardrail_id == "gr-12345"
        assert fake_ssm.calls == [
            "/coa/bedrock/guardrail-id",
            "/coa/bedrock/retrieval-guardrail-id",
            "/coa/bedrock/retrieval-guardrail-version",
        ]

    def test_missing_ssm_parameter_returns_empty_in_local(self, fake_ssm):
        fake_ssm.error = PortError(PortErrorCode.NOT_FOUND, "ParameterNotFound")

        config = load_config()
        assert config.guardrail_id == ""

    @patch.dict("os.environ", {"ENVIRONMENT": "production"})
    def test_missing_ssm_parameter_returns_empty_guardrail(self, fake_ssm):
        """Guardrail SSM param missing is not fatal — enforcement is at Synthesizer level."""
        fake_ssm.error = PortError(PortErrorCode.NOT_FOUND, "ParameterNotFound")

        config = load_config()
        assert config.guardrail_id == ""

    @patch.dict("os.environ", {"ENVIRONMENT": "production"})
    def test_ssm_access_denied_returns_empty_guardrail(self, fake_ssm):
        """SSM access errors are non-fatal for guardrail (enforcement at Synthesizer)."""
        fake_ssm.error = PortError(
            PortErrorCode.INTERNAL,
            "AccessDeniedException",
            provider_code="AccessDeniedException",
        )

        config = load_config()
        assert config.guardrail_id == ""

    def test_the_disable_switch_clears_both_guardrails(self):
        """Both, not one: "was the guardrail on for this request?" needs one answer.

        The primary guardrail masks PII in the question and the retrieval one screens
        chunks, so a benchmark that turned off only the first would still be measuring
        a screened corpus on any Tier-3 arm.
        """
        with patch.dict("os.environ", {"SERVE_GUARDRAILS_DISABLED": "true"}):
            config = load_config()

        assert config.guardrail_id == ""
        assert config.retrieval_guardrail_id == ""

    def test_disabling_guardrails_is_reported_at_error(self):
        # The only trace a stack leaves that it is serving unguarded traffic, so it
        # has to be loud enough to alarm on rather than filed under info.
        import structlog

        with (
            patch.dict("os.environ", {"SERVE_GUARDRAILS_DISABLED": "1"}),
            structlog.testing.capture_logs() as logs,
        ):
            load_config()

        disabled = [log for log in logs if log["event"] == "guardrails_disabled_by_configuration"]
        assert len(disabled) == 1
        assert disabled[0]["log_level"] == "error"
        assert disabled[0]["guardrail_id_ignored"] is True

    def test_guardrails_stay_on_unless_explicitly_disabled(self):
        # Absent, empty and unrecognised all leave the guardrail ON: this switch may
        # only ever be turned on deliberately, so anything short of a recognised
        # truthy value is not a request to serve unguarded traffic.
        for value in ("", "false", "no", "0", "off", "maybe", "TRUE-ish"):
            with patch.dict("os.environ", {"SERVE_GUARDRAILS_DISABLED": value}):
                assert load_config().guardrail_id == "gr-12345", value
        with patch.dict("os.environ", {}, clear=True):
            assert load_config().guardrail_id == "gr-12345"

    @patch.dict(
        "os.environ",
        {
            "VKG_ENDPOINT": "http://custom-vkg:9090",
            "NEPTUNE_ENDPOINT": "neptune.cluster.us-east-1.neptune.amazonaws.com",
            "OPENSEARCH_ENDPOINT": "search.us-east-1.es.amazonaws.com",
            "BEDROCK_MODEL_ID": "us.anthropic.claude-opus-4-6-v1",
            "BEDROCK_REGION": "us-west-2",
            "DATA_SOURCES_TABLE": "my-ds-table",
            "METRIC_DEFINITIONS_TABLE": "my-metrics-table",
        },
    )
    def test_loads_env_vars(self):
        config = load_config()

        assert config.vkg_endpoint == "http://custom-vkg:9090"
        assert config.neptune_endpoint == "neptune.cluster.us-east-1.neptune.amazonaws.com"
        assert config.opensearch_endpoint == "search.us-east-1.es.amazonaws.com"
        assert config.bedrock_model_id == "us.anthropic.claude-opus-4-6-v1"
        assert config.bedrock_region == "us-west-2"
        assert config.data_sources_table == "my-ds-table"
        assert config.metric_definitions_table == "my-metrics-table"

    def test_config_is_frozen(self):
        config = load_config()

        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            config.guardrail_id = "new-value"

    def test_tier1_metric_timeout_defaults_to_35_seconds(self):
        assert load_config().tier1_metric_timeout_s == 35

    @patch.dict("os.environ", {"TIER1_METRIC_TIMEOUT_S": "75"})
    def test_tier1_metric_timeout_env_override(self):
        assert load_config().tier1_metric_timeout_s == 75

    @patch.dict("os.environ", {"TIER1_METRIC_TIMEOUT_S": "999"})
    def test_tier1_metric_timeout_out_of_range_falls_back(self):
        assert load_config().tier1_metric_timeout_s == 35


@pytest.mark.unit
class TestDeepReasoningBudgetConfig:
    """Deep-reasoning Tier-3 budget knobs, including the P0 synthesis reserve."""

    def test_deep_reasoning_budget_defaults(self):
        config = load_config()

        assert config.deep_reasoning_time_budget_s == 30
        assert config.deep_reasoning_max_steps == 5
        assert config.deep_reasoning_per_tool_timeout_s == 30
        assert config.deep_reasoning_max_fanout == 5
        assert config.deep_reasoning_synthesis_reserve_s == 8

    @patch.dict("os.environ", {"DEEP_REASONING_SYNTHESIS_RESERVE_S": "12"})
    def test_synthesis_reserve_env_override(self):
        config = load_config()
        assert config.deep_reasoning_synthesis_reserve_s == 12

    @patch.dict("os.environ", {"DEEP_REASONING_SYNTHESIS_RESERVE_S": "9999"})
    def test_synthesis_reserve_out_of_range_falls_back(self):
        """Out-of-range (>120) reserve warns and falls back to the default."""
        config = load_config()
        assert config.deep_reasoning_synthesis_reserve_s == 8

    @patch.dict("os.environ", {"AGENTIC_SYNTHESIS_RESERVE_S": "12"})
    def test_deprecated_agentic_env_var_still_honored(self):
        """A deployment on the pre-rename env var name keeps its tuned value.

        Fails if the ``AGENTIC_*`` fallback is dropped: the value would silently
        revert to the 8s default rather than erroring, quietly changing the budget
        a tuned deployment depends on.
        """
        config = load_config()
        assert config.deep_reasoning_synthesis_reserve_s == 12

    @patch.dict(
        "os.environ",
        {"DEEP_REASONING_SYNTHESIS_RESERVE_S": "20", "AGENTIC_SYNTHESIS_RESERVE_S": "12"},
    )
    def test_new_env_var_wins_over_deprecated(self):
        config = load_config()
        assert config.deep_reasoning_synthesis_reserve_s == 20

    @patch.dict("os.environ", {"TIER3_STRATEGY": "agentic"})
    def test_deprecated_tier3_strategy_value_normalizes(self):
        """``TIER3_STRATEGY=agentic`` must still select the reasoning loop.

        Without the alias it falls into the invalid-value branch and reverts to
        lexical-baseline, silently turning a deep-reasoning deployment single-shot.
        """
        config = load_config()
        assert config.tier3_strategy == "deep-reasoning"

    def test_ontology_edge_mode_defaults_to_soft_prior(self):
        config = load_config()
        assert config.deep_reasoning_ontology_edge_mode == "soft_prior"

    @patch.dict("os.environ", {"DEEP_REASONING_ONTOLOGY_EDGE_MODE": "strict"})
    def test_ontology_edge_mode_strict_honored(self):
        config = load_config()
        assert config.deep_reasoning_ontology_edge_mode == "strict"

    @patch.dict("os.environ", {"DEEP_REASONING_ONTOLOGY_EDGE_MODE": "bogus"})
    def test_ontology_edge_mode_invalid_falls_back(self):
        config = load_config()
        assert config.deep_reasoning_ontology_edge_mode == "soft_prior"

    def test_ontology_source_defaults_to_graph(self):
        config = load_config()
        assert config.deep_reasoning_ontology_source == "graph"

    @patch.dict("os.environ", {"DEEP_REASONING_ONTOLOGY_SOURCE": "file"})
    def test_ontology_source_file_without_path_falls_back_to_graph(self):
        """A 'file' source with no DEEP_REASONING_ONTOLOGY_FILE is a misconfig (rdflib would
        parse the CWD → IsADirectoryError). load_config falls back to 'graph'."""
        config = load_config()
        assert config.deep_reasoning_ontology_source == "graph"

    @patch.dict(
        "os.environ",
        {"DEEP_REASONING_ONTOLOGY_SOURCE": "file", "DEEP_REASONING_ONTOLOGY_FILE": "/nonexistent/onto.ttl"},
    )
    def test_ontology_source_file_with_missing_path_falls_back_to_graph(self):
        config = load_config()
        assert config.deep_reasoning_ontology_source == "graph"

    def test_max_no_progress_steps_default(self):
        config = load_config()
        assert config.deep_reasoning_max_no_progress_steps == 2

    @patch.dict("os.environ", {"DEEP_REASONING_MAX_NO_PROGRESS_STEPS": "5"})
    def test_max_no_progress_steps_env_override(self):
        config = load_config()
        assert config.deep_reasoning_max_no_progress_steps == 5


_STOP_SIGNAL_ENV = (
    "DEEP_REASONING_SUFFICIENCY_MIN_CONFIDENCE",
    "DEEP_REASONING_PROGRESS_SIMILARITY_THRESHOLD",
    "DEEP_REASONING_STABILITY_STEPS",
    "DEEP_REASONING_STOP_TELEMETRY",
)


@pytest.mark.unit
class TestDeepReasoningStopSignalConfig:
    """Early-stop knobs: validated once at load_config(), bad values fall back with a warning."""

    @pytest.fixture(autouse=True)
    def _clean_env(self, monkeypatch):
        for name in _STOP_SIGNAL_ENV:
            monkeypatch.delenv(name, raising=False)
            monkeypatch.delenv(name.replace("DEEP_REASONING", "AGENTIC", 1), raising=False)

    @staticmethod
    def _load(monkeypatch, **env: str):
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        with structlog.testing.capture_logs() as logs:
            monkeypatch.setattr("coa_serve.config._config_provider", lambda: _FakeConfigProvider())
            config = load_config()
        return config, [entry for entry in logs if entry.get("log_level") == "warning"]

    def test_defaults_are_off(self, monkeypatch):
        config, _ = self._load(monkeypatch)
        assert config.deep_reasoning_sufficiency_min_confidence == 0.0
        assert config.deep_reasoning_progress_similarity_threshold == 0.0
        assert config.deep_reasoning_stability_steps == 2
        assert config.deep_reasoning_stop_telemetry is False

    def test_valid_values_are_honored(self, monkeypatch):
        config, warnings = self._load(
            monkeypatch,
            DEEP_REASONING_SUFFICIENCY_MIN_CONFIDENCE="0.7",
            DEEP_REASONING_PROGRESS_SIMILARITY_THRESHOLD="1",
            DEEP_REASONING_STABILITY_STEPS="3",
            DEEP_REASONING_STOP_TELEMETRY="true",
        )
        assert config.deep_reasoning_sufficiency_min_confidence == 0.7
        assert config.deep_reasoning_progress_similarity_threshold == 1.0
        assert config.deep_reasoning_stability_steps == 3
        assert config.deep_reasoning_stop_telemetry is True
        assert warnings == []

    @pytest.mark.parametrize("raw", ["true", "85", "-1", "abc"])
    @pytest.mark.parametrize(
        "name, field",
        [
            ("DEEP_REASONING_SUFFICIENCY_MIN_CONFIDENCE", "deep_reasoning_sufficiency_min_confidence"),
            ("DEEP_REASONING_PROGRESS_SIMILARITY_THRESHOLD", "deep_reasoning_progress_similarity_threshold"),
        ],
    )
    def test_invalid_threshold_falls_back_with_warning(self, monkeypatch, name, field, raw):
        config, warnings = self._load(monkeypatch, **{name: raw})
        assert getattr(config, field) == 0.0
        assert [w["name"] for w in warnings] == [name]

    @pytest.mark.parametrize(
        "name, field",
        [
            ("DEEP_REASONING_SUFFICIENCY_MIN_CONFIDENCE", "deep_reasoning_sufficiency_min_confidence"),
            ("DEEP_REASONING_PROGRESS_SIMILARITY_THRESHOLD", "deep_reasoning_progress_similarity_threshold"),
            ("DEEP_REASONING_STABILITY_STEPS", "deep_reasoning_stability_steps"),
            ("DEEP_REASONING_STOP_TELEMETRY", "deep_reasoning_stop_telemetry"),
        ],
    )
    def test_empty_value_is_the_default_without_warning(self, monkeypatch, name, field):
        config, warnings = self._load(monkeypatch, **{name: ""})
        assert getattr(config, field) == getattr(ServiceConfig, field)
        assert warnings == []

    @pytest.mark.parametrize("raw", ["true", "85", "-1", "abc", "0", "21"])
    def test_invalid_stability_steps_falls_back_with_warning(self, monkeypatch, raw):
        config, warnings = self._load(monkeypatch, DEEP_REASONING_STABILITY_STEPS=raw)
        assert config.deep_reasoning_stability_steps == 2
        assert [w["name"] for w in warnings] == ["DEEP_REASONING_STABILITY_STEPS"]

    @pytest.mark.parametrize("raw", ["true", "TRUE", "1", "yes", "On"])
    def test_telemetry_true_spellings(self, monkeypatch, raw):
        config, warnings = self._load(monkeypatch, DEEP_REASONING_STOP_TELEMETRY=raw)
        assert config.deep_reasoning_stop_telemetry is True
        assert warnings == []

    @pytest.mark.parametrize("raw", ["false", "False", "0", "no", "OFF"])
    def test_telemetry_false_spellings(self, monkeypatch, raw):
        config, warnings = self._load(monkeypatch, DEEP_REASONING_STOP_TELEMETRY=raw)
        assert config.deep_reasoning_stop_telemetry is False
        assert warnings == []

    @pytest.mark.parametrize("raw", ["85", "-1", "abc", "enabled"])
    def test_invalid_telemetry_falls_back_with_warning(self, monkeypatch, raw):
        config, warnings = self._load(monkeypatch, DEEP_REASONING_STOP_TELEMETRY=raw)
        assert config.deep_reasoning_stop_telemetry is False
        assert [w["name"] for w in warnings] == ["DEEP_REASONING_STOP_TELEMETRY"]

    def test_agentic_names_are_not_read(self, monkeypatch):
        """The knobs postdate the AGENTIC_* -> DEEP_REASONING_* rename: no legacy alias."""
        config, warnings = self._load(
            monkeypatch,
            AGENTIC_SUFFICIENCY_MIN_CONFIDENCE="0.5",
            AGENTIC_PROGRESS_SIMILARITY_THRESHOLD="0.9",
            AGENTIC_STABILITY_STEPS="4",
            AGENTIC_STOP_TELEMETRY="1",
        )
        assert config.deep_reasoning_sufficiency_min_confidence == 0.0
        assert config.deep_reasoning_progress_similarity_threshold == 0.0
        assert config.deep_reasoning_stability_steps == 2
        assert config.deep_reasoning_stop_telemetry is False
        assert not [w for w in warnings if w.get("event") == "deprecated_env_var"]

    def test_existing_knobs_keep_their_agentic_alias(self, monkeypatch):
        monkeypatch.delenv("DEEP_REASONING_MAX_NO_PROGRESS_STEPS", raising=False)
        config, _ = self._load(monkeypatch, AGENTIC_MAX_NO_PROGRESS_STEPS="4")
        assert config.deep_reasoning_max_no_progress_steps == 4


@pytest.mark.unit
class TestLexicalRetrieverStrategyConfig:
    """LEXICAL_RETRIEVER_STRATEGY parsing into ServiceConfig.lexical_retriever_strategy.

    Mirrors the existing tier3_strategy validate-or-warn handling: a valid value
    is honored, an invalid value warns (invalid_lexical_retriever_strategy) and
    falls back to the default, and an absent var yields the documented default.
    structlog.testing.capture_logs() is used for the warning assertion
    (the package does not configure caplog), consistent with test_strategies.py.
    """

    def test_absent_var_yields_default(self):
        """No env var → topic_beam, the strongest single-shot strategy.

        Standard mode's default engine. Guards the deployment default against a
        silent revert: topic_beam scores 45.13% strict on the SEC-10-Q benchmark
        (195 questions) versus 34.36% for the older hand-rolled path, so a
        regression here costs ~11pp for every caller that does not explicitly set
        options.retrieverStrategy.
        """
        config = load_config()
        assert config.lexical_retriever_strategy == "topic_beam"

    def test_absent_var_yields_lexical_baseline_tier3_strategy(self):
        """No env var → lexical-baseline, so standard mode actually runs topic_beam.

        Both halves are load-bearing: under "hand-rolled", main.py passes
        lexical_retriever_strategy=None to the Orchestrator and Tier 3 runs the
        hand-rolled VectorRetriever + GraphTraverser path regardless of what
        LEXICAL_RETRIEVER_STRATEGY says.
        """
        config = load_config()
        assert config.tier3_strategy == "lexical-baseline"

    @patch.dict("os.environ", {"LEXICAL_RETRIEVER_STRATEGY": "traversal"})
    def test_valid_value_is_honored(self):
        """A valid value is parsed straight through."""
        config = load_config()
        assert config.lexical_retriever_strategy == "traversal"

    @patch.dict("os.environ", {"LEXICAL_RETRIEVER_STRATEGY": "entity_based"})
    def test_other_valid_value_is_honored(self):
        """All registered strategy values are accepted (sourced from the enum)."""
        config = load_config()
        assert config.lexical_retriever_strategy == "entity_based"

    @patch.dict("os.environ", {"LEXICAL_RETRIEVER_STRATEGY": "not-a-real-strategy"})
    def test_invalid_value_warns_and_falls_back(self):
        """An invalid value logs invalid_lexical_retriever_strategy (warn) and falls back."""
        import structlog

        with structlog.testing.capture_logs() as logs:
            config = load_config()

        # Falls back to chunk_based_semantic, NOT the topic_beam default: the guard
        # also fires when the registry itself is unloadable (valid set collapses to
        # {"chunk_based_semantic"}), so recovering to topic_beam could "recover" to a
        # value that is not resolvable. See config.load_config.
        assert config.lexical_retriever_strategy == "chunk_based_semantic"
        warn_entries = [entry for entry in logs if entry.get("event") == "invalid_lexical_retriever_strategy"]
        assert warn_entries, "expected an invalid_lexical_retriever_strategy warning"
        assert warn_entries[0]["log_level"] == "warning"
        assert warn_entries[0]["value"] == "not-a-real-strategy"
        assert warn_entries[0]["fallback"] == "chunk_based_semantic"

    def test_load_config_does_not_import_graphrag_toolkit(self):
        """load_config must not pull in graphrag_toolkit (botocore sync-only invariant).

        Run in a fresh subprocess so a graphrag_toolkit already imported by a
        sibling test in the same process cannot mask a regression. Asserts that
        after calling load_config, no graphrag module is present in sys.modules.
        """
        import subprocess
        import sys

        code = (
            "import sys; "
            "from unittest.mock import patch; "
            "import coa_serve.config as cfg; "
            "Fake = type('Fake', (), {'get': lambda self, n: 'gr-test'}); "
            "patch.object(cfg, '_config_provider', lambda: Fake()).start(); "
            "c = cfg.load_config(); "
            "assert c.lexical_retriever_strategy == 'topic_beam', c.lexical_retriever_strategy; "
            "leaked = sorted(mod for mod in sys.modules if 'graphrag' in mod); "
            "assert not leaked, leaked; "
            "print('OK')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"load_config import-leak check failed.\nstdout={result.stdout}\nstderr={result.stderr}"
        )
        assert "OK" in result.stdout


@pytest.mark.unit
class TestValidLexicalRetrieverStrategiesFallback:
    """`_valid_lexical_retriever_strategies` defensive paths.

    The function loads the `RetrieverStrategy` enum from `lexical/strategies.py`
    by path so config-load doesn't trigger the graphrag/botocore import chain.
    These tests cover the three broken-install / load-failure fallbacks: missing
    file, unrecognized loader (None spec), and an exception during exec_module.
    All three log a structured warning and fall back to {"chunk_based_semantic"}
    so the documented default still loads on a broken install.
    """

    def test_missing_strategies_file_warns_and_falls_back(self):
        """Missing strategies.py → warn + fallback to {chunk_based_semantic}."""
        from pathlib import Path

        import structlog
        from coa_serve.config import _valid_lexical_retriever_strategies

        # Force the file-existence probe to return False, simulating a broken install.
        with patch.object(Path, "exists", return_value=False), structlog.testing.capture_logs() as logs:
            strategies = _valid_lexical_retriever_strategies()

        assert strategies == {"chunk_based_semantic"}
        warn_entries = [entry for entry in logs if entry.get("event") == "lexical_strategies_module_missing"]
        assert warn_entries, "expected a lexical_strategies_module_missing warning"
        assert warn_entries[0]["log_level"] == "warning"

    def test_none_spec_warns_and_falls_back(self):
        """spec_from_file_location returning None → warn + fallback."""
        import structlog
        from coa_serve.config import _valid_lexical_retriever_strategies

        with (
            patch(
                "coa_serve.config.importlib.util.spec_from_file_location",
                return_value=None,
            ),
            structlog.testing.capture_logs() as logs,
        ):
            strategies = _valid_lexical_retriever_strategies()

        assert strategies == {"chunk_based_semantic"}
        warn_entries = [entry for entry in logs if entry.get("event") == "lexical_strategies_spec_unavailable"]
        assert warn_entries, "expected a lexical_strategies_spec_unavailable warning"
        assert warn_entries[0]["log_level"] == "warning"

    def test_exec_module_exception_warns_and_falls_back(self):
        """An exception while executing strategies.py → warn + fallback + sys.modules cleanup."""
        import sys

        import structlog
        from coa_serve.config import _valid_lexical_retriever_strategies

        # Build a real spec but force exec_module to raise.
        real_spec_from_file_location = __import__(
            "importlib.util", fromlist=["spec_from_file_location"]
        ).spec_from_file_location

        def fake_spec_from_file_location(name, location):
            spec = real_spec_from_file_location(name, location)
            spec.loader.exec_module = MagicMock(side_effect=SyntaxError("simulated"))
            return spec

        with (
            patch(
                "coa_serve.config.importlib.util.spec_from_file_location",
                side_effect=fake_spec_from_file_location,
            ),
            structlog.testing.capture_logs() as logs,
        ):
            strategies = _valid_lexical_retriever_strategies()

        assert strategies == {"chunk_based_semantic"}
        warn_entries = [entry for entry in logs if entry.get("event") == "lexical_strategies_load_failed"]
        assert warn_entries, "expected a lexical_strategies_load_failed warning"
        assert warn_entries[0]["log_level"] == "warning"
        assert warn_entries[0]["error_type"] == "SyntaxError"
        # The half-built module was popped from sys.modules in the finally block.
        assert "_lexical_strategies_for_config" not in sys.modules

    def test_load_config_still_succeeds_when_registry_load_fails(self):
        """End-to-end: load_config() returns a valid config even if the registry can't be loaded."""
        with patch(
            "coa_serve.config._valid_lexical_retriever_strategies",
            return_value={"chunk_based_semantic"},
        ):
            config = load_config()

        # Default value still loads cleanly.
        assert config.lexical_retriever_strategy == "chunk_based_semantic"
