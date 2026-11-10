"""G2 metrics-core: M-01 compute route + M-06 readiness ledger.

Fixtures are written with data_source='fixture' and removed in tearDownClass;
no metric_observation rows are touched. Window/source assertions use dedicated
probe definitions (and a probe fact table) so they do not depend on what other
suites left in the shared fact tables. Values below are hand-computed from the
inserted rows, not copied from any prior run.
"""

from __future__ import annotations

import os
import sys
import unittest
from importlib.resources import files

sys.path.insert(0, "/app/src")

from fastapi.testclient import TestClient

import platform_core.api as api_module
from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.sqlsplit import split_sql_statements

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
AS_OF = "2025-12-31"
Q4 = {"periodStart": "2025-10-01", "periodEnd": "2025-12-31"}
INST = "M01-INST-A"

# Dedicated probe metrics: the window/source assertions must not depend on
# whether other suites left rows (of any data_source) in the global fact tables.
# WINDOW_PROBE reads only this class's institution rows; SOURCE_PROBE reads a
# table owned by this class, so its availableDataSources is deterministic.
WINDOW_PROBE = "TEST-METRIC-PERIOD-WINDOW"
SOURCE_PROBE = "TEST-METRIC-SOURCE-PROBE"
SOURCE_PROBE_TABLE = "platform.qa_datasource_probe"
PROBE_IDS = (WINDOW_PROBE, SOURCE_PROBE)

# account rows: (id, risk_class, principal_balance, start_class, end_class,
#                balance_start, period_decrease_amount)
ACCOUNTS = (
    ("A1", "special", 80, "normal", "special", 100, 20),
    ("A2", "normal", 200, "normal", "normal", 200, 0),
    ("A3", "substandard", 150, "special", "substandard", 150, 0),
    ("A4", "special", 50, "special", "special", 50, 0),
    ("A5", "doubtful", 120, "substandard", "doubtful", 120, 0),
    ("A6", "substandard", 80, "substandard", "substandard", 80, 0),
    ("A7", "loss", 90, "doubtful", "loss", 90, 0),
    ("A8", "doubtful", 60, "doubtful", "doubtful", 60, 0),
    ("A9", "loss", 40, "loss", "loss", 40, 0),
)


