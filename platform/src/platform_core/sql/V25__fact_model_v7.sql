-- V25: fact model v7 -- fill the 52 blocked_semantics metrics from business meaning.
--
-- Design rules kept from V22-V24:
--   * CREATE TABLE IF NOT EXISTS / ALTER TABLE ... ADD COLUMN IF NOT EXISTS, so the
--     migration is re-entrant on both fresh and existing databases;
--   * one independent fact table per real business entity, no per-metric orphan table;
--   * every new table/column carries COMMENT text with four labels:
--       business_meaning / why_this_way / basis (regulatory|industry|inferred) /
--       inference_note (only when basis = inferred);
--   * no business values are seeded here; only schema, comments and bindings.
--
-- Target: 44 of the 52 blocked_semantics metrics become structurally computable.
-- The remaining 8 (FIN-BANK-019/020/021/036, FIN-INS-012/022/023, CUST-004) get an
-- explicit reason + decision owner in metric_definition.missing / decision_owner.

-- =====================================================================
-- 1. BANK: extend the account snapshot into a period-movement fact
-- =====================================================================

ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS period_start date;
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS risk_class_start text
    CHECK (risk_class_start IN ('normal', 'special', 'substandard', 'doubtful', 'loss'));
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS risk_class_end text
    CHECK (risk_class_end IN ('normal', 'special', 'substandard', 'doubtful', 'loss'));
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS balance_start numeric CHECK (balance_start >= 0);
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS balance_end numeric CHECK (balance_end >= 0);
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS period_decrease_amount numeric
    CHECK (period_decrease_amount >= 0);
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS dpd_start integer CHECK (dpd_start IS NULL OR dpd_start >= 0);
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS dpd_end integer CHECK (dpd_end IS NULL OR dpd_end >= 0);
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS first_payment_due_date date;
ALTER TABLE platform.bank_loan_account
  ADD COLUMN IF NOT EXISTS first_payment_default_flag boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN platform.bank_loan_account.period_start IS
  'business_meaning: 该行所描述报告期的起始日（期初观察日）。'
  'why_this_way: 迁徙矩阵必须同时看到期初与期末，单靠 as_of 只能表达期末；'
  'period_start 与 as_of 成对保存，避免再建一张按期间重复的账户表。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_loan_account.risk_class_start IS
  'business_meaning: 报告期初该账户的五级分类。'
  'why_this_way: 迁徙率分子分母都按“期初分类”分组，期初分类必须与期末分类同表可比。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_loan_account.risk_class_end IS
  'business_meaning: 报告期末该账户的五级分类。'
  'why_this_way: 迁徙率=期初某类中期末落入更差类的余额/期初该类余额；期末分类是判定迁徙方向的唯一依据。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_loan_account.balance_start IS
  'business_meaning: 报告期初该账户的贷款本金余额。'
  'why_this_way: 监管迁徙矩阵以“期初余额”为观察基数，分子取迁徙账户的期初余额，'
  '分母取期初余额减期间减少，二者同基数才不会重复扣减。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_loan_account.balance_end IS
  'business_meaning: 报告期末该账户的贷款本金余额。'
  'why_this_way: 用于核对期初减期间减少加新增后是否等于期末；不直接进入 013–016 的公式。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_loan_account.period_decrease_amount IS
  'business_meaning: 报告期内该账户期初余额的减少额，含正常收回、不良处置、核销。'
  'why_this_way: 迁徙率分母按期初余额扣除期间减少，否则已结清/核销账户会虚增分母。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_loan_account.dpd_start IS
  'business_meaning: 报告期初该账户的逾期天数（自然日，未逾期为 0）。'
  'why_this_way: 017/018 以“期初 DPD 区间”定义 cohort，必须与期末 DPD 同表保存。'
  'basis: industry';
COMMENT ON COLUMN platform.bank_loan_account.dpd_end IS
  'business_meaning: 报告期末该账户的逾期天数（自然日，未逾期为 0）。'
  'why_this_way: 期末 DPD 决定是否滚入下一档（30→60、60→90）。'
  'basis: industry';
COMMENT ON COLUMN platform.bank_loan_account.first_payment_due_date IS
  'business_meaning: 该账户首个还款期的应还款日。'
  'why_this_way: 033 首逾率按“首个还款期”形成 vintage，必须有一个明确的业务时间列落窗。'
  'basis: industry';
COMMENT ON COLUMN platform.bank_loan_account.first_payment_default_flag IS
  'business_meaning: 首个还款期是否发生逾期（首期应还而未足额还）。'
  'why_this_way: 首逾标志在首个还款期一次性计算后稳定保存，避免每次重算历史。'
  'basis: inferred; '
  'inference_note: 定义只写“首个还款期即发生逾期”，未规定宽限日与部分还款阈值；'
  '这里取“首个还款期应还日次日起未足额还款”为真，宽限日按合同默认 0 天，'
  '被反驳点：若合同允许 3 天宽限，需把宽限日加入标志计算。';

ALTER TABLE platform.ins_claim_case
  ADD COLUMN IF NOT EXISTS filing_date date;
COMMENT ON COLUMN platform.ins_claim_case.filing_date IS
  'business_meaning: 理赔立案日（报案被正式受理并立案的日期）。'
  'why_this_way: 018 报案立案率的分子按立案事件日落窗，不能拿报案日或已决日代替。'
  'basis: inferred; '
  'inference_note: 定义把“立案数量”与“有效报案数量”并列，但原表只有 report/decision 两个时点；'
  '推敲路径：立案是报案之后、查勘之前的独立事件，故新增 filing_date 承载；'
  '被反驳点：若理赔系统把“立案”等同“报案受理”，则 filing_date 应等于 report_date。';

-- =====================================================================
-- 2. BANK: institution-level regulatory report facts
-- =====================================================================

CREATE TABLE IF NOT EXISTS platform.bank_provision_snapshot (
  institution       text NOT NULL,
  as_of             date NOT NULL,
  provision_balance numeric NOT NULL CHECK (provision_balance >= 0),
  npl_balance       numeric NOT NULL CHECK (npl_balance >= 0),
  loan_balance      numeric NOT NULL CHECK (loan_balance >= 0),
  data_source       text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture           boolean NOT NULL DEFAULT false,
  created_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_provision_snapshot_key UNIQUE (institution, as_of, data_source)
);
COMMENT ON TABLE platform.bank_provision_snapshot IS
  'business_meaning: 贷款拨备报表快照，一行=一个法人机构在一个报告期末的贷款损失准备、'
  '不良贷款余额与各项贷款余额。'
  'why_this_way: 拨备覆盖率(022)与贷款拨备率(023)共用同一组监管报表余额，同一 as_of 一次取值，'
  '不拆成两张单指标表。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_provision_snapshot.provision_balance IS
  'business_meaning: 贷款损失准备余额（已计提未核销的准备金）。'
  'why_this_way: 022/023 的分子都是它；监管报表按报告期末余额填报，不是期间计提额。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_provision_snapshot.npl_balance IS
  'business_meaning: 不良贷款余额（次级+可疑+损失）。'
  'why_this_way: 022 分母必须与准备金同一报告期末，不能从五级分类明细临时汇总，避免口径串期。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_provision_snapshot.loan_balance IS
  'business_meaning: 各项贷款余额（含贷款、贸易融资、票据融资、融资租赁、买入返售、透支、垫款；不含一般风险准备）。'
  'why_this_way: 023 分母按监管“各项贷款”口径一次填报，避免用客户贷款余额漏项。'
  'basis: regulatory';

