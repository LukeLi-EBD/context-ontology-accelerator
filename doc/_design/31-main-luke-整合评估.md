# 31 · main ⇄ luke 整合评估（只读）

- 评估时间：2026-11-06 10:16:22 +08:00（`Get-Date`）
- 评估对象：`D:\agentABC\coa`（git 仓库根 = `D:/agentABC/coa`，`git rev-parse --show-toplevel`）
- 评估性质：只读。已执行 `git fetch origin` / `git fetch luke` 与 `git merge-tree --write-tree`（仅写对象库，不落工作树）；未切换分支、未提交、未推送、未建 worktree、未跑 Docker。
- 快照：luke = `7d609a8`（38 个自有提交）；origin/main = `bc18564`。评估期间另一条并行轨道把 luke 从 `3864ab4` 推进到 `7d609a8`（V21 metrics v5），本文数字均按 `7d609a8` 复算。

## 0 · 结论（TL;DR）

| 项 | 结论 |
|---|---|
| 能否整合 | **能整合**：`git merge-tree --write-tree luke origin/main` 退出码 0，**真实冲突文件 0 个** |
| 冲突性质 | 纯追加式（路径不相交）：我们只新增 `platform/`、`doc/`、`luke_doc/` 并改 1 行级 `.gitignore`；上游从未有这三个目录、也未改 `.gitignore` |
| 距离 | luke 领先 main 38 个提交；main 领先 luke 1 个提交（`bc18564`，镜像同步 #364，2026-11-06 00:08:12 +0000） |
| 合并代价 | 合并提交会向 luke 引入上游 8 天增量：425 文件、+48,557/−2,912；`platform` 与 `packages` 子树哈希两侧一致，无内容覆盖 |
| 推荐 | **方案 A：把 origin/main 合进 luke**（无需 force push，保留 38 个提交与审计链） |
| 最大风险 | 仓库是 shallow clone（`bacd1aa` 处 grafted）且正被并行轨道推进，执行合并前必须冻结写入并重新取一次 tip；其次是合并后根级工具链（`Makefile`/`ruff.toml` 的 `ruff format .`）会扫到 `platform/` |

## 1 · 仓库结构与 remote 事实

```
$ git rev-parse --show-toplevel      -> D:/agentABC/coa
$ git rev-parse --is-shallow-repository -> true
$ git remote -v
origin  https://github.com/aws/context-ontology-accelerator.git (fetch/push)   # 上游（AWS 官方镜像）
luke    git@github.com:LukeLi-EBD/context-ontology-accelerator.git (fetch/push) # 我们的 fork
```

**重要纠正：仓库只有 2 个 remote，不存在 `upstream` remote。** 用户的"origin/upstream/luke 三个 remote"里，`origin` 就是上游，"已 sync fork"的对象是 `luke`（fork）。

| 引用 | 提交 | 时间（原始时区） | 说明 |
|---|---|---|---|
| `origin/main`（fetch 后） | `bc18564` | 2026-11-06 00:08:12 +0000 | `Mirror sync 34c119ce (#364)`，上游最新快照 |
| `luke/main`（fork main） | `bc18564` | 同上 | **fork 已 sync 到上游最新** |
| 本地 `main` 分支 | `bacd1aa` | 2026-10-29 20:11:05 +0000 | **落后 1 个同步提交**（fetch 只更新了 `origin/main`，本地 main 未快进） |
| `luke`（工作分支） | `7d609a8` | 2026-11-06 10:16:01 +0800 | `V21 metrics v5: land the 13-row verdict` |

fetch 记录：

```
From https://github.com/aws/context-ontology-accelerator
   bacd1aa..bc18564  main -> origin/main
 * [new tag]         v0.3.9 -> v0.3.9
From github.com:LukeLi-EBD/context-ontology-accelerator
   bacd1aa..bc18564  main -> luke/main
```

> 说明：上游是"镜像同步"仓库，每次 sync 用一个 squash 快照提交（`Mirror sync <sha> (#PR)`）。因此 `main` 的"1 个提交"代表 #313–#364 区间的整体快照，**不能按 commit 数理解上游变更量**；变更量以文件面为准（§4）。
> 另：shallow 克隆在 `bacd1aa` 处 grafted，本地 `git log origin/main` 只能看到 2 条记录，diff 仍正确。

