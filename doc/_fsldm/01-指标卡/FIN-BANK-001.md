# FIN-BANK-001 · 逾期天数（DPD）

> 来源档：**evidenced**（provenance_label=原文｜evidence_basis=regulatory）
> publishable：**true**｜inference：**false**｜formula_disabled：false｜domain：bank
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

贷款合同到期（含批准展期后到期）未归还时，自到期日次日起至观察日累计的自然日天数。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `numerator = max(观察日 − 应还款日, 0)` |
| denominator | 不适用（非比率；分子为天数） |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | point-in-time（观察日；窗长 0） |
| granularity | agreement（单笔贷款协议） |
| unit | 天 |

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCED` |
| missing | `无` |
| 台账备注 | Grade A：研究稿可定位监管原文/条款（未与 PDF 逐字核验） |

**证据缺口**：无证据缺口：研究稿可定位监管原文/条款（**未与 PDF 逐字核验**）；`publishable=true`。

## 5. 平台可出数现状

可出数（四元组齐全 + 可发布；矩阵 §3.5）

> 本项依据 `_fsldm/02-导入验证/指标可计算性矩阵.md` §3.5 的分层，不重新实测；如后续补事实表或改判证据档，须同步更新本卡与索引。
