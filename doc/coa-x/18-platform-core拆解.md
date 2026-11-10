# 18 platform-core 拆解（M3a 第三条判据的落地清单）

> 日期：2026-11-10
> 范围：只读核对 `packages/platform-core` 29 个顶层条目、8099 桥的 KERNEL 路由表、契约归属与运行中的容器；**不搬代码、不开 worktree、不建 PR**。
> 本文回答三件事：① 29 个条目里哪些是活代码；② 43 条 KERNEL 路由归哪个限界上下文；③ 按什么顺序搬，哪些不能与 P8 并行。

## 0. 摘要

| 结论 | 数字 / 事实 |
|---|---|
| 判据已改 | M3a 第三条从「目录不存在」改为三条：入口不再 import / 活代码已按限界上下文迁入 COA 包 / 目录只剩归档物（`00-总计划.md` §5.2 第 3 步，`17-M3a出口盘点.md` §0.5） |
| 29 个条目分档 | **活 4**（`src/`、`config/`、`reasoner/`、`pyproject.toml`）、**半活 2**（`tests/`、`web/`）、**非运行期 23** |
| KERNEL 路由 | **43 条**：术语/别名 1、数据字典 5、指标卡 2、推理 2、本体生命周期 15、事实账本 10、实体与溯源 2、指标详情 1、浏览树/实例 2、质量 1、可答性 1、文档摄入 1 |
| 契约归属 | 38 条落 `ControlPlaneService`（含 `dictionary` / `facts` / `ontologygraph` 模块）、3 条落 `MetricService`、1 条落 `DataLayerService` |
| 搬迁顺序 | **R1 迁移链**（先，但等 P8）→ **R2 reasoner**（次，不可与 P8 并行）→ **R3 KERNEL 路由**（最后） |
| 核心风险 | 目录不是死代码，是 8099 的最大后端；硬删 = 43 条路由退化 503、迁移链断源、7879 失去构建源 |

## 1. 判据与机械检查

| # | 判据 | 机械检查 | 当前 |
|---|---|---|---|
| 1 | coa 的任何入口都不再 import `platform-core` | 对 `packages/*/src`、`doc/coa-x/tools/*.py`、`coa-runtime` 组合根 `grep -n "platform_core"`；命中即不满足 | **不满足**：起栈脚本把 `packages/platform-core/src` 插进 `sys.path`（`coa_api_local.py` L54）并 import `platform_core.*`（L878–881、L955–962、L1781）；`local_bootstrap.py` 同；`packages/local-providers/tests` import 其适配器 |
| 2 | 活代码已按限界上下文迁入 COA 包 | 每块（迁移链 / reasoner / 43 条路由）≥1 次真跑通，且新旧响应逐字段一致 | **不满足**：三块都还在原目录 |
| 3 | 目录只剩归档物 | `Test-Path packages/platform-core` = `True` 但 `Get-ChildItem` 只剩 README/历史脚本/旧配置；`grep -rn "platform_core" --include=*.py --include=*.toml --include=*.yml` 在代码与配置中 0 命中 | **不满足**：29 个条目里 4 个是运行物，`src/` 是包本身 |

判据为什么改、原判据错在哪，写在 `17-M3a出口盘点.md` §0.5，本文不重复；这里只给落地清单。

## 2. 29 个条目的三档清单

### 2.1 汇总

| 档 | 条数 | 条目 |
|---|---:|---|
| **活**（删了会掉功能或起不了栈） | 4 | `src/`、`config/`、`reasoner/`、`pyproject.toml` |
| **半活**（有代码在跑，但不在 8099 主路径上） | 2 | `tests/`、`web/` |
| **非运行期**（构建、起栈、种子、日志、文档） | 23 | `data/`、`seed/`、`fuseki/`、`rdfs/`、`scripts/`、`examples/`、`freeze-manifests/`、`logs/`、`.lock/`、`Dockerfile`、`docker-compose.yml`、`docker-compose.acceptance.yml`、`docker-compose.oxigraph-host.yml`、`requirements.txt`、`platform.example.yaml`、`.env`、`.env.example`、`.dockerignore`、`.gitignore`、`OPEN-QUESTIONS.md`、`README.md`、`RUN.md`、`WORKLOG.md` |

### 2.2 逐条

