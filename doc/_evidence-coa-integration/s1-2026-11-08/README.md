# S1-COA-LOCAL-PROVIDER-METRIC 证据

日期：2026-11-08　机器：Windows　宿主：`D:\agentABC\coa`

## 结论

| 验收项 | 结果 |
| --- | --- |
| OSI 解析 | **85/85 成功**（`errors=0`、`warnings=0`） |
| round-trip 语义一致 | **True**（COA `serialize_osi_yaml` → 再解析 → 逐字段比对） |
| 平台 manifest 基线 | total=85 / publishable=**60** / executable=**56** / both=**43**（复算一致） |
| 对账 | 56 条 executable 全部通过 COA SQL 校验；23 条一致（平台不可执行、COA 亦无 SQL）；仅 **6 条差异**且均有原因 |
| 调用链 | `run_s1 → coa_metrics.validator.validate_metric → JsonDataSourceLookup`，594 次 lookup 调用，见 `report/callchain.txt` |
| 长驻服务 | 未启动；仅对已运行的 8080 做 HTTP GET，未写 8080，未连 PG/AWS |
| 上游两个纯逻辑测试文件 | **240 passed / 0 failed / 4 skipped**（skip 为测试文件自身标记的 `DynamoDBDataSourceLookup` 已废弃用例） |

## 差异逐条（6 条）

| metric | executable | sqlSource | 平台原因 |
| --- | --- | --- | --- |
| FIN-BANK-035 | False | fact_function | 库内该口径无任何观测记录 |
| FIN-BANK-036-v1 | False | fact_function | 库内该口径无任何观测记录 |
| FIN-INS-004 | False | binding | 库内该口径无任何观测记录 |
| FIN-INS-017 | False | binding | 四元组不完整：缺 denominator_agg |
| FIN-INS-022-v2 | False | binding | 库内该口径无任何观测记录 |
| FIN-INS-023-v2 | False | binding | 库内该口径无任何观测记录 |

6 条差异都不是 SQL 合法性问题：平台 `executable` 还取决于观测数据与四元组完整性，COA validator 只判断 SQL 语法/结构/列引用。

## 测试依赖口径

- 独立 venv 直装包为 9 个：`boto3 botocore pydantic pydantic-settings structlog PyYAML sqlglot pytest httpx`。
- 第 9 个 `httpx` 是 `packages/metric-service/pyproject.toml` 自身声明的依赖，仅用于让
  `test_validator.py` 中的 `TestNeptuneOntologyLookupUriValidation` 在 import 期加载
  `coa_metrics.neptune_client`；未引入任何新实现。
- 4 个 skip 均为测试文件内的 `pytest.skip("DynamoDBDataSourceLookup deprecated — replaced by
  SmusCatalogDataSourceLookup")`，非本切片排除，未做任何静默跳过。完整输出见 `report/pytest.txt`。

## 文件索引

| 路径 | 说明 |
| --- | --- |
| `raw/manifest.json` | `GET /metrics/report/manifest` 原始响应 |
| `raw/metrics/<metricId>.json` | 85 条指标 `/metrics/{id}` + `/browse/metrics/{id}` 合并原始响应 |
| `raw/catalog_dictionaries.json` | `GET /catalog/dictionaries` 全部 375 行（28 张表） |
| `snapshot/catalog.json` | `JsonDataSourceLookup` 消费的目录快照 |
| `snapshot/bindings.json` | 从 committed 迁移解析的 binding 行 + fact_function 映射 |
| `snapshot/reconcile_inputs.json` | 每条指标的 publishable/executable/原因/definitionVersion/sqlSource |
| `snapshot/metrics.osi.yaml` | 85 条指标 + 28 个 dataset 的 OSI v1.0 文档（COA 序列化器产出） |
| `report/validation.json` | 逐条校验结果（errors/warnings/lookup 调用数） |
| `report/reconcile.md` | 上方对账表与分类计数 |
| `report/callchain.txt` | 调用栈、模块路径、方法级样本 |
| `report/env.txt` | Python/平台/PYTHONPATH/AWS 环境变量存在性 |
| `report/pytest.txt` | 上游两个测试文件的完整输出 |
| `report/sensitive_scan.txt` | 98 个文件、0 命中 |

## 每个快照的来源与导出方式

