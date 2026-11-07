# q_S05 · SHACL 校验与推理物化

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S05` |
| 分组 | A 核心工作流 S0-S14 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PARTIAL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_S05.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 SHACL shapes 已装载、推理服务可用、物化产物写入独立命名图，且推理作业没有持续失败。

## 2 输入

- `GET /validation/shapes`
- `GET /reasoning/status`
- `GET /health/dashboard（取 inferenceFailures / shaclViolations）`

## 3 期待输出

shapes 文件非空；reasoner available=true；inferenceFailures.count 应为 0 或极低；aboxGraphs 应覆盖真实 A-Box 命名图。

## 4 真实输出

```
$ GET /validation/shapes
  HTTP 200  files=['core.ttl'] shapesVersion=c33943c929040b570b82a5f7d701786c322f57e39577205969296d90b6f0b0a0
$ GET /reasoning/status
  HTTP 200  engine=robot profile=EL available=True serviceEnabled=True
  aboxGraphs=['urn:platform:graph:abox:main']  pointer.inferred=995
$ GET /health/dashboard
  inferenceFailures=3  lastJob.state=failed
  shaclViolations=None conforms=None
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
