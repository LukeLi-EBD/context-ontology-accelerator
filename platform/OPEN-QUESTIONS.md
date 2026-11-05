# 开放问题台账（S0–S11）

> 规则：每条必须给出「按哪条原则自定 / 定了什么 / 将来什么条件触发重审」，不留只有“待定”的条目。
> 状态：`open`（已有默认动作，可继续） / `resolved`（已实测或已被上层决策取代）。

| ID | 问题 | 自定依据 | 当前默认动作 | 触发重审条件 | 状态 |
|---|---|---|---|---|---|
| OQ-01 | Oxigraph 镜像实际为 `0.5.7`，03 §2.2/§8.1.1 原写 `0.4.x` | 「文档与代码不一致时以 03–07 为准；必须偏离先记录并改文档」；本机只缓存 0.5.7，且 `/query`、`/update` 已实测可用 | 全仓统一 pin `oxigraph/oxigraph:0.5.7`，03 已同步为 0.5.7；S1 能力探测以该版本为准 | S1 能力探测发现 0.5.x 与 0.4.x 的关键语义差异，或需要回退旧版本 | resolved（文档已改） |
| OQ-02 | Oxigraph 官方镜像为 distroless（无 shell/curl），无法做容器内 healthcheck | 「不做运维/可观测性扩张」+「不得伪造健康」；03 §16.1 的图探针本来就由平台执行 | compose 对 oxigraph 用 `service_started`；真实图探针由 `platform probe` / 启动自检第 5 项 / `/readyz` 承担；03 §8.1.1 已修正 | 镜像提供健康子命令，或改用 pyoxigraph 进程内（则不需要该 healthcheck） | resolved（文档已改） |
| OQ-03 | 07 的 `blob` DDL 没有 `metadata` 列，但 04 的 `put()` 带 metadata | 「端口契约优先」+「不静默丢弃输入」 | S0 在 `blob.metadata jsonb` 存调用方 metadata（同内容共享）；S2 起 key 级业务元数据落 `platform.document.metadata`，`blob.metadata` 仅保留存储提示（如 filename） | 需要按 ref（而非内容）保存独立元数据时，把 metadata 从 blob 迁到 blob_ref | resolved（S2 已落业务表） |
| OQ-04 | S0 的 `learn`/`lean` 都是 3 容器，与 03 D17（learn 5 容器）不同 | 「一次只推进一个切片」+「不把未实现服务伪装成常驻」 | S0 只起 3 容器；`COMPOSE_PROFILES=learn` 仅表达意图；embedding/reasoner 已在 S3/S5 补齐，learn = 5 容器 | —（条件已满足） | resolved（S5 已补齐 reasoner） |
| OQ-05 | ObjectStore 是内容寻址（按 hash），但端口签名是 `bucket/key` | 「CAS 去重」+「端口契约保持 AWS 级语义」 | `blob_ref.owner_id = "<bucket>/<key>"` 建立 key→hash 映射；同 key 覆盖写时替换 ref 并递减旧 refcount；`delete` 幂等软删 | 需要对象版本化/不可变快照时（S2 文档版本），改为 ref 带 version 列 | open |
| OQ-06 | `graph.provider` 允许 `fuseki`/`age`/`pyoxigraph`，但 S0 只有 `oxigraph-http` | 「不写死 fuseki，只保留端口兼容」+「能力不虚报」 | 配置校验阶段直接 `E_PROVIDER_UNSUPPORTED` 退出 78，绝不静默回退 oxigraph | 实现 fuseki/pyoxigraph 适配器时；或用户决定启用 Fuseki 双跑 | open |
| OQ-07 | S0 用 CLI smoke 而非 pytest 作为验收 | 「至少一条可执行验收（pytest 或脚本）」+「不新增仅用于测试的依赖」 | `platform smoke` 在容器内跑 7 项断言；宿主机 `tests/acceptance.ps1` 覆盖两条失败路径 | 需要并入 CI 或契约测试框架时，再引入 pytest（版本需 pin） | open |
| OQ-08 | Windows bind mount 上目录 fsync 不可用 | 「Windows 实际跑通优先」+「07 的原子性协议」 | 文件级 `fsync` 照做；目录 fsync 失败仅记 debug 日志（`fsync_dir=unsupported`），rename 仍为同卷原子替换 | 生产换 Linux 卷（目录 fsync 生效）；或 Windows 断电一致性出现实测问题 | open |
| OQ-09 | 11MB 启动探针每次启动都会写一次（虽然同 hash 去重） | 「启动自检必须有存储探针」+「路径真实」 | 探针使用固定内容，命中已有 hash 时不重复落盘；但仍执行 put/head/get/sha/delete 全链路 | 启动耗时敏感时，改为 `--probe-storage=false`（需新增配置与文档） | open |
| OQ-10 | PostgreSQL 18 官方镜像的 PGDATA 变为 `/var/lib/postgresql/18/docker`，按 03 原写法挂 `/var/lib/postgresql/data` 会启动失败（实测报错：`in 18+, PGDATA is /var/lib/postgresql/18/docker`） | 「Windows/Docker 实际跑通优先」+「卷路径以镜像事实为准」 | compose 卷目标改为 `/var/lib/postgresql`；03 §8.1.1 已同步；`docker compose down -v` 后重建通过 | 换用非官方 PG 镜像或 PG 17 及以下时，恢复 `/var/lib/postgresql/data` | resolved（已实测） |
| OQ-11 | compose 注入 `PLATFORM__DATABASE__URL` 会补上 YAML 中缺失的 `database.url`，导致“缺必填项”的失败用例被 ENV 掩盖 | 「ENV 优先级高于 YAML」（04 §10.1）+「失败用例必须可稳定复现」 | 失败用例改用与 ENV 无关的 `graph.provider=fuseki`（78）；保留 ENV 覆盖能力作为部署便利 | 若禁止 ENV 覆盖数据库连接，需在配置加载层显式禁用该键并改验收 | resolved（已实测） |
| OQ-12 | 03 §5.2.1 写“GSP 覆盖 GET/POST/PUT，DELETE 未文档化；裸 `/store` 可读”，与 0.5.7 实测不一致：实测 DELETE 默认图/命名图均 204；裸 `/store` 是整个数据集（`?default` 才是默认图，Turtle Accept 读数据集会 400）；SERVICE 返回 HTTP 200 但 JSON 损坏 | 用户要求「`GSP_SUPPORT` 只能填实测值」+「实测偏差必须记录并给应对」 | `GSP_SUPPORT=full`；适配层固定用 `?default`/`?graph=`；GSP 只作为兼容出口，平台主路径走 SPARQL Update；`SERVICE` 继续被平台护栏拦截，manifest 标 `federation_service=false`。03 §5.2.1 不改（以实测表为准），差异见 S1 设计 §3 | 升级 Oxigraph 版本后重跑 `platform graph-capabilities`，若 `full` 不再成立则降级为 `partial` 并切换发布路径为 SPARQL-only | open |
| OQ-13 | 本体 `content_hash` 用“排序后的 N-Triples 行 + sha256”，未实现 RDFC-1.0；含空白节点的本体每次解析标签可能不同，哈希不稳定 | D18「不自研算法」+「幂等优先」 | 无空白节点本体可稳定去重；含空白节点时可能新建版本，靠 `semver`/`label` 人工判别。S1 设计 §9 已标注 | 出现真实含空白节点且需要去重的本体时，引入成熟 RDF 规范化库（不自研） | open |
| OQ-14 | 03 §4 写“回滚=切读指针”，04 §5.2 写“rollback 是发布一个指向旧内容的新版本，不删除历史” | 「文档冲突以 03 为准」+「04 的不可变版本语义」 | 合并执行：新建版本行（新 `version_id`，复用旧 `content_hash`/`graph_iri`，`rollback_of` 记录来源），再把 `graph_pointer` 切到新行；旧版本行不修改、图不删除。两份文档的意图都满足 | 若将来要求“回滚不产生版本号”，则改为纯指针切换并更新 04 §5.2 | open |
| OQ-15 | bootstrap 只支持单文件（`ontology.init_source`），不是扫描目录；文件缺失时 `skipped` 而不是启动失败 | 03 §8.2 只给 `init_source` 单值；「bootstrap 是可选便利，不应阻塞 serve」 | `once`/`watch` 都按单文件处理；缺失记 `ontology_job=skipped`，serve 继续；文件变更按 content_hash 判断 | 需要一次导入多份 T-Box 时，改为目录扫描（按文件名排序、逐文件版本化） | open |
| OQ-16 | 文档 `document_id` 直接取内容 sha256，同内容不同文件名只能保留首次的 `filename` | 「内容寻址天然幂等」+「不让重复上传产生重复行」；文件名不是身份 | `document_id=sha256`；重复上传返回 200 + `deduplicated=true`，不覆盖首次文件名/元数据；`status` 仍为 `parsed|degraded` | 业务需要“同一内容多份命名/多归属”时，增加 `document_alias` 或 `document_key` 表，document_id 改为 UUID、sha256 做唯一索引 | open |
| OQ-17 | 非 PDF（docx/pptx/xlsx/txt/html）统一记为第 1 页，丢失原始幻灯片/工作表页码 | 04 §5.6 `ParsedDocument` 只有 `pages`；S2 不做版面/幻灯片语义 | `document_page.page_number=1`；manifest 保留 MarkItDown 的原始文本；S6 引用显示“文档/页 1” | S6 引用质量要求精确到幻灯片/工作表时，解析器改为按 `blocks` 拆分并映射页号 | open |
| OQ-18 | `token_estimate` 用 `ceil(字符数/2)` 估算，不是模型 tokenizer | 「不新增依赖、不引入算法」+ S6 预算只需保守上界 | 每块 `token_estimate=max(1, ceil(len(text)/2))`；S6 用该列做预算粗算 | 接入实际 LLM tokenizer（DeepSeek/方舟）后，改为离线 tokenizer 计数并重算该列 | open |
| OQ-19 | 入库顺序是“先解析、后写 CAS、再写 PG”，不是对象与元数据的单事务 | 「坏文件不落半成品」优先于“先存原件”；04 §4.1 的 put 本身是独立事务 | 解析失败 → 不写 CAS/不写表；CAS 写成功但 PG 事务失败 → 仅当 `document` 行不存在时删除本次对象引用 | 需要“原件必留档（即使解析失败）”时，改为先 CAS 后解析，并增加 `document(status=failed)` 的显式隔离 | open |
| OQ-20 | `markitdown[docx,pptx,xlsx]` 连带 pandas/numpy/onnxruntime，镜像体积与构建时间明显增加 | 03 §3.4.7 指定 MarkItDown 统一覆盖 Office；「不新增自研解析」 | 接受当前 extras；多阶段构建保证运行镜像不含编译器；版本 pin 0.1.9 | 镜像体积 > 1.5 GB 或构建时间不可接受时，按格式拆 extras（先 docx，pptx/xlsx 延后）或改用轻量专用库 | open |
| OQ-21 | `GET /documents/{id}/source` 把原件读入内存再 `Response` 返回（上限 200 MB） | 「presign=false 时走平台流式代理」；S2 先用响应体直出 | 单用户场景接受 ≤200 MB 内存峰值；响应头 `X-Presign=false` 明示未直连 | 需要下载 >200 MB 或多人并发时，改为 `StreamingResponse` + `ObjectStore.get_stream` | open |
| OQ-22 | 文件类型按扩展名路由，不做内容嗅探（magika 虽随 MarkItDown 安装但不用于路由） | 「扩展名是用户声明，解析失败由引擎报告」+「不引入额外判定算法」 | `.pdf/.docx/.pptx/.xlsx/.html/.htm/.txt/.md/.csv` 白名单；其余 400 `E_DOC_FORMAT_UNSUPPORTED`；扩展名与内容不符由引擎抛 `E_DOC_PARSE_FAILED` | 出现大量“扩展名错标”的真实资料时，启用 magika 内容嗅探并保留扩展名作为提示 | open |
| OQ-23 | `ocr.enabled=true` 从 S0 的“degraded 提示”改为 S2 启动 fail-fast（exit 78） | D22「OCR 关闭」+「缺能力不得静默伪装」；S2 没有 OCR 引擎 | 配置校验直接 `E_OCR_UNSUPPORTED` 78；扫描件在入库时以 `NO_OCR_ENABLED` + `degraded=true` 如实返回 | 真正接入 OCR（PaddleOCR/Tesseract）后，允许 `ocr.enabled=true` 并删除该 fail-fast | resolved（S2 已实现） |
| OQ-24 | 中文词法检索用 `word_similarity(q, text)`，而 S3 设计初稿写的是 `similarity(text, q)` | D18「用现成库/函数，不自写算法」+「中文必须可召回」；`similarity` 以整段文本 trigram 并集为分母，1200 字 chunk 命中 4 字查询会接近 0，等于屏蔽中文 | 词法分数 = `ts_rank_cd + word_similarity`；候选条件 `word_similarity >= min_similarity(0.05)`；S3 设计 §2.3 已同步并标注偏离 | 引入 `zhparser`/中文分词后，改回 `ts_rank_cd` 为主的纯 FTS 评分，并按实测调阈值 | resolved（已实测，S3 设计已改） |
| OQ-25 | `document_chunk.text_search` 生成列 + HNSW 索引在 `ALTER TABLE` 时需要对既有行回填/建索引 | 「迁移必须幂等」+「不预建全量大表」；当前库仅 14 文档，迁移 <1s | 迁移 `V4` 直接 `ALTER TABLE ... ADD COLUMN ... GENERATED ...`；`CREATE INDEX` 不并发（单机可接受） | 文档量到百万 chunk 或需在线迁移时，改为 `CREATE INDEX CONCURRENTLY` + 回填作业（需拆迁移脚本与作业） | open |
| OQ-26 | `embedding.provider=fake` 的向量是“字符 trigram 哈希”，不是模型；早期汇报的“真实 BGE-M3”与台账表述冲突 | 用户要求「不许含糊，查明事实」 | **事实：learn 档走真实 BGE-M3**。`provider=local-bge`，TEI 加载 `data/models/bge-m3` 真实权重（12 文件 2.295 GB，`pytorch_model.bin` 2.27 GB，xlm-roberta 24 层）；`/v1/models` 返回 `model=/data/models/bge-m3`，embeddings 返回 1024 维；预热后单条中文请求 91/105/110 ms，冷启动约 124 s。`fake-hash-1024` 仅 `smoke-s3` 进程内确定性测试使用，模型名隔离、不入生产索引 | 若需要离线更轻量方案，可换 fastembed，但当前真实模型已满足链路与验收 | resolved（2026-11-05 实测，S3 设计 §10.2） |
| OQ-27 | TEI CPU 后端实测限制单请求 batch ≤ 4（日志：`Backend does not support a batch size > 4`），与设计默认 16 不符 | 「实测优先于默认值」+「错误必须显式」 | `EmbeddingConfig.batch_size` 类默认 16；`data/platform.yaml` 置 4；客户端按 `batch_size` 切批，超限由 TEI 返回 4xx 时映射为 `E_EMBED_UNAVAILABLE` | 换 GPU/新 TEI 版本或换 embedding 后端后，按实测上限调回更大 batch 以提升索引吞吐 | open |
| OQ-28 | S3 落地 embedding 后 learn 常驻为 4 容器（reasoner 仍在 S5），与 03 D17 的 5 容器仍有 1 个差距 | 「不把未实现服务伪装成常驻」+ 05 §1.6「learn 全开」 | S5 已落地 `reasoner`；learn profile 现为 5 容器（platform/postgres/oxigraph/embedding/reasoner） | —（条件已满足） | resolved（S5 已补齐） |
| OQ-29 | `Unsupported` 在 `api._HTTP_STATUS` 映射为 **400**，而 S4 设计 §4 表写 503（用于 `E_LLM_NOT_CONFIGURED`/`E_EXTRACTION_DISABLED`） | 「不破坏已跑通的契约」优先于改表；S0 起 `Unsupported` 一直是 400，改 503 会噪声化 S0–S3 验收 | 保持 400；设计 §9.4 已标注偏差；客户端按 `providerCode` 而非状态码分支 | 若外部客户端依赖 503 语义（“稍后重试”），则把 `Unsupported` 拆成 `Unsupported`(400) 与 `Unavailable`(503) 两个端口码 | open |
| OQ-30 | A-Box（`urn:platform:graph:abox:main`）不版本化、无 update/delete 流程，已批准事实无法在 S4 内撤回 | D20「默认读最新图版本」只约束 T-Box；单机单租户 + 候选行保留 provenance | 审批只做 `INSERT DATA`；重复审批被状态机拦住；撤错事实需要 S5 之后的治理能力（未实现） | S8 已实施：PG `fact_assertion` 账本（source/asserted_at/state active·retracted·superseded）+ A-Box 只投影 active；撤回=显式置 retracted + append-only `fact_event`，不覆盖、不删审计；同 `(s,p)` 多值全部返回并标 conflict；支持单条/按来源批量/恢复。证据：`smoke-s8` 全绿、S8 设计 §2/§6 | resolved（2026-11-05） |
| OQ-31 | `smoke-s4` 每次运行都会把 1 条 nonce 三元组永久写进 A-Box，并用 `uuid4` nonce 语料避免干扰 | 「验收必须可重复」+「不改主路径语义」 | 测试三元组属 `urn:platform:entity:库<nonce>`，可人工清理；断言只比较计数增量，不比较全量 | S8 已实施：smoke s4–s8 全部改用 `urn:platform:test:<nonce>:sN` 独立图，审批带 `graph`、物化带 `aboxGraphs`，finally `DROP GRAPH` + `purge_test`（审计不删）；`acceptance.ps1` 增加 `demo abox purity`（abox:main 计数前后一致且无 test 图残留）。证据：S8 设计 §7 | resolved（2026-11-05） |
| OQ-32 | `approve()` 先写图、后改 PG 状态：若 PG 更新得 0 行（并发被拒/被批），图里已多出一条三元组 | 设计 §2.5 明确「先写图再更新状态，图失败则候选保持 pending」——优先“不丢已批准事实”；RDF 集合语义使重复插入无害 | 0 行 → 抛 `Conflict`；多余三元组留在图中（集合语义下重复不可见）；候选行状态不变 | 需要严格“状态与图原子一致”时，改为先 `UPDATE ... WHERE state='pending'` 抢占，再写图，失败则回滚状态（需状态机加 `writing` 中间态） | open |
| OQ-33 | S0 判据写“3 容器 healthy”，但 compose 只给 platform/postgres 配了 healthcheck；oxigraph 镜像无内置探针（image 内无 curl/wget），`docker compose ps` 显示 Up 而非 healthy | 「以可执行证据代替状态标签」+「不把未验证的东西说成健康」 | 保持不加探针；oxigraph 的可用性由 `/readyz` 的 `graph=ok`、`platform smoke` 的 graph_roundtrip 与 acceptance 的“停图→69/503→恢复”证明 | 若需要编排层自动等待图服务，改用 `depends_on: condition: service_healthy` 时必须先给 oxigraph 加探针（可基于 bash `/dev/tcp` 或注入探针脚本） | open |
| OQ-34 | S5 v0.1 设计允许 `profile=RDFS`，但 ROBOT 1.9.6 `reason --help` 只有 ELK/HermiT/JFact，**无 RDFS 推理器**；ELK 实测也推不出 `rdfs:range` 与 `subPropertyOf` 断言传播 | 「推理器只做驱动，不自研算法」+「实测优先于设计」 | 实测（2026-11-05）：ELK 可推 `subClassOf` 传递与 `domain`，**推不出** `range`/`subPropertyOf`；改用 Apache Jena 6.2.0 一次性作业 `riot --rdfs=<vocab> --output=nt`，实测四类闭包全出（见 S5 设计 §9.4）。镜像 `agent-rdfs:0.1-s5`，compose `rdfs` 服务 `profiles:["job"]`（非常驻），退出码 0/2/3 已实测；`reasoning.profile=RDFS` 仍 78 fail-fast 并提示该作业 | 把 export→job→import 自动编排进 `materialize()`（新 OQ-39）；或改用常驻 RDFS 服务 | resolved |
| OQ-35 | S5 形状 `LocatedInObject` 要求 `platform:locatedIn` 为 IRI 且 `maxCount 1`，与 S4 “位于”被抽成字面量冲突 | 用户拍板：`locatedIn` 必须是 IRI（指向实体），字面量改写 `hasLocationLabel`（`xsd:string` 弱标注） | S4 抽取可解析实体 → IRI；解析不到 → **不写** `locatedIn`，写 `hasLocationLabel`（confidence 0.4）+ 人工队列。SHACL：`locatedIn` 约束 `sh:nodeKind sh:IRI`（去掉 `maxCount`），新增可选 `LocationLabel`（`xsd:string`, `maxCount 1`）。`smoke-s4` 22/22 重跑；A-Box `validate('abox')` = `conforms=True, violations=0` | —（冲突已消除） | resolved |
| OQ-36 | ROBOT `reason` 默认只回吐源公理，不产生 `ClassAssertion` 蕴含（`alice a Student` 不会推出 `alice a Person`）；必须显式 `--axiom-generators "SubClass ClassAssertion" -d true` | 「物化必须真的产生蕴含」+「驱动成熟工具而非自研」 | reasoner 容器固定这两组参数；S5 设计 §2.1 已写明；`inferred.entailed` 断言据此通过 | 需要属性链/逆属性/数据属性蕴含时，扩展 axiom generators 并补对应用例 | open |
| OQ-37 | `graph_oxigraph.py` 的 `IRI_RE` 过宽（`^[^<>"{}|^`\s]+$`），`"bogus"` 也被当成合法 IRI；直接收紧会改变 S1–S4 的图名校验行为 | 「不破坏已通过部分」+「非法输入必须报对错误」 | 不改全局 `IRI_RE`；仅在 `reasoning._resolve_target` 增加 scheme 检查（`":" in target`），使 `graph=bogus` → `E_VALIDATE_TARGET` | 将来统一图名校验时，把 scheme 校验下沉到 `GraphStore` 并回归 S1–S4 | open |
| OQ-38 | 04 §5.3 写了独立 `explain(packId)`，但 S6 不做结果缓存/持久化，packId 无法二次查询 | 「不做未消费的能力」+「缺省不新增依赖」 | S6 把 `explain` 收敛为响应内联 `steps`（`graph.seed/graph.facts/search.hybrid/budget.cut`），不提供 `GET /context/explain` | 出现“需要按 packId 审计”的需求时再引入 pack 持久化（PG 表 + TTL） | resolved |
| OQ-39 | RDFS 闭包作业最初只能手工 `docker compose --profile job run --rm rdfs`，`materialize()` 不自动 export/job/import | 用户要求「RDFS→OWL→SHACL 串成一条链且幂等」+「任一步失败整次失败、不半途落图」 | `materialize()` 已串联：`ReasonerClient.rdfs_closure()`（reasoner `POST /v1/rdfs`，Jena 5.5.0 `riot --rdfs`）→ ELK（输入含闭包）→ SHACL 门禁 → 单次 `replace_graph`；`input_hash` 纳入 `mode`，同版本同 mode 重跑 `skipped=true`；`mode=validate` 只门禁、`mode=rdfs` 只闭包+门禁。一次性 job 保留作离线复现。证据：S5 设计 §9.5 | 若 Jena 闭包耗时成为瓶颈，改为常驻 RDFS 服务或增量闭包 | resolved（2026-11-05 实测） |
| OQ-40 | `ontology.init_mode=watch` 每 30s 把 pointer 回退到 `ontology.init_semver` 内容，覆盖用户在 UI/CLI 发布的本体 | 「bootstrap 是可选便利，不应反向覆盖运行期发布」+「不破坏已通过部分」 | `ontology_pg.bootstrap` 检测 pointer 的 `semver ≠ init_semver` 时返回 `skipped`（`pointer managed outside init source`）；同 semver 仍按 content_hash 幂等 | 若确实要求 watch 强制以文件为准，改为每次检测文件 hash 并显式 `force=true` 发布 | resolved（S7 实测） |
| OQ-41 | `index.html` 通过 `file://` 直开时 `Origin: null`，平台无 CORS 头，浏览器拦截 `/ui/api/*` | 用户硬要求「index.html 能直接打开」+「不引入前端框架/构建链」 | `api.py` 加 `CORSMiddleware`：`allow_origins=["null","http://127.0.0.1:8080","http://localhost:8080"]`，GET/POST；无鉴权，不是安全边界；`smoke-s7` 增 `ui.file_origin` 断言 | 引入鉴权/多用户后，收紧来源并改为同源托管 | resolved（2026-11-05 实测） |
| OQ-42 | `EmbeddingClient.available()` 以 `embedding.endpoint=http://embedding:80/v1` 拼出 `/v1/health`、`/v1/models`，TEI 均为 404 → 永远“不可用”；概览页的 embedding 行反而因 `and` 返回 0 被标 `ok=true` | 净室验证发现「读数为绿但实际不可用」，与「降级必须可见」冲突 | 修正探测：先剥尾部 `/v1` 探 `/health`，再退 `/v1/models`；`webui._probe_embedding` 不可用时抛 `E_EMBED_UNAVAILABLE`，概览如实标红 | 换非 TEI 后端时，按厂商健康端点调整探测顺序（保持“探测失败即 degraded”） | resolved（2026-11-05 净室实测） |
| OQ-43 | TEI 冷启动加载 2.3 GB 权重约 2 分钟，`seed.ps1` 若立刻索引会退词法（`embeddings=0`），示例站点“有内容但无向量” | 用户要求「净室从零到可用」且示例打开即有内容 | `seed.ps1` 在索引前轮询概览 `embedding.ok`，最长 300 s；未就绪则打印警告后继续（诚实降级）。净室实测：up 11.3 s + seed 124.1 s，`embedding ready` 后索引 `embeddings=2` | 若未来换外部 embedding，轮询逻辑仍走同一 `embedding.ok`，无需改脚本 | resolved（2026-11-05 净室实测） |
| OQ-44 | `merge` 后原断言 `state=retracted` 且 `superseded_by` 指向新断言，`restore` 明确拒绝；因此**合并不可逆**（撤错合并只能再发一条新断言，不能回到两值冲突态） | S9 只要求“合并为一条新断言、原两条 retracted 并 linked”，未要求 unmerge；为防误恢复把裁决结果拉回冲突，先拒绝 `restore` | `merge` 写 `merged` / `merge_superseded` 事件并互链；原断言不可恢复；审计保留全部前值 | S10 已实施：`unmerge(eventId)` 把新断言置 `retracted`、原两条恢复 `active` 并清 `superseded_by`，追加 `unmerged` 正向事件；`keep`/`keep_both` 走同一个 `undo_resolution`，追加 `resolution_undo`。原裁决事件不删除，两条撤销操作后链仍 `verify` 通过。证据：`smoke-s10` **22/22**，S10 设计 §9 | resolved（2026-11-05） |
| OQ-45 | `facts-replay` 在空库重放时，会把 `purge_test` 清理掉的测试断言（`fact_assertion` 行已删、事件仍在）按事件重建出来，因此相对“当前库快照”会多出 `extra` 条；这些 extra 是历史测试产物，不是状态不一致 | 「审计事件不可删」+「重放必须忠实于事件链」；若为了比对去丢弃 extra，等于隐藏链上的真实事件 | 重放结果分别返回 `matched/mismatched/extra`：`ok` 只要求 snapshot 中每条状态一致且无 missing；`extra` 如实列出。正式环境不用 `purge_test` 时 extra 为 0 | 需要严格“库内只剩快照事实”时，改为把导出/重放限定到完整链的某一前缀，或为 `purge_test` 写补偿事件 | S12 已实施：`purge_test` 对每条删除断言追加 `purged_test_graph` 事件（V11 迁移扩展 action），`reconstruct` 遇该事件即移除事实；`compare.ok` 现在同时要求无 `extra`。历史遗留（S12 前无事件的 purge）由 `reconcile_purges` 逐条补写并标 `reconciled=true`，仅限 `urn:platform:test:` 图。证据：`smoke-s12` **11/11**（`replay.purge_exact`）、acceptance 41/41 | resolved（2026-11-05） |
| OQ-46 | S9 的按时间窗/来源导出，返回的事件是过滤后的子集；`hash=sha256(prev_hash + body)` 使子集首条无法自证（`prev_event` 指向被过滤掉的事件）。实测 `facts-export --from 2026-11-04T21:26:27+00:00` 得到 59 条，`facts-verify` 报 `event 298 hash mismatch`，退出 1 | 「链完整才可校验」+「过滤导出在 S9 已对外声明」；S10 重放进一步暴露该缺口，但修复属于 S9 语义，不在本切片擅自改 | 旧行为（S10–S11）：过滤导出的 `chain.ok=false`、CLI 退出 1；文档要求用不过滤的全量导出做 verify/replay | 需要可验证的按来源/时间窗导出时，S11 增加“链锚点”（导出首事件的 `prevEvent/prevHash` 或锚定前缀）并让 `verify_records` 支持起始锚；或改为按来源导出完整前缀链 | S12 已实施后者：`events.ndjson` 永远是到 `cutoff_seq` 的完整前缀链；`--from/--to/--source` 只作用于 `assertions.ndjson`、`summary.md` 与事件窗口统计；`export.json` 记录 `cutoff_seq/cutoff_hash/verified_prefix/excluded_count`；`facts-verify` 对链碎片返回 `verified_prefix=false` 并失败。证据：`smoke-s12` 的 `export.prefix_verified`/`export.tamper_fails`，CLI 实测 `--from` 导出 `verified_prefix=true` | resolved（2026-11-05） |
| OQ-47 | `publish(version_id)` 不带 proposal 时走 legacy direct 路径：不跑 SHACL/一致性/breaking 门禁、不触发物化、不改 proposal 状态 | 「不破坏已通过部分」+「启动期 reasoner 未就绪不能把主干打红」；bootstrap 与 S1 smoke 依赖该路径 | 旧行为（S11）：无 proposal → legacy 直发；有 proposal（显式或该版本最新提案）→ governed 三道门禁 + 物化补偿 | 要求“所有发布必须提案”时，在 API 层强制 `proposalId`，并把 bootstrap 改为带系统提案 | S12 已按用户方案二关闭：无 `proposalId` 时在门禁**全部通过之后**原子创建隐式提案（`implicit=true`，审计追加 `proposed`/`approved` 事件），breaking 必须显式 `acknowledgeBreaking=true`；被拒时版本状态与指针零写入。仅 `draft/approved/superseded` 可走该路径，`published` 为幂等 no-op；已发布/superseded 的旧提案不会被当作审批放行。证据：`smoke-s12` 的 `legacy.breaking_rejected`（`E_ONTOLOGY_BREAKING`，status 仍 draft、指针不变）与 `legacy.implicit_gated_publish` | resolved（2026-11-05） |
| OQ-48 | 两套回滚并存：S1 `rollback` 按 OQ-14 新建版本行并切指针；S11 `rollback_to` 只把旧版本状态改回 `published`、被回滚版转 `superseded`，不新建版本 | 用户 S11 明确 `rollbackTo(version)` 语义；同时「不重构已通过部分」要求保留 S1 行为 | CLI 用 `rollback-to` 调 S11，旧 `rollback` 保留；两者都不删版本与图 | 需要统一回滚语义时，合并为单一入口并回写 OQ-14 与 04 §5.2 | open（S11 新增） |
| OQ-49 | breaking 是保守集合规则：删类/删属性、domain/range 集合变小、`owl:minCardinality` 由无到有即判破坏；不判断现存实例是否真的受影响 | 「破坏项必须在发布前列出」+「不自研一致性推断」；实例影响交给门禁② | `diff.breakingItems` 列出五类；`removedClassInstances` 只作为影响面参考；`acknowledgeBreaking` 是唯一放行方式 | 需要精确影响面（例如只对确有实例的类报警）时，在 diff 内追加实例级验证查询，仍不改判定框架 | open（S11 新增） |
| OQ-50 | 导入冲突只与**当前指针图**按 subject 出向三元组比较，不比对历史版本；明细最多返回 50 条（`conflictCount` 为全量） | 「默认 reject 且绝不静默覆盖」+「导入不是全库审计」；历史版本可能本就有不同定义 | `on_conflict=reject` 抛 `E_ONTOLOGY_IMPORT_CONFLICT` 并给差异；`new_version` 建 draft 并记录 `import_conflict_accepted` | 需要“跨全部历史版本检测冲突”时，遍历版本图或引入规范化内容哈希（受 OQ-13 约束） | open（S11 新增） |
| OQ-51 | `superseded` 版本不得物理删除，图与行随版本数线性增长；`smoke-s11` 的测试版本也按此保留，只恢复指针 | 用户硬要求「不允许物理删除任何版本」+「导出内容可再导入」 | 版本行与 `urn:platform:graph:tbox:<version>` 图永久保留；测试用独立 `urn:platform:smoke:s11:<nonce>:` 命名空间，结束后只回指针 | 图体积或备份时间成为瓶颈时，增加只读归档/冷存储导出（仍不删除在线版本） | open（S11 新增） |
| OQ-52 | ROBOT 对“存在不可满足类”的 T-Box 以非零退出返回 500（旧 reasoner 只把报文含 `inconsisten` 判为不一致），导致 S11 一致性门禁拿到 `E_REASONER_BAD_RESPONSE` 而不是本体错误码 | 「门禁必须以本体错误码拒绝」+「不自研推理/不改 ROBOT」；`smoke-s5` 的 v3（A⊑B 且 A⊑owl:Nothing）走直接发布时暴露 | `_gate_consistency` 捕获 `E_REASONER_BAD_RESPONSE` 且报文含 `unsatisfiable` 时映射为 `E_ONTOLOGY_INCONSISTENT`（details `reason=unsatisfiable`），指针不切换；`smoke-s5` 改断言发布被拒 | reasoner 服务改为返回结构化 `consistent=false`/`unsatisfiableClasses` 时，删除文本匹配并改读字段 | resolved（2026-11-05，S12） |
| OQ-53 | 窗口导出（`--from/--to/--source`）的 `assertions.ndjson` 只含窗口内断言，而 `events.ndjson` 是完整前缀链；用该文件到空库重放时，窗口外的前缀事实会相对窗口快照报 `extra` | 用户 S12 明确“过滤只作用于视图、链必须完整”；重放语义未要求覆盖窗口导出 | 窗口导出只承诺“可 verify 的完整前缀 + 窗口视图”；只有全量导出（无过滤）承诺 replay 与快照逐条一致。`export.json` 的 `filter/excluded_count` 明示窗口范围 | 需要窗口导出也能精确重放时，增加 `scope=window` 重放模式，或在导出中携带 cutoff 时刻的前缀快照（体积换精度） | open（S12 新增） |
| OQ-54 | S12 之前 `purge_test` 只删断言行、不写事件；为让老库的导出仍可自证，`export_events` 会把 `urn:platform:test:` 图的孤儿断言补写成 `purged_test_graph`，`reconciled=true` | 「导出必须可复现库状态」+「不伪造正常业务清理」；只有 `purge_test` 会删断言行且只接受 test 图 | 补写事件发生在导出时刻（`createdAt` 为补写时间，非真实清理时间），payload 标 `reconciled=true`；非 test 图的孤儿断言不补写，仍以 `extra` 如实暴露 | 历史数据不再需要兼容，或要求事件时间与真实清理时间一致（无法从现存数据恢复）时，改为一次性离线修复脚本并冻结在线补写 | open（S12 新增） |
| OQ-55 | pypdfium2（PDFium）非线程安全：`parse_concurrency=2` 并发解析 PDF 时进程 native segfault（corpus 实测 3 秒内崩溃）。但 CLI 仍要求“并发可配”，不能把并发写死为 1 | 用户要求「失败隔离，单文件失败不得中断整批」+「并发可配」；native crash 会杀掉整批，比慢更不可接受 | `parsers.py` 用模块级 `_PDFIUM_LOCK` 串行化 PDF 打开/逐页取文本/关闭；解析池的并发只对 docx/txt/md 有效。代价：PDF 解析吞吐受单核限制 | 出现“PDF 占比高且解析是瓶颈”时，改为多进程解析（每进程独立 PDFium）或换线程安全解析器；不得在无锁情况下恢复并发 |
| OQ-55 结论（2026-11-05 P0） | **P2，暂不修**。实测平台侧解析仅 **3.1 ms/chunk**，TEI 嵌入 **1.54 s/chunk**，解析占比约 **0.2%**，不是当前瓶颈 | 触发条件：**一次批量导入数百 PDF 且解析时间超过总时长 20%** 时才做 | 选定方案：**改并发模型（2–3 个独立子进程，各加载一份 PDFium），不换库**。否决 PyMuPDF/MuPDF（AGPL，对外提供产品需商业许可）、Tika（额外 Java 容器）、docling（带模型权重，与轻依赖取向冲突） | 真正贵的是扫描件 OCR（1,220 页 / 1,434 s），优先压 OCR |
| OQ-56 | 批次身份 = 解析后的根目录绝对路径（`import_batch.root_path UNIQUE`）；目录改名/移动后再次导入会生成新批次，旧批次的续跑记录按原路径保留 | 「同一目录再次执行即续跑」最直观；用路径做键不需要额外 ID，且与用户命令一致 | 移动目录 = 新批次（重新扫描、去重仍按 sha 命中已有文档，不会重复解析）；旧批次只读保留 | 需要“移动后继续续跑”时，把批次身份改为“内容指纹（目录清单 sha）+ 可选 name”，或增加 `--batch <id>` 强制指定 |
| OQ-57 | dry-run 只能预测扫描期失败（空/超限/不可读），无法预测损坏/加密 PDF 的解析失败，因此 `toImport` 与最终 `documentsAdded` 在含坏文件的语料上必然有差额 | 「dry-run 必须快」+「解析失败只有真解析才知道」；为了预测而预解析等于把导入跑两遍 | dry-run 输出 `willFail`（仅扫描期）并额外给出 `toImport`；严格等式验收只在干净语料上做（S13 实测 120=120） | 需要高精度预估时，增加 `--probe`（只解析头部做格式校验），代价是 dry-run 变慢 |
| OQ-58 | 本机 BGE-M3（CPU/TEI，batch=4）实测入库吞吐 ≈ 0.63–1.30 chunks/s，瓶颈是嵌入而非磁盘；几十 GB 语料全量本地嵌入时间不可接受 | 用户要求给出真实决策数据，而不是估算；S13 实测峰值 RSS 118–121 MB、吞吐如上 | 默认仍 `embedding.provider=local-bge`；大批量导入与全量重建的耗时按 chunk 数外推。换外部 embedding 与模型分区的结构见 S3 设计与 `reindex` 设计 | 引入 GPU、外部 embedding 或增大 TEI batch 后重测；以实测决定默认 provider |
| OQ-59 | 批次没有心跳：进程被 Ctrl+C / kill -9 后，`import_batch.status` 仍是 `running`，直到下一次执行同一目录才被改写；UI 会短暂显示“运行中” | 「不做定时扫描/文件监听（P2）」+「不新增后台进程」；心跳需要常驻写库或独立 worker | 下次执行即修正状态；CLI `imports` 与 UI 以 `updated_at` 让用户判断是否陈旧；`KeyboardInterrupt` 路径会立即置 `interrupted` | 需要准确的“运行中/已死”判断时，增加 `heartbeat_at` 列与基于超时的僵尸批次回收（属 P2 运维能力） |
| OQ-60 | reasoner 容器内**没有并发锁**：同一时刻可接受多个推理请求，每个请求都会起一个 `java -Xmx2g`，内存叠加后越过 `mem_limit` 即被 OOM 杀掉 | 「失败隔离」+「不因一次推理阻塞平台其余接口」；改请求逻辑的风险高于改配额，且当前处于长任务运行期（R1：不得打断） | 只调高配额：`mem_limit: 3g → 4g`（`JAVA_OPTS=-Xmx2g` 不变，留 2g 给元空间/线程栈/uvicorn）；**不加进程内锁**，串行化留待下个维护窗口 | 出现并发推理 OOM（`docker inspect` 出现 `OOMKilled=true` 或 reasoner 被重启）时，在 `reasoner/app.py` 增加进程内 `asyncio.Lock`，第二个请求直接返回 `E_REASONER_BUSY`（不排队），并补一条 smoke 用例 | open（S13 新增） |
| OQ-61 | reasoner 需**单飞锁**（single-flight）：同一时刻只跑一个推理，第二个请求返回 `E_REASONER_BUSY` 而非排队等 OOM；当前代码无 `asyncio.Lock`，仅靠 `mem_limit` 兜底 | 「快速失败优于排队拖垮」；但改 `reasoner/app.py` 属源码变更，当前有并行会话在编辑 `src/`，本轮禁止触碰 | 本轮只落 `docker-compose.yml` 配额（`mem_limit: 4g`，见 W-15）；锁逻辑推迟 | **下个维护窗口，随源码一起改**（与 W-13/W-15 同批），不得单独提前改 `src/` | open（S13 新增） |
| OQ-62 | 跨主机锁**无法验活**：不同 host 时拿不到对方 pid 的存在性，只能靠 `-Force` 人工接管（仍可能误伤活着的 40 分钟任务） | 「宁可拒绝也不误杀」；但跨机场景下"自动接管"必然有误判窗口，文件锁本身不具备跨机语义 | 同机任务：靠 `pid`+`host` 验活 + 心跳（已实现）；跨机：默认拒绝，仅 `-Force` 接管并 warn | 出现 >1 台机器并行跑长任务的真实需求时：① 强制"长任务只允许在一台机器上调度"（最省事）；② 或改用带租约/心跳的统一调度（如 PG advisory lock + `pg_stat_activity` 心跳、或引入 Etcd/ZooKeeper 租约）；在此之前**禁止跨机并行** | open（S13 新增） |

