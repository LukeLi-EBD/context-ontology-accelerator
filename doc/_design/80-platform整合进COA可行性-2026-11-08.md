# platform/ 整合进 COA 可行性评估

> 方向：COA 当主干，`platform/` 降格为 COA 的一个或一组成员包。
> 口径沿用 79 号文档的 A/B/C 三分，不重新统计：
> **A 可回灌 8,659 行 / B 重叠应废弃 16,404 行 / C 净新增 14,102 行**（另有验收脚手架 4,810 行、web 6,255 行）。
> 本文只做只读核实，不改代码、不启动长期服务、不碰 8080。

---

## 0. 结论（先看）

| 问题 | 结论 |
| --- | --- |
| 能否作为 COA uv workspace 成员 | **今天不能直接加成员**。根 workspace 的 `smithy-generated/control-plane-python-server`、`data-layer-python-server` 缺失，`uv lock/sync` 在解析阶段必败；加 `platform` 成员不会修复它。生成 smithy 或改根 members 都不是零改动 |
| 依赖冲突 | **只有一处硬冲突：`pydantic`**（COA `>=2.13.4` vs platform `==2.10.4`）。`fastapi`/`uvicorn`/`httpx`/`rdflib`/`PyYAML` 兼容；`psycopg`、`pyshacl`、`markitdown` 等是纯增量 |
| 推荐运行形态 | **中粒度 + 进程内 provider**：A 抽成 `packages/local-providers`，被 COA 的 `GraphClient`/`VectorClient`/`LLMClient`/`MetadataStoreClient` 直接 import；platform 长驻 HTTP 不再是主干；PG/Oxigraph 作为外部基础设施；不模拟 Lambda/AgentCore |
| 「在 COA 上二开」能否成立 | **分层成立**：代码归属层成立；运行主干层只在 COA 业务包作为主路径时成立；COA 原生 handler/Lambda 层 **不成立**。只把 platform 放进目录、继续由 platform API 服务，则只是目录结构层成立 |
| 首切片 | `packages/local-providers` 的 JSON catalog lookup + `coa_metrics` OSI 校验，独立 venv 运行，绕开 `uv sync` 与 AWS |

---

## 1. 工程可行性

### 1.1 作为 workspace 成员的技术形态

`platform/pyproject.toml` 已存在：setuptools 后端、包名 `platform-core`、`requires-python >=3.12`、src layout、含 SQL package data。从 PEP 517 角度，它可以作为一个 uv workspace 成员。

但根 `pyproject.toml` 的 `members` 里有：

- `smithy-generated/control-plane-python-server`
- `smithy-generated/data-layer-python-server`

这两个目录缺失且被 gitignore。`uv lock` / `uv sync` 在 workspace 解析阶段就会失败，不会等到安装阶段。**加 `platform` 成员不改变这个事实**。

要把 workspace 变成可用，只有三条路：

| 做法 | 是否零改动 | 后果 |
| --- | --- | --- |
| `make generate` 生成 smithy（JDK21 + Gradle + Maven Central 网络） | 是（不修改源码，但引入生成物） | 前置成本；成功后 workspace 可解析 |
| 从根 `members` 移除两个缺失成员 | **否**，修改上游元数据 | 依赖 generated models 的包可能 import 失败 |
| 保持 platform 在 workspace 外，用独立 venv / path dependency | 是 | 可以运行，但不是“workspace 成员被管理” |

另外，仓库根目录名 `platform/` 与 Python 标准库 `platform` 同名。当前没有 `__init__.py`，PEP 420 下通常会继续找到标准库模块，但这是长期风险；若整合，建议移到 `packages/platform-core/`，不要保留根级 `platform/`。

### 1.2 依赖冲突清单

| 依赖 | COA 约束 | platform 约束 | 结论 |
| --- | --- | --- | --- |
| Python | `>=3.12` | `>=3.12` | 兼容 |
| `pydantic` | `>=2.13.4`（多个包） | `==2.10.4` | **硬冲突**；platform 必须上抬到 `>=2.13.4` |
| `pydantic-settings` | `>=2.0`（coa-common） | 无 | 增量 |
| `fastapi` | `>=0.115`（ontology-engine） | `==0.115.6` | 兼容（解析到 0.115.6） |
| `uvicorn` | `>=0.30` | `==0.34.0` | 兼容 |
| `httpx` | `>=0.27` | `==0.28.1` | 兼容 |
| `rdflib` | `>=7.0` | `==7.1.4` | 兼容 |
| `psycopg[binary,pool]` | 无 | `==3.2.3` | 增量；原生二进制依赖，COA Lambda 打包时不应装入 |
| `PyYAML` | `>=6.0` | `==6.0.2` | 兼容 |
| `pyshacl` | 无 | `==0.30.1` | 增量 |
| `pypdfium2` | `>=4.30.0`（dev） | `==5.14.0` | 兼容（5.14 满足 >=4.30） |
| `pdfplumber` / `markitdown` | 无 | 固定版本 | 增量；依赖较重，建议放入 optional extra |
| `sqlglot` | `>=25.0` | 无 | 增量 |
| `uv` | `>=0.13.4`（根） | 无 | 仅根 workspace 要求 |

