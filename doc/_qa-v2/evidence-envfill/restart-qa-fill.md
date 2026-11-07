# platform-qa-fill 停栈与恢复记录

- 停栈时间：2026-11-07 09:33 左右（Asia/Shanghai）
- 操作：`docker compose -p platform-qa-fill stop`（仅停止；未删除容器、未删除卷、未执行 `down -v`）
- 数据根：`D:/agentABC/data-qa-fill`；卷 `platform-qa-fill_pgdata`、`platform-qa-fill_oxigraph-data` 保留
- 取消停栈前置条件：8080 `agent-platform` 与 8082 `platform-acceptance` 全程未触碰

## 恢复命令

```powershell
# 方式 A：原样起回（不重建、不改配置，容器与卷都在）
docker compose -p platform-qa-fill start
```

```powershell
# 方式 B：走既有脚本（保留原参数；-BootstrapSource 仅在数据根缺失时生效，
# 现有 data-qa-fill 不会被改写，T-Box 内容哈希不变）
powershell -ExecutionPolicy Bypass -File scripts\acceptance-stack.ps1 up `
  -ComposeProject platform-qa-fill `
  -ApiPort 8085 -PgPort 5435 -ReasonerPort 7885 -EmbeddingPort 8086 -OxigraphPort 0 `
  -DataRoot D:\agentABC\data-qa-fill -ModelsDir D:\agentABC\data\models `
  -WaitSeconds 180 -EmbeddingWaitSeconds 600
```

注：`acceptance-stack.ps1` 内部固定传 `-BootstrapSource '../doc/_fsldm/fsldm-merged.ttl'` 与默认
`-ExtraOntologySeeds '../doc/_fsldm/fsldm-metrics.ttl'`，这两项只在新播种数据根时生效。

## 容器清单（停栈前采集，2026-11-07 00:50Z 启动）

| 容器 | ID | 镜像 | 端口 | 挂载 | 启动时间 |
|---|---|---|---|---|---|
| platform-qa-fill-api | cd29fe67cd551ad73ea595b02c12cce7792a8617b72ac8158034f8e4039506d6 | agent-platform:0.1-s5 | 127.0.0.1:8085→8080 | bind `D:/agentABC/data-qa-fill`→/data | 2026-11-07T00:50:31Z |
| platform-qa-fill-postgres | ada848f1561263b330697d3047bfea5ab04655b7bf461a5f2dc7aa7c85173708 | pgvector/pgvector:pg18-trixie | 127.0.0.1:5435→5432 | volume `platform-qa-fill_pgdata`→/var/lib/postgresql | 2026-11-07T00:50:26Z |
| platform-qa-fill-embedding | 96466f1b2012e094619d04b025d130cc0d74c22b720f004ca9964a21d99c5ba8 | ghcr.io/huggingface/text-embeddings-inference:cpu-1.8 | 127.0.0.1:8086→80 | bind `D:/agentABC/data/models`→/data/models | 2026-11-07T00:50:26Z |
| platform-qa-fill-reasoner | a1a5300f52b50841f1d0916928f6e81616c9070ca3d4fcf07c30736995d03ab8 | agent-reasoner:0.1-s5 | 127.0.0.1:7885→7879 | 无 | 2026-11-07T00:50:26Z |
| platform-qa-fill-oxigraph | ba73f41bbbb9ede15227edb4400ffcda8498c292f6d278d148f4ac8615d275f8 | oxigraph/oxigraph:0.5.7 | 无 | volume `platform-qa-fill_oxigraph-data`→/data | 2026-11-07T00:50:26Z |

## 停栈前内存基线

| 项 | 读数 |
|---|---|
| qa-fill 整栈 | 3.262 GiB（embedding 2.693 GiB） |
| acceptance 整栈 | 3.179 GiB（embedding 2.151 GiB） |
| agent-platform 整栈 | 3.343 GiB（embedding 1.728 GiB） |
| 合计 | 9.784 GiB（embedding 合计 6.572 GiB） |
| 主机可用内存 | 8.55 GB（已用 73.1%） |
| docker_data.vhdx | 16,233 MB |