**OQ-62 补充 · legacy 锁策略（12:04）**：旧格式锁（无 `pid`/`host`）**一律按"可能存活"处理**——`acquire` 默认拒绝（`E_LOCK_LEGACY_UNKNOWN`，退 76），仅 `-Force` 可接管；持锁方 `heartbeat` 时自动补写 `pid`/`host` 完成升级（`info: lock upgraded to pid/host format`）。因此旧锁在 ≤5 分钟内自然转正，无需人工迁移。残留风险：若旧锁的持锁进程**从未再心跳**且真的已死，就只能等人工 `-Force`，无法自动回收——但这是有意的保守取舍（宁可等人，也不误杀活任务）。

### OQ-40（2026-11-05）TEI `RAYON_NUM_THREADS` 是否生效 — 未验证
- 现象：`docker-compose.yml` 已设 `RAYON_NUM_THREADS=3`，但 8g/8192 warmup 期间 `docker stats` 观察 CPU 395%（≈4 核跑满），无法证明线程被限制在 3。
- 影响：R5“留 1 核给 API/PG/IO”的承诺只能靠容器 `cpus: 4` 兜底，不能靠 rayon 线程数。
- 替代手段：容器级 `cpus: "4"`（已生效，`NanoCpus=4e9`）；若需更细，可改 `EMBEDDING_CPUS=3` 覆盖。
- 待验证：进入容器 `ls /proc/1/task | wc -l`（镜像无 shell，需换方式）或跑负载时观察单核利用率分布。

