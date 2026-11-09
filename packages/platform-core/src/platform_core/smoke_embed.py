"""S13b embedding-partition contract tests (3 contracts + guard errors).

Contracts:
1. partitions are mutually invisible: a 1024d query never returns a 2048d chunk;
2. after switching the pointer, queries hit the new partition and are non-empty;
3. switching back keeps the old partition usable.
Also checks the write/search guards raise E_EMBED_MODEL_MISMATCH / E_EMBED_DIM_MISMATCH.

S14H-BURST: every run is isolated. It uses a throwaway namespace
(``smoke-embed-<token>``) and throwaway partition names
(``smoke-hash-1024-<token>`` / ``smoke-hash-2048-<token>``), so no production
vector partition is ever written. Any production pointer it must touch is
snapshotted, restored, and verified; the suite fails (exit 1) when the active
partition, the T-Box pointer, or the inferred pointer is left polluted.
"""

from __future__ import annotations

import uuid
from io import BytesIO
from typing import Any

from .assembly import Runtime, assemble
from .config import load_config
from .errors import PortError
from .adapters.embedding import FAKE_MODEL

P1_DIMS = 1024
P2_DIMS = 2048

TEXT_A = "量子纠缠实验在低温光学平台上完成，测量了纠缠态的保真度。"
TEXT_B = "财务报销制度规定差旅费用在三十日内提交凭证。"


def _overrides(values: dict[str, str]) -> dict[str, str]:
    return {f"PLATFORM__{key.replace('.', '_').upper()}": value for key, value in values.items()}


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)


def _snapshot(runtime: Runtime) -> dict[str, Any]:
    """Capture every pointer this suite could plausibly disturb."""
    tbox = runtime.metadata.query(
        "SELECT version_id FROM platform.graph_pointer WHERE name = 'tbox/current'"
    )
    inferred = runtime.metadata.query(
        "SELECT ontology_version FROM platform.inferred_pointer WHERE name = 'default'"
    )
    return {
        "embedding": runtime.vectors.pointer(),
        "tbox": str(tbox[0]["version_id"]) if tbox else None,
        "inferred": str(inferred[0]["ontology_version"]) if inferred else None,
    }


def _expected_embedding(runtime: Runtime) -> dict[str, Any]:
    """The production partition this config declares (never the live pointer)."""
    return {
        "provider": runtime.config.embedding.provider,
        "model": runtime.embedding.model_name(),
        "dimensions": runtime.embedding.dimensions(),
    }


def _restore_embedding(runtime: Runtime, snapshot: dict[str, Any]) -> dict[str, Any]:
    before = runtime.vectors.pointer()
    target = snapshot["embedding"]
    runtime.vectors.set_pointer(
        target["provider"], target["model"], target["dimensions"]
    )
    after = runtime.vectors.pointer()
    print(
        "restore embedding pointer: before="
        f"{before['provider']}:{before['model']}@{before['dimensions']} after="
        f"{after['provider']}:{after['model']}@{after['dimensions']}"
    )
    return after


def _verify_no_pollution(
    runtime: Runtime,
    suite: _Case,
    snapshot: dict[str, Any],
    expected: dict[str, Any],
    created_versions: set[str],
) -> None:
    active = runtime.vectors.pointer()
    suite.check(
        "post.active_partition",
        active == expected,
        f"active={active['provider']}:{active['model']}@{active['dimensions']} "
        f"expected={expected['provider']}:{expected['model']}@{expected['dimensions']}",
    )
    current = _snapshot(runtime)
    tbox_now = current["tbox"]
    suite.check(
        "post.tbox_pointer",
        tbox_now == snapshot["tbox"] and tbox_now not in created_versions,
        f"tbox={tbox_now} snapshot={snapshot['tbox']} smoke_versions={sorted(created_versions)}",
    )
    suite.check(
        "post.inferred_pointer",
        current["inferred"] == snapshot["inferred"],
        f"inferred={current['inferred']} snapshot={snapshot['inferred']}",
    )


