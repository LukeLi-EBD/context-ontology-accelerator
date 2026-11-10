# P1-01 Ingestion 列表数值对账（2026-11-11）

对账对象：`/namespaces/{namespaceId}/documents` 页「Import batches」表 vs `serve_local` 库内
`platform.import_batch` / `platform.import_item` / `platform.import_run`。
环境：真实桥 `doc/coa-x/tools/coa_api_local.py`（`127.0.0.1:8699`，`COA_LOCAL_AUTH_MODE=enforce`）
+ 本机 vite（`5174`）+ PG `coa-local-pg`（`127.0.0.1:5444/serve_local`）。
namespace：`ed70a15c-2d42-4dc9-8c61-33b2584f05fd`。

页面值由浏览器读取表格单元格渲染文本（状态文案连同颜色/副行一起记录）；
库内值由 `psql` 直连 `serve_local` 取得。时间统一换算到 `Asia/Shanghai` 后比较，
页面显示 `YYYY/MM/DD HH:MM:SS`，库内格式化为 `YYYY-MM-DD HH24:MI:SS`。

## 取数 SQL（列表口径，与 `platform_core/importer.py` 的 `ingestion_runs()` 一致）

```sql
-- 计数：原样取自 importer.py 的列表查询，仅把 WHERE 收窄到单批次
SELECT b.batch_id, b.root_path, b.status, b.created_at, b.updated_at, b.finished_at,
       COUNT(i.rel_path) AS total,
       COUNT(i.rel_path) FILTER (WHERE i.status IN ('indexed', 'failed')) AS completed,
       COUNT(i.rel_path) FILTER (WHERE i.status = 'indexed') AS indexed,
       COUNT(i.rel_path) FILTER (WHERE i.status = 'failed')  AS failed,
       COUNT(i.rel_path) FILTER (WHERE i.degraded)          AS degraded
  FROM platform.import_batch b
  LEFT JOIN platform.import_item i ON i.batch_id = b.batch_id
 WHERE b.batch_id = '<batch_id>'
 GROUP BY b.batch_id, b.root_path, b.status, b.created_at, b.updated_at, b.finished_at;

-- 列表行左侧链接的 runId 实际是 batch_id；右侧 lastRun.run_id 来自这里
SELECT DISTINCT ON (batch_id) batch_id, run_id, status, started_at, finished_at, exit_code
  FROM platform.import_run
 WHERE batch_id = '<batch_id>'
 ORDER BY batch_id, started_at DESC;

-- 时间：页面按 +08 渲染，库内按同一时区格式化后再比
SELECT to_char(created_at AT TIME ZONE 'Asia/Shanghai', 'YYYY-MM-DD HH24:MI:SS') AS started,
       to_char(finished_at AT TIME ZONE 'Asia/Shanghai', 'YYYY-MM-DD HH24:MI:SS') AS finished
  FROM platform.import_batch WHERE batch_id = '<batch_id>';

-- 子项真实性：indexed 是否真有向量、failed 是否确实没有
SELECT i.rel_path, i.status, i.degraded,
       (SELECT count(*) FROM platform.chunk_embedding e
          JOIN platform.document_chunk c ON c.chunk_id = e.chunk_id
         WHERE c.document_id = i.document_id AND e.model = 'BAAI/bge-m3') AS vectors
  FROM platform.import_item i
 WHERE i.batch_id = '<batch_id>'
 ORDER BY i.rel_path;
```

## 表 1：单批次九列（batch `d3a5f8a4-1fb4-4ec8-85a1-01955e1c8f12`）

root：`C:\Users\cpslau\AppData\Local\Temp\p1-gate-e2e-8iskkft7`（3 个文件，全部成功）

| 列 | 页面值 | 库内值 | 取数 SQL | 相等? |
|---|---|---|---|---|
| runId（行左侧链接 = batch_id） | `d3a5f8a4-1fb4-4ec8-85a1-01955e1c8f12` | 同左 | `SELECT b.batch_id ...` | 是 |
| status | `Completed`（绿色） | `completed` | `SELECT b.status ...` | 是 |
| total | 3 | 3 | `COUNT(i.rel_path)` | 是 |
| completed | 3 | 3 | `COUNT(...) FILTER (WHERE i.status IN ('indexed','failed'))` | 是 |
| indexed | 3 | 3 | `COUNT(...) FILTER (WHERE i.status='indexed')` | 是 |
| failed | 0 | 0 | `COUNT(...) FILTER (WHERE i.status='failed')` | 是 |
| degraded | 0 | 0 | `COUNT(...) FILTER (WHERE i.degraded)` | 是 |
| startedAt | `2026/11/11 02:44:02` | `2026-11-11 02:44:02` | `to_char(b.created_at AT TIME ZONE 'Asia/Shanghai', ...)` | 是 |
| finishedAt | `2026/11/11 02:44:02` | `2026-11-11 02:44:02` | `to_char(b.finished_at AT TIME ZONE 'Asia/Shanghai', ...)` | 是 |

