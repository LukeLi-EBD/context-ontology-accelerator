"""S7 acceptance: five static pages, their view APIs, the UI chain
(upload -> index -> extract -> approve -> materialize) and visible
truncated/degraded markers. Runs against the live HTTP container plus a
local runtime for fixtures.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx

from .assembly import Runtime
from .errors import PortError

RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def _tbox(prefix: str) -> str:
    return f"""
@prefix owl: <{OWL}> .
@prefix rdfs: <{RDFS}> .
<urn:platform:smoke:{prefix}:onto> a owl:Ontology .
<urn:platform:smoke:{prefix}:Facility> a owl:Class ; rdfs:label "S7设施{prefix}" .
<urn:platform:smoke:{prefix}:Site> a owl:Class ;
    rdfs:label "S7监测点{prefix}" ;
    rdfs:subClassOf <urn:platform:smoke:{prefix}:Facility> .
<urn:platform:smoke:{prefix}:Region> a owl:Class ; rdfs:label "S7行政区{prefix}" .
<urn:platform:rel:locatedIn> a owl:ObjectProperty ;
    rdfs:label "S7位于{prefix}" ;
    rdfs:domain <urn:platform:smoke:{prefix}:Site> ;
    rdfs:range <urn:platform:smoke:{prefix}:Region> .