## 2 · 合并基与距离

```
$ git merge-base luke origin/main -> bacd1aa393e31cf2bdbff1bb12186df99479cf71
$ git rev-list --left-right --count luke...origin/main -> 38    1
```

- 合并基 = `bacd1aa`（2026-10-29 的镜像同步点，也是我们 fork 的第一次导入点）。
- luke 独有 **38 个提交**（用户估计"20+"，实际 38）。
- origin/main 独有 **1 个提交**（`bc18564`）。

## 3 · 我方提交与文件面

### 3.1 luke 侧 38 个提交（`bacd1aa..luke`，新→旧）

```
7d609a8 V21 metrics v5: land the 13-row verdict (variants, rule set, effective_date)
3864ab4 close S14 A/B gaps: one-click S14 acceptance and read-only archived baselines
fb771fe bundle: carry CAS blobs end-to-end (A-1)
4fff3b2 drill: cold-start migration drill + bundle carry-over fixes
0858d39 bundle: carry document_page text
a063bd3 replay: advance fact_event sequence after restore
4250ba0 replay: preserve fact event created_at
0a9d67f bundle: parse graph/tbox.ttl as turtle during verify
7a01f3e bundle: carry metric registry, observations and entity facts
af2dc0b fix(shacl): 补回 BNode 导入，修复 SHACL 违规提取 NameError
c1e24c9 feat(metrics): 补缴费记录与分期计划实体，两条指标实体驱动出数
62bcc0a S16: archive 1200 test ontology versions by batch (status-only, reversible)
819e3d0 S16: /context/resolve p50 2884ms -> 62ms (cold 181ms)
7c9a45d S15: ontology deprecate for test-version cleanup + governance scroll fix
93816cc S14 governance console: governed write endpoints with gate-visible dry-run
ecf312a S14-H-03: DROP SILENT cleanup, deterministic s6 empty context, computability fixtures
1e8e6ed T6: acceptance — narrow the reasoner-absent SKIP rule to per-line error-code checks
631b632 Merge feat/metric-loader into luke: metric fact loader + read-only browse UI
edc1f32 T6: acceptance — SKIP reasoner lifecycle checks when the profile is absent
398fa21 T6: read-only browse UI - 7 GET endpoints + native HTML/JS 3-tab page
b49c89d T6: metric fact loader — declared mapping, whole-batch rollback, upsert idempotency
28369a3 T5: parameterize compose for parallel stacks; default config unchanged
6151f25 T4: metric output engine minimal loop (fixture) — V19 metric_observation
33a5ffc T3: 口径基准 v3 字段化 + 出数护栏 — V18 metric_definition（79 条）
2cbb25a T1/T2: 术语层落库 — 15 锚点类/18 altLabel + SHACL Warning；seedHit@1 0→9/24
1dfc983 Q8: 补齐多实现插槽 + 双跑证据
5db11b2 Q7: 修契约偏差 — 启动门禁阻断、命名图白名单、range_read、embedding 校验
1f52357 Q4: check_answerable 本体覆盖度前置检查
87e42f0 Q3/OQ-65: publish --existing 同内容向前发布
d48740e MERGED: 整合 _impl 进 coa/platform，单一项目、本地可运行
23b02cd 同步 graph-count、本体哈希修复与术语层文档
96914e8 性能优化收尾与 background 资源档
8655aae 导出/导入 bundle 与迁移固化
06d0486 reasoner 构建时自动下载并校验 robot.jar，不入库
305589c 补齐平台自包含构建文件与运行手册
4d1cf87 平台本地化实现（_impl 白名单）
5b0e565 补交 COA 识别报告到 luke_doc
c6d6ada 导入 coa 代码并汇总 _* 目录 Markdown 文档
```

### 3.2 文件面（`bacd1aa..luke`）

```
$ git diff --shortstat bacd1aa luke -> 271 files changed, 71859 insertions(+)
```

| 顶层目录 | 文件数 | 增/删 | 变更类型 |
|---|---|---|---|
| `platform/` | 195 | +42,036 / −0 | 全部新增（A） |
| `doc/`（含中文文件名，git 以 C 引号显示） | 74 | +29,572 / −0 | 全部新增（A） |
| `luke_doc/` | 1 | +238 / −0 | 全部新增（A） |
| `.gitignore` | 1 | +13 / −0 | 唯一修改（M），在 `d48740e` 中追加 platform 运行时忽略规则 |
| **合计** | **271** | **+71,859 / −0** | **270 A + 1 M，无任何删除（D）** |

