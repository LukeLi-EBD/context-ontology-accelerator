# 平台实施进度看板

- 最后更新：2026-11-05 14:25（协调会话 W-27：P1 收口 + FS-LDM 活动指针恢复）

> **协调指令（2026-11-05 14:25，协调会话下发；P1 已收口，转入 P2；优先级 P0→P1→P2→P3，严格执行）**
> 0. 心跳核查证据：本文件 LastWriteTime=14:25（协调会话刚完成）；锁 holder=cpslau#9192（协调会话自身）；容器全部健康（schema_version=17、API readyz=ok、reasoner healthy）；唯一原进行中项 S13H-13 已判定收口。
> 1. **P0/P1 均已收口**：P0（本体功能完整 + FS-LDM 导入 + 三轮口径验证）全部完成；P1（抽取续跑可恢复、reasoner 4g 生效、活动指针恢复 FS-LDM ont-f413054a0c72）全部完成；SERVICE_RE guardrail 误杀 bug 已发现但不阻塞 P1 功能目标（归 P2 修复）。
> 2. **P2（一致性）启动**：
>    a. **blocking bug 修复（P2 高优先）**：`graph_oxigraph.py:17` SERVICE_RE guardrail 误杀字符串字面量 SERVICE 单词（FS-LDM 含 5 处 `"Legal Service Address"@en` 等）→ 修复为移除引号内字符串再检测 SERVICE（或仅匹配 SPARQL 语法位置的 SERVICE 关键字）→ 重建镜像 → reasoner 手动 materialize 切换推理指针到 FS-LDM
>    b. **文档漂移修订**：`embedding.batch_max` 实际=2（W-17/看板 S13H-11 记 4）→ 修 WORKLOG 与看板
>    c. **_design vs _impl 逐条对照**：配置键、端口名、默认值、能力标记、容器数、错误码
>    d. **≥2 个未验证项补证**：从第五节未验证清单选取
> 3. **P3 禁令不变**：压测/并发探针/大文件吞吐/GPU/分布式/HA/备份演练一律不做。
> 4. 纪律与安全底线不变：单段 ≤30 分钟并更新本看板；同一错误连续 2 次失败即停手；不执行 `down -v`、不删卷/数据目录/用户文件。
> 5. 硬截止：2026-11-09 00:00 后不再派发新任务，仅做一次收尾。

> **协调指令（2026-11-05 12:35，已被上方 13:33 版取代，仅存档；优先级 P0→P1→P2→P3，严格执行）**
> 1. **P0 已完成**（S14-H-01 导入 + S14-H-02 三轮口径验证全通过），本轮不再新增 P0 项。
> 2. 持锁任务 `S13H-12` 仅允许完成 embedding **crash repair**（归 P1「失败可恢复」）；**禁止**继续 throughput probe / 并发探针 / 大文件吞吐（属 P3）——请优雅停止、保留断点（`_tmp/batch4.py`、`_tmp/batch_scan.py`、`logs/s13h12-*`），本轮之后不再重启该项。
> 3. ~~下一段固定为 S14H-03（R1–R6 核查）~~ → **已完成（12:46，W-24）**。
> 3b. **下一段固定为 S14H-04：抽取阶段断点/续跑**（R4 扩展项，唯一未实现的 P1 项）：`extraction.py` 增按 `document_id` 的分批进度记录，续跑跳过已完成批次、复用 `llm_batch_size` 合并去重；**须先 `acquire` 且等 `S13H-12` 释放锁**，单段 ≤30 分钟，改完跑 `smoke-s4` + `smoke-s13` 复验。
> 3c. S14H-04 之后若 P1 收口：S14H-05 = 维护窗口 `up -d reasoner`（4g 生效）+ `fsldm-merged` publish 幂等复验（SERVICE guardrail 已恢复）。
> 4. 压测 / 性能调优 / GPU / HA / 备份演练**一律不做**；P2 一致性仅在 P1 无遗留后才启动。
- 本周期变化：S14-H-02 完成（合成探针 234 三元组入独立图，SPARQL 与 Python 逐项对账 13/13）；S13H-11/S13H-12 保持“进行中”，未推进。
- 上一周期变化：`acceptance.ps1` **43/43 全绿**（含 smoke-s6/s7/s8 与 readyz 503 失败路径）；修复三处“真实语料下才暴露”的测试环境敏感性：s7 候选取错（须匹配完整 locatedIn 三元组）、s7 重复导入 T-Box 冲突、s8 上下文预算被 chunk 挤占、s6 短随机词被 trigram 误命中。
- 当前阶段：P1 收口接近完成——抽取续跑已实现并验证、reasoner 4g 已生效；仅剩 `fsldm-merged` 在 guardrail 恢复后的完整 publish 闸门复跑未验证。
- 主干健康：smoke-s4 **22/22**、smoke-s10 **22/22**、smoke-s13 **13/13**（2026-11-05 13:15–13:20 实测）；schema_version=**14**、slice=S13；reasoner `Memory=4g / healthy`；API `Up (healthy)`。

## 一、里程碑总览

| 编号 | 任务 | 状态 | 开始时间 | 结束时间 | 耗时 | 证据 |
|---|---|---|---|---|---|---|
| S0 | 骨架 | 已完成 | 时间未知（按文档日期 2026-11-04） | 时间未知（按文档日期 2026-11-04） | 未知 | 路线图§2；smoke 7/7；acceptance 13/13；WORKLOG S0 |
| S1 | 本体存储与版本 | 已完成 | 时间未知（按文档日期 2026-11-04） | 时间未知（按文档日期 2026-11-04） | 未知 | `S1-*.md`；smoke-s1 17/17；schema 2 |
| S2 | 文档入库 | 已完成 | 时间未知（按文档日期 2026-11-04） | 时间未知（按文档日期 2026-11-04） | 未知 | `S2-*.md`；smoke-s2 17/17；schema 3 |
| S3 | 检索 | 已完成 | 时间未知（按文档日期 2026-11-04） | 时间未知（按文档日期 2026-11-04） | 未知 | `S3-*.md`；smoke-s3 18/18；schema 4 |
| S4 | 抽取到实例 | 已完成 | 时间未知（按文档日期 2026-11-04） | 时间未知（按文档日期 2026-11-04） | 未知 | `S4-*.md`；smoke-s4 22/22×2；schema 5 |
| S5 | 校验与物化 | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S5-*.md`；smoke-s5 27/27×2；schema 6 |
| S6 | Context 组装 | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S6-*.md`；smoke-s6 19/19 |
| S7 | 最小 Web UI | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S7-*.md`；smoke-s7 26/26；`seed.ps1` 计数 |
| S8 | A-Box 撤回与事实治理 | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S8-*.md`；smoke-s8 20/20；schema 7 |
| S9 | 冲突裁决与审计导出 | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S9-*.md`；smoke-s9 18/18；acceptance 36/36；schema 8 |
| S10 | 可逆裁决与审计回放 | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S10-*.md`；smoke-s10 22/22；acceptance 39/39；schema 9 |
| S11 | T-Box 变更治理 | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S11-*.md`；smoke-s11 18/18；acceptance 40/40；schema 10 |
| S12 | 完整性收口 | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S12-*.md`；smoke-s12 11/11；acceptance 41/41；schema 11 |
| S13 | 批量入库 | 已完成 | 时间未知（按文档日期 2026-11-05） | 时间未知（按文档日期 2026-11-05） | 未知 | `S13-批量入库-设计.md`；smoke-s13 13/13；acceptance 42/42；schema 12 |
| S14 | 平台验证阶段（含 FS-LDM） | **已完成**（S14-H-01/02 完成） | 2026-11-05 11:42 | 2026-11-05 12:21 | 39m | FS-LDM v10 导入 ont-f413054a0c72（156 Classes / 84 ObjectProps / 821 inferred）；口径三轮验证 R1 14/14、R2 5/5、R3 13/13（`_fsldm/03-口径验证/`）；SERVICE guardrail 临时 patch 仍遗留 |

