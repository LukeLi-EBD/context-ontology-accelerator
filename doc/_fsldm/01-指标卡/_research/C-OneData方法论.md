# C - 阿里巴巴 OneData 方法论（面向指标口径治理的抽取）

> 调研目的：只抽取「可用于指标卡 / 口径卡设计」的部分，不涉及代码与实现。
> 调研日期：2026-11-05
> 证据分级：**A = 阿里云官方帮助中心 / 官方产品文档**；**B = 厂商白皮书 / 官方出版物**；**C = 二手解读（开发者社区、博客、培训材料）**。

## 0. 先给结论：公开资料的可信度边界

- 结论：OneData 的**落地规则**（分层、原子/派生指标、维度唯一性、版本与下线）在阿里云 Dataphin / DataWorks 帮助中心有大量官方文档，可逐条核实；但 OneData 作为**方法论本身的完整定义**没有一份官方"方法论白皮书"，官方只以"源自阿里内部实践的 OneData 数据治理方法论"一句带过。
- 来源：What is Dataphin（EN 帮助中心）/ https://help.aliyun.com/en/dataphin/fullmanaged/product-overview/what-is-a-dataphin / 更新 2026-03-30
- 性质：官方文档
- 核实状态：已核实

- 结论：中文互联网上关于 OneData 的体系化叙述（含"三层架构""规范定义四要素"）主要来自《大数据之路：阿里巴巴大数据实践》的读书笔记与开发者社区文章，属二手；其中不少术语（如"修饰词""修饰类型"）在现行官方帮助中心已改名为"业务限定"。
- 来源：《大数据之路：阿里巴巴大数据实践——OneData数据中台体系》（阿里云开发者社区）/ https://developer.aliyun.com/article/1674625 / 2025-08-02
- 性质：二手解读
- 核实状态：已核实（文章内容），但其术语与官方现行文档存在代际差异

- 结论：OneData / OneID / OneService 的"三段式"提法只在厂商产品页与厂商博客出现，帮助中心没有给出三者的定义；且存在"OneData = 全部"与"OneData = OneModel"两种用法，引用时必须注明出处与年份。
- 来源：Dataphin 产品页（"applies Alibaba Group's OneData, OneID & OneService technologies"）/ https://www.alibabacloud.com/de/product/dataphin ；
  《Dataphin 的前世今生：缘起》"OneData（OneModel+OneID+OneService）" / https://developer.aliyun.com/article/785026 / 2021-07-03
- 性质：官方产品页（仅提法）+ 二手（定义）
- 核实状态：部分核实（提法已核实，定义未获官方文档背书）

**资料盘点**：官方文档约 15 篇（A 级），厂商白皮书 2 篇（B 级），二手文章 3 篇（C 级）。本文件所有"规则型"结论均优先取自 A 级。

---

## 1. 体系边界：OneData / OneID / OneService / 数据中台 / Dataphin

| 名称 | 解决什么问题 | 形态 | 彼此关系 | 证据 |
|---|---|---|---|---|
| **OneData** | 指标口径混乱、模型重复建设、数据孤岛；让同一业务含义只加工一次、只有一个口径 | 方法论 + 工具链（规范定义 → 模型设计 → 开发平台） | 方法论母体；Dataphin 是它的产品化 | A（Dataphin 基于 OneData）/ C（体系描述） |
| **OneID** | 同一实体（客户/商品/账户）在多源系统里 ID 不一致，无法跨域聚合 | 实体识别与 ID-Mapping + 实体标签资产 | 被表述为 OneData 的组成部分（OneModel+OneID+OneService） | C（厂商博客）；官方仅有邻近能力（ID Mapping） |
| **OneService** | 数据只能"取"，不能"服务化"复用；接口各自为政 | 主题式数据单元 + 统一 API 出口 | 同上，OneData 的消费端 | C |
| **数据中台** | 组织级：把公共数据能力沉淀为可复用资产，供多业务线共享 | 组织 + 平台 + 治理机制 | 比 OneData 更大；OneData 是其中一套建设方法 | C（行业/厂商叙述） |
| **Dataphin** | 上述方法论的落地平台：集成、规范建模、指标定义、资产治理、数据服务 | 商业产品（SaaS/半托管/独享） | OneData 的产品化载体 | A |

