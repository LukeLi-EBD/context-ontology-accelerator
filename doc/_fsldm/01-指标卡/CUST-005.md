# CUST-005 · RFM-R（无交易代理口径）〔推测〕

> 来源档：**inferred**（provenance_label=推测｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：customer
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

对无有效交易客户，用注册/开卡/首单/保单生效日作为代理最近行为日计算 R，并单独标记未激活。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `numerator = max(基准日 − 代理事件日, 0)；无任何代理事件则 R=NULL（不置 0，不参与分档）` |
| denominator | 不适用（非比率） |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | point-in-time（月末基准日） |
| granularity | customer（无交易客户单独标记） |
| unit | 天 |

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCE_MISSING` |
| missing | `regulatory_source` |
| 台账备注 | 台账“部分”：仅行业公式或原文存疑；允许内部出数，须标 source=INDUSTRY + inference=true |

**证据缺口**：无原文也无成文行业公式，仅有 industry 背景；`publishable=false`，不得出数。

## 5. 平台可出数现状

不可出数：`E_METRIC_NOT_PUBLISHABLE`

> 本项依据 `_fsldm/02-导入验证/指标可计算性矩阵.md` §3.5 的分层，不重新实测；如后续补事实表或改判证据档，须同步更新本卡与索引。