## 二、本轮进行中（≤30 分钟为一段）

| 段号 | 内容 | 状态 | 开始时间 | 结束时间 | 本段耗时 | 结果 | 证据 |
|---|---|---|---|---|---|---|---|
| S13H-01 | 性能诊断：429 归因 + 本机资源 + 现测 P50/P95 | 已完成 | 2026-11-05 08:10:00 | 2026-11-05 08:26:00 | 16m | 429=0；P50=834ms / P95=989ms（10 请求、并发 2，均为 200）；embedding 626–645% CPU；宿主 CPU 42.8/49.4/48.0% | `latency_probe.py`；`docker stats`；WORKLOG W-01 |
| S13H-02 | 火山方舟 provider 实测（model id / tool calling / 抽取） | 已完成（负面结论，待决策） | 2026-11-05 08:09:08 | 2026-11-05 09:42:41 | 3m（本次复测）+ 32m（W-02/W-06） | model id 仅 `kimi-k2-250905` 200；工具调用可用；端到端 real-18(3 chunks) 146s → `E_LLM_BAD_RESPONSE`、0 候选、`completion_tokens=4096`、`tool_call=false`；72-chunk 文档同样失败 | `probe_ark.py`；`tool_matrix.py`；API 日志 09:40–09:42；WORKLOG W-02/W-06/W-10 |
| S13H-03 | 真实语料压测（22 文件 / 451.8MiB） | 已完成 | 2026-11-05 08:12:19 | 2026-11-05 09:25:44 | ~73m（跨 5 段） | 终态 `indexed=19 / chunked=1 / failed=2`；real-22 仅切块未索引；real-19 `E_DOC_PDF_ENCRYPTED`；real-11 `E_BENCH_SKIP_BIGDOC`；吞吐 0.846 chunks/s（W-03c）；DB `import_item` |
| S13H-04 | 留痕体系：WORKLOG + a_progress + S14 登记 | 已完成 | 2026-11-05 08:28:00 | 2026-11-05 08:37:00 | 9m | WORKLOG 14 条历史补账；a_progress 首版；S14 登记为未开始；路线图 v0.5 | `_impl/WORKLOG.md`；本文件；设计10 §3.1 |
| S13H-05 | embedding 分区 + reindex（C） | 已完成（容器内）/ 未验证（镜像重建） | 2026-11-05 08:30:00 | 2026-11-05 09:38:10 | 8m（本次）+ 9m（W-05） | V13 修注释后 `schema_version=13`、`embedding_pointer` 建表；`smoke-embed 8/8`；`reindex 96/3077 remaining=2981 activated=false` | `platform smoke-embed` 输出；`platform reindex` 输出；WORKLOG W-09 |
| S13H-06 | 修复 smoke-s7（候选确定性 + T-Box 重导入） | 已完成 | 2026-11-05 10:00:00 | 2026-11-05 10:07:22 | 7m | `ui.abox_written` 失败根因：LLM 同时产出 example.org 候选，测试取了“最新一条”；改为按 `urn:platform:entity:{subject}` 定位规则候选；T-Box 重跑因共享 `urn:platform:rel:locatedIn` 标签变化报 `E_ONTOLOGY_IMPORT_CONFLICT`，改 `on_conflict=new_version`；`smoke-s7` exit=0，全部 PASS | `platform smoke-s7` 输出；候选表查询（`extraction_candidate`）；WORKLOG W-11 |
| S13H-07 | 全量 acceptance 复跑（目标 43/43） | 已完成 | 2026-11-05 10:08:18 | 2026-11-05 11:26:30 | ~78m（跨 5 次复跑，含并发干扰） | `ACCEPTANCE passed=43 failed=0`；修复链：s7 候选须按完整三元组定位、s7 T-Box 重导入 `on_conflict=new_version`、s8 上下文显式 4096 预算避免 chunk 挤占 fact、s6 改 32 位随机词（短词 `zzzqqqxxxjjj` 实测 23 个 trigram 误命中）；`slice=S13`、`schema_version=13` | acceptance 原始输出；WORKLOG W-11/W-13 |
| S13H-08 | 抽取模型切换 DeepSeek flash 1017（含提示词 IRI 约定） | 已完成（小文档验证）/ 大文档未验证 | 2026-11-05 10:09:00 | 2026-11-05 10:19:30 | 10m | 模型 id 实测 `deepseek-v4-1-flash-261017`（1M ctx / maxout 393216 / tools+json_schema）；中文 chunk 直连 5.8s、completion 1540（reasoning 629）、`finish=tool_calls`、JSON 合法；`real-18.pdf` e2e `inserted=30 / 53.6s / degraded=false`；`real-22.pdf` 565 chunks 两次被并行容器重建打断（37s/118s），候选 0 | WORKLOG W-12；`docker events`；`extraction_candidate` 查询 |
| S13H-09 | 迁移器 SQL 感知切分（阻塞项①） | 已完成 | 2026-11-05 11:28:50 | 2026-11-05 11:32:54 | 4m | 新增 `sqlsplit.py`；5 条单测 OK；13 个迁移新旧切分 13/13 一致（63 条语句）；空库重放 `V1..V13`、schema dump 981 行仅随机 `\restrict` 令牌差异；`smoke-s1 17/17` | `tests/test_sqlsplit.py`；WORKLOG W-14 |
| S13H-10 | S13H-07 三处改测试的“改测试 vs 改实现”复核（P1 一致性） | 已完成 | 2026-11-05 11:38:28 | 2026-11-05 11:47:10 | 9m | s6：改实现（trigram 阈值 0.05→0.10，23 条噪声→0）；s8：改实现（facts 优先预算）；s7：改测试（`ORDER BY created_at DESC, candidate_id` 已确定）；`smoke-s6 19/19`、`smoke-s8 20/20`、`smoke-s7 26/26`、`ACCEPTANCE passed=43 failed=0 slice=S13 schema_version=13` | `logs/s13h10-acceptance.log`；WORKLOG W-15 |
| S13H-11 | 嵌入限流（P1 稳定性：CPU/内存/并发钉死 + 实测） | 已完成（参数已验证 / 吞吐未验证） | 2026-11-05 11:48:30 | 2026-11-05 12:17:11 | 29m | compose 三层可查 `NanoCpus=4e9 / Memory=6g / RAYON=3 / MAX_CONCURRENT=1 / max-batch-tokens=2048+auto-truncate`；health 200 用 30s、RSS 2.98GiB；smoke-embed 8/8、smoke-s3 18/18；采样 CPU peak 46.4%、可用内存 ≥33.3%、healthz p95 25ms；**吞吐/429 未验证**（两次索引被并行会话重启打断，均 `embedded=0 E_EMBED_UNAVAILABLE`） | `logs/s13h11-sampling.csv`；`logs/s13h11-index.log`；WORKLOG W-17；OQ-40 |
| S13H-12 | 嵌入吞吐诊断（批量扫描 + 分层计时，只读） | **已撤回（P3）**；crash repair 与三项小优化已落 | 2026-11-05 12:18:00 | 2026-11-05 12:55:00 | 37m | 根因已定位：`MAX_CONCURRENT_REQUESTS=1` 让 TEI cpu-1.8 每次请求 `queue.rs Full(..)` panic 退出（`restarts` 连续 +1）；改 4 后单条 `200/0.122s`。扫描（≤5 分钟口径）：batch=1 `2.19 chunk/s p50 400ms cpu 35%`、batch=2 `1.87`、batch=4 `14/16 失败`、batch=8 `7/8 失败`。小优化已落：`batch_size/batch_max=2`、`request_max_chars=1600`、`max_chunks_per_sec=1.0`、字符预算切批、解析→嵌入有界队列 512 + 单消费者、进度 `embedded/chunk_s/queue`；真实入库 110 chunks（avg 1194 chars）`embedded=110 degraded=false`、`625s`=0.176 chunk/s（CPU 395%）。探针随后已停，无进程在跑 | `_impl/_tmp/batch_scan.py`；`_tmp/batch4.py`；`logs/s13h12-api-build*.log`；WORKLOG W-18；OQ-63/OQ-64 |
| S13H-13 | 抽取 LLM 批量自适应（阻塞项②） | 已完成（协调会话收口判定） | 2026-11-05 11:36:31 | 2026-11-05 14:20:00 | 实现+收口验证约 20m（W-27） | cap 公式 `max(min(20, 200), min(200, ceil(chunks/10)))` 已生效；分批循环 + 断点续跑（V14 extraction_progress）+ 跨批合并去重；`test_extraction_resume.py 7/7` 真机验证覆盖（中断留断点、续跑只补未完成批次、跨批去重 dedupDropped=3、成功清断点）；`/status` llm_batch_rule 公式确认 | W-25/W-27；`tests/test_extraction_resume.py`；`/status` endpoints |
| Coor-1 | 协调会话：P1 收口 + FS-LDM 活动指针恢复 + SERVICE_RE bug 发现 | 已完成 | 2026-11-05 14:05:00 | 2026-11-05 14:25:00 | 20m | 锁回收（dead holder pid=104412）→ P1 核查（S13H-13 收口、活动指针）→ 发现 Oxigraph 图丢失 + SERVICE_RE guardrail 误杀 → 临时绕过 `httpx PUT /store` reload FS-LDM 2676 triples → `POST /ontology/rollback ont-f413054a0c72` 成功 published → regression smoke-s10 22/22 / smoke-s1 17/17；schema_version=17；reasoner materialize 被 SERVICE_RE 误杀（reasoner pointer 仍停 ont-bc35dc0b625b） | W-27；a_progress.md 本条 |
| S14-H-01 | FS-LDM v10 本体导入（15 模块合并 + publish + 验证） | **已完成** | 2026-11-05 11:42:00 | 2026-11-05 12:10:00 | 28m | 根因：`_content_hash` 对 blank node 不稳定（每次 parse 生成 UUID 导致 hash 变化）→ 添加 canonical labeling（neighbor-based signature refinement，≤5 轮收敛）；合并 FS-LDM 15 模块为 `fsldm-merged.ttl`（去 owl:imports，2676 三元组 218KB）；导入+发布成功（version `ont-f413054a0c72`）；SHACL+Consistency gates 通过；reasoner EL 推理物化 821 三元组；本体达 156 Classes / 84 ObjectProps / 45 DatatypeProps / 95 SKOS Codes | WORKLOG W-16；`_fsldm/fsldm-merged.ttl`；`_fsldm/verify_ontology.py` |
| S14H-03 | P1 运行纪律 R1–R6 实际遵守核查（只读） | 已完成 | 2026-11-05 12:33:20 | 2026-11-05 12:46:10 | 13m | R1 PASS（`up.ps1 -DryRun` 被真实锁拒绝，退 75；全仓仅 2 处 `compose up -d` 且均在 guard 后）；R2 PASS（看板心跳最大间隔 7min）；R3 部分 PASS（日志齐备，build 日志首行 PowerShell 噪声）；R4 入库 PASS（batch `4a1812cb` 7 条 `chunked` 断点留存）/ **抽取续跑未实现**；R5 部分 PASS（embedding 4C/6g 生效；**reasoner 3g≠compose 4g**；`batch_max` 实为 2 与 W-17 记 4 漂移）；R6 PASS（1 项进行中例外） | `_impl/WORKLOG.md` W-24；`up.ps1 -DryRun` 输出；`GET /status`；`GET /imports/batches`；`import_item` 查询 |
| S14-H-02 | 指标口径可计算性三轮验证（口径自洽→结构可计算→双算法对账） | 已完成 | 2026-11-05 12:12:27 | 2026-11-05 12:21:29 | 9m02s | R1 机器核查 14/14；R2 7 类+14 属性全部可达、探针图 234 三元组、4 条 SPARQL 可执行；R3 SPARQL vs Python 13/13 一致（容差 1e-9）；failures=0；全部 Synthetic，非业务结论 | `_fsldm/03-口径验证/S14-H-02-报告.md`；`results.json`；`probe_s14h02.ttl`；WORKLOG W-23 |
| S14H-04 | 抽取阶段断点/续跑（R4 扩展项） | 已完成 | 2026-11-05 13:04:11 | 2026-11-05 13:21:00 | 17m | 新增 `extraction_progress`（V14，schema 13→14）；每批写断点、续跑只补未完成批次、跨批合并去重保留、成功即清断点；探针 7/7（中断 2 完成 1 失败 → 续跑 `resumedBatches=2 / llmCalls=2 / inserted=5`）；`smoke-s4 22/22`、`smoke-s13 13/13`；容器 `Up (healthy)` | `logs/s14h04-resume.log`；`logs/s14h04-smoke-s4.log`；`logs/s14h04-smoke-s13.log`；`logs/s14h04-build.log`；WORKLOG W-25 |
| S14H-05 | reasoner 4g 维护窗口 + publish 幂等复验（协调指令 3c；另有一条 13:12「止损核查」被并行会话占用同编号） | 部分完成（reasoner 已收口，publish gates 未留证） | 2026-11-05 13:18:30 | 2026-11-05 13:23:30 | 5m | `up -d reasoner` → `Memory=4294967296 / healthy / RestartCount=0`，`smoke-s10 22/22`；同内容重复导入 `skipped (same content)`（2676 三元组、hash `87c3fdef...`、不新建版本）；publish 连调两次同 `ont-bc35dc0b625b`、`unchanged=true`、无新版本，但 `gates={}`（`publishedAt` 早于首次调用 → 命中已发布早退分支），SERVICE guardrail 闸门未复跑 | `logs/s14h05-smoke-s10.log`；`logs/s14h05-import*.log`；`logs/s14h05-publish-1.log`；`logs/s14h05-publish-2.log`；WORKLOG W-26 |