- 结论：OneData 不是一个"数据模型"，而是一套**从规范定义到模型落地的建设与治理方法**；它的最小可复用单元是"规范定义"（数据域、业务过程、维度、原子指标、业务限定、统计周期、派生指标）。
- 来源：逻辑结构说明（核心概念）/ https://help.aliyun.com/zh/dataphin/product-overview/logical-structure-that / 未标注更新时间
- 性质：官方文档
- 核实状态：已核实

- 结论：官方文档只承诺"Dataphin 基于阿里内部 OneData 数据治理方法论"，并未给出 OneData 的方法论全文；因此凡涉及"OneData 要求必须如何"的强断言，若无帮助中心对应条目，只能算二手经验。
- 来源：What is Dataphin（EN）/ 同上
- 性质：官方文档
- 核实状态：已核实

**对本项目的含义**：可以放心借"Dataphin 帮助中心里写死的规则"，不要借"某篇文章总结的 OneData 十大原则"。

---

## 2. 分层规范：ODS → DWD → DWS → ADS

### 2.1 官方分层其实是"三层 + 细分"

官方口径是 **ODS / CDM / ADS** 三层，CDM 再细分为 **DIM（维度层）、DWD（明细层）、DWS（汇总层）**。我们常说的"ODS→DWD→DWS→ADS 四层"是工程化拆解，不是官方原始命名。

- 结论：官方分层为 ODS（数据引入层）、CDM（数据公共层，含 DIM/DWD/DWS）、ADS（数据应用层）；"四层"说法是行业对 CDM 的再拆分。
- 来源：数仓分层 / https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/several-positions-layered / 更新 2023-07-07
- 性质：官方文档
- 核实状态：已核实

### 2.2 各层职责与建模方式

| 层 | 职责 | 建模方式 | 放什么 | 不放什么 |
|---|---|---|---|---|
| **ODS** | 源系统数据几乎原样同步入仓，是数据准备区 | 不做维度建模；保持源表结构；分区（ds）+ 生命周期 | 原始表、增量/全量标识（di/df） | 指标计算、跨源 join 结果、业务语义改写 |
| **DIM** | 统一描述实体属性与层级 | 维度建模（雪花，减少冗余） | 一实体一维表：主键、属性、层级、关联维度 | 度量值、事实明细 |
| **DWD** | 按业务过程构建最细粒度事实 | 维度建模（星型/雪花），可宽表化冗余维度属性 | 一业务过程一事实表；事务型（di）/周期快照型（df）；该过程的度量 | 其他业务过程的度量（下单表不得含支付金额）、多种粒度混存 |
| **DWS** | 按分析主题构建公共粒度汇总 | 维度建模 + 宽表化预聚合 | 一表对应一个统计粒度 + 该粒度下若干派生指标 | 明细数据、跨事实的聚合结果 |
| **ADS** | 面向具体产品/报表的个性化结果 | 反范式宽表、按需加工 | 某产品口径的最终指标结果 | 回灌公共层、被公共层反向引用 |

- 结论：DWD 的事实表设计有四条硬约束——先声明粒度、只放与业务过程相关的事实、同表不混粒度、同表度量单位一致。
- 来源：明细数据层（DWD）/ https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/the-detail-data-layer / 更新 2023-07-07
- 性质：官方文档
- 核实状态：已核实

- 结论：DWS 的汇总"不跨越事实"——聚集的维度与度量必须与原始模型一致，因此**原子指标只能基于一张事实表定义**；跨事实的组合只能走"衍生原子指标"。
- 来源：汇总数据层（DWS）/ https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/summary-data-layer / 更新 2021-10-25
- 性质：官方文档
- 核实状态：已核实

- 结论：DWS 一张表对应一个统计粒度（维度或维度组合），承载该粒度下的若干派生指标；这是"指标卡按粒度归档"的直接依据。
- 来源：汇总数据层（DWS）/ 同上
- 性质：官方文档
- 核实状态：已核实

### 2.3 跨层引用规则（官方明文）

