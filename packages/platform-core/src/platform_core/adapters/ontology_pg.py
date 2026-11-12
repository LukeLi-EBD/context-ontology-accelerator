"""OntologyRegistry (S1 subset): import -> publish -> rollback over PG + graph + CAS.

Boundary (04 section 5.2): this file is state machine + orchestration only. RDF
parsing is rdflib, graph stores are Oxigraph, CAS is the S0 ObjectStore. No
diffing, no canonicalization, no graph algorithms.

Decision for the two upstream wordings:
- 03 section 4: rollback = switch the read pointer.
- 04 section 5.2: rollback publishes a new version pointing at the old content.
S1 does both: a new version row is created (immutable history), then the pointer
moves to it (the old content is never mutated or deleted).
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import json

import httpx
from psycopg.types.json import Jsonb
from rdflib import BNode, Graph, Namespace, OWL, RDF, RDFS, URIRef

from ..config import OntologyConfig, TermsConfig
from ..errors import EXIT_CONFIG, PortError, PlatformError
from ..facts import event_hash
from ..ontology_lifecycle import list_transitions, record_transition, validate_transition
from ..ports import Manifest
from ..termlex import assert_guards_compilable
from .. import termgate, termgov
from .graph_oxigraph import OxigraphHttpStore, parse_rdf
from .metadata_pg import MetadataPg
from .object_layered import LayeredObjectStore

log = logging.getLogger(__name__)

ONTOLOGY_BUCKET = "ontology"
POINTER_NAME = "tbox/current"
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.+-]+)?$")
ONTOLOGY_ACTIONS = (
    "imported", "proposed", "approved", "breaking_acknowledged", "published",
    "superseded", "rolled_back", "publish_reverted", "import_conflict_accepted",
)
# 阻断也是事件：被拒的 publish 不产生版本，但"谁试过绕过、试了几次、从哪来"
# 只能靠哈希链回答，所以单独记一个动作。
PUBLISH_BLOCKED_ACTION = "publish_blocked"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
PARSE_LINE_RE = re.compile(r"at line (\d+)")
RDFS_CLASS = "http://www.w3.org/2000/01/rdf-schema#Class"
RDFS_DOMAIN = "http://www.w3.org/2000/01/rdf-schema#domain"
RDFS_RANGE = "http://www.w3.org/2000/01/rdf-schema#range"
OWL_CLASS = "http://www.w3.org/2002/07/owl#Class"
OWL_OBJECT = "http://www.w3.org/2002/07/owl#ObjectProperty"
OWL_DATATYPE = "http://www.w3.org/2002/07/owl#DatatypeProperty"
OWL_ANNOTATION = "http://www.w3.org/2002/07/owl#AnnotationProperty"
OWL_RESTRICTION = "http://www.w3.org/2002/07/owl#Restriction"
OWL_ON_PROPERTY = "http://www.w3.org/2002/07/owl#onProperty"
OWL_MIN_CARD = "http://www.w3.org/2002/07/owl#minCardinality"
OWL_MIN_QCARD = "http://www.w3.org/2002/07/owl#minQualifiedCardinality"


TERM_HIGH_WATER_SCOPE = "metric"


def read_term_high_water(meta: Any) -> dict[str, Any] | None:
    """Last non-zero effective term-set measurement (None until first publish)."""
    try:
        rows = meta.query(
            "SELECT concepts_in_scheme, aliases, version_id, graph_iri, updated_at "
            "FROM platform.term_high_water WHERE scope = %s",
            (TERM_HIGH_WATER_SCOPE,),
        )
    except Exception:  # table missing before V44 is applied
        return None
    if not rows:
        return None
    row = rows[0]
    return {
        "conceptsInScheme": int(row["concepts_in_scheme"]),
        "aliases": int(row["aliases"]),
        "versionId": row.get("version_id"),
        "graph": row.get("graph_iri"),
        "updatedAt": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


def raise_term_high_water(
    meta: Any, counts: dict[str, Any], version_id: str, graph_iri: str
) -> None:
    """Raise the mark only; never lower it (history is the safety baseline)."""
    concepts = int(counts.get("conceptsInScheme") or 0)
    aliases = int(counts.get("aliases") or 0)
    existing = read_term_high_water(meta)
    if existing and existing["conceptsInScheme"] >= concepts:
        return
    meta.execute(
        """
        INSERT INTO platform.term_high_water
            (scope, concepts_in_scheme, aliases, version_id, graph_iri, updated_at)
        VALUES (%s, %s, %s, %s, %s, now())
        ON CONFLICT (scope) DO UPDATE SET
            concepts_in_scheme = EXCLUDED.concepts_in_scheme,
            aliases = EXCLUDED.aliases,
            version_id = EXCLUDED.version_id,
            graph_iri = EXCLUDED.graph_iri,
            updated_at = now()
        """,
        (TERM_HIGH_WATER_SCOPE, concepts, aliases, version_id, graph_iri),
    )


def _term_high_water(registry: Any, meta: Any) -> dict[str, Any] | None:
    """Stored mark, falling back to the current pointer's graph for the first run."""
    mark = read_term_high_water(meta)
    if mark is not None:
        return mark
    try:
        current = termgov.graph_coverage(SimpleNamespace(ontology=registry, graph=registry._graph))
    except Exception:
        return None
    actual = current.get("actual") or {}
    if not actual:
        return None
    return {
        "conceptsInScheme": int(actual.get("conceptsInMetricScheme") or 0),
        "aliases": int(actual.get("aliases") or 0),
        "versionId": current.get("versionId"),
        "graph": current.get("graph"),
        "updatedAt": None,
    }


