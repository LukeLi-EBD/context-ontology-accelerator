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


if __name__ == "__main__":
    unittest.main(verbosity=2)