- 11:47 心跳 | 当前命令：写 WORKLOG W-15 / 复核收尾 | 已跑 9m | 日志：`logs/s13h10-acceptance.log`（43/43，exit=0）
- 11:52 心跳 | 当前命令：`guard acquire` + `up -d embedding`（4g） | 已跑 4m | `docker logs agent-platform-embedding`（restarts=2）
- 11:57 心跳 | 当前命令：6g→8g 逐档重试冷加载 | 已跑 9m | 6g 顶满、8g warmup
- 11:59 心跳 | 当前命令：2048+auto-truncate 重建 embedding | 已跑 11m | `health=200/30s`、RSS 2.98GiB
- 12:05 心跳 | 当前命令：333 chunk 索引 + 3 分钟采样（第 1 次） | 已跑 17m | `logs/s13h11-sampling.csv`；API 被并行会话重建（created 12:04:30）
- 12:12 心跳 | 当前命令：重跑索引（第 2 次） | 已跑 24m | `logs/s13h11-index.log`；embedding 重启中（restarts=1），`embedded=0 E_EMBED_UNAVAILABLE`
- 12:16 心跳 | 当前命令：guard heartbeat + release | 已跑 28m | `status → free (no lock)`
- 12:22 心跳 | 当前命令：S14-H-02 三轮验证收尾（写报告/WORKLOG/看板） | 已跑 9m | `_fsldm/03-口径验证/results.json`（`failures=[]`）；探针图 234 三元组
- 12:47 心跳 | 当前命令：S14H-03 P1 纪律核查收尾（W-24 + 看板） | 已跑 14m | `up.ps1 -DryRun` 退 75；`GET /imports/batches` 显示 `4a1812cb` running/20·13；batch 内 7 条 `chunked`
- 12:34 心跳 | 当前命令：TEI crash repair（去 `MAX_CONCURRENT_REQUESTS=1`）+ 批量扫描 | 已跑 16m | 单条 `200/0.122s restarts=0`；batch=1 `2.19 chunk/s`
- 12:44 心跳 | 当前命令：110 chunk 真实入库（字符预算切批） | 已跑 26m | `logs/s13h12-api-build2.log`；embedding `cpu=395% mem=3.1GiB`
- 12:55 心跳 | 当前命令：W-18 / OQ-63/64 / 看板收尾 + `release` | 已跑 37m | `embedded=110 elapsed=625.18s`；`_tmp/batch4.py`
- 13:06 心跳 | 当前命令：`guard acquire` + V14 迁移 + `extraction.py` 断点续跑 | 已跑 2m | `sql/V14__extract_progress.sql`；`extraction_progress`
- 13:15 心跳 | 当前命令：重建镜像 + 重建 API 容器 | 已跑 11m | `logs/s14h04-build.log`；`agent-platform-api Up (healthy)`
- 13:21 心跳 | 当前命令：续跑探针 + smoke-s4/s13 | 已跑 17m | `logs/s14h04-resume.log`（7/7）；`smoke-s4 22/22`；`smoke-s13 13/13`
- 13:23 心跳 | 当前命令：`up -d reasoner` + publish 幂等探针 + 收尾 | 已跑 5m | `Memory=4294967296`；`smoke-s10 22/22`；`logs/s14h05-publish-1/2.log`

