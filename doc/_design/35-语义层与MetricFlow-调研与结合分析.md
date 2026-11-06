# 35 · 语义层（dbt Semantic Layer / MetricFlow）调研与结合分析

- 调研时间：2026-11-06 13:00:03 +08:00（`Get-Date`）
- 性质：**只读调研 + 文档**。未改平台代码、未装依赖、未跑 Docker、未提交。
- 本地证据快照：`D:\agentABC\metricflow` @ `fe4b8c1`（2026-10-13），`metricflow/__about__.py` = `0.214.0.dev0`（开发版本号，非发布版本号）；另有 `D:\agentABC\dbt`（Rust 版 dbt 源码快照，含 `Cargo.toml` / `crates/`）。
- 官方文档访问日期：2026-11-06。
- 证据等级：**[官方]** = 官方文档原文；**[代码]** = 本地仓库源码可定位；**[推断]** = 我基于前两者的判断；**[未找到证据]** = 已检索但无可靠出处。

---

## 0 · 结论（TL;DR）

| 项 | 结论 |
|---|---|
| 查实项 | **26 条**事实/判定（F-01~F-26），其中 5 条是否定性结论或未找到证据 |
| 语义层共性 | 定义层（实体/维度/度量/指标）→ 查询改写为 SQL → 交给数仓执行；**不存数据、不做 ETL、不做推理** |
| 五类对象映射 | semantic model **部分映射**；entity **能映射**；dimension **不能完整映射**；measure **部分映射**；metric **部分映射** |
| 口径→SQL 最大缺口 | 没有维度登记表、没有实体/粒度绑定、没有度量登记表、没有指标依赖图、没有时间列绑定、没有机器可读过滤规则 |
| 三方案推荐 | **A：只借数据模型，自研单方言编译器**。理由是唯一保持 `metric_definition` 单一口径账本、且不冲击 RDF 权威模型的路径 |
| 要补字段 | **9 个**（7 个 P0 + 2 个 P1），本轮不执行迁移 |
| 不引入 | MetricFlow 整包、dbt YAML 第二真源、云 SL 服务层、时轴物理表、多方言渲染、自动多跳 join |

---

## 1 · “语义层”这一类组件的共性边界

### 1.1 dbt Semantic Layer（重点对象）

**[官方]** dbt Semantic Layer 的定位是：把指标定义从 BI 层移到建模层，集中定义后供下游工具一致消费；原文明确“If a metric definition changes in dbt, it’s refreshed everywhere it’s invoked”。（[dbt Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl)）

