"""S5 acceptance: SHACL gate, ROBOT/ELK materialization, idempotency, rollback,
reasoner outage, inconsistency, config fail-fast and the reasoning HTTP routes.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx

from .adapters.reasoner_robot import ReasonerClient
from .assembly import Runtime
from .config import load_config
from .errors import PlatformError, PortError
from .validation import ShaclValidator

RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
LOCATED_IN = "urn:platform:rel:locatedIn"


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def _tbox(prefix: str, extra: str = "") -> str:
    return f"""
@prefix owl: <{OWL}> .
@prefix rdfs: <{RDFS}> .
@prefix rdf: <{RDF}> .
<urn:platform:smoke:onto:{prefix}> a owl:Ontology .
<urn:platform:smoke:{prefix}:Thing> a owl:Class .
<urn:platform:smoke:{prefix}:Person> a owl:Class ;
    rdfs:subClassOf <urn:platform:smoke:{prefix}:Thing> .
<urn:platform:smoke:{prefix}:Student> a owl:Class ;
    rdfs:subClassOf <urn:platform:smoke:{prefix}:Person> .
{extra}
"""


def _write(tmp_dir: Path, name: str, text: str) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / name
    path.write_text(text, encoding="utf-8")
    return path


def _insert(runtime: Runtime, abox: str, triple: str) -> None:
    runtime.graph.update(f"INSERT DATA {{ GRAPH <{abox}> {{ {triple} }} }}")


def run_smoke_s5(runtime: Runtime, base_url: str, bad_config: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    abox = f"urn:platform:test:{uuid.uuid4().hex[:10]}:s5"
    tmp_dir = Path(runtime.config.storage.tmp_dir)
    nonce = uuid.uuid4().hex[:8]
    bad_client: ReasonerClient | None = None

    try:
        runtime.metadata.open(retry_seconds=10.0)
        runtime.metadata.migrate()

        # 1. reasoner health
        health = runtime.reasoner.health()
        suite.check(
            "reasoner.health",
            bool(health.get("available")) and bool(health.get("robotVersion")),
            f"robot={health.get('robotVersion')}",
        )

        # 2. import + publish v1
        v1_path = _write(tmp_dir, f"s5-{nonce}-v1.ttl", _tbox(nonce))
        v1 = runtime.ontology.import_source(str(v1_path), "1.0.0")
        runtime.ontology.publish(v1["versionId"], acknowledge_breaking=True, purpose="smoke")
        suite.check(
            "ontology.publish.v1",
            runtime.ontology.current()["versionId"] == v1["versionId"],
            f"version={v1['versionId']}",
        )

        # 3. A-Box individual
        alice = f"urn:platform:smoke:{nonce}:alice"
        _insert(runtime, abox, f"<{alice}> a <urn:platform:smoke:{nonce}:Student> .")
        suite.check("abox.insert", runtime.graph.count_graph(abox) >= 1, f"triples={runtime.graph.count_graph(abox)}")

        # 4. materialize v1
        first = runtime.reasoning.materialize(abox_graphs=[abox])
        expected_target = f"urn:platform:inferred:{v1['versionId']}"
        suite.check(
            "materialize.first",
            first["consistent"] is True and first["inferred"] > 0 and first["targetGraph"] == expected_target,
            f"inferred={first['inferred']} target={first['targetGraph']}",
        )

        # 5. inferred graph holds the entailments, not the source triples
        person = f"urn:platform:smoke:{nonce}:Person"
        thing = f"urn:platform:smoke:{nonce}:Thing"
        student = f"urn:platform:smoke:{nonce}:Student"
        suite.check(
            "inferred.entailed",
            runtime.graph.ask(f"ASK {{ GRAPH <{expected_target}> {{ <{alice}> a <{person}> }} }}")
            and runtime.graph.ask(f"ASK {{ GRAPH <{expected_target}> {{ <{alice}> a <{thing}> }} }}"),
            f"target={expected_target}",
        )
        suite.check(
            "inferred.excludes_source",
            not runtime.graph.ask(f"ASK {{ GRAPH <{expected_target}> {{ <{alice}> a <{student}> }} }}"),
            "source triple must stay in the A-Box graph",
        )

        # 6. idempotent rerun
        second = runtime.reasoning.materialize(abox_graphs=[abox])
        suite.check(
            "materialize.idempotent",
            second["skipped"] is True and second["inferred"] == 0 and second["targetGraph"] == expected_target,
            f"skipped={second['skipped']} inferred={second['inferred']}",
        )
        suite.check(
            "materialize.single_graph",
            runtime.graph.count_graph(expected_target) == first["inferred"],
            f"count={runtime.graph.count_graph(expected_target)} expected={first['inferred']}",
        )

        # 7. new A-Box fact is picked up (no stale cache)
        bob = f"urn:platform:smoke:{nonce}:bob"
        _insert(runtime, abox, f"<{bob}> a <{student}> .")
        third = runtime.reasoning.materialize(abox_graphs=[abox])
        suite.check(
            "materialize.incremental_input",
            third["skipped"] is False and third["inferred"] > first["inferred"],
            f"inferred={third['inferred']} before={first['inferred']}",
        )

        # 8. SHACL conforming data
        _insert(runtime, abox, f"<{alice}> <{LOCATED_IN}> <urn:platform:smoke:{nonce}:beijing> .")
        ok_validation = runtime.reasoning.validate(abox)
        suite.check(
            "shacl.conforms",
            ok_validation["conforms"] is True and ok_validation["violationCount"] == 0,
            f"conforms={ok_validation['conforms']} shapes={ok_validation['shapes']}",
        )

        # 9. SHACL violation: literal object, and nothing is materialized
        bad = f"urn:platform:smoke:{nonce}:bad"
        _insert(runtime, abox, f'<{bad}> <{LOCATED_IN}> "not-an-iri" .')
        before_inferred = runtime.graph.count_graph(expected_target)
        bad_validation = runtime.reasoning.validate(abox)
        suite.check(
            "shacl.violation",
            bad_validation["conforms"] is False
            and bad_validation["violationCount"] >= 1
            and any(item["focusNode"] == bad for item in bad_validation["violations"]),
            f"conforms={bad_validation['conforms']} count={bad_validation['violationCount']}",
        )
        # The gate must stop materialization before the reasoner runs.
        try:
            runtime.reasoning.materialize(force=True, abox_graphs=[abox])
            suite.fail("shacl.no_write", "materialize ignored the SHACL violation")
        except PortError as exc:
            suite.check(
                "shacl.no_write",
                exc.code == "Conflict"
                and exc.provider_code == "E_SHACL_VIOLATION"
                and runtime.graph.count_graph(expected_target) == before_inferred,
                f"{exc.code}/{exc.provider_code} inferred={before_inferred}",
            )
        runtime.graph.update(
            f'DELETE DATA {{ GRAPH <{abox}> {{ <{bad}> <{LOCATED_IN}> "not-an-iri" . }} }}'
        )

        # 10. reasoner outage: explicit code, sources untouched
        bad_client = ReasonerClient(
            runtime.config.reasoning.model_copy(update={"endpoint": "http://127.0.0.1:9"}),
            robot_version="test",
        )
        outage = type(runtime.reasoning)(
            runtime.config.reasoning,
            runtime.metadata,
            runtime.graph,
            bad_client,
            runtime.validator,
            runtime.ontology,
        )
        source_before = runtime.graph.count_graph(abox)
        target_before = runtime.graph.count_graph(expected_target)
        try:
            outage.materialize(force=True, abox_graphs=[abox])
            suite.fail("reasoner.outage", "expected E_REASONER_UNAVAILABLE")
        except PortError as exc:
            suite.check(
                "reasoner.outage",
                exc.code == "Unavailable" and exc.provider_code == "E_REASONER_UNAVAILABLE",
                f"{exc.code}/{exc.provider_code}",
            )
        suite.check(
            "reasoner.outage_untouched",
            runtime.graph.count_graph(abox) == source_before
            and runtime.graph.count_graph(expected_target) == target_before,
            f"source={source_before} target={target_before}",
        )

        # 11. v2 materialization, then rollback pointer to v1
        v2_path = _write(
            tmp_dir,
            f"s5-{nonce}-v2.ttl",
            _tbox(
                nonce,
                f"<urn:platform:smoke:{nonce}:Teacher> a owl:Class ; "
                f"rdfs:subClassOf <urn:platform:smoke:{nonce}:Person> .",
            ),
        )
        v2 = runtime.ontology.import_source(str(v2_path), "2.0.0")
        runtime.ontology.publish(v2["versionId"], acknowledge_breaking=True, purpose="smoke")
        carol = f"urn:platform:smoke:{nonce}:carol"
        _insert(runtime, abox, f"<{carol}> a <urn:platform:smoke:{nonce}:Teacher> .")
        v2_result = runtime.reasoning.materialize(force=True, abox_graphs=[abox])
        suite.check(
            "materialize.v2",
            v2_result["targetGraph"] == f"urn:platform:inferred:{v2['versionId']}"
            and runtime.reasoning.status()["pointer"]["ontologyVersion"] == v2["versionId"],
            f"pointer={runtime.reasoning.status()['pointer']['ontologyVersion']}",
        )
        runtime.ontology.rollback(v1["versionId"])
        # S1 rollback creates a *new* version row (semver 1.0.0+rollback.N) that
        # reuses the v1 graph; the pointer therefore moves to the new id.
        rolled_version = runtime.ontology.current()["versionId"]
        rolled_target = f"urn:platform:inferred:{rolled_version}"
        rolled = runtime.reasoning.materialize(force=True, abox_graphs=[abox])
        pointer = runtime.reasoning.status()["pointer"]
        suite.check(
            "pointer.rollback",
            pointer["ontologyVersion"] == rolled_version
            and pointer["targetGraph"] == rolled_target
            and runtime.graph.count_graph(rolled_target) > 0,
            f"pointer={pointer['ontologyVersion']} target={pointer['targetGraph']}",
        )
        suite.check(
            "pointer.rollback_read",
            rolled["targetGraph"] == rolled_target
            and runtime.ontology.get(rolled_version)["contentHash"]
            == runtime.ontology.get(v1["versionId"])["contentHash"],
            f"{rolled['targetGraph']} rollbackOf={v1['versionId']}",
        )

        # 12. inconsistent T-Box: refused, no inferred graph
        bad_path = _write(
            tmp_dir,
            f"s5-{nonce}-bad.ttl",
            f"""
