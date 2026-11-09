# data/（运行时目录，内容不入库）

compose 把 `platform/data` 挂载到容器 `/data`，平台默认读 `/data/platform.yaml`。
本目录在仓库中只保留这份说明；实际内容由使用者本地生成，`.gitignore` 已忽略 `data/*`。

## 目录结构与放置方式

| 路径 | 必需 | 说明 |
| --- | --- | --- |
| `data/platform.yaml` | 是 | 从 `platform/platform.example.yaml` 复制后填入真实口令/地址 |
| `data/blobs/` | 是 | 文件系统 CAS 大件存储；启动时若不存在，`/readyz` 会报 `blobs directory missing`，先建空目录 |
| `data/tmp/` | 是 | 解析临时目录 |
| `data/models/bge-m3/` | 是（learn 档） | BGE-M3 模型，2.14 GB，只读挂载给 TEI；未放置时 embedding 容器起不来，检索退化为仅词法 |
| `data/ontology/bootstrap.ttl` | 否 | 初始本体；`ontology.init_mode=watch` 时按 30s 轮询 |
| `data/shapes/` | 是（物化时） | SHACL shapes 目录，`reasoning.shapes_dir` 指向此处 |
| `data/jobs/rdfs/` | 否 | RDFS 一次性作业的 `in.ttl` / `out.nt` |
| `data/exports/` | 否 | 审计导出 NDJSON |
| `data/logs/` | 否 | 运行日志（也可用 `platform/logs/`，二者均被忽略） |

## BGE-M3 离线拷贝

模型目录需包含 `config.json`、`pytorch_model.bin`（约 2.17 GB）、`colbert_linear.pt`、
`sentencepiece`/`tokenizer` 相关文件等 TEI 可识别结构，总约 2.14 GB：

```powershell
# 从已有机器离线拷贝（保持目录结构，路径固定为 data/models/bge-m3）
robocopy D:\agentABC\_impl\data\models D:\repo\platform\data\models /E
```

模型体积原因不入库，仓库不提供下载脚本，避免引入额外依赖。
