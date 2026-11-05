<!-- 本文档已脱敏用于公开发布，原始内容见内部仓库 -->
# D:\AgentABC 里的 AI 项目：核心代码摘要 + 最简版内核

> 生成时间：2026-11-03 ｜ 分析范围：`D:\AgentABC` 下 5 个 AI 相关仓库（hermes-agent / pi / deepseek-harness / nanobot / altimate-code）
> 目的：不读十万行，只读「能解释架构的几百行」。

---

## 0. 结论先看

这五个项目表面上天差地别（Python / TypeScript、CLI / Web / 插件树），但**内核是同一个东西**。把各自的框架糖剥掉，agent 内核只剩五件事：

| # | 共同骨架 | 一句话 | 各家怎么叫 |
|---|---|---|---|
| 1 | **统一响应类型** | 厂商差异只在一个 dataclass 里收敛 | hermes `NormalizedResponse` ／ pi `AssistantMessage` ／ dsh `StreamChunk` |
| 2 | **单一出网口** | 全项目只有一个地方发 HTTP，上层不认识任何厂商 | hermes `ProviderTransport` ／ pi `streamFn` ／ dsh `LlmAdapter.stream` |
| 3 | **工具注册表** | `schema + handler + 可用性探针`，import 即注册 | hermes `tools/registry.py` ／ pi `AgentTool` ／ dsh `ToolRuntime` |
| 4 | **请求副本治理** | 压缩/清洗只作用在副本上，落盘历史永不改写 | hermes `api_messages` ／ pi `transformContext` ／ nanobot `messages_for_model` |
| 5 | **先落盘再执行** | 先把 `assistant(tool_calls)` 写进日志，再跑工具 | hermes `turn_tool_round.py:130` ／ dsh `Session.append` ／ altimate V2 `settle` |

第 5 条是最反直觉、也最容易被自己写 agent 时忽略的：崩溃恢复、断点续跑、UI 回放全都依赖它。

配套产物：
- **`mini_agent.py`（343 行，单文件，可直接跑）** —— 上面五条的最小实现，同时也是四家的对照标本
- 本文 —— 每家的「最核心的 6~10 个文件」+ 主循环原文 + 阅读顺序

---

## 1. 五个项目一览

| 项目 | 语言 | 规模 | 它到底是什么 | 主循环位置 | 主循环行数 |
|---|---|---|---|---|---|
| **hermes-agent** | Python 3.11+ | 19725 文件 / 359MB | 自改进式个人 agent，同一内核跑 CLI / 20+ 消息平台 / TUI / Electron；会从经验里造 skill | `agent/conversation_loop.py:1656` | 1867（整文件） |
| **pi** | TypeScript monorepo | 1922 文件 / 37MB | 极简 coding agent，内核只有 **6 个文件 2519 行**，其余全是壳 | `packages/agent/src/agent-loop.ts:163` | 949（整文件，循环本体 ~160） |
| **deepseek-harness** | TypeScript × 68 包 | 16083 文件 / 198MB | 「一切皆插件」的 agent harness（Cordis 依赖注入），日志即真相 | `packages/core/agent-loop/src/agent.ts:298` | 705 |
| **nanobot** | Python | 597 文件 / 85MB | 可自托管的常驻个人 agent，以聊天渠道为入口；自带「核心行数」统计脚本 | `nanobot/agent/runner.py:272` | 1353 |
| **altimate-code** | TypeScript + Bun | 3669 文件 / 81MB | OpenCode 的 fork，塞进一整套**确定性**数据工程工具（78 个 SQL/dbt/血缘工具） | V1 `session/prompt.ts:1031` ／ V2 `core/session/runner/llm.ts:380` | 4825 ／ **408** |

值得注意的是「内核有多薄」这件事：

- pi 整个 agent 内核 **2519 行 / 6 文件**，其中主循环 949 行
- deepseek-harness 的循环本体 **705 行**，但它靠 68 个包做组合
- altimate 重写后的 V2 循环 **408 行**（Effect-TS），比 V1 的 4825 行小 12 倍
- nanobot 自称「超轻量」，按它自己的脚本口径核心 **9209 行 / 28 文件**，但**不含 LLM 层和工具层** —— 加回去「能真跑起来」要 ~18.2k 行

> 一句话：**框架可以很大，循环总是很小。** 大的是「怎么把它接进真实世界的缝隙」——审批、沙箱、持久化、渠道、压缩、多租户。

