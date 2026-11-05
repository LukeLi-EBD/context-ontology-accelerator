# FS-LDM 资产清点与导入可行性初判（只读盘点）

- 盘点对象：`D:\FS-LDM`
- 盘点方式：只读。文件树/哈希/大小由 PowerShell 统计；PDF 有无文本层、是否加密由标准库探测（未装 pypdf/pymupdf，不作 OCR）；文档内容抽样自既有抽取产物 `_extract\*.md`（Teradata 三本官方文档全文），PPT/DOC 用 `_extract\ppt2txt.py` 的 OLE 解析现场抽样。
- 抽样纪律：官方 PDF 只读目录 + 章节首段；单文件 > 200 页不超过 4 处抽样；未联网。
- 盘点时间：2026-11-05

---

## 0. 结论速览

| 问题 | 结论 |
| --- | --- |
| 目录规模 | 70 个原始文件 / 40.84 MB（38.9 MiB）；PPT 15、PDF 8、MD 13、TTL 20、JSON 2、PY 8、TXT 4、DOC 1；约 19 份**不重复**文档 |
| 模型资产 | 有完整**逻辑模型**（3 本官方 PDF，均带文本层，已抽成 md）；**没有任何 DDL / SQL / ERwin 物理模型文件**；无独立字段字典（属性名散落正文，无数据类型/长度）；1 份扫描件需 OCR、1 份加密件 |
| 主题域/实体 | 文档明确写出 **10 个 Foundation 主题域 + 3 个扩展**；实体 **2,705 个有定义 / 2,719 个出现 / 7,147 条父子关系**（机器可读）；逐域实体骨架共提炼 **约 105 个**（每域 9–18 个） |
| 明细数据 | **没有任何明细数据（0 个 CSV/Parquet/Excel/导出文件），指标只能做口径验证，不能做数值验证** |
| 指标口径 | 文档定义 **0 条**（Roll Rate / 迁徙率 / DPD 分档 / 贷前中后 / RFM / 留存 口径全部找不到）；只有 DPD 相关**字段**与"留存率"作为**业务问题**出现 |
| 导入可行性 | **②需转换**（主判决），并触及 ③：逻辑模型可机读，但物理层与数据层缺失。不适合判为①"可直接导入" |

---

## 1. 文件清单

### 1.1 规模

- 文件数：**70**（本次抽样另产生 1 个 `__pycache__\ppt2txt.cpython-312.pyc`，见文末备注，不计入）
- 总大小：**40,844,749 B ≈ 38.95 MiB**（其中 8.7 KB 为上述 pyc）
- 目录层级：根目录 + 3 个一级子目录（`FS-LDM`、`_extract`、`fsldm-ontology`），最深两层

### 1.2 类型分布

| 类型 | 数量 | 合计大小 | 说明 |
| --- | --- | --- | --- |
| `.ppt` | 15 | 18.16 MB | 培训/交流胶片（PowerPoint 97-2003，OLE2） |
| `.pdf` | 8 | 13.83 MB | 官方 3 本 + 白皮书 + 课堂练习 + 2 份其他 |
| `.md` | 13 | 3.94 MB | 抽取产物 + 本体文档/报告 |
| `.json` | 2 | 2.25 MB | 抽取的模型元数据 + 本体实体目录 |
| `.ttl` | 20 | 1.84 MB | 既有 OWL/SHACL/SKOS 产物（非原始文档） |
| `.doc` | 1 | 0.61 MB | SPDB 客户化设计说明（Word 97） |
| `.py` | 8 | 0.11 MB | 抽取脚本 3 + 本体工具 5 |
| `.txt` | 4 | 0.08 MB | 4 份培训 PPT 的文本抽取 |
| **SQL / DDL / XLSX / CSV / 图片 / 数据库导出** | **0** | — | 见第 5 节 |

### 1.3 目录树（两层内）

