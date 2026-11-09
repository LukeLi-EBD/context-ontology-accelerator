"""``FileAuthorization`` — the JSON source behind ``AuthorizationPolicies``.

The tests use the two table shapes as the input (``policies`` = Roles table
``cedarPolicy``, ``principals`` = ResourceRoleMappings items) so a reader can
check the file contract against the DynamoDB one item by item.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from coa_local_providers.authz_file import FileAuthorization

_POLICY = 'permit(principal, action == SCL::Action::"query", resource);'


def _write(tmp_path: Path, document: object) -> str:
    path = tmp_path / "authz.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return str(path)


def _document() -> dict:
    return {
        "policies": {"default": "// no default grants", "data-analyst": _POLICY},
        "principals": {
            "User::alice": [
                {"resourceId": "demo", "role": "data-analyst"},
                {"resourceId": "GLOBAL", "role": "platform-viewer"},
            ],
            "Group::analysts": [{"resourceId": "demo", "role": "data-analyst"}],
        },
    }


def test_policies_join_the_requested_roles_and_default(tmp_path: Path) -> None:
    source = FileAuthorization.from_path(_write(tmp_path, _document()))
    joined = source.policies_for_roles({"data-analyst"})
    assert joined is not None
    assert _POLICY in joined
    assert "no default grants" in joined


def test_a_missing_role_is_unavailable_not_an_empty_policy_set(tmp_path: Path) -> None:
    source = FileAuthorization.from_path(_write(tmp_path, _document()))
    assert source.policies_for_roles({"unprovisioned-role"}) is None


def test_a_missing_default_role_is_unavailable(tmp_path: Path) -> None:
    document = _document()
    del document["policies"]["default"]
    source = FileAuthorization.from_path(_write(tmp_path, document))
    assert source.policies_for_roles({"data-analyst"}) is None


def test_grants_resolve_under_user_email_and_group_keys(tmp_path: Path) -> None:
    source = FileAuthorization.from_path(_write(tmp_path, _document()))

    by_user = source.grants_for_principal(user_id="alice", email="", groups=[], namespace="demo")
    assert [(g.role, g.resource_id) for g in by_user] == [
        ("data-analyst", "demo"),
        ("platform-viewer", "GLOBAL"),
    ]

    by_group = source.grants_for_principal(user_id="bob", email="", groups=["analysts"], namespace="demo")
    assert [(g.role, g.resource_id) for g in by_group] == [("data-analyst", "demo")]


def test_email_keys_are_case_insensitive_like_the_table(tmp_path: Path) -> None:
    document = {
        "policies": {"default": "// none"},
        "principals": {"User::alice@example.com": [{"resourceId": "demo", "role": "data-analyst"}]},
    }
    source = FileAuthorization.from_path(_write(tmp_path, document))
    found = source.grants_for_principal(user_id="u1", email="Alice@Example.com", groups=[], namespace="demo")
    assert [(g.role, g.resource_id) for g in found] == [("data-analyst", "demo")]


def test_an_unknown_principal_has_no_grants(tmp_path: Path) -> None:
    source = FileAuthorization.from_path(_write(tmp_path, _document()))
    assert source.grants_for_principal(user_id="nobody", email="", groups=[], namespace="demo") == ()


def test_restrictions_are_parsed_in_the_table_shape(tmp_path: Path) -> None:
    document = {
        "policies": {"default": "// none"},
        "principals": {
            "User::restricted": [
                {
                    "resourceId": "demo",
                    "role": "data-analyst",
                    "tableAllowlist": ["demo.orders"],
                    "columnDenylist": {"demo.orders": ["ssn"]},
                    "allowedMetrics": ["revenue"],
                }
            ]
        },
    }
    source = FileAuthorization.from_path(_write(tmp_path, document))
    (grant,) = source.grants_for_principal(user_id="restricted", email="", groups=[], namespace="demo")
    assert grant.table_allowlist == ("demo.orders",)
    assert grant.column_denylist == {"demo.orders": ("ssn",)}
    assert grant.allowed_metrics == ("revenue",)


def test_a_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        FileAuthorization.from_path(tmp_path / "absent.json")


@pytest.mark.parametrize(
    "document",
    [
        [],
        {"principals": {}},
        {"policies": []},
        {"policies": {"default": 1}},
        {"policies": {}, "principals": {"User::a": {"role": "x"}}},
        {"policies": {}, "principals": {"User::a": [{"resourceId": "demo"}]}},
        {"policies": {}, "principals": {"User::a": [{"role": "r"}]}},
        {"policies": {}, "principals": {"User::a": [{"role": "r", "resourceId": "demo", "tableAllowlist": "x"}]}},
        {"policies": {}, "principals": {"User::a": [{"role": "r", "resourceId": "demo", "columnDenylist": []}]}},
    ],
)
def test_malformed_files_raise_instead_of_degrading(tmp_path: Path, document: object) -> None:
    path = _write(tmp_path, document)
    with pytest.raises(ValueError):
        FileAuthorization.from_path(path)