def _embed(runtime: Runtime, model: str, texts: list[str], dims: int) -> list[list[float]]:
    return runtime.embedding.embed_with("fake", model, texts, dims)


def _write_partition(runtime: Runtime, model: str, dims: int, document_id: str) -> int:
    rows = runtime.metadata.query(
        "SELECT chunk_id, text FROM platform.document_chunk "
        "WHERE document_id = %s ORDER BY seq",
        (document_id,),
    )
    if not rows:
        return 0
    vectors = _embed(runtime, model, [str(row["text"]) for row in rows], dims)
    runtime.vectors.upsert(
        document_id,
        [
            {"chunkId": str(row["chunk_id"]), "vector": vector}
            for row, vector in zip(rows, vectors)
        ],
        model,
        enforce_active=False,
    )
    return len(rows)


def _chunk_model(runtime: Runtime, chunk_id: str) -> set[str]:
    rows = runtime.metadata.query(
        "SELECT model FROM platform.chunk_embedding WHERE chunk_id = %s", (chunk_id,)
    )
    return {row["model"] for row in rows}


def _cleanup(runtime: Runtime, document_ids: list[str], models: list[str]) -> None:
    for model in models:
        runtime.metadata.execute(
            "DELETE FROM platform.chunk_embedding WHERE model = %s", (model,)
        )
    if not document_ids:
        return
    marks = ", ".join(["%s"] * len(document_ids))
    params = tuple(document_ids)
    runtime.metadata.execute(
        f"""
        DELETE FROM platform.chunk_embedding e
         USING platform.document_chunk c
         WHERE e.chunk_id = c.chunk_id AND c.document_id IN ({marks})
        """,
        params,
    )
    runtime.metadata.execute(
        f"DELETE FROM platform.document_chunk WHERE document_id IN ({marks})", params
    )
    runtime.metadata.execute(
        f"DELETE FROM platform.document WHERE document_id IN ({marks})", params
    )


