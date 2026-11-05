# dsh-superagent 原型架构

> 一句话定位：这是一个挂在 DSH（DeepSeek Harness）宿主上的**单机、单仓、单账号的超级智能体编排原型**——它不实现 ReAct 循环与工具执行，而是把"事件→授权→工单→执行→回写"的治理链路做进领域模型，用可持久化的效果队列把主会话与每个工单的 Executor Session 串起来。

- 代码位置：`D:\agentABC\dsh-superagent-prototype`
- 形态：DSH 插件 bundle（`package.json:30-33` 声明 `dsh.bundle.patch`，`:34-45` 声明 `dsh.client`，`:11-21` 声明 node 入口 `lib/index.js`）
- 规模：`src/` 111 个文件（含 1 个 CSS）、15,205 行 TypeScript；`src/client/` 27 个文件、4,037 行；`tests/` 48 个 `*.spec.ts` 测试文件
- 文档对应关系：本文对应 `_arch` 编号 14；项目自身文档在 `dsh-superagent-prototype/docs/`（001 领域模型、002 授权、003 执行、004 提示词、005 面板、006 部署、007 架构、008 食谱）

---

## 1. 项目定位

### 1.1 它是什么

`dsh-superagent` 是论文《Super-agent 设计探索》的**研究性原型**，仓库 README 明确写了"这是研究原型、为公开做了适配、部分设计属于后续方向而非已实现"。它不是通用 Agent 框架，也不是独立服务，而是 DSH profile 里的一个 bundle：

| 组成 | 说明 | 证据 |
| --- | --- | --- |
| 宿主 | DSH 提供 Session、Agent、模型、工具、权限、Workspace、Web 服务器、客户端插槽 | `package.json:62-86` peer 依赖 `@deepseek-ai/dsh-*`；`src/app/sessions.ts:152` 使用 `ctx.permissionPresets.set` |
| 本仓库 | 领域编排（触发器/评估/授权/工单/指派/回复）+ 策略门禁 + 两个 Source 适配器 + 管理面板 | `src/core/*`、`src/sources/*`、`src/client/*` |
| 外部世界 | GitHub（`gh` CLI）、飞书（`lark-cli`）、模型 API、worker 工作目录中的 `git` | `src/sources/github.ts`、`src/sources/feishu.ts`、`src/infra/commands.ts` |

因此它的"智能体"是**借来的**：主 Session 与 worker Session 都是 DSH Agent；本仓库负责"谁在什么授权下、对哪条线程、做什么、做到什么程度"。

### 1.2 原型意图与验证目标

从代码与文档看，原型要验证的是四件事（按源码归纳）：

1. **事件驱动的授权模型**：触发器不是直接变成任务，而是先经"门禁（gate）+ 评估（evaluation）"两层判定；显式请求得到"路由卡"，主 Session 通常直接 `orchestrator_route` 开工，隐式候选得到"评估卡"，需先验证规则与方向。
2. **授权凭据（Mandate）的可审计性**：接受一次工作必须落下"策略版本 + 范围 + 强度 + 命中规则 + 来源身份 + 来源接收方式"，后续扩权只能新建工单，不能改写旧授权。
3. **主 Session 与 worker Session 的分层**：主 Session 只做路由/评审/回复，不使用文件工具写代码（shell 仍在其工具面内）；每个工单独立 worker Session、独立工作目录与独立指派记录。
4. **崩溃可恢复的编排**：领域状态落 SQLite，跨 Session 的副作用走持久化 Effects 队列，重启后从队列续跑，而不是靠内存状态。

### 1.3 与成熟项目的关系

- **与 DSH 的关系**：DSH 是运行时与"操作系统"；本项目是跑在它上面的"调度与治理应用"。所有 Agent 生命周期、工具沙箱、模型切换、上下文压缩都由 DSH 提供，本项目只声明 preset（`cordis.patch.yml:20-119` 的 worker preset、`:125-193` 的 router preset）。
- **与通用 Agent 框架的关系**：通用框架提供的是"Agent 循环 + 工具协议"；本项目提供的是"多来源事件接入 + 准入策略 + 工单编排 + 人机回复"。二者不在同一层，不能直接替代。
- **与论文的关系**：论文给出五模块愿景；本仓库是可运行的最小闭环。README 明确说未实现的部分属于"future work"，不能把论文里的能力当成此时代码已具备的能力。
- **与 `_digest` 对照分析的关系**：`_digest/SuperAgent-原型对照分析.md` 提供了模块映射视角，可作阅读索引；本文所有结论均以当前源码为准，若与旧摘要冲突以源码为准。

### 1.4 硬边界（源码可验证）

| 边界 | 事实 | 位置 |
| --- | --- | --- |
| 单仓 | 一个部署只配置一个 `repository` | `src/deployment.ts:45-46`；`src/sources/github.ts:25` |
| 单账号 | GitHub 侧一个 agent 登录身份；飞书侧一个 bot 身份 | `src/deployment.ts:97-105`；`src/deployment.ts:114-129` |
| 单机 | 用 `proper-lockfile` 锁住 `stateDir`，拿不到锁就拒绝启动 | `src/app/runtime.ts:93` |
| 单进程 | 主 Session、worker Session、HTTP API、面板数据都在同一个 DSH 进程内 | `src/app/runtime.ts:59`（单个 `Runtime` 实例持有全部子系统）；`src/app/sessions.ts:138` |
| 单库 | 全部领域状态在一个 SQLite 文件里，WAL 模式 | `src/app/store.ts:58-65` |

---

## 2. 技术栈与工程结构

### 2.1 技术栈

| 层 | 选型 | 说明 |
| --- | --- | --- |
| 语言/运行时 | TypeScript + Node.js | ESM，`"type": "module"`（`package.json:8`）；Node `^22.19.0 || >=24`（`package.json:53-56`） |
| 插件框架 | cordis（DSH 生态） | `Context`、`inject`、`ctx.effect`、`ctx.set`（`src/index.ts:8-27`） |
| Agent 宿主 | `@deepseek-ai/dsh-*` | Session、Agent、Subprocess、WebServer、Client UI；DSH `^0.2.1-alpha.2`（`package.json:55`） |
| 持久化 | `node:sqlite`（Node 内置 SQLite） | `src/app/store.ts:1`、`:58-65` |
| 校验 | zod | 部署配置、策略/设置、工具参数（`src/deployment.ts:7`、`src/policy.ts:6`、`src/app/tools/executor.ts:2`）；核心领域模型为手写 TS 类型，不依赖 zod |
| 构建 | tsdown | node 入口、client 入口、`.d.ts`（`tsdown.config.ts`） |
| 测试 | vitest | 48 个 spec，使用内存 SQLite 与宿主 fixture |
| 前端 | React + DSH Client UI 插槽 | `src/client/index.tsx:48-57` |

### 2.2 目录地图

