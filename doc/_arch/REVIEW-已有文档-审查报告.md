# `_arch` 已有架构文档审查报告（源码核验版）

> 审查时间：2026-11-04
> 审查对象：`D:/AgentABC/_arch` 下 13 份既有架构文档
> 核验基准：各文档对应的本地源码仓库（见下表），以文件存在性、行号指向的实际代码行、类名/函数名/配置项、模块计数与主链路调用方向为依据
> 审查边界：编号 10、14、16、17、18、19 的文档由并行会话生成，本次**未读取、未修改、未评判**；`_digest` 未改动；所有子项目源码**只读**

---

## 一、审查范围与方法

### 1.1 范围

| # | 文档 | 源码仓库 | 文档行数（修订后） |
|---|---|---|---|
| 01 | `01-airflow-架构.md` | `D:/AgentABC/airflow` | 约 590 |
| 02 | `02-dolphinscheduler-架构.md` | `D:/AgentABC/dolphinscheduler` | 约 470 |
| 03 | `03-Taier-架构.md` | `D:/AgentABC/Taier` | 约 520 |
| 04 | `04-seatunnel-架构.md` | `D:/AgentABC/seatunnel` | 约 520 |
| 05 | `05-canal-架构.md` | `D:/AgentABC/canal` | 约 520 |
| 06 | `06-dbt-架构.md` | `D:/AgentABC/dbt` | 约 540 |
| 07 | `07-metricflow-架构.md` | `D:/AgentABC/metricflow` | 约 510 |
| 08 | `08-debezium-架构.md` | `D:/AgentABC/debezium` | 约 540 |
| 09 | `09-parser-架构.md` | `D:/AgentABC/parser` | 约 420 |
| 11 | `11-QwenPaw-Data-架构.md` | `D:/AgentABC/QwenPaw-Data` | 约 500 |
| 12 | `12-hermes-agent-架构.md` | `D:/AgentABC/hermes-agent` | 约 760 |
| 13 | `13-deepseek-harness-架构.md` | `D:/AgentABC/deepseek-harness` | 约 760 |
| 15 | `15-nanobot-架构.md` | `D:/AgentABC/nanobot` | 约 420 |

### 1.2 方法

1. **路径与行号自动化核查**：用脚本抽取每份文档中所有 `` `路径:行号` `` 与 `` `路径:行号-行号` `` 形式的反引号引用，按仓库根解析（支持 `.../` 缩写与省略前缀的短路径），统计"文件是否存在""行号是否越界"。共覆盖 **767 个去重路径点位**、逐条出现约 1000 处。
2. **源码行内容比对**：对每处 `文件:行号`，打印该行实际源码内容，与文档描述逐个比对，区分"文件对但行号指向装饰器/空行/docstring/同名异包文件"。
3. **标识符存在性核查**：抽取文档中反引号包裹的类名/函数名/配置项，在仓库全量文本中精确检索；不存在者逐一回源确认是占位符、外部项目符号，还是编造的标识符。
4. **主链路完整性核查**：从入口点逐跳核对文档 §4 列出的调用链，检查每跳类/方法是否真实存在、方向是否与源码一致、是否遗漏关键中间层。
5. **规模与版本核查**：对文件数、行数、模块数、体积、版本号、commit 等可测陈述用 `os.walk`/`git`/`grep` 复算。

每份文档修订后均重新执行第 1 步复查：**13 份文档正文（不含「修订记录」）残留无法解析的路径引用仅 3 处**，均为已知的跨仓库或内部类写法（见 §5.4）。

---

## 二、总表