---

## 2. hermes-agent（Python，最值得抄「工程约束」的一家）

### 2.1 定位
自改进 agent：从经验中创建 skill，使用中改进 skill。同一 core 跑在 CLI / ~20 个消息平台网关 / TUI / Electron 桌面端。两条写在 `AGENTS.md` 里的铁律：**每会话 prompt caching 神圣不可破坏（唯一例外是压缩）**；**core 是窄腰，能力放边缘**。

### 2.2 主循环：`agent\conversation_loop.py:1656-1703`

```python
1656  while _prelude_action != "break" and (
1657      (s.api_call_count < agent.max_iterations and agent.iteration_budget.remaining > 0) or agent._budget_grace_call
1658  ):
1659      if _run_phase(begin_iteration, agent, s).action == "break": break
1661      _run_phase(prepare_iteration, agent, s)
1662      _run_phase(assemble_api_request, agent, s)
1663      _pg = _run_phase(run_preflight_gate, agent, s)
1664      if _pg.action == "return": return _pg.result
...
1676      early_result = _run_api_retry_loop(agent, s)
...
1692      _v = _run_phase(run_tool_round if s.assistant_message.tool_calls else finish_text_response, agent, s)
```

它**不是**一个 2000 行的 while，而是：所有循环局部变量装进 `_LoopState`（1388-1468），每个阶段是 `agent/turn_*.py` 里的一个函数，靠 `_run_phase()` 反射注入状态、回写 verdict（`action ∈ {fallthrough, continue, break, return}` + `result`）。改行为 = 改一个 ~300 行的 `turn_*.py`。

**这是最值得学的一条工程约束**：重试、打断、溢出、恢复、压缩各自独立可测，而不是纠缠在一个函数里。

### 2.3 三处「接口代码」

**① 统一响应** `agent\transports\types.py`（98 行，全文即契约）

```python
15  @dataclass
16  class ToolCall:
26      id: str | None
27      name: str
28      arguments: str          # JSON 字符串
29      provider_data: dict | None   # 协议私有状态逃生舱
60  @dataclass
61  class NormalizedResponse:
68      content: str | None
69      tool_calls: list[ToolCall] | None
70      finish_reason: str
71      reasoning: str | None = None
72      usage: Usage | None = None
```

`provider_data` 这个「逃生舱」是必需的：Gemini 的 `thought_signature`、Codex 的 reasoning items、Anthropic 的 reasoning_details 必须原样回放，否则多轮必 400。

**② 传输抽象** `agent\transports\base.py`（53 行）

```python
12  class ProviderTransport(ABC):
20      def api_mode(self) -> str
24      def convert_messages(self, messages, **kwargs) -> Any
28      def convert_tools(self, tools) -> Any
32      def build_kwargs(self, model, messages, tools=None, **params) -> dict
39      def normalize_response(self, response, **kwargs) -> NormalizedResponse
```

已注册 4 种：`chat_completions` / `codex`(Responses) / `anthropic`(Messages) / `bedrock`(Converse)。

**③ 工具注册** `tools\registry.py:709`

```python
709  def register(self, name, toolset, schema, handler, check_fn=None,
                 requires_env=None, is_async=False, ..., execution_timeout=None):
```

`check_fn` 在**导出 schema 时**过滤（不适用的工具根本不进请求 → 既省 token 又避免 400），`handler(args, **kw) -> str` 强制返回字符串。注册是 import 副作用——新增工具 = 新增一个文件，不改任何中心列表。

### 2.4 最小示例（现成的，不用自己写）
- **`D:\AgentABC\hermes-agent\mini_swe_runner.py`（406 行）** ← 最重要。一个**完全不 import AIAgent** 的独立最小 agent，自带 tool schema、自带 while、自带工具执行。主循环在 275-306 行。
  ```bash
  python mini_swe_runner.py --task "Create a hello world Python script" --env local
  python mini_swe_runner.py --task "List files" --env docker --image python:3.11-slim
  ```
- 最短的 `AIAgent(...)` 构造：`evals\output_caps_local_capture.py:79`

### 2.5 核心文件 Top 8