- 结论：ADS 优先调用 CDM；已有 CDM 数据时，ADS 不得绕过 CDM 从 ODS 重复加工；ODS 数据不能被应用层任务直接引用（中间层未沉淀时，通过 CDM 视图访问）。
- 来源：层次调用规范（DataWorks）/ https://help.aliyun.com/zh/dataworks/user-guide/principles-for-using-data-at-different-data-layers / 更新 2026-05-27
- 性质：官方文档
- 核实状态：已核实

- 结论：CDM 汇总层优先调用明细层，并尽量复用已产出的粗粒度汇总；CDM 明细层累计快照事实表优先调用事务型事实表；CDM 任务深度建议 ≤10 层。
- 来源：层次调用规范（DataWorks）/ 同上
- 性质：官方文档
- 核实状态：已核实

- 结论：官方两处表述存在不一致：Dataphin"数仓分层"页写 ADS 由"CDM 层与 ODS 层加工生成"，而 DataWorks/MaxCompute"层次调用规范"禁止应用层直接引用 ODS。落地时应采用更严格的后者。
- 来源：数仓分层（Dataphin）/ 同上；层次调用规范（DataWorks）/ 同上
- 性质：官方文档（两页冲突）
- 核实状态：已核实（冲突本身可核实），冲突原因未核实

### 2.4 为什么禁止 DWS 反向依赖 ADS

**官方没有一句"禁止 DWS 引用 ADS"的明文。** 这是由"调用只能向下"的整体规范和调度依赖方向推出的，属推论，必须与"官方规则"区分。

- 结论：官方未明文禁止 DWS 引用 ADS；但层次调用规范确立了"应用层调用公共层、公共层调用更下层"的单向原则，反向依赖与之相悖。
- 来源：层次调用规范（DataWorks）/ 同上
- 性质：行业实践总结（推论）
- 核实状态：未核实（帮助中心无对应条文）

三条可解释的后果（推论，供评审时讲清理由）：
1. **依赖成环**：ADS 依赖 DWS、DWS 又依赖 ADS，调度无法拓扑排序，重跑无法收敛。
2. **口径污染**：ADS 是单产品个性化口径，一旦被公共层引用，公共层就被某个产品的口径绑死，失去复用价值。
3. **责任倒挂**：公共层本应定义"唯一口径"，反向依赖等于让下游定义上游，口径变更无法追责。

---

## 3. 指标定义体系（重点）

### 3.1 三类指标与构成要素

| 类型 | 官方定义要点 | 构成 | 例子 |
|---|---|---|---|
| **原子指标** | 对指标统计口径、具体算法的抽象；绑定一张维度/事实逻辑表；含度量单位、数据类型、指标口径、计算逻辑、是否可累加 | 业务过程 + 度量 + 计算逻辑（+ 可累加性） | 支付金额 = `sum(pay_amt)` |
| **业务限定** | 统计的业务范围，类似 SQL 的 WHERE（**不含时间区间**） | 一组条件 | 支付宝支付、男性客户 |
| **统计周期** | 派生指标来源数据的时间跨度 | 最近 1 天 / 7 天 / 30 天… | 最近 7 天 |
| **统计粒度** | 统计分析的对象/视角，即聚合的 GROUP BY | 维度或维度组合 | 买家、门店、省份 |
| **派生指标** | 原子指标 + 业务限定 + 统计周期 + 统计粒度 | 四元组 | 最近 7 天买家支付宝支付金额 |
| **衍生原子指标** | 基于**已提交原子指标**设定计算逻辑而成 | 已提交原子指标 + 表达式 | 人均支付金额 = 支付金额 / 支付人数 |
| **复合指标** | 由**派生指标**通过运算规则计算 | 派生指标 + 运算（比值/同环比/差值） | 最近 30 天转化率 = 买家数 / 访客数 |

- 结论：派生指标 = 原子指标 + 业务限定 + 统计周期 + 统计粒度；其中统计周期与统计粒度必选，业务限定可选；派生指标唯一归属于一个原子指标，并继承其主题域。
- 来源：明确统计指标 / https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/the-statistical-index / 更新 2024-12-31
- 性质：官方文档
- 核实状态：已核实

