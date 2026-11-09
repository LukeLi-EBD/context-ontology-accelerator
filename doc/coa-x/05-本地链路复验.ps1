<#
.SYNOPSIS
    一条命令复验 COA 本地查询链路（不连 AWS，不碰 8080 / 验收栈）。

.DESCRIPTION
    按依赖顺序拉起：临时 pgvector(5443) → 真实迁移 → 灌 chunk+向量 → 临时 Oxigraph(7878)
    → 灌 FS-LDM 本体 → LLM（默认远端 Ark；llama-local 时起本机 8077）→ context-manager(8091)
    → data-layer(8092) → 发一条真实 Query → 断言 200 且 Tier-2/3 有真实结果。

    前置条件见同目录 05-本地链路复验.md。缺任何一项都会在启动前失败并说明原因，
    不会静默降级、不会回落到 AWS。

.PARAMETER Namespace
    查询使用的 namespace（必须是 UUID v4，且与 Cedar 策略一致）。

.PARAMETER LlmProvider
    ark（默认）：用火山方舟 coding plan 端点，密钥从 packages/platform-core/.env 或环境变量读。
    llama-local：起本机 llama.cpp 0.5B（8077），只用于不联网的冒烟，不承诺 Tier-2 质量。
    本脚本从不把密钥写入任何文件或日志。

.PARAMETER Keep
    保留容器、进程与日志以便排查；默认全部清理。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\05-本地链路复验.ps1
    powershell -ExecutionPolicy Bypass -File .\05-本地链路复验.ps1 -Keep
    powershell -ExecutionPolicy Bypass -File .\05-本地链路复验.ps1 -LlmProvider llama-local
#>
[CmdletBinding()]
param(
    [string]$Namespace = "550e8400-e29b-41d4-a716-446655440000",
    [ValidateSet("llama-local", "ark")]
    [string]$LlmProvider = "ark",
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

# Ark（火山方舟 coding plan）：密钥只从 .env 或环境变量读，绝不写盘。
$ArkEnvFile  = Join-Path $Repo "packages\platform-core\.env"
$ArkBaseUrl  = "https://ark.cn-beijing.volces.com/api/coding/v3"
$ArkModel    = "deepseek-v4-1-flash-261017"

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

function Get-EnvValue([string]$Path, [string]$Key) {
    # 只读取，不回显；返回值直接进进程环境变量，不落盘。
    if (-not (Test-Path $Path)) { return $null }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*$([regex]::Escape($Key))\s*=") {
            return (($line -split "=", 2)[1]).Trim()
        }
    }
    return $null
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
if ($LlmProvider -eq "llama-local") {
    Assert-True (Test-Path $Model) "GGUF model: $Model"
} else {
    $arkKey = $env:COA_LLM_HTTP_API_KEY
    if (-not $arkKey) { $arkKey = Get-EnvValue $ArkEnvFile "PLATFORM__LLM__API_KEY" }
    Assert-True ([bool]$arkKey) "Ark api key from `$env:COA_LLM_HTTP_API_KEY or $ArkEnvFile (value not printed)"
    $arkBase = Get-EnvValue $ArkEnvFile "PLATFORM__LLM__BASE_URL"
    $arkModelName = Get-EnvValue $ArkEnvFile "PLATFORM__LLM__MODEL"
    if ($arkBase) { $ArkBaseUrl = $arkBase }
    if ($arkModelName) { $ArkModel = $arkModelName }
    Write-Host "  ok  llm=ark base=$ArkBaseUrl model=$ArkModel" -ForegroundColor Green
}
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
# 端口先开、再初始化：只等端口会让第一次连接被拒。用 pg_isready 等真正的可服务状态。
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    & docker exec $PgContainer pg_isready -U platform -d platform 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Milliseconds 500
}
Assert-True $ready "pgvector accepting connections"
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

