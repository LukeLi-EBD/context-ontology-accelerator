# 问答质量（/answer/quality）真跑证据（2026-11-11）

- 被测基线：`luke` @ `02aed081`（含 `dc2fa27c` 按事实修正 G05/G06 标注、`cf1db4f5` 括号标签别名）
- 代码树：`D:\agentABC\wt\luke-all`（分支 `luke`，HEAD `02aed081`）
- 演示栈：桥 `:8210`（本树代码，DSN 指向 5944）、Oxigraph `:7878`、Ontology Workbench `:8131`（`/health` 200，本次问答链路未调用）
- 数据库：`coa-takeover-pg`（127.0.0.1:5944，库 `platform`，schema 53；`tbox/current = ont-4dc7ec9f8f9f`）
- 8080 / 8082 / 哨兵：未启停、未写入；8080 只在 §8 做了一次只读单条探测（不落 run 行、不落 source_ref，已验证）

## 0. 结论摘要

| 项 | 结论 |
| --- | --- |
| 全量 10 条通过率 | **10/10 = 1.0**（`runId=aq-4294f0d6e064`，`evaluatedCount=10/10`，`truncated=false`） |
| 引用 | 24 条，**24 条可解析**（`citationResolvableRate=1.0`），brokenLinks 0 |
| 改前同库同问句 | 旧代码（`254fa3a0`）8/10（`runId=aq-e7ab28f3724b`），失败仅 G05/G06 标注 |
| 历史 3 条 0/10 | **数据状态导致，不是逻辑错误**：三条 run 全部 10 条以 `E_ANSWER_VERSION` 拒答、0 引用；当时 5944 的 `tbox/current` 指针尚未写入（05:29:40 UTC 才由真实发布创建），三条 run 的时间是 04:47 / 04:54 UTC |
| 是否改过阈值/判定 | **没有**。本轮只重启桥换成本树代码，未改任何代码、标注、阈值 |

---

## 1. 本次读数（接口原文）

```
GET http://127.0.0.1:8210/answer/quality?limit=10&strategy=lexical
Authorization: Bearer <local-dev token>
```

```json
{"cases":10,"passed":10,"failed":0,"passRate":1.0,
 "casesWithCitations":10,"citationCoverageRate":1.0,
 "citations":24,"resolvableCitations":24,"citationResolvableRate":1.0,
 "brokenLinkRate":0.0,"regression":false}
```

- `goldenSet = {"id":"r02-golden-10","count":10,"evaluated":10,"available":10,"caseId":null}`
- `runId = aq-4294f0d6e064`，`persisted=true`（写入 `platform.answer_quality_run`，可回查）
- 库内回查：`select run_id, evaluated, passed, failed, pass_rate, citations, resolvable_citations from platform.answer_quality_run` → `aq-4294f0d6e064 | 10 | 10 | 0 | 1.0000 | 24 | 24`

四层覆盖（`layerCoverage`，口径是"至少一条该层引用的条目数"，不是逐层正确率）：

| 层 | covered/evaluated | 说明 |
| --- | --- | --- |
| ontology | 10/10 | 每条回答/拒答都带 `ontology-version` 或本体词条引用 |
| terms | 3/10 | 只有 G01/G02/G05 命中 rdfs/skos 词条；其余问句的实体在 ontology 层命中 |
| metrics | 3/10 | G02/G03/G04 命中指标/公式/规则集 |
| facts | 2/10 | G02/G04 命中 fact-projection |

---

## 2. 逐条判定

