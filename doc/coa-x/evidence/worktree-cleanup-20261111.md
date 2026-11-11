# worktree 清理证据（2026-11-11）

## 0. 口径与基线

- 仓库根：`D:\agentABC\coa`；worktree 根：`D:\agentABC\wt`。
- 基线：`luke` @ `38b9c4c5`。
- 执行时间：2026-11-11 11:00–11:40（Asia/Shanghai）。
- 执行约束：先只读盘点再三档处置；删 worktree 只用 `git worktree remove`，**不加 `--force`**；白名单 7 棵不动；不 kill 进程、不 `git reset` 清障；不碰 8080 / 8082 / 5944、容器、卷、`READONLY` 哨兵；不动 `D:\agentABC\coa` 主工作区内容与 `.git` 配置。

## 1. 清理前后三个数字

| 指标 | 清理前 | 清理后 | 变化 |
|---|---|---|---|
| 注册 worktree（`git worktree list`，含主树） | 68 | **25** | −43 |
| `wt` 下的实际目录 | 67 | **29** | −38（其中 5 个是未注册残目录，见 §5） |
| 本地分支（`git branch`） | 75 | **32** | −43 |
| D 盘可用空间（字节） | 91,049,586,688 | 96,091,377,664 | **+5,041,790,976（≈ +4.69 GiB）** |

口径说明：

- 可用空间为同一命令行时点实测值；清理期间有其他并行会话在写盘，且各树顶层 junction 只释放链接本身，故该增量与被删树名义体积（≈3,822.6 MB）不构成严格对账关系，仅作实测参考（+4.69 GiB ≈ 4,808 MB）。
- 已删 38 棵树的**名义体积合计 ≈ 3,822.6 MB**（按不跟随 junction 的口径统计，不含 `node_modules` 链接目标）。
- 表中「清理后 32 条分支」为清理动作结束时的实测值；本文档为提交证据另建了分支 `docs/worktree-cleanup-20261111`，故当前仓库实际为 33 条本地分支。

## 2. 已删除的 38 棵 worktree

判定条件（逐棵在删除前复核）：分支 HEAD 是 `luke` 的祖先（`git merge-base --is-ancestor`）+ `git status --porcelain` 为空 + 无未跟踪文件 + 不在白名单。

### 2.1 一次删除成功（34 棵）

| 路径 | 分支 | 名义体积(MB) |
|---|---|---|
| `wt/test-sync` | `feat/test-sync` | 833.4 |
| `wt/ontology-owner-migrate` | `feat/ontology-owner-migrate` | 764.7 |
| `wt/synth-routes` | `chore/synth-routes` | 267.4 |
| `wt/sparql-guard` | `feat/sparql-guard` | 79.3 |
| `wt/p0-evidence` | `chore/p0-evidence` | 78.4 |
| `wt/perf-baseline` | `feat/perf-baseline` | 69.5 |
| `wt/authz-map37` | `feat/authz-map37` | 66.9 |
| `wt/test-infra` | `chore/test-infra` | 66.5 |
| `wt/canvas-tests` | `chore/canvas-tests` | 64.4 |
| `wt/p1-02-import-gate` | `p1/import-gate` | 64.1 |
| `wt/p1-15-degraded` | `p1/degraded-flag` | 63.8 |
| `wt/p1-run-repeatability` | `feat/p1-run-repeatability` | 63.8 |
| `wt/import-idempotency` | `test/import-idempotency` | 63.8 |
| `wt/api-stack-size` | `chore/api-stack-size` | 62.4 |
| `wt/r1-platform-db` | `feat/r1-platform-db` | 61.5 |
| `wt/get-import-job` | `fix/get-import-job-local-store` | 60.8 |
| `wt/contract-gap-45` | `feat/contract-gap-45` | 60.0 |
| `wt/p8-ingestion-runs` | `feat/p8-ingestion-runs` | 59.8 |
| `wt/p14-quality-history` | `feat/p14-quality-history` | 59.8 |
| `wt/int-audit`（detached `526650ce`） | — | 56.1 |
| `wt/domain-review` | `docs/domain-review` | 55.9 |
| `wt/base-audit`（detached `a71c47f0`） | — | 55.8 |
| `wt/contract-design` | `docs/contract-design` | 54.9 |
| `wt/dict-comments` | `feat/dict-comments` | 38.1 |
| `wt/datagen-series` | `verify/reload-isolated-20261107` | 37.9 |
| `wt/r02-fix` | `fix/r02-golden` | 37.7 |
| `wt/abox-materialize` | `feat/abox-materialize` | 37.4 |
| `wt/fix-baseline` | `fix/o03-o06-baseline` | 37.4 |
| `wt/r-qa-integration` | `feat/r-qa-integration` | 36.3 |
| `wt/terms` | `feat/terms-gate` | 35.3 |
| `wt/ontology` | `feat/o-gov` | 34.8 |
| `wt/source-ref` | `feat/source-ref` | 34.7 |
| `wt/canvas` | `feat/canvas` | 34.5 |
| `wt/dict` | `feat/dict` | 34.5 |

