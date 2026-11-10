# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
<#
.SYNOPSIS
  鉴权闸门 → namespaceId UUID 闸门的顺序验证（一条命令跑完四个用例）。

.DESCRIPTION
  合并后的 dispatch 必须是这个顺序：

      _match → 鉴权（401，产出 actor）→ namespaceId UUID（400）→ KERNEL / handler

  本脚本起一个隔离的桥（默认 8599）和隔离的 PG（默认 5844 / 容器 coa-authz-pg），
  用 dev issuer 铸一个真实 token，然后验证：

    1. 无 token + 合法 UUID  → 401
    2. 无 token + 非法 UUID  → 401   ← 判据：顺序错了这里会变 400
    3. 有 token + 非法 UUID  → 400 E_NAMESPACE_ID_INVALID
    4. 有 token + 合法 UUID  → 进入正常链路（不是 401/400/503）

  用例 2 是关键：先鉴权、后校验 id，未认证的调用方不能探测 id 合法性。
  用例 1/3/4 防止修复顺序时把别的分支改坏。

  脚本退出码 0 表示四个用例全过；非 0 表示至少一条失败，并打印实际状态与 body。
  默认结束时会停掉桥与容器；-KeepRunning 保留容器便于排查。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\verify-authz-gate-order.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\verify-authz-gate-order.ps1 -KeepRunning
#>
[CmdletBinding()]
param(
    [switch]$KeepRunning,
    [int]$BridgePort = 8599,
    [int]$PgPort = 5844,
    [string]$PgContainer = "coa-authz-pg"
)

$ErrorActionPreference = "Stop"

$Repo   = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Tools  = Join-Path $Repo "doc\coa-x\tools"
$Bridge = Join-Path $Tools "coa_api_local.py"
$Bootstrap = Join-Path $Tools "local_bootstrap.py"

$Python = $null
foreach ($candidate in @(
    (Join-Path $Repo ".venv-coa-local\Scripts\python.exe"),
    (Join-Path $Repo "..\..\coa\.venv-coa-local\Scripts\python.exe")
)) {
    if (Test-Path $candidate) { $Python = (Resolve-Path $candidate).Path; break }
}
if (-not $Python) {
    throw "venv python not found; expected .venv-coa-local in the repo or in ..\..\coa"
}
if (-not (Test-Path $Bridge)) { throw "bridge not found: $Bridge" }

# Refuse to reuse an occupied port: this script must never talk to (or kill) a
# shared 8099/8599 instance belonging to another parallel line.
if (Get-NetTCPConnection -LocalPort $BridgePort -State Listen -ErrorAction SilentlyContinue) {
    throw "port $BridgePort is already in use; pass -BridgePort with a free port"
}

function Wait-Port([int]$Port, [string]$Name, [int]$Seconds = 60) {
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "$Name did not listen on :$Port within ${Seconds}s"
}

# ── isolated PG ─────────────────────────────────────────────────────────
$containerExists = $false
docker inspect $PgContainer 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { $containerExists = $true }

$containerRunning = $false
if ($containerExists) {
    $state = docker inspect -f "{{.State.Running}}" $PgContainer 2>$null
    $containerRunning = [bool]($state -and $state.Trim() -eq "true")
}
if ((-not $containerRunning) -and (Get-NetTCPConnection -LocalPort $PgPort -State Listen -ErrorAction SilentlyContinue)) {
    throw "port $PgPort is already in use by something other than $PgContainer; pass -PgPort with a free port"
}

if ($containerExists) {
    docker start $PgContainer | Out-Null
} else {
    docker run -d --name $PgContainer `
        --publish "127.0.0.1:${PgPort}:5432" `
        -e POSTGRES_USER=platform `
        -e POSTGRES_PASSWORD=platform_dev `
        -e POSTGRES_DB=platform `
        -v coa-authz-pg-data:/var/lib/postgresql/18/docker `
        pgvector/pgvector:pg18-trixie | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "failed to create container $PgContainer" }
}
Wait-Port $PgPort $PgContainer 60

$PlatformDsn = "postgresql://platform:platform_dev@127.0.0.1:${PgPort}/platform"
$ServeDsn    = "postgresql://platform:platform_dev@127.0.0.1:${PgPort}/serve_local"

$serveDb = docker exec $PgContainer psql -U platform -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='serve_local'"
if (-not ($serveDb -match "1")) {
    docker exec $PgContainer psql -U platform -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE serve_local" | Out-Null
}
foreach ($dsn in @($PlatformDsn, $ServeDsn)) {
    & $Python $Bootstrap migrate --dsn $dsn | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "schema migration failed: $dsn" }
}

