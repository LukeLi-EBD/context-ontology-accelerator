-- V30: v9 final-ruling seed for 27 metric definitions
-- (26 E1 baseline rows = 25 table-2 + FIN-INS-012, plus the FIN-BANK-036 family index).
--
-- Idempotent: INSERT ... ON CONFLICT (metric_id) DO UPDATE guarded by IS DISTINCT
-- FROM, so replays are true no-ops (no updated_at churn, no snapshot drift).
-- Only the 27 listed rows change; the other 58 definitions and all
-- metric_field_binding rows are untouched. Executable quartet columns
-- (formula_expr/numerator_agg/denominator_agg/window_kind/min_window_days/grain/
-- output_mode/rule_set_json), definition_version and formula_disabled keep v5 semantics.
-- name_zh/domain/evidence_status are supplied only to satisfy NOT NULL on the insert
-- path and are carried from the existing row, never overwritten.
-- publishable=true means released as an internal industry baseline, not regulatory filing.

ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS decision_date date;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS ruling text;

INSERT INTO platform.metric_definition
  (metric_id, name_zh, domain, evidence_status, display_name, definition,
   formula_text, denominator_text, observation_period, granularity, unit,
   evidence_basis, provenance_label, inference, publishable, note,
   decision_owner, decision_date, ruling, updated_at)
