# FIN-INS-017 · 报案率〔行业〕

> 来源档：**industry**（provenance_label=行业通行｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：insurance
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

统计期内报案件数占有效保单件数的比例，反映出险报案频度。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `numerator / denominator * 100` |
| denominator | 有效保单件数（同期时点或期间平均，按保单号去重，剔除注销/退保）；单位 件 |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | period（统计期，月度/年度） |
| granularity | product（险种）/ institution |
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
