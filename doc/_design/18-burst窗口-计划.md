# 18-burst 窗口 · 立即执行版（S14H-BURST）

> 状态：**立即执行**（窗口 = 从启动时刻起持续，直到手动停止或全量完成）。原 22:00–07:00 定时窗口作废。
> 唯一写者纪律：重任务必须持有 `compose-guard` heavy 锁；burst 期间**不重建镜像**。

## 0. 已确认的基线（2026-11-05 15:00 实测）

| 项 | 实测值 |
|---|---|
| 宿主逻辑核 | 20 |
| 选档规则 | ≥12 核 → embedding cpus=8；≤8 核 → 总核数-2（不低于 4）；9–11 核 → 6 |
| 阶梯测试（S14H-CORES） | 8（当前）→ 12 → 16，`burst.ps1 on -Cpus N -Rayon N`；某档提升 <15% 退回前档；16 核时宿主 CPU ≥80% 立即退 12；`restarts` 增长或 smoke 不通过立即退回 |
| 环境上限（实测） | 宿主 20 逻辑核，但 Docker Desktop VM 只分配 12 CPU；`--cpus 16` 会被拒绝（`range of CPUs is from 0.01 to 12.00`），16 档不可执行 |
| 最终定档（实测） | **8 核**：12 核仅 +6.5% 吞吐，低于 15% 门槛，已退回 |
| `NanoCpus` | `8000000000`（8.00 核） |
| `RAYON_NUM_THREADS` | 8 |
| `max_chunks_per_sec`（/status） | `0.0`（不限速） |
| embedding `RestartCount` | 0 |
| `/readyz` | 200 |
| `smoke-embed` | `S13b SMOKE 12/12`（含 3 条防污染收尾断言） |
| real-12（438 chunk） | `embedded=438/438, remaining=0, degraded=false`；补跑 138 条 / 213.3s = 0.65 chunk/s |

## 1. 前置条件检查清单（逐条可执行）

| # | 检查 | 命令 | 期望 |
|---|---|---|---|
| 1 | 镜像 tag/构建时间 | `docker inspect -f '{{.Config.Image}} {{.Created}}' agent-platform-api` | `agent-platform:0.1-s5`，构建时间晚于最近一次代码修改 |
| 2 | 服务就绪 | `curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:8080/readyz` | `200` |
| 3 | schema 版本 | `curl.exe -s http://127.0.0.1:8080/status` → `.schemaVersion` | `17`（与 `SUPPORTED_SCHEMA_VERSION` 一致） |
| 4 | burst 脚本 dry-run | `powershell -File scripts/burst.ps1 on -DryRun -Deadline "2026-11-06 07:00"` | 打印 `cpus/rayon/rate` 三项真实值，不改变容器 |
| 5 | 大文档四条已验收 | `logs\s14h17-*.log` + 本文档 0 节 | 中断续跑 `embedded==parsed`、重复 0、checkpoint 生效、real-15 向量齐 |
| 6 | 向量分区正确 | `docker compose exec -T platform python -m platform_core.cli smoke-embed --config /data/platform.yaml` 后查 `/status` | `embedding.model=BAAI/bge-m3`（不是 `fake-hash-1024`） |
| 7 | 正式指针干净 | `psql ... "SELECT name,version_id FROM platform.graph_pointer"` | `tbox/current` = 生产版本（非 smoke `ont-*`） |

> **任一条不满足 → 不启动 burst，跳过并报告**，不允许定时任务硬跑。

## 2. 精确命令序列

```powershell
# 0) 持锁（owner 必须是长驻进程 PID；本脚本 acquire 后自己 release）
powershell -File scripts/compose-guard.ps1 acquire -Purpose "burst-window" -TtlMinutes 30 -Owner "$env:COMPUTERNAME\$env:USERNAME#$PID"

# 1) 开档（自动按核数选 cpus/rayon，rate=0）
powershell -File scripts/burst.ps1 on -Deadline "2026-11-06 07:00"
# 确认
docker inspect -f '{{.HostConfig.NanoCpus}}' agent-platform-embedding        # 8000000000
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' agent-platform-embedding | Select-String RAYON
(Invoke-RestMethod http://127.0.0.1:8080/status).providers.embedding.limits.max_chunks_per_sec  # 0
docker compose exec -T platform python -m platform_core.cli smoke-embed --config /data/platform.yaml  # 8/8
docker inspect -f '{{.RestartCount}}' agent-platform-embedding                # 不增长

# 2) 单篇入库 + 索引（示例：real-12；每篇都记录墙钟）
$doc = (curl.exe -s -F "file=@D:\agentABC\_impl\data\bench-real\real-12.docx" http://127.0.0.1:8080/documents | ConvertFrom-Json)
$t1 = Get-Date
$r = (curl.exe -s -X POST "http://127.0.0.1:8080/documents/$($doc.documentId)/index" | ConvertFrom-Json)
$wall = [math]::Round((New-TimeSpan $t1 (Get-Date)).TotalSeconds,1)
"wall=${wall}s chunk/s=$([math]::Round($r.embedded/$wall,2)) remaining=$($r.remaining) degraded=$($r.degraded)"

# 3) 断点续跑（中断/暂停后）
#    - 直接重复 POST 同一 document 的 /index：按 chunk_embedding 已有行跳过
curl.exe -s -X POST "http://127.0.0.1:8080/documents/<documentId>/index"
#    - 每 50 提交一次断点（存在 platform.document.manifest.embedCheckpoint）
docker compose exec -T postgres psql -U platform -d platform -c `
  "SELECT manifest->'embedCheckpoint' FROM platform.document WHERE document_id='<documentId>';"
