# 26 /context/resolve 性能优化（S16）

- 日期：2026-11-06
- 范围：`search.hybrid` 分段计时 + 三项可证收益的优化 + 24 条查询集质量回归 + 版本历史盘点（只盘点）
- 基线：`_design/25-性能基线.md`（background 档，c1 `/context/resolve` p50 2884 ms）

## 0. 结论

| 指标 | before | after | 判定 |
|---|---|---|---|
| `/context/resolve` p50（固定 query，c1，60 req） | 2884 ms | **62 ms** | 通过（≤800 ms） |
| `/context/resolve` p50（固定 query，c4，80 req） | 3049 ms | **62 ms** | 通过（c4/c1 = 1.0 ≤ 1.5） |
| 24 条 query 轮转 p50（c1 / c4） | — | 94 ms / 94 ms | 通过 |
| 冷启动首个请求（cache miss） | 2858 ms | **181 ms** | 通过 |
| MRR@10（6 条 gold） | 0.5000 | 0.5000 | 守住 |
| seedHit@1（24 条） | 7/24 | 7/24 | 守住 |
| 全量 acceptance | 43 passed | 43 passed / 0 failed / 0 skipped / 0 degraded | 通过 |

本轮 **2 项改动生效、1 项（含 2 个变体）试过无效并回退假设、0 项代码回退**。指针已恢复 `ont-3f57d8ce6636`（2961 triples）。

## 1. 定位方法

在 `SearchService.hybrid_search` 内加入分段计时（`timingMs.pointer/embed/vector/lexical/rrf/total`），并由 `ContextResolver` 写入 `steps[search.hybrid].output`；同时 `/status.search.queryCache` 暴露查询 embedding 缓存命中率。计时为纯观测，开销 <0.1 ms。

before 数据取自未改代码时的实测：`/search?mode=vector` 1008.6 ms、`mode=lexical` 1797.1 ms、`mode=hybrid` 2812 ms；`/context/resolve` 2858 ms（`search.hybrid` 2829 ms，`graph.seed/facts` ≈1 ms）。psql 直接执行旧词法 SQL：`word_similarity(q.raw, c.text) >= 0.1` 全表 14 028 chunk 用时 1750–1824 ms；TEI 单条 query 直连 138 ms。

## 2. 分段耗时（代表 query：`押品覆盖率是多少？`）

| 段 | before | after 冷（miss） | after 热（hit） | 说明 |
|---|---|---|---|---|
| pointer | 0.7 ms | 0.7 ms | 0.7 ms | 单行 embedding_pointer |
| **embed** | **1002 ms**（TEI 138 + 限速 sleep ≈860 + HTTP） | **113 ms** | **0.004 ms** | 限速 sleep 被移除；重复 query 命中 LRU |
| vector | 6 ms | 6 ms | 3.4 ms | HNSW，`candidate_k=30` |
| **lexical** | **1797 ms** | **36 ms** | 36 ms | 旧 SQL 全表 seq scan → trigram GIN |
| rrf | 0.1 ms | 0.13 ms | 0.13 ms | 两路 ≤60 行融合 |
| `search.hybrid` 合计 | 2812 ms | 156 ms | 40 ms | |
| `/context/resolve` 合计 | 2858 ms | **181 ms** | **62 ms** | graph.seed/facts 1 ms |

24 条 query 的分段中位数：pointer 0.69 ms、embed 0.004 ms（全部命中缓存）、vector 3.37 ms、lexical 63.99 ms、rrf 0.13 ms。

## 3. 根因与改动收益

### 3.1 词法检索全表扫描 → trigram GIN（-1760 ms）

旧 WHERE：`word_similarity(q.raw, c.text) >= 0.10`，函数式谓词无法走 `document_chunk_text_trgm_idx`，每次对 14 028 个 chunk 做 trigram 相似度（1.75–1.82 s）。

改为 PG 官方可索引算子：`q.raw <% c.text`（语义等价 `word_similarity(q.raw, c.text) >= pg_trgm.word_similarity_threshold`）。阈值在连接级设置为 `search.min_similarity`（`MetadataPg` 的 `options=-c pg_trgm.word_similarity_threshold=0.1`），保证与旧阈值完全一致。

- 代表 query：1824 ms → 37.5 ms；结果集合相同（58 行，top-30 顺序一致）。
- alias 查询同样受益（每条 1.8 s → 30–70 ms）。
- 改动：`adapters/search_pg.py`、`adapters/metadata_pg.py`、`assembly.py`。

