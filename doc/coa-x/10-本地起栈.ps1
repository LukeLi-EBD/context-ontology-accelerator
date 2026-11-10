<#
.SYNOPSIS
  COA 原版本地栈一键启停。

.DESCRIPTION
  本脚本只管理下面这些东西（其余一律不碰）：

    容器 coa-local-pg        127.0.0.1:5444  pgvector/pgvector:pg18-trixie，库 platform + serve_local
    容器 coa-local-oxigraph  127.0.0.1:7878  oxigraph/oxigraph:0.5.7，数据卷 coa-local-oxigraph-data
    容器 coa-local-reasoner  127.0.0.1:7879  agent-reasoner:0.1-s5（ROBOT 1.9.6 + ELK + Jena riot）
    进程 coa-api-local       127.0.0.1:8099  doc/coa-x/tools/coa_api_local.py
    进程 coa-ontology-local  127.0.0.1:8101  doc/coa-x/tools/coa_ontology_local.py
    进程 coa-serve-local     127.0.0.1:8091  run_local.py context-manager（Query / KBSearch 的上游）
    进程 coa-web-5173        127.0.0.1:5173  vite --config vite.dev-local.config.mjs（packages/web-app）

  5173 **必须**用 packages/web-app/vite.dev-local.config.mjs 起（@auth 别名到
  .dev-local/auth-stub，给固定本地 token）。默认 vite.config.ts 走真实 OIDC，
  本地没有 IdP 时前端会报 "Auth token is empty."，所有 apiClient 页面全空。

  本体生命周期（versions/proposals/publish/rollback）不再单独占端口：8099
  进程内直接装配 platform_core 的 ASGI 应用，见 coa_api_local.py 的 KERNEL。

  不管理：8080/8082 验收栈、8081 BGE 嵌入服务（只读复用）。

.PARAMETER Stop
  停止本脚本管理的四个进程（按端口 + 命令行双重确认），并 docker stop 两个容器。
  容器数据在命名卷里，不会丢；下次启动原样回来。

.PARAMETER Seed
  启动前把 doc/_fsldm/fsldm-merged.ttl 重新灌入 Oxigraph 命名图并写回注册表。
  幂等（GSP PUT 覆盖），用于重建数据卷之后；命名空间用 -Namespace。

.PARAMETER KeepContainers
  与 -Stop 一起用：只停进程，保留容器运行。

.PARAMETER StrictReconcile
  验收模式：第 4.5 步只读对账一旦发现差异（退出码非零）或根本没跑成，起栈直接失败。
  常规开发与 -Stop 路径不加该开关，差异只告警。等价于环境变量 COA_RECONCILE_STRICT=1。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1
  powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1 -Seed
  powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1 -Stop
  powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1 -StrictReconcile   # 8 步验收 / 功能点核对 / M3 闸门
#>
[CmdletBinding()]
param(
    [switch]$Stop,
    [switch]$Seed,
    [string]$Namespace = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd",
    [switch]$KeepContainers,
    [switch]$StrictReconcile
)

$ErrorActionPreference = "Stop"

$Repo    = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Tools   = Join-Path $Repo "doc\coa-x\tools"
$Python  = Join-Path $Repo ".venv-coa-local\Scripts\python.exe"
$WebApp  = Join-Path $Repo "packages\web-app"
$ViteJs  = Join-Path $WebApp "node_modules\vite\bin\vite.js"
$ViteCfg = Join-Path $WebApp "vite.dev-local.config.mjs"
$RunDir  = Join-Path $env:TEMP "coa-local-stack"
$PidFile = Join-Path $RunDir "pids.json"
$PgName  = "coa-local-pg"
$OxiName = "coa-local-oxigraph"
$ReasonerName = "coa-local-reasoner"
$ReasonerImage = "agent-reasoner:0.1-s5"