| # | 文档 | 核验路径点位（去重） | 修订后失效路径 | 修订条目 | 失效/错位（修订前，含重复引用） | 主要问题 | 修订程度 |
|---|---|---|---|---|---|---|---|
| 01 | Airflow | 86 | 0 | 6 | 6 | 行号指向相邻行/空行（配置、UI 依赖、pyproject、序列化函数） | 小修 |
| 02 | DolphinScheduler | 61 | 1（内部类名写法） | 19 | 19 | 3 个 `META-INF/services` 文件实际不存在（改用 `@AutoService`）；行号漂移；模块/体积/枚举计数 | 中修 |
| 03 | Taier | 56 | 1（内部类名写法） | 6 | 11 | `ZkService`/`JobSubmitDealer`/`FlinkClient` 等方法行号 +1；`TaskStatus` 枚举数、`IClient` 方法数 | 小修 |
| 04 | SeaTunnel | 66 | 0 | 13 | 7（+6 处语义） | 入口类写错（`SeaTunnelApplication`→`SeaTunnelClient`）；把 `CoordinatorService` 线程池写成单线程；`SupportMultiTableSource` 不存在；部署路径写错 | 中修 |
| 05 | Canal | 50 | 0 | 19 | 16 | Netty 版本适用范围、proto 真实目录、ZK 根路径、事务缓冲 flush 分支与过滤位置、`startup.sh` 位置 | 中修 |
| 06 | dbt | 64 | 0 | 36 | 24 | `Schedule`→任务图 的归属文件写错（应为 `dbt-tasks-sa/src/graph.rs:199`）；`dbt-docs` 包名/计数；跨仓库误引 `metricflow/converters/expression_utils.py` | 中修 |
| 07 | MetricFlow | 43 | 1（`../dbt/` 跨仓库引用） | 16（覆盖 23 个位置） | 14 | dataflow 节点数 24→23；`NodeEvaluator` 实为 `NodeEvaluatorForLinkableInstances`；时序图 `ENG→ME` 方向缺一层；行号多指向装饰器/空行 | 小修 |
| 08 | Debezium | 50 | 0 | 27 | 38 | `EmbeddedEngine` 类在仓库中不存在（应为 `DebeziumEngine`/`AsyncEmbeddedEngine`）；PG 快照锁模式写错（ACCESS SHARE ≠ ACCESS EXCLUSIVE）；`SchemaOnlySnapshotter` 不存在（实为 `NoDataSnapshotter`）；模块数与体积 | 中修 |
| 09 | parser | 28 | 0 | 20 | 14（+5 处规模） | 体积口径（104MB→89.3MB）；`examples` 计数（1476→1141 `.sql`）；`StarRocks` 双 `.g4`；多处 lexer 行号偏移 | 小修 |
| 11 | QwenPaw-Data | 76 | 0（`bi-xxx` 已改真实示例） | 29 | 29 | `model_config.py` 不存在（实为 `model_config_api.py`）；`core.py` 构造点/中间件注入行号偏移；两处 plan 状态语义（`finish_plan`、`apply_plan_changes`）与源码相反 | 中修 |
| 12 | hermes-agent | 69 | 0 | 17 | 14（+2 编造类/函数） | 编造 `SessionAdmission`、`_append_tool_result`；租约表 `session_turn_leases` 与网关 admission 账本混写；多处 +1/+2 行号 | 小修 |
| 13 | deepseek-harness | 72 | 0 | 39 | 43 | 裸短路径 `agent-loop/index.ts` 等被解析到同名异包文件（已统一补 `packages/...`）；`dsh-web-app` 实际在 `packages/bundle/web-app`；`export`→`flush` 持久化语义；`.ts(x)` 计数 | 中修 |
| 15 | nanobot | 46 | 0 | 8 | 5（+3 处描述） | `run()`、`events.py` 行号偏移；`[all]` extra 不存在；`read_file` 豁免语义；`TurnContext` 字段数 | 小修 |
| **合计** | — | **767** | **3** | **255** | **约 246** | — | 小修 6 / 中修 7 / 未改 0 |

> 说明：修订条目数大于失效数，是因为一条修订常同时覆盖同一错误在多处复现（如 07 的 14 处失效分布在 23 个位置）。

---

## 三、逐份要点

### 3.1 `01-airflow-架构.md`（小修，6 条）

- **§2.1 配置系统**：原引 `config_templates/config.yml:19` 声称是 `core:`/`options:`；实际 `:19` 是空行，`core:` 在 `:20`、`options:` 在 `:22`。已改。
- **§2.1 序列化**：原引 `serialized_objects.py:1766` 为 `_json_schema`；实际 `:1763` 才是 `_json_schema`，`:1766` 是 `serialize_dag`。已拆分标注。
- **§2.1 UI**：`ui/package.json:5` 实为 `"type": "module"`（`dev` 脚本在 `:11`，且含 `--strictPort`）；`codegen` 在 `:17` 而非 `:31`。已改。
- **§2.1/§10 凭据与依赖方向**：`airflow-core/pyproject.toml:142` 才是 `pyjwt`（`:141` 为 `pygments`）；`task-sdk/pyproject.toml:50` 才是 `apache-airflow-core`（`:49` 为 `dependencies = [`）。两处（正文 + 存疑节）均已改。
- **复核通过**：调度主循环 `_run_scheduler_loop:1948`、`_do_scheduling:2149`、`_critical_section_enqueue_task_instances:1278`、`process_executor_events:1447`；dag 解析 `DagFileProcessorManager` 全部 9 个内部函数行号；task-sdk 侧 `run:1752`/`_execute_task:2286`/`finalize:2390`、`ti_update_state:451`；`serialization/definitions/` 恰 12 个模块、`scheduler_job_runner.py` 4637 行等规模陈述全部正确。

