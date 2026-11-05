# 实时资源体检报告（res-health-1139）

- 采集时间：2026-11-05 11:38–11:40（Asia/Shanghai）
- 采集方式：只读优先；仅执行了 1 个已退出容器移除 + `docker builder prune -f`
- 禁止项全部遵守：未执行 `docker system prune -a`、未碰 volume、未 `down -v`、未删 `data/`、未停平台容器、未关 Trae、未动 `D:\FS-LDM`

## 1. 宿主快照

| 指标 | 清理前(11:38) | 清理后(11:39) |
|---|---|---|
| 物理内存总量 | 32,594 MB | 32,594 MB |
| 可用内存 | 15,133 MB (46.4%) | 15,530 MB (47.6%) |
| 逻辑核数 | 20 | 20 |
| CPU 即时占用 | 9.7% | 2.6% |
| C 盘可用 | 29.44 GB | 29.44 GB |
| vmmem（WSL2 虚拟机） | 6,574 MB | 6,610 MB |
| 运行中容器 | 6 | 6 |
| 构建缓存 | 2.998 GB（可回收 1.453） | 1.545 GB（可回收 0） |

## 2. 进程 / 容器明细与判定

| 进程/容器 | CPU | 内存 | 内存占比 | 判定 | 处置 |
|---|---|---|---|---|---|
| `vmmem` (pid 102464) | 未测到 | 6,610 MB | 20.3% | 必要 | 勿动（Docker/WSL2 虚拟机整体） |
| `Trae CN.exe` renderer (20288) | 78.7s 累计 | 449–658 MB | ~1.4–2.0% | 必要 | 勿动（当前会话渲染主进程） |
| `Trae CN.exe` 其余 15 个进程（gpu/utility/node×5/native×2/扩展） | 累计 3–47s | 23–271 MB 各 | 合计 ~1.4 GB | 必要 | 勿动（单实例 Electron 正常拆分，未见重复主进程/重复窗口） |
| `node.exe`（.workbuddy 22.22.2） | — | 107 MB | 0.3% | 必要 | 勿动（WorkBuddy 运行时） |
| `WorkBuddy` ×4 (55900/89168/62800/…) | 76–336s 累计 | 197–293 MB | 合计 ~0.9 GB | 必要 | 勿动（后台任务在跑） |
| `com.docker.backend` (77344) | 2,714.9s 累计 | 177 MB | 0.5% | 必要 | 勿动（Docker Desktop 引擎） |
| `agent-platform-embedding` | 0.80% | 2,815 MB | 24.1% | 必要（长任务在用） | 勿动；**未限核**（见第 4 节） |
| `agent-platform-reasoner` | 182.59% | 121.9 MB | ≤3.97% | 必要（正在跑 ELK 推理 `robot.jar -Xmx2g`） | 勿动 |
| `agent-platform-api` | 3.10% | 192.9 MB | 1.6% | 必要 | 勿动 |
| `agent-platform-postgres` | 5.15% | 308.4 MB | 2.6% | 必要 | 勿动（数据卷 pgdata） |
| `agent-platform-oxigraph` | 0.00% | 9.4 MB | 0.08% | 必要 | 勿动（数据卷 oxigraph-data） |
| `oxi-empty` | 0.00% | 0.4 MB | 0.00% | 可暂停（benchmark 基线实例） | 暂留：占用可忽略，且基线任务可能复用 |
| `oxi-bench` | — | — | — | 可清理（`Exited(137)` 9 小时） | **已移除** |
| Docker 构建缓存 | — | — | — | 可清理 | **已 prune，回收 1.453 GB** |
| Docker 悬空镜像 1.24 GB | — | — | — | 可清理（需确认） | 未动（本轮禁止 prune 镜像，仅记录） |
| `SOGOUSmartAssistant` ×2 / `SogouCloud` / `SGTool` | 累计 2,859s/1,212s/615s/248s | 13–60 MB | <0.2% 合计 | 可暂停（输入法常驻） | 建议用户自行决定，未动 |
| `wps` / `wpscloudsvr` | 364s/165s 累计 | 120/22 MB | 0.4% | 可暂停（无任务时应空闲） | 未动 |
| `Memory Compression` | — | 789 MB | 2.4% | 必要 | 勿动（系统内存压缩） |