#    - embedded 与 parsed 差异
docker compose exec -T postgres psql -U platform -d platform -c `
  "SELECT count(c.*) AS parsed, count(e.*) AS embedded FROM platform.document d LEFT JOIN platform.document_chunk c ON c.document_id=d.document_id LEFT JOIN platform.chunk_embedding e ON e.chunk_id=c.chunk_id WHERE d.document_id='<documentId>' GROUP BY d.document_id;"
#    - 批间暂停（大文档）：?max_batches=1 每次只跑一批
#      POST /documents/<id>/index?max_batches=1  → paused=true；再次 POST 续跑

# 4) 全量：列出未完成文档，逐个 POST /index（每篇独立墙钟）
docker compose exec -T postgres psql -U platform -d platform -c `
  "SELECT d.document_id, d.filename, count(c.*) AS parsed, count(e.*) AS embedded FROM platform.document d LEFT JOIN platform.document_chunk c ON c.document_id=d.document_id LEFT JOIN platform.chunk_embedding e ON e.chunk_id=c.chunk_id GROUP BY 1,2 HAVING count(c.*) <> count(e.*) ORDER BY 3 DESC;"

# 5) 关档（校验 + 恢复 4 核/RAYON3/rate1.0，再 smoke-embed + /readyz）
powershell -File scripts/burst.ps1 off
powershell -File scripts/compose-guard.ps1 release -Owner "$env:COMPUTERNAME\$env:USERNAME#$PID"
```

## 3. 观测指标（每 30 分钟一行，固定格式）

`时间 | 已处理chunk | 已嵌入chunk | chunk/s | 宿主CPU% | 可用内存GB | C盘可用GB | D盘可用GB | embedding容器CPU%`

采样命令（原样执行，结果追加到 `_design/a_progress.md` 与 `_impl/WORKLOG.md`）：

```powershell
$cpu=(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$os=Get-CimInstance Win32_OperatingSystem; $freeGB=[math]::Round($os.FreePhysicalMemory/1048576,1)
$cGB=[math]::Round((Get-PSDrive C).Free/1GB,1); $dGB=[math]::Round((Get-PSDrive D).Free/1GB,1)
$emb=(docker stats --no-stream --format "{{.Container}} {{.CPUPerc}}" agent-platform-embedding)
$ts=Get-Date -Format 'yyyy-MM-dd HH:mm'
$line="$ts | <已处理> | <已嵌入> | <chunk/s> | $cpu% | $freeGB | $cGB | $dGB | $emb"
Add-Content -LiteralPath D:\agentABC\_design\a_progress.md -Value "- BURST-SAMPLE $line"
Add-Content -LiteralPath D:\agentABC\_impl\WORKLOG.md -Value "- BURST-SAMPLE $line"
$line
```

## 4. 熔断（自动执行，不请示）

| 条件 | 动作 |
|---|---|
| 宿主 CPU 连续 3 次采样 >90% | 降到 6 核；再连续 3 次越线 → 回 4 核 + 暂停入库 |
| 可用内存 <4 GB | 同上（先降 6 核，仍不足回 4 核并暂停） |
| C 盘可用 <15 GB 或 D 盘可用 <20 GB | 立即暂停入库；先核对日志/临时文件增长项再决定 |
| 12 核试探期间宿主 CPU >70% | 立即退回 8 核 |

每次触发写一行：`FUSE: 原因 / 动作 / 当时数值`（CPU%、内存GB、C/D 盘GB）。

降档步骤：

```powershell
# 6 核
$env:EMBEDDING_CPUS='6'; $env:RAYON_NUM_THREADS='6'
docker compose up -d --force-recreate embedding
# 回 4 核 + 恢复限速 1.0（并暂停入库）
powershell -File scripts/burst.ps1 off
```

## 5. 回滚 / 恢复校验（off 之后）

1. `curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:8080/readyz` → `200`
2. `docker compose exec -T platform python -m platform_core.cli smoke-embed --config /data/platform.yaml` → `8/8`
3. 三项实际值：`NanoCpus=4000000000`、`RAYON_NUM_THREADS=3`、`rate=1.0`
4. 中断续跑：见 2.3；checkpoint 在 `platform.document.manifest->'embedCheckpoint'`，`lastOrdinal/embedded` 可直接查；`embedded` 低于 `parsed` 时重复 POST `/index` 即可续跑（按 `chunk_embedding` 去重）。
5. 向量分区若被 smoke 污染：`platform_core.cli reindex --activate-only --provider local-bge`。

## 6. 禁止项

- ❌ `docker compose down -v` / `docker system prune` / 删数据
- ❌ 修改 chunk 尺寸（分块参数）
- ❌ 开量化（embedding 模型）
- ❌ `max_chunks_per_sec=0` 后忘记还原（off 必须回到 1.0）
- ❌ burst 期间重建镜像或改代码（等本批跑完）
