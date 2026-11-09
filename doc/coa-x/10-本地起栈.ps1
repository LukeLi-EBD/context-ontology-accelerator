<#
.SYNOPSIS
  COA 原版本地栈一键启停。

.DESCRIPTION
  本脚本只管理下面五个东西（其余一律不碰）：

    容器 coa-local-pg        127.0.0.1:5444  pgvector/pgvector:pg18-trixie，库 platform
    容器 coa-local-oxigraph  127.0.0.1:7878  oxigraph/oxigraph:0.5.7，数据卷 coa-local-oxigraph-data
    进程 coa-api-local       127.0.0.1:8099  doc/coa-x/tools/coa_api_local.py
    进程 coa-ontology-local  127.0.0.1:8101  doc/coa-x/tools/coa_ontology_local.py
    进程 coa-serve-local     127.0.0.1:8091  run_local.py context-manager（Query / KBSearch 的上游）

  不管理：8080/8082 验收栈、5173 前端 dev server、8081 BGE 嵌入服务（只读复用）。

.PARAMETER Stop
  停止本脚本管理的三个进程（按端口 + 命令行双重确认），并 docker stop 两个容器。
  容器数据在命名卷里，不会丢；下次启动原样回来。

.PARAMETER Seed
  启动前把 doc/_fsldm/fsldm-merged.ttl 重新灌入 Oxigraph 命名图并写回注册表。
  幂等（GSP PUT 覆盖），用于重建数据卷之后；命名空间用 -Namespace。

.PARAMETER KeepContainers
  与 -Stop 一起用：只停进程，保留容器运行。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1
  powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1 -Seed
  powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1 -Stop
#>
[CmdletBinding()]
param(
    [switch]$Stop,
    [switch]$Seed,
    [string]$Namespace = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd",
    [switch]$KeepContainers
)

$ErrorActionPreference = "Stop"

$Repo    = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Tools   = Join-Path $Repo "doc\coa-x\tools"
$Python  = Join-Path $Repo ".venv-coa-local\Scripts\python.exe"
$RunDir  = Join-Path $env:TEMP "coa-local-stack"
$PidFile = Join-Path $RunDir "pids.json"
$PgName  = "coa-local-pg"
$OxiName = "coa-local-oxigraph"

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
    if (Test-Path $PidFile) { Remove-Item $PidFile -Force }
    if (-not $KeepContainers) {
        foreach ($name in @($PgName, $OxiName)) {
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
    "--publish", "7878:7878",
    "-v", "coa-local-oxigraph-data:/data",
    "oxigraph/oxigraph:0.5.7", "serve", "--location", "/data", "--bind", "0.0.0.0:7878"
)
Wait-Port 5444 "coa-local-pg" 60
Wait-Port 7878 "coa-local-oxigraph" 30

# 2) environment for both local processes (no secrets; local DSN only)
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
    $ServeDsn = "postgresql://platform:platform_dev@127.0.0.1:5444/serve_local"
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
    $env:COA_VECTOR_PG_DSN              = $ServeDsn
    $env:COA_PROVIDER_METADATA_STORE    = "postgres"
    $env:COA_METADATA_PG_DSN            = $ServeDsn
    $env:COA_PROVIDER_QUERY_EXECUTOR    = "postgres"
    $env:COA_EXECUTOR_POSTGRES_DSN      = $ServeDsn
    $env:COA_PROVIDER_WAREHOUSE_ADMIN   = "postgres"
    $env:COA_WAREHOUSE_ADMIN_PG_DSN     = $ServeDsn
    $env:COA_PROVIDER_METRIC_INDEX      = "platform-pg"
    $env:COA_METRIC_INDEX_PG_DSN        = $ServeDsn
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

    $hasServeDb = docker exec $PgName psql -U platform -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='serve_local'" 2>$null
    if (-not ($hasServeDb -match "1")) {
        Write-Host "  [warn] database serve_local is missing - Query / KBSearch will fail until it is bootstrapped"
        Write-Host "         see 10-本地起栈.md §serve 库一次性初始化"
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

if ($started.Count -gt 0) {
    $json = $started | ConvertTo-Json
    [System.IO.File]::WriteAllText($PidFile, $json, (New-Object System.Text.UTF8Encoding($false)))
}

# 5) summary
Write-Host ""
Write-Host "Stack is up:"
Write-Host "  8099  coa-api-local      (bridge -> 8101 for /ontology/*, -> 8091 for /query|/kb/search)"
Write-Host "  8101  coa-ontology-local (Oxigraph 7878, PG registry 5444)"
Write-Host "  8091  coa-serve-local    (context-manager, serve_local DB)"
Write-Host "  5444  coa-local-pg"
Write-Host "  7878  coa-local-oxigraph"
Write-Host ""
Write-Host "Frontend: run the 5173 dev server separately (local-only vite config)."
Write-Host "Stop:     powershell -ExecutionPolicy Bypass -File .\10-本地起栈.ps1 -Stop"
