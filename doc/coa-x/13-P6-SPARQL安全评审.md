# P6 裸 SPARQL 安全评审（F72–F74）

- 日期：2026-11-10
- 范围：D 组 F72–F74（裸 SPARQL）。只出结论，不改代码、不改契约、不加页签。
- 工作区：`D:/agentABC/wt/p6-sparql`，分支 `feat/p6-sparql`。
- 底座：本机 Oxigraph 0.5.7（`coa-local-oxigraph`，7878）+ AWS Neptune。
- 结论口径：每条先给结论，再给依据。查不实的标「未核实」。

## 0. 结论摘要

| # | 项 | 结论 | 判定 |
|---|---|---|---|
| 1 | 超时 | 客户端 10s 硬超时 + 行数上限可做；Oxigraph 没有可依赖的服务端硬中断 | 有条件可做 |
| 2 | 结果规模 | 5000 行 + 4 MB 响应上限可做；不做上限会打爆网关（实测 6s 可拉 747 MB） | 可做 |
| 3 | 图范围 | 解析层注入 `FROM` / `FROM NAMED` 白名单可做；不能靠字符串过滤 | 可做 |
| 4 | 语句白名单 | 只放 `SELECT` / `ASK`；整段解析，多语句自然 400；`;` 不能靠切分 | 可做 |
| 5 | 注入与权限 | Neptune 可上只读 IAM；Oxigraph 无认证、无可用只读账号；本地 `/update` 原对 `0.0.0.0` 暴露，**已收口到 `127.0.0.1`** | 部分做不了 |
| 6 | 审计 | 结构化日志记哈希/行数/耗时，不落原文，可做 | 可做 |
| 7 | 配额 | 单进程信号量 + 每命名空间令牌桶可做；跨实例严格全局配额做不了 | 本地可做 |
| 8 | 风险取舍 | 见 §8，含 8 条残余风险与代价 | — |

## 1. 超时

### 1.1 结论

- 硬上限：**10 秒**（客户端）。`SELECT` 10s 未返回 → 504 `E_SPARQL_TIMEOUT`。
- 行数上限：**5000 行**。与超时分开，不能互相替代。
- Oxigraph：**没有可依赖的服务端硬中断**。`--timeout-s` 参数存在，但 0.5.7 实测不中断计算。
- Neptune：用每查询 `queryTimeout` 提示，建议 10000 ms；实际取「提示 / 集群参数 / 引擎」三者最小值。

### 1.2 依据

代码与实测：

- `oxigraph serve --help` 有 `--timeout-s <TIMEOUT_S>`，帮助原文：
  `Timeout for request processing in seconds. Currently only used for SPARQL queries. Might be used to set up things like HTTP query timeout`。
- 本机 `coa-local-oxigraph` 启动参数**没有** `--timeout-s`（`docker inspect` 确认），所以当前实例没有任何服务端超时。
- 一次性容器 `p6-oxi-test` 加 `--timeout-s 1` 后实测：
  - `SELECT (COUNT(*) AS ?n) WHERE { VALUES ?a {1..10000} VALUES ?b {1..10000} }`：**5.5 s 返回 200**，未超时。
  - 同样 1 亿组合的流式 `SELECT *`：6 s 内下载 **747 MB**，客户端主动断开，服务端未中断；断开后日志为 broken pipe。
- 结论：`--timeout-s` 只能当「尽力而为」，不能当安全边界。0.5.7 的内部实现未核实，但行为已实测。

Neptune 依据（AWS 文档）：

- `neptune_query_timeout` 是集群参数，单位毫秒，范围 10–2,147,483,647，默认 **120,000 ms**，静态参数（改后需重启）。
- 查询内 `queryTimeout` 提示可按查询覆盖；文档明确「提示、集群参数、引擎限制三者取最低」。
- 现有 `SPARQLFirewall` 已经会注入该提示（`firewall.py` §F6），复用它即可。

### 1.3 实现要求

1. 网关 → 后端 HTTP 客户端超时 10s（现有 `OxigraphGraphClient` / Neptune 客户端默认就是 10.0s）。
2. Neptune 请求注入 `queryTimeout = 10000`；`TimeLimitExceededException` 映射 504。
3. Oxigraph **不要注入 Neptune 提示**。该提示是一个真实三元组模式，Oxigraph 会当成必须匹配的模式，导致所有查询返回空。见 §3.5。
4. Oxigraph 可选加 `--timeout-s 10`，只作为尽力而为；不得在验收里把它当硬保证。
5. 客户端断开后，服务端可能继续算。用并发上限（§7）限制影响面。