> 说明：容器在 11:37–11:39 之间被**外部编排流程**重启（api `StartedAt=11:39:06`、reasoner `11:39:28`、oxigraph `ExitCode=137`），三者 `RestartCount=0`，说明是任务脚本主动重启而非崩溃循环；本次未干预。

## 3. 清理执行记录

| 动作 | 对象 | 结果 |
|---|---|---|
| `docker rm oxi-bench` | `Exited(137)` 一次性容器 | 已移除（数据卷保留） |
| `docker builder prune -f` | 371 → 81 条构建缓存 | 2.998 GB → 1.545 GB，**回收 1.453 GB** |
| 清理 `_impl/logs` 超 1 天日志 | `D:\agentABC\_impl\logs` | **目录不存在**，未测到可清理日志，未执行 |
| 结束僵尸探针进程 | `probe_*.py` / `latency_probe.py` | 未测到 `python.exe` 进程，无需处理 |
| 确认 reindex/import 是否在跑 | `pg_stat_activity` | **未测到**（psql 库名/凭据不匹配，无法确认）；因此未暂停 embedding |
| 重复 Trae 实例清理 | Trae CN.exe | 仅 1 个实例/1 个主窗口，无重复，未动 |

## 4. 稳定性结论与建议

- **embedding 未限核**：`NanoCpus=0`、`CpuQuota=0`、`CpuShares=0`、`MemLimit=0`，R5 要求的 `cpus: 4` **未落实**。当前实测 CPU 仅 0.80%，宿主 20 核余量充足（总占用 2.6%），**目前不需要紧急限核**；但一旦触发批量索引，它可占满多核，与 reasoner（182% CPU）抢核。建议在下一次编排重启时补 `cpus: 4`、`mem_limit: 8g`。
- **内存余量**：可用 15,530 MB / 32,594 MB = **47.6%**，远高于 15% 警戒线，无触发风险。
- **主要内存去向**：vmmem 6.6 GB（Docker/WSL2 整体，含 embedding 2.8 GB）+ Trae 家族 ~2.3 GB + WorkBuddy ~0.9 GB。
- **隐患点**：(1) reasoner 容器内存上限 3 GB，内部却跑 `java -Xmx2g`，并发两个推理任务即可能 OOM；(2) embedding 无任何资源上限；(3) 宿主内存 32 GB 对"Trae + Docker + 平台 + WPS/输入法"同时在线偏紧，可用常年在 40–50%。
- **下一轮建议**：① 给 embedding 与 reasoner 显式限核/限内存；② 把 `llm` 类模型权重与 Docker vhdx 迁到 D 盘（C 盘仍只有 29 GB 可用）；③ bench 结束后统一 `docker image prune`（可再回收 1.24 GB）；④ 为平台容器加 `restart: on-failure` 之外的显式 `healthcheck` 间隔，避免编排脚本频繁重启造成观测噪声。

## 5. 清理前后对比汇总

| 指标 | 前 | 后 |
|---|---|---|
| C 盘可用 | 29.44 GB | 29.44 GB（Docker 数据在 vhdx 内，prune 不改变宿主可用空间） |
| 宿主可用内存 | 15,133 MB | 15,530 MB |
| 运行中容器数 | 6 | 6（另移除 1 个 Exited） |
| 构建缓存 | 2.998 GB | 1.545 GB |
| 镜像总量 | 3.257 GB（22 个，1.24 可回收） | 3.257 GB（未动） |
| 数据卷 | 305 MB（2 个，使用中） | 305 MB（未动） |

平台健康：`GET http://127.0.0.1:8080/readyz` → **HTTP 200**，`database/graph/storage` 均 `ok`。

