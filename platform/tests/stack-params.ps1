# stack-params.ps1 - parameterisation checks for the parallel-stack work.
#
# Covers:
#   1. default stack renders exactly as before (project/container/ports/data root)
#   2. a named stack (-p platform-b + env) renders scoped names, ports and data root
#   3. stack.ps1 up rejects an occupied host port with a clear E_STACK_PORT_IN_USE
#   4. stack.ps1 status gives up on /readyz after the requested timeout
#
# Usage: powershell -ExecutionPolicy Bypass -File tests/stack-params.ps1
# Exit 0 = all checks passed.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$script:failed = 0

function Assert-True($condition, [string]$name, [string]$detail = '') {
    if ($condition) {
        Write-Host "[PASS] $name $detail"
    } else {
        Write-Host "[FAIL] $name $detail"
        $script:failed++
    }
}

function Get-ConfigJson([string[]]$composeFiles) {
    $composeArgs = @('compose') + $composeFiles + @('config', '--format', 'json')
    $raw = & docker @composeArgs
    if ($LASTEXITCODE -ne 0) { throw "docker compose config failed: $composeFiles" }
    return ($raw | ConvertFrom-Json)
}

# --- 1. default equivalence ------------------------------------------------
$default = Get-ConfigJson @('-f', 'docker-compose.yml')
Assert-True ($default.name -eq 'agent-platform') 'default project name' $default.name
Assert-True ($default.services.postgres.container_name -eq 'agent-platform-postgres') 'default postgres container name' $default.services.postgres.container_name
Assert-True ($default.services.platform.container_name -eq 'agent-platform-api') 'default api container name' $default.services.platform.container_name
Assert-True ($default.services.platform.ports[0].published -eq '8080') 'default api port' $default.services.platform.ports[0].published
Assert-True ($default.services.postgres.ports[0].published -eq '5432') 'default postgres port' $default.services.postgres.ports[0].published
Assert-True ($null -eq $default.services.oxigraph.ports) 'default oxigraph has no host port' 'no mapping'
Assert-True ($default.services.platform.volumes[0].source -eq 'D:/agentABC/data') 'default data root' $default.services.platform.volumes[0].source

# --- 2. named stack --------------------------------------------------------
$previous = @{}
foreach ($key in @('COMPOSE_PROJECT_NAME', 'PLATFORM_PORT', 'POSTGRES_PORT', 'OXIGRAPH_PORT', 'PLATFORM_DATA_ROOT')) {
    $previous[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}
try {
    $env:COMPOSE_PROJECT_NAME = 'platform-b'
    $env:PLATFORM_PORT = '8081'
    $env:POSTGRES_PORT = '5433'
    $env:OXIGRAPH_PORT = '7879'
    $env:PLATFORM_DATA_ROOT = 'D:/agentABC/data-b'
    $stackB = Get-ConfigJson @('-p', 'platform-b', '-f', 'docker-compose.yml', '-f', 'docker-compose.oxigraph-host.yml')
} finally {
    foreach ($key in $previous.Keys) {
        if ($null -eq $previous[$key]) { Remove-Item "Env:$key" -ErrorAction SilentlyContinue }
        else { Set-Item "Env:$key" $previous[$key] }
    }
}
Assert-True ($stackB.name -eq 'platform-b') 'named project' $stackB.name
Assert-True ($stackB.services.postgres.container_name -eq 'platform-b-postgres') 'named postgres container' $stackB.services.postgres.container_name
Assert-True ($stackB.services.platform.ports[0].published -eq '8081') 'named api port' $stackB.services.platform.ports[0].published
Assert-True ($stackB.services.postgres.ports[0].published -eq '5433') 'named postgres port' $stackB.services.postgres.ports[0].published
Assert-True ($stackB.services.oxigraph.ports[0].published -eq '7879') 'opt-in oxigraph port' $stackB.services.oxigraph.ports[0].published
Assert-True ($stackB.services.platform.volumes[0].source -eq 'D:/agentABC/data-b') 'named data root' $stackB.services.platform.volumes[0].source

# --- 3. occupied port is rejected -----------------------------------------
$listener = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $listener) {
    Write-Host '[SKIP] no listening port available to provoke a conflict'
} else {
    $occupied = [int]$listener.LocalPort
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\stack.ps1') `
        up -Name stack-port-probe -ApiPort $occupied -PgPort 59992 -ReasonerPort 59993 `
        -EmbeddingPort 59994 -FusekiPort 59995 -DataRoot D:/agentABC/data-probe 2>&1
    $code = $LASTEXITCODE
    $text = ($output | Out-String)
    Assert-True ($code -ne 0) 'occupied port exits non-zero' "exit=$code port=$occupied"
    Assert-True ($text -match 'E_STACK_PORT_IN_USE') 'occupied port has clear error code'
}

# --- 4. ready probe honours its timeout ------------------------------------
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$output = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\stack.ps1') `
    status -Name stack-ready-probe -ApiPort 59999 -ProbeSeconds 2 2>&1
$code = $LASTEXITCODE
$sw.Stop()
$text = ($output | Out-String)
Assert-True ($code -ne 0) 'unready stack exits non-zero' "exit=$code"
Assert-True ($text -match 'E_STACK_NOT_READY') 'unready stack has clear error code'
Assert-True ($sw.Elapsed.TotalSeconds -lt 30) 'probe timed out near requested budget' ("elapsed={0:N1}s" -f $sw.Elapsed.TotalSeconds)

Write-Host ''
if ($script:failed -gt 0) {
    Write-Host "STACK-PARAMS failed=$($script:failed)"
    exit 1
}
Write-Host 'STACK-PARAMS passed=all failed=0'
exit 0