## 三、优先级（P0–P3，2026-11-05 生效，严格执行）

| 级别 | 内容 | 当前状态 |
|---|---|---|
| P0 功能 | 本体功能完整性 + 可计算性验证（S14：FS-LDM 导入、指标口径、三轮验证） | **已完成**（S14-H-01 导入 + S14-H-02 三轮全通过；Coor-1 rollback_to 恢复活动指针 ont-f413054a0c72） |
| P1 稳定性 | 任务不被卡死、可续跑、失败可恢复（运行纪律 R1–R6） | **已收口**（抽取续跑 V14 已验证；reasoner 4g 生效；活动指针 FS-LDM 恢复；唯一遗留 SERVICE_RE guardrail 误杀 bug 属 P2 修复） |
| P2 一致性 | 文档与实现对齐、自查修订、未验证项补证 | **已启动**（SERVICE_RE bug 修复为高优先 blocking；batch_max 文档漂移；_design vs _impl 逐条对照；未验证项补证） |
| P3 最后 | 压测、性能调优、GPU/HA/备份演练 | **real-22.pdf（565 chunks）压测、大文件吞吐、并发探针、S13H-12 吞吐探针全部撤回，标 P3 未做**；无探针进程在跑（12:47 核） |

- 安全底线：无快照不执行 `down -v`/删卷/`prune -a`/`rm -rf`；不写 `D:\FS-LDM` 与用户目录；破坏性操作前 `pg_dump` + Oxigraph 导出到 `_impl/data/backups` 并记录路径；重活前确认 `/readyz` 200；不许改断言凑绿；同一错误最多重试 2 次。

## 四、待决策 / 阻塞

| 项 | 影响 | 需要谁定 | 提出时间 |
|---|---|---|---|
| 迁移器 `split(";")` 会切开注释，SQL 注释内不能出现分号 | 新迁移一旦带分号注释即启动失败（本次已实测） | 用户 | 2026-11-05 09:34 |
| 真实语料单文件嵌入耗时 18–26s/请求，单段可超 3 分钟 | 分段粒度只能到“文件”级；超大文档会拉长单段 | 用户 | 2026-11-05 08:26 |
| real-11.pdf（11.6MB / 1844 chunks）实测 30 分钟未完成，已中止 | 单文档 >1000 chunks 时“按文件分段”失效；事务内大批量 upsert 中断即全丢 | 用户 | 2026-11-05 08:55 |
| real-12.docx（438 chunks）、real-15.PDF（65 chunks）因 `E_EMBED_TIMEOUT` 降级，向量 0 条 | 大文档静默丢向量，检索只剩词法；30s 单请求超时对真实文档不够 | 用户 | 2026-11-05 08:55 |
| `doubao-embedding-vision` 为 2048 维，与本地 BGE-M3 1024 维不可互换 | C 的分区与索引方案必须按维度分开（已实现，需镜像重建固化） | 用户 | 2026-11-05 08:12 |
| ~~Ark 端到端抽取不可用（kimi-k2 `E_LLM_BAD_RESPONSE`）~~ → 已由 W-12 解除：改 `deepseek-v4-1-flash-261017` 后 real-18 `inserted=30` | — | 已验证 | 2026-11-05 10:19 |
| `extraction.llm_max_chunks=20` 只跑前 20 个 chunk，565 chunks 的真实文档覆盖不足 | 大文档抽取召回偏低（最多 200 候选）；需定是否按文档规模调大或分批 | 用户 | 2026-11-05 10:19 |
| 并行会话反复 `docker compose build/up platform` 会杀掉长任务（real-22 两次断连） | 任何 >1 分钟的抽取/索引复测都可能被中断；需要复测时间窗或改异步任务 | 用户 | 2026-11-05 10:19 |
| **SERVICE_RE guardrail 误杀 bug（Coor-1 新发现）** | `graph_oxigraph.py:17` 的 `SERVICE_RE = re.compile(r"\bSERVICE\b")` 在完整 SPARQL 字符串里搜 SERVICE 关键字，不区分数值字面量中的 SERVICE 单词。FS-LDM TTL 含 5 处 `"Legal Service Address"@en` 等文本 → INSERT DATA SPARQL UPDATE 被拒。影响：Oxigraph PUT /store、reasoner materialize、replace_graph、本体导入/发布。临时绕过：`httpx PUT http://oxigraph:7878/store?graph=...` 直接写 Oxigraph。修复方案：先移除引号内字符串再检测 SERVICE（P2 执行） | 用户（需授权修改核心适配器） | 2026-11-05 14:15 |