# ── bridge ──────────────────────────────────────────────────────────────
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:COA_LOCAL_API_PORT = "$BridgePort"
$env:COA_LOCAL_DEV_AUTH = "on"
$env:COA_LOCAL_DEV_USERS = "local-dev@example.invalid"
$env:COA_LOCAL_DEV_ADMIN_USER = "local-dev@example.invalid"
$env:COA_LOCAL_AUTH_MODE = "enforce"
$env:COA_CONTROL_PLANE_PG_DSN = $PlatformDsn
$env:PLATFORM__DATABASE__URL = $ServeDsn

$outLog = Join-Path $env:TEMP "coa-authz-order-$BridgePort.out.log"
$errLog = Join-Path $env:TEMP "coa-authz-order-$BridgePort.err.log"
Remove-Item $outLog, $errLog -Force -ErrorAction SilentlyContinue

$bridge = Start-Process -FilePath $Python -ArgumentList @($Bridge) -PassThru `
    -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog

$base = "http://127.0.0.1:$BridgePort"
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    if ($bridge.HasExited) { break }
    try {
        $r = Invoke-WebRequest -UseBasicParsing "$base/health" -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
}
if (-not $ready) {
    if (Test-Path $outLog) { Get-Content $outLog -Tail 30 | Write-Host }
    if (Test-Path $errLog) { Get-Content $errLog -Tail 30 | Write-Host }
    if (-not $bridge.HasExited) { Stop-Process -Id $bridge.Id -Force -ErrorAction SilentlyContinue }
    throw "bridge did not become healthy on $base"
}

function Invoke-Probe([string]$Name, [string]$Path, [string]$Token) {
    $tmp = [IO.Path]::GetTempFileName()
    if ($Token) {
        $code = & curl.exe -s --max-time 15 -o $tmp -w "%{http_code}" `
            -H "Authorization: Bearer $Token" "$base$Path"
    } else {
        $code = & curl.exe -s --max-time 15 -o $tmp -w "%{http_code}" "$base$Path"
    }
    $body = Get-Content -Raw $tmp
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    [pscustomobject]@{ Name = $Name; Status = [int]$code; Body = $body }
}

try {
    $tokenResp = & curl.exe -s --max-time 10 -X POST "$base/local/auth/token" `
        -H "Content-Type: application/json" -d '{\"email\":\"local-dev@example.invalid\"}'
    $token = ($tokenResp | ConvertFrom-Json).token
    if (-not $token) { throw "dev token mint failed: $tokenResp" }

    $validUuid = "11111111-1111-4111-8111-111111111111"
    $invalidUuid = "not-a-uuid"

    $results = @(
        (Invoke-Probe "1 no token + valid UUID"   "/namespaces/$validUuid/sources"   $null),
        (Invoke-Probe "2 no token + invalid UUID" "/namespaces/$invalidUuid/sources" $null),
        (Invoke-Probe "3 token + invalid UUID"    "/namespaces/$invalidUuid/sources" $token),
        (Invoke-Probe "4 token + valid UUID"      "/namespaces/$validUuid/sources"   $token)
    )

    $failures = @()
    if ($results[0].Status -ne 401) {
        $failures += "case 1 expected 401, got $($results[0].Status)"
    }
    # The judgement case: authorization must run before the UUID gate.
    if ($results[1].Status -ne 401) {
        $failures += "case 2 expected 401 (got $($results[1].Status)); authz gate is not before the UUID gate"
    }
    if ($results[2].Status -ne 400 -or $results[2].Body -notmatch "E_NAMESPACE_ID_INVALID") {
        $failures += "case 3 expected 400 E_NAMESPACE_ID_INVALID, got $($results[2].Status)"
    }
    if ($results[3].Status -in @(400, 401, 503)) {
        $failures += "case 4 expected the normal chain, got $($results[3].Status)"
    }

    Write-Host ""
    Write-Host "gate order: _match -> authz(401) -> namespaceId UUID(400) -> KERNEL/handler"
    Write-Host ("{0,-28} {1,6}  {2}" -f "case", "status", "body")
    foreach ($r in $results) {
        $snippet = ($r.Body -replace "\s+", " ")
        if ($snippet.Length -gt 120) { $snippet = $snippet.Substring(0, 120) + "..." }
        Write-Host ("{0,-28} {1,6}  {2}" -f $r.Name, $r.Status, $snippet)
    }
    Write-Host ""

    if ($failures.Count -gt 0) {
        foreach ($f in $failures) { Write-Host "[FAIL] $f" -ForegroundColor Red }
        exit 1
    }
    Write-Host "[PASS] 4/4 gate-order cases" -ForegroundColor Green
    exit 0
}
finally {
    if (-not $bridge.HasExited) {
        Stop-Process -Id $bridge.Id -Force -ErrorAction SilentlyContinue
    }
    if (-not $KeepRunning) {
        docker stop $PgContainer | Out-Null
    }
}