### 3.2 查询 embedding 的索引限速误用（-860 ms）

`EmbeddingClient.embed_with` 的保底限速 `max_chunks_per_sec=1.0` 对**单条 query embedding** 同样生效：`ahead = 1/1.0 - 0.14 ≈ 0.86 s`，每次查询固定 sleep ≈860 ms。

`embed_with` 新增 `rate_limit: bool = True`；交互查询路径传 `False`，文档入库路径保持原限速。改动：`adapters/embedding.py`、`search.py`。

### 3.3 非中文别名在中文语料上的爆炸（-3.0~4.2 s/条）

`lexicon.lexical_queries` 会给出 `Account` / `Policy` / `Collateral Item` 等英文别名。在阈值 0.10 下这些词与 70% 语料（9 807–10 658 / 14 028 chunk）相似，GIN 需回表重检 ~2 600 行，单条 2.9–4.2 s；而这些别名结果按设计被压到 base 结果之下，只在 base 不足 30 条时补位。

改动：query 含 CJK 时，丢弃无 CJK 的别名（`search.py`）。24 条集上平均 `search.hybrid` 893 → 275 ms（改动前），MRR/seedHit 不变。

### 3.4 查询 embedding LRU 缓存（重复 query 命中）

`SearchService` 增加 key = `(provider, model, dimensions, query)` 的 LRU（默认 256），命中率可观测：`/status.search.queryCache`（本轮压测后 hits=322 / misses=25，hitRate 0.928）与 `/search` 响应 `embeddingCache`、`/context/resolve` 的 `steps[search.hybrid].output.embeddingCache`。文档 chunk 向量不走该缓存。

代表 query 热路径 embed 0.004 ms；冷路径 113 ms。

### 3.5 试过、无效（已记录，不改代码）

| 试验 | 结果 | 结论 |
|---|---|---|
| `candidate_k` 30 → 10（LIMIT 10 vs 30 实测） | 760 ms vs 752 ms | 无效：耗时在相似度计算（1 632 行），不在排序 |
| 把 score 只算一次（子查询物化） | 755 ms | 无效：PG 未复用表达式，成本不变 |
| 后处理下推 / 再收候选 | `_rrf` 0.13 ms、`_merge_lexical` 排序 ≤30 行 | 无收益：Python 侧仅字典融合，无可下推 |

## 4. 质量回归（24 条固定查询集）

`coa/platform/logs/bench-20261106/quality_eval.py`：A 组 12（含 6 条附录 B gold 别名问句，goldChunkId 用 `text ILIKE` 定位）+ B 组 5 场景 + C 组 7 指标问法。before 用旧词法 SQL 复刻并与同一向量列表融合，after 走线上 `hybrid_search`。

| 指标 | before | after |
|---|---|---|
| MRR@10（分母 6） | 0.5000 | **0.5000** |
| seedHit@1（24 条） | 7 | **7** |
| top-10 顺序完全一致 | — | 22/24（2 条仅因丢弃英文别名补位行而变化，未含 gold） |
| `search.hybrid` 平均 | 4290.8 ms | **274.8 ms** |

注：查询集按 `24-术语层-落地-方案.md` §5.2–§5.4 与 05 §1.1/§1.2 重建并固化在脚本中（Provisional 口径）。gold 6 条 MRR 与旧实现逐条相同。

## 5. 验收与生态

- 全量 acceptance：`ACCEPTANCE passed=43 failed=0 skipped=0 degraded=0`
- 验收后指针恢复到 `ont-3f57d8ce6636`（reasoner materialize 997 inferred，2796 ms）
- `/readyz` 200；`/status` 各 provider 正常；embedding 指针 `local-bge:BAAI/bge-m3@1024`
- 原始数据：`coa/platform/logs/bench-20261106/`（`bench_context.py`、`quality_eval.json`、`quality_eval.py`）

## 6. 残余瓶颈（本轮不改）

1. **高频中文词**（如 `不良率怎么算？`）在阈值 0.10 下真实命中 1 632 个 chunk，`word_similarity` 需对每个长 chunk 计算，单次词法仍 ~750 ms；这是旋转集 p95 797 ms / p99 2.95 s 的来源。可考虑：对超长 text 只取前缀计算、按命中规模自适应提高阈值、或离线维护 term→chunk 倒排；均会改变打分口径，需单独立项 + 质量对照。
2. 含 ASCII 长 query（`不良率 / NPL ratio 是多少？`）仍 ~2.9 s（自身 trigram 命中过多），不在别名过滤覆盖范围。
3. 目标口径 p50 已达标；p95/p99 未纳入本轮硬指标，如实记录。