def _term_audit_payload(gates: dict[str, Any] | None) -> dict[str, Any] | None:
    """Hash-chain-visible summary of the term gate decision.

    The evidence pack is a separate, non-chained table; putting purpose /
    exempted / verdict / baseline / current into ``ontology_event.payload`` keeps
    "why a zero-term version was allowed" inside the tamper-evident audit chain.
    Never contains token material.
    """
    gate = (gates or {}).get("terms")
    if not isinstance(gate, dict):
        return None
    guard = gate.get("vocabGuard") or {}
    exemption = guard.get("exemption")
    return {
        "gate": gate.get("gate"),
        "verdict": gate.get("verdict"),
        "blocked": bool(gate.get("blocked")),
        "exempted": bool(exemption),
        "purpose": guard.get("purpose"),
        "purposeVerified": guard.get("purposeVerified"),
        "tokenStatus": guard.get("tokenStatus"),
        "remoteAddr": guard.get("remoteAddr"),
        "baseline": guard.get("highWater"),
        "current": guard.get("effective"),
        "findingCodes": sorted({
            str(item.get("code")) for item in (gate.get("findings") or [])
            if item.get("code")
        }),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


OWNER_SOURCE_PLATFORM = "platform"


def _owner_namespace_id(namespace_id: str | None) -> str | None:
    """Normalise the owning namespace (V52 `ontology_version.namespace_id`).

    The column is a uuid and NULL is a valid value ("not attributed yet"), so an
    absent namespace stays absent instead of being invented. A value that is
    present but not a uuid is a caller bug and fails loudly: silently storing
    NULL would make "no namespace" indistinguishable from "wrong namespace".
    """
    if namespace_id is None or not str(namespace_id).strip():
        return None
    try:
        return str(uuid.UUID(str(namespace_id).strip()))
    except (TypeError, ValueError) as exc:
        raise PortError(
            code="InvalidArgument",
            message=f"namespaceId must be a UUID, got {namespace_id!r}",
            provider="platform",
            provider_code="E_ONTOLOGY_BAD_NAMESPACE_ID",
        ) from exc


def ontology_event_body(
    event_id: int,
    version_id: str,
    proposal_id: str | None,
    action: str,
    actor: str | None,
    reason: str | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Canonical body for the T-Box audit chain (same rule as fact_event)."""
    return {
        "eventId": int(event_id),
        "versionId": version_id,
        "proposalId": proposal_id,
        "action": action,
        "actor": actor,
        "reason": reason,
        "payload": payload or {},
    }


def verify_ontology_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    prev_id: int | None = None
    prev_hash = ""
    for index, record in enumerate(records):
        if index and int(record.get("prevEvent") or 0) != prev_id:
            return {
                "ok": False, "checked": index,
                "error": f"event {record['eventId']} prevEvent={record.get('prevEvent')} "
                         f"expected={prev_id}",
            }
        body = ontology_event_body(
            int(record["eventId"]), record["versionId"], record.get("proposalId"),
            record["action"], record.get("actor"), record.get("reason"),
            record.get("payload") or {},
        )
        digest = event_hash(prev_hash, body)
        if digest != record.get("hash"):
            return {"ok": False, "checked": index,
                    "error": f"event {record['eventId']} hash mismatch"}
        prev_id = int(record["eventId"])
        prev_hash = digest
    return {"ok": True, "checked": len(records)}


def _content_hash(triples: list[Any]) -> str:
    """sha256 over a deterministic canonical form of the triple set.

    S14H-P0: the previous hand-rolled blank-node labeling was not stable for
    deeply nested OWL restrictions — the same FS-LDM staging graph produced
    different hashes in the import and publish paths (expected fac7… vs
    actual 425f…), blocking publish with E_ONTOLOGY_HASH_MISMATCH. rdflib's
    SHA-256 based canonicalizer is deterministic across parses/processes.
    """
    if not triples:
        return hashlib.sha256(b"").hexdigest()
    from rdflib import Graph
    from rdflib.compare import to_isomorphic

    graph = Graph()
    for triple in triples:
        graph.add(triple)
    # graph_digest() is a 268-bit int (67 hex chars), so hash it again to fit
    # the character(64) column while keeping the value deterministic.
    digest = to_isomorphic(graph).graph_digest()
    return hashlib.sha256(f"{digest:067x}".encode("utf-8")).hexdigest()


def _row_to_version(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["version_id"],
        "semver": row["semver"],
        "status": row["status"],
        "contentHash": row["content_hash"],
        "tripleCount": row["triple_count"],
        "format": row["source_format"],
        "graph": row["graph_iri"],
        "rollbackOf": row["rollback_of"],
        "label": row["label"],
        "createdAt": row["created_at"].isoformat(),
        "publishedAt": row["published_at"].isoformat() if row["published_at"] else None,
    }


IMPORT_MAX_BYTES = 50 * 1024 * 1024
IMPORT_MAX_DEPTH = 5
DEFAULT_IMPORT_SEARCH_DIRS = (
    "/data/ontology-imports",
    "/data/ontology",
    "/data/vocab",
)
IMPORT_FORMATS = {"ttl": "turtle", "turtle": "turtle", "nt": "nt", "ntriples": "nt"}


def import_format_from_name(filename: str | None, fallback: str = "turtle") -> str:
    suffix = Path(filename or "").suffix.lstrip(".").lower()
    return IMPORT_FORMATS.get(suffix, fallback)


def _parse_position(exc: Exception, text: str) -> dict[str, Any]:
    """Real line/column from rdflib's exception; null when it cannot be derived."""
    message = str(exc)
    match = PARSE_LINE_RE.search(message)
    line: int | None = int(match.group(1)) if match else None
    if line is None:
        raw_lines = getattr(exc, "lines", None)
        if isinstance(raw_lines, int):
            line = raw_lines + 1  # rdflib counts newlines from zero
    offset = getattr(exc, "_i", None)
    column: int | None = None
    if isinstance(offset, int) and 0 <= offset <= len(text):
        column = offset - text.rfind("\n", 0, offset)
    return {
        "line": line,
        "column": column,
        "columnSource": "rdflib:_i" if column is not None else None,
    }


def build_import_document(
    raw: bytes,
    rdf_format: str = "turtle",
    target_namespace: str | None = None,
    author: str | None = None,
    change_summary: str | None = None,
    search_dirs: list[str] | None = None,
    published_graphs: dict[str, bytes] | None = None,
    shapes_dir: str | None = None,
    consistency_checker: Any = None,
    consistency_timeout_s: float = 120.0,
    shapes_provider: Any = None,
) -> tuple[dict[str, Any], Graph]:
    """G-01 third slice: parse + owl:imports closure + SHACL validation.

    Resolution order per IRI: caller-provided `published_graphs` (published /
    known versions), then local TTL/NT files under `search_dirs`, then
    unresolved. There is deliberately no network fetch: offline IRIs are
    reported as `E_IMPORTS_OFFLINE` and stay critical. SHACL runs only when
    deployed shapes exist for `target_namespace`; persistence and publish
    pointer switching stay out of this slice.
    """
    if len(raw) > IMPORT_MAX_BYTES:
        raise PortError(
            code="ResourceExhausted",
            message=f"{len(raw)} bytes exceeds the 50MB import limit",
            provider="platform",
            provider_code="E_ONTOLOGY_SOURCE_TOO_LARGE",
            details={"bytes": len(raw), "maxBytes": IMPORT_MAX_BYTES},
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PortError(
            code="InvalidArgument",
            message=f"import body is not UTF-8: {exc}",
            provider="rdflib",
            provider_code="E_ONTOLOGY_PARSE",
            details={"line": None, "column": None, "encoding": "utf-8"},
        ) from exc

    graph = Graph()
    try:
        graph.parse(data=text, format=rdf_format)
    except Exception as exc:
        position = _parse_position(exc, text)
        raise PortError(
            code="InvalidArgument",
            message=(
                f"RDF parse failed ({rdf_format})"
                + (f" at line {position['line']}" if position["line"] else "")
                + (f", column {position['column']}" if position["column"] else "")
                + f": {exc}"
            ),
            provider="rdflib",
            provider_code="E_ONTOLOGY_PARSE",
            details={"format": rdf_format, **position},
        ) from exc

    base_triples = len(graph)
    directories = [Path(item) for item in (search_dirs or DEFAULT_IMPORT_SEARCH_DIRS)]
    published = published_graphs or {}
    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    visited: set[str] = set()

    def visit(iri: str, declared_by: str, depth: int, path: frozenset[str]) -> list[str]:
        if iri in path:
            raise PortError(
                code="InvalidArgument",
                message=f"owl:imports cycle detected at {iri}",
                provider="platform",
                provider_code="E_IMPORTS_CYCLE",
                details={"iri": iri, "path": sorted(path) + [iri], "depth": depth},
            )
        if depth > IMPORT_MAX_DEPTH:
            raise PortError(
                code="InvalidArgument",
                message=f"owl:imports depth {depth} exceeds limit {IMPORT_MAX_DEPTH}",
                provider="platform",
                provider_code="E_IMPORTS_DEPTH",
                details={"iri": iri, "declaredBy": declared_by, "depth": depth},
            )
        if iri in visited:
            return []

        raw_import, source, local_file = _resolve_import_offline(iri, directories, published)
        if raw_import is None:
            unresolved.append(
                {
                    "iri": iri,
                    "declaredBy": declared_by,
                    "resolved": False,
                    "critical": True,
                    "reason": "E_IMPORTS_OFFLINE",
                    "message": "no published graph or local file found; network fetch is disabled",
                }
            )
            visited.add(iri)
            return []

        fmt = "nt" if source.endswith(".nt") else "turtle"
        try:
            before = len(graph)
            before_imports = set(graph.triples((None, OWL.imports, None)))
            graph.parse(data=raw_import.decode("utf-8"), format=fmt, publicID=iri)
            new_imports = sorted(
                {
                    str(obj)
                    for _, _, obj in set(graph.triples((None, OWL.imports, None)))
                    - before_imports
                }
            )
        except Exception as exc:
            position = _parse_position(exc, raw_import.decode("utf-8", errors="replace"))
            unresolved.append(
                {
                    "iri": iri,
                    "declaredBy": declared_by,
                    "resolved": False,
                    "critical": True,
                    "reason": "E_ONTOLOGY_PARSE",
                    "message": str(exc),
                    "line": position["line"],
                    "column": position["column"],
                }
            )
            visited.add(iri)
            return []
        visited.add(iri)
        resolved.append(
            {
                "iri": iri,
                "source": source,
                "file": local_file,
                "triples": len(graph) - before,
                "declaredBy": declared_by,
                "depth": depth,
            }
        )
        return new_imports

    queue: list[tuple[str, str, int, frozenset[str]]] = [
        (iri, "root", 1, frozenset()) for iri in child_imports_root(graph)
    ]
    while queue:
        iri, declared_by, depth, path = queue.pop(0)
        for child in visit(iri, declared_by, depth, path):
            queue.append((child, iri, depth + 1, path | {iri}))

    imports_declared = sorted(
        {str(item) for item in graph.objects(None, OWL.imports)}
        | {item["iri"] for item in resolved}
        | {item["iri"] for item in unresolved}
    )

    shacl: dict[str, Any] = {
        "shapesId": None,
        "shapesVersion": None,
        "namespace": target_namespace,
        "conforms": None,
        "violations": [],
        "violationCount": 0,
        "status": "not_deployed",
        "engine": None,
    }
    blockers: list[dict[str, Any]] = []
    if unresolved:
        blockers.append(
            {
                "code": "E_IMPORTS_UNRESOLVED",
                "message": "one or more critical owl:imports could not be resolved",
            }
        )
    if shapes_provider is not None:
        shapes = shapes_provider(target_namespace) if target_namespace else None
    else:
        shapes = _load_deployed_shapes(shapes_dir, target_namespace)
    if shapes is not None:
        shacl.update(
            {
                "shapesId": shapes["shapesId"],
                "shapesVersion": shapes["shapesVersion"],
                "status": "validated",
            }
        )
        result = _run_shacl(shapes, graph)
        shacl.update(result)
        if shacl["conforms"] is False:
            blockers.append(
                {
                    "code": "E_SHACL_VIOLATION",
                    "message": f"SHACL violations: {shacl['violationCount']}",
                }
            )
        elif shacl["status"] == "engine_missing":
            blockers.append(
                {
                    "code": "E_SHACL_ENGINE_MISSING",
                    "message": "pyshacl is not installed; SHACL was not executed",
                }
            )
        elif shacl["status"] == "bad_shapes":
            blockers.append(
                {"code": "E_SHACL_BAD_SHAPES", "message": shacl.get("error") or "bad shapes"}
            )
    else:
        blockers.append(
            {
                "code": "E_SHACL_NOT_DEPLOYED",
                "message": (
                    "no SHACL shapes are deployed for this namespace yet"
                    if target_namespace
                    else "targetNamespace is required to select deployed shapes"
                ),
            }
        )

    consistency: dict[str, Any] = {
        "checked": False,
        "consistent": None,
        "status": "not_run",
        "engine": None,
        "detail": None,
        "durationMs": None,
    }
    if not blockers:
        started = time.monotonic()
        consistency["checked"] = True
        if consistency_checker is None:
            consistency.update(
                {
                    "status": "unavailable",
                    "detail": "consistency gate is not configured",
                }
            )
            blockers.append(
                {
                    "code": "E_CONSISTENCY_UNAVAILABLE",
                    "message": "consistency gate is not configured",
                }
            )
        else:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            try:
                future = executor.submit(
                    consistency_checker, graph.serialize(format="nt").encode("utf-8")
                )
                payload = future.result(timeout=consistency_timeout_s)
            except concurrent.futures.TimeoutError:
                consistency.update(
                    {
                        "status": "timeout",
                        "detail": f"consistency check exceeded {consistency_timeout_s:.0f}s",
                    }
                )
                blockers.append(
                    {
                        "code": "E_CONSISTENCY_TIMEOUT",
                        "message": f"consistency check exceeded {consistency_timeout_s:.0f}s",
                    }
                )
            except Exception as exc:  # PortError from the real reasoner client
                provider_code = getattr(exc, "provider_code", None)
                status = "timeout" if provider_code == "E_REASONER_TIMEOUT" else "unavailable"
                code = (
                    "E_CONSISTENCY_TIMEOUT"
                    if status == "timeout"
                    else "E_CONSISTENCY_UNAVAILABLE"
                )
                consistency.update(
                    {
                        "status": status,
                        "detail": str(exc),
                        "providerCode": provider_code,
                    }
                )
                blockers.append({"code": code, "message": str(exc)})
            else:
                is_consistent = bool(payload.get("consistent"))
                detail = (
                    payload.get("unsatisfiable")
                    or payload.get("unsatisfiableClasses")
                    or payload.get("reason")
                    or payload.get("error")
                )
                if isinstance(detail, list):
                    detail = detail[0] if detail else None
                consistency.update(
                    {
                        "consistent": is_consistent,
                        "status": "consistent" if is_consistent else "inconsistent",
                        "engine": payload.get("engine")
                        or payload.get("profile")
                        or "reasoner",
                        "detail": None if is_consistent else (str(detail) if detail else "engine-reason-unknown"),
                    }
                )
                if not is_consistent:
                    blockers.append(
                        {
                            "code": "E_CONSISTENCY_FAILED",
                            "message": consistency["detail"],
                        }
                    )
            finally:
                elapsed_ms = int((time.monotonic() - started) * 1000)
                consistency["durationMs"] = elapsed_ms
                executor.shutdown(wait=False)

    reason = _pick_reason([item["code"] for item in blockers])
    result = {
        "importId": f"imp-{uuid.uuid4().hex[:12]}",
        "triples": base_triples,
        "totalTriples": len(graph),
        "classes": len(set(graph.subjects(RDF.type, OWL.Class))),
        "objectProperties": len(set(graph.subjects(RDF.type, OWL.ObjectProperty))),
        "dataProperties": len(set(graph.subjects(RDF.type, OWL.DatatypeProperty))),
        "targetNamespace": target_namespace,
        "author": author,
        "changeSummary": change_summary,
        "format": rdf_format,
        "importsDeclared": imports_declared,
        "importsResolved": resolved,
        "unresolvedImports": unresolved,
        "shacl": shacl,
        "consistency": consistency,
        "usable": not blockers,
        "reason": reason,
        "usableReasons": blockers,
        "published": False,
        "persisted": False,
        "slice": "G-01.imports+shacl+consistency",
    }
    return result, graph


def parse_import_document(
    raw: bytes,
    rdf_format: str = "turtle",
    target_namespace: str | None = None,
    author: str | None = None,
    change_summary: str | None = None,
    search_dirs: list[str] | None = None,
    published_graphs: dict[str, bytes] | None = None,
    shapes_dir: str | None = None,
    consistency_checker: Any = None,
    consistency_timeout_s: float = 120.0,
) -> dict[str, Any]:
    """Pure wrapper used by tests and read-only callers."""
    result, _graph = build_import_document(
        raw,
        rdf_format=rdf_format,
        target_namespace=target_namespace,
        author=author,
        change_summary=change_summary,
        search_dirs=search_dirs,
        published_graphs=published_graphs,
        shapes_dir=shapes_dir,
        consistency_checker=consistency_checker,
        consistency_timeout_s=consistency_timeout_s,
    )
    return result


SH = Namespace("http://www.w3.org/ns/shacl#")

_REASON_PRIORITY = [
    "E_IMPORTS_UNRESOLVED",
    "E_SHACL_VIOLATION",
    "E_CONSISTENCY_FAILED",
    "E_CONSISTENCY_TIMEOUT",
    "E_CONSISTENCY_UNAVAILABLE",
    "E_SHACL_BAD_SHAPES",
    "E_SHACL_ENGINE_MISSING",
    "E_SHACL_NOT_DEPLOYED",
]


def _pick_reason(codes: list[str]) -> str | None:
    for code in _REASON_PRIORITY:
        if code in codes:
            return code
    return None


def _namespace_segment(namespace: str) -> str:
    text = namespace.strip().rstrip(":")
    if text.startswith("urn:"):
        tail = text.split(":")[-1]
    else:
        tail = text.rstrip("/#").rsplit("/", 1)[-1].rstrip("#")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", tail) or "default"


def _shapes_digest(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def _load_deployed_shapes(
    shapes_dir: str | None, namespace: str | None
) -> dict[str, Any] | None:
    """Deployed shapes for one namespace; None means nothing is deployed."""
    if not shapes_dir or not namespace:
        return None
    directory = Path(shapes_dir) / _namespace_segment(namespace)
    files = sorted(directory.glob("*.ttl")) if directory.is_dir() else []
    if not files:
        return None
    manifest: dict[str, Any] = {}
    for name in ("manifest.json", "shapes.json"):
        candidate = directory / name
        if candidate.is_file():
            try:
                manifest = json.loads(candidate.read_text(encoding="utf-8"))
            except ValueError:
                manifest = {}
            break
    shapes_id = str(manifest.get("id") or directory.name)
    version = str(manifest.get("version") or _shapes_digest(files))
    graph = Graph()
    try:
        for path in files:
            graph.parse(path.as_posix(), format="turtle")
    except Exception as exc:
        return {
            "graph": None,
            "error": str(exc),
            "shapesId": shapes_id,
            "shapesVersion": version,
            "files": [item.name for item in files],
        }
    return {
        "graph": graph,
        "shapesId": shapes_id,
        "shapesVersion": version,
        "files": [item.name for item in files],
        "digest": _shapes_digest(files),
    }


def _node_value(report: Graph, node: Any, predicate: URIRef) -> str | None:
    value = next(report.objects(node, predicate), None)
    if isinstance(value, URIRef):
        return str(value)
    if value is not None and not isinstance(value, BNode):
        return str(value)
    return None


def _extract_violations(report: Graph) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for node in report.subjects(RDF.type, SH.ValidationResult):
        violations.append(
            {
                "focusNode": _node_value(report, node, SH.focusNode),
                "path": _node_value(report, node, SH.resultPath),
                "constraint": _node_value(report, node, SH.sourceConstraintComponent),
                "message": _node_value(report, node, SH.resultMessage),
                "severity": _node_value(report, node, SH.resultSeverity),
                "sourceShape": _node_value(report, node, SH.sourceShape),
            }
        )
    violations.sort(key=lambda item: str(item.get("focusNode") or ""))
    return violations


def _run_shacl(shapes: dict[str, Any], data_graph: Graph) -> dict[str, Any]:
    if shapes.get("graph") is None:
        return {
            "conforms": None,
            "violations": [],
            "violationCount": 0,
            "status": "bad_shapes",
            "error": shapes.get("error"),
            "engine": None,
        }
    try:
        import pyshacl
        from pyshacl import validate
    except ImportError as exc:
        return {
            "conforms": None,
            "violations": [],
            "violationCount": 0,
            "status": "engine_missing",
            "error": str(exc),
            "engine": {"name": "pyshacl", "status": "missing"},
        }
    engine = {"name": "pyshacl", "version": str(getattr(pyshacl, "__version__", "unknown"))}
    try:
        conforms, report_graph, _ = validate(
            data_graph,
            shacl_graph=shapes["graph"],
            inference="rdfs",
            abort_on_first=False,
        )
    except Exception as exc:
        return {
            "conforms": None,
            "violations": [],
            "violationCount": 0,
            "status": "error",
            "error": str(exc),
            "engine": engine,
        }
    violations = _extract_violations(report_graph)
    return {
        "conforms": bool(conforms),
        "violations": violations,
        "violationCount": len(violations),
        "status": "validated",
        "engine": engine,
    }


IMPORT_STAGING_PREFIX = "urn:platform:graph:import:"


def persist_import(
    result: dict[str, Any],
    graph: Graph,
    raw: bytes,
    meta: Any,
    graph_store: Any,
    graph_iri: str | None = None,
) -> dict[str, Any]:
    """Write the merged graph to a staging graph, then record the import.

    Order matters: the graph is written first so a graph failure never leaves
    a record behind. If the record insert fails the staging graph is dropped,
    so there is no half-import. Nothing here touches a published pointer.
    """
    import_id = result["importId"]
    staging = graph_iri or f"{IMPORT_STAGING_PREFIX}{import_id}"
    digest = hashlib.sha256(raw).hexdigest()
    version_id = f"ont-draft-{digest[:12]}"
    payload = {**result, "versionId": version_id, "stagingGraph": staging}

    try:
        graph_store.replace_graph(staging, graph.serialize(format="nt").encode("utf-8"), "nt")
    except Exception as exc:
        raise PortError(
            code="Unavailable",
            message=f"cannot write staging graph {staging}: {exc}",
            provider="platform",
            provider_code="E_ONTOLOGY_STAGE_FAILED",
            details={"graph": staging, "cause": str(exc)},
        ) from exc

    shacl = result.get("shacl") or {}
    try:
        with meta.tx() as tx:
            rows = tx.execute_returning(
                """
                INSERT INTO platform.ontology_import (
                    import_id, version_id, target_namespace, author, change_summary,
                    base_triples, total_triples, classes, object_properties, data_properties,
                    shapes_id, shapes_version, conforms, violation_count,
                    usable, reason, source_sha256, staging_graph, payload
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING created_at
                """,
                (
                    import_id,
                    version_id,
                    result.get("targetNamespace"),
                    result.get("author") or "unknown",
                    result.get("changeSummary"),
                    int(result.get("triples") or 0),
                    int(result.get("totalTriples") or 0),
                    int(result.get("classes") or 0),
                    int(result.get("objectProperties") or 0),
                    int(result.get("dataProperties") or 0),
                    shacl.get("shapesId"),
                    shacl.get("shapesVersion"),
                    shacl.get("conforms"),
                    int(shacl.get("violationCount") or 0),
                    bool(result.get("usable")),
                    result.get("reason"),
                    digest,
                    staging,
                    Jsonb(payload),
                ),
            )
    except Exception as exc:
        try:
            graph_store.update(f"DROP SILENT GRAPH <{staging}>")
        except Exception:
            pass
        raise PortError(
            code="Unavailable",
            message=f"cannot record import {import_id}: {exc}",
            provider="postgres",
            provider_code="E_ONTOLOGY_RECORD_FAILED",
            details={"importId": import_id, "stagingDropped": True},
        ) from exc

    created_at = rows[0]["created_at"]
    result.update(
        {
            "versionId": version_id,
            "stagingGraph": staging,
            "sourceSha256": digest,
            "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
            "persisted": True,
        }
    )
    return result


def get_import_record(meta: Any, import_id: str) -> dict[str, Any] | None:
    rows = meta.query(
        """
        SELECT import_id, version_id, target_namespace, author, change_summary,
               base_triples, total_triples, classes, object_properties, data_properties,
               shapes_id, shapes_version, conforms, violation_count,
               usable, reason, source_sha256, staging_graph, created_at
          FROM platform.ontology_import
         WHERE import_id = %s
        """,
        (import_id,),
    )
    if not rows:
        return None
    row = dict(rows[0])
    created = row.get("created_at")
    if hasattr(created, "isoformat"):
        row["created_at"] = created.isoformat()
    return row


IMPORT_TBOX_PREFIX = "urn:platform:graph:tbox:"


def _import_version_id(import_id: str) -> str:
    """Deterministic version id so a repeated publish returns the same one."""
    return "ont-" + hashlib.sha256(f"g01-import:{import_id}".encode("utf-8")).hexdigest()[:12]


def _find_version_by_hash(meta: Any, content_hash: str) -> dict[str, Any] | None:
    """Latest version whose canonical hash equals ``content_hash`` (OQ-65).

    Prefer the currently published one, then the most recent superseded/approved
    version, then a draft, so a forward publish targets a stable historical row.
    """
    rows = meta.query(
        """
        SELECT version_id, status, content_hash, graph_iri, triple_count, semver
        FROM platform.ontology_version
        WHERE content_hash = %s
        ORDER BY created_at DESC
        """,
        (content_hash,),
    )
    if not rows:
        return None
    priority = {"published": 0, "superseded": 1, "approved": 2, "draft": 3}
    return min(rows, key=lambda row: (priority.get(row["status"], 9),))


def _compact_diff(diff: dict[str, Any], example_limit: int = 5) -> dict[str, Any]:
    summary = diff.get("summary") or {}
    return {
        "from": diff.get("from"),
        "to": diff.get("to"),
        "addedTriples": int(summary.get("addedTriples") or 0),
        "removedTriples": int(summary.get("removedTriples") or 0),
        "addedClasses": len(summary.get("addedClasses") or []),
        "removedClasses": len(summary.get("removedClasses") or []),
        "addedProperties": len(summary.get("addedProperties") or []),
        "removedProperties": len(summary.get("removedProperties") or []),
        "examples": {
            "addedClasses": (summary.get("addedClasses") or [])[:example_limit],
            "removedClasses": (summary.get("removedClasses") or [])[:example_limit],
            "addedProperties": (summary.get("addedProperties") or [])[:example_limit],
            "removedProperties": (summary.get("removedProperties") or [])[:example_limit],
        },
        "breaking": bool(diff.get("breaking")),
        "breakingItems": (diff.get("breakingItems") or [])[:example_limit],
    }


def _import_impact(
    graph_store: Any, diff: dict[str, Any], abox_graphs: list[str]
) -> dict[str, Any]:
    """Existing entities/graphs touched by the change (removed classes + domain/range)."""
    summary = diff.get("summary") or {}
    removed_instances = summary.get("removedClassInstances") or []
    affected_iris = [str(item["class"]) for item in removed_instances]
    affected_iris += [str(item["property"]) for item in summary.get("domainChanges") or []]
    affected_iris += [str(item["property"]) for item in summary.get("rangeChanges") or []]

    affected_triples = 0
    affected_graphs = 0
    if affected_iris:
        values = " ".join(f"<{iri}>" for iri in sorted(set(affected_iris)))
        for graph_iri in abox_graphs:
            query = (
                f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{graph_iri}> {{ ?s ?p ?o . "
                f"FILTER(?s IN ({values}) || ?o IN ({values})) }} }}"
            )
            try:
                payload = graph_store.query(query)
                count = int(payload["bindings"][0]["values"]["n"]["value"])
            except Exception:
                continue
            if count:
                affected_graphs += 1
                affected_triples += count
    return {
        "addedTriples": int(summary.get("addedTriples") or 0),
        "removedTriples": int(summary.get("removedTriples") or 0),
        "affectedEntities": sum(int(item.get("instances") or 0) for item in removed_instances),
        "affectedGraphs": affected_graphs,
        "affectedTriples": affected_triples,
        "aboxGraphs": list(abox_graphs),
    }


def publish_import(
    meta: Any,
    graph_store: Any,
    objects: Any,
    registry: Any,
    import_id: str,
    *,
    dry_run: bool = True,
    actor: str = "operator",
    change_summary: str | None = None,
    acknowledge_breaking: bool = False,
    abox_graphs: list[str] | None = None,
    publish_existing: bool = False,
    expected_version_id: str | None = None,
    purpose: str | None = None,
    purpose_verified: bool | None = None,
    purpose_status: str | None = None,
    remote_addr: str | None = None,
    namespace_id: str | None = None,
) -> dict[str, Any]:
    """G-01 publish: dry-run diff/impact, then a governed version publish.

    Nothing is renamed or overwritten: the staging graph is copied into a new
    versioned graph ``urn:platform:graph:tbox:{versionId}`` and the record is
    marked published only by the pointer switch. The old version is kept.
    """
    record = get_import_record(meta, import_id)
    if record is None:
        raise PortError(
            code="NotFound",
            message=f"import {import_id} not found",
            provider="platform",
            provider_code="E_ONTOLOGY_IMPORT_NOT_FOUND",
            details={"importId": import_id},
        )

    staging = record["staging_graph"]
    # Only an explicit uuid is stored. `record["target_namespace"]` is the
    # ontology id/IRI the staging request named, not a namespace uuid, so it is
    # never converted into one here.
    owner_namespace = _owner_namespace_id(namespace_id)
    version_id = _import_version_id(import_id)
    tbox_graph = f"{IMPORT_TBOX_PREFIX}{version_id}"
    pointer = registry.current()
    previous_version = pointer["versionId"] if pointer else None
    previous_graph = pointer["graph"] if pointer else None

    try:
        staging_nt = graph_store.export_graph(staging)
    except PortError as exc:
        raise PortError(
            code="Unavailable",
            message=f"staging graph {staging} is unavailable: {exc.message}",
            provider="platform",
            provider_code="E_ONTOLOGY_STAGE_MISSING",
            details={"importId": import_id, "stagingGraph": staging},
        ) from exc
    if not staging_nt.strip():
        raise PortError(
            code="NotFound",
            message=f"staging graph {staging} is empty",
            provider="platform",
            provider_code="E_ONTOLOGY_STAGE_MISSING",
            details={"importId": import_id, "stagingGraph": staging},
        )

    # Canonical hash is computed before the diff so `publish_existing` can look
    # up a version that already holds exactly this content (OQ-65 forward publish).
    triples = parse_rdf(staging_nt, "nt")
    content_hash = _content_hash(list(triples))
    canonical_version: dict[str, Any] | None = None
    if publish_existing:
        canonical_version = _find_version_by_hash(meta, content_hash)
        if canonical_version is None:
            raise PortError(
                code="NotFound",
                message=(
                    "publishExisting=true but no version has the same canonical content hash"
                ),
                provider="platform",
                provider_code="E_ONTOLOGY_EXISTING_NOT_FOUND",
                details={"importId": import_id, "canonicalHash": content_hash},
            )

    diff = registry.diff_graphs(
        previous_graph, staging,
        from_version_id=previous_version, to_version_id=version_id,
    )
    impact = _import_impact(graph_store, diff, list(abox_graphs or []))
    base: dict[str, Any] = {
        "importId": import_id,
        "versionId": version_id,
        "previousVersionId": previous_version,
        "pointer": previous_graph,
        "dryRun": dry_run,
        "diff": _compact_diff(diff),
        "impact": impact,
        "usable": bool(record["usable"]),
        "reason": record["reason"],
        "canonicalEqualTo": canonical_version["version_id"] if canonical_version else None,
    }
    # --- G8 terms gate ---
    # off keeps the payload unchanged unless the non-configurable vocab-zero
    # guard fires; warn/block evaluate the staged T-Box before any row is
    # written. The guard compares the *effective* term set against the stored
    # high-water mark (not the current pointer), so consecutive collapses are
    # caught as well, and purpose=smoke with a verified internal token is the only
    # exemption (missing/invalid/unconfigured token is recorded as forged and the
    # zero-term publish is still blocked).
    terms_gate: dict[str, Any] | None = None
    terms_cfg = getattr(registry, "_terms_gate", None)
    if terms_cfg is not None:
        if purpose is not None and purpose_verified is None:
            # 进程内自检探针（platform smoke-sN）无法带 HTTP 头：从同一环境变量
            # 取 token，走同样的常量时间比较；未配置 => fail-closed。
            env_ctx = termgate.smoke_env_context(
                purpose, env_name=getattr(terms_cfg, "smoke_token_env", None),
                remote_addr=remote_addr,
            )
            purpose_verified = env_ctx["purpose_verified"]
            purpose_status = env_ctx["purpose_status"]
        baseline: dict[str, Any] | None = None
        baseline_error: str | None = None
        high_water: dict[str, Any] | None = None
        try:
            baseline = termgov.graph_coverage(
                SimpleNamespace(ontology=registry, graph=graph_store)
            )
        except Exception as exc:  # observability must not break publishing
            baseline_error = f"{type(exc).__name__}: {exc}"
        try:
            high_water = _term_high_water(registry, meta)
        except Exception as exc:
            baseline_error = baseline_error or f"{type(exc).__name__}: {exc}"
        terms_gate = termgate.evaluate_content(
            staging_nt.decode("utf-8"),
            "nt",
            terms_cfg,
            baseline=baseline,
            high_water=high_water,
            context={
                "importId": import_id,
                "versionId": version_id,
                "source": "tbox-publish",
                "dryRun": dry_run,
                "actor": actor,
                "path": "POST /ontology/import",
                "purpose": purpose,
                "purposeVerified": purpose_verified,
                "purposeStatus": purpose_status,
                "remoteAddr": remote_addr,
                "baselineError": baseline_error,
            },
        )
        if terms_gate is not None:
            termgate.remember(registry, terms_gate)
            base["termsGate"] = terms_gate
    # --- end G8 terms gate ---
    if dry_run:
        return {
            **base,
            "published": False,
            "publishedAt": None,
            "publishExisting": bool(publish_existing),
        }

    # 前置条件：import-publish 与其他发布入口用同一口径，避免“换个端点绕过”。
    registry._assert_pointer_precondition(
        version_id, expected_version_id, previous_version, actor,
        change_summary or f"G-01 import {import_id}", "import-publish",
    )

    if not record["usable"]:
        raise PortError(
            code="Conflict",
            message=f"import {import_id} is not usable: {record['reason']}",
            provider="platform",
            provider_code="E_IMPORT_NOT_USABLE",
            details={"importId": import_id, "reason": record["reason"], "usable": False},
        )

    # --- G8 terms gate ---
    if terms_gate is not None and terms_gate.get("blocked"):
        guard = terms_gate.get("vocabGuard") or {}
        forged = next(
            (item for item in (terms_gate.get("findings") or [])
             if item.get("code") == termgate.VOCAB_ZERO_FORGED_CODE),
            None,
        )
        unconfigured = guard.get("tokenStatus") == "unconfigured"
        # 被拒也要进哈希链：版本行不会产生，但绕过尝试本身必须可审计。
        registry.record_publish_rejection(
            version_id, None, actor, "term gate blocked publish", terms_gate,
            mode="import", path="POST /ontology/import",
        )
        raise PortError(
            code="Conflict",
            message=(
                f"term gate blocked publish: {terms_gate['blocking']} blocking finding(s)"
                + (
                    "；smoke token 未配置，已按 fail-closed 处理（token 环境变量未配置时"
                    "一律拒绝豁免）"
                    if unconfigured
                    else ""
                )
            ),
            provider="platform",
            provider_code=termgate.E_TERM_GATE_BLOCKED,
            details={
                "importId": import_id,
                "versionId": version_id,
                "gate": terms_gate["gate"],
                "verdict": terms_gate["verdict"],
                "blocking": terms_gate["blocking"],
                "warnings": terms_gate["warnings"],
                "problems": terms_gate["findings"],
                "vocabGuard": terms_gate.get("vocabGuard"),
                "exemptionRejected": forged.get("message") if forged else None,
                "allowed": [
                    "fix the blocking findings and re-import the T-Box",
                    "publish a T-Box version that still carries the MetricScheme terms",
                    "a self-check probe must pass purpose=smoke with the X-Smoke-Token "
                    "header issued by the operator; the exemption is recorded in the "
                    "evidence pack and the ontology_event audit chain",
                ],
            },
        )
    # --- end G8 terms gate ---
    gate_kwargs = {"extra_gates": {"terms": terms_gate}} if terms_gate is not None else {}

    with meta.advisory_lock(f"g01:import-publish:{import_id}") as acquired:
        if not acquired:
            raise PortError(
                code="Aborted",
                message=f"another publish is running for import {import_id}",
                provider="platform",
                provider_code="E_IMPORT_PUBLISH_BUSY",
                retryable=True,
                details={"importId": import_id},
            )

        if publish_existing:
            # OQ-65: activate the version that already holds this canonical
            # content. Same governance path: SHACL + consistency + breaking +
            # materialization all run; only the version/graph are reused.
            target_id = canonical_version["version_id"]
            summary = change_summary or f"G-01 import {import_id} (publish existing)"
            published = registry.publish(
                target_id,
                None,
                acknowledge_breaking=acknowledge_breaking,
                actor=actor,
                reason=summary,
                activate_existing=True,
                expected_version_id=expected_version_id,
                purpose=purpose,
                purpose_verified=purpose_verified,
                purpose_status=purpose_status,
                remote_addr=remote_addr,
                **gate_kwargs,
            )
            return {
                **base,
                "versionId": target_id,
                "canonicalEqualTo": target_id,
                "previousVersionId": published.get("previousVersionId"),
                "pointer": published.get("graph"),
                "published": True,
                "publishedAt": published.get("publishedAt"),
                "publishedBy": actor,
                "mode": "activate_existing",
                "proposalId": published.get("proposalId"),
                "gates": published.get("gates") or {},
                "idempotent": bool(published.get("idempotent")),
                "unchanged": bool(published.get("unchanged")),
            }

        existing = registry._fetch(version_id)
        if existing and existing["status"] in ("published", "superseded"):
            proposals = meta.query(
                "SELECT against_version FROM platform.ontology_proposal "
                "WHERE version_id = %s ORDER BY created_at LIMIT 1",
                (version_id,),
            )
            published_at = existing["published_at"]
            if terms_cfg is not None:
                # Repeat publish of content that is already published: the pointer
                # did not move, but the mark should still reflect this effective
                # term set (idempotent re-runs must never lose the baseline).
                try:
                    raise_term_high_water(
                        meta,
                        termgov.measure_graph(
                            SimpleNamespace(graph=graph_store), existing["graph_iri"]
                        ),
                        version_id,
                        existing["graph_iri"],
                    )
                except Exception as exc:
                    log.warning(
                        "term high-water mark not raised",
                        extra={"event": {"event": "term_high_water_failed",
                                         "version_id": version_id, "error": str(exc)}},
                    )
            return {
                **base,
                "previousVersionId": (
                    proposals[0]["against_version"] if proposals else previous_version
                ),
                "pointer": previous_graph,
                "published": True,
                "publishedAt": (
                    published_at.isoformat() if hasattr(published_at, "isoformat") else published_at
                ),
                "idempotent": True,
            }

        source_key = f"sources/{content_hash}.ttl"
        if not existing:
            objects.put(
                ONTOLOGY_BUCKET,
                source_key,
                staging_nt,
                "text/turtle",
                {"kind": "ontology_source", "content_hash": content_hash, "importId": import_id},
            )
            try:
                graph_store.replace_graph(tbox_graph, staging_nt, "nt")
            except Exception as exc:
                raise PortError(
                    code="Unavailable",
                    message=f"cannot write version graph {tbox_graph}: {exc}",
                    provider="platform",
                    provider_code="E_ONTOLOGY_STAGE_FAILED",
                    details={"graph": tbox_graph, "cause": str(exc)},
                ) from exc
            count = graph_store.count_graph(tbox_graph)
            if count != len(triples):
                graph_store.update(f"DROP SILENT GRAPH <{tbox_graph}>")
                raise PortError(
                    code="DataLoss",
                    message=f"version graph holds {count} triples, expected {len(triples)}",
                    provider="platform",
                    provider_code="E_ONTOLOGY_TRIPLE_MISMATCH",
                    details={"graph": tbox_graph, "count": count, "expected": len(triples)},
                )
            try:
                with meta.tx() as tx:
                    tx.execute(
                        """
                        INSERT INTO platform.ontology_version
                          (version_id, semver, status, content_hash, triple_count,
                           source_format, source_key, graph_iri, label,
                           namespace_id, attribution_source)
                        VALUES (%s, '0.0.0', 'draft', %s, %s, 'turtle', %s, %s, %s, %s, %s)
                        """,
                        (
                            version_id, content_hash, len(triples), source_key,
                            tbox_graph, f"G-01 import {import_id}",
                            owner_namespace,
                            OWNER_SOURCE_PLATFORM if owner_namespace else None,
                        ),
                    )
                    registry._append_event(
                        tx, version_id, None, "imported", actor, None,
                        {
                            "importId": import_id,
                            "stagingGraph": staging,
                            "sourceSha256": record["source_sha256"],
                            "triples": len(triples),
                        },
                    )
            except Exception as exc:
                try:
                    graph_store.update(f"DROP SILENT GRAPH <{tbox_graph}>")
                except Exception:
                    pass
                raise PortError(
                    code="Unavailable",
                    message=f"cannot record version {version_id}: {exc}",
                    provider="postgres",
                    provider_code="E_ONTOLOGY_RECORD_FAILED",
                    details={"versionId": version_id, "graphDropped": True},
                ) from exc

        summary = change_summary or f"G-01 import {import_id}"
        proposal = registry.propose(version_id, summary, actor=actor)
        registry.approve(proposal["proposalId"], actor=actor, reason=summary)
        published = registry.publish(
            version_id,
            proposal["proposalId"],
            acknowledge_breaking=acknowledge_breaking,
            actor=actor,
            reason=summary,
            expected_version_id=expected_version_id,
            purpose=purpose,
            purpose_verified=purpose_verified,
            purpose_status=purpose_status,
            remote_addr=remote_addr,
            **gate_kwargs,
        )
        return {
            **base,
            "previousVersionId": previous_version,
            "pointer": tbox_graph,
            "published": True,
            "publishedAt": published.get("publishedAt"),
            "proposalId": proposal["proposalId"],
            "gates": published.get("gates") or {},
            "idempotent": False,
        }


def child_imports_root(graph: Graph) -> list[str]:
    return sorted({str(item) for item in graph.objects(None, OWL.imports)})


def _resolve_import_offline(
    iri: str, directories: list[Path], published: dict[str, bytes]
) -> tuple[bytes | None, str, str | None]:
    """Published graph first, then a local file named after the IRI tail."""
    if iri in published:
        return published[iri], "published", None
    tail = iri.rstrip("/#").rsplit("/", 1)[-1]
    if tail:
        for directory in directories:
            for suffix in (".ttl", ".nt", ".owl", ".rdf"):
                candidate = directory / f"{tail}{suffix}"
                if candidate.is_file():
                    return candidate.read_bytes(), "local-file", candidate.name
    return None, "", None


class OntologyRegistry:
    port = "OntologyRegistry"

    def __init__(
        self,
        metadata: MetadataPg,
        graph: OxigraphHttpStore,
        objects: LayeredObjectStore,
        config: OntologyConfig,
    ) -> None:
        self._meta = metadata
        self._graph = graph
        self._objects = objects
        self._config = config
        # S11 governance dependencies. The legacy direct publish path (used by
        # bootstrap/S1) stays dependency-free; governed publish requires all of
        # them and fails closed when any is missing.
        self._validator: Any = None
        self._reasoner: Any = None
        self._materializer: Any = None
        self._abox_graphs: list[str] = []
        self._reason_profile = "EL"
        # --- G8 terms gate ---
        # None = no gate (direct/legacy registries); assembly installs the
        # configured TermsConfig so publish honours terms.gate.
        self._terms_gate: TermsConfig | None = None
        self._last_terms_gate: dict[str, Any] | None = None
        # --- end G8 terms gate ---

    # --- G8 terms gate ---
    def set_terms_gate(self, config: TermsConfig | None) -> None:
        self._terms_gate = config
    # --- end G8 terms gate ---

    def set_governance(
        self,
        *,
        validator: Any = None,
        reasoner: Any = None,
        materializer: Any = None,
        abox_graphs: list[str] | None = None,
        reason_profile: str = "EL",
    ) -> None:
        self._validator = validator
        self._reasoner = reasoner
        self._materializer = materializer
        self._abox_graphs = list(abox_graphs or [])
        self._reason_profile = reason_profile

    def manifest(self) -> Manifest:
        return Manifest(
            provider="pg+oxigraph",
            port=self.port,
            capabilities=[
                "ontology.import",
                "ontology.publish",
                "ontology.rollback",
                "ontology.get",
                "ontology.list",
                "ontology.pointer",
                "ontology.propose",
                "ontology.approve",
                "ontology.diff",
                "ontology.publish.governed",
                "ontology.rollbackTo",
                "ontology.export",
                "ontology.audit",
            ],
            notes={
                "slice": "S12",
                "gates": ["shacl", "consistency", "breaking-acknowledge"],
                "publish": "no direct path: omitted proposalId becomes an implicit gated proposal",
                "rollback": "rollbackTo switches the pointer; both graphs are kept",
                "pointer": POINTER_NAME,
            },
        )

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _error(code: str, detail: str, key: str, hint: str = "") -> PlatformError:
        return PlatformError(
            code=code, detail=detail, stage="ontology", key=key,
            hint=hint, exit_code=EXIT_CONFIG,
        )

    def _load_source(self, path: str) -> tuple[bytes, str, list[Any]]:
        source = Path(path)
        if not source.is_file():
            raise self._error(
                "E_ONTOLOGY_SOURCE_MISSING",
                f"ontology source file not found: {source}",
                key="file",
                hint="pass --file or mount it under /data",
            )
        raw = source.read_bytes()
        if len(raw) > self._config.max_source_bytes:
            raise self._error(
                "E_ONTOLOGY_SOURCE_TOO_LARGE",
                f"{len(raw)} bytes exceeds ontology.max_source_bytes={self._config.max_source_bytes}",
                key="ontology.max_source_bytes",
            )
        rdf_format = self._detect_format(source.suffix)
        try:
            triples = parse_rdf(raw, rdf_format)
        except PortError as exc:
            raise self._error(
                "E_ONTOLOGY_PARSE", exc.message, key="file", hint="fix the Turtle/TriG source"
            ) from exc
        return raw, rdf_format, triples

    @staticmethod
    def _detect_format(suffix: str) -> str:
        return "trig" if suffix.lower() in (".trig",) else "turtle"

    def _fetch(self, version_id: str) -> dict[str, Any] | None:
        rows = self._meta.query(
            """
            SELECT version_id, semver, status, content_hash, triple_count, source_format,
                   source_key, graph_iri, rollback_of, label, created_at, published_at,
                   namespace_id, attribution_source
              FROM platform.ontology_version
             WHERE version_id = %s
            """,
            (version_id,),
        )
        return rows[0] if rows else None

    def _require(self, version_id: str) -> dict[str, Any]:
        row = self._fetch(version_id)
        if row is None:
            raise PortError(
                code="NotFound",
                message=f"ontology version not found: {version_id}",
                provider="postgres",
                provider_code="E_ONTOLOGY_VERSION_NOT_FOUND",
            )
        return row

    def _pointer(self) -> dict[str, Any] | None:
        rows = self._meta.query(
            """
            SELECT p.name, p.version_id, p.updated_at, v.semver, v.content_hash, v.graph_iri
              FROM platform.graph_pointer p
              JOIN platform.ontology_version v ON v.version_id = p.version_id
             WHERE p.name = %s
            """,
            (POINTER_NAME,),
        )
        if not rows:
            return None
        row = rows[0]
        return {
            "name": row["name"],
            "versionId": row["version_id"],
            "semver": row["semver"],
            "contentHash": row["content_hash"],
            "graph": row["graph_iri"],
            "updatedAt": row["updated_at"].isoformat(),
        }

    # ---- audit chain -----------------------------------------------------

    def _last_publish_previous(self, version_id: str) -> str | None:
        """Previous version recorded on this version's latest published event."""
        rows = self._meta.query(
            "SELECT payload FROM platform.ontology_event "
            "WHERE version_id = %s AND action = 'published' "
            "ORDER BY event_id DESC LIMIT 1",
            (version_id,),
        )
        if not rows:
            return None
        payload = rows[0]["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return payload.get("previousVersionId") or payload.get("previous")

    def _append_event(
        self, tx: Any, version_id: str, proposal_id: str | None, action: str,
        actor: str | None, reason: str | None, payload: dict[str, Any],
    ) -> int:
        tx.execute("SELECT pg_advisory_xact_lock(hashtext('platform:ontology:event'))")
        last = tx.query(
            "SELECT event_id, hash FROM platform.ontology_event "
            "ORDER BY event_id DESC LIMIT 1"
        )
        prev_id = int(last[0]["event_id"]) if last else None
        prev_hash = last[0]["hash"] if last else ""
        row = tx.execute_returning(
            """
            INSERT INTO platform.ontology_event
              (version_id, proposal_id, action, actor, reason, payload, prev_event)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING event_id
            """,
            (version_id, proposal_id, action, actor, reason, Jsonb(payload), prev_id),
        )
        event_id = int(row[0]["event_id"])
        body = ontology_event_body(
            event_id, version_id, proposal_id, action, actor, reason, payload
        )
        digest = event_hash(prev_hash, body)
        tx.execute(
            "UPDATE platform.ontology_event SET hash = %s WHERE event_id = %s",
            (digest, event_id),
        )
        return event_id

    def _assert_pointer_precondition(
        self,
        version_id: str,
        expected_version_id: str | None,
        actual_version_id: str | None,
        actor: str,
        reason: str | None,
        operation: str,
    ) -> None:
        """可选的前置条件：指针必须仍是调用方看到的版本。

        ``expected_version_id`` 为 None 时保持原行为（调用方无需改动）。
        不匹配时不写指针，只追加一条审计事件，然后返回 409。
        """
        if expected_version_id is None or actual_version_id == expected_version_id:
            return
        with self._meta.tx() as tx:
            self._append_event(
                tx,
                version_id,
                None,
                "pointer_precondition_rejected",
                actor,
                reason or "expectedVersionId mismatch",
                {
                    "operation": operation,
                    "expectedVersionId": expected_version_id,
                    "actualVersionId": actual_version_id,
                },
            )
        raise PortError(
            code="Conflict",
            message=(
                f"tbox/current precondition failed: expected {expected_version_id}, "
                f"actual {actual_version_id or 'none'}"
            ),
            provider="platform",
            provider_code="E_ONTOLOGY_POINTER_PRECONDITION",
            details={
                "expectedVersionId": expected_version_id,
                "actualVersionId": actual_version_id,
                "operation": operation,
            },
        )

    def record_publish_rejection(
        self,
        version_id: str,
        proposal_id: str | None,
        actor: str | None,
        reason: str | None,
        guard: dict[str, Any],
        *,
        mode: str,
        path: str,
    ) -> int | None:
        """Append a *blocked* publish to the hash-chained ``ontology_event`` log.

        A rejected publish leaves no version row, which used to mean the audit
        chain stayed silent — the only trace was the non-chained evidence pack.
        ``publish_blocked`` answers "did anyone try to bypass the guard, how
        many times, from where" and carries the same decision fields as the
        allow path (purpose / tokenStatus / purposeVerified / remoteAddr /
        verdict / baseline / current / rejected reason). Never token material.
        """
        vocab = guard.get("vocabGuard") or {}
        forged = next(
            (item for item in (guard.get("findings") or [])
             if item.get("code") == termgate.VOCAB_ZERO_FORGED_CODE),
            None,
        )
        payload = {
            "mode": mode,
            "path": path,
            "rejected": True,
            "gate": guard.get("gate"),
            "verdict": guard.get("verdict"),
            "vocabGuard": vocab,
            "findings": guard.get("findings") or [],
            "exemptionRejected": forged.get("message") if forged else None,
            "purpose": vocab.get("purpose"),
            "purposeVerified": vocab.get("purposeVerified"),
            "tokenStatus": vocab.get("tokenStatus"),
            "remoteAddr": vocab.get("remoteAddr"),
            "baseline": vocab.get("highWater"),
            "current": vocab.get("effective"),
            "terms": _term_audit_payload({"terms": guard}),
        }
        try:
            with self._meta.tx() as tx:
                return self._append_event(
                    tx, version_id, proposal_id, PUBLISH_BLOCKED_ACTION,
                    actor, reason, payload,
                )
        except Exception:  # 审计写入失败不能把原始阻断变成 500
            log.exception(
                "failed to append publish_blocked audit event for %s", version_id
            )
            return None

    def ensure_chain(self) -> dict[str, Any]:
        """Backfill prev_event/hash for events written before S11 (none expected)."""
        with self._meta.tx() as tx:
            rows = tx.query(
                "SELECT event_id, version_id, proposal_id, action, actor, reason, "
                "payload, prev_event, hash FROM platform.ontology_event ORDER BY event_id"
            )
            prev_id: int | None = None
            prev_hash = ""
            for row in rows:
                event_id = int(row["event_id"])
                if row["prev_event"] != prev_id or not row["hash"]:
                    tx.execute(
                        "UPDATE platform.ontology_event SET prev_event = %s WHERE event_id = %s",
                        (prev_id, event_id),
                    )
                body = ontology_event_body(
                    event_id, row["version_id"], row["proposal_id"], row["action"],
                    row["actor"], row["reason"], row["payload"] or {},
                )
                digest = event_hash(prev_hash, body)
                if row["hash"] != digest:
                    tx.execute(
                        "UPDATE platform.ontology_event SET hash = %s WHERE event_id = %s",
                        (digest, event_id),
                    )
                prev_id = event_id
                prev_hash = digest
        return {"ok": True}

    def events(self, version_id: str | None = None, limit: int = 500) -> dict[str, Any]:
        self.ensure_chain()
        clauses = ""
        params: list[Any] = []
        if version_id:
            clauses = "WHERE e.version_id = %s"
            params.append(version_id)
        rows = self._meta.query(
            f"""
            SELECT e.event_id, e.version_id, e.proposal_id, e.action, e.actor, e.reason,
                   e.payload, e.prev_event, e.hash, e.created_at
              FROM platform.ontology_event e
              {clauses}
             ORDER BY e.event_id DESC
             LIMIT %s
            """,
            tuple(params + [limit]),
        )
        items = [
            {
                "eventId": int(row["event_id"]),
                "versionId": row["version_id"],
                "proposalId": row["proposal_id"],
                "action": row["action"],
                "actor": row["actor"],
                "reason": row["reason"],
                "payload": row["payload"] or {},
                "prevEvent": int(row["prev_event"]) if row["prev_event"] else None,
                "hash": row["hash"],
                "createdAt": row["created_at"].isoformat(),
            }
            for row in rows
        ]
        return {"items": items, "count": len(items)}

    def verify_events(self) -> dict[str, Any]:
        self.ensure_chain()
        rows = self._meta.query(
            """
            SELECT event_id, version_id, proposal_id, action, actor, reason,
                   payload, prev_event, hash
              FROM platform.ontology_event ORDER BY event_id
            """
        )
        records = [
            {
                "eventId": int(row["event_id"]),
                "versionId": row["version_id"],
                "proposalId": row["proposal_id"],
                "action": row["action"],
                "actor": row["actor"],
                "reason": row["reason"],
                "payload": row["payload"] or {},
                "prevEvent": int(row["prev_event"]) if row["prev_event"] else None,
                "hash": row["hash"],
            }
            for row in rows
        ]
        return verify_ontology_records(records)

    # ---- graph helpers ---------------------------------------------------

    def _ensure_graph(self, row: dict[str, Any]) -> int:
        count = self._graph.count_graph(row["graph_iri"])
        if count != row["triple_count"]:
            self._load_graph(row)
            count = self._graph.count_graph(row["graph_iri"])
        return count

    def _definition_conflicts(
        self, triples: list[Any], current_graph: str
    ) -> list[dict[str, Any]]:
        """Compare outgoing triples per subject IRI against the current T-Box."""
        current_nt = self._graph.export_graph(current_graph)
        current = parse_rdf(current_nt, "nt")

        def group(items: list[Any]) -> dict[str, set[tuple[str, str]]]:
            out: dict[str, set[tuple[str, str]]] = {}
            for s, p, o in items:
                out.setdefault(str(s), set()).add((p.n3(), o.n3()))
            return out

        candidate = group(triples)
        existing = group(current)
        conflicts: list[dict[str, Any]] = []
        for iri in sorted(set(candidate) & set(existing)):
            added = sorted(candidate[iri] - existing[iri])
            removed = sorted(existing[iri] - candidate[iri])
            if not added and not removed:
                continue
            conflicts.append({
                "iri": iri,
                "added": [f"{p} {o}" for p, o in added],
                "removed": [f"{p} {o}" for p, o in removed],
            })
        return conflicts

    # ---- import ----------------------------------------------------------

    def import_source(
        self,
        path: str,
        semver: str,
        label: str | None = None,
        rdf_format: str | None = None,
        on_conflict: str = "reject",
        graph_iri: str | None = None,
        namespace_id: str | None = None,
    ) -> dict[str, Any]:
        if not SEMVER_RE.match(semver or ""):
            raise self._error(
                "E_ONTOLOGY_BAD_SEMVER",
                f"semver must look like 1.0.0, got {semver!r}",
                key="semver",
            )
        if on_conflict not in ("reject", "new_version", "ignore"):
            raise PortError(
                code="InvalidArgument",
                message=f"on_conflict must be reject, new_version or ignore, got {on_conflict!r}",
                provider="platform",
                provider_code="E_ONTOLOGY_ON_CONFLICT",
                details={"allowed": ["reject", "new_version", "ignore"]},
            )

        raw, detected_format, triples = self._load_source(path)
        if rdf_format:
            try:
                triples = parse_rdf(raw, rdf_format)
                detected_format = rdf_format
            except PortError as exc:
                raise self._error("E_ONTOLOGY_PARSE", exc.message, key="file") from exc
        content_hash = _content_hash(triples)
        owner_namespace = _owner_namespace_id(namespace_id)

        # S16: an archived (deprecated) version is never revived implicitly by a
        # re-import; only a live version with the same content may be reused.
        existing = self._meta.query(
            """
            SELECT version_id, semver, status FROM platform.ontology_version
             WHERE content_hash = %s AND status <> 'deprecated'
             ORDER BY created_at LIMIT 1
            """,
            (content_hash,),
        )
        if existing:
            log.info(
                "ontology import skipped (same content)",
                extra={"event": {"event": "ontology_import", "result": "skipped", "hash": content_hash}},
            )
            return {
                "versionId": existing[0]["version_id"],
                "semver": existing[0]["semver"],
                "status": existing[0]["status"],
                "contentHash": content_hash,
                "tripleCount": len(triples),
                "skipped": True,
                "conflicts": [],
            }

        # Conflict detection against the current published T-Box: the same IRI
        # with a different definition must never be silently overwritten.
        pointer = self._pointer()
        conflicts: list[dict[str, Any]] = []
        if pointer:
            conflicts = self._definition_conflicts(triples, pointer["graph"])
        if conflicts and on_conflict == "ignore":
            # Q/T2: an additive annotation layer (skos labels, prov provenance)
            # lands on top of an explicitly allowed diff; the diff itself is
            # still reported so the publish gate can show what changed.
            log.warning(
                "ontology import overrides IRI diffs on operator request",
                extra={"event": {"event": "ontology_import", "conflicts": len(conflicts)}},
            )
        elif conflicts and on_conflict == "reject":
            raise PortError(
                code="Conflict",
                message=(
                    f"import conflicts with the current T-Box on {len(conflicts)} IRI(s); "
                    "refusing to overwrite"
                ),
                provider="platform",
                provider_code="E_ONTOLOGY_IMPORT_CONFLICT",
                details={
                    "onConflict": on_conflict,
                    "conflicts": conflicts[:50],
                    "conflictCount": len(conflicts),
                },
            )

        version_id = f"ont-{uuid.uuid4().hex[:12]}"
        target_graph = graph_iri or f"urn:platform:graph:tbox:{version_id}"
        if graph_iri:
            if not graph_iri.startswith("urn:platform:graph:tbox:"):
                raise PortError(
                    code="InvalidArgument",
                    message=f"graph IRI must start with urn:platform:graph:tbox:, got {graph_iri}",
                    provider="platform",
                    provider_code="E_ONTOLOGY_BAD_GRAPH",
                )
            used = self._meta.query(
                "SELECT version_id FROM platform.ontology_version WHERE graph_iri = %s",
                (graph_iri,),
            )
            if used:
                raise PortError(
                    code="Conflict",
                    message=f"graph already owns a version: {graph_iri}",
                    provider="platform",
                    provider_code="E_ONTOLOGY_GRAPH_IN_USE",
                    details={"versionId": used[0]["version_id"]},
                )
        suffix = "trig" if detected_format == "trig" else "ttl"
        source_key = f"sources/{content_hash}.{suffix}"
        self._objects.put(
            ONTOLOGY_BUCKET,
            source_key,
            raw,
            "text/turtle" if suffix == "ttl" else "application/trig",
            {"kind": "ontology_source", "content_hash": content_hash},
        )

        with self._meta.tx() as tx:
            tx.execute(
                """
                INSERT INTO platform.ontology_version
                  (version_id, semver, status, content_hash, triple_count, source_format,
                   source_key, graph_iri, label, namespace_id, attribution_source)
                VALUES (%s, %s, 'draft', %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    version_id, semver, content_hash, len(triples), detected_format,
                    source_key, target_graph, label,
                    owner_namespace,
                    OWNER_SOURCE_PLATFORM if owner_namespace else None,
                ),
            )
            self._append_event(
                tx, version_id, None, "imported", "operator", None,
                {
                    "semver": semver, "contentHash": content_hash,
                    "tripleCount": len(triples), "graph": target_graph,
                    "format": detected_format,
                    "conflictsAccepted": len(conflicts),
                    "onConflict": on_conflict,
                },
            )
            if conflicts:
                self._append_event(
                    tx, version_id, None, "import_conflict_accepted", "operator", None,
                    {"conflicts": conflicts[:50], "onConflict": on_conflict},
                )
        log.info(
            "ontology imported",
            extra={
                "event": {
                    "event": "ontology_import",
                    "result": "created",
                    "version_id": version_id,
                    "hash": content_hash,
                    "triples": len(triples),
                }
            },
        )
        return {
            "versionId": version_id,
            "semver": semver,
            "status": "draft",
            "contentHash": content_hash,
            "tripleCount": len(triples),
            "graph": target_graph,
            "skipped": False,
            "conflicts": conflicts,
        }

    # ---- G-01: versioned import with closure + gates ---------------------

    def import_document(
        self,
        *,
        raw: bytes | None = None,
        path: str | None = None,
        rdf_format: str | None = None,
        semver: str = "0.0.0",
        label: str | None = None,
        actor: str = "operator",
        on_conflict: str = "reject",
        graph_iri: str | None = None,
        namespace: str | None = None,
        namespace_id: str | None = None,
        validate_shacl: bool = True,
        check_consistency: bool = True,
    ) -> dict[str, Any]:
        """Import a TTL document, resolve its owl:imports closure, run gates.

        Unlike `import_source` (S1/S11 draft path), this method never reports a
        false success: parse errors surface with a line number, unresolved
        imports are listed (and make the result unusable), SHACL runs against
        the target namespace's deployed shapes, and the consistency gate maps
        to `usable=false` rather than a silent downgrade.
        """
        if not SEMVER_RE.match(semver or ""):
            raise self._error(
                "E_ONTOLOGY_BAD_SEMVER",
                f"semver must look like 1.0.0, got {semver!r}",
                key="semver",
            )
        if on_conflict not in ("reject", "new_version", "ignore"):
            raise PortError(
                code="InvalidArgument",
                message=f"on_conflict must be reject, new_version or ignore, got {on_conflict!r}",
                provider="platform",
                provider_code="E_ONTOLOGY_ON_CONFLICT",
                details={"allowed": ["reject", "new_version", "ignore"]},
            )
        if raw is None:
            source = Path(path or "")
            if not source.is_file():
                raise self._error(
                    "E_ONTOLOGY_SOURCE_MISSING",
                    f"ontology source file not found: {source}",
                    key="file",
                    hint="pass content in the request body or mount the file under /data",
                )
            raw = source.read_bytes()
            if rdf_format is None:
                rdf_format = self._detect_format(source.suffix)
        if len(raw) > self._config.max_source_bytes:
            raise self._error(
                "E_ONTOLOGY_SOURCE_TOO_LARGE",
                f"{len(raw)} bytes exceeds ontology.max_source_bytes={self._config.max_source_bytes}",
                key="ontology.max_source_bytes",
            )
        rdf_format = rdf_format or "turtle"

        graph = Graph()
        self._parse_into(graph, raw, rdf_format, public_id="urn:platform:import:root")
        imports, unresolved = self._resolve_imports(graph)

        # T2: any term:guardRegex that does not compile blocks the import; a
        # pattern that compiles but never matches is only counted at runtime.
        assert_guards_compilable(graph)

        triples = list(graph)
        content_hash = _content_hash(triples)
        version_id = f"ont-{uuid.uuid4().hex[:12]}"
        target_graph = graph_iri or f"urn:platform:graph:tbox:{version_id}"
        if graph_iri and not graph_iri.startswith("urn:platform:graph:tbox:"):
            raise PortError(
                code="InvalidArgument",
                message=f"graph IRI must start with urn:platform:graph:tbox:, got {graph_iri}",
                provider="platform",
                provider_code="E_ONTOLOGY_BAD_GRAPH",
            )

        namespace = namespace or self._detect_namespace(graph)
        owner_namespace = _owner_namespace_id(namespace_id)
        data_nt = graph.serialize(format="nt").encode("utf-8")

        shacl: dict[str, Any] = {
            "conforms": None,
            "namespace": namespace,
            "violations": [],
            "violationCount": 0,
            "shapes": [],
            "shapesVersion": None,
            "status": "not_requested",
        }
        if validate_shacl:
            if self._validator is None:
                shacl["status"] = "unavailable"
                shacl["error"] = "SHACL gate is not configured"
            elif not namespace:
                shacl["status"] = "no_namespace"
            elif not self._validator.shapes(namespace):
                shacl["status"] = "not_deployed"
            else:
                try:
                    result = self._validator.validate(data_nt, target_graph, namespace)
                    shacl = {**result, "status": "validated"}
                except PortError as exc:
                    shacl["status"] = "error"
                    shacl["conforms"] = False
                    shacl["error"] = exc.message
                    shacl["providerCode"] = exc.provider_code

        consistency: dict[str, Any] = {"checked": False, "consistent": None}
        if check_consistency and not unresolved:
            try:
                result = self._gate_consistency(data_nt, include_abox=False)
                consistency = {**result, "checked": True}
            except PortError as exc:
                consistency = {
                    "checked": True,
                    "consistent": False,
                    "providerCode": exc.provider_code,
                    "message": exc.message,
                }

        usable_reasons: list[dict[str, Any]] = []
        if unresolved:
            usable_reasons.append(
                {
                    "code": "E_ONTOLOGY_IMPORTS_UNRESOLVED",
                    "message": f"{len(unresolved)} owl:imports IRI(s) could not be resolved",
                    "imports": [item["iri"] for item in unresolved],
                }
            )
        if shacl.get("conforms") is False:
            usable_reasons.append(
                {
                    "code": "E_ONTOLOGY_SHACL_FAILED",
                    "message": "SHACL validation failed against the deployed shapes",
                    "violations": shacl.get("violationCount", 0),
                }
            )
        if consistency.get("consistent") is False:
            usable_reasons.append(
                {
                    "code": "E_ONTOLOGY_INCONSISTENT",
                    "message": "consistency gate failed (ROBOT/ELK)",
                    "providerCode": consistency.get("providerCode"),
                }
            )
        usable = not usable_reasons

        existing = self._meta.query(
            """
            SELECT version_id, semver, status, graph_iri FROM platform.ontology_version
             WHERE content_hash = %s ORDER BY created_at LIMIT 1
            """,
            (content_hash,),
        )
        if existing:
            return {
                "importId": existing[0]["version_id"],
                "versionId": existing[0]["version_id"],
                "semver": existing[0]["semver"],
                "status": existing[0]["status"],
                "graph": existing[0]["graph_iri"],
                "namespace": namespace,
                "contentHash": content_hash,
                "triples": len(triples),
                "classes": self._count_type(graph, OWL.Class),
                "objectProperties": self._count_type(graph, OWL.ObjectProperty),
                "dataProperties": self._count_type(graph, OWL.DatatypeProperty),
                "imports": imports,
                "unresolvedImports": unresolved,
                "shacl": shacl,
                "consistency": consistency,
                "usable": usable,
                "usableReasons": usable_reasons,
                "skipped": True,
                "importedBy": actor,
            }

        pointer = self._pointer()
        conflicts: list[dict[str, Any]] = []
        if pointer:
            conflicts = self._definition_conflicts(triples, pointer["graph"])
        if conflicts and on_conflict == "ignore":
            # Q/T2: an additive annotation layer (skos labels, prov provenance)
            # lands on top of an explicitly allowed diff; the diff itself is
            # still reported so the publish gate can show what changed.
            log.warning(
                "ontology import overrides IRI diffs on operator request",
                extra={"event": {"event": "ontology_import", "conflicts": len(conflicts)}},
            )
        elif conflicts and on_conflict == "reject":
            raise PortError(
                code="Conflict",
                message=(
                    f"import conflicts with the current T-Box on {len(conflicts)} IRI(s); "
                    "refusing to overwrite"
                ),
                provider="platform",
                provider_code="E_ONTOLOGY_IMPORT_CONFLICT",
                details={
                    "onConflict": on_conflict,
                    "conflicts": conflicts[:50],
                    "conflictCount": len(conflicts),
                    "usable": False,
                    "usableReasons": [
                        {"code": "E_ONTOLOGY_IMPORT_CONFLICT", "message": "definition conflict"}
                    ],
                },
            )

        stored = graph.serialize(format="turtle").encode("utf-8")
        source_key = f"sources/{content_hash}.ttl"
        self._objects.put(
            ONTOLOGY_BUCKET,
            source_key,
            stored,
            "text/turtle",
            {"kind": "ontology_source", "content_hash": content_hash, "importId": version_id},
        )

        payload = {
            "semver": semver,
            "contentHash": content_hash,
            "tripleCount": len(triples),
            "graph": target_graph,
            "format": "turtle",
            "namespace": namespace,
            "importId": version_id,
            "importedBy": actor,
            "usable": usable,
            "usableReasons": usable_reasons,
            "unresolvedImports": unresolved,
            "imports": imports,
            "shacl": {
                "status": shacl.get("status"),
                "namespace": shacl.get("namespace"),
                "conforms": shacl.get("conforms"),
                "violationCount": shacl.get("violationCount", 0),
                "shapes": shacl.get("shapes", []),
                "shapesVersion": shacl.get("shapesVersion"),
            },
            "consistency": consistency,
            "conflictsAccepted": len(conflicts),
            "onConflict": on_conflict,
        }
        with self._meta.tx() as tx:
            tx.execute(
                """
                INSERT INTO platform.ontology_version
                  (version_id, semver, status, content_hash, triple_count, source_format,
                   source_key, graph_iri, label, namespace_id, attribution_source)
                VALUES (%s, %s, 'draft', %s, %s, 'turtle', %s, %s, %s, %s, %s)
                """,
                (
                    version_id, semver, content_hash, len(triples),
                    source_key, target_graph, label,
                    owner_namespace,
                    OWNER_SOURCE_PLATFORM if owner_namespace else None,
                ),
            )
            self._append_event(tx, version_id, None, "imported", actor, None, payload)
            if conflicts:
                self._append_event(
                    tx, version_id, None, "import_conflict_accepted", actor, None,
                    {"conflicts": conflicts[:50], "onConflict": on_conflict},
                )
        log.info(
            "ontology import evaluated",
            extra={
                "event": {
                    "event": "ontology_import",
                    "result": "created",
                    "version_id": version_id,
                    "triples": len(triples),
                    "usable": usable,
                    "unresolved": len(unresolved),
                }
            },
        )
        return {
            "importId": version_id,
            "versionId": version_id,
            "semver": semver,
            "status": "draft",
            "graph": target_graph,
            "namespace": namespace,
            "contentHash": content_hash,
            "triples": len(triples),
            "classes": self._count_type(graph, OWL.Class),
            "objectProperties": self._count_type(graph, OWL.ObjectProperty),
            "dataProperties": self._count_type(graph, OWL.DatatypeProperty),
            "imports": imports,
            "unresolvedImports": unresolved,
            "shacl": shacl,
            "consistency": consistency,
            "usable": usable,
            "usableReasons": usable_reasons,
            "conflicts": conflicts,
            "skipped": False,
            "importedBy": actor,
        }

    def _parse_into(
        self, graph: Graph, raw: bytes, rdf_format: str, public_id: str = ""
    ) -> None:
        """Parse into the shared graph so bnodes from different files cannot clash."""
        try:
            graph.parse(data=raw.decode("utf-8"), format=rdf_format, publicID=public_id)
        except Exception as exc:
            match = PARSE_LINE_RE.search(str(exc))
            line = int(match.group(1)) if match else None
            raise PortError(
                code="InvalidArgument",
                message=(
                    f"RDF parse failed ({rdf_format})"
                    + (f" at line {line}" if line else "")
                    + f": {exc}"
                ),
                provider="rdflib",
                provider_code="E_ONTOLOGY_PARSE",
                details={"format": rdf_format, "line": line, "publicId": public_id or None},
            ) from exc

    def _resolve_imports(self, graph: Graph) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        resolved: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        visited: set[str] = set()
        queue: list[tuple[str, int, str]] = [
            (str(iri), 0, "root") for iri in sorted(set(graph.objects(None, OWL.imports)))
        ]
        while queue:
            iri, depth, declared_by = queue.pop(0)
            if iri in visited:
                continue
            visited.add(iri)
            if len(visited) > self._config.import_max_imports:
                unresolved.append(
                    {
                        "iri": iri,
                        "declaredBy": declared_by,
                        "reason": "import-limit",
                        "message": f"more than {self._config.import_max_imports} imports",
                    }
                )
                break
            if depth > self._config.import_max_depth:
                unresolved.append(
                    {
                        "iri": iri,
                        "declaredBy": declared_by,
                        "reason": "max-depth",
                        "message": f"depth {depth} > {self._config.import_max_depth}",
                    }
                )
                continue
            raw, source_kind, reason = self._resolve_import(iri)
            if raw is None:
                unresolved.append(
                    {
                        "iri": iri,
                        "declaredBy": declared_by,
                        "reason": reason or "unresolved",
                    }
                )
                continue
            before = len(graph)
            try:
                self._parse_into(graph, raw, "turtle", public_id=iri)
            except PortError as exc:
                unresolved.append(
                    {
                        "iri": iri,
                        "declaredBy": declared_by,
                        "reason": "parse-error",
                        "message": exc.message,
                        "line": (exc.details or {}).get("line"),
                    }
                )
                continue
            resolved.append(
                {
                    "iri": iri,
                    "declaredBy": declared_by,
                    "source": source_kind,
                    "triplesAdded": len(graph) - before,
                }
            )
            for child in sorted(set(graph.objects(URIRef(iri), OWL.imports))):
                if str(child) not in visited:
                    queue.append((str(child), depth + 1, iri))

        # Anything declared before the limit/depth cut-off that was never even
        # attempted must still appear in unresolvedImports.
        declared = {str(iri) for iri in set(graph.objects(None, OWL.imports))}
        for iri in sorted(declared - visited):
            unresolved.append({"iri": iri, "declaredBy": "queue", "reason": "not-attempted"})
        return resolved, unresolved

    def _resolve_import(self, iri: str) -> tuple[bytes | None, str, str]:
        """Resolve one import IRI: local mirror first, then HTTP if enabled."""
        tail = iri.rstrip("/#").rsplit("/", 1)[-1]
        if tail:
            mirror = Path(self._config.import_dir)
            for suffix in (".ttl", ".owl", ".rdf"):
                candidate = mirror / f"{tail}{suffix}"
                if candidate.is_file():
                    return candidate.read_bytes(), f"mirror:{candidate.name}", ""
        if iri.startswith(("http://", "https://")):
            if not self._config.import_fetch_enabled:
                return None, "", "http-fetch-disabled"
            try:
                response = httpx.get(
                    iri,
                    timeout=self._config.import_fetch_timeout_ms / 1000,
                    follow_redirects=True,
                    headers={"Accept": "text/turtle, application/rdf+xml;q=0.9, */*;q=0.1"},
                )
            except httpx.HTTPError as exc:
                return None, "", f"fetch-error:{type(exc).__name__}"
            if response.status_code != 200:
                return None, "", f"http-{response.status_code}"
            return response.content, f"http:{iri}", ""
        return None, "", "unsupported-scheme"

    def _detect_namespace(self, graph: Graph) -> str | None:
        if self._validator is None:
            return None
        class_iris = [str(s) for s in graph.subjects(RDF.type, OWL.Class)]
        class_iris += [str(s) for s in graph.subjects(RDF.type, URIRef(RDFS_CLASS))]
        namespaces = sorted(
            getattr(self._validator, "namespaces", lambda: [])() or [], key=len, reverse=True
        )
        for candidate in namespaces:
            if any(iri.startswith(candidate) for iri in class_iris):
                return candidate
        return None

    @staticmethod
    def _count_type(graph: Graph, rdf_type: Any) -> int:
        return len(set(graph.subjects(RDF.type, rdf_type)))

    def import_record(self, import_id: str) -> dict[str, Any]:
        """Answer 'which version / who imported this graph' from the audit chain."""
        row = self._fetch(import_id)
        if row is None:
            raise PortError(
                code="NotFound",
                message=f"ontology import not found: {import_id}",
                provider="postgres",
                provider_code="E_ONTOLOGY_IMPORT_NOT_FOUND",
            )
        events = self.events(import_id)["items"]
        imported = next((item for item in events if item["action"] == "imported"), None)
        payload = (imported or {}).get("payload", {})
        return {
            "importId": import_id,
            "versionId": import_id,
            "semver": row["semver"],
            "status": row["status"],
            "graph": row["graph_iri"],
            "triples": row["triple_count"],
            "contentHash": row["content_hash"],
            "importedBy": (imported or {}).get("actor", "unknown"),
            "importedAt": (imported or {}).get("createdAt"),
            "namespace": payload.get("namespace"),
            "usable": payload.get("usable"),
            "usableReasons": payload.get("usableReasons", []),
            "unresolvedImports": payload.get("unresolvedImports", []),
            "shacl": payload.get("shacl"),
            "consistency": payload.get("consistency"),
            "events": events,
        }

    # ---- publish / rollback ---------------------------------------------

    def _load_graph(self, row: dict[str, Any]) -> dict[str, Any]:
        raw, _meta = self._objects.get(ONTOLOGY_BUCKET, row["source_key"])
        triples = parse_rdf(raw, row["source_format"])
        actual = _content_hash(triples)
        if actual != row["content_hash"]:
            raise PortError(
                code="DataLoss",
                message="ontology source content hash does not match the version row",
                provider="layered",
                provider_code="E_ONTOLOGY_HASH_MISMATCH",
                details={"expected": row["content_hash"], "actual": actual},
            )
        return self._graph.replace_graph(row["graph_iri"], raw, row["source_format"])

    # ---- proposals / governed publish ------------------------------------

    def _proposal_fetch(self, proposal_id: str) -> dict[str, Any] | None:
        rows = self._meta.query(
            """
            SELECT proposal_id, version_id, against_version, change_summary, status,
                   breaking, acknowledged_breaking, diff, impact, created_by, created_at,
                   approved_by, approved_at, published_at
              FROM platform.ontology_proposal
             WHERE proposal_id = %s
            """,
            (proposal_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def _row_to_proposal(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "proposalId": row["proposal_id"],
            "versionId": row["version_id"],
            "againstVersion": row["against_version"],
            "changeSummary": row["change_summary"],
            "status": row["status"],
            "breaking": bool(row["breaking"]),
            "acknowledgedBreaking": bool(row["acknowledged_breaking"]),
            "diff": row["diff"] or {},
            "impact": row["impact"] or {},
            "createdBy": row["created_by"],
            "createdAt": row["created_at"].isoformat(),
            "approvedBy": row["approved_by"],
            "approvedAt": row["approved_at"].isoformat() if row["approved_at"] else None,
            "publishedAt": row["published_at"].isoformat() if row["published_at"] else None,
        }

    def propose(
        self,
        version_id: str,
        change_summary: str,
        actor: str = "operator",
        against_version: str | None = None,
    ) -> dict[str, Any]:
        if not change_summary or not change_summary.strip():
            raise PortError(
                code="InvalidArgument",
                message="change_summary is required for a proposal",
                provider="platform",
                provider_code="E_ONTOLOGY_SUMMARY_REQUIRED",
            )
        row = self._require(version_id)
        if row["status"] not in ("draft", "proposed"):
            raise PortError(
                code="Conflict",
                message=f"version {version_id} is {row['status']}; only draft/proposed can be proposed",
                provider="platform",
                provider_code="E_ONTOLOGY_STATUS",
                details={"status": row["status"], "expected": ["draft", "proposed"]},
            )
        self._ensure_graph(row)
        if against_version:
            self._require(against_version)
            self._ensure_graph(self._require(against_version))
        else:
            pointer = self._pointer()
            against_version = pointer["versionId"] if pointer else None

        diff = self.diff(against_version, version_id)
        impact = {
            "addedTriples": diff["summary"]["addedTriples"],
            "removedTriples": diff["summary"]["removedTriples"],
            "addedClasses": len(diff["summary"]["addedClasses"]),
            "removedClasses": len(diff["summary"]["removedClasses"]),
            "addedProperties": len(diff["summary"]["addedProperties"]),
            "removedProperties": len(diff["summary"]["removedProperties"]),
            "domainChanges": len(diff["summary"]["domainChanges"]),
            "rangeChanges": len(diff["summary"]["rangeChanges"]),
            "removedClassInstances": sum(
                item["instances"] for item in diff["summary"]["removedClassInstances"]
            ),
            "breakingItems": len(diff["breakingItems"]),
        }
        proposal_id = f"prop-{uuid.uuid4().hex[:12]}"
        with self._meta.tx() as tx:
            if row["status"] == "draft":
                record_transition(
                    tx, entity_kind="version", entity_id=version_id, version_id=version_id,
                    proposal_id=None, from_status="draft", to_status="proposed",
                    actor=actor, reason="proposal submitted",
                    payload={"changeSummary": change_summary.strip()},
                )
            record_transition(
                tx, entity_kind="proposal", entity_id=proposal_id, version_id=version_id,
                proposal_id=proposal_id, from_status=None, to_status="proposed",
                actor=actor, reason="proposal submitted",
                payload={"changeSummary": change_summary.strip(), "against": against_version},
            )
            tx.execute(
                "UPDATE platform.ontology_version SET status = 'proposed' WHERE version_id = %s",
                (version_id,),
            )
            tx.execute(
                """
                INSERT INTO platform.ontology_proposal
                  (proposal_id, version_id, against_version, change_summary, status,
                   breaking, diff, impact, created_by)
                VALUES (%s, %s, %s, %s, 'proposed', %s, %s, %s, %s)
                """,
                (
                    proposal_id, version_id, against_version, change_summary.strip(),
                    bool(diff["breaking"]), Jsonb(diff), Jsonb(impact), actor,
                ),
            )
            self._append_event(
                tx, version_id, proposal_id, "proposed", actor, None,
                {"changeSummary": change_summary.strip(), "against": against_version,
                 "breaking": bool(diff["breaking"]), "impact": impact},
            )
        return {
            "proposalId": proposal_id,
            "versionId": version_id,
            "againstVersion": against_version,
            "changeSummary": change_summary.strip(),
            "status": "proposed",
            "breaking": bool(diff["breaking"]),
            "diff": diff,
            "impact": impact,
        }

    def approve(
        self, proposal_id: str, actor: str = "operator", reason: str | None = None
    ) -> dict[str, Any]:
        proposal = self._proposal_fetch(proposal_id)
        if proposal is None:
            raise PortError(
                code="NotFound",
                message=f"ontology proposal not found: {proposal_id}",
                provider="postgres",
                provider_code="E_ONTOLOGY_PROPOSAL_NOT_FOUND",
            )
        if proposal["status"] == "published":
            raise PortError(
                code="Conflict",
                message=f"proposal {proposal_id} is already published",
                provider="platform",
                provider_code="E_ONTOLOGY_PROPOSAL_STATUS",
            )
        if proposal["status"] not in ("proposed", "review"):
            raise PortError(
                code="Conflict",
                message=(
                    f"proposal {proposal_id} is {proposal['status']}; only proposed/review "
                    "can be approved"
                ),
                provider="platform",
                provider_code="E_ONTOLOGY_PROPOSAL_STATUS",
                details={"status": proposal["status"]},
            )
        version_id = proposal["version_id"]
        reviewed_implicitly = proposal["status"] == "proposed"
        validate_transition("proposal", proposal["status"], "approved")
        with self._meta.tx() as tx:
            if reviewed_implicitly:
                # Compatibility edge proposed -> approved is recorded as the two
                # real steps, so no review/actor/time is ever missing.
                record_transition(
                    tx, entity_kind="proposal", entity_id=proposal_id,
                    version_id=version_id, proposal_id=proposal_id,
                    from_status="proposed", to_status="review", actor=actor,
                    reason=reason or "implicit review before approve",
                    payload={"implicit": True},
                )
                self._append_event(
                    tx, version_id, proposal_id, "review", actor,
                    reason or "implicit review before approve", {"implicit": True},
                )
            tx.execute(
                "UPDATE platform.ontology_proposal "
                "SET status = 'approved', approved_by = %s, approved_at = now() "
                "WHERE proposal_id = %s",
                (actor, proposal_id),
            )
            tx.execute(
                "UPDATE platform.ontology_version SET status = 'approved' WHERE version_id = %s",
                (version_id,),
            )
            record_transition(
                tx, entity_kind="proposal", entity_id=proposal_id,
                version_id=version_id, proposal_id=proposal_id,
                from_status="review", to_status="approved", actor=actor,
                reason=reason,
                payload={"changeSummary": proposal["change_summary"],
                         "breaking": bool(proposal["breaking"])},
            )
            record_transition(
                tx, entity_kind="version", entity_id=version_id,
                version_id=version_id, proposal_id=proposal_id,
                from_status=proposal["status"], to_status="approved", actor=actor,
                reason=reason,
            )
            self._append_event(
                tx, version_id, proposal_id, "approved", actor, reason,
                {"changeSummary": proposal["change_summary"], "breaking": bool(proposal["breaking"])},
            )
        return {
            "proposalId": proposal_id,
            "versionId": version_id,
            "status": "approved",
            "approvedBy": actor,
            "approvedAt": _now(),
            "reviewedImplicitly": reviewed_implicitly,
        }

    def review(
        self, proposal_id: str, actor: str = "operator", reason: str | None = None
    ) -> dict[str, Any]:
        """Move proposed -> review; repeated calls are idempotent, not illegal."""
        proposal = self._proposal_fetch(proposal_id)
        if proposal is None:
            raise PortError(
                code="NotFound",
                message=f"ontology proposal not found: {proposal_id}",
                provider="postgres",
                provider_code="E_ONTOLOGY_PROPOSAL_NOT_FOUND",
            )
        if proposal["status"] == "review":
            return {
                "proposalId": proposal_id,
                "versionId": proposal["version_id"],
                "status": "review",
                "reviewedBy": proposal.get("reviewed_by") or actor,
                "reviewedAt": _now(),
                "unchanged": True,
            }
        validate_transition("proposal", proposal["status"], "review")
        version_id = proposal["version_id"]
        with self._meta.tx() as tx:
            tx.execute(
                "UPDATE platform.ontology_proposal SET status = 'review' WHERE proposal_id = %s",
                (proposal_id,),
            )
            tx.execute(
                "UPDATE platform.ontology_version SET status = 'review' WHERE version_id = %s",
                (version_id,),
            )
            record_transition(
                tx, entity_kind="proposal", entity_id=proposal_id,
                version_id=version_id, proposal_id=proposal_id,
                from_status=proposal["status"], to_status="review",
                actor=actor, reason=reason,
                payload={"changeSummary": proposal["change_summary"]},
            )
            record_transition(
                tx, entity_kind="version", entity_id=version_id,
                version_id=version_id, proposal_id=proposal_id,
                from_status=proposal["status"], to_status="review",
                actor=actor, reason=reason,
            )
            self._append_event(
                tx, version_id, proposal_id, "review", actor, reason,
                {"changeSummary": proposal["change_summary"], "breaking": bool(proposal["breaking"])},
            )
        return {
            "proposalId": proposal_id,
            "versionId": version_id,
            "status": "review",
            "reviewedBy": actor,
            "reviewedAt": _now(),
            "reason": reason,
            "unchanged": False,
        }

    def transitions(
        self,
        proposal_id: str | None = None,
        version_id: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        items = list_transitions(
            self._meta, version_id=version_id, proposal_id=proposal_id, limit=limit
        )
        return {
            "items": items,
            "count": len(items),
            "filter": {"proposalId": proposal_id, "versionId": version_id},
            "empty": not items,
            "emptyReason": None if items else "无流转记录",
            "readOnly": True,
        }

    def list_proposals(self, version_id: str | None = None) -> dict[str, Any]:
        rows = self._meta.query(
            """
            SELECT proposal_id, version_id, against_version, change_summary, status,
                   breaking, acknowledged_breaking, diff, impact, created_by, created_at,
                   approved_by, approved_at, published_at
              FROM platform.ontology_proposal
             WHERE (%s::text IS NULL OR version_id = %s)
             ORDER BY created_at DESC
            """,
            (version_id, version_id),
        )
        items = [self._row_to_proposal(row) for row in rows]
        return {"items": items, "count": len(items)}

    def get_proposal(self, proposal_id: str) -> dict[str, Any]:
        row = self._proposal_fetch(proposal_id)
        if row is None:
            raise PortError(
                code="NotFound",
                message=f"ontology proposal not found: {proposal_id}",
                provider="postgres",
                provider_code="E_ONTOLOGY_PROPOSAL_NOT_FOUND",
            )
        return self._row_to_proposal(row)

    def _publish_evidence(
        self, *, version_id: str, row: dict[str, Any], proposal: dict[str, Any] | None,
        mode: str, gates: dict[str, Any], verdict: str, actor: str,
        reason: str | None, diff: dict[str, Any] | None = None,
        error: PortError | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """O-04: observe publish gates and persist an evidence pack.

        Bookkeeping must never change the gate verdict: any failure here is
        swallowed and reported in the publish payload.
        """
        try:
            from ..evidence import build_pack, record

            against = None
            against_id = (diff or {}).get("from")
            if against_id and against_id != version_id:
                rows = self._meta.query(
                    "SELECT version_id, semver, content_hash, triple_count "
                    "FROM platform.ontology_version WHERE version_id = %s",
                    (against_id,),
                )
                against = rows[0] if rows else None
            shapes = None
            if self._validator is not None:
                try:
                    version = self._validator.shapes_version()  # type: ignore[attr-defined]
                except Exception:
                    version = None
                shapes = {"version": version}
            pack = build_pack(
                version=row, against=against, proposal=proposal, mode=mode,
                gates=gates, verdict=verdict, actor=actor, reason=reason,
                diff=diff, error=error, shapes=shapes,
                extra={
                    # 调用者身份线索：来源地址与 smoke token 是否校验通过。
                    "remoteAddr": ((gates.get("terms") or {}).get("vocabGuard") or {})
                    .get("remoteAddr"),
                    "purposeVerified": ((gates.get("terms") or {}).get("vocabGuard") or {})
                    .get("purposeVerified"),
                    **(extra or {}),
                },
            )
            record(self._meta, pack)
            return {
                "evidenceId": pack["evidenceId"],
                "sha256": pack["sha256"],
                "verdict": verdict,
                "downloadUrl": f"/ontology/evidence/{pack['evidenceId']}/download",
            }
        except Exception as exc:
            log.warning(
                "ontology evidence pack not written",
                extra={"event": {"event": "ontology_evidence_failed",
                                 "version_id": version_id, "error": str(exc)}},
            )
            return {"verdict": verdict, "error": str(exc)}

    def _gate_shacl(self, nt: bytes, graph_iri: str) -> dict[str, Any]:
        if self._validator is None:
            raise PortError(
                code="Unsupported",
                message="SHACL gate is not configured",
                provider="platform",
                provider_code="E_ONTOLOGY_GATE_UNAVAILABLE",
            )
        result = self._validator.validate(nt, graph_iri)
        if not result.get("conforms"):
            raise PortError(
                code="Conflict",
                message="SHACL validation failed; publish rejected",
                provider="pyshacl",
                provider_code="E_ONTOLOGY_SHACL_FAILED",
                details={"violations": result.get("violations", [])[:50]},
            )
        return result

    def _gate_consistency(self, tbox_nt: bytes, include_abox: bool = True) -> dict[str, Any]:
        if self._reasoner is None:
            raise PortError(
                code="Unsupported",
                message="consistency gate is not configured",
                provider="platform",
                provider_code="E_ONTOLOGY_GATE_UNAVAILABLE",
            )
        # Evidence pack (O-04 gap): a passing consistency gate used to record only
        # {profile, consistent:true}, so after the fact nobody could tell "checked
        # with real data" from "checked an empty A-Box". Always record the exact
        # input: which graphs, how many triples each, the total, and a hash.
        # Missing input is stated explicitly (aboxGraphs: [] + emptyAbox: true)
        # instead of being hidden by defaults.
        # ``verdict`` must not claim a pass on an empty A-Box: an empty input can
        # never falsify consistency, so the gate reports ``not_applicable`` while
        # keeping the reasoner's raw ``consistent`` answer for the record.
        abox = b""
        abox_graphs: list[str] = list(self._abox_graphs) if include_abox else []
        abox_graph_triples: dict[str, int] = {}
        abox_unavailable: list[dict[str, str]] = []
        for graph_iri in abox_graphs:
            try:
                data = self._graph.export_graph(graph_iri)
            except PortError as exc:
                # A configured graph that cannot be read is *not* an empty graph:
                # say so instead of silently counting zero.
                abox_unavailable.append(
                    {"graph": graph_iri, "error": exc.provider_code or exc.code}
                )
                abox_graph_triples[graph_iri] = 0
                continue
            abox_graph_triples[graph_iri] = sum(
                1 for line in data.splitlines() if line.strip()
            )
            abox += data + b"\n"
        tbox_triples = sum(1 for line in tbox_nt.splitlines() if line.strip())
        abox_triples = sum(abox_graph_triples.values())
        evidence = {
            "aboxGraphs": abox_graphs,
            "aboxGraphTriples": abox_graph_triples,
            "aboxTriples": abox_triples,
            "tboxTriples": tbox_triples,
            "emptyAbox": abox_triples == 0,
            "aboxGraphsUnavailable": abox_unavailable,
            "inputHash": hashlib.sha256(tbox_nt + b"\x00" + abox).hexdigest(),
        }
        try:
            result = self._reasoner.reason(
                tbox_nt, abox, self._reason_profile, consistency_first=True
            )
        except PortError as exc:
            # ROBOT exits non-zero on an unsatisfiable class instead of returning
            # consistent=false. That is still a reason to refuse the publish, and
            # the gate must speak ontology codes rather than a raw reasoner 500.
            if (
                exc.provider_code == "E_REASONER_BAD_RESPONSE"
                and "unsatisfiable" in (exc.message or "").lower()
            ):
                raise PortError(
                    code="Conflict",
                    message="ontology has unsatisfiable classes; publish rejected",
                    provider="robot",
                    provider_code="E_ONTOLOGY_INCONSISTENT",
                    details={"profile": self._reason_profile, "reason": "unsatisfiable",
                             "input": evidence},
                ) from exc
            raise
        if not result.get("consistent", True):
            raise PortError(
                code="Conflict",
                message="ontology consistency check failed; publish rejected",
                provider="robot",
                provider_code="E_ONTOLOGY_INCONSISTENT",
                details={"profile": self._reason_profile, "input": evidence},
            )
        checked = not evidence["emptyAbox"]
        if checked:
            empty_reason = None
        elif abox_unavailable:
            empty_reason = "configured A-Box graphs are unreadable"
        elif not abox_graphs:
            empty_reason = "no A-Box graphs configured"
        else:
            empty_reason = "configured A-Box graphs hold no triples"
        return {
            "consistent": True,
            "profile": self._reason_profile,
            # No A-Box means consistency was not actually exercised; never report
            # that as a pass in the gate result or the evidence pack.
            "verdict": "pass" if checked else "not_applicable",
            "checked": checked,
            "emptyAboxReason": empty_reason,
            **evidence,
        }

    def claim_namespace(self, version_id: str, namespace_id: str) -> dict[str, Any]:
        """Attach the publisher's namespace to a version that has no owner yet.

        Rows written before V52 (and drafts registered by callers that could not
        name a namespace) carry NULL. Publishing is the moment the caller states
        which namespace the version belongs to, so the claim is recorded there.
        An existing owner is never overwritten: a different one is a conflict.
        """
        owner = _owner_namespace_id(namespace_id)
        if owner is None:
            raise PortError(
                code="InvalidArgument",
                message="namespaceId is required to claim a version",
                provider="platform",
                provider_code="E_ONTOLOGY_BAD_NAMESPACE_ID",
            )
        row = self._require(version_id)
        current = row.get("namespace_id")
        if current is not None:
            if str(current) != owner:
                raise PortError(
                    code="Conflict",
                    message=(
                        f"version {version_id} already belongs to namespace {current}; "
                        f"refusing to reassign it to {owner}"
                    ),
                    provider="platform",
                    provider_code="E_ONTOLOGY_NAMESPACE_CONFLICT",
                    details={"namespaceId": str(current), "requested": owner},
                )
            return {"versionId": version_id, "namespaceId": str(current), "claimed": False}
        with self._meta.tx() as tx:
            tx.execute(
                """
                UPDATE platform.ontology_version
                   SET namespace_id = %s, attribution_source = %s
                 WHERE version_id = %s AND namespace_id IS NULL
                """,
                (owner, OWNER_SOURCE_PLATFORM, version_id),
            )
        return {"versionId": version_id, "namespaceId": owner, "claimed": True}

    def publish(
        self,
        version_id: str,
        proposal_id: str | None = None,
        acknowledge_breaking: bool = False,
        actor: str = "operator",
        reason: str | None = None,
        activate_existing: bool = False,
        expected_version_id: str | None = None,
        extra_gates: dict[str, Any] | None = None,
        purpose: str | None = None,
        purpose_verified: bool | None = None,
        purpose_status: str | None = None,
        remote_addr: str | None = None,
    ) -> dict[str, Any]:
        row = self._require(version_id)
        # OQ-65 residual / B-5: an archived version is a read-only baseline. It
        # must be rejected before any graph check, otherwise a cache miss would
        # try to reload it from the original TTL and surface the historical
        # canonicalizer drift as E_ONTOLOGY_HASH_MISMATCH.
        if row["status"] in ("deprecated", "rejected"):
            raise PortError(
                code="Conflict",
                message=(
                    f"version {version_id} is {row['status']}; an archived version is "
                    "a read-only baseline and cannot be published"
                ),
                provider="platform",
                provider_code="E_ONTOLOGY_STATUS",
                details={"status": row["status"], "readOnly": True},
            )
        # Graph integrity is checked before any governance branch so a damaged or
        # unreachable graph always fails without touching version/pointer state.
        # Only reload when the graph is actually missing/short: reloading on every
        # publish made two concurrent publish-existing calls clear each other's
        # graph, and one observed count=0 (test_8 concurrent forward publish).
        count = self._ensure_graph(row)
        if count != row["triple_count"]:
            raise PortError(
                code="DataLoss",
                message=(
                    f"graph triple count {count} != version triple_count {row['triple_count']}"
                ),
                provider="layered",
                provider_code="E_ONTOLOGY_TRIPLE_MISMATCH",
            )
        proposal = None
        if proposal_id:
            proposal = self._proposal_fetch(proposal_id)
            if proposal is None:
                raise PortError(
                    code="NotFound",
                    message=f"ontology proposal not found: {proposal_id}",
                    provider="postgres",
                    provider_code="E_ONTOLOGY_PROPOSAL_NOT_FOUND",
                )
            if proposal["version_id"] != version_id:
                raise PortError(
                    code="InvalidArgument",
                    message="proposal does not belong to the requested version",
                    provider="platform",
                    provider_code="E_ONTOLOGY_PROPOSAL_VERSION_MISMATCH",
                    details={"proposalVersion": proposal["version_id"], "version": version_id},
                )
        else:
            # Only pending proposals are honoured here: a published/superseded
            # proposal must not be mistaken for an approval that could open a
            # back door (S12/OQ-47).
            rows = self._meta.query(
                "SELECT proposal_id FROM platform.ontology_proposal "
                "WHERE version_id = %s AND status IN ('proposed', 'approved') "
                "ORDER BY created_at DESC LIMIT 1",
                (version_id,),
            )
            if rows:
                proposal = self._proposal_fetch(rows[0]["proposal_id"])

        governed = proposal is not None
        implicit = False
        diff: dict[str, Any] = {}
        breaking = False
        # G8/O-05: extra gates are recorded alongside SHACL/consistency/breaking
        # without changing their decisions. Empty by default, so the legacy
        # payload stays byte-identical when terms.gate=off.
        gates: dict[str, Any] = dict(extra_gates or {})
        if not governed:
            # S12/OQ-47: there is no direct publish path any more. A call without
            # a proposal is turned into an implicit proposal that must pass the
            # same SHACL + consistency + breaking gates. Nothing is written until
            # every gate has passed, so a refusal leaves version/pointer untouched.
            if proposal_id is None and row["status"] == "published":
                return {
                    "id": version_id,
                    "semver": row["semver"],
                    "graph": row["graph_iri"],
                    "triples": count,
                    "proposalId": None,
                    "governed": True,
                    "unchanged": True,
                    "idempotent": True,
                    "mode": "activate_existing" if activate_existing else "publish",
                    "previousVersionId": self._last_publish_previous(version_id),
                    "publishedBy": actor,
                    "gates": gates,
                    "publishedAt": _now(),
                }
            if row["status"] not in ("draft", "approved", "superseded"):
                raise PortError(
                    code="Conflict",
                    message=(
                        f"version {version_id} is {row['status']}; only a draft, approved "
                        "or superseded version can be re-published"
                    ),
                    provider="platform",
                    provider_code="E_ONTOLOGY_STATUS",
                    details={
                        "status": row["status"],
                        "expected": ["draft", "approved", "superseded"],
                    },
                )
            pointer = self._pointer()
            against = pointer["versionId"] if pointer else None
            diff = self.diff(against, version_id)
            try:
                tbox_nt = self._graph.export_graph(row["graph_iri"])
                gates["shacl"] = self._gate_shacl(tbox_nt, row["graph_iri"])
                gates["consistency"] = self._gate_consistency(tbox_nt)
                breaking = bool(diff["breaking"])
                if breaking and not acknowledge_breaking:
                    raise PortError(
                        code="Conflict",
                        message=(
                            "implicit publish contains breaking changes; pass "
                            "acknowledgeBreaking=true to confirm them"
                        ),
                        provider="platform",
                        provider_code="E_ONTOLOGY_BREAKING",
                        details={
                            "mode": "implicit",
                            "breakingItems": diff.get("breakingItems", []),
                            "diff": diff,
                        },
                    )
            except PortError as exc:
                evidence = self._publish_evidence(
                    version_id=version_id, row=row, proposal=proposal,
                    mode="direct_publish", gates=gates, verdict="fail",
                    actor=actor, reason=reason, diff=diff, error=exc,
                )
                raise
            gates["breaking"] = {
                "breaking": breaking, "acknowledged": bool(acknowledge_breaking),
            }
            implicit = True
        if governed:
            if row["status"] != "approved":
                raise PortError(
                    code="Conflict",
                    message=(
                        f"version {version_id} is {row['status']}; an approved proposal is "
                        "required before publish"
                    ),
                    provider="platform",
                    provider_code="E_ONTOLOGY_NOT_APPROVED",
                    details={"status": row["status"], "proposalId": proposal["proposal_id"]},
                )
            if proposal["status"] != "approved":
                raise PortError(
                    code="Conflict",
                    message=(
                        f"proposal {proposal['proposal_id']} is {proposal['status']}; "
                        "approve it before publish"
                    ),
                    provider="platform",
                    provider_code="E_ONTOLOGY_PROPOSAL_NOT_APPROVED",
                    details={"status": proposal["status"]},
                )

        if governed:
            diff = proposal["diff"] or {}
            try:
                tbox_nt = self._graph.export_graph(row["graph_iri"])
                gates["shacl"] = self._gate_shacl(tbox_nt, row["graph_iri"])
                gates["consistency"] = self._gate_consistency(tbox_nt)
                breaking = bool(proposal["breaking"])
                if breaking and not (acknowledge_breaking or proposal["acknowledged_breaking"]):
                    raise PortError(
                        code="Conflict",
                        message="proposal contains breaking changes; acknowledge them to publish",
                        provider="platform",
                        provider_code="E_ONTOLOGY_BREAKING",
                        details={
                            "breakingItems": diff.get("breakingItems", []),
                            "diff": diff,
                        },
                    )
            except PortError as exc:
                evidence = self._publish_evidence(
                    version_id=version_id, row=row, proposal=proposal,
                    mode="governed", gates=gates, verdict="fail",
                    actor=actor, reason=reason, diff=diff, error=exc,
                )
                raise
            gates["breaking"] = {
                "breaking": breaking,
                "acknowledged": bool(acknowledge_breaking or proposal["acknowledged_breaking"]),
            }

        # --- G8/O-05 vocab-zero guard (both governed and implicit publishes) ---
        # predicate: high_water.conceptsInScheme > 0 and effective.conceptsInScheme == 0
        #            => blocking, independent of terms.gate; only purpose=smoke with a
        #            verified internal token (hmac, fail-closed) may exempt
        # 判据针对"生效术语集"，不针对"T-Box 图内容"：等术语解耦到独立命名图/指针后，
        # 版本图里没有术语是正常状态，本判据只比较发布后生效术语集与高水位。
        # It must run before the tx below: a rejected publish must not leave version
        # rows or pointer/event changes behind. The implicit branch (POST
        # /ontology/publish without a proposal) is the path smoke re-publishes take,
        # so it is covered here too — a guard only wired into publish_import would
        # never see those.
        if self._terms_gate is not None and "terms" not in gates:
            if purpose is not None and purpose_verified is None:
                # 进程内自检探针（platform smoke-sN / CLI）无法带 HTTP 头：从同一
                # 环境变量取 token，走同样的常量时间比较；未配置 => fail-closed。
                env_ctx = termgate.smoke_env_context(
                    purpose,
                    env_name=getattr(self._terms_gate, "smoke_token_env", None),
                    remote_addr=remote_addr,
                )
                purpose_verified = env_ctx["purpose_verified"]
                purpose_status = env_ctx["purpose_status"]
            high_water: dict[str, Any] | None = None
            baseline_error: str | None = None
            try:
                high_water = _term_high_water(self, self._meta)
            except Exception as exc:  # observability must not break publishing
                baseline_error = f"{type(exc).__name__}: {exc}"
            snapshot = termgov.snapshot_from_graph(
                SimpleNamespace(graph=self._graph), row["graph_iri"]
            )
            guard = termgate.evaluate_snapshot(
                snapshot,
                self._terms_gate,
                high_water=high_water,
                context={
                    "versionId": version_id,
                    "actor": actor,
                    "path": "POST /ontology/publish",
                    "purpose": purpose,
                    "purposeVerified": purpose_verified,
                    "purposeStatus": purpose_status,
                    "remoteAddr": remote_addr,
                    "activateExisting": bool(activate_existing),
                    "implicit": bool(implicit),
                    "baselineError": baseline_error,
                },
            )
            if guard is not None:
                gates["terms"] = guard
                termgate.remember(self, guard)
            if guard is not None and guard.get("blocked"):
                vocab_guard = guard.get("vocabGuard") or {}
                forged = next(
                    (item for item in (guard.get("findings") or [])
                     if item.get("code") == termgate.VOCAB_ZERO_FORGED_CODE),
                    None,
                )
                unconfigured = vocab_guard.get("tokenStatus") == "unconfigured"
                # 被拒也要进哈希链（含伪造尝试）；此时还没有 pid，隐式发布留空。
                self.record_publish_rejection(
                    version_id,
                    proposal["proposal_id"] if proposal else None,
                    actor, "term vocab guard blocked publish", guard,
                    mode="activate_existing" if activate_existing else (
                        "implicit" if implicit else "governed"
                    ),
                    path="POST /ontology/publish",
                )
                error = PortError(
                    code="Conflict",
                    message=(
                        "term vocab guard blocked publish: the effective term set dropped "
                        "to zero while the high-water mark is non-zero"
                        + (
                            "；smoke token 未配置，已按 fail-closed 处理（token 环境变量"
                            "未配置时一律拒绝豁免）"
                            if unconfigured
                            else ""
                        )
                    ),
                    provider="platform",
                    provider_code=termgate.E_TERM_GATE_BLOCKED,
                    details={
                        "versionId": version_id,
                        "gate": guard["gate"],
                        "verdict": guard["verdict"],
                        "vocabGuard": guard["vocabGuard"],
                        "findings": guard["findings"],
                        "exemptionRejected": forged.get("message") if forged else None,
                        "mode": "activate_existing" if activate_existing else (
                            "implicit" if implicit else "governed"
                        ),
                        "allowed": [
                            "publish a T-Box version that still carries the MetricScheme terms",
                            "a self-check probe must pass purpose=smoke with the "
                            "X-Smoke-Token header issued by the operator; the exemption "
                            "is recorded in the evidence pack and the ontology_event "
                            "audit chain",
                        ],
                    },
                )
                self._publish_evidence(
                    version_id=version_id, row=row, proposal=proposal,
                    mode="activate_existing" if activate_existing else "publish",
                    gates=gates, verdict="fail", actor=actor, reason=reason,
                    diff=diff, error=error,
                )
                raise error
        # --- end G8/O-05 vocab-zero guard ---

        current = self._meta.query(
            "SELECT version_id FROM platform.graph_pointer WHERE name = %s", (POINTER_NAME,)
        )
        previous_id = current[0]["version_id"] if current else None
        self._assert_pointer_precondition(
            version_id, expected_version_id, previous_id, actor, reason, "publish"
        )
        implicit_pid = f"prop-{uuid.uuid4().hex[:12]}" if implicit else None
        pid = proposal["proposal_id"] if proposal else implicit_pid
        impact = {
            "addedTriples": diff["summary"]["addedTriples"],
            "removedTriples": diff["summary"]["removedTriples"],
            "addedClasses": len(diff["summary"]["addedClasses"]),
            "removedClasses": len(diff["summary"]["removedClasses"]),
            "addedProperties": len(diff["summary"]["addedProperties"]),
            "removedProperties": len(diff["summary"]["removedProperties"]),
            "domainChanges": len(diff["summary"]["domainChanges"]),
            "rangeChanges": len(diff["summary"]["rangeChanges"]),
            "removedClassInstances": sum(
                item["instances"] for item in diff["summary"]["removedClassInstances"]
            ),
            "breakingItems": len(diff["breakingItems"]),
        } if implicit else {}

        with self._meta.tx() as tx:
            tx.execute("SELECT pg_advisory_xact_lock(hashtext('platform:ontology:publish'))")
            # Two concurrent publishes (e.g. the same import pushed twice) must
            # not both append a "published" event. Re-read state after the lock;
            # the loser returns the same idempotent payload as a repeat call.
            lock_rows = tx.query(
                "SELECT status FROM platform.ontology_version WHERE version_id = %s",
                (version_id,),
            )
            lock_ptr = tx.query(
                "SELECT version_id FROM platform.graph_pointer WHERE name = %s",
                (POINTER_NAME,),
            )
            locked_previous = lock_ptr[0]["version_id"] if lock_ptr else None
            if (
                lock_rows
                and lock_rows[0]["status"] == "published"
                and locked_previous == version_id
            ):
                return {
                    "id": version_id,
                    "semver": row["semver"],
                    "graph": row["graph_iri"],
                    "triples": count,
                    "proposalId": proposal["proposal_id"] if proposal else None,
                    "governed": True,
                    "implicitProposal": False,
                    "unchanged": True,
                    "idempotent": True,
                    "mode": "activate_existing" if activate_existing else "publish",
                    "previousVersionId": locked_previous,
                    "publishedBy": actor,
                    "gates": {},
                    "publishedAt": _now(),
                }
            previous_id = locked_previous
            if implicit:
                summary = "implicit proposal: direct publish"
                tx.execute(
                    """
                    INSERT INTO platform.ontology_proposal
                      (proposal_id, version_id, against_version, change_summary, status,
                       breaking, acknowledged_breaking, diff, impact, created_by,
                       approved_by, approved_at)
                    VALUES (%s, %s, %s, %s, 'approved', %s, %s, %s, %s, %s, %s, now())
                    """,
                    (
                        implicit_pid, version_id, diff.get("from"), summary,
                        bool(breaking), bool(acknowledge_breaking),
                        Jsonb(diff), Jsonb(impact), actor, actor,
                    ),
                )
                self._append_event(
                    tx, version_id, implicit_pid, "proposed", actor, None,
                    {"changeSummary": summary, "against": diff.get("from"),
                     "breaking": bool(breaking), "implicit": True, "impact": impact},
                )
                self._append_event(
                    tx, version_id, implicit_pid, "approved", actor, reason,
                    {"changeSummary": summary, "breaking": bool(breaking),
                     "implicit": True},
                )
                # O-02: an implicit proposal still walks the full chain, so the
                # lifecycle view never shows an approved/published proposal that
                # skipped review.
                record_transition(
                    tx, entity_kind="proposal", entity_id=implicit_pid,
                    version_id=version_id, proposal_id=implicit_pid,
                    from_status="proposed", to_status="review", actor=actor,
                    reason="implicit review during direct publish",
                    payload={"implicit": True, "mode": "direct_publish"},
                )
                record_transition(
                    tx, entity_kind="proposal", entity_id=implicit_pid,
                    version_id=version_id, proposal_id=implicit_pid,
                    from_status="review", to_status="approved", actor=actor,
                    reason=reason, payload={"breaking": bool(breaking), "implicit": True},
                )
            if acknowledge_breaking and breaking:
                if not implicit:
                    tx.execute(
                        "UPDATE platform.ontology_proposal SET acknowledged_breaking = true "
                        "WHERE proposal_id = %s",
                        (pid,),
                    )
                self._append_event(
                    tx, version_id, pid, "breaking_acknowledged",
                    actor, reason, {"breakingItems": diff.get("breakingItems", [])},
                )
            if previous_id and previous_id != version_id:
                prior = tx.query(
                    "SELECT status FROM platform.ontology_version WHERE version_id = %s",
                    (previous_id,),
                )
                tx.execute(
                    "UPDATE platform.ontology_version SET status = 'superseded' "
                    "WHERE version_id = %s AND status = 'published'",
                    (previous_id,),
                )
                self._append_event(
                    tx, previous_id, None, "superseded", actor, reason,
                    {"replacedBy": version_id},
                )
                if prior and prior[0]["status"] == "published":
                    record_transition(
                        tx, entity_kind="version", entity_id=previous_id,
                        version_id=previous_id, proposal_id=None,
                        from_status="published", to_status="superseded",
                        actor=actor, reason=reason or f"superseded by {version_id}",
                        payload={"replacedBy": version_id},
                    )
            # Forward publishing an existing version records this run's real
            # timestamp; a plain first publish has published_at NULL anyway.
            tx.execute(
                "UPDATE platform.ontology_version "
                "SET status = 'published', published_at = "
                "CASE WHEN %s THEN now() ELSE COALESCE(published_at, now()) END "
                "WHERE version_id = %s",
                (bool(activate_existing), version_id),
            )
            tx.execute(
                """
                INSERT INTO platform.graph_pointer (name, version_id, updated_at, updated_by)
                VALUES (%s, %s, now(), %s)
                ON CONFLICT (name) DO UPDATE
                  SET version_id = EXCLUDED.version_id, updated_at = now()
                """,
                (POINTER_NAME, version_id, actor),
            )
            if pid is not None:
                tx.execute(
                    "UPDATE platform.ontology_proposal "
                    "SET status = 'published', published_at = now() WHERE proposal_id = %s",
                    (pid,),
                )
            # 豁免关键字段进哈希链：``published`` 事件的 payload 里显式带一份
            # 术语门禁摘要（purpose / 是否豁免 / 判定结论 / 基线 / 当前值），
            # 使其不只存在于非链式的证据包表。gate=off 且未触发零术语时摘要为
            # None，不写键，保持 off 基线逐字一致。
            terms_audit = _term_audit_payload(gates)
            published_payload = {
                "mode": (
                    "activate_existing" if activate_existing
                    else ("implicit_governed" if implicit else "governed")
                ),
                "previous": previous_id,
                "previousVersionId": previous_id,
                "publishedBy": actor,
                "canonicalHash": row.get("content_hash"),
                "breaking": bool(breaking),
                "gates": gates,
            }
            if terms_audit is not None:
                published_payload["terms"] = terms_audit
            self._append_event(
                tx, version_id, pid, "published", actor, reason,
                published_payload,
            )
            # O-02: close the chain with approved -> published on both the
            # proposal and the version entity.
            if pid is not None:
                proposal_payload = {
                    "previousVersionId": previous_id,
                    "mode": "activate_existing" if activate_existing else "publish",
                }
                if terms_audit is not None:
                    proposal_payload["terms"] = terms_audit
                record_transition(
                    tx, entity_kind="proposal", entity_id=pid,
                    version_id=version_id, proposal_id=pid,
                    from_status="approved", to_status="published",
                    actor=actor, reason=reason,
                    payload=proposal_payload,
                )
            version_payload = {
                "previousVersionId": previous_id,
                "activateExisting": bool(activate_existing),
            }
            if terms_audit is not None:
                version_payload["terms"] = terms_audit
            record_transition(
                tx, entity_kind="version", entity_id=version_id,
                version_id=version_id, proposal_id=pid,
                from_status=row["status"], to_status="published",
                actor=actor, reason=reason,
                payload=version_payload,
            )

        if governed or implicit:
            if self._materializer is None:
                self._restore_after_failed_publish(
                    version_id, previous_id, pid, actor,
                    "materializer not configured",
                )
                evidence = self._publish_evidence(
                    version_id=version_id, row=row, proposal=proposal,
                    mode="activate_existing" if activate_existing else "publish",
                    gates=gates, verdict="fail", actor=actor, reason=reason,
                    diff=diff, error=PortError(
                        code="Unsupported",
                        message="materialization gate is not configured",
                        provider="platform",
                        provider_code="E_ONTOLOGY_GATE_UNAVAILABLE",
                    ),
                )
                raise PortError(
                    code="Unsupported",
                    message="materialization gate is not configured; publish reverted",
                    provider="platform",
                    provider_code="E_ONTOLOGY_GATE_UNAVAILABLE",
                )
            try:
                materialized = self._materializer()
                gates["materialization"] = {
                    "jobId": materialized.get("jobId"),
                    "inferred": materialized.get("inferred"),
                    "skipped": materialized.get("skipped"),
                    # reasoning.materialize_online=false records the deferral here
                    # so evidence says "offline window" instead of an unexplained skip.
                    "deferred": materialized.get("deferred"),
                }
            except Exception as exc:
                cause_code = getattr(exc, "provider_code", None) or getattr(exc, "code", "Internal")
                cause_detail = getattr(exc, "message", None) or str(exc)
                self._restore_after_failed_publish(
                    version_id, previous_id, pid, actor, cause_detail,
                )
                evidence = self._publish_evidence(
                    version_id=version_id, row=row, proposal=proposal,
                    mode="activate_existing" if activate_existing else "publish",
                    gates=gates, verdict="fail", actor=actor, reason=reason,
                    diff=diff, error=PortError(
                        code="Conflict",
                        message=f"materialization failed: {cause_detail}",
                        provider="platform",
                        provider_code="E_ONTOLOGY_MATERIALIZE_FAILED",
                        details={"cause": cause_code, "detail": cause_detail},
                    ),
                )
                log.warning(
                    "ontology publish reverted after materialization failure",
                    extra={"event": {"event": "ontology_publish_reverted",
                                     "version_id": version_id, "error": cause_detail}},
                )
                raise PortError(
                    code="Conflict",
                    message=f"materialization failed; publish reverted: {cause_detail}",
                    provider="platform",
                    provider_code="E_ONTOLOGY_MATERIALIZE_FAILED",
                    details={"cause": cause_code, "detail": cause_detail},
                ) from exc

        # The pointer now points at this version, so it is the effective term set;
        # raise (never lower) the high-water mark used by the vocab-zero guard.
        if self._terms_gate is not None:
            try:
                raise_term_high_water(
                    self._meta,
                    termgov.measure_graph(SimpleNamespace(graph=self._graph), row["graph_iri"]),
                    version_id,
                    row["graph_iri"],
                )
            except Exception as exc:  # marking must not turn a publish into a failure
                log.warning(
                    "term high-water mark not raised",
                    extra={"event": {"event": "term_high_water_failed",
                                     "version_id": version_id, "error": str(exc)}},
                )

        evidence = self._publish_evidence(
            version_id=version_id, row=row, proposal=proposal,
            mode="activate_existing" if activate_existing else "publish",
            gates=gates, verdict="pass", actor=actor, reason=reason, diff=diff,
        )
        log.info(
            "ontology published",
            extra={
                "event": {
                    "event": "ontology_publish",
                    "version_id": version_id,
                    "graph": row["graph_iri"],
                    "triples": count,
                    "governed": True,
                    "implicit": implicit,
                }
            },
        )
        return {
            "id": version_id,
            "semver": row["semver"],
            "graph": row["graph_iri"],
            "triples": count,
            "proposalId": pid,
            "governed": True,
            "implicitProposal": bool(implicit),
            "mode": "activate_existing" if activate_existing else "publish",
            "previousVersionId": previous_id,
            "publishedBy": actor,
            "idempotent": False,
            "gates": gates,
            "evidence": evidence,
            "publishedAt": _now(),
        }

    def _restore_after_failed_publish(
        self, version_id: str, previous_id: str | None, proposal_id: str | None,
        actor: str, cause: str,
    ) -> None:
        with self._meta.tx() as tx:
            tx.execute(
                "UPDATE platform.ontology_version SET status = 'approved' "
                "WHERE version_id = %s",
                (version_id,),
            )
            if proposal_id:
                tx.execute(
                    "UPDATE platform.ontology_proposal SET status = 'approved', "
                    "published_at = NULL WHERE proposal_id = %s",
                    (proposal_id,),
                )
            if previous_id:
                tx.execute(
                    "UPDATE platform.ontology_version SET status = 'published' "
                    "WHERE version_id = %s",
                    (previous_id,),
                )
                tx.execute(
                    """
                    INSERT INTO platform.graph_pointer (name, version_id, updated_at, updated_by)
                    VALUES (%s, %s, now(), %s)
                    ON CONFLICT (name) DO UPDATE
                      SET version_id = EXCLUDED.version_id, updated_at = now()
                    """,
                    (POINTER_NAME, previous_id, actor),
                )
            else:
                tx.execute(
                    "DELETE FROM platform.graph_pointer WHERE name = %s", (POINTER_NAME,)
                )
            self._append_event(
                tx, version_id, proposal_id, "publish_reverted", actor, cause,
                {"previous": previous_id, "cause": cause},
            )

    def rollback_to(
        self, version_id: str, actor: str = "operator", reason: str | None = None,
        expected_version_id: str | None = None,
    ) -> dict[str, Any]:
        target = self._require(version_id)
        if target["status"] == "draft":
            raise PortError(
                code="Conflict",
                message=f"version {version_id} is draft; only imported/reviewed history can be restored",
                provider="platform",
                provider_code="E_ONTOLOGY_STATUS",
                details={"status": target["status"]},
            )
        # B-5: archived versions are read-only baselines. Activating one would
        # rebuild its graph from the original TTL, which for pre-S14H-P0 rows
        # carries a different canonical hash. Use restore-deprecated (batch) or
        # re-import the source as a new version instead.
        if target["status"] == "deprecated":
            raise PortError(
                code="Conflict",
                message=(
                    f"version {version_id} is deprecated; archived versions are read-only "
                    "baselines (use restore-deprecated or import the source again)"
                ),
                provider="platform",
                provider_code="E_ONTOLOGY_READONLY",
                details={"status": target["status"], "readOnly": True},
            )
        self._ensure_graph(target)
        current = self._meta.query(
            "SELECT version_id FROM platform.graph_pointer WHERE name = %s", (POINTER_NAME,)
        )
        previous_id = current[0]["version_id"] if current else None
        self._assert_pointer_precondition(
            version_id, expected_version_id, previous_id, actor, reason, "rollback"
        )
        if previous_id == version_id:
            return {
                "id": version_id, "status": "published", "previous": version_id,
                "unchanged": True, "graph": target["graph_iri"],
            }
        with self._meta.tx() as tx:
            tx.execute("SELECT pg_advisory_xact_lock(hashtext('platform:ontology:publish'))")
            if previous_id:
                prior = tx.query(
                    "SELECT status FROM platform.ontology_version WHERE version_id = %s",
                    (previous_id,),
                )
                tx.execute(
                    "UPDATE platform.ontology_version SET status = 'superseded' "
                    "WHERE version_id = %s AND status = 'published'",
                    (previous_id,),
                )
                self._append_event(
                    tx, previous_id, None, "superseded", actor, reason,
                    {"rolledBackTo": version_id},
                )
                if prior and prior[0]["status"] == "published":
                    record_transition(
                        tx, entity_kind="version", entity_id=previous_id,
                        version_id=previous_id, proposal_id=None,
                        from_status="published", to_status="superseded",
                        actor=actor, reason=reason or f"rolled back to {version_id}",
                        payload={"rolledBackTo": version_id},
                    )
            tx.execute(
                "UPDATE platform.ontology_version "
                "SET status = 'published', published_at = COALESCE(published_at, now()) "
                "WHERE version_id = %s",
                (version_id,),
            )
            tx.execute(
                """
                INSERT INTO platform.graph_pointer (name, version_id, updated_at, updated_by)
                VALUES (%s, %s, now(), %s)
                ON CONFLICT (name) DO UPDATE
                  SET version_id = EXCLUDED.version_id, updated_at = now()
                """,
                (POINTER_NAME, version_id, actor),
            )
            self._append_event(
                tx, version_id, None, "rolled_back", actor, reason,
                {
                    "previous": previous_id,
                    "previousVersionId": previous_id,
                    "target": version_id,
                    "publishedBy": actor,
                },
            )
            record_transition(
                tx, entity_kind="version", entity_id=version_id,
                version_id=version_id, proposal_id=None,
                from_status=target["status"], to_status="published",
                actor=actor, reason=reason,
                payload={"previousVersionId": previous_id, "mode": "rollback"},
            )
        if self._materializer is not None:
            try:
                self._materializer()
            except Exception as exc:  # keep the pointer on the target
                log.warning(
                    "ontology rollback materialization failed",
                    extra={"event": {"event": "ontology_rollback_materialize_failed",
                                     "error": str(exc)}},
                )
        return {
            "id": version_id,
            "semver": target["semver"],
            "status": "published",
            "previous": previous_id,
            "graph": target["graph_iri"],
            "triples": target["triple_count"],
            "publishedAt": _now(),
        }

    # ---- diff / export ---------------------------------------------------

    def deprecate(
        self,
        version_id: str,
        actor: str = "operator",
        reason: str | None = None,
        note: str | None = None,
        batch: str | None = None,
    ) -> dict[str, Any]:
        """Retire a non-current version without deleting rows or audit events."""
        target = self._require(version_id)
        pointer = self._pointer()
        if pointer and pointer["versionId"] == version_id:
            raise PortError(
                code="Conflict",
                message=f"version {version_id} is the current pointer; roll back first",
                provider="platform",
                provider_code="E_ONTOLOGY_ACTIVE_VERSION",
                details={"versionId": version_id},
            )
        if target["status"] == "deprecated":
            return {
                "id": version_id, "status": "deprecated", "unchanged": True,
                "previousStatus": "deprecated",
            }
        with self._meta.tx() as tx:
            tx.execute("SELECT pg_advisory_xact_lock(hashtext('platform:ontology:publish'))")
            tx.execute(
                "UPDATE platform.ontology_version SET status = 'deprecated' "
                "WHERE version_id = %s AND status <> 'deprecated'",
                (version_id,),
            )
            payload: dict[str, Any] = {
                "previousStatus": target["status"],
                "note": note or reason,
            }
            if batch:
                payload["batch"] = batch
            self._append_event(
                tx, version_id, None, "deprecated", actor, reason, payload,
            )
            record_transition(
                tx, entity_kind="version", entity_id=version_id,
                version_id=version_id, proposal_id=None,
                from_status=target["status"], to_status="deprecated",
                actor=actor, reason=reason, payload=payload,
            )
        return {
            "id": version_id,
            "semver": target["semver"],
            "previousStatus": target["status"],
            "status": "deprecated",
            "deprecatedBy": actor,
            "note": note or reason,
        }

    def deprecate_batch(
        self,
        version_ids: list[str],
        actor: str = "archive-bot",
        reason: str | None = None,
        batch: str | None = None,
    ) -> dict[str, Any]:
        """Deprecate many versions one-by-one; each keeps its own audit event."""
        deprecated = unchanged = 0
        failed: list[dict[str, Any]] = []
        for version_id in version_ids:
            try:
                result = self.deprecate(
                    version_id, actor=actor, reason=reason, batch=batch
                )
                if result.get("unchanged"):
                    unchanged += 1
                else:
                    deprecated += 1
            except PortError as exc:
                failed.append({"id": version_id, "code": exc.provider_code or exc.code})
        return {
            "batch": batch,
            "requested": len(version_ids),
            "deprecated": deprecated,
            "unchanged": unchanged,
            "failed": failed,
        }

    def restore_deprecated(
        self,
        batch: str,
        actor: str = "operator",
        reason: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Undo a deprecate batch by reversing the latest event that carries `batch`.

        Statuses are restored to the `previousStatus` recorded on the event and a
        new `restored` event is appended, so the hash chain stays intact.
        """
        rows = self._meta.query(
            """
            SELECT DISTINCT ON (version_id) version_id, event_id, payload
              FROM platform.ontology_event
             WHERE action = 'deprecated' AND payload->>'batch' = %s
             ORDER BY version_id, event_id DESC
            """,
            (batch,),
        )
        targets: list[dict[str, Any]] = []
        for row in rows:
            current = self._require(str(row["version_id"]))
            if current["status"] != "deprecated":
                continue
            payload = row["payload"] or {}
            previous = str(payload.get("previousStatus") or "superseded")
            if previous == "deprecated":
                continue
            targets.append({
                "id": str(row["version_id"]),
                "eventId": int(row["event_id"]),
                "previousStatus": previous,
            })
        if dry_run:
            return {"batch": batch, "dryRun": True, "restorable": len(targets), "items": targets}
        restored = 0
        for item in targets:
            with self._meta.tx() as tx:
                tx.execute("SELECT pg_advisory_xact_lock(hashtext('platform:ontology:publish'))")
                tx.execute(
                    "UPDATE platform.ontology_version SET status = %s "
                    "WHERE version_id = %s AND status = 'deprecated'",
                    (item["previousStatus"], item["id"]),
                )
                self._append_event(
                    tx, item["id"], None, "restored", actor, reason,
                    {
                        "batch": batch,
                        "previousStatus": "deprecated",
                        "restoredTo": item["previousStatus"],
                        "note": reason,
                    },
                )
            restored += 1
        return {"batch": batch, "dryRun": False, "restored": restored, "targets": len(targets)}

    @staticmethod
    def _term_text(term: dict[str, Any]) -> str:
        if term.get("kind") == "iri":
            return term.get("iri") or ""
        return term.get("value") or ""

    def _query_terms(self, graph_iri: str, pattern: str) -> set[str]:
        result = self._graph.query(
            f"SELECT DISTINCT ?v WHERE {{ GRAPH <{graph_iri}> {{ {pattern} }} }}"
        )
        return {
            self._term_text(b["values"]["v"]) for b in result["bindings"]
            if b.get("values", {}).get("v")
        }

    def _query_pairs(self, graph_iri: str, predicate: str) -> dict[str, set[str]]:
        result = self._graph.query(
            f"SELECT DISTINCT ?p ?v WHERE {{ GRAPH <{graph_iri}> "
            f"{{ ?p <{predicate}> ?v }} }}"
        )
        out: dict[str, set[str]] = {}
        for binding in result["bindings"]:
            values = binding.get("values", {})
            if "p" not in values or "v" not in values:
                continue
            p = self._term_text(values["p"])
            v = self._term_text(values["v"])
            out.setdefault(p, set()).add(v)
        return out

    def _required_properties(self, graph_iri: str) -> set[str]:
        result = self._graph.query(
            f"""
            SELECT DISTINCT ?v WHERE {{
              GRAPH <{graph_iri}> {{
                ?r a <{OWL_RESTRICTION}> ;
                   <{OWL_ON_PROPERTY}> ?v ;
                   ?card ?n .
                VALUES ?card {{ <{OWL_MIN_CARD}> <{OWL_MIN_QCARD}> }}
                FILTER(?n > 0)
              }}
            }}
            """
        )
        return {
            self._term_text(b["values"]["v"]) for b in result["bindings"]
            if b.get("values", {}).get("v")
        }

    def _instance_count(self, class_iri: str) -> int:
        if not self._abox_graphs:
            return 0
        values = " ".join(f"<{g}>" for g in self._abox_graphs)
        result = self._graph.query(
            f"""
            SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {{
              VALUES ?g {{ {values} }}
              GRAPH ?g {{ ?s a <{class_iri}> }}
            }}
            """
        )
        if not result["bindings"]:
            return 0
        return int(result["bindings"][0]["values"]["n"]["value"])

    @staticmethod
    def _markdown_diff(diff: dict[str, Any]) -> str:
        s = diff["summary"]
        lines = [
            f"## Ontology diff: {diff['from'] or '(empty)'} -> {diff['to']}",
            "",
            f"- added classes: {len(s['addedClasses'])}",
            f"- removed classes: {len(s['removedClasses'])}",
            f"- added properties: {len(s['addedProperties'])}",
            f"- removed properties: {len(s['removedProperties'])}",
            f"- added triples: {s['addedTriples']}",
            f"- removed triples: {s['removedTriples']}",
        ]
        for item in s["addedClasses"]:
            lines.append(f"  - + class `{item}`")
        for item in s["removedClasses"]:
            lines.append(f"  - - class `{item}`")
        for item in s["addedProperties"]:
            lines.append(f"  - + property `{item}`")
        for item in s["removedProperties"]:
            lines.append(f"  - - property `{item}`")
        for item in s["domainChanges"]:
            lines.append(
                f"  - domain `{item['property']}`: {item['from']} -> {item['to']}"
            )
        for item in s["rangeChanges"]:
            lines.append(
                f"  - range `{item['property']}`: {item['from']} -> {item['to']}"
            )
        for item in s["removedClassInstances"]:
            lines.append(f"  - instances of removed class `{item['class']}`: {item['instances']}")
        lines.append("")
        if diff["breaking"]:
            lines.append("### Breaking changes (acknowledgement required)")
            for item in diff["breakingItems"]:
                lines.append(f"- `{item['kind']}`: {item.get('iri') or item.get('property')}")
        else:
            lines.append("### No breaking changes")
        return "\n".join(lines)

    def diff(self, from_version_id: str | None, to_version_id: str) -> dict[str, Any]:
        to_row = self._require(to_version_id)
        from_row = self._require(from_version_id) if from_version_id else None
        if from_row:
            self._ensure_graph(from_row)
        self._ensure_graph(to_row)
        return self.diff_graphs(
            from_row["graph_iri"] if from_row else None,
            to_row["graph_iri"],
            from_version_id=from_version_id,
            to_version_id=to_version_id,
        )

    def diff_graphs(
        self,
        from_graph: str | None,
        to_graph: str,
        *,
        from_version_id: str | None = None,
        to_version_id: str | None = None,
    ) -> dict[str, Any]:
        """Diff two graph IRIs (G-01 publish dry-run compares a staging graph)."""
        if from_graph:
            added = self._graph.query(
                f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{to_graph}> {{ ?s ?p ?o }} "
                f"MINUS {{ GRAPH <{from_graph}> {{ ?s ?p ?o }} }} }}"
            )
            removed = self._graph.query(
                f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{from_graph}> {{ ?s ?p ?o }} "
                f"MINUS {{ GRAPH <{to_graph}> {{ ?s ?p ?o }} }} }}"
            )
            added_n = int(added["bindings"][0]["values"]["n"]["value"])
            removed_n = int(removed["bindings"][0]["values"]["n"]["value"])
        else:
            added_n = self._graph.count_graph(to_graph)
            removed_n = 0

        class_pattern = (
            "?v a ?t . VALUES ?t { "
            f"<{OWL_CLASS}> <{RDFS_CLASS}> }}"
        )
        property_pattern = (
            "?v a ?t . VALUES ?t { "
            f"<{OWL_OBJECT}> <{OWL_DATATYPE}> <{OWL_ANNOTATION}> }}"
        )
        empty: set[str] = set()
        to_classes = self._query_terms(to_graph, class_pattern)
        from_classes = self._query_terms(from_graph, class_pattern) if from_graph else empty
        to_props = self._query_terms(to_graph, property_pattern)
        from_props = self._query_terms(from_graph, property_pattern) if from_graph else empty

        to_domains = self._query_pairs(to_graph, RDFS_DOMAIN)
        from_domains = self._query_pairs(from_graph, RDFS_DOMAIN) if from_graph else {}
        to_ranges = self._query_pairs(to_graph, RDFS_RANGE)
        from_ranges = self._query_pairs(from_graph, RDFS_RANGE) if from_graph else {}
        to_required = self._required_properties(to_graph)
        from_required = self._required_properties(from_graph) if from_graph else empty

        domain_changes = []
        for prop in sorted(set(to_domains) | set(from_domains)):
            before = sorted(from_domains.get(prop, empty))
            after = sorted(to_domains.get(prop, empty))
            if before != after:
                domain_changes.append({"property": prop, "from": before, "to": after})
        range_changes = []
        for prop in sorted(set(to_ranges) | set(from_ranges)):
            before = sorted(from_ranges.get(prop, empty))
            after = sorted(to_ranges.get(prop, empty))
            if before != after:
                range_changes.append({"property": prop, "from": before, "to": after})

        removed_classes = sorted(from_classes - to_classes)
        removed_instances = [
            {"class": cls, "instances": self._instance_count(cls)}
            for cls in removed_classes
        ]

        breaking_items: list[dict[str, Any]] = []
        if from_graph:
            for cls in removed_classes:
                breaking_items.append({"kind": "class_removed", "iri": cls})
            for prop in sorted(from_props - to_props):
                breaking_items.append({"kind": "property_removed", "iri": prop})
            for item in domain_changes:
                if set(item["from"]) - set(item["to"]):
                    breaking_items.append(
                        {"kind": "domain_narrowed", "property": item["property"],
                         "from": item["from"], "to": item["to"]}
                    )
            for item in range_changes:
                if set(item["from"]) - set(item["to"]):
                    breaking_items.append(
                        {"kind": "range_narrowed", "property": item["property"],
                         "from": item["from"], "to": item["to"]}
                    )
            for prop in sorted(to_required - from_required):
                breaking_items.append({"kind": "property_became_required", "iri": prop})

        diff = {
            "from": from_version_id,
            "to": to_version_id,
            "summary": {
                "addedTriples": added_n,
                "removedTriples": removed_n,
                "addedClasses": sorted(to_classes - from_classes),
                "removedClasses": removed_classes,
                "addedProperties": sorted(to_props - from_props),
                "removedProperties": sorted(from_props - to_props),
                "domainChanges": domain_changes,
                "rangeChanges": range_changes,
                "removedClassInstances": removed_instances,
            },
            "breaking": bool(breaking_items),
            "breakingItems": breaking_items,
        }
        diff["markdown"] = self._markdown_diff(diff)
        return diff

    def export_version(self, version_id: str, rdf_format: str = "turtle") -> dict[str, Any]:
        if rdf_format not in ("turtle", "nquads"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported export format: {rdf_format}",
                provider="platform",
                provider_code="E_ONTOLOGY_EXPORT_FORMAT",
                details={"allowed": ["turtle", "nquads"]},
            )
        row = self._require(version_id)
        self._ensure_graph(row)
        nt = self._graph.export_graph(row["graph_iri"])
        if rdf_format == "turtle":
            graph = Graph()
            graph.parse(data=nt.decode("utf-8"), format="nt")
            content = graph.serialize(format="turtle")
        else:
            lines = []
            for line in nt.decode("utf-8").splitlines():
                line = line.strip()
                if not line.endswith("."):
                    continue
                lines.append(line[:-1].rstrip() + f" <{row['graph_iri']}> .")
            content = "\n".join(lines) + ("\n" if lines else "")
        return {
            "versionId": version_id,
            "format": rdf_format,
            "graph": row["graph_iri"],
            "triples": row["triple_count"],
            "content": content,
        }

    def rollback(self, to_version_id: str, namespace_id: str | None = None) -> dict[str, Any]:
        target = self._require(to_version_id)
        # The new row restores the target's content, so it belongs to the same
        # namespace. Inheriting is the only honest default: a legacy target with
        # no owner stays unowned instead of being guessed into one.
        owner_namespace = _owner_namespace_id(namespace_id)
        owner_source = OWNER_SOURCE_PLATFORM if owner_namespace else None
        if not owner_namespace:
            owner_namespace = target.get("namespace_id")
            owner_source = target.get("attribution_source")
        # Target content must still be in the graph; reload from CAS if not.
        if self._graph.count_graph(target["graph_iri"]) != target["triple_count"]:
            self._load_graph(target)

        prior = self._meta.query(
            "SELECT COUNT(*) AS n FROM platform.ontology_version WHERE rollback_of = %s",
            (to_version_id,),
        )
        attempt = int(prior[0]["n"]) + 1
        new_id = f"ont-{uuid.uuid4().hex[:12]}"
        semver = f"{target['semver']}+rollback.{attempt}"

        with self._meta.tx() as tx:
            tx.execute("SELECT pg_advisory_xact_lock(hashtext('platform:ontology:publish'))")
            tx.execute(
                """
                INSERT INTO platform.ontology_version
                  (version_id, semver, status, content_hash, triple_count, source_format,
                   source_key, graph_iri, rollback_of, label, published_at,
                   namespace_id, attribution_source)
                VALUES (%s, %s, 'published', %s, %s, %s, %s, %s, %s, %s, now(), %s, %s)
                """,
                (
                    new_id, semver, target["content_hash"], target["triple_count"],
                    target["source_format"], target["source_key"], target["graph_iri"],
                    to_version_id, f"rollback of {to_version_id}",
                    owner_namespace, owner_source,
                ),
            )
            current = tx.query(
                "SELECT version_id FROM platform.graph_pointer WHERE name = %s", (POINTER_NAME,)
            )
            if current and current[0]["version_id"] != new_id:
                tx.execute(
                    "UPDATE platform.ontology_version SET status = 'superseded' "
                    "WHERE version_id = %s AND status = 'published'",
                    (current[0]["version_id"],),
                )
            tx.execute(
                """
                INSERT INTO platform.graph_pointer (name, version_id, updated_at, updated_by)
                VALUES (%s, %s, now(), 'local')
                ON CONFLICT (name) DO UPDATE
                  SET version_id = EXCLUDED.version_id, updated_at = now()
                """,
                (POINTER_NAME, new_id),
            )
        log.info(
            "ontology rolled back",
            extra={
                "event": {
                    "event": "ontology_rollback",
                    "new_version_id": new_id,
                    "to": to_version_id,
                    "graph": target["graph_iri"],
                }
            },
        )
        return {
            "id": new_id,
            "semver": semver,
            "status": "published",
            "rollbackOf": to_version_id,
            "graph": target["graph_iri"],
            "contentHash": target["content_hash"],
            "publishedAt": _now(),
        }

    # ---- read ------------------------------------------------------------

    def get(self, version_id: str) -> dict[str, Any]:
        return _row_to_version(self._require(version_id))

    def list_versions(
        self, include_deprecated: bool = True, namespace_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Versions, optionally scoped to one namespace.

        Without ``namespace_id`` the legacy single-tenant view is preserved:
        every row is returned, attributed or not. With it, only rows whose V52
        owner is that namespace are returned; rows with NULL are never treated
        as "this namespace" -- ``count_unattributed_versions`` reports them so
        the caller can see the gap instead of silently getting a smaller list.
        """
        clauses: list[str] = []
        params: list[Any] = []
        if not include_deprecated:
            clauses.append("status <> 'deprecated'")
        if namespace_id is not None:
            owner = _owner_namespace_id(namespace_id)
            if owner is None:
                raise PortError(
                    code="InvalidArgument",
                    message="namespaceId must be a non-empty UUID when filtering versions",
                    provider="platform",
                    provider_code="E_ONTOLOGY_BAD_NAMESPACE_ID",
                )
            clauses.append("namespace_id = %s")
            params.append(owner)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._meta.query(
            f"""
            SELECT version_id, semver, status, content_hash, triple_count, source_format,
                   source_key, graph_iri, rollback_of, label, created_at, published_at
              FROM platform.ontology_version
              {where}
             ORDER BY created_at
            """,
            tuple(params),
        )
        return [_row_to_version(row) for row in rows]

    def count_unattributed_versions(self, include_deprecated: bool = True) -> int:
        """Rows that belong to no namespace yet (V52 NULL), same window as the list."""
        clause = "" if include_deprecated else "AND status <> 'deprecated'"
        rows = self._meta.query(
            "SELECT count(*) AS n FROM platform.ontology_version "
            f"WHERE namespace_id IS NULL {clause}"
        )
        return int(rows[0]["n"])

    def current(self) -> dict[str, Any] | None:
        return self._pointer()

    def graph_count(self, version_id: str) -> int:
        row = self._require(version_id)
        return self._graph.count_graph(row["graph_iri"])

    def status(self) -> dict[str, Any]:
        return {"pointer": self._pointer(), "versions": self.list_versions()}

    # ---- init job (`served` by serve) ------------------------------------

    def record_job(
        self, kind: str, status: str, detail: dict[str, Any], error: str | None = None,
        job_id: str | None = None, started_at: str | None = None,
    ) -> str:
        job_id = job_id or f"job-{uuid.uuid4().hex[:12]}"
        with self._meta.tx() as tx:
            if started_at:
                tx.execute(
                    """
                    INSERT INTO platform.ontology_job
                      (job_id, kind, status, detail, error, started_at, finished_at)
                    VALUES (%s, %s, %s, %s, %s, %s, now())
                    ON CONFLICT (job_id) DO UPDATE
                      SET status = EXCLUDED.status, detail = EXCLUDED.detail,
                          error = EXCLUDED.error, finished_at = now()
                    """,
                    (job_id, kind, status, Jsonb(detail), error, started_at),
                )
            else:
                tx.execute(
                    """
                    INSERT INTO platform.ontology_job (job_id, kind, status, detail, error, finished_at)
                    VALUES (%s, %s, %s, %s, %s, now())
                    """,
                    (job_id, kind, status, Jsonb(detail), error),
                )
        return job_id

    def bootstrap(self, source: str, semver: str) -> dict[str, Any]:
        """Import+publish the bootstrap file when its content differs from the pointer."""
        started = _now()
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        path = Path(source)
        if not path.is_file():
            self.record_job(
                "ontology_init", "skipped", {"source": source, "reason": "missing"},
                job_id=job_id,
            )
            return {"status": "skipped", "reason": "source missing", "source": source}

        row = self._meta.query(
            """
            SELECT v.version_id, v.content_hash, v.semver FROM platform.graph_pointer p
              JOIN platform.ontology_version v ON v.version_id = p.version_id
             WHERE p.name = %s
            """,
            (POINTER_NAME,),
        )
        if row:
            # The init watcher only owns versions it published itself (semver
            # = init_semver). A user/CLI published T-Box must not be clobbered
            # on the next poll, otherwise S7 imports vanish within one tick.
            if str(row[0]["semver"]) != semver:
                self.record_job(
                    "ontology_init", "skipped",
                    {
                        "source": source,
                        "reason": "pointer managed outside init source",
                        "version_id": row[0]["version_id"],
                        "semver": row[0]["semver"],
                    },
                    job_id=job_id, started_at=started,
                )
                return {
                    "status": "skipped",
                    "reason": "pointer managed outside init source",
                    "versionId": row[0]["version_id"],
                }
            try:
                _, _, triples = self._load_source(source)
            except PlatformError as exc:
                self.record_job(
                    "ontology_init", "failed", {"source": source}, exc.detail,
                    job_id=job_id, started_at=started,
                )
                raise
            if _content_hash(triples) == row[0]["content_hash"]:
                self.record_job(
                    "ontology_init", "skipped",
                    {"source": source, "reason": "unchanged", "version_id": row[0]["version_id"]},
                    job_id=job_id, started_at=started,
                )
                return {"status": "skipped", "reason": "unchanged", "versionId": row[0]["version_id"]}

        imported = self.import_source(source, semver, label="bootstrap")
        published = self.publish(imported["versionId"])
        self.record_job(
            "ontology_init", "done",
            {"source": source, "version_id": imported["versionId"], "graph": published["graph"]},
            job_id=job_id, started_at=started,
        )
        return {"status": "done", "versionId": imported["versionId"], **published}