### OQ-63（2026-11-05）TEI cpu-1.8 在 batch>=3 与 `--max-batch-tokens` 超限时 panic — 已定位，规避生效
- 现象：`core/src/queue.rs:87` `panicked ... "Full(..)"` → 容器退出，客户端见 `Server disconnected`。
  实测 batch=4 → 14/16 失败、batch=8 → 7/8 失败；`MAX_CONCURRENT_REQUESTS=1` 连单条请求都会触发。
- 规避（已落地）：① TEI 侧不再设 `MAX_CONCURRENT_REQUESTS=1`（改 4），单飞由平台 `BoundedSemaphore(1)` 保证；
  ② 平台按“条数 ≤2 且总字符 ≤1600”切批，避免触发 TEI 的内部 split。
- 未解决：镜像本身的上限没有提高（仍是 2 条/请求）；真正提高需换 backend（ORT/GPU）或调大 `--max-batch-tokens` 并给足内存，
  属 P3 性能项，不在本轮做。
- 影响：批量下发在 1194 字符/块的语料上基本退化为逐条发送（1600 预算塞不下 2 块）。

### OQ-64（2026-11-05）嵌入吞吐上限 ~0.18 chunk/s（1200 字符块）— 已实测，待产品决策
- 实测：110 chunks（avg 1194 chars）`elapsed_s=625.18` → 0.176 chunk/s，期间 CPU 395%（4 核打满）；
  短块（367 chars）单条 400ms ≈ 2.19 chunk/s、CPU 仅 35%。