| 目录 | 文件数 | 职责 | 关键入口 |
| --- | --- | --- | --- |
| `src/core/` | 15 | 纯领域层：模型、引擎、准入门禁、评估、工单、指派、回复、端口 | `engine.ts`、`model.ts`、`ports.ts` |
| `src/app/` | 38 | 应用层：装配、持久化、Effects、Passes、Session、评估器、出站、HTTP、面板数据 | `runtime.ts`、`passes.ts`、`sessions.ts`、`assessment.ts` |
| `src/executor/` | 2 | DSH Executor：工作目录、worker Session、报告回传 | `dsh.ts`、`slots.ts` |
| `src/sources/` | 16 | Source 协议、注册表、GitHub/飞书适配 | `kind.ts`、`registry.ts`、`github.ts` |
| `src/infra/` | 5 | 命令执行、环境 shim、健康、文本、路径 | `commands.ts`、`environment.ts`、`paths.ts` |
| `src/client/` | 27 | 浏览器面板：总览、工单、执行、策略、来源、部署配置 | `index.tsx`、`app.tsx` |
| `prompts/` | 15 | 主会话/worker/交接/团队协作提示词 | `orchestrator.md`、`worker.md`、`team/*` |
| `skills/` | 2 | GitHub/飞书操作技能（给 Agent 读） | `dsh-superagent-github/SKILL.md` |
| 根目录 | 8 | 插件入口、部署配置、默认策略、限制、bundle patch | `index.ts`、`deployment.ts`、`policy.ts`、`limits.ts` |

### 2.3 代码规模热点（维护者从哪里开始读）

| 文件 | 行数 | 为什么重要 |
| --- | --- | --- |
| `src/executor/dsh.ts` | 673 | Executor 全生命周期：准备目录、起 Session、下发、收报告、重试 |
| `src/sources/github.ts` | 459 | GitHub 轮询、通知、评论/PR/CI 触发器归一化 |
| `src/core/tickets.ts` | 423 | 工单状态机、订阅、输入、关闭/恢复/停止 |
| `src/app/sessions.ts` | 352 | 两个 Session 的创建、权限、prompt、relay、报告绑定 |
| `src/core/model.ts` | 353 | 全部领域结构与不变量 |
| `src/core/evals.ts` | 340 | 门禁、评估批次、决策、接受时建单 |
| `src/app/tools/main.ts` | 301 | 主 Session 的 14 个编排工具 |
| `src/app/store.ts` | 291 | SQLite 包装、迁移、原子事务、聚合读写 |
| `src/app/assessment.ts` | 282 | 主会话评估器的投递、恢复、决策回写 |
| `src/app/http.ts` | 247 | `/orchestrator/api/*` 查询、操作与设置 API |
| `src/policy.ts` | 242 | 策略 schema、默认值、允许名单与版本 |

### 2.4 构建、测试与本地验证

| 动作 | 命令/入口 | 结果 |
| --- | --- | --- |
| 类型检查 + 测试 + 构建 | `pnpm check`（`package.json:51`） | 依次跑 `typecheck`、`test`、`build` |
| 单测 | `pnpm test`（`package.json:50`） | 48 个 spec |
| 构建 | `pnpm build`（`package.json:48`） | `lib/` 产物 |
| 安装到 DSH | 按 `docs/006-deployment.md` 配置 profile 与 bundle | 由 profile 的 `cordis.patch.yml` 挂载 |
| 面板 | 浏览器打开 DSH → 左侧锤子图标 | 主面板 + 插件管理配置页 |

---

## 3. 整体架构

### 3.1 进程与组件视图

```text
┌──────────────────────────── DSH 宿主进程（Node） ─────────────────────────────┐
│                                                                              │
│  cordis 插件容器                                                               │
│  ├─ dsh-superagent（main）                                                     │
│  │    └─ Runtime ──────────────── SQLite(stateDir)/lock                       │
│  │         ├─ Engine（core，唯一写入口）                                        │
│  │         │    ├─ Intake / Evals / Tickets / Assignments / Replies           │
│  │         │    └─ Policy（版本化准入规则）                                     │
│  │         ├─ MasterAssessor ── 主 Session（DSH Agent，路由/评审/回复）          │
│  │         ├─ DshExecutor ───── 工单 worker Session（DSH Agent，逐工单）         │
│  │         ├─ Passes（2s tick：到期评估 + Effects 泵）                           │
│  │         ├─ Effects（持久化副作用队列）                                        │
│  │         └─ HTTP /orchestrator/api/*（查询 + 操作 + 设置）                     │
│  │                                                                           │
│  ├─ dsh-superagent-github（Source 插件）── gh CLI 子进程 ── GitHub API           │
│  ├─ dsh-superagent-feishu（Source 插件，默认 disabled）── lark-cli ── 飞书    │
│  └─ dsh-superagent/client（浏览器插件）── 面板/设置页 ── HTTP API                 │
│                                                                              │
│  工单工作目录（executor.directory）── git / 仓库 / 构建命令 ── 宿主机文件系统     │
└──────────────────────────────────────────────────────────────────────────────┘
```

关键点：worker **不是一个独立守护进程**，而是宿主内由 `ctx.sessionController.create` 建出的 DSH Agent Session（`src/app/sessions.ts:138-160`）。它共享宿主的模型与工具，但拥有自己的 Session id、角色 preset、工作目录与指派记录。

### 3.2 分层与依赖方向

| 层 | 包含 | 允许依赖 | 禁止 |
| --- | --- | --- | --- |
| L0 领域 | `src/core/` | 仅标准库（不引入 zod、不 import 应用层） | 不碰 SQLite、不碰 DSH、不碰网络 |
| L1 策略 | `src/policy.ts`、`src/limits.ts` | L0 模型；`policy.ts` 另取 `src/infra/environment.ts` 的 `WORKER_COMMANDS`（唯一的反向依赖） | 不做其他 IO |
| L2 应用 | `src/app/`、`src/executor/`、`src/sources/` | L0/L1 + DSH 端口 | 领域逻辑不得回流到 UI/工具层 |
| L3 适配 | `src/infra/`、`src/client/` | 标准库 / 浏览器 API | 不定义业务规则 |

`src/core/ports.ts` 是这条边界的物化：`Policy`、`SourceScope`、`Candidate`、`Assessor`、`Executor`、`Outbox`、`Repositories`、`DomainEvents` 等端口接口定义在 core，依赖注入形状在 `src/core/part.ts`；实现类全部在 app/executor/sources。这样 `Engine` 可以用内存实现跑单测，而线上注入 SQLite 实现。

### 3.3 核心模块清单

| 模块 | 职责 | 目录/关键文件 |
| --- | --- | --- |
| `Engine` | 编排器与事务边界；暴露 `receive / evaluateDue / decide / report / attach / reply / stopTicket / retryTicket` 等用例 | `src/core/engine.ts:24` |
| `Intake` | 触发器去重、范围过滤、线程归并、订阅扇出、入队 | `src/core/intake.ts:16` |
| `Evals` | 门禁（gate）、评估批次、决策、接受时建单与授权凭据 | `src/core/evals.ts:27` |
| `Tickets` | 工单状态机、订阅、输入、结束/恢复/停止、指派启动 | `src/core/tickets.ts:29` |
| `Assignments` | 工单与 Executor 的绑定；接管、报告、输入投递回执 | `src/core/assignments.ts:30` |
| `Replies` | 回复的受理、发送、回执 | `src/core/replies.ts:26` |
| `Policy` | 默认策略、schema、允许名单、评估模式（`off/observe/auto`）、版本计算 | `src/policy.ts` |
| `Runtime` | 组合根：建 Store/Effects/Passes/Sessions/Assessor/Executor/Sources，初始化与停机 | `src/app/runtime.ts:59` |
| `Store` | SQLite schema、迁移、聚合读写、原子事务 | `src/app/store.ts:51` |
| `Effects` | 持久化副作用队列（assessment/launch/delivery/relay/notice/reply…） | `src/app/effects.ts:46` |
| `Passes` | 2 秒一拍：到期评估 + Effects 泵 | `src/app/passes.ts:22` |
| `Sessions` | 主/worker Session 的创建、权限、prompt、relay、事件绑定 | `src/app/sessions.ts:93` |
| `MasterAssessor` | 把候选卡片投给主 Session，再把决策回写 Engine | `src/app/assessment.ts:89` |
| `DshExecutor` | 工单目录准备、worker 启动、输入下发、报告接收、重试 | `src/executor/dsh.ts:207` |
| `SourceRegistry` | Source kind 注册与部署配置解析 | `src/sources/registry.ts:13` |
| `GitHubSource` | 轮询仓库/通知，生成 comment/issue/PR/CI 触发器 | `src/sources/github.ts:38` |
| `FeishuSource` | 飞书消息/群/话题线程适配（默认关闭） | `src/sources/feishu.ts:31` |
| `Outbox` | 出站消息排队、发送、回执 | `src/app/outbox.ts:22` |
| `HTTP API` | `/orchestrator/api/*` 概览、工单、设置、健康 | `src/app/http.ts:151` |
| `Client Panel` | 浏览器插件：面板、侧栏、插件配置 | `src/client/index.tsx:50` |
| `Prompts/Skills` | 主/worker/交接/团队提示词与来源操作技能 | `prompts/`、`skills/` |

