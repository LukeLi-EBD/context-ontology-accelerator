# P0-16 本地演示清单与冷启动记录

- 基线：`39bf8919`
- 一键脚本：[10-本地起栈.ps1](../10-本地起栈.ps1)
- 状态：**冷启动本轮未执行**（共享端口被其他并行线占用）；下面第 3 节是今天对运行中栈的只读实测，明确标为 warm，不冒充 cold。

## 1. 一条命令冷启动

在 `doc/coa-x` 目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1
```

- 空库/重建数据卷：加 `-Seed`（幂等，GSP PUT 覆盖）。
- 验收模式：加 `-StrictReconcile`（对账有差异直接失败）。
- 停止：`-Stop`；只停进程保留容器：`-Stop -KeepContainers`。

脚本自带 7 个端口/进程自检，正常结束会打印 8099 / 8101 / 8091 / 5173 / 5444 / 7878 / 7879 的归属说明。5173 **必须**走 `vite.dev-local.config.mjs`，否则本地无 IdP 会出现 `Auth token is empty.`。

## 2. 演示清单（每项都有命令/URL/预期）

| # | 动作 | 命令或 URL | 预期（冷启动干净态） |
| --- | --- | --- | --- |
| 1 | 起栈 | 上面的一键命令 | 脚本退出码 0，7 个端口全部 listening |
| 2 | 桥健康 | `GET http://127.0.0.1:8099/health` | `200 {"status":"ok","provider":"postgres"}` |
| 3 | 本体服务健康 | `GET http://127.0.0.1:8101/health` | `200 {"status":"ok"}` |
| 4 | 系统健康 | `GET http://127.0.0.1:8099/system-health` | `200`，`status` 非 degraded；`schemaVersion.consistent=true` |
| 5 | 指针 | 同上的 `pointer` 字段 | `ok=true`，`status=published`，`tripleCount>0` |
| 6 | 前端 | `GET http://127.0.0.1:5173/` | `200`，`<title>Context Ontology Accelerator</title>` |
| 7 | 图存储 | `GET http://127.0.0.1:7878/` | `200`（Oxigraph 在线） |
| 8 | 对账 | `python doc/coa-x/tools/reconcile_control_plane_ops.py --quiet` | `unregistered_gaps 0`，退出码 0 |

“空库也能起”的验证方式：首次启动不加 `-Seed`，第 4 项允许 `pointer.ok=false`，但 `postgres/oxigraph/ontologyService` 三个组件必须 `ok`；再加 `-Seed` 重启后第 5 项必须变为 `ok=true`。本轮没有执行这一步。

## 3. warm 实测记录（2026-11-11，运行中的共享栈，只读）

共享栈由其他并行线维护，本任务只读探测，未启停、未改配置：

| URL | 实测 |
| --- | --- |
| `GET :8099/health` | `200 {"status":"ok","provider":"postgres"}` |
| `GET :8101/health` | `200 {"status":"ok"}` |
| `GET :5173/` | `200`，`len=598`，`title=Context Ontology Accelerator` |
| `GET :8099/system-health` | `200`，但 `status=degraded`：`postgres/oxigraph/ontologyService` 为 `ok`；`contextManager` 为 `error`（8091 未监听，`ConnectError`）；`objectStore` 为 `error`（对象根目录不存在）；`schemaVersion={codeVersion:49, dbVersion:53, consistent:false}`；`pointer.ok=true`，`versionId=ont-6b12938750ac`，`semver=0.10.0+rollback.2`，`tripleCount=2696`，`namedGraphs=33` |
| 端口 | 5444/7878/7879 listening；8091 **not** listening |

结论：栈的桥、本体服务、前端、图存储在跑；`contextManager` 与对象存储未起，且库版本 53 高于本树代码 49，所以 `consistent=false`。这不满足第 2 节第 4 项的干净态预期，不能当作冷启动通过记录。

## 4. 显式开口项 `DEMO-COLDSTART`

- **为什么不执行**：一键脚本固定占用 5444 / 7878 / 7879 / 8099 / 8101 / 8091 / 5173，这些端口当前被其他并行线的共享栈占用；本任务的硬约束是不碰共享端口，`-Stop` 也会误停别人的栈。脚本没有端口参数化，无法在隔离端口冷启动。
- **影响面**：演示清单的第 1、4、5、7、8 项本轮只有 warm 或静态证据，没有“从零起栈”的一次性记录；第 2、3、6 项有真实响应。
- **期限**：不晚于下一个 tag。到点在一个端口空闲的窗口（或独立机器）跑一次完整一键冷启动，把脚本自检与第 2 节 8 项结果贴回本节。
- **谁来还**：本地栈维护人（`10-本地起栈.ps1` 的 owner）。
- **关闭条件**：冷启动后 `status` 非 degraded、`schemaVersion.consistent=true`、8 项全过。
