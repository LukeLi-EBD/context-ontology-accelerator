# scripts/data-fix

一次性数据修复脚本的受控目录。收进来的唯一标准是：**脚本会写生产数据**。只读脚本一律不收。

背景：2026-11-11 05:50 左右，`.p1-evidence/backfill_ownership.py` 在 git 之外直接连
5944 的 `platform` 库，一个事务里 UPDATE 了 `ontology_version` / `ontology_proposal` /
`ontology_event` 共 13,355 行，但没有留下任何 `ontology_event` 审计记录，事后无法归因。
本目录用「先 dry-run、执行必写事件、事件失败整体回滚」把这类写入收进可审计的路径。

## 收录清单（会写库）

| 脚本 | 写哪个库 | 连接配置 | 写什么 |
| --- | --- | --- | --- |
| `backfill_ownership.py` | 目标 `platform` | `TARGET_DSN` | 回填 `ontology_id` / `attribution_source` |
| `migrate_ontology.py` | 源 `platform` → 目标 `platform` | 两个位置参数 DSN | COPY 三张本体表到空目标库 |
| `migrate_six_rows.py` | `serve_local` → `platform` | `SERVE_LOCAL_DSN` / `TARGET_DSN` | 迁 2 version + 1 proposal + 3 event |
| `write_pointers.py` | 目标 `platform` | `TARGET_DSN` | 写 `graph_pointer` 的 `tbox/<ont>/current` |
| `mark_legacy_fixtures.py` | `serve_local` | `SERVE_LOCAL_DSN` | 给 78 行夹具打 `legacy_fixture` 标记 |

公共依赖：`psycopg[binary]>=3.1`。

## 未收录清单（只读，不进仓库）

| 文件 | 不收录理由 |
| --- | --- |
| `apply_v52_v53.py` | DDL 迁移执行器，不是数据修复；且它的审计事件会占用源库真实事件 id，导致全量迁移主键冲突。迁移仍由 git 版本 + `schema_version` 台账治理 |
| `build_event_id_map.py` | 只读两个库，写本地 CSV |
| `reconcile_rows.py` | 只读对账，只打印 JSON |
| `inventory_serve_local.py` | 只读，写本地清单文件 |
| `serve_local_disposition.py` | 只读，写本地 markdown |
| `probe_pointer_and_coverage.sql` | 只读查询 |
| `embed_stub.py` | 本地 HTTP 桩，不碰数据库 |
| `measure_peak.py` | 只测 RSS/耗时，自己不写库 |
| `run-real*.ps1` | 压测驱动，目标是临时库 `realcorpus`，不是生产 `platform` |

`mark_legacy_fixtures.py` 原先从 `serve_local_disposition.py` 导入夹具 id 集合；为保持
「只读脚本不入库」的边界，两组 id 已原样内联，并注明来源。

## 通用开关

所有脚本共用 `audit.common_parser`：

- **默认 dry-run**：不带 `--apply` 只统计并打印「哪些表、会改多少行」，不写库。
  实现上用 `conn.transaction(force_rollback=True)` 兜底，即使脚本意外写了也会回滚。
- `--apply`：真正执行。先打印同一份计划，再在一个事务里完成「数据改动 + 审计事件」。
- `--batch-id`：批次 id，默认 `YYYYMMDDTHHMMSSZ-<8 hex>`。
- `--actor`：审计 actor，默认 `$COA_ACTOR`，再退到 `<系统用户>@<主机名>`。

示例：

```powershell
# 只看计划
python scripts/data-fix/backfill_ownership.py

# 执行（显式）
python scripts/data-fix/backfill_ownership.py --apply --batch-id 20261111T080000Z-manual
```

dry-run 输出示例：

```text
[DRY-RUN] script=scripts/data-fix/backfill_ownership.py batch_id=20261111T080000Z-1a2b3c4d
  platform.ontology_version          update   rows=1908     where=ontology_id IS NULL AND graph_iri matches
  platform.ontology_proposal         update   rows=1313     where=ontology_id IS NULL AND version exists
  platform.ontology_event            update   rows=10134    where=ontology_id IS NULL AND post-backfill version.ontology_id IS NOT NULL
  params={"attribution_source": "legacy_unmapped", ...}
[DRY-RUN] 未写库；确认计划后加 --apply 执行。
```

## 审计事件

每次 `--apply` 必须在同一个事务里写一条 `platform.ontology_event`：

| 字段 | 值 |
| --- | --- |
| `version_id` | `data-fix:<batch_id>`（合成 id；该列无外键，真实版本 id 是 `ont-<12 hex>`） |
| `action` | `data-fix` |
| `actor` | `--actor` / `$COA_ACTOR` / `用户@主机` |
| `reason` | `scripts/data-fix/xxx.py batch=<id> affected=<json>` |
| `payload.script` | 脚本相对路径 |
| `payload.batchId` | 批次 id |
| `payload.affectedRows` | 每张表实际影响行数 |
| `payload.plannedRows` | 每张表 dry-run 预测行数 |
| `payload.params` | 参数摘要（批次、标记值、id 集合、脱敏 DSN、迁移清单等） |
| `payload.beforeCounts` / `afterCounts` | 每张表执行前后总行数 |
| `payload.dsn` | 脱敏后的连接串（密码替换为 `***`） |
| `payload.host` / `pid` / `startedAt` / `finishedAt` | 执行位置与时间 |

`prev_event` / `hash` 复刻 `platform_core.facts.event_hash` 与
`ontology_pg._append_event` 的链式规则，后续 `verify_ontology_records` 能继续校验。

**没有写事件就算失败**：`audit.append_audit_event` 会回读事件并核对 hash；任何一步失败都抛
`AuditWriteError`，整个事务回滚——数据改动不生效，脚本非零退出。

## 回滚自检

`selfcheck_rollback.py` 在一次性测试库上真实验证「事件写失败 → 整体回滚」：

```powershell
python scripts/data-fix/selfcheck_rollback.py `
  --dsn postgresql://platform:platform_dev@127.0.0.1:55944/datafix_selfcheck
```

它会：

1. 建最小化的 `platform.ontology_event` 和 `datafix_selfcheck.items`；
2. 给 `ontology_event` 装一个必然报错的 BEFORE INSERT 触发器，执行 apply，断言抛
   `AuditWriteError` 且 items 一行未改、事件一行未留；
3. 删触发器后重跑，断言 3 行全部改掉且恰好 1 条 `action='data-fix'` 事件，payload 字段
   齐全、hash 与 `platform_core` 规则一致；
4. dry-run 再跑，断言 items 与事件数都不变。

安全闸：必须显式 `--dsn`；库名必须含 `test` / `selfcheck` / `datafix`；拒绝
`platform` / `serve_local` / `postgres` / `realcorpus`。
