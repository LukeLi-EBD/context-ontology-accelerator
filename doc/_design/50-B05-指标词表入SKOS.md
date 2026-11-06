# 50 · B-05 指标词表并入 SKOS 术语层

> 状态：已完成（2026-11-06）
> 产出：`doc/_fsldm/fsldm-metrics.ttl`（85 概念）、`platform/seed/shapes/fsldm/metrics.ttl`（4 条 Warning 形状）、`platform/tests/test_metrics_skos.py`（9 条单测）
> 新本体版本：`ont-11f92ebb3326`，semver `1.2.1`，三元组 3625，推断 1171

## 1. 目标与边界

把 PostgreSQL `platform.metric_definition` 的 85 行（79 主 + 6 变体）投影为 SKOS 术语层，让指标名成为
`/context/resolve` 的种子；**公式、窗口、聚合、grain、unit、fact_function 等计算字段仍留在 PG**，不进 SKOS。

- 词表与 18 条业务别名共用 `term:` 命名空间；仅有词面冲突者改挂 `metric:`。
- 版本发布走既有 `ontology import` + `publish` 门禁，绕开 GSP 写保护。
- 指标口径文本变更不触发 T-Box 重发布门禁（见 §6 dry-run）。

## 2. 词表生成

`doc/_fsldm/build_metrics_skos.py`（只读 PG、幂等）逐行生成：

| 字段 | 映射 |
| --- | --- |
| `skos:prefLabel@zh` | `name_zh` |
| `skos:altLabel@zh` | `display_name` 去〔行业〕、去括号简称、去空白、去 `→` 后的唯一写法 |
| `skos:notation` | `metric_id`（唯一） |
| `skos:definition@zh` | `definition` 首句（按 。/；切分） |
| `skos:broader` | 6 个变体（`variant_of` 非空）指向族索引 |
| `metric:variant` | 变体标记（`true`，供形状 4 定位） |
| `skos:inScheme` | `term:MetricScheme` |

生成结果校验（rdflib 解析）：**633 三元组 / 85 概念 / 85 个唯一 notation / 6 个 broader / 85 个 definition**。

### 重名检测

- 提取 `fsldm-terms.ttl` 全部 `@zh/@en` 字面量（18 条业务别名）与指标词面做交集。
- **冲突数 0**，85 个概念全部落在 `term:`（`term:M-<metric_id>`），无需 `metric:` 前缀。
- altLabel 去歧义：出现多处的词面只在族索引（非变体）保留；实际丢弃 2 条
  （`13 个月保费继续率`、`25 个月保费继续率`，与 `13/25个月继续率` 变体重复）。

## 3. SHACL 形状（Warning 档）

`platform/seed/shapes/fsldm/metrics.ttl`，部署为 `data/shapes/fsldm/metrics.ttl`，
随 `load_directory` 注册进 `fsldm` 命名空间（manifest `0.1.0 → 0.2.0`）。`terms.ttl` 与 `shapes.ttl` 未改动。

| 形状 | 约束 |
| --- | --- |
| `metric:MetricNotationShape` | `notation` 必填且恰 1 个 |
| `metric:MetricNotationUniqueShape` | `notation` 全词表唯一（SPARQL 反查） |
| `metric:MetricPrefLabelShape` | `prefLabel@zh` 必填 |
| `metric:MetricDefinitionShape` | `definition@zh` 非空必填 |
| `metric:MetricVariantBroaderShape` | `metric:variant true` 必须有 `skos:broader` |

全部 `sh:severity sh:Warning`，pyshacl 以 `allow_warnings=True` 运行：
**不会进入发布阻断门禁**。发布时实测 `conforms=true / violations=0`；
负面 fixture（重复 notation、缺 pref/definition、变体缺 broader）产出 ≥3 条 Warning 但 `conforms` 仍为 true。

## 4. 发布

1. 导出当前 T-Box（`ont-3f57d8ce6636`，2961 三元组）；
2. 与 `fsldm-metrics.ttl` 拼接为 3625 三元组；
3. `platform ontology import --semver 1.2.1 --on-conflict new_version` → draft `ont-11f92ebb3326`；
4. `platform ontology publish` → SHACL 0 违规、一致性通过、reasoner materialize 1171。