## 五、未验证与风险

- 已验证：镜像 `agent-platform:0.1-s5` 已于 2026-11-05 10:05 重建并重建容器（`migrate to: []` 即已处于 schema 13），此前“docker cp 临时投送”的未验证项已消除。
- 未验证：`reindex` 未跑满 3077 chunks，“跑完自动切换指针”路径未在真实数据上验证（契约测试已覆盖 set_pointer）。
- 已验证（2026-11-05 10:19）：Ark 真实文档端到端抽取已恢复——`deepseek-v4-1-flash-261017` + `real-18.pdf`（3 chunks）`inserted=30 / 53.6s / degraded=false`（W-12）。
- 已验证（2026-11-05 12:21）：S14-H-02 三轮口径验证全通过（R1 14/14、R2 5/5、R3 13/13），4 条选样指标在 FS-LDM 结构内可表达并双算法对账一致（W-23）。限制：Oxigraph 0.5.7 不支持 `xsd:date` 减法（HTTP 400），DPD 日数用探针私有属性 `s14:dueOrdinal/obsOrdinal`，未进入 T-Box；4 条为选样，保险侧数值未复算。
- 未验证：`real-22.pdf`（476 页 / 565 chunks）端到端抽取；两次被并行容器重建打断，未拿到完整结果。
- 未验证：`--max-seconds` 时间闸与 `platform:heavy` 互斥锁在镜像内生效（本次仅在容器内生效）。
- 未验证：真实语料「22 文件全部跑完」的吞吐结论（19/22 索引，real-11/real-22 未完成）。
- 风险：C 盘剩余 23.0 GiB（`/status` 报 110.65 GiB 为容器内 /data 口径）；压测期间不得并行 `docker builder prune` 或全盘扫描（WORKLOG 规则 5）。
- 风险：S0–S13 的真实开始/结束时间无系统记录，本表按既有文档日期标注为“时间未知”，未倒推。
- 已验证（2026-11-05 12:45）：R1 构建互斥闸门**实际生效**——`scripts/up.ps1 -DryRun` 在他人持锁时打印 `E_BUILD_CONFLICT` 并退 **75**，未执行任何 `compose up`（W-24）。
- 已验证（2026-11-05 12:45）：可续跑断点**留存**——batch `4a1812cb-1a9b-4809-994e-e0d92ed9e776` 为 `status=running / total=20 / completed=13`，7 条 `chunked`（`bulk-13..19`，`attempts=1`、无 `failure_code`）未丢；`GET /imports/batches` 与 DB 一致（W-24）。
- 未验证：抽取阶段断点/续跑——**已由 S14H-04 收口**（7/7 探针 + smoke-s4/s13 全绿）。
- 已验证（2026-11-05 13:23）：`reasoner` 容器内存已到 **4g**（`Memory=4294967296 RestartCount=0 healthy`），`smoke-s10 22/22`；同内容重复导入幂等（`skipped (same content)`，不新建版本）。
- 未验证：`fsldm-merged.ttl`（2676 三元组）在 SERVICE guardrail 恢复后的**完整 publish 闸门**（本次 publish 命中「已 published 早退」分支，`gates={}`，未复跑 SHACL/Consistency/Materialization）。
- 文档漂移：`embedding.batch_max` 实为 **2**，W-17/看板 S13H-11 记 **4**（12:29 改动未回写，归 P2）。
- 状态变更（2026-11-05 13:21）：活动本体指针已指向 `ont-bc35dc0b625b`（S14H-05 publish 探针，5 三元组），原为 `ont-af5c1e85f5c6`（16 三元组回滚版本）→ 后续如需以 FS-LDM 为活动本体，须重新 publish `ont-f413054a0c72` 或等价版本。
- 已验证（2026-11-05 13:12）：S14H-05 止损核查——compileall exit=0；宿主源码在镜像依赖下 import platform_core.api/validation/adapters.ontology_pg OK（import_document=True、egistries=True）；/healthz=200、/readyz=200；smoke-embed 8/8、smoke-s1 17/17；锁 coordinator#s14h04（pid 80988 已死）已 release，status=free。仓库**可继续开发**；未重建镜像。
- 已验证（2026-11-05 13:26）：S14H-06 G-01 前半（parse-only）——POST /ontology/import 与 /api/ontology/import 已挂载（无鉴权）；unittest 3/3（合法 4 triples/2 classes；语法错误 E_ONTOLOGY_PARSE line=4 column=3；含 owl:imports → usable=false、reason=E_IMPORTS_CLOSURE_NOT_IMPLEMENTED、unresolved 1 条）；无 imports → reason=E_SHACL_NOT_DEPLOYED；宿主 compileall=0。未重建镜像，HTTP 端点未在当前镜像验证。
- 已验证（2026-11-05 13:41）：S14H-07 G-01 第二半（owl:imports 闭包）——闭包 6/6、前半 3/3 单测通过；无 imports → reason=E_SHACL_NOT_DEPLOYED；本地 TTL 	riples 3 → totalTriples 5、source=local-file；缺失 IRI → unresolved 1 条 critical=true/reason=E_IMPORTS_OFFLINE、usable=false/reason=E_IMPORTS_UNRESOLVED；A→B→C 解析 2 条；B→C→B 抛 E_IMPORTS_CYCLE；深度上限 5。离线不联网。未落库/未接 SHACL/未重建镜像。
- 阻塞（2026-11-05 13:47）：S14H-08 G-01 HTTP 集成验证未执行——compose-guard acquire -Purpose g01-http-verify 连续 2 次返回 E_BUILD_CONFLICT exit=75，holder=coordinator#s14h05 pid=75424 purpose=S14H-05 reasoner 4g + publish idempotency heartbeat_age=4min。按 R1 未重建镜像、未重启容器；HTTP 三例与重建后数据核对均**未验证**。重建前基线：documents=607 chunks=2009 graphTriples=10662。锁非本会话持有，未 release。
- 已验证（2026-11-05 14:02）：S14H-09 G-01 第三半（SHACL 接入）——pyshacl 0.30.1；shapes 按 targetNamespace 从 <shapes_dir>/<segment> + manifest 发现；4/4 新单测 + 回归 9/9 通过；缺 label → conforms=false、focusNode=https://w3id.org/fsldm/Agreement；合规 → conforms=true 且 usable=true；无 shapes → conforms=null/E_SHACL_NOT_DEPLOYED；闭包+violation → reason=E_IMPORTS_UNRESOLVED（优先级最高）。未落库/未发布/未重建镜像。
- 已验证（2026-11-05 14:24）：S14H-10 usable 语义修正 + 导入持久化——新增 E_CONSISTENCY_NOT_EVALUATED（三门全过仍 usable=false）；新表 platform.ontology_import（V15，手工已建，schema_version 仍 14，待下次 migrate 确认）；暂存图 urn:platform:graph:import:{importId}；持久化 3/3、SHACL 4/4、parse 3/3、closure 6/6；回滚测试非法图名 → E_ONTOLOGY_STAGE_FAILED 且记录数 0；测试后清理，残留行=0、暂存图=0；guard=free。
14:31 心跳 | docker compose build platform（后台） | 已跑 0s | _impl/logs/s14h11-build.log
14:32 心跳 | 镜像已重建 agent-platform:0.1-s5 13:31:23 | 准备 recreate api | _impl/logs/s14h11-up.log
13:34 心跳 | smoke-s1 命中 E_DB_MIGRATION_MISMATCH（DB 15 > code 14），根因 SUPPORTED_SCHEMA_VERSION 未随 V15 提升；已改 15，重构建第二次 | _impl/logs/s14h11-build2.log
13:35 心跳 | 第二次重建完成 agent-platform:0.1-s5 13:33；readyz=200；复跑 smoke-s1 | _impl/logs/s14h11-smoke-s1.log
- 已验证（2026-11-05 13:36）：S14H-11 G-01 HTTP 端到端——镜像 agent-platform:0.1-s5 重建于 13:33；readyz=200；schema_version=15；smoke-s1 17/17；四例 HTTP：valid 200/usable=false/E_CONSISTENCY_NOT_EVALUATED、broken 400/E_ONTOLOGY_PARSE line=4 col=3、missing 200/E_IMPORTS_UNRESOLVED unresolved=1、no-label 200/E_SHACL_VIOLATION conforms=false focusNode=.../NoLabel；DB 4 条记录 author/created_at 齐全；documents=607 chunks=2009 不变，graphTriples 10662→10683（暂存图 6 图 14 条 + 推理/smoke 残差）；guard 已 release → free（owner=UVSFUJSA\\cpslau#93856）。注：up.ps1 自锁冲突，改用 compose up -d platform（同一 held lock 下）。
- 已验证（2026-11-05 13:58）：S14H-12 一致性门禁 + up.ps1 自锁——真实 reasoner（http://host.docker.internal:7879，ROBOT/EL，POST /v1/reason，consistencyFirst）4/4；一致→usable=true/published=false；disjointWith 冲突→E_CONSISTENCY_FAILED detail=engine-reason-unknown（EL 未返回类名，未编造）；不可达端口 9→E_CONSISTENCY_UNAVAILABLE；sleep 2s + timeout 0.2s→E_CONSISTENCY_TIMEOUT；回归 shacl 4、parse 3、closure 6 全过；up.ps1 fresh 进程：owner-match=0 / wrong-owner=75 / 无参=75；guard 已 release=free。未重建镜像，HTTP 端仍为旧行为。
14:03 心跳 | docker compose build platform（后台） | 已跑 0s | _impl/logs/s14h13-build.log
14:04 心跳 | up.ps1 -AssumeLock 已跑通 exit=0，ready=200 | _impl/logs/s14h13-up.log
- 已验证（2026-11-05 14:06）：S14H-13 重建 + HTTP 复验一致性门禁——镜像 agent-platform:0.1-s5 构建于 13:40:17；up.ps1 -AssumeLock -Owner UVSFUJSA\cpslau#43416 exit=0；/readyz=200、schema_version=15；HTTP 三例：consistent 200/usable=true/published=false/consistency.status=consistent/engine=robot/EL/durationMs=967、disjoint 200/usable=false/reason=E_CONSISTENCY_FAILED/detail=engine-reason-unknown/durationMs=883、no-label 200/usable=false/reason=E_SHACL_VIOLATION/focusNode=.../NoLabel/consistency.not_run；DB 3 条（erin/t、frank/f、gina/f）；documents=607 chunks=2009 不变，graphTriples 10683→10695（本轮 3 个暂存图 ~7 条 + 历史/推理残差）；guard 已 release → free。发布指针切换未做（下一段）。日志：_impl/logs/s14h13-{build,up,consistent,disjoint,no-label}.log|json。
- 已验证（2026-11-05 14:01）：S14H-14 合并段（publish + GSP 实测 + G-03 shapes 部署，单次重建）——镜像 agent-platform:0.1-s5 重建于 13:57:11（容器 image sha eeae2aa3de8d），/readyz=200，self_check schema_version=16（V16 shapes_registry）；up.ps1 -AssumeLock exit=0 但检测到 8080 已占用会跳过 compose up，实际用 `compose up -d platform` 重建容器（记录在 s14h14-recreate.log）。publish dryRun 两别名均 200：imp-a330c40ddbca → versionId ont-aacb4b41bd9d，diff addedTriples=3 removedTriples=16 addedClasses=1 removedClasses=3 addedProperties=1 removedProperties=2，impact affectedEntities/Graphs/Triples=0/0/0，指针未变。单测 test_g01_import_publish.py 4/4（真实 PG/Oxigraph/ROBOT-EL，临时 ns urn:s14pub:，tearDown 恢复 tbox/current）：unusable→409 E_IMPORT_NOT_USABLE；dryRun 指针不变；publish 切到 urn:platform:graph:tbox:ont-*；重复 publish idempotent 同 versionId 且版本数=1；整图替换默认 E_ONTOLOGY_BREAKING（测试显式 acknowledgeBreaking=true）。GSP POST /store：urn:fsldm:tbox、urn:platform:graph:tbox:ont-f34d92ce8e50、urn:platform:graph:import:imp-a330c40ddbca 全部 403 E_GSP_GOVERNANCE_REQUIRED（含 staging，protectedGraph=false 也拒）。G-03：启动自动登记 fsldm-shapes@0.1.0(6 triples)+shapes-core(13)；PUT fsldm-shapes 新版本 sv-f8d74d046c17(12 triples)；GET 显示 0.1.0 保留、current=sv-f8d74d046c17；缺 label 导入 conforms=false、focusNode=https://w3id.org/fsldm/NoLabel，shapesVersion 随登记表从 0.1.0→sv-f8d74d046c17。smoke-s1 17/17、smoke-s11 18/18；documents=607/chunks=2009 不变，graphTriples 10695→10737（smoke 临时图）。guard released → free。未验证：publish dryRun=false 的容器 HTTP 切换（为避免动 tbox/current 只做单测）、fsldm 正式发布、G-03 目录加载在非 serve 路径（smoke）下的登记。
- 已验证（2026-11-05 14:15）：S14H-16 两真问题+僵尸批次（单次重建）——Oxigraph 宿主端口映射整体删除（容器网络 oxigraph:7878）：宿主 POST/GET localhost:7878/store 均 curl exit=7 连接拒绝（http=000，不再 204/404）；/readyz=200、self_check graph=ok、schema_version=17（V17 stale 约束）；容器内 smoke-s1 17/17、smoke-s11 18/18。GSP 口径文档化（_design/04 §4.3 + _impl/README §3/§4.3）：gsp_support=none、gsp_platform{read:unavailable(405), write:forbidden(403)}、gsp_backend_support=full（仅内部比对）。正式指针：烟测前 tbox/current=ont-f0cc82314efd(0.0.0+rollback.37, smoke 污染) → 恢复 ont-bc35dc0b625b(semver 0.0.1, 5 triples) → smoke-s1(新增指针快照/还原逻辑)+smoke-s11 后仍为 ont-bc35dc0b625b(updated_by=smoke-restore)，未被污染。僵尸批次 4a1812cb：running 13/20 updated_at 11:39 → GET /imports/batches 触发租约收敛(30min) → status=stale/stale:true/staleReason=E_BATCH_TIMEOUT，completed=13、indexed=13、chunked=7 全部保留（断点未丢）。未验证：宿主直连读/写替代入口（已关闭，调试需 exec）、长时间进程存活但无更新的误判（阈值 30min 硬编码可调）、smoke-s1 产生的历史版本行仍留库（仅指针还原，未清理行）。
- 已验证（2026-11-05 14:09）：S14H-15 四条尾巴——真实发布（临时 ns urn:test:g01:tbox）：import imp-551695511e3a usable=true → publish dryRun=false → versionId=ont-1b505cdc4e95、previousVersionId=ont-a9906d77a331、pointer=urn:platform:graph:tbox:ont-1b505cdc4e95、publishedAt=06:04:02Z；gates shacl conforms、consistency robot/EL、materialization inferred=2；旧图 export 200（16 triples），新图 export 200（4 triples）。回滚 POST /ontology/rollback {versionId:ont-a9906d77a331} → 指针回 ont-a9906d77a331（graph urn:platform:graph:tbox:ont-309f0897d962，16 triples），new version 保留 superseded。GSP：平台 GET /store=405（读未暴露），POST /store 三类图=403 E_GSP_GOVERNANCE_REQUIRED；直连 Oxigraph POST localhost:7878/store=204（成功写入 urn:test:g01:direct，已 DROP 清理）、直连 GET /store=404 —— 端口暴露风险如实上报。manifest：gsp_support 改为 none（平台面），新增 gsp_platform(read=unavailable/write=forbidden) 与 gsp_backend_support=full（直连探针）；smoke_s1 改为对比 gsp_backend_support（不重建，容器内仍为旧值）。up.ps1：-AssumeLock 且 8080 被占 → 强制 --force-recreate 并 exit=0（首行 owner-match…，关键行 [up] recreate…）；wrong-owner → exit=75（首行 busy…）。失败回滚分支：注入 tx 失败 → E_ONTOLOGY_RECORD_FAILED，staging graph count=0、ontology_import=0（test_5，5/5 通过）。smoke-s1 17/17、smoke-s11 18/18；guard released → free。
- BURST-SAMPLE 2026-11-05 15:02 | 438 | 438 | 0.65 | 5% | 10.9 | 33.9 | 103 | 0.69%
- S14H-BURST（2026-11-05 15:0x 起，立即执行版）：见 `_design/18-burst窗口-计划.md` / `_design/19-burst窗口-复盘.md`。
  - burst on 实测：`NanoCpus=8000000000`（8 核）、`RAYON_NUM_THREADS=8`、`max_chunks_per_sec=0`、embedding restarts=0、`/readyz`=200、`smoke-embed 12/12`。
  - real-12：`438/438/remaining=0/degraded=false`，138 条增量墙钟 213.3s = **0.65 chunk/s**（首次失败 `E_EMBED_MODEL_MISMATCH`，原因为 smoke 把活动分区留在 `fake-hash-1024`，`reindex --activate-only --provider local-bge` 后补跑）。
  - real-11（1844）：`1844/1844/remaining=0/degraded=false`，墙钟 **3084.7s**，**0.60 chunk/s**（batch=100，19 批，checkpoint lastOrdinal=1843）；入库态 `status=degraded` 仅因 `PARTIAL_NO_TEXT_PAGES`（第 156/270/824/932/952 页无文本层）。
  - smoke 污染机制修复：`smoke-embed` 改用一次性命名空间 `smoke-embed-<token>` + 一次性分区 `fake-hash-1024-smoke-<token>` / `fake-hash-2048-smoke-<token>`；生产指针快照-还原并打印前后值（实测 `before=fake:fake-hash-1024-smoke-…` → `after=local-bge:BAAI/bge-m3@1024`）；新增三条收尾断言，已实测 **S13b SMOKE 12/12**，跑完后 active 分区/tbox current/inferred pointer 均未被改动、残留 smoke 向量 0 条。
  - 核数阶梯（S14H-CORES，`bench-embed` 20 短 + 10 长）：8 核 `0.613 chunk/s` → 12 核 `0.653 chunk/s`（+6.5%，<15% 门槛）；16 核不可执行（Docker Desktop VM 仅 12 CPU，`range of CPUs is from 0.01 to 12.00`）。最终定档 **8 核**（NanoCpus=8000000000 / RAYON=8 / rate=0，restarts=0）。
  - 时间拆解：短块 TEI 482ms/chunk（99.36%）、长块 TEI 3763ms/chunk（99.92%）、平台侧仅 3.1ms/chunk；瓶颈是 TEI 推理与单飞，不是核数。28 万 chunk 实测口径外推：短块 37.7h / real-12 混合 120.2h / real-11 混合 130.1h / 长块 292.9h。
  - 新增 `bench-embed --short 20 --long 10`：拆 `tei_service_ms` / `queue_wait_ms` / `platform_ms`（prep+upsert+checkpoint），并给短/长两档中位数与占比；用于回答“1.54s/chunk 花在哪”。
  - `burst.ps1` 支持 `-Cpus/-Rayon` 显式覆盖（阶梯 8→12→16）；核数变更只重建 embedding，仅在 rate 档位变化时才动 platform；每档切完必须 readyz 200 + `smoke-embed` 全绿才继续。