**[官方]** 组件与许可边界（[SL architecture](https://docs.getdbt.com/docs/use-dbt-semantic-layer/sl-architecture)）：

| 组件 | 作用 | 许可/可用性 |
|---|---|---|
| MetricFlow | YAML 定义语义模型与指标、生成 SQL | Apache 2.0，可本地跑 |
| dbt Semantic Interfaces | 指标/维度/关系的配置规范 | Apache 2.0 |
| Service layer | 接收查询请求、分发到目标查询引擎 | 专有，dbt Cloud（Starter/Enterprise） |
| Semantic Layer APIs | GraphQL / JDBC 查询接口 | 专有，dbt Cloud |

结论：**开源可拿到的只有“定义 + 编译成 SQL”**；服务层、API、缓存、Exports 都是云产品。

### 1.2 其他形态（简要对照）

- **Cube**：**[官方]** 自称“open-source semantic layer”，核心是 **Semantic SQL**：AI/BI 不直接查数仓，而是查语义层，由语义层做受控代理（[Cube Introduction](https://cube.dev/docs/product/introduction)）。
- **AtScale**：**[官方]** 定义为“ sits between your data warehouse and the tools that access it”，是集中存放指标定义、业务术语、数据关系的层；明确“**What it’s not: a database or data warehouse**”（[AtScale: What is a Semantic Layer?](https://www.atscale.com/semantic-layer/)）。

### 1.3 共性边界（[推断]，与上面官方描述一致）

所有语义层都在做同一件事：**把“业务口径”从“物理 SQL”里抽出来，成为一个可被多种消费端复用的查询改写层**。共性能力：

1. 定义层：实体/维度/度量/指标（含聚合、比率、派生、累计、转化）。
2. 物理映射：每个语义对象绑定到一张已存在的表/视图。
3. 查询改写：接收“指标 + 维度 + 时间窗 + 过滤”，推导 join，生成目标方言 SQL。
4. 治理面：命名唯一、类型校验、访问控制（云产品才有）。
5. 消费面：BI/表格/API/CLI。

共性**不做**：不存业务数据、不做 ETL、不做 RDF/OWL 推理、不做监管条款语义关联、不做术语同义词体系。

---

## 2 · MetricFlow 事实清单（带出处）

> 说明：`metricflow` 仓库仍在演进。**[代码]** 指 `fe4b8c1` 快照；**[官方]** 指 2026-11-06 的 docs.getdbt.com。两者有代际差时以官方最新 spec 为准，并明确标注。

### 2.1 仓库与版本事实

| ID | 事实 | 出处 | 等级 |
|---|---|---|---|
| F-01 | 本地快照 commit `fe4b8c1`（2026-10-13），版本 `0.214.0.dev0` | `metricflow/__about__.py`；`git log -1` | **[代码]** |
| F-02 | MetricFlow 定位为“把简单指标定义翻译成可复用 SQL，并对目标 SQL 引擎执行” | [pyproject.toml](file:///D:/agentABC/metricflow/pyproject.toml) description | **[代码]** |
| F-03 | 官方支持仓库：Snowflake、BigQuery、Databricks、Postgres（**dbt v1 only**）、Redshift | [About MetricFlow](https://docs.getdbt.com/docs/build/about-metricflow) | **[官方]** |
| F-04 | 方言渲染器在仓库中按引擎分文件：athena / big_query / clickhouse / databricks / duckdb / postgres / redshift / snowflake / trino / vertica | [render 目录](file:///D:/agentABC/metricflow/metricflow/sql/render) | **[代码]** |

### 2.2 对象模型（5 类，不是 4 类）

任务描述为“四层”，实际可落库对象是 **5 类**：semantic model / entity / dimension / measure / metric；metric 内部再分 5 型。

| ID | 事实 | 出处 | 等级 |
|---|---|---|---|
| F-05 | semantic model 字段：`name`、`node_relation`、`defaults.agg_time_dimension`、`primary_entity`、`entities[]`、`measures[]`、`dimensions[]`、`description`、`label`、`config` | [schemas.py L564-L586](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/parsing/schemas.py#L564-L586) | **[代码]** |
| F-06 | entity 四型：`primary` / `unique` / `foreign` / `natural` | [entity_type.py](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/type_enums/entity_type.py)；[Entities](https://docs.getdbt.com/docs/build/entities) | **[代码]** **[官方]** |
| F-07 | dimension 两型：`categorical` / `time`；time 维度必须带 `type_params.time_granularity` | [dimension.py](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/protocols/dimension.py#L36-L47)；[Dimensions](https://docs.getdbt.com/docs/build/dimensions) | **[代码]** **[官方]** |
| F-08 | measure 聚合：`sum`、`min`、`max`、`count_distinct`、`sum_boolean`、`average`、`percentile`、`median`、`count`；支持 `expr`、`agg_params`、`non_additive_dimension`、`agg_time_dimension` | [aggregation_type.py](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/type_enums/aggregation_type.py)；[measure.py](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/protocols/measure.py#L49-L105) | **[代码]** |
| F-09 | metric 五型：`simple` / `ratio` / `cumulative` / `derived` / `conversion` | [metric_type.py](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/type_enums/metric_type.py)；[Creating metrics](https://docs.getdbt.com/docs/build/metrics-overview) | **[代码]** **[官方]** |
| F-10 | 各型参数：simple=`measure`/`agg`；ratio=`numerator`/`denominator`；derived=`expr`+`metrics[]`+offset；cumulative=`window`/`grain_to_date`/`period_agg`；conversion=`base_measure`/`conversion_measure`/`entity`/`window`/`constant_properties` | [metric.py L96-L391](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/protocols/metric.py#L96-L391)；[schemas.py L92-L210](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/parsing/schemas.py#L92-L210) | **[代码]** |
| F-11 | **官方最新 spec 变化**：`measures` 已被废弃，改为 `type: simple` 指标；实体/维度改为在 `columns` 下定义；`type_params` 的字段上提为顶层键 | [Measures（deprecated 提示）](https://docs.getdbt.com/docs/build/measures)；[Upgrading to v1.12](https://docs.getdbt.com/docs/dbt-versions/core-upgrade/upgrading-to-v1.12?version=1.12) | **[官方]** |

> **[推断]** F-11 说明“measure”这一层是**过渡形态**，不是稳定内核。我们要学的是“度量作为可复用聚合单元”的思想，而不是照抄它的 YAML 位置。

### 2.3 时间、过滤、join

| ID | 事实 | 出处 | 等级 |
|---|---|---|---|
| F-12 | 特殊时间维度 `metric_time`；粒度用后缀表达，如 `metric_time__month` | [MetricFlow commands §Time granularity](https://docs.getdbt.com/docs/build/metricflow-commands) | **[官方]** |
| F-13 | 时间类指标/维度**必须提供 time spine**（一张 dbt 模型/物理表），用于累计、offset、conversion、SCD II、`join_to_timespine` | [MetricFlow time spine](https://docs.getdbt.com/docs/build/metricflow-time-spine) | **[官方]** |
| F-14 | filter 用 Jinja 模板，如 `--where "{{ Dimension('order_id__is_food_order') }} = True"`、`--where "{{ TimeDimension('metric_time','week') }} >= '2024-02-01'"` | [MetricFlow commands §Query](https://docs.getdbt.com/docs/build/metricflow-commands) | **[官方]** |
| F-15 | join 由 entity 图自动推导：semantic model 为节点、entity 为边；fct↔dim 用 left join，多 fct 用 full outer；**禁止 fan-out / chasm join**；多跳上限 2 跳（最多 3 表） | [Joins](https://docs.getdbt.com/docs/build/join-logic) | **[官方]** |
| F-16 | 维度跨模型引用用双下划线：`entity__dimension` | 同上 | **[官方]** |

### 2.4 编译链

| ID | 事实 | 出处 | 等级 |
|---|---|---|---|
| F-17 | 编译链：dbt 项目 → semantic manifest（解析+schema 校验）→ `MetricFlowQueryParser.parse_and_validate_query` 产出 query spec → `DataflowPlanBuilder.build_plan` 产出 dataflow plan → `DataflowToSqlPlanConverter` → execution plan → `executor.execute_plan` | [metricflow_engine.py L557-L669](file:///D:/agentABC/metricflow/metricflow/engine/metricflow_engine.py#L557-L669) | **[代码]** |
| F-18 | **必须先有物理关系**：semantic model 对应一个 dbt 模型/表（`node_relation`）；指标本身默认不物化 | [Semantic models](https://docs.getdbt.com/docs/build/semantic-models)；[FAQ](https://docs.getdbt.com/docs/use-dbt-semantic-layer/sl-faqs)（“does not store a physical copy”） | **[官方]** |
| F-19 | 生成 SQL 依赖目标方言：同一语义计划由不同 renderer 渲染 | [render 目录](file:///D:/agentABC/metricflow/metricflow/sql/render) | **[代码]** |

### 2.5 可用性、检验、治理

| ID | 事实 | 出处 | 等级 |
|---|---|---|---|
| F-20 | CLI：`list metrics/dimensions/entities/saved-queries`、`validate-configs`、`health-checks`、`query`、`tutorial` | [main.py L300-L652](file:///D:/agentABC/metricflow/dbt-metricflow/dbt_metricflow/cli/main.py#L300-L652)（list/validate）、[L124-L300](file:///D:/agentABC/metricflow/dbt-metricflow/dbt_metricflow/cli/main.py#L124-L300)（query）；[MetricFlow commands](https://docs.getdbt.com/docs/build/metricflow-commands) | **[代码]** **[官方]** |
| F-21 | **支持只编译不执行**：`mf query --explain` / `dbt sl query --compile` 打印 SQL 后直接 `exit()`，不落数仓执行 | [main.py L226-L271](file:///D:/agentABC/metricflow/dbt-metricflow/dbt_metricflow/cli/main.py#L226-L271) | **[代码]** **[官方]** |
| F-22 | 校验分两层：语义 manifest 校验 + 数仓校验（表/列存在、函数可用、join 歧义）；`--skip-dw` 可只做语义校验 | [main.py L566-L626](file:///D:/agentABC/metricflow/dbt-metricflow/dbt_metricflow/cli/main.py#L566-L626) | **[代码]** |
| F-23 | **未找到“指标级版本化/废弃/迁移”的一等机制**。找到的只有：旧 `dbt_metrics` 包与旧 SL 在 2023-12-15 废弃、以及 YAML spec 迁移工具 `dbt-autofix` | [Deprecation: dbt Metrics](https://docs.getdbt.com/docs/dbt-versions/release-notes/Dec-2023/legacy-sl)；[Migrate to latest YAML spec](https://docs.getdbt.com/docs/build/latest-metrics-spec) | **[未找到证据]** |
| F-24 | **未找到 metric 级影响面分析**。dbt 的血缘/impact analysis 是 **model/column 级**（dbt Explorer、column-level lineage） | [Column-level lineage](https://docs.getdbt.com/docs/explore/column-level-lineage)；[dbt Explorer](https://docs.getdbt.com/docs/collaborate/explore-projects) | **[未找到证据]**（metric 级） |
| F-25 | 只有“私有指标”开关 `is_private`（不出现在 API/终端用户），不是废弃机制 | [metric.py L347](file:///D:/agentABC/metricflow/metricflow_semantic_interfaces/protocols/metric.py#L347) | **[代码]** |

### 2.6 它明确不做什么

| ID | 事实 | 出处 | 等级 |
|---|---|---|---|
| F-26 | 不做 RDF/OWL/SHACL/SPARQL 推理；不做业务术语同义词；不做指标到监管条款/本体层的血缘；不支持自定义聚合；不做物理数据存储 | 由架构（YAML→semantic manifest→SQL）与仓库依赖推断；FAQ 明示“不存物理副本”“不支持自定义聚合” | **[推断]** + **[官方]**（最后两条） |

---

## 3 · 我们的现状基线（只列与本文相关的）

| 资产 | 现状 | 证据 |
|---|---|---|
| 权威模型 | RDF + OWL + SHACL + SPARQL（Oxigraph） | 既有架构，本文不复测 |
| 版本治理 | `draft → proposed → approved → published → superseded`；diff/impact；SHACL/ELK 门禁；rollback | 既有实现 |
| 口径账本 | `platform.metric_definition` **85 行 = 79 主 + 6 变体** | V18/V21 迁移 |
| 口径字段 | `metric_kind`、`formula_expr`、`numerator_agg`、`denominator_agg`、`window_kind`、`min_window_days`、`grain`、`unit`、`fact_function`、`effective_date`、`variant_of`、`output_mode`、`rule_set_json`、`publishable`、`evidence_basis` | [V19](file:///D:/agentABC/coa/platform/src/platform_core/sql/V19__metric_observation.sql#L4-L13)、[V20](file:///D:/agentABC/coa/platform/src/platform_core/sql/V20__metric_entities.sql#L16)、[V21](file:///D:/agentABC/coa/platform/src/platform_core/sql/V21__metric_definition_v5.sql#L12-L22) |
| 出数 | `compute=true`，任务给定口径为 **4 条**；仓库实际已绑定 **9 个** `fact_function`（V20 两条 + V22 七条），最终可出数以 DB 复核为准。公式用安全 AST 求值，分子/分母来自 `fact_function` 聚合 | [metrics.py L238-L386](file:///D:/agentABC/coa/platform/src/platform_core/metrics.py#L238-L386) |
| 事实表 | V22 建 bank 事实表（贷款账户、还款计划、授信、申请、催收、核销等），同文件后续建 insurance/customer 事实表；每表带 `data_source/fixture` 溯源 | [V22 L17-L177](file:///D:/agentABC/coa/platform/src/platform_core/sql/V22__fact_model_v6.sql#L17-L177) |
| 术语层 | SKOS 注解层：15 锚点类 / 18 别名 | 既有实现 |
| Web | `/browse/metrics` 只读口径卡；无 group-by/时间序列查询 | [api.py L589-L670](file:///D:/agentABC/coa/platform/src/platform_core/api.py#L589-L670) |

**一句话**：我们有“口径文本 + 二元算术 + 每指标一个 PL/pgSQL 聚合函数”，没有“维度/实体/度量/指标依赖”的可编译模型。

---

## 4 · MetricFlow 对象 → 我们资产的映射

### 4.1 五类对象映射表

| MetricFlow 对象 | 我们的对应物 | 判定 | 理由 | 建议落点 |
|---|---|---|---|---|
| **semantic model**（一张物理关系 + 其上的实体/维度/度量） | 事实表（`bank_loan_account` 等）+ `fsldm` 类 | **部分映射** | MetricFlow 要求“一个语义模型 = 一张物理关系”；我们的事实是规范化的多表，且类是本体的概念类，不是物理表 | 物理绑定留 PG（一指标族一张视图/表）；语义类留本体；**不要**把 semantic model 建成 OWL 类 |
| **entity**（join key，primary/unique/foreign/natural） | 实体 IRI + 事实表 PK/FK（`account_id`、`customer_no`） | **能映射** | 实体身份在两端都存在；差别只在唯一性类型我们没显式声明 | 身份/层级留本体（已是权威）；`primary/foreign` 与唯一性落 PG 元数据；唯一性可选加 SHACL（`owl:InverseFunctionalProperty` 或 `sh:maxCount 1`） |
| **dimension**（time/categorical + 粒度） | 只有 `grain` 文本 + 事实表里的 `product/channel/institution/region` 列 | **不能完整映射** | 没有维度登记表、没有时间维度角色、没有层级、没有“哪些指标可按哪些维度和粒度切” | **新建 PG 维度登记表**；业务概念（产品/渠道/机构/地区）可在本体挂类/层级；时间维度留 PG，不进 T-Box |
| **measure**（命名聚合：agg + expr + 非可加维度） | `numerator_agg` / `denominator_agg` + `fact_function` | **部分映射** | 我们只有“分子/分母各自一个聚合”，没有命名度量、没有表达式、没有非可加维度处理 | **新建 PG 度量登记表**；度量是物理实现细节，**不进本体** |
| **metric**（simple/ratio/derived/cumulative/conversion） | `metric_definition` + `formula_expr` + `variant_of` | **部分映射** | 口径账本已在；但只支持分子/分母二元算术，无指标依赖图、无累计/转化语义 | `metric_definition` 继续做唯一口径账本；只把“监管含义/条款/术语/版本替代”升本体 |

### 4.2 三桶结论（留 PG / 升本体 / 不进本体）

- **继续留 PG**：semantic model 的物理绑定、measure 登记、dimension 登记、metric 依赖图、时间绑定、filter_spec。这些是“查询怎么算”的实现细节，进本体会让每次加列/改聚合都触发 T-Box 发布门禁。
- **升本体**：entity 身份与层级（`fsldm` 类/对象属性）、业务维度的概念与层级（产品/渠道/机构/地区）、指标 ↔ 监管条款/术语/版本替代关系。这些是“这个口径在业务世界指什么”，只有本体能承载。
- **不进本体**：物理表名/列名、SQL 表达式、聚合函数名、方言、join 路径、缓存策略。它们是编译器输入，不是业务概念。

### 4.3 指标类型逐型判定

| MetricFlow 类型 | 我们的现状 | 判定 | 说明 |
|---|---|---|---|
| `simple` | `metric_kind=duration` 等单值指标，`formula_expr='numerator'` | **部分映射** | 能表达“单聚合”，但没有度量名与表达式复用 |
| `ratio` | `formula_expr='numerator / denominator * 100'` + 两个 agg | **能映射** | 这是目前唯一被完整支撑的型 |
| `derived` | 无指标依赖图 | **不能映射** | 只有分子/分母，不能 `metric A = metric B - metric C` |
| `cumulative` | `window_kind=period` 只表达观察窗 | **不能映射** | 没有“累计到某粒度/期初至今”的语义 |
| `conversion` | 无 | **不能映射** | 没有 base/conversion 事件配对与实体 join |
| `rule_set` | `output_mode=rule_set` + `rule_set_json`（FIN-BANK-034） | **我们自有扩展** | MetricFlow 五型里没有规则型；这是我们的差异化，不应为了对齐而删 |

---

## 5 · “口径 → SQL”这条链我们缺什么

| ID | 缺口 | 现状 | 缺什么 | 直接后果 |
|---|---|---|---|---|
| G1 | 维度登记 | 无 | 维度名、类型（time/categorical）、来源列、允许的粒度、层级 | 无法 group-by，只能整表出单值 |
| G2 | 实体/粒度绑定 | 只有 `grain` 文本（`customer/agreement/...`） | 实体名、主键、实体类型、本体 IRI、join 路径 | 无法判断聚合到哪一层，join 靠手写 SQL |
| G3 | 度量登记 | 只有分子/分母两个 agg | 度量名、`agg`、`expr`、非可加维度、聚合时间列 | 同一聚合逻辑在多个 `fact_function` 里重复 |
| G4 | 指标依赖图 | 无 | `metric_inputs`（引用其他 metric/measure、别名、过滤、offset） | derived/cumulative 无法编译，也无法做环检测 |
| G5 | 时间绑定 | `window_kind` + `min_window_days`，但没有时间列 | 时间列、时间粒度、instant/period 口径、时轴来源 | 期间指标只能靠 PL/pgSQL 里硬写日期条件 |
| G6 | 过滤规则 | 排除项写在 `denominator_text` 散文里 | 机器可读的 `filter_spec`（字段/操作符/值/作用域） | 78 条口径的“剔除趸交/撤销/核销”无法复用与校验 |
| G7 | 币种/汇率 | 只有 `unit` | 币种、汇率规则、是否统一折算 | 多币种指标口径无法一致 |
| G8 | 空值填充 | 无 | `fill_nulls_with` / 时轴补零策略 | 月度序列会缺口，趋势不可比 |
| G9 | 通用编译器 | 每指标一个 `platform.metric_fact_*` 函数 | 一个“度量 CTE → 实体/粒度聚合 → 比率/派生 → group-by → 时间窗”的通用构造器 | 79 条要写 79 个函数，改口径要改 SQL |
| G10 | 编译期校验 | 只有运行期 `compute` 与错误码 | `validate`/`explain`：干跑出 SQL、依赖环、维度可用性、分母唯一性 | 口径错误只能在跑数时暴露 |

> **[推断]** G1-G6 是“能不能编译”的硬缺口；G7-G8 是“算得对不对/好不好看”的软缺口；G9-G10 是工程化缺口。

---

## 6 · 三方案对比与推荐

### 6.1 方案对比

| 维度 | **A. 只借数据模型，自研编译器** | **B. 引入 MetricFlow 作编译层** | **C. 维持现状，模板化 SQL** |
|---|---|---|---|
| 做法 | 在 PG 增维度/度量/实体/依赖元数据；用一个通用 SQL 构造器编译到 PostgreSQL | 在我们的宽表/视图上写 semantic model YAML，用 `mf query --explain` 编译 | 继续每指标一个 `fact_function`，把常用 ratio 抽成 SQL 模板 |
| 成本 | **中**：V23 元数据 + 编译器 + 双跑验证，约 3-4 个切片 | **高**：dbt 项目/适配器 + YAML 双写 + time spine + Python 运行时 + 版本跟随 | **低（短期）**：无新增结构 |
| 风险 | SQL 正确性、口径回归；可用“与现有可算指标双跑等值”兜底 | **双真源**（PG 账本 vs YAML）、dbt 版本漂移、Postgres 仅 dbt v1 支持、无法接 RDF/SHACL | 79 个函数、维度不可组合、改口径要改 SQL、错误码分散 |
| 对 RDF 权威模型冲击 | **低**：不动 T-Box；仅 PG 增表；可选独立 SHACL 文件 | **高**：要么放弃 RDF 权威，要么维护 YAML↔RDF 双向同步 | **低**：不动 |
| 单机/少用户适配 | 好 | 差（服务层是云产品；本地只有引擎） | 好但天花板低 |
| 长期可维护 | 中（自研但边界清晰、单方言） | 差（上游 spec 还在变：measure 已废弃） | 差（线性膨胀） |

### 6.2 推荐：A，且**只做窄口径**

**理由一句话**：只有 A 能在不引入第二真源、不冲击 SHACL/推理/版本治理的前提下，把“维度组合 + 聚合正确性”补上；B 会把口径账本撕成两半，C 在 79 条规模上必然失控。

**最小落地（本轮只设计，不实施）**：

1. **元数据（V23）**：新增 `platform.semantic_entity`、`platform.semantic_dimension`、`platform.semantic_measure` 三张登记表；`metric_definition` 增 `metric_type`、`metric_inputs`、`entity_binding`、`dimension_binding`、`time_binding`、`measure_binding`、`filter_spec`。
2. **编译器**：一个 PostgreSQL 单方言构造器，固定五段 CTE：
   - `measures`：按度量表达式聚合；
   - `entity_grain`：按实体主键/粒度去重；
   - `time_window`：instant/period + 时间列；
   - `metric_algebra`：ratio/derived（拓扑序，检测环）；
   - `group_by`：只允许登记过的维度与粒度。
3. **干跑**：新增 `compile`/`validate`（只返回 SQL、依赖序、错误码），不执行；复用现有 `E_METRIC_NOT_DRIVABLE` 等错误码语义。
4. **双跑**：对现有可算指标（任务口径 4 条；仓库已绑定 9 个 `fact_function`，以 DB 复核为准），新旧实现逐值比对，必须完全相等才允许切换；不等则回退，不修断言。
5. **边界**：只覆盖“有事实表 + 单实体粒度 + 已登记维度”的指标；`output_mode=index/rule_set`、`formula_disabled=true` 继续拒绝。

**明确不做**：不引入 `dbt`、不写 YAML、不建 time spine 物理表（用 `generate_series` 生成时轴）、不做多方言、不做自动多跳 join。

---

## 7 · 本体 vs 语义层：分工表

| 事项 | 本体（RDF/OWL/SHACL/SPARQL） | 语义层（MetricFlow 思路） | 结论 |
|---|---|---|---|
| 指标定义唯一账本 | 不适合（T-Box 发布太重） | 适合（PG `metric_definition`） | **留 PG** |
| 维度组合、group-by、粒度 | 不适合 | 强 | **学语义层** |
| 聚合正确性（非可加、去重、比率） | 不适合 | 强 | **学语义层** |
| 实体身份、层级、子类推理 | 强 | 弱（只有 join key 类型） | **留本体** |
| 指标 ↔ 监管条款/文件版本 | **只有本体能做** | 不做 | **本体独有** |
| 业务术语/同义词/别名扩展 | **只有本体能做**（SKOS 15/18） | 不做 | **本体独有** |
| 跨域实体关系（客户-保单-理赔-贷款） | **只有本体能做** | 只做 join 路径 | **本体独有** |
| 口径版本 diff/impact/rollback/审计 | 已有且强 | **无 metric 级机制**（F-23/F-24） | **留本体治理** |
| 编译 SQL / 干跑 / explain | 不做 | 强 | **学语义层** |
| 物理表/视图绑定 | 不做 | 强 | **留 PG** |
| 数据血缘到本体层 | 不做 | 只有 model/column 级 | **两边都不做，登记为缺口** |
| 消费 API/缓存/Exports | 我们已有只读 REST | 云 SL 强，但用不上 | **维持现状** |

---

## 8 · 不该学的部分（搬过来会破坏现状或纯属负担）

| ID | 不学 | 原因 | 会破坏什么 / 负担 |
|---|---|---|---|
| N-01 | 把 `semantic model`/`measure`/物理列写进 OWL T-Box | 物理 schema 变更会触发 T-Box 发布门禁；度量是实现细节，不是业务概念 | 污染权威模型；每次加列都要走三道门禁；SHACL 难写 |
| N-02 | 用 dbt YAML 作为第二真源 | PG 账本与 YAML 必然漂移；两套命名/类型/过滤 | 破坏“唯一口径来源”；审计链无法覆盖 YAML |
| N-03 | “改一处自动全刷新” | 我们要求 proposal→approved→published 与审计留痕 | 绕过治理门禁与 rollback；违反既有硬约束 |
| N-04 | 强制 time spine 物理表 | 单机多一张表、多一条维护链（F-13） | 纯负担；PG `generate_series` 足够 |
| N-05 | 自动多跳 join（≤2 跳） | 我们的事实表唯一性约束不完整，自动 join 有 fan-out 风险（F-15） | 可能算错数且难发现；应显式绑定 join |
| N-06 | 多方言 renderer（10 种） | 我们只有 PostgreSQL | 10 倍维护面，零收益 |
| N-07 | 云 SL 服务层/GraphQL/JDBC/Exports/缓存 | 单机、少用户、已有只读 REST | 纯负担；且是专有云产品 |
| N-08 | 接受“指标无版本化” | 我们有版本治理与 `variant_of`/`effective_date` | 退化到 YAML 覆盖，破坏审计与回滚 |
| N-09 | 用 `measure` 作为长期内核 | 官方已废弃 measure、并入 simple metric（F-11） | 学一个正在退场的抽象 |
| N-10 | 用 MetricFlow 的错误码/校验语义替换我们的 | 我们已有 `E_METRIC_*` 错误码与 fixture 护栏 | 破坏 API 契约与既有负例测试 |

---

## 9 · 要补的字段与最小迁移建议（本轮不执行）

### 9.1 字段清单（9 个）

| # | 字段 | 现状 | 为什么 | 类型 | 优先级 |
|---|---|---|---|---|---|
| 1 | `metric_type` | 只有 `metric_kind`（duration/ratio 等）+ `output_mode` | 编译器需要按 simple/ratio/derived/cumulative/conversion/rule_set 分派 | text + CHECK | **P0** |
| 2 | `metric_inputs` | 无 | derived/cumulative/ratio 的依赖图、别名、offset、环检测 | jsonb | **P0** |
| 3 | `entity_binding` | 只有 `grain` 文本 | 实体名、主键、`primary/foreign`、本体 IRI、粒度 | jsonb | **P0** |
| 4 | `dimension_binding` | 无 | 允许的 group-by 维度、来源列、类型、层级 | jsonb / 关联登记表 | **P0** |
| 5 | `time_binding` | 只有 `window_kind`、`min_window_days` | 时间列、粒度、instant/period、时轴来源 | jsonb | **P0** |
| 6 | `measure_binding` | 只有 `numerator_agg`/`denominator_agg` | 命名度量、`expr`、非可加维度、聚合时间列 | jsonb | **P0** |
| 7 | `filter_spec` | 排除项是 `denominator_text` 散文 | 机器可读的剔除规则（字段/操作符/值/作用域） | jsonb | **P0** |
| 8 | `unit_currency` / `fx_rule` | 只有 `unit` | 多币种口径一致（银行指标） | jsonb | **P1** |
| 9 | `null_fill` / `time_spine_policy` | 无 | 月度序列补零、趋势可比 | jsonb / text | **P1** |

### 9.2 最小迁移建议（仅设计）

- 版本：当前 `SUPPORTED_SCHEMA_VERSION = 22`（[metadata_pg.py L19](file:///D:/agentABC/coa/platform/src/platform_core/adapters/metadata_pg.py#L19)），下一版为 **V23**。
- 形态：`ALTER TABLE ... ADD COLUMN IF NOT EXISTS` + `CREATE TABLE IF NOT EXISTS`，可重入；`SUPPORTED_SCHEMA_VERSION` 22→23。
- 新表：`platform.semantic_entity`、`platform.semantic_dimension`、`platform.semantic_measure`（都以 `data_source`/`fixture` 标记溯源，沿用 V22 约定）。
- 种子：**只灌现有已绑定 `fact_function` 的指标**（及其事实表所需的实体/维度/度量），其余未绑定指标保持 `NULL` 并继续 `E_METRIC_NOT_DRIVABLE`，不造数据、不假装可算。
- 切换：不改现有 `compute` 路径；编译器先以 `compile` 干跑存在，双跑等值后再决定是否替换。
- 不动：T-Box、SHACL 正式 shapes、版本指针、审计链。

---

## 10 · 开放问题与风险

| ID | 问题 | 现状 | 建议 |
|---|---|---|---|
| OQ-1 | 指标级版本化放哪 | 本体有版本治理；`metric_definition` 只有 `variant_of`/`effective_date`，无 `supersedes` | 若未来要“口径版本”，在 PG 加 `status/supersedes/superseded_by` 并关联 `ontology_version`，不要塞进 T-Box |
| OQ-2 | 时轴来源 | MetricFlow 要求物理 time spine（F-13） | 用 `generate_series` + 粒度函数；不建表 |
| OQ-3 | 实体唯一性 | 事实表有 UNIQUE 约束，但本体未断言 | 可选独立 SHACL 文件（`sh:maxCount 1` / `owl:InverseFunctionalProperty`），不进阻断门禁 |
| OQ-4 | join 路径 | 自动 join 有 fan-out 风险（F-15） | 显式登记 join；不允许编译器自由推导多跳 |
| OQ-5 | PostgreSQL 支持 | 官方仅 **dbt v1** 支持 Postgres（F-03）；dbt v2 已转 Rust | 这是不选 B 的硬理由之一，选 A 不受影响 |
| OQ-6 | measure 抽象寿命 | 官方已废弃 measure（F-11） | 只借“命名聚合单元”概念，不借 YAML 位置与类型名 |

---

## 11 · 出处清单

**官方文档（2026-11-06 访问）**

1. dbt Semantic Layer：https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl
2. SL Architecture：https://docs.getdbt.com/docs/use-dbt-semantic-layer/sl-architecture
3. SL FAQs：https://docs.getdbt.com/docs/use-dbt-semantic-layer/sl-faqs
4. Semantic models：https://docs.getdbt.com/docs/build/semantic-models
5. Creating metrics：https://docs.getdbt.com/docs/build/metrics-overview
6. Entities：https://docs.getdbt.com/docs/build/entities
7. Dimensions：https://docs.getdbt.com/docs/build/dimensions
8. Measures（deprecated 提示）：https://docs.getdbt.com/docs/build/measures
9. Joins：https://docs.getdbt.com/docs/build/join-logic
10. MetricFlow time spine：https://docs.getdbt.com/docs/build/metricflow-time-spine
11. MetricFlow commands：https://docs.getdbt.com/docs/build/metricflow-commands
12. About MetricFlow：https://docs.getdbt.com/docs/build/about-metricflow
13. Upgrading to v1.12：https://docs.getdbt.com/docs/dbt-versions/core-upgrade/upgrading-to-v1.12?version=1.12
14. Migrate to latest YAML spec：https://docs.getdbt.com/docs/build/latest-metrics-spec
15. Deprecation: dbt Metrics（2023-12-15）：https://docs.getdbt.com/docs/dbt-versions/release-notes/Dec-2023/legacy-sl
16. Column-level lineage：https://docs.getdbt.com/docs/explore/column-level-lineage
17. Cube Introduction：https://cube.dev/docs/product/introduction
18. AtScale: What is a Semantic Layer?：https://www.atscale.com/semantic-layer/

**本地仓库（`D:\agentABC\metricflow` @ `fe4b8c1`）**

- `metricflow/__about__.py`（版本）
- `metricflow_semantic_interfaces/type_enums/metric_type.py`（指标五型）
- `metricflow_semantic_interfaces/type_enums/entity_type.py`（实体四型）
- `metricflow_semantic_interfaces/type_enums/aggregation_type.py`（聚合九种）
- `metricflow_semantic_interfaces/protocols/{semantic_model,entity,dimension,measure,metric}.py`
- `metricflow_semantic_interfaces/parsing/schemas.py`（YAML schema）
- `metricflow/engine/metricflow_engine.py`（编译链）
- `dbt-metricflow/dbt_metricflow/cli/main.py`（CLI 与 `--explain`）
- `metricflow/sql/render/`（方言渲染器）

**我们的资产**

- `coa/platform/src/platform_core/sql/V18__metric_definition.sql`
- `coa/platform/src/platform_core/sql/V19__metric_observation.sql`
- `coa/platform/src/platform_core/sql/V20__metric_entities.sql`
- `coa/platform/src/platform_core/sql/V21__metric_definition_v5.sql`
- `coa/platform/src/platform_core/sql/V22__fact_model_v6.sql`
- `coa/platform/src/platform_core/metrics.py`
- `coa/platform/src/platform_core/api.py`
- `coa/platform/src/platform_core/adapters/metadata_pg.py`

---

## 12 · 变更记录

| 日期 | 内容 |
|---|---|
| 2026-11-06 | 首版：完成 dbt SL / MetricFlow / Cube / AtScale 调研；完成五类对象映射、三方案对比、分工表、不学清单与 9 个待补字段设计；未执行任何迁移或代码改动 |