变更集合中 **没有一条 D（删除）记录，也没有一条针对上游已有文件的 M 记录**（除 `.gitignore`，而上游并未改它）。这是本次能"零冲突"的根本原因。

## 4 · 试合并结果（把 origin/main 合进 luke）

```
$ git merge-tree --write-tree luke origin/main
3dfd18dc3e62c8088fe8a7778dd6d940629302d6
$ echo $LASTEXITCODE -> 0
```

- 合并结果树：`3dfd18d`；输出中**没有任何冲突文件行**，退出码 0。
- 合并会向 luke 引入的净变更（`git diff luke <merged-tree>`）：**425 文件，+48,557/−2,912**。
- 子树哈希校验（证明"取并集且互不覆盖"）：

```
luke:platform   -> a3d44de55939b277cdf85d84a7080b0baf2f1703
merged:platform -> a3d44de55939b277cdf85d84a7080b0baf2f1703   # 我们的平台原封不动
origin/main:packages   -> 8b3265a010d3416fb46351bfe4b2f762bc417ba8
merged:packages        -> 8b3265a010d3416fb46351bfe4b2f762bc417ba8   # 上游代码原封不动
```

### 4.1 冲突文件清单（按用户要求分类）

**真实冲突文件：0 个。** 下表按类别列出"本可能冲突但实际不冲突"的依据与命中数：

| 类别 | 双方是否改动 | 冲突文件数 | 判定依据 |
|---|---|---|---|
| 我们的 `platform/` | 仅我方新增 195 文件；上游**根本没有该目录**（`git ls-tree origin/main` 无 `platform`） | 0 | 无 add/add、无 modify/delete |
| 我们的 `doc/`（74）+ `luke_doc/`（1） | 仅我方新增；上游只有 `external-docs/`，无 `doc/`、`luke_doc/` | 0 | 路径不相交 |
| 上游根目录基础设施（`infra/` 53、`packages/` 286、`libs/` 21、`models/` 4、`connectors/` 4） | 仅上游改动；我方 38 个提交中零改动 | 0 | 我方未触达 |
| CI / workflows | 上游改 `.github/workflows/pr.yml`（+8/−2，仅补 pnpm 10.34.5 步骤）；我方未改 `.github` | 0 | 单边改动 |
| 依赖锁文件 | 上游改 `uv.lock`、`pnpm-lock.yaml`、`external-docs/pnpm-lock.yaml`；我方未改 | 0 | 单边改动 |
| README / 文档 | 上游未改根 `README.md`；改 `NOTICE`、`VERSION`；我方只新增 `doc/` | 0 | 路径不相交 |
| 根级工具链配置 | 上游改 `pyproject.toml`、`ruff.toml`、`Makefile`、`.dockerignore`、`nx.json`、`package.json`、`pnpm-workspace.yaml`；我方未改 | 0 | 单边改动 |
| `.gitignore` | **只有我方改**（+13 行）；上游未改 | 0 | 单边改动，合并自动取我方 |
| modify/delete | 我方无任何 D 记录；上游无任何 D 记录（`git diff --name-status bacd1aa origin/main` 无 `^D`） | 0 | 不存在该情形 |

### 4.2 上游 8 天增量分布（合并将引入的部分）

| 目录 | 文件数 | 增/删 |
|---|---|---|
| `packages/` | 286 | +37,721 / −1,914 |
| `infra/`（CDK 构造/栈） | 53 | +3,782 / −246 |
| `libs/` | 21 | +780 / −12 |
| `scripts/` | 17 | +1,218 / −61 |
| `external-docs/` | 14 | +1,241 / −164 |
| `tests/` | 14 | +3,191 / −54 |
| 根文件（11 个，含 `uv.lock`/`pyproject.toml`/`Makefile`） | 11 | — |
| `.github/` | 1 | +8 / −2 |
| `connectors/` | 4 | +5 / −2 |
| `models/` | 4 | +251 / −4 |
| **合计** | **425** | **+48,557 / −2,912** |

