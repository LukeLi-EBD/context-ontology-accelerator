"""Registry behaviour: the four refusals, and the happy path against real adapters.

The happy-path cases import the actual local implementation, not a stub, so a
rename in ``coa_local_providers`` or ``platform_core`` breaks this test instead
of silently falling back.
"""

from __future__ import annotations

import pytest

from coa_runtime.catalog import InterfaceSpec, ProviderSpec, catalog
from coa_runtime.contexts import CONTEXT_INTERFACES, assemble
from coa_runtime.errors import (
    MissingConfigurationError,
    ProviderMismatchError,
    ProviderNotAvailableError,
    ResolutionErrors,
    UnknownInterfaceError,
    UnknownProviderError,
)
from coa_runtime.registry import NOT_AVAILABLE, OK, ProviderRegistry, default_registry
from coa_runtime.settings import Settings

REGISTRY = default_registry()


def test_catalog_has_one_key_per_interface() -> None:
    specs = catalog()
    keys = [spec.key for spec in specs.values()]
    assert len(keys) == len(set(keys))
    assert all(key.startswith("COA_PROVIDER_") for key in keys)


def test_catalog_covers_all_13_new_ports() -> None:
    names = set(catalog())
    expected = {
        "ContextManagerPort",
        "SchemaProvider",
        "ControlPlaneStore",
        "ConfigProvider",
        "TaskQueuePort",
        "WorkflowPort",
        "EventBusPort",
        "SchedulerPort",
        "ComputePort",
        "ServiceRegistryPort",
        "IdentityPort",
        "ChangeFeedPort",
        "OcrPort",
    }
    assert expected <= names


def test_catalog_covers_all_10_reused_interfaces() -> None:
    names = set(catalog())
    expected = {
        "GraphClient",
        "VectorClient",
        "LLMClient",
        "QueryExecutor",
        "GraphStorePort",
        "ObjectStorePort",
        "MetadataStorePort",
        "SecretProvider",
        "DataSourceLookup",
        "OntologyLookup",
    }
    assert expected <= names


def test_missing_key_is_refused() -> None:
    with pytest.raises(MissingConfigurationError) as excinfo:
        REGISTRY.resolve("GraphClient", Settings({}))
    assert excinfo.value.key == "COA_PROVIDER_GRAPH"
    assert "oxigraph" in excinfo.value.allowed


def test_empty_value_is_refused_like_a_missing_key() -> None:
    with pytest.raises(MissingConfigurationError):
        REGISTRY.resolve("GraphClient", Settings({"COA_PROVIDER_GRAPH": "   "}))


def test_unknown_value_is_refused_and_lists_allowed() -> None:
    with pytest.raises(UnknownProviderError) as excinfo:
        REGISTRY.resolve("GraphClient", Settings({"COA_PROVIDER_GRAPH": "neo4j"}))
    assert excinfo.value.value == "neo4j"
    assert set(excinfo.value.allowed) == {"oxigraph", "fuseki", "neptune"}


def test_registered_but_unwired_provider_is_refused_with_reason() -> None:
    with pytest.raises(ProviderNotAvailableError) as excinfo:
        REGISTRY.resolve("GraphClient", Settings({"COA_PROVIDER_GRAPH": "neptune"}))
    assert excinfo.value.reason
    assert "AWS" in excinfo.value.reason


def test_value_is_case_and_space_insensitive() -> None:
    status = REGISTRY.status("GraphClient", Settings({"COA_PROVIDER_GRAPH": "  Oxigraph "}))
    assert status.status == OK


def test_unknown_interface_is_refused() -> None:
    with pytest.raises(UnknownInterfaceError):
        REGISTRY.resolve("NopePort", Settings({}))


def test_mismatched_shape_is_refused_async_expected() -> None:
    class SyncGraph:
        def query(self, sparql: str) -> list[dict]:  # sync on purpose
            return []

        def ask(self, sparql: str) -> bool:
            return True

    spec = InterfaceSpec(
        name="GraphClient",
        key="COA_PROVIDER_GRAPH",
        context="知识图",
        required_methods=("query", "ask"),
        expects_async=True,
        providers={"fake": ProviderSpec("fake", lambda _s: SyncGraph(), True)},
    )
    registry = ProviderRegistry({spec.name: spec})
    with pytest.raises(ProviderMismatchError) as excinfo:
        registry.resolve("GraphClient", Settings({"COA_PROVIDER_GRAPH": "fake"}))
    assert "must be async" in excinfo.value.reason