CREATE TABLE IF NOT EXISTS platform.bank_concentration_stat (
  institution                text NOT NULL,
  as_of                      date NOT NULL,
  capital_balance            numeric CHECK (capital_balance >= 0),
  capital_net                numeric CHECK (capital_net >= 0),
  tier1_capital_net          numeric CHECK (tier1_capital_net >= 0),
  max_single_customer_loan   numeric CHECK (max_single_customer_loan >= 0),
  max_single_customer_exposure numeric CHECK (max_single_customer_exposure >= 0),
  max_group_exposure         numeric CHECK (max_group_exposure >= 0),
  max_group_credit           numeric CHECK (max_group_credit >= 0),
  total_related_exposure     numeric CHECK (total_related_exposure >= 0),
  data_source                text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture                    boolean NOT NULL DEFAULT false,
  created_at                 timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_concentration_stat_key UNIQUE (institution, as_of, data_source)
);
COMMENT ON TABLE platform.bank_concentration_stat IS
  'business_meaning: 集中度监管报表快照，一行=一个法人机构在一个报告期末的资本与各类最大暴露/授信。'
  'why_this_way: 025–030 需要“按客户/关联组取 max 再除以法人资本”，单方言编译器不做跨行排序，'
  '所以把监管报表已汇总的最大值落成机构级事实；一行一机构一报告期，避免逐客户明细重复。'
  'basis: inferred; '
  'inference_note: 推敲路径：监管报送表本身按“最大一家/一组”填报，故事实层直接承载 max；'
  '被反驳点：若要做客户级集中度排行，需要客户暴露明细表与排序执行器，本表不提供服务。';
COMMENT ON COLUMN platform.bank_concentration_stat.capital_balance IS
  'business_meaning: 商业银行资本余额（025 分母）。'
  'why_this_way: 025 原文用“资本余额”，与 026–030 的“资本净额/一级资本净额”不同，故单列。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_concentration_stat.capital_net IS
  'business_meaning: 资本净额。'
  'why_this_way: 028 单一集团客户授信集中度、029 全部关联度原文分母均为资本净额。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_concentration_stat.tier1_capital_net IS
  'business_meaning: 一级资本净额。'
  'why_this_way: 026/027/030 原文分母为一级资本净额；与资本净额分开保存，避免混用。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_concentration_stat.max_single_customer_loan IS
  'business_meaning: 对最大单一借款人的贷款余额。'
  'why_this_way: 025 分子是“对同一借款人的贷款余额”，报表只保留最大值。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_concentration_stat.max_single_customer_exposure IS
  'business_meaning: 对最大单一非同业客户的风险暴露（含表内外）。'
  'why_this_way: 026/030 分子按风险暴露而非贷款余额；与 025 的贷款余额分开。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_concentration_stat.max_group_exposure IS
  'business_meaning: 对最大一组非同业关联客户的风险暴露。'
  'why_this_way: 027 的分子按关联组去重后的暴露；单列以区别于单一客户。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_concentration_stat.max_group_credit IS
  'business_meaning: 最大一家集团客户的授信总额。'
  'why_this_way: 028 原文是“授信总额”而非风险暴露或贷款余额。'
  'basis: regulatory';
COMMENT ON COLUMN platform.bank_concentration_stat.total_related_exposure IS
  'business_meaning: 全部关联方授信总额。'
  'why_this_way: 029 是全部关联方汇总值，不是最大值。'
  'basis: regulatory';

-- =====================================================================
-- 3. INSURANCE: period underwriting/claim/expense statistics
-- =====================================================================

CREATE TABLE IF NOT EXISTS platform.ins_underwriting_stat (
  institution                text NOT NULL,
  product                    text NOT NULL,
  channel                    text NOT NULL DEFAULT '-',
  business_line              text NOT NULL
    CHECK (business_line IN ('property', 'life', 'health', 'other')),
  period_start               date NOT NULL,
  period_end                 date NOT NULL,
  signed_premium             numeric NOT NULL DEFAULT 0,
  plan_premium               numeric NOT NULL DEFAULT 0 CHECK (plan_premium >= 0),
  collected_premium          numeric NOT NULL DEFAULT 0,
  ceded_premium              numeric NOT NULL DEFAULT 0 CHECK (ceded_premium >= 0),
  retained_premium           numeric NOT NULL DEFAULT 0 CHECK (retained_premium >= 0),
  unearned_reserve_change    numeric NOT NULL DEFAULT 0,
  earned_premium             numeric NOT NULL DEFAULT 0,
  paid_claims                numeric NOT NULL DEFAULT 0 CHECK (paid_claims >= 0),
  claim_reserve_change       numeric NOT NULL DEFAULT 0,
  reinsurance_recoverable    numeric NOT NULL DEFAULT 0 CHECK (reinsurance_recoverable >= 0),
  reinsurance_reserve_change numeric NOT NULL DEFAULT 0,
  long_term_reserve_change   numeric NOT NULL DEFAULT 0,
  expense_total              numeric NOT NULL DEFAULT 0 CHECK (expense_total >= 0),
  commission_expense         numeric NOT NULL DEFAULT 0 CHECK (commission_expense >= 0),
  surrender_amount           numeric NOT NULL DEFAULT 0 CHECK (surrender_amount >= 0),
  beginning_reserve_total    numeric NOT NULL DEFAULT 0 CHECK (beginning_reserve_total >= 0),
  policyholder_deposit_beginning numeric NOT NULL DEFAULT 0
    CHECK (policyholder_deposit_beginning >= 0),
  separate_account_beginning numeric NOT NULL DEFAULT 0
    CHECK (separate_account_beginning >= 0),
  current_term_premium       numeric NOT NULL DEFAULT 0 CHECK (current_term_premium >= 0),
  data_source                text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture                    boolean NOT NULL DEFAULT false,
  created_at                 timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ins_underwriting_stat_key
    UNIQUE (institution, product, channel, business_line, period_start, period_end, data_source)
);
ALTER TABLE platform.ins_underwriting_stat
  ADD COLUMN IF NOT EXISTS reinsurance_reserve_change numeric NOT NULL DEFAULT 0;
COMMENT ON COLUMN platform.ins_underwriting_stat.reinsurance_reserve_change IS
  'business_meaning: 摊回保险责任准备金变动（本期摊回−转回，可为负）。'
  'why_this_way: 009 再保后已赚保费=已赚−分出+摊回责任准备金变动，必须单列才能与摊回赔款区分。'
  'basis: regulatory';

