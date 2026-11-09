<#
.SYNOPSIS
    一条命令复验 COA 本地查询链路（不连 AWS，不碰 8080 / 验收栈）。

.DESCRIPTION
    按依赖顺序拉起：临时 pgvector(5443) → 真实迁移 → 灌 chunk+向量 → 临时 Oxigraph(7878)
    → 灌 FS-LDM 本体 → 本机 OpenAI 兼容 LLM(8077) → context-manager(8091)
    → data-layer(8092) → 发一条真实 Query → 断言 200 且 Tier-3 有证据。

    前置条件见同目录 05-本地链路复验.md。缺任何一项都会在启动前失败并说明原因，
    不会静默降级、不会回落到 AWS。

.PARAMETER Namespace
    查询使用的 namespace（必须是 UUID v4，且与 Cedar 策略一致）。

.PARAMETER Keep
    保留容器、进程与日志以便排查；默认全部清理。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\05-本地链路复验.ps1
    powershell -ExecutionPolicy Bypass -File .\05-本地链路复验.ps1 -Keep
#>
[CmdletBinding()]
param(
    [string]$Namespace = "550e8400-e29b-41d4-a716-446655440000",
    [switch]$Keep
)

$ErrorActionPreference = "Stop"

# ---- fixed topology -------------------------------------------------------
$Repo        = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Python      = Join-Path $Repo ".venv-coa-local\Scripts\python.exe"
$Model       = "D:\agentABC\_tmp\llm\qwen2.5-0.5b-instruct-q4_k_m.gguf"
$PgContainer = "coa-verify-pg"
$OxiContainer= "coa-verify-oxi"
$PgPort      = 5443
$OxiPort     = 7878
$LlmPort     = 8077
$CmPort      = 8091
$DlPort      = 8092
$EmbedPort   = 8081

$PgDsn       = "postgresql://platform:platform_dev@127.0.0.1:$PgPort/platform"
$OxiUrl      = "http://127.0.0.1:$OxiPort"
$LlmUrl      = "http://127.0.0.1:$LlmPort/v1"
$CmUrl       = "http://127.0.0.1:$CmPort"
$DlUrl       = "http://127.0.0.1:$DlPort"

$LogDir      = Join-Path $env:TEMP "coa-verify"
$AuthzFile   = Join-Path $LogDir "authz.json"
$QueryFile   = Join-Path $LogDir "query.json"
$AnswerFile  = Join-Path $LogDir "answer.json"
$Bootstrap   = Join-Path $PSScriptRoot "tools\local_bootstrap.py"
$Runner      = Join-Path $PSScriptRoot "tools\run_local.py"

$StartedProcs = @()
$StartedBoxes = @()

function Write-Step([string]$Text) {
    Write-Host ""
    Write-Host "== $Text" -ForegroundColor Cyan
}

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "FAILED: $Message" }
    Write-Host "  ok  $Message" -ForegroundColor Green
}

function Test-Port([int]$Port) {
    $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Port([int]$Port, [int]$TimeoutSec, [string]$Name) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port $Port) { Write-Host "  ok  $Name listening on $Port" -ForegroundColor Green; return }
        Start-Sleep -Milliseconds 500
    }
    throw "FAILED: $Name did not listen on $Port within ${TimeoutSec}s"
}

function Wait-Http([string]$Url, [int]$TimeoutSec, [string]$Name) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $code = (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5).StatusCode
            if ($code -ge 200 -and $code -lt 500) { Write-Host "  ok  $Name responding ($Url)" -ForegroundColor Green; return }
        } catch { }
        Start-Sleep -Seconds 1
    }
    throw "FAILED: $Name not responding at $Url within ${TimeoutSec}s"
}