| # | 路径 | 行数 | 读它为什么 |
|---|---|---|---|
| 1 | `agent\conversation_loop.py` | 1867 | turn 主循环 + `_LoopState` + `_run_phase` |
| 2 | `run_agent.py` | 1555 | `AIAgent` 门面，14 个 mixin 组装 |
| 3 | `agent\turn_tool_round.py` | 313 | 一个工具轮的完整语义（校验→去重→落盘→执行→压缩） |
| 4 | `model_tools.py` | 993 | `handle_function_call()` 工具调度总闸（hooks/审批/截断） |
| 5 | `tools\registry.py` | 1086 | 注册表 + AST 自动发现 |
| 6 | `agent\transports\types.py` + `base.py` | 98 + 53 | 所有厂商差异的收敛点 |
| 7 | `agent\context_compressor.py` | 5825 | 阈值(3002) + 两段式压缩(5528) |
| 8 | `hermes_state.py` | 1718 | `SessionDB` 门面（schema 在 `hermes_state_common.py:451`） |

跳过：`gateway/`（20 个平台 adapter，5288 行）、`hermes_cli/`、`apps/`（Electron 4176 文件）、`tests/`（6804 文件）。

### 2.6 三个可直接抄的设计
1. **prompt 分层字节稳定**（`agent\system_prompt.py:730`）：stable → context → volatile 三层，越易变越靠后，最长公共前缀越长 cache 命中越高；system prompt 整个会话只构建一次并存 DB。
2. **两段式压缩**：Phase1 本地剪旧 tool result（不花钱），Phase2 才用小模型摘要中段；保护 head + token 预算 tail。
3. **先落盘后执行**（`turn_tool_round.py:130-133`）：注释写得很直白——崩溃恢复必须能看到已执行的块。

---

## 3. pi（TypeScript，最值得抄「循环的纯净度」）

### 3.1 定位
TS monorepo，依赖方向 `tui → coding-agent → agent → ai → telemetry`。**`packages/agent` 只有 6 个文件 2519 行，是整颗心脏**；`coding-agent` 7.6 万行全是壳（工具、会话树、压缩、扩展）。

### 3.2 主循环：`packages\agent\src\agent-loop.ts:163-321`

文件头两行注释就把设计说完了：

```
1  /**
2   * Agent loop that works with AgentMessage throughout.
3   * Transforms to Message[] only at the LLM call boundary.
4   */
```

双层 while（176-186）：

```ts
179   while (true) {                 // 外层：agent 本该停下后，又有排队消息进来
180     let hasMoreToolCalls = true;
183     while (hasMoreToolCalls || pendingMessages.length > 0) {   // 内层：工具调用 + 中途插话
```

一轮的核心（241-292）：

```ts
241   const message = await streamAssistantResponse(currentContext, config, signal, emit, streamFunction);
243   newMessages.push(message);
245   if (message.stopReason === "error" || message.stopReason === "aborted") { ... return }   // 错误不进异常通道
259   const toolCalls = message.content.filter((c) => c.type === "toolCall");
267   const executedToolBatch =
268     message.stopReason === "length"            // 输出被截断 → 这批工具调用参数可能是残的
269       ? await failToolCallsFromTruncatedMessage(toolCalls, emit)
270       : await executeToolCalls(currentContext, message, config, signal, emit);
272   hasMoreToolCalls = !executedToolBatch.terminate;
```

循环本身**不认识任何厂商、任何工具语义**。全部可变行为由 `AgentLoopConfig` 的 9 个回调注入（`agent\src\types.ts:193-342`）：`convertToLlm` / `transformContext` / `prepareRequest` / `prepareNextTurn` / `finishTurn` / `getSteeringMessages` / `getFollowUpMessages` / `beforeToolCall` / `afterToolCall`。

### 3.3 接口代码

**① 统一消息协议** `packages\ai\src\types.ts`（898 行）：`TextContent|ThinkingContent|ImageContent|ToolCall`（414-449）、`Usage`、`SystemMessage`（**system prompt 和 tool 声明都挂在 system 消息上**，546-562）、`ToolResultMessage`、`AssistantMessageEvent`（流式：start / text_delta / toolcall_end / done / error，806-822）。

**② Provider 契约** `packages\ai\src\types.ts:311`

```ts
311  export interface ProviderStreams {
312    stream(model: Model<Api>, context: TranscriptContext, options?: StreamOptions): AssistantMessageEventStream;
```

10 个实现：openai-completions / openai-responses / anthropic-messages / google-generative-ai / google-vertex / bedrock-converse / mistral / azure / codex / pi-messages。差异全部集中在 `convertMessages()` / `convertTools()` / `mapStopReason()` 三个函数里。