### 3.2 `02-dolphinscheduler-架构.md`（中修，19 条）

- **服务注册机制（结构性问题）**：§4 步骤 9、§7 A.4/B.3 及文末对比共 4 处引用 `META-INF/services/org.apache.dolphinscheduler.plugin.task.api.TaskChannelFactory` 等 3 个文件；仓库中**不存在**任何 `META-INF/services` 文件（实测 0 个），实现类改用 `@AutoService(TaskChannelFactory.class)` 编译期生成（全仓 122 处 `@AutoService`，如 `ShellTaskChannelFactory.java:25`）。已改为 SPI 自动生成口径。
- **行号错位 7 处**：`IWorkflowControlClient` 的 `@RpcService` `:30`（import 行）→ `:42`；`WorkflowGraphTopologyLogicalVisitor` 子图裁剪 `:69-78`→`:63-75`；`WorkflowTopologyLogicalTransitionWithTaskFinishLifecycleEventHandler.handle()` `:41`→`:34`；`sendTaskResultAlert()` `:57`→`:63`；`TaskExecutionStatus` 枚举 `:29-38`→`:28-37`；`CommandEngine.run()` `:126`→`:127`；Alert HA 由 `AlertHAServer` 改指 `AlertServer.java:85/:86`（`AlertHAServer.java` 仅 47 行且无该调用）。
- **名称/数值**：`reassignWorkflowInstanceHost` 实为 delegator 的 `reassignMasterHost()`（`:104`）；`TaskExecutorStateTracker`→`ITaskExecutorStateTracker`；`idStep/fetchSize` 归属 `CommandFetchStrategy.IdSlotBasedFetchConfig`（`:49-50`）；根 pom 模块 27→26（`pom.xml:36-61`）、体积 174MB→94MB、`CommandEngine` 94→222 行、loadbalancer 5→4 个实现、状态机具体类 12/13→各 10 个、task-plugin 约 40→36 子模块/37 种 TaskChannel。
- **遗留**：`onSucceedEvent():233`、`WorkflowScheduleTrigger.java:45` 为多行签名的末行（起始行分别是 231/43），已在修订记录中说明，未强行改号。

### 3.3 `03-Taier-架构.md`（小修，6 条）

- `ZkService.zkRegistration()` `:176`→`:177`（`:176` 为空行）；`JobSubmitDealer.submitEngineJob()` `:348`→`:349`；`FlinkClient.deployJobCluster` `:449`→`:450`；`retryNum++` `:235`→`:236-237`。
- **计数**：`TaskStatus` 原写 26 个值，实际 23 个枚举常量（`taier-worker/taier-worker-api/.../pluginapi/enums/TaskStatus.java`）；§7A `IClient` 方法数 11→12。
- **复核通过**：§4 全链路 MasterListener:58 → JobGraphBuilderTrigger:44/48/64 → CycleJobBuilder:56/67 → AbstractJobBuilder:91/178/219 → ScheduleJobService:112/191/207/223 → ScheduleActionService:141/151 → JobDealer:159/204/341 → GroupPriorityQueue:55/79/108/147 → JobSubmitDealer:334/353/360 → WorkerOperator:91/96/101 → JobStatusDealer:120/161/197/212/221-222，逐跳真实且方向正确；§6 `FailoverStrategy`、`ShardCache` 均真实。
- **未改**：体积"约 58MB"与实际 32MB（不含 `.git`）/50MB（含 `.git`）有出入，因口径不可复现且非事实性结论，按存疑保留。

### 3.4 `04-seatunnel-架构.md`（中修，13 条）

- **入口认错（关键）**：§3.1 原称入口为 `SeaTunnelApplication`；实际 `bin/seatunnel.sh:41` 的 `APP_MAIN="org.apache.seatunnel.core.starter.seatunnel.SeaTunnelClient"`，入口为 `SeaTunnelClient`（`SeaTunnelClient.java:34`）。已改。
- **线程模型**：§2.1/§3.2 原写 Master 上 `MDCExecutorService` **单线程**驱动 job 状态机；实际 `CoordinatorService.java:305-315` 使用 `ThreadPoolExecutor(coreThreadNum, maxThreadNum, …)`，`ServerConfigOptions.java:525-529` 中 `core-thread-num` 默认 10。已改。
- **不存在的类**：`SupportMultiTableSource` 全仓不存在，§7.1 已改为 `getProducedCatalogTables()`；`MultiCatalogTransform`→`AbstractMultiCatalogTransform:41`。
- **路径/命令**：`SeaTunnelServer` 同名的 core-starter 版本仅 36 行，§3.1/§3.3 已补 `seatunnel-engine/seatunnel-engine-server/...` 全路径；§8 `docker/docker-compose.yaml`→`seatunnel-cli/benchmark/docker/docker-compose.yml`；`seatunnel.sh -m master`→`seatunnel-cluster.sh -r master`（`-m` 实为 `--member`）。
- **遗留**：§2.2 模块表漏列 `seatunnel-resource-managers` 等新增模块（未重写，建议补）。