# ---- 4. LLM endpoint -------------------------------------------------------
if ($LlmProvider -eq "llama-local") {
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
} else {
    Write-Step "4/7 Volcano Ark chat endpoint"
    try {
        $probe = Invoke-WebRequest -Uri "$ArkBaseUrl/models" -UseBasicParsing -TimeoutSec 30 `
            -Headers @{ Authorization = "Bearer $arkKey" }
        Assert-True ($probe.StatusCode -eq 200) "ark /models reachable (HTTP $($probe.StatusCode))"
    } catch {
        throw "FAILED: ark endpoint unreachable at $ArkBaseUrl : $($_.Exception.Message)"
    }
}

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
# 本地显式开启「先到先得 + 短尾」：一条腿给出可接受结果后就不再等另一条。
# 仅本地复验这样设；AWS 部署保持默认（gather），因为那会改变线上选优语义与 p50/p99。
$env:SERVE_TIER2_PARALLEL_MODE            = "first_win"
if ($LlmProvider -eq "llama-local") {
    $env:COA_LLM_HTTP_BASE_URL            = $LlmUrl
    $env:COA_LLM_HTTP_MODEL               = "qwen2.5-0.5b"
    $env:COA_LLM_HTTP_TIMEOUT_S           = "300"
    $env:SERVE_VKG_TRANSLATION_TIMEOUT_S  = "300"
} else {
    $env:COA_LLM_HTTP_BASE_URL            = $ArkBaseUrl
    $env:COA_LLM_HTTP_MODEL               = $ArkModel
    $env:COA_LLM_HTTP_API_KEY             = $arkKey
    $env:COA_LLM_HTTP_TIMEOUT_S           = "120"
    $env:SERVE_VKG_TRANSLATION_TIMEOUT_S  = "60"
}
$env:COA_PROVIDER_AUTHORIZATION           = "local-file"
$env:COA_AUTHORIZATION_FILE               = $AuthzFile
$env:GRAPH_URI_TEMPLATE                   = "https://ontology.local/{namespace}"
$env:RESOLVE_TIMEOUT_S                    = "420"

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
# 同一套不带 BOM 的写法：data-layer / CM 按严格 JSON 解析，BOM 会被判为非法前缀。
# 不要用 Set-Content -Encoding utf8（Windows PowerShell 5.1 会写 BOM）。
Write-Json $AnswerFile $body

Write-Host "  http_status=$status elapsed=$([Math]::Round($stopwatch.Elapsed.TotalSeconds,1))s body=$AnswerFile"
Assert-True ($status -eq 200) "HTTP 200 (not 500)"

$parsed = $body | ConvertFrom-Json
$result = $parsed.result
Assert-True ($null -ne $result) "response carries a result"
# 成功判据：tier>=2 即可。合法 tier=2 是契约的一部分（结构化层真的查了表），
# 不能因为「没走到 Tier-3」就判失败 —— 那是把正确答案当失败。
$tier = [double]$result.tier
Assert-True ($tier -ge 2) "Tier-2 or Tier-3 answered (tier=$tier)"
if ($tier -lt 3) {
    Assert-True ($result.resultRows.Count -ge 1) "Tier-2 returned rows ($($result.resultRows.Count))"
    # 退化常量：把占位/常量塞进 SELECT 冒充查询结果（'N/A'、'0'、NOT_ANSWERABLE 之类），
    # SQL 里没有 FROM。这类回答不是「Tier-2 通过」，必须判失败。
    $sql = [string]$result.queryUsed
    Assert-True ($sql -match '(?i)\bfrom\b') "Tier-2 SQL reads a table, not a bare constant (queryUsed='$sql')"
    $firstCell = ""
    foreach ($prop in $result.resultRows[0].PSObject.Properties) { $firstCell = ([string]$prop.Value).Trim(); break }
    Assert-True ($firstCell -notmatch '(?i)^\s*NOT_ANSWERABLE') "no refusal disguised as a Tier-2 row (firstCell='$firstCell')"
} else {
    Assert-True ($result.supportingContent.Count -ge 1) "supporting evidence present ($($result.supportingContent.Count) chunks)"
}

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