COMMENT ON TABLE platform.ins_underwriting_stat IS
  'business_meaning: 保险业务期间统计事实，一行=一个机构×产品×渠道×业务线在一个报告期的'
  '保费/准备金/赔付/费用组成项。'
  'why_this_way: 综合赔付率、综合成本率、费用率、退保率的分子分母必须同期间、同口径可加总；'
  '把组成项拆到列而不是拆成多张单指标表，12 条指标共用一张事实。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.product IS
  'business_meaning: 险种/产品代码；无产品归属时填 ''-''。'
  'why_this_way: 008/013/027 需要限定财产险，product 与 business_line 同时保存便于下钻。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_underwriting_stat.channel IS
  'business_meaning: 销售渠道代码；无渠道归属时填 ''-''。'
  'why_this_way: 026 渠道费用率与 028 手续费占比按渠道分组，''-'' 表示该行不参与渠道口径。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_underwriting_stat.business_line IS
  'business_meaning: 业务大类：property 财产险 / life 寿险 / health 短期健康险 / other。'
  'why_this_way: 008/011/013/027 限定财产险、009 限定短期健康险、019/020 限定长期险，'
  '用业务大类过滤比用具体产品码更稳定。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_underwriting_stat.period_start IS
  'business_meaning: 统计期起始日。'
  'why_this_way: 期间事实必须能还原“同期”；period_end 用于落窗，period_start 用于核对。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.period_end IS
  'business_meaning: 统计期截止日，也是绑定窗口的业务时间列。'
  'why_this_way: 编译器按 period_end 落窗后对组成项求和，天然支持月/季/年多粒度。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.signed_premium IS
  'business_meaning: 签单保费（含已起保与未起保，批增批减调整，退保不冲减）。'
  'why_this_way: 006 计划达成、026 渠道费用率、028 手续费占比的分母都要求“签单/保费收入”口径。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_underwriting_stat.plan_premium IS
  'business_meaning: 计划保费（同期、同口径、锁定计划版本）。'
  'why_this_way: 006 分母只能来自预算/计划系统，不能由实际保费推算。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_underwriting_stat.collected_premium IS
  'business_meaning: 实收保费=本期保费收款−本期批退/退费（收付实现制）。'
  'why_this_way: 003 与 006 的实际完成额都按实收口径可加总；批退跨期冲减留在本列，不拆表。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_underwriting_stat.ceded_premium IS
  'business_meaning: 分出保费。'
  'why_this_way: 009 再保后已赚、010 已赚保费都要从保费中扣分出。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.retained_premium IS
  'business_meaning: 自留保费=原保险保费−分出保费。'
  'why_this_way: 008/011/013/027 的分母都从自留保费出发，避免每次用两张表相减。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.unearned_reserve_change IS
  'business_meaning: 未到期责任准备金变动/提转差（本期提取−本期转回，可为负）。'
  'why_this_way: 自留保费扣未到期准备金变动才等于当期承保口径；允许负值以支持转回。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.earned_premium IS
  'business_meaning: 已赚保费。'
  'why_this_way: 009 再保后已赚、010 财政部口径直接使用已赚保费。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.paid_claims IS
  'business_meaning: 赔付支出（本期实际支付赔款）。'
  'why_this_way: 008/009/010/011/013 的分子都从赔付支出出发。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.claim_reserve_change IS
  'business_meaning: 未决赔款准备金变动（本期提取−转回，可为负）。'
  'why_this_way: 综合赔付率必须含未决变动，否则跨期赔付被低估。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.reinsurance_recoverable IS
  'business_meaning: 摊回赔款/摊回保险责任准备金。'
  'why_this_way: 008/009/011/013 要求“扣摊回”，故以正数保存、公式中相减。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.long_term_reserve_change IS
  'business_meaning: 长期财产险责任准备金提转差。'
  'why_this_way: 013 旧规两年赔付率的分子分母都要加回长期责任准备金提转差。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.expense_total IS
  'business_meaning: 费用合计=业务及管理费+手续费佣金+分保费用+税金等。'
  'why_this_way: 011 综合成本率、026 渠道费用率、027 综合费用率的分子统一用费用合计。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.commission_expense IS
  'business_meaning: 手续费及佣金支出。'
  'why_this_way: 028 单独衡量渠道成本结构，不能直接复用费用合计。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_underwriting_stat.surrender_amount IS
  'business_meaning: 退保金（长期险及投资型业务退保给付）。'
  'why_this_way: 019/020 的分子都是退保金，与赔付支出分开保存。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.beginning_reserve_total IS
  'business_meaning: 期初长期险责任准备金（019 为本期期初；020 为上年末）。'
  'why_this_way: 退保率分母含期初余额，不能只用本期保费。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.policyholder_deposit_beginning IS
  'business_meaning: 保户储金及投资款期初余额。'
  'why_this_way: 019 现行口径的分母还要加保户储金及投资款，单列避免与责任准备金混算。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.separate_account_beginning IS
  'business_meaning: 独立账户负债期初余额。'
  'why_this_way: 019 投资型业务退保率的分母包含独立账户负债。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_underwriting_stat.current_term_premium IS
  'business_meaning: 本年度签单保费（019）/本年长期险保费收入（020）。'
  'why_this_way: 退保率分母的“本年保费”与签单/实收口径不同，单列以便两种退保率并存。'
  'basis: regulatory';

CREATE TABLE IF NOT EXISTS platform.ins_claim_reserve_snapshot (
  claim_no          text NOT NULL,
  institution       text,
  product           text,
  as_of             date NOT NULL,
  reported_reserve  numeric NOT NULL DEFAULT 0 CHECK (reported_reserve >= 0),
  ibnr_reserve      numeric NOT NULL DEFAULT 0 CHECK (ibnr_reserve >= 0),
  expense_reserve   numeric NOT NULL DEFAULT 0 CHECK (expense_reserve >= 0),
  case_status       text NOT NULL CHECK (case_status IN ('open', 'closed')),
  data_source       text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture           boolean NOT NULL DEFAULT false,
  created_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ins_claim_reserve_snapshot_key UNIQUE (claim_no, as_of, data_source)
);
COMMENT ON TABLE platform.ins_claim_reserve_snapshot IS
  'business_meaning: 未决赔款准备金评估快照，一行=一个赔案在一个评估日的三类准备金与案件状态。'
  'why_this_way: 未决准备金是时点余额，不能由赔案事件累加；014 与 016 共用同一张评估表。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_claim_reserve_snapshot.reported_reserve IS
  'business_meaning: 已发生已报案未决赔款准备金。'
  'why_this_way: 014 分子三项之一；与 IBNR 分开以保留审计口径。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_claim_reserve_snapshot.ibnr_reserve IS
  'business_meaning: 已发生未报案（IBNR）准备金。'
  'why_this_way: 014 明确要求含 IBNR，不能只取已报案部分。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_claim_reserve_snapshot.expense_reserve IS
  'business_meaning: 理赔费用准备金。'
  'why_this_way: 014 明确含理赔费用准备金。'
  'basis: regulatory';
COMMENT ON COLUMN platform.ins_claim_reserve_snapshot.case_status IS
  'business_meaning: 评估日案件状态：open 未决 / closed 已决。'
  'why_this_way: 016 分母只数未决件，014 只汇总未决余额。'
  'basis: regulatory';

