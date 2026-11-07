# q_R04 · R-04 /browse 六 tab 交叉跳转

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_R04` |
| 分组 | D 本轮特性 R 检索问答 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PASS` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_R04.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证交叉跳转的路径模板已注册、URL 稳定、且明确不新增写操作。

## 2 输入

- `GET /browse/links`

## 3 期待输出

返回 paths/templates/artifacts，stable=true、readOnly=true、writeOperations 为空或明确列出只读。

## 4 真实输出

```
$ GET /browse/links
  HTTP 200  stable=True readOnly=True
  paths=[{"id": "triples-to-entity", "label": "三元组 → 实体页", "from": "/browse/triples", "to": "entity.html", "template": "/ui/entity.html?iri={iri}", "method": "GET", "href": null}, {"id": "metrics-to-definition", "label": "口径卡 → 口径定义", "from": "/browse/metrics", "to": "/browse/metrics/{metricId} + browse met ...(截断)
  templates={"triples-to-entity": "/ui/entity.html?iri={iri}", "metrics-to-definition": "/ui/browse.html?tab=metrics&metricId={metricId}", "tree-to-entity": "/ui/entity.html?iri={iri}", "entity-to-tab": "/ui/browse.html?tab={tab}&entity={iri}"} writeOperations=0
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