- 结论：创建派生指标有两条硬约束——原子指标与业务限定必须来自同一张维表/事实表，且数据时效相同；派生指标必须能落到一个统计粒度上。
- 来源：创建派生指标 / https://help.aliyun.com/zh/dataphin/fullmanaged/user-guide/create-derived-metrics / 更新 2026-01-27
- 性质：官方文档
- 核实状态：已核实

- 结论：原子指标必须标注"是否可累加"；去重计数类指标不可累加（如各品牌购买人数相加会重复计人），这是防止上层错误汇总的关键字段。
- 来源：创建原子指标 / https://help.aliyun.com/zh/dataphin/fullmanaged/user-guide/creating-atomic-metrics / 更新 2026-09-08
- 性质：官方文档
- 核实状态：已核实

- 结论：衍生指标不能凭空造：它必须引用**已提交**的原子指标作为输入，并在"指标口径"（自然语言，≤1000 字）与"计算逻辑"（表达式）两处同时留痕；平台会维护"相关指标"（由该原子指标派生出的全部指标）。
- 来源：创建衍生原子指标 / https://help.aliyun.com/zh/dataphin/semimanaged-v4/user-guide/create-a-composite-metric / 更新 2025-05-28；管理原子指标 / 见 §5
- 性质：官方文档
- 核实状态：已核实

- 结论：复合指标是"派生指标之间的运算"，不是"原子指标之间的运算"；Dataphin 与 DataWorks 均如此定义，并支持同环比、差值等。
- 来源：复合指标（DataWorks）/ https://help.aliyun.com/zh/dataworks/user-guide/composite-indicators / 更新 2026-06-02；Create derived and composite metrics（Dataphin EN）/ https://www.alibabacloud.com/help/en/dataphin/semimanaged-v4/user-guide/create-a-logical-summary-table / 更新 2026-06-04
- 性质：官方文档
- 核实状态：已核实

**派生链怎么记录（官方做法，可直接抄）**：
1. 原子指标记录：来源逻辑表、统计周期标识字段、计算逻辑、可累加性、主题域。
2. 派生指标记录：所引用的原子指标（唯一）、业务限定、统计周期、统计粒度。
3. 衍生原子指标记录：`指标口径`（自然语言）+ `计算逻辑`（引用已提交原子指标的表达式）+ `可引用列表`。
4. 复合指标记录：引用的派生指标 + 运算规则（表达式或同环比配置）。
5. 反向可查：原子指标详情页的"相关指标"列出其全部下游派生/衍生/复合指标——这是变更影响面分析的入口。

### 3.2 这套三段式能否直接写"指标卡"？

**能，但指标卡应锚定"原子指标 + 派生规则"，而不是锚定一次报表结果。** 直接照搬"派生指标"会把指标卡做成"某张报表的口径"，无法复用。

建议映射（指标卡字段 ← OneData 元素）：

| 指标卡字段 | 取自 OneData | 说明 |
|---|---|---|
| 指标 ID / 中文名 / 英文名 | 派生指标命名（见 §5） | 英文名按 `{原子}_{周期}_{限定}` 生成 |
| 度量定义 | 原子指标（计算逻辑 + 来源主表） | 必须写清聚合函数与字段 |
| 口径描述 | 指标口径（自然语言 ≤1000 字） | 业务可读版本 |
| 修饰词清单 | 业务限定（逐条枚举） | 每条限定须可判定、可枚举 |
| 时间周期 | 统计周期 | 与调度频率分开记录 |
| 统计粒度 | 统计粒度 | 明确 GROUP BY 维度 |
| 可累加性 | 原子指标字段 | 标注可加 / 半可加 / 不可加 |
| 单位 / 数据类型 | 度量单位 / 数据类型 | 防止"元 vs 万元"类事故 |
| 派生链 | 原子指标 → 派生指标 → 衍生/复合 | 记录引用 ID，而非文字描述 |
| 数据来源 | 来源主表（仅事实/维度逻辑表） | 物理定位另存，避免与语义混淆 |
| 版本 / 状态 / 负责人 | 版本信息 + 业务/运维负责人 | 见 §5 |

- 结论：三段式可以直接映射为指标卡主体，但 OneData 不提供四项内容，需要我们在卡上补齐：**生效区间、口径变更记录（含旧值）、口径边界/排除条件、物理数据定位**。
- 来源：综合 §3.1 各官方页；缺口判断为本文件推论
- 性质：行业实践总结
- 核实状态：未核实（属映射设计，不是官方结论）