CREATE TABLE IF NOT EXISTS platform.ins_persistence_stat (
  institution           text NOT NULL,
  product               text NOT NULL,
  channel               text NOT NULL DEFAULT '-',
  cohort_period         date NOT NULL,
  valuation_basis       text NOT NULL
    CHECK (valuation_basis IN ('grace', 'natural', 'vehicle_renewal')),
  renewal_year          integer NOT NULL CHECK (renewal_year >= 1),
  first_year_premium    numeric NOT NULL DEFAULT 0 CHECK (first_year_premium >= 0),
  renewed_premium       numeric NOT NULL DEFAULT 0 CHECK (renewed_premium >= 0),
  due_vehicle_count     integer NOT NULL DEFAULT 0 CHECK (due_vehicle_count >= 0),
  renewed_vehicle_count integer NOT NULL DEFAULT 0 CHECK (renewed_vehicle_count >= 0),
  data_source           text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture               boolean NOT NULL DEFAULT false,
  created_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ins_persistence_stat_key
    UNIQUE (institution, product, channel, cohort_period, valuation_basis,
            renewal_year, data_source)
);
COMMENT ON TABLE platform.ins_persistence_stat IS
  'business_meaning: 保单继续/续保 cohort 统计，一行=一批新单在一个评价口径下第 N 个保单年度的'
  '首年实收保费、续期实收保费或车辆续保件数。'
  'why_this_way: 继续率是 cohort 口径，编译器不做逐单跨期 join；把 cohort 已汇总值落成事实，'
  '宽限期/自然月两口径并列而不互相覆盖。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.cohort_period IS
  'business_meaning: 承保 cohort 起始月（取当月 1 日）。'
  'why_this_way: 022/023 的观察对象是“评价期前溯 12/24 个月承保的新单”，cohort_period 是唯一业务时间列。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.valuation_basis IS
  'business_meaning: 评价口径：grace 宽限期 / natural 自然月 / vehicle_renewal 车险续保队列。'
  'why_this_way: 022-v1/v2、023-v1/v2 必须并列可追溯，不能合并成一个“继续率”列。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.renewal_year IS
  'business_meaning: 观察的是第几个保单年度（2=13 个月继续率，3=25 个月继续率；车险为 1）。'
  'why_this_way: 同一 cohort 的 13/25 个月继续率放在同一表按 renewal_year 区分。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.first_year_premium IS
  'business_meaning: 该 cohort 首个保单年度实收规模保费（按保单号去重，已剔除趸交/撤单/终止等）。'
  'why_this_way: 022/023 的分母固定为 cohort 首年实收保费。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.renewed_premium IS
  'business_meaning: 该 cohort 第 N 个保单年度首期实收规模保费（宽限或自然月口径）。'
  'why_this_way: 继续率分子；与 first_year_premium 同 cohort 同口径。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.due_vehicle_count IS
  'business_meaning: 到期应续保车辆数（按车辆/VIN 去重，含脱保车辆）。'
  'why_this_way: 024 车险续保率分母。'
  'basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.renewed_vehicle_count IS
  'business_meaning: 到期车辆中实际在本司续保的车辆数。'
  'why_this_way: 024 车险续保率分子。'
  'basis: industry';

-- =====================================================================
-- 4. CUSTOMER: behavior / cohort / AUM facts
-- =====================================================================

CREATE TABLE IF NOT EXISTS platform.cust_behavior_snapshot (
  customer_no              text NOT NULL,
  institution              text,
  as_of                    date NOT NULL,
  last_behavior_date       date,
  days_since_last_behavior integer CHECK (days_since_last_behavior IS NULL
    OR days_since_last_behavior >= 0),
  last_txn_date            date,
  days_since_proxy_event   integer CHECK (days_since_proxy_event IS NULL
    OR days_since_proxy_event >= 0),
  data_source              text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture                  boolean NOT NULL DEFAULT false,
  created_at               timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cust_behavior_snapshot_key UNIQUE (customer_no, as_of, data_source)
);
COMMENT ON TABLE platform.cust_behavior_snapshot IS
  'business_meaning: 客户行为快照，一行=一个客户在一个观察日的最近有效行为、最近交易与代理事件距今天数。'
  'why_this_way: RFM-R 是“基准日−最近行为日”的日期差，编译器不做日期函数；按月末预算成快照。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_behavior_snapshot.last_behavior_date IS
  'business_meaning: 最近一次有效行为日（交易/还款/缴费/保单生效）。'
  'why_this_way: 保留原始日期，便于核对 days_since_last_behavior。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_behavior_snapshot.days_since_last_behavior IS
  'business_meaning: 基准日−最近一次有效行为日，未发生为 NULL。'
  'why_this_way: 001 直接取该列；NULL 不置 0，避免把“从未行为”误判为“今天活跃”。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_behavior_snapshot.last_txn_date IS
  'business_meaning: 最近一次有效交易日期（剔除退款）。'
  'why_this_way: 005 用它判断客户是否“无交易”，从而切换到代理事件口径。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_behavior_snapshot.days_since_proxy_event IS
  'business_meaning: 无交易客户的代理事件（注册/开卡/首单/保单生效）距基准日天数。'
  'why_this_way: 005 的 R 用代理事件日；与 days_since_last_behavior 分开，避免两种口径混算。'
  'basis: industry';

CREATE TABLE IF NOT EXISTS platform.cust_cohort_stat (
  cohort_key             text NOT NULL,
  institution            text NOT NULL,
  cohort_month           date NOT NULL,
  as_of                  date NOT NULL,
  cohort_customers       integer NOT NULL DEFAULT 0 CHECK (cohort_customers >= 0),
  retained_customers     integer NOT NULL DEFAULT 0 CHECK (retained_customers >= 0),
  active_customers       integer NOT NULL DEFAULT 0 CHECK (active_customers >= 0),
  prior_month_active     integer NOT NULL DEFAULT 0 CHECK (prior_month_active >= 0),
  active_and_prior_month integer NOT NULL DEFAULT 0 CHECK (active_and_prior_month >= 0),
  data_source            text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture                boolean NOT NULL DEFAULT false,
  created_at             timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cust_cohort_stat_key UNIQUE (cohort_key, as_of, data_source)
);
COMMENT ON TABLE platform.cust_cohort_stat IS
  'business_meaning: 客户留存 cohort 统计，一行=一个获客 cohort 在一个观察日的初始/留存/活跃户数。'
  'why_this_way: 留存率与流失率是 cohort 口径，编译器不做逐客户跨期 join；预先按 cohort 聚合。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_cohort_stat.cohort_key IS
  'business_meaning: cohort 唯一键（机构|获客月），用于按 cohort 输出。'
  'why_this_way: 编译器只按一个实体列分组；cohort_key 把“机构×获客月”组合成单列实体键。'
  'basis: inferred; '
  'inference_note: 推敲路径：006/007 的 grain 是 cohort，而编译器仅支持单实体列，故用组合键；'
  '被反驳点：若下游要求分别按机构、获客月下钻，需要拆成两列并新增 cohort 执行器。';
COMMENT ON COLUMN platform.cust_cohort_stat.cohort_customers IS
  'business_meaning: cohort 初始客户数（起始月满足激活/首单条件，按客户号去重）。'
  'why_this_way: 006/007 的共同分母。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_cohort_stat.retained_customers IS
  'business_meaning: 第 N 月仍活跃的 cohort 客户数。'
  'why_this_way: 006 留存率分子。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_cohort_stat.active_customers IS
  'business_meaning: 观察窗口内发生过有效行为的 cohort 客户数。'
  'why_this_way: 007 流失率分子=cohort_customers−active_customers。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_cohort_stat.prior_month_active IS
  'business_meaning: 上月活跃客户数（按客户号去重，月末活跃口径）。'
  'why_this_way: 008 月度滚动留存率的分母。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_cohort_stat.active_and_prior_month IS
  'business_meaning: 本月活跃且上月也活跃的客户数。'
  'why_this_way: 008 月度滚动留存率的分子。'
  'basis: industry';

CREATE TABLE IF NOT EXISTS platform.cust_aum_snapshot (
  customer_no     text NOT NULL,
  institution     text,
  product_type    text NOT NULL DEFAULT '-',
  as_of           date NOT NULL,
  aum             numeric NOT NULL DEFAULT 0 CHECK (aum >= 0),
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cust_aum_snapshot_key UNIQUE (customer_no, product_type, as_of, data_source)
);
COMMENT ON TABLE platform.cust_aum_snapshot IS
  'business_meaning: 客户 AUM 快照，一行=一个客户×产品大类在一个观察日的可计入资产市值合计。'
  'why_this_way: AUM 跨存款/理财/基金/保险/国债，编译器不能跨表汇总；按客户×产品大类预聚合，'
  '既支持客户级时点 AUM，也支持按自然日计算日均。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_aum_snapshot.product_type IS
  'business_meaning: 产品大类（deposit/wealth/fund/insurance/bond 等）；无归属填 ''-''。'
  'why_this_way: 012 要求按账户去重避免双计，产品大类是去重与下钻的最小维度。'
  'basis: industry';
