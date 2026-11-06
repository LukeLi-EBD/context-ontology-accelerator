# CUST-011 · 钱包份额（SOW）〔行业〕

> 来源档：**industry**（provenance_label=行业通行｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：customer
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

本公司在该客户某品类获得的业务额占该客户该品类总消费的比例。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `numerator / denominator * 100` |
| denominator | 客户在该品类的总消费/总资产（外部数据或模型估算，同期、同币种）；单位 元 |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | period（年度/滚动 12 个月，与时点变体分开） |
| granularity | customer × category |
| unit | % |

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `INDUSTRY_ONLY` |
| missing | `regulatory_source` |
| 台账备注 | Grade C：学术/厂商/行业资料，非监管原文；仅内部出数 |

**证据缺口**：缺监管原文（`missing=regulatory_source`）；仅有行业通行公式，`publishable=false`，不得对外出数；内部出数须标 `source=INDUSTRY` + `inference=true`。

## 5. 平台可出数现状

不可出数：`E_METRIC_NOT_PUBLISHABLE`

> 本项依据 `_fsldm/02-导入验证/指标可计算性矩阵.md` §3.5 的分层，不重新实测；如后续补事实表或改判证据档，须同步更新本卡与索引。