**结论：** 唯一必须改版本的是 `pydantic`；平台代码从 2.10.4 到 2.13.4 需要回归，但属于 minor 升级，风险可控、必须实测。`fastapi`/`uvicorn` 不是 COA 所有包的依赖，但如果 platform 仍作为长驻服务留在 workspace，它们必须留在 platform 的依赖里；若 platform 只作为 provider 包，建议改成 `[project.optional-dependencies] server`。

### 1.3 `smithy-generated/` 与 `uv sync` 是否会挡路

- 挡的是“**workspace 成员管理**”这条路，不挡“platform 代码被 COA import”这条路。
- 若坚持 workspace 成员：必须先解决 H0（生成 smithy 或改根 members），否则 `uv sync` 永远过不去。
- 若接受首切片用独立 venv：完全绕开，代价是暂时不能声明“workspace 成员”。

**直接回答 Q1：** 可以作为成员包的技术形态存在，但**今天加不进当前 workspace**；硬冲突只有 pydantic 一处；缺 smithy 是 workspace 级阻塞，不是 platform 级阻塞。

---

## 2. 运行形态

### 2.1 三种候选

| 形态 | 调用链 | 评价 |
| --- | --- | --- |
| A. COA handler → 本地 HTTP → platform sidecar | COA 进程通过 HTTP 调 platform 的 `/graph`、`/metrics` 等 | 保留 platform 长驻形态；但 platform 仍是运行时主干，COA 只是客户端；协议面还要新增端点 |
| B. COA Protocol → platform provider 进程内 import | COA 的 `GraphClient`/`VectorClient`/`LLMClient`/`MetadataStoreClient` 直接实例化 platform 的本地实现 | 无 HTTP 跳、无双份序列化、协议面最小；COA 业务包成为主路径 |
| C. 混合：进程内 provider + sidecar 仅做管理面 | 关键路径走 B；platform 的 web/health/ops 作为可选 sidecar | 兼顾运维与主干归属 |

### 2.2 推荐

**推荐 B，C 作为运维补充。**

理由：

1. **协议面很窄**：`GraphClient` 只有 `query`/`ask`/`health_check` 三个方法；`VectorClient` 只有 `search`/`hybrid_search`/`health_check`；`LLMClient` 只有 converse/stream；`MetadataStoreClient` 约 10 个方法。进程内实现比新增一套 HTTP 端点便宜。
2. **避免双份真相**：HTTP sidecar 会把 platform 的 B 类 API 继续当主干，和 COA 的 `context-manager`/`ontology-engine` 形成两套语义；进程内 provider 只有一套调用链。
3. **单机形态更简单**：PG 和 Oxigraph 仍是外部进程（或 Oxigraph 用 `pyoxigraph` 内嵌），业务进程只有一个；不需要模拟 Lambda 事件、API Gateway、AgentCore 帧。
4. **不与 8080 冲突**：过渡期可以让 8080 继续跑 platform 的旧 API，但新路径不经过它；8080 只作为只读数据和回退基线。

**必须承认的边界：** 进程内 provider 不是“直接 import 就通”。platform 的 A 类模块是自己的 `GraphStorePort`/`ObjectStorePort` 语义，COA 的 `GraphStore` 有 17 个方法、`GraphClient` 3 个、`VectorClient` 3 个，需要写适配层；这是中粒度工作量的主体。

**不建议：** 为了跑 COA 而模拟 AgentCore Runtime、Bedrock、Neptune、AOSS。那是路线 1 的成本，不是本路线的目标。

---

## 3. 三种整合粒度

> 三种粒度都假定：A 类保留、B 类不进入新主干、C 类作为新增。差别在“放在哪里”和“怎么被调用”。

### 3.1 粗粒度：platform 整体作为 sidecar