### 3.4 架构上的四个关键决定

1. **领域层可脱离宿主**：`Engine` 只依赖 `EngineOptions` 注入的端口（`Repositories`/`Policy`/`Executor`/`Assessor`/`Outbox`/`DomainEvents`），写用例经 `repo.atomic` 包事务（`src/core/engine.ts:48`），不直接持有 SQLite；因此单测可注入内存仓库。
2. **单一写入口**：领域状态（触发器/线程/工单/指派/决策）的变更只经 `Engine`；HTTP、面板、工具不直接改这些表。设置、提示词、来源游标等运维状态由 app 层直写（`src/app/settings.ts`、`src/app/prompts.ts`）。
3. **效果与状态分离**：状态在 SQLite 里同步落盘，跨 Session 的动作（投递卡片、起 worker、发消息）变成 Effects 行，由 `Passes` 异步执行；失败按退避重试，代际校验防止旧结果覆盖新行（`src/app/effects.ts:61-146`）。
4. **两个 Session 角色**：主 Session（`router` preset，文件工具禁写但仍可用 shell）只评估与回复；worker（`worker` preset，5s 前台命令转后台）只做单工单；两者都由 `Sessions.ensure` 设成 `danger-full-access`（`cordis.patch.yml:125-193`、`src/app/sessions.ts:145-152`）。

---

## 4. 核心代码路径

### 4.1 入口点

| 入口 | 作用 | 位置 |
| --- | --- | --- |
| Node 插件入口 | 读取部署配置 → 构造 `Runtime` → 暴露 `ctx.orchestrator` 服务 | `src/index.ts:10` |
| GitHub Source 插件 | 解析 Source 配置，注册 kind 与轮询 loop | `src/sources/github.ts:112` |
| 飞书 Source 插件 | 解析配置，注册 kind 与事件消费 | `src/sources/feishu.ts:132` |
| 浏览器插件 | 注册主面板、侧栏图标、插件配置页 | `src/client/index.tsx:50` |
| Bundle patch | 声明三个插件与两个 preset，并写入默认配置 | `cordis.patch.yml:4-12`、`:20-193` |
| 组合根 | 构造时加锁、开库；`Runtime.initialize()` 做部署解析、健康、主 Session、Source 与 Passes 启动 | `src/app/runtime.ts:93`、`:201` |
| HTTP API | `/orchestrator/api/overview` 等 | `src/app/http.ts:151` |

### 4.2 关键类与函数（按调用顺序）

| 类/函数 | 角色 | 位置 |
| --- | --- | --- |
| `Runtime` 构造 | 建 Store/Effects/Passes/Sessions/Policy/Assessor/Executor/Outbox/Engine | `src/app/runtime.ts:59` |
| `Runtime.initialize` | 解析部署、建 Setup/健康/主 Session、启动 Source 与 Passes（加锁在构造函数） | `src/app/runtime.ts:93`、`:201` |
| `SourceRegistry.register` | 根据部署配置装配启用的 Source | `src/sources/registry.ts:13` |
| `GitHubSource.pollRound` | 一轮仓库/通知轮询，产出触发器 | `src/sources/github.ts:280` |
| `SourceContext.receive` | 适配器 → Runtime 的写入口 | `src/sources/host.ts:31-42` |
| `Passes.receive` | 把触发器交给 Engine，并请求泵 | `src/app/passes.ts:34` |
| `Engine.receive` | 调 `Intake.receive`，返回受理结果 | `src/core/engine.ts:48` |
| `Intake.receive` | 幂等、范围过滤、订阅扇出、待评估入队 | `src/core/intake.ts:19` |
| `Engine.evaluateDue` | 找出到期评估，逐个 `Evals.start` | `src/core/engine.ts:75` |
| `Evals.start` | 门禁、批处理、向 Assessor 请求卡片 | `src/core/evals.ts:71` |
| `MasterAssessor.request` | 把评估以 `assessment` 效果入队 | `src/app/assessment.ts:104` |
| `Effects.dispatch` | 到点取效果，交给 handler，按 `due`/退避重试执行，写入前比对 `seq+generation` | `src/app/effects.ts:103` |
| `MasterAssessor` 的 assessment handler | 生成候选卡片，`Sessions.prompt` 投给主 Session | `src/app/assessment.ts:96` |
| 主 Session 工具 `orchestrator_eval` | 读取候选评估详情 | `src/app/tools/main.ts:203` |
| 主 Session 工具 `orchestrator_eval_decide` | accept/reject/stop → `Engine.decide` | `src/app/tools/main.ts:215` |
| `Evals.decide` | 校验决策、写决策行、接受时建单 | `src/core/evals.ts:131` |
| `Tickets.create` | 生成工单与首个指派、订阅来源线程、`Executor.start` 入队 `launch`（目录准备在 launch 内做） | `src/core/tickets.ts:37` |
| `DshExecutor.launch` | 准备目录、`Sessions.ensure`、下发工作 prompt | `src/executor/dsh.ts:424` |
| `Sessions.ensure` | 按 worker id 建/复用 Session，绑定 ticket | `src/app/sessions.ts:138` |
| 主 Session `orchestrator_route` | 显式请求直接路由到工单（内部仍走 `Engine.decide`） | `src/app/tools/main.ts:127` |
| worker 工具 `orchestrator_ack` | 声明已读输入 | `src/app/tools/executor.ts:29` |
| worker 工具 `orchestrator_trigger_handback` | 交还/请求更多上下文 | `src/app/tools/executor.ts:66` |
| worker 工具 `orchestrator_report` | 上报进展/结果/PR | `src/app/tools/executor.ts:75` |
| `Assignments.report` | 落指派报告、更新工单与 attention、可能结束工单 | `src/core/assignments.ts:99` |
| `Tickets.threadClosed` | PR 关闭/合并等来源事件结束工单 | `src/core/tickets.ts:77` |
| `Outbox.send` | 通过 Source Channel 发消息并等待回执 | `src/app/outbox.ts:27` |
| `Sessions.relay` | 主 Session 把结果/问题转给线程与工单 | `src/app/sessions.ts:171` |

### 4.3 一条典型运行链：GitHub 评论 → 评估 → 工单 → worker → 回复

以"某人在被监听的 issue/PR 上 @ 了 agent"为例，完整路径如下（每一步都能在源码定位）：