### 3.5 `05-canal-架构.md`（中修，19 条）

- **依赖归属**：§2.1 原把 Netty 4.1.68 算作 admin 面；实际 `CanalAdminWithNetty.java:7` 是 `org.jboss.netty`，`io.netty` 仅见于 `NettySocketChannel` 等 4 个文件（数据面/RDS 下载链路）。`AbstractCanalLifeCycle` 属 `common` 模块，非 Netty3。
- **proto 位置**：实际为 `protocol/src/main/java/com/alibaba/otter/canal/protocol/` 下的 `EntryProtocol.proto`、`CanalProtocol.proto`、`AdminProtocol.proto`（§2.1 原路径 `protocol/src/main/protobuf/CanalEntry.proto` 不存在）。
- **行为语义**：事务 buffer `entries` 赋值在 `:90`（`:38` 是类声明）；四种 flush 分支按 `EventTransactionBuffer:67-87` 实际改写；`checkFreeSlotAt` 用 `min(get, ack)`；事务头尾过滤实际在 `EntryEventSink:99`（原写在 `LogEventConvert`）。
- **配置/路径**：ZK 根节点 `destinations`（`ZookeeperPathUtils.java:41-42`）；`fallbackIntervalInSeconds` 在 `default-instance.xml:131`；过滤键 `canal.instance.filter.black.field`；`startup.sh` 实为 `deployer/src/main/bin/startup.sh`。
- **遗留（建议补写）**：§4 漏 `CanalServerWithEmbedded.start(destination)` 一跳（`:81` 惰性生成、`:137` `instance.start`）；时序图把 `LogDecoder.decode` 画在 `LogEventConvert` 参与者上。

### 3.6 `06-dbt-架构.md`（中修，36 条）

- **结构性归属错误**：§3.3 原把"`Schedule`→任务图"归给 `compilation_pipeline.rs:48` 的 `schedule_phase`（该函数只返回 `Schedule<String>`）；实际建图是 `crates/dbt-tasks-sa/src/graph.rs:199` 的 `build_phased_task_graph`（返回 `DiGraph<Arc<dyn Task>, ()>`）。已改。
- **跨仓库误引**：`metricflow/converters/expression_utils.py` 在本仓库不存在，属独立 `dbt-labs/metricflow` 仓库；§11 已改口径并指向本仓 `crates/dbt-metricflow/src/lib.rs:3838`。
- **名称/计数**：仓库无 `dbt-docs` 包，实际为 `crates/dbt-docs-core`、`crates/dbt-docs-server`（含 `web/` 的 `dbt-docs-web`）；`AdapterType` 方言数 17→**18**（`dbt-adapter-core/src/lib.rs:50-94`，已复算）；`pyproject.toml:10` 才是 Rust classifier；`main_impl.rs:33` 才是 `FS_DEFAULT_MAX_BLOCKING_THREADS`。
- **行号**：`driver.rs` `write_metadata` :143→:133；`task_runner.rs` `visit_parallel` :394→:398；`default.rs` `try_get_compiled_sql` :64→:62；`resolver.rs` `into_typed_with_jinja` :822→:843；`v12.rs` `into_map_compiled_sql`/`StreamingYamlMap` :96/:52→:90/:23；`schedule.rs`、`materialize.rs`、`adapter_impl.rs` 等二级行号同步修正。
- **规模**：82MB→55.6MB（排除 `.git/target/node_modules`），文件数 4868 与原文一致；仓库确认无 `target/`，`manifest/run_results/catalog` 均为运行期产物（已补"运行后生成"口径）。
- **遗留**：未覆盖 `dbt-docs-core`、`dbt-adapter-engine`、`dbt-lineage-core` 等实际 crate（88 个 crates），建议单独补一节。

### 3.7 `07-metricflow-架构.md`（小修，16 条 / 23 个位置）

