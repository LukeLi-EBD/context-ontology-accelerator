# Tika 与 COA 文档解析链路核查（2026-11-04）

## 一、COA 里有没有 Apache Tika：没有

全仓 `grep -i tika`（含 coa/ 全部源码、依赖、infra、文档）**0 命中**。COA 的文档解析是「unstructured(OSS) + Amazon Textract」双路径，无 Tika、无 Bedrock Data Automation（`grep -i DataAutomation` 亦 0 命中）。

| 环节 | 实现 | 证据（行号为真实核对） |
|---|---|---|
| 依赖声明 | `unstructured[pdf,docx]>=0.27.16`、`pypdfium2>=4.30.0`、`pypdf>=6.21.2`、`pillow` | `packages/sources/documents/preprocessing/requirements.txt:4-11` |
| 支持格式 | 仅 `.txt .md .docx .pdf`（**不含 HTML**） | `libs/common/src/coa_common/constants.py:183-194` |
| DOCX | `unstructured.partition_docx` → 元素转 Markdown | `packages/sources/src/coa_sources/documents/preprocessing/processors.py:71-87` |
| PDF（文字层） | `unstructured.partition_pdf(strategy="fast")`，即 **pdfminer**，无版面模型 | 同文件 `:95-145`（`:131-134` 调用） |
| PDF（扫描件） | 先用 `pypdfium2` 判定 `<50 字符/页`，再 300 DPI 渲染 PNG，走 **Textract `DetectDocumentText`**，线程池并发 | `:148-200`（判定）、`:203-302`（OCR） |
| PDF（表格） | `enableTableExtraction=true` 时全量改走 **Textract `AnalyzeDocument` FeatureTypes=[TABLES]**，默认关闭 | `:304-415`；默认值 `libs/common/.../constants.py:257-258` |
| IAM 声明 | `textract:DetectDocumentText`、`textract:AnalyzeDocument` | `infra/lib/stacks/services/sources-stack.ts:2094-2098`、`:2541-2542` |
| 分发 | `_PROCESSORS` 仅注册 `.txt/.md/.docx`，`.pdf` 单独分支（需 textract client） | `processors.py:573-578` |
| 后续链路 | Lambda 写 staging 文本 → `kg_build` 分块 + Bedrock Embedding → OpenSearch + Neptune | `documents/preprocessing/handler.py:4-15`、`kg_build/graph_build.py:9,108` |

结论：**COA 不含文档解析之外的兜底方案**。非结构化文档一律先由 preprocessing 抽成纯文本/Markdown（图片型 PDF 靠 Textract OCR），再交给 GraphRAG 分块与 LLM 抽取；不支持格式直接拒收，不靠人工转结构化，也不让 LLM 直吃二进制。值得注意：COA 用 Textract 是为了「AWS 原生免运维」，其解析能力本身并不比 OSS 强多少（文字层仍用 pdfminer）。

## 二、单机方案：Tika 该不该用

**Tika 能给什么**：1000+ MIME 识别（tika-core Detector）、格式覆盖极广的文本/元数据抽取（PDFBox/POI/OCR 插件）、可选 OCR（`tika-parser-ocr-module` + Tesseract）；三种形态——`tika-server` REST（9998，`PUT /tika`、`/rmeta`）、`tika-app.jar` CLI 一次性进程、Java 库嵌入。

**代价**：JVM 常驻 1–2 GB（可 `-Xmx` 压到 512 MB 但大 PDF 易 OOM）；冷启动 5–15 s、单次 CLI 也有 1–3 s JVM 启动税；镜像约 0.4–1.2 GB；中文 PDF 常用 CID 字体且缺 ToUnicode CMap，PDFBox 抽出的文字层出现乱码/丢字的概率明显高于 PyMuPDF 系（经验结论，需用自己的样本实测）；扫描件 OCR 还要额外装 `chi_sim` 训练数据，中文准确率一般。

| 方案 | 格式覆盖 | 中文质量 | 部署重量(5=轻) | 许可 |
|---|---|---|---|---|
| MarkItDown | 4（pdf/docx/pptx/xlsx/html/epub） | 4（底层走 pdfminer） | 5（纯 Python） | MIT |
| pypdfium2 | 3（仅 PDF） | 4 | 5 | Apache-2.0 / BSD-3 |
| pdfplumber | 3（PDF+表格） | 4 | 5 | MIT |
| PyMuPDF | 4 | 5 | 5 | **AGPL-3.0**（网络服务有传染风险） |
| python-docx | 1（仅 docx） | 4 | 5 | MIT |
| Unstructured | 5 | 3（fast=pdfminer，hi_res 需 torch） | 2 | Apache-2.0 |
| Docling | 4 | 4–5（版面/表格强） | 2（torch，数百 MB~GB） | MIT |
| Apache Tika | 5（老格式最强） | 3 | 2（JVM） | Apache-2.0 |
| AWS Textract | 3（PDF/图片） | 3（`DetectDocumentText` 支持中日韩；`AnalyzeDocument` 的 FORMS/TABLES 仅英文，以官方文档为准） | 1（外部服务，违背单机自足） | 商业 |

**推荐（默认 vs 可选）**
1. 默认（P0）**零额外容器、纯进程内**：MIME 路由自写（扩展名+magic 约 40 行）→ PDF 用 `pypdfium2` 取文字并按 `<50 字符/页` 判扫描件（直接复用 COA 的阈值思路）→ 需要表格时用 `pdfplumber.extract_tables`（MIT）→ DOCX/PPTX/XLSX/HTML 用 **MarkItDown**（MIT，直接产出 Markdown 喂 LLM）→ txt/md/csv 透传。
2. 扫描件 OCR **默认关闭**，返回 `degraded` + `warnings`；确需开启时按 profile 启用 PaddleOCR 或 Tesseract(chi_sim)（P1）。
3. **Tika 定位为可选 fallback，不做默认、不做常驻容器**：只在原生库搞不定的老/冷门格式（.doc/.ppt/.xls/.rtf/.odt/.msg/.eml/压缩包/未知 MIME）上启用，形态优先「`docker run --rm` 或 `java -jar tika-app.jar --text` 一次性进程」，仅在批量老格式导入时才起 9998 profile。理由：单机场景格式以 PDF/Word/HTML 为主，Tika 的覆盖优势换不来 1–2 GB 常驻内存。
4. 不把 Docling/Unstructured 的 ML 依赖放进默认路径（torch 体积大，收益集中在复杂版式，留 P2）。

**`DocumentParser` 端口设计（对齐 `_design/04` §5.6，不改该文件）**
- 端口只输出 `ParsedDocument{pages, blocks, tables, metadata, provider, warnings}`，**绝不透出 Tika 的 SAX/XML 中间结构**，否则换实现必改下游。
- 增加 `capabilities() -> {OCR, TABLES, OFFDOC, ...}`；不支持返回 `Unsupported`，禁止静默降级成纯文本。
- 实现内部做链式路由 `DetectMime → Router → [Native | MarkItDown | OCR | TikaFallback]`，优先级与开关走配置装配；换解析器只改装配，不动契约。
- `Block.id` 稳定可复算（`hash(ref+page+idx)`）并保留 `page/bbox`，供本体抽取做证据定位与溯源。
- OCR/批量解析只走 `parseAsync`（本地线程池/子进程），异步是能力位，不新增端口。
- 同时输出「Markdown 文本 + 结构化块」，避免下游退化为只吃纯文本、丢失表格与层级。
