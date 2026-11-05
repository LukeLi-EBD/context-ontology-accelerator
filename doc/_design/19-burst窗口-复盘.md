# 19-burst 窗口 · 复盘（S14H-BURST）

> 状态：进行中（本模板随窗口运行实时填；结论在窗口结束后补全）。

## 结论

1. **1.54s/chunk 花在哪**：99.9% 是 TEI 推理本身，不是平台。8 核实测短块 `482ms/chunk`（TEI 99.36% / 排队 0% / 平台 0.64%），长块 `3763ms/chunk`（TEI 99.92%）；平台侧（prep+upsert+checkpoint）仅 3.1ms/chunk。real-12/real-11 的 1.5–1.7s/chunk 是短块与长块混合后的加权值。
2. **加核有没有线性收益**：没有。8 → 12 仅 +6.5%（0.613 → 0.653 chunk/s，低于 15% 门槛）；embedding 容器在 8 核与 12 核下都只吃约 650% CPU，单飞（`BoundedSemaphore(1)`）+ 逐请求批处理决定了 TEI 的并联度，加核吃不到。16 核无法执行：Docker Desktop VM 只有 12 CPU（`docker` 报 `range of CPUs is from 0.01 to 12.00`）。
3. **最终档位**：**8 核**（`NanoCpus=8000000000`, `RAYON=8`, `rate=0`），`restarts=0`，宿主 CPU 峰值 41%、可用内存 10.7 GB。28 万 chunk 估算见下节，口径为“实测单位耗时 × 外推总量”。

## 窗口时长（待填）

- 开始：2026-11-05 15:00（立即执行版，无固定结束）
- 结束：待填（手动停止或全量完成）
- 总时长：待填

## 实际处理量

| 文档 | chunks | embedded | remaining | degraded | 墙钟 | chunk/s |
|---|---|---|---|---|---|---|
| real-12.docx | 438 | 438 | 0 | false | 213.3s（补跑 138 条） | 0.65（本次增量） |
| real-11.pdf | 1844 | 1844 | 0 | false（索引层） | 3084.7s | 0.60 |
| 全量（剩余） | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |

> real-11 入库阶段 `status=degraded` 的唯一原因：`PARTIAL_NO_TEXT_PAGES`（第 156/270/824/932/952 页无文本层），属解析告警；索引结果 `degraded=false`、`remaining=0`、`contentHashDuplicates=0`。

## 平均 / 峰值吞吐

- 8 核（`NanoCpus=8000000000`, `RAYON=8`, `rate=0`）：
  - 实测 real-12 增量：138 条 / 213.3s = **0.65 chunk/s**
  - 实测 real-11：1844 条 / 3084.7s = **0.60 chunk/s**
  - 实测 `bench-embed`（20 短 + 10 长）：30 条 / 48.9s = **0.613 chunk/s**
- 阶梯测试（20 短 + 10 长同一批样本）：

| 档位 | chunk/s | vs 前档 | 宿主 CPU 峰值 | 可用内存 | `NanoCpus` | restarts |
|---|---|---|---|---|---|---|
| 8 | 0.613 | 基线 | 41% | 10.7 GB | 8000000000 | 0 |
| 12 | 0.653 | +6.5% | 37% | 10.7 GB | 12000000000 | 0 |
| 16 | 不可执行 | — | — | — | — | Docker VM 仅 12 CPU |

- 判据执行：12 核提升 6.5% < 15% → **退回 8 核**；16 核因 Docker VM 上限无法测试（未触发 80% CPU 熔断）。
- 每档切完均 `/readyz`=200 + `smoke-embed 12/12`。

## 时间拆解（20 短 + 10 长，`bench-embed`）

| 档位 | TEI service ms | queue wait ms | platform ms | 三段占比 | chunk/s |
|---|---|---|---|---|---|
| 8（最终）短块 | 482.2 | 0.001 | 3.1 | 99.36% / 0.00% / 0.64% | 0.613 |
| 8（最终）长块 | 3763.3 | 0.002 | 3.1 | 99.92% / 0.00% / 0.08% | 0.613 |
| 12 短块 | 501.9 | 0.001 | 1.8 | 99.64% / 0.00% / 0.36% | 0.653 |
| 12 长块 | 3489.7 | 0.002 | 1.8 | 99.95% / 0.00% / 0.05% | 0.653 |
| 16 | 不可执行（Docker VM 12 CPU 上限） | — | — | — | — |

