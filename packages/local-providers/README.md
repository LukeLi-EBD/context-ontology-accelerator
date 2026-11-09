# local-providers（S1-COA-LOCAL-PROVIDER-METRIC）

本目录是 S1 切片新增的**本地 provider**，服务于 `coa_metrics.validator`，不进入根 workspace members。

## 边界

- 只新增文件；未改动 COA 上游任何既有文件。
- 不执行 `uv sync` / `make generate` / `docker build`；不连 AWS；不启动 PG / Oxigraph / 任何长驻服务。
- 通过独立 venv（仓库根 `.venv-coa-local`）+ `PYTHONPATH` 使用，依赖仅：
  `boto3 botocore pydantic pydantic-settings structlog PyYAML sqlglot pytest httpx`
  （`httpx` 是 `coa-metrics` 自身声明的依赖，仅为让上游 `test_validator.py` 的 Neptune 用例可导入）。

## 内容

| 路径 | 作用 |
| --- | --- |
| `src/coa_local_providers/json_lookup.py` | `JsonDataSourceLookup`，实现 `coa_metrics.lookups.DataSourceLookup` 的 7 个方法，读取 JSON 目录快照 |
| `src/coa_local_providers/osi_bridge.py` | 把 `OsiMetric` 转成 `validate_metric` 需要的 camelCase `metric_body` |
| `src/coa_local_providers/snapshot.py` | 只读导出（HTTP GET）与 binding/公式到 SQL 的编译 |
| `src/coa_local_providers/win_compat.py` | Windows 上补齐 `resource` 模块，使 `coa_common` 可导入；不参与任何业务逻辑 |
| `src/coa_local_providers/pytest_winshim.py` | 同一 shim 的 pytest 插件形式，供上游测试文件直接运行 |
| `scripts/export_snapshot.py` | 导出 manifest/指标/目录 + 解析 committed binding，生成 OSI YAML |
| `scripts/run_s1.py` | 用 COA `parse_osi_yaml` + `validate_metric` 逐条校验并对账 |

## 复现

```powershell
$env:PYTHONPATH="D:\agentABC\coa\libs\common\src;D:\agentABC\coa\packages\metric-service\src;D:\agentABC\coa\packages\local-providers\src"
D:\agentABC\coa\.venv-coa-local\Scripts\python.exe packages/local-providers/scripts/export_snapshot.py
D:\agentABC\coa\.venv-coa-local\Scripts\python.exe packages/local-providers/scripts/run_s1.py
```

证据与结论见 `doc/_evidence-coa-integration/s1-2026-11-08/`。