if (-not (Test-Path $Python)) {
    throw "venv python not found: $Python"
}
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Test-PortListening([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Port([int]$Port, [string]$Name, [int]$Seconds = 40) {
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Test-PortListening $Port) {
            Write-Host ("  [ok] {0} :{1} listening" -f $Name, $Port)
            return
        }
        Start-Sleep -Seconds 1
    }
    throw ("{0} did not listen on :{1} within {2}s - check doc/coa-x/tools/*.log" -f $Name, $Port, $Seconds)
}

function Get-ContainerRunning([string]$Name) {
    $state = docker inspect -f "{{.State.Running}}" $Name 2>$null
    return ($LASTEXITCODE -eq 0 -and $state.Trim() -eq "true")
}

function Ensure-Container([string]$Name, [string[]]$RunArgs) {
    if (Get-ContainerRunning $Name) {
        Write-Host ("  [ok] container {0} already running" -f $Name)
        return
    }
    $exists = docker inspect $Name 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host ("  [start] container {0}" -f $Name)
        docker start $Name | Out-Null
        return
    }
    Write-Host ("  [create] container {0}" -f $Name)
    docker run -d --name $Name @RunArgs | Out-Null
    if ($LASTEXITCODE -ne 0) { throw ("failed to create container {0}" -f $Name) }
}

function Stop-PortOwner([int]$Port, [string]$Marker) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) {
        Write-Host ("  [--] :{0} not listening" -f $Port)
        return
    }
    $procId = ($conn | Select-Object -First 1).OwningProcess
    $proc = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $procId) -ErrorAction SilentlyContinue
    if ($proc -and $proc.CommandLine -like ("*" + $Marker + "*")) {
        Write-Host ("  [stop] {0} pid={1} (:{2})" -f $Marker, $procId, $Port)
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host ("  [skip] :{0} owned by pid={1}, command line does not contain {2}" -f $Port, $procId, $Marker)
    }
}

# ── Stop ────────────────────────────────────────────────────────────────
if ($Stop) {
    Write-Host "Stopping COA local stack"
    Stop-PortOwner 8099 "coa_api_local.py"
    Stop-PortOwner 8101 "coa_ontology_local.py"
    Stop-PortOwner 8091 "run_local.py"
    Stop-PortOwner 5173 "vite"
    if (Test-Path $PidFile) { Remove-Item $PidFile -Force }
    if (-not $KeepContainers) {
        foreach ($name in @($PgName, $OxiName, $ReasonerName)) {
            if (Get-ContainerRunning $name) {
                Write-Host ("  [stop] container {0}" -f $name)
                docker stop $name | Out-Null
            }
        }
    }
    Write-Host "Done. Data volumes are preserved."
    return
}

# ── Start ───────────────────────────────────────────────────────────────
Write-Host "Starting COA local stack"

# 0) Contract sources must be committed: gradlew build runs :smithyFormat and
# rewrites models/src, so a dirty tree means the stack and the committed
# contract disagree. See "契约改动的验证顺序" in 10-本地起栈.md.
& $Python (Join-Path $Repo "scripts\check-smithy-sources.py")
if ($LASTEXITCODE -ne 0) {
    throw "models/src has uncommitted changes - 按上方出路处理：提交 / 暂存 / 或先跑生成再看产物"
}

# 1) containers
Ensure-Container $PgName @(
    "--publish", "127.0.0.1:5444:5432",
    "-e", "POSTGRES_USER=platform",
    "-e", "POSTGRES_PASSWORD=platform_dev",
    "-e", "POSTGRES_DB=platform",
    "-v", "coa-local-pg-data:/var/lib/postgresql/18/docker",
    "pgvector/pgvector:pg18-trixie"
)
Ensure-Container $OxiName @(
    # 只绑回环：Oxigraph 无认证，/update 可改图删图。发布到 0.0.0.0 等于把写口
    # 开放给同网段。8101/8099 都通过 http://127.0.0.1:7878 访问，回环绑定不影响。
    "--publish", "127.0.0.1:7878:7878",
    "-v", "coa-local-oxigraph-data:/data",
    "oxigraph/oxigraph:0.5.7", "serve", "--location", "/data", "--bind", "0.0.0.0:7878"
)
Ensure-Container $ReasonerName @(
    "--publish", "127.0.0.1:7879:7879",
    $ReasonerImage
)
Wait-Port 5444 "coa-local-pg" 60
Wait-Port 7878 "coa-local-oxigraph" 30
Wait-Port 7879 "coa-local-reasoner" 60

