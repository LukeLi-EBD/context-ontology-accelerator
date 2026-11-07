# q_S06 · Context 组装 API

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S06` |
| 分组 | A 核心工作流 S0-S14 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PARTIAL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_S06.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证术语归一 → 子图 → 混合召回 → citations 的上下文包能被组装，且 tokenBudget 生效。

## 2 输入

- `POST /context/resolve  {"query":"青岛监测站位于哪里","tokenBudget":2048}`

## 3 期待输出

HTTP 200；返回 id/taskType/ontologyVersion/graphs/terms/entities/facts/chunks/citations 等层级，且至少部分层级非空。

## 4 真实输出

```
$ POST /context/resolve
  HTTP 200  10904 bytes
  id = pack-3979c221c50e
  taskType = answer
  ontologyVersion = ont-6e81732555e5
  graphs = ["urn:platform:graph:tbox:ont-6e81732555e5", "urn:platform:inferred:ont-6e81732555e5"]
  terms = []
  entities = []
  facts = []
  chunks = [{"docId": "462c7fe6194c9a85b149ecf9b67a4b55504d6b7f63a29a505c66c32c9c3de982", "chunkId": "462c7fe6194c9a85b149ecf9b67a4b55504d6b7f63a29a505c66c32c9c3 ...(截断)
  citations = [{"id": "doc:462c7fe6194c9a85b149ecf9b67a4b55504d6b7f63a29a505c66c32c9c3de982#462c7fe6194c9a85b149ecf9b67a4b55504d6b7f63a29a505c66c32c9c3de982:0000",  ...(截断)
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