- 判定：长块是**算力瓶颈**（CPU 已满），不是串行等待；短块是**单请求未并行**（受 TEI batch 上限 2 限制）。
- 选项：A 保持现状（28 万 chunk 约 442h，估算）；B 缩短 chunk（会伤检索粒度，用户已禁止）；C 换 ORT/GPU 后端（P3）。
- 状态：open，需用户按 P0 功能节奏决定是否需要提速。

### OQ-65（2026-11-05）发布路径只认“新内容”：同 canonical 内容只能靠 `rollback-to` 假装发布 — 设计债
- 现象：FS-LDM 正式 T-Box 二次导入与首次内容 canonical 相等（2676 三元组不变，仅注释/序列化不同）→ `persist_import` 走 canonical hash 去重返回 `skipped: true` + 已有版本 `ont-f413054a0c72`，因此无法新建 draft；`propose` 又因该版本已 `superseded` 被拒。正式切换只能 `rollback-to ont-f413054a0c72`。
- 后果：① 审计链写 `rolled_back` 而非 `published`；② `rollback_to` 用 `COALESCE(published_at, now())` 沿用旧发布时间，看不出本次发布；③ 无 `publishedBy` / `previousVersionId` 字段；④ 版本谱系呈现“新版本 → 旧版本”的倒退观感，实际语义是“向前激活既有内容”。
- 方案（不改状态机，只加一条入口）：
  1. `publish(version_id, ..., resume_from_version: str | None = None)`：`publish` 增 `resumeFromVersion`（CLI `ontology publish --existing <versionId>`）；当目标内容与既有版本 canonical 相等时，允许以既有 `versionId` 为目标走 **publish** 分支，而不是 rollback。
  2. 语义仍走 `publish` 的 governed 分支：跑 SHACL/一致性/breaking 门禁（相等内容 diff 为空），写 `published` 事件；payload 增 `canonicalEqualTo: <versionId>` 与 `previousVersionId`。
  3. `rollback_to` 保留运维回退语义，但事件 payload 加 `mode: "rollback"`；新入口写 `mode: "activate_existing"`，两者审计可区分。
  4. `diff` 输出增 `canonicalEqual: true` / `equalTo: <versionId>`，CLI 与前端明示“内容与既有版本相同（canonical equal）”。
  5. 可选（依赖迁移）：`ontology_version` 增 `published_by` 列（当前只有 `published_at`），迁移 V18。