`lastRun.run_id`（右侧链接目标）：`1cc2958c-f7db-49b1-9220-caeb2b2ffd8e`，库内
`import_run` 同一批次仅 1 条，`status=completed`、`exit_code=0`，页面一致。
说明：**行左侧 `runId` 与右侧 `lastRun.run_id` 是两个字段**，前者是 `batch_id`。

## 表 2：混合批次六列（batch `93d5802e-ee0d-4463-afe8-8c30b238c978`）

root：`C:\Users\cpslau\AppData\Local\Temp\p1-mixed-mix01\docs`（3 个文件，2 成功 / 1 失败）

| 列 | 页面值 | 库内值 | 取数 SQL | 相等? |
|---|---|---|---|---|
| status | `Completed`（绿色）+ 红字 `embedding degraded: E_EMBED_UNAVAILABLE` | `completed` | `SELECT b.status ...` | 值相等（口径见下） |
| total | 3 | 3 | `COUNT(i.rel_path)` | 是 |
| completed | 3 | 3 | `COUNT(...) FILTER (WHERE i.status IN ('indexed','failed'))` | 是 |
| indexed | 2 | 2 | `COUNT(...) FILTER (WHERE i.status='indexed')` | 是 |
| failed | 1 | 1 | `COUNT(...) FILTER (WHERE i.status='failed')` | 是 |
| degraded | 3 | 3 | `COUNT(...) FILTER (WHERE i.degraded)` | 是 |

补充：`startedAt=2026/11/11 05:17:06`、`finishedAt=2026/11/11 05:17:36` 也与库一致；
`lastRun.run_id=de1ae0bb-ff7d-44ef-b829-483a886e729c`（最后一次 invocation，`exit_code=1`）。
子项真实性：`mixed-doc-1/2.txt` 为 `indexed` 且各有 1 条 `BAAI/bge-m3` 向量；
`mixed-doc-3.txt` 为 `failed`、0 条向量。

### 混合批次的造数步骤（可复现）

1. embedding 指向一个固定返回 503 的临时端点（`http://127.0.0.1:8698/v1`），
   `python -m platform_core.cli import <dir> --namespace-id <ns> --config <yaml>`；
   3 个文件全部落 `failed / E_EMBED_UNAVAILABLE`。
2. 恢复本机 TEI（`http://127.0.0.1:8081/v1`），执行
   `... import <dir> --retry-failed --batch-size 2`：2 个转 `indexed`，余 1 个 `pending`。
3. 再次切回 503 端点，执行 `... import <dir> --batch-size 2`：最后 1 个重新落 `failed`。
   最终 `indexed=2 / failed=1`，批次 `completed`，CLI 退出码 1。

> `--retry-failed` 会把该批次全部 `failed` 重置为 `pending`，所以「只重试一部分」靠
> `--batch-size` 限制单次处理文件数；不要用删文件的方式制造部分失败（行会卡在 `pending`）。

## 行数口径（页面行 ≠ `import_run` 行）

页面一行 = 一个 `import_batch`（按 `root_path` 归并），**不是** `import_run` 的行数；
页面上那五个数字是 `import_item` 的聚合，**不是** `import_run.counters`。同一批次重跑
4 次只占页面 1 行。不要拿 `SELECT count(*) FROM platform.import_run` 去对页面行数，
否则会以为页面漏行。

## 状态口径

`import_batch.status='completed'` 的含义是「每个发现的条目都处理过（indexed 或 failed）」，
**不代表全部成功**（契约 `models/src/main/smithy/ingestion-runs.smithy` 的
`IngestionRunStatus.COMPLETED` 注释同义）。子项失败由 Failed 计数与失败原因文案暴露：
前端在绿色 `Completed` 下方追加红字失败信息（取自 `ingestion_runs()` 的 failures 查询）。

本轮不动状态枚举：改成红色 `Failed` 需同时改 smithy 枚举、库 CHECK 约束、前端派生三处，
P0 已出口，收益不抵风险，记「下个 tag 后评估」。

## 遗留观察（已另立 P1-15）

混合批 `degraded=3`，但其中 2 条已 `indexed` 且确有向量，仍带 `degraded=true`：
重试成功沿用了失败轮的标记。页面与库一致（都是 3），不是映射错误；`degraded` 语义收口
另开分支处理。