# 1.5) Schema for BOTH databases, before any process starts.
# 8099's in-process app reads serve_local (PLATFORM__DATABASE__URL); 8101's
# registry, the fact ledger and the control-plane handlers read platform
# (COA_CONTROL_PLANE_PG_DSN).  One migration chain serves both, but they are
# separate databases: migrating only one leaves the other starting fine and
# failing on its first write to a new table/column.
$SchemaPlatformDsn = "postgresql://platform:platform_dev@127.0.0.1:5444/platform"
$ServeLocalDsn     = "postgresql://platform:platform_dev@127.0.0.1:5444/serve_local"
$SchemaServeDbExists = docker exec $PgName psql -U platform -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='serve_local'" 2>$null
if (-not ($SchemaServeDbExists -match "1")) {
    Write-Host "  [create] database serve_local"
    docker exec $PgName psql -U platform -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE serve_local" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "failed to create database serve_local" }
}
foreach ($SchemaDsn in @($SchemaPlatformDsn, $ServeLocalDsn)) {
    $SchemaDb = ($SchemaDsn -split "/")[-1]
    Write-Host ("  [migrate] {0}" -f $SchemaDb)
    & $Python (Join-Path $Tools "local_bootstrap.py") migrate --dsn $SchemaDsn
    if ($LASTEXITCODE -ne 0) { throw ("schema migration failed: {0}" -f $SchemaDb) }
}

# 2) environment for both local processes (no secrets; local DSN only)
# Prompt/template files are UTF-8; without this the child falls back to the
# console code page (cp936) and 8101 dies on UnicodeDecodeError at import time.
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:COA_PROVIDER_ONTOLOGY_GRAPH   = "oxigraph"
$env:COA_ONTOLOGY_OXIGRAPH_URL     = "http://127.0.0.1:7878"
$env:COA_PROVIDER_ONTOLOGY_REGISTRY = "postgres"
$env:COA_PROVIDER_ONTOLOGY_JOBS     = "postgres"
$env:COA_PROVIDER_ONTOLOGY_OBJECTS  = "fs"
$env:COA_PROVIDER_ONTOLOGY_VECTOR   = "pgvector"
$env:COA_PROVIDER_ONTOLOGY_EMBEDDING = "http"
$env:COA_CONTROL_PLANE_PG_DSN      = "postgresql://platform:platform_dev@127.0.0.1:5444/platform"
$env:DYNAMODB_TABLE                = "coa-local-ontologies"
$env:NDB_GRAPH_URI_BASE            = "https://coa.local/graph"
# F58/F59 的术语 lexicon 图落在本地 A-Box 基址下，图适配器默认白名单只有
# urn:platform:。这里显式放宽给本地栈使用：
# 本地放宽，生产不放宽；该前缀不得进入生产白名单。
$env:COA_LOCAL_GRAPH_ALLOWED_EXTRA_PREFIXES = "$($env:NDB_GRAPH_URI_BASE)"
# P3 reasoning: the demo A-Box graph, named <base>/<namespace>/<encoded IRI>.
# The kernel's materialize body rejects non-urn IRIs by design, so the local
# composition root injects the graph on the assembled config instead.
$env:COA_LOCAL_REASONING_ABOX_GRAPH = "$($env:NDB_GRAPH_URI_BASE)/$Namespace/urn%3Acoa%3Aabox%3Aplatform-synthetic"
# T-Box+A-Box 16MB + RDFS closure 70MB on the demo data, above the 50MiB default.
$env:PLATFORM__REASONING__MAX_ASSEMBLY_BYTES = "157286400"
$env:COA_ONTOLOGY_PORT             = "8101"
$env:COA_LOCAL_API_PORT            = "8099"
# Artifact bytes (S3 role) live beside the stack's logs/pid, served by 8099.
$env:COA_LOCAL_OBJECT_ROOT         = Join-Path $RunDir "objects"
$env:COA_LOCAL_OBJECT_BASE         = "http://127.0.0.1:8099/_local/objects"
# Document uploads (POST /sources/upload-urls) land in their own bucket dir.
$env:BUCKET_NAME                   = "coa-local-documents"
# Existing local embedding service (text-embeddings-inference, BAAI/bge-m3).
$env:COA_EMBEDDING_URL             = "http://127.0.0.1:8081/v1"
$env:COA_EMBEDDING_MODEL           = "BAAI/bge-m3"
$env:COA_EMBEDDING_DIMENSIONS      = "1024"
$env:COA_VECTOR_DIMENSIONS         = "1024"