```text
D:\FS-LDM
├─ EB6546.pdf                       # 加密 PDF（/Encrypt /Filter/Standard V4 R4，含 DCT 图像，无字体）
├─ FS-LDM-1.ppt                     # 培训材料 DAY-1 完整版（546 个文本块）
├─ FS-LDM培训材料(DAY-1)——NCR…ppt    # 客户化方法论（与 DAY-4 同文）
├─ FS-LDM培训材料(DAY-2)-NCR…ppt
├─ FS-LDM培训材料(DAY-3)-NCR…ppt
├─ FS-LDM培训材料(DAY-4)——NCR…ppt    # 与 DAY-1 同文
├─ FSLDM课堂练习.pdf                 # 57 页，纯练习题（与 FS-LDM\ 下同名文件字节相同）
├─ HSB-EDW-FS-LDM逻辑数据模型培训.ppt # 徽商银行项目培训（1,069 个文本块，最详尽）
├─ NCR-DWModel-verview.ppt          # BOC 项目：FS-LDM 主题概览（2002）
├─ NCR-DWModel1.ppt                 # BOC 项目：LDM 概念与定制步骤
├─ SPDB-LDM-模型详细设计说明文档.doc  # 浦发客户化 LDM 设计（含目录/实体/主键，无字段类型）
├─ 数据仓库模型.ppt                 # 十大主题知识培训（2012，Amarsoft）
├─ 数据模型设计标准工艺.pdf          # 34 页，0 字体 / 214 图像 → 扫描件
├─ 金融领域数据模型实例讲解.ppt      # 正文几乎全为图片，可抽文本仅 114 块且为占位符
├─ 银行数据仓库解决方案交流.ppt      # 南昌商业银行交流（解决方案/实施，非模型细节）
├─ FS-LDM\                          # 官方文档归集（4 份 PPT 与根目录重复）
│  ├─ FS-LDM-1.ppt / -2.ppt / -3.PPT / -4.PPT
│  ├─ FS-LDM金融业逻辑数据模型白皮书.pdf      # 2 页
│  ├─ FSLDM课堂练习.pdf
│  ├─ Teradata FS-LDM 10.00.00 Appendices-Book 1.pdf      # 612 页
│  ├─ Teradata FS-LDM 10.00.00 Reference Guide-Book 1.pdf # 638 页
│  └─ Teradata FS-LDM 10.00.00 Reference Guide-Book 2.pdf # 710 页
├─ _extract\                        # 既有抽取产物（脚本可复现）
│  ├─ extract_model.py  ppt2txt.py
│  ├─ fsldm_model.json              # 1.51 MB 结构化模型
│  ├─ FS-LDM-1..4.txt               # 培训 PPT 文本
│  ├─ FSLDM课堂练习.md  whitepaper.md
│  └─ Teradata … Appendices-Book 1.md / Reference Guide-Book 1.md / -Book 2.md
└─ fsldm-ontology\                  # 既有本体工程（19 个 TTL + 6 个工具 + 3 份报告 + 4 份文档）
   ├─ fsldm-core/party/agreement/product/event/asset/location/channel/campaign/org/finance.ttl
   ├─ fsldm-ext-banking/-insurance/-investment.ttl  fsldm-codes.ttl  fsldm-shapes.ttl  fsldm-all.ttl
   ├─ catalog\（fsldm-entities.json / .ttl，coverage.md）
   ├─ examples\（anny-tom.ttl 正例 / anny-tom-invalid.ttl 反例）
   ├─ reports\（lint.md / credit-check.md / query-check.md）
   └─ tools\（ttl_lint / shacl_check / gen_catalog / credit_probe / query_check / run_all）
```

### 1.4 最大 10 个文件

| # | 大小 | 文件 |
| --- | --- | --- |
| 1 | 3.68 MB | FS-LDM\Teradata FS-LDM 10.00.00 Reference Guide-Book 2.pdf |
| 2 | 3.33 MB | FS-LDM\Teradata FS-LDM 10.00.00 Reference Guide-Book 1.pdf |
| 3 | 3.02 MB | 银行数据仓库解决方案交流.ppt |
| 4 | 2.46 MB | FS-LDM\Teradata FS-LDM 10.00.00 Appendices-Book 1.pdf |
| 5 | 2.33 MB | HSB-EDW-FS-LDM逻辑数据模型培训.ppt |
| 6 | 2.15 MB | 数据模型设计标准工艺.pdf |
| 7 | 1.51 MB | _extract\fsldm_model.json |
| 8 | 1.48 MB | fsldm-ontology\catalog\fsldm-entities.ttl |
| 9 | 1.36 MB | FS-LDM\FS-LDM-1.ppt |
| 10 | 1.36 MB | FS-LDM-1.ppt |

