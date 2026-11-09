# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for coa_control_plane.ssm_config (ConfigProvider seam)."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from coa_ports import PortError, PortErrorCode
from coa_runtime.errors import MissingConfigurationError
from coa_control_plane.ssm_config import get_smus_domain_id


def _resolution(provider):
    """A stand-in for ``coa_runtime.Resolution``; only ``.instance`` is read."""
    return SimpleNamespace(instance=provider)


@pytest.mark.unit
class TestGetSMUSDomainId:
    @patch("coa_control_plane.ssm_config.resolve")
    def test_returns_domain_id(self, mock_resolve):
        provider = SimpleNamespace(get=lambda name: "dzd_domain123")
        mock_resolve.return_value = _resolution(provider)

        result = get_smus_domain_id("/coa")

        assert result == "dzd_domain123"

    @patch("coa_control_plane.ssm_config.resolve")
    def test_asks_for_the_documented_parameter(self, mock_resolve):
        seen: list[str] = []

        def get(name: str) -> str:
            seen.append(name)
            return "dzd_domain123"

        mock_resolve.return_value = _resolution(SimpleNamespace(get=get))
        get_smus_domain_id("/coa")
        assert seen == ["/coa/smus/domain-id"]

    @patch("coa_control_plane.ssm_config.resolve")
    def test_region_override_reaches_the_settings(self, mock_resolve):
        captured = {}

        def resolve(interface: str, settings):
            captured["interface"] = interface
            captured["region"] = settings.get("AWS_REGION")
            return _resolution(SimpleNamespace(get=lambda name: "dzd_domain123"))

        mock_resolve.side_effect = resolve
        get_smus_domain_id("/coa", region_name="eu-west-1")
        assert captured == {"interface": "ConfigProvider", "region": "eu-west-1"}

    @patch("coa_control_plane.ssm_config.resolve")
    def test_missing_parameter_raises_value_error(self, mock_resolve):
        mock_resolve.return_value = _resolution(SimpleNamespace(get=lambda name: None))
        with pytest.raises(ValueError, match="not found at SSM parameter"):
            get_smus_domain_id("/coa")

    @patch("coa_control_plane.ssm_config.resolve")
    def test_empty_value_raises_value_error(self, mock_resolve):
        mock_resolve.return_value = _resolution(SimpleNamespace(get=lambda name: ""))
        with pytest.raises(ValueError, match="not found at SSM parameter"):
            get_smus_domain_id("/coa")

    @patch("coa_control_plane.ssm_config.resolve")
    def test_provider_errors_propagate(self, mock_resolve):
        from coa_ports import PortError as Error

        def boom(name: str) -> str:
            raise Error(PortErrorCode.UNAVAILABLE, "ssm down", provider="ssm")

        mock_resolve.return_value = _resolution(SimpleNamespace(get=boom))
        with pytest.raises(PortError):
            get_smus_domain_id("/coa")

    @patch("coa_control_plane.ssm_config.resolve")
    def test_unconfigured_provider_is_an_explicit_configuration_error(self, mock_resolve):
        """No ConfigProvider is not "no domain id" — it must not be swallowed."""
        mock_resolve.side_effect = MissingConfigurationError(
            "ConfigProvider has no provider configured",
            interface="ConfigProvider",
            key="COA_PROVIDER_CONFIG",
            allowed=("env", "ssm"),
        )
        with pytest.raises(MissingConfigurationError):
            get_smus_domain_id("/coa")
