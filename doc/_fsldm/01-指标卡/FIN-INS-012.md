# FIN-INS-012 · 两年综合成本率（2003）

> 来源档：**evidenced**（provenance_label=原文｜evidence_basis=regulatory）
> publishable：**true**｜inference：**false**｜formula_disabled：false｜domain：insurance
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

旧规口径下连续两年费用率与赔付率之和，用于历史对照。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `两年综合成本率 = 两年费用率 + 两年赔付率（两项均为两年合计口径，*100）` |
| denominator | 两年合计自留保费（扣未到期责任准备金提转差）；单位 元 |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | period（两年滚动，≥730 天） |
| granularity | institution（财险公司） |
| unit | % |

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCED` |
| missing | `无` |
| 台账备注 | Grade B：研究稿可定位监管原文/条款（未与 PDF 逐字核验） |

**证据缺口**：无证据缺口：研究稿可定位监管原文/条款（**未与 PDF 逐字核验**）；`publishable=true`。

## 5. 平台可出数现状

结构性未驱动：`E_METRIC_NOT_DRIVABLE` / `E_METRIC_EVIDENCE_MISSING`（缺四元组或事实字段）

> 本项依据 `_fsldm/02-导入验证/指标可计算性矩阵.md` §3.5 的分层，不重新实测；如后续补事实表或改判证据档，须同步更新本卡与索引。