### 1.5 重复与冗余（去重后约 19 份文档）

- 字节级完全相同：`FSLDM课堂练习.pdf`（根 与 `FS-LDM\`）。
- **文本内容一致、哈希不同**（应为另存/改元数据副本）：`FS-LDM-2/3/4.ppt` 与 `FS-LDM培训材料(DAY-2/3/4)`；`FS-LDM培训材料(DAY-1)` 与 `(DAY-4)`（两份都是 160 块 / 3,727 字符的"客户化方法论"）。
- `FS-LDM-1.ppt`（根与 `FS-LDM\`）同为 546 块 / 约 13.7 KB 文本的 DAY-1 完整版，**与 `培训材料(DAY-1)` 不是同一份**（后者只是方法论）。

---

## 2. 模型资产识别

判定"可直接解析为结构化文本"的依据：PDF 内是否存在 `/Font`、`/ToUnicode`、可解压内容流中的文本算子；`.ppt/.doc` 走 OLE2 记录树抽取。

| 文件 | 类别 | 用途（一句话） | 可解析性 |
| --- | --- | --- | --- |
| `Reference Guide-Book 1.pdf`（638 页） | **模型文档（核心）** | Foundation 十主题域的概览/概念/详细模型说明（Ch1–4），含 ER 图与逐实体叙述 | ✅ 有文本层（101 字体、13 个 ToUnicode），已抽成 md，可直接解析 |
| `Reference Guide-Book 2.pdf`（710 页） | **模型文档（核心）** | Banking(Ch5–8)/Insurance(Ch9–12)/Investment(Ch13–16) 三扩展的模型说明与属性列举 | ✅ 有文本层（151 字体），已抽成 md |
| `Appendices-Book 1.pdf`（612 页） | **模型字典（核心）** | 附录 A 父子关系表、附录 B 迁移属性对照、附录 C 实体定义（A–Z，C-1~C-364） | ✅ 有文本层，已抽成 md；是**唯一可机读的实体/关系全量清单** |
| `FS-LDM金融业逻辑数据模型白皮书.pdf`（2 页） | 概述/白皮书 | 卖点式介绍：模型结构、主题、优势，无细节 | ✅ 文本层（26 字体） |
| `FSLDM课堂练习.pdf`（57 页） | 教学练习 | 分主题选择题 + 综合案例（Anny/Tom），无口径内容 | ✅ 文本层（13 字体） |
| `FS-LDM-1.ppt` / `-2` / `-3` / `-4`（及副本） | 培训材料 | DAY1 模型概述+Party+内部机构；DAY2 Product/Agreement/Asset/Location；DAY3 Event/Channel/Campaign/Finance；DAY4 客户化方法论 | ✅ OLE2 可抽文本（无幻灯片边界，非严格结构化） |
| `HSB-EDW-FS-LDM逻辑数据模型培训.ppt` | 培训材料（项目版） | 徽商银行项目培训：方法论 → 主题域逐个讲解（1,069 块文本，最详尽的二手解读） | ✅ OLE2 可抽文本 |
| `NCR-DWModel1.ppt` / `NCR-DWModel-verview.ppt` | 培训材料（2002） | 中行(BOC)项目：LDM 基本概念、主题概览、客户化步骤 | ✅ OLE2 可抽文本 |
| `数据仓库模型.ppt` | 培训材料 | 2012 年"十大主题"知识培训，大段为现场照片 | ✅ 文本可抽但信息密度低 |
| `金融领域数据模型实例讲解.ppt` | 培训材料 | 名义"实例讲解"，**可抽文本 114 块全是占位符**，实质内容在图片里 | ⚠️ 文本可抽但无内容；需看图/OCR |
| `银行数据仓库解决方案交流.ppt` | 方案交流 | 架构/实施/建议，**不含模型细节** | ✅ OLE2 可抽文本 |
| `SPDB-LDM-模型详细设计说明文档.doc` | **客户化设计说明** | 浦发银行 LDM 客户化：建模方法 + 各章"主要实体/主要分类/重要关系/贷款类合约" | ✅ Word97 OLE2 可抽正文；**只有实体/主键级，无字段数据类型** |
| `数据模型设计标准工艺.pdf`（34 页） | 工艺规范 | 建模标准与工艺流程（疑为内部规范） | ❌ **扫描件：0 字体 / 0 FontFile / 214 图像（22 张 JPEG）→ 需 OCR** |
| `EB6546.pdf`（431 KB） | 未知/未标注 | 无字体、含 DCT 图像，且 `/Encrypt /Filter/Standard V4 R4` | ❌ **加密 + 疑似扫描/图片导出 → 需先解密再 OCR**（内容未读取） |
| `_extract\*.md / *.json` | **已抽取产物** | 三本官方文档的文本版 + 实体/关系结构化 JSON | ✅ 已是结构化文本 |
| `fsldm-ontology\*.ttl` | **已转换产物** | 手工建的 OWL 骨架（157 类 / 85 对象属性 / 45 数据属性 / 28 SHACL） | ✅ 已是本体，但只覆盖 5.6% |

**关键缺口（不是"文档不够多"，而是"缺一整层"）**

1. **没有任何 DDL / CREATE TABLE / SQL / `.erwin` 文件。** 逻辑模型（实体+关系+属性名）在，物理建表脚本完全不在。
2. **没有独立字段字典。** 属性名以粗体散落在 Reference Guide 正文（Book1 Ch4、Book2 Ch8/12/16），无数据类型、长度、主键约束的机器可读清单；命名规则另见 Book1 p44。
3. Appendices 标称 "Book 1 of 2"，但 Book1 已含 A/B/C 三附录且实体定义到 `Z BONDS`（C-363），**内容完整，Book 2 缺失不构成阻断**。

---

## 3. 主题域与实体骨架

### 3.1 主题域出处（原文可核）

- Reference Guide-Book 1，**PDF p85**：`Party / Event / Party Asset / Location / Product / Campaign / Agreement / Channel / Internal Organization / Finance`（"These ten major subject areas…"）。
- 同书 **p59**：说明"ten major subject areas are the primary business things or events"，并解释 logical view 与 subject area 的区别。
- 扩展域：Reference Guide-Book 2，**Ch5 p17**（Banking）、**Ch9 p315**（Insurance）、**Ch13 p531**（Investment）。
- 逐实体归属：v10 官方**只给 10 个域，不给逐实体归属**（`catalog\coverage.md` 亦如此注明）。故下表实体名取"该域章节正文中**显式出现**的实体"，不按名字前缀推断。

### 3.2 主题域 | 实体名 | 来源

| 主题域 | 实体名（章节内显式出现） | 来源文档 | 页码/章节 |
| --- | --- | --- | --- |
| **PARTY** | PARTY, INDIVIDUAL, ORGANIZATION, HOUSEHOLD, BUSINESS, EXTERNAL ORGANIZATION, INTERNAL ORGANIZATION, ASSOCIATION, PARTY IDENTIFICATION, PARTY STATUS, PARTY RELATED, PARTY GROUP, PARTY LOCATOR, ASSOCIATE, SITE | Reference Guide-B1 | p91–168（文档页 4-7 起，§Party Subject Area / Detail） |
| **PARTY ASSET** | PARTY ASSET, LIABILITY, PARTY LIABILITY, REAL ESTATE, MOTOR VEHICLE, VESSEL, SECURITY ASSET, RECEIVABLE, OTHER ASSET, ASSET VALUE HIST, ASSET FEATURE, PARTY LIAB CREDIT RATING, PARTY ASSET TO LOCATOR | Reference Guide-B1 | p169–186（4-85 起，§Party Asset） |
| **PRODUCT** | PRODUCT, FEATURE, PRODUCT FEATURE, PRODUCT PACKAGE, PRODUCT GROUP, RATE FEATURE, TERM FEATURE, QUANTITY FEATURE, AMOUNT FEATURE, PRODUCT FEATURE ELIGIBILITY, PRODUCT FEATURE LEEWAY, PACKAGE OFFERING, PRODUCT PARTY, PRODUCT RELATED | Reference Guide-B1 | p187–234（4-103 起，§Product） |
| **AGREEMENT** | AGREEMENT, FINANCIAL AGREEMENT, ACCOUNT, ACCOUNT GROUP, APPLICATION, QUOTATION, STATEMENT, AGREEMENT STATEMENT, ACCOUNT COLLECTION STATUS, ACCOUNT PRODUCT HISTORY, DEFAULT RECOVERY, LEGAL ACTION, EXTERNAL AGREEMENT, PORTFOLIO | Reference Guide-B1 | p235–290（4-151 起，§Agreement） |
| **INTERNAL ORGANIZATION** | INTERNAL ORGANIZATION, ORGANIZATION LEVEL, INTERNAL ORG GRP FUNCT, INTERNAL ORG GROUP SKILL, INTERNAL ORG WORKSTATION, WORKSTATION TERMINAL, ORG ORG BUSINESS TYPE, PARTY RELATED, PARTY CHANNEL, PARTY REVENUE | Reference Guide-B1 | p291–306（4-207 起，§Internal Organization） |
| **EVENT** | EVENT, CONTACT EVENT, ACCOUNT EVENT, FINANCIAL EVENT, EVENT GROUP, EVENT PARTY, EVENT PRODUCT, EVENT RELATED, CONTACT SESSION, CASE, WEB VISIT, WEB SESSION, IVR LEG, RECOVERY COLLECT CONTACT EVENT, DIRECT CONTACT EVENT | Reference Guide-B1 | p307–360（4-223 起，§Event） |
| **LOCATION** | LOCATOR, POINT LOCATOR, GEOGRAPHICAL AREA, GEOSPATIAL LOCATOR, STREET ADDRESS, PARCEL ADDRESS, POST OFFICE BOX ADDRESS, CITY, COUNTY, COUNTRY, POSTAL CODE, TELEPHONE NUMBER, ELECTRONIC ADDRESS, SITE, TERRITORY, LOCATOR RELATED HIST | Reference Guide-B1 | p361–382（4-277 起，§Location） |
| **CAMPAIGN** | CAMPAIGN, PROMOTION, TARGET PROMOTION, OFFER, PRODUCT OFFER, OPPORTUNITY, PROPOSAL, AD, AD ORDER, AD PLACEMENT, WEB AD PLACEMENT, MARKET SEGMENT, PROMO SEGMENT, CAMPAIGN ACCOUNT, CAMPAIGN CONDITION | Reference Guide-B1 | p383–446（4-299 起，§Campaign） |
| **CHANNEL** | CHANNEL, CHANNEL TYPE, ACCESS DEVICE, WEB SITE, WEB PAGE, WEB VISIT, WEB SERVER, ATM CHANNEL, CALL CENTER CHANNEL, TELEPHONE CHANNEL, POINT OF SALE CHANNEL, PARTY CHANNEL, ACCOUNT CHANNEL, CHANNEL TO LOCATOR | Reference Guide-B1 | p447–476（4-363 起，§Channel） |
| **FINANCE** | CHART OF ACCOUNT, CHART OF ACCOUNT SEGMENT, SET OF BOOKS, GL MAIN ACCOUNT, EXPENSE ACCOUNT, REVENUE ACCOUNT, LIABILITY ACCOUNT, ASSET ACCOUNT, FIXED ASSET, AP INVOICE (+LINE), AR INVOICE (+LINE), RECEIPT, VENDOR, VENDOR PO, PROJECT, TASK, FINANCIAL PLAN | Reference Guide-B1 | p477–584（4-393 起，§Finance；§Finance & Performance Management） |
| *扩展：Banking* | COLLATERAL AGREEMENT, RISK MITIGANT AGREEMENT, CREDIT AGREEMENT, ACCOUNT GROUP, SECURITIZATION POOL/TRANCHE, BASEL DEFAULT STATUS PARAM, PORTFOLIO VALUE AT RISK, STRESS TEST RESULT | Reference Guide-B2 | Ch5–8，p17–314 |
| *扩展：Insurance* | INSURANCE AGREEMENT / POLICY, CLAIM, CLAIM COVERAGE, COVERAGE FEATURE, UNDERWRITE CLASS, REINSURANCE AGREEMENT, SUBROGATION, INSURABLE INTEREST | Reference Guide-B2 | Ch9–12，p315–530 |
| *扩展：Investment* | BOND, STOCK, OPTION PRODUCT, MONEY MARKET PRODUCT, SWAP AGREEMENT, REPURCHASE AGREEMENT, PORTFOLIO, INVESTMENT POSITION, MARKET QUOTE, REAL ESTATE INVESTMENT TRUST | Reference Guide-B2 | Ch13–16，p531–685 |

### 3.3 数量（可核的硬数字）

| 指标 | 数值 | 证据 |
| --- | --- | --- |
| 有定义的实体 | **2,705** | `_extract\fsldm_model.json` counts；源自 Appendices 附录 C |
| 出现的实体总数 | **2,719** | 同上（附录 A 关系端点并集） |
| 父子关系条数 | **7,147** | 附录 A 表，去跨页重复后 |
| 不同关系短语 | 2,180 | 同上 |
| 码表类实体（`* TYPE` 等） | **828** | 同上 |
| 关联实体（原文标 associative entity） | **111** | 同上 |
| 子类型关系 | 55 | 由定义文本匹配 |
| 本体已显式建模 | **151（5.6%）** | `catalog\coverage.md` |

> 说明：`_extract\extract_model.py` 的"主题域归类"是按名称前缀 + 关系图标签传播的**推断**（例如把 `CREDIT AGREEMENT` 归到 PARTY），**不是官方口径**，不要当权威数据用。

---

## 4. 既有实验结果

分两簇，全部在 `D:\FS-LDM` 内，无外部数据参与。

### 4.1 抽取簇（`_extract\`）

| 项 | 做了什么 | 基于什么 | 结论 | 可信度 |
| --- | --- | --- | --- | --- |
| `ppt2txt.py` | 零依赖 OLE2 解析，遍历 PPT 记录树抽 `TextCharsAtom`/`TextBytesAtom` | 15 个 `.ppt` 原件 | 可稳定抽出 114–1,069 块/份；无版式、无幻灯片边界 | **中高**：脚本在库内可重跑；但**无页码**，且不抽图片内文字 |
| `extract_model.py` | 从 Appendices 的 md 解析三张表（父子关系/实体定义/迁移属性），做跨页表头去重、`<br>` 还原、父子延续、子类型与关联实体识别 | `Appendices-Book 1.md`（1.39 MB） | 2,705 定义 / 7,147 关系 / 828 码表 / 111 关联实体 | **中高**：数字与原文表结构可对账；但**实体→主题域映射是启发式**（脚本自注"仅用于统计"） |
| `FS-LDM-1..4.txt`、`whitepaper.md`、`FSLDM课堂练习.md` | 格式转换 | 对应 PDF/PPT | 纯文本化，无分析 | **高**（客观存在物） |

### 4.2 本体簇（`fsldm-ontology\`）

| 项 | 做了什么 | 结论 | 可信度标注 |
| --- | --- | --- | --- |
| 19 个 TTL（10 域 + 3 扩展 + core/codes/shapes/all） | 手工把十域主实体、3 个扩展、18 套 SKOS 码表建成 OWL；28 条 SHACL | 30,121 三元组 / 157 类 / 85 对象属性 / 45 数据属性 | **中**：结构自洽，但**覆盖 5.6%**，是"概念骨架"不是全模型 |
| `tools\ttl_lint.py` + `shacl_check.py` → `reports\lint.md` | 零依赖自写 Turtle 解析器 + 13 条 OWL 规则 + SHACL Core 子集执行器 | **错误 0 / 警告 0** | **中**：**自建检查器**，无 rdflib/pyshacl/Java 交叉验证（刻意零依赖）；"0 错误"只覆盖它实现的 13 条规则 |
| `tools\credit_probe.py` → `reports\credit-check.md` | 四族 30 条信贷指标，逐条检查"本体里有没有放操作数的类/属性/概念" | 可表达 29 / 部分 1（RWA 缺风险权重）/ 不可表达 0；分族 93%/100%/100%/100% | **低（作为"可用"证据）**：需求清单是**作者自己列的**，补完自然全绿——报告与验收文档均自承"自我循环"；**无任何数据参与** |
| `tools\query_check.py` → `reports\query-check.md` | 5 条真实 SPARQL，只校验**术语是否声明过** | 5 条术语全齐（9/12/9/9/8 个），未声明 0 | **低-中**：**不执行查询**，只查名字；作者自述抓不到方向/基数/类型（Q3 初稿把 `metricOf` 写反仍全放行） |
| `FS-LDM信贷语义验收.md` | 人工分析 + 加权评分 | **62/100**；D1 97 / D2 64 / D3 22 / D4 100 / D5 5 | **高（作为过程记录）**：明确写出"97% 只是结构上放得下""30 条指标**一条都没真正算出来过**""无引擎、无 ETL、无真实数据"，并记录 5 次检查器自身纠错。**本目录里最诚实的文件** |
| `examples\anny-tom.ttl` / `-invalid.ttl` | 课堂案例实例化（Anny/Tom 夫妻 + Gold-Point 公司 + 联名账户） | 217 三元组 / 10 条埋错 | **低（作为数据）**：**纯手工编造的示例**（`310101198504120011` 之类假证件号），只服务 SHACL 正反例，不可用于任何指标 |
| `FS-LDM本体架构.md` / `本体建模指南.md` / `README.md` | 架构分层、D1–D12 决策记录、30 秒上手 | — | **高**（设计文档，与代码一致） |

**三条必须打折的结论**

1. "30/30 指标可表达" ≠ "能算出来"。作者自评 D3=22/100。
2. "lint 0 错误" 是自建检查器结论，不等于通过标准 OWL/SHACL 校验。
3. "62/100" 是自评分，无第三方复评。

---

## 5. 样例数据可用性（关键）

**结论：无明细数据。指标只能做口径验证，不能做数值验证。**

依据：

1. 全目录 **0 个** `.csv / .parquet / .xlsx / 数据库导出`。类型分布里没有任何数据文件（见 1.2）。
2. `.json` 仅 2 个，都是模型元数据：`_extract\fsldm_model.json`（实体/关系）、`fsldm-ontology\catalog\fsldm-entities.json`（实体目录），**不含任何业务记录**。
3. 唯一"像数据"的是 `examples\anny-tom.ttl`（217 三元组）——**手工编造的课堂案例**，数值均为示意（假证件号、假收入），无时间跨度、无标签、不可复现生成。
4. 你提到的"xlsx 结论表"在本目录**不存在**；结论表只有 `reports\*.md`（Markdown 表格）。
5. `_extract\fsldm_model.json` 里的 `definitions` 是**实体定义文本**，不是字段值。

因此：**账户级/客户级/交易级明细、逾期状态标签、放款/还款日期等一概没有。** Roll Rate、Vintage、留存率的数值结果无从谈起。

若要做数值验证，最小数据集需自备（本目录无法提供）：

| 必需字段 | 用途 |
| --- | --- |
| 账户号、客户号、产品/贷款类型 | 粒度与维度 |
| 放款日、到期日、首期应还款日、最后足额还款日 | DPD 锚点、MOB、Vintage 分桶 |
| 每期应还/实还金额、未偿本金 | 余额与逾期余额 |
| 观察日快照（按月） | 时点切片 |
| 五级分类取值、核销金额/日期 | 不良率、迁徙率、损失率 |

---

## 6. 指标口径线索

判据：文档中是否**定义了计算口径**（公式、分档规则、判定条件），而不只是出现相关字段名。

| 指标 | 文档中是否定义口径 | 能找到的最近线索 | 出处 |
| --- | --- | --- | --- |
| 信贷迁徙率 / Roll Rate | **找不到**（全库 0 命中：`roll rate`、`migration rate`、`迁徙`、`滚动`） | 只有"同一账户两个时点的分类/DPD 都在"的结构基础 | Reference Guide-B1 p235–290（Agreement 章）；无公式 |
| 逾期分档 M0–M6 / DPD 分桶 | **找不到分档规则**（无 M0–M6、无桶边界） | 有**字段**：`Days Past Due Cnt`、`Past Due Amt`、`Acct Crncy Past Due Amt`、`Past Due GT 90/180/360 Days Amt`、`ACCOUNT COLLECTION STATUS`（"number of days past due, charged off, in collections"） | B2 **p249**（属性表）；B1 p235–290（ACCOUNT COLLECTION STATUS 叙述） |
| 贷前 / 贷中 / 贷后分析 | **找不到**（无对应术语） | 有 APPLICATION / QUOTATION / OFFER 等贷前实体，但无阶段划分与分析口径 | B1 p235–290 |
| 客户 RFM | **找不到**（`RFM`、`recency` 0 命中） | 无 | — |
| 客户留存 | **找不到公式** | 只有**业务问题清单**："What is the retention rate by product or product type?"、"Retention Questions: What is the retention rate…by LOB and by Class?" | B2 **p27**、**p330**（Business Questions 章） |

**汇总：5 条里找到口径 0 条，全部缺失。** 文档提供的是"数据应该长什么样"的**载体**（DPD 字段、分类字段、关系链），不是"指标怎么算"的**定义**。这与 FS-LDM 的定位一致（逻辑数据模型，应用中性，不承载报表口径）——口径必须另行引入（监管制度 / 内部风险政策 / 行业实践），不能指望从这套文档里"提炼"。

> 注意区分：`reports\credit-check.md` 里的 30 条"口径"是**作者写的**，不是文档里的；其"可表达"只能说明本体有地方放，不说明口径正确。

---

## 7. 导入可行性初判

### 三档判决

| 档 | 是否适用 | 依据 |
| --- | --- | --- |
| ① 可直接导入（结构化文本/DDL 齐全） | **不适用** | 逻辑模型可机读（Appendices 附录 A/C 已完整解析成 2,705 实体 + 7,147 关系），但 **DDL/物理模型/ERwin 文件为 0**，"完整导入"所需的字段级信息不存在 |
| ② 需转换（OCR / DDL 改写为 OWL/TTL） | **主判决** | 见下 |
| ③ 缺关键输入（缺字段字典或缺数据） | **部分适用** | 字段字典只有"属性名+描述"散落正文，无数据类型/长度/主键；明细数据为 0 |

### 为什么是②而不是①

- **规模**：要转的是 **2,705 实体 + 7,147 父子关系 + 828 码表**（约 612 页结构化表格，已全部落成 md/JSON，可一次性机转）。既有成果只覆盖 151 类（5.6%），说明**转换本身不是瓶颈，建模取舍才是**。
- **语义损耗点**（既有本体文档已验证过，非猜测）：
  1. 关联实体主键是"参与方 × 角色 × 起始日"，退化成一条边会同时丢角色与时间（`AGREEMENT PARTY`）；
  2. `EVENT` 子类型是**包含式**、`ACCOUNT` 子类型是**互斥式**，同一模型两种语义并存（B1 图 1-4 / 1-5）；
  3. "必须有"写成 `someValuesFrom` 会在开放世界下把"数据缺失"判成"本体不一致" → 必须走 SHACL；
  4. 时间语义（业务/记录/观察）在逻辑模型中混用，落到本体必须先拆。
- **需要 OCR/解密的只有 2 份，且都不是核心**：`数据模型设计标准工艺.pdf`（34 页扫描）、`EB6546.pdf`（加密+图片）。三本官方文档**均有文本层，不需要 OCR**——这是本次盘点最重要的"少花钱"结论。

### 为什么又触及③

- **缺字段字典（半套）**：属性名与描述可从 Reference Guide 正文回收，但**无数据类型、无长度、无主键约束**。OWL 数据属性需要 XSD 类型（date/decimal/int），必须重新推断；推错的直接后果是 SHACL 校验与日期算术（MOB = 观察日 − 放款日）失效。
- **缺数据**：见第 5 节。没有数据 → 导入后**无法验证任何指标数值**，只能验证"口径放得下"。

### 一句话判决

> **FS-LDM 的"语义层"够完整、够机读，可以转成一套可用的本体（②）；但"物理层"（DDL/字段类型）与"数据层"（明细）在本目录里是空的，因此可以验证"模型能不能承载监管指标"，不能验证"指标算得对不对"（触及③）。**

---

## 附：本次盘点的两点备注

1. **`D:\FS-LDM\_extract\__pycache__\ppt2txt.cpython-312.pyc` 是本次抽样产生的副产物**（为复用 `ppt2txt.py` 的 OLE 解析而 import，Python 自动写了缓存）。盘点开始时该目录不存在。**按"不修改/不删除"约束，我没有删除它**（删除请求被安全策略拦截，也不应绕过）——请你自行删除，或在后续明确授权我清理。除此之外，该目录未被写入任何内容。
2. 页码统一用 **PDF 物理页**，部分处附官方文档页（如 4-7）；两者差约 84 页（前置页）。引用时建议以官方文档页为准。