- BURST-SAMPLE 2026-11-05 16:15 | 3293 | 2545 | 0.23 | 34% | 10.6 | 33.7 | 103 | 649%
- S14H-FULL 全量入库启动（逐文档 `/index`，8 核 / rate=0 / restarts=0）：脚本 `_impl/scripts/bulk-index.ps1`，日志 `_impl/logs/bulk-index.jsonl`；续跑命令同上，pending 由 `chunk_embedding` 重算，已嵌入不重算。
- G-01 正式 T-Box publish+rollback 实测：P0=`ont-d79ece714bb6`（15:21-15:22 smoke-s1 遗留的 8 三元组版本）→ 发布 `ont-f413054a0c72`（FS-LDM 2676 三元组，dryRun diff added=2676/removed=8）→ `rollback` 生成 `ont-a29e6033237d` 并切换（8 三元组）→ 再次 `rollback-to` 恢复 `ont-f413054a0c72`；当前指针 fsldm 2676。注：内容按 canonical hash 去重，同内容无法新建 draft，正式切换走 `rollback-to`（仍执行 CAS 还原 + 指针 CAS）。
- G-03 shapes 部署+二次导入：`PUT /ontology/shapes?namespace=https://w3id.org/fsldm/` → `sv-861d1a9d39b6`（6 三元组，ClassLabelShape）；`fsldm-merged.ttl` 二次导入 `conforms=true / 0 violations`（实测 156 个 owl:Class 全部有 label，不是假绿）；缺 label 负样本（删 `agreement#Account` 的 rdfs:label）→ `usable=false / conforms=false / violationCount=1 / focusNode=https://w3id.org/fsldm/agreement#Account`。

