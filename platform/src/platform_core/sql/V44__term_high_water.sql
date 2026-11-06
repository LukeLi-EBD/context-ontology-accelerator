-- O-05 vocab guard: high-water mark of the *effective* term set.
-- 迁移登记（唯一权威：doc/_design/54 §2.2）：V44 = 术语高水位表，归属
-- `feat/terms-gate`（O-05/O-08 门禁线）；V41 指标观测 synthetic、V42 悬空行标记、
-- V43 字典绑定均由各自分支按序合入，本线不得占用。
--
-- The guard must survive the future decoupling of the term layer from the
-- T-Box version graph, so it is stored here as a pointer-independent count
-- (and not inferred from the current version graph at check time). Publish
-- only raises the mark; it never lowers it.
CREATE TABLE IF NOT EXISTS platform.term_high_water (
    scope text PRIMARY KEY,
    concepts_in_scheme integer NOT NULL,
    aliases integer NOT NULL,
    version_id text,
    graph_iri text,
    updated_at timestamptz NOT NULL DEFAULT now()
);