### 1.4 做不了的部分

- **Oxigraph 上「到点必杀」做不到**。没有 kill 接口，`--timeout-s` 实测无效；客户端超时只是不再等，服务端 CPU 仍可能被占用。
- 验收时必须把这条写成「残余风险」，不能写成「已解决」。

## 2. 结果规模

### 2.1 结论

- 行数上限：**5000**。结果超过 5000 行时，返回前 5000 行并显式标记 `truncated=true`，同时给 `rowCount`（实际扫描/预取到的行数，最多 5001）。
- 响应字节上限：**4 MB**。超过直接 413 `E_SPARQL_RESULT_TOO_LARGE`，不做静默截断。
- 网关不能依赖后端自觉。Oxigraph 没有结果行数上限；`coa-gateway` 的 `OxigraphGraphClient` 也没有截断逻辑。

### 2.2 依据

- 实测：5000 行 `SELECT ?s ?p ?o` 的 JSON 约 **1.1 MB / 49 ms**。5000 行是安全值。
- 实测：1 亿行 `SELECT *` 在 6 s 内输出 **747 MB**，没有上限。直连网关会把进程内存打爆。
- 平台限制：Lambda 同步响应 6 MB；API Gateway 集成超时 29 s（AWS 文档）。4 MB 给 6 MB 留余量。
- 现有 `query_postgres.py` 已有「取 `max_rows + 1`，多一行则 `truncated=true`」的先例，照抄口径。
- 现有 `oxigraph.py` 适配器虽然有 `max_rows`，但它是「取全量后切」，对 747 MB 这种响应没有保护作用；不能作为网关级防线。

### 2.3 实现要求

1. 解析后给 `SELECT` 注入顶层 `LIMIT 5001`（已有 `LIMIT` 且更小则保留更小值）。`ASK` 不注入。
2. 读取响应时流式累计字节；超过 4 MB 立即停止读取并返回 413。不要尝试解析半截 JSON。
3. 返回体固定带：`rowCount`、`returnedRows`、`truncated`、`elapsedMs`。
4. UI 看到 `truncated=true` 必须显示「结果已截断，只显示前 5000 行」，不能静默。
5. `ASK` 只返回布尔，不受行数上限影响，但仍受 10s 超时和字节上限约束。

### 2.4 代价与边界

- 长字面量可以突破 4 MB：5000 行 × 1 MB 字面量 = 5 GB。字节上限会先触发，返回 413；这是显式失败，不是截断。
- `COUNT(*)`、`GROUP BY`、属性路径这类「先算完再出行」的查询，行数上限帮不上；只能靠 10s 客户端超时和并发上限。见 §8 R2。

## 3. 图范围

### 3.1 结论

- 当前是**一个 Oxigraph 实例装多个命名空间**，不是「一命名空间一实例」。所以隔离必须做在图级，不能靠端点隔离。
- 强制方式：**解析后注入数据集子句**，把默认图和命名图都限定到白名单；用户自己写的 `FROM` / `FROM NAMED` 一律拒绝。
- `SERVICE` 一律拒绝；`LOAD` 是更新语句，解析层自然拒绝。
- `GRAPH <iri>` 只允许白名单内 IRI；`GRAPH ?g` 可放行，但必须靠注入的 `FROM NAMED` 把变量范围锁死在白名单。

### 3.2 依据

实测（本机 7878）：

- 默认图是空的：`SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }` 返回 **0**。不注入数据集，用户写 `SELECT * WHERE {?s ?p ?o}` 会得到 0 行，这是功能问题，不只是安全问题。
- 多 `FROM` 可执行：`FROM <g> FROM <g>` 的计数是单图的 **2 倍**（121,130 → 242,260），说明是并集且**不去重**。注入前必须对图列表去重。
- `FROM NAMED <g>` + `GRAPH ?g` 实测只返回该图，说明 `FROM NAMED` 能锁住 `GRAPH ?g` 的范围。
- 数据图命名实测有两套：
  - 当前平台：`https://coa.local/graph/<namespaceId>/...`
  - 旧链路：`https://ontology-workbench.local/<namespaceId>/...`
- 同一实例内还有三类平台图，IRI 不带 namespace：
  - T-Box：`urn:platform:graph:tbox:ont-<id>`
  - 推理：`urn:platform:inferred:ont-<id>`
  - 导入：`urn:platform:graph:import:imp-<id>`