## 5 · 冲突性质逐类判断

- **"同文件不同段落可自动合"**：唯一候选是 `.gitignore`。实际上游未改，属单边改动，无需自动合并，直接保留我方版本。
- **"同段落改法冲突"**：不存在。双方对同一文件的同一区域均未同时改动。
- **"我们删过/挪过上游文件导致 modify-delete"**：不存在。我方 38 个提交对上游树是纯增量；`d48740e` 是新增 `platform/`，不是搬运或删除上游目录。
- **上游是否改过 `platform/` 或 `_impl` 迁移相关路径**：**没有**。上游树中不存在 `platform/`、`_impl/`、`luke_doc/`；唯一名字相近的是上游自有文件 `packages/control-plane/src/coa_control_plane/namespace/deletion_pipeline/delete_platform.py`（控制面"删除平台"功能，与我们的 `platform/` 无关）。
- **平台自包含性**：`platform/` 有自己的 `pyproject.toml`（`platform-core`，独立依赖）、`requirements.txt`、`docker-compose.yml`、各 Dockerfile；`git grep '\.\./\(packages\|infra\|libs\)/'` 在 `platform/` 下**零命中**，不引用上游代码。因此上游根 `pyproject.toml`/`uv.lock` 变更不会破坏平台构建。

## 6 · 三种整合策略对比

| 维度 | A：main 合进 luke（保留历史） | B：luke rebase 到 main（线性） | C：不合并，双目录共存 |
|---|---|---|---|
| 冲突量级 | **0 文件**（已用 merge-tree 实测） | 预计 0（路径不相交），但需实测重放 | **0**（不做合并动作） |
| 是否 force push | **不需要**（普通 `git push luke luke`） | **需要**（改写了 luke 全部提交，与项目"禁止 force 推送"惯例冲突） | 不需要 |
| 对 38 个提交的影响 | 全部保留原 SHA，另加 1 个 merge commit | 38 个 SHA 全部重写；`631b632`（feat/metric-loader 合并提交）被摊平，合并历史丢失 | 完全不动 |
| 对验收脚本的影响 | `platform/` 子树哈希不变，脚本零改动；但根工具链/CI 上下文变了，**需合并后重跑一次 acceptance**（期望 `passed=43 failed=0`） | 同上，且因 SHA 变化，历史汇报/文档中引用的 SHA 全部失效 | 零影响 |
| 可回退性 | 好：未推送 `git reset --hard 7d609a8`；已推送 `git revert -m 1 <merge>`（单次即可撤销整棵树） | 差：依赖 reflog，且已 force push 时协作者全部需要重新同步 | 无需回退（未发生变更） |
| 额外代价/风险 | 引入 425 文件上游增量；根 `Makefile` 的 `ruff format .` 会扫到 `platform/`；仓库体积上升 | 破坏审计链与"禁止 force"约束；rebase 时 `platform/` 195 文件重放耗时较长 | fork 双线维护、上游 infra 永远得不到；未来合并冲突债务累积 |
| 适合场景 | **推荐**：本项目强调留痕、可审计、可回退 | 不适用（违反既有约束） | 仅当明确"只要 platform"、彻底放弃上游同步时 |

> 补充：B 的"预计 0 冲突"依据是本方 38 个提交改动路径（`platform/`、`doc/`、`luke_doc/`、`.gitignore`）与上游 425 文件增量完全不相交；但 rebase 会逐提交重放，一旦未来某提交改到上游文件就会立刻冲突，本次不实测（避免写 ref）。

## 7 · 推荐方案与分步执行清单（本次不执行）

**推荐 A：`git merge --no-ff origin/main` 到 luke。** 理由：0 冲突（已实测）、不 force push（符合项目惯例）、38 个提交与审计链完整保留、单次 revert 可整体回退、`platform/` 子树不变所以验收脚本零改动。