| 项 | 内容 |
| --- | --- |
| 要动什么 | platform 保持独立服务与 compose；在 COA 侧新增 `coa-local-clients`，用 HTTP 实现 `GraphClient`/`VectorClient`/`LLMClient`/`MetadataStoreClient`；为缺失的协议方法补 platform 端点 |
| 工作量 | **M**：4 个客户端适配 + 补端点；若要把 `ontology-engine` 的 17 个 `GraphStore` 方法也走 HTTP，升到 L |
| 8080 影响 | **零**。platform 原样运行，8080 可继续作为 sidecar；不需要改数据或容器 |
| 上游改动 | 新文件为主；不修改 COA 现有源码。根 workspace 仍因 smithy 不可 sync |
| 主要问题 | platform 仍是运行时主干；COA 只做客户端；两套 API/语义继续存在；“整合”只到目录和调用关系 |

### 3.2 中粒度：A 抽成 `packages/local-providers`

| 项 | 内容 |
| --- | --- |
| 要动什么 | A 8,659 行抽成 `packages/local-providers`：`graph_oxigraph`/`graph_fuseki`/`vector_pg`/`search_pg`/`metadata_pg`/`object_*`/`embedding`/`llm_openai`/`reasoner_*`/`parsers`/`validation`/`shapes` + 装配/配置子集；实现 COA Protocol；C 14,102 行拆成 3–5 个扩展包（provenance、facts/audit、canvas、datagen、metric-observations、change-impact、term-governance、healthboard）；B 16,404 行冻结为 legacy，不进入新主干 |
| 工作量 | **L**：A 不是平移，要写协议适配；C 要换宿主；B 要逐步退出 |
| 8080 影响 | **高（终态）**。B 的 API/UI 不再是主干；过渡期 8080 可原样运行做回退，退役后现有 API 契约消失，数据（37,477 行观测、610 个版本）保留 |
| 上游改动 | 根 `pyproject.toml` 增加 2–4 个 members（元数据改动）；COA 现有源码在 ontology-engine/metric-service 路径可保持 0 修改；若包含 context-manager，H3/H4 必须改现有文件，不能声明零改动 |
| 主要问题 | A 的协议适配是主体；B 退役会打断 8080 的现有验收；pydantic 上抬需要回归 |

### 3.3 细粒度：必要模块拆进对应 COA package

| 项 | 内容 |
| --- | --- |
| 要动什么 | 按 COA 包就近拆：graph/vector/metadata → `ontology-engine/stores`；embedding/LLM → `coa_common` 或 `context-manager/clients`；parser → `sources/preprocessing`；validation/reasoner → `ontology-engine/validation`；config/assembly → `coa_common`；C 类仍要独立包或塞进对应包 |
| 工作量 | **XL**：移动点多、导入图复杂、循环依赖风险；每动一个上游包都要处理测试与合并冲突 |
| 8080 影响 | **高且立即**：platform_core 被拆散，8080 无法原样运行；需要先建替代主路径 |
| 上游改动 | **不能维持零改动**：必须修改 COA 现有包的文件与导入，后续上游升级冲突概率最高 |
| 主要问题 | 与上游内部结构强耦合；不适合作为“二开”的边界，容易被上游 drift 拖死 |

### 3.4 对比汇总

| 维度 | 粗粒度 | 中粒度 | 细粒度 |
| --- | --- | --- | --- |
| 工作量 | M | **L** | XL |
| 8080 影响 | 零 | 高（终态） | 高（立即） |
| 上游现有源码改动 | 0 | ontology/metric 路径 0；context-manager 非 0 | 非 0 |
| COA 是否运行主干 | 否 | **是（library/runtime 层）** | 是（更深，但耦合上游） |
| 主要风险 | 名义整合 | A 适配 + B 退役 | 上游合并冲突、循环依赖 |

---

## 4. 推荐与口径判定

### 4.1 推荐：中粒度

**理由：**

1. 它把 A 类放在 COA 的扩展点位置，而不是继续让 platform 的 API 当主干；这才可能让“COA 当主干”成立。
2. 它保住了上游包源码的零修改（ontology-engine/metric-service 路径），只新增 provider 与扩展包；比细粒度更适合长期跟上上游。
3. 它不要求一次退役 8080；可以先让 COA 路径跑通，再把 B 类逐项下线。
4. 它避免了粗粒度的“两套 API/两套语义继续存在”。

**不选粗粒度：** 它把 platform 继续当运行时主干，COA 只是 HTTP 客户端；“整合”只到目录与调用关系，不满足本问题的方向。

**不选细粒度：** 它直接改 COA 包内部，上游升级会持续冲突；工作量 XL，收益不比中粒度多。

### 4.2 「在 COA 上二开」成立在哪一层

