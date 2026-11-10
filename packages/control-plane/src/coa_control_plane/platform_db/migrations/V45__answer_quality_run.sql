-- V45: 质量运行单次记录（F86 收口）
--
-- 背景：/answer/quality 每次跑完黄金集就把结果丢在响应里，历史无法回补。
-- P12（趋势图 + 两周积累）未批准，这里只落“一次运行一行”的原始记录：
-- 指标列 + detail jsonb（分层覆盖 / 拒答分布 / 断链明细）。不做视图、不做趋势。
--
-- 口径：run 指一次完整黄金集评估（caseId 下钻不落表）。run_id 由 API 生成，
-- 不依赖自增，便于日志与响应里的 runId 直接对上。
--
-- 幂等：CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS。

CREATE TABLE IF NOT EXISTS platform.answer_quality_run (
  run_id                    text PRIMARY KEY,
  ran_at                    timestamptz NOT NULL DEFAULT now(),
  strategy                  text NOT NULL CHECK (strategy IN ('lexical', 'vector', 'hybrid')),
  golden_set                text NOT NULL,
  evaluated                 integer NOT NULL,
  passed                    integer NOT NULL,
  failed                    integer NOT NULL,
  pass_rate                 numeric(6,4) NOT NULL,
  cases_with_citations      integer NOT NULL,
  citation_coverage_rate    numeric(6,4) NOT NULL,
  citations                 integer NOT NULL,
  resolvable_citations      integer NOT NULL,
  citation_resolvable_rate  numeric(6,4) NOT NULL,
  broken_links              integer NOT NULL,
  broken_link_rate          numeric(6,4) NOT NULL,
  regression                boolean NOT NULL,
  detail                    jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS answer_quality_run_ran_at_idx
  ON platform.answer_quality_run (ran_at DESC);