- 工作量：接口+分支 ~0.5d；事件/payload/diff 字段 ~0.25d；CLI + smoke 用例（同内容发布、breaking 拦截、幂等、审计链 verify）~0.5d；文档回写（OQ-48 / 04 §5.2）~0.25d；合计 **1.5d**（含迁移），不含迁移 **1.25d**。
- 与 OQ-48 关系：OQ-48 是“两套回滚并存”，本条是“发布入口缺失”；修复本条时可一并统一入口，但不改变 `rollback` 的新建版本语义。
- 状态：**closed（2026-11-06 00:07 已修，commit `87e42f0`）**。落地：`publish --existing` / API `publishExisting=true`；`registry.publish(activate_existing=True)` 仍走 SHACL/一致性/breaking 全门禁，`published_at=now()`，`published` 事件带 `mode=activate_existing`/`publishedBy`/`previousVersionId`，`rolled_back` 事件同样补 `publishedBy`/`previousVersionId`，两者按 `action` 可区分；事务内 advisory lock 二次检查保证并发发布只一次生效。单测 `tests/test_g01_import_publish.py` 9/9（新增同内容、幂等、并发、回滚后再发布 4 条）。
- 残留（本轮新发现，未修）：`ont-f413054a0c72` 的 `sources/….ttl` 存的是 `persist_import` 的**原始 TTL**，而行的 `content_hash` 按 **merged 图**计算；`_load_graph` 重新解析原文件后哈希不一致（expected `87c3fdef…` / actual `6257b89…`），因此对**该历史版本**调用 `publish` 会报 `E_ONTOLOGY_HASH_MISMATCH`（`rollback-to` 走 `_ensure_graph`，不受影响）。新建版本路径不受影响。触发条件=需要重新发布历史 FS-LDM 版本时，先回填该版本的 source 对象或放宽 `_load_graph` 的源文件哈希校验（按 versionId 一次性修复，不做全局放宽）。

