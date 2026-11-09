# S7 one-command start: check port -> compose up -> wait ready -> print URLs.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/up.ps1 [-DryRun]
# 互斥：入口先过 compose-guard（R1 技术拦截），busy 时直接退出 75，绝不 compose up。
param(
    [switch]$DryRun,       # 只做闸门校验，不实际启动/重启容器（用于验证 guard）
    [switch]$AssumeLock,   # 调用方已持锁：仅当 -Owner 与当前锁 owner 一致时放行
    [string]$Owner = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# --- R1 技术拦截：有重任务持锁则拒绝任何启动/重建 ---
# -AssumeLock: 持锁者本人调用 up.ps1 时不再被自己挡住；owner 不匹配仍退 75。
if ($AssumeLock) {
    if (-not $Owner) {
        Write-Host '[up] -AssumeLock 需要同时提供 -Owner <当前锁 owner>'
        exit 1
    }
    & (Join-Path $PSScriptRoot 'compose-guard.ps1') check -Owner $Owner
} else {
    & (Join-Path $PSScriptRoot 'compose-guard.ps1') check
}
if ($LASTEXITCODE -ne 0) {
    Write-Host '[up] E_BUILD_CONFLICT: 已有重任务持锁，拒绝启动/重建。'
    Write-Host '[up] 查看 holder: powershell -ExecutionPolicy Bypass -File scripts/compose-guard.ps1 status'
    exit 75
}
Write-Host '[up] guard ok (heavy lock free or owner-match)'

if ($DryRun) {
    Write-Host '[up] dry-run: guard 通过，未执行 docker compose up。'
    exit 0
}


if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'docker not found; install Docker Desktop first.'
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker engine is not running; start Docker Desktop first.'
}

$base = 'http://127.0.0.1:8080'
$listening = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($listening) {
    $healthy = $false
    try {
        Invoke-WebRequest "$base/healthz" -UseBasicParsing -TimeoutSec 3 | Out-Null
        $healthy = $true
    }
    catch { }
    if (-not $healthy) {
        throw 'Port 8080 is taken by another process; free it or set PLATFORM_PORT.'
    }
    if ($AssumeLock) {
        Write-Host '[up] recreate: port 8080 is already served; forcing compose recreate (--force-recreate).'
        docker compose up -d --force-recreate platform
        if ($LASTEXITCODE -ne 0) { throw 'docker compose up (--force-recreate) failed.' }
    }
    else {
        Write-Host '[up] platform already running on 8080; skip compose up (lock is free, nothing to rebuild).'
    }
}
else {
    Write-Host '[up] docker compose up -d ...'
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed.' }
}

Write-Host '[up] waiting for /readyz ...'
$deadline = (Get-Date).AddSeconds(150)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest "$base/readyz" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    }
    catch { }
    Start-Sleep -Seconds 3
}
if (-not $ready) {
    Write-Host '[up] not ready after 150s; current status:'
    docker compose ps
    throw 'Platform is not ready; check docker compose logs platform.'
}

docker compose ps
Write-Host ''
Write-Host "[up] ready: $base/ui/"
Write-Host '[up] next: powershell -ExecutionPolicy Bypass -File scripts/seed.ps1'
Write-Host "[up] api docs: $base/docs"
