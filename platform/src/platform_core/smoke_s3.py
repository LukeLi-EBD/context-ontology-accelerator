"""S3 acceptance: 8 fixed Chinese documents, hybrid/vector/lexical search, RRF
stability, idempotent indexing, dimension errors, embedding degradation, config
fail-fast and the HTTP search/index routes.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import httpx

from .assembly import Runtime, assemble
from .config import load_config
from .errors import PlatformError, PortError

CORPUS: list[tuple[str, str, str]] = [
    (
        "quantum",
        "s3-quantum.txt",
        "量子计算研究简报。量子纠缠是量子信息科学的核心现象，两个粒子无论相隔多远都保持关联。"
        "量子比特可以处于叠加态，量子门对叠加态进行变换，量子测量使叠加态坍缩。"
        "量子隐形传态利用量子纠缠与经典信道传输量子态，量子密钥分发依靠测量塌缩检测窃听。"
        "实验室正在建设超导量子处理器与离子阱量子计算机，量子纠错码是实用化的关键瓶颈。"
        "量子纠缠的制备、分发与保真度评估是当前量子网络研究的主要方向。"
        "本文用于验证检索系统能否稳定召回与量子纠缠主题相关的chunk。",
    ),
    (
        "budget",
        "s3-budget.txt",
        "年度预算与财务报表说明。本年度预算按照部门成本中心编制，财务报表包含资产负债表、利润表与现金流量表。"
        "预算执行率按月统计，超支部门需要提交预算调整申请。财务分析关注毛利率、费用率与现金流周转。"
        "年度审计由外部会计师事务所执行，审计报告提交董事会审议。",
    ),
    (
        "reimbursement",
        "s3-reimbursement.txt",
        "财务报销制度实施细则。本制度规定了差旅费报销、办公用品报销与业务招待费报销的流程与标准。"
        "报销人须在费用发生后十五个工作日内提交报销单据，报销单据须附发票原件与审批单。"
        "财务报销制度要求部门负责人初审、财务复核、总经理终审三级审批，报销金额超过一万元须额外提交说明。"
        "违规报销将追回款项并计入个人诚信记录。",
    ),
    (
        "attendance",
        "s3-attendance.txt",
        "员工考勤管理办法。员工上下班须通过门禁与考勤系统打卡，迟到早退按分钟累计扣减绩效。"
        "请假分为事假、病假、年假与婚丧假，请假须提前在系统提交并由直属主管审批。"
        "远程办公须提前报备，考勤异常每月由人力资源部汇总通报。",
    ),
    (
        "ml",
        "s3-machine-learning.txt",
        "机器学习与神经网络导论。监督学习依赖标注数据，损失函数衡量预测与标签的差异。"
        "反向传播算法通过链式法则计算梯度，随机梯度下降更新网络参数。"
        "卷积神经网络擅长图像识别，循环神经网络与注意力机制擅长序列建模。"
        "过拟合通过正则化、数据增强与早停缓解，模型评估使用交叉验证与混淆矩阵。",
    ),
    (
        "contract",
        "s3-contract.txt",
        "合同法基础条款解读。合同成立需要要约与承诺，合同生效以签字盖章为准。"
        "违约责任包括继续履行、采取补救措施与赔偿损失，不可抗力可以部分或全部免除责任。"
        "合同争议解决方式包括协商、调解、仲裁与诉讼，仲裁条款须明确仲裁机构。",
    ),
    (
        "food",
        "s3-food.txt",
        "食品安全与营养指南。食品加工须控制温度与时间以避免微生物污染，冷藏链保障生鲜品质。"
        "营养均衡强调蛋白质、碳水化合物、脂肪、维生素与矿物质的合理配比。"
        "食品安全抽检覆盖农药残留、重金属与添加剂指标，不合格产品下架并追溯来源。",
    ),
    (
        "city",
        "s3-city.txt",
        "城市规划与公共交通专题。城市总体规划确定用地布局、道路网络与公共设施配置。"
        "公共交通优先策略包括地铁、快速公交与自行车道建设，交通需求管理通过拥堵收费与限行调节。"
        "城市更新关注老旧小区改造、历史街区保护与绿地系统完善。",
    ),
]

TARGET_QUERY = "量子纠缠"
SECOND_QUERY = "财务报销制度"


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def _error_code(response: httpx.Response) -> str:
    try:
        return response.json()["error"]["providerCode"]
    except Exception:  # noqa: BLE001
        return ""


def _overrides(values: dict[str, str]) -> dict[str, str]:
    return {f"PLATFORM__{key.replace('.', '__').upper()}": value for key, value in values.items()}


def _top_chunks(result: dict[str, Any], count: int = 3) -> list[str]:
    return [item["chunkId"] for item in result["results"][:count]]


def run_smoke_s3(runtime: Runtime, base_url: str, bad_config: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    config_path = str(runtime.bundle.path)

    # Fake embedding runtime: deterministic, isolated by model name.
    fake_bundle = load_config(
        config_path,
        environ=_overrides(
            {"embedding.provider": "fake", "embedding.model": "fake-hash-1024"}
        ),
    )
    fake = assemble(fake_bundle)
    degraded_runtime: Runtime | None = None
    original_pointer: dict[str, Any] | None = None

    try:
        fake.metadata.open(retry_seconds=10.0)
        fake.metadata.migrate()
        fake_model = fake.embedding.model_name()
        if fake_model != "fake-hash-1024":
            raise RuntimeError(f"fake runtime model is {fake_model!r}, expected fake-hash-1024")
        # S13b: search reads the active partition from the pointer table, so a
        # fake-vector run must point the DB at its own partition and restore it.
        original_pointer = fake.vectors.pointer()
        fake.vectors.set_pointer("fake", fake_model, fake.embedding.dimensions())

        # 1. ingest 8 fixed documents
        documents: dict[str, str] = {}
        ingest_ok = True
        for slug, filename, text in CORPUS:
            result = fake.documents.ingest_stream(BytesIO(text.encode("utf-8")), filename)
            documents[slug] = result["documentId"]
            ingest_ok = ingest_ok and result["chunkCount"] > 0
        suite.check(
            "corpus.ingest",
            ingest_ok and len(documents) == len(CORPUS),
            f"documents={len(documents)} all_chunks>0={ingest_ok}",
        )

        # 2. index each document with fake vectors
        indexed = {slug: fake.search.index_document(document_id) for slug, document_id in documents.items()}
        fully_embedded = all(
            item["chunks"] > 0 and item["embedded"] == item["chunks"] and not item["degraded"]
            for item in indexed.values()
        )
        suite.check(
            "index.embedded",
            fully_embedded,
            "chunks=" + ",".join(f"{k}:{v['embedded']}/{v['chunks']}" for k, v in indexed.items()),
        )

        # 3. hybrid query A: top-3 stable across two runs, top-1 is the target document
        first = fake.search.hybrid_search(TARGET_QUERY, limit=3)
        second = fake.search.hybrid_search(TARGET_QUERY, limit=3)
        stable = _top_chunks(first) == _top_chunks(second)
        target_top = bool(first["results"]) and first["results"][0]["documentId"] == documents["quantum"]
        suite.check(
            "search.hybrid.target",
            stable and target_top,
            f"stable={stable} top1={first['results'][0]['documentId'][:8] if first['results'] else None} "
            f"quantum={documents['quantum'][:8]}",
        )

        # 4. hybrid query B: stable top-3, target within top 2
        third = fake.search.hybrid_search(SECOND_QUERY, limit=3)
        fourth = fake.search.hybrid_search(SECOND_QUERY, limit=3)
        top_documents = [item["documentId"] for item in third["results"][:2]]
        suite.check(
            "search.hybrid.finance",
            _top_chunks(third) == _top_chunks(fourth)
            and documents["reimbursement"] in top_documents,
            f"stable={_top_chunks(third) == _top_chunks(fourth)} top2={[d[:8] for d in top_documents]}",
        )

        # 5. lexical mode: results, not degraded
        lexical = fake.search.hybrid_search(TARGET_QUERY, limit=5, mode="lexical")
        suite.check(
            "search.lexical",
            bool(lexical["results"]) and lexical["degraded"] is False and lexical["routes"] == ["lexical"],
            f"hits={len(lexical['results'])} routes={lexical['routes']} degraded={lexical['degraded']}",
        )

        # 6. vector mode: results with descending scores
        vector = fake.search.hybrid_search(TARGET_QUERY, limit=5, mode="vector")
        scores = [item["score"] for item in vector["results"]]
        suite.check(
            "search.vector",
            bool(vector["results"]) and scores == sorted(scores, reverse=True) and vector["routes"] == ["vector"],
            f"hits={len(vector['results'])} scores={scores[:3]}",
        )

        # 7. wrong vector dimensions -> InvalidArgument, nothing written
        before = fake.vectors.count(fake_model)
        document_id = documents["quantum"]
        chunk_rows = fake.metadata.query(
            "SELECT chunk_id FROM platform.document_chunk WHERE document_id = %s LIMIT 1",
            (document_id,),
        )
        chunk_id = chunk_rows[0]["chunk_id"]
        try:
            fake.vectors.upsert(
                document_id, [{"chunkId": chunk_id, "vector": [0.1] * 8}], fake_model
            )
            suite.fail("vectors.dim_guard", "8-dim vector was accepted")
        except PortError as exc:
            after = fake.vectors.count(fake_model)
            suite.check(
                "vectors.dim_guard",
                exc.code == "InvalidArgument"
                and exc.provider_code == "E_EMBED_DIM_MISMATCH"
                and after == before,
                f"{exc.code}/{exc.provider_code} rows={before}->{after}",
            )

        # 8. idempotent re-index does not grow embedding rows
        again = fake.search.index_document(document_id)
        after_index = fake.vectors.count(fake_model)
        suite.check(
            "index.idempotent",
            again["embedded"] == again["chunks"] and after_index >= before,
            f"embedded={again['embedded']} rows={before}->{after_index}",
        )

        # 9. embedding endpoint unavailable -> indexing degrades, search falls back to lexical
        degraded_bundle = load_config(
            config_path,
            environ=_overrides(
                {
                    "embedding.provider": "local-bge",
                    "embedding.endpoint": "http://127.0.0.1:9/v1",
                    "embedding.timeout_ms": "2000",
                    "embedding.api_key_env": "S3_EMPTY_KEY",
                }
            ),
        )
        degraded_runtime = assemble(degraded_bundle)
        degraded_runtime.metadata.open(retry_seconds=10.0)
        # S13b: indexing reads the active partition from the pointer table; point it
        # at the degraded runtime's own partition so the dead endpoint is exercised.
        # S14H-P0: isolation — earlier runs may have left vectors for this fixed
        # fixture under the real partition model, which would make index_document
        # skip every chunk (embedded=1, reasons=[]) and never hit the dead endpoint.
        degraded_model = degraded_runtime.embedding.model_name()
        degraded_runtime.metadata.execute(
            """
            DELETE FROM platform.chunk_embedding e
             USING platform.document_chunk c
             WHERE e.chunk_id = c.chunk_id
               AND c.document_id = %s
               AND e.model = %s
            """,
            (document_id, degraded_model),
        )
        degraded_runtime.vectors.set_pointer(
            "local-bge",
            degraded_runtime.embedding.model_name(),
            degraded_runtime.embedding.dimensions(),
        )
        degraded_index = degraded_runtime.search.index_document(document_id)
        suite.check(
            "embedding.unavailable.index",
            degraded_index["embedded"] == 0
            and degraded_index["degraded"] is True
            and "E_EMBED_UNAVAILABLE" in degraded_index["reasons"],
            f"embedded={degraded_index['embedded']} reasons={degraded_index['reasons']}",
        )
        fallback = degraded_runtime.search.hybrid_search(TARGET_QUERY, limit=3)
        suite.check(
            "embedding.unavailable.search",
            bool(fallback["results"])
            and fallback["degraded"] is True
            and fallback["routes"] == ["lexical"]
            and any("E_EMBED" in reason for reason in fallback["reasons"]),
            f"hits={len(fallback['results'])} routes={fallback['routes']} reasons={fallback['reasons']}",
        )
        try:
            degraded_runtime.search.hybrid_search(TARGET_QUERY, mode="vector")
            suite.fail("embedding.unavailable.strict", "vector mode did not fail")
        except PortError as exc:
            suite.check(
                "embedding.unavailable.strict",
                exc.code == "Unavailable" and exc.provider_code == "E_EMBED_UNAVAILABLE",
                f"{exc.code}/{exc.provider_code}",
            )
        # restore the fake partition for the remaining steps
        fake.vectors.set_pointer("fake", fake_model, fake.embedding.dimensions())

        # 10. bad search config -> fail-fast exit 78
        try:
            load_config(bad_config)
            suite.fail("config.failfast", "candidate_k<top_k was accepted")
        except PlatformError as exc:
            suite.check(
                "config.failfast",
                exc.code == "E_CONFIG_SEARCH_RANGE" and exc.exit_code == 78,
                f"{exc.code} exit={exc.exit_code}",
            )

        # 11. empty query -> InvalidArgument
        try:
            fake.search.hybrid_search("   ")
            suite.fail("search.empty_query", "empty query was accepted")
        except PortError as exc:
            suite.check(
                "search.empty_query",
                exc.code == "InvalidArgument" and exc.provider_code == "E_SEARCH_QUERY_EMPTY",
                f"{exc.code}/{exc.provider_code}",
            )

        # 12. HTTP routes on the running server (production embedding config)
        with httpx.Client(timeout=httpx.Timeout(180.0)) as client:
            response = client.get(f"{base}/search", params={"q": TARGET_QUERY, "limit": 5})
            payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            suite.check(
                "http.search",
                response.status_code == 200 and len(payload.get("results", [])) > 0,
                f"http={response.status_code} hits={len(payload.get('results', []))} "
                f"degraded={payload.get('degraded')} routes={payload.get('routes')}",
            )
            index_response = client.post(f"{base}/documents/{document_id}/index")
            suite.check(
                "http.index",
                index_response.status_code == 200
                and index_response.json().get("documentId") == document_id,
                f"http={index_response.status_code} embedded={index_response.json().get('embedded')} "
                f"degraded={index_response.json().get('degraded')}",
            )
            bad_mode = client.get(f"{base}/search", params={"q": TARGET_QUERY, "mode": "bogus"})
            suite.check(
                "http.search_bad_mode",
                bad_mode.status_code == 400 and _error_code(bad_mode) == "E_SEARCH_MODE",
                f"http={bad_mode.status_code} code={_error_code(bad_mode)}",
            )
            status = client.get(f"{base}/status")
            suite.check(
                "http.status",
                status.status_code == 200
                and status.json().get("slice") in {"S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12", "S13"},
                f"http={status.status_code} slice={status.json().get('slice')}",
            )

        # 13. every result carries a usable citation
        complete = all(
            item.get("documentId") and item.get("chunkId") and item.get("text") and item.get("pageFrom")
            for item in first["results"]
        )
        suite.check("results.reference", complete, f"checked={len(first['results'])}")

    finally:
        if degraded_runtime is not None:
            degraded_runtime.close()
        if original_pointer is not None:
            try:
                fake.vectors.set_pointer(
                    original_pointer["provider"],
                    original_pointer["model"],
                    original_pointer["dimensions"],
                )
            except Exception:  # noqa: BLE001 - restore is best-effort
                pass
        fake.close()

    total = len(suite.results)
    passed = sum(1 for _, ok, _ in suite.results if ok)
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print(f"S3 SMOKE {passed}/{total}")
    return 0 if passed == total else 1