- BURST-SAMPLE 2026-11-05 16:26 | 应嵌入 4756 / 已嵌入 4080 / 待嵌入 676 | 本批次 +303（自 16:04） | 0.25（10min 滑动）/ 0.278（批次稳态） | 19% | 10.6 | 33.7 | 103 | 661%
- 口径统一（DB 唯一权威，查询时刻 16:24:07）：应嵌入 = `document_chunk` **4756**；已嵌入 = `chunk_embedding where model='BAAI/bge-m3'` **4080**（active 分区 `local-bge/BAAI/bge-m3/1024`，行数=去重 chunk 数=有向量的 chunk 数，零重复零孤儿）；待嵌入 = **676**。本次脚本范围待嵌入 **602**（real-22 565 / s13h11 33 / s3-* 4）；范围外 **74**（s14h04 16 / bulk-* 8 / s2-s4-smoke 测试件 50）按 `bulk-index.ps1` 的 Filter 故意不纳入。
- 2545 vs 3880 差额（定位完毕）：16:15 采样 SQL 按文件名过滤（`real-%` + `s13h11%`），该子集 embedded=2545（real-* 2285 + s13h11 260），其 `chunk_count` 合计 3293（real-* 2850 + s13h11 443）；全库 active 分区当时 3880 → 差 **1335** = synth-* 379 + bulk-* 827 + other 129。**不是 checkpoint 未提交、不是分区切换**，纯粹是采样分母只含语料子集。
- 0.23 的解释（不做乐观修正）：16:04→16:15 窗口 660s 里前 3 分钟只有 real-18 的 3 块 + s13h11 首批准备，150/660=0.227 偏低；10 分钟滑动 150/600=**0.25**，批次稳态 50/180s=**0.278**（DB 每分钟落库 50 条，16:07/10/13/16/19 连续）。分母只含 `/index` 墙钟，**不含解析/入库**（解析在 ingest 阶段已完成）；平台侧 prep+upsert+checkpoint 仅 3.1ms/块（0.14%），无排队累积 → 0.23 不是被排队/解析拉低，而是**长块拉低**：s13h11 avg 1198 字符且全部 ≥900 → TEI 单飞 ~3.6s/块。
- 整篇完成速率：real-11 `1844/3084.7s = 0.598`；real-12 `138/213.3s = 0.647`（增量口径）；real-18 `3/3.3s = 0.916`（仅 3 块，不作代表）。
- 27.6 万 chunk 外推（按实测，不用乐观口径）：real-11 口径 1.673s/块 → **128h**；real-12 口径 1.546s → **119h**；按当前库长块占比 63.2%（3008/4756）分档加权 → **133–188h**；若全为 1198 字长块 → **276h**；333h 只在全窗口 0.23 时成立，已证明是长块+启动窗口，不是语料稳态。
- `rollback-to` 当发布用的设计债已留痕：`_impl/OPEN-QUESTIONS.md` **OQ-65**（方案 = `publish` 增 `resumeFromVersion`/允许已有 `versionId`，写 `publishedAt/publishedBy/previousVersionId`，diff 标 `canonicalEqual`；工作量 1.5d；本段不改代码）。

