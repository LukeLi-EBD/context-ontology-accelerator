# DeepSeek Super-agent 原型：代码 vs 文章 对照分析

分析对象：`https://github.com/deepseek-ai/dsh-superagent-prototype`
对应文章：《Super-agent 设计探索：迈向更自主的 Agent 系统》（DeepSeek Harness 团队，2026-10-31 晚，公众号）

分析时间：2026-11-03
本地路径：`D:\AgentABC\dsh-superagent-prototype`

---

## 0. 先给结论

| 问题 | 答案 |
|---|---|
| 这是能跑的代码吗？ | **是**。TypeScript 3 万行，类型检查 0 错误、构建成功、1197 个测试里 1158 个通过（我本地实测）。 |
| 下载下来就能用吗？ | **不能**。它不是独立程序，是 **DeepSeek Harness 的一个插件包（bundle）**，必须先装 DSH、配模型、开一个专用 GitHub 账号。 |
| 和文章匹配吗？ | **前半段吻合得惊人，后半段完全是空的。** 五大模块里：2 个完整实现、1 个半实现（靠宿主）、2 个零实现。 |
| 为什么提交？ | 文章是主体，代码是**可执行附录**。README 自己承认「为公开发布改造过，与文章描述的实现不完全一致」。 |
| 处于什么阶段？ | **工程原型 v0.1.0**，单仓库 / 单机 / 双渠道 / Unix 部署。不是 demo，也远不是产品。 |

一句话概括这个仓库的性质：**它把文章第 1～3 节写成了真代码，第 4～6 节留在了 PPT 里。**

---

## 1. 仓库事实（客观数据）

| 项 | 值 |
|---|---|
| Star / Fork | **15,122 / 1,616**（2026-11-03） |
| 提交数 | **1 个**（2026-10-31 12:05 UTC，`feat: add the dsh-superagent research prototype`） |
| 协议 | MIT |
| 文件 / 体积 | 216 个文件 / 3.0 MB |
| 语言 | TypeScript（147 个 .ts + 30 个 .tsx） |
| 文档 | `docs/` 9 篇共 1,973 行；`prompts/` 438 行；README 39 行；SETUP 79 行 |
| 测试 | 59 个 spec 文件、1,197 个用例、14,960 行；`it.skip` 数量 **0** |
| 版本 | `package.json` 写 `0.1.0`，`private: true`（不发布到 npm） |

代码分层（行数）：

| 层 | 文件 | 行数 | 职责 |
|---|---:|---:|---|
| `src/core` | 15 | 2,088 | 领域模型：Engine + Intake/Evals/Tickets/Assignments/Replies 五个部件 |
| `src/app` | 38 | 5,292 | 胶水：Runtime、Store(SQLite)、Effects、Settings、Prompts、Tools、HTTP、Views |
| `src/executor` | 2 | 838 | DshExecutor + 后台作业管理（worker 槽位、job/subagent 收尾） |
| `src/sources` | 16 | 2,059 | GitHub 与飞书两个 Source（触发、轮询、频道、读） |
| `src/infra` | 5 | 347 | CLI 传输、进程环境/shims、健康板、路径 |
| `src/client` | 26 | 4,037 | Web 面板（React），中英双语 |
| `tests` | 65 | 14,960 | 含一个模拟 DSH 宿主 `fixtures/host.ts` |

注意一个比例：**测试代码和产品代码差不多一样多**。这是"认真在写"的信号，不是发个 demo 蹭热度。

---

## 2. 我实测它到底能不能跑

在 `D:\AgentABC\dsh-superagent-prototype` 下执行（pnpm 11.7.0 / Node 22.22.2）：

| 步骤 | 结果 |
|---|---|
| `pnpm install --frozen-lockfile` | ✅ 17.7 秒装完，所有 `@deepseek-ai/dsh-*` 依赖都在 **npm 公开仓库**上（`dsh-agent` 有 42 个版本） |
| `pnpm typecheck`（tsc --noEmit） | ✅ **0 错误** |
| `pnpm build`（tsdown） | ✅ 2.5 秒，产出 `lib/` 693 KB（index 450 KB + github-watch + feishu-watch + client） |
| `pnpm test`（vitest） | ⚠️ **1,158 通过 / 39 失败**（59 个文件里 50 个全绿） |

**39 个失败全是 Windows 环境问题，不是逻辑问题**，看失败点就很清楚：

