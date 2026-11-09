"""``coa_ports.ConfigProvider`` over SSM Parameter Store.

Same call as before (``get_parameter``), but absence is expressed the way the
port defines it: ``get`` returns ``None`` and ``require`` raises ``not_found``.
SSM cannot enumerate parameters cheaply, so ``as_mapping`` returns only the
keys this instance has actually read.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from coa_ports import PortError, PortErrorCode

from .errors import to_port_error


class SsmConfig:
    """Read-only SSM parameter lookup (sync, as the SDK is)."""

    def __init__(
        self, client: Any = None, *, region: str | None = None, client_config: Any = None
    ) -> None:
        self._client_obj = client
        self._region = region
        self._client_config = client_config
        self._seen: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        try:
            response = self._client().get_parameter(Name=key)
        except Exception as exc:  # noqa: BLE001
            error = to_port_error(exc, provider="ssm", message=f"ssm parameter {key}")
            if error.code is PortErrorCode.NOT_FOUND:
                return None
            raise error from exc
        value = str(response.get("Parameter", {}).get("Value", ""))
        self._seen[key] = value
        return value

    def require(self, key: str) -> str:
        value = self.get(key)
        if value is None:
            raise PortError(
                PortErrorCode.NOT_FOUND,
                f"ssm parameter {key} not found",
                provider="ssm",
                provider_code="ParameterNotFound",
                details={"name": key},
            )
        return value

    def as_mapping(self) -> Mapping[str, str]:
        return dict(self._seen)

    def _client(self) -> Any:
        if self._client_obj is None:
            import boto3

            self._client_obj = boto3.client(
                "ssm", region_name=self._region, config=self._client_config
            )
        return self._client_obj


__all__ = ["SsmConfig"]