- 结论：不建议把"复合指标"塞进单张指标卡；复合指标本质是"指标间运算"，应单独建"计算规则卡"，只引用指标 ID，避免口径二次描述。
- 来源：复合指标（DataWorks）/ 同上
- 性质：行业实践总结
- 核实状态：未核实（属设计建议）

---

## 4. 一致性维度与一致性事实

### 4.1 为什么建

- 结论：维度在企业级数仓中必须唯一；在 Dataphin 中，**每个维度在所属业务板块内有且只有一种定义**，这样同一维度在不同业务过程中传达的信息才一致。
- 来源：定义维度与构建总线矩阵 / https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/define-the-dimensions-and-construction-bus-matrix / 更新 2023-12-06
- 性质：官方文档
- 核实状态：已核实

- 结论：官方用"总线矩阵"把"主题域 × 业务过程"与"一致性维度"交叉标注（Y/N），以此指导事实模型该关联哪些维度。
- 来源：定义维度与构建总线矩阵 / 同上
- 性质：官方文档
- 核实状态：已核实

- 结论：一致性维度（conformed dimension）指多个事实表复用同一套维度键、属性与取值，从而支持跨事实的 drill-across；一致性事实（conformed fact）指同一度量在不同事实表中名称、定义、单位一致，可安全相加或比较。
- 来源：Kimball Group, Dimensional Modeling Techniques（2013）/ https://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf
- 性质：官方理论文档（B 级）
- 核实状态：部分核实（已核实其为 Kimball 术语体系；一致性事实的完整原文段落未取到，定义按通行表述）

### 4.2 跨主题域（银行/保险多业务线）怎么做

可执行做法（按优先级）：
1. **先定公共维度，再挂业务过程**：客户、机构、产品、账户、日期、渠道六类通常先做一致性维度；每个维度指定唯一 Owner。
2. **代理键统一**：同一实体在各业务线的维表使用同一代理键生成规则；源系统自然键只作属性。
3. **总线矩阵评审**：新建事实表前，必须在矩阵上标出用到哪些一致性维度；未列入的维度需走"新增维度"评审，不得私建。
4. **属性口径登记**：维度属性（如"客户等级""机构层级"）的口径写入指标卡/维度卡，变更走版本流程。
5. **共享而非复制**：业务线引用同一维表（或视图），不允许各自复制一份再改名。

- 结论：跨业务线复用失败，多数不是"维表建错"，而是"维度属性口径分叉 + 无 Owner 仲裁"；一旦各业务线各自维护客户等级，后续任何跨线汇总都不可信。
- 来源：综合 §4.1；成因为本文件归纳
- 性质：行业实践总结
- 核实状态：未核实（属归纳，无单一出处）

**失败案例（公开资料能给到的）**：
- 结论：阿里内部曾因"卖家侧（小二）与商家侧"数据口径不一致，导致商家按错误预测备货、活动报名未通过；这是公开叙述中少见的、直接由口径不一致造成业务损失的案例。
- 来源：《Dataphin 的前世今生：缘起》/ https://developer.aliyun.com/article/785026 / 2021-07-03
- 性质：二手解读（厂商博客，非事故报告）
- 核实状态：未核实（无原始事故记录，仅单方叙述）

- 结论：银行数据仓库建设中的语义异质性（同一术语在不同部门/系统定义不同）是已被学术研究确认的结构性难题，跨业务线复用一致性维度必须先解决语义统一。
- 来源：Rosenkranz et al., "Supporting Financial Data Warehouse Development: A Communication Theory-Based Approach", ICIS 2010 / http://aisel.aisnet.org/cgi/viewcontent.cgi?article=1011&context=icis2010_submissions
- 性质：二手解读（学术论文）
- 核实状态：已核实（论文摘要明确语义异质性高）

- 结论：**未找到**可公开核实的具体"某银行/保险公司因一致性维度建设失败"的完整案例（含公司名、时间、损失）；市面文章多为泛化描述，不能当案例引用。
- 来源：检索结论（无对应文献）
- 性质：—
- 核实状态：未核实（公开资料缺失）

