# 运行手册（platform）

面向"另一台机器 clone 后能跑起来"。所有命令以仓库根为工作目录，compose 文件为
`platform/docker-compose.yml`；也可 `cd platform` 后省略 `-f`。

## 1. 前置条件

- Docker Desktop（WSL2 后端）。实测 VM 上限：**12 CPU / 11.68 GiB**；16 CPU 会被 Docker Desktop 直接拒绝。
- 宿主建议 16 GB 内存、D 盘可用 ≥ 20 GB（`/readyz` 会因 `min_free_pct=10` 失败）。
- 端口占用（全部绑 `127.0.0.1`）：
  - `8080` 平台 API/UI，`8081` embedding（TEI），`5432` PostgreSQL，`7879` reasoner
  - `7878` Oxigraph **不映射宿主**（无鉴权，暴露即可绕过 GSP 治理）
- 模型与镜像：`agent-platform:0.1-s5`、`agent-reasoner:0.1-s5`、`agent-rdfs:0.1-s5`、pgvector、oxigraph、TEI 均由本地构建或拉取。

## 2. 目录准备

```powershell
cd platform
Copy-Item .env.example .env                # 填 POSTGRES_PASSWORD、ARK_API_KEY
Copy-Item platform.example.yaml data\platform.yaml   # 填 database.url 中的口令（须与 .env 一致）
New-Item -ItemType Directory -Force data\blobs, data\tmp, data\shapes | Out-Null
```

- `data/models/bge-m3/`：BGE-M3 模型约 **2.14 GB**（含 `pytorch_model.bin` 2.17 GB），目录固定，只读挂载给 TEI。
  离线拷贝：`robocopy <源>\models data\models /E`。不放入时 embedding 容器无法启动，检索退化为仅词法（响应标注 `lexicalOnly`）。
- `reasoner/robot.jar`（93 MB）不在仓库内，构建 reasoner 前必须放置，见 `reasoner/README.md`。
- `data/` 全部内容被 `.gitignore` 忽略，只保留 `data/README.md`。

## 3. 启动顺序

```powershell
docker compose -f platform/docker-compose.yml build      # 首次构建；无 robot.jar 时 reasoner 会失败
docker compose -f platform/docker-compose.yml up -d
docker compose -f platform/docker-compose.yml ps
```

迁移在平台启动时自动执行，脚本位于 `src/platform_core/sql/V1__s0.sql … V17__import_batch_stale.sql`，
**当前最新为 V17**（历史任务描述里的 V16 已过时）。

期望返回：

```powershell
curl.exe -s http://127.0.0.1:8080/readyz
# {"ok":true,"checks":{"database":{"status":"ok"},"graph":{"status":"ok"},
#  "storage":{"status":"ok","disk_free_pct":...},"embedding":{...},"reasoner":{...}}}
# 任一 status=fail 时 HTTP 非 200，detail 指明原因

curl.exe -s http://127.0.0.1:8080/status
# 关键字段：disk{free_pct,free_bytes,total_bytes}、counts{blobs,refs}、
#          ontology{pointer,versions,statuses}、triples
```

UI：浏览器打开 `http://127.0.0.1:8080/`（原生 HTML，无需前端构建链）。

## 4. 验收入口

| 命令 | 期望 |
| --- | --- |
| `docker compose exec -T platform platform smoke-s1` | 逐项 `[PASS]`，退出码 0 |
| `docker compose exec -T platform platform smoke-embed` | 8/8 `[PASS]`（含 `E_EMBED_MODEL_MISMATCH` 守卫断言） |
| `powershell -File platform/tests/acceptance.ps1` | 逐项输出 `[PASS] name detail` / `[FAIL] name detail`，末尾统计；**退出码 0 = 全部通过**，非 0 = 有失败项 |

`acceptance.ps1` 覆盖 `docker compose config`、各 smoke-sN、演示库纯净性等；单项失败不中断，最后汇总。
所有 smoke 写入独立命名图并在结束时清理，不污染演示库。

## 5. 并发与资源

- 重型锁：`scripts/compose-guard.ps1` 管理 `.lock/`，长操作必须
  `compose-guard acquire -Purpose <描述> -TtlMinutes 30 -Owner <owner>` →
  每 ≤5 分钟 heartbeat → 结束 `compose-guard release`。
  `status` 查看当前持有者；`-Force` 仅用于确认遗留死锁后强制接管。
- `up.ps1` 通过锁检查；`-AssumeLock -Owner <owner>` 仅在 owner 与当前锁一致时跳过检查。
- embedding 档位（`scripts/burst.ps1`）：
  - `burst.ps1 on`：cpus 4→8、`RAYON_NUM_THREADS` 3→8、`max_chunks_per_sec` 1.0→0（不限速）
  - `burst.ps1 off`：恢复 4 核 / RAYON 3 / rate 1.0，并跑 `smoke-embed` 8/8 + `/readyz`
  - `-Cpus/-Rayon` 用于阶梯测试；实测 12 核对 8 核提升仅 6.5%（<15% 阈值，故退回 8 核），16 核被 Docker Desktop 拒绝
  - 切档后必须 `readyz` + `smoke-embed` 全过才可批量作业
- 批量入库：`scripts/bulk-index.ps1` 分段可续跑；限速默认 `max_chunks_per_sec=1.0`（约实测上限 2.19 chunk/s 的 60%）。

## 6. 常见故障

| 现象 | 原因与处置 |
| --- | --- |
| `E_DB_MIGRATION_MISMATCH` | 库里 `schema_version` 与代码期望不一致（多为旧数据卷）。比对 `platform.schema_version` 最大值与 `sql/` 最新 Vxx；必要时重建数据卷（会丢数据） |
| `E_EMBED_MODEL_MISMATCH` | 查询/写入的向量模型与分区指针不一致。检查 `embedding.active_model` 与 `dim`，不要混用模型向量；切回旧模型需 `platform reindex --provider` |
| embedding 容器反复重启，日志含 `queue.rs` `Full(..)` panic | `MAX_CONCURRENT_REQUESTS` 过低（=1 必崩）。compose 默认 4，回退不要低于 4 |
| PowerShell 报 `MissingSwitchStatementClause` / 脚本乱码 | `.ps1` 必须以 **UTF-8 BOM** 保存（Windows PowerShell 5.1 按 ANSI 读取无 BOM 文件） |
| `/readyz` 中 `storage.status=fail` | `data/blobs` 目录缺失或磁盘可用低于 10% |
| reasoner 相关接口 `E_REASONER_UNAVAILABLE` | reasoner 容器未起（缺 `robot.jar` 或 profile 未开）；平台其余功能不受影响 |

## 7. 已知限制

- 扫描件（图片型 PDF）需显式开启 OCR（`ocr.enabled=true`，镜像内置 tesseract 中英文）。
- `.ppt` / `.doc` 旧格式需先转换为 `.pptx` / `.docx` 才能解析。
- 加密 PDF 不可解析，入库时会标记失败计数。
- 平台面 GSP（Graph Store Protocol）**只读返回 405、写入返回 403 `E_GSP_GOVERNANCE_REQUIRED`**；
  后端 Oxigraph 仅容器内网访问，调试需 `docker compose exec platform ...`。
- 外部 embedding（如火山方舟）为实验性适配器，默认不装配；默认仅本机 BGE-M3。
