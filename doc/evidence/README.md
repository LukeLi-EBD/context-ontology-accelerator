# 验收证据索引（doc/evidence）

本目录是**被 git 跟踪**的验收证据目录。2026-11-06 之前验收日志写在 `platform/logs/`，
该目录被 `.gitignore` 排除，第三方按文档路径无法复核；从 2026-11-06 起，两套验收脚本
都会把 transcript 固定写到这里。

## 命名与判定

| 脚本 | 文件名 | 说明 |
|---|---|---|
| `platform/tests/acceptance.ps1`（S0–S13） | `acceptance-s0s13-<project>-<yyyyMMdd-HHmmss>-<git sha>.log` | 43 项固定检查 + smoke 自检；`skipped>0` 即不通过 |
| `platform/scripts/acceptance-s14.ps1`（S14 全量 unittest） | `acceptance-s14-<project>-<yyyyMMdd-HHmmss>-<git sha>.log` | discovered/executed 自检；`skipped>0` 即不通过 |

判定规则与限制见 [69-验收可证明性与栈隔离](../_design/69-验收可证明性与栈隔离-2026-11-06.md)。

## 新目录下的运行记录

| 时间（本机） | 文件 | 结论 |
|---|---|---|
| 2026-11-06 23:36 | `acceptance-s14-20261106-233605-6ca8561.log` | 脚本自身缺陷（空 `--exclude` 参数）导致 runner 协议失败，非业务结论；已修复 |
| 2026-11-06 23:37 | `acceptance-s14-20261106-233619-6ca8561.log` | 共享栈全量：366 discovered / 366 executed / 366 passed / 0 skipped，exit 0 |
| 2026-11-06 23:38 | `acceptance-s0s13-20261106-233802-6ca8561.log` | 共享栈：API 容器被并行会话重建，`readyz status=0`，exit 1（环境干扰） |
| 2026-11-06 23:47 | `acceptance-s0s13-20261106-234255-50368c6.log` | 共享栈：`smoke-s5 exit=137`，容器被并行会话重建，exit 1（环境干扰） |
| 2026-11-06 23:52 | `acceptance-s0s13-20261106-234834-45ae42c.log` | 共享栈：43 passed / 0 failed / 0 skipped，exit 0 |
| 2026-11-06 23:53 | `acceptance-s0s13-20261106-235319-45ae42c.log` | 共享栈复跑：43 passed / 0 failed / 0 skipped，exit 0 |
| 2026-11-07 00:00 | `acceptance-s0s13-20261107-000031-93b7f7c.log` | 共享栈锁占用注入：`E_BUILD_CONFLICT`（holder=`SIMULATED\other-session#999`），exit 75，未执行任何 smoke |
| 2026-11-07 00:14 | `acceptance-s0s13-platform-acceptance-20261107-001411-8b2d6a7.log` | 隔离栈首次启动：入口自检失败（`compose` 子命令参数错误），exit 1；脚本已修复 |
| 2026-11-07 00:15 | `acceptance-s0s13-platform-acceptance-20261107-001506-8b2d6a7.log` | 隔离栈缺 embedding：三项 `E_EMBED_UNAVAILABLE`，exit 1（环境缺口） |
| 2026-11-07 00:15 | `acceptance-s0s13-platform-acceptance-20261107-001536-8b2d6a7.log` | 隔离栈补起 embedding 前：`smoke-s13` 失败后中止，exit 1 |
| 2026-11-07 00:33 | `acceptance-s0s13-platform-acceptance-20261107-003328-82244bb.log` | **隔离栈终态**：43 passed / 0 failed / 0 skipped，exit 0 |
| 2026-11-07 00:37 | `acceptance-s14--20261107-003732-b2bcd8d.log` | 脚本参数块 UTF-8 无 BOM 被 PS 5.1 误读，项目名为空导致协议失败；已加 BOM 修复 |
| 2026-11-07 00:39 | `acceptance-s14-platform-acceptance-20261107-003809-b2bcd8d.log` | **隔离栈全量**：381 discovered / 378 executed / 360 passed / 5 failed / 13 errors / 0 skipped，exit 2（真实失败见下） |
| 2026-11-07 00:40 | `acceptance-s0s13-platform-acceptance-20261107-004023-b2bcd8d.log` | 锁占用注入演练：`E_BUILD_CONFLICT`，exit 75，未执行任何 smoke |
| 2026-11-07 00:47 | `acceptance-s0s13-platform-acceptance-20261107-004430-ea7c94f.log` | **隔离栈终态复跑**（脚本最后一次改动后）：43 passed / 0 failed / 0 skipped，exit 0，锁正常释放 |

