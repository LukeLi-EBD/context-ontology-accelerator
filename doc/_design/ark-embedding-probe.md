# 火山方舟 Coding Plan Embedding 接口探测报告

- 报告时间：2026-11-05 11:46（Asia/Shanghai）
- 探测端点：`https://ark.cn-beijing.volces.com/api/coding/v3`（**全程仅使用 coding base，未调用 `/api/v3`**）
- API Key：`ark-ea35***e67d`（前 8 位 + 后 4 位掩码，明文不进本文件）
- 探测方式：纯只读 HTTP 调用（Python 3.12 `urllib`），**未改 `_impl` 代码、未写 `.env`、未重启任何容器**
- 请求总量：39 次（模型列表 2 次 + 单条 4 次 + 批量 5 次 + 失败路径 4 次 + 长文本 3 次 + 限速 20 次 + 字段回显 1 次），累计约 2.7 万 tokens

---

## 1. 结论先行

| 问题 | 结论 |
|---|---|
| coding plan 是否提供 embedding 接口 | **支持**（`POST /embeddings` 在 coding base 上返回 200） |
| 推荐模型 | **`doubao-embedding-vision-251215`**（实测唯一可用的 embedding 模型） |
| 输出维度 | **2048**（本地 BGE-M3 为 1024，维度不一致 → 必须全量重建） |
| 批次上限 | **单请求最多 10 条**（11 条起 400） |
| 单条延迟 | **P50 0.261s / P95 0.705s**（20 次连续请求实测） |
| 是否建议切换 | **建议作为"可选 provider"接入，不建议立刻设为默认**（理由与风险见第 7 节） |

关键前提：`/models` 列出的 9 个 embedding 模型里，**只有 `doubao-embedding-vision-251215` 通过了 coding plan 的权限校验**；所有 `*-text-*` 模型（含最新的 `doubao-embedding-large-text-250515`）调用即 `404 UnsupportedModel`。模型列表 ≠ 可用清单，**必须以真实调用为准**。

---

## 2. 探测项 1：`GET /models`

- 状态：`200`，耗时 `0.245s`，返回 `55` 个模型
- 响应无维度字段（`/models` 不暴露 `dim`），维度靠第 3 节实测

embedding 类模型（`id` 含 `embedding`）与可用性：

| 模型 id | domain / task_type | api_supported | 实测 `POST /embeddings` |
|---|---|---|---|
| `doubao-embedding-vision-251215` | Embedding / image_embedding, text_embedding | `embeddings/multimodal` | **200，2048 维** |
| `doubao-embedding-large-text-250515` | （无 domain 字段） | `embeddings` | 404 `UnsupportedModel` |
| `doubao-embedding-large-text-240915` | （无 domain 字段） | `embeddings` | 404 `UnsupportedModel` |
| `doubao-embedding-text-240715` | （无 domain 字段） | `embeddings` | 404 `UnsupportedModel` |
| `doubao-embedding-text-240515` | （无 domain 字段） | `embeddings` | 未测 |
| `doubao-embedding-vision-250615` | （无 domain 字段） | `embeddings/multimodal` | 未测 |
| `doubao-embedding-vision-250328` | （无 domain 字段） | `embeddings, embeddings/multimodal` | 未测 |
| `doubao-embedding-vision-241215` | （无 domain 字段） | `embeddings, embeddings/multimodal` | 未测 |

> 原始片段（`GET /models`，节选）：
> ```json
> {"id":"doubao-embedding-vision-251215","domain":"Embedding",
>  "task_type":["image_embedding","text_embedding"],
>  "api_supported":{"embeddings/multimodal":true},"status":"Published"}
> ```
> 说明：`/models` 是**账号可见模型全集**，不区分 plan 权益；是否属于 coding plan 由调用时的 `UnsupportedModel` 判定。

---

## 3. 探测项 2：`POST /embeddings` 单条

请求：

```json
{"model":"doubao-embedding-vision-251215","input":"本体论平台用于抽取事实与知识图谱构建。"}
```

