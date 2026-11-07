# q_S11 · T-Box 变更治理与提案/事件

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S11` |
| 分组 | A 核心工作流 S0-S14 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PASS` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_S11.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证版本生命周期、提案、事件、回滚计划四类治理对象可查询。

## 2 输入

- `GET /governance/proposals`
- `GET /ontology/events`
- `GET /health/ontology-diff/flow`

## 3 期待输出

三类端点 200 且返回 items/count；flow 返回 states 列表覆盖 proposal→…→superseded。

## 4 真实输出

```
$ GET /governance/proposals
  HTTP 200  count=15 returned=15 current={"name": "tbox/current", "versionId": "ont-6e81732555e5", "semver": "0.0.0", "contentHash": "9417debca40282e5503d73f1446b98374a14508c7380807f548db54d6 ...(截断)
$ GET /ontology/events
  HTTP 200  count=104
$ GET /health/ontology-diff/flow
  HTTP 200  states=['proposed', 'review', 'approved', 'published', 'draft', 'superseded'] count=39 empty=False
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