1. **轮询产生触发器**
   `GitHubSource.pollRound`（`src/sources/github.ts:280`）拉取仓库事件与通知；`github-trigger.ts` 把评论、issue、PR、CI 失败归一化成 `Trigger`，带上 `id`、actor、thread 键、channel 地址、原始元数据。
2. **进入编排**
   适配器通过 `SourceContext.receive` 调 `Runtime`，落到 `Passes.receive`（`src/app/passes.ts:34`）→ `Engine.receive`（`src/core/engine.ts:48`）。
3. **准入范围与扇出**
   `Intake.receive`（`src/core/intake.ts:19`）：
   - 按 `Trigger.id` 幂等去重（id 由 Source 生成，包含事件类型与外部 id）；
   - 调 `SourceScope.scope` 做**监听范围**过滤，不在范围直接写 `filtered` disposition；
   - 按 `threads` 找订阅该线程的工单，给它们各加一条 `TicketInput` 并 `wake`（已结束的工单只有"人的消息 + 非 context 线程 + 非被人 stop"才可恢复）；
   - 若有工单接手（`owners(trigger)` 非空），**不再为评估排队**；否则把触发器挂到线程，等下一轮评估。
   注意：允许名单与 `explicit/inferred` 强度不在这里判定，而在下一步 `Evals.start` 的门禁里。
4. **2 秒拍与评估启动**
   `Passes` 的 tick（`src/app/passes.ts:28` 的 `setInterval(..., 2000)`）→ `Engine.evaluateDue`（`src/core/engine.ts:75`）→ `Evals.start`（`src/core/evals.ts:71`）：
   - **门禁**：按"人类/非人类 + 允许名单 + admission 表 + 是否直接 @ + 是否订阅线程 + `eval.mode`"判定 `explicit` / `inferred` / 拒绝；被拒绝的触发器只记 disposition，不打扰主 Session；
   - **批次**：把线程上等待的触发器合成一批，挑出最强触发器作为主候选，读取线程快照、相关工单、历史决策、当前策略版本；
   - **上锁**：在 `Thread` 上标记 `evaluating`，同一线程此时只允许一个评估。
5. **投递候选卡片**
   `Evals.start` 把候选交给 `Assessor.request`（`src/core/evals.ts:118`）→ `MasterAssessor.request`（`src/app/assessment.ts:104`）入队 `assessment` 效果。
   `Passes` 泵到该效果后，`MasterAssessor` 生成卡片（显式请求是"路由卡"，隐式信号是"评估卡"），经 `host.deliver` → `Sessions.prompt(masterId, id, text, 'steer')`（`src/app/runtime.ts:133`）投给主 Session。
6. **主 Session 判断**
   主 Session 是 `router` preset 的 DSH Agent（`cordis.patch.yml:125-193`）：文件工具禁写，但 shell 仍可用；编排工具是主要工作面：
   - 显式卡片：调 `orchestrator_route`（`src/app/tools/main.ts:127`）直接开/续工单（内部仍走 `Engine.decide`）；
   - 隐式卡片：先 `orchestrator_read` 补上下文，再调 `orchestrator_eval`（`main.ts:203`）查看评估，最后 `orchestrator_eval_decide`（`main.ts:215`）给出 `accept/reject/stop`。
7. **决策落库**
   `Engine.decide` → `Evals.decide`（`src/core/evals.ts:131`）：校验决策与候选匹配、校验策略版本，写 `Decision`；`accept` 时构造不可变 `Mandate` 并调 `Tickets.create`（`src/core/tickets.ts:37`）。
8. **准备工单属性并入队启动**
   `Tickets.create` 通过 `prepareTicket` 钩子（`src/core/part.ts:15`，Runtime 注入为 `DshExecutor.prepare`，`src/executor/dsh.ts:238`）计算 `execution`（worktree 名、目录、指派文本），再调 `Executor.start`（`src/executor/dsh.ts:264`）入队 `launch`；真正的 `sh -c` 准备命令在 launch 内跑。
9. **启动 worker**
   `DshExecutor.launch`（`src/executor/dsh.ts:424`）：
   - `prepareDirectory`（`:247`）在工作目录父级跑 `executor.prepare` 命令（默认空；可配 `git worktree add`）；
   - `Sessions.ensure`（`src/app/sessions.ts:138`）按 `workerSessionId(ticketId)` 建/复用 DSH Session，挂 `worker` preset；
   - `Sessions.prompt` 下发工作说明（工单、授权范围、线程上下文、可用技能、报告规范）；
   - 调 `engine.assignmentStarted` 把 `Assignment` 置为运行中。
10. **worker 执行**
    worker 在自己的工作目录里读代码、改代码、跑测试、发 PR（用 GitHub/飞书技能与 shim 的 `gh`/`git`/`lark-cli`）。过程中：
    - 收到新人类消息 → `orchestrator_ack` 声明已读；
    - 需要更多上下文或无法继续 → `orchestrator_trigger_handback`；
    - 阶段性完成 → `orchestrator_report`（`src/app/tools/executor.ts:75`）。
11. **报告回传与工单推进**
    `orchestrator_report` 在同一个 `store.atomic` 里完成三件事：认领 PR、调 `Assignments.report`（更新 `Ticket` 的 attention/answers/undelivered，`ready`/`dropped` 且满足 `followsDone` 时调 `Tickets.end`）、由 `reportRelay`（`src/app/notices.ts:121`）生成转述后调 `Sessions.relay`（`src/app/tools/executor.ts:98`）；relay 只入队 `relay` 效果，由主 Session 接手，需要发回来源时再走 `Outbox`。worker 一轮结束（idle）或失败时，`DshExecutor` 也会调 `this.relay`（`src/executor/dsh.ts:420`、`:667-669`）把状态转给主 Session。
12. **回写来源**
    `Outbox.send`（`src/app/outbox.ts:27`）按线程的 Channel 调 GitHub/飞书 CLI 发评论/消息，成功后写 `Receipt`；`Passes` 继续推进下一个效果。来源若随后关闭/合并 PR，`Tickets.threadClosed`（`src/core/tickets.ts:77`）结束工单。

如果把这条链压缩成"会话 → 意图 → 工具调用 → 结果"：主 Session 收到卡片是"会话输入"，读线程/评估是"意图理解"，`orchestrator_route` / `orchestrator_eval_decide` 是"工具调用"，`Decision + Ticket` 是"结果落库"；worker 的 `report` 与 `Outbox` 则是结果的第二次回传。

---

## 5. 关键数据结构与状态管理

### 5.1 领域聚合

