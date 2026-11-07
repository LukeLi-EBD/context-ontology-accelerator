# q_O02 · O-02 T-Box 提案/审批/supersede 状态机

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_O02` |
| 分组 | B 本轮特性 O 本体治理 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PARTIAL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_O02.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证状态迁移有 actor/reason/time 留痕，非法迁移被拒（只读侧检查已记录的状态流）。

## 2 输入

- `GET /health/ontology-diff/flow`
- `GET /governance/events`
- `SQL: SELECT count(*) FROM platform.ontology_event`

## 3 期待输出

flow.states 覆盖 proposal→review→approved→published→superseded；事件表非空且含 actor/reason/time 语义列。

## 4 真实输出

```
$ GET /health/ontology-diff/flow
  HTTP 200  states=['proposed', 'review', 'approved', 'published', 'draft', 'superseded'] count=39 empty=False emptyReason=None
$ GET /governance/events
  HTTP 200  count=104 categories={"published": 14, "rolled_back": 3, "superseded": 18, "other": 69}
$ SQL select count(*) from platform.ontology_event
  ontology_event 行数 = 104
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