| 层 | 是否成立 | 条件 |
| --- | --- | --- |
| 目录结构 | **成立** | `platform/` 移到 `packages/` 下即可；但这是最弱的一层，不能单独作为验收口径 |
| 代码归属 | **成立** | A/C 代码作为 COA workspace 的新包，新增代码归 COA 所有；上游现有文件不改 |
| 运行主干（library/runtime） | **有条件成立** | 本地 runner 的主路径必须执行 COA 的 `ontology-engine`/`metric-service` 业务类，provider 只是被注入；platform `api.py` 不再是主 API |
| COA 原生 handler/Lambda 层 | **不成立** | 不生成 smithy、不解决 AgentCore/Bedrock/Neptune/AOSS，就无法运行原生 handler |

**正面回答：** 中粒度下，「在 COA 上二开」可以在**代码归属 + 运行主干（library 层）**成立；不能在**COA 原生 handler/Lambda 层**成立。若最终仍由 platform 的 `/api` 服务所有请求，那只是在目录结构层成立，不能对外声称“在 COA 上二开”。

---

## 5. 第一个可交付切片

**编号：S1-COA-LOCAL-PROVIDER-METRIC**
**目标：同时绕开 `uv sync` 与 AWS，并证明“platform 的 A 类能力以 COA 扩展点方式被 COA 业务逻辑消费”。**

### 5.1 范围

| 做 | 不做 |
| --- | --- |
| 在 COA 仓库新增 `packages/local-providers/`（暂不加入 workspace members） | 不执行 `uv sync` / `make generate` |
| 放入 `JsonDataSourceLookup`：从 8080 只读导出的目录快照构造 lookup | 不连 8080 的 PG、不写库、不重启容器 |
| 用 COA 的 `coa_metrics.osi_parser` / `validator` 作为调用方 | 不 import `metric_api_handler`、不跑 Lambda |
| 独立 venv + `PYTHONPATH` 直接引用 `libs/common/src` 与 `packages/metric-service/src` | 不装 workspace、不装 `fastapi`/`uvicorn` |
| 输入 85 条指标定义，输出逐条校验报告 | 不连 Neptune/AOSS/DynamoDB/Bedrock |
| 证据落 `doc/_evidence-coa-integration/s1-2026-11-08/` | 不放入 `doc/_qa*` |

### 5.2 执行路径

```powershell
cd D:\agentABC\coa
py -3.12 -m venv .venv-coa-local
.\.venv-coa-local\Scripts\python -m pip install -U pip
.\.venv-coa-local\Scripts\pip install boto3 botocore pydantic pydantic-settings structlog PyYAML sqlglot pytest
$env:PYTHONPATH="D:\agentABC\coa\libs\common\src;D:\agentABC\coa\packages\metric-service\src;D:\agentABC\coa\packages\local-providers\src"
.\.venv-coa-local\Scripts\python -m pytest `
  packages\metric-service\tests\unit\test_osi_parser.py `
  packages\metric-service\tests\unit\test_validator.py -q
```

注意：`packages/local-providers` 暂不进入根 `members`，因此不会触发 workspace 解析；等 smithy 生成后再加入。

### 5.3 验证口径

| 检查 | 通过条件 |
| --- | --- |
| 依赖隔离 | 只装 8 个 pip 包；`uv sync` 未执行；无 `smithy-generated/` |
| 上游纯逻辑测试 | 两个测试文件全绿 |
| AWS 隔离 | `AWS_*` 未设置；无 AWS 网络调用；无 `SMUSClient` 实例化 |
| 解析覆盖 | 85/85 条指标解析成功 |
| 往返一致 | parse → serialize → re-parse 字段语义一致 |
| 校验对账 | 与 `publishable=60 / executable=56 / both=43` 逐条对账，每个差异有原因 |
| 归属证明 | 调用链是 COA `validator` → `LocalDataSourceLookup`；不是 platform API 处理请求 |
| 零长驻服务 | 只跑进程内脚本/pytest；PG/Oxigraph 不启动 |

### 5.4 完成定义

7 项全部有可复现命令与输出，`reconcile.md` 无未解释项。达到后再考虑：
- 把 `local-providers` 加入 workspace（前提：smithy 已生成）；
- `GraphClient` 适配器（3 个方法，最小协议面）；
- `MetadataStoreClient` 适配器（10 个方法）；
- context-manager 的 H3/H4 替换（最后做，成本最高）。

---

## 6. 未验证 / 遗留

| 项 | 状态 |
| --- | --- |
| `pydantic` 2.10.4 → 2.13.4 的平台回归 | 未执行；需实测 |
| 作为 workspace 成员加入后的 `uv lock` | 未执行；当前被 smithy 缺失阻断 |
| A 类协议适配的真实行数 | 未测量；本文只给量级 |
| `packages/local-providers` 的最终包边界 | 未定；首切片只放 lookup |
| context-manager 的 H3/H4 | 未处理；中粒度若要 Q&A 必须做 |
| 8080 | 未接触；本文所有读取均为只读 |
