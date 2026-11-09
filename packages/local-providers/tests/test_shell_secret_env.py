"""Real-call tests for the ``SecretProvider`` ACL shell.

No mocks: the shell wraps the real platform provider, which reads the real
process environment. ``monkeypatch.setenv`` writes a real environment
variable, so the read path is the production one.
"""

from __future__ import annotations

import os

import pytest

from coa_local_providers.shells import EnvSecretShell
from coa_ports import PortError, PortErrorCode, SecretProvider
from platform_core.ports import EnvSecretProvider

SECRET_NAME = "COA_SHELL_SAMPLE_SECRET"
SECRET_VALUE = "s3cr3t-value-9f2"


def test_shell_is_a_secret_provider() -> None:
    assert isinstance(EnvSecretShell(EnvSecretProvider()), SecretProvider)


def test_shell_reads_a_real_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SECRET_NAME, SECRET_VALUE)
    shell = EnvSecretShell(EnvSecretProvider())
    assert shell.get(SECRET_NAME) == SECRET_VALUE
    assert os.environ[SECRET_NAME] == SECRET_VALUE


def test_missing_secret_maps_to_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(SECRET_NAME, raising=False)
    shell = EnvSecretShell(EnvSecretProvider(), provider="env")
    with pytest.raises(PortError) as excinfo:
        shell.get(SECRET_NAME)
    error = excinfo.value
    assert error.code is PortErrorCode.NOT_FOUND
    assert error.provider == "env"
    assert error.provider_code == "E_SECRET_NOT_FOUND"
    assert error.details["name"] == SECRET_NAME


def test_error_message_never_echoes_a_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SECRET_NAME, SECRET_VALUE)
    shell = EnvSecretShell(EnvSecretProvider())

    class Leaky:
        def get(self, name: str) -> str:
            raise _PlatformError("NotFound", "secret x is not set", details={"name": "x", "value": SECRET_VALUE})

    with pytest.raises(PortError) as excinfo:
        EnvSecretShell(Leaky()).get("x")
    assert SECRET_VALUE not in str(excinfo.value)
    assert "value" not in excinfo.value.details


def test_unexpected_exception_is_internal_not_not_found() -> None:
    class Broken:
        def get(self, name: str) -> str:
            raise RuntimeError("socket closed")

    with pytest.raises(PortError) as excinfo:
        EnvSecretShell(Broken()).get("x")
    assert excinfo.value.code is PortErrorCode.INTERNAL
    assert excinfo.value.provider_code == "RuntimeError"


def test_unauthorised_platform_code_maps_to_internal_not_a_guess() -> None:
    class Odd:
        def get(self, name: str) -> str:
            raise _PlatformError("AccessDenied", "no")

    with pytest.raises(PortError) as excinfo:
        EnvSecretShell(Odd()).get("x")
    assert excinfo.value.code is PortErrorCode.INTERNAL


def test_constructor_rejects_an_object_without_get() -> None:
    with pytest.raises(TypeError):
        EnvSecretShell(object())


class _PlatformError(Exception):
    """Stands in for ``platform_core.ports.PortError`` in the mapping tests.

    The real class cannot be constructed with arbitrary codes from a test
    without depending on its internals, and this test targets the mapping
    table rather than the platform class.
    """

    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.provider = "env"
        self.provider_code = f"E_{code.upper()}"
        self.details = details or {}
