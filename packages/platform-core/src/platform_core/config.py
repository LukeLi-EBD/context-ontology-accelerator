"""Configuration schema, loading and fail-fast validation.

Source of truth: _design/03 section 8 (defaults + validation), _design/04 section 10.1.
Priority: CLI (not exposed in S0) < environment < platform.yaml < built-in defaults.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .errors import EXIT_CONFIG, PlatformError

SUPPORTED_CONFIG_VERSION = 1
ENV_PREFIX = "PLATFORM__"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HttpConfig(_Strict):
    port: int = Field(default=8080, ge=1, le=65535)
    bind: str = "0.0.0.0"


class DatabaseConfig(_Strict):
    url: str
    pool_max: int = Field(default=10, ge=1, le=100)
    statement_timeout_ms: int | None = Field(default=None, ge=0)


class GraphConfig(_Strict):
    # Q8-a: the schema accepts every known provider name; whether it is
    # *assembled* is decided in _apply_semantics with E_PROVIDER_NOT_IMPLEMENTED
    # (known but missing adapter) vs E_PROVIDER_INVALID (unknown value).
    provider: str = "oxigraph-http"
    endpoint: str = "http://oxigraph:7878"
    data_dir: str | None = None
    default_graph: str | None = None
    readonly: bool = False
    allow_service: bool = False
    allow_update: bool = False
    timeout_ms: int = Field(default=30000, ge=0, le=300000)
    max_rows: int = Field(default=10000, ge=1)
    max_construct_triples: int = Field(default=200000, ge=1)


class CanvasConfig(_Strict):
    """D1 canvas multi-hop (design 53/55). provider is decided at assembly time."""

    # Q8-a split codes: known-but-unassembled -> E_PROVIDER_NOT_IMPLEMENTED,
    # unknown -> E_PROVIDER_INVALID (see _apply_semantics).
    provider: str = "off"
    simple_max_hops: int = Field(default=3, ge=1, le=4)
    full_max_hops: int = Field(default=4, ge=1, le=6)
    max_nodes: int = Field(default=200, ge=1, le=1000)
    max_edges: int = Field(default=400, ge=1, le=2000)
    max_paths: int = Field(default=20, ge=1, le=50)
    timeout_ms: int = Field(default=500, ge=100, le=5000)


class StorageConfig(_Strict):
    small_object_provider: Literal["pg", "fs"] = "pg"
    large_object_provider: Literal["fs", "pg", "silo"] = "fs"
    provider: Literal["fs", "pg", "silo", "in-memory"] | None = None
    root: str = "/data"
    tmp_dir: str = "/data/tmp"
    min_free_pct: int = Field(default=10, ge=0, le=100)
    gc_grace_hours: int = Field(default=48, ge=0)
    pg_blob_max_file_mb: int = Field(default=10, ge=1)
    pg_blob_max_total_pct: int = Field(default=20, ge=0, le=100)
    pg_blob_max_count: int = Field(default=100000, ge=1)
    fs_hard_max_file_mb: int = Field(default=256, ge=1)
    pg_mode: Literal["auto", "bytea", "lo"] = "auto"
    require_range_read: bool = True
    endpoint: str | None = None
    bucket: str | None = None
    access_key_ref: str | None = None
    secret_key_ref: str | None = None
    routing: dict[str, Any] | None = None


class RuntimeConfig(_Strict):
    mode: Literal["learn", "lean"] = "learn"


class OntologyConfig(_Strict):
    """S1 ontology bootstrap settings (03 section 8.2)."""

    init_mode: Literal["off", "once", "watch"] = "watch"
    init_source: str = "/data/ontology/bootstrap.ttl"
    init_semver: str = "0.0.0"
    watch_interval_seconds: int = Field(default=30, ge=5, le=3600)
    max_source_bytes: int = Field(default=5 * 1024 * 1024, ge=1024)
    # G-01: owl:imports closure. Local mirror wins over the network so offline
    # boxes can resolve imports; unresolved IRIs are reported, never dropped.
    import_dir: str = "/data/ontology-imports"
    import_fetch_enabled: bool = True
    import_fetch_timeout_ms: int = Field(default=5000, ge=500, le=60000)
    import_max_depth: int = Field(default=4, ge=1, le=10)
    import_max_imports: int = Field(default=50, ge=1, le=200)


class OcrConfig(_Strict):
    """D22: OCR stays off in the single-node build (S2 ships no OCR engine)."""

    enabled: bool = False
    engine: Literal["paddleocr", "tesseract"] = "paddleocr"
    lang: str = "chi_sim+en"
    min_chars_per_page: int = Field(default=20, ge=1, le=500)


class DocumentsConfig(_Strict):
    """S2 ingest settings (10 section 3)."""

    bucket: str = Field(default="documents", min_length=1)
    max_upload_bytes: int = Field(default=200 * 1024 * 1024, ge=1024 * 1024, le=2 * 1024**3)
    chunk_max_chars: int = Field(default=1200, ge=100, le=20000)
    chunk_overlap_chars: int = Field(default=200, ge=0, le=19999)
    min_chunk_chars: int = Field(default=1, ge=1, le=100)
    extract_tables: bool = True
    parser: Literal["local"] = "local"


class EmbeddingConfig(_Strict):
    """S3 embedding client (04 section 4.4; 03 section 3.5 pins 1024 dims)."""

    provider: Literal["local-bge", "openai-compatible", "ark", "fake", "disabled"] = "local-bge"
    model: str = "BAAI/bge-m3"
    dimensions: int = Field(default=1024, ge=1, le=4096)
    endpoint: str = "http://embedding:80/v1"
    timeout_ms: int = Field(default=30000, ge=1000, le=300000)
    # R5/S13H-11 CPU tier. 2026-11-05 12:35 实测：TEI cpu-1.8 (candle CPU)
    # 单请求 batch>=4 会触发 core/src/queue.rs 的 `Full(..)` panic 并退出
    # （batch=4: 14/16 请求 `Server disconnected`；batch=8: 7/8 失败）。
    # batch=2 稳定、batch=1 反而最快（2.19 vs 1.87 chunk/s），故默认取 2。
    batch_size: int = Field(default=2, ge=1, le=32)
    batch_max: int = Field(default=2, ge=1, le=32)
    chunk_per_request_max: int = Field(default=32, ge=1, le=256)
    # 单请求总字符预算：TEI --max-batch-tokens=2048，超预算会走 split 路径并
    # 触发 queue.rs panic（2026-11-05 12:44 110-chunk 真实文档实测 restarts+1）。
    request_max_chars: int = Field(default=1600, ge=200, le=8000)
    # Platform-side single-flight gate is fixed at 1; this is the HTTP timeout.
    request_timeout_s: int = Field(default=60, ge=1, le=600)
    # 保底限速：默认约为实测上限（2.19 chunk/s）的 60% 取整。0 表示不限。
    max_chunks_per_sec: float = Field(default=1.0, ge=0.0, le=1000.0)
    # S14H-17 大文档修复：自适应超时 = base(timeout_ms) + perChar * 批内最长块字符数，
    # 上限 timeout_max_s；仅 E_EMBED_TIMEOUT 重试 retry_max 次（线性退避）。
    adaptive_timeout_per_char_s: float = Field(default=0.02, ge=0.0, le=1.0)
    timeout_max_s: int = Field(default=120, ge=10, le=600)
    retry_max: int = Field(default=2, ge=0, le=5)
    retry_backoff_s: float = Field(default=1.0, ge=0.1, le=10.0)
    # 长块单独发（不与任何块合批）；短块仍按 batch_size<=2 合批。
    long_chunk_chars: int = Field(default=900, ge=200, le=20000)
    # 分段提交/断点：普通文档每 50 chunk 提交；>500 chunk 的大文档每批 100。
    index_commit_chunks: int = Field(default=50, ge=1, le=1000)
    large_doc_chunks: int = Field(default=500, ge=100, le=100000)
    large_doc_batch_chunks: int = Field(default=100, ge=1, le=1000)
    service_enabled: bool = True
    api_key_env: str = "EMBEDDING_API_KEY"
    # Ark is used for the non-default partition only (platform reindex --provider=ark).
    # The probe on 2026-11-05 returned 2048 dims, so it cannot share vectors with BGE-M3.
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/coding/v3"
    ark_model: str = "doubao-embedding-vision"
    ark_dimensions: int = Field(default=2048, ge=1, le=4096)
    ark_api_key_env: str = "PLATFORM__LLM__API_KEY"


class SearchConfig(_Strict):
    """S3 hybrid search (03 D19: RRF k=60)."""

    enabled: bool = True
    top_k: int = Field(default=10, ge=1, le=100)
    candidate_k: int = Field(default=30, ge=1, le=500)
    rrf_k: int = Field(default=60, ge=1, le=1000)
    # 0.05 let one shared trigram through: a random 13-char token scored 0.077
    # against 23 unrelated chunks (measured 2026-11-05 on 1425 real chunks).
    # 0.10 removes those hits; a meaningful 3-char term scores 0.5+.
    min_similarity: float = Field(default=0.10, ge=0.0, le=1.0)
    # S16: LRU cache for query-string embeddings (interactive repeats only).
    query_embedding_cache_size: int = Field(default=256, ge=0, le=4096)
    # T2: alias strings merged into the lexical route only (RRF stays two-route).
    lexical_expand: bool = True
    lexical_expand_max: int = Field(default=4, ge=1, le=10)
    # S14H-17 chunk-level segmented transactions / checkpoints (see search.py).
    index_commit_chunks: int = Field(default=50, ge=1, le=1000)
    large_doc_chunks: int = Field(default=500, ge=100, le=100000)
    large_doc_batch_chunks: int = Field(default=100, ge=1, le=1000)


class ContextConfig(_Strict):
    """S6 context assembly (04 section 5.3). Orchestration only; no in-app ranking."""

    enabled: bool = True
    default_token_budget: int = Field(default=2048, ge=64, le=32768)
    max_token_budget: int = Field(default=8192, ge=64, le=65536)
    default_top_k: int = Field(default=10, ge=1, le=50)
    graph_limit: int = Field(default=50, ge=1, le=500)
    seed_limit: int = Field(default=10, ge=1, le=100)
    # Q4: minimum T-Box term coverage before an answer is considered possible.
    answerable_min_coverage: float = Field(default=0.6, ge=0.0, le=1.0)
    # T1/T2: SKOS alias expansion over the T-Box (design 24 section 7-1).
    # Toggle exists so before/after can be measured on the same build.
    term_expand: bool = True
    term_expand_max_hits: int = Field(default=5, ge=1, le=20)


class LlmConfig(_Strict):
    """S4 OpenAI-compatible LLM client (04 section 4.6). Empty base_url/model = unconfigured."""

    # `ark` = Volcengine Ark coding plan, which speaks the OpenAI-compatible
    # protocol but bills/limits differently (base URL must end with /coding/v3).
    provider: Literal["openai-compatible", "ark", "disabled"] = "openai-compatible"
    # Q8-a: preset fills base_url/model/api_key_env only when they are empty;
    # an explicit value always wins.
    preset: Literal["deepseek", "volcano-ark", "ollama"] | None = None
    base_url: str = ""
    model: str = ""
    timeout_ms: int = Field(default=30000, ge=1000, le=300000)
    max_retries: int = Field(default=1, ge=0, le=3)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    api_key_env: str = "LLM_API_KEY"


class ExtractionRule(_Strict):
    name: str = Field(min_length=1, max_length=64)
    pattern: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    object: str = Field(min_length=1)


class ExtractionConfig(_Strict):
    """S4 rule/LLM extraction settings."""

    enabled: bool = True
    max_candidates_per_chunk: int = Field(default=10, ge=1, le=100)
    # Legacy floor for the adaptive LLM batch size (kept for existing configs).
    llm_max_chunks: int = Field(default=20, ge=1, le=1000)
    # Explicit override: when set it wins over the adaptive batch size.
    max_chunks: int | None = Field(default=None, ge=1, le=5000)
    rules: list[ExtractionRule] = Field(default_factory=list)


class ReasoningConfig(_Strict):
    """S5 SHACL + EL materialization (04 section 4.5, 05 section 2)."""

    # Q8-a: on-demand is a recognised enum value but returns
    # E_REASONING_ON_DEMAND_NOT_IMPLEMENTED at runtime (no query rewriter yet).
    mode: Literal["off", "rdfs", "materialize", "on-demand", "validate"] = "materialize"
    profile: Literal["RDFS", "EL", "OWL2EL", "OWL2QL", "OWL2RL", "OWL2DL"] = "EL"
    # Q8-a: enum accepts robot/elk/hermit/konclude; unimplemented engines are
    # rejected in _apply_semantics with E_PROVIDER_NOT_IMPLEMENTED.
    engine: str = "robot"
    service_enabled: bool = True
    endpoint: str = "http://reasoner:7879"
    timeout_ms: int = Field(default=300000, ge=1000, le=3600000)
    inferred_graph_prefix: str = "urn:platform:inferred:"
    abox_graphs: list[str] = Field(
        default_factory=lambda: ["urn:platform:graph:abox:main"]
    )
    shapes_dir: str = "/data/shapes"
    consistency_first: bool = True
    max_violations: int = Field(default=200, ge=1, le=5000)
    # Split of the former single max_input_bytes. Stage 1 (RDFS closure) bounds
    # the source bytes, stage 2 (ROBOT/ELK) bounds the assembled payload
    # (source + closure). Both default to 50MiB, so behaviour is unchanged.
    max_source_bytes: int = Field(default=50 * 1024 * 1024, ge=1024, le=500 * 1024 * 1024)
    max_assembly_bytes: int = Field(
        default=50 * 1024 * 1024, ge=1024, le=500 * 1024 * 1024
    )
    # Offline-window guard: when false (default) a governed publish/rollback
    # does NOT start a full A-Box materialization. Inference then runs only via
    # the explicit offline `materialize` action, never as a publish side effect.
    materialize_online: bool = False


class LogConfig(_Strict):
    level: Literal["debug", "info", "warning", "error"] = "info"
    format: Literal["json", "text"] = "json"


class DatagenConfig(_Strict):
    """Synthetic-data generator safety switch.

    Writing to the official ``platform`` schema is allowed only in explicitly
    designated test environments. The default (false) keeps the generator in
    the isolated ``synthetic`` schema. Turning this back to false is the
    pre-production isolation gate.
    """

    allow_official_schema: bool = False


# --- G8 terms gate config ---
# 严重级别映射：默认 blocking 的问题码。覆盖缺失（definition/notation）与
# 覆盖率下降只产生 warning，不拦截发布。
DEFAULT_TERMS_BLOCKING_CODES: tuple[str, ...] = (
    "SURFACE_SHARED_BY_MULTIPLE_CONCEPTS",
    "PREF_CONFLICTS_WITH_ALT_OF_OTHER_CONCEPT",
    "CONCEPT_MISSING_PREF_LABEL",
    "SUPPRESSED_SURFACE_STILL_ALIAS",
    "ALIAS_INCOMPLETE",
    "ALIAS_TARGET_MISSING",
    "GUARD_REGEX_INVALID",
)

TERMS_GATE_KNOWN = ("off", "warn", "block")
TERMS_GATE_IMPLEMENTED = ("off", "warn", "block")


class TermsConfig(_Strict):
    """T-Box 发布前的术语门禁（O-05）。

    ``gate`` 三档：off 完全不跑核对；warn 记录问题但不拦截；block 在
    blocking 级问题存在时拒绝发布。``blocking_codes`` 是严重级别阈值，
    可按问题码把默认 warning 提升/降级。``coverage_decrease_tolerance``
    是覆盖率相对上一发布版本允许的下降幅度（0 表示任何下降都记 warning）。
    """

    gate: str = "warn"
    blocking_codes: list[str] = Field(default_factory=lambda: list(DEFAULT_TERMS_BLOCKING_CODES))
    coverage_decrease_tolerance: float = Field(default=0.0, ge=0.0, le=1.0)
    # 方案 A：`purpose=smoke` 必须携带内部 token。名字是保存密钥的**环境变量名**，
    # 密钥本身不进配置文件、不进日志、不进证据包。未配置 => fail-closed（拒绝豁免）。
    smoke_token_env: str = "PLATFORM_SMOKE_TOKEN"


# --- end G8 terms gate config ---


class EntityViewConfig(_Strict):
    """Entity detail presentation filters.

    Only the read-only entity view applies these; both the graphs and
    /browse/sparql keep every triple. Extend the list when other meta-level
    types should stop being shown as neighbours/classes.
    """

    ignore_types: list[str] = Field(
        default_factory=lambda: [
            "http://www.w3.org/2002/07/owl#Thing",
            "http://www.w3.org/2002/07/owl#NamedIndividual",
        ]
    )


# --- G7 quota config ---
class QuotaConfig(_Strict):
    """C2 budget guardrail (design 87). provider is decided at assembly time.

    Same Q8-a split as graph/canvas: every known provider name is accepted by
    the schema, then _g7_apply_quota_semantics rejects unknown values with
    E_PROVIDER_INVALID and known-but-unassembled values with
    E_PROVIDER_NOT_IMPLEMENTED. ``full`` stays a skeleton in C2-1.
    """

    provider: str = "off"
    # 0 = unlimited; the simple implementation still counts when a limit is 0.
    daily_token_limit: int = Field(default=0, ge=0)
    daily_request_limit: int = Field(default=0, ge=0)
    # What callers may do when the limit is reached: skip the LLM call and keep
    # the retrieval/rules path (degrade), or fail the request (reject).
    on_exceed: Literal["degrade", "reject"] = "degrade"
    # Scope key used by assembled consumers (full will key by user/tenant).
    default_scope: str = Field(default="global", min_length=1, max_length=64)
    # Pre-call token estimate for the gate (chars per token); the recorded value
    # is the provider's reported usage when available (see LlmClient.last_usage).
    chars_per_token: int = Field(default=4, ge=1, le=16)


def _g7_apply_quota_semantics(model: PlatformConfig, warnings: list[str]) -> None:
    known = ("off", "simple", "full")
    implemented = ("off", "simple")
    if model.quota.provider not in known:
        raise _config_error(
            "E_PROVIDER_INVALID",
            (
                f"quota.provider={model.quota.provider!r} is not a known provider; "
                f"known values: {', '.join(known)}"
            ),
            key="quota.provider",
            hint="fix the name; unknown names are configuration errors, not missing adapters",
        )
    if model.quota.provider not in implemented:
        raise _config_error(
            "E_PROVIDER_NOT_IMPLEMENTED",
            (
                f"quota.provider={model.quota.provider} is a known provider but no adapter "
                "is assembled (C2-2 full stays behind this switch)"
            ),
            key="quota.provider",
            hint="use quota.provider=simple, or quota.provider=off to disable counting",
        )
    if (
        model.quota.provider == "simple"
        and model.quota.daily_token_limit == 0
        and model.quota.daily_request_limit == 0
    ):
        warnings.append(
            "quota.provider=simple with both daily limits 0: usage is counted but nothing is enforced"
        )
# --- end G7 quota config ---


class PlatformConfig(_Strict):
    mode: Literal["dev", "single", "test"] = "single"
    config_version: int = 1
    data_dir: str = "/data"
    http: HttpConfig = Field(default_factory=HttpConfig)
    database: DatabaseConfig
    graph: GraphConfig = Field(default_factory=GraphConfig)
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    # Declared but not assembled in S0 (see S0 design section 4.2).
    llm: LlmConfig = Field(default_factory=LlmConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    ocr: OcrConfig = Field(default_factory=OcrConfig)
    documents: DocumentsConfig = Field(default_factory=DocumentsConfig)
    ontology: OntologyConfig = Field(default_factory=OntologyConfig)
    reasoning: ReasoningConfig = Field(default_factory=ReasoningConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    entity_view: EntityViewConfig = Field(default_factory=EntityViewConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    datagen: DatagenConfig = Field(default_factory=DatagenConfig)
    # --- G7 quota config ---
    quota: QuotaConfig = Field(default_factory=QuotaConfig)
    # --- end G7 quota config ---
    # --- G8 terms gate config ---
    terms: TermsConfig = Field(default_factory=TermsConfig)
    # --- end G8 terms gate config ---
    jobs: dict[str, Any] = Field(default_factory=dict)
    server: dict[str, Any] = Field(default_factory=dict)
    requirements: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "sparql_query": ["graph.sparql"],
            "fact_write": ["graph.update"],
            "object_put": ["object.put"],
            "object_get": ["object.get"],
            "document_ingest": ["document.ingest"],
        }
    )
    degradation: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "allow": [],
            "deny": [
                "sparql_query",
                "fact_write",
                "object_put",
                "object_get",
                "document_ingest",
            ],
        }
    )


@dataclass
class ConfigBundle:
    config: PlatformConfig
    path: Path
    sources: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def source_of(self, dotted_key: str) -> str:
        return self.sources.get(dotted_key, "default")


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            flat.update(_flatten(item, child))
    else:
        flat[prefix] = value
    return flat


def _parse_env_scalar(raw: str) -> Any:
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw
    if isinstance(parsed, (dict, list)):
        return raw
    return parsed


def _env_overrides(environ: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, raw in environ.items():
        if not key.startswith(ENV_PREFIX):
            continue
        parts = key[len(ENV_PREFIX) :].lower().split("__")
        if len(parts) < 2:
            continue
        # Secrets are read by the SecretProvider, never merged into the config
        # document (so they cannot leak through /status, logs or repr()).
        if parts[-1] == "api_key":
            continue
        node = result
        for part in parts[:-1]:
            existing = node.get(part)
            if not isinstance(existing, dict):
                existing = {}
                node[part] = existing
            node = existing
        node[parts[-1]] = _parse_env_scalar(raw)
    return result


def _config_error(code: str, detail: str, key: str | None = None, hint: str = "") -> PlatformError:
    return PlatformError(
        code=code,
        detail=detail,
        stage="config",
        key=key,
        hint=hint,
        exit_code=EXIT_CONFIG,
    )


def load_config(path: str | Path, environ: dict[str, str] | None = None) -> ConfigBundle:
    """Load, merge and validate configuration. Raises PlatformError (exit 78)."""

    config_path = Path(path)
    if not config_path.is_file():
        raise _config_error(
            "E_CONFIG_FILE",
            f"configuration file not found: {config_path}",
            key="config",
            hint="mount ./data:/data and pass --config /data/platform.yaml",
        )

    try:
        yaml_doc = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise _config_error("E_CONFIG_YAML", f"invalid YAML: {exc}", key="config") from exc
    if not isinstance(yaml_doc, dict):
        raise _config_error("E_CONFIG_YAML", "top-level YAML value must be a mapping", key="config")

    environ = environ if environ is not None else dict(os.environ)
    env_doc = _env_overrides(environ)
    merged = _deep_merge(yaml_doc, env_doc)

    try:
        model = PlatformConfig.model_validate(merged)
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first.get("loc", ())) or "config"
        raise _config_error(
            "E_CONFIG_SCHEMA",
            f"{first.get('msg', 'invalid value')} (got {first.get('input')!r})",
            key=location,
            hint="fix the value or remove the key; unknown keys are rejected",
        ) from exc

    warnings = _apply_semantics(model, merged)
    sources = {key: "yaml" for key in _flatten(yaml_doc)}
    sources.update({key: "env" for key in _flatten(env_doc)})
    sources["config.file"] = "yaml"
    return ConfigBundle(config=model, path=config_path, sources=sources, warnings=warnings)


def _apply_semantics(model: PlatformConfig, merged: dict[str, Any]) -> list[str]:
    warnings: list[str] = []

    if model.mode == "test":
        raise _config_error(
            "E_MODE_TEST_UNSUPPORTED",
            "mode=test requires memory doubles which S0 does not implement",
            key="mode",
            hint="use mode=single",
        )
    if model.config_version > SUPPORTED_CONFIG_VERSION:
        raise _config_error(
            "E_CONFIG_VERSION",
            f"config_version {model.config_version} is newer than supported {SUPPORTED_CONFIG_VERSION}",
            key="config_version",
        )

    storage_raw = merged.get("storage", {}) if isinstance(merged.get("storage"), dict) else {}

    if "provider" in storage_raw and model.storage.provider is not None:
        shorthand = model.storage.provider
        if shorthand == "in-memory":
            raise _config_error(
                "E_STORAGE_IN_MEMORY",
                "in-memory object storage is only allowed in mode=test",
                key="storage.provider",
            )
        if shorthand == "silo":
            raise _config_error(
                "E_PROVIDER_NOT_IMPLEMENTED",
                "storage.provider=silo is a known provider but no Silo adapter is assembled (P1)",
                key="storage.provider",
                hint="use storage.provider=fs",
            )
        if "small_object_provider" not in storage_raw:
            model.storage.small_object_provider = shorthand  # type: ignore[assignment]
        if "large_object_provider" not in storage_raw:
            model.storage.large_object_provider = shorthand  # type: ignore[assignment]

    if (
        model.storage.large_object_provider == "pg"
        and model.storage.require_range_read
        and model.storage.pg_mode == "bytea"
    ):
        raise _config_error(
            "E_CONFIG_E011",
            "range_read requires pg_mode=lo (or set require_range_read=false)",
            key="storage.require_range_read",
        )
    # Q8-a: "can it be assembled?" replaces a blanket whitelist rejection.
    # Known-but-missing adapters are E_PROVIDER_NOT_IMPLEMENTED; unknown values
    # are E_PROVIDER_INVALID. Both exit 78 but the codes mean different things.
    if model.storage.large_object_provider == "pg":
        raise _config_error(
            "E_PROVIDER_NOT_IMPLEMENTED",
            (
                "large_object_provider=pg is a known provider but its bytea/lo tier "
                "cannot serve a truthful range_read; no adapter is assembled"
            ),
            key="storage.large_object_provider",
            hint="use large_object_provider=fs",
        )
    if model.storage.large_object_provider == "silo":
        raise _config_error(
            "E_PROVIDER_NOT_IMPLEMENTED",
            "large_object_provider=silo is a known provider but no Silo adapter is assembled (P1)",
            key="storage.large_object_provider",
            hint="use large_object_provider=fs",
        )

    graph_known = (
        "oxigraph-http", "oxigraph", "pyoxigraph", "pyoxigraph-memory", "fuseki", "age"
    )
    graph_implemented = ("oxigraph-http", "oxigraph", "fuseki")
    if model.graph.provider not in graph_known:
        raise _config_error(
            "E_PROVIDER_INVALID",
            (
                f"graph.provider={model.graph.provider!r} is not a known provider; "
                f"known values: {', '.join(graph_known)}"
            ),
            key="graph.provider",
            hint="fix the name; unknown names are configuration errors, not missing adapters",
        )
    if model.graph.provider not in graph_implemented:
        raise _config_error(
            "E_PROVIDER_NOT_IMPLEMENTED",
            (
                f"graph.provider={model.graph.provider} is a known provider but no adapter "
                "is assembled (pyoxigraph/pyoxigraph-memory/age stay P2)"
            ),
            key="graph.provider",
            hint="use graph.provider=oxigraph-http or graph.provider=fuseki",
        )
    if model.graph.provider == "oxigraph":
        warnings.append("graph.provider=oxigraph: alias of oxigraph-http (same HTTP adapter)")
        model.graph.provider = "oxigraph-http"
    if not model.graph.endpoint:
        raise _config_error("E_CONFIG_REQUIRED", "graph.endpoint is required", key="graph.endpoint")

    # Q8-a (design 53 §5.2): canvas opens every known provider name and rejects
    # only the unknown ones. D1-2 assembles `full`; the switch now covers all
    # three values.
    canvas_known = ("off", "simple", "full")
    canvas_implemented = ("off", "simple", "full")
    if model.canvas.provider not in canvas_known:
        raise _config_error(
            "E_PROVIDER_INVALID",
            (
                f"canvas.provider={model.canvas.provider!r} is not a known provider; "
                f"known values: {', '.join(canvas_known)}"
            ),
            key="canvas.provider",
            hint="fix the name; unknown names are configuration errors, not missing adapters",
        )
    if model.canvas.provider not in canvas_implemented:
        raise _config_error(
            "E_PROVIDER_NOT_IMPLEMENTED",
            (
                f"canvas.provider={model.canvas.provider} is a known provider but no adapter "
                "is assembled"
            ),
            key="canvas.provider",
            hint="use canvas.provider=simple or full, or canvas.provider=off to disable",
        )
    if model.canvas.provider == "simple" and model.canvas.simple_max_hops > 3:
        warnings.append(
            "canvas.simple_max_hops>3: simple is hard-capped at 3 hops, the extra value is ignored"
        )

    if model.storage.pg_blob_max_file_mb > 1024:
        warnings.append(
            "storage.pg_blob_max_file_mb > 1024 exceeds bytea single-value guidance; "
            "objects will be routed to fs"
        )
    if model.storage.small_object_provider == "fs":
        warnings.append("storage.small_object_provider=fs: all objects are stored in the fs CAS")

    if model.documents.chunk_overlap_chars >= model.documents.chunk_max_chars:
        raise _config_error(
            "E_CONFIG_CHUNK_OVERLAP",
            (
                f"documents.chunk_overlap_chars={model.documents.chunk_overlap_chars} must be "
                f"smaller than documents.chunk_max_chars={model.documents.chunk_max_chars}"
            ),
            key="documents.chunk_overlap_chars",
            hint="lower chunk_overlap_chars or raise chunk_max_chars; the chunker must advance",
        )

    if model.ocr.enabled:
        raise _config_error(
            "E_OCR_UNSUPPORTED",
            "ocr.enabled=true is not supported: the single-node S2 build ships no OCR engine (D22)",
            key="ocr.enabled",
            hint="set ocr.enabled=false; scanned PDFs are reported as degraded with NO_OCR_ENABLED",
        )

    if model.search.candidate_k < model.search.top_k:
        raise _config_error(
            "E_CONFIG_SEARCH_RANGE",
            (
                f"search.candidate_k={model.search.candidate_k} must be >= "
                f"search.top_k={model.search.top_k}"
            ),
            key="search.candidate_k",
            hint="candidate_k is the per-route candidate pool; it cannot be smaller than top_k",
        )

    if model.context.default_token_budget > model.context.max_token_budget:
        raise _config_error(
            "E_CONFIG_CONTEXT",
            (
                f"context.default_token_budget={model.context.default_token_budget} must be <= "
                f"context.max_token_budget={model.context.max_token_budget}"
            ),
            key="context.default_token_budget",
            hint="lower the default budget or raise max_token_budget",
        )

    if model.embedding.provider in ("local-bge", "openai-compatible") and not model.embedding.endpoint:
        raise _config_error(
            "E_CONFIG_REQUIRED",
            "embedding.endpoint is required for the HTTP embedding providers",
            key="embedding.endpoint",
        )
    if model.embedding.provider == "fake":
        warnings.append(
            "embedding.provider=fake: deterministic test vectors only, never index production data"
        )
    if model.embedding.provider == "disabled":
        warnings.append("embedding.provider=disabled: semantic search falls back to lexical (FTS)")

    for rule in model.extraction.rules:
        try:
            compiled = re.compile(rule.pattern)
        except re.error as exc:
            raise _config_error(
                "E_CONFIG_EXTRACTION_RULE",
                f"extraction rule {rule.name!r} has an invalid regex: {exc}",
                key="extraction.rules",
                hint="fix the pattern or remove the rule",
            ) from exc
        missing = {"subject", "object"} - set(compiled.groupindex)
        if missing:
            raise _config_error(
                "E_CONFIG_EXTRACTION_RULE",
                (
                    f"extraction rule {rule.name!r} must define named groups "
                    f"{sorted(missing)}"
                ),
                key="extraction.rules",
                hint="use (?P<subject>...) and (?P<object>...) in the pattern",
            )
    if not model.extraction.enabled:
        warnings.append("extraction:disabled")
    # Q8-a: llm.preset maps to a base_url/model/api_key triplet. Explicit values
    # always win; the preset only fills empty fields (never overwrites).
    llm_presets = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "api_key_env": "DEEPSEEK_API_KEY",
        },
        "volcano-ark": {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "ep-xxxx",
            "api_key_env": "ARK_API_KEY",
        },
        "ollama": {
            "base_url": "http://ollama:11434/v1",
            "model": "qwen2.5:7b-instruct",
            "api_key_env": "OLLAMA_API_KEY",
        },
    }
    if model.llm.preset:
        preset = llm_presets[model.llm.preset]
        filled: list[str] = []
        if not model.llm.base_url:
            model.llm.base_url = preset["base_url"]
            filled.append("base_url")
        if not model.llm.model:
            model.llm.model = preset["model"]
            filled.append("model")
        if model.llm.api_key_env == "LLM_API_KEY" and preset["api_key_env"]:
            model.llm.api_key_env = preset["api_key_env"]
            filled.append("api_key_env")
        warnings.append(
            f"llm.preset={model.llm.preset}: filled {', '.join(filled) or 'nothing'} "
            "(explicit values were kept)"
        )

    if model.llm.provider == "disabled":
        warnings.append("llm.provider=disabled: extraction uses rules only")
    elif not (model.llm.base_url and model.llm.model):
        warnings.append("llm.base_url/model are empty: extraction uses rules only (auto mode)")

    # ---- S5 reasoning semantics -----------------------------------------
    # Q8-a: engine names are opened at the enum layer; only assembled adapters
    # pass. robot (ELK materialize) and hermit (consistency/classify) exist.
    engine_known = ("robot", "elk", "hermit", "konclude")
    engine_implemented = ("robot", "hermit")
    if model.reasoning.engine not in engine_known:
        raise _config_error(
            "E_PROVIDER_INVALID",
            (
                f"reasoning.engine={model.reasoning.engine!r} is not a known engine; "
                f"known values: {', '.join(engine_known)}"
            ),
            key="reasoning.engine",
            hint="fix the name; unknown names are configuration errors",
        )
    if model.reasoning.engine not in engine_implemented:
        raise _config_error(
            "E_PROVIDER_NOT_IMPLEMENTED",
            (
                f"reasoning.engine={model.reasoning.engine} is a known engine but no "
                "adapter is assembled; ROBOT exposes ELK via engine=robot"
            ),
            key="reasoning.engine",
            hint="use engine=robot (ELK materialize) or engine=hermit (DL consistency/classify)",
        )

    if model.reasoning.mode == "on-demand":
        warnings.append(
            "reasoning.mode=on-demand: recognised but NOT implemented "
            "(E_REASONING_ON_DEMAND_NOT_IMPLEMENTED at runtime)"
        )

    if model.reasoning.mode != "off":
        # ROBOT's `reason` offers ELK/HermiT/JFact only: there is no RDFS
        # reasoner to delegate to, and S5 never implements one in-process.
        if model.reasoning.profile == "OWL2DL":
            if model.reasoning.engine != "hermit":
                raise _config_error(
                    "E_CONFIG_REASONING",
                    "reasoning.profile=OWL2DL requires reasoning.engine=hermit (ROBOT/HermiT)",
                    key="reasoning.profile",
                    hint="set reasoning.engine=hermit, or use profile=EL/OWL2EL for ELK",
                )
            if model.reasoning.mode != "validate":
                raise _config_error(
                    "E_CONFIG_REASONING",
                    "reasoning.profile=OWL2DL is only supported for mode=validate; "
                    "materialize stays on ROBOT/ELK",
                    key="reasoning.profile",
                    hint="use mode=validate for DL consistency, or profile=EL for materialize",
                )
        if model.reasoning.profile in ("RDFS", "OWL2QL", "OWL2RL"):
            raise _config_error(
                "E_CONFIG_REASONING",
                (
                    f"reasoning.profile={model.reasoning.profile} is not implemented: "
                    "the assembled reasoners are ROBOT/ELK (OWL 2 EL) and ROBOT/HermiT (DL validate)"
                ),
                key="reasoning.profile",
                hint=(
                    "use profile=EL or OWL2EL for ELK; OWL2DL with engine=hermit for DL "
                    "validate; RDFS closure is the one-shot Jena job "
                    "(docker compose --profile job run --rm rdfs)"
                ),
            )
        if not model.reasoning.inferred_graph_prefix:
            raise _config_error(
                "E_CONFIG_REASONING",
                "reasoning.inferred_graph_prefix is required when reasoning.mode != off",
                key="reasoning.inferred_graph_prefix",
                hint="e.g. urn:platform:inferred:",
            )
        if (
            model.graph.default_graph
            and model.reasoning.inferred_graph_prefix == model.graph.default_graph
        ):
            raise _config_error(
                "E_CONFIG_REASONING",
                "reasoning.inferred_graph_prefix must not equal graph.default_graph",
                key="reasoning.inferred_graph_prefix",
                hint="materialization must never overwrite the source graph (04 section 10.1 #8)",
            )
        if model.reasoning.service_enabled and not model.reasoning.endpoint:
            raise _config_error(
                "E_CONFIG_REQUIRED",
                "reasoning.endpoint is required when reasoning.service_enabled=true",
                key="reasoning.endpoint",
            )
    if model.reasoning.mode == "off":
        warnings.append("reasoning:off(NO_OWL_DL)")
    elif not model.reasoning.service_enabled:
        warnings.append("reasoner:offline_only")
    if model.runtime.mode == "lean" and model.reasoning.mode != "off":
        warnings.append("reasoner:profile_required(lean)")

    # --- G8 terms gate config ---
    if model.terms.gate not in TERMS_GATE_KNOWN:
        raise _config_error(
            "E_PROVIDER_INVALID",
            (
                f"terms.gate={model.terms.gate!r} is not a known gate; "
                f"known values: {', '.join(TERMS_GATE_KNOWN)}"
            ),
            key="terms.gate",
            hint="fix the name; unknown names are configuration errors, not missing adapters",
        )
    if model.terms.gate not in TERMS_GATE_IMPLEMENTED:
        raise _config_error(
            "E_PROVIDER_NOT_IMPLEMENTED",
            (
                f"terms.gate={model.terms.gate} is a known gate but no adapter is assembled"
            ),
            key="terms.gate",
            hint="use terms.gate=off, warn or block",
        )
    if model.terms.gate == "off":
        warnings.append("terms.gate=off: terminology check is skipped at publish")
    # --- end G8 terms gate config ---

    _g7_apply_quota_semantics(model, warnings)

    return warnings