- `expected [438, 438] to deeply equal [448, 384]` —— 断言 `chmod 0700`/`0600` 的文件权限位，Windows 的 `statSync().mode` 不返回 POSIX 位
- `environment.spec.ts` 一整组 —— worker 的 `sh` 包装脚本（shim），Windows 没有 `sh`
- `service-script.spec.ts` —— 依赖 `ps -p` 和 `tmux`
- `deployment.spec.ts` / `docs.spec.ts` —— 路径分隔符与反引号格式

**这个发现有实际意义**：`scripts/dsh-superagent`（250 行 Python）第 166 行硬性要求

```python
if not dsh or not shutil.which('tmux'):
    raise RuntimeError('Both dsh and tmux must be on PATH.')
```

所以 **官方运维脚本是 Unix-only 的**（tmux 会话托管 DSH 进程）。代码本身跨平台（worker preset 里用 `!!js process.platform === 'win32'` 切 pwsh），但你在这台 Windows 上照着文档走，最后一步会卡住。

---

## 3. "能跑"的三个层次，它只达到第 2 层

很多人说"能跑"其实混了三件事，这里必须拆开：

| 层次 | 含义 | 它达到吗 |
|---|---|---|
| L1 能编译 | 代码语法/类型自洽，能出构建产物 | ✅ 已实测通过 |
| L2 能测试 | 领域逻辑在模拟宿主上跑通 | ✅ 1,158/1,197；模拟宿主 `tests/fixtures/host.ts` 是官方自己写的 |
| L3 能端到端跑起来 | 装 DSH + 配模型 + 真实 GitHub 账号 + 真仓库 + 真 PR | ⚠️ **路径存在，但需要你自备全部外部条件** |

L3 的完整前置条件（`docs/006-deployment.md` + `SETUP.md`）：

```
Node 22.19+ / pnpm / git 2.32+ / Python 3.8+ / tmux
+ DeepSeek Harness 0.2.1（npm 全局装）
+ 一个模型 provider（DSH 里配）
+ 一个【专用的】GitHub 账号（不能是你自己的）
+ gh CLI 2.48+，且只登录那个账号
+ 一个 github.com 上的仓库（不支持 GitHub Enterprise）
+ 可选：飞书 bot + lark-cli 1.0.90
```

然后：

```sh
npm install -g @deepseek-ai/dsh@0.2.1-rc.3
pnpm install && pnpm build
dsh superagent --from-default-profile web --dump-config > /dev/null
dsh plugin --profile superagent add "link:$PWD"
```

**最有说服力的一句话在 README 第 13 行**：

> Setup has many steps, so an agent does it with you. Ask your coding agent: *"Read SETUP.md in this repository and set up dsh-superagent with me."*

连官方都没信心写一条命令装完，要靠另一个 agent 陪你问 9 个问题（专用账号、仓库、白名单、checkout 路径、commit 身份、要不要自动合并……）。**这不是产品级安装体验，是研究原型的安装体验。**

---

## 4. 五大模块逐条对照

文章的五大模块是：**双层架构、事件驱动、异步多信道交互、存算分离、外部 Watchdog**。

### 4.1 双层架构 Router / Worker —— ✅ 完整实现，且最忠实

| 文章设计 | 代码实现 | 位置 |
|---|---|---|
| 常驻 Router 层，只分派不干活 | **Main Session**（代码里叫 `orchestrator`），专属 preset `dsh-superagent-router` | `cordis.patch.yml` |
| Router 可以不配 Bash | Router 有 bash，但 `tool-fs` 被设成 `write: false, edit: false`；不读代码是**提示词约束而非工具限制**（007 明说） | `src/app/sessions.ts` |
| Router 用轻量模型即可 | 支持按角色分别指定模型（`role-models.ts`），Eval 用一个、Executor 用一个 | `src/app/role-models.ts` |
| Worker 上下文隔离、独立目录 | 每个 Ticket 一个 Session 名 `worker-<ticketId>` + 一个独立目录，默认 `<stateDir>/work` | `src/executor/dsh.ts` |
| Worker 用最强模型、挂完整工具 | preset `dsh-superagent-worker`，允许 subagent（走 DSH `standard` 预设） | `cordis.patch.yml` |
| Worker 不直接对人说话，只向 Router 汇报 | 6 个工具，**没有** `ask_user_question` / `present`，只能 `orchestrator_report` | `src/app/tools/executor.ts` |
| Router 每步长输入短输出，靠批处理摊薄 | 每次 `passes` 轮询（**2 秒一次**）把同一 Thread 排队的 Trigger **合并成一次 Eval** | `src/app/passes.ts:28`、`src/core/engine.ts:75` |