## 6. 处置（2026-11-05 11:45 更新：只改配置，未重启）

> 原则：长任务（S13 acceptance）运行期间不改运行时，只落配置与文档。

### 6.1 已改文件与 diff 摘要

| 文件 | 改动 | 说明 |
|---|---|---|
| `D:\agentABC\_impl\docker-compose.yml` L103-104 | `reasoner.mem_limit: 3g` → **4g** | `JAVA_OPTS=-Xmx2g` 不变，2g 余量给元空间/线程栈/uvicorn |
| `D:\agentABC\_impl\docker-compose.yml` L82-84 | embedding 新增 **`cpus: "4"`** | 落实 R5；`docker compose config` 渲染为 `cpus: 4` |
| `D:\agentABC\_impl\OPEN-QUESTIONS.md` | 新增 **OQ-60** | reasoner 无并发锁，本轮只调配额、不改逻辑；触发条件=出现 OOMKilled |
| `D:\agentABC\_impl\WORKLOG.md` | 新增 **W-15** | 记录"待下个维护窗口生效"及生效/验证命令 |

校验：`docker compose --env-file .env config -q` → 退出码 0；回读 `cpus: 4`、`mem_limit: "4294967296"`。

### 6.2 待维护窗口清单

| 参数 | 旧值（当前运行时） | 新值（配置文件） | 生效命令 | 验证命令 |
|---|---|---|---|---|
| `reasoner.mem_limit` | 3221225472 (3g) | **4294967296 (4g)** | `docker compose --profile learn up -d reasoner embedding` | `docker inspect agent-platform-reasoner --format '{{.HostConfig.Memory}}'` → `4294967296` |
| `embedding.cpus` | 0（NanoCpus=0） | **4 核** | 同上（同一次 up -d） | `docker inspect agent-platform-embedding --format '{{.HostConfig.NanoCpus}}'` → `4000000000` |
| `reasoner` 并发串行化 | 无锁 | **未改逻辑**（OQ-60） | 需改 `reasoner/app.py`，另行排期 | 并发两次 `/v1/reason`，第二次应返回 `E_REASONER_BUSY`（待实现） |

生效条件：**长任务结束后的维护窗口**执行一次 `up -d`；本次未重启任何容器。

### 6.3 `oxi-empty` 处置结论：**保留，不 stop**

理由：① 实测 0.4 MB / 0% CPU，资源代价可忽略；② 它是空图基线实例（对应 `oxi-*` 基准序列），当前 S13 acceptance/benchmark 仍在跑，停掉可能破坏基线可比性；③ 无数据卷、无业务数据，随时可停可删。建议：benchmark 系列全部结束后统一 `docker stop oxi-empty`（保留容器，不删卷）。

### 6.4 R1 违规判定：**有（并发会话导致）**

- 证据 1：`agent-platform-api` `StartedAt=2026-11-05T03:39:06Z`（本地 11:39:06）、`reasoner` `11:39:28`、`oxigraph` `ExitCode=137` 且 `11:37:17` 重启，三者 `RestartCount=0` → 非崩溃自动重启，是外部 `compose up -d / restart` 主动拉起。
- 证据 1b：11:45 复核时 `reasoner` 又变成 `StartedAt=11:42:31`（`RestartCount` 仍为 0、`MemLimit` 仍为 3g）→ 窗口内**至少 2 次**外部重建/重启，且非本次操作所致（本轮只执行了只读的 `docker compose config`）。
- 证据 2：`WORKLOG.md` W-13「遗留①」已自行记录：*"readyz 503 while graph down 首轮 status=0 系并发会话重启 api 容器所致（RestartCount=0、ExitCode=0、日志为优雅 Shutdown）"*。
- 证据 3：11:40–11:41 同一时刻 `_impl/logs/s13h10-acceptance.log`、`s13h10-smoke-s7.log` 正在写入 → 确有 acceptance 长任务在跑，此时重启容器即打断任务 = **违反 R1**。
- 责任会话：**未测到**（`docker events --since 03:30 --until 03:45` 该时间窗无记录返回，daemon 事件未保留）；仅能判定为"并行会话"，无法定位 session id。
- 整改建议：在 `_impl/scripts` 增加 `compose-guard.ps1`——检测 `docker ps` 中存在 `agent-platform-*` 且 `logs/s13h*-acceptance.log` 在 5 分钟内有写入时，拒绝 `up -d/restart` 并提示"长任务运行中"；所有会话统一走该入口。

