"""Per-context assembly (plan §11.3 rule 6).

The composition root assembles one bounded context at a time. A context lists
only the interfaces it consumes, so an unconfigured interface used by another
context cannot block startup here.
"""

from __future__ import annotations

from collections.abc import Mapping

from .errors import UnknownInterfaceError
from .registry import ProviderRegistry, Resolution, default_registry
from .settings import Settings

CONTEXT_INTERFACES: Mapping[str, tuple[str, ...]] = {
    # 问答与检索
    "answering": ("GraphClient", "VectorClient", "LLMClient", "QueryExecutor", "Embedding", "ConfigProvider"),
    # 指标
    "metrics": ("QueryExecutor", "GraphClient", "MetricGraph", "ConfigProvider", "SecretProvider"),
    # 本体
    "ontology": ("GraphStorePort", "MetadataStorePort", "SchemaProvider", "ConfigProvider"),
    # 知识图
    "knowledge-graph": ("GraphClient", "GraphStorePort", "ChangeFeedPort", "ConfigProvider"),
    # 文档摄入
    "ingestion": ("ObjectStorePort", "TaskQueuePort", "OcrPort", "Embedding", "EventBusPort"),
    # 数据源接入
    "data-sources": ("QueryExecutor", "DataSourceLookup", "SecretProvider", "ConfigProvider"),
    # 控制面
    "control-plane": ("ControlPlaneStore", "IdentityPort", "ChangeFeedPort", "ConfigProvider"),
}


def interfaces_for(context: str) -> tuple[str, ...]:
    try:
        return CONTEXT_INTERFACES[context]
    except KeyError as exc:
        raise UnknownInterfaceError(
            f"unknown context {context!r}",
            interface=context,
            allowed=tuple(CONTEXT_INTERFACES),
        ) from exc


def assemble(
    context: str,
    settings: Settings,
    registry: ProviderRegistry | None = None,
) -> dict[str, Resolution]:
    """Resolve every interface of one context; raise ``ResolutionErrors`` on any failure."""
    registry = registry or default_registry()
    return registry.resolve_many(settings, interfaces_for(context))


__all__ = ["CONTEXT_INTERFACES", "assemble", "interfaces_for"]