# 3) optional TTL reload (named graph + registry row)
if ($Seed) {
    Write-Host ("  [seed] fsldm-merged.ttl -> namespace {0}" -f $Namespace)
    & $Python (Join-Path $Tools "coa_ontology_local.py") --seed --namespace $Namespace
    if ($LASTEXITCODE -ne 0) { throw "seed failed" }
}

# 4) processes
$started = @{}
if (Test-PortListening 8099) {
    Write-Host "  [ok] coa-api-local already listening on :8099 (not restarted)"
} else {
    $out = Join-Path $Tools "api-8099.log"
    $err = Join-Path $Tools "api-8099.err.log"
    $p = Start-Process -FilePath $Python `
        -ArgumentList "doc\coa-x\tools\coa_api_local.py" `
        -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $started["api"] = $p.Id
    Write-Host ("  [start] coa-api-local pid={0} log={1}" -f $p.Id, $out)
}

if (Test-PortListening 8101) {
    Write-Host "  [ok] coa-ontology-local already listening on :8101 (not restarted)"
} else {
    $out = Join-Path $Tools "ontology-8101.log"
    $err = Join-Path $Tools "ontology-8101.err.log"
    $p = Start-Process -FilePath $Python `
        -ArgumentList "doc\coa-x\tools\coa_ontology_local.py" `
        -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $started["ontology"] = $p.Id
    Write-Host ("  [start] coa-ontology-local pid={0} log={1}" -f $p.Id, $out)
}

Wait-Port 8099 "coa-api-local" 60
Wait-Port 8101 "coa-ontology-local" 90

