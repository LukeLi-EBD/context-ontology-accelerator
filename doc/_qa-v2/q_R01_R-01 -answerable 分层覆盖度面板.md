# q_R01 · R-01 /answerable 分层覆盖度面板

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_R01` |
| 分组 | D 本轮特性 R 检索问答 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PARTIAL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_R01.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证四层覆盖计数可见、missing 分布可下钻、按类型筛选、空态明确。

## 2 输入

- `GET /answerable/panel`
- `GET /answerable?q=青岛`

## 3 期待输出

panel 含 layers/missing/candidates/trend/misjudgments；四层 evaluated=24；/answerable 单题判定带缺层说明。

## 4 真实输出

```
$ GET /answerable/panel
  HTTP 200  readOnly=True querySet={"id": "r01-24", "count": 24, "evaluated": 24, "groups": ["A", "B", "C"], "source": "doc/_design/24 §5.2 + platform/test ...(截断)
  layer ontology: evaluated=24 covered=1 missing=18 coverageRate=0.0417
  layer terms: evaluated=24 covered=7 missing=16 coverageRate=0.2917
  layer metrics: evaluated=24 covered=6 missing=7 coverageRate=0.25
  layer facts: evaluated=24 covered=6 missing=0 coverageRate=0.25
$ GET /answerable?q=%E9%9D%92%E5%B2%9B
  HTTP 200  answerable=False coverage=0.0 threshold=0.6
  {"query":"青岛","answerable":false,"coverage":0.0,"threshold":0.6,"coverageChars":{"covered":0,"total":2},"ontologyVersion":"ont-6e81732555e5","ontologyGraph":"urn:platform:graph:tbox:ont-6e81732555e5","termSource":"skos+rdfs:label","termCount":506,"matchedTerms":[],"missing":[{"text":"青岛","span":[0,2],"reason":"no_ontol ...(截断)
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