响应：

| 项 | 值 |
|---|---|
| HTTP 状态 | `200` |
| 耗时 | `0.324s`（后续同文本复测 `0.423s`） |
| `data[0].embedding` 长度 | **2048** |
| `data[0].keys` | `embedding, index, object` |
| `usage` | `{"prompt_tokens":30,"total_tokens":30}` |
| 顶层 `model` 回显 | `doubao-embedding-vision`（**不带版本后缀**，适配器不可用回显做模型版本校验） |
| 顶层 keys | `created, id, data, model, object, usage` |

> 原始片段（embedding 数组截断）：
> ```json
> {"created":1793850257,"id":"021793850257067c280e...",
>  "data":[{"embedding":[0.04345703125,-0.004913330078125,0.017578125,...],
>           "index":0,"object":"embedding"}],
>  "model":"doubao-embedding-vision","object":"list",
>  "usage":{"prompt_tokens":30,"total_tokens":30}}
> ```

文本可用性：该模型是 multimodal 模型，**纯文本 input 正常工作**，返回 2048 维文本向量。

---

## 4. 探测项 3：批次上限

同一请求放入 N 条中文短文本（每条约 8 汉字）：

| N | HTTP | 耗时 | `data` 条数 | `usage.prompt_tokens` | 备注 |
|---|---|---|---|---|---|
| 1 | 200 | 0.344s | 1 | 32 | — |
| 4 | 200 | 0.548s | 4 | 128 | — |
| **10** | 200 | 0.888s | 10 | 320 | **上限档** |
| 32 | **400** | 0.132s | — | — | 见下 |
| 64 | **400** | 0.157s | — | — | 见下 |

> 命中上限的原始错误（N=32）：
> ```json
> {"error":{"code":"InvalidParameter","param":"input","type":"BadRequest",
>  "message":"The parameter `input` specified in the request are not valid: Embeddings API input limit exceeded: max 10, got 32. Request id: 021793850268492ef74dd90a5750f77dc784a69dff0f3adf497c0"}}
> ```
> N=64 除 `got 64` 外完全一致。

**结论：`batch_max = 10`，硬上限、服务端显式拒绝、message 可直接解析出上限值与实际值。** 未观察到 429/413。

---

## 5. 探测项 4：失败路径

| 场景 | 请求 | HTTP | `error.code` | `error.message`（原文） | 是否可区分 |
|---|---|---|---|---|---|
| 错误模型名 | `model:"doubao-embedding-nonexistent-xyz"` | **404** | `UnsupportedModel` | The requested model does not support the coding plan feature. Please refer to the documentation at https://www.volcengine.com/docs/82379/1925114 to select a compatible model. | 是（与参数错误分离） |
| 空字符串 | `input:""` | **400** | `InvalidParameter` | The parameter `input` specified in the request are not valid: input could not be empty. | 是（`param:"input"`） |
| 空数组 | `input:[]` | **400** | `MissingParameter` | The request failed because it is missing `input` parameter. | 是（空数组被当作缺参） |
| 超长文本 | `input:"测"×8192` | **200** | — | — | 未报错，见下 |

超长文本实测（同一模型，`"测"` 重复）：

| 字符数 | HTTP | prompt_tokens | 维度 | 耗时 |
|---|---|---|---|---|
| 2048 | 200 | 2067 | 2048 | 0.324s |
| 4096 | 200 | 4115 | 2048 | 0.515s |
| **8192** | **200** | **8211** | 2048 | 0.832s |

**未观察到截断或报错**：8192 字符（≈8211 tokens）全量计入 `prompt_tokens` 并通过。单输入 token 上限大于 8211，具体值**未取到**（按要求不继续加长以免产生费用）。适配器仍需自行按 chunk 预算切分，不能依赖服务端截断。

---

## 6. 探测项 5：计费口径