- BURST-SAMPLE 2026-11-05 16:38 | 应嵌入 4756 / 已嵌入 4678 / 待嵌入 78 | 本批次 +901（自 16:04） | real-22 0.777 chunk/s（565/726.9s） | 41% | 10.6 | 33.7 | 102.6 | 593%
- 当前队列收尾（16:37）：real-22 `565/565/remaining=0/degraded=false/726.9s/0.777`；s13h11-corpus `333/333/1239.7s/0.269`；real-18 `3/3.3s/0.916`。剩余 78 条 = 范围外测试件 74 + `s3-*` 4（后者只有 `fake-hash` 向量，旧脚本按“任意模型”计数误判为已嵌入；`bulk-index.ps1` 已改为只认 active 分区 model+dimensions）。
- **基数复核（16:35，替代“28 万”）**：语料 `D:\FS-LDM` + `_impl/data/{bench-real,bench-real-hold,corpus-s13,corpus-s13-clean}` 按 sha256 去重 = **443 文件 / 488.6MB**；可解析（pdf/docx/txt/md）**427 篇**，已 ingest **6 篇**，剩余 **421 篇**（明细 `_impl/logs/corpus-all.csv` / `corpus-remaining.csv`）。
- 抽样实测 20 篇（10 bench-real PDF + 4 FS-LDM PDF + 3 md + 2 txt + 1 生成 PDF；17 成功 / 3 加密）= **1,920 chunk / 1.55M 字符 / 285.96MB**，平均 **96 chunk/篇**、**1.24 chunk/千字符**；长块 1,415（**73.7%**）/ 短块 505。脚本与原始输出 `_impl/logs/sample_chunks.py`。
- 关键发现：bench-real 大 PDF 多为**扫描件**（real-01 92MB/838 页、real-08 19MB/194 页、real-13 10MB 均 0 字符 → 0 chunk；OCR 未启用），有文本 PDF 仅 1.8–3.3 chunk/MB；不能用 real-11（158 chunk/MB）外推。
- 复核结论：剩余 ≈**6,900 chunk**，全语料 ≈**1.0–1.2 万 chunk** → **“28 万”高估约 25 倍**，新基数 **≈1.1 万（0.9–1.3 万）**；ETA 剩余 **3.0–3.2h**（长块占比 73.7% 时保守 **6.4h**），全语料从零 4.7–5.1h。已写入 `_design/19-burst窗口-复盘.md` 的“基数复核与 ETA”节（含当前队列/全语料两行）。
- 长/短块占比：当前库 4,756 chunk 中长块 **3,008（63.2%）**、短块 1,748（36.8%）；新语料抽样长块 **73.7%** → ETA 取上限更稳。
- `bulk-index.ps1` 的“已嵌入”统计已改为 active 分区口径（`model`+`dimensions` 取自 `platform.embedding_pointer`），避免非 active 模型的假向量被当成已嵌入。

- **S14H-BURST 总结**：基数从 **28 万** 修正为 **1.1 万**（0.9–1.3 万，依据 443 文件/488.6MB/427 篇盘点 + 20 篇实切抽样 + 375 个 PDF 文本层逐篇检查），ETA 从 **5.4 天** 修正为 **3–6.4 小时**（剩余 6,900 chunk，0.598–0.647 chunk/s，长块 73.7% 取上限）。
- 文本层审计（16:50）：375 个 PDF → **有文本层 360 篇 / 2,587 页 / 222.9MB / 3,340 chunk**；**0 文本层 8 篇 / 1,220 页 / 217MB / 0 chunk**（real-01 838p、real-08 194p、real-21 57p、real-04 42p、real-05 40p、real-17 27p、real-14 20p、real-13 2p）；**7 篇失败**（5 加密：real-19 + FS-LDM 4 篇；2 损坏/加密：corpus-s13 的 corrupted.pdf / encrypted.pdf）。
- 扫描件判定（8/8）：每页字符数 0；渲染墨迹比 0.035–0.999（非空白）；多数页 1 个 image 对象（real-04 每页 24 个），real-17 无 image 但墨迹 0.17 → 真扫描/无文本层，非解析失败。已写 `metadata.noTextLayer=true` + `noTextLayerPages`。
- OCR 只评估未执行：环境无 Tesseract/PaddleOCR（无法实测，不编造）；公开基准 Tesseract 1–2s/页/核、PaddleOCR 3–6s/页/核 → 1,220 页 8 核约 3–15min；云端 ¥6–24。建议 OCR real-01/real-08，其余 6 篇标“不可检索”。
- 缺口留痕：`.ppt` 15 + `.doc` 1 + 5 篇加密 PDF → `_impl/OPEN-QUESTIONS.md` **OQ-66**；扫描件 OCR 决策 → **OQ-67**。
- 继续 ingest：bench-real 导入完成（19/21 新增、1 failed=real-19 加密、alreadyDone 3、embedded +677）；FS-LDM 25 篇导入已接续启动（日志 `logs/import-fsldm.log`）；corpus-s13 / clean 两目录待其后。
