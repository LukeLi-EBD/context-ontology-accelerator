# 落地执行手册：把 `integ/luke-r2` 落到 `luke` 与远端 `luke`

> 状态：**只写不执行**。本文件写于 2026-11-11，基线 `luke` = `38b9c4c5`，预演分支 `integ/luke-r2` = `48857228`（领先 12 笔）。
> 适用范围：本地合并预演已完成、验证全绿，准备把 `luke` 快进并推到远端 `luke`（`git@github.com:LukeLi-EBD/context-ontology-accelerator.git`）。
> 本文所有命令均为 Windows PowerShell 可直接粘贴形式，路径用反斜杠。

---

## 0. 一句话结论

**先停「文档自动同步」会话 → 在一小时内完成 快进 `luke` → 验证 → 推 `luke` → 复核远端 sha**。任何一步超时，本地 `reset --hard` 回退，**不推**，远端保持 `38b9c4c5`。

---

## 1. 前置条件清单（全部满足才开工）

| # | 检查项 | 命令 | 期望 |
|---|---|---|---|
| 1 | 「文档自动同步」会话已在 Trae 里停掉 | 见 §1.1（没有可 kill 的 PID，只能在 Trae 会话层停） | 会话状态为已停止 |
| 2 | 主工作区没有别人正在改的文件 | `git -C D:\agentABC\coa status --short` | 空输出（或只有你本轮明确无关、且你确认不会与文档线相撞的文件） |
| 3 | 没有残留 stash | `git -C D:\agentABC\coa stash list` | 空输出（当前实测为 0 条） |
| 4 | `luke` 仍指向基线 | `git -C D:\agentABC\coa rev-parse --short luke` | `38b9c4c5` |
| 5 | 远端 `luke` 仍指向基线 | `git -C D:\agentABC\coa ls-remote luke luke` | `38b9c4c5...	refs/heads/luke` |
| 6 | 预演分支提交数 | `git -C D:\agentABC\wt\integ-r2 rev-list --count luke..integ/luke-r2` | `12` |
| 7 | 预演分支是 `luke` 的后代 | `git -C D:\agentABC\wt\integ-r2 merge-base --is-ancestor luke integ/luke-r2; $LASTEXITCODE` | `0`（0 = 是后代，可 fast-forward） |
| 8 | 预演分支工作区干净 | `git -C D:\agentABC\wt\integ-r2 status --short` | 空输出 |
| 9 | `luke` 所在 worktree 干净 | `git -C D:\agentABC\wt\luke-all status --short` | 空输出（`luke` 当前 checkout 在 `D:\agentABC\wt\luke-all`） |
| 10 | Docker 可用（迁移门禁用） | `docker version --format '{{.Server.Version}}'` | 有版本号 |

### 1.1 为什么必须先停「文档自动同步」会话

它大约每小时做三件事：对主工作区做 `git stash push`、`git reset`、生成 `docs: auto-sync` 提交并 **push 到远端 `luke`**。本机没有可 kill 的 PID（它是 Trae 里的会话进程，不是独立服务），所以只能在 Trae 界面里停。

不停会出的事，按严重度：

1. **快进被抹掉**：你在 `wt/luke-all` 把 `luke` 快进到 `48857228` 后，它下一次 `reset` 会把主树/`luke` 引用改回它认知的基线，你的 12 笔提交从 `luke` 上消失（提交对象还在，靠 `integ/luke-r2` 还能找回）。
2. **远端被抢先**：它在 `:01–:07` 推 `docs: auto-sync`，与你推的 fast-forward 争同一个分支。若它先推成功，你的 `git push` 会被拒（non-fast-forward），需要重新 `fetch` + 重算快进；若用了 `--force`（**本手册禁止**）则会直接覆盖对方提交。
3. **stash/reset 打断验证**：验证要读工作区文件（`libs/ts-shared`、`infra/**`）。它 `stash push` 期间读到的可能是半截状态，验证数字不可信；上一轮主树被外部进程删掉 9 个 `libs/ts-shared` 文件的异常也应视为同类风险，出现即停、不要重跑掩盖。

**确认停干净的判据**：跨过一个完整的 `:01–:07` 窗口后，`git -C D:\agentABC\coa rev-parse luke` 与 `git -C D:\agentABC\coa ls-remote luke luke` 都仍是 `38b9c4c5`，且 `git -C D:\agentABC\coa log --oneline -1 luke` 不是 `docs: auto-sync`。

---

## 2. 落地步骤（快进路线，推荐）

> 全程在**同一个小时窗口**内完成（见 §5）。命令按顺序粘贴，**每一步先看输出再走下一步**。