# 5) serve context-manager: the real upstream of DataLayerService Query / KBSearch
if (Test-PortListening 8091) {
    Write-Host "  [ok] coa-serve-local already listening on :8091 (not restarted)"
} else {
    $ServeDir = Join-Path $RunDir "serve"
    New-Item -ItemType Directory -Force -Path $ServeDir | Out-Null
    $AuthzFile = Join-Path $ServeDir "authz.json"
    $authz = @"
{
  "policies": {
    "default": "// local baseline: no static forbids in this run",
    "platform-admin": "permit(principal, action, resource);"
  },
  "principals": {
    "User::local-user": [
      { "resourceId": "GLOBAL", "role": "platform-admin" }
    ]
  }
}
"@
    [System.IO.File]::WriteAllText($AuthzFile, $authz, (New-Object System.Text.UTF8Encoding($false)))

    # LLM credentials are operator-local config, never committed.
    $EnvFile = Join-Path $Repo "packages\platform-core\.env"
    $LlmKey = $null; $LlmBase = $null; $LlmModel = $null
    if (Test-Path $EnvFile) {
        foreach ($line in Get-Content $EnvFile) {
            if ($line -match "^\s*PLATFORM__LLM__API_KEY\s*=")   { $LlmKey   = (($line -split "=", 2)[1]).Trim() }
            if ($line -match "^\s*PLATFORM__LLM__BASE_URL\s*=")  { $LlmBase  = (($line -split "=", 2)[1]).Trim() }
            if ($line -match "^\s*PLATFORM__LLM__MODEL\s*=")     { $LlmModel = (($line -split "=", 2)[1]).Trim() }
        }
    }
    if (-not $LlmBase)  { $LlmBase  = "https://ark.cn-beijing.volces.com/api/coding/v3" }
    if (-not $LlmModel) { $LlmModel = "deepseek-v4-1-flash-261017" }

    $env:COA_PROVIDER_CONFIG            = "env"
    $env:COA_PROVIDER_SECRETS           = "env"
    $env:COA_PROVIDER_GRAPH             = "oxigraph"
    $env:COA_GRAPH_OXIGRAPH_URL         = "http://127.0.0.1:7878"
    $env:COA_PROVIDER_GRAPH_ADMIN       = "oxigraph"
    $env:COA_PROVIDER_METRIC_GRAPH      = "oxigraph"
    $env:COA_PROVIDER_VECTOR            = "platform-pgvector"
    $env:COA_VECTOR_PG_DSN              = $ServeLocalDsn
    $env:COA_PROVIDER_METADATA_STORE    = "postgres"
    $env:COA_METADATA_PG_DSN            = $ServeLocalDsn
    $env:COA_PROVIDER_QUERY_EXECUTOR    = "postgres"
    $env:COA_EXECUTOR_POSTGRES_DSN      = $ServeLocalDsn
    $env:COA_PROVIDER_WAREHOUSE_ADMIN   = "postgres"
    $env:COA_WAREHOUSE_ADMIN_PG_DSN     = $ServeLocalDsn
    $env:COA_PROVIDER_METRIC_INDEX      = "platform-pg"
    $env:COA_METRIC_INDEX_PG_DSN        = $ServeLocalDsn
    $env:COA_PROVIDER_EMBEDDING         = "bge-local"
    $env:COA_EMBEDDING_BGE_ENDPOINT     = "http://127.0.0.1:8081/v1"
    $env:COA_PROVIDER_LLM               = "openai-http"
    $env:COA_LLM_HTTP_BASE_URL          = $LlmBase
    $env:COA_LLM_HTTP_MODEL             = $LlmModel
    $env:COA_LLM_HTTP_API_KEY           = $LlmKey
    $env:COA_LLM_HTTP_TIMEOUT_S         = "120"
    $env:SERVE_VKG_TRANSLATION_TIMEOUT_S = "60"
    $env:SERVE_TIER2_PARALLEL_MODE      = "first_win"
    $env:COA_PROVIDER_AUTHORIZATION     = "local-file"
    $env:COA_AUTHORIZATION_FILE         = $AuthzFile
    $env:GRAPH_URI_TEMPLATE             = "https://coa.local/graph/{namespace}"
    $env:RESOLVE_TIMEOUT_S              = "420"

    $ServeLocalDbExists = docker exec $PgName psql -U platform -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='serve_local'" 2>$null
    if (-not ($ServeLocalDbExists -match "1")) {
        Write-Host "  [warn] database serve_local disappeared after step 1.5 - Query / KBSearch will fail"
    }

    $out = Join-Path $Tools "serve-8091.log"
    $err = Join-Path $Tools "serve-8091.err.log"
    $p = Start-Process -FilePath $Python `
        -ArgumentList "doc\coa-x\tools\run_local.py", "context-manager", "--port", "8091" `
        -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $started["serve"] = $p.Id
    Write-Host ("  [start] coa-serve-local pid={0} log={1}" -f $p.Id, $out)
    try {
        Wait-Port 8091 "coa-serve-local" 60
    } catch {
        Write-Host ("  [warn] coa-serve-local did not come up: {0}" -f $_.Exception.Message)
    }
}