- 同一实例实测同时存在两个命名空间（`ed70a15c-...` 与 `a38f978c-...`）的图，跨命名空间隔离必须显式做。
- 图枚举 `SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }` 实测 **186–253 ms**（3 次），可以 60s 缓存。

### 3.3 白名单怎么来

v1 建议：

- 只放**命名空间自己的数据图**：IRI 前缀匹配 `https://coa.local/graph/<namespaceId>/`，以及实例里存在的旧前缀 `https://ontology-workbench.local/<namespaceId>/`。
- **排除 T-Box、推理图、导入图**（`urn:platform:graph:tbox:*`、`urn:platform:inferred:*`、`urn:platform:graph:import:*`）。理由：它们按 ontology/import id 命名，需要 namespace→ontology/import 映射；v1 不做映射，避免跨命名空间误放。代价是用户查不到 T-Box、推理和导入三元组；schema 走已有接口，导入数据在 v1 裸查里不可见。
- 白名单来源：内部执行一次 `SELECT DISTINCT ?g`，按前缀过滤；缓存 60s。不要相信客户端传图名。
- 图数量上限：**200**。超过则 503 `E_SPARQL_SCOPE_TOO_LARGE`，不生成超长查询。这是显式失败。

### 3.4 解析层怎么挡（不能字符串过滤）

复用 `packages/context-manager/src/coa_serve/tier2/sparql/firewall.py` 的 `SPARQLFirewall`，但要做三处扩展：

1. **单图改图集合**：现有 `check(named_graph=...)` 只支持一个图；改成 `named_graphs: frozenset[str]`，`GRAPH` 的 term 必须在集合内；`GRAPH ?g` 额外放行（因为数据集已注入）。
2. **数据集注入**：现有 `_scope_to_graph` 注入 `FROM <g> FROM NAMED <g>`；改成对去重后的每个图各注入一次 `FROM` 和 `FROM NAMED`。
3. **拒绝用户数据集子句**：现有 `_check_patterns` 已拒绝 `datasetClause`（`FROM / FROM NAMED is not allowed`），保留。

现有防火墙已经做的事（可直接复用）：

- 先 `parseQuery` 整段解析；再用 mask + 解析树 + algebra 三路交叉校验。
- 拒绝 `SERVICE`（algebra 的 `ServiceGraphPattern` + 文本 `SERVICE` 双查）。
- 拒绝 `\u` / `\U` 码点转义、相对 IRI、重复前缀标签。
- 拒绝 `GRAPH` 指向非白名单图。
- 注入顶层 `LIMIT`。
- 对「要执行的最终文本」再跑一遍全部规则（F4），防止重写引入漏洞。

### 3.5 必须注意的坑

- **Neptune 超时提示不能给 Oxigraph**：`_with_timeout` 往 WHERE 里插入的是真实三元组模式。Oxigraph 会把它当必须匹配的模式，结果是 0 行。按后端分流：Neptune 注入，Oxigraph 不注入。
- **图列表必须去重**：重复 `FROM` 会让计数翻倍。
- **多图默认图是并集**：同一条三元组出现在两个图里会重复计数，这是 SPARQL bag 语义，不是 bug；文档里要写明。

### 3.6 代价

- T-Box/推理图 v1 不可查。
- 图数量 > 200 的命名空间直接拒绝。
- `GRAPH ?g` 放行依赖「注入的 `FROM NAMED` 一定正确」；所以必须在执行前对最终文本做一次校验（防火墙 F4 已具备）。

## 4. 语句白名单

### 4.1 结论

- 只放 `SELECT` / `ASK`。`CONSTRUCT` / `DESCRIBE` / 任何 `INSERT` / `DELETE` / `LOAD` / `CLEAR` / `DROP` 一律 400。
- 多语句（`;` 拼接）用**整段解析**拦，不切分、不正则过滤。
- 注释和字符串里的 `;` 不误判；属性路径里的 `;` 也正常。

### 4.2 依据

实测（Oxigraph 0.5.7）：

| 输入 | 结果 |
|---|---|
| `SELECT * WHERE { ?s ?p ?o } LIMIT 1; DROP ALL` | 400，响应体 `error at 1:42: expected one of OFFSET, VALUES` |
| `SELECT * WHERE { ?s ?p ?o } LIMIT 1;`（仅尾部 `;`） | 400（Oxigraph 严格） |
| 字面量里含 `;` | 200 |
| 注释里含 `;` | 200 |
| `CONSTRUCT ...` + `Accept: text/turtle` | 200（Oxigraph **接受** CONSTRUCT） |
| `DESCRIBE <...>` | 可用（同上，形式被接受） |