| 步骤 | 命令 | 验收点 |
|---|---|---|
| 0 前置冻结 | 通知并行轨道暂停写；`git status --porcelain`（应为空） | 输出 0 行；记录 `git rev-parse HEAD`（当前 `7d609a8`） |
| 1 刷新引用 | `git fetch origin --prune`；`git fetch luke --prune` | `origin/main` 仍为 `bc18564`（若变，重跑第 3 步预演） |
| 2 备份 | `git tag pre-merge-main-luke 7d609a8`；`git branch backup/luke-pre-merge 7d609a8` | 两个引用均指向合并前 tip |
| 3 干跑预演 | `git merge-tree --write-tree luke origin/main` | 退出码 0，输出仅树 SHA、无冲突行 |
| 4 执行合并 | `git switch luke`（已在 luke，可省）；`git merge --no-ff origin/main -m "Merge upstream main (mirror sync #364) into luke"` | `git log -1` 显示 2 个父提交；`git status` 干净 |
| 5 结构与内容校验 | `git rev-parse HEAD:platform`；`git diff --stat HEAD^1 HEAD -- platform` | platform 树哈希仍为 `a3d44de`；`-- platform` diff 为空；`git rev-parse HEAD:packages` = `8b3265a` |
| 6 功能验收（需允许 Docker 时另起窗口） | `platform/scripts/up.ps1` 后执行 `platform/scripts/acceptance.ps1` | `passed=43 failed=0`（当前基线）；`/readyz` 200；本体指针 `ont-3f57d8ce6636` 不变 |
| 7 推送 | `git push luke luke`（禁止 `--force`） | 远端 `luke/luke` = 本地 HEAD；fork `luke/main` 仍为 `bc18564` 未被修改 |
| 8 留痕 | 由用户决定是否写入 `_design/a_progress.md`（**本次任务明确不写**） | 记录 merge sha、验收数字、风险项 |

回退点：
- 推送前：`git reset --hard 7d609a8`（或 `git reset --hard backup/luke-pre-merge`）。
- 推送后：`git revert -m 1 <merge-sha>`（产生一个反向提交，不改写历史，仍符合"禁止 force"）。

## 8 · 风险清单

| # | 风险 | 证据 | 等级 / 处置 |
|---|---|---|---|
| R1 | 仓库 shallow（`is-shallow=true`，`bacd1aa` grafted），本地看不到上游完整历史 | `git rev-parse --is-shallow-repository`；`git log` 显示 `(grafted)` | 低：合并/推送正常；需要完整历史时再 `git fetch --unshallow` |
| R2 | 分支是"活的目标"：评估期间 luke 被并行轨道从 `3864ab4` 推到 `7d609a8` | 首次 `git log -1 luke` vs 末次对比 | **中高**：执行合并前必须重新取 tip 并冻结写入，否则 merge 基线与验收数字漂移 |
| R3 | 本地 `main` 分支落后上游（`bacd1aa` vs `bc18564`） | §1 表 | 低：本次不依赖本地 main；需要时 `git switch main && git merge --ff-only origin/main` |
| R4 | 明文密钥 | `git grep -E 'AKIA[0-9A-Z]{16}|-----BEGIN .*PRIVATE KEY-----|sk-[A-Za-z0-9]{20,}'` 在 luke 全树（排除 lock）**零命中**；`git ls-tree` 无任何真实 `.env`，只有 `platform/.env.example`（`POSTGRES_PASSWORD=CHANGE_ME`、`PLATFORM__LLM__API_KEY=${ARK_API_KEY}` 占位）、`connectors/.env.example`、`packages/ontology-engine/demo/.env.example` | 低：无明文密钥入库；真实 `.env` 由 `platform/.gitignore` + 根 `.gitignore` 双重忽略 |
| R5 | 大文件 | 两侧最大跟踪文件：`uv.lock` 809 KB（luke）/ 765 KB（main）、`pnpm-lock.yaml` 376 KB；**无 >1 MB 跟踪文件**；`robot.jar`、`models/`、`platform/models/` 均在 ignore 内 | 低 |
| R6 | `.gitignore` 差异 | 我方在 `d48740e` 追加 13 行（`platform/data|logs|tmp|.lock|models|.env|platform.yaml|*.log|*.jsonl`）；`platform/.gitignore` 另含 `data/*`（保留 README）、`logs/`、`*.log`、`*.jsonl`、`.env`、`models/`、`reasoner/robot.jar`；上游未改 `.gitignore` | 低（无冲突）。注意：`*.jsonl` 连带忽略 `platform/tests/fixtures/**/*.jsonl`，当前 0 个 `.jsonl` 被跟踪；若后续要提交 fixture，需 `-f` 或加例外 |
| R7 | `data/` 误提交 | `D:\agentABC\data` 在仓库外（compose 绝对路径绑定）；仓库内仅跟踪 `platform/data/README.md` 占位，`git check-ignore` 命中 `platform/data/x` | 低 |
| R8 | `platform/logs` 与 fixture | `git check-ignore -v platform/logs/x.log` -> `platform/.gitignore:4:logs/`；`git ls-tree platform` 中 0 个 `.log`/`.jsonl` 被跟踪 | 低 |
| R9 | 合并后根级工具链扫到 platform | 上游 `ruff.toml` 仅 `extend-exclude=["workshop"]`；`Makefile` 执行 `uv run ruff format .` / `ruff check --fix .`；根 `pyproject.toml` 的 `source=["packages","libs"]` 未包含 platform | 中：不要在仓库根跑 `make format/lint`；platform 走自己的 `platform/pyproject.toml`；若 CI 未来加根 lint job 需显式排除 `platform` |
| R10 | CI 触发面 | `.github/workflows/pr.yml` 仅 `pull_request: branches:[main]` + `merge_group` + `workflow_dispatch`；本次推送到 fork 的 `luke` 分支不触发 | 低 |
| R11 | 本地/远端残留 `feat/metric-loader` 分支 | `git branch -vv`：`feat/metric-loader 66216c1 [luke/feat/metric-loader]`，已并入 `631b632` | 低：清理属另行任务，不影响本次整合 |