| 文件 | 来源 | 导出方式 |
| --- | --- | --- |
| `raw/manifest.json` | 运行中平台 `GET /metrics/report/manifest` | 只读 HTTP GET，原样落盘 |
| `raw/metrics/<metricId>.json` | `GET /metrics/{id}` + `GET /browse/metrics/{id}` | 只读 HTTP GET，两个响应合并后逐条落盘（85 个文件） |
| `raw/catalog_dictionaries.json` | `GET /catalog/dictionaries?limit=200&offset=…` | 只读 HTTP GET，分页拉全 375 行 |
| `snapshot/catalog.json` | 上述 `raw/catalog_dictionaries.json` | `export_snapshot.py` 按 `catalog → data_source`、`schema.table → columns` 重组成 `JsonDataSourceLookup` 快照 |
| `snapshot/bindings.json` | 仓库内 committed 迁移 `platform/src/platform_core/sql/V*.sql` 与 `metric_binding_overrides.py` | 文本/AST 解析，**未连 PG**；`fact_function` 映射同源 |
| `snapshot/reconcile_inputs.json` | `raw/manifest.json` + `raw/metrics` | 按 metricId 汇总 publishable/executable/原因/definitionVersion/sqlSource |
| `snapshot/metrics.osi.yaml` | 上述全部快照 | 构造 COA `OsiDocument` 后由 `coa_metrics.osi_parser.serialize_osi_yaml` 输出 |
| `report/validation.json` `report/reconcile.md` | `metrics.osi.yaml` + `catalog.json` + `reconcile_inputs.json` | `run_s1.py` 进程内调用 `parse_osi_yaml` / `validate_metric` / `JsonDataSourceLookup`，**不再访问 8080** |
| `report/callchain.txt` | 运行时栈 | `RecordingLookup` 包裹 `JsonDataSourceLookup`，记录方法级首调用栈与调用样本 |
| `report/pytest.txt` | 上游测试 | `pytest` 以 `-p coa_local_providers.pytest_winshim` 加载 Windows `resource` shim 后运行 |
| `report/env.txt` | 运行时环境 | Python/平台/PYTHONPATH/AWS 变量存在性（只记录 set/unset，不记录值） |
| `report/sensitive_scan.txt` | 本目录全部文件 | 正则扫描 AWS key/私钥/口令/token/邮箱/本机路径 |

## 入库与提交边界

- 本目录**未被 `.gitignore` 覆盖**，会入库；入库前已全量扫描，`report/sensitive_scan.txt` 记录 0 命中。
- `.venv-coa-local/` **不得入库**（它不在 `.gitignore` 内）。提交时按具体路径 add，例如
  `git add doc/_evidence-coa-integration/s1-2026-11-08 packages/local-providers`，不要 `git add .`。
- `git diff --stat` 为空：未修改 COA 上游任何既有文件；未 `.gitignore`、未根 `pyproject.toml`。
- 全程未启动长驻服务、未写 8080、未连 PG/AWS。

## 复现

```powershell
$env:PYTHONPATH="D:\agentABC\coa\libs\common\src;D:\agentABC\coa\packages\metric-service\src;D:\agentABC\coa\packages\local-providers\src"
D:\agentABC\coa\.venv-coa-local\Scripts\python.exe packages/local-providers/scripts/export_snapshot.py
D:\agentABC\coa\.venv-coa-local\Scripts\python.exe packages/local-providers/scripts/run_s1.py
D:\agentABC\coa\.venv-coa-local\Scripts\python.exe -m pytest packages/metric-service/tests/unit/test_osi_parser.py packages/metric-service/tests/unit/test_validator.py -q -p coa_local_providers.pytest_winshim
```

## 数据来源说明

- 指标语义、publishable/executable、目录元数据来自运行中的 8080 只读 GET。
- SQL 表达式来自 committed 迁移 `platform/src/platform_core/sql/V*.sql` 的 `metric_field_binding`
  与 `platform.metric_fact_*` 函数绑定（含 `metric_binding_overrides.py` 修正）；未连 PG。
- 23 条无绑定指标以平台 `formulaText` 作为表达式原样承载，`sqlSource=formula_text_fallback`，COA 判为
  非 SQL，与平台 `executable=False` 一致。