工具数量对得上文章的定位：**Router 14 个工具，Worker 6 个工具**（007 文档明列）。Router 那 14 个里有一半是 `orchestrator_read` / `orchestrator_route` / `orchestrator_eval*`，确实是"看和派"。

> **差异**：文章说 Router 层"内部不必局限于单个 Session，部分逻辑未必需要 LLM"。仓库里是**判定的单个常驻 LLM Session**——正好是文章说的"团队选择最直接的实现"。

### 4.2 事件驱动 + 两级过滤 —— ✅ 实现，而且比文章更制度化

文章讲的 Fast Path / Slow Path，在代码里是**两个完全分离的东西**：

**Fast Path（确定性、零 token）= `gate()`**，`src/policy.ts:191-211`

```ts
gate(trigger, thread, tickets) {
  if (!trigger.human) return machineGate(trigger)          // 机器人/CI 走另一条
  const allowed = allowedSender(settings, trigger.actor)   // 白名单
  const scope = listened(sources, trigger.source, ...)     // 这个群/这个仓库关不关注
  const cell = admissionCell(!!allowed, !!trigger.addressed)
  if (allowed && trigger.addressed) return { strength: 'explicit', via: 'addressed' }
  if (admission === 'explicit') return { strength: 'explicit' }
  if (admission === 'inferred' && mode !== 'off') ...
  return { admissible: false, reason: 'not_a_member' }
}
```

这就是文章说的"针对事件来源、群组范围、用户白名单等确定性条件直接代码快筛"。**它跑在任何 LLM 调用之前。**

**Slow Path（语义判断）= `MasterAssessor`**，`src/app/assessment.ts`（282 行）
通过 `orchestrator_eval` 给模型一个**有界的**上下文窗口，模型回 `orchestrator_eval_decide`。

**仓库比文章多做了三件事**（文章没细讲，代码里是硬约束）：

1. **准入表是 3×3 的**：`名单内/外` × `@了没@`，每格可选 `explicit / inferred / ignore`，默认值是保守的（未列名单且没 @ 你 → `ignore`）
2. **Policy 有版本号**，每个授权（Mandate）记录它是在哪个版本下被批准的。**改规则不会撤销正在跑的工单**，只发一条"策略已变"的通知；工单恢复前会**重新校验**授权
3. **三档模式 `off / observe / auto`，默认 `observe`** —— 推断出的工作**全流程评估、但不执行**，只记一条 `wouldAccept`

第 3 条极其重要，它直接对应文章里那句"系统启动时的全局预设值为观察模式"。**代码里确实是 `observe` 默认**（002 的表格 + `src/admission.ts`）。

### 4.3 订阅直通 —— ✅ 实现，连"交回"都做了

文章：*"已订阅，Fast Path：同一 Thread 下后续事件由程序直通已订阅 Worker……若新事件超出当前任务范围，Worker 也可取消订阅或交回 Router 层重新分派。"*

代码：`Subscription` 是 Thread ↔ Ticket 的多对多关系，扇出（fan-out）**绕开 gate 和 Eval**，且"不检查是谁发的"。配套三个工具：

| 工具 | 对应文章哪句 |
|---|---|
| `orchestrator_thread_follow` | Worker 主动订阅相关 Thread 做上下文 |
| `orchestrator_thread_unrelated` | "取消订阅"（只丢自己这条） |
| `orchestrator_trigger_handback` | "交回 Router 重新分派"（每 Trigger 只能交回一次，带理由） |

甚至连**权限边界**都想到了（文章没提）：订阅只给上下文，**不给授权**。一个已结束的工单被人在 Thread 里回复时，可以在**原授权**下复活，不需要重新走 Eval——但"上下文订阅"不会复活它。

> ⚠️ **但文章的三个数字无法复现**：关掉直通后 Router 决策 +30%、读缓存 token 23.23M→31.77M（+37%）。仓库里**没有任何 benchmark 目录或压测脚本**，也没有合成负载生成器。这几个数字只能信文章。

### 4.4 Inline & Spill + 链式召回 —— ✅ 实现，而且量化得很精确

文章花了一整节讲"把上下文窗口当 Cache 管"，代码里落实为具体数字：