---

## 5. 命名与口径管理（重点）

### 5.1 命名规范（官方明文）

- 结论：派生指标英文名由系统按 `{原子指标英文名}_{统计周期缩写}_{业务限定英文名}` 预生成，首位必须为字母，仅允许字母/数字/下划线，≤100 字符，且**在汇总表内唯一**。
- 来源：创建派生指标 / https://help.aliyun.com/zh/dataphin/fullmanaged/user-guide/create-derived-metrics / 更新 2026-01-27
- 性质：官方文档
- 核实状态：已核实

- 结论：原子指标英文名 ≤64 字符（字母/数字/下划线），输入时会实时匹配"数据标准"中已配置的**词根**并推荐；表命名：事实表 `fct_{业务过程缩写}[_{标签}]_{di/df}`，汇总表 `dws_{统计粒度}`，ODS 表名尽量与源系统一致。
- 来源：创建原子指标 / 同上；明细数据层（DWD）/ 同上；汇总数据层（DWS）/ 同上；数据引入层（ODS）/ https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/introduced-data-layer / 更新 2023-07-07
- 性质：官方文档
- 核实状态：已核实

### 5.2 口径变更治理（官方机制）

- 结论：原子指标每次"保存并提交"生成一个新版本；版本信息含版本号、修改人、创建时间、状态、备注，支持版本详情、版本对比（差异高亮）与回滚（回滚不可撤销）。
- 来源：管理原子指标 / https://help.aliyun.com/zh/dataphin/fullmanaged/user-guide/untitled-document-1746523143119 / 更新 2025-06-24
- 性质：官方文档
- 核实状态：已核实

- 结论：指标不可随意删除：草稿才可删除；已提交的只能"下线"；"下线并删除"时**若存在依赖对象则操作不生效**——先解依赖，再下线。
- 来源：管理原子指标 / 同上
- 性质：官方文档
- 核实状态：已核实

- 结论：存在开发状态机（草稿 → 提交中 → 已提交 / 开发中），Dev-Prod 模式下提交后还需发布到生产；提交时必须填写提交备注。
- 来源：管理原子指标 / 同上；创建派生指标 / 同上
- 性质：官方文档
- 核实状态：已核实

- 结论：复合指标"每次提交生成一个新版本，每个版本提交成功后不可重复提交"，并提供版本对比与回滚。
- 来源：复合指标（DataWorks）/ https://help.aliyun.com/zh/dataworks/user-guide/composite-indicators / 更新 2026-06-02
- 性质：官方文档
- 核实状态：已核实

- 结论：官方文档**未**描述指标变更的"审批流"（谁批准、几人会签）；只有提交/发布动作。把"审批"写成 OneData 的官方要求属于过度引申。
- 来源：管理原子指标、创建派生指标（均无审批章节）
- 性质：—
- 核实状态：未核实（官方材料缺失）

### 5.3 "同名不同义 / 同义不同名"的处理机制

官方现有机制（可核实的部分）：
1. **唯一归属**：派生指标只能归属一个原子指标 → 同名指标无法挂到两个不同度量上。
2. **唯一性约束**：派生指标英文名在汇总表内唯一；维度在业务板块内唯一。
3. **强制命名结构**：`原子_周期_限定` 把差异暴露在名字里，减少"同名"空间。
4. **词根/数据标准**：新建指标时匹配已配置词根，抑制同义不同名。
5. **影响面可见**：原子指标的"相关指标"列出全部下游，改名前可先看影响。

- 结论：Dataphin 用"唯一归属 + 唯一命名 + 词根"压制同名/同义问题，但**没有可核实的官方"同义词表/别名表"机制**；同义不同名主要靠词根与评审，不靠系统强制。
- 来源：创建原子指标、创建派生指标、管理原子指标 / 同上
- 性质：官方文档（机制存在性）+ 本文件推论（缺失项）
- 核实状态：部分核实

**给我们口径卡的落地建议**（不是官方要求）：
- 一指标一稳定 ID（不随名称变），名称与别名分离存放；改名不改 ID。
- 别名表只增不删，每条别名记录来源（哪个报表/哪个部门这样叫）。
- 口径卡必须写"排除条件/边界"，因为同名不同义多半死在边界（是否含退款、是否含税、是否去重）。
- 变更记录保留旧口径原文，不做覆盖式编辑；用版本号 + 生效日期，而不是"最后修改时间"。
- 废弃用"下线"而非删除，保留可追溯性。

