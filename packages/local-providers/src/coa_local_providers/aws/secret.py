"""``coa_ports.SecretProvider`` over AWS Secrets Manager.

Same single call the services used before (``get_secret_value``). Values are
returned to the caller and never logged or embedded in an error.
"""

from __future__ import annotations

import base64
from typing import Any

from .errors import to_port_error


class SecretsManagerSecret:
    """Secret lookup by secret id/ARN (sync, as the SDK is)."""

    def __init__(
        self, client: Any = None, *, region: str | None = None, client_config: Any = None
    ) -> None:
        self._client_obj = client
        self._region = region
        self._client_config = client_config

    def get(self, name: str) -> str:
        try:
            response = self._client().get_secret_value(SecretId=name)
        except Exception as exc:  # noqa: BLE001
            raise to_port_error(exc, provider="secretsmanager", message="secret lookup failed") from exc
        if "SecretString" in response:
            return str(response["SecretString"])
        return base64.b64decode(response["SecretBinary"]).decode("utf-8")

    def _client(self) -> Any:
        if self._client_obj is None:
            import boto3

            self._client_obj = boto3.client(
                "secretsmanager", region_name=self._region, config=self._client_config
            )
        return self._client_obj


__all__ = ["SecretsManagerSecret"]
