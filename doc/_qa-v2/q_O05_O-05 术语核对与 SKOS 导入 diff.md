# q_O05 · O-05 术语核对与 SKOS 导入 diff

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_O05` |
| 分组 | B 本轮特性 O 本体治理 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `FAIL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_O05.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 85 概念 / 18 别名已进当前 T-Box，并有覆盖率/冲突报告与核对记录。

## 2 输入

- `GET /ontology/terms/coverage`
- `GET /ontology/terms/checks`
- `GET /browse/terms`
- `SPARQL: 按命名图统计 skos:Concept 数`

## 3 期待输出

按判据：expected 85 概念/18 别名，actual 应接近且 complete=true；checks 有核对记录；词表在当前 T-Box 指针指向的图里。

## 4 真实输出

```
$ GET /ontology/terms/coverage
  HTTP 200  expected={"concepts": 85, "aliases": 18, "baselineSource": "doc/_design/50-指标 SKOS 词表-v1.md（85 概念）+ doc/_design/52-后续路线图-v1.md（18 别名）", "note": "基线来自设计文档；可用 expectConcepts/expectAliases 覆盖，不是推算值"}
  actual.concepts=85 actual.aliases=0 complete=False missingConcepts=0
  graph=urn:platform:graph:tbox:ont-6e81732555e5
$ GET /ontology/terms/checks
  HTTP 200  count=0 empty=True emptyReason=尚无术语核对记录
$ GET /browse/terms
  HTTP 200  entries=0 classes=[]
$ SPARQL SELECT ?g (COUNT(DISTINCT ?c) AS ?n) WHERE { GRAPH ?g { ?c a <http://www.w3.org/ ...(截断)
  [{"g": {"type": "uri", "value": "urn:platform:graph:tbox:ont-6e81732555e5"}, "n": {"type": "literal", "value": "180", "datatype": "http://www.w3.org/2001/XMLSchema#integer"}}]
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