| # | 条目 | 档 | 证据 | 处置建议 |
|---:|---|---|---|---|
| 1 | `src/` | 活 | 起栈脚本插 `sys.path` 并 import；43 条 KERNEL 路由由它承载；`local_bootstrap` 跑它的 `sql/` 迁移 | 拆成三块迁：迁移链 → R1；路由 → R3；适配器随端口实现走 |
| 2 | `config/` | 活 | `authoritative-8080.yaml` 被起栈脚本当生命周期配置读（`_LIFECYCLE_CONFIG`，`coa_api_local.py` L506） | 随 R3 一起迁；先确认它是否只服务 8080 语义，若是则归档进 `examples/` |
| 3 | `reasoner/` | 活 | 7879 容器 `coa-local-reasoner`，镜像 `agent-reasoner:0.1-s5`，`docker history` 显示 `COPY app.py /app/app.py` | **R2** 迁到 ontology-engine 侧，重建镜像 |
| 4 | `pyproject.toml` | 活 | 定义包与 `platform` CLI；测试用 `pip install -e` 路径 | R1/R3 完成后随目录归档；期间不能先删 |
| 5 | `tests/` | 半活 | 随包单测，import 本包；`packages/local-providers/tests` 也 import 其适配器 | R3 完成后按块迁到归属包的测试目录，遗留的归档 |
| 6 | `web/` | 半活 | 被 `api.py` 挂到 `/ui`；8099 桥不代理 `/ui`，当前无入口 | 直接归档（老 UI，产品入口只有 `packages/web-app`） |
| 7 | `data/` | 非运行期 | docker 栈的挂载数据目录；本地栈走 host 进程 + 独立 work 目录 | 归档 |
| 8 | `seed/` | 非运行期 | 8080/acceptance 的种子（ontology / shapes）；本地 `shapes_dir` 被桥指到临时目录 | 若 P2 的 SHACL 闸门要复用，先复制到归属包再归档（M3b 议题） |
| 9 | `fuseki/` | 非运行期 | Fuseki 容器配置；本地图库是 Oxigraph | 归档 |
| 10 | `rdfs/` | 非运行期 | 推理 profile / 规则资产，随 8080 镜像用 | 归档；若 reasoner 需要，并入 R2 |
| 11 | `scripts/` | 非运行期 | 旧栈起停脚本 | 归档 |
| 12 | `examples/` | 非运行期 | 示例配置 | 归档 |
| 13 | `freeze-manifests/` | 非运行期 | 冻结清单，测试比对用 | 归档 |
| 14 | `logs/` | 非运行期 | 旧栈运行日志 | 归档（不入库） |
| 15 | `.lock/` | 非运行期 | 依赖锁定目录 | 归档 |
| 16–29 | `Dockerfile`、3 个 `docker-compose*.yml`、`requirements.txt`、`platform.example.yaml`、`.env`、`.env.example`、`.dockerignore`、`.gitignore`、`OPEN-QUESTIONS.md`、`README.md`、`RUN.md`、`WORKLOG.md` | 非运行期 | 旧栈构建/起栈/文档 | `Dockerfile` 若被 8080 退役前复用则保留到退役当天；其余归档 |

### 2.3 `src/` 内部的活模块（模块级 import 证据）

| 模块 | 谁在用 | 迁往 |
|---|---|---|
| `api.py` | 起栈脚本 `create_app`；43 条路由的实现 | 按路由域拆（R3） |
| `assembly.py` / `config.py` / `ontology_init.py` | 起栈脚本初始化 | control-plane 的启动装配 |
| `catalog.py`（`introspect_pg`） | 桥的 catalog 同步（L955） | control-plane / metadata store |
| `dictionary_api.py` | 桥直接调用（L956）；F60–F66 | control-plane（`ControlPlaneService` 字典域） |
| `term_api.py` | `api.py` 模块级 import；F58/F59 | control-plane |
| `metric_external.py` | `api.py` 模块级 import；F54–F57 | metric-service |
| `answerable.py` | `/answerable` 路由；F76/F79 | data-layer（`DataLayerService`） |
| `healthboard.py` | 桥 `/system-health`（L1781） | control-plane / 运行观测 |
| `errors.py` | 桥的错误映射 | 迁到 `coa-common` 或端口层 |
| `adapters/metadata_pg.py` | 桥的库版本闸 + `local_bootstrap` 迁移 | **R1** |
| `adapters/ontology_pg.py` 等 | `assembly` 装配 | control-plane |
| `impact.py` | `_governance_impact` 内联可用；`/ontology/impact` 未在桥登记 | 随 F107 / P13 |
| `sql/V*.sql`（至 V48） | `local_bootstrap` 迁移；`SUPPORTED_SCHEMA_VERSION` 闸 | **R1** |