### 步骤 1：落地前打本地备份引用（不改任何分支）

```powershell
$old = git -C D:\agentABC\wt\integ-r2 rev-parse luke
Write-Output "backup target: $old"
git -C D:\agentABC\wt\integ-r2 update-ref refs/backup/luke-pre-r2 $old
git -C D:\agentABC\wt\integ-r2 rev-parse --short refs/backup/luke-pre-r2
```

期望：打印 `backup target: 38b9c4c5...`（完整 sha），最后一行 `38b9c4c5`。

### 步骤 2：复核远端 tip 仍是 `38b9c4c5`

```powershell
git -C D:\agentABC\coa fetch luke
git -C D:\agentABC\coa ls-remote luke luke
git -C D:\agentABC\coa rev-parse --short luke
```

期望：`ls-remote` 输出 `38b9c4c5...	refs/heads/luke`；本地 `luke` 也是 `38b9c4c5`。
**只要远端不是 `38b9c4c5`：停手**。说明自动同步又推过东西，回到 §1 重新评估，不要在别人的 tip 上直接快进。

### 步骤 3：确认可以快进（祖先判断）

```powershell
git -C D:\agentABC\wt\integ-r2 merge-base --is-ancestor refs/backup/luke-pre-r2 integ/luke-r2
Write-Output "is-ancestor exit=$LASTEXITCODE"
git -C D:\agentABC\wt\integ-r2 rev-list --count refs/backup/luke-pre-r2..integ/luke-r2
```

期望：`is-ancestor exit=0`，提交数 `12`。

### 步骤 4：把 `luke` 快进到预演分支（只动本地分支）

`luke` 当前 checkout 在 `D:\agentABC\wt\luke-all`，所以必须在这个 worktree 里做，不能在主树 `git branch -f`（会报被 checkout）。

```powershell
git -C D:\agentABC\wt\luke-all status --short
git -C D:\agentABC\wt\luke-all merge --ff-only integ/luke-r2
git -C D:\agentABC\wt\luke-all rev-parse --short HEAD
```

期望：`status` 空；`merge --ff-only` 输出 `Fast-forward`；最后一行 `48857228`。
若 `status` 非空 → **停手**，先问清 `wt/luke-all` 的归属，不要 reset 别人的工作区。

备选（仅当 `wt/luke-all` 不可用时，需该 worktree 的 owner 知情）：在主仓直接改引用，会让 `wt/luke-all` 变成"落后于分支"的状态：

```powershell
# 备选方案，慎用；执行后 wt/luke-all 的 index/worktree 会显示为落后
git -C D:\agentABC\coa update-ref refs/heads/luke (git -C D:\agentABC\wt\integ-r2 rev-parse integ/luke-r2)
git -C D:\agentABC\coa rev-parse --short luke
```

### 步骤 5：推之前再跑一次验证（在 `D:\agentABC\wt\integ-r2`）

> 该 worktree 已装好依赖、已构建生成客户端；`wt/luke-all` 不要拿来跑测试。

**5.1 infra 类型检查**

```powershell
Set-Location D:\agentABC\wt\integ-r2\infra
pnpm exec tsc --noEmit
Write-Output "INFRA_TSC_EXIT=$LASTEXITCODE"
```

期望：`INFRA_TSC_EXIT=0`，无 error 行。

**5.2 五个 infra jest 套件（合并后同跑）**

```powershell
Set-Location D:\agentABC\wt\integ-r2\infra
pnpm exec jest test/services/data-layer-stack.test.ts test/scripts/ssm-refs-check.test.ts test/model-id-defaults.test.ts test/preflight-arm64.test.ts test/utils/python-bundling.test.ts --maxWorkers=4 --coverage=false
Write-Output "JEST_EXIT=$LASTEXITCODE"
```

期望：`Test Suites: 5 passed, 5 total`；`Tests: 3 skipped, 157 passed, 160 total`；`JEST_EXIT=0`。
逐套应为 6 / 34 / 35 / 10 / 72 passed。**不要去掉 `--coverage=false`**：子集跑会因 `lib/**` 行覆盖不到 80%（实测 69.06%）而 exit 1，那是度量假象，不是测试失败。

**5.3 canvas pytest**