def run_smoke_embed(runtime: Runtime) -> int:
    suite = _Case()
    token = uuid.uuid4().hex[:8]
    p1_model = f"{FAKE_MODEL}-smoke-{token}"
    p2_model = f"fake-hash-2048-smoke-{token}"
    namespace = f"smoke-embed-{token}"

    config_path = str(runtime.bundle.path)
    fake_bundle = load_config(
        config_path,
        environ=_overrides({"embedding.provider": "fake", "embedding.model": p1_model}),
    )
    fake_rt = assemble(fake_bundle)
    snapshot = _snapshot(runtime)
    expected = _expected_embedding(runtime)
    document_ids: list[str] = []
    created_versions: set[str] = set()
    try:
        fake_rt.metadata.open(retry_seconds=10.0)
        fake_rt.metadata.migrate()

        # 0. only the throwaway 1024 partition is ever the active write target.
        fake_rt.vectors.set_pointer("fake", p1_model, P1_DIMS)

        # 1. ingest two documents and index doc A into the throwaway 1024 partition.
        doc_a = fake_rt.documents.ingest_stream(
            BytesIO(TEXT_A.encode("utf-8")), f"{namespace}-a.txt"
        )["documentId"]
        doc_b = fake_rt.documents.ingest_stream(
            BytesIO(TEXT_B.encode("utf-8")), f"{namespace}-b.txt"
        )["documentId"]
        document_ids.extend([doc_a, doc_b])
        indexed = fake_rt.search.index_document(doc_a)
        suite.check(
            "index.active_partition",
            indexed["embedded"] > 0
            and indexed["model"] == p1_model
            and indexed["dimensions"] == P1_DIMS,
            f"embedded={indexed['embedded']} model={indexed['model']} dims={indexed['dimensions']}",
        )
        # doc B gets a 2048 vector only (inactive partition write).
        written = _write_partition(fake_rt, p2_model, P2_DIMS, doc_b)
        suite.check("partition.b.write", written > 0, f"chunks={written}")

        # 2. Contract 1: partitions are mutually invisible.
        query = "量子纠缠"
        active = fake_rt.vectors.pointer()
        vector = _embed(fake_rt, active["model"], [query], active["dimensions"])[0]
        hits = fake_rt.vectors.search(vector, active["model"], 10)
        hit_models = {
            model for item in hits for model in _chunk_model(fake_rt, item["chunkId"])
        }
        doc_b_hits = [item for item in hits if item["documentId"] == doc_b]
        suite.check(
            "contract.1.partition_invisible",
            bool(hits) and p2_model not in hit_models and not doc_b_hits,
            f"hits={len(hits)} models={sorted(hit_models)} docB={len(doc_b_hits)}",
        )

        # 3. Contract 2: switch the throwaway pointer, queries hit the new partition.
        fake_rt.vectors.set_pointer("fake", p2_model, P2_DIMS)
        switched = fake_rt.search.hybrid_search("财务报销", limit=5, mode="vector")
        suite.check(
            "contract.2.switched_nonempty",
            switched.get("results") and not switched.get("degraded"),
            f"hits={len(switched.get('results') or [])} degraded={switched.get('degraded')} "
            f"reasons={switched.get('reasons')}",
        )

        # 4. Contract 3: switch back, the old partition is still usable.
        fake_rt.vectors.set_pointer("fake", p1_model, P1_DIMS)
        back = fake_rt.search.hybrid_search("量子纠缠", limit=5, mode="vector")
        suite.check(
            "contract.3.switch_back",
            back.get("results") and not back.get("degraded"),
            f"hits={len(back.get('results') or [])} degraded={back.get('degraded')}",
        )

        # 4b. leave production active immediately, not at the end of the run.
        restored = _restore_embedding(runtime, snapshot)
        suite.check(
            "restore.before_guards",
            restored == expected,
            f"restored={restored} expected={expected}",
        )

        # 5. Write guard: wrong model under the active pointer.
        try:
            fake_rt.vectors.upsert(
                doc_a,
                [
                    {"chunkId": str(row["chunk_id"]), "vector": [0.0] * P2_DIMS}
                    for row in fake_rt.metadata.query(
                        "SELECT chunk_id FROM platform.document_chunk "
                        "WHERE document_id = %s ORDER BY seq LIMIT 1",
                        (doc_a,),
                    )
                ],
                p2_model,
            )
            suite.check("guard.model_mismatch", False, "upsert accepted a foreign model")
        except PortError as exc:
            suite.check(
                "guard.model_mismatch",
                exc.provider_code == "E_EMBED_MODEL_MISMATCH",
                f"{exc.code}/{exc.provider_code}",
            )

        # 6. Query guard: dimension does not match the (restored) production model.
        try:
            fake_rt.vectors.search([0.0] * P2_DIMS, expected["model"], 5)
            suite.check("guard.dim_mismatch", False, "search accepted a foreign dimension")
        except PortError as exc:
            suite.check(
                "guard.dim_mismatch",
                exc.provider_code == "E_EMBED_DIM_MISMATCH",
                f"{exc.code}/{exc.provider_code}",
            )

        # 7. Partitions listing shows both throwaway models with their own dimension.
        parts = {item["model"]: item["dimensions"] for item in fake_rt.vectors.partitions()}
        suite.check(
            "partition.listed",
            parts.get(p1_model) == P1_DIMS and parts.get(p2_model) == P2_DIMS,
            f"partitions={ {k: v for k, v in parts.items() if 'smoke' in k} }",
        )
    finally:
        try:
            _restore_embedding(runtime, snapshot)
        except Exception:  # noqa: BLE001 - never mask the real failure
            pass
        try:
            _cleanup(fake_rt, document_ids, [p1_model, p2_model])
        except Exception:  # noqa: BLE001
            pass
        fake_rt.close()

    _verify_no_pollution(runtime, suite, snapshot, expected, created_versions)

    total = len(suite.results)
    passed = sum(1 for _, ok, _ in suite.results if ok)
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print(f"S13b SMOKE {passed}/{total}")
    return 0 if passed == total else 1