最简 provider 全文 15 行（`packages\ai\src\providers\deepseek.ts`）：

```ts
6  export function deepseekProvider(): Provider<"openai-completions"> {
7    return createProvider({
8      id: "deepseek", name: "DeepSeek",
10     baseUrl: "https://api.deepseek.com",
11     auth: { apiKey: envApiKeyAuth("DeepSeek API key", ["DEEPSEEK_API_KEY"]) },
13     api: openAICompletionsApi(),
```

**③ 工具类型** `packages\agent\src\types.ts:466`

```ts
466  export interface AgentTool<TParameters extends TSchema = TSchema, TDetails = any> extends Tool<TParameters> {
467    label: string;
473    prepareArguments?: (args: unknown) => Static<TParameters>;
478    outputSchema?: TSchema;
483    execute: (toolCallId, params: Static<TParameters>, signal?: AbortSignal,
487              onUpdate?: AgentToolUpdateCallback<TDetails>) => Promise<AgentToolResult<TDetails>>;
490    replay?: "never" | "safe";
498    executionMode?: ToolExecutionMode;      // "sequential" | "parallel"
499  }
```

### 3.4 最小示例（仓库自带，且参与 typecheck）
`packages\coding-agent\examples\sdk\`（14 个文件 791 行），最核心的 `01-minimal.ts` 全文 27 行：

```ts
8  import { createAgentSession } from "@earendil-works/pi-coding-agent";
10 const { session } = await createAgentSession();
13 session.subscribe((event) => {
14   if (event.type === "message_update" && event.assistantMessageEvent.type === "text_delta") {
15     process.stdout.write(event.assistantMessageEvent.delta);
19 await session.prompt("What files are in the current directory?");
```

另有 `05-tools.ts`（按名字开关工具）、`12-full-control.ts`、`docs/how-pi-works.md`（60 行高层导读）。
**最简工具样板**：`packages\coding-agent\src\core\tools\write.ts`（97 行全文）——TypeBox 声明 schema + `Operations` 接口注入 IO（可换 SSH 远端）+ 同路径写串行化。

### 3.5 核心文件 Top 8

| # | 路径 | 行数 |
|---|---|---|
| 1 | `packages\agent\src\agent-loop.ts` | 949 |
| 2 | `packages\agent\src\types.ts`（全部契约 + 9 个回调） | 539 |
| 3 | `packages\ai\src\types.ts`（统一消息协议） | 898 |
| 4 | `packages\ai\src\models.ts`（Provider 工厂 + 认证解析） | 1269 |
| 5 | `packages\ai\src\api\openai-completions.ts` | 1736 |
| 6 | `packages\agent\src\agent.ts`（有状态的壳） | 613 |
| 7 | `packages\coding-agent\src\core\agent-session.ts`（产品层总装） | 4428 |
| 8 | `packages\coding-agent\src\core\compaction\compaction.ts` | 1119 |

跳过：`packages/chord`（13k 行，与 agent 无依赖）、`durable`（25k，另一条产品线）、`env`、`evals`、所有 `test/`（共 12MB+）、`coding-agent/docs/`（2.9MB 含截图）。

### 3.6 最值得抄的三条
1. **system prompt / 工具声明也是消息**：`SystemMessage` 带 `sections` / `toolsAdded` / `toolsRemoved`，重放即得当前状态 → 对话可持久化、可分支、可回放，工具集能在会话中途改。
2. **压缩接在 `prepareNextTurn` 上**（`agent-session.ts:899-933`）：回合之间替换 context，而不是在循环里写 if。
3. **`stopReason === "length"` 时整批工具拒绝执行**（`agent-loop.ts:267-270`）——很容易漏但很关键。

---

## 4. deepseek-harness（TypeScript × 68 包，最值得抄「日志即真相」）

### 4.1 定位
DeepSeek 开源的 agent harness，命令 `dsh`。架构信条：**一切皆插件**（Cordis 驱动，无特权内核），模型适配器、工具注册表、**会话日志、agent loop 本身都是可替换插件**。三种硬约定：`Model-visible ⟺ logged`（进模型的必须能从日志重建）、`Plugins, not loop changes`、`Registrations are effects`。

同一运行时输出 5 种 profile：`web` / `headless` / `sdk` / `sdk-minimal` / `acp`，外加 Electron 桌面。

### 4.2 主循环：`packages\core\agent-loop\src\agent.ts`

`kick()` 252-265 就是 `while (await this.turn()) {}`；`turn()` 298-398；`step()` 400-561（一次模型请求 + 工具执行）。

```ts
315   while (true) {
318     const decision = await this.preStep(target, { turn, step })
319     if (decision.kind === 'reject') { turnEnds = { kind: 'blocked' }; return false }
323     if (turnEnds && decision.messages.length === 0) break
331     this.session.append('step/start', { turn, step })
337     try {
340       const stepEnd = await this.step(decision)
343       if (turnEnds === null || turnEnds.kind !== 'max-tokens') turnEnds = stepEnd   // max-tokens 是 sticky 的
344     } catch (error) {
346       for (const event of toolRecovery.results())        // 失败也要补写 tool/result，保证回放合法
347         this.session.append('tool/result', event.data, ...)
356     } finally {
358       this.session.append('step/end', { turn, step })
```

流式落盘只有 8 行（453-460）：

```ts
453   const stream = preparedCall?.stream(request) ?? this.loopCtx.llm.stream(request)
457   for await (const chunk of stream) { signal.throwIfAborted(); live.push(chunk) }
```

### 4.3 三条核心接口

**① 日志即真相** `packages\core\session\src\index.ts:984-1005` `deriveMessages()` —— 会话只 append，模型历史从日志**投影**出来。压缩不改日志，只写一个 `surfaceOp: { op: 'replace', startSeq, endSeq }` 把中段遮蔽。fork / resume / UI 回放 / 遥测全部从这一条派生。

**② 模型调用是可拦截的流** `packages\llm\llm\src\index.ts:208-303`

```ts
208  abstract class LlmAdapter {
302    abstract stream(options): AsyncIterable<StreamChunk>;   // 只需实现这一个方法
```

所有请求再包一层 `llm/stream` 瀑布（1166-1180），重试/降级/计量/压缩触发都挂在这里，**不用改循环**。

**③ 工具 = schema + 输出契约 + 一个 gate** `packages\core\tools\src\index.ts:224`

```ts
224  export interface ToolDefinition extends ToolSchema {
226    readonly output: ToolOutputDefinition      // 强制 output.schema + render()
237    execute(args: unknown, exec: ToolRunContext): Promise<unknown>   // 只返回 canonical JSON 值
281    isConcurrencySafe?(args): boolean          // 只有严格 true 才并行
```

权限走独立 gate（1501-1547）：`PreToolDecision = allow | deny | cancel | ask`，`ask` 只接受 `allowed-once`，其余一律 fail-closed（`unavailable` 也拒绝）。工具只消费结果，不自己判权限 → 一个 patch 就能把整个部署从 `workspace-write` 切成 `read-only`。

### 4.4 最小示例
| 形态 | 路径 | 说明 |
|---|---|---|
| **最快跑起来** | `python\sdk\examples\minimal.py` | `DeepSeekHarness(provider=..., profile='sdk-minimal')` → `harness.run(prompt)` |
| **最小内核需要哪些插件** | `packages\bundle\sdk-minimal\cordis.patch.yml`（173 行） | 显式列出 llm → session → tools → agent → agent-loop → sysprompt → persistence |
| **40 行驱动一个 Agent** | `packages\bundle\headless\src\index.ts:335-404` | `agents.create()` → `followup()` → `whenIdle()` |
| 一次性任务 | `pnpm dsh --profile headless "task"` | 无 HTTP 无浏览器 |

### 4.5 核心文件 Top 10

`core/agent-loop/src/agent.ts`(705) ／ `core/agent-loop/src/index.ts`(929) ／ `core/tools/src/index.ts`(1993) ／ `core/session/src/index.ts`(1453) ／ `core/session/src/surface.ts`(712) ／ `core/agent/src/index.ts`(691) ／ `llm/llm/src/index.ts`(1218) ／ `core/system-prompt/src/index.ts`(691) ／ `core/agent-loop/src/tool-calls.ts`(290) ／ `compaction/compaction-basic/src/index.ts`(452)

跳过：`.agents/`（3828 文件的工作笔记）、`snapshots/`（1677 个回放快照）、`apps/`、`packages/client|host`（UI）。

### 4.6 一个必须知道的坑
`docs\architecture.zh.md:87-108` 里的 `agent/pre-step`、`agent/request`、`llm/stream`、`tools/pre-execute` 是 **waterfall（必须调 `next()` 才继续）**，而 `agent/turn-stopping` 是 serial。自己复刻时如果全做成普通事件数组，压缩插件会意外切断链条。

---

## 5. nanobot（Python，最值得抄「上下文治理」）

### 5.1 定位
可自托管的常驻个人 agent：小核心 + 20 个聊天渠道 + 记忆 + 定时 + MCP + WebUI。**不是**面向代码仓库的 coding agent。

### 5.2 它自己定义的「核心有多小」

仓库根目录有 `core_agent_lines.sh`，实测输出：

```
Core runtime
  agent/   5650    bus/  424    config/  810    cron/  765    session/ 1560
  core total        9209 lines      （28 个 .py，占包内 58,750 行的 15.7%）
Separate buckets
  tools/ 7905   skills/ 2189   api/ 400   cli/ 3538   channels/ 16356   utils/ 3597
```

三个口径陷阱（引用这个数字时必须注明）：`-maxdepth 1` 只算目录顶层、**排除 `providers/` 和 `agent/tools/`**、`skills/` 把 `.md` 也计入行数。
→ 「能真跑起来」的最小集 ≈ 核心 9209 + providers 7468 + 最小工具骨架 ~1500 ≈ **18.2k 行**。

### 5.3 主循环：`nanobot\agent\runner.py:272`

```python
272   async def run(self, spec: AgentRunSpec) -> AgentRunResult:
289       for iteration in range(spec.max_iterations):
295           messages_for_model = self._drop_orphan_tool_results(messages)
296           messages_for_model = self._backfill_missing_tool_results(messages_for_model)
297           messages_for_model = self._microcompact(messages_for_model)
298           messages_for_model = self._apply_tool_result_budget(spec, messages_for_model)
299           messages_for_model = self._snip_history(spec, messages_for_model)
301           messages_for_model = self._drop_orphan_tool_results(messages_for_model)
315           await hook.before_iteration(context)
316           response = await self._request_model(spec, messages_for_model, hook, context)
334           if response.should_execute_tools:
361               results, new_events, fatal_error = await self._execute_tools(...)
423               continue
```

**关键就是那 6 行 `messages_for_model`**：每轮做一次无损治理（去孤儿子工具结果 → 补缺失结果 → microcompact → 结果预算 → 剪历史 → 再去孤儿），而 `messages` 本身一个字节都不动。

### 5.4 接口代码

- **Provider**：`providers\base.py:92` `class LLMProvider(ABC)` + `providers\registry.py:92` 的 `PROVIDERS` 元组（**37 个 provider / 6 种 backend**，`openai_compat|anthropic|azure_openai|openai_codex|github_copilot|bedrock`）。加一个 provider = 加一条 `ProviderSpec` + config 一个字段。
- **工具基类**：`agent\tools\base.py:124` `class Tool(ABC)`，抽象 `name/description/parameters` + `async execute(**kwargs)` + `to_schema()`；`@tool_parameters({...})` 装饰器声明 schema；并发声明 `read_only / concurrency_safe / exclusive`。
- **注册表**：`agent\tools\registry.py:8`；`get_definitions()` 把内置工具稳定排序在前、`mcp_*` 在后 —— **为了 prompt cache 命中**。
- **自动发现**：`agent\tools\loader.py:22` 用 `pkgutil.iter_modules` 扫包内所有非抽象 Tool 子类。

### 5.5 最小示例
`docs\python-sdk.md:5-19` 只有 10 行：

```python
from nanobot import Nanobot
bot = Nanobot.from_config()
result = await bot.run("What time is it in Tokyo?")
print(result.content)
```
底层是 `agent\loop.py:1713` 的 `process_direct()`，绕开消息总线直接跑一个回合。

### 5.6 核心文件
`agent\loop.py`(1743) ／ `agent\runner.py`(1353) ／ `agent\memory.py`(1166) ／ `session\manager.py`(740) ／ `agent\tools\filesystem.py`(1022) ／ `agent\tools\mcp.py`(942)

---

## 6. altimate-code（OpenCode fork，只记一句：双内核）

- **V1（生产在跑）**：`packages\opencode\src\session\prompt.ts:1031`，整个文件 4825 行，是典型的「上帝文件」。退出条件不是「没调工具」，而是 `lastAssistant.finish` 不在 `["tool-calls","unknown"]` 且没有未失败的 tool part 且 `parentID` 对齐当前 user（1146-1160）。
- **V2（重写中）**：`packages\core\src\session\runner\llm.ts:380`，**只有 408 行**，Effect-TS 写成。核心创新是 **durable-first**：每遇到一个 `tool-call` 事件立刻 `settle`（先落 DB 记 pending，再产生副作用），`:342` 返回 `needsContinuation` 决定下一步。
- 它的真正价值不在 agent 内核，而在 **78 个确定性数据工程工具**（SQL 解析/血缘/FinOps/dbt）+ `CONTEXT.md` 那套术语体系。

> ⚠️ 引用它的行数前必须先声明 V1 还是 V2，两者主循环差 12 倍。

---

## 7. 最简版：`mini_agent.py`（343 行）

位置：`D:\AgentABC\_digest\mini_agent.py`。单文件、零第三方依赖（只用标准库），可编译可跑。

```bash
cd D:\AgentABC\_digest
set OPENAI_API_KEY=sk-x***MASKED***
set OPENAI_BASE_URL=https://api.deepseek.com/v1
set MODEL=deepseek-chat
python mini_agent.py "列出当前目录的文件，挑一个说明它的作用"
```

它和四家的对应关系：

| mini_agent.py 里的东西 | 行数 | 抄自谁的哪个文件 |
|---|---|---|
| `Response` / `ToolCall` / `Usage` | ~30 | hermes `agent/transports/types.py` |
| `LLM.complete()` + SSE 聚合 | ~60 | pi `api/openai-completions.ts` 的 `stream()` + `convertMessages()` |
| `@tool` 装饰器 + `dispatch()` | ~40 | hermes `tools/registry.py` + nanobot `tools/base.py` |
| `compact()` + `estimate_tokens()` | ~35 | nanobot `runner.py` 的 `messages_for_model` + pi `compaction.ts` |
| `run()` 主循环 | ~45 | pi `agent-loop.ts` 的双层 while 精简成单层 |
| 四个内置工具 | ~60 | pi `coding-agent/src/core/tools/write.ts` 的模式 |

刻意**没做**的（都是四家里几万行的部分，属于「接进真实世界的缝隙」，不是内核）：审批 UI、沙箱、会话树/分支、MCP、多 provider 注册、token 精确计量、流式工具增量、扩展热加载、遥测。

---

## 8. 建议的阅读顺序（按投入产出排）

**第一梯队：只读循环（约 1 小时）**
1. `pi\packages\agent\src\agent-loop.ts` 前 340 行 —— 看纯净的循环长什么样
2. `pi\packages\agent\src\types.ts:193-342` —— 9 个回调，理解「行为靠注入不靠继承」
3. `hermes-agent\mini_swe_runner.py` 全文（406 行）—— 独立可跑的最小 agent
4. 本文的 `mini_agent.py` —— 对照，确认自己真的看懂了

**第二梯队：看接口怎么收口（约 1 小时）**
5. `hermes-agent\agent\transports\types.py` + `base.py`（151 行，全文）
6. `pi\packages\ai\src\types.ts:414-660`（消息与内容块）
7. `deepseek-harness\packages\core\tools\src\index.ts:224-300` + `1501-1547`（工具契约 + 权限 gate）

**第三梯队：看真实世界的缝隙（按需）**
8. `pi\packages\coding-agent\src\core\agent-session.ts:899-933, 1580-1626`（压缩接线 / 工具装载）
9. `hermes-agent\agent\context_compressor.py:3002-3015, 5528-5575`（压缩策略）
10. `deepseek-harness\packages\core\session\src\index.ts:984-1005`（日志投影）

---

## 附：几个容易踩的认知陷阱

1. **hermes 的 `agent/AGENTS.md` 说 `max_iterations` 默认 500 已过时**，代码是 `run_agent.py:241` 的 `sys.maxsize`。
2. **`run_conversation` 找不到方法体是正常的** —— 它在 `agent/turn_facade.py:22`，只负责转发。
3. **`self.client.chat.completions.create` 不是唯一出网口** —— 流式走 `_StreamingCall`，Anthropic / Codex / Bedrock 各有自己的路径，统一收敛点是 `perform_api_call`（`agent/turn_api_call.py:67`）。
4. **hermes 的 `tools/` 下 285 个文件不是 285 个工具** —— 大量是 `<tool>_<topic>.py` 兄弟文件。
5. **nanobot 的「9.2k 行核心」不可运行** —— 它不含 LLM 层和工具层。
6. **altimate 有两个主循环** —— V1 4825 行 / V2 408 行。