```powershell
$parts = @("D:\agentABC\wt\integ-r2\packages\platform-core\src")
$parts += Get-ChildItem D:\agentABC\wt\integ-r2\packages -Directory | ForEach-Object { Join-Path $_.FullName "src" }
$parts += Get-ChildItem D:\agentABC\wt\integ-r2\libs -Directory | ForEach-Object { Join-Path $_.FullName "src" }
$parts += "D:\agentABC\coa\.venv-coa-local\Lib\site-packages"
$env:PYTHONPATH = ($parts | Where-Object { Test-Path $_ }) -join ";"
Set-Location D:\agentABC\wt\integ-r2\packages\platform-core\tests
& D:\agentABC\coa\.venv\Scripts\python.exe -m pytest test_d1_canvas.py test_d1_canvas_full.py -q
Write-Output "CANVAS_EXIT=$LASTEXITCODE"
```

期望：`34 passed`；`CANVAS_EXIT=0`。

**5.4 迁移幂等门禁**

```powershell
Set-Location D:\agentABC\wt\integ-r2
powershell -NoProfile -ExecutionPolicy Bypass -File D:\agentABC\wt\integ-r2\scripts\ci\migration-idempotency.ps1 -Python "D:\agentABC\coa\.venv-coa-local\Scripts\python.exe"
Write-Output "GATE_EXIT=$LASTEXITCODE"
```

期望：9 项全 `PASS`、`applied=50`、`last=V53`、二次运行 `applied=[]`、`gaps=[]`；`GATE_EXIT=0`。容器用随机高位端口，结束自删。

**5.5 前端类型与构建**

```powershell
Set-Location D:\agentABC\wt\integ-r2
pnpm --filter @coa/control-plane-client --filter @coa/data-layer-client build
Set-Location D:\agentABC\wt\integ-r2\packages\web-app
pnpm exec tsc --noEmit
Write-Output "WEBAPP_TSC_EXIT=$LASTEXITCODE"
Set-Location D:\agentABC\wt\integ-r2
pnpm --filter coa-web-app build
Write-Output "BUILD_EXIT=$LASTEXITCODE"
```

期望：`WEBAPP_TSC_EXIT=0`、`BUILD_EXIT=0`，vite 输出 `built in ~9s`，`index-*.js` 约 2,833 kB（有 >500 kB 警告，属既有）。
> `tsc --noEmit` 依赖生成客户端的 `dist-types`，换 worktree 后第一次必须先做上面那次 `--filter ... build`，否则会报一堆 `@coa/control-plane-client` 找不到。

**5.6 工作区复核**

```powershell
git -C D:\agentABC\wt\integ-r2 status --short
git -C D:\agentABC\wt\luke-all rev-parse --short HEAD
```

期望：`status` 空（`coverage/`、`dist-types/` 均被 gitignore）；`HEAD` = `48857228`。

### 步骤 6：推远端 `luke`（fast-forward，不加任何 force 参数）

```powershell
git -C D:\agentABC\coa push luke luke:luke
Write-Output "PUSH_EXIT=$LASTEXITCODE"
```

期望：`PUSH_EXIT=0`，输出类似 `38b9c4c5..48857228  luke -> luke`。

### 步骤 7：复核远端已落地

```powershell
git -C D:\agentABC\coa ls-remote luke luke
git -C D:\agentABC\coa fetch luke
git -C D:\agentABC\coa rev-parse --short luke
git -C D:\agentABC\coa rev-parse --short refs/backup/luke-pre-r2
```

期望：远端与本地 `luke` 都是 `48857228`；备份引用仍是 `38b9c4c5`（**不要删**，留到下一个 tag 之后）。

---

## 3. 十二条提交的顺序（以及不用 fast-forward 时的逐条做法）

### 3.1 十二条到底是什么

12 笔 = 5 笔合并提交（无独立 diff，只表达"哪条分支从哪来"）+ 7 笔内容提交。

| 序 | 提交 | 类型 | 内容 | 最小验证 |
|---|---|---|---|---|
| 1 | `df722f47` | 内容 · CI | 迁移幂等门禁 job + 3 个脚本 | `Test-Path D:\agentABC\wt\integ-r2\scripts\ci\migration-idempotency.ps1` → `True`；跑 §5.4 门禁 → 9 PASS |
| 2 | `1a1d4889` | 合并 | `fix/red-infra-jest` | 无独立操作，看第 3 行 |
| 3 | `ba463c31` | 内容 · 测试 | 3 套可移植性修复 | 三套 → 6 / 35 / 34 passed，0 failed |
| 4 | `9e1a200f` | 合并 | `fix/red-shell-bundling` | 无独立操作，看第 5 行 |
| 5 | `f413f1bb` | 内容 · 测试 | arm64 预检 + python-bundling + `.gitattributes` | 两套 → 10 passed / 72 passed + 3 skipped；再跑五套 → 157 passed / 3 skipped |
| 6 | `81ead422` | 合并 | `ci/migration-idempotency` | 无独立操作 |
| 7 | `c88e5eeb` | 内容 · 文档 | 7/30/31 等口径与路径更正 | `git -C D:\agentABC\wt\integ-r2 diff --check` → 无输出 |
| 8 | `2c9fc4da` | 内容 · 文档 | 5 套不是"环境天然红"的更正 | 同上 |
| 9 | `50cd4914` | 合并 | `docs/fix-wrong-claims` | 无独立操作 |
| 10 | `8cdc3ad3` | 内容 · 文档 | worktree 清理证据 | 文件存在：`doc\coa-x\evidence\worktree-cleanup-20261111.md` |
| 11 | `f63bd8b3` | 合并 | `docs/worktree-cleanup-20261111` | 无独立操作 |
| 12 | `48857228` | 内容 · 文档 | canvas 34/0、3 条 skip、去掉 07b BOM | 五套 + canvas + tsc + build（即 §5 全量） |

