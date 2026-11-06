-- V42: 生命周期/证据“孤儿行”的旁路标记表（append-only）。
--
-- 背景：测试清理（test_g01 / smoke_s1）删除 ontology_version 行，但
-- ontology_lifecycle_transition 与 ontology_evidence 保留下来，形成悬空行。
-- 约束：历史行不可删除、不可改写，只能在旁路表追加“孤儿标记”。
--
-- 集成方须知：
--   1) 本文件只定义结构，不对共享库执行；由集成方按既定顺序（V41 之后）应用，
--      并登记到 metadata_pg.MIGRATIONS（当前代码支持到 V34，V35+ 由集成方管理）。
--   2) 标记行只增不改；重复扫描使用 ON CONFLICT (entity_kind, entity_ref) DO NOTHING。
--   3) 审计链（/ontology/verify）校验必须忽略本表，不能据此过滤事件链。
--   4) 业务读侧（transition/evidence 列表）按需 NOT EXISTS 过滤，默认保留可追溯性。

CREATE TABLE IF NOT EXISTS platform.ontology_orphan_mark (
  mark_id      bigserial PRIMARY KEY,
  entity_kind  text NOT NULL
               CHECK (entity_kind IN ('lifecycle_transition', 'evidence')),
  entity_ref   text NOT NULL,          -- transition.seq 或 evidence.evidence_id（文本化）
  version_id   text NOT NULL,          -- 已被删除/不存在的版本 id
  cause        text NOT NULL
               CHECK (cause IN (
                 'test_cleanup_version_deleted',  -- test_g01 等 teardown DELETE
                 'smoke_direct_sql',              -- smoke_s1 直接 SQL 恢复/删除
                 'unknown'
               )),
  detected_by  text NOT NULL,          -- 标记来源（脚本/session 标识）
  marked_at    timestamptz NOT NULL DEFAULT now(),
  note         text,
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT ontology_orphan_mark_target_uniq UNIQUE (entity_kind, entity_ref)
);

CREATE INDEX IF NOT EXISTS ontology_orphan_mark_version_idx
  ON platform.ontology_orphan_mark (version_id);

CREATE INDEX IF NOT EXISTS ontology_orphan_mark_kind_idx
  ON platform.ontology_orphan_mark (entity_kind, marked_at DESC);

COMMENT ON TABLE platform.ontology_orphan_mark IS
  '悬空 transition/evidence 的只增标记；原表行永不删除，标记可用于读侧过滤与统计';
COMMENT ON COLUMN platform.ontology_orphan_mark.entity_ref IS
  'lifecycle_transition.seq 或 evidence.evidence_id，按 entity_kind 解释';
COMMENT ON COLUMN platform.ontology_orphan_mark.cause IS
  '已知成因；未知成因不得猜测，使用 unknown 并在 note 写明证据';
