# FIN-BANK-020 · 迁徙率（户数口径变体）〔推测〕

> 来源档：**inferred**（provenance_label=推测｜evidence_basis=none）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：bank
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

以户数而非余额计算的迁徙率变体，仅用于内部风控观察；监管口径为余额法。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `numerator / denominator * 100` |
| denominator | 期初该分类户数（按客户号去重，不按账户去重）；单位 户 |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | period（报告期，季度） |
| granularity | customer/account（户数口径） |
| unit | % |

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `NO_SOURCE` |
| missing | `source` |
| 台账备注 | 台账 no-source：无监管原文且无成文行业公式；不出数；v4 以推测口径补公式，仍不出数 |

**证据缺口**：无成文来源（`missing=source`）；v4 按实务常识推测补写公式，`publishable=false`，不得出数。

## 5. 平台可出数现状

不可出数：`E_METRIC_NOT_PUBLISHABLE`

> 本项依据 `_fsldm/02-导入验证/指标可计算性矩阵.md` §3.5 的分层，不重新实测；如后续补事实表或改判证据档，须同步更新本卡与索引。