# ---------------------------------------------------------------------------
# Definition agg vs binding agg
# ---------------------------------------------------------------------------
# The compiler reads only platform.metric_field_binding.agg; the published
# caliber is metric_definition.numerator_agg/denominator_agg. A divergence is
# tolerated only when it is proven equivalent. Keys are (metric_id, role);
# values are (definition_agg, binding_agg, evidence). "Equivalent" means the
# business caliber matches, with the precondition spelled out in the evidence;
# it is not a license to keep a known-wrong aggregation.
AGG_EQUIVALENT_WHITELIST: dict[tuple[str, str], tuple[str, str, str]] = {
    ("CUST-006", "numerator"): (
        "count_distinct", "sum",
        "定义=明细粒度的客户号去重（retained_customers 列注释：第 N 月仍活跃的 cohort 客户数）；"
        "绑定 sum 作用于已按 cohort 去重的预聚合列。cust_cohort_stat 唯一键 "
        "(cohort_key, as_of, data_source) 保证每 cohort 每快照一行，cohort=获客月分区互不重叠，"
        "故 Σ预聚合去重户数 = 明细去重户数。前提：窗口内同一 cohort 只有一个观察快照"
        "（当前 synthetic 为 1200 cohort / 1 snapshot）。",
    ),
    ("CUST-006", "denominator"): (
        "count_distinct", "sum",
        "同 CUST-006 分子：cohort_customers 列注释=按客户号去重；cohort 分区互不重叠，"
        "Σ预聚合户数 = 明细去重户数（前提同上：窗口内单快照）。",
    ),
    ("CUST-007", "numerator"): (
        "count_distinct", "sum",
        "分子口径=流失户数=cohort_customers−active_customers（列注释：cohort 初始户数、"
        "观察窗口内有效行为户数，均按客户号去重）；两列在预聚合行内相减后 sum，"
        "等价于明细粒度去重流失户数（cohort 分区不重叠，前提同 CUST-006）。",
    ),
    ("CUST-007", "denominator"): (
        "count_distinct", "sum",
        "同 CUST-006 分母：cohort_customers 已按客户号去重，Σ=明细去重初始户数"
        "（前提同 CUST-006）。",
    ),
    ("CUST-008", "numerator"): (
        "count_distinct", "sum",
        "分子=本月且上月也活跃的客户数（active_and_prior_month 列注释）；绑定按 institution "
        "对 cohort 行求和，cohort=获客月分区不重叠，Σ=明细粒度去重户数。",
    ),
    ("CUST-008", "denominator"): (
        "count_distinct", "sum",
        "分母=上月活跃客户数（prior_month_active 列注释：按客户号去重，月末活跃口径）；"
        "按 institution 对 cohort 行求和，cohort 分区不重叠，Σ=明细去重户数。",
    ),
    ("FIN-BANK-025", "numerator"): (
        "sum", "max",
        "bank_concentration_stat 唯一键 (institution, as_of, data_source) + 绑定 instant 等值取 "
        "as_of ⇒ 每机构每快照恰好 1 行 ⇒ SUM(x)=MAX(x)=x；实测 1440 个机构×快照分组，"
        "SUM<>MAX 为 0。max_single_customer_loan 本身已是机构内单一客户最大值。",
    ),
    ("FIN-BANK-026", "numerator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：唯一键保证每机构每快照 1 行，SUM=MAX="
        "max_single_customer_exposure；实测 1440 组无差异。",
    ),
    ("FIN-BANK-026", "denominator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：每机构每快照 1 行，SUM=MAX=tier1_capital_net；"
        "实测 1440 组无差异。",
    ),
    ("FIN-BANK-027", "numerator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：SUM=MAX=max_group_exposure；实测 1440 组无差异。",
    ),
    ("FIN-BANK-027", "denominator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：SUM=MAX=tier1_capital_net；实测 1440 组无差异。",
    ),
    ("FIN-BANK-028", "numerator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：SUM=MAX=max_group_credit；实测 1440 组无差异。",
    ),
    ("FIN-BANK-028", "denominator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：SUM=MAX=capital_net；实测 1440 组无差异。",
    ),
    ("FIN-BANK-029", "numerator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：SUM=MAX=total_related_exposure；实测 1440 组无差异。",
    ),
    ("FIN-BANK-029", "denominator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：SUM=MAX=capital_net；实测 1440 组无差异。",
    ),
    ("FIN-BANK-030", "numerator"): (
        "sum", "max",
        "同 FIN-BANK-025 的 n=1 推演：SUM(GREATEST(...))=MAX(GREATEST(...))；"
        "实测 1440 组无差异。",
    ),
    ("FIN-INS-024", "numerator"): (
        "count_distinct", "sum",
        "定义=按 VIN 去重（renewed_vehicle_count 列注释：到期车辆中实际在本司续保的车辆数）；"
        "绑定 sum 作用于预聚合列。ins_persistence_stat 唯一键 "
        "(institution, product, channel, cohort_period, valuation_basis, renewal_year, data_source) "
        "保证一行=一批 cohort 的车辆数，车辆按 cohort 分区不重叠，Σ=明细去重 VIN 数。",
    ),
    ("FIN-INS-024", "denominator"): (
        "count_distinct", "sum",
        "同 FIN-INS-024 分子：due_vehicle_count 列注释=按车辆/VIN 去重（含脱保车辆）；"
        "cohort 行分区不重叠，Σ=明细去重 VIN 数。",
    ),
    # V41 观测聚合语义分层：definition_agg 是"观测行跨实体合成"口径，binding.agg 是
    # "实体内明细聚合"口径。两者不同层，不是同一聚合被改坏。
    ("FIN-INS-015", "denominator"): (
        "sum", "count_distinct",
        "V41：分母供给端按保单号去重（COUNT(DISTINCT policy_no)）写成预聚合观测值，"
        "观测层跨实体用 SUM；binding 的 count_distinct 是实体内去重，两层组合正确。",
    ),
    ("FIN-INS-016", "denominator"): (
        "sum", "count_distinct",
        "同 FIN-INS-015：分母为保单号去重件数，V41 后观测层声明 sum，"
        "binding 保留实体内 count_distinct；两层组合正确。",
    ),
    ("FIN-INS-018", "numerator"): (
        "sum", "count_distinct",
        "V41：分子为到期车辆/保单去重件数；实体内 count_distinct、观测层跨实体 sum，"
        "两层组合正确。",
    ),
    ("FIN-INS-018", "denominator"): (
        "sum", "count_distinct",
        "同 FIN-INS-018 分子：分母按去重件数采集，V41 观测层声明 sum，"
        "binding 保留实体内 count_distinct；两层组合正确。",
    ),
    ("FIN-INS-025", "denominator"): (
        "sum", "count_distinct",
        "V41 新增 fact function：分母在函数内写 COUNT(DISTINCT policy_no)，"
        "观测层跨渠道用 sum；binding 的 count_distinct 描述函数内的去重，两层组合正确。",
    ),
}

