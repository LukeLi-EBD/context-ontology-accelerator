"""The configuration catalog: one key per interface, one entry per provider.

Source of truth for the config matrix (plan §2 D5 / §7). Every interface owns
exactly one key. A provider is listed even when it is not wired yet, so an
operator sees "known but unavailable" instead of "unknown value"; the
``implemented`` flag and ``notes`` say why.

Provider names are lowercase and stable; they are configuration API.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from coa_ports import (
    ChangeFeedPort,
    ComputePort,
    ConfigProvider,
    ContextManagerPort,
    EventBusPort,
    GraphAdminPort,
    IdentityPort,
    MetadataStorePort,
    MetricIndexPort,
    ObjectStorePort,
    SchedulerPort,
    SchemaProvider,
    SecretProvider,
    ServiceRegistryPort,
    TaskQueuePort,
    WarehouseAdminPort,
    WorkflowPort,
)

from .errors import ProviderNotAvailableError
from .settings import Settings

Factory = Callable[[Settings], Any]


def _pending(reason: str) -> Factory:
    """A provider whose implementation is not wired yet.

    Calling it raises instead of returning a stand-in: a placeholder object
    would be a silent fallback.
    """

    def _raise(_settings: Settings) -> Any:
        raise ProviderNotAvailableError("provider is registered but not implemented", reason=reason)

    return _raise


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    factory: Factory
    implemented: bool
    notes: str = ""


@dataclass(frozen=True)
class InterfaceSpec:
    """One interface: its config key, owning context, and providers.

    Attributes:
        name: Interface name used in code and in error messages.
        key: The single configuration key selecting the provider.
        context: Owning bounded context (plan §11.1).
        protocol: ``coa_ports`` protocol for a structural check, when one exists.
        required_methods: Method names checked when no protocol exists.
        expects_async: ``True``/``False`` enforces the call style of
            ``required_methods``; ``None`` skips the check.
        port_location: Module that owns the Protocol when it lives outside
            ``coa_ports`` (plan §7.2 exceptions). Empty means ``coa_ports``.
        providers: Provider name -> spec. Insertion order is the documented order.
    """

    name: str
    key: str
    context: str
    providers: Mapping[str, ProviderSpec]
    protocol: type | None = None
    required_methods: tuple[str, ...] = ()
    expects_async: bool | None = None
    port_location: str = ""
    notes: str = ""

    @property
    def allowed(self) -> tuple[str, ...]:
        return tuple(self.providers)


# ── factories over existing local implementations ───────────────────────────


def _oxigraph(settings: Settings) -> Any:
    from coa_local_providers.graph_oxigraph import OxigraphGraphClient

    return OxigraphGraphClient(
        settings.require("COA_GRAPH_OXIGRAPH_URL", interface="GraphClient"),
        timeout_ms=settings.get_int("COA_GRAPH_OXIGRAPH_TIMEOUT_MS", default=30000, interface="GraphClient"),
        max_rows=settings.get_int("COA_GRAPH_OXIGRAPH_MAX_ROWS", default=10000, interface="GraphClient"),
    )


def _fuseki(settings: Settings) -> Any:
    from coa_local_providers.graph_fuseki import FusekiGraphClient

    server = settings.require("COA_GRAPH_FUSEKI_SERVER_URL", interface="GraphClient")
    dataset = settings.get("COA_GRAPH_FUSEKI_DATASET") or "ds"
    return FusekiGraphClient(server, dataset=dataset)


def _pgvector(settings: Settings) -> Any:
    from coa_local_providers.vector_pg import PgVectorClient

    return PgVectorClient(
        settings.require("COA_VECTOR_PG_DSN", interface="VectorClient"),
        model=settings.get("COA_VECTOR_MODEL") or "BAAI/bge-m3",
        dimensions=settings.get_int("COA_VECTOR_DIMENSIONS", default=1024, interface="VectorClient"),
    )


def _graph_admin(settings: Settings) -> Any:
    from coa_local_providers.graph_admin import OxigraphGraphAdmin

    return OxigraphGraphAdmin(
        settings.require("COA_GRAPH_OXIGRAPH_URL", interface="GraphAdminPort"),
        timeout_ms=settings.get_int("COA_GRAPH_OXIGRAPH_TIMEOUT_MS", default=30000, interface="GraphAdminPort"),
    )


def _warehouse_admin(settings: Settings) -> Any:
    from coa_local_providers.warehouse_admin import PgWarehouseAdmin

    dsn = settings.get("COA_WAREHOUSE_ADMIN_PG_DSN") or settings.require(
        "COA_METADATA_PG_DSN", interface="WarehouseAdminPort"
    )
    return PgWarehouseAdmin(dsn)


def _metric_index_pg(settings: Settings) -> Any:
    from coa_local_providers.metric_index_pg import PgMetricIndex

    dsn = settings.get("COA_METRIC_INDEX_PG_DSN") or settings.require(
        "COA_METADATA_PG_DSN", interface="MetricIndexPort"
    )
    return PgMetricIndex(dsn)


def _metric_graph_neptune(_settings: Settings) -> Any:
    from coa_local_providers.metric_graph import NeptuneSparqlTransport

    return NeptuneSparqlTransport()


def _metric_graph_oxigraph(settings: Settings) -> Any:
    from coa_local_providers.metric_graph import oxigraph_transport

    base = (
        settings.get("COA_METRIC_GRAPH_URI_BASE")
        or settings.get("NDB_GRAPH_URI_BASE")
        or "https://ontology-workbench.local"
    )
    return oxigraph_transport(
        settings.require("COA_GRAPH_OXIGRAPH_URL", interface="MetricGraph"),
        graph_base=base,
        timeout_ms=settings.get_int("COA_GRAPH_OXIGRAPH_TIMEOUT_MS", default=30000, interface="MetricGraph"),
        max_rows=settings.get_int("COA_GRAPH_OXIGRAPH_MAX_ROWS", default=10000, interface="MetricGraph"),
    )


def _postgres_executor(settings: Settings) -> Any:
    from coa_local_providers.query_pg import PostgresQueryExecutor

    return PostgresQueryExecutor(
        settings.require("COA_EXECUTOR_POSTGRES_DSN", interface="QueryExecutor"),
        max_rows=settings.get_int("COA_EXECUTOR_MAX_ROWS", default=1000, interface="QueryExecutor"),
    )


def _llm_shell(settings: Settings) -> Any:
    from coa_local_providers.shells.llm import PlatformLLMShell
    from platform_core.adapters.llm_openai import LlmClient
    from platform_core.config import LlmConfig
    from platform_core.ports import EnvSecretProvider

    config = LlmConfig(
        provider=settings.get("COA_LLM_PROVIDER") or "openai-compatible",
        base_url=settings.get("COA_LLM_BASE_URL") or "",
        model=settings.get("COA_LLM_MODEL") or "",
        timeout_ms=settings.get_int("COA_LLM_TIMEOUT_MS", default=30000, interface="LLMClient"),
        api_key_env=settings.get("COA_LLM_API_KEY_ENV") or "LLM_API_KEY",
    )
    return PlatformLLMShell(
        LlmClient(config, EnvSecretProvider()),
        timeout_s=settings.get_float("COA_LLM_TIMEOUT_S", default=60.0, interface="LLMClient"),
    )


def _bge_local(settings: Settings) -> Any:
    from coa_local_providers.embedding_bge import BgeLocalEmbedding

    return BgeLocalEmbedding(
        settings.get("COA_EMBEDDING_BGE_ENDPOINT") or "http://embedding:80/v1",
        model=settings.get("COA_EMBEDDING_BGE_MODEL") or "BAAI/bge-m3",
        dimensions=settings.get_int("COA_EMBEDDING_BGE_DIMENSIONS", default=1024, interface="Embedding"),
    )


def _external_http(settings: Settings) -> Any:
    from coa_local_providers.embedding_http import ExternalHttpEmbedding

    return ExternalHttpEmbedding(
        endpoint=settings.require("COA_EMBEDDING_HTTP_ENDPOINT", interface="Embedding"),
        model=settings.require("COA_EMBEDDING_HTTP_MODEL", interface="Embedding"),
        api_key=settings.require("COA_EMBEDDING_HTTP_API_KEY", interface="Embedding"),
        dimensions=settings.get_int("COA_EMBEDDING_HTTP_DIMENSIONS", default=1024, interface="Embedding"),
    )


def _metadata_pg(settings: Settings) -> Any:
    from platform_core.adapters.metadata_pg import MetadataPg

    store = MetadataPg(settings.require("COA_METADATA_PG_DSN", interface="MetadataStorePort"))
    store.open(retry_seconds=settings.get_float("COA_METADATA_PG_OPEN_TIMEOUT_S", default=10.0))
    return store


def _metadata_store(settings: Settings) -> Any:
    """Wrap ``MetadataPg`` so the interface has ``probe`` and COA errors."""
    from coa_local_providers.shells import MetadataStoreShell

    return MetadataStoreShell(_metadata_pg(settings), provider="postgres")


def _env_secrets(_settings: Settings) -> Any:
    from coa_local_providers.shells import EnvSecretShell
    from platform_core.ports import EnvSecretProvider

    return EnvSecretShell(EnvSecretProvider(), provider="env")


def _env_config(settings: Settings) -> Any:
    from .env_config import EnvironmentConfigProvider

    return EnvironmentConfigProvider(settings.snapshot())


def _sync_client_config() -> Any:
    """The customer-path botocore policy (fail-fast, <=1 retry) the services used."""
    from coa_common import sync_boto_config

    return sync_boto_config()


def _ssm_config(settings: Settings) -> Any:
    from coa_local_providers.aws import SsmConfig

    return SsmConfig(
        region=settings.get("AWS_REGION") or settings.get("AWS_DEFAULT_REGION"),
        client_config=_sync_client_config(),
    )


def _secretsmanager(settings: Settings) -> Any:
    from coa_local_providers.aws import SecretsManagerSecret

    return SecretsManagerSecret(
        region=settings.get("AWS_REGION") or settings.get("AWS_DEFAULT_REGION"),
        client_config=_sync_client_config(),
    )


def _s3_object_store(settings: Settings) -> Any:
    from coa_local_providers.aws import S3ObjectStore

    return S3ObjectStore(
        region=settings.get("AWS_REGION") or settings.get("AWS_DEFAULT_REGION"),
        probe_bucket=settings.get("COA_OBJECT_STORE_PROBE_BUCKET") or "",
        client_config=_sync_client_config(),
    )


# ── the catalog ─────────────────────────────────────────────────────────────

_SHELL = "薄壳未落地（阶段 1 第 3 步）"
_AWS = "AWS provider 未接入（阶段 7）"


def _providers(*specs: ProviderSpec) -> Mapping[str, ProviderSpec]:
    return {spec.name: spec for spec in specs}


def _done(name: str, factory: Factory, notes: str = "") -> ProviderSpec:
    return ProviderSpec(name=name, factory=factory, implemented=True, notes=notes)


def _todo(name: str, reason: str = _SHELL) -> ProviderSpec:
    return ProviderSpec(name=name, factory=_pending(reason), implemented=False, notes=reason)


SPECS: tuple[InterfaceSpec, ...] = (
    # ── 13 new ports (plan §7.2) ──
    InterfaceSpec(
        name="ContextManagerPort",
        key="COA_PROVIDER_CONTEXT_MANAGER",
        context="问答与检索",
        protocol=ContextManagerPort,
        providers=_providers(_todo("local-http"), _todo("agentcore", _AWS)),
        notes="替代 AgentCore Runtime 调用",
    ),
    InterfaceSpec(
        name="SchemaProvider",
        key="COA_PROVIDER_SCHEMA",
        context="本体",
        protocol=SchemaProvider,
        providers=_providers(_todo("local-http"), _todo("lambda", _AWS)),
        notes="替代 Glue / DescribeSchema Lambda",
    ),
    InterfaceSpec(
        name="ControlPlaneStore",
        key="COA_PROVIDER_CONTROL_PLANE_STORE",
        context="控制面",
        required_methods=("get", "put", "query", "update", "delete"),
        expects_async=False,
        port_location="coa_control_plane.ports",
        providers=_providers(_todo("postgres"), _todo("dynamodb", _AWS)),
        notes="同步 DynamoDB item 语义，镜像 coa_common.dao.DatastoreDAO；阶段 7 实现",
    ),
    InterfaceSpec(
        name="ConfigProvider",
        key="COA_PROVIDER_CONFIG",
        context="全部上下文",
        protocol=ConfigProvider,
        providers=_providers(_done("env", _env_config, "进程环境变量"), _done("ssm", _ssm_config, "AWS SSM")),
    ),
    InterfaceSpec(
        name="TaskQueuePort",
        key="COA_PROVIDER_TASK_QUEUE",
        context="编排",
        protocol=TaskQueuePort,
        providers=_providers(_todo("sqlite"), _todo("sqs", _AWS)),
        notes="替代 SQS",
    ),
    InterfaceSpec(
        name="WorkflowPort",
        key="COA_PROVIDER_WORKFLOW",
        context="编排",
        protocol=WorkflowPort,
        providers=_providers(_todo("local"), _todo("stepfunctions", _AWS)),
        notes="替代 StepFunctions",
    ),
    InterfaceSpec(
        name="EventBusPort",
        key="COA_PROVIDER_EVENT_BUS",
        context="编排",
        protocol=EventBusPort,
        providers=_providers(_todo("in-process"), _todo("eventbridge", _AWS)),
        notes="替代 EventBridge",
    ),
    InterfaceSpec(
        name="SchedulerPort",
        key="COA_PROVIDER_SCHEDULER",
        context="编排",
        protocol=SchedulerPort,
        providers=_providers(_todo("local"), _todo("eventbridge-scheduler", _AWS)),
    ),
    InterfaceSpec(
        name="ComputePort",
        key="COA_PROVIDER_COMPUTE",
        context="编排",
        protocol=ComputePort,
        providers=_providers(_todo("local"), _todo("ecs", _AWS)),
        notes="替代 ECS run-task",
    ),
    InterfaceSpec(
        name="ServiceRegistryPort",
        key="COA_PROVIDER_SERVICE_REGISTRY",
        context="编排",
        protocol=ServiceRegistryPort,
        providers=_providers(_todo("compose"), _todo("cloudmap", _AWS)),
        notes="替代 Cloud Map；compose 走 DNS 别名",
    ),
    InterfaceSpec(
        name="IdentityPort",
        key="COA_PROVIDER_IDENTITY",
        context="控制面",
        protocol=IdentityPort,
        providers=_providers(_todo("local"), _todo("cognito", _AWS)),
    ),
    InterfaceSpec(
        name="ChangeFeedPort",
        key="COA_PROVIDER_CHANGE_FEED",
        context="控制面 / 知识图",
        protocol=ChangeFeedPort,
        providers=_providers(_todo("postgres"), _todo("dynamodb-streams", _AWS)),
        notes="替代 DynamoDB Streams",
    ),
    InterfaceSpec(
        name="OcrPort",
        key="COA_PROVIDER_OCR",
        context="文档摄入",
        required_methods=("extract", "health_check"),
        expects_async=True,
        port_location="coa_serve.ports",
        providers=_providers(_todo("local"), _todo("textract", _AWS)),
    ),
    # ── 10 reused interfaces (plan §7.1) ──
    InterfaceSpec(
        name="GraphClient",
        key="COA_PROVIDER_GRAPH",
        context="知识图",
        required_methods=("query", "ask"),
        expects_async=True,
        providers=_providers(_done("oxigraph", _oxigraph), _done("fuseki", _fuseki), _todo("neptune", _AWS)),
        notes="COA 异步 GraphClient；平台同步适配器是另一接口 GraphStorePort",
    ),
    InterfaceSpec(
        name="GraphAdminPort",
        key="COA_PROVIDER_GRAPH_ADMIN",
        context="数据源接入 / 知识图",
        protocol=GraphAdminPort,
        expects_async=False,
        providers=_providers(_done("oxigraph", _graph_admin), _todo("neptune", _AWS)),
        notes="控制面：引擎探活、集群清单、标签；GraphClient 不承担这些，AWS 侧登记未接线",
    ),
    InterfaceSpec(
        name="VectorClient",
        key="COA_PROVIDER_VECTOR",
        context="问答与检索",
        required_methods=("search",),
        expects_async=True,
        providers=_providers(_done("platform-pgvector", _pgvector), _todo("aoss", _AWS)),
    ),
    InterfaceSpec(
        name="MetricIndexPort",
        key="COA_PROVIDER_METRIC_INDEX",
        context="问答与检索 / 控制面",
        protocol=MetricIndexPort,
        expects_async=True,
        providers=_providers(
            _done("platform-pg", _metric_index_pg, "直接检索 platform.metric_definition（单租户，检索只接此实现）"),
            _todo("aoss", _AWS),
        ),
        notes="替换 metric-service 的 OpenSearch 指标索引；不复用 VectorClient（后者返回文档分块 VectorHit）",
    ),
    InterfaceSpec(
        name="MetricGraph",
        key="COA_PROVIDER_METRIC_GRAPH",
        context="指标 / 知识图",
        required_methods=("query", "update"),
        expects_async=False,
        providers=_providers(
            _done(
                "neptune",
                _metric_graph_neptune,
                "沿用 metric-service 现有 SigV4 传输；AWS 路径未在本机验证",
            ),
            _done("oxigraph", _metric_graph_oxigraph),
        ),
        notes=(
            "指标图同步 SPARQL 传输，返回 Neptune 结果形状；"
            "不复用 GraphStorePort（后者把 binding 拍平成字符串，丢失 term 类型）"
        ),
    ),
    InterfaceSpec(
        name="LLMClient",
        key="COA_PROVIDER_LLM",
        context="问答与检索",
        # ``converse_stream`` is an async generator (not a coroutine function),
        # so it cannot go through the ``expects_async`` check; the shell still
        # exposes it and raises ``PortError(unsupported)`` on use.
        required_methods=("converse", "health_check"),
        expects_async=True,
        providers=_providers(
            _done("openai-compatible", _llm_shell, "同步 complete_json 的异步薄壳；流式与 embed 显式 unsupported"),
            _todo("llama-cpp", "实现位于 coa-gateway 验证跑道，未迁入"),
            _todo("bedrock", _AWS),
        ),
        notes="converse/health_check 可包；converse_stream/embed 抛 PortError(unsupported)；embed 归 EmbeddingPort",
    ),
    InterfaceSpec(
        name="QueryExecutor",
        key="COA_PROVIDER_QUERY_EXECUTOR",
        context="问答与检索 / 数据源接入",
        required_methods=("execute",),
        expects_async=True,
        providers=_providers(_done("postgres", _postgres_executor), _todo("athena", _AWS)),
    ),
    InterfaceSpec(
        name="WarehouseAdminPort",
        key="COA_PROVIDER_WAREHOUSE_ADMIN",
        context="数据源接入 / 控制面",
        protocol=WarehouseAdminPort,
        expects_async=False,
        providers=_providers(_done("postgres", _warehouse_admin), _todo("athena", _AWS)),
        notes="workgroup/catalog 本地为 no-op，run_query 只读；AWS 侧登记未接线",
    ),
    InterfaceSpec(
        name="GraphStorePort",
        key="COA_PROVIDER_GRAPH_STORE",
        context="本体 / 知识图",
        required_methods=("query", "update", "clear_graph"),
        expects_async=False,
        providers=_providers(_todo("oxigraph"), _todo("fuseki"), _todo("neptune", _AWS)),
        notes="平台同步 GraphStore 形状，供本体写 schema 图",
    ),
    InterfaceSpec(
        name="ObjectStorePort",
        key="COA_PROVIDER_OBJECT_STORE",
        context="文档摄入 / 数据源接入",
        protocol=ObjectStorePort,
        providers=_providers(_todo("fs"), _todo("pg"), _done("s3", _s3_object_store, "AWS S3")),
    ),
    InterfaceSpec(
        name="MetadataStorePort",
        key="COA_PROVIDER_METADATA_STORE",
        context="本体 / 控制面",
        protocol=MetadataStorePort,
        providers=_providers(_done("postgres", _metadata_store), _todo("dynamodb", _AWS)),
        notes="薄壳已落地：MetadataPg 的 list[dict] 转 tuple[Mapping]，补 probe（S9）",
    ),
    InterfaceSpec(
        name="SecretProvider",
        key="COA_PROVIDER_SECRETS",
        context="全部上下文",
        protocol=SecretProvider,
        providers=_providers(_done("env", _env_secrets), _done("secretsmanager", _secretsmanager, "AWS Secrets Manager")),
    ),
    InterfaceSpec(
        name="DataSourceLookup",
        key="COA_PROVIDER_DATA_SOURCE_LOOKUP",
        context="数据源接入",
        required_methods=("lookup",),
        expects_async=True,
        providers=_providers(_todo("json-snapshot"), _todo("postgres"), _todo("smus", _AWS)),
    ),
    InterfaceSpec(
        name="OntologyLookup",
        key="COA_PROVIDER_ONTOLOGY_LOOKUP",
        context="本体",
        required_methods=("lookup",),
        expects_async=True,
        providers=_providers(_todo("graph"), _todo("neptune", _AWS)),
    ),
    # ── extra infrastructure interface used by every retrieval path ──
    InterfaceSpec(
        name="Embedding",
        key="COA_PROVIDER_EMBEDDING",
        context="问答与检索 / 文档摄入",
        required_methods=("embed",),
        expects_async=True,
        providers=_providers(
            _done("bge-local", _bge_local),
            _done("external-http", _external_http),
            _todo("bedrock", _AWS),
        ),
    ),
)


def catalog() -> Mapping[str, InterfaceSpec]:
    """Interface name -> spec. Fails loudly if two interfaces share a key."""
    specs: dict[str, InterfaceSpec] = {}
    keys: dict[str, str] = {}
    for spec in SPECS:
        if spec.name in specs:
            raise ValueError(f"duplicate interface {spec.name}")
        if spec.key in keys:
            raise ValueError(f"interface {spec.name} reuses key {spec.key} of {keys[spec.key]}")
        specs[spec.name] = spec
        keys[spec.key] = spec.name
    return specs


__all__ = ["InterfaceSpec", "ProviderSpec", "SPECS", "catalog"]
