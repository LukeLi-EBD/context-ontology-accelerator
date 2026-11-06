# FIN-BANK-006 · 部分还款/最低还款逾期判定〔推测〕

> 来源档：**inferred**（provenance_label=推测｜evidence_basis=none）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：bank
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/09-definitions-v4.seed.json`（v4，2026-11-06）；规则见 `_fsldm/00-口径基准-v4.md` §2。

## 1. 定义

借款人未按合同还足当期应还金额（含信用卡最低还款额）时，按合同口径判定该期是否逾期及逾期起点。

## 2. 公式与分母

| 项 | 内容 |
| --- | --- |
| formula | `若 实还金额 < 当期应还金额（或最低还款额）→ 该期逾期标志=1，起点=应还款日次日；整期逾期口径` |
| denominator | 不适用（判定规则） |

## 3. 观察期 / 粒度 / 单位

| 项 | 内容 |
| --- | --- |
| observationPeriod | point-in-time（应还款日后逐日更新） |
| granularity | account（单笔贷款/信用卡账户） |
| unit | 标志（0/1）与天 |

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
