# 术语层 LLM 两轮判定记录

> 本文件由一次性脚本生成，仅用于留痕。模型来自平台现有配置 `PLATFORM__LLM__*`（ark / DeepSeek），Base URL 为 coding plan 端点；**密钥不入档、不进日志**。

- 生成时间（脚本时钟）：2026-11-05 22:07:27，总耗时 122.0s
- 模型：`deepseek-v4-1-flash-261017`；provider：`ark`；temperature=0.2, response_format=json_object
- 覆盖类数：26；批次：6 × 2 轮

## 一、Prompt 摘要

- 第一轮 system：金融监管术语审校员；只接受监管/信贷/保险通用说法；必须同义（排除上下位、组成部分、相关概念）；无把握返回空；只输出 JSON。
- 第一轮 user：每类生成 0-5 个中文业务别名，每条附 `why`（一句理由）与 `ambiguity`（一句潜在歧义）。
- 第二轮 system：自我反驳；drop 条件为营销词/网络说法/内部简称/多义词/非同义/与本批类名重复。
- 第二轮 user：把第一轮候选连同本批全部类名一起回灌，逐条 keep/drop。

## 二、原始输出

### Round 1 / Batch 1

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是金融监管术语审校员。任务：给一个本体类找业务别名。硬规则：1) 只输出金融监管、信贷、保险业务中的通用说法，不是营销词、网络用语、公司内部简称；2) 别名必须与给定中文名同义（不是上下位、不是组成部分、不是相关概念）；3) 不要编造定义，不要输出你不确定的词；4) 如无可靠别名，candidates 返回空数组。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "为下列本体类各生成 0-5 个中文业务别名（可含行业通用缩写）。输出格式：{\"items\":[{\"iri\":\"...\",\"candidates\":[{\"term\":\"...\",\"why\":\"一句理由\",\"ambiguity\":\"你看到的一句潜在歧义\"}]}]}\n[{\"iri\": \"fsldm:Party\", \"prefLabel\": \"当事人\", \"fsldmEntity\": \"PARTY\", \"subjectArea\": \"Party\", \"ontologyComment\": \"\"}, {\"iri\": \"party:Individual\", \"prefLabel\": \"个人\", \"fsldmEntity\": \"INDIVIDUAL\", \"subjectArea\": \"Party\", \"ontologyComment\": \"\"}, {\"iri\": \"party:Organization\", \"prefLabel\": \"机构\", \"fsldmEntity\": \"ORGANIZATION\", \"subjectArea\": \"Party\", \"ontologyComment\": \"\"}, {\"iri\": \"party:Household\", \"prefLabel\": \"家庭\", \"fsldmEntity\": \"HOUSEHOLD\", \"subjectArea\": \"Party\", \"ontologyComment\": \"\"}, {\"iri\": \"party:PartyGroup\", \"prefLabel\": \"当事人分组\", \"fsldmEntity\": \"PARTY GROUP\", \"subjectArea\": \"Party\", \"ontologyComment\": \"\"}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"fsldm:Party","candidates":[{"term":"当事方","why":"与“当事人”同义，指法律或交易关系中的一方","ambiguity":"在部分文件中“当事方”更偏合同语境"}]},{"iri":"party:Individual","candidates":[{"term":"自然人","why":"金融监管和信贷业务中用于指称作为当事人的个人","ambiguity":"法律上“自然人”与“个人”基本对应，但有时与个体工商户等经营主体并列使用"}]},{"iri":"party:Organization","candidates":[{"term":"组织机构","why":"与“机构”同义，指作为当事人的组织实体","ambiguity":"可能被理解为机构内部组织架构"},{"term":"非自然人","why":"反洗钱、信贷等业务中常用以统称机构类当事人","ambiguity":"是相对于自然人的宽泛分类，未必等同所有法律意义上的机构"}]},{"iri":"party:Household","candidates":[{"term":"住户","why":"统计和信贷业务中常用指家庭户/住户单位","ambiguity":"也可指居住单元或住户房屋"},{"term":"家庭户","why":"户籍和客户管理语境中与家庭作为当事人单位同义","ambiguity":"带有户籍登记色彩，不一定等同经济家庭"},{"term":"居民家庭","why":"消费信贷、保险等业务中常指作为一类当事人的家庭","ambiguity":"偏统计/零售业务口径，可能仅指居民家庭"}]},{"iri":"party:PartyGroup","candidates":[{"term":"当事人组","why":"将若干当事人作为一个组处理的同义说法","ambiguity":"可能被理解为临时的数据分组而非业务实体"},{"term":"当事方分组","why":"与“当事人分组”同义，指对当事方进行的分组","ambiguity":"“分组”也可指操作动作"}]}]}
```

usage：`{"completion_tokens": 2431, "prompt_tokens": 422, "total_tokens": 2853, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 2038}}`

### Round 1 / Batch 2

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是金融监管术语审校员。任务：给一个本体类找业务别名。硬规则：1) 只输出金融监管、信贷、保险业务中的通用说法，不是营销词、网络用语、公司内部简称；2) 别名必须与给定中文名同义（不是上下位、不是组成部分、不是相关概念）；3) 不要编造定义，不要输出你不确定的词；4) 如无可靠别名，candidates 返回空数组。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "为下列本体类各生成 0-5 个中文业务别名（可含行业通用缩写）。输出格式：{\"items\":[{\"iri\":\"...\",\"candidates\":[{\"term\":\"...\",\"why\":\"一句理由\",\"ambiguity\":\"你看到的一句潜在歧义\"}]}]}\n[{\"iri\": \"party:PartyRiskGrade\", \"prefLabel\": \"当事人风险等级\", \"fsldmEntity\": \"PARTY RISK GRADE\", \"subjectArea\": \"Party\", \"ontologyComment\": \"\"}, {\"iri\": \"fsldm:Agreement\", \"prefLabel\": \"协议\", \"fsldmEntity\": \"AGREEMENT\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}, {\"iri\": \"agmt:Account\", \"prefLabel\": \"账户\", \"fsldmEntity\": \"ACCOUNT\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}, {\"iri\": \"agmt:CreditAgreement\", \"prefLabel\": \"授信协议\", \"fsldmEntity\": \"CREDIT AGREEMENT\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}, {\"iri\": \"agmt:Policy\", \"prefLabel\": \"保单\", \"fsldmEntity\": \"POLICY\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"party:PartyRiskGrade","candidates":[{"term":"当事人风险评级","why":"与“当事人风险等级”同指对当事人风险高低的评级结果，仅“等级/评级”用词差异。","ambiguity":"“评级”有时也指评级过程或评级体系，而非等级结果。"}]},{"iri":"fsldm:Agreement","candidates":[{"term":"合同","why":"在金融业务中“协议”与“合同”常作为同义法律文件名称互换使用。","ambiguity":"法律语境下合同可能被视为协议的更正式子类。"},{"term":"合约","why":"金融业务中常用“合约”指代具有法律约束力的协议安排。","ambiguity":"“合约”在衍生品等场景更常用，可能带特定业务范围色彩。"}]},{"iri":"agmt:Account","candidates":[]},{"iri":"agmt:CreditAgreement","candidates":[{"term":"授信合同","why":"与“授信协议”同指银行给予授信额度及条件的合同文件。","ambiguity":"不同机构可能将授信合同与具体贷款合同区分使用。"},{"term":"信贷协议","why":"信贷业务中常与“授信协议”互换，指信贷安排的法律协议。","ambiguity":"“信贷”范围可能覆盖授信以外的具体贷款安排。"}]},{"iri":"agmt:Policy","candidates":[{"term":"保险单","why":"“保单”是“保险单”的常用简称，二者同指保险合同凭证。","ambiguity":"严格法律语境下保险单是保险合同凭证，未必等同于保险合同本身。"}]}]}
```