结论：Oxigraph 自己会接受 `CONSTRUCT` / `DESCRIBE`，所以必须在我们的解析层拒绝，不能指望后端。

### 4.3 实现要求

- `rdflib.parseQuery` 后判断 `algebra.name` 必须是 `SelectQuery` 或 `AskQuery`。
- 不做 `split(";")`。`;` 在 SPARQL 里是合法的谓词-宾语分隔符，切分会破坏合法查询，而且挡不住变体。
- 尾部单个 `;`：建议统一 `rstrip(";")` 后再执行（现有防火墙已这么做），避免 Oxigraph 400；这是宽容，不是漏洞。
- 解析失败统一 400 `E_SPARQL_SYNTAX`，把后端/解析器消息截断 500 字符后返回（见 §6 的脱敏）。

## 5. 注入与权限

### 5.1 只读凭证

**Oxigraph：没有可用的只读账号。**

- Oxigraph 0.5.7 没有认证/授权配置；`--help` 里没有用户名、密码、token 参数。
- `serve-read-only` 子命令存在，帮助原文：只允许读；但明确警告「另一个进程正在写时以只读打开是未定义行为」。本机 ETL 会持续写，所以**不能**对同一数据目录同时跑读写实例 + 只读实例。

**原缺陷（已修复）：本地 `/update` 曾对整个网络开放。**

- 现象：`coa-local-oxigraph` 曾以 `--publish 7878:7878` 启动，等价 `HostIp=""`，Docker 把它发布到 `0.0.0.0` 和 `[::]`。同网段任何主机不需要认证就能 `POST /update` 改图删图。这是**先于 P6 的 P0 缺陷**，不是 P6 引入的。
- 影响面确认：8101（ontology）、8099（api 桥）都通过 `http://127.0.0.1:7878` 访问（`10-本地起栈.ps1` 第 207/311 行）；5173 经 8099/8101 间接访问；没有服务走容器网络名。所以可以直接绑回环，不会断链路。
- 修复：`doc/coa-x/10-本地起栈.ps1` 的 Oxigraph 发布参数改为 `127.0.0.1:7878:7878`，并用同名、同镜像、同数据卷重建容器生效。8080/8082 未改。

**证据（2026-11-10 实测）**

| 项 | 修复前 | 修复后 |
|---|---|---|
| `docker port` | `0.0.0.0:7878`, `[::]:7878` | `127.0.0.1:7878` |
| `HostConfig.PortBindings.HostIp` | `""`（全接口） | `"127.0.0.1"` |
| 宿主机 7878 监听 | `127.0.0.1`、`::1`、`::` | 仅 `127.0.0.1` |
| 非回环 `POST /update`（`192.168.1.14:7878`） | **204**（可达） | `curl: (7) Failed to connect to 192.168.1.14 port 7878 ... Could not connect to server` |
| 非回环 `GET /query`（同上地址） | 200 | 同上，连接被拒 |

回环仍正常：`127.0.0.1:7878/query` → 200，`/update` → 204。数据卷未动，总量 253,810 条不变。

**三条链路复验（同一时点）**

| 链路 | 请求 | 结果 |
|---|---|---|
| 8101 本体服务读 | `GET /graph/statements?namespace=ed70a15c-…&limit=2` | 200，返回真实三元组 |
| 8101 本体服务读 | `GET /graph/schema?namespace=ed70a15c-…` | 200，61,815 B |
| 8099 api 桥 | `GET /system-health` 的 `oxigraph` 组件 | `status=ok` |
| 8099 api 桥 | `GET /namespaces` | 200 |
| 5173 页面 | 浏览器实测首页 + `/namespaces` | 表格加载 4 行，无认证/500 错误 |
| 写通道（回环） | `INSERT DATA` → 回读 → `DROP GRAPH` | 204 / 读到 42 / 204，总量回到 253,810，无残留 |

**边界：这是缓解，不是根治。**

1. 只收口了网络可达面。**宿主机本机的任何进程仍可直连 `127.0.0.1:7878` 写图删图**——Oxigraph 本身没有认证。
2. 只覆盖本机开发栈。生产或其它宿主要单独保证：安全组/网络策略不放行 7878，容器不发布该端口。本改动不替代生产侧网络隔离。
3. 运行中的栈来自主仓 `D:/agentABC/coa` 的脚本。本次改的是工作区 `D:/agentABC/wt/p6-sparql` 的副本；主仓脚本**未同步**，下次用主仓脚本起栈会退回 `7878:7878`。同步后才能持久。
4. Oxigraph 的只读保证仍是三件事叠加：网络收口（本次已做）、应用层只发 `/query`（P6 待做）、解析层白名单（§3、§4 待做）。
5. 残余风险无法消除：能访问 7878 的进程仍然可以写。验收报告必须如实写。