| 项 | 值 |
| --- | --- |
| `tbox/current` | `ont-11f92ebb3326` |
| tbox graph | `urn:platform:graph:tbox:ont-11f92ebb3326` |
| semver | `1.2.1` |
| 三元组 | 3625 |
| `inferred_pointer` | `ont-11f92ebb3326` / `urn:platform:inferred:ont-11f92ebb3326` / 1171 |

> 注：`acceptance.ps1` 的 smoke 用例会临时发布 smoke T-Box 并改写指针；两套验收后已用 SQL 把
> `graph_pointer` 与 `inferred_pointer` 恢复为 B-05 版本（`--to` rollback 会新建版本号，不可用于精确恢复）。

## 5. 检索扩展与 before/after

`platform_core/termlex.py` 新增 `concept_query`：只取
`skos:Concept + skos:notation + skos:inScheme term:MetricScheme` 的 `prefLabel/altLabel`，
与既有 `class_query`（`term:termBatch` 锚点）合并进同一张词表；命中即成为 `_seeds` 的 canonical，
`_facts` 随后取到该概念的 definition/altLabel 事实。

同版本切换对比（`/context/resolve` 传 `ontologyVersion`，24 条通用问法 + 10 条指标问法）：

| 集合 | 种子命中 | 指标命中 | 种子总数 | 指标命中总数 | facts |
| --- | --- | --- | --- | --- | --- |
| 通用 24 · before | 1/24 | 0/24 | 1 | 0 | 12 |
| 通用 24 · after | **18/24** | **18/24** | 18 | 18 | 174 |
| 指标 10 · before | 0/10 | 0/10 | 0 | 0 | 0 |
| 指标 10 · after | **10/10** | **10/10** | 10 | 10 | 101 |

指标问法命中示例：`逾期天数怎么算` → `term:M-FIN-BANK-001`（altLabel 命中），facts 带 definition。

## 6. 指标口径文本变更不触发 T-Box 门禁（dry-run）

在 PG 直接改 `FIN-BANK-001` 的 `definition` 文本并恢复：

| 阶段 | `ontology_import` 行数 | `tbox/current` |
| --- | --- | --- |
| 改前 | 20 | `ont-11f92ebb3326` |
| 改后 | 20 | `ont-11f92ebb3326` |
| 恢复后 | 20 | `ont-11f92ebb3326` |

指标口径文本的写入路径不调用 `ontology import/publish`，SHACL 与一致性门禁均未重跑；
SKOS 是发布时快照，文本更新只在下次显式重发布时进入 T-Box。

## 7. 单测与验收

- `platform/tests/test_metrics_skos.py` 共 **9 条**全绿：
  3 条词表行为（pref/alt 命中、类别名不受影响）、2 条形状（正例 0 违规 / 负例仅 Warning）、
  4 条实时（85 概念唯一 notation、pref+definition 齐全、6 变体有 broader、计算字段未泄漏）。
- `acceptance.ps1`：**passed=43 failed=0 skipped=0**。
- `acceptance-s14.ps1`：当时记录 **passed=168 failed=0 skipped=0**；**2026-11-06 回写：该次无独立日志、未复现，不作为结论**。可复核 212/0/0（`_tmp_acc3_s14.log`，`f44a8b6`）/ 366/0/0（`doc/evidence/acceptance-s14-20261106-233619-6ca8561.log`，`6ca8561`）。
- 终态：`/readyz=200`、`metric_observation=0`、`tbox/current=ont-11f92ebb3326`。

## 8. 变更文件

| 文件 | 说明 |
| --- | --- |
| `doc/_fsldm/fsldm-metrics.ttl` | 指标 SKOS 词表（生成物） |
| `doc/_fsldm/build_metrics_skos.py` | 词表生成器（只读 PG、幂等） |
| `platform/seed/shapes/fsldm/metrics.ttl` | 4 条 Warning 形状 |
| `platform/seed/shapes/fsldm/manifest.json` | 版本 `0.2.0` |
| `platform/src/platform_core/termlex.py` | `concept_query` + 注解吸收重构 |
| `platform/tests/test_metrics_skos.py` | 9 条单测 |
| `platform/tests/test_answer_layers.py`、`test_q4_answerable.py` | 版本 pin 更新为 `ont-11f92ebb3326` |