## 7. R1 技术拦截落地（2026-11-05 11:46）

> 制度（WORKLOG R1"单写者"）无法约束并行会话（§6.4 已证实违规但定位不到责任会话），本轮改为**脚本级互斥**：`_impl/scripts/compose-guard.ps1` + `up.ps1` 闸门。**未重启任何容器、未改 `src/`。**

### 7.1 实现

| 项 | 内容 |
|---|---|
| 锁文件 | `_impl/.lock/heavy.lock`（JSON：`owner` / `started_at` / `heartbeat_at` / `purpose` / `ttl_minutes`） |
| `acquire -Purpose <str> -TtlMinutes 30` | 被占且心跳 < TTL → `E_BUILD_CONFLICT`，退出码 **75**，打印 holder 的 owner/purpose/started_at/heartbeat_age；心跳 ≥ TTL → `warn: stale lock taken over` 并接管 |
| `check` | 只判断不获取；`free`→0，`busy`→75（stale 视作 free） |
| `release [-Owner]` | 仅 owner 相同可释放；不匹配 → `E_OWNER_MISMATCH`，退出码 1，锁保留 |
| `heartbeat` | 长任务循环内轻量刷新 `heartbeat_at`，不重读整锁（无锁时 `E_NO_LOCK`→1） |
| `status` | 打印锁内容 + `state=busy/stale` + 心跳年龄 |
| 入口接入 | `scripts/up.ps1` 第一段执行 `compose-guard.ps1 check`，非 0 即打印 `E_BUILD_CONFLICT` 并 `exit 75`，**绝不执行 `docker compose up`**；新增 `-DryRun` 仅做闸门校验 |

### 7.2 锁口径统一

- **权威**：PG advisory lock `platform:heavy`（`src/platform_core/importer.py` L517-520，进程内、随任务释放）——运行时唯一真权威，**保持不变**。
- **前置闸门**：`compose-guard` 文件锁——跨会话/跨进程入口拦截，解决"PG 锁只在进程内、拦不住别的会话 `compose up`"的漏洞。两者层次不同，**不重复、不 deprecated**。
- **未接入（有意）**：`tests/acceptance.ps1` L46 也直接 `docker compose up -d`，但该测试正在运行，编辑 .ps1 可能被 PowerShell 增量读取而破坏执行 → 本轮不动，列为待办：本轮 acceptance 结束后把 L45-46 改为同样先 `guard check`。

### 7.3 真实验证输出（11:46）

| 测试 | 命令 | 实际输出（关键行） | 退出码 |
|---|---|---|---|
| 1 acquire | `compose-guard.ps1 acquire -Purpose test -TtlMinutes 30` | `acquired owner=UVSFUJSA\cpslau purpose=test` | 0 |
| 1b check | `compose-guard.ps1 check` | `busy owner=UVSFUJSA\cpslau purpose=test ... heartbeat_age=0min` | **75** |
| 1c 入口拦截 | `up.ps1 -DryRun` | `[up] E_BUILD_CONFLICT: 已有重任务持锁，拒绝启动/重建。` | **75** |
| 1d 未重启证明 | `docker inspect agent-platform-reasoner --format '{{.RestartCount}}'` | before=0 / after=0 | — |
| 2 误释放 | `compose-guard.ps1 release -Owner '另一个owner'` | `E_OWNER_MISMATCH: 拒绝释放。锁持有者=UVSFUJSA\cpslau，请求者=另一个owner`；`LOCK_STILL_EXISTS=True` | **1** |
| 3 释放后通过 | `release` + `up.ps1 -DryRun` | `released owner=...` / `[up] guard ok (heavy lock free)` / `dry-run: 未执行 docker compose up` | 0 / 0 |
| 4 僵尸锁接管 | 写入 heartbeat 60min 前的假锁 → `acquire -Purpose stale-takeover` | `free (stale lock present, age=60min > ttl=30min)` → `warn: stale lock taken over (previous owner=ghost\other-session, heartbeat_age=60min > ttl=30min)` | 0 |
| 5 心跳 | `heartbeat` | `heartbeat ok at 2026-11-05T03:46:25Z (owner=UVSFUJSA\cpslau)` | 0 |
| 6 收尾 | `release` → `check` | `released owner=...`；`LOCK_CLEANED=True`；`free` | 0 / 0 |