| 结构 | 关键字段 | 不变量/说明 | 位置 |
| --- | --- | --- | --- |
| `Trigger` | `id`、`source`、`threads[]`、`actor`、`human`、`addressed`、`text`、`channel`、`meta` | 不可变；`id` 由 Source 生成，是幂等与审计的最小单位 | `src/core/model.ts:23` |
| `TriggerDisposition` | `filtered`、`evalId`、`decisionId`、`fanout`、`context`、`requeued`、`handbacks`、`acked` | 记录触发器去了哪里；决定后续消息归谁处理 | `src/core/model.ts:42` |
| `Thread` | `key`、`ref`、`subscriptions`、`context`、`correlated`、`pending`、`evaluating`、`expired`、`meta` | 同一时刻最多一个 `evaluating`；评估期间新触发器进 `pending` | `src/core/model.ts:157` |
| `Evaluation` | `id`、`threadKey`、`triggerIds`、`primary`、`strength`、`actor`、`basis`、`policyVersion`、`deadline` | 挂在线程上；到期/策略变化会作废 | `src/core/model.ts:136` |
| `Decision` | `id`、`evalId`、`threadKey`、`triggerIds`、`kind`、`reason[]`、`strength`、`ticketId`、`mandate`、`audit` | `kind` 五值：ignore/accept/reopen/stop/unavailable；接受必须带 mandate | `src/core/model.ts:192` |
| `Mandate` | `strength`、`policyVersion`、`basis`、`actor`、`scope` | **不可变**；扩权=新工单；人员叫停才撤销 | `src/core/model.ts:126` |
| `Ticket` | `id`、`title`、`decisionId`、`mandate`、`channels`、`assignments`、`inputs`、`undelivered`、`follows`、`origin`、`execution`、`ended` | 无独立 `state` 字段：阶段由 `ended/assignments/report` 派生 | `src/core/model.ts:277` |
| `Assignment` | `id`、`state`（pending/running/ended）、`startedAt`、`endedAt`、`endedReason`、`report`、`deliveredAt`、`idleAt` | 与工单独立；最终报告决定工单是否结束 | `src/core/model.ts:218` |
| `TicketInput` | `kind`（trigger/policy-changed/reopen/resumed/text/note）、`triggerId`、`readAt`、`deliveredTo` | 人类消息进入订阅工单后的投递单元 | `src/core/model.ts:235` |

### 5.2 存储布局（`src/app/store.ts:70-91`）

| 表/键 | 内容 | 用途 |
| --- | --- | --- |
| `kv` | schema 版本、主 Session id（`master-id`）、设置/提示词修订号、来源游标 | 元数据与重启恢复锚点 |
| `trigger` | `id` 主键 + `value`（Trigger JSON）+ `at` | 去重与审计 |
| `disposition` | `id` 主键 + `value`（TriggerDisposition JSON） | 解释"为什么没做/去了哪个工单" |
| `trigger_thread` | `(thread, id)` 主键 + `at`、`human` | 线程时间线、判断谁能处理后续消息 |
| `thread` | `key` 主键 + `value`（Thread JSON，含 `pending/evaluating`） | 评估串行与订阅 |
| `ticket` | `id` 主键 + `value`（Ticket JSON，含 assignments/inputs/follows） | 执行主线 |
| `decision` | `id` 主键 + `thread` + `value`（Decision JSON） | 主 Session 审批链 |
| `outbox` | `id` 主键 + `value`（消息 + receipt 状态） | 至少一次投递与按会话排序 |
| `effect` | `kind`、`key`、`value`、`seq`、`generation`、`attempts`、`error`、`due`、`since` | 崩溃续跑、代际校验、重试 |
| 生成列/索引 | `ticket.open/active`、`thread.active/subscribed`、`outbox.pending/dropped` | 让 Passes 只扫描活跃行 |

所有聚合是 **JSON 文本 + 少量生成列（generated columns）**，读取时反序列化；schema 版本当前为 11，兼容最低 10，启动时迁移（`src/app/store.ts:45`、`:70-91`）。

### 5.3 事务与一致性

| 机制 | 行为 | 位置 |
| --- | --- | --- |
| `Store.atomic` | 一个回调内所有写在一个事务里；嵌套调用支持回滚 | `src/app/store.ts:140` |
| 单写者 | 所有领域写都在 `Engine` 的用例里发生 | `src/core/engine.ts` |
| 评估串行 | `Thread.evaluating` 只允许一个评估；后来触发器进 `pending` | `src/core/intake.ts`、`src/core/evals.ts:71` |
| 乐观校验 | 决策校验 `evalId + policyVersion`，并确认候选仍是线程上的活动评估 | `src/core/evals.ts:131` |
| 效果重试 | 失败写回 `attempts/error/due`，按 `retry` 区间指数退避；`Later` 只推后 `due` 不计失败；停机时运行中的行保留，下次启动重跑 | `src/app/effects.ts:130-146` |
| 效果限流 | `assessment` 4、`delivery` 4、`reply` 1、`launch` 受 `maxWorkers`/slot 约束；`relay/notice` 以 `ordered: true` 串行（并发 1） | `src/app/assessment.ts:101`、`src/executor/dsh.ts:232-235`、`src/app/outbox.ts:24`、`src/app/effects.ts:70-71`、`src/app/sessions.ts:104-105` |
| 停机 | `Runtime.shutdown` 释放锁并停止 tick；未完成效果留给下次启动 | `src/app/runtime.ts:230` |

### 5.4 状态机

工单没有持久化的 `state` 字段，阶段是**派生**的（`src/core/stage.ts:9-21`）：

| 判定顺序 | 条件 | 阶段 |
| --- | --- | --- |
| 1 | `ticket.ended` 存在 | `ended` |
| 2 | `ticket.delivery` 存在（输入投递失败） | `person/delivery` |
| 3 | `ticket.attention` 存在（等待人回答） | `person/answer` |
| 4 | 最新指派报告为 `ready` | `person/review` |
| 5 | 报告为 `blocked`/`failed` 且仍等人 | `person/blocked|failed` |
| 6 | 无指派或最新指派为 `pending` | `working/queued` |
| 7 | 报告为 `waiting` 或指派已 `ended` | `idle` |
| 8 | 其余 | `working` |

指派自身只有 `pending → running → ended` 三态；报告状态是 `progress / waiting / ready / blocked / failed / dropped`（`src/core/model.ts:211-216`）。工单结束由 `Ticket.ended` 记录，结局为 `completed / merged / closed / dropped / stopped`（`src/core/model.ts:273`）。

评估的生命周期是**线程内的临时字段**，不是独立状态表：

```text
Thread.pending ──Evals.start──> Thread.evaluating ──assessor 卡片──> Decision(kind)
                                      │
                                      ├─超时/策略变化/评估器失败──> Decision(unavailable)
                                      └─候选被更强批次取代/线程结束──> 释放 evaluating
```

Decision 的 `kind` 只有 `ignore / accept / reopen / stop / unavailable`；`auto`/`observe` 只影响 inferred 候选能否被接受或只记录 `would_accept`，不改变主 Session 的卡片流程。

### 5.5 幂等与恢复

- 触发器以 `Trigger.id` 去重，重复事件不产生第二个工单（`src/core/intake.ts:19`）。
- 出站消息带 `messageId`，回执按 id 落库；崩溃窗口内可能重复发送，属于**至少一次**语义，通道侧是否幂等决定最终效果（按 `Outbox.send` 的"先发后回执"路径推断）。
- 效果队列保证"动作不丢"，但不保证"动作只做一次"；因此 `launch`/`delivery` 都先检查工单/指派当前状态再执行（`src/executor/dsh.ts:290`、`:424`）。

---

## 6. 接口与配置

### 6.1 插件入口与 bundle 组装

`package.json` 同时声明：

- `exports`：`.`（node 插件）、`./client`（浏览器插件）、`./github-watch`、`./feishu-watch`（`package.json:11-21`）；
- `dsh.bundle.patch`：`cordis.patch.yml`（`package.json:30-33`）；
- `dsh.client`：platform `web`，入口 `lib/client.js`，依赖 6 个 DSH 客户端包（`package.json:34-44`）；
- Node 版本 `^22.19.0 || >=24`，DSH `^0.2.1-alpha.2`（`package.json:53-56`）。

`cordis.patch.yml` 挂三个插件并写默认配置：