usage：`{"completion_tokens": 2182, "prompt_tokens": 435, "total_tokens": 2617, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 1834}}`

### Round 1 / Batch 3

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是金融监管术语审校员。任务：给一个本体类找业务别名。硬规则：1) 只输出金融监管、信贷、保险业务中的通用说法，不是营销词、网络用语、公司内部简称；2) 别名必须与给定中文名同义（不是上下位、不是组成部分、不是相关概念）；3) 不要编造定义，不要输出你不确定的词；4) 如无可靠别名，candidates 返回空数组。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "为下列本体类各生成 0-5 个中文业务别名（可含行业通用缩写）。输出格式：{\"items\":[{\"iri\":\"...\",\"candidates\":[{\"term\":\"...\",\"why\":\"一句理由\",\"ambiguity\":\"你看到的一句潜在歧义\"}]}]}\n[{\"iri\": \"agmt:IndividualInsurancePolicy\", \"prefLabel\": \"个人保险单\", \"fsldmEntity\": \"INDIVIDUAL INSURANCE POLICY\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}, {\"iri\": \"agmt:GroupInsurancePolicy\", \"prefLabel\": \"团体保险单\", \"fsldmEntity\": \"GROUP INSURANCE POLICY\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}, {\"iri\": \"agmt:CommercialInsurancePolicy\", \"prefLabel\": \"商业保险单\", \"fsldmEntity\": \"COMMERCIAL INSURANCE POLICY\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}, {\"iri\": \"ins:InsuranceAgreement\", \"prefLabel\": \"保险合同（保单）\", \"fsldmEntity\": \"INSURANCE AGREEMENT\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}, {\"iri\": \"fsldm:Product\", \"prefLabel\": \"产品\", \"fsldmEntity\": \"PRODUCT\", \"subjectArea\": \"Product\", \"ontologyComment\": \"\"}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"agmt:IndividualInsurancePolicy","candidates":[{"term":"个人保单","why":"保险业务中对个人保险单的常用简称，语义与个人保险单一致。","ambiguity":"可能被泛指个人持有的任何保单，但业务语境下通常即个人保险单。"},{"term":"个险保单","why":"“个险”为个人保险业务的行业通用简称，个险保单即个人保险单。","ambiguity":"“个险”有时指个人保险业务条线，单独出现时需结合上下文确认指保单。"}]},{"iri":"agmt:GroupInsurancePolicy","candidates":[{"term":"团体保单","why":"保险业务中对团体保险单的常用简称，语义与团体保险单一致。","ambiguity":"可能被用于泛指团体持有的保单，但通常即团体保险单。"},{"term":"团险保单","why":"“团险”为团体保险业务的行业通用简称，团险保单即团体保险单。","ambiguity":"“团险”也可指团体保险业务条线，需上下文确认指保单。"}]},{"iri":"agmt:CommercialInsurancePolicy","candidates":[{"term":"商业保单","why":"保险业务中对商业保险单的常用简称，语义与商业保险单一致。","ambiguity":"可能被理解为商业保险公司签发的保单，而非商业保险单这一合同类型。"},{"term":"商业险保单","why":"保险业务中常用“商业险”指商业保险，商业险保单即商业保险单。","ambiguity":"“商业险”常与交强险对举，可能被限缩理解为商业车险保单。"}]},{"iri":"ins:InsuranceAgreement","candidates":[{"term":"保单","why":"保险业务中对保险合同的常用简称，常与保险合同互换使用。","ambiguity":"严格说保单是合同凭证，可能被理解为单证而非合同关系。"},{"term":"保险单","why":"保险单是保险合同的书面凭证，业务中常作为保险合同的同义说法。","ambiguity":"可能侧重指纸质或电子单证，而非合同权利义务本身。"},{"term":"保险契约","why":"保险契约是保险合同的传统同义表述，法律与业务文件中可见。","ambiguity":"偏法律文书用语，日常业务使用频率低于保单。"}]},{"iri":"fsldm:Product","candidates":[]}]}
```

usage：`{"completion_tokens": 2007, "prompt_tokens": 454, "total_tokens": 2461, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 1510}}`

### Round 1 / Batch 4

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是金融监管术语审校员。任务：给一个本体类找业务别名。硬规则：1) 只输出金融监管、信贷、保险业务中的通用说法，不是营销词、网络用语、公司内部简称；2) 别名必须与给定中文名同义（不是上下位、不是组成部分、不是相关概念）；3) 不要编造定义，不要输出你不确定的词；4) 如无可靠别名，candidates 返回空数组。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "为下列本体类各生成 0-5 个中文业务别名（可含行业通用缩写）。输出格式：{\"items\":[{\"iri\":\"...\",\"candidates\":[{\"term\":\"...\",\"why\":\"一句理由\",\"ambiguity\":\"你看到的一句潜在歧义\"}]}]}\n[{\"iri\": \"ins:InsuranceProduct\", \"prefLabel\": \"保险产品\", \"fsldmEntity\": \"INSURANCE PRODUCT\", \"subjectArea\": \"Product\", \"ontologyComment\": \"\"}, {\"iri\": \"fsldm:Metric\", \"prefLabel\": \"度量\", \"fsldmEntity\": \"\", \"subjectArea\": \"\", \"ontologyComment\": \"\"}, {\"iri\": \"fsldm:Asset\", \"prefLabel\": \"资产\", \"fsldmEntity\": \"PARTY ASSET\", \"subjectArea\": \"Asset\", \"ontologyComment\": \"\"}, {\"iri\": \"asset:CollateralItem\", \"prefLabel\": \"抵押物项\", \"fsldmEntity\": \"COLLATERAL ITEM\", \"subjectArea\": \"Asset\", \"ontologyComment\": \"\"}, {\"iri\": \"bank:CollateralAgreement\", \"prefLabel\": \"抵押协议\", \"fsldmEntity\": \"COLLATERAL AGREEMENT\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"ins:InsuranceProduct","candidates":[{"term":"险种","why":"保险业务中常用“险种”指代保险产品类别，可作为保险产品的业务称呼。","ambiguity":"“险种”更常指产品分类或类别，可能不指某一具体产品。"}]},{"iri":"fsldm:Metric","candidates":[{"term":"指标","why":"监管报送、风险计量和信贷业务中通常把metric称为“指标”。","ambiguity":"“指标”也常指考核目标或KPI，含义可能偏业务考核。"}]},{"iri":"fsldm:Asset","candidates":[]},{"iri":"asset:CollateralItem","candidates":[{"term":"押品","why":"银行信贷和监管中常用“押品”统称抵押或质押担保物，与抵押物项对应。","ambiguity":"“押品”可能同时涵盖质押物，范围略宽于严格抵押物。"},{"term":"抵押物","why":"信贷法律文件中常用“抵押物”指作为担保的抵押物项。","ambiguity":"“抵押物”通常指抵押方式下的担保物，可能不含质押物。"}]},{"iri":"bank:CollateralAgreement","candidates":[{"term":"抵押合同","why":"法律和信贷业务中“抵押合同”是设立抵押担保的协议，与抵押协议同义。","ambiguity":"“抵押合同”强调合同文本，可能与协议框架文件有细微差别。"}]}]}
```

