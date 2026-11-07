# q_R02 · R-02 引用与拒答质量闭环（10 例 golden set）

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_R02` |
| 分组 | D 本轮特性 R 检索问答 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `FAIL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_R02.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 golden set 10 例通过率、citation 覆盖率、断链率、拒答原因是否达标。

## 2 输入

- `GET /answer/quality`
- `GET /prov/refusals（非法参数，验证错误码）`

## 3 期待输出

按判据「10 例通过；拒答必带缺层；citation 覆盖按类型统计；断链率不退化」。

## 4 真实输出

```
$ GET /answer/quality
  HTTP 200  strategy=lexical
  summary={"cases": 10, "passed": 6, "failed": 4, "passRate": 0.6, "casesWithCitations": 10, "citationCoverageRate": 1.0, "citations": 39, "resolvableCitations": 39, "citationResolvableRate": 1.0, "brokenLinkRate": 0.0, "baselineBrokenLinkRate": 0.0, "regression": false}
  cases=4  citationCoverageByType=[{"type": "definition", "cases": 5, "refused": 2, "withCitations": 5, "citations": 23, "resolvable": 23, "citationCoverageRate": 1.0, "resolvableRate": 1.0}, {"type": "rule_set", " ...(截断)
  refusalsByReason=[{"type": "definition", "reasonCode": "E_ANSWER_NOT_COVERED", "count": 2}, {"type": "value", "reasonCode": "E_ANSWER_METRIC_NOT_FOUND", "count": 4}]  brokenLinks=[]
$ GET /prov/refusals
  HTTP 400  {"error":{"code":"InvalidArgument","provider":"platform","providerCode":"E_PROV_LOOKUP_REQUIRED","message":"refusal lookup requires requestId or query","retryable":false,"details":{"fields":["requestId","query"]}}}
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
