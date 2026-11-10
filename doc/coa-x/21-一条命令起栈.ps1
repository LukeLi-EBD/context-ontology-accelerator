# One-command local stack for the COA control plane (M3b).
#
#   powershell -ExecutionPolicy Bypass -File doc/coa-x/21-一条命令起栈.ps1
#   ... -Reset        # delete containers + volumes first, start from zero
#   ... -Seed         # also load the FSLDM folios into one namespace
#   ... -Build        # rebuild the dependency image even if it exists
#
# Ports are fixed by doc/coa-x/stack/docker-compose.yml:
#   PG 6044, Oxigraph 7988 (loopback), engine 8812, bridge 8799.
# Nothing here touches the shared 8099/5173/8080/8082/7878/5444 stack.
#
# Messages are ASCII on purpose: Windows PowerShell 5.1 reads BOM-less UTF-8
# as ANSI and non-ASCII text would be mangled in the console.

[CmdletBinding()]
param(
    [switch]$Reset,
    [switch]$Seed,
    [switch]$Build,
    [int]$EnginePort = 0,
    [int]$TimeoutSeconds = 300
)

# Native tools (docker) write progress to stderr; with 'Stop' PowerShell 5.1
# turns that into a terminating NativeCommandError.  Keep 'Continue' and check
# every exit code explicitly instead.
$ErrorActionPreference = 'Continue'
# The engine's host publish defaults to 8812; pass -EnginePort when another
# worktree already owns that port.  The bridge always reaches it on the
# compose network as ontology-engine:8812, so this only affects manual curls.
if ($EnginePort -gt 0) { $env:COA_STACK_ENGINE_PORT = "$EnginePort" }
$ComposeFile = Join-Path $PSScriptRoot 'stack/docker-compose.yml'
$BridgeBase = 'http://127.0.0.1:8799'
$Image = 'coa-m3-local:dev'
# The contract validates namespace ids as UUID v4, so the probe namespace must
# carry the v4 version/variant nibbles (a zero-filled UUID is rejected with 400).
$Namespace = '550e8400-e29b-41d4-a716-446655440000'

function Invoke-Compose {
    # Arguments must arrive through an explicit array.  Bare `-d`/`-v` tokens
    # get eaten by PowerShell's own parameter binding (-Debug/-Verbose), which
    # silently turned `up -d` into an attached `up` and `down -v` into `down`.
    param([string[]]$ComposeArgs)
    $output = & docker compose -f $ComposeFile @ComposeArgs 2>&1 | Out-String
    if ($output.Trim()) { Write-Host $output.TrimEnd() }
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($ComposeArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Wait-Url {
    param([string]$Url, [int]$TimeoutSeconds)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($resp.StatusCode -eq 200) { return $true }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    return $false
}

function Get-Json {
    param([string]$Url)
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
    # The API answers application/json without a charset; PowerShell 5 would
    # otherwise decode UTF-8 labels as Latin-1 and print mojibake.
    $text = [System.Text.Encoding]::UTF8.GetString($resp.RawContentStream.ToArray())
    return ($text | ConvertFrom-Json)
}

Write-Host '[stack] checking docker...'
& docker version --format '{{.Server.Version}}' | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'docker daemon is not reachable'
}

$timer = [System.Diagnostics.Stopwatch]::StartNew()

if ($Reset) {
    Write-Host '[stack] -Reset: removing containers and volumes...'
    Invoke-Compose -ComposeArgs @('down', '--volumes', '--remove-orphans')
}

$imageExists = $false
& docker image inspect $Image 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { $imageExists = $true }

if ($Build -or -not $imageExists) {
    Write-Host '[stack] building dependency image (first run downloads wheels)...'
    $buildStart = Get-Date
    Invoke-Compose -ComposeArgs @('build')
    Write-Host ("[stack] image build took {0:n1}s" -f ((Get-Date) - $buildStart).TotalSeconds)
}

Write-Host '[stack] starting services (postgres -> migrate -> engine/bridge)...'
Invoke-Compose -ComposeArgs @('up', '--detach')

if ($Seed) {
    Write-Host "[stack] seeding namespace $Namespace ..."
    Invoke-Compose -ComposeArgs @('run', '--rm', 'seed')
}

Write-Host "[stack] waiting for $BridgeBase/health (timeout ${TimeoutSeconds}s)..."
if (-not (Wait-Url -Url "$BridgeBase/health" -TimeoutSeconds $TimeoutSeconds)) {
    Write-Host '[stack] FAILED: bridge did not become healthy. Recent logs:'
    & docker compose -f $ComposeFile logs --tail 80 bridge ontology-engine migrate
    throw 'bridge health check timed out'
}

$timer.Stop()
$readySeconds = [math]::Round($timer.Elapsed.TotalSeconds, 1)
Write-Host "[stack] bridge is up after ${readySeconds}s"
Write-Host ''

# ---- acceptance probes -----------------------------------------------------
$health = Get-Json -Url "$BridgeBase/system-health"
$namespaces = Get-Json -Url "$BridgeBase/namespaces"
$search = Get-Json -Url "$BridgeBase/namespaces/$Namespace/graph/search?q=Party&limit=5"

$nsCount = @($namespaces.namespaces).Count
if ($null -ne $search.total_count) {
    $hitCount = [int]$search.total_count
} else {
    $hitCount = @($search.hits).Count
}

Write-Host '---- results ----'
Write-Host ("/system-health            status={0}" -f $health.status)
foreach ($c in $health.components) {
    Write-Host ("  component {0,-16} {1}" -f $c.name, $c.status)
}
if ($health.schemaVersion) {
    Write-Host ("  schema code={0} db={1} consistent={2}" -f `
        $health.schemaVersion.codeVersion, $health.schemaVersion.dbVersion, $health.schemaVersion.consistent)
}
Write-Host ("/namespaces              HTTP 200, items={0}" -f $nsCount)
Write-Host ("/graph/search            HTTP 200, matches={0} (namespace={1})" -f $hitCount, $Namespace)
Write-Host ''
Write-Host ("[stack] total time to /health 200: {0}s" -f $readySeconds)
if ($Seed -eq $false) {
    Write-Host '[stack] note: -Seed not requested, so /graph/search returned an empty graph.'
}
Write-Host '[stack] stop: docker compose -f doc/coa-x/stack/docker-compose.yml down'