> 注：首次执行因 PS5 按 ANSI 读取无 BOM 的 UTF-8 脚本导致中文注释解析失败（`RedirectionNotSupported`），已改为 **UTF-8 with BOM** 保存后全部用例通过。

### 7.4 验收脚本止损阀（`tests/acceptance.ps1`，2026-11-05 11:52）

**先说影响（已改变判定语义，非静默改动）**：
- 变更前：L45-46 `docker compose up -d` 兼作"确保服务在跑"的兜底，半挂的容器会被重建拉起；该项 FAIL 会直接计入 failed。
- 变更后：① 容器全 `running` → PASS 但**不重建**；② 缺失/已停止宿 → 才启动，且 `guard` 判定 busy（他人持锁）→ 打印 `skipped: heavy lock busy` 并计 `skipped`（**既不 PASS 也不 FAIL**，不重试、不重启）；③ 存在但 `healthy=false` → 打印 `[DEGRADED]` 并计 `degraded`，**不重建**，由调用方决定。
- 后果：验收不再"修复环境"，只报告现状。若容器处于半死状态，后续 smoke 可能大面积超时（变更前会被 `up -d` 兜底）。这是有意的取舍：验收脚本自身是长任务中断来源之一，先止损。
- 另：纯 smoke 类步骤（`platform smoke-*`、`facts-*`、`check-config`）**不持锁也能跑**；最后的 reasoner/oxigraph 停起（L194-234）是验收用例本身，属于预期内 stop/start，不是"重建"。

| 改动 | 内容 |
|---|---|
| `param([switch]$OnlyPreflight)` | 只跑前置检查（config + 容器状态 + guard 判定）后 `exit 0`，不进入 smoke/停起用例 |
| 首行输出 | `heavy_lock=free` 或 `heavy_lock=busy owner=... purpose=...`（脚本启动即打印，便于事后归因"这次跑有没有被别人影响"） |
| 容器就绪判定 | `docker compose config --services` × `docker compose ps -a --format '{{.Service}}|{{.State}}|{{.Health}}'`，不再靠 `up -d` 兜底 |
| 长任务持锁 | 全量运行 `acquire -Purpose "acceptance full run" -TtlMinutes 30 -Owner "<host>\<user>#<PID>"`，`try/finally` 收尾 `release`；拿不到锁只告警继续（本脚本无 import/reindex 步骤） |
| owner 身份 | 改为带 `$PID`，否则同用户的不同会话 owner 相同、无法区分（本轮实测暴露该缺陷并已修） |

验证（真实输出，11:51-11:52）：

| 用例 | 命令 | 实际输出 | 退出码 |
|---|---|---|---|
| 他人持锁 → skip | 外部会话持 `embedding-throttle` 锁时跑 `acceptance.ps1 -OnlyPreflight` | `heavy_lock=busy owner=UVSFUJSA\cpslau purpose=embedding-throttle` / `skipped: heavy lock busy (...)` | 0 |
| 未重启证明 | 同上，`docker inspect --format '{{.RestartCount}}'` | 6 个容器 before 全 0 / after 全 0（embedding/api/reasoner/postgres/oxigraph/oxi-empty） | — |
| 假锁 acquire | `compose-guard.ps1 acquire -Purpose test-acceptance` | `E_BUILD_CONFLICT ... holder.purpose=embedding-throttle heartbeat_age=1min` | **75**（被外部锁正确拒绝） |
| `up.ps1` 闸门 | `up.ps1 -DryRun` | `[up] E_BUILD_CONFLICT` | **75** |