## 3. 43 条 KERNEL 路由的领域归属

来源：`doc/coa-x/tools/coa_api_local.py` L549–L695（`KERNEL` 路由表）。契约归属按 `models/src/main/smithy` 实测。

| 领域 | 条数 | 路由组（简写） | 契约归属 | 搬迁目的地 |
|---|---:|---|---|---|
| 术语 / 别名 | 1 | `ListTerms` | `ControlPlaneService`（`dictionary` 模块，`control-plane.smithy` L18 / L271） | `packages/control-plane` |
| 数据字典 | 5 | 列表 / 详情 / 视图 / 注释覆盖 / 刷新 | 同上 | `packages/control-plane` |
| 指标卡 | 2 | `GetMetricCard`、`GetMetricFamily` | `MetricService`（`metric-catalog.smithy`） | `packages/metric-service` |
| 推理 | 2 | 物化、状态 | `ontologygraph`（折进 `ControlPlaneService`）；算力在 7879 | 路由进 `control-plane`，算力留 `reasoner`（R2） |
| 本体生命周期 | 15 | 版本 4、导入、提案 3、发布、回滚、事件、校验、bundle 3 | `ControlPlaneService`（`ontologygraph`） | `packages/control-plane` |
| 事实账本 | 10 | 事实 / 冲突 / 批量 / 撤回 / 恢复 / 事件 | `ControlPlaneService`（`facts.smithy`） | `packages/control-plane` |
| 实体与溯源 | 2 | 实体、PROV | `ontologygraph`（折进 `ControlPlaneService`） | `packages/control-plane` |
| 指标详情 | 1 | `GetMetric` | `MetricService` | `packages/metric-service` |
| 浏览树 / 实例 | 2 | 浏览树、类下实例 | `ontologygraph`（折进 `ControlPlaneService`） | `packages/control-plane` |
| 质量 | 1 | `GET /answer/quality` | **无契约**（P14 补 `ListAnswerQualityRuns`） | `packages/control-plane`（运行观测） |
| 可答性 | 1 | `CheckAnswerable` | `DataLayerService`（`data-layer.smithy` L44） | `packages/data-layer` |

**归属结论**：38 → `control-plane`，3 → `metric-service`，1 → `data-layer`。所以 R3 的主战场是 `packages/control-plane`，不是每个服务各摊一点。

## 4. 三段搬迁顺序

| 段 | 内容 | 顺序 | 前置依赖（硬） | 不可并行的包 |
|---|---|---|---|---|
| **R1 迁移链** | `adapters/metadata_pg.py`（含 `SUPPORTED_SCHEMA_VERSION` 闸）+ `sql/V*.sql`（至 V48）+ 迁移运行器 | **先**，但**等 P8** | P8 要在同一条链上加 **V47**（`import_batch.namespace_id`）并改闸门；两边同时改 = 冲突 + 基线漂移 | **P8**（明确不可并行） |
| **R2 reasoner** | `reasoner/app.py` + `Dockerfile` + 7879 容器重建 | **次** | 需 R1 完成后才有稳定的库版本基线；重建镜像要重启 7879，期间推理物化不可用 | **P8**（拍板不可并行；同一时刻只允许一个包动 platform-core 目录） |
| **R3 KERNEL 路由** | 38 条 → `control-plane`、3 条 → `metric-service`、1 条 → `data-layer` | **最后** | 需 R1 提供迁移后的 schema；每条路由要有「新旧响应逐字段一致」的实证 | 无（但每批最多 1 个领域，避免大爆炸合并） |

> **「不可与 P8 并行」的准确含义**（2026-11-10 拍板）：R1/R2 都要改 `packages/platform-core` 内的文件，而 P8 的 V47 迁移落在同一条链上；并行会让 P8 的合并基线与迁移版本号来回漂移。这是**排期约束**，不是技术不可能。

### 4.1 R1：迁移链搬到哪里（建议，未动手）

**建议：`packages/control-plane/src/coa_control_plane/platform_db/`**（新增子包），迁移运行器一并进去，`local_bootstrap.py` 只保留「调用 + 本地参数」：

- `platform_db/migrations/V*.sql`（从 `platform-core/src/platform_core/sql/` 原样搬，不重写）
- `platform_db/migrate.py`（`MetadataPg` + 版本闸 + `migrate()`）
- `platform_db/README.md`（版本号规则、禁用回填、V47 归 P8）

