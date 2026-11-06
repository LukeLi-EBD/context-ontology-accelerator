# 03 术语层第一批候选 · L1 SKOS 别名（PROPOSAL ONLY）

> 状态：提案，未批准、未加载、未合并进 `fsldm-merged.ttl`、未写入平台 `data/shapes`。
> 对应 TTL：`03-skos-terms-l1.proposed.ttl`（本目录）。
> 依据：`../05-术语层-设计与分析.md` §4.3（A 档表 L340–L345、B 档表 L351–L362）。
> 解析校验：rdflib 7.6.0，285 三元组、18 条 TermEntry、语法合法（详见 `_design/24-术语层落地-方案.md` §6）。
> 五项 open 已于 2026-11-06 全部裁定，见 24 号方案 §7；TTL 已按裁定同步（`term:canonicalFor` / `term:suppressedSurface` / `term:guardRegex` / `term:decision`）。

## 一、18 条别名总表

| 条目号（05 文档） | 别名 | 所属类（prefLabel） | 档位 | 证据出处 | confidence | open |
|---|---|---|---|---|---|---|
| `05#A-01` | 帐户 | `agmt:Account`（账户） | A / evidenced | `453_FSLDM课堂练习.pdf` p20/seq19，doc `08b15dc6…3cdae5a`；本体注释 `fsldm-merged.ttl` L1552 | — | — |
| `05#A-02` | 授信合同 | `agmt:CreditAgreement`（授信协议） | A / evidenced | `SPDB-LDM.pdf` p30/seq44，doc `2c99ce56…d40b541`；Book2 L4247 | — | — |
| `05#A-03` | 自然人 | `party:Individual`（个人） | A / evidenced | `SPDB-LDM.pdf` p22/seq34，同 doc；Book1 L5184 | — | — |
| `05#A-04` | 当事人关系 | `party:PartyRelationship`（当事人之间的关系） | A / evidenced | `FS-LDM-1.txt` p1/seq10，doc `22c84924…143334`；本体注释 L1331 | — | — |
| `05#A-05` | 抵押物 | `asset:CollateralItem`（抵押物项） | A / evidenced | `SPDB-LDM.pdf` p15/seq22；Book1 L17305 | — | — |
| `05#A-06` | 抵押合同 | `bank:CollateralAgreement`（抵押协议） | A / evidenced | `SPDB-LDM.pdf` p37/seq68；Book2 L4231 | — | — |
| `05#B-01` | 当事方 | `fsldm:Party`（当事人） | B / inferred | LLM 判定记录 Round2/Batch1 keep；05 附录 A | high | — |
| `05#B-02` | 当事人组 | `party:PartyGroup`（当事人分组） | B / inferred | LLM 判定记录 Round2/Batch1 keep | high | — |
| `05#B-03` | 当事方分组 | `party:PartyGroup`（当事人分组） | B / inferred | LLM 判定记录 Round2/Batch1 keep | high | — |
| `05#B-04` | 保险单 | `agmt:Policy`（保单） | B / inferred | LLM 判定记录 Round2/Batch2 keep | high | 已裁（T6）：Policy 为 canonical，无遗留 |
| `05#B-05` | 个人保单 | `agmt:IndividualInsurancePolicy`（个人保险单） | B / inferred | LLM 判定记录 Round2/Batch3 keep | high | — |
| `05#B-06` | 个险保单 | `agmt:IndividualInsurancePolicy`（个人保险单） | B / inferred | LLM 判定记录 Round2/Batch3 keep | medium | 已裁：保留 medium + `guardRegex` 约束 |
| `05#B-07` | 团体保单 | `agmt:GroupInsurancePolicy`（团体保险单） | B / inferred | LLM 判定记录 Round2/Batch3 keep | high | — |
| `05#B-08` | 团险保单 | `agmt:GroupInsurancePolicy`（团体保险单） | B / inferred | LLM 判定记录 Round2/Batch3 keep | medium | 已裁：保留 medium + `guardRegex` 约束 |
| `05#B-09` | 商业保单 | `agmt:CommercialInsurancePolicy`（商业保险单） | B / inferred | LLM 判定记录 Round2/Batch3 keep | medium | 已裁：保留 medium + 弱 `guardRegex` |
| `05#B-10` | 保险契约 | `ins:InsuranceAgreement`（保险合同（保单）） | B / inferred | LLM 判定记录 Round2/Batch3 keep | high | 已裁（T6）：留在本类，`保单` 词面受抑 |
| `05#B-11` | 风险缓释合同 | `bank:RiskMitigantAgreement`（风险缓释协议） | B / inferred | LLM 判定记录 Round2/Batch5 keep | high | — |
| `05#B-12` | 保障项目 | `ins:Coverage`（保障项） | B / inferred | LLM 判定记录 Round2/Batch5 keep | high | — |

合计：**A 6 + B 12 = 18 条**；覆盖 **15 个类**（`party:PartyGroup`、`agmt:IndividualInsurancePolicy`、`agmt:GroupInsurancePolicy` 各 2 条，其余 1 条）。

## 二、标识符与字段口径

- 条目号：`05#A-01` … `05#A-06` / `05#B-01` … `05#B-12`，一一对应 TTL 中 `term:docRef`。
- `term:status`：`term:evidenced`（A 档，必须有 `term:source`）或 `term:inferred`（B 档，必须有 `term:confidence`）。
- `term:confidence`：`term:high` / `term:medium`，只用于 B 档；A 档不带等级（证据即最高强度）。
- `term:source`：A 档的可复核定位串（文件名 + 页/seq + `document_id`，必要时附本体行号）。
- `prov:wasGeneratedBy`：B 档统一指向按批次的 Activity（`term:review-batch1/2/3/5`，每批 1 个节点，挂模型、协议与记录位置），不逐条建活动节点。
- `dct:source`：指向 05 文档行号与 LLM 记录批次，供人工复核。

## 三、本批刻意不做的

| 不做 | 原因 |
|---|---|
| `skos:definition` | 本批只做别名；最小必填集是 15 个挂 `term:termBatch` 的锚点类，属 T1，其中 3 条（`PartyGroup` / `GroupInsurancePolicy` / `CommercialInsurancePolicy`）需从 Book1 L3014 / L14152 摘句新写（见 24 号方案 §7-4） |
| `skos:broader` / `skos:narrower` | 类上下位只走 `rdfs:subClassOf`，避免两套层次冲突（05 §2.5） |
| `skos:closeMatch` | 本批无跨词表映射需求 |
| 上位词 / 角色词（客户、集团客户、押品、险种…） | 全部 C 档否决，留作"检索扩展词表（非本体）"，见 05 附录 A |
| 旧 146 条无语言标签大写 `altLabel` 迁移 | 属 T7，需人工确认下游消费方 |

## 四、与既有本体的交叉校验（rdflib，只读）

```
batch classes: 15
class not found in merged: []
prefLabel != rdfs:label@zh: []
new altLabel already used in merged: []
legacy untagged altLabel in merged: 146
VERDICT: PASS
```

即：15 个类全部存在于 `fsldm-merged.ttl`（共 156 个 `owl:Class`）；`skos:prefLabel@zh` 与 `rdfs:label@zh` 逐类相等；18 条新 `altLabel@zh` 与既有 95 条 `prefLabel@zh`、146 条旧 `altLabel` 均无冲突；裁定新增的 1 条 `term:canonicalFor`、1 条 `term:suppressedSurface`、3 条 `term:guardRegex`、5 条 `term:decision` 全部通过静态检查（285 三元组）。
