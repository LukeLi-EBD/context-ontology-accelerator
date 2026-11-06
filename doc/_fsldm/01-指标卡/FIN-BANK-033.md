# FIN-BANK-033 · 首逾率（FPD）〔行业〕

> 来源档：**industry**（provenance_label=行业通行｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：bank
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

新发放贷款在首个还款期即发生逾期的账户占比，用于早期风险识别（固定采用账户口径变体 A）。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `numerator / denominator * 100（变体 A：分子=首期应还且首个还款期逾期的账户数；分母=同期首期应还账户数）` |
| denominator | 同期首期应还账户数（按账户去重，不含未到首个还款期的账户）；单位 户 |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | period（按放款月形成 vintage，观察至首个还款期后 30 天） |
| granularity | account（放款批次/vintage） |
| unit | % |

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCE_MISSING` |
| missing | `regulatory_source` |
| 台账备注 | 台账“部分”：仅行业公式或原文存疑；允许内部出数，须标 source=INDUSTRY + inference=true |

**证据缺口**：缺监管原文（`missing=regulatory_source`）；仅有行业通行公式，`publishable=false`，不得对外出数；内部出数须标 `source=INDUSTRY` + `inference=true`。

## 5. 平台可出数现状

不可出数：`E_METRIC_NOT_PUBLISHABLE`

> 本项依据 `_fsldm/02-导入验证/指标可计算性矩阵.md` §3.5 的分层，不重新实测；如后续补事实表或改判证据档，须同步更新本卡与索引。