### 7.5 后续

- OQ-61：reasoner 单飞锁 + `E_REASONER_BUSY`，**随下个窗口源码一起改**。
- `res-health` 的 §6.2 待维护窗口（reasoner 4g / embedding cpus=4）仍未生效，等长任务结束后一次 `up -d`。

### 7.6 计分语义对照表与运行职责（2026-11-05 11:56）

**PASS / SKIP / DEGRADED 分开计数**，汇总行固定为 `ACCEPTANCE passed=N failed=N skipped=N degraded=N`；`DEGRADED` **不计入 PASS**。

| 场景 | 变更前（`up -d` 兜底） | 变更后（止损阀） |
|---|---|---|
| 容器全 running 且 healthy | `up -d` 幂等执行（但**仍可能按配置重建**）→ PASS | **PASS，不重建**（`containers running (no restart needed)`） |
| **环境半死**：容器 running 但 `health=unhealthy` | `up -d` 可能重建拉起；若重建成功则**故障被掩盖**、计 PASS | **DEGRADED**（`degraded+N`，不计 PASS），**不重建**；退出码 **69** |
| 容器 Exited / 缺失（无他人持锁） | `up -d` 拉起 → PASS | `up -d` 拉起（仅此情况才启动）→ PASS |
| 容器 Exited / 缺失，且**他人持锁** | 照样 `up -d` → **打断长任务** | **SKIP**（`skipped: heavy lock busy` + `WARN: acceptance incomplete`），退出码 **75** |
| 他人正在跑长任务，但容器都 healthy | 不识别，照样 `up -d` → 打断 | 跳过 ensure 步骤，其余 smoke 正常跑，退出码 0 |
| 断言失败 | failed+1 → 1 | 同左 |

**退出码取值与理由**：

| 码 | 含义 | 为什么选它 |
|---|---|---|
| **1** | 断言失败（failed>0） | 沿用原语义 |
| **69** | DEGRADED：环境不健康且未重建 | EX_UNAVAILABLE（sysexits 通用约定）；**未选 78 是因为 78 在本仓库已被 `check-config` 用完**（验收用例里 6 处断言 `exit=78 expected=78`），冲突会导致误读 |
| **75** | SKIP 导致环境未就绪（验收不完整） | 复用 guard 的 E_BUILD_CONFLICT 语义：因锁冲突未能准备环境；另已打印 `WARN: acceptance incomplete`，不静默当通过 |
| 0 | 全通过，或仅跳过"不影响本次验证"的步骤 | — |
| 78 | 仅作为 check-config 用例的**被断言值**出现，不是本脚本退出码 | 避免与 69 混淆 |

### 7.7 运行职责：`up -d` 的兜底能力归谁

**结论：没有被"悄悄移除后无人接手"，但责任明确转移了。**

| 场景 | 谁负责拉起 | 入口 |
|---|---|---|
| 半死容器（DEGRADED） | **guard 持有者**（当前跑长任务/维护窗口的会话）在窗口结束时负责 `docker compose up -d`；无锁时由**人工**负责 | `scripts/up.ps1`（内部先 `guard check` 再 `compose up`） |
| 容器 Exited 且锁空闲 | 任何会话/人工均可 | `scripts/up.ps1` 或 `acceptance.ps1` 的 ensure 分支 |
| 容器 Exited 且锁被他人持有 | **禁止任何人拉起**（会打断长任务）；等持锁者释放或 TTL 30min 过期 | 锁过期后 `acquire` 自动 `warn: stale lock taken over` 接管 |
| 验收发现 DEGRADED | 验收**只报告**（退出 69），由调用方（CI/人工/持锁者）决策 | 报告 + `WARN` |

