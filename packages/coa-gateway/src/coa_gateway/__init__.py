"""COA contract gateway — local implementations behind upstream Protocols."""

from coa_gateway.catalog import build_json_source_catalog
from coa_gateway.gateway import LocalGateway
from coa_gateway.graph_fuseki import FusekiGraphClient
from coa_gateway.graph_neptune import NeptuneGraphClient
from coa_gateway.graph_oxigraph import OxigraphGraphClient
from coa_gateway.llm_llama_cpp import LlamaCppLLMClient
from coa_gateway.query_postgres import PostgresQueryExecutor
from coa_gateway.registry import PROVIDERS, build_client, build_gateway
from coa_gateway.settings import (
    DEFAULTS,
    INTERFACES,
    ProviderConfigError,
    ProviderNotConfigured,
    ProviderSettings,
    UnknownProviderError,
)
from coa_gateway.vector_memory import InMemoryVectorClient

__all__ = [
    "DEFAULTS",
    "INTERFACES",
    "InMemoryVectorClient",
    "LlamaCppLLMClient",
    "LocalGateway",
    "NeptuneGraphClient",
    "OxigraphGraphClient",
    "PROVIDERS",
    "PostgresQueryExecutor",
    "FusekiGraphClient",
    "ProviderConfigError",
    "ProviderNotConfigured",
    "ProviderSettings",
    "UnknownProviderError",
    "build_client",
    "build_gateway",
    "build_json_source_catalog",
]