SELECT v.metric_id,
       COALESCE(m.name_zh, v.name_zh),
       COALESCE(m.domain, v.domain),
       COALESCE(m.evidence_status, v.evidence_status),
       v.display_name, v.definition, v.formula_text, v.denominator_text,
       v.observation_period, v.granularity, v.unit, v.evidence_basis,
       v.provenance_label, v.inference, v.publishable, v.note,
       v.decision_owner, v.decision_date::date, v.ruling, now()
  FROM (VALUES
    ('FIN-BANK-002', '逾期分档（M0–M6）', 'bank', 'EVIDENCE_MISSING', '逾期分档（M0–M6）〔行业〕', '按逾期天数将账户划入 M0–M6 月度分桶，M0 未逾期、M1 逾期 1–30 天、M2 逾期 31–60 天，其余每 30 天一档至 M6', 'M 档 = floor((max(观察日−应还款日,0)−1)/30)+1，DPD=0 记 M0', '不适用（分档规则）', 'point-in-time（月末观察日快照）', 'account（单笔贷款/信用卡账户）', '档（M0–M6）', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 行业通行分桶，不是监管定义。反驳：若系统或合同把 M1 定义为 0–30 天，整个边界偏移一档；拿到内部贷后制度只改档界说明，不改 ID。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-005', 'Stage 2“30 天显著增加”', 'bank', 'EVIDENCE_MISSING', 'Stage 2“30 天显著增加”〔行业〕', '自初始确认后信用风险显著增加但尚未发生信用减值的金融资产划入第二阶段，30 天逾期作为可推翻的显著增加假设', 'Stage2 = (DPD>30) ∧ 未发生信用减值，允许以定量或定性证据推翻', '全部存续金融资产余额或笔数', 'point-in-time（报告日）', 'asset（单笔资产，非零售按债务人）', '阶段（Stage 1/2/3）与占比 %', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 30 天阈值来自 IFRS 9 B5.5.18 可推翻假设，原文未取到，定义原则属行业通行。反驳：若公司采用 60 天阈值或低信用风险简化，30 天不成立；拿到原文只补引注。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-017', '逾期迁徙率 30→60', 'bank', 'EVIDENCE_MISSING', '逾期迁徙率 30→60〔行业〕', '期初逾期 30–59 天的账户在观察期末迁徙到 60 天及以上的比例', 'numerator/denominator*100', '期初 DPD30–59 账户数或余额（按账户去重，不剔除期间结清/核销，保留在分母计未迁徙）', 'period（自然月，月度滚动）', 'account，可汇总 product', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 行业 roll rate 标准写法。反驳：若分母剔除结清/核销，比率虚高且不能与 018 相乘；017/018/019 分母规则必须一致。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-018', '逾期迁徙率 60→90', 'bank', 'EVIDENCE_MISSING', '逾期迁徙率 60→90〔行业〕', '期初逾期 60–89 天的账户在观察期末迁徙到 90 天及以上的比例', 'numerator/denominator*100', '期初 DPD60–89 账户数或余额（按账户去重，不剔除期间结清/核销）', 'period（自然月，月度滚动）', 'account，可汇总 product', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 与 017 同规则。反驳：若 90 天以上已进入不良处置并转出，需保留在分母否则低估迁徙；转出单独 memo。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-019', '30→90 累计迁徙率', 'bank', 'EVIDENCE_MISSING', '30→90 累计迁徙率〔行业〕', '期初 DPD30–59 的同批账户在连续两个自然月内累计迁徙到 90 天以上的比例', 'numerator/denominator*100（主口径用直接 cohort，不用两比率乘积）', '期初 DPD30–59 账户数（同批、按账户去重，不剔除期间结清/核销）', 'period（连续两个自然月，≥60 天）', 'account', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 直接 cohort 与 r30→60 × r60→90 在无新增退出时等价，有进出时以直接 cohort 为准。反驳：若把一个季度当两个月，窗口错配；乘积保留为对账视图。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-033', '首逾率（FPD）', 'bank', 'EVIDENCE_MISSING', '首逾率（FPD）〔行业〕', '新发放贷款在首个还款期即发生逾期的账户占比（固定账户口径变体 A）', 'numerator/denominator*100', '同期首期应还账户数（按账户去重，不含未到首个还款期）', 'period（按放款月形成 vintage，观察至首个还款期后 30 天）', 'account（放款批次）', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 三套候选固定 A，避免分子分母混搭。反驳：若改用金额口径或首期含宽限期，结果不可比；切换变体需新 ID。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-034', '早期预警（EWS）', 'bank', 'EVIDENCE_MISSING', '早期预警（EWS）〔推测〕', '按可配置规则集监测资产质量恶化信号，命中对象进入预警清单，按规则严重度与命中数输出 L1–L3', '预警等级 = f(命中规则集合)，规则 R01–R10 与阈值沿用 v5 rule_set_json', '不适用', 'point-in-time（日/周）', 'customer 或 agreement', '等级 L1–L3 加命中清单', 'industry', '推测', true, false, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 监管只要求建立机制，不规定公式；v5 的 10 条规则与阈值是可执行定义，本表不新增规则。反驳：阈值未校准会误报，必须业务确认；拿到监管细则只改阈值来源。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-006', '部分还款/最低还款逾期判定', 'bank', 'EVIDENCE_MISSING', '部分还款/最低还款逾期判定〔推测〕', '未按合同还足当期应还金额（含信用卡最低还款额）时判定该期逾期，按整期逾期而非仅未还部分', '逾期标志=1 若 实还金额<当期应还金额或最低还款额，逾期起点=应还款日次日', '当期应还期次数（按账户×期次去重）', 'point-in-time（逐日更新，月末快照）', 'account', '标志 0/1 与天', 'industry', '推测', true, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 无成文公式，按合同实务。反驳：信用卡最低还款与贷款整期应还不同，若合同允许部分还款不逾期则不成立；须业务确认合同条款。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-020', '迁徙率（户数口径变体）', 'bank', 'EVIDENCE_MISSING', '迁徙率（户数口径变体）〔推测〕', '以户数而非余额计算的迁徙率变体：期初该分类客户中期末迁徙到更高分类的客户占比；仅作内部风控对照，监管口径为余额法。', 'numerator/denominator*100', '期初该分类客户数（按客户号去重、账户合并、剔除内部/测试/销户；单位 户）', 'period（报告期，季度，≥90 天）', 'customer', '%', 'industry', '推测', true, true, '终裁：户数口径迁徙率（监管余额法的内部对照变体）：分母=期初该分类客户数（客户号去重、账户合并、剔除内部/测试/销户）；分子=同批客户中期末迁徙到更高分类的客户数（任一账户迁徙计 1）；季度；customer；count distinct/count distinct。 理由：指标名为“迁徙率（户数口径变体）”，户数口径与名称一致；仅内部风控观察，不与监管余额法混算。 被反驳点：客户多账户分属不同分类时“任一迁徙即计 1”会高估；若风险管理部改按主账户或加权口径，本值不成立。 改判触发：风险管理部出具口径书；或该指标正式改名为“风险加权资产占比”（届时另立 metric_id，不挂 020）。 未采用：用户建议的“风险加权资产占比”与 020 的指标语义（迁徙率户数口径）不符，未采用；RWA 占比应作为新指标另立 ID。 未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。', '平台专家组', '2026-11-06', 'E2-2'),
    ('FIN-BANK-021', '迁徙率（五级分类迁徙矩阵）', 'bank', 'EVIDENCE_MISSING', '迁徙率（五级分类迁徙矩阵）〔推测〕', '五级分类迁徙矩阵口径：期初正常类与关注类贷款在观察期末迁徙为不良（次级/可疑/损失）的比例；核销不计入迁徙分母，单独列示。', 'numerator/denominator*100', '期初正常类+关注类贷款余额（剔除期内已核销金额，核销单列 memo；单位 元）', 'period（报告期，季度，≥90 天）', 'institution/product', '%', 'industry', '推测', true, true, '终裁：五级分类迁徙矩阵，按“期初正常+关注 → 期末不良（次级/可疑/损失）”计量；分子=期初正常+关注余额中期末转为不良的余额；分母=期初正常+关注余额（剔除期内已核销金额，核销单列 memo）；季度；institution/product；sum/sum。 理由：与监管五级分类迁徙矩阵同构，可与 013–016 对账；核销不进分母，避免已出表资产稀释迁徙率，同时单列保留可追溯。 被反驳点：剔除核销会缩小分母、抬高迁徙率；若监管或审计要求分母含核销，本值不成立。 改判触发：风险管理部或审计出具口径书；监管原文到位；核销/重组政策变更。 未采用：不采用“期末余额为分母”的旧写法：期末分母会把本期迁徙结果混入基数，跨期不可比。 未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。', '平台专家组', '2026-11-06', 'E2-1'),
    ('FIN-BANK-031', '申请通过率', 'bank', 'EVIDENCE_MISSING', '申请通过率〔推测〕', '统计期内首次受理的信贷申请中，在观察截止日（期末+30 天）前完成审批且结论为通过的申请笔数占比', 'numerator/denominator*100', '统计期内首次受理笔数（同上排除）', 'period（统计期+30 天审批观察）', 'institution/channel，可下钻 product', '%', 'industry', '推测', true, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 v5 已定唯一分母；本表只补分子与观察窗。反驳：若审批跨期超过 30 天，通过率被低估；须按审批完成期归属或延长观察窗。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-032', '额度使用率', 'bank', 'EVIDENCE_MISSING', '额度使用率〔推测〕', '同一时点已用授信本金占已批复且有效授信额度的比例', 'numerator/denominator*100', '已批复且有效额度（排除拒绝/撤销/过期/冻结/注销/内部/测试）', 'point-in-time（月末）', 'customer/agreement', '%', 'industry', '推测', true, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 v5 已定唯一分母。反驳：循环额度、一次性额度、外币未折算会让比率失真；须固定额度类型与折算规则。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-035', '催收回收率', 'bank', 'EVIDENCE_MISSING', '催收回收率〔推测〕', '观察期初在催账户的本金在观察期内现金回收的比例', 'numerator/denominator*100', '观察期初在催账户本金余额（按账户去重，排除已核销/转出/重组退出/内部/测试/结清）', 'period（3/6/12 个月）', 'institution/product', '%', 'industry', '推测', true, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 v5 已定 cohort 口径。反驳：若以物抵债计入回收或分子含利息，回收率可能超过 100%；非现金处置另设 memo。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-BANK-036-v1', '不良处置率', 'bank', 'EVIDENCE_MISSING', '不良处置率〔推测〕', '期内完成处置的不良资产账面金额（gross，含核销）占期初不良资产余额的比例。', '主口径 = numerator/denominator*100（v1）', '期初不良资产余额（单位 元）', 'period（季度/年度，≥90 天）', 'institution/product/处置方式', '%', 'industry', '推测', true, true, '终裁：默认推荐 -v1 不良处置率（分子=期内完成处置不良账面金额，分母=期初不良资产余额）；族索引 FIN-BANK-036 保持 formula_disabled=true、output_mode=index，不单独出数；仅显式 variant=v2 时走处置回收率。 理由：处置率是过程主指标，回收率是结果指标；主指标优先，默认 v1 消除取数歧义。 被反驳点：若考核以现金回收为主，默认 v2 更合适；此时 v1 不作为默认。 改判触发：风险/资保部门书面指定默认变体；监管报送明确以回收率为主。 未采用：不采用“按调用方自选”的模糊路由：同一 ID 两式并存会导致同名指标不可比。 未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。', '平台专家组', '2026-11-06', 'E2-3'),
    ('FIN-INS-003', '实收保费', 'insurance', 'EVIDENCE_MISSING', '实收保费〔行业〕', '按收付实现制，统计期内实际收到的保费扣除批退与退费', 'numerator = Σ本期保费收款 − Σ本期批退/退费', '不适用（可加总指标）', 'period（统计期，月/季/年）', 'product/channel/institution', '元', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 行业通行，收付实现制。反驳：预收/退费跨期时与权责发生制不同；对外披露用原保险保费收入，不用本口径。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-INS-006', '保费达成率', 'insurance', 'EVIDENCE_MISSING', '保费达成率〔行业〕', '实际保费完成额占计划保费的比重', 'numerator/denominator*100', '计划保费（锁定版本、同期同口径）', 'period（考核期，月/季/年）', 'institution/channel', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 管理指标。反驳：计划中途调整或口径不一致会让达成率失真；须锁定计划版本。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-INS-007', '简单赔付率', 'insurance', 'EVIDENCE_MISSING', '简单赔付率〔行业〕', '赔款支出占保费收入的比重（简单口径，不调未决准备金与再保摊回）', 'numerator/denominator*100', '原保险保费收入（同期同口径）', 'period（报告期）', 'product', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 行业简单口径。反驳：若改用已赚保费，结果不同；不能与综合赔付率混比。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-INS-017', '报案率', 'insurance', 'EVIDENCE_MISSING', '报案率〔行业〕', '统计期内报案件数占有效保单件数的比例', 'numerator/denominator*100', '有效保单件数（按保单号去重，剔除退保/注销）', 'period（统计期，月/年）', 'product/institution', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 与立案率是相邻指标，不互为分母。反驳：若保单件数用时点而非期间平均，长险短险混合会失真；须固定件数口径。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-INS-022-v1', '13 个月保费继续率（宽限期口径）', 'insurance', 'EVIDENCE_MISSING', '13 个月保费继续率（宽限期口径）〔推测〕', '族索引，默认 v1 宽限期口径，第 1 个保单年度结束后宽限期内实收第 2 个保单年度首期规模保费占首年实收规模保费的比例', 'numerator/denominator*100', '该批新单首个保单年度实收规模保费（剔除趸交/犹豫撤单/理赔终止/免缴/注销/迁出/中止/转换终止，按保单号去重）', 'period（12 个月 cohort，观察至宽限期截止，默认 60 天可配置）', 'product（长期寿险期交新单）', '%', 'industry', '推测', true, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 协会原文存疑，默认 v1 是按原文最自洽解释。反驳：若协会本意是自然月，v1 不成立，应切 v2；原文到位只改 provenance 与注，不改变体 ID。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-INS-023-v1', '25 个月保费继续率（宽限期口径）', 'insurance', 'EVIDENCE_MISSING', '25 个月保费继续率（宽限期口径）〔推测〕', '族索引，默认 v1 宽限期口径，第 2 个保单年度结束后宽限期内实收第 3 个保单年度首期规模保费占首年实收规模保费的比例', 'numerator/denominator*100', '同 022 首年实收规模保费（剔除项同 022，按保单号去重）', 'period（24 个月 cohort，观察至宽限期截止）', 'product（长期寿险期交新单）', '%', 'industry', '推测', true, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 25 个月原文照抄首年宽限期属笔误，v5 已修正。反驳：若协会本意是第 25 个保单月自然月，应切 v2；需 24 个月状态历史。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-INS-024', '续保率（车险）', 'insurance', 'EVIDENCE_MISSING', '续保率（车险）〔行业〕', '到期应续保车辆中实际在本司续保的比例', 'numerator/denominator*100', '到期应续保车辆数（按 VIN 去重，含脱保车辆）', 'period（月度/保单年度到期队列）', 'product（车险）/channel', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 车险按 VIN 而非保单号。反驳：车辆过户/退保重投会让 VIN 去重误算续保；须过户标识。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-INS-026', '渠道费用率', 'insurance', 'EVIDENCE_MISSING', '渠道费用率〔行业〕', '单一渠道费用支出占该渠道签单保费的比例', 'numerator/denominator*100', '该渠道签单保费（同期、渠道归属一致）', 'period（报告期）', 'channel', '%', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 费用与保费必须同渠道归属。反驳：跨渠道共担费用分摊规则不同会失真；须固定分摊表。', '平台专家组', '2026-11-06', 'E1'),
    ('CUST-005', 'RFM-R（无交易代理口径）', 'customer', 'EVIDENCE_MISSING', 'RFM-R（无交易代理口径）〔推测〕', '无有效交易客户用注册/开卡/首单/保单生效日作为代理最近行为日计算 R，并单独标记未激活', 'numerator = max(基准日−代理事件日,0)，无任何代理事件则 NULL', '不适用（非比率）', 'point-in-time（月末基准日）', 'customer', '天', 'industry', '推测', true, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 仅调研建议，无权威做法。反驳：代理事件不是“行为”，R 语义被稀释；应仅用于未激活分层，不进入主 RFM 分档。', '平台专家组', '2026-11-06', 'E1'),
    ('CUST-009', '产品持有数', 'customer', 'EVIDENCE_MISSING', '产品持有数〔行业〕', '客户在观察时点持有的有效产品数量，按产品大类去重', 'numerator = count(distinct 产品类别) where 产品状态有效', '不适用（计数指标）', 'point-in-time（月末/季末）', 'customer', '个', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 大类去重与细类计数是两口径。反驳：同一产品多账户持有，按大类去重不重复，按账户计会虚高；须固定大类口径。', '平台专家组', '2026-11-06', 'E1'),
    ('CUST-010', '人均产品数', 'customer', 'EVIDENCE_MISSING', '人均产品数〔行业〕', '客户平均持有有效产品数，反映交叉销售深度', 'numerator/denominator（不做 *100，结果为个/户）', '客户数（同一客群、同一时点、按客户号去重、剔除销户）', 'point-in-time（月末/季末）', 'segment/institution', '个/户', 'industry', '行业通行', false, true, '依据行业通行做法定稿为平台基线；将来获原文后替换。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。 分子分母同客群同时点。反驳：客户数含未激活/销户会稀释均值；须固定客群定义。', '平台专家组', '2026-11-06', 'E1'),
    ('FIN-INS-012', '两年综合成本率（2003）', 'insurance', 'EVIDENCE_MISSING', '两年综合成本率（2003）', '两年费用与赔付合计占两年自留保费净额的比重（2003 旧规口径的代数合并式）', 'numerator/denominator*100', '两年自留保费合计 − 两年未到期责任准备金提转差', 'period（两年滚动，≥730 天）', 'institution（财险公司）', '%', 'regulatory', '原文', false, true, '旧规两项比率的等价代数变形，不伪造新原文；仅历史对照，不作现行报送口径。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。', '平台专家组', '2026-11-06', 'carry-v6'),
    ('FIN-BANK-036', '不良处置率/处置回收率', 'bank', 'EVIDENCE_MISSING', '不良处置率/处置回收率（口径族·索引）〔推测〕', '口径族索引：不良处置率（-v1，默认）与处置回收率（-v2）并列；本行不单独出数。', '不适用（族索引；见 FIN-BANK-036-v1 / -v2）', '不适用（族索引；v1=期初不良资产余额，v2=期内处置标的账面金额）', '不适用（族索引；季度/年度）', '不适用（族索引）', '%', 'industry', '推测', true, false, '终裁：默认变体 FIN-BANK-036-v1；族索引 formula_disabled=true、output_mode=index，不单独出数；v2 仅在显式指定时启用。未获监管原文，本终裁为平台内部基线，不代表监管报送口径；对外报送须替换为原文口径。', '平台专家组', '2026-11-06', 'E2-3')
  ) AS v(metric_id, name_zh, domain, evidence_status, display_name, definition, formula_text, denominator_text, observation_period, granularity, unit, evidence_basis, provenance_label, inference, publishable, note, decision_owner, decision_date, ruling)
  LEFT JOIN platform.metric_definition m ON m.metric_id = v.metric_id
 WHERE true
ON CONFLICT (metric_id) DO UPDATE SET
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  note = EXCLUDED.note,
  decision_owner = EXCLUDED.decision_owner,
  decision_date = EXCLUDED.decision_date,
  ruling = EXCLUDED.ruling,
  updated_at = now()
WHERE (
    metric_definition.display_name, metric_definition.definition, metric_definition.formula_text, metric_definition.denominator_text, metric_definition.observation_period, metric_definition.granularity, metric_definition.unit, metric_definition.evidence_basis, metric_definition.provenance_label, metric_definition.inference, metric_definition.publishable, metric_definition.note, metric_definition.decision_owner, metric_definition.decision_date, metric_definition.ruling
  ) IS DISTINCT FROM (
    EXCLUDED.display_name, EXCLUDED.definition, EXCLUDED.formula_text, EXCLUDED.denominator_text, EXCLUDED.observation_period, EXCLUDED.granularity, EXCLUDED.unit, EXCLUDED.evidence_basis, EXCLUDED.provenance_label, EXCLUDED.inference, EXCLUDED.publishable, EXCLUDED.note, EXCLUDED.decision_owner, EXCLUDED.decision_date, EXCLUDED.ruling
  );