# Divergences judged NOT equivalent. These are definition defects (or missing
# quartet fields), reported for the definition owner; they may not be
# whitelisted. Keys are (metric_id, role); values are
# (definition_agg, binding_agg, impact_and_fix_owner).
AGG_DEFINITION_DEFECTS: dict[tuple[str, str], tuple[str | None, str, str]] = {
    ("CUST-013", "denominator"): (
        "count", "count_distinct",
        "定义文本要求分母=期内自然日天数；count(as_of) 数的是行数（产品大类×快照日），"
        "count_distinct(as_of) 数的是有数据的快照日数，两者都不是自然日数。"
        "影响：产出的是“有快照日的 AUM 均值”而非自然日日均，采样越稀偏离越大，"
        "方向不固定；publishable=false，尚未对外。修法需定义 Owner 先定自然日口径，"
        "不能靠改绑定猜。",
    ),
    ("FIN-INS-017", "denominator"): (
        None, "count_distinct",
        "metric_definition.denominator_agg 为空（quartet 缺项）；denominator_text 要求"
        "按保单号去重并剔除退保/注销，绑定的 count_distinct(policy_no) + "
        "policy_status='in_force' 与文本一致。影响：publishable=true 时对外只能看到"
        "实际取值，看不到分母口径声明；修法是补定义字段，不是改绑定。",
    ),
}


