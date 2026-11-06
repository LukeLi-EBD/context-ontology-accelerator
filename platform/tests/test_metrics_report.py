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
    formula_text="numerator/denominator*100",
    formula_expr="numerator / denominator",
    missing=None,
    inference=False,
    output_mode="value",
    variant_of=None,
    provenance="原文",
    formula_disabled=False,
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
        "metric_kind": "ratio",
        "formula_expr": formula_expr,
        "formula_text": formula_text,
        "numerator_agg": "sum",
        "denominator_agg": "sum",
        "window_kind": "month",
        "min_window_days": 28,
        "observation_period": "period（自然月）",
        "grain": "institution",
        "granularity": "institution",
        "unit": "%",
        "effective_date": "2026-01-01",
        "variant_of": variant_of,
        "output_mode": output_mode,
        "provenance_label": provenance,
        "computability_tier": tier,
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
        return list(self.rows)


def _client(rows=ROWS):
    runtime = SimpleNamespace(metadata=FakeMetadata(rows))
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