| 用例 | 问句 | 类型 | 期望 | 实际 | 判定 | 引用 | 可解析 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01 | 产品包的产品特性有哪些 | definition | 应答 | 应答（`answerType=ontology`） | **通过** | 3 | 3 | ontology-version + ProductPackage/ProductFeature |
| G02 | 13个月继续率（有效保单件数）的口径是什么 | definition | 应答，需 metric-definition + formula | 应答（`answerType=definition`） | **通过** | 6 | 6 | FIN-INS-021@v3.0 指标 + 公式 + fact-projection + Policy/StatusActive |
| G03 | 逾期分档（M0–M6）是什么 | rule_set | 应答，需 rule-set | 应答（`answerType=rule_set`） | **通过** | 4 | 4 | FIN-BANK-002@v3.0 指标 + 公式 + 规则集 |
| G04 | 13个月继续率是多少 | definition | 应答，需 metric-definition，允许 degraded | 应答（`degraded=true`，`reasonCode=E_ANSWER_VALUE_DEGRADED`） | **通过** | 4 | 4 | 标注 `allowDegraded=true`；数值层未就绪，按口径放行 |
| G05 | 当事人关系历史记录保留多久 | definition | 拒答，缺 ontology | 拒答（`E_ANSWER_NOT_COVERED`），缺 ontology | **通过** | 2 | 2 | 命中 core#Party，但无"保留期"概念 |
| G06 | 抵押物价值发生巨大变化时银行如何处理 | definition | 拒答，缺 ontology | 拒答（`E_ANSWER_NOT_COVERED`），缺 ontology | **通过** | 1 | 1 | 只发出 ontology-version |
| G07 | 量子计算机的制冷功率是多少 | value | 拒答，缺 ontology+metrics | 拒答（`E_ANSWER_METRIC_NOT_FOUND`），缺 metrics/ontology/terms | **通过** | 1 | 1 | 域外问句 |
| G08 | 火星探测器电池功率是多少 | value | 拒答，缺 ontology+metrics | 拒答（`E_ANSWER_METRIC_NOT_FOUND`） | **通过** | 1 | 1 | 域外问句 |
| G09 | 量子退火机的能耗是多少 | value | 拒答，缺 ontology+metrics | 拒答（`E_ANSWER_METRIC_NOT_FOUND`） | **通过** | 1 | 1 | 域外问句 |
| G10 | 超导磁悬浮列车的时速是多少 | value | 拒答，缺 ontology+metrics | 拒答（`E_ANSWER_METRIC_NOT_FOUND`） | **通过** | 1 | 1 | 域外问句 |

补充说明：

- G02/G03/G04 的 `actual.missing` 里出现 `facts, ontology`，但用例仍通过。`missing` 是"未被解析成实体的片段所落的层"的提示（例如括号里的限定语），**不是**用例失败条件；判定只看 `failures`（期望是否拒答、必需引用类型、引用是否可解析、是否非预期 degraded）。
- G06–G10 的"可解析"各为 1 条，等同于 `ontology-version` 一条；全部 `resolvable=true`。
- 拒答用例带 1–2 条引用是设计内行为：拒答也要指出"我依据的是哪一版本本体"。

---

## 3. 改前 / 改后同问句对比（解释历史 0/10 与本次 10/10）

三个时点、同一问句 G05「当事人关系历史记录保留多久」：

| 时点 | 代码 | 数据状态 | 实际行为 | 用例判定 |
| --- | --- | --- | --- | --- |
| 04:47 UTC（历史 run） | 旧 | 5944 无 `tbox/current` | 拒答 `E_ANSWER_VERSION`，引用 0 | 失败（10 条全失败） |
| 13:40 UTC（本轮改前） | `254fa3a0`，标注 `expectRefused=false` | 5944 已有 `tbox/current=ont-4dc7ec9f8f9f` | 拒答 `E_ANSWER_NOT_COVERED`，引用 2（ontology-version + core#Party），缺 ontology | 失败：`expected refused=false, got true` |
| 13:41 UTC（本轮改后） | `02aed081`，标注 `expectRefused=true` + 缺 ontology | 同上 | 同上（行为未变） | **通过** |

G06 同理：改前 `expected refused=false, got true`；改后通过，引用 1 条。

改前（旧代码 + 现库）整轮为 **8/10**，逐条：

```
G01 pass  G02 pass  G03 pass  G04 pass
G05 FAIL  expected refused=false, got true
G06 FAIL  expected refused=false, got true
G07 pass  G08 pass  G09 pass  G10 pass
```

结论：**改前改后的回答行为完全一致**（同一问句同样拒答、同样引用、同样缺层），差异只在 golden 标注；`dc2fa27c` 是"按真实本体能力改标注"，不是"改判定让分变好看"。该提交同时补了回归断言：字符覆盖 0.75 高于阈值但缺两个概念必须拒答、阈值降到 0.5 仍拒答、实体零命中阈值降到 0 也拒答。

回归测试（只读，指向同一 5944 + 7878）：

```
TEST_PG_DSN=postgresql://platform:platform_dev@127.0.0.1:5944/platform
TEST_OXIGRAPH_URL=http://127.0.0.1:7878
pytest packages/platform-core/tests/test_q4_answerable.py -q
→ 17 passed
```