def test_mismatched_shape_is_refused_missing_method() -> None:
    class HalfGraph:
        async def query(self, sparql: str) -> list[dict]:
            return []

    spec = InterfaceSpec(
        name="GraphClient",
        key="COA_PROVIDER_GRAPH",
        context="知识图",
        required_methods=("query", "ask"),
        expects_async=True,
        providers={"fake": ProviderSpec("fake", lambda _s: HalfGraph(), True)},
    )
    with pytest.raises(ProviderMismatchError) as excinfo:
        ProviderRegistry({"GraphClient": spec}).resolve(
            "GraphClient", Settings({"COA_PROVIDER_GRAPH": "fake"})
        )
    assert "missing callable method 'ask'" in excinfo.value.reason


def test_protocol_check_rejects_wrong_shape() -> None:
    from coa_ports import ObjectStorePort

    class NotAStore:
        pass

    spec = InterfaceSpec(
        name="ObjectStorePort",
        key="COA_PROVIDER_OBJECT_STORE",
        context="文档摄入",
        protocol=ObjectStorePort,
        providers={"fake": ProviderSpec("fake", lambda _s: NotAStore(), True)},
    )
    with pytest.raises(ProviderMismatchError) as excinfo:
        ProviderRegistry({"ObjectStorePort": spec}).resolve(
            "ObjectStorePort", Settings({"COA_PROVIDER_OBJECT_STORE": "fake"})
        )
    assert "not an instance of ObjectStorePort" in excinfo.value.reason


def test_factory_failure_is_reported_as_mismatch() -> None:
    def boom(_settings: Settings):
        raise RuntimeError("port 7878 refused")

    spec = InterfaceSpec(
        name="GraphClient",
        key="COA_PROVIDER_GRAPH",
        context="知识图",
        required_methods=("query",),
        providers={"fake": ProviderSpec("fake", boom, True)},
    )
    with pytest.raises(ProviderMismatchError) as excinfo:
        ProviderRegistry({"GraphClient": spec}).resolve(
            "GraphClient", Settings({"COA_PROVIDER_GRAPH": "fake"})
        )
    assert "7878 refused" in excinfo.value.reason


def test_factory_missing_sub_key_stays_a_config_error() -> None:
    def needs_key(settings: Settings):
        settings.require("COA_GRAPH_OXIGRAPH_URL", interface="GraphClient")
        raise AssertionError("unreachable")

    spec = InterfaceSpec(
        name="GraphClient",
        key="COA_PROVIDER_GRAPH",
        context="知识图",
        required_methods=("query",),
        providers={"fake": ProviderSpec("fake", needs_key, True)},
    )
    with pytest.raises(MissingConfigurationError) as excinfo:
        ProviderRegistry({"GraphClient": spec}).resolve(
            "GraphClient", Settings({"COA_PROVIDER_GRAPH": "fake"})
        )
    assert excinfo.value.key == "COA_GRAPH_OXIGRAPH_URL"


def test_real_oxigraph_provider_satisfies_the_interface() -> None:
    pytest.importorskip(
        "rdflib",
        reason="rdflib 不在本机 venv；同一构造已在 coa-gateway-verify 容器实跑通过",
    )
    settings = Settings({"COA_PROVIDER_GRAPH": "oxigraph", "COA_GRAPH_OXIGRAPH_URL": "http://127.0.0.1:7878"})
    resolution = REGISTRY.resolve("GraphClient", settings)
    assert resolution.provider == "oxigraph"
    assert resolution.context == "知识图"
    from coa_local_providers.graph_oxigraph import OxigraphGraphClient

    assert isinstance(resolution.instance, OxigraphGraphClient)


def test_real_env_secret_provider_matches_the_coa_port() -> None:
    resolution = REGISTRY.resolve("SecretProvider", Settings({"COA_PROVIDER_SECRETS": "env"}))
    from coa_ports import SecretProvider

    assert isinstance(resolution.instance, SecretProvider)


