"""Single authoritative source for published metric binding corrections.

Migrations such as V25 seed bindings with ``ON CONFLICT ... DO UPDATE``. Replaying
them (datagen reseed, migration reentrancy tests, integration ordering) would
silently rewind corrections that were applied by a later migration. To make
rewinds impossible, every published correction is registered here and
``MetadataPg.migrate`` replays this registry after each migration run, including
no-op runs.

Adding a future V3x binding correction:
1. add the corrected row(s) to ``BINDING_OVERRIDES``;
2. add the same correction to the V3x migration (for DBs that migrate forward);
3. the regression test ``test_20`` asserts DB == registry after a forced rewind.

Only fields present in the override are written; ``None`` means "keep current".
"""

from __future__ import annotations

from typing import Any

BINDING_OVERRIDES: tuple[dict[str, Any], ...] = (
    {
        "metric_id": "FIN-BANK-013",
        "definition_version": "v3.0",
        "role": "numerator",
        "value_expr": "GREATEST(balance_start - period_decrease_amount, 0)",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-013",
        "definition_version": "v3.0",
        "role": "denominator",
        "value_expr": "GREATEST(balance_start - period_decrease_amount, 0)",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-014",
        "definition_version": "v3.0",
        "role": "numerator",
        "value_expr": "GREATEST(balance_start - period_decrease_amount, 0)",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-014",
        "definition_version": "v3.0",
        "role": "denominator",
        "value_expr": "GREATEST(balance_start - period_decrease_amount, 0)",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-015",
        "definition_version": "v3.0",
        "role": "numerator",
        "value_expr": "GREATEST(balance_start - period_decrease_amount, 0)",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-015",
        "definition_version": "v3.0",
        "role": "denominator",
        "value_expr": "GREATEST(balance_start - period_decrease_amount, 0)",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-016",
        "definition_version": "v3.0",
        "role": "numerator",
        "value_expr": "GREATEST(balance_start - period_decrease_amount, 0)",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-016",
        "definition_version": "v3.0",
        "role": "denominator",
        "value_expr": "GREATEST(balance_start - period_decrease_amount, 0)",
        "window_mode": "period",
    },
    # FIN-BANK-017/018 与 CUST-006/007/008 的定义是 period，但 V25 种子把两条绑定
    # 都写成了 instant：周期请求会被编译器当成 as_of，窗口退化成一个点。这里只改
    # window_mode，不动任何公式与聚合口径。
    {
        "metric_id": "FIN-BANK-017",
        "definition_version": "v3.0",
        "role": "numerator",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-017",
        "definition_version": "v3.0",
        "role": "denominator",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-018",
        "definition_version": "v3.0",
        "role": "numerator",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-BANK-018",
        "definition_version": "v3.0",
        "role": "denominator",
        "window_mode": "period",
    },
    {
        "metric_id": "CUST-006",
        "definition_version": "v3.0",
        "role": "numerator",
        "window_mode": "period",
    },
    {
        "metric_id": "CUST-006",
        "definition_version": "v3.0",
        "role": "denominator",
        "window_mode": "period",
    },
    {
        "metric_id": "CUST-007",
        "definition_version": "v3.0",
        "role": "numerator",
        "window_mode": "period",
    },
    {
        "metric_id": "CUST-007",
        "definition_version": "v3.0",
        "role": "denominator",
        "window_mode": "period",
    },
    {
        "metric_id": "CUST-008",
        "definition_version": "v3.0",
        "role": "numerator",
        "window_mode": "period",
    },
    {
        "metric_id": "CUST-008",
        "definition_version": "v3.0",
        "role": "denominator",
        "window_mode": "period",
    },
    {
        "metric_id": "FIN-INS-018",
        "definition_version": "v3.0",
        "role": "numerator",
        "value_expr": "claim_no",
        "filter_sql": "claim_status <> 'withdrawn' AND filing_date IS NOT NULL",
        "window_column": "report_date",
    },
)

_REPLAY_SQL = """UPDATE platform.metric_field_binding AS b
SET value_expr = COALESCE(v.value_expr, b.value_expr),
    filter_sql = COALESCE(v.filter_sql, b.filter_sql),
    window_column = COALESCE(v.window_column, b.window_column),
    window_mode = COALESCE(v.window_mode, b.window_mode)
FROM (VALUES %s) AS v(metric_id, definition_version, role, value_expr,
                      filter_sql, window_column, window_mode)
WHERE b.metric_id = v.metric_id
  AND b.definition_version = v.definition_version
  AND b.role = v.role"""


def replay_binding_overrides(conn: Any) -> None:
    """Reapply the registry through an open psycopg connection."""

    if not BINDING_OVERRIDES:
        return
    rows = [
        (
            item["metric_id"],
            item["definition_version"],
            item["role"],
            item.get("value_expr"),
            item.get("filter_sql"),
            item.get("window_column"),
            item.get("window_mode"),
        )
        for item in BINDING_OVERRIDES
    ]
    placeholders = ", ".join(["(%s, %s, %s, %s, %s, %s, %s)"] * len(rows))
    params: list[Any] = [value for row in rows for value in row]
    conn.execute(_REPLAY_SQL % placeholders, params)