### OQ-66（2026-11-05）`.ppt` / `.doc` 与加密 PDF 的解析缺口
- 现状：`parsers.mime_for_filename` 只覆盖 pdf / docx / txt / md / pptx / csv / html；`D:\FS-LDM` 里 **15 个 `.ppt` + 1 个 `.doc`** 无法解析（当前直接不计入“可解析 427 篇”）。加密 PDF 共 **5 篇**：`real-19.pdf`（bench-real）+ `EB6546.pdf`、`Appendices-Book 1.pdf`、`Reference Guide-Book 1.pdf`、`Reference Guide-Book 2.pdf`（FS-LDM），一律 `E_DOC_PDF_ENCRYPTED`，**不重试**。
- 方案 A（推荐）：镜像内加 LibreOffice headless（`soffice --headless --convert-to pdf`），把 `.ppt/.doc` 先转 PDF 再走现有 PDF 解析；转换后再做文本层检查（转出的 PDF 也可能无文本层）。
- 方案 B（纯排除）：继续把这两类标为已知缺口，不引入依赖；代价是 FS-LDM 少 16 篇（其中 15 篇 PPT 属培训/展示材料，对检索价值中低）。
- 工作量：A = 镜像层 +0.5d（体积约 +400MB）、批量转换脚本 +0.25d、回归（含转出后无文本层的分支）+0.25d，合计 **1d**；B = 0d（仅文档化）。
- 加密 PDF：需拿到密码或用 qpdf 离线解密后才可解析；当前**不引入自动破解**，按“不可解析”记账。
- **结论（2026-11-05 20:09）：采用方案 A，已执行。** 镜像 `agent-platform:0.1-s5` 已加 `libreoffice-impress` + `libreoffice-writer`（与 tesseract 同一次重建，总增重 +460MB / 271.3s）；**16/16 文件转换成功、36.6s**，产出 PDF 共 **857 chunk**，已全部入库并嵌入（remaining=0，无 failureCode）。转换脚本 `_impl/data/tmp/convert-office.sh`，逐条回执 `convert.jsonl`（rc/秒/字节/failureCode），驱动器 `_impl/logs/stage_files.py`。加密 PDF 仍 7 篇不可解析、未破解，见 OQ-67 附录。
- 状态：**closed（已执行）**；仅剩加密 PDF 7 篇按“不可解析”记账。