- **节点数**：全文 4 处"24 种 DataflowPlanNode"→**23 种**。已复算：`metricflow/dataflow/nodes/` 共 24 个 `.py`，其中 `__init__.py` 无类，`DataflowPlanNode` 子类恰 23 个。
- **类名**：`NodeEvaluator` 不存在，实际类为 `NodeEvaluatorForLinkableInstances`（`node_evaluator.py:153`，`evaluate_node:390`）。
- **跨仓库路径**：`crates/dbt-schemas/.../semantic_manifest.rs` 在本仓库不存在，已改为 `../dbt/...:16`（`pub struct SemanticManifest`）。
- **行号**：`CHANGELOG.md:11`→`:8`；`semantic_manifest_lookup.py:39`→`:25`/`:28`（已复核 `class` 在 25、`__init__` 在 28）；`dfs_me_planner.py:39/:47`→`:37`/`:52`；`optimization_levels.py:15/:26`→`:16`/`:27`；`sql_plan.py:32`→`:28`；`attribute_recipe.py:29`→`:30`；`sg_linkable_spec_resolver.py:50`→`:54`；`metricflow_engine.py:526`→`:528`；`sql_client.py:18`→`:15`。
- **时序图**：原 `ENG-->>ME: build_plan(...)` 与源码相反（`metricflow_engine.py:620` 调 `_dataflow_plan_builder.build_plan`，`dataflow_plan_builder.py:279` 才调 `me_planner.build_plan`），已补 `ENG→DF→ME` 两条边。
- **依赖口径**：§11 明确 MetricFlow 解析 measure 表达式用的是 sqlglot（`requirements-files/requirements.txt:12`），不依赖本仓 `parser`。

### 3.8 `08-debezium-架构.md`（中修，27 条）

- **不存在的类**：`EmbeddedEngine`（4 处）在仓库中不存在；引擎契约是 `DebeziumEngine`（`DebeziumEngine.java:46`，工厂 `:415`），实现为 `AsyncEmbeddedEngine`（`:86`）。`SchemaOnlySnapshotter` 不存在，实际为 `NoDataSnapshotter`（`debezium-connector-common/.../snapshot/mode/NoDataSnapshotter.java:14`）。
- **语义错误**：PG 快照锁原写 `LOCK TABLE … IN ACCESS EXCLUSIVE MODE`；实际 `debezium-connector-postgres/.../snapshot/lock/SharedSnapshotLock.java:33` 为 `LOCK TABLE %s IN ACCESS SHARE MODE;`（Oracle 版才是 `ROW SHARE MODE`）。已改。
- **服务注册**：`META-INF/services/org.apache.kafka.connect.connector.Connector` 不存在；真实文件为各 connector 模块下的 `META-INF/services/org.apache.kafka.connect.source.SourceConnector`（内容为对应 `XxxConnector`）。§7.1 已改。
- **规模/构建**：根 `pom.xml:7` 是 jboss-parent、版本在 `:13`；模块 31→36（`pom.xml:217-254`）；体积 50MB→39MB。
- **行号**：`BaseSourceTask` 76→80、`poll()` 348→359、`emitCreateRecord` 63→67、`ChangeEventSourceCoordinator` 134→136、`dispatchDataChangeEvent` 250→278、`doPoll` 441→407、`createChunkedDataEvents` 583→587 等 18 处逐条校正。
- **未改**：若干"附近/起"的区间表述（如步骤 13 `:300` 起）未强行精确化。

### 3.9 `09-parser-架构.md`（小修，20 条）

- **规模**：原"1768 文件 / 104MB（含 `.git`）"→实测不含 `.git` 为 1768 文件 / 89.3MB，含 `.git` 为 1797 / 100.2MB（已复算，`.git` 29 个文件）。已改。
- **样例计数**：`examples/` 原"1476 个 `.sql`"→全仓 16 个 `examples/` 目录共 1502 个文件（`.sql` 1141、`.cql` 45、`.js` 309、`.tree` 6、`.md` 1）。已复算，按方言逐目录求和与原文分布（`plsql` 342、`mongodb` 309、`postgresql` 218）一致。
- **语法文件**：`starrocks` 实为 `StarRocksSQL.g4` + `StarRocksSQLLex.g4` 两个 `.g4`，非"单文件语法"。
- **行号**：`mysql_base_lexer.go` 10→9、16→17（3 处）；`redshift_lexer_base.go` 9→10、`pushTag` 15→17、`isTag` 19→21、`popTag` 27→28；PG 测试 `:53→:49` 等 6 处；`CLAUDE.md:37→:33`；`postgresql/Makefile:7→:6-8`。
- **陈述**：§6"每方言都有 `examples/*.sql`"→"多数方言"（`cql` 用 `.cql`、`mongodb` 用 `.js`、`partiql` 无 `examples/`）；§8 断点由不存在的 `stream.Fill()/GetAllTokens()` 改为 `:56` 建流后遍历 `lexer.GetAllTokens()`。
- **复核通过**：16 方言 `package` 与目录一一对应、方言零横向依赖、156 个 `.go` / 257 万行 / 35 个 `.g4`、`Root()` 行号 1908/8104、CI `ALL_PARSERS` 16 项均与源码一致。

