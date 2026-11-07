# q_S07 · 最小 Web UI 页面

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S07` |
| 特性名称 | 最小 Web UI 页面 |
| 分组 | A 核心工作流 S0-S14 |
| 文档依据 | 10-实施路线图.md S7；46 技术说明书 UI 章节 |
| **评估轮次** | **R2（第 2 轮复评）** |
| **本轮采集时间 T2** | **2026-11-07 07:56:21 +0800** |
| **判据栈** | 双栈 |
| 结论（T2） | **PASS** |
| 证据截图 | ![终端输出截图](screenshots/q_S07.png) |
| 完整原始输出 | `evidence/q_S07.txt` |

## 0 时间区分（本轮新增）

> 同一特性在不同时间点、不同栈上的状态不同，结论必须带坐标。T0/T1 的旧产物完整保存在
> `_history/2026-11-06_2352/`，独立复核见 `../_evidence-audit/qa_verdict_recheck.md`。

| 轮次 | 时间 | 栈 / 代码基线 | 结论 | 说明 |
| --- | --- | --- | --- | --- |
| **T0 原始采集** | 2026-11-06 23:52 +08 | 数据栈 8080 · 旧镜像 | PASS | R1 采集器，存在 200KB 静默截断与写死结论 |
| **T1 独立复核 / 修复基线** | 2026-11-07 05:45–06:08 +08 | 验收栈 8082 · `8b3f36f` | PASS | 复核定性：一致 |
| **T2 本轮复评** | 2026-11-07 07:56:21 +0800 | 数据栈 8080 + 验收栈 8082 双栈同题 | **PASS** | 采集器已修截断、verdict 由证据动态推导 |

栈说明：
- **数据栈 8080**：镜像 `715d59e8`（11-07 00:53 +08 构建），全量数据，用于验证「数据内容 / 规模」类判据。注意 T0(11-06 23:52) 时 8080 跑的是更早的镜像，容器在 00:53 被重建过，**同一端口跨时间也不是同一个基线**。
- **验收栈 8082**：镜像 `80cb274f` / `agent-platform:0.1-s5`（11-07 05:45 +08 构建），代码等价 `8b3f36f`，验收残留小库，用于验证「代码行为 / 契约」类判据。
- 验收栈 A-Box 为空导致的 `404 / 0` 不判为功能缺陷；两栈版本不同属独立数据库，不计为漂移。

## 1 测试目标

验证原生 HTML 前端页面可访问（无构建链），且关键 tab 页面存在。

## 2 输入

- `GET /ui/index.html`
- `GET /ui/browse.html`
- `GET /ui/entity.html`
- `GET /ui/health.html`

> 零污染约束：仅 HTTP GET、只读 SQL `SELECT`、只读 SPARQL `SELECT`、一个已确认不写库的纯读
> `POST /context/resolve`。未调用 `/answer`（会写 PROV 拒答事件），未运行 smoke/acceptance，
> 未触发 seed / refresh / import / materialize / approve / publish / reindex / rollback。
> 验收栈 SPARQL 因 A-Box 为空显式标注 `SKIP`，不做无意义的图查询。

## 3 期待输出

四个页面 HTTP 200 且返回 HTML 文本，非 404 / 非空白。

## 4 真实输出（T2 · 双栈同题）

### 4.1 数据栈 127.0.0.1:8080（全量数据 / 旧代码）

```
$ GET /ui/index.html
  -> 200  2ms  1373 chars | FULL_LENGTH=1373 chars  SHA256=a7d6b1392df96e2a  PARSE=non-json  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-wi ...(截断)
  <!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, initial-scale=1">   <tit ...(截断)
$ GET /ui/browse.html
  -> 200  2ms  11387 chars | FULL_LENGTH=11387 chars  SHA256=b3b0239116b827a1  PARSE=non-json  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-wi ...(截断)
  <!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, initial-scale=1">   <tit ...(截断)
$ GET /ui/entity.html
  -> 200  1ms  2628 chars | FULL_LENGTH=2628 chars  SHA256=02e7e06308b909ad  PARSE=non-json  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-wi ...(截断)
  <!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, initial-scale=1">   <tit ...(截断)