- 明确禁止：验收脚本在锁被他人持有时拉起容器（这是本次要堵的洞）。
- 兜底失效的边界：如果持锁会话崩溃且不做 heartbeat，锁最长 30 分钟后作废，下一个 `up.ps1`/`acquire` 会接管——因此不会出现"永久无人管"。
- 长任务侧的义务（写进规程）：跑 `import/reindex` 的长任务必须 `acquire` 并在循环里 `heartbeat`，结束后 `release`。

### 7.8 心跳 + PID 存活验证：接管判据（2026-11-05 12:01）

**要修的漏洞**：锁只靠 `heartbeat_at` + TTL 30min 判活。若持锁方跑 40 分钟任务且不心跳，30 分钟后锁被判"僵尸"并被**合法接管** → 等于又造出一个任务打断入口（旧的 `embedding-throttle` 锁就是 0 心跳的实例）。

**改动**：锁内新增 `pid` 与 `host`；stale 判定从"心跳超时"改为"心跳超时 **且** 持有进程确实不存活"。

| 心跳状态 | host | pid 可验证 | 结果 | 输出 / 退出码 |
|---|---|---|---|---|
| `age < TTL` | 任意 | 任意 | 拒绝获取 | `E_BUILD_CONFLICT` / **75** |
| `age < TTL` 且 `age ≥ 10min` | 同机 | 存活 | 拒绝，但提醒 | `warn: holder not heartbeating (pid N alive)` + busy / **75** |
| `age ≥ TTL` | 同机 | **存活** | **拒绝接管** | `E_LOCK_HOLDER_ALIVE` / **76** |
| `age ≥ TTL` | 同机 | 不存在 | 接管 | `warn: stale lock taken over (... process not alive)` / **0** |
| `age ≥ TTL` | 跨机 / 无 pid | 不可验证 | 拒绝 | `E_LOCK_HOLDER_ALIVE`（不可验证）/ **76** |
| `age ≥ TTL` | 跨机 / 无 pid | 不可验证 + `-Force` | 接管 | `warn: cross-host takeover forced` / **0** |

- `check` 在 `age ≥ TTL` 但 pid 存活时返回 **busy(75)**，不把锁判成 free（避免"看门狗"误判）。
- `status` 新增 `holder_alive=True/False/<空>`，state 细分 `busy` / `stale-but-holder-alive` / `stale-unverifiable` / `stale-holder-dead`。
- **R2 规程**：任何 >10 分钟的操作，**每 ≤5 分钟** `heartbeat` 一次；`2×` 间隔（10min）未更新即在 `check` 报警。心跳不是"建议"，是锁有效性的前提。

实测（隔离 root `%TEMP%\guardtest`，不触碰真实锁）：

| 用例 | 输出关键行 | 退出码 |
|---|---|---|
| pid=真实存活(45212)，心跳 60min | `E_LOCK_HOLDER_ALIVE: 心跳超时但持有进程仍存活，拒绝接管。` / `holder.pid=45212` / `heartbeat_age=60min` | **76** |
| pid=99999（不存在） | `warn: stale lock taken over (... process not alive)` → `acquired` | 0 |
| 跨机 `OTHER-PC` 不带 Force | `E_LOCK_HOLDER_ALIVE: 无法验证持有者是否存活（host=OTHER-PC pid=1234）` | **76** |
| 跨机 + `-Force` | `warn: cross-host takeover forced` → `acquired` | 0 |
| acquire→等 120s→heartbeat | `state=busy heartbeat_age=2min` → `heartbeat ok` → `state=busy heartbeat_age=0min` | 0 |
| 心跳 12min + pid 存活 | `warn: holder not heartbeating (pid 23540 alive, age=12min)` + `busy` | **75** |
| 收尾 | `released`、`CLEANED=True`、`free` | 0 |

