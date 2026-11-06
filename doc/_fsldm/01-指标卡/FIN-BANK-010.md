# FIN-BANK-010 · 重组贷款（现行）

> 来源档：**evidenced**（provenance_label=原文｜evidence_basis=regulatory）
> publishable：**true**｜inference：**false**｜formula_disabled：false｜domain：bank
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

因债务人财务困难而作出有利于债务人的合同调整或提供再融资所形成的资产，观察期至少 1 年且不少于连续 2 个还款期。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `重组标志 = 财务困难 ∧ 合同调整；观察期 = max(1 年, 连续 2 个还款期)；重组后分类下限：原正常/关注→至少关注，再次重组→至少次级；规则型` |
| denominator | 不适用（判定规则） |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | period（观察期 ≥ 365 天且 ≥ 连续 2 个还款期，自调整后首次还款日起算） |
| granularity | agreement（单笔协议） |
| unit | 标志/档 |

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