---

## 4. 历史 3 条 0/10 的根因（数据，不是逻辑）

三条 run（5944）：

```
aq-7f24b4ceb114 | 2026-11-11 04:47:41+00 | evaluated=10 pass=0 rate=0.0000 citations=0
aq-09cf7b95aee6 | 2026-11-11 04:54:55+00 | evaluated=10 pass=0 rate=0.0000 citations=0
aq-c48d41ffd810 | 2026-11-11 04:54:55+00 | evaluated=10 pass=0 rate=0.0000 citations=0
```

三份 `detail` 的内容一致：

- `refusalsByReason`：`definition ×5 / rule_set ×1 / value ×4`，**全部是 `E_ANSWER_VERSION`**；
- `citationCoverageByType`：三类全部 `citations=0, withCitations=0`；
- `layerCoverage`：ontology / terms / metrics / facts 四层 `covered=0`；
- `refusalsWithoutLayers`：10 条全在列（连"缺哪层"都无处可报）。

`E_ANSWER_VERSION` 的出处：`AnswerabilityService._version()` 在没有版本或 `current()` 为空时抛
`NotFound: no published ontology version: answerability needs a T-Box`
（[answerable.py:226-249](file:///d:/agentABC/wt/luke-all/packages/platform-core/src/platform_core/answerable.py#L226-L249)；`current()` 读 `platform.graph_pointer` 的 `tbox/current`，[ontology_pg.py:1617-1637](file:///d:/agentABC/wt/luke-all/packages/platform-core/src/platform_core/adapters/ontology_pg.py#L1617-L1637)）。

5944 的指针时间线：

```
select name, version_id, updated_at, updated_by from platform.graph_pointer where name='tbox/current';
tbox/current | ont-4dc7ec9f8f9f | 2026-11-11 05:29:40.101182+00 | local-dev@example.invalid
```

`tbox/current` 只有这一行，创建于 **05:29:40 UTC**，由真实发布写入（同一秒有 `published` 事件 18577）。三条 0/10 run 都在 04:47–04:54 UTC，**指针还不存在**。

所以：三条 0/10 = 当时 5944 还没发布过 T-Box（只有 11-10 21:51 由 `p1-backfill:v52` 回填的各版本指针，没有 `tbox/current`），答案管线拿不到任何本体版本 → 全部 `E_ANSWER_VERSION`、零引用。**不是判定逻辑错误**：同一份旧代码在补齐指针后重跑为 8/10，另外 2 条失败的原因是可解释的标注错误。

---

## 5. 演示口径判断：这个分数能不能说话

**能说，但要带限定，且必须说清楚它是什么分数。**

可以说的：
- 在 `luke@02aed081` 代码、5944 新库、`lexical` 策略、`top_k=5`、golden 10 条（4 条正向 + 6 条拒答）下，`GET /answer/quality?limit=10` 为 **10/10，24 条引用全部可解析**，结果落库可回查（`aq-4294f0d6e064`），一条命令可复现。
- 拒答不是"不答"，而是带 reasonCode 与缺失层（`E_ANSWER_NOT_COVERED` / `E_ANSWER_METRIC_NOT_FOUND`），并且可以说明依据的本体版本。

不能说的：
- 不能说"问答准确率 100%"。10 条里 6 条是拒答，拒答判定天然比开放问答容易；样本只有 10 条，且 G05/G06 的标注刚刚（19:52）按事实修正过。
- 不能用这个分数代表 `hybrid`/`vector` 策略；本次只跑了默认 `lexical`。
- **不能用 8080 页面说 10/10**：8080 现网镜像 `agent-platform:0.1-s6-readonly` 构建于 2026-11-10 21:23:08 UTC（= 11-11 05:23 +08），早于 19:52 的标注修正；容器启动于 11-11 00:39:56 UTC（= 08:39 +08），也早于修正。§8 的单条只读实测已确认 8080 上 G05 仍判失败（旧标注）；全量分数按推断为 8/10，**未在 8080 上跑全量、未验证**。其库是 5432（1,908/1,313/10,134）。
- 演示若走 8131 的 Workbench UI，也要确认它读的是哪套库；本轮 8131 只探了 `/health`，未验证其问答链路。

一句话版本：**"演示栈（8210/5944）上 10/10、24 条引用全可解析，可复现、可回查；这是 golden 10 条的口径，不是通用准确率；8080 镜像未更新，别拿它说这个分。"**

---

## 6. 复现命令

```powershell
# 1) 启动桥（本树代码，指向 5944 / 7878）
powershell -NoProfile -ExecutionPolicy Bypass -File D:\agentABC\.runbook-lukeall\start-api-lukeall.ps1

# 2) 取本地开发 token
$t = (Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8210/local/auth/token' `
      -ContentType 'application/json' -Body '{"email":"local-dev@example.invalid"}').accessToken