### 3.10 `11-QwenPaw-Data-架构.md`（中修，29 条）

- **不存在的文件**：§7 引用 `context_manager/api/model_config.py`；该文件不存在，真实模块为 `packages/qwenpaw-data-context/src/context_manager/api/model_config_api.py:27`（`APIRouter(prefix="/api/system/model-config")`）与 `context_manager/model_config_store.py`。已改。
- **两处语义与源码相反**：① `finish_plan` 并不校验"无 in_progress"，而是把未终态节点统一置为 `done`/`abandoned`（`state.py:720-723`）；② `apply_plan_changes` 只重置**下游**节点，不含被修订节点自身（`mark_downstream_todo`，`task_graph.py:354`）。
- **行号**：`core.py:235`→`:248`（Agent 构造点）、`toolkit.py:310`→`:315`（`skills_or_loaders`）、`chats.py:21`→`:22`、`hint.py` 三处（`:19→:21`、`:41→:48`、`:66→:65`）、`sql_artifact.py:40→:42`、`settlement.py:15→:16`、`chat.py:31→:30`、`cm_server.py:268→:269`、`cm_api.py:1403→:1404`、`toolkit.py:266→:268` 等。
- **短路径歧义**：`registry.py:12` 实际应为 `host/core/registry.py:32`（`QwenPawDataHostRegistry.get()`），原写法易与 `graph/adapters/registry.py` 混淆。已补全。
- **计数**：`SKILL.md` 31→32（31 个挂载 + 1 个根 CLI skill）；MCP 工具 22→20（其中元数据查询 15）；`algo` 4,000→9,681 行；`graph+knowledge` ~15k→25,158 行；`Python 3.12`→`≥3.11`（`pyproject.toml:20` 为 `requires-python = ">=3.11"`）。
- **占位符**：`bi-xxx/SKILL.md` 改为真实示例 `atomic/bi-anomaly-detection/SKILL.md`。

### 3.11 `12-hermes-agent-架构.md`（小修，17 条）

- **两个编造标识符**：`SessionAdmission`（仓内不存在，准入门实际是 `TurnLeaseAdmission`，`agent/turn_facade_lease.py:260`，租约对象 `DurableTurnLease:34`）；`_append_tool_result`（不存在，实际为 `make_tool_result_message()`，`agent/tool_dispatch_helpers.py:448` + `messages.append`，`agent/tool_executor.py:1162`）。均已替换。
- **账本混淆**：§4 步骤 1 把"SQLite 里的 admission 行"当作 turn 租约；租约实际写入 `session_turn_leases`（`hermes_state_common.py:623`），原 `:511` 是 queue/steer/redirect 账本。已改。
- **行号**：`conversation_loop.py` `:1648→:1650`、`:1701→:1702`；`turn_iteration_prep.py` `:166→:167`；result dict `:690-721→:687-721`；transports `_REGISTRY :17→:16`、`get_transport :25→:26`；`registered_api_modes :41→:44`。
- **短路径补全**：`registry.py`→`tools/registry.py:121`/`:178-201`/`:721-728`；`base.py` 3 处补为 `gateway/platforms/base.py`。
- **确认未改**：`~/.hermes/.env`、`~/.hermes/config.yaml` 是运行时配置路径而非仓库文件（仓库仅有 `cli-config.yaml.example`），正文表述正确；`_digest/AI-Agent核心摘要.md` 为外部参考，未改。
- **遗留**：建议单独补一节并发语义，区分网关 `session_admissions` 与 turn 租约（本次未重写）。

### 3.12 `13-deepseek-harness-架构.md`（中修，39 条）