usage：`{"completion_tokens": 1861, "prompt_tokens": 433, "total_tokens": 2294, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 1545}}`

### Round 1 / Batch 5

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是金融监管术语审校员。任务：给一个本体类找业务别名。硬规则：1) 只输出金融监管、信贷、保险业务中的通用说法，不是营销词、网络用语、公司内部简称；2) 别名必须与给定中文名同义（不是上下位、不是组成部分、不是相关概念）；3) 不要编造定义，不要输出你不确定的词；4) 如无可靠别名，candidates 返回空数组。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "为下列本体类各生成 0-5 个中文业务别名（可含行业通用缩写）。输出格式：{\"items\":[{\"iri\":\"...\",\"candidates\":[{\"term\":\"...\",\"why\":\"一句理由\",\"ambiguity\":\"你看到的一句潜在歧义\"}]}]}\n[{\"iri\": \"bank:RiskMitigantAgreement\", \"prefLabel\": \"风险缓释协议\", \"fsldmEntity\": \"RISK MITIGANT AGREEMENT\", \"subjectArea\": \"Agreement\", \"ontologyComment\": \"\"}, {\"iri\": \"agmt:Claim\", \"prefLabel\": \"理赔\", \"fsldmEntity\": \"CLAIM\", \"subjectArea\": \"Event\", \"ontologyComment\": \"\"}, {\"iri\": \"agmt:ClaimCoverage\", \"prefLabel\": \"理赔保障项\", \"fsldmEntity\": \"CLAIM COVERAGE\", \"subjectArea\": \"Event\", \"ontologyComment\": \"\"}, {\"iri\": \"ins:Coverage\", \"prefLabel\": \"保障项\", \"fsldmEntity\": \"COVERAGE FEATURE\", \"subjectArea\": \"Product\", \"ontologyComment\": \"\"}, {\"iri\": \"evt:FinancialEvent\", \"prefLabel\": \"金融事件\", \"fsldmEntity\": \"FINANCIAL EVENT\", \"subjectArea\": \"Event\", \"ontologyComment\": \"\"}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"bank:RiskMitigantAgreement","candidates":[{"term":"风险缓释合同","why":"金融监管文本中合同与协议常作同义表述，均指用于缓释风险的协议安排","ambiguity":"法律文本中合同与协议有时作形式区分，且未限定风险类型"},{"term":"缓释协议","why":"银行业风险监管语境中对风险缓释协议的常见简称","ambiguity":"脱离上下文可能指其他类型的缓释安排"}]},{"iri":"agmt:Claim","candidates":[{"term":"索赔","why":"保险业务中与理赔对应的通用说法，英文claim常译为索赔或理赔","ambiguity":"更侧重提出赔偿请求的行为，可能不等同于保险人理赔处理"},{"term":"赔案","why":"保险理赔中常用的案件称谓，常指一起理赔事项","ambiguity":"指理赔案件或事项，可能不是事件本身"}]},{"iri":"agmt:ClaimCoverage","candidates":[]},{"iri":"ins:Coverage","candidates":[{"term":"保障项目","why":"保险产品中保障项的常见完整说法，指具体保障内容","ambiguity":"可能泛指多个保障项集合，而原类可能指单个保障特征"},{"term":"保险责任","why":"保险条款中表示保障范围的通用术语，常与保障项对应","ambiguity":"通常指保险人承担赔偿或给付责任的范围，可能比单个保障项更宽"},{"term":"保障责任","why":"保险产品中表示具体保障责任的通用说法","ambiguity":"可能指责任范围而非单个保障项"}]},{"iri":"evt:FinancialEvent","candidates":[]}]}
```

usage：`{"completion_tokens": 3381, "prompt_tokens": 444, "total_tokens": 3825, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 3030}}`

### Round 1 / Batch 6

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是金融监管术语审校员。任务：给一个本体类找业务别名。硬规则：1) 只输出金融监管、信贷、保险业务中的通用说法，不是营销词、网络用语、公司内部简称；2) 别名必须与给定中文名同义（不是上下位、不是组成部分、不是相关概念）；3) 不要编造定义，不要输出你不确定的词；4) 如无可靠别名，candidates 返回空数组。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "为下列本体类各生成 0-5 个中文业务别名（可含行业通用缩写）。输出格式：{\"items\":[{\"iri\":\"...\",\"candidates\":[{\"term\":\"...\",\"why\":\"一句理由\",\"ambiguity\":\"你看到的一句潜在歧义\"}]}]}\n[{\"iri\": \"evt:AccountEvent\", \"prefLabel\": \"账户事件\", \"fsldmEntity\": \"ACCOUNT EVENT\", \"subjectArea\": \"Event\", \"ontologyComment\": \"\"}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"evt:AccountEvent","candidates":[]}]}
```

usage：`{"completion_tokens": 219, "prompt_tokens": 259, "total_tokens": 478, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 200}}`