### 3.2 如果不用 fast-forward，改用逐条 cherry-pick

只 replay **7 笔内容提交**（5 笔合并提交没有 diff，cherry-pick 会得到空提交或干脆报空）。顺序按上表 1 → 3 → 5 → 7 → 8 → 10 → 12，每笔之后做该行的最小验证。

```powershell
Set-Location D:\agentABC\wt\luke-all
git cherry-pick df722f47
git cherry-pick ba463c31
git cherry-pick f413f1bb
git cherry-pick c88e5eeb
git cherry-pick 2c9fc4da
git cherry-pick 8cdc3ad3
git cherry-pick 48857228
```

必须知道的代价：

1. **合并结构丢失**：`luke` 上不再有"这五条从哪来"的记录，后续反查要靠台账/本手册。
2. **文档里的合并哈希失效**：`07b`、`07`、`31` 里写的 `1a1d4889`、`9e1a200f` 在 cherry-pick 后不存在，必须另补一笔文档更正，否则口径又是错的。
3. **`.gitattributes` 要单独确认**：第 3 笔带 `*.sh text eol=lf`，cherry-pick 后 `git -C D:\agentABC\wt\luke-all status --short` 若出现大量 `.sh` 改动，说明工作区换行与属性不一致，先停、查明再继续。
4. cherry-pick 第 1 笔后，`scripts/ci/migration-idempotency.ps1` 才存在；在那之前跑门禁会报"文件不存在"，属顺序错误。

结论：**优先 fast-forward**；cherry-pick 只在 `luke` 已经分叉、无法快进时使用。

---

## 4. 回滚方案

### 4.1 推到远端之前（代价 0）

```powershell
git -C D:\agentABC\wt\luke-all reset --hard refs/backup/luke-pre-r2
git -C D:\agentABC\wt\luke-all rev-parse --short HEAD
```

期望：`38b9c4c5`。远端没动过，`integ/luke-r2` 原样保留，随时可再来一次。

### 4.2 推到远端之后，方案 A：追加反转提交（不改写历史）

```powershell
# 在 wt/luke-all 上，把树恢复成 38b9c4c5 的内容，再提交一笔
git -C D:\agentABC\wt\luke-all restore --source=refs/backup/luke-pre-r2 --staged --worktree .
git -C D:\agentABC\wt\luke-all commit -m "revert: 回退 integ/luke-r2 的落地（内容恢复至 38b9c4c5）"
git -C D:\agentABC\wt\luke-all push luke luke:luke
```

- 代价：历史保留 12 笔 + 1 笔回退，别人 `pull` 不冲突；远端不重写。
- 缺点：之后再想落地同样内容，需要 `revert` 那笔回退（或重新合并），会多一次冲突处理。
- 适用：已有人拉到、或不确定有没有人拉。

### 4.3 推到远端之后，方案 B：`reset` + `--force-with-lease`（改写远端历史）

```powershell
git -C D:\agentABC\wt\luke-all reset --hard refs/backup/luke-pre-r2
git -C D:\agentABC\wt\luke-all push --force-with-lease luke luke:luke
```

- 代价：远端 `luke` 历史被重写；任何已 `fetch`/`pull` 过的人都会分叉，需要他们 `reset --hard`；与"文档自动同步"会话重启后的 push 会互相踩。
- 门槛：**必须先确认没人拉过**，且只用于 `luke` 这一条整合分支，且用 `--force-with-lease`（不要裸 `--force`）。
- **边界（硬规则）：绝不对 `main` 强推。** 包括 GitHub 上的 `main`、`origin/main`、以及任何名为 `main`/`master` 的受保护分支。`luke` 是个人整合主线，才允许在确认无人拉取时用 `--force-with-lease`。

### 4.4 回滚后要一起做的事

