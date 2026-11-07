# q_S03 · 混合检索与 RRF 融合

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S03` |
| 分组 | A 核心工作流 S0-S14 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PASS` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_S03.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 pgvector + FTS 双路召回、RRF(k=60) 融合，且非降级模式。

## 2 输入

- `GET /search?q=青岛&limit=3`
- `GET /ui/api/search?q=青岛&limit=3`

## 3 期待输出

HTTP 200；mode=hybrid、rrfK=60、routes 含 vector 与 lexical、degraded=false、results 非空且每条带 chunkId 与 citation。

## 4 真实输出

```
$ GET /search?q=%E9%9D%92%E5%B2%9B&limit=3
  HTTP 200  mode=hybrid rrfK=60 routes=['vector', 'lexical'] degraded=False reasons=[]
  results=3  first={"chunkId": "d51a0f411b3f3bcbeef43564e5e4544a95283b3f6e3fe18c9ff88f5893df2ab2:0000", "documentId": "d51a0f411b3f3bcbeef43564e5e4544a95283b3f6e3fe18c9ff88f5893df2ab2", "pageFrom": 1, "pageTo": 1, "text": "海岸带监测周报3e9ff5ac。本周完成了潮间带沉积 ...(截断)
$ GET /ui/api/search?q=%E9%9D%92%E5%B2%9B&limit=3
  HTTP 200  {"id":"pack-b857239572c2","taskType":"answer","ontologyVersion":"ont-6e81732555e5","graphs":["urn:platform:graph:tbox:ont-6e81732555e5","urn:platform:inferred:ont-6e81732555e5"],"terms":[],"entities":[],"facts":[],"chunk ...(截断)
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