### Round 2 / Batch 1

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是同一术语审校员，现在做自我反驳。对第一轮每个候选逐条判定，verdict 只能是 keep 或 drop。drop 条件：营销词/网络说法/公司内部专用简称/多义词/与给定中文名不是同义关系（上下位或组成部分）/与其他类的中文名重复造成歧义。每条给一句 reason。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "第一轮候选如下。逐条判定并输出：{\"items\":[{\"iri\":\"...\",\"verdicts\":[{\"term\":\"...\",\"verdict\":\"keep|drop\",\"reason\":\"一句\",\"polysemy\":true|false}]}]}\n本批所有类的中文名（用于判重复）：[\"当事人\", \"个人\", \"机构\", \"家庭\", \"当事人分组\", \"当事人风险等级\", \"协议\", \"账户\", \"授信协议\", \"保单\", \"个人保险单\", \"团体保险单\", \"商业保险单\", \"保险合同（保单）\", \"产品\", \"保险产品\", \"度量\", \"资产\", \"抵押物项\", \"抵押协议\", \"风险缓释协议\", \"理赔\", \"理赔保障项\", \"保障项\", \"金融事件\", \"账户事件\"]\n[{\"iri\": \"fsldm:Party\", \"prefLabel\": \"当事人\", \"candidates\": [{\"term\": \"当事方\", \"why\": \"与“当事人”同义，指法律或交易关系中的一方\", \"ambiguity\": \"在部分文件中“当事方”更偏合同语境\"}]}, {\"iri\": \"party:Individual\", \"prefLabel\": \"个人\", \"candidates\": [{\"term\": \"自然人\", \"why\": \"金融监管和信贷业务中用于指称作为当事人的个人\", \"ambiguity\": \"法律上“自然人”与“个人”基本对应，但有时与个体工商户等经营主体并列使用\"}]}, {\"iri\": \"party:Organization\", \"prefLabel\": \"机构\", \"candidates\": [{\"term\": \"组织机构\", \"why\": \"与“机构”同义，指作为当事人的组织实体\", \"ambiguity\": \"可能被理解为机构内部组织架构\"}, {\"term\": \"非自然人\", \"why\": \"反洗钱、信贷等业务中常用以统称机构类当事人\", \"ambiguity\": \"是相对于自然人的宽泛分类，未必等同所有法律意义上的机构\"}]}, {\"iri\": \"party:Household\", \"prefLabel\": \"家庭\", \"candidates\": [{\"term\": \"住户\", \"why\": \"统计和信贷业务中常用指家庭户/住户单位\", \"ambiguity\": \"也可指居住单元或住户房屋\"}, {\"term\": \"家庭户\", \"why\": \"户籍和客户管理语境中与家庭作为当事人单位同义\", \"ambiguity\": \"带有户籍登记色彩，不一定等同经济家庭\"}, {\"term\": \"居民家庭\", \"why\": \"消费信贷、保险等业务中常指作为一类当事人的家庭\", \"ambiguity\": \"偏统计/零售业务口径，可能仅指居民家庭\"}]}, {\"iri\": \"party:PartyGroup\", \"prefLabel\": \"当事人分组\", \"candidates\": [{\"term\": \"当事人组\", \"why\": \"将若干当事人作为一个组处理的同义说法\", \"ambiguity\": \"可能被理解为临时的数据分组而非业务实体\"}, {\"term\": \"当事方分组\", \"why\": \"与“当事人分组”同义，指对当事方进行的分组\", \"ambiguity\": \"“分组”也可指操作动作\"}]}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"fsldm:Party","verdicts":[{"term":"当事方","verdict":"keep","reason":"“当事方”与“当事人”在法律或交易关系中同义，均指关系中的一方。","polysemy":false}]},{"iri":"party:Individual","verdicts":[{"term":"自然人","verdict":"keep","reason":"在作为当事人的个人语境下，“自然人”与“个人”基本同义，是金融监管和信贷中的常用称谓。","polysemy":false}]},{"iri":"party:Organization","verdicts":[{"term":"组织机构","verdict":"drop","reason":"“组织机构”可被理解为机构内部的组织架构，存在多义，不宜作为“机构”的同义标签。","polysemy":true},{"term":"非自然人","verdict":"drop","reason":"“非自然人”是相对于自然人的宽泛分类，未必等同于所有法律或业务意义上的机构，属于上位概念而非同义。","polysemy":false}]},{"iri":"party:Household","verdicts":[{"term":"住户","verdict":"drop","reason":"“住户”还可指居住单元或房屋，且统计住户与家庭不完全等同，存在多义和口径差异。","polysemy":true},{"term":"家庭户","verdict":"drop","reason":"“家庭户”带有户籍登记色彩，是行政统计口径，不一定等同于作为当事人单位的家庭。","polysemy":false},{"term":"居民家庭","verdict":"drop","reason":"“居民家庭”偏统计或零售业务口径，通常是家庭的下位分类，不是“家庭”的同义术语。","polysemy":false}]},{"iri":"party:PartyGroup","verdicts":[{"term":"当事人组","verdict":"keep","reason":"“当事人组”与“当事人分组”同义，指将若干当事人作为一个组处理的业务实体。","polysemy":false},{"term":"当事方分组","verdict":"keep","reason":"“当事方”与“当事人”同义，因此“当事方分组”整体与给定中文名同义。","polysemy":false}]}]}
```

usage：`{"completion_tokens": 2623, "prompt_tokens": 792, "total_tokens": 3415, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 2167}}`

### Round 2 / Batch 2

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是同一术语审校员，现在做自我反驳。对第一轮每个候选逐条判定，verdict 只能是 keep 或 drop。drop 条件：营销词/网络说法/公司内部专用简称/多义词/与给定中文名不是同义关系（上下位或组成部分）/与其他类的中文名重复造成歧义。每条给一句 reason。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "第一轮候选如下。逐条判定并输出：{\"items\":[{\"iri\":\"...\",\"verdicts\":[{\"term\":\"...\",\"verdict\":\"keep|drop\",\"reason\":\"一句\",\"polysemy\":true|false}]}]}\n本批所有类的中文名（用于判重复）：[\"当事人\", \"个人\", \"机构\", \"家庭\", \"当事人分组\", \"当事人风险等级\", \"协议\", \"账户\", \"授信协议\", \"保单\", \"个人保险单\", \"团体保险单\", \"商业保险单\", \"保险合同（保单）\", \"产品\", \"保险产品\", \"度量\", \"资产\", \"抵押物项\", \"抵押协议\", \"风险缓释协议\", \"理赔\", \"理赔保障项\", \"保障项\", \"金融事件\", \"账户事件\"]\n[{\"iri\": \"party:PartyRiskGrade\", \"prefLabel\": \"当事人风险等级\", \"candidates\": [{\"term\": \"当事人风险评级\", \"why\": \"与“当事人风险等级”同指对当事人风险高低的评级结果，仅“等级/评级”用词差异。\", \"ambiguity\": \"“评级”有时也指评级过程或评级体系，而非等级结果。\"}]}, {\"iri\": \"fsldm:Agreement\", \"prefLabel\": \"协议\", \"candidates\": [{\"term\": \"合同\", \"why\": \"在金融业务中“协议”与“合同”常作为同义法律文件名称互换使用。\", \"ambiguity\": \"法律语境下合同可能被视为协议的更正式子类。\"}, {\"term\": \"合约\", \"why\": \"金融业务中常用“合约”指代具有法律约束力的协议安排。\", \"ambiguity\": \"“合约”在衍生品等场景更常用，可能带特定业务范围色彩。\"}]}, {\"iri\": \"agmt:Account\", \"prefLabel\": \"账户\", \"candidates\": []}, {\"iri\": \"agmt:CreditAgreement\", \"prefLabel\": \"授信协议\", \"candidates\": [{\"term\": \"授信合同\", \"why\": \"与“授信协议”同指银行给予授信额度及条件的合同文件。\", \"ambiguity\": \"不同机构可能将授信合同与具体贷款合同区分使用。\"}, {\"term\": \"信贷协议\", \"why\": \"信贷业务中常与“授信协议”互换，指信贷安排的法律协议。\", \"ambiguity\": \"“信贷”范围可能覆盖授信以外的具体贷款安排。\"}]}, {\"iri\": \"agmt:Policy\", \"prefLabel\": \"保单\", \"candidates\": [{\"term\": \"保险单\", \"why\": \"“保单”是“保险单”的常用简称，二者同指保险合同凭证。\", \"ambiguity\": \"严格法律语境下保险单是保险合同凭证，未必等同于保险合同本身。\"}]}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"party:PartyRiskGrade","verdicts":[{"term":"当事人风险评级","verdict":"drop","reason":"“评级”可指评级过程或评级体系，不必然等同于“风险等级”这一结果，存在多义。","polysemy":true}]},{"iri":"fsldm:Agreement","verdicts":[{"term":"合同","verdict":"drop","reason":"法律语境下“合同”常被视为“协议”的正式子类，并非完全同义。","polysemy":false},{"term":"合约","verdict":"drop","reason":"“合约”多用于衍生品等特定业务范围，范围窄于通用“协议”，非同义。","polysemy":true}]},{"iri":"agmt:Account","verdicts":[]},{"iri":"agmt:CreditAgreement","verdicts":[{"term":"授信合同","verdict":"keep","reason":"与“授信协议”仅“协议/合同”用词差异，指向同一授信法律文件。","polysemy":false},{"term":"信贷协议","verdict":"drop","reason":"“信贷协议”范围可能覆盖具体贷款安排，宽于“授信协议”，非同义。","polysemy":false}]},{"iri":"agmt:Policy","verdicts":[{"term":"保险单","verdict":"keep","reason":"“保险单”是“保单”的通用全称，同指保险合同凭证。","polysemy":false}]}]}
```