### OQ-67（2026-11-05）扫描件 OCR：现在是 0 chunk，是否补检索能力
- 事实：375 个 PDF 中 **8 篇无文本层**（real-01/04/05/08/13/14/17/21 = 1,220 页 / 217MB），当前 0 chunk；已全部标 `metadata.noTextLayer=true`，import 走 sha 去重不会反复重试。
- 本地 OCR：本环境**未安装** Tesseract / PaddleOCR（`command -v` 均无），因此**本段无法实测单页耗时**，只能给公开基准与安装后验证方法；不得把估算写成实测。
  - 公开基准（300 DPI、CPU）：Tesseract 5（`--psm 3`）约 **1–2 s/页/核**；PaddleOCR（CPU）约 **3–6 s/页/核**。
  - 1,220 页、8 核：Tesseract 约 **3–5 min**，PaddleOCR 约 **8–15 min**；单核则 20–41 min / 61–122 min。
  - 实测方法（装好后）：抽 5 页（大/中/小各覆盖），`tesseract page.png out --psm 3 -l eng+chi_sim` 计时，取中位数代入 1,220 页。
- 云端 OCR：通用文字识别按页计价，常见 **¥0.005–0.02/页**（Azure Read ≈¥0.011/页、Google Vision ≈¥0.011/页），1,220 页合计 **¥6–24**；不含人工抽检。
- 结论：**值得 OCR** 的是 real-01（838 页，唯一“大部头”）、real-08（194 页）；其余 6 篇共 188 页但多为表格/样例，可直接标“不可检索”等业务确认。若 OCR，产物仍走同一 chunk+embedding 流程，预计新增 1.0–1.5k chunk（约 0.5–1h）。
- **结论（2026-11-05 20:09）：采用本地 tesseract，已执行。** 300 DPI、`chi_sim+eng`、4 线程/篇、逐篇串行；实测 **8 篇 / 1,220 页 / 1,434.1s（23.9min，≈51 页/分钟、≈1.18s/页@4线程）**，字符 **1,462,343**，**失败页 0**，产出 **1,465 chunk** 全部嵌入（remaining=0）。
  - 逐篇：real-01 838p/1010.7s/1184 chunk；real-08 194p/108.8s/157；real-21 57p/37.7s/36；real-04 42p/29.9s/17；real-05 40p/73.6s/57；real-17 27p/11.5s/3；real-14 20p/158.7s/10；real-13 2p/3.2s/1。
  - 质量：中文封面/版权页/正文（如 CSCO 证据类别与推荐等级）可检索，`hybrid_search` 已真实命中 real-01；英文人名与符号有噪声，未做校对。云端 OCR（¥6–24）未采用。
