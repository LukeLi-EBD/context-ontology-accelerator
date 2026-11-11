# P1-15 只读镜像证据（8080）与 P1-16 取数路径

- 采集时间：2026-11-11 11:43–11:46 CST
- 对象：`agent-platform-api`（`127.0.0.1:8080`，镜像 `agent-platform:0.1-s6-readonly`）
- 方式：GET / `docker inspect` / 容器内只读 `grep`；写接口只发了 1 次按设计应被拒绝的 `POST /facts` 探针
- 未改：未重启容器、未改 DSN、未动 `READONLY` 哨兵、未碰 8082 与 5944 的写入

## 1. `GET /readonly`

```
HTTP/1.1 200 OK
server: uvicorn
content-type: application/json

{"mode":"read_only","since":"2026-11-10T21:26:39+00:00","sentinel":"/data/READONLY","auditFile":"/data/audit/readonly-20261111.jsonl","blockedToday":1}
```

判据：200 **PASS**。响应体是 5 字段扁平 JSON（`mode` / `since` / `sentinel` / `auditFile` / `blockedToday`），`mode=read_only`。

## 2. OpenAPI 路径数

```
GET /openapi.json → 200，112287 bytes
info: {"title":"Platform Kernel","version":"0.1.0"}
paths（唯一路径）: 139
operations（path × method）: 149
```

判据：**149 对不上"路径数"，对得上"操作方法数"**。

- 唯一路径 139 条；
- 按 `path + method` 展开是 **149** 个操作（GET/POST/PUT/PATCH/DELETE 计数之和），由脚本从 `/openapi.json` 解析得出，未参考任何文档；
- 若计划里写的是"149 个路径"，口径应改为"149 个 operation / 139 个 path"。

## 3. 冻结期间写接口实证 `POST /facts`

请求：`POST /facts`，body `{"subject":"urn:runbook:readonly-probe","predicate":"urn:runbook:probe","object":"probe-1"}`

实际响应：

```
HTTP/1.1 409 Conflict
x-platform-mode: read-only
x-audit-id: c4a03c9559694615

{"error": {
  "code": "Conflict",
  "provider": "platform",
  "providerCode": "E_PLATFORM_READ_ONLY",
  "message": "platform is in read-only freeze; writes are disabled until the freeze is lifted",
  "retryable": true,
  "details": {"method": "POST", "path": "/facts", "mode": "read_only",
              "auditId": "c4a03c9559694615", "since": "2026-11-10T21:26:39+00:00"}
}}
```

判据：状态码 **409**、`providerCode` **`E_PLATFORM_READ_ONLY`**，原文 `message` 为 `platform is in read-only freeze; writes are disabled until the freeze is lifted`。**PASS**

旁证（同一时刻前后）：

```
POST 前  /readonly.blockedToday = 1
POST 后  /readonly.blockedToday = 2      ← 被计数为"已拦截"，不是"已写入"
POST 后  GET /facts?limit=1 → {"items":[],"count":0,"conflicts":[]}   ← 探针没有落库
```

## 4. 现网配置（只读采集）

### 4.1 镜像

| 项 | 值 |
| --- | --- |
| `Config.Image` | `agent-platform:0.1-s6-readonly` |
| Image ID | `sha256:f954e40c0c36744f3c8ecc24890c98ba876624affb280c7f29f85cd77c3431f8` |
| `StartedAt` | `2026-11-11T00:39:56.6464872Z` |
| `RestartCount` | `0` |

### 4.2 DSN 三处（口令打码）

| # | 位置 | 值 |
| --- | --- | --- |
| 1 | 挂载配置 `/data/platform.yaml:10` → `database.url` | `postgresql://platform:platform_dev@postgres:5432/platform`（挂载点 `D:/agentABC/data` → `/data`，**ro=true**） |
| 2 | 环境变量 `PLATFORM__DATABASE__URL` | `postgresql://platform:***@postgres:5432/platform`（真实口令，已打码） |
| 3 | 环境变量 `POSTGRES_PASSWORD` + `POSTGRES_PORT` | `POSTGRES_PASSWORD=***`、`POSTGRES_PORT=5432`（与 1/2 成对） |

其他相关环境变量：`PLATFORM_READ_ONLY=0`、`PLATFORM_READONLY_AUDIT_DIR=/data/audit`、`PLATFORM_PORT=8080`、`PLATFORM__RUNTIME__MODE=learn`。

观察（事实）：`PLATFORM_READ_ONLY=0`，但 `/readonly` 仍是 `read_only` —— 冻结由挂载的哨兵文件 `/data/READONLY` 驱动，不是这个 env 开关。

### 4.3 这个镜像实际连的库

`postgres:5432` 落到容器 `agent-platform-postgres`（库 `platform`）。实测行数：

```
ontology_version=1908   ontology_proposal=1313   ontology_event=10134
```

对照本演示用的接管库（`coa-takeover-pg`，5944）：`1910 / 1314 / 10137`。两者相差 2 / 1 / 3 行，**不是同一个库**。

## 5. P1-16 三个数的取数路径

| 数 | 取数路径 | 结果 |
| --- | --- | --- |
| 1,910 | `GET :8210/namespaces/{ns}/ontologies/{oid}/versions` → `total`；并用 `select count(*) from platform.ontology_version`（5944）对账 | 一致 = 1910 |
| 1,314 | `GET :8210/namespaces/{ns}/ontologies/{oid}/proposals` → `count`；库 `platform.ontology_proposal`（5944） | 一致 = 1314 |
| 10,137 | **页面/接口未确认**；只在库里找到等值项：`select count(*) from platform.ontology_event`（5944）= 10137 | 仅 SQL 证据 |

补充事实：

- 演示桥 `:8210` 只暴露 `/system-health`（需要 bearer token），其响应里没有版本/提案/事件计数；没有 `/ui/api/overview`。
- 8080 的 `/ui/api/overview` 存在，但它查的是 `5432` 库：`totalVersions=1908`，事件等数字对应 `10134`。**如果 P1-16 的页面是 8080 那套 UI，它不会显示 1,910 / 1,314 / 10,137。**
- 本演示的 web UI 未起（见 [luke-demo-runbook.md](luke-demo-runbook.md) 7.4），所以三个数**只有接口/SQL 证据，没有页面渲染证据**。

## 6. P1-16 另两项

- 「旧镜像 + 旧 DSN」成对回退演练：**无，需另做**。未做，不做演练性回退。
- 三处 DSN 同窗落地记录：**无，需另做**。本轮只采集了 4.2 的三处现值，没有"同一时间窗把三处一起改并验证"的记录。

## 7. 判据汇总

| # | 项 | 本轮 |
| --- | --- | --- |
| 1 | `/readonly` 200 + body 形状 | PASS |
| 2 | OpenAPI 路径数 | 唯一 path 139 / operation 149（149 是操作数，不是路径数） |
| 3 | `POST /facts` → 409 + `E_PLATFORM_READ_ONLY` | PASS（audit 计数 1→2，未落库） |
| 4 | DSN 三处 + 镜像 tag | 已采集（见 4.1 / 4.2） |
| 5 | 页面 1,910 / 1,314 / 10,137 | 1910、1314 有接口+SQL；10137 仅 SQL，页面未确认 |
