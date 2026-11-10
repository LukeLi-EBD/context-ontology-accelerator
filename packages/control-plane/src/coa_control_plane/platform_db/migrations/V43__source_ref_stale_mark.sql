-- V43: 值级溯源档1 悬空引用标记表入库
--
-- 背景：platform.source_ref_stale_mark 由 2026-11-07 的值级溯源档1 直接 DDL 建在
-- 8080（144 行标记），当时 SQL 目录止于 V42。按迁移重建会丢表丢标记，故本迁移
-- 把既有 DDL 原样登记。字段、约束、索引与 8080 现存表逐字段一致。
--
-- 语义：append-only。只插入，不删除；撤销一条标记用 active=true 使其失效，
-- active=false（默认）表示“当前仍视为已失效”。source_ref 唯一，重复写入用
-- ON CONFLICT DO NOTHING（见 mark_stale.sql）。
--
-- 幂等：CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS；对已有 8080
-- 执行为空操作（表已存在、144 行不变）。

CREATE TABLE IF NOT EXISTS platform.source_ref_stale_mark (
  mark_id      bigserial PRIMARY KEY,
  source_ref   text NOT NULL,
  ref_kind     text NOT NULL,
  metric_id    text,
  cause        text NOT NULL CHECK (cause IN (
                 'target_recomputed','metric_zero_observation','target_removed','unknown')),
  detected_by  text NOT NULL,
  marked_at    timestamptz NOT NULL DEFAULT now(),
  note         text,
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  active       boolean NOT NULL DEFAULT false,
  CONSTRAINT source_ref_stale_mark_ref_uniq UNIQUE (source_ref)
);

CREATE INDEX IF NOT EXISTS source_ref_stale_mark_metric_idx
  ON platform.source_ref_stale_mark (metric_id);

CREATE INDEX IF NOT EXISTS source_ref_stale_mark_cause_idx
  ON platform.source_ref_stale_mark (cause, marked_at DESC);
