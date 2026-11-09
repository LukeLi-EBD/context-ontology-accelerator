"""S14H-CORES: embedding throughput probe (short vs long chunk tiers).

Creates a throwaway document namespace (``bench-<token>``), inserts synthetic
chunks directly (no parser variance), indexes them through the real
``index_document`` path, and reports where the wall time goes:

* ``tei_service_ms``: HTTP call to TEI ``/v1/embeddings`` (no gate wait)
* ``queue_wait_ms``: time blocked on the platform single-flight semaphore
* ``platform_ms``: prep + pgvector upsert + checkpoint commit, per chunk

The probe never touches the embedding/graph pointers and always deletes the
rows it created.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
import uuid
from typing import Any

from .assembly import Runtime

SHORT_CHARS = (160, 320)
LONG_CHARS = (1200, 1500)


def _text(seed: int, chars: int) -> str:
    base = f"bench 段落 {seed}：低温光学平台上的纠缠态测量与报销制度条款 "
    while len(base) < chars:
        base += f"第{len(base)}字符补足 "
    return base[:chars]


def _insert_document(
    runtime: Runtime, short_n: int, long_n: int
) -> tuple[str, list[int]]:
    token = uuid.uuid4().hex
    document_id = token
    rows: list[tuple[str, int, int, str]] = []  # chunk_id, seq, chars, text
    seq = 0
    for index in range(short_n):
        text = _text(index, SHORT_CHARS[0] + (index % 5) * 40)
        rows.append((hashlib.sha256(f"{token}-s-{index}".encode()).hexdigest(), seq, len(text), text))
        seq += 1
    for index in range(long_n):
        text = _text(1000 + index, LONG_CHARS[0] + (index % 4) * 100)
        rows.append((hashlib.sha256(f"{token}-l-{index}".encode()).hexdigest(), seq, len(text), text))
        seq += 1

    total_chars = sum(width for _, _, width, _ in rows)
    runtime.metadata.execute(
        """
        INSERT INTO platform.document
            (document_id, sha256, bucket, object_key, filename, mime_type,
             size_bytes, status, page_count, char_count, chunk_count,
             parser, parser_version)
        VALUES (%s, %s, 'documents', %s, %s, 'text/plain', %s, 'parsed',
                0, %s, %s, 'bench-embed', 'bench')
        """,
        (
            document_id,
            hashlib.sha256(token.encode()).hexdigest(),
            document_id,
            f"bench-embed-{token[:8]}.txt",
            total_chars,
            total_chars,
            len(rows),
        ),
    )
    for chunk_id, ordinal, width, text in rows:
        runtime.metadata.execute(
            """
            INSERT INTO platform.document_chunk
                (chunk_id, document_id, seq, page_from, page_to,
                 char_start, char_end, text, token_estimate)
            VALUES (%s, %s, %s, 1, 1, 0, %s, %s, %s)
            """,
            (chunk_id, document_id, ordinal, width, text, max(1, width // 3)),
        )
    return document_id, [width for _, _, width, _ in rows]


def _short_warnings(widths: list[int], short_n: int) -> str | None:
    if any(width >= 900 for width in widths[:short_n]):
        return "short tier contains a chunk >= long_chunk_chars"
    return None


def run_bench_embed(runtime: Runtime, short_n: int, long_n: int) -> int:
    runtime.embedding.reset_metrics()
    document_id, widths = _insert_document(runtime, short_n, long_n)
    started = time.monotonic()
    try:
        indexed = runtime.search.index_document(document_id)
    finally:
        wall_s = time.monotonic() - started
    samples = runtime.embedding.drain_metrics()

    tiers: dict[str, list[dict[str, float]]] = {"short": [], "long": []}
    for sample in samples:
        tier = "long" if int(sample["chars"]) >= 900 else "short"
        chunks = max(1, int(sample["chunks"]))
        tiers[tier].append(
            {
                "service": float(sample["serviceMs"]) / chunks,
                "wait": float(sample["waitMs"]) / chunks,
            }
        )

    timing = indexed.get("timingMs") or {}
    chunks = max(1, int(indexed.get("chunks") or 0))
    platform_per_chunk = (
        float(timing.get("prep", 0.0))
        + float(timing.get("upsert", 0.0))
        + float(timing.get("checkpoint", 0.0))
    ) / chunks

    report: dict[str, Any] = {
        "chunks": int(indexed.get("chunks") or 0),
        "embedded": int(indexed.get("embedded") or 0),
        "remaining": int(indexed.get("remaining") or 0),
        "degraded": bool(indexed.get("degraded")),
        "model": indexed.get("model"),
        "wallS": round(wall_s, 3),
        "chunkPerS": round(int(indexed.get("embedded") or 0) / max(wall_s, 0.001), 3),
        "platformMsPerChunk": round(platform_per_chunk, 3),
        "timingMs": timing,
        "tiers": {},
    }
    for tier, values in tiers.items():
        if not values:
            continue
        service = statistics.median(item["service"] for item in values)
        wait = statistics.median(item["wait"] for item in values)
        per_chunk = service + wait + platform_per_chunk
        report["tiers"][tier] = {
            "batches": len(values),
            "teiServiceMs": round(service, 3),
            "queueWaitMs": round(wait, 3),
            "platformMs": round(platform_per_chunk, 3),
            "totalMsPerChunk": round(per_chunk, 3),
            "sharePct": {
                "tei": round(service / per_chunk * 100, 2) if per_chunk else 0,
                "wait": round(wait / per_chunk * 100, 2) if per_chunk else 0,
                "platform": round(platform_per_chunk / per_chunk * 100, 2)
                if per_chunk
                else 0,
            },
        }
    warning = _short_warnings(widths, short_n)
    if warning:
        report["warning"] = warning
    _cleanup(runtime, document_id)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not report["degraded"] else 1


def _cleanup(runtime: Runtime, document_id: str) -> None:
    runtime.metadata.execute(
        "DELETE FROM platform.document WHERE document_id = %s", (document_id,)
    )
