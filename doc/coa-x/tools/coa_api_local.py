"""Run the upstream COA HTTP API locally on PostgreSQL + Oxigraph.

This is the local composition root for the *original* COA backend
``packages/control-plane`` (namespaces/roles/grants) plus the ``sources``,
``metric-service`` and ``ontology-engine`` Lambda handlers.  It replaces the
AWS-only bindings, it does not change any Smithy operation:

* DynamoDB item storage  -> PostgreSQL JSONB (``coa_local_providers.control_plane_pg``)
* DataZone project       -> ``pg.coa_local_projects``
* API Gateway proxy      -> this FastAPI bridge (routing copied from
  ``infra/bin/app.ts``)
* Metric graph            -> Oxigraph (``COA_PROVIDER_METRIC_GRAPH=oxigraph``)
* Metric index            -> ``platform.metric_definition`` (``platform-pg``)

Every substitution is selected by the ``COA_PROVIDER_*`` key; when a key is
missing or points at an unimplemented provider the process refuses to start
instead of silently degrading.

Usage (from the repo root)::

    .venv-coa-local\\Scripts\\python.exe doc\\coa-x\\tools\\coa_api_local.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlencode

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

REPO = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
# The snapshot is written at start-up.  In the container stack the worktree is
# mounted read-only, so allow the location to be redirected into a writable
# volume; the default keeps the host workflow unchanged.
SNAPSHOT_PATH = Path(
    os.environ.get("COA_LOCAL_CATALOG_SNAPSHOT") or (TOOLS / "local-catalog.json")
)
SEED_DIR = REPO / "libs/common/src/coa_authorization/seed"

# The local MetricGraph provider (oxigraph) and the pg-backed providers reuse
# platform_core's adapters; PYTHONPATH does not always carry the workspace src,
# so add it here rather than relying on the launch command.
_WORKSPACE_SRC = sorted(
    [*(REPO / "packages").glob("*/src"), *(REPO / "libs").glob("*/src")]
) + [REPO / "smithy-generated/control-plane-python-server"]
for _p in reversed(_WORKSPACE_SRC):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
PLATFORM_CORE_SRC = REPO / "packages/platform-core/src"

LOCAL_EMAIL = "local-dev@example.invalid"
LOCAL_USER = "local-user"
LOCAL_ROLES = "platform-admin"
DEMO_SOURCE_ID = "platform-demo"
DEMO_TABLE = "platform.bank_loan_account"
DEMO_COLUMNS = [
    {"name": "institution", "data_type": "text"},
    {"name": "loan_id", "data_type": "text"},
    {"name": "amount", "data_type": "numeric"},
    {"name": "status", "data_type": "text"},
    {"name": "origination_date", "data_type": "date"},
]

BUILT_IN_ROLES = [
    ("GLOBAL", "platform-admin", "Platform Admin", "Full access to all resources across all namespaces", "global_admin.cedar"),
    ("GLOBAL", "platform-viewer", "Platform Viewer", "Read-only access across all namespaces", "global_viewer.cedar"),
    ("GLOBAL", "default", "Default", "Default policy applied to all authenticated users", "default.cedar"),
    ("NAMESPACE", "namespace-owner", "Namespace Owner", "Full control within a namespace", "namespace_owner.cedar"),
    ("NAMESPACE", "data-steward", "Data Steward", "Manage data sources, ontologies, metrics, and documents within a namespace", "namespace_data_steward.cedar"),
    ("NAMESPACE", "data-analyst", "Data Analyst", "Query and read access within a namespace", "namespace_data_analyst.cedar"),
    ("NAMESPACE", "namespace-maintainer", "Namespace Maintainer", "Full control within a namespace", "namespace_maintainer.cedar"),
]


# ---------------------------------------------------------------------------
# Authentication / authorization (parity with the API Gateway authorizer)
# ---------------------------------------------------------------------------

from coa_common.auth.token_authorizer import TokenAuthorizer  # noqa: E402

# ``enforce`` is the only default. ``disabled`` exists solely for a local
# developer who explicitly opts out; it prints a loud warning at startup.
_AUTH_MODE_ENFORCE = "enforce"
_AUTH_MODE_DISABLED = "disabled"
_AUTH_MODE = _AUTH_MODE_ENFORCE

_DEV_AUTH_ENABLED = False
_DEV_AUTH_ISSUER = ""
_DEV_AUTH_KID = "coa-local-dev"
_DEV_AUTH_PRIVATE_KEY: Any = None
_DEV_AUTH_JWKS: dict[str, Any] = {}
_DEV_AUTH_USERS: set[str] = set()

# Routes that exist in this local bridge but are newer than the authorizer's
# ``_PATH_MAPPING`` (they were added by parallel lines before the contract was
# regenerated). Without an entry the authorizer denies them for every role, so
# the local stack is extended here — visibly, and only in this process.
# Action choices follow the closest already-mapped sibling; global (namespace-
# less) reads rely on the ``platform-viewer`` grant seeded below.
_LOCAL_AUTHZ_EXTENSIONS: dict[str, dict[str, tuple[str, str]]] = {
    "/namespaces/{namespaceId}/terms": {
        "GET": ("viewNamespace", "Namespace"),
        "POST": ("manageOntology", "Namespace"),
    },
    "/namespaces/{namespaceId}/dictionaries": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/dictionaries/{sourceId}": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/dictionaries/{sourceId}/view": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/dictionaries/{sourceId}/comment-coverage": {
        "GET": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/dictionaries/{sourceId}/refresh": {"POST": ("manageSource", "Namespace")},
    "/namespaces/{namespaceId}/ingestion-runs": {
        "GET": ("viewNamespace", "Namespace"),
        "POST": ("manageSource", "Namespace"),
    },
    "/namespaces/{namespaceId}/sparql": {"POST": ("query", "Namespace")},
    "/namespaces/{namespaceId}/metrics/report/manifest": {"GET": ("readMetric", "Namespace")},
    "/namespaces/{namespaceId}/metrics/families/{familyId}": {"GET": ("readMetric", "Namespace")},
    "/namespaces/{namespaceId}/induce/datasources": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/embeddings": {"POST": ("manageSource", "Namespace")},
    "/namespaces/{namespaceId}/embeddings/batch": {"POST": ("manageSource", "Namespace")},
    "/namespaces/{namespaceId}/embeddings/by-ontology/{ontologyId}": {
        "GET": ("searchDocuments", "Namespace")
    },
    "/namespaces/{namespaceId}/validate": {"POST": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/validate/jobs": {
        "GET": ("viewNamespace", "Namespace"),
        "POST": ("viewNamespace", "Namespace"),
    },
    "/namespaces/{namespaceId}/validate/jobs/{jobId}": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/versions": {
        "GET": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}": {
        "GET": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}/diff": {
        "GET": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}/export": {
        "GET": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/import": {
        "POST": ("manageOntology", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals": {
        "GET": ("viewNamespace", "Namespace"),
        "POST": ("manageOntology", "Namespace"),
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals/{proposalId}": {
        "GET": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals/{proposalId}/review": {
        "POST": ("manageOntology", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/publish": {
        "POST": ("manageOntology", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/rollback": {
        "POST": ("manageOntology", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/events": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/verify": {
        "POST": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/export": {
        "POST": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/inspect": {
        "POST": ("viewNamespace", "Namespace")
    },
    "/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/import": {
        "POST": ("manageOntology", "Namespace")
    },
    "/namespaces/{namespaceId}/facts": {
        "GET": ("viewNamespace", "Namespace"),
        "POST": ("manageOntology", "Namespace"),
    },
    "/namespaces/{namespaceId}/facts/conflicts": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/facts/conflicts/undo": {"POST": ("manageOntology", "Namespace")},
    "/namespaces/{namespaceId}/facts/conflicts/batch": {"POST": ("manageOntology", "Namespace")},
    "/namespaces/{namespaceId}/facts/retract": {"POST": ("manageOntology", "Namespace")},
    "/namespaces/{namespaceId}/facts/{factId}": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/facts/{factId}/retract": {"POST": ("manageOntology", "Namespace")},
    "/namespaces/{namespaceId}/facts/{factId}/restore": {"POST": ("manageOntology", "Namespace")},
    "/namespaces/{namespaceId}/facts/{factId}/events": {"GET": ("viewNamespace", "Namespace")},
    "/namespaces/{namespaceId}/answerable": {"POST": ("query", "Namespace")},
    # Global reads: the path carries no namespace, so namespace roles cannot
    # match. They map onto the read actions platform-viewer already grants.
    "/entities/{entityId}": {"GET": ("searchDocuments", "Namespace")},
    "/entities/{entityId}/provenance": {"GET": ("searchDocuments", "Namespace")},
    "/metrics/{metricId}": {"GET": ("readMetric", "Namespace")},
    "/browse/ontology/tree": {"GET": ("viewNamespace", "Namespace")},
    "/browse/ontology/instances": {"GET": ("viewNamespace", "Namespace")},
    "/answer/quality": {"GET": ("query", "Namespace")},
}


class _LocalDevTokenAuthorizer(TokenAuthorizer):  # type: ignore[misc]
    """RS256 verifier backed by an in-memory JWKS (no HTTP round-trip).

    The bridge mints its own development tokens. Fetching the JWKS over HTTP
    from the same process would block the event loop that has to serve it, so
    the key set is held in memory while signature/issuer/expiry checks stay
    exactly the ones the production authorizer uses.
    """

    def __init__(self, *, issuer: str, jwks: dict[str, Any]) -> None:
        super().__init__(issuer=issuer)
        self._memory_jwks = jwks

    def _extract_groups(self, claims: dict[str, Any]) -> list[str]:
        from coa_common.auth.token_authorizer import extract_groups_claim

        return extract_groups_claim(claims)

    def _get_jwks_uri(self) -> str:  # pragma: no cover - never used
        return "memory://coa-local-dev/jwks"

    def _get_jwks(self) -> dict[str, Any]:
        return self._memory_jwks


def _init_auth() -> None:
    """Configure authentication from explicit local settings.

    Refuses to start in ``enforce`` mode without an identity source instead of
    silently falling back to an anonymous principal.
    """
    global _AUTH_MODE, _DEV_AUTH_ENABLED, _DEV_AUTH_ISSUER
    global _DEV_AUTH_PRIVATE_KEY, _DEV_AUTH_JWKS, _DEV_AUTH_USERS

    mode = os.environ.get("COA_LOCAL_AUTH_MODE", _AUTH_MODE_ENFORCE).strip().lower()
    if mode not in (_AUTH_MODE_ENFORCE, _AUTH_MODE_DISABLED):
        raise SystemExit(
            f"refusing to start: COA_LOCAL_AUTH_MODE={mode!r} is not one of "
            f"{_AUTH_MODE_ENFORCE!r}/{_AUTH_MODE_DISABLED!r}"
        )
    _AUTH_MODE = mode

    # The authorizer Lambda's own env names, backed by the local PG partitions.
    os.environ.setdefault("ROLES_TABLE_NAME", os.environ["ROLES_TABLE"])
    os.environ.setdefault(
        "RESOURCE_ROLE_MAPPINGS_TABLE_NAME", os.environ["RESOURCE_ROLE_MAPPINGS_TABLE"]
    )
    os.environ.setdefault("NAMESPACES_TABLE_NAME", os.environ["NAMESPACES_TABLE"])

    if mode == _AUTH_MODE_DISABLED:
        print(
            "[api] WARNING: COA_LOCAL_AUTH_MODE=disabled — EVERY route is served as "
            f"{LOCAL_EMAIL} with role {LOCAL_ROLES!r}; there is no authentication or "
            "authorization. Never expose this bridge beyond 127.0.0.1.",
            file=sys.stderr,
        )
        return

    dev_auth = os.environ.get("COA_LOCAL_DEV_AUTH", "off").strip().lower()
    if dev_auth not in ("on", "off"):
        raise SystemExit(
            f"refusing to start: COA_LOCAL_DEV_AUTH={dev_auth!r} must be 'on' or 'off'"
        )

    if dev_auth == "on":
        from cryptography.hazmat.primitives.asymmetric import rsa
        from jwt.algorithms import RSAAlgorithm

        port = int(os.environ.get("COA_LOCAL_API_PORT", "8099"))
        host_for_issuer = os.environ.get("COA_LOCAL_AUTH_ISSUER_HOST", "127.0.0.1")
        _DEV_AUTH_ISSUER = (
            os.environ.get("COA_LOCAL_AUTH_ISSUER")
            or f"http://{host_for_issuer}:{port}/local/auth"
        ).rstrip("/")
        users = os.environ.get("COA_LOCAL_DEV_USERS") or LOCAL_EMAIL
        _DEV_AUTH_USERS = {u.strip() for u in users.split(",") if u.strip()}
        if not _DEV_AUTH_USERS:
            raise SystemExit("refusing to start: COA_LOCAL_DEV_USERS resolved to an empty list")

        _DEV_AUTH_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = json.loads(RSAAlgorithm.to_jwk(_DEV_AUTH_PRIVATE_KEY.public_key()))
        jwk.update({"kid": _DEV_AUTH_KID, "use": "sig", "alg": "RS256"})
        _DEV_AUTH_JWKS = {"keys": [jwk]}

        import coa_control_plane.authorization.handler as authz_handler

        authz_handler._token_authorizer = _LocalDevTokenAuthorizer(  # noqa: SLF001
            issuer=_DEV_AUTH_ISSUER, jwks=_DEV_AUTH_JWKS
        )
        _DEV_AUTH_ENABLED = True
        print(
            "[api] WARNING: COA_LOCAL_DEV_AUTH=on — POST /local/auth/token mints real "
            f"RS256 tokens for {sorted(_DEV_AUTH_USERS)} without any IdP. This is a "
            "local development convenience only; never expose it or ship it.",
            file=sys.stderr,
        )
        print(f"[api] dev token issuer: {_DEV_AUTH_ISSUER}")
    else:
        issuer = os.environ.get("JWKS_ISSUER")
        if not issuer:
            raise SystemExit(
                "refusing to start: authentication is enabled but no identity source is "
                "configured. Set JWKS_ISSUER (and optionally JWKS_URI/CLIENT_ID) for a real "
                "OIDC issuer, or COA_LOCAL_DEV_AUTH=on for the explicit local dev issuer. "
                "COA_LOCAL_AUTH_MODE=disabled bypasses checks and is not a default."
            )
        print(f"[api] authentication: enforcing bearer tokens from {issuer}")


def _apply_local_authz_extensions() -> None:
    """Register bridge-only routes in the authorizer's path map (this process only)."""
    import coa_control_plane.authorization.handler as authz_handler

    added = 0
    for resource, methods in _LOCAL_AUTHZ_EXTENSIONS.items():
        if resource in authz_handler._PATH_MAPPING:  # noqa: SLF001
            continue
        authz_handler._PATH_MAPPING[resource] = dict(methods)  # noqa: SLF001
        added += 1
    if added:
        print(
            f"[api] authorization map: +{added} local-only routes "
            "(not in the deployed contract; fail-closed in AWS)"
        )