| 插件 | 默认行为 | 配置 |
| --- | --- | --- |
| `dsh-superagent` | 启用 | `stateDir`（唯一必填）、三个 volatile 上限 |
| `dsh-superagent-github` | 启用 | `repository`（单仓）、`cli`（gh 路径）、`pollSeconds`、4 个 `observe*` 开关（`src/sources/github.ts:25-28`） |
| `dsh-superagent-feishu` | 默认 `disabled: true` | `cli`（lark-cli 路径）、`chats`、`directMessages`、`otherChats` |
| `worker` preset | `worker` 角色 | worker 工具面、5s 前台命令超时 |
| `router` preset | 主 Session 角色 | 文件工具 `write:false`、编排工具、无 persona（提示词完整）、5s 命令转后台 |

### 6.2 插件配置（`src/deployment.ts:15-23`）

| 配置 | 说明 | 约束 |
| --- | --- | --- |
| `stateDir` | 唯一状态目录：SQLite、锁、worker shim、git 配置、默认工单目录 | 必填；以 `/` 开头的绝对路径（`deployment.ts:13`） |
| `promptMaxChars` | 保存的提示词配置最大字符数 | volatile，改后无需重启（`deployment.ts:17-18`） |
| `admissionContextMaxPages` | 一次评估最多读取的线程上下文页数 | volatile，默认 10 |
| `admissionContextTimeoutMs` | 一次上下文读取的时限 | volatile，默认 15000 |

Source 的仓库/CLI、执行器目录、prepare、blockedCommands、允许发送者都**不在这里**：仓库在 GitHub Source 配置里，执行器与允许发送者在运行时 Settings 里；旧配置键会由 `MOVED` 映射提示迁移位置（`deployment.ts:31-35`）。

### 6.3 运行时设置与策略

设置 schema 在 `src/policy.ts:99-105`，持久化在 SQLite；每次保存生成新的 `policyVersion`（`src/policy.ts:116`），并触发 `notice` 让运行中的工单感知规则变化，但**不撤销已发 mandate**。

| 设置块 | 关键项 | 影响 |
| --- | --- | --- |
| `policy` | `rules`（规则表）、`sources[source].allowed`、`admission` 单元格、`bots` | 决定谁能触发、什么强度可开工 |
| `eval` | `mode`（`off`/`observe`/`auto`）、`timeoutSeconds`、`model` | 候选评估是否接受、评估时限、评估模型 |
| `executor` | `maxWorkers`、`directory`、`prepare`、`blockedCommands`、`model` | worker 数量、工作目录、准备命令 |
| `sources[name]` | `enabled`、`config` | 开关来源与来源自身配置 |
| `paused` | 全局暂停 | 暂停时 `assessment/reply/launch/delivery` 停摆 |

**门禁规则**（`src/policy.ts:167-236`）的核心顺序：

1. 来源是否在监听范围（`scope`）；非人类触发器（bot/CI/system）只能成为 `inferred` 候选，不能授权；
2. 人类发送者是否在该 Source 的 `allowed` 名单；
3. 是否直接 @/私聊（Source 声明的 `addressed`）：允许名单里的人 @ → 直接 `explicit`，不再查 admission 表；其余情况按 `admissionCell(允许?, @?)` 取单元格判强度；
4. 线程已有工单且 `participating`：允许名单内 → `explicit` follow-up；否则只要 `eval.mode` 非 `off` → `inferred` follow-up；
5. 否则按 admission 表与 `eval.mode` 决定是否产生 `inferred` 候选（`observe` 只记录 `would_accept`，`auto` 才允许接受）；
6. 未通过 → 写 disposition 的 `filtered`/原因，不打扰主 Session。

### 6.4 Source 扩展接口

`src/sources/kind.ts:85-113` 的 `SourceKind` 协议包含：

- `schema` / `fields` / `facts` / `health`：配置 schema、面板字段、只读状态、健康条目；
- `scope`：判断触发器属于 listen/observe/ignore；
- `channel`：`send`（幂等发送，返回 `sent`/`gone`）、`link`、`allowed`；
- `threadContext`：评估时有限读取线程消息与图片；
- `find` / `repliesTo`：搜索与回复关系；
- `policy`：允许名单与 admission 表行；
- `refreshLabels`：刷新来源显示名；
- `environment`：为 worker 注册环境变量与 shim。

新增来源（如 Jira、邮件）只需实现该协议并在 `SourceRegistry` 注册，不改领域层；这也是 GitHub/飞书字段没有泄漏进 `core/` 的原因。

### 6.5 主 Session 与 worker 的工具面

| 角色 | 工具 | 作用 |
| --- | --- | --- |
| 主 Session | `orchestrator_route` | 显式请求 → 直接路由到工单 |
| 主 Session | `orchestrator_read` | 读取线程/工单/评估/设置等资源 |
| 主 Session | `orchestrator_ticket_retry` | 重试停滞工单（投递失败或 blocked/failed） |
| 主 Session | `orchestrator_ticket_request_status` | 向 worker 请求状态 |
| 主 Session | `orchestrator_ticket_note` | 给工单补充上下文（不授权） |
| 主 Session | `orchestrator_trigger_requeue` | 把触发器送回评估 |
| 主 Session | `orchestrator_eval` | 查看候选项与规则命中 |
| 主 Session | `orchestrator_eval_read` | 读取候选的上下文/图片 |
| 主 Session | `orchestrator_eval_decide` | accept/reject/stop |
| 主 Session | `orchestrator_reply` | 回复线程（可附带工单更新） |
| 主 Session | `orchestrator_thread_unsubscribe` | 取消线程订阅 |
| 主 Session | `orchestrator_settings_save` | 保存运行时设置 |
| 主 Session | `orchestrator_policy_sync` | 同步策略/名册 |
| 主 Session | `orchestrator_prompts_save` | 保存提示词配置 |
| worker | `orchestrator_ack` | 声明已读输入 |
| worker | `orchestrator_thread_unrelated` | 声明某线程与本工单无关 |
| worker | `orchestrator_thread_follow` | 订阅额外线程做只读上下文 |
| worker | `orchestrator_trigger_handback` | 交还控制权/请求上下文 |
| worker | `orchestrator_report` | 进展、结果、PR、阻塞 |

（工具注册见 `src/app/tools/main.ts:155` 与 `src/app/tools/executor.ts:23`。）

### 6.6 HTTP 与面板

`src/app/http.ts:151-213` 注册 `/orchestrator/api/*`，只允许同源/回环访问（`:234-241` 的 prefix 注册器 + `sameOrigin` 校验）。主要端点：

| 端点 | 方法 | 用途 |
| --- | --- | --- |
| `state` | GET | 面板/CLI 消费的完整状态快照 |
| `overview` | GET | 工单/评估/worker/健康总览 |
| `search` | GET | 全局搜索（线程/工单/来源） |
| `sources`、`POST sources/:id/labels` | GET/POST | 来源健康、刷新标签 |
| `threads`、`threads/:key`、`POST threads/:key/unsubscribe` | GET/POST | 线程列表/详情、取消订阅 |
| `triggers/:id/requeue` | POST | 触发器重排 |
| `decisions`、`POST decisions/:id/dismiss` | GET/POST | 决策历史、忽略某决策 |
| `tickets`、`tickets/:id`、`POST tickets/:id/retry`、`POST tickets/:id/stop` | GET/POST | 工单列表/详情、重试、停止 |
| `settings`、`PUT settings/:block`、`POST executor/pause` | GET/PUT/POST | 读设置、按块保存、全局暂停 |
| `policy/history`、`POST policy-sync/:id` | GET/POST | 策略历史、同步来源名册 |
| `prompts`、`PUT prompts`、`POST prompts/preview` | GET/PUT/POST | 提示词查看、保存、预览 |
| `models`、`POST setup/check` | GET/POST | 模型列表、重新自检 |