usage：`{"completion_tokens": 1439, "prompt_tokens": 736, "total_tokens": 2175, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 1120}}`

### Round 2 / Batch 3

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是同一术语审校员，现在做自我反驳。对第一轮每个候选逐条判定，verdict 只能是 keep 或 drop。drop 条件：营销词/网络说法/公司内部专用简称/多义词/与给定中文名不是同义关系（上下位或组成部分）/与其他类的中文名重复造成歧义。每条给一句 reason。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "第一轮候选如下。逐条判定并输出：{\"items\":[{\"iri\":\"...\",\"verdicts\":[{\"term\":\"...\",\"verdict\":\"keep|drop\",\"reason\":\"一句\",\"polysemy\":true|false}]}]}\n本批所有类的中文名（用于判重复）：[\"当事人\", \"个人\", \"机构\", \"家庭\", \"当事人分组\", \"当事人风险等级\", \"协议\", \"账户\", \"授信协议\", \"保单\", \"个人保险单\", \"团体保险单\", \"商业保险单\", \"保险合同（保单）\", \"产品\", \"保险产品\", \"度量\", \"资产\", \"抵押物项\", \"抵押协议\", \"风险缓释协议\", \"理赔\", \"理赔保障项\", \"保障项\", \"金融事件\", \"账户事件\"]\n[{\"iri\": \"agmt:IndividualInsurancePolicy\", \"prefLabel\": \"个人保险单\", \"candidates\": [{\"term\": \"个人保单\", \"why\": \"保险业务中对个人保险单的常用简称，语义与个人保险单一致。\", \"ambiguity\": \"可能被泛指个人持有的任何保单，但业务语境下通常即个人保险单。\"}, {\"term\": \"个险保单\", \"why\": \"“个险”为个人保险业务的行业通用简称，个险保单即个人保险单。\", \"ambiguity\": \"“个险”有时指个人保险业务条线，单独出现时需结合上下文确认指保单。\"}]}, {\"iri\": \"agmt:GroupInsurancePolicy\", \"prefLabel\": \"团体保险单\", \"candidates\": [{\"term\": \"团体保单\", \"why\": \"保险业务中对团体保险单的常用简称，语义与团体保险单一致。\", \"ambiguity\": \"可能被用于泛指团体持有的保单，但通常即团体保险单。\"}, {\"term\": \"团险保单\", \"why\": \"“团险”为团体保险业务的行业通用简称，团险保单即团体保险单。\", \"ambiguity\": \"“团险”也可指团体保险业务条线，需上下文确认指保单。\"}]}, {\"iri\": \"agmt:CommercialInsurancePolicy\", \"prefLabel\": \"商业保险单\", \"candidates\": [{\"term\": \"商业保单\", \"why\": \"保险业务中对商业保险单的常用简称，语义与商业保险单一致。\", \"ambiguity\": \"可能被理解为商业保险公司签发的保单，而非商业保险单这一合同类型。\"}, {\"term\": \"商业险保单\", \"why\": \"保险业务中常用“商业险”指商业保险，商业险保单即商业保险单。\", \"ambiguity\": \"“商业险”常与交强险对举，可能被限缩理解为商业车险保单。\"}]}, {\"iri\": \"ins:InsuranceAgreement\", \"prefLabel\": \"保险合同（保单）\", \"candidates\": [{\"term\": \"保单\", \"why\": \"保险业务中对保险合同的常用简称，常与保险合同互换使用。\", \"ambiguity\": \"严格说保单是合同凭证，可能被理解为单证而非合同关系。\"}, {\"term\": \"保险单\", \"why\": \"保险单是保险合同的书面凭证，业务中常作为保险合同的同义说法。\", \"ambiguity\": \"可能侧重指纸质或电子单证，而非合同权利义务本身。\"}, {\"term\": \"保险契约\", \"why\": \"保险契约是保险合同的传统同义表述，法律与业务文件中可见。\", \"ambiguity\": \"偏法律文书用语，日常业务使用频率低于保单。\"}]}, {\"iri\": \"fsldm:Product\", \"prefLabel\": \"产品\", \"candidates\": []}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"agmt:IndividualInsurancePolicy","verdicts":[{"term":"个人保单","verdict":"keep","reason":"个人保单是个人保险单的常用简称，业务语境下同义且不与现有类名重复。","polysemy":false},{"term":"个险保单","verdict":"keep","reason":"个险保单是个人保险业务中的通用说法，语义指向个人保险单，并非公司内部专用简称。","polysemy":false}]},{"iri":"agmt:GroupInsurancePolicy","verdicts":[{"term":"团体保单","verdict":"keep","reason":"团体保单是团体保险单的常用简称，语义一致且无同类名冲突。","polysemy":false},{"term":"团险保单","verdict":"keep","reason":"团险保单是团体保险业务通用说法，指团体保险单，不属于公司内部专用简称。","polysemy":false}]},{"iri":"agmt:CommercialInsurancePolicy","verdicts":[{"term":"商业保单","verdict":"keep","reason":"商业保单在业务中可作商业保险单的简称，语义基本一致。","polysemy":false},{"term":"商业险保单","verdict":"drop","reason":"商业险常特指商业车险或与交强险对举，作商业保险单别名易产生歧义。","polysemy":true}]},{"iri":"ins:InsuranceAgreement","verdicts":[{"term":"保单","verdict":"drop","reason":"保单已是给定中文类名且可指单证或合同，作为保险合同别名会与已有类重复并造成歧义。","polysemy":true},{"term":"保险单","verdict":"drop","reason":"保险单与已有类名“保单”同义重复，且侧重合同凭证而非合同关系本身。","polysemy":true},{"term":"保险契约","verdict":"keep","reason":"保险契约是保险合同的传统法律同义表述，不与现有类名重复。","polysemy":false}]},{"iri":"fsldm:Product","verdicts":[]}]}
```

usage：`{"completion_tokens": 3670, "prompt_tokens": 908, "total_tokens": 4578, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 3225}}`

### Round 2 / Batch 4

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是同一术语审校员，现在做自我反驳。对第一轮每个候选逐条判定，verdict 只能是 keep 或 drop。drop 条件：营销词/网络说法/公司内部专用简称/多义词/与给定中文名不是同义关系（上下位或组成部分）/与其他类的中文名重复造成歧义。每条给一句 reason。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "第一轮候选如下。逐条判定并输出：{\"items\":[{\"iri\":\"...\",\"verdicts\":[{\"term\":\"...\",\"verdict\":\"keep|drop\",\"reason\":\"一句\",\"polysemy\":true|false}]}]}\n本批所有类的中文名（用于判重复）：[\"当事人\", \"个人\", \"机构\", \"家庭\", \"当事人分组\", \"当事人风险等级\", \"协议\", \"账户\", \"授信协议\", \"保单\", \"个人保险单\", \"团体保险单\", \"商业保险单\", \"保险合同（保单）\", \"产品\", \"保险产品\", \"度量\", \"资产\", \"抵押物项\", \"抵押协议\", \"风险缓释协议\", \"理赔\", \"理赔保障项\", \"保障项\", \"金融事件\", \"账户事件\"]\n[{\"iri\": \"ins:InsuranceProduct\", \"prefLabel\": \"保险产品\", \"candidates\": [{\"term\": \"险种\", \"why\": \"保险业务中常用“险种”指代保险产品类别，可作为保险产品的业务称呼。\", \"ambiguity\": \"“险种”更常指产品分类或类别，可能不指某一具体产品。\"}]}, {\"iri\": \"fsldm:Metric\", \"prefLabel\": \"度量\", \"candidates\": [{\"term\": \"指标\", \"why\": \"监管报送、风险计量和信贷业务中通常把metric称为“指标”。\", \"ambiguity\": \"“指标”也常指考核目标或KPI，含义可能偏业务考核。\"}]}, {\"iri\": \"fsldm:Asset\", \"prefLabel\": \"资产\", \"candidates\": []}, {\"iri\": \"asset:CollateralItem\", \"prefLabel\": \"抵押物项\", \"candidates\": [{\"term\": \"押品\", \"why\": \"银行信贷和监管中常用“押品”统称抵押或质押担保物，与抵押物项对应。\", \"ambiguity\": \"“押品”可能同时涵盖质押物，范围略宽于严格抵押物。\"}, {\"term\": \"抵押物\", \"why\": \"信贷法律文件中常用“抵押物”指作为担保的抵押物项。\", \"ambiguity\": \"“抵押物”通常指抵押方式下的担保物，可能不含质押物。\"}]}, {\"iri\": \"bank:CollateralAgreement\", \"prefLabel\": \"抵押协议\", \"candidates\": [{\"term\": \"抵押合同\", \"why\": \"法律和信贷业务中“抵押合同”是设立抵押担保的协议，与抵押协议同义。\", \"ambiguity\": \"“抵押合同”强调合同文本，可能与协议框架文件有细微差别。\"}]}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"ins:InsuranceProduct","verdicts":[{"term":"险种","verdict":"drop","reason":"“险种”指保险产品的类别/分类，与“保险产品”是上下位关系而非同义。","polysemy":false}]},{"iri":"fsldm:Metric","verdicts":[{"term":"指标","verdict":"drop","reason":"“指标”可指考核目标/KPI，是多义词，与“度量”并非严格同义。","polysemy":true}]},{"iri":"fsldm:Asset","verdicts":[]},{"iri":"asset:CollateralItem","verdicts":[{"term":"押品","verdict":"drop","reason":"“押品”通常统称抵押和质押担保物，范围宽于“抵押物项”，属上位概念。","polysemy":false},{"term":"抵押物","verdict":"keep","reason":"“抵押物”与“抵押物项”同义，且未与其他类中文名重复。","polysemy":false}]},{"iri":"bank:CollateralAgreement","verdicts":[{"term":"抵押合同","verdict":"keep","reason":"“抵押合同”是设立抵押担保的法律协议，与“抵押协议”同义。","polysemy":false}]}]}
```