| 文章概念 | 代码实现 | 位置 |
|---|---|---|
| 从最少信息开始（ID + 摘要） | 候选卡片、`{id, from, preview}` 50 字符存根 | `src/app/cards.ts` |
| 利用局部性 Inline 邻近内容 | Thread 窗口 = **前 5 条 + Trigger 前后各 5 条**；普通消息 400 字符，紧邻两条放宽到 1,200 字符 | 007「Result shapes」 |
| 超上限则 Spill + 留续读入口 | 截断时带 `chars` 字段和 read pointer，`orchestrator_eval_read` 按 id 展开 | 同上 |
| 链式召回（每一跳内联下一跳 ID） | `RESOURCES` 里 `trigger/<id>` → `thread/<key>` → `ticket/<id>` → `/assignments` `/inputs` `/transcript`，全部 `next_offset` 翻页 | `src/app/resources.ts` |

**这是全文匹配度最高的一块**。文章讲的是设计思想，代码里是"4,000 字符文本页、20 条列表、50 最大、8,000 上限"这种抠到字符的常数。

### 4.5 全双工异步 ReAct Loop —— ⚠️ 用了，但不是它实现的

文章：*"将耗时命令与子任务工具调用改为异步的 start() 和 stop()"*，并自己说明 **"这一异步任务机制已在 DeepSeek Harness 中实现，但尚未默认开启"**。

仓库的做法完全一致——**它不实现，它打开**：

- Worker preset 里 shell 的 `timeoutMs: 5000`：前台命令 5 秒没跑完，自动转后台作业
- `tool-jobs` 的 `waitTimeoutMs: 5000`：等 job 也只等 5 秒
- job 完成 → 唤醒 Session，把结果当新消息投递
- `orchestrator_ticket_request_status` 可以随时问 Worker 进展

还有一条很硬的约束（`src/app/sessions.ts` 的 `noWait` guard）：**Router 禁止 `sleep`、禁止 shell timeout > 30 秒、禁止 job 等待 > 5 秒**。理由写在 004：*"a blocked step delays new candidates"* —— Router 一卡住，新工单就进不来。

> 所以这一项准确表述是：**能力已具备，实现归属宿主（DSH），本仓库只负责配置和调度。**

### 4.6 多信道交互 —— ✅ 两个信道，❌ 缺邮件/日程

| 信道 | 状态 | 备注 |
|---|---|---|
| GitHub | ✅ | 通知、Issue、PR、CI、review thread 回复，全部有 |
| 飞书 | ✅ 但默认关闭 | `cordis.patch.yml` 里 `disabled: true`，要自己配 bot + lark-cli |
| 邮件 / 日程 | ❌ | 文章多处提到个人助手场景，代码里零实现 |

文章那条"简单有效的硬性规定：单次回复不超过 100 词"——**代码里就是一个常量**：

```ts
// src/infra/text.ts:3
export const IM_WORDS = 100
```

确认（acknowledgement）也被限制在 100 词，PR 的高密度交付要求放在 `prompts/team/delivery.md`（人工可编辑）。

### 4.7 存算分离 / BYOM —— ❌ 零实现

这是**最大的落差**。全文搜索 `watchdog|cloud|storage separ|compute|sandbox|remote` —— **0 命中**。

实际情况：

| 文章要素 | 仓库实际情况 |
|---|---|
| 计算（Agent Loop）在云端 | 本地 DSH 进程，`127.0.0.1:3082` |
| 状态（会话日志）与计算分离 | 本地 SQLite `<stateDir>/orchestrator.sqlite`，单文件、单进程独占（还用 `proper-lockfile` 加锁） |
| 环境留在原地、BYOM 接入 | 本地目录 + `git worktree`，`prepare` 命令在**同一台机器同一个 OS 用户**下跑 |
| 跨设备切换执行环境 | 无 |
| 间歇在线设备被唤醒后补跑 | 无 |

它确实做了**结构上的分离**（Store 是唯一写者、Session 可断点恢复、每个 Ticket 一个目录），但**物理上全在一台机器上**。文章说的"第一步把计算与状态分离""第二步把云端 Loop 与重状态环境解耦"，两步都还是设计。

### 4.8 外部 Watchdog —— ❌ 零实现

文章：*"在主系统外部配置了一个独立 Watchdog Session，用定时消息驱动它……由模型判断各 Worker 是否有实质进展、方向是否偏离整体目标。"*

代码里 `watchdog` **一次都没出现**。它有的是另一套东西（这套做得挺认真，但不是同一件事）：

