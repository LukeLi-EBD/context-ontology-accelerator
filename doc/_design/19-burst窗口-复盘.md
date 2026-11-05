# 19-burst 窗口 · 复盘（S14H-BURST）

> 状态：进行中（本模板随窗口运行实时填；结论在窗口结束后补全）。

## 结论

1. **1.54s/chunk 花在哪**：99.9% 是 TEI 推理本身，不是平台。8 核实测短块 `482ms/chunk`（TEI 99.36% / 排队 0% / 平台 0.64%），长块 `3763ms/chunk`（TEI 99.92%）；平台侧（prep+upsert+checkpoint）仅 3.1ms/chunk。real-12/real-11 的 1.5–1.7s/chunk 是短块与长块混合后的加权值。
2. **加核有没有线性收益**：没有。8 → 12 仅 +6.5%（0.613 → 0.653 chunk/s，低于 15% 门槛）；embedding 容器在 8 核与 12 核下都只吃约 650% CPU，单飞（`BoundedSemaphore(1)`）+ 逐请求批处理决定了 TEI 的并联度，加核吃不到。16 核无法执行：Docker Desktop VM 只有 12 CPU（`docker` 报 `range of CPUs is from 0.01 to 12.00`）。
3. **最终档位**：**8 核**（`NanoCpus=8000000000`, `RAYON=8`, `rate=0`），`restarts=0`，宿主 CPU 峰值 41%、可用内存 10.7 GB。基数与外推见下节（早期“28 万”已复核为 ≈1.1 万）。

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

## 基数复核与 ETA（2026-11-05 16:35，替换早期“28 万”估算）

- **“28 万 chunk”是早期规划假设，无语料依据**（首次出现在 `_design/外部算力-BGE-M3-可行性.md` 的公开报价折算，后被本文沿用）；本段已按磁盘语料复核并**废弃**。
- 语料盘点（`D:\FS-LDM` + `_impl/data/{bench-real,bench-real-hold,corpus-s13,corpus-s13-clean}`，按 sha256 去重）：**443 个文件 / 488.6MB**；可解析（pdf/docx/txt/md；`.doc`/`.ppt` 无解析器，不计）**427 篇**，已 ingest **6 篇**（real-11/12/18/22 + 2 个 corpus txt），剩余 **421 篇**。
- 抽样实测（20 篇：10 bench-real PDF + 4 FS-LDM PDF + 3 md + 2 txt + 1 生成 PDF；17 篇成功、3 篇加密）：**1,920 chunk / 1.55M 字符 / 285.96MB**，平均 **96 chunk/篇**、**1.24 chunk/千字符**；长块 1,415 / 短块 505（**73.7% 长块**）。
- 关键事实：bench-real 的大 PDF 多为**扫描件**——real-01（92MB/838 页）、real-08（19MB/194 页）、real-13（10MB）文本层为 0 → 0 chunk（OCR 未启用）；有文本的 PDF 仅 **1.8–3.3 chunk/MB**。因此**不能**用 real-11（158 chunk/MB，文本密集）外推。
- 分层外推剩余 421 篇：bench-real 17 篇 ≈ **750–950**；FS-LDM 25 篇 ≈ **4,200**（md 3.76MB × 1.0 chunk/千字 ≈3,950，PDF ≈250）；corpus-s13 254 篇 + clean 124 篇 ≈ **1,730**（生成 PDF ≈3 chunk/篇）。**剩余 ≈6,900 chunk，全语料 ≈1.0–1.2 万 chunk**。
- 结论：**“28 万”高估约 25 倍**，可信新基数 **≈1.1 万 chunk（区间 0.9–1.3 万）**。

### 纠错过程（保留证据链）
1. **原始出处**：`外部算力-BGE-M3-可行性.md` 把“28 万 chunk × 单位耗时”折成算力报价，本复盘直接沿用并规划 130h（5.4 天）；该数没有任何磁盘盘点或抽样支撑。
2. **第一步反证（总量）**：按 sha256 盘点全部候选语料 = 443 文件 / 488.6MB / 可解析 427 篇。即使每篇 100 块也只有 4.3 万，**28 万在总量上就不成立**。
3. **第二步实测（抽样）**：20 篇按现策略实切 = 1,920 chunk（96 chunk/篇、1.24 chunk/千字符）；长块 73.7%。
4. **第三步修正假设**：375 个 PDF 逐篇检查文本层——**360 篇有文本（2,587 页 / 222.9MB / 3,340 chunk）**；**8 篇 0 文本（1,220 页 / 217MB / 0 chunk）**；7 篇失败（5 加密 + 2 损坏/加密）。此前“大 PDF 必文本密集、按 158 chunk/MB 外推”的假设被推翻（real-01 92MB/838 页实际 0 chunk）。
5. **第四步分层外推**：剩余 421 篇 ≈ 6,900 chunk；已入库语料 ≈3,300 → **全语料 ≈1.0–1.2 万**。
6. **结论落地**：基数 28 万 → **1.1 万**；ETA 5.4 天 → **3–6.4 小时**（已并入下表）。

| 阶段 | chunk 数 | 速率口径 | ETA |
|---|---|---|---|
| 当前队列（real-22 尾 + s3 4 条） | 569 | real-22 实测 ≈0.76 chunk/s | ≈16:40（已跑完） |
| 全语料剩余（421 篇 ingest + index） | ≈6,900 | 0.598–0.647（实测定档） | **3.0–3.2h**；按 73.7% 长块保守 **6.4h** |
| 扫描件缺口（待决策） | 8 篇 / 1,220 页 / 217MB | OCR 未启用，现为 0 chunk | 本地 Tesseract/PaddleOCR 估算 **3–15min（8 核）**；云端 **¥6–24** |
| 全语料总计（从零） | ≈1.0–1.2 万 | 同上 | 4.7–5.1h（长块保守 9–11h） |

- 扫描件判定依据（8/8 一致）：每页 `get_text_range()` 字符数 = 0；页面渲染墨迹比 0.035–0.999（非空白）；多数页含 1 个 image 对象（type=3），real-04 每页 24 个；real-17 无 image 对象但墨迹 0.17（矢量/嵌套对象）→ 均为**无文本层**，非解析失败。已给 8 篇写 `metadata.noTextLayer=true`（`noTextLayerPages` 一并写入）。
- 长/短块占比：当前库 4,756 chunk 中长块 **3,008（63.2%）**、短块 1,748（36.8%）；新抽样语料长块 **73.7%** → 后续更偏长块，ETA 取区间上限更稳。
- 早期“130h（约 5.4 天）”随之作废（它=28 万 × real-11 混合口径）；换成 1.1 万同口径约 **4.7h**。

## 下一步建议

- 保持 8 核 + `rate=0` 跑全量；若需再提速，方向是 TEI 侧（提高 TEI 内部批/并发或用 GPU），不是加核。
- 尽快给 `smoke-s4`/`smoke-s5` 也补上同样的“独立命名空间 + 指针断言”，避免非 `smoke-embed` 套件再次污染。

## 证据链接

- `logs\s14hbr-real11.json`（real-11 结果）
- `logs\s14h17-build*.log`、`logs\s14h17-up*.log`
- `_design/a_progress.md` 的 `BURST-SAMPLE` 行
- `_impl/WORKLOG.md` 的 `BURST-SAMPLE` 行
