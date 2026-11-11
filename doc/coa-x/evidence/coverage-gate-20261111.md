# infra 80% 行覆盖门限核查（coverage-gate）

- 核查日期：2026-11-11
- 基线：`luke` @ `38b9c4c5`（干净 checkout）
- 工作区：`D:\agentABC\wt\cov-audit`，分支 `audit/coverage-gate`
- 结论：**无缺口。** 全量 infra 套件全局行覆盖 `2505/2567 = 97.58%`，高于 80% 门限；`69.06%` 是过滤跑时分母塌缩造成的度量假象，不是覆盖欠账。
- 约束：本次只核查、只出证据，未改门限、未改 CI 配置、未 push、未建 PR。

## 1. 门限出处

| 配置 | 位置 | 取值 | 说明 |
|---|---|---|---|
| `collectCoverage` | `infra/jest.config.js:14` | `true` | 默认就收集覆盖，`--coverage=false` 才是关掉 |
| `collectCoverageFrom` | `infra/jest.config.js:17` | `["lib/**/*.ts","bin/**/*.ts"]` | 名义统计范围 |
| `coverageThreshold.global.lines` | `infra/jest.config.js:18-22` | `80` | 只有全局行一个门限；无按目录/按文件门限，statements/branches/functions 不设限 |

## 2. CI 路径

| 场景 | 位置 | 命令 |
|---|---|---|
| PR | `.github/workflows/pr.yml:178` | `pnpm nx affected -t test --base="origin/${BASE_REF}" --head=HEAD --output-style=stream` |
| 合入队列 | `.github/workflows/pr.yml:270` | `pnpm nx run-many -t test --output-style=stream` |

- nx 的 `test` target 由 `infra/project.json` 的 `test`（只声明 inputs）与 `infra/package.json:12` 的 script 合并而来；`nx show project infra --json` 实测 `scriptContent` 为：
  `jest --maxWorkers=4 && uv run pytest test/lambdas -q`
- 该脚本**没有** `--coverage=false`；全仓（排除 `node_modules`）grep `coverage=false` 无命中。
- 结论：本地默认配置与 CI 是同一条路径，80% 门限在 CI 生效。`coverage.xml` 仅作产物上传（`pr.yml:194`、`pr.yml:282`），没有额外比对逻辑。

## 3. 全量实测数字

命令（工作区内，`infra/` 目录）：

```powershell
pnpm exec jest --maxWorkers=4 --coverage --coverageReporters=json-summary
```

```text
Test Suites: 5 failed, 47 passed, 52 total
Tests:       70 failed, 1 skipped, 1145 passed, 1216 total
Lines:       2505/2567 = 97.58%
Statements:  97.46%
Branches:    84.73%
Functions:   88.65%
```

- 输出中没有任何 `coverage threshold ... not met` 报错；`exit 1` 只来自 5 个套件的用例失败，不是门限。
- 失败的 5 个套件正是 `data-layer-stack` / `ssm-refs-check` / `model-id-defaults` / `preflight-arm64` / `python-bundling`，失败原因全部是 Windows 本机环境：`ssm-refs-check` 起 python 返回 9009；`model-id-defaults`、`preflight-arm64` 走 bash 失败；`python-bundling` 为 symlink `EPERM` 与路径分隔符；`data-layer-stack` 断言正则要求 `/`、Windows 给出 `\`。
- 因此 97.58% 是**保守下限**（失败用例只会少算分子）。同一套 160 个用例在 Linux 侧为 157 passed / 0 failed / 3 skipped，集合一致。

## 4. 三种跑法的分母对照

| 跑法 | 进入分母的文件数 | 行分母 | 行覆盖（本机实测） |
|---|---:|---:|---|
| 单套件 `test/app-connector-tag.test.ts` | 1 | 52 | 100% |
| 你点名的 5 个套件 | 11 | 375 | 本机 242/375 = 64.53%（70 个用例红）；你侧全绿时报出的 69.06% 属同一跑法 |
| 全量 52 套件 | 52 | 2567 | 2505/2567 = 97.58% |

- 机制：过滤跑时 Jest 只对**实际被 import 的 TS 文件**插桩，未加载的文件不进分母，所以分母从 2567 行塌缩到 375 行。
- 结论：`69.06%` 与 `97.58%` 分母不同，不可比；它不是"5 个套件只覆盖了全部代码的 69%"，也不是既有覆盖欠账（基线本身就是 38b9c4c5）。

## 5. fail-open 缺陷（单列）

**现象：** 即使全量跑，`bin/app.ts`（575 行）与 `lib/stacks/index.ts`（4 行）也从不进入分母。

**根因：** `infra/jest.config.js` 未设置 `coverageProvider`，Jest 默认 `babel`；而项目用 `ts-jest` 转换测试与源码。`collectCoverageFrom` 对"未被任何测试加载的文件"需要单独 transform 才能插桩，babel 侧没有 TS preset，于是这些文件被静默跳过——`collectCoverageFrom` 的"未加载文件计入"这一半实际失效。

**实测证据：** 全量跑覆盖报告只有 52 个文件；`bin/app.ts`、`lib/stacks/index.ts` 不在其中。单套件跑只出现 1 个文件（52 行），可排除"文件本来就不在统计范围"的解释。

**修复方向（本次不做）：**
1. 给 babel 补 TS transform（`@babel/preset-typescript`），让未加载文件也能插桩；或
2. 换 `coverageProvider: "v8"`，并确认 v8 在 ts-jest 下能覆盖未加载的 TS 文件。

**修完可能发生什么：** 分母会把 `bin/app.ts` 等当前 0 覆盖入口算进去，全量行覆盖几乎必然下降，**有可能掉到 80% 以下并直接变红**；这等于改变门限的真实含义，需要单独立项评估和配套补测。

**为何本次不做：** 本次任务是核查门限出处与判定 69.06% 的性质，明确不改门限、不改 CI 配置；修度量口径会改变门禁语义，属于独立决策，不能夹在证据核查里顺手改。

## 6. 两个边界

1. **PR 完全不碰 infra 时，这个 target 不跑。** `nx affected` 以项目为粒度：实测 `nx show projects --affected --files=infra/lib/utils/api-utils.ts` 输出 `infra`、`unit-guards`；一旦 infra 受影响，跑的是整条 `pnpm run test`（无测试路径过滤，jest 也没有 `testPathIgnorePatterns`），52 个套件全跑、分母保持 52 文件/2567 行——所以局部改动不会因分母变小而误报红。反之，没碰 infra 的 PR 不经过这道门禁。
2. **新增未被任何测试 import 的文件不进分母。** 这是第 5 节 fail-open 的直接后果：新增文件会被 80% 门限"看不见"；一旦它被某个测试 import，就会按真实覆盖进入分母并拉低全局值（这一侧是正常行为）。