## 7. 版本历史盘点（只盘点，不动数据）

当前 `platform.ontology_version`：总 1151，`deprecated` 2（`9.9.9-gov-e2e`、`9.9.8-gov-bad`），**非作废 1149**（比上一轮 1115 多 34，主要来自本轮 acceptance 与既有 smoke 自建版本）。

### 7.1 分类（按 semver 模式 / label / actor）

| 类别 | 判定依据 | 数量 | 状态分布 | 主要 actor |
|---|---|---|---|---|
| s12/s13 | semver `11.x` / `12.x`，label `v1..v5`、`conflict`、`s12 base/breaking` | **490** | approved 63 / draft 196 / superseded 231 | operator |
| smoke-crud | semver `1.0.0` / `2.0.0` / `3.0.0`，label `smoke v1` 等 | **463** | draft 51 / superseded 412 | operator |
| rollback 后缀 | semver `…+rollback.N`，label `rollback of ont-…` | **168** | published 2 / superseded 166 | operator 83、空 83、s14h05 1、burst-ops 1 |
| e2e | semver `0.1.0` | **17** | draft 17 | operator |
| base-zero | semver `0.0.0`，label `bootstrap` / `G-01 import …` | **6** | approved 2 / superseded 4 | operator 3、s14-p0 3 |
| probes | semver `0.0.1` / `9.9.9` / `9.9.10` | **3** | superseded 3 | — |
| **真实交付** | semver `1.1.0`，label `FS-LDM v10 + L1 term layer` | **2** | draft 1（4 triples）/ published 1（2961 triples，当前指针） | operator |

**测试/探测产物 = 1147 / 1149 = 99.83%**；真实可交付只有 1 条 published（`ont-3f57d8ce6636`）和 1 条 1.1.0 draft（`ont-587cc7df09a5`，4 triples，未发布）。

### 7.2 归档方案（下一轮执行，本轮不批量标记）

1. **保留**：`ont-3f57d8ce6636`（published，当前指针）、`ont-587cc7df09a5`（draft，同版本未发布）；如需要审计演示，可额外保留 1 条 `+rollback` 样例。
2. **批量置 `deprecated` 的对象**：上表 6 类共 1147 条。命令形态：
   `platform ontology deprecate --id <version_id> --actor archive-bot --reason "test artifact: <class>"`
3. **绝不物理删除**：`deprecate` 只改 `status` 并追加 `ontology_event`（action=`deprecated`，含 `previousStatus` 与 note），审计链 `prev_event/hash` 不断；`ontology_event` 行数不变。
4. **顺序**：先 s12/s13（490）→ smoke-crud（463）→ rollback（168，含 2 条 published，非指针，`deprecate` 允许）→ e2e/probes/base-zero（26）。每类跑完做一次 `ontology audit verify` 抽样。
5. **预估影响**：1147 次单行事务 + 1147 条审计事件；按现有单次 advisory lock + tx 估算 ~10–20 ms/条，整体约 15–25 s。`graph_pointer`、`graph_iri`、audit 哈希均不变。

### 7.3 批量前必须先确认的点（smoke 依赖）

- `list_versions()` **不带 status 过滤**，`/browse/versions` 与 `web` 表格仍会列出全部行；因此"作废后列表变短"不会自动发生，需要后续给 `/browse/versions` 增加 `status` 过滤参数（本轮不改 UI）。
- 唯一的数量型 smoke 断言是 `smoke_s1.invalid_turtle_side_effects`：比较 `before/after = len(list_versions())`（全集，含 deprecated），只验证"非法 Turtle 不新增版本"，批量作废不影响它。
- `smoke_s1` 的清理由"运行前快照差集"决定删除范围，只删除本次新建行；既有 deprecated 行不会被删。
- `acceptance.ps1` 的 `post.tbox_pointer` / `post.inferred_pointer` 只比较版本 ID，不做数量断言。
- 结论：**当前没有 smoke 断言依赖"未作废数量"**；批量作废可直接进行。但若未来把 `/browse/versions` 改成默认过滤 deprecated，需要同步检查 `web/governance.html` 与本报告 7.3 的列表数量展示。
