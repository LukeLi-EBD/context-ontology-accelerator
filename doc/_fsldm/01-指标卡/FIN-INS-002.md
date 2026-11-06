# FIN-INS-002 · 签单保费

> 来源档：**evidenced**（provenance_label=原文｜evidence_basis=regulatory）
> publishable：**true**｜inference：**false**｜formula_disabled：false｜domain：insurance
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

统计期内销售的保单保费总额，按销售/承保时点归集，批改按批单调整。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `numerator = Σ统计期内销售保单保费总额（含已起保与未起保；批增/批减调整；退保不冲减）` |
| denominator | 不适用（可加总指标） |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | period（统计期，按销售/承保时点归集） |
| granularity | product（险种）/ channel（渠道） |
| unit | 元 |

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCED` |
| missing | `无` |
| 台账备注 | Grade A：研究稿可定位监管原文/条款（未与 PDF 逐字核验） |

**证据缺口**：无证据缺口：研究稿可定位监管原文/条款（**未与 PDF 逐字核验**）；`publishable=true`。

## 5. 平台可出数现状

结构性未驱动：`E_METRIC_NOT_DRIVABLE` / `E_METRIC_EVIDENCE_MISSING`（缺四元组或事实字段）

> 本项依据 `_fsldm/02-导入验证/指标可计算性矩阵.md` §3.5 的分层，不重新实测；如后续补事实表或改判证据档，须同步更新本卡与索引。