- 测试在隔离目录 `%TEMP%\guardtest` 进行（复制脚本即可改变锁路径），**真实 `_impl/.lock/heavy.lock` 全程未被覆盖或释放**（当时由并行会话的 `embedding-throttle` 持有）。
- 坑（第二次踩到）：Write 工具写出的 UTF-8 无 BOM 会被 PS5 按 ANSI 解析、中文注释直接导致 `MissingSwitchStatementClause`；脚本必须 **UTF-8 with BOM** 保存。

### 7.9 旧格式锁（无 `pid`/`host`）的接管判据（2026-11-05 12:04）

**风险场景**：现场真实锁 `embedding-throttle` 是旧格式（`holder_alive` 为空）。若照既有规则"心跳超时即僵尸"，它断心跳 30 分钟后会被合法接管，**正好打掉正在跑的嵌入任务**。

**策略：旧格式一律按"可能存活"处理**（不能靠"字段缺失"推断"进程已死"）。

| 锁格式 | 心跳 | 持有者可验证 | `acquire` 行为 | 输出 / 退出码 |
|---|---|---|---|---|
| 旧格式（无 pid/host） | 未超时 | 否 | 拒绝 | `E_BUILD_CONFLICT` / **75** |
| 旧格式（无 pid/host） | 超时 | 否 | **拒绝** | `E_LOCK_LEGACY_UNKNOWN` / **76** |
| 旧格式 + `-Force` | 超时 | 否 | 接管 | `warn: legacy lock takeover forced` / 0 |
| 新格式 · 同机 pid 存活 | 超时 | 是 | 拒绝 | `E_LOCK_HOLDER_ALIVE` / **76** |
| 新格式 · 同机 pid 不存在 | 超时 | 是（已死） | 接管 | `warn: stale lock taken over` / 0 |
| 新格式 · 跨机 | 超时 | 否 | 拒绝 | `E_LOCK_HOLDER_ALIVE`（不可验证）/ **76** |

- **自动升级**：持锁方调 `heartbeat` 时，若锁为旧格式，就地补写 `pid`(当前进程) 与 `host`，并打 `info: lock upgraded to pid/host format`。旧锁在持锁方下一次心跳（≤5min）即自然转正，无需人工迁移。
- **`check` 不再显示空白**：旧格式输出 `holder_alive=unknown (legacy)`，避免被误读成"已死"；心跳 ≥10min 时警告文案也区分为 `holder not heartbeating (legacy lock, age=Nmin)`。

实测（隔离目录 `%TEMP%\guardtest2`，不碰真实锁）：

| 用例 | 实际输出（关键行） | 退出码 |
|---|---|---|
| 旧格式 + 心跳 60min → `check` | `busy (stale but unverifiable: legacy lock, 无法验证持有者; 需 acquire -Force) ... holder_alive=unknown (legacy) heartbeat_age=60min` | **75** |
| 同上 → `acquire` | `E_LOCK_LEGACY_UNKNOWN: 锁为旧格式（无 pid/host），无法验证持有者，拒绝接管。` / `heartbeat_age=60min (ttl=30min)` | **76** |
| 同上 + `-Force` | `warn: legacy lock takeover forced (previous owner=ghost\legacy heartbeat_age=60min)` → `acquired` | 0 |
| 旧格式 → `heartbeat` | `info: lock upgraded to pid/host format` / `heartbeat ok ... pid=48616 host=UVSFUJSA`；锁文件新增 `"pid": 48616, "host": "UVSFUJSA"` | 0 |
| 升级后 `check` | `busy ... pid=48616 host=UVSFUJSA ... holder_alive=True heartbeat_age=0min`（不再 legacy） | 75（因当前用户仍非 owner 场景下的 busy 属预期） |

**真实锁现状（12:04，只读）**：`purpose=embedding-throttle`、`heartbeat_age=15min`、**旧格式**、`holder_alive=unknown (legacy)`、`state=busy`。按兜底纪律**未接管**，等持锁方 `heartbeat` 自动升级；若 40 分钟（约 12:28）仍未升级，上报由人协调。