写操作要求 `x-orchestrator-request: 1` 且来源同源（`sameOrigin`，`http.ts:75-79`），没有独立的鉴权层，依赖 DSH WebServer 的访问控制。

面板（`src/client/index.tsx:50`）注册主面板、侧栏图标、插件管理配置页；它只消费上述 API，不直接读 SQLite。

### 6.7 外部依赖

| 依赖 | 用途 | 安装/约束 |
| --- | --- | --- |
| `gh` | GitHub 读写 | worker 通过 shim 使用 agent 身份 |
| `git` | 工作目录、PR 分支 | 不可被 `blockedCommands` 禁止 |
| `lark-cli` | 飞书消息 | 飞书 Source 启用时必需 |
| 模型 API | 主/worker Session | 由 DSH 配置，角色可分别指定模型 |
| `sh` | `executor.prepare` 命令 | `src/executor/dsh.ts:254` 固定用 `sh -c` |

---

## 7. 数据流与典型场景

### 7.1 场景 A：显式请求（@ 或指派）

1. GitHub 评论命中 `explicit` → `Intake` 去重/范围校验 → 线程待评估。
2. `Evals.start` 仍生成一次评估（用于审计与 disposition），但卡片是"路由卡"；主 Session 直接 `orchestrator_route`。
3. `orchestrator_route` 内部调 `Engine.decide(accept)` → `Evals.decide` → `Tickets.create`（沿用触发器的线程与频道），`Executor.prepare` 目录，`Executor.start` 入队 `launch`。
4. worker 收到带 mandate 的工作说明；完成后 `orchestrator_report`。
5. 主 Session 摘要并 `orchestrator_reply` → `Outbox` → 来源评论；PR 绑定线程，后续讨论直接进 worker。

显式请求**不经过 `orchestrator_eval` 的 accept/reject 审批**，但仍经过门禁（允许发送者、范围、来源身份），并留下完整评估/决策记录。

### 7.2 场景 B：订阅线程中的后续人类消息

1. 线程已绑定工单且发送者被允许 → `Intake` 不建评估，直接生成 `TicketInput` 并入队 `delivery`。
2. `DshExecutor.deliverQueued`（`src/executor/dsh.ts:290`）把输入投给 worker：worker 忙时排队，空闲时立即唤醒。
3. worker `orchestrator_ack` 声明已读；需要时 `orchestrator_report` 更新状态。
4. 若 worker 已完成且工单结束，人类消息可重新开指派；但被人员 `stop` 的工单拒绝恢复。

这是"全双工"的核心：人不必每次 @ agent，worker 持续持有线程订阅。

### 7.3 场景 C：隐式信号（CI 失败、PR 评论、issue 变动）

1. 来源产生 `inferred` 触发器；门禁允许且 `eval.mode` 不为 `off` 时进入评估。
2. 主 Session 收到"评估卡"，可读线程与规则命中，决定 accept/reject/stop。
3. `reject/stop` 只落决策；accept 后与场景 A 相同。
4. `observe` 模式下即使规则命中，accept 也被拒绝，只记录 `would_accept`；`auto` 模式才允许**在规则足够明确时**接受 inferred 候选，但卡片与决策流程不变。

### 7.4 场景 D：失败、暂停与重启

| 情况 | 行为 | 位置 |
| --- | --- | --- |
| `executor.prepare` 失败 | 不自动重试；删空目录，非空保留，工单标记失败并通知，等人工输入或显式 retry | `src/executor/dsh.ts:254-258`、`:278-283` |
| worker 启动失败 | 非 prepare 类错误按退避重试；耗尽后标记失败 | `src/executor/dsh.ts:276-283` |
| worker 一轮结束但没报告 | 监听 `agent/status`，`turnEnded` 记录 `idleAt`；需要时由主 Session 追问或补报告 | `src/executor/dsh.ts:479`、`:625`、`:642` |
| 输入投递失败 | 记录到工单，`delivery` 效果 `quiet`，不报健康错误 | `src/executor/dsh.ts:235` |
| 全局暂停 | assessment/launch/delivery/reply 的并发上限置 0；已有 worker 继续；评估截止时间暂停计时 | `src/app/assessment.ts:101`、`src/app/outbox.ts:24`、`src/executor/dsh.ts:232-235` |
| 进程崩溃 | SQLite 状态 + Effects 行保留，重启后重跑；重复投递按 `Trigger.id`/消息 id 去重 | `src/app/effects.ts:98-103` |
| 锁冲突 | `proper-lockfile` 拿不到锁 → 拒绝启动，避免双进程写同一库 | `src/app/runtime.ts:93` |

---

## 8. 与成熟实现的差异、局限与演进建议

### 8.1 差异对比

| 维度 | 本项目（原型） | 成熟编排/Agent 平台（如 Airflow、通用 Agent 框架） |
| --- | --- | --- |
| 运行单元 | 领域"工单 + DSH Session" | DAG Task / 独立 Agent 服务 |
| 调度 | 2s 内存 tick + SQLite Effects 队列（`due`/退避） | 分布式调度器、队列、心跳 |
| 扩展 | 单进程、单库、单机锁 | 水平扩展、多租户、HA |
| Agent 循环 | 交给 DSH | 自带 ReAct/工具循环 |
| 授权 | 领域内 mandate + 策略版本 | 通常靠外部 IAM/审批系统 |
| 可观测 | 面板 + 健康状态 + 日志 | 指标、追踪、告警、审计平台 |
| 事件源 | GitHub/飞书两种 | 插件市场/连接器生态 |

### 8.2 局限（按源码可证实）

1. **单点主 Session**：所有候选评估与回复都经过同一个主 Session；`assessment` 并发上限 4、`reply` 串行 1（`src/app/assessment.ts:101`、`src/app/outbox.ts:24`），relay 按入队顺序串行投递，吞吐上限明确。
2. **宿主耦合**：Session、工具、权限、模型、Web 服务器都来自 DSH alpha；升级 DSH 可能破坏 preset/工具契约。
3. **安全边界弱**：主 Session 与 worker 都被设成 `danger-full-access`（`src/app/sessions.ts:152`）；router 只禁了文件工具写入，shell 仍可写；`blockedCommands` 只按命令名拦截，绝对路径仍可执行，项目自己的 UI 也写明"不是安全边界"（`src/client/locales.ts:379`）。
4. **不可信输入**：GitHub/飞书正文、PR 描述都进入主/worker 上下文，提示注入只能靠门禁、卡片与提示词约束，没有内容隔离/沙箱标注。
5. **单仓单账号**：插件只配置一个 repository 与一个 agent 身份（`src/deployment.ts:45-46`、`:97-105`），无法多租户/多仓并行治理。
6. **平台不中立**：`prepare` 固定 `sh -c`（`src/executor/dsh.ts:254`），`stateDir` 校验以 `/` 开头（`src/deployment.ts:13`）；Windows 虽有 `pwsh` preset 与 `pwsh-sandbox`，但 prepare 路径仍偏 Unix（**推测**：Windows 部署需要额外适配）。
7. **无保留策略**：`trigger/thread/ticket/decision/outbox/effect` 持续增长，没有归档/清理任务（`store.ts` 只有迁移，无 retention）。
8. **可观测性有限**：只有健康状态、面板、日志；没有指标、追踪、外部告警（`src/infra/health.ts` 只是状态模型）。
9. **不是独立服务**：没有 CLI 启动器/独立 daemon，必须挂 DSH profile；不能直接部署到 Kubernetes。
10. **投递语义**：Outbox "先发送后回执"，崩溃窗口可能重复评论/消息；依赖通道幂等（按代码路径推断）。