**Neptune：可做真正的只读凭证。**

- IAM 只给 `neptune-db:connect` + `neptune-db:ReadDataViaQuery`；不给 `WriteDataViaQuery` / `DeleteDataViaQuery`。
- 查询服务用独立角色，不复用写入角色。
- 现有 `graph_neptune.py` 已实现 SigV4，签名 service 为 `neptune-db`；只需换凭证来源。

### 5.2 Cedar action

**推荐：新增 `runSparql`，资源类型 `Namespace`。**

理由：

- 裸 SPARQL 能读该命名空间全部数据图，还能用重查询拖垮存储；风险高于普通 `query`。
- 现有 `query` 被 `platform-viewer` 全局持有；如果复用，等于给所有只读用户开放裸查询和 DoS 面。
- 新 action 可以单独授予、单独收回，不影响普通查询。

代价：

- 改 `libs/common/src/coa_authorization/cedar-schema.json` 增加一个 action。
- 改 seed 策略：`namespace_owner.cedar`、`data_steward.cedar`，可选 `data_analyst.cedar`；**不要**给 `global_viewer.cedar`。
- 改权限矩阵文档（`11-复盘与规划.md` §2）和前端角色说明。
- 在 `packages/control-plane/src/coa_control_plane/authorization/handler.py` 的 `_PATH_MAPPING` 增加一条：
  `"/namespaces/{namespaceId}/sparql": {"POST": ("runSparql", "Namespace")}`。
- 未登记的路由按现有规则**直接 Deny**，所以这条映射是必须的，不是可选。

备选（不改 schema）：复用 `("/namespaces/{namespaceId}/query", "query", "Namespace")`。代价是上面说的权限扩大；如果产品确认「能普通查询的人就应该能裸查」，可以选这条，但要写进评审记录。

本地注意：8099 网关源码里没有看到 Cedar 调用；Cedar 生效点在 control-plane 授权 handler。本地验收能验路由和防火墙，不能验 Cedar 拒绝路径。**本地是否另有前置鉴权：未核实。**

### 5.3 注入面

- SPARQL 没有参数绑定。真正的注入面是我们自己拼接数据集子句，不是用户语句本身。
- 图 IRI 只能来自服务端白名单；`FROM` 注入前必须校验 IRI 是绝对 IRI、无空白/尖括号，且在白名单集合内。
- 用户语句永远不拼进内部管理查询；内部图枚举查询是常量语句。
- 拒绝 `SERVICE` 是防 SSRF 的关键：实测 `SERVICE <http://127.0.0.1:7878/query> {...}` 能成功发起请求并拿回结果。也就是说，只要放行 `SERVICE`，查询就能打内网。
- 纵深防御：给 Oxigraph 容器加出网限制（只允许必要出口），不要只靠解析层。容器网络改动不在 P6 范围内，列为后续项。

## 6. 审计

### 6.1 结论

记录「谁、在哪个命名空间、跑了什么形态、多久、多少行、是否截断、结果码」；**不记查询原文、不记结果值**。

### 6.2 字段

| 字段 | 示例 | 说明 |
|---|---|---|
| `event` | `sparql.run` | 固定 |
| `ts` | ISO8601 | 服务端时间 |
| `request_id` | `...` | 网关请求 ID |
| `caller_id` | `...` | 认证主体 |
| `namespace_id` | UUID | 资源 |
| `backend` | `oxigraph` / `neptune` | 后端 |
| `form` | `SELECT` / `ASK` | 语句形态 |
| `query_hash` | 32 位 hex | HMAC-SHA256(secret, namespace + "\n" + 原文)，截断 |
| `graph_count` | 12 | 白名单图数量 |
| `row_count` | 5001 | 预取行数 |
| `returned_rows` | 5000 | 实际返回 |
| `truncated` | true / false | 是否截断 |
| `duration_ms` | 123 | 总耗时 |
| `response_bytes` | 1048576 | 响应体字节数 |
| `outcome` | `ok` / `rejected` / `timeout` / `error` | 结果 |
| `rule` | `F1`…`F7` 或 `null` | 防火墙规则 |
| `error_code` | `E_SPARQL_SYNTAX` | 错误码 |