COMMENT ON COLUMN platform.cust_aum_snapshot.aum IS
  'business_meaning: 该客户该产品大类在该观察日的可计入资产市值。'
  'why_this_way: 012 时点值与 013 日均值的唯一数值来源。'
  'basis: industry';

-- ---- dimension/key column comments (same four labels) ----
COMMENT ON COLUMN platform.bank_provision_snapshot.institution IS
  'business_meaning: 法人机构代码，报表主体。'
  'why_this_way: 022/023 是机构级监管指标，实体列必须与报表主体一致。basis: regulatory';
COMMENT ON COLUMN platform.bank_provision_snapshot.as_of IS
  'business_meaning: 报告期末日，拨备与不良余额的同一观察时点。'
  'why_this_way: instant 绑定只认一个报告期末，避免拨备与不良跨期相除。basis: regulatory';

COMMENT ON COLUMN platform.bank_concentration_stat.institution IS
  'business_meaning: 法人机构代码，报表主体。'
  'why_this_way: 集中度指标按法人资本与法人最大暴露相除，实体必须是法人机构。basis: regulatory';
COMMENT ON COLUMN platform.bank_concentration_stat.as_of IS
  'business_meaning: 报告期末日。'
  'why_this_way: 资本与暴露必须同一时点；instant 绑定按该列落窗。basis: regulatory';

COMMENT ON COLUMN platform.ins_underwriting_stat.institution IS
  'business_meaning: 保险机构代码，期间统计主体。'
  'why_this_way: 011/019/027 等机构级指标按该列分组；产品/渠道行再汇总到机构。basis: regulatory';

COMMENT ON COLUMN platform.ins_claim_reserve_snapshot.claim_no IS
  'business_meaning: 赔案号，未决准备金的最小评估单元。'
  'why_this_way: 016 案均未决金额按赔案去重计数，必须保留赔案主键。basis: regulatory';
COMMENT ON COLUMN platform.ins_claim_reserve_snapshot.institution IS
  'business_meaning: 承保机构代码。'
  'why_this_way: 支持按机构追溯未决余额；当前 014/016 按产品分组，但保留机构维度。basis: regulatory';
COMMENT ON COLUMN platform.ins_claim_reserve_snapshot.product IS
  'business_meaning: 险种/产品代码。'
  'why_this_way: 014/016 的绑定实体列，按产品汇总未决余额与件数。basis: industry';
COMMENT ON COLUMN platform.ins_claim_reserve_snapshot.as_of IS
  'business_meaning: 准备金评估日。'
  'why_this_way: 未决准备金是时点余额，instant 绑定按该列落窗。basis: regulatory';

COMMENT ON COLUMN platform.ins_persistence_stat.institution IS
  'business_meaning: 保险机构代码。'
  'why_this_way: cohort 可跨机构汇总；保留机构列支持机构级继续率。basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.product IS
  'business_meaning: 险种/产品代码。'
  'why_this_way: 022/023/024 按产品分组输出，是绑定实体列。basis: industry';
COMMENT ON COLUMN platform.ins_persistence_stat.channel IS
  'business_meaning: 销售渠道代码；无渠道归属填 ''-''。'
  'why_this_way: 继续率可按渠道下钻；当前绑定按产品汇总，渠道只作为维度保留。basis: industry';

COMMENT ON COLUMN platform.cust_behavior_snapshot.customer_no IS
  'business_meaning: 客户号，RFM-R 的最小观察单元。'
  'why_this_way: 001/005 按客户输出最近行为距今天数，实体列必须是客户号。basis: industry';
COMMENT ON COLUMN platform.cust_behavior_snapshot.institution IS
  'business_meaning: 归属机构代码。'
  'why_this_way: 支持按机构汇总客户行为；当前绑定按客户输出。basis: industry';
COMMENT ON COLUMN platform.cust_behavior_snapshot.as_of IS
  'business_meaning: 行为快照基准日（通常为月末）。'
  'why_this_way: days_since_* 都是相对该基准日计算，instant 绑定按该列落窗。basis: industry';

COMMENT ON COLUMN platform.cust_cohort_stat.institution IS
  'business_meaning: 归属机构代码。'
  'why_this_way: 008 月度滚动留存率按机构汇总，实体列取机构。basis: industry';
COMMENT ON COLUMN platform.cust_cohort_stat.cohort_month IS
  'business_meaning: 获客 cohort 的起始月（当月 1 日）。'
  'why_this_way: 留存率必须按获客批次观察；与 cohort_key 组合保留可追溯性。basis: industry';
COMMENT ON COLUMN platform.cust_cohort_stat.as_of IS
  'business_meaning: 观察日。'
  'why_this_way: 006/007 的 N 月留存按观察日时点取值，instant 绑定按该列落窗。basis: industry';

COMMENT ON COLUMN platform.cust_aum_snapshot.customer_no IS
  'business_meaning: 客户号，AUM 的最小观察单元。'
  'why_this_way: 012/013 按客户输出时点与日均 AUM，实体列必须是客户号。basis: industry';
COMMENT ON COLUMN platform.cust_aum_snapshot.institution IS
  'business_meaning: 归属机构代码。'
  'why_this_way: 支持按机构汇总 AUM；当前绑定按客户输出。basis: industry';
COMMENT ON COLUMN platform.cust_aum_snapshot.as_of IS
  'business_meaning: AUM 观察日。'
  'why_this_way: 时点 AUM 取该日余额；日均 AUM 按该日计数，instant/period 绑定都按该列落窗。'
  'basis: industry';

-- =====================================================================
-- 5. metric_field_binding: 44 metrics -> 83 rows
-- =====================================================================

INSERT INTO platform.metric_field_binding
  (metric_id, definition_version, role, fact_table, entity_column, value_expr,
   agg, filter_sql, window_column, window_mode) VALUES
-- ---- BANK 013-016: five-class migration matrix ----
('FIN-BANK-013','v3.0','numerator','platform.bank_loan_account','institution','GREATEST(balance_start - period_decrease_amount, 0)','sum',
 'risk_class_start = ''normal'' AND risk_class_end IN (''special'',''substandard'',''doubtful'',''loss'')','as_of','instant'),
('FIN-BANK-013','v3.0','denominator','platform.bank_loan_account','institution','balance_start','sum',
 'risk_class_start = ''normal''','as_of','instant'),
('FIN-BANK-014','v3.0','numerator','platform.bank_loan_account','institution','GREATEST(balance_start - period_decrease_amount, 0)','sum',
 'risk_class_start = ''special'' AND risk_class_end IN (''substandard'',''doubtful'',''loss'')','as_of','instant'),
('FIN-BANK-014','v3.0','denominator','platform.bank_loan_account','institution','balance_start','sum',
 'risk_class_start = ''special''','as_of','instant'),
('FIN-BANK-015','v3.0','numerator','platform.bank_loan_account','institution','GREATEST(balance_start - period_decrease_amount, 0)','sum',
 'risk_class_start = ''substandard'' AND risk_class_end IN (''doubtful'',''loss'')','as_of','instant'),
