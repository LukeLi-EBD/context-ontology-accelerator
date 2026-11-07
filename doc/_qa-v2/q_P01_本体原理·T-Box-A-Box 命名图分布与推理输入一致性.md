# q_P01 · 本体原理·T-Box/A-Box 命名图分布与推理输入一致性

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_P01` |
| 分组 | F 本体原理专项 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `FAIL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_P01.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

从本体原理检查：T-Box 与 A-Box 是否分区、实例图命名是否有单一权威、推理器读入的图是否等于真实数据所在图。

## 2 输入

- `SPARQL: 按命名图统计三元组 TOP`
- `GET /reasoning/status（aboxGraphs）`
- `GET /health/dashboard（coverage.instances.graphs）`

## 3 期待输出

推理器的 aboxGraphs 应与看板统计的 A-Box 图集合一致；命名图 IRI 应由注册表驱动而非散落硬编码。

## 4 真实输出

```
$ SPARQL SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g ORDER BY  ...(截断)
  [{"g": {"type": "uri", "value": "urn:platform:graph:tbox:ont-6e81732555e5"}, "n": {"type": "literal", "value": "3340", "datatype": "http://www.w3.org/2001/XMLSchema#integer"}}, {"g": {"type": "uri", "value": "urn:platform:inferred:ont-6e81732555e5"}, "n": {"type": "literal", "value": "995", "datatype": "http://www.w3.org/2001/XMLSchema#integer"}}, {"g": {"type": "uri", "value": "urn:platform:prov"}, "n": {"type": "literal", "value": "916", "datatype": "http://www.w3.org/2001/XMLSchema#integer"}}, {"g": {"type": "uri", "value": "urn:platform:inferred:ont-bf6823ba0464"}, "n": {"type": "literal", "value": "18", "datatype": "http://www.w3.org/2001/XMLSchema#integer"}}, {"g": {"type": "uri", "value": "urn:platform:inferred:ont-5d6b21232775"}, "n ...(截断)
$ GET /reasoning/status
  reasoning.aboxGraphs = ['urn:platform:graph:abox:main']
$ GET /health/dashboard
  dashboard.coverage.instances.graphs = ['urn:platform:graph:abox:main']
  instances.total = 0
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
