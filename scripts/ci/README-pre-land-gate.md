# 合并前门禁（pre-land gate）

谁合并谁跑。一条命令跑完下面 7 项，每项打印 `PASS / FAIL / SKIP + 原因 + 耗时`，结束给总结论、退出码，并在 `doc/coa-x/evidence/pre-land-gate/` 留一份带时间戳的 markdown 记录。

不需要启动任何服务，不连 AWS，不碰 8080 / 8082 / 8210 / 7878。

## 一条命令

在仓库根目录：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ci/pre-land-gate.ps1
```

| id | 检查内容 |
| --- | --- |
| `smithy` | 在临时目录干净重生成 smithy 产物，与提交的 `smithy-generated/` 逐文件比对，并校验 `.inputs.sha256` 指纹 |
| `infra-tsc` | `infra` 目录 `tsc --noEmit` |
| `web-tsc` | `web-app` 目录 `tsc --noEmit` |
| `web-build` | `pnpm --filter coa-web-app build` |
| `infra-jest` | `infra/test` 下 5 个 jest 套件，带 `--coverage=false` |
| `canvas-pytest` | `platform-core/tests/test_d1_canvas.py` 与 `test_d1_canvas_full.py` |
| `migration` | `scripts/ci/migration-idempotency.ps1`，独立容器 + 随机端口，跑完自动删除 |

退出码：`0` 全部通过；`1` 至少一项失败；`2` 参数错误。

## 失败怎么办

1. 看终端 `[FAIL]` 那行后面最后 30 行输出，或打开本次 evidence 的 `## Failure output`。
2. 修完重跑。不要带着失败的结果合并。
3. 只有确认该项与本次改动无关、或本机环境确实跑不了时，才跳过，并且必须写原因（见下一节）。

## 跳过怎么写

```powershell
# 单项跳过，等号后面是原因
-Skip "web-build=本次只改文档"

# 多项跳过一次写
-Skip "web-tsc=只改后端,infra-jest=只改后端"

# 全部跳过（只留记录，不做任何检查）
-Skip all
```

跳过的项在终端显示 `[SKIP]`，原因会写进 evidence 的 `## Skipped`。不写 `-Skip` 就不会跳过，不存在静默跳过。

## 常用参数

| 参数 | 说明 |
| --- | --- |
| `-Skip "<id>[=原因],..."` | 跳过指定检查 |
| `-Python <path>` | canvas / 迁移用的解释器；默认 `$env:COA_GATE_PYTHON` → `<repo>\.venv\Scripts\python.exe` → PATH 上的 `python` |
| `-JavaHome <path>` | smithy 的 Gradle 需要 JDK 17+；本机只有 Java 8 时用它指向 IDE 自带 JBR 等目录 |
| `-EvidenceDir <dir>` | 覆盖留痕目录（默认 `doc/coa-x/evidence/pre-land-gate`） |
| `-ListOnly` | 只列出检查项 id，不执行 |

## 本机依赖（一次性）

- `pnpm install --frozen-lockfile`（`infra` / `web-app` 的 `node_modules`）
- Python 解释器带 `pytest / psycopg / fastapi / yaml`（`uv sync` 生成的 `.venv` 即可）
- Docker Desktop（迁移门禁要起一个临时 postgres 容器）
- JDK 17+（Smithy Gradle 不接受 Java 8）
- `openapi-generator-cli-7.12.0.jar`，默认放在 `$HOME/.local/share/openapi-generator`，缺失时脚本会尝试下载

## 口径说明

- smithy 比对只覆盖 `smithy-generated/` 中被 git 跟踪的产物；`build-info` 是构建元数据（含绝对路径），不参与比对。
- 比对会忽略行尾空白与 Windows 下的模块路径分隔符差异，但会把数量写进明细；真实内容差异一律 FAIL。
- 本门禁不包含：需要长驻服务或 AWS 的端到端用例、全量 pytest、覆盖率统计。
