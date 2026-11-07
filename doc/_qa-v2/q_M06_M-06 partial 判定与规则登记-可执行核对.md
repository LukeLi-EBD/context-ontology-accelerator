# q_M06 · M-06 partial 判定与规则登记/可执行核对

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_M06` |
| 分组 | C 本轮特性 M 口径与指标 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PASS` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_M06.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 20 条台账（9 partial + 11 规则）逐条有状态，且「仅登记」可导出、不与可执行混淆。

## 2 输入

- `GET /metrics-readiness`
- `GET /metrics-readiness?status=registered_only`
- `GET /metrics-readiness?kind=rule`
- `GET /metrics-readiness?status=registered_only&format=csv`

## 3 期待输出

按 58 号：executed=16 / registered_only=1 / not_executable=3，总 20；registered_only 可单独筛出并导出 CSV。

## 4 真实输出

```
$ GET /metrics-readiness
  HTTP 200  count=20 counts={'executed': 16, 'registered_only': 1, 'not_executable': 3}
$ .../status=registered_only
  HTTP 200  count=1 first={"itemKind": "partial", "metricId": "CUST-005", "status": "registered_only", "reason": "代理事件优先级仅登记在 decision_recommendation；当前绑定使用预计算 days_since_proxy_event，未按裁决的 COALESCE 优先级执行，且不支持按 asOf 求天数差", "detail": {"binding": "precomputed days_since_proxy_event", "mis ...(截断)
$ .../kind=rule
  HTTP 200  count=11
$ .../registered_only&format=csv
  HTTP 200  244 bytes  item_kind,metric_id,status,reason,evidence_ref,checked_at
 partial,CUST-005,registered_only,代理事件优先级仅登记在 decision_recommendation；当前绑定使用预计算 days_since_proxy_event，未按裁决的 COALESCE 优先级执 ...(截断)
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