- **附录（7 篇，2026-11-05 P0 处置：不解密、不 OCR、不再检测）**：按用户口径标 `skippedReason=content_in_named_md`。已核实的同名 md 对应关系（均已入库）：`Appendices-Book 1.pdf → Teradata FS-LDM 10.00.00 Appendices-Book 1.md`（1,386 chunk）、`Reference Guide-Book 1.pdf → …Reference Guide-Book 1.md`（1,125）、`Reference Guide-Book 2.pdf → …Reference Guide-Book 2.md`（1,263）、`EB6546.pdf → whitepaper.md`（ASCII 的 "The Financial Services Logical Data Model"，2 chunk）。
  - **未找到同名 md 的 3 篇**：`bench-real/real-19.pdf`（10 页、加密）、`corpus-s13/bad/corrupted.pdf`（29 B、结构损坏）、`corpus-s13/bad/encrypted.pdf`（828 B、加密）。这 3 篇在 `platform.document` 中无记录、仓库内也无对应 md，无法按“同名 md 覆盖”入库；保持 `E_DOC_PDF_ENCRYPTED`/解析失败，需用户提供 md 或原件。**与“7 篇都有同名 md”的口径不一致，此处如实记账。**
  - 本轮未执行 `qpdf --decrypt`、未做 OCR、未修改任何 PDF 原件；未安装 qpdf（宿主与容器均无），未尝试爆破/猜测密码。
- 状态：**closed（已执行，非评估）**。

### OQ-68（2026-11-05）音频转写（faster-whisper）：本轮跳过，待下一轮镜像
- 触发：`s14h-ocr-toolchain` 镜像重建已于 18:29 完成（`tesseract 5.5.0` + `chi_sim/eng` + `LibreOffice 25.2.3.2`，镜像 521MB→981MB，+460MB，271.3s）。"把 CPU 版 faster-whisper 一起装进镜像"的要求在重建完成之后才到；按约定**重建已完成则不为它再重建一次**，本轮跳过。
- 下一轮方案：镜像 `pip install faster-whisper`；模型用 `small`（约 500MB），**优先**由 compose 挂载 `data/models/whisper-small`（控制镜像体积），镜像内只留 pip 包与 ctranslate2 依赖。
- 用法（待下一轮在 `RUN.md` 增"音频转写用法"一节）：输入音频 → 输出 `.txt` + `.srt`；`compute_type=int8`、`cpu_threads` 默认 4；转写与 embedding 串行，不与索引抢核。
- 工作量：镜像层 + compose 挂载 + RUN.md ≈ 0.5d；音频回归（各 1 条 wav/mp3）≈ 0.25d。
- 状态：open（本轮不做；下一轮镜像一并处理）。

### OQ-69（2026-11-05）restore-test 清理条件过宽：误清历史版本图缓存 938→22 — 已定位，待补清理工具
- 现象：本轮 bundle 导入验证收尾时，清理脚本按 `urn:platform:graph:tbox:*` / `urn:platform:inferred:ont-*` 且“非 KEEP”模糊条件删图，
  把 Oxigraph 命名图从 **938 张清到 22 张**（含大量历史版本 T-Box 缓存与历史 inferred 物化图）。
- 影响与定性：**源图未丢**。T-Box 源内容仍在 CAS（`ontology_version.source_key`），`export_version` / `rollback` 会经
  `_ensure_graph` 从 CAS **惰性重载**（已抽验 2 个历史上被清空的版本：清理前 0 → 导出后恢复为 3 / 8 三元组，canonical 与
  `content_hash` 一致）；生产当前指针 `ont-f413054a0c72` 未受影响（图 2,676 三元组、canonical `4c48…` 与 bundle MANIFEST 一致）。
  唯一真实成本是**历史 inferred 缓存需按需重跑物化**（未重跑全部历史，避免 CPU 占用）。
- 推荐做法（强约束，写进任何清理脚本/工具）：
  1. **只允许精确 IRI 前缀白名单** `urn:platform:graph:restore:*`（`import-bundle` 专用），前缀匹配后仍要 `startswith` 且拒绝
     `restore-lookalike:*` 这类近似名；
  2. **禁止**按 `tbox:*`、`inferred:*`、`ont-*` 等模糊条件批量 `DROP SILENT GRAPH`；历史版本图属于“可重建缓存”，
     删除需按 versionId 精确列举并先导出/确认 CAS 存在；
  3. 清理前先 `SELECT` 候选集合并打印数量 + IRI 清单，干跑（`--dry-run`）确认；清理后核对删除数 = 候选数；
  4. 回归测试固化：3 张 `restore:` 图 + 2 张历史图 → 只删 3（`tests/test_bundle.py::RestoreCleanupTests`）。
- 已落地：`bundle.select_restore_graphs` / `bundle.cleanup_restore_graphs` 精确前缀白名单实现 + 2 条单测。
- 状态：open（清理工具已收口；历史 inferred 缓存按需重跑，不批量回填）。