def _seed_dev_global_viewer() -> None:
    """Bootstrap real global grants for the local dev users.

    The primary dev account gets ``platform-admin`` (production bootstraps its
    first admin out of band; this is the local equivalent, and it is a normal
    ResourceRoleMappings row that can be revoked through the API). Any other
    configured dev user only gets ``platform-viewer``, so 403 behaviour stays
    testable. No write ever falls back to a role without a row.
    """
    if not _DEV_AUTH_ENABLED:
        return
    from coa_common.dao import DynamoDBDAO
    from coa_common.principal_keys import sanitize_principal_key

    dao = DynamoDBDAO(
        os.environ["RESOURCE_ROLE_MAPPINGS_TABLE"], region=os.environ["AWS_REGION"]
    )
    now = datetime.now(timezone.utc).isoformat()
    primary = (os.environ.get("COA_LOCAL_DEV_ADMIN_USER") or LOCAL_EMAIL).strip()
    granted: list[tuple[str, str]] = []
    for email in sorted(_DEV_AUTH_USERS):
        role = "platform-admin" if email == primary else "platform-viewer"
        principal = sanitize_principal_key(email)
        key = f"Platform::GLOBAL#User::{principal}"
        if dao.get({"PK": key, "SK": f"ROLE#{role}"}):
            continue
        item = {
            "PK": key,
            "SK": f"ROLE#{role}",
            "resourceType": "Platform",
            "resourceId": "GLOBAL",
            "principalType": "User",
            "principalId": email,
            "role": role,
            "principalKey": f"User::{principal}",
            "resourceRoleKey": f"Platform::GLOBAL#ROLE#{role}",
            "namespaceKey": "GLOBAL",
            "principalRoleKey": f"User::{principal}#ROLE#{role}",
            "grantedBy": "coa-local-bootstrap",
            "grantedAt": now,
        }
        dao.put(item, auto_timestamp=False)
        granted.append((email, role))
    if granted:
        print(f"[api] dev role bootstrap: {granted}")


def _auth_error_json(status: int, error: str, message: str, **extra: Any) -> JSONResponse:
    body: dict[str, Any] = {"error": error, "message": message, **extra}
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(body, status_code=status, headers=headers)