| 判据 | 实测/文档 | 结论 |
|---|---|---|
| 响应 `usage` 字段 | 仅 `prompt_tokens` / `total_tokens`，无 `cached_tokens`、无金额字段 | 计量单位是 **token**，不是"按请求次数" |
| 响应头 | 仅有 `x-request-id`、`x-client-request-id`、`x-envoy-upstream-service-time`，**无计费/配额头** | 无用量回执 |
| 计费单价 | 响应与 `/models` 均无价格字段；官方文档未在本次探测中读取 | **未确认** |
| 是否计入 coding plan 额度 | coding plan 为订阅制，embedding 是否包含在套餐内、是否单独计费 | **未确认**（风险项，见第 7 节） |

> 说明：批量 N=10 的 `prompt_tokens=320` 恰为 N=1 的 10 倍（32×10），说明 token 按文本累加计费，**批处理不省 token**，只省请求数/延迟。

---

## 7. 探测项 6：配额与限速

连续 20 次单条请求，间隔 100ms：

| 指标 | 值 |
|---|---|
| 成功次数 | **20/20（200）** |
| 429 次数 | **0** |
| P50 | **0.261s** |
| P95 | **0.705s** |
| min / max | 0.208s / 0.705s |
| mean | 0.288s |

延迟序列（秒）：`0.233, 0.223, 0.267, 0.208, 0.338, 0.337, 0.255, 0.304, 0.289, 0.219, 0.705, 0.327, 0.211, 0.242, 0.220, 0.313, 0.336, 0.217, 0.239, 0.273`

- 20 次 @100ms 间隔**未触发任何限流**；真实速率上限 **未取到**（不做更高并发以免浪费）。
- 响应无 `x-ratelimit-*` 头，配额只能从 429 反推，当前证据只支持"≥20 次/2 秒不触发"。

---

## 8. 失败码表（供适配器映射）

| 内部错误码建议 | 触发条件 | HTTP | 上游 `code` | 判定依据 |
|---|---|---|---|---|
| `E_EMBED_MODEL_NOT_ENTITLED` | 模型不在 coding plan 权益内 | 404 | `UnsupportedModel` | message 含 "does not support the coding plan feature" |
| `E_EMBED_INPUT_EMPTY` | 单条空字符串 / 列表含空串 | 400 | `InvalidParameter` | message 含 "input could not be empty" |
| `E_EMBED_INPUT_MISSING` | `input:[]` 或缺失 | 400 | `MissingParameter` | message 含 "missing `input` parameter" |
| `E_EMBED_BATCH_TOO_LARGE` | N>10 | 400 | `InvalidParameter` | message 含 "max 10, got N"（可正则解析上限） |
| `E_EMBED_RATE_LIMITED` | 触发限流 | 429 | 未取到 | 本次未触发 |
| `E_EMBED_AUTH` | key 无效/无权限 | 401/403 | 未取到 | 本次未出现，**未验证** |

> 401/403 未出现，因此未按"立刻停止"条件中断探测；`/api/v3` 全程未被调用。

---

## 9. 若切换：适配器要求

配置键（沿用现有 provider 配置结构，全部可通过 env 注入）：

| 键 | 建议值 | 依据 |
|---|---|---|
| `EMBEDDING_BASE_URL` | `https://ark.cn-beijing.volces.com/api/coding/v3` | 唯一允许的 base；`/api/v3` 会产生额外计费，适配器应做**前缀断言**拒绝 `/api/v3` |
| `EMBEDDING_MODEL` | `doubao-embedding-vision-251215` | 唯一实测可用 |
| `EMBEDDING_DIM` | `2048` | 实测 `data[0].embedding` 长度 |
| `EMBEDDING_BATCH_MAX` | `10` | 服务端硬上限 |
| `EMBEDDING_TIMEOUT` | `30s`（单条）/ `60s`（批量） | 实测最长 0.888s，留足网络抖动余量 |
| `EMBEDDING_RETRY` | `max=2`，仅重试 429/5xx，指数退避 0.5s/1.5s；400/404 **不重试** | 400/404 为确定性错误 |
| `EMBEDDING_API_KEY` | 仅写本地未跟踪 `.env`，汇报掩码 | 既有安全约束 |

