# P0-15 测试基线命名

- 基线：`39bf8919`
- 结论：**82 条可复现失败已全部修复；第 83 条无法命名，按开口项登记，不硬凑。**
- 与本文件配套的证据目录：`doc/coa-x/evidence/`

## 1. 83 vs 82 的现状

`19-测试基线对账与隐患立项.md` §1.1 记录的原文是：

> 基线汇总记 83 条，本轮可复现 82 条，差 1 条未能复现，待补测试名或基线日志。

本次从 git 侧核查：

```text
$ git log --all --oneline -S "基线汇总记 83"
7e756e76 test: 修复测试基建与打包声明，改根因不改业务行为
```

“83”这个数字**第一次出现在仓库里，就是那条修复提交本身**；之前没有任何基线日志、CSV 或测试名清单进入 git。也就是说，83 的原始条目从未被提交过，当前仓库没有材料把它逐条还原。

## 2. 82 条的构成（照 19 号文，不改口径）

| 归类 | 条数 | 具体 |
|---|---:|---|
| context-manager 测试跟不上端口层 | 70 | `test_config.py` 69 + `test_factory.py` 1 |
| ontology-engine 契约变更 | 3 | `test_ingest_from_s3_states.py`，`resolve()` 返回值形状改为 `.instance` |
| local-providers 实现噪声 | 1 | 404 响应体多出 `providerCode/providerMessage: null` |
| tests/unit 基建 | 7 | 版本清单 1、守卫 1、README `platform/` 1、镜像路径 1、Lambda 声明 1、源码树遍历 2 |
| 环境限制 | 1 | `test_client_ports.py::test_query_executor_requires_its_dsn_instead_of_falling_back`（`ModuleNotFoundError: platform_core`） |
| **合计** | **82** | 82 条都有测试名与根因 |

修复提交 `7e756e76` 已把这 82 条全部收掉；本文件不再重复修。

## 3. 本次实测（2026-11-11，`39bf8919`）

命令（共享 venv + 指向本 worktree 的 `PYTHONPATH`）：

```powershell
$paths = (Get-ChildItem packages -Directory | % { Join-Path $_.FullName 'src' }) +
         (Get-ChildItem libs -Directory | % { Join-Path $_.FullName 'src' })
$env:PYTHONPATH = ($paths -join ';')
python -m pytest packages/context-manager/tests/unit/test_config.py `
                 packages/context-manager/tests/unit/test_factory.py -q
```

连续两次结果一致：

```text
80 passed in 1.88s
80 passed in 1.72s
```

这 80 条覆盖了 82 条里最大的 70 条簇（69 + 1），两次跑数字一致，满足“连续两次跑结果一致”。

同一基线上另外两项实测（只报实际跑到的，不推断）：

| 命令 | 结果 | 说明 |
| --- | --- | --- |
| `pytest tests/unit -q`（补 `smithy-generated/control-plane-python-server` 到 `PYTHONPATH`） | **310 passed / 308 failed** | Windows 无 `sh`，仓库级 suite 在本机不是可用基线；不代表 83 条 |
| `pytest packages/context-manager/tests/unit -q`（整个目录） | 收集失败 | `ModuleNotFoundError: graphrag_toolkit`，本机依赖缺失，非产品缺陷 |

因此本文件**只把 `test_config.py + test_factory.py` 的 80 条**作为可重复基线；其余 12 条（3+1+7+1）沿用 19 号文的记录，未在本轮重新逐条跑，不写成“已复测”。

## 4. 显式开口项 `BASE-83-UNNAMED`

- **为什么不修**：83 的原始条目没有任何日志进入 git（`git log -S` 只有记录该数字的修复提交本身），无法用现有材料命名第 83 条；为凑数字新增或拆分测试已被 19 号文明确禁止。
- **影响面**：只影响“83/83 全命名”这句话能否成立；不影响“82 条可复现失败已修复”的结论，也不影响本文件的 80 条可重复基线。
- **期限**：不晚于下一个 tag。到点若仍无基线日志，口径正式改为“82 条可复现 + 1 条不可追溯”，不再保留 83 的说法。
- **谁来还**：质量线 / 测试基线维护人（当前台账里 19 号文的维护者）。
- **关闭条件**：拿到原始 83 条日志或测试名清单，补进本文件第 2 节；否则按上面的期限降级口径。