### 2.2 `git worktree remove` 报错但已反注册、残留已清干净（4 棵）

这 4 棵的 `git worktree remove` 返回 `Directory not empty`，但 git 已在同一次调用中移除注册项并删除树内 `.git`；随后用「不跟随 reparse point」的方式把残留清空（只删 junction 链接本身，见 §7）。

| 路径 | 分支 | 名义体积(MB) | 报错 |
|---|---|---|---|
| `wt/p1-ingestion-runs` | `feat/p1-ingestion-runs` | 91.8 | `Directory not empty`（顶层 `node_modules` 为 junction） |
| `wt/p7-d-group` | `feat/p7-d-group` | 73.8 | 同上 |
| `wt/p4-dict-ops` | `feat/p4-dict-ops` | 65.6 | 同上 |
| `wt/authz-close` | `feat/authz-close` | 59.8 | 同上 |

## 3. 已删除的 43 条本地分支（分组）

删除方式：在 `D:\agentABC\wt\luke-all`（HEAD = `luke`）内执行 `git branch -d`，让 git 自带的「已并入当前 HEAD」校验生效；不使用 `-D`。

**`chore/*`（6）**：`chore/api-stack-size`、`chore/canvas-tests`、`chore/demo-schema53`、`chore/p0-evidence`、`chore/synth-routes`、`chore/test-infra`

**`docs/*`（2）**：`docs/contract-design`、`docs/domain-review`

**`feat/*`（27）**：`feat/abox-materialize`、`feat/authz-close`、`feat/authz-map37`、`feat/canvas`、`feat/contract-gap-45`、`feat/data-takeover`、`feat/datagen-series`、`feat/dict`、`feat/dict-comments`、`feat/integration`、`feat/o-gov`、`feat/ontology-owner-migrate`、`feat/p1-ingestion-runs`、`feat/p1-run-repeatability`、`feat/p10-p11`、`feat/p14-quality-history`、`feat/p15-graph-browse`、`feat/p4-dict-ops`、`feat/p6-sparql`、`feat/p7-d-group`、`feat/p8-ingestion-runs`、`feat/perf-baseline`、`feat/r1-platform-db`、`feat/source-ref`、`feat/sparql-guard`、`feat/terms-gate`、`feat/test-sync`

**`fix/*`（3）**：`fix/get-import-job-local-store`、`fix/o03-o06-baseline`、`fix/r02-golden`

**`integ/*`（1）**：`integ/merge-20261110`

**`p1/*`（2）**：`p1/degraded-flag`、`p1/import-gate`

**`test/*`（1）**：`test/import-idempotency`

**`verify/*`（1）**：`verify/reload-isolated-20261107`

合计 6+2+27+3+1+2+1+1 = **43** 条。

## 4. 跳过不删的 worktree

> 口径更正：上一条简报正文写「11 棵」，实际为 **16 棵**（当时把 7 条「HEAD 有未并入提交」并成了 4 行）。另 `wt/mig-ci` 为扫描开始后新增，未纳入本次范围。

### 4.1 白名单（7 棵，本次完全未动）

`wt/luke-all`（`luke`，当前主线）、`wt/merge-rehearsal`（`integ/quota-m0`）、`wt/ingestion-accept`（`feat/ingestion-accept`，3 个未跟踪证据产物原样保留）、`wt/p1-gate`（`p1/gate-and-e2e`）、`wt/ontology-jobs-table`（`feat/ontology-jobs-table`）、`wt/readonly-freeze`（`feat/readonly-freeze`）、`wt/m3-local-stack`（`feat/m3-local-stack`）。

### 4.2 判定为「不能删」的 16 棵

> 下表「脏」数据为 2026-11-11 11:45 实测（`git status --porcelain` 计数）；其中 `red-shell` 在删除判定时非空、现已被并行线清干净，仍单列说明。