不记录：

- `sparql` 原文。
- 任何 bindings / 字面量 / 图内容。
- provider 的完整错误消息（可能含 URL 或查询片段）；只记 `error_code` 和 `rule`。

### 6.3 依据与取舍

- 代码库里没有 `audit_events` / `audit_log` 表；P6 说存储不改，所以 v1 只写结构化日志，不建表。
- 用 HMAC 而不是裸 SHA256：短查询（如 `ASK {}`）裸哈希可被离线猜出；HMAC 需要进程密钥。代价是换密钥后旧哈希不可比，只用于同一密钥周期内的关联。
- 不落原文的代价：事后无法复现用户到底跑了什么，只能让用户重跑。这是隐私与可运维性的取舍，建议接受，并写进用户文档。

## 7. 配额

### 7.1 结论

- 每命名空间：**30 次/分钟，突发 5**（建议值，可调）。
- 每实例并发：**2**；全实例总并发：**2**（本地单进程）。
- 获取许可最多等 1s；等不到 → 429，带 `Retry-After`。
- 超限统一 429 `E_SPARQL_QUOTA_EXCEEDED`。

### 7.2 实现

- 进程内 `asyncio.Semaphore(2)` 控并发；`asyncio.wait_for(acquire, 1.0)` 超时 → 429。
- 每命名空间滑动窗口计数（60s），内存字典；进程重启清零。
- 参数放环境变量，便于验收时调小（例如 2 次/分钟）验证 429。
- 响应头：`Retry-After: <秒>`；响应体给 `retryAfterSeconds`。

### 7.3 做不了的部分

- 多副本 / 多 Lambda 实例下，进程内计数是**每实例**的，不是全局配额。要全局严格配额，需要 API Gateway 使用计划、WAF 速率规则或共享计数器（DynamoDB/Redis）；这些是基础设施改动，不在 P6。
- 结论写「本地单进程有效；AWS 侧依赖 API Gateway 限流，P6 不新建共享计数器」。

## 8. 已知风险与取舍

| # | 风险 | 推荐处置 | 代价 | 状态 |
|---|---|---|---|---|
| R1 | 本地 Oxigraph `/update` 曾对 `0.0.0.0:7878` 暴露 | 端口改为 `127.0.0.1:7878` | 需重启容器；主仓脚本待同步 | **已修复**（证据见 §5.1）；宿主机本机进程仍可写，属缓解 |
| R2 | Oxigraph 无法硬杀长查询 | 并发 2 + 10s 客户端超时 + 可选 CPU 限额 | 慢查询会占住一个并发位；极端情况仍可拖慢实例 | 接受，写残余风险 |
| R3 | Oxigraph 只读模式与在线写入互斥 | 应用层只发 `/query` + 网络收口；未来做只读副本 | 无法给出「数据库层只读」的强保证 | 接受 |
| R4 | T-Box/推理/导入图 v1 不可查 | 先只放数据图；需要时再做 namespace→ontology/import 映射 | 功能缺口，用户可能问「为什么查不到推理或导入结果」 | 产品决策 |
| R5 | 图数量 > 200 的命名空间被拒 | 显式 503，不生成超长查询 | 大命名空间不可用裸 SPARQL | 接受 |
| R6 | 跨实例全局配额做不到 | 本地进程内；AWS 用 API Gateway 限流 | 多实例下实际额度会放大 | 接受 |
| R7 | provider 错误消息可能带内部 URL/片段 | 只回传截断 500 字符的消息；日志只记 code | F74「原样展示」会打折扣 | 接受 |
| R8 | 旧 `platform-core` 的 `/browse/sparql` 只有正则前置检查 | 不改造，明确不复用；如仍可达，单独立项收口 | 存在并行入口，审计会漏 | 记录，不在 P6 |

补充：

- `platform-core/src/platform_core/api.py` 的 `/browse/sparql` 是 GET + 正则 `^(prefix|base)* (select|ask)` + 5000 字符上限，随后依赖适配器的字符串检查（`SERVICE`、`FROM/FROM NAMED <iri>`、`GRAPH <iri>`）。它**不是解析层**：`GRAPH ?g`、注释/转义等变体没有解析级保证；适配器默认 `allowed_graph_prefixes=("urn:platform:",)`，对本机 `https://coa.local/...` 数据图也不适用。**不能**作为 F72–F74 的实现基础。
- 现有 `SPARQLFirewall` 的 F2 假设「一个 source 一个图 / 一个端点」。COA 是「一个实例多命名空间」，这个假设不成立，必须按 §3.4 扩展后再复用。

