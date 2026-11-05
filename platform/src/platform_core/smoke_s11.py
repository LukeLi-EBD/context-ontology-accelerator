"""S11 acceptance: T-Box change governance.

Covers the lifecycle (draft -> proposed -> approved -> published -> superseded),
SPARQL diff with breaking flags, the three publish gates, rollbackTo, import
conflict detection and export round-trip. Test T-Boxes use a per-run IRI
namespace; the original pointer is restored at the end.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import httpx

from .assembly import Runtime
from .errors import PortError


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def _expect(error_cls, code: str, action):
    try:
        action()
    except error_cls as exc:  # type: ignore[misc]
        return exc if getattr(exc, "provider_code", None) == code else exc
    return None


def _prefixes() -> str:
    return (
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
    )


def run_smoke_s11(runtime: Runtime, base_url: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    nonce = uuid.uuid4().hex[:8]
    ns = f"urn:platform:smoke:s11:{nonce}:"
    tmp_dir = Path(runtime.config.storage.tmp_dir) / f"s11-{nonce}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    alpha, beta, gamma, delta = (f"{ns}{name}" for name in ("Alpha", "Beta", "Gamma", "Delta"))
    link, extra = f"{ns}link", f"{ns}extra"
    x_cls, y_cls, ind = f"{ns}X", f"{ns}Y", f"{ns}dual"

    def tbox(body: str) -> str:
        return _prefixes() + f"@prefix ex: <{ns}> .\n" + body

    def write(name: str, body: str) -> str:
        path = tmp_dir / f"{name}.ttl"
        path.write_text(tbox(body), encoding="utf-8")
        return str(path)

    v1_body = f"ex:Alpha a owl:Class .\nex:Beta a owl:Class .\n" \
              f"ex:link a owl:ObjectProperty ; rdfs:domain ex:Alpha ; rdfs:range ex:Beta .\n"
    v2_body = (
        f"ex:Alpha a owl:Class .\nex:Beta a owl:Class .\n"
        f"ex:Gamma a owl:Class ; rdfs:subClassOf ex:Beta .\n"
        f"ex:link a owl:ObjectProperty ; rdfs:domain ex:Gamma ; rdfs:range ex:Beta .\n"
        f"ex:extra a owl:DatatypeProperty ; rdfs:domain ex:Gamma ; rdfs:range xsd:string .\n"
    )
    v3_body = v1_body + "ex:Delta a owl:Class .\n"
    v4_body = f"ex:Alpha a owl:Class .\n" \
              f"ex:link a owl:ObjectProperty ; rdfs:domain ex:Alpha .\n"
    v5_body = v4_body + (
        f"ex:X a owl:Class ; owl:disjointWith ex:Y .\n"
        f"ex:Y a owl:Class .\n"
        f"ex:dual a owl:NamedIndividual , ex:X , ex:Y .\n"
    )
    conflict_body = f"ex:Alpha a owl:Class ; rdfs:label \"alpha-redefined\" .\n"

    initial = runtime.ontology.current() or {}
    initial_id = initial.get("versionId")
    test_versions: dict[str, str] = {}
    restored = False

    try:
        runtime.metadata.open(retry_seconds=10.0)
        runtime.metadata.migrate()

        for index, (name, body) in enumerate((
            ("v1", v1_body), ("v2", v2_body), ("v3", v3_body),
            ("v4", v4_body), ("v5", v5_body),
        ), start=1):
            imported = runtime.ontology.import_source(
                write(name, body), f"11.0.{index}", name
            )
            test_versions[name] = imported["versionId"]
        suite.check(
            "setup.import",
            len(set(test_versions.values())) == 5,
            f"versions={len(test_versions)}",
        )

        # 1. draft -> proposed -> approved -> published, with a complete audit chain
        proposal = runtime.ontology.propose(
            test_versions["v1"], "add Alpha/Beta/link", actor="operator"
        )
        suite.check(
            "lifecycle.propose",
            proposal["status"] == "proposed"
            and proposal["versionId"] == test_versions["v1"]
            and proposal["diff"]["summary"]["addedClasses"]
            and proposal["impact"]["addedTriples"] > 0,
            f"proposal={proposal['proposalId']}",
        )
        # 2. publish before approve must be rejected with a stable code
        refused = _expect(
            PortError, "E_ONTOLOGY_NOT_APPROVED",
            lambda: runtime.ontology.publish(
                test_versions["v1"], proposal_id=proposal["proposalId"]
            ),
        )
        suite.check(
            "publish.unapproved",
            isinstance(refused, PortError)
            and refused.provider_code == "E_ONTOLOGY_NOT_APPROVED"
            and (runtime.ontology.current() or {}).get("versionId") != test_versions["v1"],
            f"code={getattr(refused, 'provider_code', None)}",
        )
        approved = runtime.ontology.approve(proposal["proposalId"], actor="operator")
        published = runtime.ontology.publish(
            test_versions["v1"], proposal_id=proposal["proposalId"],
            acknowledge_breaking=True, actor="operator",
        )
        v1_events = runtime.ontology.events(test_versions["v1"])["items"]
        actions = {event["action"] for event in v1_events}
        suite.check(
            "lifecycle.publish",
            approved["status"] == "approved"
            and published["governed"] is True
            and (runtime.ontology.current() or {}).get("versionId") == test_versions["v1"]
            and {"imported", "proposed", "approved", "published"} <= actions
            and runtime.ontology.verify_events()["ok"] is True,
            f"pointer={published['id']} actions={sorted(actions)}",
        )

        # 3. diff over three minimal versions: additions, removals, domain changes
        d12 = runtime.ontology.diff(test_versions["v1"], test_versions["v2"])
        d23 = runtime.ontology.diff(test_versions["v2"], test_versions["v3"])
        domain_change = next(
            (item for item in d12["summary"]["domainChanges"] if item["property"] == link), {}
        )
        suite.check(
            "diff.added",
            gamma in d12["summary"]["addedClasses"]
            and extra in d12["summary"]["addedProperties"]
            and domain_change.get("from") == [alpha]
            and domain_change.get("to") == [gamma]
            and d12["summary"]["addedTriples"] > 0,
            f"added={len(d12['summary']['addedClasses'])} domain={domain_change}",
        )
        suite.check(
            "diff.removed",
            gamma in d23["summary"]["removedClasses"]
            and extra in d23["summary"]["removedProperties"]
            and delta in d23["summary"]["addedClasses"]
            and d23["summary"]["removedTriples"] > 0
            and isinstance(d23.get("markdown"), str) and d23["markdown"].strip() != "",
            f"removed={d23['summary']['removedClasses']}",
        )

        # 4. breaking change: rejected without acknowledgement, accepted with it
        breaking_proposal = runtime.ontology.propose(
            test_versions["v4"], "drop Beta and its range", actor="operator",
            against_version=test_versions["v1"],
        )
        suite.check(
            "breaking.detected",
            breaking_proposal["breaking"] is True
            and any(item["kind"] == "class_removed"
                    for item in breaking_proposal["diff"]["breakingItems"]),
            f"items={len(breaking_proposal['diff']['breakingItems'])}",
        )
        runtime.ontology.approve(breaking_proposal["proposalId"], actor="operator")
        refused = _expect(
            PortError, "E_ONTOLOGY_BREAKING",
            lambda: runtime.ontology.publish(
                test_versions["v4"], proposal_id=breaking_proposal["proposalId"]
            ),
        )
        suite.check(
            "breaking.reject",
            isinstance(refused, PortError)
            and refused.provider_code == "E_ONTOLOGY_BREAKING"
            and (runtime.ontology.current() or {}).get("versionId") == test_versions["v1"],
            f"code={getattr(refused, 'provider_code', None)}",
        )
        acked = runtime.ontology.publish(
            test_versions["v4"], proposal_id=breaking_proposal["proposalId"],
            acknowledge_breaking=True, actor="operator",
        )
        stored = runtime.ontology.get_proposal(breaking_proposal["proposalId"])
        suite.check(
            "breaking.acknowledge",
            (runtime.ontology.current() or {}).get("versionId") == test_versions["v4"]
            and stored["acknowledgedBreaking"] is True
            and any(event["action"] == "breaking_acknowledged"
                    for event in runtime.ontology.events(test_versions["v4"])["items"]),
            f"pointer={acked['id']}",
        )

        # 5. consistency failure blocks publish and leaves the pointer untouched
        inconsistent = runtime.ontology.propose(
            test_versions["v5"], "disjoint classes with one dual-typed instance",
            actor="operator", against_version=test_versions["v4"],
        )
        runtime.ontology.approve(inconsistent["proposalId"], actor="operator")
        refused = _expect(
            PortError, "E_ONTOLOGY_INCONSISTENT",
            lambda: runtime.ontology.publish(
                test_versions["v5"], proposal_id=inconsistent["proposalId"]
            ),
        )
        suite.check(
            "consistency.reject",
            isinstance(refused, PortError)
            and refused.provider_code == "E_ONTOLOGY_INCONSISTENT"
            and (runtime.ontology.current() or {}).get("versionId") == test_versions["v4"],
            f"code={getattr(refused, 'provider_code', None)} "
            f"pointer={(runtime.ontology.current() or {}).get('versionId')}",
        )

        # 6. rollbackTo: the old graph stays readable and the rolled-back version
        # becomes superseded; neither version is deleted
        rolled = runtime.ontology.rollback_to(
            test_versions["v1"], actor="operator", reason="acceptance rollback"
        )
        v1_row = runtime.ontology.get(test_versions["v1"])
        v4_row = runtime.ontology.get(test_versions["v4"])
        with httpx.Client(base_url=base, timeout=60.0) as client:
            old_version = client.get(f"/ontology/versions/{test_versions['v4']}")
        suite.check(
            "rollback.pointer",
            (runtime.ontology.current() or {}).get("versionId") == test_versions["v1"]
            and v1_row["status"] == "published"
            and v4_row["status"] == "superseded"
            and runtime.ontology.graph_count(test_versions["v4"]) > 0
            and runtime.ontology.graph_count(test_versions["v1"]) > 0
            and rolled["previous"] == test_versions["v4"]
            and old_version.status_code == 200
            and old_version.json().get("status") == "superseded"
            and old_version.json().get("graphTripleCount", 0) > 0,
            f"v1={v1_row['status']} v4={v4_row['status']} http={old_version.status_code}",
        )

        # 7. import conflict: default reject with a diff, new_version accepts
        conflict_path = write("conflict", conflict_body)
        refused = _expect(
            PortError, "E_ONTOLOGY_IMPORT_CONFLICT",
            lambda: runtime.ontology.import_source(
                conflict_path, "11.1.0", "conflict", on_conflict="reject"
            ),
        )
        details = getattr(refused, "details", {}) if refused else {}
        suite.check(
            "import.conflict_reject",
            isinstance(refused, PortError)
            and refused.provider_code == "E_ONTOLOGY_IMPORT_CONFLICT"
            and details.get("conflictCount", 0) >= 1
            and any(item.get("iri") == alpha for item in details.get("conflicts", [])),
            f"count={details.get('conflictCount')}",
        )
        accepted = runtime.ontology.import_source(
            conflict_path, "11.1.1", "conflict", on_conflict="new_version"
        )
        suite.check(
            "import.conflict_new_version",
            accepted["versionId"] not in test_versions.values()
            and accepted["status"] == "draft"
            and len(accepted["conflicts"]) >= 1,
            f"version={accepted['versionId']}",
        )

        # 8. export -> import round-trip: diff must be empty
        exported = runtime.ontology.export_version(test_versions["v1"], "turtle")
        nquads = runtime.ontology.export_version(test_versions["v1"], "nquads")
        turtle_path = tmp_dir / "roundtrip.ttl"
        turtle_path.write_text(exported["content"], encoding="utf-8")
        reimported = runtime.ontology.import_source(
            str(turtle_path), "11.2.0", "roundtrip", on_conflict="reject"
        )
        roundtrip_diff = runtime.ontology.diff(
            test_versions["v1"], reimported["versionId"]
        )
        suite.check(
            "export.roundtrip",
            reimported["skipped"] is True
            and roundtrip_diff["summary"]["addedTriples"] == 0
            and roundtrip_diff["summary"]["removedTriples"] == 0
            and not roundtrip_diff["summary"]["addedClasses"]
            and not roundtrip_diff["summary"]["removedClasses"]
            and roundtrip_diff["breaking"] is False
            and len(nquads["content"].splitlines()) == exported["triples"],
            f"skipped={reimported['skipped']} added={roundtrip_diff['summary']['addedTriples']} "
            f"removed={roundtrip_diff['summary']['removedTriples']} nq={len(nquads['content'].splitlines())}",
        )

        with httpx.Client(base_url=base, timeout=60.0) as client:
            versions = client.get("/ontology/versions")
            chain = client.get("/ontology/verify")
            page = client.get("/ui/ontology.html")
            script = client.get("/ui/app.js")
            suite.check(
                "http.ontology",
                versions.status_code == 200
                and versions.json().get("pointer", {}).get("versionId") == test_versions["v1"]
                and chain.status_code == 200 and chain.json().get("ok") is True,
                f"http={versions.status_code}",
            )
            suite.check(
                "ui.governance",
                page.status_code == 200
                and 'id="onto-versions"' in page.text
                and 'id="onto-proposal-form"' in page.text
                and 'id="onto-proposal-version"' in page.text
                and 'id="onto-proposal-note"' in page.text
                and 'id="onto-proposal-actor"' in page.text
                and 'id="onto-diff-preview"' in page.text
                and 'id="onto-publish"' in page.text
                and 'id="onto-rollback"' in page.text
                and "loadOntologyGovernance" in script.text
                and "previewOntologyDiff" in script.text
                and "publishOntologyVersion" in script.text
                and "rollbackOntologyVersion" in script.text,
                f"page={page.status_code} script={script.status_code}",
            )
            status = client.get("/status").json()
            suite.check(
                "http.status",
                status.get("slice") in {"S11", "S12", "S13"} and "ontology" in status.get("providers", {}),
                f"slice={status.get('slice')}",
            )

        # restore the pointer that was active before the smoke run
        if initial_id and initial_id != test_versions["v1"]:
            runtime.ontology.rollback_to(
                initial_id, actor="operator", reason="s11 smoke cleanup"
            )
        restored = True
        suite.check(
            "cleanup.pointer",
            (runtime.ontology.current() or {}).get("versionId") == initial_id
            or initial_id is None,
            f"initial={initial_id}",
        )
    except PortError as exc:
        suite.fail("runtime", f"{exc.code}/{exc.provider_code}: {exc.message}")
    except httpx.HTTPError as exc:
        suite.fail("http", str(exc))
    finally:
        if not restored:
            try:
                if initial_id:
                    runtime.ontology.rollback_to(
                        initial_id, actor="operator", reason="s11 smoke cleanup"
                    )
            except Exception as exc:  # noqa: BLE001 - cleanup must not mask results
                suite.fail("cleanup.pointer", str(exc))
        shutil.rmtree(tmp_dir, ignore_errors=True)

    passed = sum(1 for _, ok, _ in suite.results if ok)
    total = len(suite.results)
    print(f"SMOKE-S11 {passed}/{total}")
    for name, ok, detail in suite.results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    return 0 if passed == total else 1