---

## 6. 与 FS-LDM 的关系

### 6.1 两者是什么

- 结论：FS-LDM（Financial Services Logical Data Model）是 Teradata 的金融行业**逻辑数据模型**（iLDM 之一），以 ERwin 模型文件交付；当前版本含 3,100+ 实体、12,700+ 属性、5,100+ 关系，覆盖零售/对公银行、经纪、投资、信用卡、财险与寿险。
- 来源：The Financial Services Logical Data Model（Steve Hoberman，Teradata 白皮书）/ https://assets.teradata.com/resourceCenter/downloads/WhitePapers/EB6546.pdf / 出版日期未标注（作者引用 2013 年前后资料）
- 性质：厂商白皮书（B 级）
- 核实状态：已核实（实体/属性/关系数量与覆盖范围均在白皮书正文）

- 结论：OneData 的"数据域/主题域"是面向分析的主题边界（如商品域、交易域、会员域），"业务过程"是不可拆分的业务活动事件（下单、支付、发货、确认收货）；它们用来组织事实表与指标，不描述实体关系。
- 来源：逻辑结构说明 / https://help.aliyun.com/zh/dataphin/product-overview/logical-structure-that ；明细数据层（DWD）/ 同上
- 性质：官方文档
- 核实状态：已核实

### 6.2 能不能一对一映射

**不能。二者不是同类物。**

| 维度 | FS-LDM | OneData |
|---|---|---|
| 本质 | 逻辑数据模型（实体—关系，ER） | 数据分层 + 指标治理方法论 |
| 建模对象 | 实体、属性、关系、主题域 | 数据域、业务过程、维度、指标 |
| 粒度 | 实体级（Party/Agreement/Event 等） | 业务过程级 + 统计粒度（维度组合） |
| 用途 | 定义"数据长什么样"、跨系统统一语义 | 定义"数据怎么分层加工、指标怎么算" |
| 变更驱动 | 模型版本（ERwin 文件） | 指标版本 + 分层规范 |

- 结论：不能做"FS-LDM 主题域 = OneData 数据域"的一对一映射：FS-LDM 的主题域是**实体归类**，OneData 的数据域是**分析主题 + 业务过程集合**，边界依据不同；强行对齐会产生大量多对多关系。
- 来源：综合 §6.1 两处来源
- 性质：行业实践总结（分析结论）
- 核实状态：未核实（无官方对照文档；结论由定义推导）

- 结论：唯一可做的局部近似是"FS-LDM 实体 → OneData 维度/业务对象"，但仍需先做粒度对齐与命名统一，且不能反向推出业务过程。
- 来源：同上
- 性质：行业实践总结
- 核实状态：未核实（属映射设计）

**正确用法**：把 FS-LDM 当"实体与属性的权威词典 + 逻辑模型基线"，把 OneData 当"指标卡与口径治理的骨架"；两者在"维度/实体"这一层握手，不在"域"这一层硬凑。

---

## 7. 可借用 / 不适用

### 7.1 可直接借用（8 条，每条一句话、可执行）

1. **指标卡强制四元组**：原子指标 + 业务限定 + 统计周期 + 统计粒度，缺一项不签发。
2. **唯一归属**：每个指标只挂一个原子指标，并登记来源主表；禁止跨表拼装"原子指标"。
3. **可累加性标注**：每个原子指标必须标"可加/半可加/不可加"，去重计数一律不可加。
4. **固定命名结构**：`{原子}_{周期}_{限定}`，全局唯一，改名不改 ID。
5. **只下线不删除**：有下游依赖时先解依赖再生产下线；历史版本与旧口径原文保留。
6. **变更即新版本**：每次口径变更生成新版本，必填变更备注，保留版本对比与可回滚点（单机可用 Git/版本表实现）。
7. **维度域内唯一**：一实体一维表一主键，跨业务线共享同一维表，不复制不改名。
8. **先声明粒度**：任何度量入卡前先写清统计粒度与单位；同一事实不混粒度、不混单位。