usage：`{"completion_tokens": 2104, "prompt_tokens": 698, "total_tokens": 2802, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 1823}}`

### Round 2 / Batch 5

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是同一术语审校员，现在做自我反驳。对第一轮每个候选逐条判定，verdict 只能是 keep 或 drop。drop 条件：营销词/网络说法/公司内部专用简称/多义词/与给定中文名不是同义关系（上下位或组成部分）/与其他类的中文名重复造成歧义。每条给一句 reason。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "第一轮候选如下。逐条判定并输出：{\"items\":[{\"iri\":\"...\",\"verdicts\":[{\"term\":\"...\",\"verdict\":\"keep|drop\",\"reason\":\"一句\",\"polysemy\":true|false}]}]}\n本批所有类的中文名（用于判重复）：[\"当事人\", \"个人\", \"机构\", \"家庭\", \"当事人分组\", \"当事人风险等级\", \"协议\", \"账户\", \"授信协议\", \"保单\", \"个人保险单\", \"团体保险单\", \"商业保险单\", \"保险合同（保单）\", \"产品\", \"保险产品\", \"度量\", \"资产\", \"抵押物项\", \"抵押协议\", \"风险缓释协议\", \"理赔\", \"理赔保障项\", \"保障项\", \"金融事件\", \"账户事件\"]\n[{\"iri\": \"bank:RiskMitigantAgreement\", \"prefLabel\": \"风险缓释协议\", \"candidates\": [{\"term\": \"风险缓释合同\", \"why\": \"金融监管文本中合同与协议常作同义表述，均指用于缓释风险的协议安排\", \"ambiguity\": \"法律文本中合同与协议有时作形式区分，且未限定风险类型\"}, {\"term\": \"缓释协议\", \"why\": \"银行业风险监管语境中对风险缓释协议的常见简称\", \"ambiguity\": \"脱离上下文可能指其他类型的缓释安排\"}]}, {\"iri\": \"agmt:Claim\", \"prefLabel\": \"理赔\", \"candidates\": [{\"term\": \"索赔\", \"why\": \"保险业务中与理赔对应的通用说法，英文claim常译为索赔或理赔\", \"ambiguity\": \"更侧重提出赔偿请求的行为，可能不等同于保险人理赔处理\"}, {\"term\": \"赔案\", \"why\": \"保险理赔中常用的案件称谓，常指一起理赔事项\", \"ambiguity\": \"指理赔案件或事项，可能不是事件本身\"}]}, {\"iri\": \"agmt:ClaimCoverage\", \"prefLabel\": \"理赔保障项\", \"candidates\": []}, {\"iri\": \"ins:Coverage\", \"prefLabel\": \"保障项\", \"candidates\": [{\"term\": \"保障项目\", \"why\": \"保险产品中保障项的常见完整说法，指具体保障内容\", \"ambiguity\": \"可能泛指多个保障项集合，而原类可能指单个保障特征\"}, {\"term\": \"保险责任\", \"why\": \"保险条款中表示保障范围的通用术语，常与保障项对应\", \"ambiguity\": \"通常指保险人承担赔偿或给付责任的范围，可能比单个保障项更宽\"}, {\"term\": \"保障责任\", \"why\": \"保险产品中表示具体保障责任的通用说法\", \"ambiguity\": \"可能指责任范围而非单个保障项\"}]}, {\"iri\": \"evt:FinancialEvent\", \"prefLabel\": \"金融事件\", \"candidates\": []}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"bank:RiskMitigantAgreement","verdicts":[{"term":"风险缓释合同","verdict":"keep","reason":"与“风险缓释协议”指向同一类协议安排，合同/协议在此语境可作同义表述。","polysemy":false},{"term":"缓释协议","verdict":"drop","reason":"省略“风险”限定后语义不完整，脱离上下文易指其他缓释安排，不宜作为精确同义词。","polysemy":true}]},{"iri":"agmt:Claim","verdicts":[{"term":"索赔","verdict":"drop","reason":"侧重被保险人或受益人提出赔偿请求的行为，不等同于保险人处理理赔的事件。","polysemy":false},{"term":"赔案","verdict":"drop","reason":"通常指一起理赔案件或事项，与“理赔”作为事件/过程并非同义关系。","polysemy":false}]},{"iri":"agmt:ClaimCoverage","verdicts":[]},{"iri":"ins:Coverage","verdicts":[{"term":"保障项目","verdict":"keep","reason":"“保障项目”是“保障项”的常见完整说法，指具体保障内容，语义基本一致。","polysemy":false},{"term":"保险责任","verdict":"drop","reason":"通常指保险人承担赔偿或给付责任的整体范围，较单个“保障项”更宽，属上下位关系。","polysemy":true},{"term":"保障责任","verdict":"drop","reason":"多指保障责任范围而非单个保障项，与给定类名不是精确同义关系。","polysemy":true}]},{"iri":"evt:FinancialEvent","verdicts":[]}]}
```

usage：`{"completion_tokens": 2191, "prompt_tokens": 744, "total_tokens": 2935, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 1822}}`

### Round 2 / Batch 6

请求（已省略 Authorization 头，无密钥）：

```json
[
 {
  "role": "system",
  "content": "你是同一术语审校员，现在做自我反驳。对第一轮每个候选逐条判定，verdict 只能是 keep 或 drop。drop 条件：营销词/网络说法/公司内部专用简称/多义词/与给定中文名不是同义关系（上下位或组成部分）/与其他类的中文名重复造成歧义。每条给一句 reason。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "第一轮候选如下。逐条判定并输出：{\"items\":[{\"iri\":\"...\",\"verdicts\":[{\"term\":\"...\",\"verdict\":\"keep|drop\",\"reason\":\"一句\",\"polysemy\":true|false}]}]}\n本批所有类的中文名（用于判重复）：[\"当事人\", \"个人\", \"机构\", \"家庭\", \"当事人分组\", \"当事人风险等级\", \"协议\", \"账户\", \"授信协议\", \"保单\", \"个人保险单\", \"团体保险单\", \"商业保险单\", \"保险合同（保单）\", \"产品\", \"保险产品\", \"度量\", \"资产\", \"抵押物项\", \"抵押协议\", \"风险缓释协议\", \"理赔\", \"理赔保障项\", \"保障项\", \"金融事件\", \"账户事件\"]\n[{\"iri\": \"evt:AccountEvent\", \"prefLabel\": \"账户事件\", \"candidates\": []}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"evt:AccountEvent","verdicts":[]}]}
```

usage：`{"completion_tokens": 75, "prompt_tokens": 324, "total_tokens": 399, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 55}}`

## 三、补充轮（新增 2 个类 + 语料候选词判定）

说明：第一批在首轮 26 类之外新增 `party:PartyRelationship`（关联客户/集团客户关系）与 `evt:ClaimEvent`（报案/立案/结案节点），仍按同一规则跑两轮；另对“语料里出现但首轮未提议”的词补做第二轮口径判定。

### 补充 Round1（2 个新增类）

```json
[
 {
  "role": "system",
  "content": "你是金融监管术语审校员。任务：给一个本体类找业务别名。硬规则：1) 只输出金融监管、信贷、保险业务中的通用说法，不是营销词、网络用语、公司内部简称；2) 别名必须与给定中文名同义（不是上下位、不是组成部分、不是相关概念）；3) 不要编造定义，不要输出你不确定的词；4) 如无可靠别名，candidates 返回空数组。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "为下列本体类各生成 0-5 个中文业务别名（可含行业通用缩写）。输出格式：{\"items\":[{\"iri\":\"...\",\"candidates\":[{\"term\":\"...\",\"why\":\"一句理由\",\"ambiguity\":\"你看到的一句潜在歧义\"}]}]}\n[{\"iri\": \"party:PartyRelationship\", \"prefLabel\": \"当事人之间的关系\", \"fsldmEntity\": \"PARTY RELATED\", \"subjectArea\": \"Party\", \"ontologyComment\": \"\"}, {\"iri\": \"evt:ClaimEvent\", \"prefLabel\": \"理赔事件\", \"fsldmEntity\": \"CLAIM EVENT\", \"subjectArea\": \"Event\", \"ontologyComment\": \"\"}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"party:PartyRelationship","candidates":[{"term":"当事人关系","why":"与“当事人之间的关系”同义，金融监管和合同业务中用于概括交易各方的相互关系","ambiguity":"可能被理解为单一合同中的当事人身份或合同关系，而非泛指各类当事人关系"}]},{"iri":"evt:ClaimEvent","candidates":[{"term":"赔案","why":"保险业务中对理赔事件的常用简称，指一次理赔处理对应的案件","ambiguity":"通常指已立案进入理赔流程的案件，未报案或未立案事件可能不称赔案"},{"term":"理赔案件","why":"保险理赔管理中与理赔事件同义，按案件归集一次理赔处理","ambiguity":"可能被理解为进入诉讼或仲裁的理赔案件，范围窄于一般理赔事件"}]}]}
```

usage：`{"completion_tokens": 1568, "prompt_tokens": 301, "total_tokens": 1869, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 1394}}`

### 补充 Round2（2 个新增类）

```json
[
 {
  "role": "system",
  "content": "你是同一术语审校员，现在做自我反驳。对第一轮每个候选逐条判定，verdict 只能是 keep 或 drop。drop 条件：营销词/网络说法/公司内部专用简称/多义词/与给定中文名不是同义关系（上下位或组成部分）/与其他类的中文名重复造成歧义。每条给一句 reason。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "第一轮候选如下。逐条判定并输出：{\"items\":[{\"iri\":\"...\",\"verdicts\":[{\"term\":\"...\",\"verdict\":\"keep|drop\",\"reason\":\"一句\",\"polysemy\":true|false}]}]}\n本批所有类的中文名（用于判重复）：[\"当事人\", \"个人\", \"机构\", \"家庭\", \"当事人分组\", \"当事人风险等级\", \"协议\", \"账户\", \"授信协议\", \"保单\", \"个人保险单\", \"团体保险单\", \"商业保险单\", \"保险合同（保单）\", \"产品\", \"保险产品\", \"度量\", \"资产\", \"抵押物项\", \"抵押协议\", \"风险缓释协议\", \"理赔\", \"理赔保障项\", \"保障项\", \"金融事件\", \"账户事件\", \"当事人之间的关系\", \"理赔事件\"]\n[{\"iri\": \"party:PartyRelationship\", \"prefLabel\": \"当事人之间的关系\", \"candidates\": [{\"term\": \"当事人关系\", \"why\": \"与“当事人之间的关系”同义，金融监管和合同业务中用于概括交易各方的相互关系\", \"ambiguity\": \"可能被理解为单一合同中的当事人身份或合同关系，而非泛指各类当事人关系\"}]}, {\"iri\": \"evt:ClaimEvent\", \"prefLabel\": \"理赔事件\", \"candidates\": [{\"term\": \"赔案\", \"why\": \"保险业务中对理赔事件的常用简称，指一次理赔处理对应的案件\", \"ambiguity\": \"通常指已立案进入理赔流程的案件，未报案或未立案事件可能不称赔案\"}, {\"term\": \"理赔案件\", \"why\": \"保险理赔管理中与理赔事件同义，按案件归集一次理赔处理\", \"ambiguity\": \"可能被理解为进入诉讼或仲裁的理赔案件，范围窄于一般理赔事件\"}]}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"party:PartyRelationship","verdicts":[{"term":"当事人关系","verdict":"keep","reason":"与“当事人之间的关系”同义，且未与其他类中文名重复，可作为简洁同义标签。","polysemy":false}]},{"iri":"evt:ClaimEvent","verdicts":[{"term":"赔案","verdict":"drop","reason":"“赔案”通常指已立案的理赔案件（案件记录），范围窄于理赔事件，非同义。","polysemy":false},{"term":"理赔案件","verdict":"drop","reason":"“理赔案件”可指诉讼、仲裁中的案件或具体案件记录，范围与“理赔事件”不完全等同，易产生歧义。","polysemy":true}]}]}
```

usage：`{"completion_tokens": 1836, "prompt_tokens": 516, "total_tokens": 2352, "prompt_tokens_details": {"cached_tokens": 256}, "completion_tokens_details": {"reasoning_tokens": 1670}}`

### 补充判定（语料候选词，第二轮口径）

```json
[
 {
  "role": "system",
  "content": "你是同一术语审校员，现在做自我反驳。对第一轮每个候选逐条判定，verdict 只能是 keep 或 drop。drop 条件：营销词/网络说法/公司内部专用简称/多义词/与给定中文名不是同义关系（上下位或组成部分）/与其他类的中文名重复造成歧义。每条给一句 reason。只输出 JSON。"
 },
 {
  "role": "user",
  "content": "对下列候选逐条判定，输出格式：{\"items\":[{\"iri\":\"...\",\"verdicts\":[{\"term\":\"...\",\"verdict\":\"keep|drop\",\"reason\":\"一句\",\"polysemy\":true|false}]}]}\n本批所有类的中文名：[\"当事人\", \"个人\", \"机构\", \"家庭\", \"当事人分组\", \"当事人风险等级\", \"协议\", \"账户\", \"授信协议\", \"保单\", \"个人保险单\", \"团体保险单\", \"商业保险单\", \"保险合同（保单）\", \"产品\", \"保险产品\", \"度量\", \"资产\", \"抵押物项\", \"抵押协议\", \"风险缓释协议\", \"理赔\", \"理赔保障项\", \"保障项\", \"金融事件\", \"账户事件\", \"当事人之间的关系\", \"理赔事件\"]\n[{\"iri\": \"fsldm:Party\", \"prefLabel\": \"当事人\", \"candidates\": [{\"term\": \"客户\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}, {\"term\": \"交易对手\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"party:Individual\", \"prefLabel\": \"个人\", \"candidates\": [{\"term\": \"个人客户\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"party:Organization\", \"prefLabel\": \"机构\", \"candidates\": [{\"term\": \"对公客户\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}, {\"term\": \"公司客户\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"party:PartyGroup\", \"prefLabel\": \"当事人分组\", \"candidates\": [{\"term\": \"集团客户\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}, {\"term\": \"关联客户\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"party:PartyRiskGrade\", \"prefLabel\": \"当事人风险等级\", \"candidates\": [{\"term\": \"信用评级\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"agmt:Account\", \"prefLabel\": \"账户\", \"candidates\": [{\"term\": \"账号\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"agmt:CreditAgreement\", \"prefLabel\": \"授信协议\", \"candidates\": [{\"term\": \"授信\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}, {\"term\": \"授信额度\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"bank:RiskMitigantAgreement\", \"prefLabel\": \"风险缓释协议\", \"candidates\": [{\"term\": \"担保合同\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"fsldm:Product\", \"prefLabel\": \"产品\", \"candidates\": [{\"term\": \"交易品种\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"agmt:Claim\", \"prefLabel\": \"理赔\", \"candidates\": [{\"term\": \"赔案\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}, {\"term\": \"索赔\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}, {\"iri\": \"asset:CollateralItem\", \"prefLabel\": \"抵押物项\", \"candidates\": [{\"term\": \"押品\", \"why\": \"来自 FS-LDM 语料或本体注释的候选\", \"ambiguity\": \"未评估\"}]}]"
 }
]
```

响应原文：

```json
{"items":[{"iri":"fsldm:Party","verdicts":[{"term":"客户","verdict":"drop","reason":"“客户”是当事人承担的一种业务角色，并非“当事人”的同义名称。","polysemy":false},{"term":"交易对手","verdict":"drop","reason":"“交易对手”是交易关系中的角色，不能等同所有当事人。","polysemy":false}]},{"iri":"party:Individual","verdicts":[{"term":"个人客户","verdict":"drop","reason":"“个人客户”是个人中具有客户角色的子类，不是“个人”的同义名。","polysemy":false}]},{"iri":"party:Organization","verdicts":[{"term":"对公客户","verdict":"drop","reason":"“对公客户”是机构作为银行客户的业务角色，非“机构”同义。","polysemy":false},{"term":"公司客户","verdict":"drop","reason":"“公司客户”仅指公司类客户，范围窄于“机构”。","polysemy":false}]},{"iri":"party:PartyGroup","verdicts":[{"term":"集团客户","verdict":"drop","reason":"“集团客户”是客户分组概念，范围与“当事人分组”不同。","polysemy":false},{"term":"关联客户","verdict":"drop","reason":"“关联客户”指存在关联关系的客户，非“当事人分组”同义。","polysemy":false}]},{"iri":"party:PartyRiskGrade","verdicts":[{"term":"信用评级","verdict":"drop","reason":"“信用评级”指评级活动或评级结果，与“当事人风险等级”不是同一概念。","polysemy":true}]},{"iri":"agmt:Account","verdicts":[{"term":"账号","verdict":"drop","reason":"“账号”是账户的标识符，不是账户本身。","polysemy":false}]},{"iri":"agmt:CreditAgreement","verdicts":[{"term":"授信","verdict":"drop","reason":"“授信”指授信行为或授信额度，不是“授信协议”。","polysemy":true},{"term":"授信额度","verdict":"drop","reason":"“授信额度”是额度数值，不是协议。","polysemy":false}]},{"iri":"bank:RiskMitigantAgreement","verdicts":[{"term":"担保合同","verdict":"drop","reason":"“担保合同”是风险缓释协议的一种下位类型，不能作为同义词。","polysemy":false}]},{"iri":"fsldm:Product","verdicts":[{"term":"交易品种","verdict":"drop","reason":"“交易品种”是交易标的分类，范围与“产品”不同。","polysemy":false}]},{"iri":"agmt:Claim","verdicts":[{"term":"赔案","verdict":"drop","reason":"“赔案”指理赔案件，更接近“理赔事件”，不是“理赔”的同义名。","polysemy":false},{"term":"索赔","verdict":"drop","reason":"“索赔”指提出赔偿请求，与“理赔”处理过程不同。","polysemy":false}]},{"iri":"asset:CollateralItem","verdicts":[{"term":"押品","verdict":"keep","reason":"“押品”是银行对抵押或质押担保物的常用同义说法，可保留。","polysemy":false}]}]}
```

usage：`{"completion_tokens": 3466, "prompt_tokens": 1095, "total_tokens": 4561, "prompt_tokens_details": {"cached_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 2723}}`