('FIN-BANK-015','v3.0','denominator','platform.bank_loan_account','institution','balance_start','sum',
 'risk_class_start = ''substandard''','as_of','instant'),
('FIN-BANK-016','v3.0','numerator','platform.bank_loan_account','institution','GREATEST(balance_start - period_decrease_amount, 0)','sum',
 'risk_class_start = ''doubtful'' AND risk_class_end = ''loss''','as_of','instant'),
('FIN-BANK-016','v3.0','denominator','platform.bank_loan_account','institution','balance_start','sum',
 'risk_class_start = ''doubtful''','as_of','instant'),
-- ---- BANK 017/018: DPD roll rate ----
('FIN-BANK-017','v3.0','numerator','platform.bank_loan_account','institution','account_id','count_distinct',
 'dpd_start BETWEEN 30 AND 59 AND dpd_end >= 60','as_of','instant'),
('FIN-BANK-017','v3.0','denominator','platform.bank_loan_account','institution','account_id','count_distinct',
 'dpd_start BETWEEN 30 AND 59','as_of','instant'),
('FIN-BANK-018','v3.0','numerator','platform.bank_loan_account','institution','account_id','count_distinct',
 'dpd_start BETWEEN 60 AND 89 AND dpd_end >= 90','as_of','instant'),
('FIN-BANK-018','v3.0','denominator','platform.bank_loan_account','institution','account_id','count_distinct',
 'dpd_start BETWEEN 60 AND 89','as_of','instant'),
-- ---- BANK 022/023: provision ----
('FIN-BANK-022','v3.0','numerator','platform.bank_provision_snapshot','institution','provision_balance','sum',
 NULL,'as_of','instant'),
('FIN-BANK-022','v3.0','denominator','platform.bank_provision_snapshot','institution','npl_balance','sum',
 NULL,'as_of','instant'),
('FIN-BANK-023','v3.0','numerator','platform.bank_provision_snapshot','institution','provision_balance','sum',
 NULL,'as_of','instant'),
('FIN-BANK-023','v3.0','denominator','platform.bank_provision_snapshot','institution','loan_balance','sum',
 NULL,'as_of','instant'),
-- ---- BANK 025-030: concentration ----
('FIN-BANK-025','v3.0','numerator','platform.bank_concentration_stat','institution','max_single_customer_loan','max',
 NULL,'as_of','instant'),
('FIN-BANK-025','v3.0','denominator','platform.bank_concentration_stat','institution','capital_balance','max',
 NULL,'as_of','instant'),
('FIN-BANK-026','v3.0','numerator','platform.bank_concentration_stat','institution','max_single_customer_exposure','max',
 NULL,'as_of','instant'),
('FIN-BANK-026','v3.0','denominator','platform.bank_concentration_stat','institution','tier1_capital_net','max',
 NULL,'as_of','instant'),
('FIN-BANK-027','v3.0','numerator','platform.bank_concentration_stat','institution','max_group_exposure','max',
 NULL,'as_of','instant'),
('FIN-BANK-027','v3.0','denominator','platform.bank_concentration_stat','institution','tier1_capital_net','max',
 NULL,'as_of','instant'),
('FIN-BANK-028','v3.0','numerator','platform.bank_concentration_stat','institution','max_group_credit','max',
 NULL,'as_of','instant'),
('FIN-BANK-028','v3.0','denominator','platform.bank_concentration_stat','institution','capital_net','max',
 NULL,'as_of','instant'),
('FIN-BANK-029','v3.0','numerator','platform.bank_concentration_stat','institution','total_related_exposure','max',
 NULL,'as_of','instant'),
('FIN-BANK-029','v3.0','denominator','platform.bank_concentration_stat','institution','capital_net','max',
 NULL,'as_of','instant'),
('FIN-BANK-030','v3.0','numerator','platform.bank_concentration_stat','institution',
 'GREATEST(max_single_customer_exposure, max_group_exposure)','max',
 NULL,'as_of','instant'),
('FIN-BANK-030','v3.0','denominator','platform.bank_concentration_stat','institution','tier1_capital_net','max',
 NULL,'as_of','instant'),
-- ---- BANK 033: first payment default ----
('FIN-BANK-033','v3.0','numerator','platform.bank_loan_account','institution','account_id','count_distinct',
 'first_payment_due_date IS NOT NULL AND first_payment_default_flag','first_payment_due_date','period'),
('FIN-BANK-033','v3.0','denominator','platform.bank_loan_account','institution','account_id','count_distinct',
 'first_payment_due_date IS NOT NULL','first_payment_due_date','period'),
-- ---- INSURANCE 003/006: collected vs plan ----
('FIN-INS-003','v3.0','numerator','platform.ins_underwriting_stat','institution','collected_premium','sum',
 NULL,'period_end','period'),
('FIN-INS-006','v3.0','numerator','platform.ins_underwriting_stat','institution','collected_premium','sum',
 NULL,'period_end','period'),
('FIN-INS-006','v3.0','denominator','platform.ins_underwriting_stat','institution','plan_premium','sum',
 NULL,'period_end','period'),
-- ---- INSURANCE 008-011/013/027: underwriting ratios ----
('FIN-INS-008','v3.0','numerator','platform.ins_underwriting_stat','institution',
 'paid_claims + claim_reserve_change - reinsurance_recoverable','sum',
 'business_line = ''property''','period_end','period'),
('FIN-INS-008','v3.0','denominator','platform.ins_underwriting_stat','institution',
 'retained_premium - unearned_reserve_change','sum',
 'business_line = ''property''','period_end','period'),
('FIN-INS-009','v3.0','numerator','platform.ins_underwriting_stat','institution',
 'paid_claims + claim_reserve_change - reinsurance_recoverable','sum',
 'business_line = ''health''','period_end','period'),
('FIN-INS-009','v3.0','denominator','platform.ins_underwriting_stat','institution',
 'earned_premium - ceded_premium + reinsurance_reserve_change','sum',
 'business_line = ''health''','period_end','period'),
('FIN-INS-010','v3.0','numerator','platform.ins_underwriting_stat','institution',
 'paid_claims + claim_reserve_change','sum',
 NULL,'period_end','period'),
('FIN-INS-010','v3.0','denominator','platform.ins_underwriting_stat','institution',
 'signed_premium - ceded_premium - unearned_reserve_change','sum',
 NULL,'period_end','period'),
('FIN-INS-011','v3.0','numerator','platform.ins_underwriting_stat','institution',
 'paid_claims + claim_reserve_change - reinsurance_recoverable + expense_total','sum',
 'business_line = ''property''','period_end','period'),
('FIN-INS-011','v3.0','denominator','platform.ins_underwriting_stat','institution',
 'retained_premium - unearned_reserve_change','sum',
 'business_line = ''property''','period_end','period'),
('FIN-INS-013','v3.0','numerator','platform.ins_underwriting_stat','institution',
 'paid_claims + claim_reserve_change + long_term_reserve_change - reinsurance_recoverable','sum',
 'business_line = ''property''','period_end','period'),
('FIN-INS-013','v3.0','denominator','platform.ins_underwriting_stat','institution',
 'retained_premium - unearned_reserve_change - long_term_reserve_change','sum',
 'business_line = ''property''','period_end','period'),
('FIN-INS-027','v3.0','numerator','platform.ins_underwriting_stat','institution','expense_total','sum',
 'business_line = ''property''','period_end','period'),
('FIN-INS-027','v3.0','denominator','platform.ins_underwriting_stat','institution',
 'retained_premium - unearned_reserve_change','sum',
 'business_line = ''property''','period_end','period'),