class G2MetricsCoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.client = TestClient(api_module.create_app(cls.runtime, []))
        cls._load()
        cls._seed_probes()

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.meta.tx() as tx:
            for table in ("bank_loan_account", "bank_concentration_stat",
                          "ins_policy", "ins_claim_case"):
                tx.execute(f"DELETE FROM platform.{table} WHERE data_source = 'fixture'", None)
            tx.execute(
                "DELETE FROM platform.metric_field_binding WHERE metric_id = ANY(%s)",
                (list(PROBE_IDS),),
            )
            tx.execute(
                "DELETE FROM platform.metric_definition WHERE metric_id = ANY(%s)",
                (list(PROBE_IDS),),
            )
            tx.execute(f"DROP TABLE IF EXISTS {SOURCE_PROBE_TABLE}", None)
        cls.meta.execute(
            "DELETE FROM platform.source_ref_registry WHERE source_ref LIKE %s OR source_ref LIKE %s",
            (f"%{WINDOW_PROBE}%", f"%{SOURCE_PROBE}%"),
        )
        cls.runtime.close()

    # ------------------------------------------------------------- fixtures
    @classmethod
    def _loan(cls, tx, row) -> None:
        tx.execute(
            "INSERT INTO platform.bank_loan_account (account_id, customer_no, product,"
            " risk_class, principal_balance, account_status, as_of, institution,"
            " period_start, risk_class_start, risk_class_end, balance_start,"
            " balance_end, period_decrease_amount, data_source, fixture)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (row[0], "M01-C-" + row[0], "mortgage", row[1], row[2], "active", AS_OF,
             INST, "2025-01-01", row[3], row[4], row[5], row[2], row[6], "fixture", True),
        )

    @classmethod
    def _load(cls) -> None:
        with cls.meta.tx() as tx:
            for row in ACCOUNTS:
                cls._loan(tx, row)
            for inst, tier1, exposure in (
                (INST, 8000, 120), ("M01-INST-B", 5000, 250),
            ):
                tx.execute(
                    "INSERT INTO platform.bank_concentration_stat (institution, as_of,"
                    " tier1_capital_net, max_single_customer_exposure, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s)",
                    (inst, AS_OF, tier1, exposure, "fixture", True),
                )
            for policy in (
                ("M01-P1", "term_life", "2025-11-10", 1000, 0),
                ("M01-P2", "term_life", "2025-12-20", 2000, 100),
                ("M01-P3", "health", "2025-10-15", 500, 0),
                ("M01-P4", "term_life", "2025-09-15", 3000, 0),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_policy (policy_no, product, channel,"
                    " institution, customer_no, issue_date, premium_type, premium_amount,"
                    " reversal_amount, policy_status, status_as_of, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (policy[0], policy[1], "personal", INST, "M01-C1", policy[2],
                     "regular", policy[3], policy[4], "in_force", AS_OF, "fixture", True),
                )
            for claim in (
                ("M01-K1", "term_life", "2025-11-05", "2025-11-06", "paid", 500),
                ("M01-K2", "term_life", "2025-11-20", None, "rejected", 0),
                ("M01-K3", "term_life", "2025-12-10", "2025-12-11", "paid", 600),
                ("M01-K4", "term_life", "2025-11-01", "2025-11-02", "withdrawn", 0),
                ("M01-K5", "health", "2025-10-05", "2025-10-06", "paid", 400),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_claim_case (claim_no, policy_no, product,"
                    " institution, report_date, filing_date, claim_amount, paid_amount,"
                    " claim_status, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (claim[0], "M01-P1", claim[1], INST, claim[2], claim[3],
                     claim[4] == "paid" and claim[5] or 0, claim[5], claim[4],
                     "fixture", True),
                )

    @classmethod
    def _seed_probes(cls) -> None:
        """Definitions/bindings used by the window and source assertions."""
        with cls.meta.tx() as tx:
            tx.execute(
                "DELETE FROM platform.metric_field_binding WHERE metric_id = ANY(%s)",
                (list(PROBE_IDS),),
            )
            tx.execute(
                "DELETE FROM platform.metric_observation WHERE metric_id = ANY(%s)",
                (list(PROBE_IDS),),
            )
            tx.execute(
                """
                INSERT INTO platform.metric_definition
                  (metric_id, name_zh, domain, evidence_basis, publishable, inference,
                   formula_disabled, missing, evidence_status, note, definition_version,
                   metric_kind, formula_expr, numerator_agg, denominator_agg, window_kind,
                   min_window_days, grain, unit)
                VALUES (%s, '迁徙率窗口测试指标', 'bank', 'regulatory', true, false,
                        false, NULL, 'EVIDENCED', 'test-only', 'v1', 'ratio',
                        'numerator / denominator * 100', 'sum', 'sum', 'period', 0,
                        'institution', '%%')
                ON CONFLICT (metric_id) DO UPDATE SET
                  definition_version = EXCLUDED.definition_version,
                  metric_kind = EXCLUDED.metric_kind,
                  formula_expr = EXCLUDED.formula_expr,
                  numerator_agg = EXCLUDED.numerator_agg,
                  denominator_agg = EXCLUDED.denominator_agg,
                  window_kind = EXCLUDED.window_kind,
                  min_window_days = EXCLUDED.min_window_days,
                  grain = EXCLUDED.grain,
                  unit = EXCLUDED.unit,
                  publishable = EXCLUDED.publishable,
                  formula_disabled = false
                """,
                (WINDOW_PROBE,),
            )
            tx.execute(
                """
                INSERT INTO platform.metric_field_binding
                  (metric_id, definition_version, role, fact_table, entity_column,
                   value_expr, agg, filter_sql, window_column, window_mode)
                VALUES
                  (%s, 'v1', 'numerator', 'platform.bank_loan_account', 'institution',
                   'GREATEST(balance_start - period_decrease_amount, 0)', 'sum',
                   'institution = ''M01-INST-A'' AND risk_class_start = ''normal'' AND '
                   'risk_class_end IN (''special'',''substandard'',''doubtful'',''loss'')',
                   'as_of', 'period'),
                  (%s, 'v1', 'denominator', 'platform.bank_loan_account', 'institution',
                   'GREATEST(balance_start - period_decrease_amount, 0)', 'sum',
                   'institution = ''M01-INST-A'' AND risk_class_start = ''normal''',
                   'as_of', 'period')
                ON CONFLICT (metric_id, definition_version, role) DO UPDATE SET
                  fact_table = EXCLUDED.fact_table,
                  entity_column = EXCLUDED.entity_column,
                  value_expr = EXCLUDED.value_expr,
                  agg = EXCLUDED.agg,
                  filter_sql = EXCLUDED.filter_sql,
                  window_column = EXCLUDED.window_column,
                  window_mode = EXCLUDED.window_mode
                """,
                (WINDOW_PROBE, WINDOW_PROBE),
            )
            tx.execute(
                """
                INSERT INTO platform.metric_definition
                  (metric_id, name_zh, domain, evidence_basis, publishable, inference,
                   formula_disabled, missing, evidence_status, note, definition_version,
                   metric_kind, formula_expr, numerator_agg, denominator_agg, window_kind,
                   min_window_days, grain, unit)
                VALUES (%s, '来源探测测试指标', 'bank', 'regulatory', true, false,
                        false, NULL, 'EVIDENCED', 'test-only', 'v1', 'sum',
                        'numerator', 'sum', NULL, 'period', 0, 'entity', '个')
                ON CONFLICT (metric_id) DO UPDATE SET
                  definition_version = EXCLUDED.definition_version,
                  metric_kind = EXCLUDED.metric_kind,
                  formula_expr = EXCLUDED.formula_expr,
                  numerator_agg = EXCLUDED.numerator_agg,
                  denominator_agg = EXCLUDED.denominator_agg,
                  window_kind = EXCLUDED.window_kind,
                  min_window_days = EXCLUDED.min_window_days,
                  grain = EXCLUDED.grain,
                  unit = EXCLUDED.unit,
                  publishable = EXCLUDED.publishable,
                  formula_disabled = false
                """,
                (SOURCE_PROBE,),
            )
            tx.execute(f"DROP TABLE IF EXISTS {SOURCE_PROBE_TABLE}", None)
            tx.execute(
                f"""
                CREATE TABLE {SOURCE_PROBE_TABLE} (
                  entity_key text NOT NULL,
                  as_of date NOT NULL,
                  numerator numeric NOT NULL,
                  data_source text NOT NULL,
                  fixture boolean NOT NULL DEFAULT true,
                  PRIMARY KEY (entity_key, as_of, data_source)
                )
                """,
                None,
            )
            tx.execute(f"DELETE FROM {SOURCE_PROBE_TABLE}", None)
            tx.execute(
                f"INSERT INTO {SOURCE_PROBE_TABLE}"
                " (entity_key, as_of, numerator, data_source, fixture)"
                " VALUES ('QA-DS-1', '2025-12-31', 1, 'fixture', true)",
                None,
            )
            tx.execute(
                """
                INSERT INTO platform.metric_field_binding
                  (metric_id, definition_version, role, fact_table, entity_column,
                   value_expr, agg, filter_sql, window_column, window_mode)
                VALUES (%s, 'v1', 'numerator', %s, 'entity_key', 'numerator', 'sum',
                        NULL, 'as_of', 'period')
                ON CONFLICT (metric_id, definition_version, role) DO UPDATE SET
                  fact_table = EXCLUDED.fact_table,
                  entity_column = EXCLUDED.entity_column,
                  value_expr = EXCLUDED.value_expr,
                  agg = EXCLUDED.agg,
                  filter_sql = EXCLUDED.filter_sql,
                  window_column = EXCLUDED.window_column,
                  window_mode = EXCLUDED.window_mode
                """,
                (SOURCE_PROBE, SOURCE_PROBE_TABLE),
            )

    # ------------------------------------------------------------- helpers
    def _compute(self, metric_id: str, **params):
        response = self.client.get(f"/metrics/{metric_id}/compute",
                                   params={"dataSource": "fixture", **params})
        return response

    def _rows(self, response) -> dict[str, dict]:
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertGreater(body["rowCount"], 0, body)
        return {str(row["entityKey"]): row for row in body["rows"]}

    # ---------------------------------------------------- M-01 8 selected
    def test_01_npl_ratio(self) -> None:
        # NPL 540 / total 870 = 62.0689655%
        rows = self._rows(self._compute("FIN-BANK-008", asOf=AS_OF))
        self.assertAlmostEqual(rows[INST]["numerator"], 540.0, places=6)
        self.assertAlmostEqual(rows[INST]["denominator"], 870.0, places=6)
        self.assertAlmostEqual(rows[INST]["value"], 62.068966, places=5)

    def test_02_normal_migration(self) -> None:
        # numerator 80 (100 start - 20 decrease); denominator 280 ((100-20)+(200-0))
        rows = self._rows(self._compute("FIN-BANK-013", **Q4))
        self.assertAlmostEqual(rows[INST]["numerator"], 80.0, places=6)
        self.assertAlmostEqual(rows[INST]["denominator"], 280.0, places=6)
        self.assertAlmostEqual(rows[INST]["value"], 28.571429, places=5)

    def test_03_special_migration(self) -> None:
        rows = self._rows(self._compute("FIN-BANK-014", **Q4))
        self.assertAlmostEqual(rows[INST]["value"], 75.0, places=5)

    def test_04_substandard_migration(self) -> None:
        rows = self._rows(self._compute("FIN-BANK-015", **Q4))
        self.assertAlmostEqual(rows[INST]["value"], 60.0, places=5)

    def test_05_doubtful_migration(self) -> None:
        rows = self._rows(self._compute("FIN-BANK-016", **Q4))
        self.assertAlmostEqual(rows[INST]["value"], 60.0, places=5)

    def test_06_concentration(self) -> None:
        # 120/8000=1.5%; 250/5000=5.0%
        rows = self._rows(self._compute("FIN-BANK-026", asOf=AS_OF))
        self.assertAlmostEqual(rows[INST]["value"], 1.5, places=6)
        self.assertAlmostEqual(rows["M01-INST-B"]["value"], 5.0, places=6)

    def test_07_signed_premium(self) -> None:
        rows = self._rows(self._compute("FIN-INS-002", **Q4))
        self.assertAlmostEqual(rows["term_life"]["value"], 2900.0, places=6)
        self.assertAlmostEqual(rows["health"]["value"], 500.0, places=6)

    def test_08_claim_filing_rate(self) -> None:
        # term_life: filed 2 / reported 3 (withdrawn excluded) = 66.666667
        rows = self._rows(self._compute("FIN-INS-018", **Q4))
        self.assertAlmostEqual(rows["term_life"]["numerator"], 2.0, places=6)
        self.assertAlmostEqual(rows["term_life"]["denominator"], 3.0, places=6)
        self.assertAlmostEqual(rows["term_life"]["value"], 66.666667, places=5)

    def test_09_recomputable_after_new_fact(self) -> None:
        first = self._rows(self._compute("FIN-BANK-013", **Q4))[INST]["value"]
        extra = ("A10", "normal", 100, "normal", "special", 100, 0)
        with self.meta.tx() as tx:
            self._loan(tx, extra)
        try:
            second = self._rows(self._compute("FIN-BANK-013", **Q4))[INST]
            # numerator 80+100=180; denominator 280+100=380 -> 47.368421%
            self.assertAlmostEqual(second["numerator"], 180.0, places=6)
            self.assertAlmostEqual(second["value"], 47.368421, places=6)
            self.assertNotAlmostEqual(first, second["value"], places=3)
        finally:
            self.meta.execute(
                "DELETE FROM platform.bank_loan_account WHERE data_source = 'fixture'"
                " AND account_id = 'A10'",
                None,
            )
        restored = self._rows(self._compute("FIN-BANK-013", **Q4))[INST]["value"]
        self.assertAlmostEqual(restored, first, places=6)

    # -------------------------------------------------------- explicit errors
    def test_10_non_executable_has_code_and_reason(self) -> None:
        response = self._compute("FIN-BANK-019", asOf=AS_OF)
        self.assertEqual(response.status_code, 400, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_METRIC_NOT_STRUCTURALLY_COMPUTABLE")
        self.assertIn("quartet incomplete", error["message"])
        self.assertEqual(error["details"]["metricId"], "FIN-BANK-019")

    def test_11_rule_set_routes_to_rules(self) -> None:
        response = self._compute("FIN-BANK-034", asOf=AS_OF)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_METRIC_RULE_SET_ONLY"
        )

    def test_12_missing_binding(self) -> None:
        response = self._compute("FIN-BANK-001", asOf=AS_OF, internal="true")
        self.assertEqual(response.status_code, 400, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_METRIC_BINDING_MISSING")
        self.assertIn("numerator", error["message"])

    def test_13_not_publishable_gate(self) -> None:
        response = self._compute("CUST-001", asOf=AS_OF)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_METRIC_NOT_PUBLISHABLE"
        )

    def test_14_unknown_metric(self) -> None:
        response = self._compute("NO-SUCH-METRIC", asOf=AS_OF)
        # MetricCompiler maps every lookup failure to InvalidArgument (400);
        # the stable discriminator is the provider code, not the HTTP status.
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["error"]["providerCode"], "E_METRIC_NOT_FOUND")

    def test_15_period_window_insufficient(self) -> None:
        response = self._compute(
            "FIN-INS-013",
            periodStart="2025-12-01",
            periodEnd="2025-12-31",
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_METRIC_WINDOW_INSUFFICIENT"
        )

    # ------------------------------------------------------------ M-06 ledger
    def test_16_readiness_ledger(self) -> None:
        response = self.client.get("/metrics-readiness")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["count"], 20)
        self.assertEqual(body["counts"]["executed"], 16)
        self.assertEqual(body["counts"]["registered_only"], 1)
        self.assertEqual(body["counts"]["not_executable"], 3)
        by_id = {(item["itemKind"], item["metricId"]): item for item in body["items"]}
        self.assertEqual(by_id[("partial", "CUST-005")]["status"], "registered_only")
        self.assertEqual(by_id[("partial", "FIN-BANK-019")]["status"], "not_executable")
        self.assertEqual(by_id[("rule", "FIN-BANK-007")]["detail"]["ruleCount"], 4)

    def test_17_registered_only_export(self) -> None:
        response = self.client.get(
            "/metrics-readiness", params={"status": "registered_only", "format": "csv"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("text/csv", response.headers["content-type"])
        lines = [line for line in response.text.splitlines() if line]
        self.assertEqual(len(lines), 2)  # header + CUST-005 only
        self.assertTrue(lines[0].startswith("item_kind,metric_id,status"))
        self.assertIn("CUST-005", lines[1])
        self.assertIn("registered_only", lines[1])
        self.assertNotIn("executed", response.text)

    def test_18_readiness_invalid_status(self) -> None:
        response = self.client.get(
            "/metrics-readiness", params={"status": "partial"}
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(
            response.json()["error"]["providerCode"],
            "E_METRIC_READINESS_STATUS_INVALID",
        )

    def test_19_v34_reentrant(self) -> None:
        sql = files("coa_control_plane.platform_db").joinpath(
            "migrations/V34__metrics_core_m01_m06.sql"
        ).read_text(encoding="utf-8")
        statements = split_sql_statements(sql)

        def snapshot() -> tuple:
            rows = self.meta.query(
                "SELECT item_kind, metric_id, status, reason, detail::text AS detail,"
                " evidence_ref, checked_at FROM platform.metric_readiness"
                " ORDER BY item_kind, metric_id"
            )
            bindings = self.meta.query(
                "SELECT metric_id, role, value_expr, filter_sql, window_column"
                " FROM platform.metric_field_binding"
                " WHERE metric_id IN ('FIN-BANK-013','FIN-BANK-014','FIN-BANK-015',"
                "'FIN-BANK-016','FIN-INS-018') ORDER BY metric_id, role"
            )
            return (tuple(tuple(sorted(r.items())) for r in rows),
                    tuple(tuple(sorted(r.items())) for r in bindings))

        before = snapshot()
        for _ in range(2):
            with self.meta.tx() as tx:
                for statement in statements:
                    tx.execute(statement, None)
        self.assertEqual(snapshot(), before)

    # --------------------------------------------------- anti-rewind guard
    def _assert_bindings_match_registry(self) -> None:
        from platform_core.metric_binding_overrides import BINDING_OVERRIDES

        metric_ids = sorted({item["metric_id"] for item in BINDING_OVERRIDES})
        rows = self.meta.query(
            "SELECT metric_id, definition_version, role, value_expr, filter_sql,"
            " window_column, window_mode FROM platform.metric_field_binding"
            " WHERE metric_id = ANY(%s)",
            (metric_ids,),
        )
        by_key = {(r["metric_id"], r["definition_version"], r["role"]): r for r in rows}
        for item in BINDING_OVERRIDES:
            key = (item["metric_id"], item["definition_version"], item["role"])
            self.assertIn(key, by_key)
            row = by_key[key]
            for field in ("value_expr", "filter_sql", "window_column", "window_mode"):
                if item.get(field) is not None:
                    self.assertEqual(row[field], item[field], f"{key} {field}")

    def test_20_migrate_repairs_rewound_binding(self) -> None:
        # Simulate a legacy seed replay (V25 ON CONFLICT DO UPDATE) writing the
        # pre-V34 values; migrate() must restore the published registry.
        with self.meta.tx() as tx:
            tx.execute(
                "UPDATE platform.metric_field_binding SET value_expr = 'balance_start'"
                " WHERE metric_id = 'FIN-BANK-013' AND role = 'numerator'",
                None,
            )
            tx.execute(
                "UPDATE platform.metric_field_binding"
                " SET window_column = 'filing_date', filter_sql = 'claim_status <> ''withdrawn'''"
                " WHERE metric_id = 'FIN-INS-018' AND role = 'numerator'",
                None,
            )
            tx.execute(
                "UPDATE platform.metric_field_binding SET window_mode = 'instant'"
                " WHERE metric_id = 'CUST-006' AND role = 'numerator'",
                None,
            )
        rewound = self.meta.query(
            "SELECT value_expr FROM platform.metric_field_binding"
            " WHERE metric_id = 'FIN-BANK-013' AND role = 'numerator'"
        )[0]["value_expr"]
        self.assertEqual(rewound, "balance_start")

        self.meta.migrate()  # no new version -> registry replay still runs
        self._assert_bindings_match_registry()

    def test_21_seed_source_matches_registry(self) -> None:
        # The seed statement itself must already carry the correction, so a raw
        # V25 binding replay (without migrate) cannot rewind anything. Only the
        # binding INSERT is replayed: the rest of V25 belongs to older rulings.
        sql = files("coa_control_plane.platform_db").joinpath(
            "migrations/V25__fact_model_v7.sql"
        ).read_text(encoding="utf-8")
        binding_inserts = [
            statement
            for statement in split_sql_statements(sql)
            if "INSERT INTO platform.metric_field_binding" in statement
        ]
        self.assertTrue(binding_inserts)
        with self.meta.tx() as tx:
            for statement in binding_inserts:
                tx.execute(statement, None)
        self._assert_bindings_match_registry()

    # ------------------------------------------------- period window + source
    def test_22_period_window_takes_effect(self) -> None:
        # The probe is defined as period and reads only this class's institution
        # rows. With a period request the compiler must use [periodStart, periodEnd],
        # not collapse the window onto periodStart.
        period = self._compute(WINDOW_PROBE, **Q4)
        self.assertEqual(period.status_code, 200, period.text)
        body = period.json()
        self.assertEqual(body["window"], {"start": Q4["periodStart"],
                                          "end": Q4["periodEnd"]})
        self.assertEqual(body["rowCount"], 1, body)
        row = body["rows"][0]
        self.assertAlmostEqual(row["numerator"], 80.0, places=6)
        self.assertAlmostEqual(row["denominator"], 280.0, places=6)
        self.assertAlmostEqual(row["value"], 28.571429, places=5)

        # A period value is a range, never a point: asOf alone must be refused
        # with the same code as /output, not collapsed into a one-day window.
        degenerate = self._compute(WINDOW_PROBE, asOf=AS_OF)
        self.assertEqual(degenerate.status_code, 400, degenerate.text)
        error = degenerate.json()["error"]
        self.assertEqual(error["providerCode"], "E_METRIC_WINDOW_INSUFFICIENT")
        self.assertEqual(error["message"], "period metric requires a full window")

        single_day = self._compute(WINDOW_PROBE, periodStart=AS_OF, periodEnd=AS_OF)
        self.assertEqual(single_day.status_code, 400, single_day.text)
        self.assertEqual(
            single_day.json()["error"]["providerCode"],
            "E_METRIC_WINDOW_INSUFFICIENT",
        )

        # A period that excludes the probe's snapshot really returns nothing;
        # the window is applied instead of silently using the period start.
        empty = self._compute(WINDOW_PROBE, periodStart="2025-01-01",
                              periodEnd="2025-06-30").json()
        self.assertTrue(empty["noData"])
        self.assertEqual(empty["rowCount"], 0)
        self.assertEqual(empty["window"],
                         {"start": "2025-01-01", "end": "2025-06-30"})
        self.assertNotIn("reason", empty)

    def test_23_definition_binding_agg_consistency(self) -> None:
        # The compiler reads only the binding agg, so every divergence between
        # the published definition and the binding must be either proven
        # equivalent (whitelist) or a recorded definition defect. A divergence
        # outside both lists fails; a non-equivalent entry may not be whitelisted.
        rows = self.meta.query(
            "SELECT d.metric_id, b.role, d.numerator_agg, d.denominator_agg,"
            " b.agg FROM platform.metric_definition d"
            " JOIN platform.metric_field_binding b"
            "   ON b.metric_id = d.metric_id"
            "  AND b.definition_version = d.definition_version"
            " WHERE b.role IN ('numerator','denominator')"
            "   AND ((b.role = 'numerator'"
            "         AND COALESCE(d.numerator_agg,'') <> COALESCE(b.agg,''))"
            "        OR (b.role = 'denominator'"
            "         AND COALESCE(d.denominator_agg,'') <> COALESCE(b.agg,'')))"
        )
        observed = {
            (r["metric_id"], r["role"]): (
                r["numerator_agg"] if r["role"] == "numerator" else r["denominator_agg"],
                r["agg"],
            )
            for r in rows
        }
        allowed = {k: (v[0], v[1]) for k, v in AGG_EQUIVALENT_WHITELIST.items()}
        defects = {k: (v[0], v[1]) for k, v in AGG_DEFINITION_DEFECTS.items()}
        self.assertEqual(observed, {**allowed, **defects},
                         f"definition/binding agg divergence changed: {sorted(observed)}")
        self.assertEqual(len(observed), 25)
        self.assertEqual(len({m for m, _ in observed}), 16)
        self.assertTrue(set(allowed).isdisjoint(defects),
                        "whitelist and defect list must be disjoint")
        for key, (def_agg, bind_agg, evidence) in AGG_EQUIVALENT_WHITELIST.items():
            self.assertTrue(evidence.strip(), f"whitelist entry {key} has no evidence")
            self.assertNotEqual(def_agg, bind_agg, f"whitelist entry {key} is not a divergence")
        for key, (def_agg, bind_agg, impact) in AGG_DEFINITION_DEFECTS.items():
            self.assertTrue(impact.strip(), f"defect entry {key} has no impact note")
            self.assertNotIn(key, AGG_EQUIVALENT_WHITELIST,
                             f"non-equivalent divergence {key} must not be whitelisted")

    def test_24_datasource_mismatch_is_explicit(self) -> None:
        # A source that does not exist in the fact table is reported, not
        # silently returned as an empty result. The probe is bound to a table
        # this class owns and fills with fixture rows only.
        response = self._compute(SOURCE_PROBE, **Q4, dataSource="business")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["noData"])
        self.assertEqual(body["reason"], "E_METRIC_DATASOURCE_MISMATCH")
        self.assertEqual(body["requestedDataSource"], "business")
        self.assertIn("fixture", body["availableDataSources"])
        self.assertNotIn("business", body["availableDataSources"])

        # There is no implicit default: omitting dataSource is refused, and the
        # error names the enumeration instead of silently reading fixture.
        missing = self.client.get("/metrics/FIN-BANK-013/compute",
                                  params={"periodStart": Q4["periodStart"],
                                          "periodEnd": Q4["periodEnd"]})
        self.assertEqual(missing.status_code, 400, missing.text)
        error = missing.json()["error"]
        self.assertEqual(error["providerCode"], "E_METRIC_DATA_SOURCE_REQUIRED")
        self.assertEqual(
            error["details"]["allowedDataSources"],
            ["fixture", "business", "synthetic"],
        )

    def test_25_no_period_metric_has_instant_bindings(self) -> None:
        # Guard the whole definition set, not just 013-018: a period metric
        # whose bindings are instant silently collapses the window. The only
        # intentional mix is FIN-INS-017's snapshot denominator (period-end
        # policy count), so everything else must be period.
        rows = self.meta.query(
            "SELECT d.metric_id, b.role FROM platform.metric_definition d"
            " JOIN platform.metric_field_binding b"
            "   ON b.metric_id = d.metric_id"
            "  AND b.definition_version = d.definition_version"
            " WHERE d.window_kind = 'period' AND b.window_mode = 'instant'"
        )
        observed = {(r["metric_id"], r["role"]) for r in rows}
        self.assertEqual(observed, {("FIN-INS-017", "denominator")})


if __name__ == "__main__":
    unittest.main()