| 有的 | 干什么 | 缺什么 |
|---|---|---|
| `HealthBoard`（`src/infra/health.ts`） | 每个部件一个健康项，一个写者，拒绝二次认领；连续失败 3 次才报错 | 只判"有没有报错"，不判"任务有没有进展" |
| `Effects` 持久化副作用队列 | 指数退避重试（2s→60s，reply 5s→300s）；`Later` 可延期不计失败 | 不判断"方向对不对" |
| 重启恢复 | 中断的 Assignment 带 recovery note 重启，提示"先查目录、git 历史、GitHub 再重复外部动作" | 不是外部独立进程 |
| SETUP 里的"每小时检查" | 让操作者用系统 cron 每小时后**检查服务是否活着**，死了就拉起 | 是"进程存活探测"，正是文章说**不够**的那种 |

文章的批评很准确：*"仅靠传统进程存活探测或监控脚本是不够的，因为许多异常并非进程崩溃，而是模型在执行中陷入无效循环或偏离目标。"* —— **而这个原型恰好就停在"进程存活探测"这一层。**

### 4.9 投机执行（后台先试、有价值才交付）—— ❌ 基本没有

文章举的例子是"群里有人反馈问题，Agent 先在后台复现并找修复方案，确认有价值才交付，否则全程沉默"。

仓库里的近似物只有半个：`observe` 模式会**完整跑一遍评估**（真的调模型、真的匹配规则），然后把结论记成 `wouldAccept` 而不执行。这是"**投机评估**"，不是"**投机执行**"。真正"后台先跑起来、可能白跑"的那部分没有。

---

## 5. 覆盖率总表

| # | 文章模块 | 状态 | 完成度判断 |
|---|---|---|---|
| 1 | 双层架构（Router / Worker） | ✅ 完整 | 95%：连工具集裁剪和 5 秒 shell 上限都照做了 |
| 2 | 事件驱动 + 两级过滤 | ✅ 完整 | 100%+：额外做了 Policy 版本、Mandate、准入表、三档模式 |
| 3 | 订阅直通（Thread 订阅） | ✅ 完整 | 90%：机制全有；文章的定量收益无法复现 |
| 4 | Inline & Spill + 链式召回 | ✅ 完整 | 90%：字符数都抠到位了 |
| 5 | 全双工异步交互 | ⚠️ 半 | 40%：机制在宿主里，这里只是配置 + 调度 |
| 6 | 多信道（IM/PR/邮件/日程） | ⚠️ 半 | 50%：GitHub + 飞书；邮件日程为 0 |
| 7 | 存算分离 / BYOM | ❌ 无 | 0%：单机 SQLite + 本地进程 |
| 8 | 外部 Watchdog（模型判进展） | ❌ 无 | 0%：只有健康板 + 重试 + 重启恢复 |
| 9 | 投机执行 | ❌ 基本无 | 10%：只有 observe 模式的"投机评估" |

**算术**：文章正文 7 节，代码覆盖到第 3 节末尾。**"调度与路由"这一半做完了，"持久在线与自愈"这一半没开始。**

---

## 6. 文章明说"没实现"的地方（不是我猜的）

README 第 5 行，官方自己写：

> We have adapted it for publication, so it is **not identical** to our internal version or the implementation described in *Exploring Super-agent Design*. **Some designs discussed in the article are directions for future development and are not implemented in this prototype.**

`docs/007-architecture.md` 结尾还留着两个"Open questions"：

1. **Trust**：哪些 Trigger 字段可信（actor、Thread 成员关系），哪些不可信（正文、引用）
2. **Deployment isolation**：把 agent 的 profile 钉在独立的 DSH 安装上，避免别处升级把它搞坏

这两条正好对上文章第八节的"安全与隐私"和"组织扩大后的上下文边界"。**作者知道洞在哪，只是没堵。**

### 安全模型：比文章说的更"裸"

`docs/006-deployment.md` 的「Permissions and isolation」写得很直白：

> Both presets run with **`danger-full-access`** as the operator's OS user... **A worker can execute programs by path and read the operator's home directory.** For isolation, use a dedicated OS account containing only the agent's credentials.

`docs/003-execution.md` 第 80 行更直接：

> These wrappers and directories establish **defaults, not a security boundary**.

翻译一下：Worker 以你的 OS 用户身份、无审批、全权限跑，能读你的 home 目录，所谓的"命令包装"只是**默认值**，用绝对路径就能绕过。文档给的缓解方案是"开个专用系统账号"——**把安全责任推给运维**。

这跟文章"云端 Agent 接入端侧凭据存在被入侵和提示词注入风险"的自我批评是一致的，但**原型阶段选择了先跑通、后谈安全**。

