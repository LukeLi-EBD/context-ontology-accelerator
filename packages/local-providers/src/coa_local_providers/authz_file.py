"""A file-backed :class:`AuthorizationPort`.

The serve path reads two DynamoDB tables to make one authorization decision:

* the **Roles** table — one ``cedarPolicy`` text per role (plus ``default``,
  which is always evaluated), and
* the **ResourceRoleMappings** table — the roles a principal holds, each with
  optional ``tableAllowlist`` / ``columnDenylist`` / ``allowedMetrics``.

This provider reads both from one JSON file so a local deployment can make the
SAME decision without AWS. The shapes are the table shapes, not an
abstraction over them: an operator can copy items out of DynamoDB and paste
them into the file, and the resolution rules in the serve layer stay unchanged.

File shape::

    {
      "policies": {
        "default": "<cedar text>",
        "data-analyst": "<cedar text>"
      },
      "principals": {
        "User::alice": [
          {"resourceId": "demo", "role": "data-analyst"},
          {"resourceId": "GLOBAL", "role": "platform-viewer",
           "tableAllowlist": ["demo.orders"],
           "columnDenylist": {"demo.orders": ["ssn"]},
           "allowedMetrics": ["revenue"]}
        ],
        "Group::analysts": [
          {"resourceId": "demo", "role": "data-analyst"}
        ]
      }
    }

Principal keys must use the same encoding as the RRM table's ``principalKey``
(``User::<sub-or-email>`` / ``Group::<name>``; see
``coa_common.principal_keys``). The file is validated at construction: a
missing file, invalid JSON, a non-object ``policies``/``principals``, or a
malformed grant raises instead of degrading to an empty (deny-everything or,
worse, silently-role-less) configuration.

Fail-closed behaviour:

* ``policies_for_roles`` returns ``None`` when any requested role (including
  ``default``) has no entry — the caller denies with
  ``authorization_policies_unavailable``, exactly like an unreadable table.
* ``grants_for_principal`` returns no grants for an unknown principal — Cedar
  denies for want of a role, exactly like a principal with no table items.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import structlog
from coa_common.principal_keys import build_principal_keys
from coa_ports.dto import PrincipalGrant

logger = structlog.get_logger(__name__)

# The always-evaluated baseline role. Deployed tables seed it under PK=GLOBAL,
# and the serve layer always includes it, so requiring it here keeps a local
# decision identical to the deployed one instead of quietly dropping the
# default policy's forbids.
DEFAULT_ROLE = "default"


class FileAuthorization:
    """Policies and principal grants read from one JSON file."""

    def __init__(self, policies: Mapping[str, str], principals: Mapping[str, tuple[PrincipalGrant, ...]]) -> None:
        self._policies = dict(policies)
        self._principals = dict(principals)

    @classmethod
    def from_path(cls, path: str | Path) -> FileAuthorization:
        """Load and validate the file at ``path``.

        Raises:
            FileNotFoundError: The file does not exist (the configuration
                names a source that is not there).
            ValueError: The file is not valid JSON or not the documented shape.
        """
        raw = Path(path).read_text(encoding="utf-8")
        try:
            document = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"authorization file {path} is not valid JSON: {exc}") from exc
        if not isinstance(document, dict):
            raise ValueError(f"authorization file {path} must contain a JSON object")

        policies_raw = document.get("policies")
        if not isinstance(policies_raw, dict):
            raise ValueError(f"authorization file {path} must have a 'policies' object")
        policies: dict[str, str] = {}
        for role_id, text in policies_raw.items():
            if not isinstance(text, str):
                raise ValueError(f"authorization file {path}: policy for role {role_id!r} must be a string")
            policies[str(role_id)] = text

        principals_raw = document.get("principals", {})
        if not isinstance(principals_raw, dict):
            raise ValueError(f"authorization file {path} must have a 'principals' object")
        principals = {
            str(principal_key): _parse_grants(path, principal_key, grants)
            for principal_key, grants in principals_raw.items()
        }
        logger.info(
            "authorization_file_loaded",
            path=str(path),
            roles=sorted(policies),
            principal_count=len(principals),
        )
        return cls(policies=policies, principals=principals)

    def policies_for_roles(self, role_ids: set[str]) -> str | None:
        """Joined Cedar text for ``role_ids`` + ``default``, or None if unavailable."""
        required = sorted(set(role_ids) | {DEFAULT_ROLE})
        missing = [role_id for role_id in required if role_id not in self._policies]
        if missing:
            # Not an empty policy set: an absent role is an unreadable table cell,
            # and the caller must deny rather than evaluate a partial policy set.
            logger.warning("authorization_role_policy_missing", roles=missing, effect="deny")
            return None
        joined = "\n".join(text for role_id in required if (text := self._policies[role_id]))
        return joined or None

    def grants_for_principal(
        self,
        *,
        user_id: str,
        email: str,
        groups: list[str],
        namespace: str,
    ) -> tuple[PrincipalGrant, ...]:
        """Every grant filed under any of the principal's identifiers."""
        del namespace  # the caller scopes grants; the table lookup is principal-wide
        keys = build_principal_keys(user_id=user_id, email=email, groups=groups)
        found: list[PrincipalGrant] = []
        for key in keys:
            found.extend(self._principals.get(key, ()))
        return tuple(found)


def _parse_grants(path: str | Path, principal_key: str, raw: Any) -> tuple[PrincipalGrant, ...]:
    """Validate one principal's grant list into ``PrincipalGrant`` objects."""
    if not isinstance(raw, list):
        raise ValueError(f"authorization file {path}: principal {principal_key!r} must map to a list of grants")
    grants: list[PrincipalGrant] = []
    for index, item in enumerate(raw):
        where = f"authorization file {path}: principal {principal_key!r}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be an object")
        role = item.get("role")
        resource_id = item.get("resourceId")
        if not isinstance(role, str) or not role:
            raise ValueError(f"{where} needs a non-empty 'role' string")
        if not isinstance(resource_id, str) or not resource_id:
            raise ValueError(f"{where} needs a non-empty 'resourceId' string")
        grants.append(
            PrincipalGrant(
                role=role,
                resource_id=resource_id,
                table_allowlist=_parse_str_list(where, "tableAllowlist", item.get("tableAllowlist")),
                column_denylist=_parse_denylist(where, item.get("columnDenylist")),
                allowed_metrics=_parse_str_list(where, "allowedMetrics", item.get("allowedMetrics")),
            )
        )
    return tuple(grants)


def _parse_str_list(where: str, field: str, raw: Any) -> tuple[str, ...] | None:
    if raw is None:
        return None
    if not isinstance(raw, list) or not all(isinstance(value, str) for value in raw):
        raise ValueError(f"{where}: '{field}' must be a list of strings")
    return tuple(raw)


def _parse_denylist(where: str, raw: Any) -> Mapping[str, tuple[str, ...]] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"{where}: 'columnDenylist' must be an object of table -> list of columns")
    parsed: dict[str, tuple[str, ...]] = {}
    for table, columns in raw.items():
        if not isinstance(columns, list) or not all(isinstance(column, str) for column in columns):
            raise ValueError(f"{where}: 'columnDenylist[{table!r}]' must be a list of strings")
        parsed[str(table)] = tuple(columns)
    return parsed


__all__ = ["DEFAULT_ROLE", "FileAuthorization"]