def test_real_env_config_provider_matches_the_coa_port() -> None:
    settings = Settings({"COA_PROVIDER_CONFIG": "env", "COA_SAMPLE": "1"})
    resolution = REGISTRY.resolve("ConfigProvider", settings)
    from coa_ports import ConfigProvider

    assert isinstance(resolution.instance, ConfigProvider)
    assert resolution.instance.get("COA_SAMPLE") == "1"
    assert resolution.instance.get("COA_ABSENT") is None


def test_matrix_lists_every_interface_without_constructing() -> None:
    rows = REGISTRY.matrix(Settings({}))
    assert len(rows) == len(catalog())
    assert all(row.status == "missing" for row in rows)


def test_matrix_marks_unwired_provider_as_not_available() -> None:
    rows = REGISTRY.matrix(Settings({"COA_PROVIDER_GRAPH": "neptune"}))
    graph = next(row for row in rows if row.interface == "GraphClient")
    assert graph.status == NOT_AVAILABLE
    assert graph.provider == "neptune"


def test_resolve_many_reports_every_failure_at_once() -> None:
    with pytest.raises(ResolutionErrors) as excinfo:
        REGISTRY.resolve_many(Settings({}), ("GraphClient", "VectorClient"))
    assert {error.interface for error in excinfo.value.errors} == {"GraphClient", "VectorClient"}


def test_resolve_all_fails_because_most_providers_are_unwired() -> None:
    with pytest.raises(ResolutionErrors) as excinfo:
        REGISTRY.resolve_all(Settings({}))
    assert len(excinfo.value.errors) == len(catalog())


def test_implemented_providers_are_the_ones_with_local_code() -> None:
    implemented = {
        spec.name: sorted(name for name, provider in spec.providers.items() if provider.implemented)
        for spec in catalog().values()
        if any(provider.implemented for provider in spec.providers.values())
    }
    assert implemented == {
        "ConfigProvider": ["env", "ssm"],
        "ContextManagerPort": ["local-http"],
        "DataSourceLookup": ["json-snapshot"],
        "Embedding": ["bge-local", "external-http"],
        "GraphAdminPort": ["oxigraph"],
        "GraphClient": ["fuseki", "oxigraph"],
        "GraphStorePort": ["oxigraph"],
        "LLMClient": ["openai-compatible"],
        "MetadataStorePort": ["postgres"],
        "MetricGraph": ["neptune", "oxigraph"],
        "MetricIndexPort": ["platform-pg"],
        "ObjectStorePort": ["fs", "s3"],
        "OntologyLookup": ["graph"],
        "QueryExecutor": ["postgres"],
        "SecretProvider": ["env", "secretsmanager"],
        "VectorClient": ["platform-pgvector"],
        "WarehouseAdminPort": ["postgres"],
    }


def test_aws_factories_install_the_fail_fast_botocore_policy() -> None:
    """``ssm``/``secretsmanager``/``s3`` keep the customer-path sync config."""
    specs = catalog()
    for interface, provider in (
        ("ConfigProvider", "ssm"),
        ("SecretProvider", "secretsmanager"),
        ("ObjectStorePort", "s3"),
    ):
        implementation = specs[interface].providers[provider].factory(Settings({"AWS_REGION": "eu-west-1"}))
        assert implementation._region == "eu-west-1"
        assert implementation._client_config.read_timeout == 8


def test_llm_provider_passes_the_catalog_contract_check() -> None:
    """The shell is declared against the two methods it can actually serve.

    Regression: the spec once required ``complete``, which no LLM provider has,
    so every ``resolve("LLMClient")`` failed with ``ProviderMismatchError``.
    """
    resolution = REGISTRY.resolve("LLMClient", Settings({"COA_PROVIDER_LLM": "openai-compatible"}))
    assert resolution.provider == "openai-compatible"
    assert type(resolution.instance).__name__ == "PlatformLLMShell"


def test_every_context_names_known_interfaces() -> None:
    known = set(catalog())
    for context, interfaces in CONTEXT_INTERFACES.items():
        assert set(interfaces) <= known, f"{context} references unknown interfaces"


def test_assemble_reports_missing_interfaces_for_a_context() -> None:
    with pytest.raises(ResolutionErrors) as excinfo:
        assemble("answering", Settings({}))
    names = {error.interface for error in excinfo.value.errors}
    assert names == set(CONTEXT_INTERFACES["answering"])