**为什么不放 `metadata_store/`**：`packages/control-plane/src/coa_control_plane/metadata_store/__init__.py` 已经存在，但它是 **SMUS/DataZone 元数据客户端的再导出**（`MetadataStoreClient`、`SMUSClient`、`AssetResult` 等），与 PG 迁移链不是一个东西；同名混放会让「SMUS 客户端」和「平台库 schema」搅在一起。

**为什么不新建 `packages/platform-pg`**：那等于把「一个数据库的 schema」升格成并列服务，正好复制 platform-core 长成平台的路径；provider 名里的 `platform-pg` 只是 `MetricIndexPort` 的一个实现名，不是包。

**为什么不是 `coa-runtime`**：`coa-runtime` 是组合根，`MetadataStorePort` 已在 `coa-ports`；端口属端口层，schema 与迁移属 `control-plane` 的存储实现。把 SQL 放进 runtime 会让「运行装配」和「数据演进」绑死。

**为什么迁移运行器不能只留在 `local_bootstrap.py`**：那是 `doc/coa-x/tools/` 下的本地工具，不是产品入口；生产与非本地环境也需要迁移。运行器进包，本地脚本降级为调用方。

### 4.2 R2：reasoner 的落点

- `reasoner/app.py` 实测是 7879 运行中的服务本体（镜像 `agent-reasoner:0.1-s5` 的 `COPY app.py`）。
- 建议落 `packages/ontology-engine` 侧（它已有 8101 与图/本体域），保留独立进程与端口，不并进 8101 进程；镜像改由 ontology-engine 的 Dockerfile 构建。
- `rdfs/` 若被推理 profile 使用，随 R2 一起搬，不要留在归档区。

### 4.3 R3：路由搬迁的验收口径

- 每条路由搬完必须有「旧桥响应 / 新服务响应」逐字段比对（同参数、同命名空间、同数据）；
- 搬迁期间 8099 桥只做转发切换，不重写业务逻辑；
- 每批一个领域，搬完立刻删该领域的 KERNEL 登记，防止两处同时活着。

## 5. 未决与风险

| # | 项 | 说明 |
|---|---|---|
| 1 | 38 条进 `control-plane` 后进程怎么起 | `control-plane` 当前没有本地起栈记录（`ControlPlaneStore` 端口无 provider 实现）；R3 前必须先定「control-plane 本地进程 + 端口 + base URL」 |
| 2 | 指标卡 3 条进 `metric-service` | 指标卡依赖 ontology 类名匹配与外部状态，搬家会碰 `metric_external` 的边界；需单独评审一次 |
| 3 | 质量 1 条无契约 | P14 会补 `ListAnswerQualityRuns`，搬之前先把契约补上，否则搬完还是「无契约的 KERNEL 路由」 |
| 4 | `config/authoritative-8080.yaml` | 名字带 8080，需确认它是「8080 语义配置」还是「通用生命周期配置」；前者随 8080 退役归档，后者随 R3 迁 |
| 5 | 迁移链版本号 | 现 `SUPPORTED_SCHEMA_VERSION` 由 `platform-core` 提供；搬家后必须保证 P8 的 V47 只在一处登记，否则本地库会卡在版本闸 |

## 6. 证据索引

| 事实 | 位置 |
|---|---|
| 29 个条目清单 | `Get-ChildItem -Force packages/platform-core`（2026-11-10） |
| 起栈脚本 import 与 `sys.path` | `doc/coa-x/tools/coa_api_local.py` L54、L878–881、L955–962、L1781 |
| 43 条 KERNEL 路由 | `doc/coa-x/tools/coa_api_local.py` L549–L695 |
| 生命周期配置 | `doc/coa-x/tools/coa_api_local.py` L506 |
| 迁移入口 | `doc/coa-x/tools/local_bootstrap.py`（`MetadataPg` + `migrate`） |
| 7879 镜像来源 | `docker history agent-reasoner:0.1-s5` → `COPY app.py /app/app.py` |
| 契约归属 | `models/src/main/smithy/control-plane.smithy` L14–28、L53–65、L271；`data-layer.smithy` L44；`metric-catalog.smithy` L114 |
| `metadata_store/` 已被占用 | `packages/control-plane/src/coa_control_plane/metadata_store/__init__.py` L6–13 |
| `answer_quality_run` 只写不读 | `platform_core/api.py` L6314；`sql/V45__answer_quality_run.sql` |
| 判据改判理由 | `00-总计划.md` §5.2 第 3 步；`17-M3a出口盘点.md` §0.5 |