# 3) 全量 10 条
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8210/answer/quality?limit=10&strategy=lexical' `
     -Headers @{Authorization="Bearer $t"}
$r.summary; $r.runId

# 4) 单条回看（不产生新 run）
Invoke-RestMethod -Uri 'http://127.0.0.1:8210/answer/quality?limit=10&strategy=lexical&caseId=G05' `
  -Headers @{Authorization="Bearer $t"}

# 5) 库内回查
docker exec coa-takeover-pg psql -U platform -d platform -tAc `
  "select run_id, ran_at, evaluated, passed, pass_rate, citations, resolvable_citations from platform.answer_quality_run order by ran_at"
```

---

## 7. 未验证 / 边界

- **页面截图 / DOM**：本轮只走接口与库，未起 web、未截 F86 页面。
- **8080（5432）**：只做了一次单条只读钻取（§8.1，G05 实测失败，未写库）；**未在 8080 上跑全量**，"8080 全量 8/10"仍是按镜像构建时间推断，未验证。
- **hybrid / vector 策略**：未跑。
- **8131 的问答链路**：只探 `/health` 200，未验证其是否转发到同一桥/库。
- **"分好看"的可持续性**：G05/G06 的标注修正有回归测试兜底（17 passed），但 golden 集只有 10 条；扩样后通过率可能下降。
- **本文件中"改前 8/10"的逐条失败文本**来自本轮对旧代码桥（`254fa3a0`）的一次真实调用（`runId=aq-e7ab28f3724b`）；该 run 的 `detail` 不存 `cases`，逐条失败文本仅在本轮控制台输出中可见，库内可复核的是 8/10、24/24 引用与拒答分布。

---

## 8. 8080 当前是多少分（实测 / 推断分开写）

### 8.1 已实测（只读，单条）

```
GET http://127.0.0.1:8080/answer/quality?limit=10&strategy=lexical&caseId=G05
→ 200
{"goldenSet":{"count":10,"evaluated":1,"caseId":"G05"},
 "summary":{"cases":1,"passed":0,"failed":1,"passRate":0.0,
            "casesWithCitations":1,"citations":8,"resolvableCitations":8,
            "citationResolvableRate":1.0,"brokenLinkRate":0.0}}
```

- 这条是 `caseId` 钻取：按 [api.py:6096](file:///d:/agentABC/wt/luke-all/packages/platform-core/src/platform_core/api.py#L6096)，`caseId` 非空时 `runId=None`、不写 `answer_quality_run`。
- 调用前后核对 5432：`answer_quality_run` 保持 9 行（未新增）；`source_ref_registry` 最近写入仍是 2026-11-08 08:55:45 +08，20 分钟内新增 0 行。**该探测没有写库。**
- 结论（实测）：8080 上 G05 判 **失败**，说明 8080 跑的是 G05/G06 修正前的标注（`expectRefused=false`）；同时 8 条引用全部可解析。

### 8.2 仍是推断（未跑全量）

- 8080 全量 10 条 → **推断 8/10**，依据：
  1. 镜像 `agent-platform:0.1-s6-readonly` 构建于 2026-11-10 21:23:08 UTC，容器启动于 2026-11-11 00:39:56 UTC，均早于标注修正提交 `dc2fa27c`（11-11 19:52 +08）；
  2. §8.1 实测 G05 失败，与"旧标注只挂 G05/G06"一致；
  3. 5432 的同库历史 run 在修正后可到 10/10，说明剩余 8 条不是数据问题。
- **未验证项**：没有在 8080 上跑全量 10 条（会写一条 `answer_quality_run`，属于 8080 写路径，本轮不解冻、不写）。
- 因此对 8080 只能说：**"G05 实测失败；全量按镜像时间推断 8/10，未验证。"** 不能说"8080 是 10/10"。
