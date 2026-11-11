"""Reasoning orchestration (S5/S7): RDFS closure -> EL materialization -> SHACL gate.

Boundary (D18): no classification, closure or consistency algorithm lives here.
The reasoner container runs Jena `riot --rdfs` (stage 1) then ROBOT/ELK (stage 2);
pySHACL validates (stage 3). This service only computes set differences, enforces
atomicity/idempotency/locking and records jobs + pointer (OQ-39).
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import rdflib

from .adapters.graph_oxigraph import IRI_RE
from .adapters.metadata_pg import MetadataPg
from .adapters.ontology_pg import OntologyRegistry
from .adapters.reasoner_robot import ReasonerClient
from .config import ReasoningConfig
from .errors import PortError
from .ports import Manifest
from .validation import ShaclValidator

log = logging.getLogger(__name__)

POINTER_NAME = "default"
SUPPORTED_MODES = ("rdfs", "materialize", "validate")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReasoningService:
    port = "ReasoningService"

    def __init__(
        self,
        config: ReasoningConfig,
        metadata: MetadataPg,
        graph: Any,
        reasoner: ReasonerClient,
        validator: ShaclValidator,
        ontology: OntologyRegistry,
        consistency_reasoner: Any | None = None,
    ) -> None:
        self._config = config
        self._meta = metadata
        self._graph = graph
        self._reasoner = reasoner
        self._validator = validator
        self._ontology = ontology
        # Q8-b: engine=hermit routes the consistency gate to ROBOT/HermiT while
        # materialize keeps the existing ROBOT/ELK path.
        self._consistency_reasoner = consistency_reasoner

    def manifest(self) -> Manifest:
        return Manifest(
            provider=f"robot/{self._config.profile}",
            port=self.port,
            provider_version="s5.1",
            capabilities=["reason.materialize", "reason.rdfs", "shacl.validate"],
            limits={"timeout_ms": self._config.timeout_ms},
            notes={
                "slice": "S5",
                "mode": self._config.mode,
                "profile": self._config.profile,
                "engine": self._config.engine,
                "shapesDir": self._config.shapes_dir,
                "inferredGraphPrefix": self._config.inferred_graph_prefix,
                "chain": "rdfs(jena riot) -> owl(robot/elk) -> shacl gate; one target graph",
                "not_implemented": ["query_rewriting", "incremental", "owl2dl"],
            },
        )

    # ---- SHACL -----------------------------------------------------------

    def check_consistency(self, tbox_nt: bytes) -> dict[str, Any]:
        """ROBOT/ELK consistency check for an import candidate T-Box."""
        if self._reasoner is None:
            raise PortError(
                code="Unsupported",
                message="reasoner is not configured",
                provider="platform",
                provider_code="E_CONSISTENCY_UNAVAILABLE",
            )
        if self._consistency_reasoner is not None:
            return self._consistency_reasoner.check_consistency(tbox_nt)
        result = self._reasoner.reason(
            tbox_nt, b"", profile=self._config.profile, consistency_first=True
        )
        result.setdefault("engine", f"robot/{self._config.profile}")
        return result

    def validate(self, target: str = "abox") -> dict[str, Any]:
        graph_iri = self._resolve_target(target)
        started = time.monotonic()
        try:
            data_nt = self._graph.export_graph(graph_iri)
        except PortError as exc:
            if exc.provider_code == "E_GRAPH_BAD_IRI":
                raise PortError(
                    code="InvalidArgument",
                    message=f"invalid validation target: {target!r}",
                    provider="platform",
                    provider_code="E_VALIDATE_TARGET",
                    details={"target": target},
                ) from exc
            raise
        result = self._validator.validate(data_nt, graph_iri)
        result["ms"] = int((time.monotonic() - started) * 1000)
        return result

    def _resolve_target(self, target: str) -> str:
        if target == "abox":
            return self._config.abox_graphs[0]
        if target == "tbox":
            pointer = self._ontology.current()
            if not pointer:
                raise PortError(
                    code="NotFound",
                    message="no published T-Box version to validate",
                    provider="platform",
                    provider_code="E_ONTOLOGY_NO_PUBLISHED",
                )
            return str(pointer["graph"])
        if target and ":" in target and IRI_RE.match(target):
            return target
        raise PortError(
            code="InvalidArgument",
            message=f"validation target must be 'abox', 'tbox' or an IRI, got {target!r}",
            provider="platform",
            provider_code="E_VALIDATE_TARGET",
            details={"target": target, "allowed": ["abox", "tbox", "<iri>"]},
        )

    # ---- materialization -------------------------------------------------

    def target_graph(self, version_id: str) -> str:
        return f"{self._config.inferred_graph_prefix}{version_id}"

    def publish_materializer(self) -> dict[str, Any]:
        """Materialization hook for governed publish and rollback.

        ``reasoning.materialize_online=false`` (default) keeps the online path
        from starting a full A-Box inference as a publish side effect: the
        caller records a deferred gate result and the operator runs
        ``materialize`` inside the offline window instead.
        """
        if not self._config.materialize_online:
            return {
                "jobId": None,
                "inferred": 0,
                "skipped": True,
                "deferred": "offline_only",
                "reason": "reasoning.materialize_online=false",
            }
        return self.materialize()

    def materialize(
        self, profile: str | None = None, force: bool = False,
        abox_graphs: list[str] | None = None,
    ) -> dict[str, Any]:
        mode = self._config.mode
        if mode == "off":
            raise PortError(
                code="Unsupported",
                message="reasoning.mode=off: materialization is disabled",
                provider="platform",
                provider_code="E_REASONING_DISABLED",
                details={"key": "reasoning.mode"},
            )
        if mode == "on-demand":
            raise PortError(
                code="Unsupported",
                message="reasoning.mode=on-demand is not implemented: no query rewriter/UCQ engine",
                provider="platform",
                provider_code="E_REASONING_ON_DEMAND_NOT_IMPLEMENTED",
                details={"key": "reasoning.mode", "mode": mode},
            )
        if mode not in SUPPORTED_MODES:
            raise PortError(
                code="Unsupported",
                message=f"reasoning.mode={mode} cannot materialize",
                provider="platform",
                provider_code="E_REASONING_MODE",
                details={"mode": mode, "allowed": list(SUPPORTED_MODES)},
            )

        current = self._ontology.current()
        if not current:
            raise PortError(
                code="NotFound",
                message="no published T-Box version to reason over",
                provider="platform",
                provider_code="E_ONTOLOGY_NO_PUBLISHED",
            )
        version_id = str(current["versionId"])
        tbox_iri = str(current["graph"])
        target = self.target_graph(version_id)
        effective_profile = profile or self._config.profile

        tbox_nt = self._graph.export_graph(tbox_iri)
        effective_abox = list(abox_graphs or self._config.abox_graphs)
        abox_nt = b"".join(self._graph.export_graph(iri) for iri in effective_abox)
        if not tbox_nt.strip():
            raise PortError(
                code="DataLoss",
                message=f"published T-Box graph {tbox_iri} is empty",
                provider="platform",
                provider_code="E_ONTOLOGY_EMPTY",
            )
        # mode=validate only runs the SHACL gate and never writes a graph.
        if mode == "validate":
            gate = self.validate(effective_abox[0])
            return {
                "mode": mode,
                "targetGraph": target,
                "inferred": 0,
                "skipped": False,
                "consistent": True,
                "ontologyVersion": version_id,
                "profile": effective_profile,
                "validation": gate,
                "stages": {"shacl": gate},
                "warnings": [],
            }

        input_hash = self._input_hash(tbox_nt, abox_nt, effective_profile, mode)

        with self._meta.advisory_lock(f"reasoning:{target}") as acquired:
            if not acquired:
                raise PortError(
                    code="Aborted",
                    message=f"another materialization is running for {target}",
                    provider="platform",
                    provider_code="E_REASONING_BUSY",
                    retryable=True,
                    details={"targetGraph": target},
                )
            pointer = self._pointer()
            if (
                not force
                and pointer
                and pointer["inputHash"] == input_hash
                and self._graph.count_graph(target) == int(pointer["inferred"])
            ):
                job_id = self._start_job(version_id, effective_profile, target, input_hash)
                self._finish_job(
                    job_id,
                    "skipped",
                    inferred=0,
                    consistent=True,
                    result={
                        "mode": mode,
                        "profile": effective_profile,
                        "inputHash": input_hash,
                        "ms": 0,
                        "stages": {},
                        "warnings": [],
                        "skipped": True,
                    },
                )
                log.info(
                    "materialize skipped",
                    extra={"event": {"event": "reasoning.skipped", "target": target}},
                )
                return {
                    "jobId": job_id,
                    "targetGraph": target,
                    "inferred": 0,
                    "skipped": True,
                    "consistent": True,
                    "inputHash": input_hash,
                    "ms": 0,
                    "ontologyVersion": version_id,
                    "profile": effective_profile,
                    "mode": mode,
                    "stages": {},
                    "warnings": [],
                }

            job_id = self._start_job(version_id, effective_profile, target, input_hash)
            started = time.monotonic()
            self._meta.execute(
                "UPDATE platform.reasoning_job SET state='running', started_at=now() WHERE job_id=%s",
                (job_id,),
            )
            stages: dict[str, Any] = {}
            try:
                # Stage 1: RDFS closure via Jena riot (OQ-39). Produces inferred
                # triples that ELK cannot (rdfs:range, subPropertyOf propagation).
                closure_nt = b""
                rdfs_count = 0
                if mode in ("rdfs", "materialize"):
                    stage_started = time.monotonic()
                    closure = self._reasoner.rdfs_closure(tbox_nt, abox_nt)
                    closure_nt, rdfs_count = self._closure_diff(
                        str(closure.get("reasoned", "")), tbox_nt, abox_nt
                    )
                    stages["rdfs"] = {
                        "triples": rdfs_count,
                        "ms": int((time.monotonic() - stage_started) * 1000),
                    }

                # Stage 2: OWL EL materialization via ROBOT/ELK.
                if mode == "materialize":
                    stage_started = time.monotonic()
                    response = self._reasoner.reason(
                        tbox_nt,
                        abox_nt + (b"\n" + closure_nt if closure_nt.strip() else b""),
                        effective_profile,
                        self._config.consistency_first,
                    )
                    if not response.get("consistent", True):
                        self._finish_job(
                            job_id,
                            "failed",
                            consistent=False,
                            error=("E_REASONING_INCONSISTENT", "ontology is inconsistent"),
                        )
                        raise PortError(
                            code="Conflict",
                            message="reasoner reports an inconsistent ontology; target graph untouched",
                            provider="robot",
                            provider_code="E_REASONING_INCONSISTENT",
                            details={"targetGraph": target, "ontologyVersion": version_id},
                        )
                    owl_nt, owl_count = self._diff(
                        str(response.get("reasoned", "")), tbox_nt, abox_nt, closure_nt
                    )
                    stages["owl"] = {
                        "triples": owl_count,
                        "ms": int((time.monotonic() - stage_started) * 1000),
                    }
                    inferred_nt = self._merge(owl_nt, closure_nt)
                    inferred_count = owl_count + rdfs_count
                else:
                    inferred_nt = closure_nt
                    inferred_count = rdfs_count

                # Stage 3: SHACL gate. It runs last but still before any write,
                # so a violation leaves the target graph untouched.
                stage_started = time.monotonic()
                if abox_nt.strip():
                    gate = self._validator.validate(abox_nt, effective_abox[0])
                else:
                    gate = {"conforms": True, "violationCount": 0, "shapes": None}
                stages["shacl"] = {
                    "conforms": bool(gate.get("conforms", False)),
                    "violations": int(gate.get("violationCount", 0)),
                    "ms": int((time.monotonic() - stage_started) * 1000),
                }
                if not gate.get("conforms", False):
                    focus = [
                        item.get("focusNode")
                        for item in gate.get("violations", [])
                        if item.get("focusNode")
                    ][:5]
                    raise PortError(
                        code="Conflict",
                        message="SHACL validation failed; refusing to materialize",
                        provider="pyshacl",
                        provider_code="E_SHACL_VIOLATION",
                        details={
                            "graph": effective_abox[0],
                            "violationCount": gate.get("violationCount", 0),
                            "focusNodes": focus,
                            "shapes": gate.get("shapes"),
                        },
                    )

                try:
                    self._graph.replace_graph(target, inferred_nt, "nt")
                except PortError:
                    # A half-written target must not masquerade as a result.
                    try:
                        self._graph.clear_graph(target)
                    except PortError:
                        log.error(
                            "failed to clear half-written inferred graph",
                            extra={"event": {"event": "reasoning.cleanup_failed", "target": target}},
                        )
                    raise
                self._upsert_pointer(
                    version_id, target, input_hash, inferred_count, job_id
                )
            except PortError as exc:
                self._meta.execute(
                    "UPDATE platform.reasoning_job SET state='failed', error_code=%s, "
                    "error_message=%s, finished_at=now() WHERE job_id=%s",
                    (exc.provider_code or exc.code, exc.message[:500], job_id),
                )
                raise
            except Exception as exc:  # defensive: never leave a running job behind
                self._meta.execute(
                    "UPDATE platform.reasoning_job SET state='failed', error_code=%s, "
                    "error_message=%s, finished_at=now() WHERE job_id=%s",
                    ("E_INTERNAL", str(exc)[:500], job_id),
                )
                raise

            ms = int((time.monotonic() - started) * 1000)
            self._finish_job(
                job_id,
                "succeeded",
                inferred=inferred_count,
                consistent=True,
                result={
                    "mode": mode,
                    "profile": effective_profile,
                    "inputHash": input_hash,
                    "ms": ms,
                    "stages": stages,
                    "warnings": [],
                },
            )
            log.info(
                "materialize finished",
                extra={
                    "event": {
                        "event": "reasoning.materialize",
                        "target": target,
                        "inferred": inferred_count,
                        "mode": mode,
                        "ms": ms,
                    }
                },
            )
            return {
                "jobId": job_id,
                "targetGraph": target,
                "inferred": inferred_count,
                "skipped": False,
                "consistent": True,
                "inputHash": input_hash,
                "ms": ms,
                "ontologyVersion": version_id,
                "profile": effective_profile,
                "mode": mode,
                "stages": stages,
                "warnings": [],
            }

    def _input_hash(
        self, tbox_nt: bytes, abox_nt: bytes, profile: str, mode: str | None = None
    ) -> str:
        digest = hashlib.sha256()
        digest.update(tbox_nt)
        digest.update(b"\n--abox--\n")
        digest.update(abox_nt)
        digest.update(
            f"\n--{mode or self._config.mode}:{profile}:{self._config.engine}--\n".encode("utf-8")
        )
        return digest.hexdigest()

    def _diff(
        self, reasoned_turtle: str, tbox_nt: bytes, abox_nt: bytes, extra_nt: bytes = b""
    ) -> tuple[bytes, int]:
        source = self._source_graph(tbox_nt, abox_nt, extra_nt)
        reasoned = rdflib.Graph()
        try:
            reasoned.parse(data=reasoned_turtle, format="turtle")
        except Exception as exc:
            raise PortError(
                code="DataLoss",
                message=f"reasoner output is not parseable RDF: {exc}",
                provider="robot",
                provider_code="E_REASONER_BAD_RESPONSE",
            ) from exc
        inferred = rdflib.Graph()
        for triple in reasoned:
            if triple not in source:
                inferred.add(triple)
        return (
            inferred.serialize(format="nt").encode("utf-8"),
            len(inferred),
        )

    def _closure_diff(
        self, closure_nt: str, tbox_nt: bytes, abox_nt: bytes
    ) -> tuple[bytes, int]:
        """Keep only RDFS closure triples the source graphs do not already hold."""
        if not closure_nt.strip():
            return b"", 0
        closure = rdflib.Graph()
        try:
            closure.parse(data=closure_nt, format="nt")
        except Exception as exc:
            raise PortError(
                code="DataLoss",
                message=f"RDFS closure is not parseable RDF: {exc}",
                provider="jena",
                provider_code="E_RDFS_FAILED",
            ) from exc
        source = self._source_graph(tbox_nt, abox_nt)
        inferred = rdflib.Graph()
        for triple in closure:
            if triple not in source:
                inferred.add(triple)
        return inferred.serialize(format="nt").encode("utf-8"), len(inferred)

    @staticmethod
    def _source_graph(tbox_nt: bytes, abox_nt: bytes, extra_nt: bytes = b"") -> rdflib.Graph:
        source = rdflib.Graph()
        source.parse(data=tbox_nt.decode("utf-8"), format="nt")
        if abox_nt.strip():
            source.parse(data=abox_nt.decode("utf-8"), format="nt")
        if extra_nt.strip():
            source.parse(data=extra_nt.decode("utf-8"), format="nt")
        return source

    @staticmethod
    def _merge(*chunks: bytes) -> bytes:
        graph = rdflib.Graph()
        for chunk in chunks:
            if chunk.strip():
                graph.parse(data=chunk.decode("utf-8"), format="nt")
        return graph.serialize(format="nt").encode("utf-8")

    # ---- jobs + pointer -------------------------------------------------

    def _start_job(
        self, version_id: str, profile: str, target: str, input_hash: str
    ) -> str:
        job_id = f"rsn-{uuid.uuid4().hex[:12]}"
        self._meta.execute(
            """
            INSERT INTO platform.reasoning_job
                (job_id, kind, ontology_version, profile, target_graph, input_hash, state)
            VALUES (%s, 'materialize', %s, %s, %s, %s, 'queued')
            """,
            (job_id, version_id, profile, target, input_hash),
        )
        return job_id

    def _finish_job(
        self,
        job_id: str,
        state: str,
        inferred: int | None = None,
        consistent: bool | None = None,
        error: tuple[str, str] | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        # result_summary keeps the per-stage numbers so a later status read can
        # show what the run did without re-running it; COALESCE leaves an older
        # summary alone when the caller has nothing newer to record.
        self._meta.execute(
            """
            UPDATE platform.reasoning_job
               SET state=%s, inferred=%s, consistent=%s, error_code=%s,
                   error_message=%s, result_summary=COALESCE(%s::jsonb, result_summary),
                   finished_at=now()
             WHERE job_id=%s
            """,
            (
                state,
                inferred,
                consistent,
                error[0] if error else None,
                error[1] if error else None,
                json.dumps(result, ensure_ascii=False) if result is not None else None,
                job_id,
            ),
        )

    def _pointer(self) -> dict[str, Any] | None:
        rows = self._meta.query(
            """
            SELECT name, ontology_version, target_graph, input_hash, inferred, job_id, updated_at
              FROM platform.inferred_pointer WHERE name=%s
            """,
            (POINTER_NAME,),
        )
        if not rows:
            return None
        row = rows[0]
        return {
            "name": row["name"],
            "ontologyVersion": row["ontology_version"],
            "targetGraph": row["target_graph"],
            "inputHash": row["input_hash"],
            "inferred": int(row["inferred"]),
            "jobId": row["job_id"],
            "updatedAt": row["updated_at"].isoformat(),
        }

    def _upsert_pointer(
        self, version_id: str, target: str, input_hash: str, inferred: int, job_id: str
    ) -> None:
        self._meta.execute(
            """
            INSERT INTO platform.inferred_pointer
                (name, ontology_version, target_graph, input_hash, inferred, job_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE
               SET ontology_version=EXCLUDED.ontology_version,
                   target_graph=EXCLUDED.target_graph,
                   input_hash=EXCLUDED.input_hash,
                   inferred=EXCLUDED.inferred,
                   job_id=EXCLUDED.job_id,
                   updated_at=now()
            """,
            (POINTER_NAME, version_id, target, input_hash, inferred, job_id),
        )

    def last_job(self) -> dict[str, Any] | None:
        rows = self._meta.query(
            """
            SELECT job_id, kind, ontology_version, profile, target_graph, input_hash, state,
                   inferred, consistent, error_code, error_message, result_summary,
                   started_at, finished_at
              FROM platform.reasoning_job
             -- A skipped run executed no stage, so reporting it as the last job
             -- would drop the last gate verdict off the health board. Prefer the
             -- newest job that actually ran; fall back to the newest skipped one
             -- only when that is all there is.
             ORDER BY (state = 'skipped') ASC, started_at DESC LIMIT 1
            """
        )
        if not rows:
            return None
        row = rows[0]
        return {
            "jobId": row["job_id"],
            "kind": row["kind"],
            "state": row["state"],
            "ontologyVersion": row["ontology_version"],
            "profile": row["profile"],
            "targetGraph": row["target_graph"],
            "inputHash": row["input_hash"],
            "inferred": row["inferred"],
            "consistent": row["consistent"],
            "errorCode": row["error_code"],
            "errorMessage": row["error_message"],
            "result": row["result_summary"] or {},
            "startedAt": row["started_at"].isoformat() if row["started_at"] else None,
            "finishedAt": row["finished_at"].isoformat() if row["finished_at"] else None,
        }

    def failed_jobs(self) -> int:
        """Failed materialization jobs; the health board's "推理失败数"."""
        rows = self._meta.query(
            """
            SELECT COUNT(*) AS n
              FROM platform.reasoning_job
             WHERE state = 'failed' AND kind = 'materialize'
            """
        )
        return int(rows[0]["n"]) if rows else 0

    def status(self) -> dict[str, Any]:
        pointer = self._pointer()
        # The inferred graph size is recorded in platform.inferred_pointer when
        # materialize replaces the graph, so read that stat instead of running
        # COUNT on every status call. At 322k triples the COUNT alone cost ~115 ms
        # (6 ms -> 125 ms on /reasoning/status); the stored value is exact for
        # graphs this service wrote and is refreshed on the next materialize.
        inferred_triples = int(pointer["inferred"]) if pointer else None
        available: bool | None = None
        if self._config.mode != "off":
            try:
                available = bool(self._reasoner.health().get("available"))
            except PortError:
                available = False
        return {
            "mode": self._config.mode,
            "provider": f"robot/{self._config.profile}",
            "engine": self._config.engine,
            "profile": self._config.profile,
            "serviceEnabled": self._config.service_enabled,
            "materializeOnline": self._config.materialize_online,
            "endpoint": self._config.endpoint,
            "available": available,
            "inferredGraphPrefix": self._config.inferred_graph_prefix,
            "aboxGraphs": list(self._config.abox_graphs),
            "shapesDir": self._config.shapes_dir,
            "pointer": pointer,
            "lastJob": self.last_job(),
            "failedJobs": self.failed_jobs(),
            "inferredTriples": inferred_triples,
        }