> 口径：`tei_service_ms` = 调 TEI `/v1/embeddings` 的实际耗时；`queue_wait_ms` = 平台单飞信号量等待；`platform_ms` = prep（分块查询/重复审计）+ pgvector upsert + checkpoint 提交，按 chunk 均摊。中位数取自 `bench-embed` 的批次样本。

## 峰值资源

- 宿主 CPU 峰值 41%（8 核/12 核 bench 期间均未超过 41%）；可用内存最低 10.7 GB；embedding 容器 CPU 峰值 6.67 核（666.72%）
- 已采样（15:02）：`438 | 438 | 0.65 | 5% | 10.9 GB | 33.9 GB | 103 GB | 0.69%`
- 8 核 bench 采样（3s 间隔）：宿主 29–41%，embedding 613–667%
- 12 核 bench 采样：宿主 27–37%，embedding 613–658%（与 8 核同量级，是加核无收益的直接证据）

## 熔断记录

- 无 / `FUSE: 原因 / 动作 / 当时数值`（逐条）

## 失败清单与原因

- real-12 首次调用：`E_EMBED_MODEL_MISMATCH`（向量分区指针被 smoke 留在 `fake-hash-1024`）→ `reindex --activate-only --provider local-bge` 后恢复。
- real-11 入库：`PARTIAL_NO_TEXT_PAGES`（第 156/270/824/932/952 页无文本层，解析告警，索引不受影响）。
- 16 核试探：`docker` 拒绝 `--cpus 16`（Docker Desktop VM 仅 12 CPU），判为环境上限、不可执行。

## 断点可用性

- checkpoint 位置：`platform.document.manifest->'embedCheckpoint'`（`model/lastOrdinal/embedded`）
- 实测：kill 后 `embedded=50,lastOrdinal=49`，续跑 `204/204`、重复 0；暂停 `max_batches=1` 后 `paused=true,degraded=false`
- 待填：全量期间实际中断次数与恢复耗时

## 与 1 chunk/s 基线的对比

- 基线：限速 `max_chunks_per_sec=1.0`，实测约 1 chunk/s
- 8 核实测（real-12 增量）：0.65 chunk/s —— 低于基线，因为 TEI 单飞下短块合批受限、长块单发；`bench-embed` 证明 99.9% 时间在 TEI 推理，平台侧仅 3.1ms/chunk
- 12 核：0.653 chunk/s（+6.5%，不足 15%）→ 最终留在 8 核；`rate=0` 已放开限速

## 28 万 chunk 估算（实测口径）

- **实测部分**：8 核短块 0.485s/chunk、长块 3.766s/chunk（`bench-embed` 中位数）；real-11 混合 1.673s/chunk、real-12 混合 1.546s/chunk
- **外推部分**（单位耗时 × 28 万，未含解析/入库阶段）：

| 口径 | 单 chunk | 28 万 chunk | 说明 |
|---|---|---|---|
| 短块为主 | 0.485s | ≈37.7h | 实测短块耗时外推 |
| real-12 混合 | 1.546s | ≈120.2h | 实测混合均值外推 |
| real-11 混合 | 1.673s | ≈130.1h | 实测混合均值外推（PDF 长块多） |
| 长块为主 | 3.766s | ≈292.9h | 实测长块耗时外推 |

- 推荐按 **real-11 混合口径 130h（约 5.4 天）** 规划；区间 38h–293h。

## 下一步建议

- 保持 8 核 + `rate=0` 跑全量；若需再提速，方向是 TEI 侧（提高 TEI 内部批/并发或用 GPU），不是加核。
- 尽快给 `smoke-s4`/`smoke-s5` 也补上同样的“独立命名空间 + 指针断言”，避免非 `smoke-embed` 套件再次污染。

## 证据链接

- `logs\s14hbr-real11.json`（real-11 结果）
- `logs\s14h17-build*.log`、`logs\s14h17-up*.log`
- `_design/a_progress.md` 的 `BURST-SAMPLE` 行
- `_impl/WORKLOG.md` 的 `BURST-SAMPLE` 行