1. `git -C D:\agentABC\coa ls-remote luke luke` 复核远端 sha。
2. 在台账追加一条回滚记录（原因、回滚到哪个 sha、谁操作的），不要口头说完就算。
3. **不要删** `refs/backup/luke-pre-r2`，留到下一个 tag 之后。

---

## 5. 时间窗口

自动同步每小时 `:01–:07` 跑，之后到下一次 `:01` 之前约 50 分钟是安全区。

| 时段 | 动作 |
|---|---|
| `:01–:07` | **不要动手**。等它跑完，顺带观察本轮是否真的没再产生 `docs: auto-sync`（§1.1 的判据） |
| `:08–:10` | 跑 §1 全部前置检查 + §2 步骤 1–3（备份引用、复核 tip、祖先判断） |
| `:10–:45` | §2 步骤 4–5（快进 + 全量验证）。验证里最慢的是五套 jest（约 3 分钟）和迁移门禁（约 2 分钟），留足余量 |
| `:45–:50` | §2 步骤 6–7（push + 复核）。**`:50` 是硬停线** |
| `:50–:58` | 只做记录：写台账、把 §7 的数字填进去；不要再改分支 |

### 窗口内做不完怎么体面中止

判据很简单：**只要还没执行步骤 6 的 `push`，中止就是零成本**。

```powershell
# 1) 若已快进但还没推：把本地 luke 退回基线
git -C D:\agentABC\wt\luke-all reset --hard refs/backup/luke-pre-r2
git -C D:\agentABC\wt\luke-all rev-parse --short HEAD

# 2) 复核远端确实没动
git -C D:\agentABC\coa ls-remote luke luke
```

期望：本地 `38b9c4c5`；远端 `38b9c4c5`。
然后停手，下一小时 `:08` 再来。**不要**为了赶时间跳过 §5 的验证直接推，也不要为了"先推上去再说"而省略步骤 2 的远端复核。

如果 `:45` 时验证还剩一大半没跑：直接中止，不要压缩验证项。把已跑完的数字记进台账，标注"本轮未完成，未推"。

---

## 6. 本轮（2026-11-11）实测数字存档

| 项 | 命令要点 | 实测 |
|---|---|---|
| infra `tsc --noEmit` | `pnpm exec tsc --noEmit` | 0 error，exit 0 |
| web-app `tsc --noEmit` | 先构建两个生成客户端，再 `tsc --noEmit` | 0 error，exit 0 |
| 五个 infra 套件 | `jest <5 files> --coverage=false` | 5/5 suites，**157 passed / 0 failed / 3 skipped（160）**，exit 0 |
| 逐套 | 同上单独跑 | 6 / 34 / 35 / 10 / 72 passed |
| 三条 skip | — | 2 条 symlink（本机无 `SeCreateSymbolicLinkPrivilege`）+ 1 条 Renovate（该 checkout 无 `renovate.json` 与 `ci/`） |
| canvas | `pytest test_d1_canvas.py test_d1_canvas_full.py` | **34 passed / 0 failed / 0 skipped**，exit 0 |
| 迁移门禁 | `scripts\ci\migration-idempotency.ps1` | 9 项 PASS，`applied=50`、`last=V53`、二次 `applied=[]`、`gaps=[]`，exit 0 |
| 前端构建 | `pnpm --filter coa-web-app build` | `tsc && vite build` 通过，built in 9.22s，`index-*.js` 2,833.32 kB（gzip 826.28 kB） |
| 带覆盖率门禁的子集跑 | 去掉 `--coverage=false` | 测试仍 0 failed，但 `lib/**` 行覆盖 69.06% < 80%，exit 1（子集度量假象） |

覆盖率门限出处（供复核，不是本轮改动项）：`infra/jest.config.js` 的 `collectCoverage: true`、`collectCoverageFrom: ["lib/**/*.ts","bin/**/*.ts"]`、`coverageThreshold.global.lines: 80`；CI 的 `unit-test` job 跑 `pnpm nx affected -t test`，未显式传 `--coverage`，覆盖率由配置默认开启，因此该 80% 门限在 PR 与 merge queue 都生效。

---

## 7. 落地后要补的记录

1. 在 `07-研发台账.md` / `07b` 追加：落地时间、`luke` 从 `38b9c4c5` → `48857228`、远端 sha、验证数字（直接引用 §6）。
2. 把 §6 的"带覆盖率门禁的子集跑 exit 1"说明一并写进去，避免下一个人把 69.06% 当成真实覆盖率回退。
3. `refs/backup/luke-pre-r2` 的保留期限：下一个 tag 打完并复核后再删。
