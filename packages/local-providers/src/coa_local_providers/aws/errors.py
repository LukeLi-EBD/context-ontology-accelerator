"""Map boto3/botocore failures onto the closed COA error contract.

Only the seven COA codes exist. A permission failure has no COA code of its
own, so it is reported as ``internal`` with ``provider_code=AccessDenied``
rather than being guessed into ``unavailable`` (the dependency is reachable;
the call was refused).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)
from coa_ports import PortError, PortErrorCode

_NOT_FOUND = frozenset(
    {
        "NoSuchKey",
        "NoSuchBucket",
        "ResourceNotFoundException",
        "ParameterNotFound",
        "404",
        "NotFound",
    }
)
_INVALID = frozenset({"InvalidParameter", "InvalidParameterValue", "ValidationException"})
_UNAVAILABLE = frozenset(
    {"Throttling", "ThrottlingException", "ServiceUnavailable", "RequestTimeout", "SlowDown"}
)


def to_port_error(exc: Exception, *, provider: str, message: str) -> PortError:
    """Translate a boto error; unknown failures become ``internal``."""
    if isinstance(exc, ClientError):
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in _NOT_FOUND:
            return PortError(
                PortErrorCode.NOT_FOUND,
                f"{message}: {code}",
                provider=provider,
                provider_code=code,
            )
        if code in _INVALID:
            return PortError(
                PortErrorCode.INVALID_ARGUMENT,
                f"{message}: {code}",
                provider=provider,
                provider_code=code,
            )
        if code in _UNAVAILABLE:
            return PortError(
                PortErrorCode.UNAVAILABLE,
                f"{message}: {code}",
                provider=provider,
                provider_code=code,
            )
        return PortError(
            PortErrorCode.INTERNAL,
            f"{message}: {code}",
            provider=provider,
            provider_code=code,
        )
    if isinstance(exc, (ConnectTimeoutError, ReadTimeoutError)):
        return PortError(
            PortErrorCode.TIMEOUT,
            message,
            provider=provider,
            provider_code=type(exc).__name__,
        )
    if isinstance(exc, EndpointConnectionError):
        return PortError(
            PortErrorCode.UNAVAILABLE,
            message,
            provider=provider,
            provider_code=type(exc).__name__,
        )
    if isinstance(exc, BotoCoreError):
        return PortError(
            PortErrorCode.INTERNAL,
            message,
            provider=provider,
            provider_code=type(exc).__name__,
        )
    return PortError(
        PortErrorCode.INTERNAL,
        message,
        provider=provider,
        provider_code=type(exc).__name__,
    )


def port_error_details(exc: Exception) -> Mapping[str, Any]:
    """Diagnostic details safe to attach (never includes payload or secrets)."""
    if isinstance(exc, ClientError):
        return {"operation": exc.operation_name}
    return {}


__all__ = ["to_port_error", "port_error_details"]