@prefix owl: <{OWL}> .
@prefix rdfs: <{RDFS}> .
<urn:platform:smoke:onto:{nonce}:bad> a owl:Ontology .
<urn:platform:smoke:{nonce}:A> a owl:Class ;
    rdfs:subClassOf <urn:platform:smoke:{nonce}:B> ;
    rdfs:subClassOf owl:Nothing .
""",
        )
        v3 = runtime.ontology.import_source(str(bad_path), "3.0.0")
        bad_target = f"urn:platform:inferred:{v3['versionId']}"
        pointer_before = runtime.ontology.current()["versionId"]
        try:
            runtime.ontology.publish(v3["versionId"], acknowledge_breaking=True)
            suite.fail("publish.consistency_gate", "unsatisfiable ontology was published")
        except PortError as exc:
            suite.check(
                "publish.consistency_gate",
                exc.provider_code == "E_ONTOLOGY_INCONSISTENT"
                and runtime.ontology.current()["versionId"] == pointer_before,
                f"{exc.code}/{exc.provider_code}",
            )
        suite.check(
            "publish.consistency_no_write",
            runtime.graph.count_graph(bad_target) == 0,
            f"target={bad_target}",
        )
        runtime.ontology.rollback(v1["versionId"])

        # 13. mode=off is explicit, never a silent success
        off_service = type(runtime.reasoning)(
            runtime.config.reasoning.model_copy(update={"mode": "off"}),
            runtime.metadata,
            runtime.graph,
            runtime.reasoner,
            runtime.validator,
            runtime.ontology,
        )
        try:
            off_service.materialize(force=True)
            suite.fail("reasoning.off", "mode=off was materialized")
        except PortError as exc:
            suite.check(
                "reasoning.off",
                exc.code == "Unsupported" and exc.provider_code == "E_REASONING_DISABLED",
                f"{exc.code}/{exc.provider_code}",
            )

        # 14. missing shapes directory is explicit
        empty_validator = ShaclValidator(
            runtime.config.reasoning.model_copy(update={"shapes_dir": "/data/shapes-missing"})
        )
        try:
            empty_validator.validate(b"<urn:s> <urn:p> <urn:o> .\n", "urn:g")
            suite.fail("shacl.no_shapes", "missing shapes were treated as pass")
        except PortError as exc:
            suite.check(
                "shacl.no_shapes",
                exc.code == "Unsupported" and exc.provider_code == "E_SHACL_SHAPES_MISSING",
                f"{exc.code}/{exc.provider_code}",
            )

        # 15. invalid validation target
        try:
            runtime.reasoning.validate("bogus")
            suite.fail("shacl.bad_target", "invalid target accepted")
        except PortError as exc:
            suite.check(
                "shacl.bad_target",
                exc.code == "InvalidArgument" and exc.provider_code == "E_VALIDATE_TARGET",
                f"{exc.code}/{exc.provider_code}",
            )

        # 16. HTTP routes
        with httpx.Client(base_url=base, timeout=30.0) as client:
            status = client.get("/status")
            suite.check(
                "http.status",
                status.status_code == 200 and status.json().get("slice") in {"S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12", "S13"},
                f"http={status.status_code} slice={status.json().get('slice')}",
            )
            rstatus = client.get("/reasoning/status")
            suite.check(
                "http.reasoning_status",
                rstatus.status_code == 200 and rstatus.json().get("pointer", {}).get("targetGraph") == rolled_target,
                f"http={rstatus.status_code} target={rstatus.json().get('pointer', {}).get('targetGraph')}",
            )
            validation = client.post("/validation/run", json={"graph": abox})
            suite.check(
                "http.validation",
                validation.status_code == 200 and "conforms" in validation.json(),
                f"http={validation.status_code}",
            )
            materialize = client.post("/reasoning/materialize", json={})
            suite.check(
                "http.materialize",
                materialize.status_code == 200 and "skipped" in materialize.json(),
                f"http={materialize.status_code}",
            )

        # 17. bad config (OWL2DL) fails fast
        try:
            load_config(bad_config)
            suite.fail("config.failfast", "OWL2DL reasoning config was accepted")
        except PlatformError as exc:
            suite.check(
                "config.failfast",
                exc.code == "E_CONFIG_REASONING" and exc.exit_code == 78,
                f"{exc.code} exit={exc.exit_code}",
            )

    finally:
        if bad_client is not None:
            bad_client.close()
        # SILENT: a clean abort may leave the abox uncreated; a plain DROP would
        # raise Oxigraph HTTP 500 ("The graph ... does not exist") and mask the
        # real reason (e.g. E_REASONER_UNAVAILABLE on a reasoner-less stack).
        runtime.graph.update(f"DROP SILENT GRAPH <{abox}>")
        runtime.facts.purge_test(abox)

    total = len(suite.results)
    passed = sum(1 for _, ok, _ in suite.results if ok)
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print(f"S5 SMOKE {passed}/{total}")
    return 0 if passed == total else 1
