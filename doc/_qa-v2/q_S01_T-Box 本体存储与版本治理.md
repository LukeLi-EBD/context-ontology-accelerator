# q_S01 · T-Box 本体存储与版本治理

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S01` |
| 分组 | A 核心工作流 S0-S14 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PARTIAL` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_S01.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证 T-Box 以命名图形式存入图库、版本可枚举、当前指针可读、审计链可校验。

## 2 输入

- `GET /ontology/versions`
- `GET /ontology/verify`
- `SQL: SELECT * FROM platform.graph_pointer`
- `SQL: SELECT max(version) FROM platform.schema_version`

## 3 期待输出

存在大量 ontology_version 记录；/ontology/verify ok=true；graph_pointer 只有唯一 tbox/current 且 version_id 指向已发布版本；关系 schema 版本与代码迁移头一致。

## 4 真实输出

```
$ GET /ontology/versions
  HTTP 200  count=21 total=21 deprecated=0 pointer={"name": "tbox/current", "versionId": "ont-6e81732555e5", "semver": "0.0.0", "contentHash": "9417debca40282e5503d73f1446b98374a14508c7380807f548db54d65751303", "graph": "urn:platfo ...(截断)
$ GET /ontology/verify
  HTTP 200  ok=True checked=104 prov.ok=True
$ SQL select * from platform.graph_pointer
  tbox/current|ont-6e81732555e5|2026-11-07 07:53:51.514262+08|smoke-restore
$ SQL select max(version) from platform.schema_version
  schema max version = 40
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