_LOOPBACK_ORIGIN = re.compile(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$")


def _origin_allowed(origin: str) -> bool:
    """Allow configured origins plus loopback on any port; reject the rest."""
    configured = os.environ.get("ALLOWED_ORIGIN", "").strip()
    if configured and origin == configured:
        return True
    return bool(_LOOPBACK_ORIGIN.match(origin))


def _authorize_request(
    method: str,
    template: str,
    path_params: dict[str, str],
    headers: dict[str, str],
) -> tuple[dict[str, Any] | None, JSONResponse | None]:
    """Run the real authorizer for one request; return (context, error)."""
    if _AUTH_MODE == _AUTH_MODE_DISABLED:
        return {
            "principalId": LOCAL_EMAIL,
            "userId": LOCAL_EMAIL,
            "email": LOCAL_EMAIL,
            "globalRoles": LOCAL_ROLES,
            "groups": "",
            "tokenType": "JWT",
        }, None

    import coa_control_plane.authorization.handler as authz_handler

    event = {
        "methodArn": f"arn:aws:execute-api:local:000000000000:local/prod/{method}{template}",
        "resource": template,
        "httpMethod": method.upper(),
        "headers": headers,
        "pathParameters": path_params,
        "requestContext": {"path": template, "httpMethod": method.upper()},
    }
    policy = authz_handler.handler(event, None)
    statements = (policy.get("policyDocument") or {}).get("Statement") or [{}]
    effect = statements[0].get("Effect")
    principal_id = policy.get("principalId") or ""

    if effect == "Allow":
        context = dict(policy.get("context") or {})
        context["principalId"] = principal_id
        context.setdefault("userId", principal_id)
        return context, None

    action = authz_handler._map_request_to_cedar(  # noqa: SLF001
        method.upper(), template, path_params
    )[0]
    if not principal_id:
        return None, _auth_error_json(
            401,
            "E_UNAUTHENTICATED",
            "Missing or invalid bearer token",
            detail="Send 'Authorization: Bearer <token>'.",
        )
    if action == authz_handler._UNMAPPED_ACTION:  # noqa: SLF001
        return None, _auth_error_json(
            403,
            "E_UNMAPPED_ROUTE",
            "This route has no authorization mapping; access is denied.",
            action=action,
        )
    return None, _auth_error_json(
        403,
        "E_FORBIDDEN",
        f"Permission denied for action {action!r}.",
        action=action,
    )


def _safe_authorize(
    method: str,
    template: str,
    path_params: dict[str, str],
    headers: dict[str, str],
) -> tuple[dict[str, Any] | None, JSONResponse | None]:
    """Fail closed: any authorizer failure becomes an explicit 503, never allow."""
    try:
        return _authorize_request(method, template, path_params, headers)
    except Exception as exc:  # noqa: BLE001 - boundary: must not leak a stack trace
        print(
            f"[api] authorization backend failure for {method} {template}: {exc!r}",
            file=sys.stderr,
        )
        return None, _auth_error_json(
            503,
            "E_AUTHZ_UNAVAILABLE",
            "Authorization could not be evaluated; the request was denied.",
        )


def _mint_dev_token(email: str, ttl_seconds: int = 3600) -> dict[str, Any]:
    """Mint a real RS256 JWT for an allow-listed local dev user."""
    import jwt as pyjwt

    now = int(datetime.now(timezone.utc).timestamp())
    claims = {
        "iss": _DEV_AUTH_ISSUER,
        "sub": email,
        "email": email,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    token = pyjwt.encode(
        claims, _DEV_AUTH_PRIVATE_KEY, algorithm="RS256", headers={"kid": _DEV_AUTH_KID}
    )
    return {"accessToken": token, "token": token, "tokenType": "Bearer", "expiresIn": ttl_seconds}


# ---------------------------------------------------------------------------
# Environment (explicit local configuration; no AWS calls)
# ---------------------------------------------------------------------------


def _configure_environment() -> None:
    defaults = {
        "AWS_REGION": "us-east-1",
        # Deployment resource prefix (CDK sets this on every Lambda); it seeds
        # external ids and catalog names, so there is no safe default upstream.
        "RESOURCE_PREFIX": "coa-local-",
        "LOG_LEVEL": "INFO",
        "ALLOWED_ORIGIN": "http://127.0.0.1:5173",
        # DynamoDB table names become PostgreSQL table-name partitions.
        "NAMESPACES_TABLE": "coa-local-namespaces",
        "ROLES_TABLE": "coa-local-roles",
        "RESOURCE_ROLE_MAPPINGS_TABLE": "coa-local-resource-role-mappings",
        "SOURCES_TABLE": "coa-local-sources",
        # Document ingestion + fact-candidate review (documents.smithy).
        "DOCUMENTS_TABLE": "coa-local-documents",
        "DOCUMENT_CHUNKS_TABLE": "coa-local-document-chunks",
        "FACT_CANDIDATES_TABLE": "coa-local-fact-candidates",
        "FACTS_TABLE": "coa-local-facts",
        # A-Box graph namespace used when an approved candidate is materialised.
        "NDB_GRAPH_URI_BASE": "https://coa.local/graph",
        # The metric service reads the same unified sources table under this name.
        "DATA_SOURCES_TABLE": "coa-local-sources",
        # Client-token idempotency records (POSTs from the web app send a token).
        "IDEMPOTENCY_TABLE": "coa-local-idempotency",
        "SOURCE_SCAN_JOBS_TABLE": "coa-local-source-scan-jobs",
        "ONTOLOGIES_TABLE": "coa-local-ontologies",
        # Async OSI import job records (GetImportJob reads them directly from
        # DynamoDB upstream; locally they live in the PostgreSQL item table).
        "IMPORT_JOBS_TABLE": "coa-local-metric-import-jobs",
        "COA_PROVIDER_METRIC_IMPORT_JOBS": "postgres",
        # DataZone project ids are minted by the local project store.
        "DATAZONE_DOMAIN_ID": "local-domain",
        "SMUS_DOMAIN_ID": "local-domain",
        "DATAZONE_PROJECT_PROFILE_ID": "local-profile",
        # Metric graph / index / validator.
        "COA_PROVIDER_METRIC_GRAPH": "oxigraph",
        "COA_GRAPH_OXIGRAPH_URL": "http://127.0.0.1:7878",
        "COA_PROVIDER_METRIC_INDEX": "platform-pg",
        # Host port 5432 is currently shadowed by the acceptance stack, so the
        # local COA database lives on 5444 (see report).
        "COA_METADATA_PG_DSN": os.environ.get(
            "COA_CONTROL_PLANE_PG_DSN",
            "postgresql://platform:platform_dev@127.0.0.1:5444/platform",
        ),
        "COA_PROVIDER_DATA_SOURCE_LOOKUP": "json-snapshot",
        "COA_JSON_CATALOG_SNAPSHOT": str(SNAPSHOT_PATH),
        "COA_PROVIDER_ONTOLOGY_LOOKUP": "graph",
        # The ontology-engine service (coa_ontology.main:app) is a separate
        # service and is not started by this bridge; the proxy handler then
        # answers 503 "ontology service unavailable" instead of crashing on an
        # unset variable.  Point this at a running engine to enable the layer.
        "ONTOLOGY_ENGINE_ENDPOINT": "http://127.0.0.1:8101",
        # DataLayerService (Query / KBSearch) is served by the real Lambda
        # handler, whose transport is the local-http ContextManagerPort. The
        # context-manager is a separate process (run_local.py context-manager,
        # port 8091); when it is down these two routes answer 502 rather than
        # pretending to answer.
        "COA_PROVIDER_CONTEXT_MANAGER": "local-http",
        "COA_CONTEXT_MANAGER_ENDPOINT": os.environ.get(
            "COA_CONTEXT_MANAGER_ENDPOINT", "http://127.0.0.1:8091"
        ),
        "COA_CONTEXT_MANAGER_TIMEOUT_S": "180",
        "COA_PROVIDER_CONTROL_PLANE_STORE": "postgres",
        # Local deployments have no IAM role to add to the DataZone project.
        "COA_LOCAL_SKIP_PROJECT_MEMBERSHIP": "true",
        # Queues are intentionally unset: create-source then stays synchronous
        # instead of pretending to hand work to a non-existent SQS.
        "SCAN_QUEUE_URL": "",
        "INGESTION_QUEUE_URL": "",
        "REVIEW_QUEUE_URL": "",
        "GRAPH_VERIFY_QUEUE_URL": "",
        "SOURCE_DELETE_QUEUE_URL": "",
        "ATHENA_RESULTS_BUCKET_SSM": "",
        "PROJECT_ACCESS_ROLE_ARN": "",
        "BUCKET_NAME": "",
        # Local object transport (S3 role). The provider key itself stays
        # unset here: it is chosen by 10-本地起栈.ps1 and fails closed.
        "COA_LOCAL_OBJECT_ROOT": os.path.join(tempfile.gettempdir(), "coa-local-stack", "objects"),
        # Presigned object URLs must point at *this* bridge; several parallel
        # local lines run on different ports, so never hardcode 8099.
        "COA_LOCAL_OBJECT_BASE": (
            "http://127.0.0.1:"
            + os.environ.get("COA_LOCAL_API_PORT", "8099")
            + "/_local/objects"
        ),
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)
    os.environ.setdefault(
        "COA_CONTROL_PLANE_PG_DSN",
        "postgresql://platform:platform_dev@127.0.0.1:5444/platform",
    )
    provider = os.environ["COA_PROVIDER_CONTROL_PLANE_STORE"]
    if provider != "postgres":
        sys.exit(
            f"refusing to start: COA_PROVIDER_CONTROL_PLANE_STORE={provider!r} "
            "is not implemented locally (use 'postgres')"
        )
    if not os.environ.get("COA_CONTROL_PLANE_PG_DSN"):
        sys.exit("refusing to start: COA_CONTROL_PLANE_PG_DSN is required")
    import_jobs_provider = os.environ["COA_PROVIDER_METRIC_IMPORT_JOBS"]
    if import_jobs_provider != "postgres":
        sys.exit(
            f"refusing to start: COA_PROVIDER_METRIC_IMPORT_JOBS={import_jobs_provider!r} "
            "is not implemented locally (use 'postgres')"
        )


# ---------------------------------------------------------------------------
# Provider wiring
# ---------------------------------------------------------------------------


def _install_pg_store() -> None:
    """Point every DynamoDBDAO import site at the PostgreSQL store."""
    import coa_common
    import coa_common.dao
    import coa_common.dao.dynamodb as dynamodb_module

    from coa_local_providers.control_plane_pg import PgDatastoreDAO

    dynamodb_module.DynamoDBDAO = PgDatastoreDAO  # type: ignore[assignment]
    coa_common.dao.DynamoDBDAO = PgDatastoreDAO  # type: ignore[assignment]
    coa_common.DynamoDBDAO = PgDatastoreDAO  # type: ignore[attr-defined]


def _install_local_import_jobs() -> None:
    """Point the metric import-job store at PostgreSQL.

    ``import_job_store`` builds a boto3 DynamoDB table itself, so the DAO
    substitution above never reached it and ``GetImportJob`` answered 500.
    """
    from coa_local_providers.metric_jobs_pg import install_metric_import_jobs

    install_metric_import_jobs()


def _install_local_metadata_store() -> None:
    import coa_common.metadata_store as metadata_store

    from coa_local_providers.control_plane_pg import PgProjectStore

    metadata_store.SMUSClient = PgProjectStore  # type: ignore[assignment]

    from coa_control_plane.namespace import service

    if os.environ.get("COA_LOCAL_SKIP_PROJECT_MEMBERSHIP") == "true":
        service.NamespaceService._add_service_role_memberships = (  # type: ignore[assignment]
            lambda self, project_id: None
        )


class LocalCatalogClient:
    """DataZone ``search_assets`` equivalent backed by ``local-catalog.json``.

    The sources API reads table metadata from the metadata catalog, not from
    the sources table.  Upstream that is DataZone; locally the same reads are
    served from the JSON snapshot that the data-source lookup provider already
    uses, so a table listed here is also a table ``check_source_table_exists``
    accepts.  Only the read methods the sources routes call are implemented —
    an unimplemented catalog write raises instead of pretending to succeed.
    """

    def __init__(self, **_kwargs: Any) -> None:
        pass

    # -- catalog reads ----------------------------------------------------

    def _assets(self) -> list[Any]:
        from coa_common.datazone_forms import FORM_TYPE_NAME
        from coa_common.metadata_store.base import AssetResult

        if not SNAPSHOT_PATH.exists():
            return []
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        assets = []
        for source_id, catalog in (snapshot.get("data_sources") or {}).items():
            for table_id, columns in (catalog.get("tables") or {}).items():
                database, _, table = table_id.partition(".")
                payload = {
                    "tableName": table or table_id,
                    "databaseName": database,
                    "dataSourceId": source_id,
                    "columns": json.dumps(
                        [
                            {
                                "name": column["name"],
                                "data_type": column.get("data_type", ""),
                                "business_metadata": {"review_status": "APPROVED"},
                            }
                            for column in columns
                        ]
                    ),
                    "foreignKeys": "[]",
                    "reviewStatus": "APPROVED",
                }
                assets.append(
                    AssetResult(
                        asset_id=f"local-asset-{source_id}-{table_id}",
                        name=f"DS#{source_id}:{table_id}",
                        project_id="local-domain",
                        forms_output=[{"formName": FORM_TYPE_NAME, "content": json.dumps(payload)}],
                    )
                )
        return assets

    def search_assets(self, *, project_id: str, search_text: str, max_results: int = 50, **_: Any) -> Any:
        from coa_common.metadata_store.base import SearchResult

        matches = [asset for asset in self._assets() if search_text and search_text in asset.name]
        return SearchResult(items=matches[:max_results], next_token=None)

    def find_asset_by_name(self, *, project_id: str, name: str, max_pages: int = 20) -> Any:
        for asset in self._assets():
            if asset.name == name:
                return asset
        return None

    def get_asset_forms(self, *, asset_id: str) -> dict[str, Any]:
        for asset in self._assets():
            if asset.asset_id == asset_id:
                return {"assetId": asset_id, "formsOutput": asset.forms_output}
        raise KeyError(f"asset not found: {asset_id}")

    def __getattr__(self, name: str) -> Any:
        raise NotImplementedError(f"LocalCatalogClient does not implement {name}")


def _install_local_catalog() -> None:
    """Route the sources API's metadata-catalog reads at the local snapshot.

    ``COA_PROVIDER_METADATA_CATALOG`` selects the implementation: the local
    default is ``json-snapshot``; any other value leaves the upstream
    ``SMUSClient`` in place, so the AWS path stays reachable without a code
    change.  Neither branch is silent -- the choice is printed at start-up.
    """
    provider = os.environ.get("COA_PROVIDER_METADATA_CATALOG", "json-snapshot")
    if provider != "json-snapshot":
        print(f"[api] metadata catalog -> upstream AWS client (COA_PROVIDER_METADATA_CATALOG={provider})")
        return
    # sources_handler is the entry module: importing it first resolves the
    # handler <-> database_routes cycle the same way the Lambda does.
    import coa_sources.api.sources_handler  # noqa: F401
    import coa_sources.api.database_routes as database_routes

    database_routes._get_smus_client = lambda: LocalCatalogClient()  # type: ignore[assignment]
    print("[api] metadata catalog -> json-snapshot (LocalCatalogClient)")


# ---------------------------------------------------------------------------
# Local seed data (idempotent)
# ---------------------------------------------------------------------------


def _role_items() -> list[dict[str, Any]]:
    items = []
    for scope, role_id, name, description, filename in BUILT_IN_ROLES:
        items.append(
            {
                "PK": scope if scope == "GLOBAL" else "NAMESPACE_TEMPLATE",
                "SK": f"ROLE#{role_id}",
                "name": name,
                "description": description,
                "isBuiltIn": True,
                "cedarPolicy": (SEED_DIR / filename).read_text(encoding="utf-8"),
                "scope": scope,
            }
        )
    return items


def _install_local_object_store() -> None:
    """Point the sources upload-url seam at the local object store.

    ``POST /sources/upload-urls`` presigns with ``sources_handler._get_s3()``
    and the document bucket name; both are module globals resolved at import
    time. With ``COA_PROVIDER_ONTOLOGY_OBJECTS=fs`` the same filesystem store
    the ontology artifacts use backs document uploads too, so the presigned
    URL the UI receives resolves against this bridge instead of AWS.
    """
    provider = os.environ.get("COA_PROVIDER_ONTOLOGY_OBJECTS", "").strip().lower()
    if provider != "fs":
        print(f"[api] object store -> upstream s3 (provider={provider or 'unset'})", flush=True)
        return

    from coa_local_providers.local_s3 import LocalS3, default_bucket

    import coa_sources.api.sources_handler as sources_handler

    bucket = os.environ.get("BUCKET_NAME", "").strip() or default_bucket()
    sources_handler._s3 = LocalS3()
    sources_handler._BUCKET_NAME = bucket
    document_routes = sys.modules.get("coa_sources.api.document_routes")
    if document_routes is not None:  # already imported: it bound the name by value
        document_routes._BUCKET_NAME = bucket
    print(f"[api] object store -> fs bucket={bucket}", flush=True)


def _install_local_idempotency() -> None:
    """Store client-token idempotency records in PostgreSQL, not DynamoDB.

    The web app sends a ``clientToken`` on every create, so without a store
    those requests answer 503.  The upstream ``IdempotencyStore`` is a boto3
    table wrapper; here the same five-method lifecycle is served from the PG
    item table.  Store failures are translated to ``IdempotencyStoreError`` so
    the handler still fails closed with its 503 "retry" response.
    """
    import coa_common.idempotency as idempotency

    from coa_local_providers.control_plane_pg import PgIdempotencyStore

    stores: dict[str, Any] = {}

    class _Adapter:
        def __init__(self, inner: Any) -> None:
            self._inner = inner

        def __getattr__(self, name: str) -> Any:
            attribute = getattr(self._inner, name)
            if not callable(attribute):
                return attribute

            def call(*args: Any, **kwargs: Any) -> Any:
                try:
                    return attribute(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001 - translated by design
                    raise idempotency.IdempotencyStoreError(str(exc)) from exc

            return call

    def _get_store(table_name: str) -> Any:
        store = stores.get(table_name)
        if store is None:
            store = stores[table_name] = _Adapter(PgIdempotencyStore(table_name))
        return store

    idempotency._get_store = _get_store  # type: ignore[assignment]
    print("[api] idempotency store -> postgres")


def _seed_roles() -> None:
    from coa_common.dao import DynamoDBDAO

    dao = DynamoDBDAO(os.environ["ROLES_TABLE"], region=os.environ["AWS_REGION"])
    for item in _role_items():
        if dao.get({"PK": item["PK"], "SK": item["SK"]}) is None:
            dao.put(item, auto_timestamp=True)
            print(f"[seed] role {item['PK']}/{item['SK']}")


def _write_snapshot() -> None:
    snapshot = {
        "data_sources": {
            DEMO_SOURCE_ID: {
                "catalog_available": True,
                "rejection_reasons": {},
                "tables": {DEMO_TABLE: DEMO_COLUMNS},
            }
        }
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def _seed_demo_catalog(namespace_id: str, created_by: str) -> dict[str, Any]:
    """Attach the demo warehouse to a namespace.

    Stands in for the Glue/DataZone scan pipeline, which has no local
    equivalent yet.  The source row itself is a normal DynamoDB item in the
    sources table, so the UI lists it through the real handler.
    """
    from coa_common.dao import DynamoDBDAO

    dao = DynamoDBDAO(os.environ["SOURCES_TABLE"], region=os.environ["AWS_REGION"])
    now = uuid.uuid4().hex  # unique suffix also keeps the GSI key stable
    del now
    from datetime import UTC, datetime

    created = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    item = {
        "PK": f"NS#{namespace_id}",
        "SK": f"SRC#{DEMO_SOURCE_ID}",
        "sourceId": DEMO_SOURCE_ID,
        "namespaceId": namespace_id,
        "name": "Local Warehouse (demo)",
        "sourceType": "DATABASE",
        "sourceSubType": "GLUE_DATABASE",
        "status": "APPROVED",
        # Stored blob is the Glue configuration itself; the wire member name
        # (glueConfiguration) only selects which member GetSource surfaces it
        # under (_DETAIL_CONFIG_KEYS), so it is not nested here.
        "configuration": json.dumps(
            {
                # GlueConfiguration.catalogId is contract-constrained to a
                # 12-digit account id; there is no AWS account locally.
                "catalogId": "123456789012",
                "databaseName": "platform",
                "region": os.environ["AWS_REGION"],
            }
        ),
        "tenantId": f"ns-{namespace_id}",
        "createdBy": created_by,
        "createdAt": created,
        "updatedAt": created,
        "sourceTypeCreatedAt": f"DATABASE#{created}",
    }
    dao.put(item, auto_timestamp=False)
    _write_snapshot()
    return item


# ---------------------------------------------------------------------------
# Routing (mirrors infra/bin/app.ts)
# ---------------------------------------------------------------------------

NAMESPACE = "coa_control_plane.namespace.namespace_api_handler"
ROLES = "coa_control_plane.roles.namespace_roles_handler"
# Platform-scoped role list lives in its own Lambda (GET /roles).
PLATFORM_ROLES = "coa_control_plane.roles.list_platform_roles_handler"
GRANTS = "coa_control_plane.grants.grants_handler"
SOURCES = "coa_sources.api.sources_handler"
METRICS = "coa_metrics.api.metric_api_handler"
ONTOLOGY = "coa_ontology.api_proxy_handler"
DATA_LAYER = "coa_data_layer.handler"
# Sentinel: the T-Box lifecycle lives in platform_core, not in a Lambda
# handler.  `dispatch` routes these paths to an in-process ASGI app instead of
# calling a handler.  It runs in *this* process (no port, no second config).
KERNEL = "__kernel__"
_LIFECYCLE_CONFIG = REPO / "packages/platform-core/config/authoritative-8080.yaml"

ROUTES: list[tuple[str, str]] = [
    ("/namespaces", NAMESPACE),
    ("/namespaces/{namespaceId}", NAMESPACE),
    ("/namespaces/{namespaceId}/status", NAMESPACE),
    ("/namespaces/{namespaceId}/roles", ROLES),
    ("/namespaces/{namespaceId}/roles/{roleId}", ROLES),
    ("/namespaces/{namespaceId}/grants", GRANTS),
    ("/namespaces/{namespaceId}/grants/{grantId}", GRANTS),
    # Platform-scoped roles and grants (GLOBAL partition, no namespace in path).
    ("/roles", PLATFORM_ROLES),
    ("/grants", GRANTS),
    ("/grants/{grantId}", GRANTS),
    ("/principals/{principalId}/grants", GRANTS),
    ("/namespaces/{namespaceId}/sources", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/rescan", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/tables", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/tables/{tableId}", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/approve", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/reject", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/tables/{tableId}/review", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/tables/{tableId}/metadata", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/tables/{tableId}/keys", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/tables/{tableId}/keep", SOURCES),
    (
        "/namespaces/{namespaceId}/sources/{sourceId}/tables/{tableId}/columns/{columnName}/review",
        SOURCES,
    ),
    (
        "/namespaces/{namespaceId}/sources/{sourceId}/tables/{tableId}/columns/{columnName}/metadata",
        SOURCES,
    ),
    ("/namespaces/{namespaceId}/sources/{sourceId}/scan", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/scan/{jobId}", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/rescan-schedule", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/event-rescan", SOURCES),
    ("/namespaces/{namespaceId}/sources/{sourceId}/metadata", SOURCES),
    ("/namespaces/{namespaceId}/sources/upload-urls", SOURCES),
    # P4 terms + data dictionary (F58-F66). Served by the in-process
    # platform_core kernel: terms read the published T-Box, dictionaries read
    # platform.dictionary_column/_refresh_run.
    ("/namespaces/{namespaceId}/terms", KERNEL),
    ("/namespaces/{namespaceId}/dictionaries", KERNEL),
    ("/namespaces/{namespaceId}/dictionaries/{sourceId}", KERNEL),
    ("/namespaces/{namespaceId}/dictionaries/{sourceId}/view", KERNEL),
    ("/namespaces/{namespaceId}/dictionaries/{sourceId}/comment-coverage", KERNEL),
    ("/namespaces/{namespaceId}/dictionaries/{sourceId}/refresh", KERNEL),
    # P8 ingestion runs (F17/F18). Read-only, served by the in-process
    # platform_core kernel from platform.import_batch/import_item.
    ("/namespaces/{namespaceId}/ingestion-runs", KERNEL),
    ("/namespaces/{namespaceId}/documents", SOURCES),
    ("/namespaces/{namespaceId}/documents/{documentId}/chunks", SOURCES),
    ("/namespaces/{namespaceId}/candidates", SOURCES),
    ("/namespaces/{namespaceId}/candidates/{candidateId}/approve", SOURCES),
    ("/namespaces/{namespaceId}/candidates/{candidateId}/reject", SOURCES),
    # DataLayerService: Query / KBSearch are the contract's POST forms of the
    # legacy platform GETs (/answer, /search, /browse/sparql), which are
    # deliberately not modelled (see 09 §4.16).
    ("/namespaces/{namespaceId}/query", DATA_LAYER),
    ("/namespaces/{namespaceId}/kb/search", DATA_LAYER),
    # GraphTraverse (DataLayerService). Implemented in the data-layer handler
    # from the start, but never routed locally, so it had never actually run.
    ("/namespaces/{namespaceId}/graph/traverse", DATA_LAYER),
    # RunSparql (DataLayerService, P6 F72–F74): the console behind /ontology/graph.
    ("/namespaces/{namespaceId}/sparql", DATA_LAYER),
    ("/namespaces/{namespaceId}/metrics", METRICS),
    ("/namespaces/{namespaceId}/metrics/{name}", METRICS),
    ("/namespaces/{namespaceId}/metrics/validate", METRICS),
    # P5 metric-catalog reads (F55/F57): the governed family index and the
    # report manifest live in the kernel; expose them under the contract path.
    ("/namespaces/{namespaceId}/metrics/report/manifest", KERNEL),
    ("/namespaces/{namespaceId}/metrics/families/{familyId}", KERNEL),
    ("/namespaces/{namespaceId}/bulk-delete-metrics", METRICS),
    ("/namespaces/{namespaceId}/import-osi", METRICS),
    ("/namespaces/{namespaceId}/import-osi/upload-url", METRICS),
    ("/namespaces/{namespaceId}/import-jobs/{jobId}", METRICS),
    ("/namespaces/{namespaceId}/export-osi", METRICS),
    ("/namespaces/{namespaceId}/induce", ONTOLOGY),
    ("/namespaces/{namespaceId}/induce/jobs", ONTOLOGY),
    ("/namespaces/{namespaceId}/induce/jobs/{jobId}", ONTOLOGY),
    ("/namespaces/{namespaceId}/induce/datasources", ONTOLOGY),
    ("/namespaces/{namespaceId}/induce/datasources/induced", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/accept", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/cancel", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/infer-constraints", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/infer-constraints/jobs/{jobId}", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/compile-constraints", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/validate", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/validate/jobs/{jobId}", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/repair-datatypes", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/{proposalId}/upload-url", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/update", ONTOLOGY),
    ("/namespaces/{namespaceId}/proposals/reject", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontology/foundational", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontology/foundational/{key}/load", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/search", ONTOLOGY),
    # ListStatements (F67–F70): read-only statement listing, namespace-scoped.
    ("/namespaces/{namespaceId}/graph/statements", ONTOLOGY),
    # GetCanvasManifest (F13): capabilities/limits the canvas must honour
    # before it draws. Read-only, no store access.
    ("/namespaces/{namespaceId}/graph/canvas/manifest", ONTOLOGY),
    # GetCanvasSubgraph (F08–F12) / FindGraphPath (F04–F07): read-only canvas
    # pages and bounded path search.
    ("/namespaces/{namespaceId}/graph/canvas", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/path", ONTOLOGY),
    # FindLinks: bounded (<=3 hop) neighbourhood around one IRI. Read-only.
    ("/namespaces/{namespaceId}/graph/links", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/ontology-overview", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/class", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/object-property", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/datatype-property", ONTOLOGY),
    # Health board (F126–F131): coverage, quality/reasoning and graph diff.
    # `validate` is a read-only measurement despite the POST verb.
    ("/namespaces/{namespaceId}/graph/snapshot", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/validate", ONTOLOGY),
    # GetReasoningStatus / MaterializeReasoning: inference lives in
    # platform_core (job table + reasoner client), so these two go to KERNEL
    # even though the other /graph/* reads are answered by 8101.
    ("/namespaces/{namespaceId}/graph/reasoning/materialize", KERNEL),
    ("/namespaces/{namespaceId}/graph/reasoning", KERNEL),
    ("/namespaces/{namespaceId}/graph/diff", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontologies", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/download", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontologies/upload-url", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/fetch", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/ingest-from-s3", ONTOLOGY),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/ingest-status/{jobId}", ONTOLOGY),
    ("/namespaces/{namespaceId}/embeddings", ONTOLOGY),
    ("/namespaces/{namespaceId}/embeddings/batch", ONTOLOGY),
    ("/namespaces/{namespaceId}/embeddings/search", ONTOLOGY),
    ("/namespaces/{namespaceId}/embeddings/by-entity/{entityUri}", ONTOLOGY),
    ("/namespaces/{namespaceId}/embeddings/by-ontology/{ontologyId}", ONTOLOGY),
    ("/namespaces/{namespaceId}/validate", ONTOLOGY),
    ("/namespaces/{namespaceId}/validate/jobs", ONTOLOGY),
    ("/namespaces/{namespaceId}/validate/jobs/{jobId}", ONTOLOGY),
    # T-Box lifecycle (09 §5.6). The state machine is platform-core's
    # `OntologyRegistry`; 8101 only serves the engine proxy above. Read routes
    # are exposed alongside the five write ones so the UI can render the chain.
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/versions", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}/diff", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/versions/{versionId}/export", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/import", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals/{proposalId}", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/proposals/{proposalId}/review", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/publish", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/rollback", KERNEL),
    # Governance console: audit read, chain verification and bundle migration.
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/events", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/verify", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/export", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/inspect", KERNEL),
    ("/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/import", KERNEL),
    # A-Box fact ledger (09 §4.7): the kernel keeps one ledger, so the namespace
    # segment is contract shape rather than a partition key.
    ("/namespaces/{namespaceId}/facts", KERNEL),
    ("/namespaces/{namespaceId}/facts/conflicts", KERNEL),
    # Adjudication is a write on the same ledger. These literal paths must be
    # registered before the `{factId}` placeholder; `_compile_routes` sorts
    # literal-heavy templates first.
    ("/namespaces/{namespaceId}/facts/conflicts/resolve", KERNEL),
    ("/namespaces/{namespaceId}/facts/conflicts/undo", KERNEL),
    # Predicate/subject-scoped batch keep (F33). Same literal-tail rule as the
    # two above: it must be registered before the `{factId}` placeholder.
    ("/namespaces/{namespaceId}/facts/conflicts/batch", KERNEL),
    # Batch retract also carries a literal tail, so it must not fall through to
    # `/facts/{factId}/retract` (that one keeps the single-fact shape).
    ("/namespaces/{namespaceId}/facts/retract", KERNEL),
    ("/namespaces/{namespaceId}/facts/{factId}", KERNEL),
    ("/namespaces/{namespaceId}/facts/{factId}/retract", KERNEL),
    ("/namespaces/{namespaceId}/facts/{factId}/restore", KERNEL),
    # The chain is readable without the assertion row: undo entries only hold an
    # eventId, so this path is the console's independent audit read.
    ("/namespaces/{namespaceId}/facts/{factId}/events", KERNEL),
    # GetEntity (DataLayer read). Kept un-namespaced to match the contract
    # (09 §4.8: GET /entities/{iri}); the IRI itself carries the identity.
    ("/entities/{entityId}/provenance", KERNEL),
    ("/entities/{entityId}", KERNEL),
    # GetMetric (F100): the platform metric card now carries `fieldBindings`,
    # so the read has to be reachable locally instead of only inside the kernel.
    ("/metrics/{metricId}", KERNEL),
    # F54: the metric card resolves its grain to an ontology class and offers an
    # entity-page hop, so the console needs the kernel's browse reads.
    ("/browse/ontology/tree", KERNEL),
    ("/browse/ontology/instances", KERNEL),
    # GetAnswerQuality (F86–F89): golden-set rerun, read-only.
    ("/answer/quality", KERNEL),
    # ListAnswerQualityRuns (F86 history half): reads platform.answer_quality_run.
    ("/answer/quality/runs", KERNEL),
    # CheckAnswerable (F76/F79): four-layer coverage and gaps/fixes. Same
    # platform-core evaluation as /answerable; the namespace segment is the
    # contract path, not a partition key in this local deployment.
    ("/namespaces/{namespaceId}/answerable", KERNEL),
    ("/system-health", ONTOLOGY),
]


def _compile_routes() -> list[tuple[re.Pattern[str], str, str]]:
    compiled = []
    for template, module in ROUTES:
        pattern = re.sub(r"\{([^}/]+)\}", r"(?P<\1>[^/]+)", template)
        compiled.append((re.compile(f"^{pattern}$"), template, module))
    # Literal segments win over placeholders: fewer {vars} first, longer first.
    compiled.sort(key=lambda entry: (entry[1].count("{"), -len(entry[1])))
    return compiled


_COMPILED_ROUTES = _compile_routes()
_MODULES: dict[str, Any] = {}


def _load_handler(module_name: str) -> Any:
    handler = _MODULES.get(module_name)
    if handler is None:
        import importlib

        handler = importlib.import_module(module_name).handler
        _MODULES[module_name] = handler
    return handler


def _match(path: str) -> tuple[str, dict[str, str], str] | None:
    for pattern, template, module in _COMPILED_ROUTES:
        match = pattern.match(path)
        if match:
            return template, match.groupdict(), module
    return None


# namespaceId is a UUID v4 in the contract. Validated once, here, for *every*
# route that carries it: a handler that skips the check (or looks the id up in
# a store that simply has no such row) answers 200 with an empty list, and a
# caller passing the namespace *name* then reads "no data" instead of "bad
# request". That failure mode is silent, so it is gated before dispatch rather
# than left to each handler.
#
# Ordering contract: this gate runs AFTER the authorization gate. A request
# without a valid bearer token is 401 even when the path id is malformed; only
# an authenticated caller may learn that the id itself is invalid (400).
_NAMESPACE_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def _invalid_namespace_id(path_params: dict[str, str]) -> str | None:
    """Return the offending value when ``namespaceId`` is present but not a UUID v4."""
    raw = path_params.get("namespaceId")
    if raw is None or _NAMESPACE_ID_RE.match(raw):
        return None
    return raw


# ---------------------------------------------------------------------------
# HTTP bridge
# ---------------------------------------------------------------------------


async def _kernel_call(method: str, path: str, body: bytes | None = None,
                       content_type: str = "application/json",
                       timeout: float = 120.0,
                       actor: str | None = None) -> tuple[int, bytes, str]:
    """One request to the lifecycle app, in process (httpx ASGITransport)."""
    import httpx

    headers = {"content-type": content_type} if body else {}
    if actor:
        # The kernel's own provenance seam (`Request.headers["x-actor"]`).
        headers["x-actor"] = actor
    transport = httpx.ASGITransport(app=_lifecycle_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://lifecycle", timeout=timeout
    ) as client:
        resp = await client.request(method, path, content=body, headers=headers)
    return resp.status_code, resp.content, resp.headers.get("content-type", "application/json")


_LIFECYCLE_APP: Any = None


def _lifecycle_dir() -> Path:
    base = Path(os.environ.get("TEMP") or os.environ.get("TMP") or ".") / "coa-local-stack"
    return base / "lifecycle"


def _configure_lifecycle_env() -> None:
    """Configuration the embedded platform_core app needs (local values only)."""
    work = _lifecycle_dir()
    defaults = {
        "PLATFORM__HTTP__BIND": "127.0.0.1",
        "PLATFORM__DATA_DIR": str(work),
        "PLATFORM__DATABASE__URL": "postgresql://platform:platform_dev@127.0.0.1:5444/serve_local",
        "PLATFORM__GRAPH__ENDPOINT": "http://127.0.0.1:7878",
        "PLATFORM__STORAGE__ROOT": str(work / "storage"),
        "PLATFORM__STORAGE__TMP_DIR": str(work / "tmp"),
        # The acceptance default (10% free) rejects registration on this dev box.
        "PLATFORM__STORAGE__MIN_FREE_PCT": "2",
        # Quoted: the loader parses env values as YAML, bare `off` becomes False.
        "PLATFORM__ONTOLOGY__INIT_MODE": '"off"',
        "PLATFORM__CANVAS__PROVIDER": '"off"',
        # Import validates `<shapes_dir>/<namespace>/*.ttl`; /data does not exist here.
        "PLATFORM__REASONING__SHAPES_DIR": str(work / "shapes"),
        # The consistency gate is fail-closed; use the shared local reasoner.
        "PLATFORM__REASONING__ENDPOINT": "http://127.0.0.1:7879",
        "PLATFORM__EMBEDDING__ENDPOINT": "http://127.0.0.1:8081/v1",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)
    for sub in ("", "storage", "tmp"):
        (work / sub).mkdir(parents=True, exist_ok=True)


def _assert_schema_version(metadata: Any, *, where: str) -> None:
    """Refuse to run when the database is not at the code's schema version.

    The bridge never migrates: applying DDL from a request path is the CLI's
    job.  Without this check a stale database starts fine and fails on the
    first write to a new table/column, so compare at start-up instead.
    """
    # The version gate moved with the migration chain (R1): platform-core no
    # longer owns the constant, so read it from the COA package.
    from coa_control_plane.platform_db import SUPPORTED_SCHEMA_VERSION

    row = metadata.query("SELECT to_regclass('platform.schema_version') AS reg")
    actual = 0
    if row and row[0]["reg"]:
        actual = int(
            metadata.query(
                "SELECT COALESCE(MAX(version), 0) AS v FROM platform.schema_version"
            )[0]["v"]
        )
    if actual == SUPPORTED_SCHEMA_VERSION:
        return
    database = (os.environ.get("PLATFORM__DATABASE__URL") or "<unset>").rsplit("/", 1)[-1]
    raise RuntimeError(
        f"E_DB_SCHEMA_VERSION_MISMATCH ({where}): database {database!r} is at "
        f"schema_version={actual}, code expects {SUPPORTED_SCHEMA_VERSION}. "
        "8099 does not migrate at request time; migrate both local databases, "
        "then restart: python doc/coa-x/tools/local_bootstrap.py migrate --dsn <dsn>"
    )


def _assert_lifecycle_schema() -> None:
    """Start-up gate for the embedded app's database (``serve_local``)."""
    _configure_lifecycle_env()
    from coa_control_plane.platform_db.connection import PgPool

    meta = PgPool(os.environ["PLATFORM__DATABASE__URL"], pool_max=1)
    try:
        meta.open(retry_seconds=15)
        _assert_schema_version(meta, where="8099 startup")
    finally:
        meta.close()


def _add_register_route(app: Any, runtime: Any) -> None:
    """Local draft-only registration: platform's HTTP import cannot do it.

    `/ontology/import` only stages, and `/ontology/imports/{id}/publish` ends in
    a pointer switch.  The only path that writes a `status='draft'` row is
    `OntologyRegistry.import_source` (file based), so this route adapts it.
    """
    import base64

    @app.post("/local/ontology/register")
    async def register(request: Request) -> dict[str, Any]:
        body = await request.json()
        raw = body.get("content")
        if isinstance(raw, str):
            data = raw.encode("utf-8")
        elif body.get("contentBase64"):
            data = base64.b64decode(body["contentBase64"])
        else:
            return {"error": "content or contentBase64 is required"}
        rdf_format = str(body.get("format") or "turtle")
        suffix = "trig" if rdf_format == "trig" else "ttl"
        namespace = body.get("targetNamespace") or body.get("namespace")
        existing = runtime.ontology.list_versions()
        semver = str(body.get("semver") or f"0.{len(existing) + 1}.0")
        path = _lifecycle_dir() / f"register-{uuid.uuid4().hex[:8]}.{suffix}"
        path.write_bytes(data)
        try:
            result = runtime.ontology.import_source(
                str(path), semver, label=namespace, rdf_format=rdf_format
            )
        finally:
            path.unlink(missing_ok=True)
        return {**result, "targetNamespace": namespace}


_LIFECYCLE_RUNTIME: Any = None


def _lifecycle_runtime() -> Any:
    """The assembled platform runtime (ledger, graph, metadata) for this process."""
    _lifecycle_app()
    return _LIFECYCLE_RUNTIME


def _lifecycle_app() -> Any:
    """Build the platform_core ASGI app once, inside the bridge process."""
    global _LIFECYCLE_APP, _LIFECYCLE_RUNTIME
    if _LIFECYCLE_APP is not None:
        return _LIFECYCLE_APP
    _configure_lifecycle_env()
    from platform_core.api import create_app
    from platform_core.assembly import assemble
    from platform_core.config import load_config
    from platform_core.ontology_init import start as start_ontology

    bundle = load_config(_LIFECYCLE_CONFIG)
    # Local A-Box graphs use the namespace-scoped https naming, which the
    # /reasoning/materialize body guard (urn:platform: only) rejects. The stack
    # passes the concrete graph in, so set it on the assembled config instead.
    local_abox = os.environ.get("COA_LOCAL_REASONING_ABOX_GRAPH")
    if local_abox:
        bundle.config.reasoning.abox_graphs = [local_abox]
    runtime = assemble(bundle)
    # F58/F59 read the lexicon folio from the namespace A-Box base
    # (https://coa.local/graph/...), which sits outside the adapter's production
    # write-safety whitelist (urn:platform:). The widening is opt-in so it can
    # never be inherited by a production deployment:
    #   COA_LOCAL_GRAPH_ALLOWED_EXTRA_PREFIXES = comma-separated prefixes,
    #   default empty (nothing widened).
    # 本地放宽，生产不放宽；该前缀不得进入生产白名单。
    extra_prefixes = tuple(
        item.strip()
        for item in os.environ.get(
            "COA_LOCAL_GRAPH_ALLOWED_EXTRA_PREFIXES", ""
        ).split(",")
        if item.strip()
    )
    if extra_prefixes:
        prefixes = tuple(getattr(runtime.graph, "_allowed_prefixes", ()))
        runtime.graph._allowed_prefixes = (
            *prefixes,
            *(prefix for prefix in extra_prefixes if prefix not in prefixes),
        )
    # The CLI's self-check normally opens the pool; without it every DB route
    # answers 503 E_DB_UNAVAILABLE.  No HTTP server means no lifespan either.
    runtime.metadata.open(retry_seconds=30.0)
    # Same gate as start-up, for processes that build the app without main().
    _assert_schema_version(runtime.metadata, where="in-process app")
    start_ontology(runtime)
    app = create_app(runtime, [])
    _add_register_route(app, runtime)
    _LIFECYCLE_APP = app
    _LIFECYCLE_RUNTIME = runtime
    return app


def _install_fact_ledger() -> None:
    """Point candidate approval at the platform fact ledger.

    The bridge already hosts the platform runtime in-process, so approval can
    write the ledger row, its audit event and the A-Box projection without a
    second network hop.  Without this hook ``handle_approve_candidate`` answers
    503 instead of writing the graph alone.
    """
    from coa_sources.api import candidate_routes

    def record(**fields: Any) -> dict[str, Any]:
        return _lifecycle_runtime().facts.record(**fields)

    def retract(fact_id: str, reason: str, actor: str) -> dict[str, Any]:
        return _lifecycle_runtime().facts.retract(fact_id, reason, actor)

    candidate_routes.install_fact_ledger(record, retract)
    print("[api] candidate approval -> platform fact ledger (in-process runtime)")


def _install_dictionary_introspector() -> None:
    """Wire RefreshDictionaries to the local source metadata.

    The demo source declares a Glue database, but its tables are physically in
    the same PostgreSQL that backs platform_core.  The adapter resolves the
    source row + catalog snapshot, then reads ``information_schema`` and
    ``pg_description`` for the snapshot's tables - real columns, real
    nullability, real comments.  A missing source, missing schema or a table
    that is absent from PostgreSQL fails explicitly; nothing is invented.
    """
    from coa_common.dao import DynamoDBDAO
    from platform_core.catalog import introspect_pg
    from platform_core.dictionary_api import (
        SourceColumn,
        SourceIntrospection,
        SourceIntrospectionError,
        install_source_introspector,
    )
    from platform_core.errors import PortError

    source_kinds = {
        "GLUE_DATABASE": "glue",
        "POSTGRESQL": "postgresql",
        "MYSQL": "mysql",
        "REDSHIFT": "redshift",
        "SQLSERVER": "sqlserver",
        "SNOWFLAKE": "snowflake",
        "DUCKDB": "duckdb",
    }

    def introspect(namespace_id: str, source_id: str) -> SourceIntrospection:
        dao = DynamoDBDAO(os.environ["SOURCES_TABLE"], region=os.environ["AWS_REGION"])
        item = dao.get({"PK": f"NS#{namespace_id}", "SK": f"SRC#{source_id}"})
        if not item:
            raise SourceIntrospectionError(
                "E_DICTIONARY_SOURCE_NOT_FOUND",
                f"source {source_id!r} is not registered in namespace {namespace_id!r}",
                status_code=404,
            )
        try:
            config = json.loads(item.get("configuration") or "{}")
        except ValueError as exc:
            raise SourceIntrospectionError(
                "E_DICTIONARY_SOURCE_CONFIG_INVALID",
                f"source {source_id!r} has an unreadable configuration: {exc}",
                status_code=422,
            ) from None
        kind = source_kinds.get(str(item.get("sourceSubType") or "").upper())
        if kind is None:
            raise SourceIntrospectionError(
                "E_DICTIONARY_SOURCE_KIND_UNSUPPORTED",
                f"source {source_id!r} has unsupported subtype "
                f"{item.get('sourceSubType')!r}",
                status_code=422,
            )
        schema = config.get("databaseName") or config.get("schema")
        if not schema:
            raise SourceIntrospectionError(
                "E_DICTIONARY_SOURCE_SCHEMA_MISSING",
                f"source {source_id!r} configuration has no databaseName/schema",
                status_code=422,
            )
        catalog = config.get("catalogId") or config.get("catalogName") or "local"
        try:
            snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise SourceIntrospectionError(
                "E_DICTIONARY_SNAPSHOT_MISSING",
                f"catalog snapshot is missing at {SNAPSHOT_PATH}",
                status_code=503,
            ) from None
        entry = (snapshot.get("data_sources") or {}).get(source_id) or {}
        table_ids = sorted((entry.get("tables") or {}).keys())
        tables = sorted({table_id.partition(".")[2] or table_id for table_id in table_ids})
        if not tables:
            raise SourceIntrospectionError(
                "E_DICTIONARY_SOURCE_EMPTY",
                f"source {source_id!r} has no tables in the catalog snapshot",
                status_code=422,
            )
        try:
            rows = introspect_pg(_lifecycle_runtime().metadata, schema, tables)
        except PortError as exc:
            raise SourceIntrospectionError(
                "E_DICTIONARY_SOURCE_UNAVAILABLE", exc.message, status_code=503
            ) from None
        columns = [
            SourceColumn(
                table=row["table"],
                column=row["column"],
                data_type=row["dataType"],
                is_nullable=bool(row["isNullable"]),
                comment=row.get("comment"),
            )
            for row in rows
        ]
        if not columns:
            raise SourceIntrospectionError(
                "E_DICTIONARY_SOURCE_EMPTY",
                f"tables {tables!r} exist in the snapshot but returned zero "
                f"columns from {schema!r}",
                status_code=422,
            )
        warnings: list[str] = []
        if entry.get("catalog_available") is False:
            warnings.append("E_SOURCE_CATALOG_UNAVAILABLE")
        return SourceIntrospection(
            source_kind=kind,
            catalog=str(catalog),
            schema=str(schema),
            columns=columns,
            warnings=warnings,
        )

    install_source_introspector(introspect)
    print("[api] dictionary refresh -> local source metadata (information_schema)")


def _install_document_index() -> None:
    """Index ingested documents into the store KBSearch actually reads.

    An upload lands in the local document store (``coa-local-documents`` /
    ``coa-local-document-chunks``) plus ontology vectors.  Serve answers
    KBSearch and Ask from ``platform.document`` / ``platform.document_chunk`` /
    ``platform.chunk_embedding`` in the platform database, which until now only
    the bootstrap seed filled.  AWS fills it in its ingestion/index step; the
    local bridge skipped that step, so uploaded documents could never be found
    by KB search.  After every successful ingest, mirror the parsed chunks and
    run the real ``index_document`` so both stores describe the same document.
    """
    from coa_sources.documents import local_worker
    from coa_sources.documents import store as document_store

    original = local_worker.ingest

    def mirror(namespace_id: str, document_id: str) -> None:
        document = document_store.get_document(namespace_id, document_id) or {}
        chunks = document_store.list_chunk_items(namespace_id, document_id)
        if not chunks:
            return
        runtime = _lifecycle_runtime()
        with runtime.metadata.tx() as tx:
            tx.execute(
                """
                INSERT INTO platform.document (
                    document_id, sha256, bucket, object_key, filename, mime_type,
                    size_bytes, status, page_count, char_count, chunk_count,
                    parser, parser_version, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,'parsed',%s,%s,%s,'local-md','1',%s::jsonb)
                ON CONFLICT (document_id) DO UPDATE SET
                    status = 'parsed',
                    chunk_count = EXCLUDED.chunk_count,
                    char_count = EXCLUDED.char_count
                """,
                (
                    document_id,
                    document.get("contentHash") or document_id,
                    document.get("s3Bucket") or "local",
                    document.get("s3Key") or document_id,
                    document.get("filename") or f"{document_id}.txt",
                    document.get("contentType") or "text/plain",
                    int(document.get("sizeBytes") or 0),
                    1,
                    sum(len(chunk.get("text") or "") for chunk in chunks),
                    len(chunks),
                    json.dumps({"namespaceId": namespace_id}),
                ),
            )
            for chunk in chunks:
                text = chunk.get("text") or ""
                tx.execute(
                    """
                    INSERT INTO platform.document_chunk (
                        chunk_id, document_id, seq, page_from, page_to,
                        char_start, char_end, text, token_estimate
                    ) VALUES (%s,%s,%s,1,1,%s,%s,%s,%s)
                    ON CONFLICT (chunk_id) DO NOTHING
                    """,
                    (
                        chunk["chunkId"],
                        document_id,
                        int(chunk.get("seq") or 0),
                        int(chunk.get("charStart") or 0),
                        int(chunk.get("charEnd") or 0),
                        text,
                        max(1, len(text) // 4),
                    ),
                )
        runtime.search.index_document(document_id)
        print(f"[api] serve index: {document_id} ({len(chunks)} chunks)")

    def ingest_and_index(**fields: Any) -> None:
        original(**fields)
        try:
            mirror(fields["namespace_id"], fields["document_id"])
        except Exception as exc:  # the ingest itself already succeeded
            print(f"[api] serve index failed for {fields.get('document_id')}: {exc}")

    local_worker.ingest = ingest_and_index
    print("[api] document ingest -> serve index (document/chunk/chunk_embedding)")


def _kernel_translate(
    template: str, path_params: dict[str, str], method: str, body: bytes,
    query: dict[str, str] | None = None, actor: str = "operator",
) -> tuple[str, str, bytes | None]:
    """Map a contract path onto the kernel's ``/ontology/*`` surface.

    Only the five lifecycle writes plus the read routes needed to render the
    chain are mapped; anything else is a bug in ROUTES.
    """
    # P4 terms/dictionary routes already use the kernel's contract shape
    # (`/namespaces/{ns}/terms`, `/namespaces/{ns}/dictionaries/...`), so they
    # are forwarded unchanged instead of being rewritten into `/ontology/*`.
    if (
        template.startswith("/namespaces/{namespaceId}/terms")
        or template.startswith("/namespaces/{namespaceId}/dictionaries")
        or template.startswith("/namespaces/{namespaceId}/ingestion-runs")
    ):
        target = template.format(**path_params)
        if query:
            target = f"{target}?{urlencode(query)}"
        forwarded = body or None
        if method == "POST" and template.endswith("/dictionaries/{sourceId}/refresh") and body:
            try:
                payload = json.loads(body.decode("utf-8"))
            except ValueError:
                payload = None
            if isinstance(payload, dict):
                # `requestedBy` is provenance; it must not come from the client.
                payload["requestedBy"] = actor
                forwarded = json.dumps(payload).encode("utf-8")
        return method, target, forwarded

    ontology_id = path_params.get("ontologyId", "")
    version_id = path_params.get("versionId", "")
    proposal_id = path_params.get("proposalId", "")
    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    # Provenance is taken from the authenticated caller, never from the body:
    # a client-supplied actor would let one user write audit rows as another.
    payload = {**payload, "actor": actor}

    # Bundle migration must be matched before the generic `/import` and
    # `/export` routes: `.../bundles/import` also ends with `/import`.
    if template.endswith("/bundles/export"):
        bundles = _lifecycle_dir() / "bundles"
        bundles.mkdir(parents=True, exist_ok=True)
        forwarded = {
            "out": payload.get("out") or str(bundles),
            "tag": payload.get("tag") or f"bundle-{uuid.uuid4().hex[:8]}",
            # `includeInstances` is the contract's name for the A-Box/blobs half.
            "includeBlobs": bool(
                payload.get("includeBlobs", payload.get("includeInstances", False))
            ),
            "actor": payload.get("actor") or "operator",
        }
        return "POST", "/governance/bundle/export", json.dumps(forwarded).encode("utf-8")

    if template.endswith("/bundles/inspect"):
        q = query or {}
        path = q.get("path") or q.get("bundleRef")
        if not path:
            raise ValueError("inspect requires path or bundleRef")
        return "GET", f"/governance/bundle/inspect?path={quote(path)}", None

    if template.endswith("/bundles/import"):
        forwarded = {
            "bundle": payload.get("bundle") or payload.get("bundleRef"),
            "database": payload.get("database") or "platform_restore_test",
            "replace": bool(payload.get("replace", False)),
            "keepDbOnFailure": bool(payload.get("keepDbOnFailure", False)),
            "actor": payload.get("actor") or "operator",
        }
        return "POST", "/governance/bundle/import", json.dumps(forwarded).encode("utf-8")

    if template.endswith("/import"):
        # ImportOntology: register the uploaded TTL as a draft version.
        merged = {**payload}
        merged.setdefault("targetNamespace", ontology_id)
        return "POST", "/ontology/import", json.dumps(merged).encode("utf-8")

    if template.endswith("/versions/{versionId}/diff"):
        q = (query or {}).get("against")
        suffix = f"?against={unquote(q)}" if q else ""
        return "GET", f"/ontology/versions/{version_id}/diff{suffix}", None

    if template.endswith("/versions/{versionId}/export"):
        fmt = (query or {}).get("format") or "turtle"
        return "GET", f"/ontology/versions/{version_id}/export?format={unquote(fmt)}", None

    if template.endswith("/versions/{versionId}"):
        return "GET", f"/ontology/versions/{version_id}", None

    if template.endswith("/versions"):
        return "GET", "/ontology/versions", None

    if template.endswith("/proposals/{proposalId}/review"):
        decision = str(payload.get("decision") or "").upper()
        action = "approve" if decision == "APPROVE" else "reject"
        forwarded = {
            "actor": payload.get("actor") or "operator",
            "reason": payload.get("comment") or payload.get("reason"),
        }
        return (
            "POST",
            f"/governance/proposals/{proposal_id}/{action}",
            json.dumps(forwarded).encode("utf-8"),
        )

    if template.endswith("/proposals/{proposalId}"):
        return "GET", f"/governance/proposals/{proposal_id}", None

    if template.endswith("/proposals"):
        if method == "GET":
            return "GET", "/governance/proposals", None
        # ProposeOntologyVersion: the version was registered by `import` in the
        # preceding step, so it is named explicitly (contract field `versionId`)
        # or inferred from `baseVersionId` when proposals target the draft.
        version = payload.get("versionId") or payload.get("baseVersionId")
        if not version:
            raise ValueError(
                "proposals requires versionId (the registered draft) or baseVersionId"
            )
        forwarded = {
            "changeSummary": payload.get("rationale") or payload.get("changeSummary") or "",
            "againstVersion": payload.get("againstVersion"),
            "actor": payload.get("actor") or "operator",
        }
        return (
            "POST",
            f"/ontology/versions/{version}/propose",
            json.dumps(forwarded).encode("utf-8"),
        )

    if template.endswith("/publish"):
        # F113: `planOnly` runs publish's own gate helpers without writing any
        # version, event or pointer. The kernel names the switch `dryRun`, so
        # the bridge translates; when both spellings arrive `planOnly` wins.
        plan_only = payload["planOnly"] if "planOnly" in payload else payload.get("dryRun", False)
        if not isinstance(plan_only, bool):
            raise ValueError("planOnly must be a boolean")
        # F112/F114: re-activate an already registered version instead of
        # staging a new one. Rejected when not a boolean rather than coerced,
        # so a typo cannot turn into a silent no-op.
        publish_existing = payload.get("publishExisting", False)
        if not isinstance(publish_existing, bool):
            raise ValueError("publishExisting must be a boolean")
        forwarded = {
            "versionId": payload.get("versionId"),
            "proposalId": payload.get("proposalId"),
            "acknowledgeBreaking": bool(payload.get("acknowledgeBreaking", False)),
            "actor": payload.get("actor") or "operator",
            "reason": payload.get("reason"),
            "expectedVersionId": payload.get("expectedVersionId"),
            "dryRun": plan_only,
            "publishExisting": publish_existing,
        }
        return "POST", "/governance/publish", json.dumps(forwarded).encode("utf-8")

    if template.endswith("/rollback"):
        target = payload.get("targetVersionId") or payload.get("versionId")
        if not target:
            raise ValueError("rollback requires targetVersionId")
        # F117: `newVersion` is the bridge switch; `mode` is the contract
        # spelling. There is no default: a caller that omits both is asking for
        # a rollback whose effect it never stated, so the bridge rejects it
        # instead of guessing POINTER_ONLY.
        mode = payload.get("mode")
        new_version = payload.get("newVersion")
        if new_version is not None and not isinstance(new_version, bool):
            raise ValueError("newVersion must be a boolean")
        if mode is None:
            if new_version is None:
                raise ValueError(
                    "rollback requires mode=POINTER_ONLY|NEW_VERSION (or newVersion)"
                )
            mode = "NEW_VERSION" if new_version else "POINTER_ONLY"
        if mode not in ("POINTER_ONLY", "NEW_VERSION"):
            raise ValueError("rollback mode must be POINTER_ONLY or NEW_VERSION")
        plan_only = payload["planOnly"] if "planOnly" in payload else payload.get("dryRun", False)
        if not isinstance(plan_only, bool):
            raise ValueError("planOnly must be a boolean")
        if plan_only:
            # F115: preview only. The plan route is read-only and takes the
            # target version id; the mode is echoed by the caller, because the
            # kernel plan describes the target that would be restored.
            return "GET", f"/governance/rollback/plan?versionId={target}", None
        forwarded = {
            "versionId": target,
            "actor": payload.get("actor") or "operator",
            "reason": payload.get("reason"),
        }
        if mode == "NEW_VERSION":
            # The kernel's rollback copies the target content into a new
            # version and moves the pointer there (OQ-48). It has no
            # optimistic-concurrency parameter, so `expectedVersionId` is not
            # forwarded on this branch rather than being silently dropped for
            # a path that claims to honour it.
            return "POST", "/governance/rollback", json.dumps(forwarded).encode("utf-8")
        forwarded["expectedVersionId"] = payload.get("expectedVersionId")
        return "POST", "/governance/rollback-to", json.dumps(forwarded).encode("utf-8")

    if template.endswith("/events") and "/facts" not in template:
        q = query or {}
        params = {
            key: q[key] for key in ("versionId", "action", "limit") if q.get(key)
        }
        suffix = f"?{urlencode(params)}" if params else ""
        return "GET", f"/governance/events{suffix}", None

    if template.endswith("/verify"):
        return "GET", "/ontology/verify", None

    if template == "/answer/quality":
        q = query or {}
        params = {
            key: q[key] for key in ("strategy", "limit", "caseId") if q.get(key)
        }
        suffix = f"?{urlencode(params)}" if params else ""
        return "GET", f"/answer/quality{suffix}", None

    if template == "/answer/quality/runs":
        q = query or {}
        params = {
            key: q[key] for key in ("strategy", "limit", "since") if q.get(key)
        }
        suffix = f"?{urlencode(params)}" if params else ""
        return "GET", f"/answer/quality/runs{suffix}", None

    if template == "/metrics/{metricId}":
        metric_id = path_params.get("metricId", "")
        return "GET", f"/metrics/{quote(metric_id, safe='')}", None

    if template == "/namespaces/{namespaceId}/metrics/report/manifest":
        q = query or {}
        params = {
            key: q[key]
            for key in ("scope", "domain", "evidenceBasis", "publishable")
            if q.get(key) not in (None, "")
        }
        suffix = f"?{urlencode(params)}" if params else ""
        return "GET", f"/metrics/report/manifest{suffix}", None

    if template == "/namespaces/{namespaceId}/metrics/families/{familyId}":
        family_id = path_params.get("familyId", "")
        return "GET", f"/metrics/report/families/{quote(family_id, safe='')}", None

    if template == "/browse/ontology/tree":
        return "GET", "/browse/ontology/tree", None

    if template == "/browse/ontology/instances":
        q = query or {}
        params = {
            key: q[key]
            for key in ("class", "limit", "offset")
            if q.get(key) not in (None, "")
        }
        suffix = f"?{urlencode(params)}" if params else ""
        return "GET", f"/browse/ontology/instances{suffix}", None

    if template == "/entities/{entityId}/provenance":
        iri = path_params.get("entityId", "")
        q = query or {}
        params = {key: q[key] for key in ("limit",) if q.get(key)}
        suffix = f"?{urlencode(params)}" if params else ""
        return "GET", f"/entities/{quote(iri, safe='')}/provenance{suffix}", None

    if template == "/entities/{entityId}":
        iri = path_params.get("entityId", "")
        q = query or {}
        params = {key: q[key] for key in ("limit",) if q.get(key)}
        suffix = f"?{urlencode(params)}" if params else ""
        # Encode the whole IRI so its slashes cannot be read as path separators.
        return "GET", f"/entities/{quote(iri, safe='')}{suffix}", None

    if template == "/namespaces/{namespaceId}/graph/reasoning/materialize":
        if method != "POST":
            raise ValueError(f"no kernel mapping for {method} {template}")
        forwarded = {
            key: payload[key]
            for key in ("profile", "force")
            if payload.get(key) not in (None, "")
        }
        return (
            "POST",
            "/reasoning/materialize",
            json.dumps(forwarded, ensure_ascii=False).encode("utf-8"),
        )

    if template == "/namespaces/{namespaceId}/graph/reasoning":
        return "GET", "/reasoning/status", None

    if template == "/namespaces/{namespaceId}/answerable":
        if method != "POST":
            raise ValueError(f"no kernel mapping for {method} {template}")
        namespace_id = quote(path_params.get("namespaceId", ""), safe="")
        return (
            "POST",
            f"/namespaces/{namespace_id}/answerable",
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

    if "/facts" in template:
        fact_id = path_params.get("factId", "")
        q = query or {}
        if template.endswith("/facts") and method == "POST":
            # Assert one fact. Without this the shared tail below answered a
            # list, so a POST looked like it succeeded while writing nothing.
            forwarded = {
                key: payload[key]
                for key in (
                    "subject", "predicate", "object", "objectKind", "graph",
                    "sourceKind", "sourceDocumentId", "sourceRunId", "actor",
                )
                if payload.get(key) not in (None, "")
            }
            return (
                "POST",
                "/facts",
                json.dumps(forwarded, ensure_ascii=False).encode("utf-8"),
            )
        if template.endswith("/events"):
            params = {
                key: q[key] for key in ("limit", "before", "format") if q.get(key)
            }
            suffix = f"?{urlencode(params)}" if params else ""
            return "GET", f"/facts/{quote(fact_id)}/events{suffix}", None
        if template.endswith("/facts/conflicts/batch"):
            # Batch keep is scoped by an explicit filter (predicate/subject/source)
            # and one chosen value; preview by default, write only when dryRun is false.
            forwarded = {
                key: payload[key]
                for key in (
                    "keep", "predicate", "subject", "sourceDocumentId", "actor", "reason",
                )
                if payload.get(key) not in (None, "")
            }
            if "dryRun" in payload:
                forwarded["dryRun"] = bool(payload.get("dryRun"))
            return (
                "POST",
                "/facts/conflicts/batch",
                json.dumps(forwarded, ensure_ascii=False).encode("utf-8"),
            )
        if template.endswith("/facts/conflicts/resolve"):
            # Same fields as the kernel's resolve endpoint; drop empty ones so the
            # kernel's defaults (actor=operator, mergedObjectKind=iri) still apply.
            forwarded = {
                key: payload[key]
                for key in (
                    "subject", "predicate", "action", "actor", "reason", "keep",
                    "mergedObject", "mergedObjectKind", "graph", "sourceDocumentId",
                )
                if payload.get(key) not in (None, "")
            }
            # `action=batch` previews by default, so an explicit dryRun=false is
            # the only way to write; it must survive the translation.
            if "dryRun" in payload:
                forwarded["dryRun"] = bool(payload.get("dryRun"))
            return (
                "POST",
                "/facts/conflicts/resolve",
                json.dumps(forwarded, ensure_ascii=False).encode("utf-8"),
            )
        if template.endswith("/facts/conflicts/undo"):
            forwarded = {
                key: payload[key]
                for key in ("eventId", "subject", "predicate", "actor", "reason")
                if payload.get(key) not in (None, "")
            }
            if "dryRun" in payload:
                forwarded["dryRun"] = bool(payload.get("dryRun"))
            return (
                "POST",
                "/facts/conflicts/undo",
                json.dumps(forwarded, ensure_ascii=False).encode("utf-8"),
            )
        if template.endswith("/facts/conflicts"):
            suffix = (
                "?includeAccepted=true"
                if str(q.get("includeAccepted", "")).lower() in ("1", "true", "yes")
                else ""
            )
            return "GET", f"/facts/conflicts{suffix}", None
        if template.endswith("/facts/retract"):
            # Batch retract: keep the payload shape (factIds/filters/dryRun); the
            # kernel previews unless dryRun is explicitly false. Registered ahead
            # of the single-fact `/retract` tail on purpose.
            forwarded = {
                key: payload[key]
                for key in (
                    "factIds", "subject", "predicate", "graph", "sourceDocumentId",
                    "actor", "reason", "dryRun",
                )
                if payload.get(key) not in (None, "", [])
            }
            return (
                "POST",
                "/facts/retract",
                json.dumps(forwarded, ensure_ascii=False).encode("utf-8"),
            )
        if template.endswith("/retract"):
            forwarded = {
                "actor": payload.get("actor") or "operator",
                "reason": payload.get("reason"),
            }
            return (
                "POST",
                f"/facts/{quote(fact_id)}/retract",
                json.dumps(forwarded).encode("utf-8"),
            )
        if template.endswith("/restore"):
            forwarded = {
                "actor": payload.get("actor") or "operator",
                "reason": payload.get("reason"),
            }
            return (
                "POST",
                f"/facts/{quote(fact_id)}/restore",
                json.dumps(forwarded).encode("utf-8"),
            )
        if template.endswith("/{factId}"):
            return "GET", f"/facts/{quote(fact_id)}", None
        params = {
            key: q[key]
            for key in ("state", "subject", "predicate", "sourceDocumentId", "conflict", "limit")
            if q.get(key)
        }
        suffix = f"?{urlencode(params)}" if params else ""
        return "GET", f"/facts{suffix}", None

    raise ValueError(f"no kernel mapping for {method} {template}")


async def _kernel_register_version(
    template: str, path_params: dict[str, str], body: bytes, actor: str
) -> tuple[int, bytes, str]:
    """ImportOntology: register the uploaded T-Box as a *draft* version.

    `/ontology/import` alone only stages (no `ontology_version` row), and
    `/ontology/imports/{id}/publish` publishes (pointer switch) rather than
    registering.  The draft-only path is `import_source`, exposed to the
    in-process app as `/local/ontology/register` (added by
    `_add_register_route`) because `platform_core.api` has no such endpoint.
    """
    ontology_id = path_params.get("ontologyId", "")
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except ValueError:
        return 400, b'{"error":"import body is not valid JSON"}', "application/json"
    if not isinstance(payload, dict):
        payload = {}
    register = {
        key: payload[key]
        for key in ("content", "contentBase64", "format", "semver")
        if payload.get(key)
    }
    register["targetNamespace"] = payload.get("targetNamespace") or ontology_id
    status, content, ctype = await _kernel_call(
        "POST", "/local/ontology/register", json.dumps(register).encode("utf-8"), actor=actor
    )
    if status >= 300:
        return status, content, ctype
    try:
        data = json.loads(content or b"{}")
    except ValueError:
        data = {}
    merged = {
        "importId": data.get("versionId"),
        "versionId": data.get("versionId"),
        "semver": data.get("semver"),
        "status": data.get("status") or "draft",
        "targetNamespace": register["targetNamespace"],
        "contentHash": data.get("contentHash"),
        "triples": data.get("tripleCount"),
        "skipped": data.get("skipped", False),
        "conflicts": data.get("conflicts", []),
        "changeSummary": payload.get("changeSummary"),
    }
    return 200, json.dumps(merged, ensure_ascii=False).encode("utf-8"), "application/json"


async def _kernel_proxy(
    request: Request, template: str, path_params: dict[str, str], actor: str
) -> Response:
    """Forward one lifecycle request and normalise the contract's field names."""
    body = await request.body()
    if (
        request.method == "POST"
        and template.endswith("/ontologies/{ontologyId}/import")
    ):
        status, content, ctype = await _kernel_register_version(
            template, path_params, body, actor
        )
        return Response(content=content, status_code=status, media_type=ctype)
    try:
        method, target, forwarded = _kernel_translate(
            template, path_params, request.method, body, dict(request.query_params), actor
        )
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    try:
        status, content, ctype = await _kernel_call(
            method,
            target,
            forwarded,
            # RDFS closure + ELK on the demo A-Box takes ~13s at the engine;
            # the rdflib diff around it needs a longer socket budget.
            timeout=600.0 if template.endswith("/graph/reasoning/materialize") else 120.0,
            actor=actor,
        )
    except Exception as exc:  # kernel down: say so instead of a bare 500
        return JSONResponse(
            {
                "error": "ontology lifecycle unavailable",
                "detail": str(exc),
                "mode": "in-process",
            },
            status_code=503,
        )

    # GetReasoningStatus: the kernel reports its own job table; the contract
    # speaks in `available`/`engine`/`failures`. Translate instead of leaking
    # the kernel payload, and keep `detail` readable for the health board.
    if status < 300 and request.method == "GET" and template.endswith(
        "/graph/reasoning"
    ):
        try:
            kernel_status = json.loads(content or b"{}")
        except ValueError:
            kernel_status = {}
        if isinstance(kernel_status, dict):
            last = kernel_status.get("lastJob") or {}
            available = bool(kernel_status.get("available"))
            failed_count = int(kernel_status.get("failedJobs") or 0)
            translated = {
                "available": available,
                "engine": (
                    kernel_status.get("provider") or kernel_status.get("engine")
                ) if available else None,
                "failures": {
                    "count": failed_count,
                    # Only name the failed rows when there are any; a zero
                    # count with "state=failed" would contradict itself.
                    "detail": (
                        "platform.reasoning_job kind=materialize state=failed"
                        if failed_count
                        else None
                    ),
                },
                "detail": (
                    f"mode={kernel_status.get('mode')} "
                    f"profile={kernel_status.get('profile')} "
                    f"lastJob={last.get('state') or 'none'} "
                    f"inferred={last.get('inferred')}"
                ),
                "source": (
                    "platform-core /reasoning/status (in-process kernel; "
                    "platform.reasoning_job)"
                ),
                "sampledAt": datetime.now(timezone.utc).isoformat(),
                # The health board shows the SHACL gate from the last run, so
                # the stage results travel with the status instead of being
                # inferred from /graph/validate, which cannot see them.
                "inferredTriples": kernel_status.get("inferredTriples"),
                "lastJob": (
                    {
                        "jobId": last.get("jobId"),
                        "state": last.get("state"),
                        "inferred": last.get("inferred"),
                        "consistent": last.get("consistent"),
                        "finishedAt": last.get("finishedAt"),
                        "skipped": bool((last.get("result") or {}).get("skipped")),
                        "stages": (last.get("result") or {}).get("stages") or {},
                    }
                    if last
                    else None
                ),
            }
            content = json.dumps(translated, ensure_ascii=False).encode("utf-8")

    # Two contract responses name the result differently from the kernel:
    # PublishOntology returns `publishedVersion`, RollbackOntology the same.
    # Use the translated method, not the client method: a `planOnly` rollback
    # arrives as POST but is served by the read-only plan route, and must not
    # come back with a `publishedVersion` field at all.
    if status < 300 and method == "POST" and template.endswith(
        ("/publish", "/rollback")
    ):
        try:
            data = json.loads(content or b"{}")
        except ValueError:
            data = {}
        if isinstance(data, dict):
            if "publishedVersion" not in data:
                data["publishedVersion"] = data.get("id")
            content = json.dumps(data, ensure_ascii=False).encode("utf-8")

    # GetOntologyVersion: the registry returns `id` / `graph` / `tripleCount`;
    # the contract names them `versionId` / `graphUri` / `statementCount`.
    if status < 300 and request.method == "GET" and template.endswith(
        "/versions/{versionId}"
    ):
        try:
            detail = json.loads(content or b"{}")
        except ValueError:
            detail = None
        if isinstance(detail, dict) and "id" in detail:
            detail.setdefault("versionId", detail["id"])
            detail.setdefault("graphUri", detail.get("graph"))
            detail.setdefault("statementCount", detail.get("tripleCount"))
            content = json.dumps(detail, ensure_ascii=False).encode("utf-8")

    # ListOntologyEvents: the kernel names the action/timestamp `action` /
    # `createdAt`; the contract uses `type` / `at`. Keep both so older callers
    # and the governance console can read either spelling.
    if status < 300 and request.method == "GET" and template.endswith("/events"):
        try:
            events = json.loads(content or b"{}")
        except ValueError:
            events = None
        if isinstance(events, dict):
            for item in events.get("items") or []:
                if isinstance(item, dict):
                    item.setdefault("type", item.get("action"))
                    item.setdefault("at", item.get("createdAt"))
            content = json.dumps(events, ensure_ascii=False).encode("utf-8")
    return Response(content=content, status_code=status, media_type=ctype)


_HEALTH_PROBE_TIMEOUT_S = 5.0


def _short_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:200]


async def _probe_http(client: Any, url: str) -> dict[str, Any]:
    try:
        resp = await client.get(url)
    except Exception as exc:
        return {"status": "error", "url": url, "detail": _short_error(exc)}
    if resp.status_code >= 400:
        return {"status": "error", "url": url, "detail": f"HTTP {resp.status_code}"}
    return {"status": "ok", "url": url}


async def _probe_sparql(client: Any, base: str) -> dict[str, Any]:
    """Probe Oxigraph and count named graphs in the same round trip."""
    query = "SELECT (COUNT(DISTINCT ?g) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }"
    try:
        resp = await client.post(
            f"{base}/query",
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
        )
    except Exception as exc:
        return {"status": "error", "url": base, "detail": _short_error(exc)}
    if resp.status_code >= 400:
        return {"status": "error", "url": base, "detail": f"HTTP {resp.status_code}"}
    count: int | None = None
    try:
        bindings = resp.json()["results"]["bindings"]
        count = int(bindings[0]["n"]["value"]) if bindings else 0
    except (ValueError, KeyError, IndexError):
        count = None
    return {"status": "ok", "url": base, "namedGraphs": count}


async def _local_system_health() -> dict[str, Any]:
    """GetSystemHealth, answered from the local stack instead of AWS services.

    Every component is probed live; a failing one keeps its error text so the
    console can say *which* dependency is down rather than a bare "degraded".
    """
    import httpx

    components: list[dict[str, Any]] = []
    pointer: dict[str, Any] | None = None
    named_graphs: int | None = None

    runtime: Any = None
    try:
        runtime = _lifecycle_runtime()
        runtime.metadata.query("SELECT 1")
        components.append(
            {
                "name": "postgres",
                "label": "PostgreSQL（元数据 / 事实账本 / 指标库）",
                "status": "ok",
            }
        )
    except Exception as exc:
        components.append(
            {
                "name": "postgres",
                "label": "PostgreSQL（元数据 / 事实账本 / 指标库）",
                "status": "error",
                "detail": _short_error(exc),
            }
        )

    oxigraph = os.environ.get("COA_ONTOLOGY_OXIGRAPH_URL", "http://127.0.0.1:7878").rstrip("/")
    async with httpx.AsyncClient(timeout=_HEALTH_PROBE_TIMEOUT_S) as client:
        graph = await _probe_sparql(client, oxigraph)
        named_graphs = graph.pop("namedGraphs", None)
        components.append(
            {
                "name": "oxigraph",
                "label": "Oxigraph（RDF 图存储）",
                **graph,
            }
        )
        # Probe the endpoints the process was actually configured with.  The
        # container stack puts the engine on a service name, not 127.0.0.1;
        # hard-coding the host ports made a healthy engine look down.
        ontology_engine = os.environ.get(
            "ONTOLOGY_ENGINE_ENDPOINT", "http://127.0.0.1:8101"
        ).rstrip("/")
        context_manager = os.environ.get(
            "COA_CONTEXT_MANAGER_ENDPOINT", "http://127.0.0.1:8091"
        ).rstrip("/")
        components.append(
            {
                "name": "ontologyService",
                "label": "本体服务",
                **(await _probe_http(client, f"{ontology_engine}/health")),
            }
        )
        components.append(
            {
                "name": "contextManager",
                "label": "上下文服务",
                **(await _probe_http(client, f"{context_manager}/ping")),
            }
        )

    object_root = Path(
        os.environ.get("COA_LOCAL_OBJECT_ROOT")
        or (Path(tempfile.gettempdir()) / "coa-local-stack" / "objects")
    )
    components.append(
        {
            "name": "objectStore",
            "label": "对象存储（本地文件）",
            "status": "ok" if object_root.exists() else "error",
            "detail": None if object_root.exists() else "对象根目录不存在",
            "url": str(object_root),
        }
    )

    if runtime is not None:
        try:
            from platform_core import healthboard

            pointer = healthboard.pointer_status(runtime)
        except Exception as exc:
            pointer = {"ok": False, "status": "unreadable", "detail": _short_error(exc)}

    schema_version: dict[str, Any] | None = None
    if runtime is not None:
        try:
            from coa_control_plane.platform_db import SUPPORTED_SCHEMA_VERSION

            rows = runtime.metadata.query(
                "SELECT COALESCE(MAX(version), 0) AS v FROM platform.schema_version"
            )
            db_version = int(rows[0]["v"]) if rows else None
            schema_version = {
                "codeVersion": SUPPORTED_SCHEMA_VERSION,
                "dbVersion": db_version,
                "consistent": (
                    db_version == SUPPORTED_SCHEMA_VERSION if db_version is not None else None
                ),
                "source": "platform.schema_version MAX(version) vs the version this build ships",
            }
        except Exception as exc:
            # Health must stay answerable when the migration table is
            # unreadable; the page then shows the reason instead of a guess.
            schema_version = None
            print(f"[api] schema version probe failed: {_short_error(exc)}")

    status = "ok" if all(item["status"] == "ok" for item in components) else "degraded"
    return {
        "status": status,
        "components": components,
        "pointer": pointer,
        "namedGraphs": named_graphs,
        "schemaVersion": schema_version,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }


def _make_app() -> Any:
    from urllib.parse import unquote

    app = FastAPI(title="COA control-plane (local)")

    def _cors(response: Response, origin: str | None, requested_headers: str | None = None) -> Response:
        # Never reflect an arbitrary origin: with real bearer tokens a hostile
        # page must not be able to read responses cross-origin. Local browser
        # origins on any port are allowed; anything else gets no CORS headers.
        if origin and _origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            # Echo the preflight's requested headers: the Smithy client signs
            # requests (authorization, x-amz-date, x-amz-user-agent, ...), and a
            # fixed allow-list silently drops any header the SDK adds later.
            response.headers["Access-Control-Allow-Headers"] = (
                requested_headers
                or "Authorization, Content-Type, X-Amz-Date, X-Amz-Security-Token, X-Amz-User-Agent, X-Amz-Content-SHA256"
            )
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Max-Age"] = "600"
        return response

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def dispatch(request: Request, full_path: str) -> Response:
        origin = request.headers.get("origin")
        # Match on the *raw* request target: Starlette decodes ``%2F`` into a
        # literal slash, which would split a path-parameter such as an
        # ontology URI (``https%3A%2F%2Fw3id.org%2Ffsldm%2Fcodes``) across
        # segments and make the contract route unreachable. AWS API Gateway
        # keeps those escapes until the handler reads them, so match raw and
        # unquote per parameter below.
        raw_path = request.scope.get("raw_path")
        path = raw_path.decode("latin-1").split("?", 1)[0] if raw_path else "/" + full_path
        if request.method == "OPTIONS":
            return _cors(Response(status_code=204), origin, request.headers.get("access-control-request-headers"))

        # Explicit local development issuer (COA_LOCAL_DEV_AUTH=on only).
        # It mints signed tokens, it does not bypass validation: every other
        # route still goes through the authorizer below.
        if path == "/local/auth/config" and request.method == "GET":
            if not _DEV_AUTH_ENABLED:
                return _cors(JSONResponse({"enabled": False}, status_code=404), origin)
            return _cors(
                JSONResponse(
                    {
                        "enabled": True,
                        "issuer": _DEV_AUTH_ISSUER,
                        "users": sorted(_DEV_AUTH_USERS),
                    }
                ),
                origin,
            )
        if path == "/local/auth/jwks" and request.method == "GET":
            if not _DEV_AUTH_ENABLED:
                return _cors(JSONResponse({"error": "dev auth is disabled"}, status_code=404), origin)
            return _cors(JSONResponse(_DEV_AUTH_JWKS), origin)
        if path == "/local/auth/token" and request.method == "POST":
            if not _DEV_AUTH_ENABLED:
                return _cors(JSONResponse({"error": "dev auth is disabled"}, status_code=404), origin)
            try:
                payload = json.loads((await request.body()) or b"{}")
            except ValueError:
                return _cors(JSONResponse({"error": "body is not valid JSON"}, status_code=400), origin)
            email = str((payload or {}).get("email") or "").strip()
            if not email and len(_DEV_AUTH_USERS) == 1:
                email = next(iter(_DEV_AUTH_USERS))
            if email not in _DEV_AUTH_USERS:
                return _cors(
                    JSONResponse(
                        {
                            "error": "E_UNKNOWN_DEV_USER",
                            "message": f"{email!r} is not in COA_LOCAL_DEV_USERS",
                        },
                        status_code=403,
                    ),
                    origin,
                )
            return _cors(JSONResponse(_mint_dev_token(email)), origin)

        request_headers = {k.lower(): v for k, v in request.headers.items()}

        # Local-only fixture endpoint, explicitly outside the Smithy contract.
        # It writes a source, so it is authorized as one (manageSource).
        if path == "/local/seed-catalog" and request.method == "POST":
            try:
                body = json.loads((await request.body()) or b"{}")
            except ValueError:
                return _cors(JSONResponse({"error": "body is not valid JSON"}, status_code=400), origin)
            namespace_id = (body or {}).get("namespaceId")
            if not namespace_id:
                return _cors(JSONResponse({"error": "namespaceId is required"}, status_code=400), origin)
            auth_context, auth_error = _safe_authorize(
                "POST",
                "/namespaces/{namespaceId}/sources",
                {"namespaceId": namespace_id},
                request_headers,
            )
            if auth_error is not None:
                return _cors(auth_error, origin)
            item = _seed_demo_catalog(namespace_id, auth_context["email"])
            return _cors(JSONResponse({"seeded": True, "sourceId": item["sourceId"]}), origin)

        # Local-only object transport (S3 role). Not a business route: it serves
        # and accepts artifact bytes for presigned URLs minted by the local S3
        # provider, exactly like S3 does in AWS.
        if path.startswith("/_local/objects/"):
            from coa_local_providers.local_s3 import LocalS3, NoSuchKey

            rest = path[len("/_local/objects/") :]
            bucket, _, key = rest.partition("/")
            if not bucket or not key:
                return _cors(JSONResponse({"error": "bucket and key are required"}, status_code=400), origin)
            client = LocalS3()
            try:
                if request.method == "GET":
                    obj = client.get_object(Bucket=unquote(bucket), Key=unquote(key))
                    response = Response(content=obj["Body"].read(), media_type=obj["ContentType"])
                    if obj.get("ContentDisposition"):
                        response.headers["Content-Disposition"] = obj["ContentDisposition"]
                    return _cors(response, origin)
                if request.method in ("PUT", "POST"):
                    body = await request.body()
                    client.put_object(
                        Bucket=unquote(bucket),
                        Key=unquote(key),
                        Body=body,
                        ContentType=request.headers.get("content-type", "application/octet-stream"),
                    )
                    return _cors(Response(status_code=200), origin)
                if request.method == "DELETE":
                    client.delete_object(Bucket=unquote(bucket), Key=unquote(key))
                    return _cors(Response(status_code=204), origin)
            except NoSuchKey:
                return _cors(JSONResponse({"error": "not found"}, status_code=404), origin)
            return _cors(JSONResponse({"error": "method not allowed"}, status_code=405), origin)

        if path == "/health":
            return _cors(JSONResponse({"status": "ok", "provider": "postgres"}), origin)

        # GetSystemHealth is answered here, not forwarded: the AWS handler can
        # only report DynamoDB/Neptune/OpenSearch, which this stack does not use.
        # It is still authorized (the deployed authorizer protects it too).
        if path == "/system-health" and request.method == "GET":
            _ctx, auth_error = _safe_authorize(
                "GET", "/system-health", {}, request_headers
            )
            if auth_error is not None:
                return _cors(auth_error, origin)
            return _cors(JSONResponse(await _local_system_health()), origin)

        matched = _match(path)
        if matched is None:
            return _cors(
                JSONResponse({"error": f"No route for {request.method} {path}"}, status_code=404),
                origin,
            )
        template, path_params, module = matched
        decoded_params = {k: unquote(v) for k, v in path_params.items()}
        auth_context, auth_error = _safe_authorize(
            request.method, template, decoded_params, request_headers
        )
        if auth_error is not None:
            return _cors(auth_error, origin)
        actor = auth_context["email"]
        # Authorization first, id shape second. Flipping these two would make an
        # unauthenticated caller able to probe id validity (400 before 401).
        bad_namespace_id = _invalid_namespace_id(decoded_params)
        if bad_namespace_id is not None:
            print(f"[api] {request.method} {path} -> 400 E_NAMESPACE_ID_INVALID")
            return _cors(
                JSONResponse(
                    {
                        "error": "E_NAMESPACE_ID_INVALID",
                        "message": (
                            "namespaceId must be a UUID v4; "
                            f"got {bad_namespace_id!r} for {template}"
                        ),
                    },
                    status_code=400,
                ),
                origin,
            )
        if module == KERNEL:
            print(f"[api] {request.method} {path} -> kernel ({template}) as {actor}")
            return _cors(
                await _kernel_proxy(request, template, decoded_params, actor),
                origin,
            )
        handler = _load_handler(module)
        body = await request.body()
        event = {
            "resource": template,
            "path": path,
            "httpMethod": request.method,
            "headers": request_headers,
            "multiValueHeaders": {k: [v] for k, v in request.headers.items()},
            "queryStringParameters": dict(request.query_params) or None,
            "multiValueQueryStringParameters": {k: [v] for k, v in request.query_params.items()}
            or None,
            "pathParameters": decoded_params or None,
            "stageVariables": None,
            "requestContext": {
                "resourceId": "local",
                "resourcePath": template,
                "httpMethod": request.method,
                "path": "/prod" + path,
                "accountId": "000000000000",
                "requestId": str(uuid.uuid4()),
                "identity": {
                    "sourceIp": "127.0.0.1",
                    "userAgent": request.headers.get("user-agent", ""),
                },
                "authorizer": auth_context,
            },
            "body": body.decode("utf-8") if body else None,
            "isBase64Encoded": False,
        }
        print(f"[api] {request.method} {path} -> {module} ({template}) as {actor}")
        try:
            if module == DATA_LAYER:
                # The data-layer Lambda handler drives the ContextManagerPort with
                # ``asyncio.run`` per request, which cannot run inside our event
                # loop; a worker thread gives it a clean loop. It also keeps a
                # multi-second Tier-3 query from blocking every other route.
                import asyncio

                result = await asyncio.to_thread(handler, event, None)
            else:
                result = handler(event, None)
        except Exception as exc:  # surface the real failure in the terminal
            import traceback

            traceback.print_exc()
            return _cors(JSONResponse({"error": str(exc)}, status_code=500), origin)

        headers = {
            key: value
            for key, value in (result.get("headers") or {}).items()
            if key.lower() not in {"access-control-allow-origin"}
        }
        content = result.get("body") or ""
        return _cors(
            Response(
                content=content.encode("utf-8"),
                status_code=int(result.get("statusCode", 200)),
                headers=headers,
                media_type=headers.get("Content-Type") or headers.get("content-type"),
            ),
            origin,
        )

    return app


def main() -> None:
    _configure_environment()
    _install_pg_store()
    _install_local_import_jobs()
    _install_local_metadata_store()
    _install_local_catalog()
    _install_local_object_store()
    _install_local_idempotency()
    _install_fact_ledger()
    _install_dictionary_introspector()
    _install_document_index()

    from coa_common.logging import setup_logging

    setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

    # Fail fast: the in-process app never migrates, so a stale serve_local
    # would otherwise start and only fail on the first write to a new table.
    try:
        _assert_lifecycle_schema()
    except RuntimeError as exc:
        print(f"[api] refusing to start: {exc}", file=sys.stderr)
        raise SystemExit(1) from None

    _seed_roles()
    _init_auth()
    _apply_local_authz_extensions()
    _seed_dev_global_viewer()
    _write_snapshot()

    import uvicorn

    port = int(os.environ.get("COA_LOCAL_API_PORT", "8099"))
    # Bind all interfaces: the dev browser has been observed reaching 5173 but
    # not a loopback-only 8099 (port is forwarded, loopback is not shared).
    host = os.environ.get("COA_LOCAL_API_HOST", "0.0.0.0")
    print(f"[api] COA local control plane listening on http://{host}:{port}")
    print(f"[api] namespace/source/metric/ontology handlers -> PostgreSQL + Oxigraph")
    uvicorn.run(_make_app(), host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