（第 9 条可选）公共处理逻辑下沉到最底层只加工一次，上层只引用不重算。

### 7.2 不适用（4 条，附原因）

1. **ODS/DIM/DWD/DWS/ADS 物理分层 + `fct_/dws_` 表名 + `di/df` 后缀 + `ds` 分区 + LIFECYCLE**：我们没有 Hive/ODPS/MaxCompute，单机存储无需分区与生命周期管理；照搬会增加无收益的维护成本。
2. **DWS 预聚合物化宽表**：预聚合是为大数据量下的查询性能；单机小规模下，预聚合带来的"改口径要重刷汇总"的一致性成本大于性能收益。
3. **Dev-Prod 双环境发布 + 调度依赖体系**：无调度平台与多环境；用 Git 分支 + 评审 + 版本记录替代即可，不必模拟"提交—发布—生产"流程。
4. **数据板块/项目级物理隔离与多租户权限**：单机单团队场景不需要命名空间隔离与租户权限模型；强行引入会让指标卡流程变重。

（可选第 5 条）**平台化血缘/资产地图**：没有元数据平台，血缘靠指标卡里的"引用 ID"手工维护即可，不必追求自动血缘。

---

## 8. 参考来源清单

**A 级（官方帮助中心/产品文档）**
1. 数仓分层（Dataphin，2023-07-07）https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/several-positions-layered
2. 数据引入层 ODS（2023-07-07）https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/introduced-data-layer
3. 明细数据层 DWD（2023-07-07）https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/the-detail-data-layer
4. 汇总数据层 DWS（2021-10-25）https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/summary-data-layer
5. 明确统计指标（2024-12-31）https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/the-statistical-index
6. 定义维度与构建总线矩阵（2023-12-06）https://help.aliyun.com/zh/dataphin/fullmanaged/getting-started/define-the-dimensions-and-construction-bus-matrix
7. 逻辑结构说明（核心概念）https://help.aliyun.com/zh/dataphin/product-overview/logical-structure-that
8. 创建原子指标（2026-09-08）https://help.aliyun.com/zh/dataphin/fullmanaged/user-guide/creating-atomic-metrics
9. 创建派生指标（2026-01-27）https://help.aliyun.com/zh/dataphin/fullmanaged/user-guide/create-derived-metrics
10. 创建衍生原子指标（2025-05-28）https://help.aliyun.com/zh/dataphin/semimanaged-v4/user-guide/create-a-composite-metric
11. 管理原子指标（2025-06-24）https://help.aliyun.com/zh/dataphin/fullmanaged/user-guide/untitled-document-1746523143119
12. 层次调用规范（DataWorks，2026-05-27）https://help.aliyun.com/zh/dataworks/user-guide/principles-for-using-data-at-different-data-layers
13. 复合指标（DataWorks，2026-06-02）https://help.aliyun.com/zh/dataworks/user-guide/composite-indicators
14. What is Dataphin（EN，2026-03-30）https://help.aliyun.com/en/dataphin/fullmanaged/product-overview/what-is-a-dataphin
15. Dataphin 简介（2025-05-26）https://help.aliyun.com/zh/dataphin/introduction-to-dataphin
16. Create derived and composite metrics（Dataphin EN，2026-06-04）https://www.alibabacloud.com/help/en/dataphin/semimanaged-v4/user-guide/create-a-logical-summary-table
17. Dataphin 产品页 https://www.alibabacloud.com/de/product/dataphin

**B 级（白皮书/理论文档）**
18. Teradata FS-LDM 白皮书（Steve Hoberman）https://assets.teradata.com/resourceCenter/downloads/WhitePapers/EB6546.pdf
19. Kimball Group, Dimensional Modeling Techniques（2013）https://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf

**C 级（二手解读）**
20. 《大数据之路：阿里巴巴大数据实践——OneData数据中台体系》（2025-08-02）https://developer.aliyun.com/article/1674625
21. 《Dataphin 的前世今生：缘起》（2021-07-03）https://developer.aliyun.com/article/785026
22. ICIS 2010，银行数仓语义异质性论文 http://aisel.aisnet.org/cgi/viewcontent.cgi?article=1011&context=icis2010_submissions