## 9 · 原始命令与输出（摘要）

```text
$ git rev-parse --show-toplevel
D:/agentABC/coa

$ git remote -v
origin  https://github.com/aws/context-ontology-accelerator.git (fetch/push)
luke    git@github.com:LukeLi-EBD/context-ontology-accelerator.git (fetch/push)

$ git rev-parse --is-shallow-repository
true

$ git log -1 --format='%H|%ci|%s' origin/main
bc185642fb996e6e4a4be52344c04f8061b27a29|2026-11-06 00:08:12 +0000|Mirror sync 34c119ce (2026-11-05T20:49:34Z) (#364)

$ git log -1 --format='%H|%ci|%s' luke
7d609a86f2b37160f5fcdba75fe4156dfbb0688f|2026-11-06 10:16:01 +0800|V21 metrics v5: land the 13-row verdict (variants, rule set, effective_date)

$ git merge-base luke origin/main
bacd1aa393e31cf2bdbff1bb12186df99479cf71

$ git rev-list --left-right --count luke...origin/main
38      1

$ git merge-tree --write-tree luke origin/main
3dfd18dc3e62c8088fe8a7778dd6d940629302d6
exit=0                       # 无冲突文件行

$ git diff --shortstat bacd1aa luke
271 files changed, 71859 insertions(+)

$ git diff --shortstat luke 3dfd18dc...
425 files changed, 48557 insertions(+), 2912 deletions(-)

$ git rev-parse luke:platform
a3d44de55939b277cdf85d84a7080b0baf2f1703

$ git rev-parse 3dfd18dc...:platform
a3d44de55939b277cdf85d84a7080b0baf2f1703

$ git rev-parse origin/main:packages
8b3265a010d3416fb46351bfe4b2f762bc417ba8

$ git rev-parse 3dfd18dc...:packages
8b3265a010d3416fb46351bfe4b2f762bc417ba8

$ git diff --name-status bacd1aa luke | grep '^D'   # 无输出：我方无删除
$ git diff --name-status bacd1aa origin/main | grep '^D'  # 无输出：上游无删除
```

## 10 · 边界声明

- 本评估未执行：切分支、commit、merge、push、rebase、worktree、Docker、验收脚本。
- `git merge-tree --write-tree` 只向对象库写入 1 个暂存树对象，未触碰工作区与任何引用。
- 未写入 `_design/a_progress.md`；本文件是本任务唯一产出。
- 数字口径：luke = `7d609a8`（2026-11-06 10:16:01 +0800），origin/main = `bc18564`（2026-11-06 00:08:12 +0000），merge-base = `bacd1aa`。执行合并前若 tip 再次变化，须重跑 §9 中 `merge-base` / `merge-tree` / `--shortstat` 三条命令复核。
