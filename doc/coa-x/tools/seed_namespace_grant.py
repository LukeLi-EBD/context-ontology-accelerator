# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Seed one namespace-scoped grant for the cross-namespace authz smoke test.

Local stack only. Writes a normal ``ResourceRoleMappings`` row with exactly the
shape ``POST /namespaces/{namespaceId}/grants`` writes, so the authorizer can
resolve a namespace role for a dev user without first creating a namespace and
its built-in roles. Nothing here is imported by production code.

Usage:
    python seed_namespace_grant.py <namespaceId> <principalId> <role>
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime

from coa_common.principal_keys import sanitize_principal_key
from coa_local_providers.control_plane_pg import PgDatastoreDAO

_ROLE_SK_PREFIX = "ROLE#"


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: seed_namespace_grant.py <namespaceId> <principalId> <role>",
            file=sys.stderr,
        )
        return 2
    namespace_id, principal_id, role = sys.argv[1], sys.argv[2], sys.argv[3]
    dao = PgDatastoreDAO(
        os.environ["RESOURCE_ROLE_MAPPINGS_TABLE"],
        region=os.environ.get("AWS_REGION", "us-east-1"),
    )
    sanitized = sanitize_principal_key(principal_id)
    item = {
        "PK": f"Namespace::{namespace_id}#User::{sanitized}",
        "SK": f"{_ROLE_SK_PREFIX}{role}",
        "resourceType": "Namespace",
        "resourceId": namespace_id,
        "principalType": "User",
        "principalId": principal_id,
        "role": role,
        "principalKey": f"User::{sanitized}",
        "resourceRoleKey": f"Namespace::{namespace_id}#{_ROLE_SK_PREFIX}{role}",
        "namespaceKey": f"NS#{namespace_id}",
        "principalRoleKey": f"User::{sanitized}#{_ROLE_SK_PREFIX}{role}",
        "grantedBy": "coa-authz-smoke",
        "grantedAt": datetime.now(UTC).isoformat(),
    }
    key = {"PK": item["PK"], "SK": item["SK"]}
    if dao.get(key) is None:
        dao.put(item, auto_timestamp=False)
        print(f"[seed] grant {item['PK']}/{item['SK']}")
    else:
        print(f"[seed] grant already present {item['PK']}/{item['SK']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
