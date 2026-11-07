"""G3 metrics-report API tests (M-02: publishable governance manifest + export).

Pure API tests with an in-memory metadata fake; no postgres is required.
Run them with:
  docker run --rm --entrypoint python -v <repo>/src:/app/src:ro \
    -v <repo>/tests:/app/tests:ro agent-platform:0.1-s5 \
    /app/tests/test_metrics_report.py
"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/app/src")
sys.path.insert(0, "../src")

import platform_core.api as api_module


def _row(
    metric_id,
    domain="bank",
    basis="regulatory",
    publishable=True,
    tier="structurally_computable",
    metric_kind="ratio",
    formula_text="numerator/denominator*100",
    formula_expr="numerator / denominator",
    missing=None,
    inference=False,
    output_mode="value",
    variant_of=None,
    provenance="原文",
    formula_disabled=False,
    denominator_text=None,
    window_text="period（自然月）",
    min_window_days=28,
    grain="institution",
    granularity=None,
    window_kind="period",
    numerator_bindings=1,
    denominator_bindings=1,
    observation_count=1,
    observation_start=date(2025, 1, 1),
    observation_end=date(2025, 12, 31),
):
    return {
        "metric_id": metric_id,
        "name_zh": f"{metric_id} 名称",
        "display_name": f"{metric_id} 展示名",
        "domain": domain,
        "evidence_basis": basis,
        "publishable": publishable,
        "inference": inference,
        "formula_disabled": formula_disabled,
        "missing": missing,
        "evidence_status": "defined",
        "note": None,
        "definition_version": "v3",
        "metric_kind": metric_kind,
        "formula_expr": formula_expr,
        "formula_text": formula_text,
        "denominator_text": denominator_text,
        "numerator_agg": "sum",
        "denominator_agg": "sum",
        "window_kind": window_kind,
        "min_window_days": min_window_days,
        "observation_period": window_text,
        "grain": grain,
        "granularity": granularity or grain,
        "unit": "%",
        "effective_date": "2026-01-01",
        "variant_of": variant_of,
        "output_mode": output_mode,
        "provenance_label": provenance,
        "computability_tier": tier,
        "numerator_bindings": numerator_bindings,
        "denominator_bindings": denominator_bindings,
        "observation_count": observation_count,
        "observation_start": observation_start,
        "observation_end": observation_end,
    }


ROWS = [
    _row("FIN-BANK-001"),
    _row("FIN-BANK-002", basis="industry", publishable=True, provenance="行业通行"),
    _row("FIN-BANK-003", publishable=False, missing="regulatory_source", provenance="推测"),
    _row("FIN-BANK-004", tier="blocked_semantics", formula_text=None, formula_expr=None),
    _row(
        "FIN-BANK-036",
        basis="industry",
        publishable=False,
        tier="blocked_semantics",
        output_mode="index",
        formula_text="不适用（族索引）",
        provenance="行业通行",
    ),
]


class FakeMetadata:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def query(self, sql, params=()):
        self.calls.append((sql, params))
        rows = list(self.rows)
        if "WHERE metric_id = %s" in sql:
            rows = [row for row in rows if row["metric_id"] == params[0]]
        return rows


class FakeProv:
    def __init__(self, count=0):
        self.count = count

    def decision_history(self, metric_id, limit=20):
        return {"metricId": metric_id, "count": self.count, "items": []}


def _client(rows=ROWS, prov=None):
    runtime = SimpleNamespace(metadata=FakeMetadata(rows))
    if prov is not None:
        runtime.prov = prov
    return TestClient(api_module.create_app(runtime, []))


class ManifestTests(unittest.TestCase):
    def test_1_manifest_is_db_shaped_and_complete(self):
        with _client() as client:
            payload = client.get("/metrics/report/manifest").json()
        self.assertEqual(payload["count"], len(ROWS))
        self.assertEqual(payload["meta"]["source"], "platform.metric_definition")
        self.assertEqual(payload["meta"]["total"], len(ROWS))
        self.assertEqual(payload["meta"]["allTotal"], len(ROWS))
        first = payload["items"][0]
        for key in (
            "metricId",
            "publishable",
            "evidenceBasis",
            "evidenceSource",
            "formula",
            "computability",
            "computabilityLabel",
            "gap",
            "externalEligible",
            "externalStatus",
            "variantOf",
            "outputMode",
            "definitionVersion",
        ):
            self.assertIn(key, first)

    def test_2_computability_never_implies_observed_value(self):
        with _client() as client:
            payload = client.get("/metrics/report/manifest").json()
        self.assertIn("不代表已有观测值", payload["meta"]["disclaimer"])
        tier_labels = {item["metricId"]: item["computabilityLabel"] for item in payload["items"]}
        self.assertEqual(tier_labels["FIN-BANK-001"], "结构性可算（需事实与观测）")
        self.assertEqual(tier_labels["FIN-BANK-004"], "语义阻断")

    def test_3_gap_prefers_db_missing_then_variant_guidance(self):
        with _client() as client:
            payload = client.get("/metrics/report/manifest").json()
        rows = {item["metricId"]: item for item in payload["items"]}
        self.assertEqual(rows["FIN-BANK-003"]["gap"], "缺监管原文")
        self.assertEqual(rows["FIN-BANK-003"]["gapCode"], "regulatory_source")
        self.assertEqual(rows["FIN-BANK-004"]["gap"], "公式缺失")
        self.assertIn("E_METRIC_VARIANT_REQUIRED", rows["FIN-BANK-036"]["gap"])

    def test_4_external_scope_excludes_industry_and_blocked(self):
        with _client() as client:
            governance = client.get("/metrics/report/manifest").json()
            external = client.get(
                "/metrics/report/manifest", params={"scope": "external"}
            ).json()
        self.assertEqual(governance["count"], len(ROWS))
        self.assertEqual([item["metricId"] for item in external["items"]], ["FIN-BANK-001"])
        self.assertEqual(external["meta"]["counts"]["externalEligible"], 1)
        self.assertNotIn(
            "industry",
            {item["evidenceBasis"] for item in external["items"]},
        )

    def test_5_csv_export_reuses_the_same_rows(self):
        with _client() as client:
            csv_response = client.get(
                "/metrics/report/manifest.csv", params={"scope": "external"}
            )
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("text/csv", csv_response.headers["content-type"])
        self.assertIn(
            "attachment",
            csv_response.headers["content-disposition"],
        )
        body = csv_response.content.decode("utf-8")
        self.assertTrue(body.startswith("\ufeff"))
        lines = [line for line in body.splitlines() if line.strip()]
        # 表头 + 1 条对外可出数候选
        self.assertEqual(len(lines), 2)
        self.assertIn("可算性", lines[0])
        self.assertIn("FIN-BANK-001", lines[1])

    def test_6_filters_are_applied_after_db_read(self):
        with _client() as client:
            payload = client.get(
                "/metrics/report/manifest",
                params={"domain": "bank", "evidenceBasis": "industry"},
            ).json()
        self.assertEqual(payload["count"], 2)
        self.assertEqual(
            {item["metricId"] for item in payload["items"]},
            {"FIN-BANK-002", "FIN-BANK-036"},
        )

    def test_7_invalid_scope_is_rejected(self):
        with _client() as client:
            response = client.get("/metrics/report/manifest", params={"scope": "bogus"})
        self.assertEqual(response.status_code, 422)

    def test_8_external_counts_separate_eligibility_from_executable(self):
        rows = [
            _row("FIN-BANK-001", numerator_bindings=0, denominator_bindings=0),
            _row("FIN-INS-002", output_mode="rule_set"),
            _row("FIN-INS-003", observation_count=0, observation_start=None,
                 observation_end=None),
            _row("FIN-INS-004", metric_kind="amount", formula_expr="numerator",
                 numerator_bindings=0, denominator_bindings=0),
        ]
        with _client(rows) as client:
            payload = client.get(
                "/metrics/report/manifest", params={"scope": "external"}
            ).json()
        counts = payload["meta"]["counts"]
        execution = payload["meta"]["execution"]
        self.assertEqual(counts["externalEligible"], 4)
        self.assertEqual(counts["externalCandidates"], 4)
        # binding 不是 compute 的门槛；amount 已放开，故两条为 compute。
        self.assertEqual(counts["executableNow"], 2)
        self.assertEqual(execution["executableNow"], 2)
        self.assertEqual(execution["ruleSetOnly"], 1)
        self.assertEqual(execution["unavailable"], 1)
        self.assertEqual(execution["byReason"], {"no_observations": 1})
        self.assertIn("只读预检", execution["basis"])
        self.assertIn("未含观测与窗口", execution["note"])

    def test_9_manifest_row_declares_execution_path_and_reason(self):
        rows = [
            _row("FIN-BANK-001", numerator_bindings=0, denominator_bindings=0),
            _row("FIN-INS-014", metric_kind="amount", formula_expr="numerator",
                 numerator_bindings=0, denominator_bindings=0),
            _row("FIN-INS-002", output_mode="rule_set"),
            _row("FIN-INS-003", observation_count=0, observation_start=None,
                 observation_end=None),
        ]
        with _client(rows) as client:
            payload = client.get("/metrics/report/manifest").json()
        by_id = {item["metricId"]: item for item in payload["items"]}
        compute = by_id["FIN-BANK-001"]
        self.assertEqual(compute["executionPath"], "compute")
        self.assertTrue(compute["executable"])
        # 资格判定只看三项，必须在说明里写明未检查观测与窗口。
        self.assertIn("未含观测与窗口", compute["externalReason"])
        # compute 不校验 binding：没有 binding 但已有观测，仍应判为可算。
        self.assertNotIn("numeratorBinding", compute["executionChecks"])
        amount = by_id["FIN-INS-014"]
        self.assertEqual(amount["executionPath"], "compute")
        self.assertTrue(amount["executable"])
        self.assertEqual(amount["executionReasonCode"], "compute_ready")
        rule_set = by_id["FIN-INS-002"]
        self.assertEqual(rule_set["executionPath"], "rule_set")
        self.assertFalse(rule_set["executable"])
        self.assertEqual(rule_set["executionReasonCode"], "rule_set_only")
        self.assertIn("/rules", rule_set["executionReason"])
        self.assertIn("rule_set_only", rule_set["externalReason"])
        missing = by_id["FIN-INS-003"]
        self.assertEqual(missing["executionPath"], "unavailable")
        self.assertEqual(missing["executionReasonCode"], "no_observations")
        self.assertIn("无任何观测", missing["executionReason"])

    def test_10_csv_export_carries_execution_columns(self):
        rows = [
            _row("FIN-BANK-001", numerator_bindings=0, denominator_bindings=0),
            _row("FIN-INS-002", output_mode="rule_set"),
            _row("FIN-INS-003", observation_count=0, observation_start=None,
                 observation_end=None),
        ]
        with _client(rows) as client:
            body = client.get(
                "/metrics/report/manifest.csv", params={"scope": "external"}
            ).content.decode("utf-8")
        lines = [line for line in body.splitlines() if line.strip()]
        self.assertEqual(len(lines), 4)
        for column in ("可执行路径", "可执行", "执行判定说明", "可用窗口天数", "要求窗口天数"):
            self.assertIn(column, lines[0])
        compute_line = next(line for line in lines[1:] if "FIN-BANK-001" in line)
        self.assertIn("compute", compute_line)
        self.assertIn("true", compute_line)
        rule_line = next(line for line in lines[1:] if "FIN-INS-002" in line)
        self.assertIn("rule_set", rule_line)
        self.assertIn("false", rule_line)


E1_IDS = (
    "FIN-BANK-002",
    "FIN-BANK-005",
    "FIN-BANK-017",
    "FIN-BANK-018",
    "FIN-BANK-019",
    "FIN-BANK-033",
    "FIN-BANK-034",
    "FIN-BANK-006",
    "FIN-BANK-020",
    "FIN-BANK-021",
    "FIN-BANK-031",
    "FIN-BANK-032",
    "FIN-BANK-035",
    "FIN-BANK-036-v1",
    "FIN-INS-003",
    "FIN-INS-006",
    "FIN-INS-007",
    "FIN-INS-017",
    "FIN-INS-022-v1",
    "FIN-INS-023-v1",
    "FIN-INS-024",
    "FIN-INS-026",
    "CUST-005",
    "CUST-009",
    "CUST-010",
)


def _e1_rows():
    rows = []
    for metric_id in E1_IDS:
        rows.append(
            _row(
                metric_id,
                basis="industry",
                publishable=metric_id != "FIN-BANK-034",
                tier=(
                    "blocked_semantics"
                    if metric_id in {"FIN-BANK-019", "FIN-BANK-020", "FIN-BANK-021"}
                    else "structurally_computable"
                ),
                provenance="行业通行",
            )
        )
    rows.append(_row("FIN-BANK-001", provenance="原文"))
    rows.append(_row("CUST-001", basis="industry", publishable=False, provenance="推测"))
    return rows


class IndustryBaselineTests(unittest.TestCase):
    def test_1_all_25_e1_rows_are_marked_industry(self):
        with _client(_e1_rows()) as client:
            payload = client.get("/metrics/report/manifest").json()
        check = payload["meta"]["e1Check"]
        self.assertEqual(check["expected"], 25)
        self.assertEqual(check["found"], 25)
        self.assertTrue(check["allPresent"])
        self.assertTrue(check["allIndustry"])
        self.assertEqual(check["missingIds"], [])
        self.assertEqual(check["violations"], [])
        self.assertEqual(check["publishableTrue"], 24)
        for item in payload["items"]:
            if item["metricId"] in E1_IDS:
                self.assertTrue(item["e1Baseline"])
                self.assertTrue(item["industryBaseline"])
                self.assertEqual(item["internalNotice"], "内部基线、不外报")
                self.assertEqual(item["externalLabel"], "内部基线、不外报")

    def test_2_external_scope_excludes_every_industry_row(self):
        with _client(_e1_rows()) as client:
            external = client.get(
                "/metrics/report/manifest", params={"scope": "external"}
            ).json()
        self.assertEqual([item["metricId"] for item in external["items"]], ["FIN-BANK-001"])
        self.assertEqual(external["meta"]["counts"]["industryExcludedFromExternal"], 26)
        self.assertNotIn(
            "industry", {item["evidenceBasis"] for item in external["items"]}
        )
        self.assertEqual(external["meta"]["industryNotice"], "内部基线、不外报")

    def test_3_inconsistent_or_missing_e1_row_is_reported_not_hidden(self):
        rows = _e1_rows()
        rows[0] = _row("FIN-BANK-002", basis="regulatory", provenance="原文")
        rows = [row for row in rows if row["metric_id"] != "FIN-INS-026"]
        with _client(rows) as client:
            payload = client.get("/metrics/report/manifest").json()
        check = payload["meta"]["e1Check"]
        self.assertFalse(check["allIndustry"])
        self.assertFalse(check["allPresent"])
        self.assertEqual(check["violations"], ["FIN-BANK-002"])
        self.assertEqual(check["missingIds"], ["FIN-INS-026"])


FAMILY_ROWS = [
    _row(
        "FIN-BANK-036",
        basis="industry",
        publishable=False,
        tier="blocked_semantics",
        output_mode="index",
        formula_text="不适用（族索引）",
        denominator_text="不适用（族索引；v1=期初不良资产余额，v2=期内处置标的账面金额）",
        window_text="不适用（族索引；季度/年度）",
        grain="",
        granularity="不适用（族索引）",
        provenance="行业通行",
    ),
    _row(
        "FIN-BANK-036-v1",
        basis="industry",
        publishable=True,
        variant_of="FIN-BANK-036",
        denominator_text="期初不良资产余额（单位 元）",
        window_text="period（季度/年度，≥90 天）",
        min_window_days=90,
        granularity="institution/product/处置方式",
        provenance="行业通行",
    ),
    _row(
        "FIN-BANK-036-v2",
        basis="industry",
        publishable=False,
        variant_of="FIN-BANK-036",
        formula_text="numerator / denominator * 100（分母=期内完成处置不良账面金额）",
        denominator_text="期内完成处置的不良资产账面金额（有回收方式）",
        window_text="period（季度/年度；与 v1 同一报告期）",
        min_window_days=90,
        granularity="institution，可按 product/处置方式",
        provenance="行业通行",
    ),
    _row(
        "FIN-INS-022",
        domain="insurance",
        basis="industry",
        publishable=False,
        tier="blocked_semantics",
        output_mode="index",
        formula_text="不适用（族索引）",
        denominator_text="不适用（族索引）",
        window_text="不适用（族索引；变体观察期见 v1/v2）",
        granularity="不适用（族索引）",
        provenance="行业通行",
    ),
    _row(
        "FIN-INS-022-v1",
        domain="insurance",
        basis="industry",
        publishable=True,
        variant_of="FIN-INS-022",
        denominator_text="该批新单首个保单年度实收规模保费",
        window_text="period（12 个月 cohort，观察至宽限期截止）",
        min_window_days=365,
        grain="product",
        provenance="行业通行",
    ),
    _row(
        "FIN-INS-022-v2",
        domain="insurance",
        basis="industry",
        publishable=False,
        variant_of="FIN-INS-022",
        denominator_text="该批期交新单首个保单年度实收规模保费；按保单号去重",
        window_text="period（评价期前溯 12 个月承保 cohort）",
        min_window_days=365,
        grain="product",
        provenance="行业通行",
    ),
    _row("FIN-BANK-001"),
]


class FamilyTests(unittest.TestCase):
    def test_1_families_group_index_and_variants(self):
        with _client(FAMILY_ROWS) as client:
            payload = client.get("/metrics/report/families").json()
        self.assertEqual(payload["count"], 2)
        self.assertEqual([f["familyId"] for f in payload["families"]],
                         ["FIN-BANK-036", "FIN-INS-022"])
        bank036 = payload["families"][0]
        self.assertEqual(bank036["indexMetricId"], "FIN-BANK-036")
        self.assertTrue(bank036["selectionRequired"])
        self.assertEqual(bank036["variantCount"], 2)
        self.assertEqual([v["metricId"] for v in bank036["variants"]],
                         ["FIN-BANK-036-v1", "FIN-BANK-036-v2"])

    def test_2_window_denominator_and_grain_are_side_by_side(self):
        with _client(FAMILY_ROWS) as client:
            family = client.get("/metrics/report/families/FIN-BANK-036").json()["family"]
        diffs = {diff["field"]: diff for diff in family["diffs"]}
        self.assertEqual(set(diffs), {"observationPeriod", "denominator", "grain", "formula"})
        self.assertTrue(diffs["denominator"]["different"])
        self.assertTrue(diffs["observationPeriod"]["different"])
        self.assertTrue(diffs["grain"]["different"])
        self.assertTrue(diffs["formula"]["different"])
        for variant in family["variants"]:
            self.assertIn("text", variant["window"])
            self.assertIn("minWindowDays", variant["window"])
            self.assertIn("denominator", variant)
            self.assertIn("grain", variant)

    def test_3_variant_required_guidance_is_explicit(self):
        with _client(FAMILY_ROWS) as client:
            payload = client.get("/metrics/report/families").json()
        family = payload["families"][0]
        self.assertEqual(family["guidance"]["code"], "E_METRIC_VARIANT_REQUIRED")
        self.assertIn("回填 metric_id", family["guidance"]["message"])
        self.assertEqual(len(family["guidance"]["howTo"]), 3)
        self.assertEqual(payload["guidance"]["code"], "E_METRIC_VARIANT_REQUIRED")
        self.assertFalse(family["variants"][0]["externalEligible"])

    def test_4_unknown_family_is_typed_404(self):
        with _client(FAMILY_ROWS) as client:
            response = client.get("/metrics/report/families/NOPE-FAMILY")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_METRIC_FAMILY_NOT_FOUND"
        )

    def test_5_industry_variants_keep_internal_notice(self):
        with _client(FAMILY_ROWS) as client:
            family = client.get("/metrics/report/families/FIN-INS-022").json()["family"]
        for variant in family["variants"]:
            self.assertEqual(variant["internalNotice"], "内部基线、不外报")
            self.assertFalse(variant["externalEligible"])

    def test_6_family_sql_selects_every_column_the_variant_reads(self):
        """select A / read B 的字段错位会静默把 different 退化为 false（M-03 复盘 bug）。"""
        meta = FakeMetadata(FAMILY_ROWS)
        with TestClient(
            api_module.create_app(SimpleNamespace(metadata=meta), [])
        ) as client:
            payload = client.get("/metrics/report/families").json()
        sql = next(
            stmt for stmt, _ in meta.calls if "WHERE output_mode = 'index'" in stmt
        )
        for column in (
            "denominator_text",
            "denominator_agg",
            "observation_period",
            "window_kind",
            "min_window_days",
            "granularity",
            "grain",
            "formula_text",
            "formula_expr",
            "metric_kind",
            "unit",
        ):
            self.assertRegex(sql, r"\b%s\b" % column)
        # 透出的必须是库里的 denominator_text，而不是 fallback 到 denominator_agg。
        bank036 = payload["families"][0]
        texts = {v["metricId"]: v["denominatorText"] for v in bank036["variants"]}
        self.assertEqual(texts["FIN-BANK-036-v1"], "期初不良资产余额（单位 元）")
        self.assertEqual(
            texts["FIN-BANK-036-v2"], "期内完成处置的不良资产账面金额（有回收方式）"
        )


class CardTests(unittest.TestCase):
    def test_1_main_metric_has_built_card_with_clickable_chain(self):
        with _client(FAMILY_ROWS) as client:
            payload = client.get("/browse/metrics/FIN-BANK-001/card").json()
        self.assertTrue(payload["cardExists"])
        self.assertEqual(payload["cardStateLabel"], "已建卡")
        self.assertTrue(payload["docPath"].endswith("FIN-BANK-001.md"))
        section_keys = [section["key"] for section in payload["sections"]]
        self.assertEqual(
            section_keys,
            ["definition", "formula", "denominator", "window", "grain",
             "evidence", "pipeline", "gap"],
        )
        badge_keys = [badge["key"] for badge in payload["badges"]]
        self.assertEqual(
            badge_keys, ["evidence", "publishable", "external", "computability"]
        )
        self.assertIn("/prov/decisions?metricId=FIN-BANK-001", payload["prov"]["decisionsUrl"])
        self.assertEqual(payload["prov"]["graph"], "urn:platform:prov")
        self.assertIn("/metrics/FIN-BANK-001/output", payload["links"]["output"])
        self.assertIn("运行时可无 PROV", payload["prov"]["decisionLabel"])

    def test_2_variant_without_card_shows_not_built(self):
        with _client(FAMILY_ROWS) as client:
            payload = client.get("/browse/metrics/FIN-BANK-036-v1/card").json()
        self.assertFalse(payload["cardExists"])
        self.assertEqual(payload["cardState"], "not_built")
        self.assertIn("未建卡", payload["cardStateLabel"])
        self.assertIsNone(payload["docPath"])
        self.assertEqual(payload["card"]["variantOf"], "FIN-BANK-036")

    def test_3_industry_card_carries_internal_notice_badge(self):
        with _client(FAMILY_ROWS) as client:
            payload = client.get("/browse/metrics/FIN-BANK-036-v1/card").json()
        evidence_badge = [badge for badge in payload["badges"] if badge["key"] == "evidence"][0]
        self.assertIn("内部基线、不外报", evidence_badge["label"])
        self.assertEqual(evidence_badge["tone"], "warn")
        evidence_section = [s for s in payload["sections"] if s["key"] == "evidence"][0]
        self.assertIn("内部基线、不外报", evidence_section["text"])

    def test_4_prov_decision_badge_reflects_runtime(self):
        with _client(FAMILY_ROWS, prov=FakeProv(count=3)) as client:
            payload = client.get("/browse/metrics/FIN-BANK-001/card").json()
        self.assertEqual(payload["prov"]["decisionCount"], 3)
        self.assertEqual(payload["prov"]["decisionLabel"], "PROV 判定 3 条")
        prov_badge = [badge for badge in payload["badges"] if badge["key"] == "prov"][0]
        self.assertEqual(prov_badge["tone"], "ok")

    def test_5_unknown_metric_card_is_typed_404(self):
        with _client(FAMILY_ROWS) as client:
            response = client.get("/browse/metrics/NOPE-404/card")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["providerCode"], "E_METRIC_NOT_FOUND")


if __name__ == "__main__":
    unittest.main(verbosity=2)