隔离栈 S14 的失败定性（**未修复、未跳过、未删除用例**）：

- 环境夹具缺失（隔离栈无共享栈历史数据）：`ont-11f92ebb3326` 缺失 → 3 个 answer 用例 FAIL + `AnswerableTests.setUpClass` ERROR（连带 3 个用例未执行）；85 词表未导入 → 2 个 FAIL；`fuseki:3030` 不可达 → 1 个 ERROR。
- 并行代码线与测试契约不一致（真实缺陷，非本次脚本改动引入）：`FakeOntology.publish/rollback_to` 不接受新参数 `expected_version_id`（4 个 ERROR）；`MetricCompiler.execute()` 缺必填 `data_source`（7 个 ERROR）。

## 历史日志（仓库内但被 .gitignore 排除，仅索引，不复制、不伪造内容）

路径均为 `platform/logs/`。这些文件未入版本库，第三方 checkout 后不可见，因此只登记
路径、时间与当时脚本自报汇总；内容以现场文件为准。

| 文件 | 最后写入（本机） | 脚本自报汇总 |
|---|---|---|
| `coa-integrate-acceptance.log` | 2026-11-05 22:59 | passed=40 failed=3 skipped=0 |
| `coa-integrate-acceptance2.log` | 2026-11-05 23:04 | passed=43 failed=0 skipped=0 |
| `q3-acceptance.log` | 2026-11-06 00:04 | passed=43 failed=0 skipped=0 |
| `q7-acceptance.log` | 2026-11-06 00:34 | passed=43 failed=0 skipped=0 |
| `q8-acceptance.log` | 2026-11-06 01:33 | passed=43 failed=0 skipped=0 |
| `t12-acceptance.log` | 2026-11-06 02:21 | passed=43 failed=0 skipped=0 |
| `t13-acceptance.log` | 2026-11-06 02:36 | passed=43 failed=0 skipped=0 |
| `t14-acceptance.log` | 2026-11-06 02:48 | passed=43 failed=0 skipped=0 |
| `t15-acceptance.log` | 2026-11-06 03:19 | passed=43 failed=0 skipped=0 |
| `t16-acceptance.log` | 2026-11-06 03:37 | passed=43 failed=0 skipped=0 |
| `merge-acceptance.log` | 2026-11-06 03:46 | passed=43 failed=0 skipped=0 |
| `06216c1-acceptance.log` | 2026-11-06 04:09 | passed=42 failed=1 skipped=0 |
| `066216c1-acceptance-rerun.log` | 2026-11-06 04:15 | passed=43 failed=0 skipped=0 |
| `s14h03a-acceptance.log` | 2026-11-06 04:22 | passed=43 failed=0 skipped=0 |
| `s14h03-final-acceptance.log` | 2026-11-06 04:29 | passed=43 failed=0 skipped=0 |
| `s14h-governance-acceptance.log` | 2026-11-06 04:50 | passed=43 failed=0 skipped=0 |
| `s14h-governance-final-acceptance.log` | 2026-11-06 04:55 | passed=43 failed=0 skipped=0 |
| `acceptance-20261106.log` | 2026-11-06 05:21 | passed=43 failed=0 skipped=0 |

历史日志没有 `git sha`、没有项目名，也没有 S14 全量记录；这正是“全绿不具证明力”
的原因之一，不能作为本次全量结论的替代证据。