function Stop-Port([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

function Start-Background([string]$Name, [string]$FilePath, [string[]]$Arguments) {
    $out = Join-Path $LogDir "$Name.out.log"
    $err = Join-Path $LogDir "$Name.err.log"
    $proc = Start-Process -FilePath $FilePath -ArgumentList $Arguments -PassThru -NoNewWindow `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $script:StartedProcs += $proc
    Write-Host "  ..  $Name pid=$($proc.Id) logs=$out" -ForegroundColor DarkGray
    return $proc
}

function Write-Json([string]$Path, [string]$Text) {
    # 不带 BOM：data-layer 与 CM 都把 JSON 文件按严格 json 解析，BOM 会被判为非法前缀。
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}

function Start-Box([string]$Name, [string[]]$Arguments) {
    & docker run -d --name $Name @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "FAILED: docker run $Name" }
    $script:StartedBoxes += $Name
}

function Remove-Box([string]$Name) {
    & docker rm -f $Name 2>$null | Out-Null
}

function Cleanup {
    if ($Keep) {
        Write-Host ""
        Write-Host "Kept running (pid/containers) and logs in $LogDir" -ForegroundColor Yellow
        return
    }
    Write-Host ""
    Write-Host "cleaning up..." -ForegroundColor DarkGray
    foreach ($port in @($DlPort, $CmPort, $LlmPort)) { Stop-Port $port }
    foreach ($box in $StartedBoxes) { Remove-Box $box }
    Write-Host "cleaned temp containers and processes; logs remain in $LogDir" -ForegroundColor DarkGray
}

# ---- preflight ------------------------------------------------------------
Write-Step "0/7 preflight"
Assert-True (Test-Path $Python) "project venv python: $Python"
Assert-True (Test-Path $Model) "GGUF model: $Model"
Assert-True (Test-Path $Bootstrap) "bootstrap helper: $Bootstrap"
Assert-True (Test-Path $Runner) "process runner: $Runner"
Assert-True ($null -ne (Get-Command docker -ErrorAction SilentlyContinue)) "docker on PATH"
Assert-True ((Test-Port $EmbedPort)) "BGE embedding service already running on $EmbedPort (start the local platform stack first; this script does not own it)"
if ($Namespace -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$') {
    throw "FAILED: Namespace must be a UUID v4, got '$Namespace'"
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
try {

# ---- 1. vector tables -----------------------------------------------------
Write-Step "1/7 pgvector + real migrations ($PgPort)"
Remove-Box $PgContainer
Start-Box $PgContainer @(
    "-e", "POSTGRES_USER=platform",
    "-e", "POSTGRES_PASSWORD=platform_dev",
    "-e", "POSTGRES_DB=platform",
    "-p", "127.0.0.1:${PgPort}:5432",
    "pgvector/pgvector:pg18-trixie"
)
Wait-Port $PgPort 60 "pgvector"
& $Python $Bootstrap migrate --dsn $PgDsn
if ($LASTEXITCODE -ne 0) { throw "FAILED: platform migrations" }

# ---- 2. chunks + vectors --------------------------------------------------
Write-Step "2/7 seed chunks with real BGE vectors"
& $Python $Bootstrap seed --dsn $PgDsn
if ($LASTEXITCODE -ne 0) { throw "FAILED: vector seed" }

# ---- 3. ontology ----------------------------------------------------------
Write-Step "3/7 load FS-LDM ontology into oxigraph ($OxiPort)"
Remove-Box $OxiContainer
Start-Box $OxiContainer @(
    "-p", "127.0.0.1:${OxiPort}:7878",
    "oxigraph/oxigraph:0.5.7",
    "serve", "--location", "/data", "--bind", "0.0.0.0:7878"
)
Wait-Http "$OxiUrl/" 60 "oxigraph"
& $Python $Bootstrap ontology --oxigraph $OxiUrl --namespace $Namespace
if ($LASTEXITCODE -ne 0) { throw "FAILED: ontology load" }

# ---- 4. local LLM ---------------------------------------------------------
Write-Step "4/7 local OpenAI-compatible LLM ($LlmPort)"
if (-not (Test-Port $LlmPort)) {
    $threads = [Math]::Min(12, [Environment]::ProcessorCount)
    Start-Background "llm" $Python @(
        "-m", "llama_cpp.server",
        "--model", "`"$Model`"",
        "--model_alias", "qwen2.5-0.5b",
        "--host", "127.0.0.1",
        "--port", "$LlmPort",
        "--n_ctx", "8192",
        "--n_threads", "$threads",
        "--n_threads_batch", "$threads",
        "--chat_format", "chatml"
    ) | Out-Null
} else {
    Write-Host "  ok  LLM already listening on $LlmPort" -ForegroundColor Green
}
Wait-Http "$LlmUrl/models" 120 "llm"

# ---- 5. context-manager ---------------------------------------------------
Write-Step "5/7 context-manager ($CmPort)"
Stop-Port $CmPort
$env:COA_PROVIDER_CONFIG                  = "env"
$env:COA_PROVIDER_SECRETS                 = "env"
$env:COA_PROVIDER_GRAPH                   = "oxigraph"
$env:COA_GRAPH_OXIGRAPH_URL               = $OxiUrl
$env:COA_PROVIDER_GRAPH_ADMIN             = "oxigraph"
$env:COA_PROVIDER_METRIC_GRAPH            = "oxigraph"
$env:COA_PROVIDER_VECTOR                  = "platform-pgvector"
$env:COA_VECTOR_PG_DSN                    = $PgDsn
$env:COA_PROVIDER_METADATA_STORE          = "postgres"
$env:COA_METADATA_PG_DSN                  = $PgDsn
$env:COA_PROVIDER_QUERY_EXECUTOR          = "postgres"
$env:COA_EXECUTOR_POSTGRES_DSN            = $PgDsn
$env:COA_PROVIDER_WAREHOUSE_ADMIN         = "postgres"
$env:COA_WAREHOUSE_ADMIN_PG_DSN           = $PgDsn
$env:COA_PROVIDER_METRIC_INDEX            = "platform-pg"
$env:COA_METRIC_INDEX_PG_DSN              = $PgDsn
$env:COA_PROVIDER_EMBEDDING               = "bge-local"
$env:COA_EMBEDDING_BGE_ENDPOINT           = "http://127.0.0.1:$EmbedPort/v1"
$env:COA_PROVIDER_LLM                     = "openai-http"
$env:COA_LLM_HTTP_BASE_URL                = $LlmUrl
$env:COA_LLM_HTTP_MODEL                   = "qwen2.5-0.5b"
$env:COA_LLM_HTTP_TIMEOUT_S               = "300"
$env:COA_PROVIDER_AUTHORIZATION           = "local-file"
$env:COA_AUTHORIZATION_FILE               = $AuthzFile
$env:GRAPH_URI_TEMPLATE                   = "https://ontology.local/{namespace}"
$env:RESOLVE_TIMEOUT_S                    = "420"
$env:SERVE_VKG_TRANSLATION_TIMEOUT_S      = "300"

@"
{
  "policies": {
    "default": "// local baseline: no static forbids in this run",
    "analyst": "permit(principal, action == SCL::Action::\"query\", resource) when { resource.namespace == \"$Namespace\" };"
  },
  "principals": {
    "User::alice": [
      { "resourceId": "$Namespace", "role": "analyst" }
    ]
  }
}
"@ | ForEach-Object { Write-Json $AuthzFile $_ }

Start-Background "cm" $Python @($Runner, "context-manager", "--port", "$CmPort") | Out-Null
Wait-Http "$CmUrl/ping" 90 "context-manager"

# ---- 6. data-layer --------------------------------------------------------
Write-Step "6/7 data-layer ($DlPort)"
Stop-Port $DlPort
$env:COA_PROVIDER_CONTEXT_MANAGER = "local-http"
$env:COA_CONTEXT_MANAGER_ENDPOINT = $CmUrl
$env:COA_CONTEXT_MANAGER_TIMEOUT_S = "540"
Start-Background "dl" $Python @($Runner, "data-layer", "--port", "$DlPort") | Out-Null
Wait-Port $DlPort 60 "data-layer"

# ---- 7. real query --------------------------------------------------------
Write-Step "7/7 send a real query"
# strategy=best：nl_to_sql 与 ontop 并行、各 90s 上限。顺序模式在 0.5B 上会把
# 300s 的 RESOLVE_TIMEOUT_S 全部耗在 NL->SPARQL 重试里，Tier-3 没时间合成。
@"
{
  "query": "FS-LDM 中，一个人既是客户又是员工时，客户单一视图是怎么建模的？",
  "includeSupporting": true,
  "includeDebugInfo": true,
  "strategy": "best"
}
"@ | ForEach-Object { Write-Json $QueryFile $_ }

$stopwatch = [Diagnostics.Stopwatch]::StartNew()
try {
    $response = Invoke-WebRequest -Uri "$DlUrl/namespaces/$Namespace/query" `
        -Method Post -UseBasicParsing -TimeoutSec 600 `
        -Headers @{ Authorization = "Bearer local-dev-token" } `
        -ContentType "application/json" `
        -InFile $QueryFile
    $status = $response.StatusCode
    $body = $response.Content
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $body = $reader.ReadToEnd()
}
$stopwatch.Stop()
$body | Set-Content -Encoding utf8 $AnswerFile

Write-Host "  http_status=$status elapsed=$([Math]::Round($stopwatch.Elapsed.TotalSeconds,1))s body=$AnswerFile"
Assert-True ($status -eq 200) "HTTP 200 (not 500)"

$parsed = $body | ConvertFrom-Json
$result = $parsed.result
Assert-True ($null -ne $result) "response carries a result"
Assert-True ([double]$result.tier -ge 3) "Tier-3 answered (tier=$($result.tier))"
Assert-True ($result.supportingContent.Count -ge 1) "supporting evidence present ($($result.supportingContent.Count) chunks)"

Write-Host ""
Write-Host "hop trace:" -ForegroundColor Cyan
$result.trace | ForEach-Object {
    $detail = if ($_.detail -is [string]) { $_.detail } else { ($_.detail | ConvertTo-Json -Compress) }
    Write-Host ("  {0,-22} {1,-8} {2,7}ms  {3}" -f $_.step, $_.status, $_.durationMs, $detail)
}

Write-Host ""
Write-Host "answer:" -ForegroundColor Cyan
if ([string]::IsNullOrWhiteSpace($result.synthesizedAnswer)) {
    Write-Host "  (empty — the local 0.5B model emitted only a confidence tag this run)" -ForegroundColor Yellow
} else {
    Write-Host $result.synthesizedAnswer
}

} finally {
    Cleanup
}