"""


def _write(tmp_dir: Path, name: str, text: str) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / name
    path.write_text(text, encoding="utf-8")
    return path


def run_smoke_s7(runtime: Runtime, base_url: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    tmp_dir = Path(runtime.config.storage.tmp_dir)
    nonce = uuid.uuid4().hex[:8]
    subject_name = f"S7监测点{nonce}"
    place_name = f"S7行政区{nonce}"
    test_graph = f"urn:platform:test:{uuid.uuid4().hex[:10]}:s7"
    document_id: str | None = None
    candidate_id: str | None = None

    with httpx.Client(base_url=base, timeout=60.0) as client:
        try:
            runtime.metadata.open(retry_seconds=10.0)
            runtime.metadata.migrate()

            # 1. five pages + assets are served by the platform
            pages = {
                "overview": "index.html",
                "ontology": "ontology.html",
                "documents": "documents.html",
                "search": "search.html",
                "approvals": "approvals.html",
            }
            for page, filename in pages.items():
                response = client.get(f"/ui/{filename}")
                suite.check(
                    f"ui.page.{page}",
                    response.status_code == 200 and f'data-page="{page}"' in response.text,
                    f"status={response.status_code}",
                )
            root = client.get("/", follow_redirects=False)
            suite.check(
                "ui.root",
                root.status_code in (301, 302, 307, 308)
                and "/ui/" in root.headers.get("location", ""),
                f"status={root.status_code} location={root.headers.get('location')}",
            )
            css = client.get("/ui/app.css")
            script = client.get("/ui/app.js")
            suite.check(
                "ui.assets",
                css.status_code == 200
                and script.status_code == 200
                and "truncated" in script.text
                and "degraded" in script.text,
                f"css={css.status_code} js={script.status_code}",
            )
            direct = client.get("/ui/api/overview", headers={"Origin": "null"})
            suite.check(
                "ui.file_origin",
                direct.status_code == 200
                and direct.headers.get("access-control-allow-origin") == "null",
                f"acao={direct.headers.get('access-control-allow-origin')}",
            )

            # 2. publish a labelled ontology for the browse page
            path = _write(tmp_dir, f"s7-{nonce}.ttl", _tbox(nonce))
            # The probe re-declares the shared urn:platform:rel:locatedIn IRI with
            # a per-run label, so a re-run legitimately "conflicts" with the
            # currently published T-Box. Ask for a new version explicitly instead
            # of setting on_conflict to reject (which is the product default).
            version = runtime.ontology.import_source(
                str(path), "1.0.0", on_conflict="new_version"
            )
            runtime.ontology.publish(version["versionId"], acknowledge_breaking=True)
            suite.check(
                "ontology.publish",
                runtime.ontology.current()["versionId"] == version["versionId"],
                f"version={version['versionId']}",
            )

            # 3. overview API
            overview = client.get("/ui/api/overview")
            data = overview.json() if overview.status_code == 200 else {}
            suite.check(
                "ui.api.overview",
                overview.status_code == 200
                and len(data.get("services", [])) >= 4
                and isinstance(data.get("graphs"), list),
                f"status={overview.status_code} services={len(data.get('services', []))}",
            )

            # 4. ontology browse: classes + properties
            ontology = client.get("/ui/api/ontology").json()
            suite.check(
                "ui.api.ontology",
                any(f"S7监测点{nonce}" in item["label"] for item in ontology.get("classes", []))
                and any(f"S7位于{nonce}" in item["label"] for item in ontology.get("properties", [])),
                f"classes={len(ontology.get('classes', []))} props={len(ontology.get('properties', []))}",
            )

            # 5. entity search + neighbour subgraph
            entities = client.get(
                "/ui/api/entities", params={"q": subject_name, "limit": 10}
            ).json()
            site_iri = next(
                (item["iri"] for item in entities.get("items", []) if subject_name in item["label"]),
                None,
            )
            suite.check(
                "ui.api.entities",
                bool(site_iri),
                f"items={len(entities.get('items', []))}",
            )
            neighbours = client.get(
                "/ui/api/neighbors", params={"iri": site_iri or "", "limit": 20}
            )
            edge = neighbours.json().get("edges", []) if neighbours.status_code == 200 else []
            suite.check(
                "ui.api.neighbors",
                neighbours.status_code == 200 and any(RDFS + "subClassOf" in e["p"] for e in edge),
                f"status={neighbours.status_code} edges={len(edge)}",
            )

            # 6. documents: upload -> index -> chunks
            upload = _write(
                tmp_dir,
                f"s7-{nonce}.txt",
                f"{subject_name}位于{place_name}。{subject_name}负责近岸水质监测。\n",
            )
            with upload.open("rb") as handle:
                response = client.post(
                    "/documents",
                    files={"file": (upload.name, handle, "text/plain")},
                )
            suite.check(
                "ui.upload",
                response.status_code in (200, 201) and bool(response.json().get("documentId")),
                f"status={response.status_code}",
            )
            if response.status_code in (200, 201):
                document_id = response.json()["documentId"]
                indexed = client.post(f"/documents/{document_id}/index")
                suite.check(
                    "ui.index",
                    indexed.status_code == 200 and indexed.json().get("chunks", 0) > 0,
                    f"chunks={indexed.json().get('chunks') if indexed.status_code == 200 else 'n/a'}",
                )
                chunks = client.get(f"/documents/{document_id}/chunks", params={"limit": 20})
                suite.check(
                    "ui.chunks",
                    chunks.status_code == 200
                    and any(subject_name in item["text"] for item in chunks.json().get("items", [])),
                    f"status={chunks.status_code}",
                )

                extracted = client.post(f"/documents/{document_id}/extract", json={"mode": "auto"})
                suite.check(
                    "ui.extract",
                    extracted.status_code == 200 and extracted.json().get("inserted", 0) > 0,
                    f"inserted={extracted.json().get('inserted') if extracted.status_code == 200 else 'n/a'}",
                )

            # 7. approvals carry the source snippet
            candidates = client.get("/ui/api/candidates", params={"state": "pending", "limit": 20})
            items = candidates.json().get("candidates", []) if candidates.status_code == 200 else []
            # Pick the rules candidate for this probe, not merely the newest one
            # for the document: with an LLM provider configured, `auto` mode also
            # emits LLM candidates (example.org IRIs, and sometimes the very same
            # urn:platform:entity subject with a different predicate), so matching
            # on subject alone is racy. Match the exact locatedIn triple instead.
            candidate_id = next(
                (
                    item["candidateId"]
                    for item in items
                    if item.get("documentId") == document_id
                    and item.get("subject") == f"urn:platform:entity:{subject_name}"
                    and item.get("predicate") == "urn:platform:rel:locatedIn"
                    and item.get("object") == f"urn:platform:entity:{place_name}"
                ),
                None,
            )
            evidence = next(
                (item["evidence"]["text"] for item in items if item.get("candidateId") == candidate_id),
                "",
            )
            suite.check(
                "ui.api.candidates_evidence",
                candidates.status_code == 200 and bool(candidate_id) and subject_name in evidence,
                f"pending={len(items)}",
            )

            # 8. approve -> A-Box, then materialize the chain
            if candidate_id:
                approved = client.post(
                    f"/candidates/{candidate_id}/approve", params={"graph": test_graph}
                )
                suite.check(
                    "ui.approve",
                    approved.status_code == 200 and approved.json().get("state") == "approved",
                    f"status={approved.status_code}",
                )
                suite.check(
                    "ui.abox_written",
                    runtime.graph.ask(
                        f"ASK {{ GRAPH <{test_graph}> "
                        f"{{ <urn:platform:entity:{subject_name}> "
                        f"<urn:platform:rel:locatedIn> <urn:platform:entity:{place_name}> }} }}"
                    ),
                    f"graph={test_graph} subject={subject_name}",
                )

            first = client.post(
                "/reasoning/materialize", json={"force": True, "aboxGraphs": [test_graph]}
            )
            body = first.json() if first.status_code == 200 else {}
            stages = body.get("stages", {})
            suite.check(
                "ui.materialize.chain",
                first.status_code == 200
                and body.get("mode") == "materialize"
                and {"rdfs", "owl", "shacl"} <= set(stages)
                and body.get("skipped") is False,
                f"status={first.status_code} stages={sorted(stages)}",
            )
            if first.status_code == 200:
                second = client.post(
                    "/reasoning/materialize", json={"aboxGraphs": [test_graph]}
                )
                second_body = second.json() if second.status_code == 200 else {}
                suite.check(
                    "ui.materialize.idempotent",
                    second.status_code == 200 and second_body.get("skipped") is True,
                    f"skipped={second_body.get('skipped')}",
                )

            # 9. search page API shows citations + visible truncation flag
            search = client.get(
                "/ui/api/search",
                params={"q": subject_name, "topK": 5, "tokenBudget": 2048},
            )
            search_body = search.json() if search.status_code == 200 else {}
            suite.check(
                "ui.api.search",
                search.status_code == 200
                and isinstance(search_body.get("chunks"), list)
                and isinstance(search_body.get("citations"), list)
                and "truncated" in search_body
                and "degraded" in search_body,
                f"chunks={len(search_body.get('chunks', []))}",
            )
            truncated = client.get(
                "/ui/api/search",
                params={"q": subject_name, "topK": 5, "tokenBudget": 32},
            )
            truncated_body = truncated.json() if truncated.status_code == 200 else {}
            suite.check(
                "ui.api.truncated_visible",
                truncated.status_code == 200 and truncated_body.get("truncated") is True,
                f"truncated={truncated_body.get('truncated')}",
            )

            # 10. status advertises S7 and the UI port
            status = client.get("/status").json()
            suite.check(
                "http.status",
                status.get("slice") in {"S7", "S8", "S9", "S10", "S11", "S12", "S13"}
                and "context" in status.get("providers", {}),
                f"slice={status.get('slice')}",
            )

            # 11. a bad page API payload is a stable 4xx, not a stack trace
            bad = client.get("/ui/api/neighbors", params={"iri": "bogus"})
            suite.check(
                "ui.api.bad_iri",
                bad.status_code == 400 and bad.json()["error"]["providerCode"] == "E_UI_BAD_IRI",
                f"status={bad.status_code}",
            )
        except PortError as exc:
            suite.fail("runtime", f"{exc.code}/{exc.provider_code}: {exc.message}")
        except httpx.HTTPError as exc:
            suite.fail("http", str(exc))
        finally:
            try:
                runtime.graph.update(f"DROP GRAPH <{test_graph}>")
            except PortError:
                pass
            try:
                runtime.facts.purge_test(test_graph)
            except Exception as exc:  # noqa: BLE001 - cleanup must not mask results
                suite.fail("cleanup.facts", str(exc))

    passed = sum(1 for _, ok, _ in suite.results if ok)
    total = len(suite.results)
    print(f"SMOKE-S7 {passed}/{total}")
    for name, ok, detail in suite.results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    return 0 if passed == total else 1
