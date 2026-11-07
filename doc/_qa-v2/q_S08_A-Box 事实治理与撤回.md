# q_S08 · A-Box 事实治理与撤回

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S08` |
| 分组 | A 核心工作流 S0-S14 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PARTIAL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_S08.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证事实断言表、冲突列表、按来源撤回所需的数据结构可读。

## 2 输入

- `GET /facts`
- `GET /facts/conflicts`
- `SQL: fact_assertion / fact_event 计数`

## 3 期待输出

fact_assertion 应有当前生效断言；/facts 返回 items 与 state；冲突端点返回 pending 计数。

## 4 真实输出

```
$ GET /facts
  HTTP 200  state=active count=0 items=[]
$ GET /facts/conflicts
  HTTP 200  count=0 pending=0
$ SQL select 'fact_assertion',count(*) from platform.fact_assertion union all select 'fact_event ...(截断)
fact_assertion|0
fact_event|97
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
