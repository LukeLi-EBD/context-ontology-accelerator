"""Authorization data port (replaces the Roles / ResourceRoleMappings tables).

Two reads feed the serve layer's authorization decision:

* the Cedar policy text attached to each role (the Roles table's
  ``cedarPolicy`` attribute), and
* the roles a principal holds, with their data restrictions (the
  ResourceRoleMappings table).

Both are synchronous on the request path — the serve layer calls them from
``asyncio.to_thread`` — and both must keep the fail-closed contract: an
unavailable policy source is ``None`` (deny), never an empty policy set that
would silently allow.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..dto import PrincipalGrant


@runtime_checkable
class AuthorizationPort(Protocol):
    """The policy + grant source the Cedar gate reads."""

    def policies_for_roles(self, role_ids: set[str]) -> str | None:
        """Return the joined Cedar policy text for ``role_ids`` plus ``default``.

        Returns ``None`` when any requested role has no policy available, which
        the caller must treat as a deny (``authorization_policies_unavailable``).
        """
        ...

    def grants_for_principal(
        self,
        *,
        user_id: str,
        email: str,
        groups: list[str],
        namespace: str,
    ) -> tuple[PrincipalGrant, ...]:
        """Return every grant held by the principal, under all of its identifiers.

        ``namespace`` is the namespace the request targets; providers may use it
        to narrow the lookup, but the caller applies the namespace scoping to the
        returned grants (a ``GLOBAL`` grant is platform-wide by definition).
        """
        ...
