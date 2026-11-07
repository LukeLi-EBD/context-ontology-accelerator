# q_O06 · O-06 健康与 diff 类/属性级汇总

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_O06` |
| 分组 | B 本轮特性 O 本体治理 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PASS` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_O06.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 diff 能按类/属性聚合、支持两版本对比、空态明确。

## 2 输入

- `GET /health/ontology-diff`
- `GET /health/ontology-diff/flow`
- `GET /health/ontology-snapshot`

## 3 期待输出

diff 返回 addedClasses/removedClasses/addedProperties/removedProperties/counts；snapshot 支持 from/to；空态有 emptyReason。

## 4 真实输出

```
$ GET /health/ontology-diff
  HTTP 409  from=None to=None
  counts=null addedClasses=None removedClasses=None
$ GET /health/ontology-diff/flow
  HTTP 200  states=['proposed', 'review', 'approved', 'published', 'draft', 'superseded'] count=39
$ GET /health/ontology-snapshot
  HTTP 200  from=None to={'versionId': 'ont-6e81732555e5', 'semver': '0.0.0', 'status': 'published', 'graph': 'urn:platform:graph:tbox:ont-6e81732555e5', 'triples': 3340, 'triplesSource': 'version.tripleCount（内容指纹三元组数）', 'classes': 156, 'classesSource': 'SPARQL GRAPH <urn:platform:graph:tbox:ont-6e81732555e5>：owl:Class/rdfs:Class；label=skos:prefLabel|rdfs:label', 'properties': 135, 'propertiesSource': 'SPARQL GRAPH <urn:platform:graph:tbox:ont-6e81732555e5>：owl:ObjectProperty/DatatypeProperty/AnnotationProperty', 'instances': 0, 'instancesSource': 'SPARQL COUNT(DISTINCT ?s) over A-Box graphs', 'instancesNote': None, 'empty': False, 'readOnly': True} empty=True emptyReason=当前版本没有基线版本，无法做快照对比
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