-- ---- INSURANCE 026/028: channel cost ----
('FIN-INS-026','v3.0','numerator','platform.ins_underwriting_stat','channel','expense_total','sum',
 'channel <> ''-''','period_end','period'),
('FIN-INS-026','v3.0','denominator','platform.ins_underwriting_stat','channel','signed_premium','sum',
 'channel <> ''-''','period_end','period'),
('FIN-INS-028','v3.0','numerator','platform.ins_underwriting_stat','channel','commission_expense','sum',
 'channel <> ''-''','period_end','period'),
('FIN-INS-028','v3.0','denominator','platform.ins_underwriting_stat','channel','signed_premium','sum',
 'channel <> ''-''','period_end','period'),
-- ---- INSURANCE 014/016: claim reserves ----
('FIN-INS-014','v3.0','numerator','platform.ins_claim_reserve_snapshot','product',
 'reported_reserve + ibnr_reserve + expense_reserve','sum',
 'case_status = ''open''','as_of','instant'),
('FIN-INS-016','v3.0','numerator','platform.ins_claim_reserve_snapshot','product',
 'reported_reserve + ibnr_reserve + expense_reserve','sum',
 'case_status = ''open''','as_of','instant'),
('FIN-INS-016','v3.0','denominator','platform.ins_claim_reserve_snapshot','product','claim_no','count_distinct',
 'case_status = ''open''','as_of','instant'),
-- ---- INSURANCE 017/018: report and filing rates ----
('FIN-INS-017','v3.0','numerator','platform.ins_claim_case','product','claim_no','count_distinct',
 'claim_status <> ''withdrawn''','report_date','period'),
('FIN-INS-017','v3.0','denominator','platform.ins_policy','product','policy_no','count_distinct',
 'policy_status = ''in_force''','status_as_of','instant'),
('FIN-INS-018','v3.0','numerator','platform.ins_claim_case','product','claim_no','count_distinct',
 'claim_status <> ''withdrawn'' AND filing_date IS NOT NULL','report_date','period'),
('FIN-INS-018','v3.0','denominator','platform.ins_claim_case','product','claim_no','count_distinct',
 'claim_status <> ''withdrawn''','report_date','period'),
-- ---- INSURANCE 019/020: surrender rates ----
('FIN-INS-019','v3.0','numerator','platform.ins_underwriting_stat','institution','surrender_amount','sum',
 'business_line = ''life''','period_end','period'),
('FIN-INS-019','v3.0','denominator','platform.ins_underwriting_stat','institution',
 'beginning_reserve_total + policyholder_deposit_beginning + separate_account_beginning + current_term_premium','sum',
 'business_line = ''life''','period_end','period'),
('FIN-INS-020','v3.0','numerator','platform.ins_underwriting_stat','institution','surrender_amount','sum',
 'business_line = ''life''','period_end','period'),
('FIN-INS-020','v3.0','denominator','platform.ins_underwriting_stat','institution',
 'beginning_reserve_total + current_term_premium','sum',
 'business_line = ''life''','period_end','period'),
-- ---- INSURANCE 022/023: premium persistence cohorts ----
('FIN-INS-022-v1','v3.0','numerator','platform.ins_persistence_stat','product','renewed_premium','sum',
 'valuation_basis = ''grace'' AND renewal_year = 2','cohort_period','period'),
('FIN-INS-022-v1','v3.0','denominator','platform.ins_persistence_stat','product','first_year_premium','sum',
 'valuation_basis = ''grace'' AND renewal_year = 2','cohort_period','period'),
('FIN-INS-022-v2','v3.0','numerator','platform.ins_persistence_stat','product','renewed_premium','sum',
 'valuation_basis = ''natural'' AND renewal_year = 2','cohort_period','period'),
('FIN-INS-022-v2','v3.0','denominator','platform.ins_persistence_stat','product','first_year_premium','sum',
 'valuation_basis = ''natural'' AND renewal_year = 2','cohort_period','period'),
('FIN-INS-023-v1','v3.0','numerator','platform.ins_persistence_stat','product','renewed_premium','sum',
 'valuation_basis = ''grace'' AND renewal_year = 3','cohort_period','period'),
('FIN-INS-023-v1','v3.0','denominator','platform.ins_persistence_stat','product','first_year_premium','sum',
 'valuation_basis = ''grace'' AND renewal_year = 3','cohort_period','period'),
('FIN-INS-023-v2','v3.0','numerator','platform.ins_persistence_stat','product','renewed_premium','sum',
 'valuation_basis = ''natural'' AND renewal_year = 3','cohort_period','period'),
('FIN-INS-023-v2','v3.0','denominator','platform.ins_persistence_stat','product','first_year_premium','sum',
 'valuation_basis = ''natural'' AND renewal_year = 3','cohort_period','period'),
-- ---- INSURANCE 024: vehicle renewal ----
('FIN-INS-024','v3.0','numerator','platform.ins_persistence_stat','product','renewed_vehicle_count','sum',
 'valuation_basis = ''vehicle_renewal''','cohort_period','period'),
('FIN-INS-024','v3.0','denominator','platform.ins_persistence_stat','product','due_vehicle_count','sum',
 'valuation_basis = ''vehicle_renewal''','cohort_period','period'),
-- ---- INSURANCE 025: average premium per new policy ----
('FIN-INS-025','v3.0','numerator','platform.ins_policy','channel',
 'CASE WHEN premium_type = ''single'' THEN premium_amount ELSE first_year_premium END','sum',
 'channel = ''individual_agent''','issue_date','period'),
('FIN-INS-025','v3.0','denominator','platform.ins_policy','channel','policy_no','count_distinct',
 'channel = ''individual_agent''','issue_date','period'),
-- ---- CUSTOMER 001/005: recency ----
('CUST-001','v3.0','numerator','platform.cust_behavior_snapshot','customer_no','days_since_last_behavior','max',
 'days_since_last_behavior IS NOT NULL','as_of','instant'),
('CUST-005','v3.0','numerator','platform.cust_behavior_snapshot','customer_no','days_since_proxy_event','max',
 'last_txn_date IS NULL AND days_since_proxy_event IS NOT NULL','as_of','instant'),
-- ---- CUSTOMER 006/007/008: retention ----
('CUST-006','v3.0','numerator','platform.cust_cohort_stat','cohort_key','retained_customers','sum',
 NULL,'as_of','instant'),
('CUST-006','v3.0','denominator','platform.cust_cohort_stat','cohort_key','cohort_customers','sum',
 NULL,'as_of','instant'),
('CUST-007','v3.0','numerator','platform.cust_cohort_stat','cohort_key',
 'cohort_customers - active_customers','sum',
 NULL,'as_of','instant'),
('CUST-007','v3.0','denominator','platform.cust_cohort_stat','cohort_key','cohort_customers','sum',
 NULL,'as_of','instant'),
('CUST-008','v3.0','numerator','platform.cust_cohort_stat','institution','active_and_prior_month','sum',
 NULL,'as_of','instant'),
('CUST-008','v3.0','denominator','platform.cust_cohort_stat','institution','prior_month_active','sum',
 NULL,'as_of','instant'),
-- ---- CUSTOMER 012/013: AUM ----
('CUST-012','v3.0','numerator','platform.cust_aum_snapshot','customer_no','aum','sum',
 NULL,'as_of','instant'),
('CUST-013','v3.0','numerator','platform.cust_aum_snapshot','customer_no','aum','sum',
 NULL,'as_of','period'),
