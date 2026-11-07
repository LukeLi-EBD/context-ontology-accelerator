# q_M02 · M-02 对外出数清单与 publishable 治理

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_M02` |
| 分组 | C 本轮特性 M 口径与指标 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PASS` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_M02.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 85 行清单 100% 覆盖、每条含 publishable/证据/公式/可算性/缺口，且 JSON 与 CSV 两种导出一致。

## 2 输入

- `GET /metrics/report/manifest`
- `GET /metrics/report/manifest.csv`

## 3 期待输出

count=85、meta.total=85；每条含 publishable/evidenceBasis/formula/computability/externalStatus；CSV 行数与 JSON 一致。

## 4 真实输出

```
$ GET /metrics/report/manifest
  HTTP 200  count=85 meta={"generatedAt": "2026-11-07T00:06:49.791789+00:00", "source": "platform.metric_definition", "scope": "all", "total": 85, "allTotal": 85, "counts": {"publishableTrue": 60, "industry": 46, "regulatory": 39, "externalEligible": 35, "industryExcludedFromExternal": 0, "computability": {"structurally_computable": 74, "blocked_semantics": 8, "blocked_external": 3}}, "industryNotice": "内部基线、不外报", "e1Check": {"source": "doc/_ ...(截断)
  first item keys=['metricId', 'nameZh', 'displayName', 'domain', 'publishable', 'evidenceBasis', 'evidenceBasisLabel', 'evidenceSource', 'hasRegulatoryText', 'industryBaseline', 'internalNotice', 'e1Baseline', 'formula', 'formulaExpr']
$ GET /metrics/report/manifest.csv
  HTTP 200  14238 bytes  CSV 行数=86
  head=﻿metric_id,名称,域,evidence_basis,证据来源,publishable,可算性,公式,对外状态,对外判定说明,内部标注,E1行业基线,缺口,variant_of,output_mode,definition_version
 CUST-001,RFM-R（最近一次行为）,customer,industry,行业通行,false,结构性 ...(截断)
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
