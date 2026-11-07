# q_R05 · R-05 D1-1 轻量多跳 /browse/path

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_R05` |
| 分组 | D 本轮特性 R 检索问答 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `OFF` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_R05.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 3 组固定实体对能返回路径、maxHops≤3 生效、超出返回 E_CANVAS_HOPS_EXCEEDED。

## 2 输入

- `GET /browse/path?from=<IRI1>&to=<IRI2>&maxHops=3`
- `GET /browse/path?from=<IRI1>&to=<IRI2>&maxHops=4`
- `SQL/源码: config.py CanvasConfig.provider 默认值`

## 3 期待输出

按 55 号 §5：正常返回路径；maxHops=4 返回 E_CANVAS_HOPS_EXCEEDED。

## 4 真实输出

```
$ GET /browse/path?from=urn%3Aplatform%3Asynthetic%2Finvestment_InvestmentObjective-00175&to=urn%3Aplatform%3Asynthetic%2Finvestment_InvestmentObjective-00149&maxHops=3
  HTTP 503  {"error":{"code":"Unavailable","provider":"absent","providerCode":"E_CANVAS_DISABLED","message":"canvas is disabled: canvas.provider=off (path)","retryable":false,"details":{"reason":"canvas.provider=off","method":"path"}}}
$ GET /browse/path?from=urn%3Aplatform%3Asynthetic%2Finvestment_InvestmentObjective-00175&to=urn%3Aplatform%3Asynthetic%2Finvestment_InvestmentObjective-00149&maxHops=4
  HTTP 503  {"error":{"code":"Unavailable","provider":"absent","providerCode":"E_CANVAS_DISABLED","message":"canvas is disabled: canvas.provider=off (path)","retryable":false,"details":{"reason":"canvas.provider=off","method":"path"}}}
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