$ GET /ui/health.html
  -> 200  1ms  2507 chars | FULL_LENGTH=2507 chars  SHA256=2d3783b8945f9ab2  PARSE=non-json  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-wi ...(截断)
  <!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, initial-scale=1">   <tit ...(截断)
$ GET /readyz
  -> 200  28ms  537 chars | FULL_LENGTH=537 chars  SHA256=0fb8ec1aa53f054c  PARSE=dict  KEYS=status,checks,pointerStatus,warnings,note
  status = ok
  checks = {"database": {"status": "ok"}, "graph": {"status": "ok"}, "storage": {"status": "ok", "disk_free_pct": 32.64}}
  pointerStatus = {"name": "tbox/current", "ok": true, "level": "ok", "status": "published", "versionId": "ont-11f92ebb3326", "semver": "1.2.1", "tr ...(截断)
  warnings = []
  note = pointerStatus 仅告警，不参与就绪状态码（避免启动即崩）
$ GET /status
  -> 200  642ms  11200 chars | FULL_LENGTH=11200 chars  SHA256=e7dc32324bc2d0e8  PARSE=dict  KEYS=status,version,slice,mode,runtime_mode,config_version,config_file,providers,not_implemented,degraded,storage,graph
  status = ok
  version = 0.1.0
  slice = S13
  mode = single
  runtime_mode = learn
```

### 4.2 验收栈 127.0.0.1:8082（新代码 8b3f36f / 小库）

```
$ GET /ui/index.html
  -> 200  2ms  1373 chars | FULL_LENGTH=1373 chars  SHA256=a7d6b1392df96e2a  PARSE=non-json  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-wi ...(截断)
  <!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, initial-scale=1">   <tit ...(截断)
$ GET /ui/browse.html
  -> 200  2ms  11387 chars | FULL_LENGTH=11387 chars  SHA256=b3b0239116b827a1  PARSE=non-json  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-wi ...(截断)
  <!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, initial-scale=1">   <tit ...(截断)
$ GET /ui/entity.html
  -> 200  1ms  2628 chars | FULL_LENGTH=2628 chars  SHA256=02e7e06308b909ad  PARSE=non-json  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-wi ...(截断)
  <!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, initial-scale=1">   <tit ...(截断)
$ GET /ui/health.html
  -> 200  2ms  2439 chars | FULL_LENGTH=2439 chars  SHA256=98a1ac0b8627d88a  PARSE=non-json  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, ...(截断)
  <!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=device-width, initial-scale=1">   <title>健康 ...(截断)
$ GET /readyz
  -> 200  6ms  537 chars | FULL_LENGTH=537 chars  SHA256=014659d11612174f  PARSE=dict  KEYS=status,checks,pointerStatus,warnings,note
  status = ok
  checks = {"database": {"status": "ok"}, "graph": {"status": "ok"}, "storage": {"status": "ok", "disk_free_pct": 32.64}}
  pointerStatus = {"name": "tbox/current", "ok": true, "level": "ok", "status": "published", "versionId": "ont-6e81732555e5", "semver": "0.0.0", "tr ...(截断)
  warnings = []
  note = pointerStatus 仅告警，不参与就绪状态码（避免启动即崩）
$ GET /status
  -> 200  58ms  11356 chars | FULL_LENGTH=11356 chars  SHA256=406a3270929bc0c9  PARSE=dict  KEYS=status,version,slice,mode,runtime_mode,config_version,config_file,providers,not_implemented,degraded,storage,graph
  status = ok
  version = 0.1.0
  slice = S13
  mode = single
  runtime_mode = learn
```

> 完整响应（含 `FULL_LENGTH` / `SHA256` / 结构化摘要，超大正文显式标记 `[BODY OMITTED]`）见
> `evidence/q_S07.txt`；终端渲染截图见 `screenshots/q_S07.png`。

## 5 结论

**PASS** — 四个原生页面 HTTP=[200, 200, 200, 200]，均返回 HTML 正文，无构建链依赖。



---
[返回总报告](README.md) · [T0 归档](<_history/2026-11-06_2352/q_S07_最小 Web UI 页面.md>)
