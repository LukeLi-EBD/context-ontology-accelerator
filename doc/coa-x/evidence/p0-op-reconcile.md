# P0-05 op 对账（四视图）

- 基线：`39bf8919`
- 脚本：[reconcile_control_plane_ops.py](../tools/reconcile_control_plane_ops.py)
- 已登记差异表：[reconcile-known-gaps.json](../tools/reconcile-known-gaps.json)
- 本次快照：[op-reconcile-39bf8919.csv](./op-reconcile-39bf8919.csv)（160 行数据 + 1 行表头）
- 执行命令：

```powershell
python doc/coa-x/tools/reconcile_control_plane_ops.py --quiet
python doc/coa-x/tools/reconcile_control_plane_ops.py --csv doc/coa-x/evidence/op-reconcile-39bf8919.csv --quiet
```

## 四个视图的来源

| 列 | 来源 | 解析方式 |
| --- | --- | --- |
| `model` | `models/src/main/smithy/*.smithy` | `@http(method, uri)` + `operation X` |
| `mounted` | 同名文件里的 `service { operations: [...] }` | 每个 op 必须出现在至少一个 service 列表 |
| `command` | `smithy-generated/*-typescript-client/src/commands/XCommand.ts` | 文件存在即 yes |
| `bridge` | `doc/coa-x/tools/coa_api_local.py` 的 `ROUTES` + `path == "..."` 特判 | 路径模板精确匹配（不区分 HTTP 动词） |

`bridge` 是路径级匹配：本地桥按路径分发、不按动词分发，所以 `yes` 不能证明动词也一致。`DataLayerService` 的 op 标为 `n/a`——本地桥只前置控制面，不代理 data-layer。

## 本次实测（2026-11-11）

```text
model_ops        155
control_plane_ops 147
data_layer_ops   8
mounted_ops      155
commands         155
bridge_routes    146
rows             160
gaps             6
registered_gaps  6
unregistered_gaps 0
exit=0
```

即：模型 op、service 挂载、生成命令三张表都是 **155**，逐 op 一致；桥覆盖 146 条路径（147 条控制面 op 中 146 条命中，`UploadOntology` 未接；另有 5 条 `/namespaces/...` 兜底路由未契约化）。6 条差异全部有名字、owner、到期点，逐条如下：

| 差异 | 类型 | owner | 到期 | 原因 |
| --- | --- | --- | --- | --- |
| `UploadOntology` | 无本地桥路由 | bridge | coa-x-m1 | 本地走 presign + `/_local/objects`，直传 op 未接；生产由 ontology-engine / data-layer 承接 |
| `/namespaces/{namespaceId}/embeddings` | 桥多出（未契约化） | bridge | coa-x-m1 | 本地兜底鉴权路由 |
| `/namespaces/{namespaceId}/embeddings/batch` | 桥多出（未契约化） | bridge | coa-x-m1 | 本地兜底鉴权路由 |
| `/namespaces/{namespaceId}/embeddings/by-ontology/{ontologyId}` | 桥多出（未契约化） | bridge | coa-x-m1 | 本地兜底鉴权路由 |
| `/namespaces/{namespaceId}/induce/datasources` | 桥多出（未契约化） | bridge | coa-x-m1 | 本地兜底鉴权路由 |
| `/namespaces/{namespaceId}/validate/jobs` | 桥多出（未契约化） | bridge | coa-x-m1 | 本地兜底鉴权路由 |

退出码规则：有未登记差异返回 1，全部登记返回 0。上面 6 条都在 `reconcile-known-gaps.json` 中，所以本轮 exit=0；删掉登记条目就会重新变红，登记不是免死金牌。

可重复性：同一命令连跑两次，输出 CSV 的 SHA-256 相同（`B5C5C7F4A62FB84BC66067D4C06989220007159F67FF0CE41C09F0B3D408E617`），与提交的快照一致。

## 未纳入的两类差异

1. **HTTP 动词**：桥不按动词分发，脚本只能证明路径存在。要证明动词一致，需要另跑一次真实请求（P0 演示清单里只覆盖读接口）。
2. **非业务路径**：`/health`、`/system-health`、`/local/auth/*` 只用于补 `bridge` 列，不参与“桥多出”统计；后者只统计 `/namespaces/` 前缀，避免把本地对象存储/鉴权口子算成业务路由。