('CUST-013','v3.0','denominator','platform.cust_aum_snapshot','customer_no','as_of','count_distinct',
 NULL,'as_of','period')
ON CONFLICT (metric_id, definition_version, role) DO UPDATE SET
  fact_table = EXCLUDED.fact_table, entity_column = EXCLUDED.entity_column,
  value_expr = EXCLUDED.value_expr, agg = EXCLUDED.agg,
  filter_sql = EXCLUDED.filter_sql, window_column = EXCLUDED.window_column,
  window_mode = EXCLUDED.window_mode;

-- ---- grain / minimum window for the newly bound metrics ----
UPDATE platform.metric_definition SET grain = 'institution', min_window_days = 0
 WHERE metric_id IN ('FIN-BANK-013','FIN-BANK-014','FIN-BANK-015','FIN-BANK-016',
                     'FIN-BANK-017','FIN-BANK-018','FIN-BANK-022','FIN-BANK-023',
                     'FIN-BANK-025','FIN-BANK-026','FIN-BANK-027','FIN-BANK-028',
                     'FIN-BANK-029','FIN-BANK-030','FIN-BANK-033');
UPDATE platform.metric_definition SET grain = 'institution', min_window_days = 1
 WHERE metric_id IN ('FIN-INS-003','FIN-INS-006','FIN-INS-008','FIN-INS-009',
                     'FIN-INS-010','FIN-INS-011','FIN-INS-027');
UPDATE platform.metric_definition SET grain = 'institution', min_window_days = 730
 WHERE metric_id = 'FIN-INS-013';
UPDATE platform.metric_definition SET grain = 'institution', min_window_days = 90
 WHERE metric_id = 'FIN-INS-019';
UPDATE platform.metric_definition SET grain = 'institution', min_window_days = 365
 WHERE metric_id = 'FIN-INS-020';
UPDATE platform.metric_definition SET grain = 'product', min_window_days = 0
 WHERE metric_id IN ('FIN-INS-014','FIN-INS-016');
UPDATE platform.metric_definition SET grain = 'product', min_window_days = 1
 WHERE metric_id IN ('FIN-INS-017','FIN-INS-018');
UPDATE platform.metric_definition SET grain = 'product', min_window_days = 365
 WHERE metric_id IN ('FIN-INS-022-v1','FIN-INS-022-v2','FIN-INS-024');
UPDATE platform.metric_definition SET grain = 'product', min_window_days = 730
 WHERE metric_id IN ('FIN-INS-023-v1','FIN-INS-023-v2');
UPDATE platform.metric_definition SET grain = 'channel', min_window_days = 1
 WHERE metric_id IN ('FIN-INS-025','FIN-INS-026','FIN-INS-028');
UPDATE platform.metric_definition SET grain = 'customer', min_window_days = 0
 WHERE metric_id IN ('CUST-001','CUST-005','CUST-012');
UPDATE platform.metric_definition SET grain = 'cohort', min_window_days = 0
 WHERE metric_id IN ('CUST-006','CUST-007');
UPDATE platform.metric_definition SET grain = 'institution', min_window_days = 0
 WHERE metric_id = 'CUST-008';
UPDATE platform.metric_definition SET grain = 'customer', min_window_days = 30
 WHERE metric_id = 'CUST-013';

-- ---- four-tier distribution after v7 ----
UPDATE platform.metric_definition SET computability_tier = 'structurally_computable'
 WHERE metric_id IN (
   'FIN-BANK-013','FIN-BANK-014','FIN-BANK-015','FIN-BANK-016','FIN-BANK-017',
   'FIN-BANK-018','FIN-BANK-022','FIN-BANK-023','FIN-BANK-025','FIN-BANK-026',
   'FIN-BANK-027','FIN-BANK-028','FIN-BANK-029','FIN-BANK-030','FIN-BANK-033',
   'FIN-INS-003','FIN-INS-006','FIN-INS-008','FIN-INS-009','FIN-INS-010',
   'FIN-INS-011','FIN-INS-013','FIN-INS-014','FIN-INS-016','FIN-INS-017',
   'FIN-INS-018','FIN-INS-019','FIN-INS-020','FIN-INS-022-v1','FIN-INS-022-v2',
   'FIN-INS-023-v1','FIN-INS-023-v2','FIN-INS-024','FIN-INS-025','FIN-INS-026',
   'FIN-INS-027','FIN-INS-028',
   'CUST-001','CUST-005','CUST-006','CUST-007','CUST-008','CUST-012','CUST-013'
 );

UPDATE platform.metric_definition SET computability_tier = 'blocked_semantics'
 WHERE metric_id IN ('FIN-BANK-019','FIN-BANK-020','FIN-BANK-021','FIN-BANK-036',
                     'FIN-INS-012','FIN-INS-022','FIN-INS-023','CUST-004');

-- ---- residual gaps: table/field or sign-off, no blanks ----
UPDATE platform.metric_definition SET
  missing = '公式不可翻译：引用 FIN-BANK-017 × FIN-BANK-018；编译器算术白名单不支持指标间引用。需派生率执行器，或先生成两期观测再相乘。',
  decision_owner = '指标治理/机制负责人',
  note = '原因分类：公式不可翻译（跨指标派生）'
 WHERE metric_id = 'FIN-BANK-019';
UPDATE platform.metric_definition SET
  missing = 'source',
  decision_owner = '风险管理部',
  note = '原因分类：需业务裁定。未固定迁徙分类对（正常→关注 / 关注→不良等）与户数去重主体（客户号合并多账户），需风险管理部签字。'
 WHERE metric_id = 'FIN-BANK-020';
UPDATE platform.metric_definition SET
  missing = '需业务裁定：未固定迁徙分类对；期末余额是否含期间核销/处置未明确。',
  decision_owner = '风险管理部',
  note = '原因分类：需业务裁定'
 WHERE metric_id = 'FIN-BANK-021';
UPDATE platform.metric_definition SET
  missing = '族索引指标（formula_disabled=true），不单独出数；见 FIN-BANK-036-v1 / v2。',
  decision_owner = '不适用（族索引）',
  note = '原因分类：族索引/公式关闭'
 WHERE metric_id = 'FIN-BANK-036';
UPDATE platform.metric_definition SET
  missing = '公式不可翻译：引用 FIN-INS-027 + FIN-INS-013；需派生率执行器。',
  decision_owner = '精算/指标治理',
  note = '原因分类：公式不可翻译（跨指标派生）'
 WHERE metric_id = 'FIN-INS-012';
UPDATE platform.metric_definition SET
  missing = '族索引指标（formula_disabled=true），不单独出数；见 FIN-INS-022-v1 / v2。',
  decision_owner = '不适用（族索引）',
  note = '原因分类：族索引/公式关闭'
 WHERE metric_id = 'FIN-INS-022';
UPDATE platform.metric_definition SET
  missing = '族索引指标（formula_disabled=true），不单独出数；见 FIN-INS-023-v1 / v2。',
  decision_owner = '不适用（族索引）',
  note = '原因分类：族索引/公式关闭'
 WHERE metric_id = 'FIN-INS-023';
UPDATE platform.metric_definition SET
  missing = '公式不可翻译（NTILE 非标量输出）+ 需业务裁定（客户群体边界、NULL 参与规则）。',
  decision_owner = '客户经营部',
  note = '原因分类：公式不可翻译（非标量 score）+ 需业务裁定'
 WHERE metric_id = 'CUST-004';

CREATE INDEX IF NOT EXISTS metric_field_binding_fact_idx
  ON platform.metric_field_binding (fact_table, metric_id);