| 路径 | 分支 / HEAD | 原因 |
|---|---|---|
| `wt/doc-claims` | `docs/fix-wrong-claims` | 删除判定时 `status --porcelain` 非空（台账 doc 被修改）；现复查仍有 1 个已跟踪文件被修改：`doc/coa-x/07-研发台账.md` |
| `wt/luke-runbook` | `verify/luke-runbook` `38b9c4c5`（= `luke` tip） | 删除判定时有 `powershell.exe`（PID 28876）命令行引用该路径，判为占用中；现复查另有 1 个未跟踪文件 |
| `wt/red-shell` | `fix/red-shell-bundling` | 删除判定时非空（含未跟踪 `.tmp-*` 探针文件），按规则跳过；现复查已变干净（`dirty=0`），但本轮不再回头处理，列为**可二次清理** |
| `wt/red-infra` | `fix/red-infra-jest` `ba463c31` | 分支在扫描后移动，现比 `luke` 多 1 条提交，不是 `luke` 祖先 |
| `wt/b0-contract` | `feat/b0-contract` `7c6fdf8b` | 29 个已跟踪文件未提交（`mod=29`） |
| `wt/p5-metric-card` | `feat/p5-metric-card` `0a388cf6` | 24 个已跟踪文件未提交（`mod=24`） |
| `wt/p4-dict` | `feat/p4-dict` `0d259b01` | 2 个未跟踪文件（`unt=2`，日志） |
| `wt/p9-gates` | `feat/p9-gates` `bb7ba54b` | 1 个未跟踪目录（`unt=1`，`.p9-evidence/`） |
| `wt/p13-impact` | `feat/p13-impact` `66f186d2` | 1 个未跟踪目录（`unt=1`，`.local-verify/`） |
| `wt/canvas-full` | `feat/canvas-full` `fc2c8c13` | HEAD 有 2 条未并入 `luke` 的提交（判定废弃但保留 ref） |
| `wt/metrics-core` | `feat/m-core` `24a83afe` | HEAD 有 3 条未并入 `luke` 的提交（判定废弃但保留 ref） |
| `wt/metrics-report` | `tmp/merge-v41` `fa16f81b` | HEAD 有 4 条未并入 `luke` 的提交（判定废弃但保留 ref） |
| `wt/p1-ingestion-audit` | `audit/p1-ingestion-runs` `9a4719d8` | HEAD 有 2 条未并入 `luke` 的提交（判定废弃但保留 ref） |
| `wt/quota` | `feat/quota` `1a9b1fad` | HEAD 有 1 条未并入 `luke` 的提交（判定废弃但保留 ref） |
| `wt/retrieval` | `feat/r-qa` `36aa745b` | HEAD 有 4 条未并入 `luke` 的提交（判定废弃但保留 ref） |
| `wt/dryrun` | detached `e0080ab0` | HEAD 有 2 条未并入 `luke` 的提交；树内改动已按台账判定丢弃，但按「HEAD 有未并入提交不删」保留 |

### 4.3 扫描后新增、未纳入

`wt/mig-ci`：`ci/migration-idempotency`，干净；出现时间晚于本次盘点，按「不扩大范围」未处理。

## 5. 5 个残缺目录（保持现状，待占用解除后二次清理）

这 5 个目录已被 git 反注册（不在 `git worktree list` 中，目录内无 `.git`），仓库侧无风险；因文件被运行中的进程占用，`git worktree remove` 与后续清理均无法删净。按决定**不杀进程、不强删**。

| 精确路径 | 占用进程（实测 PID） | 残留体积 | 残留文件数 |
|---|---|---|---|
| `D:\agentABC\wt\data-takeover` | `esbuild.exe` PID **58420**、**8528** | 381.4 MB | 43,231 |
| `D:\agentABC\wt\p6-sparql` | `esbuild.exe` PID **58420**、**8528** | 380.6 MB | 42,238 |
| `D:\agentABC\wt\p15-graph-browse` | `esbuild.exe` PID **58420**、**8528** | 372.0 MB | 42,121 |
| `D:\agentABC\wt\p10-p11` | `esbuild.exe` PID **58420**、**8528** | 370.9 MB | 42,006 |
| `D:\agentABC\wt\demo-schema53` | `python.exe` PID **35936**、**33504**（`demo-schema53\.venv-coa-local\Scripts\python.exe`，8099 演示栈）；`powershell.exe` PID **43860** | 61.2 MB | 5,343 |
| 合计 | — | **≈ 1.57 GB** | 125,939 |

补充事实：

- 4 棵 esbuild 相关的锁是**同一份文件对象**：worktree 内 `node_modules/.pnpm/@esbuild+win32-x64@0.25.12/.../esbuild.exe` 与 `coa/node_modules/.pnpm/...` 为硬链接，进程映像路径显示为 `D:\agentABC\coa\node_modules\...`，删除任一硬链接路径均报「访问被拒绝」。
- `demo-schema53` 的锁来自其自身 `.venv-coa-local` 下运行的 8099 演示栈；该目录下的 `doc/coa-x/tools/api-8099.err.log` 被进程持有。
- **待占用解除后二次清理**：进程退出后对上述 5 个目录执行 `git worktree remove <path>` 已无意义（已反注册），直接删除目录即可；若届时 `node_modules` junction 仍在，先删链接再删目录。

## 6. 保留的 ref

### 6.1 判定废弃但保留 ref 的 8 条

