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
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

REPO = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
SNAPSHOT_PATH = TOOLS / "local-catalog.json"
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
        "COA_LOCAL_OBJECT_BASE": "http://127.0.0.1:8099/_local/objects",
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


def _seed_demo_catalog(namespace_id: str) -> dict[str, Any]:
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
        "createdBy": LOCAL_EMAIL,
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
GRANTS = "coa_control_plane.grants.grants_handler"
SOURCES = "coa_sources.api.sources_handler"
METRICS = "coa_metrics.api.metric_api_handler"
ONTOLOGY = "coa_ontology.api_proxy_handler"
DATA_LAYER = "coa_data_layer.handler"

ROUTES: list[tuple[str, str]] = [
    ("/namespaces", NAMESPACE),
    ("/namespaces/{namespaceId}", NAMESPACE),
    ("/namespaces/{namespaceId}/status", NAMESPACE),
    ("/namespaces/{namespaceId}/roles", ROLES),
    ("/namespaces/{namespaceId}/roles/{roleId}", ROLES),
    ("/namespaces/{namespaceId}/grants", GRANTS),
    ("/namespaces/{namespaceId}/grants/{grantId}", GRANTS),
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
    ("/namespaces/{namespaceId}/metrics", METRICS),
    ("/namespaces/{namespaceId}/metrics/{name}", METRICS),
    ("/namespaces/{namespaceId}/metrics/validate", METRICS),
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
    ("/namespaces/{namespaceId}/graph/ontology-overview", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/class", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/object-property", ONTOLOGY),
    ("/namespaces/{namespaceId}/graph/datatype-property", ONTOLOGY),
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


# ---------------------------------------------------------------------------
# HTTP bridge
# ---------------------------------------------------------------------------


def _make_app() -> Any:
    from urllib.parse import unquote

    app = FastAPI(title="COA control-plane (local)")

    def _cors(response: Response, origin: str | None, requested_headers: str | None = None) -> Response:
        if origin:
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

        # Local-only fixture endpoint, explicitly outside the Smithy contract.
        if path == "/local/seed-catalog" and request.method == "POST":
            body = json.loads((await request.body()) or b"{}")
            namespace_id = body.get("namespaceId")
            if not namespace_id:
                return _cors(JSONResponse({"error": "namespaceId is required"}, status_code=400), origin)
            item = _seed_demo_catalog(namespace_id)
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

        matched = _match(path)
        if matched is None:
            return _cors(
                JSONResponse({"error": f"No route for {request.method} {path}"}, status_code=404),
                origin,
            )
        template, path_params, module = matched
        handler = _load_handler(module)
        body = await request.body()
        event = {
            "resource": template,
            "path": path,
            "httpMethod": request.method,
            "headers": {k.lower(): v for k, v in request.headers.items()},
            "multiValueHeaders": {k: [v] for k, v in request.headers.items()},
            "queryStringParameters": dict(request.query_params) or None,
            "multiValueQueryStringParameters": {k: [v] for k, v in request.query_params.items()}
            or None,
            "pathParameters": {k: unquote(v) for k, v in path_params.items()} or None,
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
                "authorizer": {
                    "principalId": LOCAL_USER,
                    "userId": LOCAL_USER,
                    "email": LOCAL_EMAIL,
                    "globalRoles": LOCAL_ROLES,
                    "groups": "",
                },
            },
            "body": body.decode("utf-8") if body else None,
            "isBase64Encoded": False,
        }
        print(f"[api] {request.method} {path} -> {module} ({template})")
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
    _install_local_metadata_store()
    _install_local_catalog()
    _install_local_object_store()
    _install_local_idempotency()

    from coa_common.logging import setup_logging

    setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

    _seed_roles()
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