## 9. 推荐实现顺序（只列顺序，不含代码）

1. **收口 R1（已完成）**：7878 已只绑回环，`/update` 不再对局域网开放；见 §5.1 的前后对比与复验。
2. **抽公共防火墙**：把 `SPARQLFirewall` 移到可复用库（或复制到 data-layer），扩展 `named_graphs` 集合、`SELECT/ASK` 白名单、按后端注入超时提示。
3. **契约**：在 data-layer（Serve）加 `RunSparql`，路径建议 `POST /namespaces/{namespaceId}/sparql`；先走 Smithy 生成链路，不手写路由。
4. **后端执行**：复用 `OxigraphGraphClient` / Neptune 客户端；加 5000 行、4 MB、10s、图白名单缓存。
5. **网关鉴权**：Cedar `runSparql`（或 `query`）+ `_PATH_MAPPING` 登记；未登记必须 Deny。
6. **审计与配额**：结构化日志 + 进程内限流。
7. **UI**：页签只做「输入框 + 运行 + 结果表 + 截断提示 + 错误码」；不展示原文日志。

## 10. 验收清单（实现后逐条跑）

> 目的：每条都能证伪。没有证据的项不能记「已落位」。

| # | 用例 | 期望 |
|---|---|---|
| A1 | `SELECT * WHERE { ?s ?p ?o } LIMIT 1` | 只返回本命名空间数据；不返回 0 行（证明数据集注入生效） |
| A2 | `SELECT * FROM <别的命名空间图> WHERE { ?s ?p ?o }` | 400 `E_SPARQL_DATASET_FORBIDDEN` |
| A3 | `SELECT * WHERE { GRAPH <别的命名空间图> { ?s ?p ?o } }` | 400 `E_SPARQL_GRAPH_FORBIDDEN` |
| A4 | `SELECT * WHERE { GRAPH ?g { ?s ?p ?o } } LIMIT 5` | 只出现白名单图名 |
| A5 | `SELECT * WHERE { SERVICE <http://127.0.0.1:7878/query> { ?s ?p ?o } }` | 400 `E_SPARQL_FEDERATED`；Oxigraph 日志无外呼 |
| A6 | `SELECT * WHERE { ?s ?p ?o } LIMIT 1; DROP ALL` | 400 `E_SPARQL_SYNTAX` |
| A7 | 字面量/注释里含 `;` 的查询 | 200 |
| A8 | `CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }` | 400 `E_SPARQL_STATEMENT_NOT_ALLOWED` |
| A9 | `DESCRIBE <...>` | 400，同上 |
| A10 | `LOAD <...>` | 400 |
| A11 | 超过 6000 字节的查询 | 400 `E_SPARQL_TOO_LONG` |
| A12 | 返回 6000 行的 `SELECT` | 200，`returnedRows=5000`，`truncated=true` |
| A13 | 构造 5 MB 结果的查询 | 413 `E_SPARQL_RESULT_TOO_LARGE` |
| A14 | 6 个并发请求 | 最多 2 个执行，其余 1s 内 429 + `Retry-After` |
| A15 | 跑一次成功查询后查日志 | 有 `query_hash`、行数、耗时；**没有**查询原文和结果值 |
| A16 | Neptune 查询超时（注入 `queryTimeout=1000` + 重查询） | 504 `E_SPARQL_TIMEOUT` |
| A17 | 未授权的调用者 | 403（Cedar Deny）；不能进防火墙 |
| A18 | `GRAPH ?g` + 注入 `FROM NAMED` 的计数 | 与逐图 `COUNT` 之和不矛盾（注意 union 重复） |

## 11. 未核实清单

| # | 项 | 原因 |
|---|---|---|
| U1 | Oxigraph `--timeout-s` 的内部语义 | 只做了黑盒实测（未中断）；源码未取到 |
| U2 | `serve-read-only` 是否真的拒绝 `/update` | 本机数据目录被写入进程占用，不能安全重启验证 |
| U3 | Neptune 8 KB 查询上限的具体作用范围 | 依据仓库注释 `neptune_db_graph.py:266`，未在 AWS 上实测 |
| U4 | AWS IAM 只读策略的实际拒绝效果 | 依据 AWS 文档，未在真实 Neptune 上跑 |
| U5 | 本地 8099 是否经过 Cedar 授权 handler | 网关源码未见 Cedar 调用；需实现时确认 |
| U6 | 旧前缀 `https://ontology-workbench.local/<namespace>/` 在新命名空间是否仍会产生 | 只在现有数据里看到；需按实例确认 |
| U7 | Oxigraph 对其它内网端口的 `SERVICE` 可达性 | 只实测了 7878 和 9；按「可达」处理，不做逐端口探测 |