| 分支 | SHA |
|---|---|
| `feat/quota` | `1a9b1fad` |
| `feat/canvas-full` | `fc2c8c13` |
| `feat/m-core` | `24a83afe` |
| `feat/metric-loader` | `66216c14` |
| `feat/r-qa` | `36aa745b` |
| `audit/p1-ingestion-runs` | `9a4719d8` |
| `tmp/merge-v41` | `fa16f81b` |
| `backup/dict-comments-48aba93` | `48aba937` |

### 6.2 保留的 3 条演练分支

`rehearse/merge-20261110` `92a3d89a`、`rehearse/merge-20261110-r2` `327fcb1c`、`rehearse/merge-20261110-r3` `ae163528`。

### 6.3 `feat/r-qa-integration` 被 git 拒绝删除

该分支已并入 `luke`（`git merge-base --is-ancestor` 为真），但**未并入远端跟踪引用** `refs/remotes/luke/feat/r-qa-integration`。`git branch -d` 实测输出：

```
warning: not deleting branch 'feat/r-qa-integration' that is not yet merged to
         'refs/remotes/luke/feat/r-qa-integration', even though it is merged to HEAD.
error: The branch 'feat/r-qa-integration' is not fully merged.
```

按「分支有远端活跃引用时保留」的约束，未使用 `-D`，保留 ref。

### 6.4 其他保留

- `feat/m-report`（`abea9576`）：未并入 `luke`，不在上述 8 条废弃名单内，按决定保留不动，登记为「未并入」。
- `backup/doc-auto-sync`：该名字归文档自动同步会话使用，本次未列入删除清单（执行时该 ref 不存在）。
- `refs/remotes/luke/automated/mirror-sync-*`：**171 条**远端跟踪镜像引用，清理前后均为 171，未改动。

## 7. 方法说明

1. **junction / 符号链接只删链接本身**：worktree 顶层 `node_modules`（及 `demo-schema53` 的 `.venv-coa-local`）是指向共享目录的 junction。清理残留时使用 `[System.IO.Directory]::Delete(path, false)` 与逐项遍历（遇 reparse point 即停，不递归），只移除链接，不触碰目标内容。
2. **共享目标完好性已实测**：
   - `D:\agentABC\coa\node_modules` 结构完整（`.pnpm` 884 项，42,561 个文件 / 0.33 GB），`nx 22.7.10`、`pnpm 10.34.5` 均可正常解析。
   - `D:\agentABC\coa\.venv-coa-local\Scripts\python.exe` 存在，目标未被删。
3. **`coa` 主工作区 21 条软链指向 `wt/merge-rehearsal` 未受影响**：`coa/node_modules/nx`、`coa/node_modules/pnpm`，以及 `coa/packages/web-app/node_modules` 下 19 个条目（`typescript`、`vite`、`react`、`react-dom`、`vitest`、`eslint` 等）均软链到 `D:\agentABC\wt\merge-rehearsal\node_modules\.pnpm\...`；`merge-rehearsal` 在白名单内未动，这 21 条链接全部保持有效。本次删除的 38 棵树中**没有**任何一棵是该路径的链接目标（实测所有指向 `wt` 的软链目标前缀只有 `D:\agentABC\wt\merge-rehearsal`）。
4. **不使用 `--force` / 不 `git reset` 清障**：删除失败的树一律跳过并记录；`git worktree remove` 报 `Directory not empty` 的 9 棵中，4 棵残留已在确认无进程占用后按第 1 条方式清干净，5 棵保留现状。
5. **`git worktree prune` 不需要跑**：`git worktree prune --dry-run -v` 清理前后均无输出；`git worktree list` 中无「registered but missing on disk」条目。
6. **与并发写者的关系**：`D:\agentABC\coa` 上有每小时一次的文档自动同步会话（切 `luke` → `stash` → `reset` → 删 `backup/doc-auto-sync` → 提交 `docs: auto-sync` → push）。清理期间观察到 `wt/red-shell`、`wt/red-infra`、`wt/doc-claims` 状态变化与新树 `wt/mig-ci` 出现，均按「跳过并记录」处理，未做任何重试硬删。
7. **未改动的文件**：本次只新增本文件，未改写 `doc/coa-x/07b-研发台账-追加区.md`（该文件另有并行修改）。
8. **提交方式**：在独立临时工作树 `D:\agentABC\_tmp\wt-cleanup-doc`（分支 `docs/worktree-cleanup-20261111`，基 `luke`）本地提交，不 push、不建 PR；提交后移除该临时工作树。

## 8. 复核命令

```text
git worktree list --porcelain | Select-String '^worktree '
git branch --format='%(refname:short)'
git worktree prune --dry-run -v
git merge-base --is-ancestor <branch> luke
```
