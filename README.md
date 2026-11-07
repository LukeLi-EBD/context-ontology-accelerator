# 本体平台（Ontology Platform）

单机、单用户的本体加速器：以本体为核心，围绕「术语 → 指标口径 → 事实」做版本化治理，并提供带引用的问答入口。

- **本体为核心**：版本化 T-Box 发布、术语门禁与高水位审计、RDFS/OWL EL 推理物化；本体版本指针是唯一事实来源。
- **口径治理**：指标定义、字段绑定、观测聚合语义分层登记；事实层可追溯，可算性预检与计算共用同一判定集合。
- **可引用问答**：答案区分 `value` 与 `definition` 意图，带图、表、文档引用与覆盖度标注，不做无依据推断。

运行与开发入口：[platform/README.md](platform/README.md)（上手指南）、[platform/RUN.md](platform/RUN.md)（运行手册与部署前置清单）。设计与集成契约见 [doc/_design/](doc/_design/)。

## Quick Start

> 本平台的运行入口在 [platform/README.md](platform/README.md) 与 [platform/RUN.md](platform/RUN.md)。
> 以下为上游 AWS COA 框架的开发步骤，不参与本平台的单机运行。

### Prerequisites

- Python 3.12, Node.js 22.23.4+, Docker
- [pnpm](https://pnpm.io/) (Node package manager — installed via `mise` or `npm install -g pnpm`)
- Java 17–24 (21 recommended) and Gradle (for Smithy codegen), plus Maven (for the
  Databricks connector `make deploy-dev` builds). JDK 25+ is not supported yet: the Athena
  Federation SDK the connector bundles fails its tests on it, and `make preflight` rejects it.
  **`brew install maven` also installs the newest OpenJDK and runs Maven on it** — after
  installing, check `mvn -v` and, if it shows Java 25+, point Maven at JDK 21:
  `export JAVA_HOME=$(/usr/libexec/java_home -v 21)` (`brew install --cask corretto@21` if
  you don't have it). `mise install` provides a supported JDK and Maven from `.mise.toml`.
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Setup

> **Use a release, not the tip of `main`.** We recommend starting from a tagged
> release — [github.com/aws/context-ontology-accelerator/releases](https://github.com/aws/context-ontology-accelerator/releases).
> `main` tracks ongoing development.

```bash
# Clone at the latest release tag (replace <tag> with a release from the link above)
git clone --branch <tag> https://github.com/aws/context-ontology-accelerator.git
cd context-ontology-accelerator

make setup      # install Python + CDK TypeScript dependencies
make format     # auto-format code
make lint       # check linting
make test       # run unit tests
```

**Full developer guide:** [external-docs/content/getting-started.md](external-docs/content/getting-started.md)

## Repository Structure

```
coa/
├── platform/                 # 本项目主体：单机本体平台
│   ├── src/platform_core/    # API、本体/指标/问答/推理实现与迁移 SQL（sql/V1–V42）
│   ├── web/                  # 浏览、问答、看板前端
│   ├── tests/                # 全量 unittest 套件（2026-11-07 基线 456 例 OK / 3 skip）
│   ├── scripts/              # stack.ps1、up.ps1、seed.ps1、drill-migrate.ps1 等
│   └── seed/                 # T-Box（bootstrap.ttl）与 SHACL 种子
├── doc/                      # 设计与记录（_design 编号设计/集成契约、_arch、_impl、_fsldm 等）
├── VERSION                   # 平台版本号
└── 上游 AWS COA 框架（保留，不参与本平台单机运行）
    ├── models/ smithy-generated/   # Smithy API 模型与生成物
    ├── infra/                      # AWS CDK 基础设施
    ├── packages/                   # control-plane、data-layer、ontology-engine、metric-service、vkg、mcp-server…
    └── libs/ connectors/ coa-skills/ external-docs/ scripts/ tests/
```

## Tech Stack

| Layer                  | Technology                                               |
| ---------------------- | -------------------------------------------------------- |
| Languages              | Python 3.12, TypeScript                                  |
| API Contracts          | Smithy → OpenAPI + Python interfaces + TypeScript client |
| IaC                    | AWS CDK (TypeScript)                                     |
| Frontend               | React + Cloudscape Design System                         |
| Package Management     | uv (Python), pnpm (TypeScript)                           |
| Monorepo Orchestration | Nx                                                       |
| Testing                | pytest (unit + integ)                                    |
| Linting                | ruff, mypy (strict)                                      |
| Codegen                | Smithy CLI (Java 17 + Gradle)                            |

## Contributing

This repository is published as a read-only mirror. We are not accepting pull requests at this time. You are welcome to report bugs and share feedback through GitHub Issues. See [CONTRIBUTING.md](CONTRIBUTING.md) for details including direction for Amazon employees.

## External Dependencies

This package depends on and may incorporate or retrieve a number of third-party
software packages (such as open source packages) at install-time or build-time
or run-time ("External Dependencies"). The External Dependencies are subject to
license terms that you must accept in order to use this package. If you do not
accept all of the applicable license terms, you should not use this package. We
recommend that you consult your company’s open source approval policy before
proceeding.

Provided below is a list of External Dependencies and the applicable license
identification as indicated by the documentation associated with the External
Dependencies as of Amazon's most recent review.

THIS INFORMATION IS PROVIDED FOR CONVENIENCE ONLY. AMAZON DOES NOT PROMISE THAT
THE LIST OR THE APPLICABLE TERMS AND CONDITIONS ARE COMPLETE, ACCURATE, OR
UP-TO-DATE, AND AMAZON WILL HAVE NO LIABILITY FOR ANY INACCURACIES. YOU SHOULD
CONSULT THE DOWNLOAD SITES FOR THE EXTERNAL DEPENDENCIES FOR THE MOST COMPLETE
AND UP-TO-DATE LICENSING INFORMATION.

YOUR USE OF THE EXTERNAL DEPENDENCIES IS AT YOUR SOLE RISK. IN NO EVENT WILL
AMAZON BE LIABLE FOR ANY DAMAGES, INCLUDING WITHOUT LIMITATION ANY DIRECT,
INDIRECT, CONSEQUENTIAL, SPECIAL, INCIDENTAL, OR PUNITIVE DAMAGES (INCLUDING
FOR ANY LOSS OF GOODWILL, BUSINESS INTERRUPTION, LOST PROFITS OR DATA, OR
COMPUTER FAILURE OR MALFUNCTION) ARISING FROM OR RELATING TO THE EXTERNAL
DEPENDENCIES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN
IF AMAZON HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. THESE LIMITATIONS
AND DISCLAIMERS APPLY EXCEPT TO THE EXTENT PROHIBITED BY APPLICABLE LAW.

| External Dependency | License | Source |
| ------------------- | ------- | ------ |
| owlready2 | LGPL-3.0 | https://pypi.org/project/owlready2/ |

## License

This project is licensed under the Apache License 2.0 — see [LICENSE](LICENSE) for details.