---

## 7. 那为什么还要提交上去？

三个理由，按重要性排：

**① 文章需要一个可讨论的实物。**
1,973 行文档 + 3 万行代码，比例本身就是答案：**文档是主体，代码是证据**。文章讲的是"相似设计约束会导出相似架构选择"这种抽象论断，没有代码就只是空谈；有了代码，别人才能指着 `gate()` 说"你这个准入表设计有问题"。15,122 star 说明这个策略奏效了——社区讨论的是一个具体实现，而不是一段愿景。

**② 内部实例的删减版，用来收外部反馈。**
文章说内部实例"已持续运行，参与问题复现修复、代码审查和 Harness 自身的迭代"。但内部版绑着内部 IM、内部凭据、内部仓库、集群调度。**要给别人看，必须把内部依赖全剜掉**，于是只剩"一个 GitHub 仓库 + 可选飞书"。这不是能力缩水，是**脱敏的必然结果**。

**③ 它真的是一份工程遗产，不是一次性 demo。**
证据：820 个测试用例 + 0 个 skip；`tests/docs.spec.ts` 会校验"007 的模块表是否列全了 src 下每个文件"；`tests/class-docs.spec.ts` 会校验"每个类前面都有 JSDoc"。**写这种测试的人，是打算长期维护的**，不是发完就跑。而且 README 明说"much of the engineering done by coding agents"——**这仓库本身就是一个"AI 写的、AI 也在维护的"样品**，这本身就是它想证明的东西。

反过来说，**如果它是完整版，就不会只有 1 个 commit、不会 `private: true`、不会被文档劝你"用专用 OS 账号隔离"**。

---

## 8. 当前处于什么阶段（一句话判断）

> **这是一个"v0.1 工程原型"：领域模型和调度骨架已经工程化到可以直接借用的程度，但持久在线、跨机执行、自愈这三件让它配得上 "Super" 的事，一件都还没做。**

具体刻度：

| 维度 | 刻度 |
|---|---|
| 领域建模 | ★★★★★ 可以当教科书看（Source/Trigger/Thread/Eval/Mandate/Ticket/Assignment/Subscription 八个概念，还有一节「Rejected concepts」专门写为什么**不**加某概念） |
| 调度与路由 | ★★★★☆ 生产可用级别的规则密度 |
| 可运行性 | ★★★☆☆ 能编译能测试；端到端要你自备 DSH + 账号；Windows 上运维脚本跑不通 |
| 持久在线 | ★☆☆☆☆ 单机单进程，靠 cron 拉活 |
| 安全隔离 | ★☆☆☆☆ 自认"不是安全边界" |
| 文档 | ★★★★★ 2,000 行、按序阅读、每篇只依赖前一篇，还带中文术语表 |

**最值得学的一点**，跟技术无关：`docs/001-domain.md` 有一节叫 **Rejected concepts**（被否决的概念），逐条写"为什么**不**引入 Principal、为什么**不**让 Eval 自己排延迟任务、为什么**不**在 Policy 变更时取消正在跑的工单"。**一份设计文档肯写"我们决定不做什么、为什么"，质量立刻不一样。** 这比多写 5,000 行代码有价值。

---

## 9. 如果你想自己跑起来，缺什么

| 缺的 | 怎么补 | 我能不能代劳 |
|---|---|---|
| DeepSeek Harness | `npm i -g @deepseek-ai/dsh@0.2.1-rc.3` | ✅ 能装 |
| 模型 provider | 在 DSH 里配（要 API key） | ⚠️ 需要你的 key |
| **专用** GitHub 账号 | 注册一个新号，接受仓库邀请 | ❌ 必须你本人 |
| gh CLI | `winget install GitHub.cli`，登录那个新号 | ⚠️ 登录要你扫码 |
| 一个 github.com 仓库 | 新建或指定 | ❌ 你决定 |
| tmux | **Windows 没有**，运维脚本 `scripts/dsh-superagent` 直接抛错 | ⚠️ 需要 WSL 或改脚本 |

**现实建议**：想在 Windows 上体验，走 **WSL2 + Ubuntu** 最省事（你已经有 WSL 环境和 Docker）。直接在 Win32 下跑，会卡在 `tmux` 那一步。

**但如果目的只是"看懂它怎么设计的"**，读 `docs/000 → 001 → 002 → 003`（共 500 行），比跑起来划算得多。**这个仓库的价值 90% 在文档，10% 在能跑。**
