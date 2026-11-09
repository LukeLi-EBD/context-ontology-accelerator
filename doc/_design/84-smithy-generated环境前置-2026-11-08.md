# `smithy-generated/` 环境前置（P1 第三步）

> 结论：**不改根 `pyproject.toml`**。`smithy-generated/control-plane-python-server` 与
> `smithy-generated/data-layer-python-server` 是根 workspace 的显式成员，且被 gitignore 忽略；
> 它们是 `uv lock/sync` 的**环境前置**，不是代码问题。
> 本文只写操作口径与原始证据，不执行生成、不触发联网构建。
> 日期：2026-11-08。

---

## 1. 事实

| 位置 | 事实 |
| --- | --- |
| 根 `pyproject.toml:49-62` | `[tool.uv.workspace] members` 列 11 项，含 `smithy-generated/control-plane-python-server`、`smithy-generated/data-layer-python-server` |
| `.gitignore:44-45`、`160-161` | `smithy-generated/` 被忽略，仓库不携带生成物 |
| `uv.lock:715-731`、`737-749` | 两个生成包以 `editable = "smithy-generated/..."` 入锁 |
| `packages/{control-plane,metric-service,ontology-engine,sources}/pyproject.toml` | 均以 `workspace = true` 依赖 `coa-control-plane-server` |
| 本机现状 | `D:\agentABC\coa\smithy-generated` **不存在**（实测 `Test-Path` = False） |

因此：在生成物补齐之前，仓库根任何 `uv lock` / `uv sync` 都不能作为“依赖已就绪”的证据；
`platform` 侧只能在独立 venv 或 path dependency 方式下工作（见 80 号文档 §1.3、§5）。

## 2. 上游原始报错（原文留档）

来源：`.github/actions/setup-build/action.yml:4-8`，逐字引用：

```
# IMPORTANT — call order: `smithy-generated/control-plane-python-server` is a uv
# workspace member (see [tool.uv.workspace] in pyproject.toml), so `uv sync`
# fails with "references a workspace ... but is not a workspace member" unless
# the generated tree already exists. Any job using this action must download the
# smithy-generated artifact BEFORE this step.
```

即上游记录的核心错误串为：

```
references a workspace ... but is not a workspace member
```

另附 83 号 §3.2 在本机 uv 0.12.7 临时目录内的**等价探针**输出（不是上游原文，仅作行为参考）：

```
`sub` references a workspace in `tool.uv.sources` ... but is not a workspace member
Distribution not found at: file:///.../sub
```

> 本机 uv 版本低于仓库 `required-version = ">=0.13.4"`，在仓库根直接执行 `uv` 会先被版本门槛拒绝：
> `Required uv version '>=0.13.4' does not match the running version '0.12.7'`。
> 未在本机复现上游完整报错；以上游 action 注释原文为准。

## 3. 补齐生成物：两条路径

### 3.1 本机生成

```bash
# 仓库根执行（需要 bash；Windows 用 Git Bash / WSL）
make generate            # 等价于 ./scripts/smithy-generate.sh
```

前置条件（`.mise.toml` + `scripts/smithy-generate.sh` 实测）：

| 项 | 要求 | 来源 |
| --- | --- | --- |
| Python | 3.12 | `.mise.toml:2` |
| Java | 17（仓库支持范围 17–24） | `.mise.toml:3-5`、`scripts/check-java-version.sh` |
| Node | 22.23.4 | `.mise.toml:6` |
| pnpm | 10.34.5（aqua 预编译发行版） | `.mise.toml:7-11`、脚本会先检查 `command -v pnpm` |
| 网络 | Maven Central + GitHub Releases（openapi-generator 7.12.0、`robot` 无关） | `scripts/smithy-generate.sh:22,183-207` |
| 可选 | `CODEARTIFACT_MAVEN_URL` + token（CI 用，规避 Maven Central 429） | `scripts/smithy-generate.sh:24-45` |

产物落在 `smithy-generated/`（gitignored，**不要提交**）。生成成功后再执行
`./scripts/setup-dev.sh`（`make setup` 的第三步），才是完整的 workspace 安装顺序：

```
make setup = install-pnpm.sh → smithy-generate.sh → setup-dev.sh
```

### 3.2 从 CI 搬生成物

上游 CI 的做法是“先下载 smithy-generated artifact，再跑 setup-build”（见 §2 原文）。
本 fork 若不复现 CI，可用等价方式：在能生成的环境执行 §3.1，把 `smithy-generated/` 整目录
拷入 `D:\agentABC\coa\smithy-generated\`。要求：

- 目录结构与上游一致（两个 `*-python-server` 成员目录必须在）；
- 不进入 git（`.gitignore` 已覆盖）；
- 记录来源 commit（生成物和 `uv.lock` 的 editable 块必须对得上）。

## 4. 完成判据与影响

| 检查 | 通过条件 |
| --- | --- |
| 目录存在 | `smithy-generated/control-plane-python-server`、`.../data-layer-python-server` 均存在 |
| workspace 可解析 | `uv lock --check`（uv ≥0.13.4）不再报 “not a workspace member” |
| 安装可执行 | `uv sync` 不再因缺成员失败（本机未实测，以 CI 既有成功流程为据） |
| 仓内改动 | 根 `pyproject.toml`、`uv.lock` **零改动** |

不影响：

- 现有 8080 / 8082 栈：`platform` 容器用镜像内依赖，不经过根 `uv sync`；
- `platform` 独立 venv（`.venv-coa-local`）与 `packages/platform-core` 的单测路径；
- 本文不新增任何生成物到工作区。

## 5. 遗留

- 本机 uv 0.12.7 低于 `>=0.13.4`，**未能验证生成物补齐后的 `uv lock/sync` 成功路径**；
  这一步留给具备 uv ≥0.13.4 + JDK17 + pnpm 的窗口执行。
- `make generate` 需要联网与 Gradle/Maven 构建，属环境动作，不在本轮“不启动长驻服务、不连 AWS”的范围之外；
  本轮**未执行**。