- **路径体系（最大问题）**：大量裸短路径（`agent-loop/index.ts`、`app-boot/index.ts`、`llm/types.ts`、`tools/index.ts`、`session/index.ts`）会被解析到同名异包文件；已统一补全为 `packages/core/agent-loop/src/…`、`packages/boot/app-boot/src/index.ts`、`packages/llm/llm/src/types.ts`、`packages/core/tools/src/index.ts`、`packages/core/session/src/index.ts`。`dsh-web-app`→`packages/bundle/web-app/cordis.patch.yml`。
- **持久化语义**：`SessionPersistence` 五方法原写 `export`，实际是 `flush()`（`packages/session/session-persistence/src/index.ts:180`）；`append` 原写"先持久化再返回"，实际 `handle.ts:86-91` 只保证 accepted/ordered/visible，崩溃安全由 `flush` 屏障负责。已改。
- **事实性指标**：`package.json:6` 是 `"type": "module"`（`packageManager` 在 `:7`）；Node `engines` `:8-10`；根 `package.json` 无 `repository`（应说"各子包"）；`.ts(x)` 5101→5751（5101 `.ts` + 650 `.tsx`）；headless `run()` 40→94 行；teardown 47→48 行、abort 融合 60→67 行。
- **Cordis**：`pnpm link:` 覆盖说法有误，实际是 workspace 成员（`vendor/cordis/package.json:4`）；`events.ts:256`→`:288`；`agent-loop/index.ts:884-891`→`:884-887`。
- **复核通过**：§4 全链路 boot 1200 → session prepare 1143 → agent-loop 750/turn 298/step 400 → llm 956/1166 → tools 551/60/122 → 落盘 798 逐跳成立（已抽查 `inbox.ts:167 splice(`、`index.ts:750 createAgent`、`agent.ts:122 constructor` 等）。
- **遗留**：`sdk-minimal` 文字顺序与 YAML 实际行序不同（可能按依赖序描述），未改。

### 3.13 `15-nanobot-架构.md`（小修，8 条）

- **行号**：`events.py:24/:42/:36`→实际类在 `:20`（Inbound）、`:39`（Outbound）、`session_key` 在 `:33-35`；`loop.py:846`→`run` 实为 `:840`；`loop.py:496`→工具注册日志在 `:501`。
- **描述**：§3.1 核心 9209 行口径补 `bus`（`core_agent_lines.sh` 的 `core_total` 含 bus）；`system prompt` 补 `recent_history`，7 段→8 段；§6.2 `read_file` 是"工具结果落文件"豁免（`runner.py:73` 的 `_TOOL_RESULT_OFFLOAD_EXEMPT_TOOLS`），不是 microcompact 排除项；`TurnContext` 字段 30 多→26（`loop.py:97-131`）。
- **命令**：§8 `pip install -e .[all]`→`pip install -e .`（`pyproject.toml:67-108` 无可选依赖 `all`）。
- **复核通过**：§4 渠道→总线→dispatch→状态机→runner→模型→工具→出站的每步入口与行号真实；597/604、381 py、226 tests、16356/7468/9209 等规模数字一致。

---

## 四、体例一致性问题汇总

### 4.1 章节骨架

- **一致**：13 份均采用 `1. 一句话定位` → `2. 技术栈与工程结构` → `3. 整体架构` → `4. 端到端主链路` → `5. 核心代码路径清单` → `6. 关键设计点` → `7. 扩展点` → `8. 本地跑起来 / 调试入口` → `9. 阅读路线` → `10. 未覆盖 / 存疑`，主链路均具备"入口 → 调用链 → 落地"三段式。
- **不一致**：
  1. **附录编号**：`04/05/06/07` 用 `11. …` 编号；`02/03/08/09/11/15` 的同类附录无编号（如"与 Airflow 的对比""在你的数据栈里的位置"）；`01/12/13` 无附录。建议统一为"附录 A/B"或不编号。
  2. **重点分级**：12 份使用 `★/★★/★★★`，`15-nanobot` 使用 `P0/P1`。语义相近但不可直接比较，建议统一。
  3. **主链路小节编号**：`07` 混用"步骤 1–8"与 `4.9/4.10`；其余文档为 `4.1、4.2…` 顺序编号。

### 4.2 「修订记录」体例（本次已统一）

- 13 份均已在文末追加 `## 修订记录`；`02` 原为「修订记录（源码核对）」、`11` 原为「修订记录（2026-11-04 复核）」，**已统一标题**。
- 表头统一为 `| # | 位置 | 原表述 | 核实结果（源码依据） | 处理 |`；`02` 原为 4 列语义（原文/改为/依据），**已调整列序与表头**；`11` 已补"（源码依据）"与摘要引言。
- 修订记录均含"核验通过、未改动的关键判断"与"未解决/存疑"（部分文档为简述），格式基本一致。

### 4.3 路径写法