适配器实现约束：

1. 校验响应 `model` 回显只有 `doubao-embedding-vision`（无版本后缀），**不能**用回显做版本一致性校验，需在配置层固定完整 id。
2. 批量结果按 `data[i].index` 回排，不要依赖顺序。
3. `usage.prompt_tokens` 逐请求累加落账，用于用量统计（计费口径未确认，仅作内部计量）。
4. 超长文本不得依赖服务端截断（实测 8211 tokens 不截断），chunk 切分仍在入库侧完成。
5. 写入侧强校验：`dim != 2048` 直接拒写（复用现有分区契约）。

**1024 → 2048 全量 reindex 估算（现有 3077 chunks）**：

| 项 | 值 |
|---|---|
| 请求数 | `ceil(3077 / 10)` = **308 次** |
| 单次耗时（10 条短文本实测） | 0.888s |
| 纯请求耗时下限 | 308 × 0.888s ≈ **274s（约 4.6 min）** |
| 按 1.5–2.5s/请求保守估算 | **462–770s（约 8–13 min）** |
| 对照本地 BGE-M3（实测 0.63–1.30 chunks/s） | 3077 chunks ≈ **40–82 min** |
| 数据量假设 | 真实 chunk 远长于探测文本（探测条 ~8 汉字 / 30 tokens），实际单请求按 500–800 tokens 估算，延迟会上升，故给出区间而非点值 |

> 以上为按实测吞吐的线性外推，**未做实盘 reindex**，不得当作已验证结论。

---

## 10. 是否建议切换

**建议：接入为可选 provider（灰度），暂不设为默认。** 理由与风险：

支持切换的理由：
1. 延迟数量级差异明显：外部 0.26s（P50）vs 本地 18–26s/请求，批量 10 条 0.888s；CPU 626–645% 的占用可直接释放。
2. 现有 embedding 分区（模型名+维度）与 `reindex` 已就绪，切换不需要改业务语义；旧 1024 维分区可原样保留，回退零成本。
3. 错误语义清晰，404/400 可精确区分，适配器映射成本低。

必须正视的风险（按严重度排序）：
1. **计费与配额未确认**：coding plan 是否包含 embedding 用量、单价多少、是否会消耗 chat 额度，全部**未取到**，不能承诺"免费/廉价"。这是**阻塞默认切换**的唯一硬条件。
2. **权益脆弱**：可用模型只有 1 个，且是 multimodal 模型；`*-text-*` 全被拒。一旦 plan 调整，默认 provider 会整体失效。
3. **数据出网**：所有 chunk 文本将发往第三方，与"单机自足"基线冲突，需业务侧确认。
4. **质量未验证**：2048 维 vision 模型的中文检索效果未做离线评测（recall/MRR 对比 BGE-M3），不能假定"维度更高=效果更好"。
5. **维度变更成本**：1024→2048 需全量重建（8–13 min 外部 vs 40–82 min 本地），虽短但需在维护窗口执行并跑三条契约测试。

落地顺序建议：① 先确认计费/配额口径（文档或控制台账单）→ ② 用现有 3077 chunks 抽样做检索质量对比 → ③ 以 `EMBEDDING_PROVIDER=ark` 灰度接入、默认仍 `local-bge` → ④ 质量与成本达标后再切换 `embedding.active_model` 指针。

---

## 11. 纪律声明

- 全程只读 HTTP 探测，**未修改任何 `_impl` 代码、未写 `.env`、未重启容器、未调用 `/api/v3`**。
- 未出现 401/403，未触发"立刻停止"条件。
- 未取到的项已明确标注"未取到/未确认"：embedding 单价、coding plan 是否含 embedding 额度、真实限流上限、单输入 token 上限、4 个未测 embedding 模型的可用性。
- 探测脚本与原始响应日志为临时中间产物，存放于系统临时目录（`%TEMP%\ark_probe*`），未写入工作区。
