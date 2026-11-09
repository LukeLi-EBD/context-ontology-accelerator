"""Settings behaviour: absence is explicit, never defaulted."""

from __future__ import annotations

import pytest

from coa_runtime.errors import MissingConfigurationError
from coa_runtime.settings import Settings


def test_absent_and_empty_are_the_same() -> None:
    settings = Settings({"A": "", "B": "  ", "C": "value"})
    assert settings.get("A") is None
    assert settings.get("B") is None
    assert settings.get("C") == "value"
    assert settings.get("NOPE") is None


def test_require_names_the_key_and_interface() -> None:
    with pytest.raises(MissingConfigurationError) as excinfo:
        Settings({}).require("COA_PROVIDER_GRAPH", interface="GraphClient")
    error = excinfo.value
    assert error.code == "config_missing"
    assert error.key == "COA_PROVIDER_GRAPH"
    assert error.interface == "GraphClient"
    assert "COA_PROVIDER_GRAPH" in str(error)


def test_int_parsing_is_strict() -> None:
    settings = Settings({"N": "12", "BAD": "twelve"})
    assert settings.get_int("N") == 12
    assert settings.get_int("MISSING", default=4) == 4
    with pytest.raises(MissingConfigurationError):
        settings.get_int("MISSING")
    with pytest.raises(MissingConfigurationError):
        settings.get_int("BAD")


def test_snapshot_drops_empty_values() -> None:
    assert Settings({"A": "", "B": "1"}).snapshot() == {"B": "1"}


def test_from_environ_reads_mapping() -> None:
    settings = Settings.from_environ({"COA_PROVIDER_GRAPH": "oxigraph"})
    assert settings.get("COA_PROVIDER_GRAPH") == "oxigraph"
