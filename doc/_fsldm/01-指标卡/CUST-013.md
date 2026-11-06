# CUST-013 · AUM（日均）〔行业〕

> 来源档：**industry**（provenance_label=行业通行｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：customer
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

观察期内客户每日 AUM 的平均值，用于平滑时点波动。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `AUM_日均 = Σ期内每日 AUM / 期内天数` |
| denominator | 期内天数（自然日，同一期间）；单位 天 |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | period（月/季/年日均，≥30 天） |
| granularity | customer × product type |
| unit | 元 |

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