# 6) frontend dev server — always the local config, never the default one.
# vite.config.ts wires @auth to the real OIDC provider; with no IdP the app
# throws "Auth token is empty." and every apiClient page renders empty. There is
# deliberately no fallback here: a missing local config must fail the stack
# rather than silently start the wrong server.
if (Test-PortListening 5173) {
    Write-Host "  [ok] coa-web-5173 already listening on :5173 (not restarted)"
} else {
    if (-not (Test-Path $ViteCfg)) { throw "missing $ViteCfg — 本地前端必须用 dev-local 配置，见 10-本地起栈.md" }
    if (-not (Test-Path $ViteJs))  { throw "vite not installed under packages/web-app/node_modules — run pnpm install" }
    $out = Join-Path $Tools "web-5173.log"
    $err = Join-Path $Tools "web-5173.err.log"
    $p = Start-Process -FilePath "node" `
        -ArgumentList @($ViteJs, "--config", $ViteCfg) `
        -WorkingDirectory $WebApp -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $started["web"] = $p.Id
    Write-Host ("  [start] coa-web-5173 pid={0} config=vite.dev-local.config.mjs log={1}" -f $p.Id, $out)
    Wait-Port 5173 "coa-web-5173" 60
}

if ($started.Count -gt 0) {
    $json = $started | ConvertTo-Json
    [System.IO.File]::WriteAllText($PidFile, $json, (New-Object System.Text.UTF8Encoding($false)))
}

# 4.5) fact ledger reconciliation (read-only).
# Dev / start-stack path: a difference is a warning. Acceptance mode
# (-StrictReconcile or COA_RECONCILE_STRICT=1): a difference must fail the stack,
# because a green run against known inconsistencies proves nothing.
$StrictReconcile = $StrictReconcile -or ($env:COA_RECONCILE_STRICT -match '^(1|true|yes)$')
try {
    & $Python (Join-Path $Tools "reconcile_fact_ledger.py") 2>&1 | ForEach-Object { Write-Host ("  {0}" -f $_) }
    if ($LASTEXITCODE -ne 0) {
        if ($StrictReconcile) {
            Write-Host "  [fail] fact ledger books disagree; strict reconcile refuses to hand over a dirty stack"
            Write-Host "         inspect, then run tools\reconcile_fact_ledger.py --fix (writes audited 'reconciled' events)"
            exit 1
        }
        Write-Host "  [warn] fact ledger books disagree: review, then run tools\reconcile_fact_ledger.py --fix"
    }
} catch {
    if ($StrictReconcile) {
        Write-Host ("  [fail] fact ledger reconcile did not run, so cleanliness is unproven: {0}" -f $_.Exception.Message)
        exit 1
    }
    Write-Host ("  [warn] fact ledger reconcile did not run: {0}" -f $_.Exception.Message)
}

# 5) summary
Write-Host ""
Write-Host "Stack is up:"
Write-Host "  8099  coa-api-local      (bridge -> 8101 for /ontology/*, lifecycle in-process, -> 8091 for /query|/kb/search)"
Write-Host "  8101  coa-ontology-local (Oxigraph 7878, PG registry 5444)"
Write-Host "  8091  coa-serve-local    (context-manager, serve_local DB)"
Write-Host "  5173  coa-web-5173       (vite --config vite.dev-local.config.mjs)"
Write-Host "  5444  coa-local-pg      (platform = control plane, serve_local = query chain)"
Write-Host "  7878  coa-local-oxigraph"
Write-Host "  7879  coa-local-reasoner (ROBOT/ELK; platform.reasoning_job via 8099)"
Write-Host ""
Write-Host "Stop:     powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1 -Stop"