### 8.3 演进建议（按收益/成本排序）

| 优先级 | 建议 | 落点 |
| --- | --- | --- |
| P0 | 把主 Session 的"评估"拆成独立角色/批量队列，或对低风险规则用确定性分类器，降低单点吞吐 | `src/app/assessment.ts`、`src/app/tools/main.ts` |
| P0 | 用 DSH 权限/沙箱替代 `danger-full-access`；为高风险命令加审批；把 `blockedCommands` 升级为 allowlist/路径校验 | `src/app/sessions.ts:152`、`src/executor/dsh.ts` |
| P1 | 抽象 Host Adapter（Session/工具/模型/HTTP），让领域层可跑在非 DSH 宿主或独立进程 | `src/app/runtime.ts`、`src/app/sessions.ts` |
| P1 | 多仓/多租户：在 `Source` 与 `Deployment` 上增加仓库维度，`stateDir` 按租户隔离 | `src/deployment.ts`、`src/core/model.ts` |
| P1 | 状态保留：`trigger/thread/disposition/effect` 定期归档；`ticket` 保留审计但压缩 payload | `src/app/store.ts`、`src/app/passes.ts` |
| P2 | 可观测：效果积压、评估时延、worker 成功率、通道失败率指标化；trace 贯穿 trigger→ticket | `src/app/http.ts`、`src/infra/health.ts` |
| P2 | 平台化：`prepare` 改为可配置 shell；路径校验支持 Windows drive letter | `src/executor/dsh.ts:254`、`src/deployment.ts:13` |
| P2 | 投递幂等：Outbox 增加"发送前占位 + 外部 id 回填"，或要求 Source 提供幂等键 | `src/app/outbox.ts` |
| P3 | 更多 Source：邮件/Jira/Linear，验证 `SourceKind` 协议的普适性 | `src/sources/kind.ts` |

---

## 9. 阅读建议

### 9.1 推荐顺序（约 2 天）

| 阶段 | 读什么 | 目标 |
| --- | --- | --- |
| 30 分钟 | `README.md`、`docs/000-philosophy.md`、`docs/001-domain.md` | 建立术语：触发器/线程/评估/授权/工单/指派/订阅/频道 |
| 1 小时 | `src/core/model.ts`、`src/core/engine.ts` | 看清聚合与用例边界；记住"只有 Engine 能写" |
| 1 小时 | `src/core/intake.ts`、`src/core/evals.ts`、`src/core/tickets.ts` | 走通"事件→门禁→评估→建单→指派" |
| 1 小时 | `src/policy.ts`、`docs/002-authorization.md` | 理解 explicit/inferred、mandate、admission 表、策略版本 |
| 2 小时 | `src/app/runtime.ts`、`src/app/passes.ts`、`src/app/effects.ts`、`src/app/store.ts` | 理解组合根、2s tick、持久化效果、崩溃恢复 |
| 2 小时 | `src/app/sessions.ts`、`src/app/assessment.ts`、`src/app/tools/main.ts` | 理解主 Session 的卡片投递与工具面 |
| 3 小时 | `src/executor/dsh.ts`、`src/app/tools/executor.ts` | 理解 worker 准备、启动、输入、报告、重试 |
| 2 小时 | `src/sources/github.ts`、`src/sources/github-trigger.ts`、`src/sources/kind.ts` | 理解来源适配与触发器归一化 |
| 半天 | `docs/007-architecture.md`、`tests/*.spec.ts` | 对照设计意图与测试覆盖，确认边界条件 |

### 9.2 调试/断点位置

| 现象 | 首选断点 | 说明 |
| --- | --- | --- |
| 事件没进来 | `src/sources/github.ts:280` `pollRound` | 看游标、通知过滤、范围判断 |
| 事件进来但没评估 | `src/core/intake.ts:19`、`src/policy.ts:167` | 看 disposition 是 filtered、duplicate 还是已归工单 |
| 评估不投递 | `src/app/assessment.ts:104`、`src/app/effects.ts:103` | 看效果是否被限流或已在运行 |
| 主 Session 不决策 | `src/app/tools/main.ts:203-224` | 看卡片是否投到正确 Session、工具参数是否匹配 |
| 工单不启动 | `src/executor/dsh.ts:247`、`:424` | 看 prepare 输出、worker slot、maxWorkers |
| worker 收不到输入 | `src/executor/dsh.ts:290`、`src/app/sessions.ts:162` | 看 ticket input 状态与 Session 忙闲 |
| 消息没发出去 | `src/app/outbox.ts:27`、`src/app/effects.ts:103` | 看 Channel 配置、receipt、重试次数 |
| 重启后状态不对 | `src/app/store.ts:70-91`、`src/app/runtime.ts:201` | 看 schema 版本、锁、未完成 effect |

### 9.3 项目内文档对照

`docs/007-architecture.md` 是最接近本文的项目自述，粒度更细（含模块表、持久化、模型面接口与开放问题）；`docs/003-execution.md` 讲工单/指派状态机；`docs/004-prompts.md` 讲提示词拼装；`docs/005-panel.md` 讲面板信息架构。建议先读本文建立骨架，再用项目文档补细节。

---

## 10. 未核实与推测

| 项 | 状态 | 说明 |
| --- | --- | --- |
| Windows 端到端可用性 | **部分推测** | 有 `pwsh` preset，但 `prepare` 固定 `sh -c`、`stateDir` 需 `/` 开头；未在 Windows 上实跑验证 |
| Outbox 重复投递窗口 | **按代码路径推断** | 先发送后回执，崩溃可能重复；通道是否幂等未在源码中强制 |
| `auto` 模式的实际启用情况 | **未核实** | schema 默认 `eval.mode = observe`（`policy.ts:84`）；`auto` 需显式开启，实际 profile 以部署为准 |
| 主 Session 的模型/上下文上限 | **未核实** | 由 DSH role-models 与宿主配置决定，本仓库只存 `eval.model`/`executor.model` |
| 飞书适配的完整度 | **未核实** | 插件默认 `disabled: true`；仅按 `src/sources/feishu.ts`、`feishu-loops.ts` 与 skills 阅读，未做线上验证 |
| `docs/007` 与源码的细微偏差 | **以源码为准** | 项目文档可能滞后；本文所有类/函数/行号已按当前源码核对 |
| 论文五模块与本仓库的逐项映射 | **参考 `_digest`** | `_digest/SuperAgent-原型对照分析.md` 给的是分析视角，不作为源码事实 |

---

**结论**：`dsh-superagent` 的价值不在"又一个 Agent 框架"，而在把**多来源事件、授权凭据、工单生命周期、主/工双 Session、崩溃可恢复的效果队列**组合成一个可运行的最小治理闭环。读懂它的关键不是从 `src/index.ts` 顺着 import 读，而是先接受"领域层不碰宿主、领域写只走 Engine、跨 Session 动作走 Effects"这三条约束，再按"触发器→评估→工单→worker→回写"的主链路走一遍。

---

## 修订记录

| 版本 | 说明 |
| --- | --- |
| v1 | 首版：按 `_arch/12-hermes-agent-架构.md` 的章节体例撰写；全部代码路径、类名、函数名与行号按当前源码核对（`src/` 111 文件、48 个 spec） |