## 附录 A：关键证据

环境：2026-11-10，Windows，Docker；Oxigraph 0.5.7；本机 `coa-local-oxigraph`。

1. 版本与模式
   - `docker exec coa-local-oxigraph oxigraph --version` → `Oxigraph 0.5.7`
   - `oxigraph --help` → 存在 `serve-read-only`；帮助警告「另一个进程在写时只读打开是未定义行为」
   - `oxigraph serve --help` → 存在 `--timeout-s`，原文见 §1.2

2. 端口与更新
   - 修复前：`docker port coa-local-oxigraph` → `0.0.0.0:7878` + `[::]:7878`；`HostIp=""`
   - 修复前：从 `http://192.168.1.14:7878/update` 发注释体更新 → 204（非回环可达）
   - 修复后：`docker port` → `127.0.0.1:7878`；`HostIp="127.0.0.1"`；宿主机仅 `127.0.0.1` 监听
   - 修复后：同一非回环地址 → `curl: (7) Failed to connect ... Could not connect to server`
   - 修复后：`127.0.0.1:7878/query` → 200；`/update` → 204
   - 修复后链路：8101 `/graph/statements`、`/graph/schema` 200；8099 `/system-health` 中 oxigraph `ok`；5173 `/namespaces` 表格 4 行
   - 修复后数据量：253,810 条，与修复前一致

3. 图与数据集
   - 默认图 `COUNT(*)` → 0
   - 同一图注入两次 `FROM` → 121,130 → 242,260
   - `FROM NAMED <g>` + `GRAPH ?g` → 只返回 `<g>`
   - `SELECT DISTINCT ?g` → 186–253 ms

4. 多语句与形式
   - `... LIMIT 1; DROP ALL` → 400，`error at 1:42: expected one of OFFSET, VALUES`
   - 尾部 `;` → 400
   - 字面量/注释含 `;` → 200
   - `CONSTRUCT` + `Accept: text/turtle` → 200
   - `DESCRIBE <...>` + `Accept: text/turtle` → 200（形式被接受）
   - `LOAD <...>` → 400（`/query` 不接受更新）

5. 超时与规模
   - `--timeout-s 1` + 1 亿组合 `COUNT` → 5.5 s，200
   - `--timeout-s 1` + 1 亿行流式 `SELECT` → 6 s / 747 MB，客户端断开，服务端未中断
   - 5000 行 JSON → 约 1.1 MB / 49 ms

6. 外部服务
   - `SERVICE <http://127.0.0.1:7878/query>` → 200，返回 1 行
   - `SERVICE <http://127.0.0.1:9/...>` → 报端口不允许，说明确实发起外呼

## 附录 B：代码索引

| 文件 | 用途 |
|---|---|
| `packages/context-manager/src/coa_serve/tier2/sparql/firewall.py` | 现成解析层防火墙（F1–F7），需按 §3.4 扩展 |
| `packages/coa-gateway/src/coa_gateway/graph_oxigraph.py` | Oxigraph 只读客户端，`/query`，10s |
| `packages/coa-gateway/src/coa_gateway/graph_neptune.py` | Neptune SigV4 客户端，`/sparql`，表单编码 |
| `packages/coa-gateway/src/coa_gateway/query_postgres.py` | `max_rows + 1` 截断先例 |
| `packages/control-plane/src/coa_control_plane/authorization/handler.py` | `_PATH_MAPPING` 与 Cedar 路由映射 |
| `libs/common/src/coa_authorization/cedar-schema.json` | Cedar action 定义 |
| `libs/common/src/coa_authorization/seed/*.cedar` | 角色策略（`global_viewer` 持有全局 `query`） |
| `packages/platform-core/src/platform_core/api.py` | 旧 `/browse/sparql`（正则前置检查，不作基础） |
| `packages/ontology-engine/src/coa_ontology/stores/neptune_db_graph.py:266` | Neptune 8 KB 查询上限注释 |
| `libs/common/src/coa_common/constants.py:335` | `MAX_QUERY_CODEPOINTS = 4000`（NL 查询口径） |
