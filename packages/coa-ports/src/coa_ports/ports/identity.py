"""Identity port (replaces Cognito / IAM identity resolution)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..dto import AuthorizationDecision, Principal


@runtime_checkable
class IdentityPort(Protocol):
    """Resolve a bearer token to a Principal and answer authorization checks."""

    async def resolve(self, auth_token: str) -> Principal:
        """Return the Principal behind ``auth_token``.

        Raises :class:`coa_ports.errors.PortError` with ``invalid_argument``
        for a malformed token and ``unavailable`` when the identity backend
        cannot be reached.
        """
        ...

    async def authorize(
        self,
        principal: Principal,
        action: str,
        resource: str,
    ) -> AuthorizationDecision:
        """Decide whether ``principal`` may perform ``action`` on ``resource``."""
        ...