- 文首统一用 `` `D:/AgentABC/<项目>` ``；正文统一用"仓库根相对路径 + `:行号`"。
- **缩写 `.../` 广泛使用**（02/03/04/05/08 等 Java 项目最多），优点是短，缺点是跨模块同名文件有歧义。本次保留原写法，仅对会歧义或失效的补齐全路径（`13` 全部补齐、`11`/`12` 补齐 4 处、`04` 补齐 1 处）。
- 建议后续统一规则：**首次出现给全路径，重复引用可缩写**；并在文首声明"路径均相对仓库根"。

### 4.4 图表风格

- 每份 2–3 个 mermaid（`flowchart` + `sequenceDiagram`），节点内普遍用 `<br/>` 换行并把 `文件:行号` 写进节点，风格一致。
- 少数图内参与者名与实际类名不一致（`05` 的 `LogDecoder`→`LogEventConvert` 参与者），已在修订记录标注，未重绘。

---

## 五、问题定级与优先级建议

### 5.1 结论：无整篇重写必要

13 份文档均具备完整主链路、可核对代码路径与设计分析，不存在"只有目录罗列 / 无调用链 / 代码路径大面积失效"的文档。修订后正文残留无法解析的路径仅 **3 处**：

| 文档 | 残留引用 | 性质 |
|---|---|---|
| 02 | `CommandFetchStrategy.IdSlotBasedFetchConfig` | Java 内部类写法，文件 `CommandFetchStrategy.java` 存在 |
| 03 | `FailoverStrategy.FaultTolerantDealer` | Java 内部类写法，文件 `FailoverStrategy.java` 存在 |
| 07 | `../dbt/crates/dbt-schemas/.../semantic_manifest.rs` | 跨仓库引用，已注明"dbt 仓库" |

### 5.2 建议补写（P1，人工）

| 文档 | 缺口 | 依据 |
|---|---|---|
| `06-dbt` | 未覆盖 `dbt-docs-core`、`dbt-docs-server`、`dbt-adapter-engine`、`dbt-lineage-core` 等实际 crate（仓库共 88 个 crates） | `crates/` 目录实测 |
| `05-canal` | §4 漏 `CanalServerWithEmbedded.start(destination)`（`:81` 惰性生成、`:137` `instance.start`）一跳；时序图参与者错位 | `CanalServerWithEmbedded.java` |
| `04-seatunnel` | §2.2 模块表漏 `seatunnel-resource-managers` 等模块 | 根 `pom.xml` |
| `12-hermes-agent` | 缺并发语义小节：网关 `session_admissions` 与 turn 租约 `session_turn_leases` 被混写 | `hermes_state_common.py:623` |
| `02-dolphinscheduler` | `onSucceedEvent`、`WorkflowScheduleTrigger` 等行号仍指向多行签名末行，建议统一改指函数起始行 | 修订记录"未改"项 |

### 5.3 建议统一（P2，可批量机械处理）

1. `15-nanobot` 的 `P0/P1` → `★` 分级体系。
2. 附录编号统一（`11.` vs 无编号）。
3. `07` 主链路小节编号统一为 `4.1…4.N`。
4. 文首增加一句"路径均相对仓库根，行号以 commit `xxx` 为准"，减少跨版本歧义。

### 5.4 存疑与未核实项（保留原状，已在各文档登记）

- 体积口径类（`03` 58MB、`13` 198MB、`15` 85MB）无法复现统一口径（磁盘占用 vs 逻辑大小 vs 含 `.git`），未强行改数。
- `06` 的 `sdf-frontend` 仅见于 `Cargo.toml:199` profile 段，`crates/` 下无同名目录；`LakeCompute` 运行时形态未能从代码确定。
- `13` 的 `sdk-minimal` 文字顺序与 YAML 实际行序不同，疑为按依赖序描述。
- `09` 的 `partiql-tests` 子模块仅见于 `partiql/README.md:6`，仓库无 `.gitmodules`。

---

## 六、审查产出与复核记录

- 修改文件：上述 13 份 `.md`（仅追加「修订记录」与就地纠错，未改名、未改章节编号、未删除原有分析）。
- 新增文件：本报告 `REVIEW-已有文档-审查报告.md`。
- 未触碰：`_arch` 下编号 10/14/16/17/18/19 文档、`_digest`、任何子项目源码。
- 复核方式：修订后重新跑路径解析（767 个点位，残留 3 处已知例外）+ 抽查关键类名/行号（`SeaTunnelServer:216`、`graph.rs:199`、`NoDataSnapshotter:14`、`SharedSnapshotLock:33`、`TurnLeaseAdmission:260`、`inbox.ts:167` 等）逐条回源确认。
