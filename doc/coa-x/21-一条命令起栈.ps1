# One-command local stack for the COA control plane (M3b).
#
#   powershell -ExecutionPolicy Bypass -File doc/coa-x/21-一条命令起栈.ps1
#   ... -Reset        # delete containers + volumes first, start from zero
#   ... -Seed         # also load the FSLDM folios into one namespace
#   ... -Build        # rebuild the dependency image even if it exists
#
# Host ports are auto-detected, starting from the preferred values in
# doc/coa-x/stack/docker-compose.yml (PG 6044, Oxigraph 7988, engine 8812,
# bridge 8799).  If a preferred port is taken by anything else, the script
# walks upward until it finds a free one and prints the choice.  Pass
# -PgPort/-OxigraphPort/-EnginePort/-BridgePort to pin a port; an explicitly
# pinned port that is busy is a hard error rather than a silent shift.
# Nothing here touches the shared 8099/5173/8080/8082/7878/5444 stack.
#
# The file is saved as UTF-8 with BOM so Windows PowerShell 5.1 renders the
# self-check table correctly.

[CmdletBinding()]
param(
    [switch]$Reset,
    [switch]$Seed,
    [switch]$Build,
    [int]$PgPort = 0,
    [int]$OxigraphPort = 0,
    [int]$EnginePort = 0,
    [int]$BridgePort = 0,
    [int]$TimeoutSeconds = 300
)

# Native tools (docker) write progress to stderr; with 'Stop' PowerShell 5.1
# turns that into a terminating NativeCommandError.  Keep 'Continue' and check
# every exit code explicitly instead.
$ErrorActionPreference = 'Continue'
$ComposeFile = Join-Path $PSScriptRoot 'stack/docker-compose.yml'
$Image = 'coa-m3-local:dev'
# The contract validates namespace ids as UUID v4, so the probe namespace must
# carry the v4 version/variant nibbles (a zero-filled UUID is rejected with 400).
$Namespace = '550e8400-e29b-41d4-a716-446655440000'
$ExpectedRoutes = 138

function Invoke-Compose {
    # Arguments must arrive through an explicit array.  Bare `-d`/`-v` tokens
    # get eaten by PowerShell's own parameter binding (-Debug/-Verbose), which
    # silently turned `up -d` into an attached `up` and `down -v` into `down`.
    param([string[]]$ComposeArgs)
    # Docker writes progress to stderr.  Convert those lines to plain strings
    # and silence the NativeCommandError records so the console only shows the
    # self-check table, not a wall of red noise.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        $output = & docker compose -f $ComposeFile @ComposeArgs 2>&1 | ForEach-Object { "$_" } | Out-String
    } finally {
        $ErrorActionPreference = $prev
    }
    if ($output.Trim()) { Write-Host $output.TrimEnd() }
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($ComposeArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Get-ContainerLine {
    param([string[]]$ComposeArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        $out = & docker compose -f $ComposeFile @ComposeArgs 2>&1 | ForEach-Object { "$_" }
    } finally {
        $ErrorActionPreference = $prev
    }
    $line = $out | Where-Object { "$_".Trim() } | Select-Object -Last 1
    if ($null -eq $line) { return '' }
    return "$line".Trim()
}

function Test-PortFree {
    param([int]$Port)
    $listener = $null
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener) { $listener.Stop() }
    }
}

function Resolve-Port {
    # Explicit > 0: keep it, but only if it is free (unless the running stack
    # already publishes it).  Explicit 0: reuse the running mapping when there
    # is one, otherwise walk upward from the preferred port.
    param([int]$Explicit, [int]$Preferred, [string]$Name, [int]$CurrentlyPublished = 0)
    if ($Explicit -gt 0) {
        if ($CurrentlyPublished -ne $Explicit -and -not (Test-PortFree -Port $Explicit)) {
            throw "$Name port $Explicit is already in use; pick another with -${Name}Port"
        }
        return $Explicit
    }
    if ($CurrentlyPublished -gt 0) { return $CurrentlyPublished }
    for ($p = $Preferred; $p -lt ($Preferred + 200); $p++) {
        if (Test-PortFree -Port $p) {
            if ($p -ne $Preferred) {
                Write-Host ("[stack] {0}: preferred {1} is busy, using free port {2}" -f $Name, $Preferred, $p)
            }
            return $p
        }
    }
    throw "${Name}: no free port in $Preferred..$($Preferred + 199)"
}

function Get-PublishedPort {
    param([string]$Service, [int]$ContainerPort)
    $line = & docker compose -f $ComposeFile port $Service $ContainerPort 2>$null
    if ($line -match ':(\d+)\s*$') { return [int]$Matches[1] }
    return 0
}

function Get-HttpStatus {
    param([string]$Url)
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
        return [int]$resp.StatusCode
    } catch {
        if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode }
        return -1
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

function Write-CheckRow {
    param([string]$Label, [string]$Value)
    Write-Host ("  {0,-22} {1}" -f $Label, $Value)
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

# ---- choose host ports -----------------------------------------------------
# If this stack is already running and we are not resetting it, reuse the
# mappings it actually published; auto-detecting then would see our own
# containers as conflict and shift every port on each restart.
$runningStack = $false
if (-not $Reset) {
    $services = @(& docker compose -f $ComposeFile ps --status running --format '{{.Service}}' 2>$null)
    $runningStack = $services -contains 'bridge'
}

if ($runningStack) {
    $publishedPg = Get-PublishedPort -Service 'postgres' -ContainerPort 5432
    $publishedOxigraph = Get-PublishedPort -Service 'oxigraph' -ContainerPort 7988
    $publishedEngine = Get-PublishedPort -Service 'ontology-engine' -ContainerPort 8812
    $publishedBridge = Get-PublishedPort -Service 'bridge' -ContainerPort 8799
} else {
    $publishedPg = 0
    $publishedOxigraph = 0
    $publishedEngine = 0
    $publishedBridge = 0
}
$PgPort = Resolve-Port -Explicit $PgPort -Preferred 6044 -Name 'Pg' -CurrentlyPublished $publishedPg
$OxigraphPort = Resolve-Port -Explicit $OxigraphPort -Preferred 7988 -Name 'Oxigraph' -CurrentlyPublished $publishedOxigraph
$EnginePort = Resolve-Port -Explicit $EnginePort -Preferred 8812 -Name 'Engine' -CurrentlyPublished $publishedEngine
$BridgePort = Resolve-Port -Explicit $BridgePort -Preferred 8799 -Name 'Bridge' -CurrentlyPublished $publishedBridge

$env:COA_STACK_PG_PORT = "$PgPort"
$env:COA_STACK_OXIGRAPH_PORT = "$OxigraphPort"
$env:COA_STACK_ENGINE_PORT = "$EnginePort"
$env:COA_STACK_BRIDGE_PORT = "$BridgePort"

$BridgeBase = "http://127.0.0.1:$BridgePort"
Write-Host ("[stack] host ports: PG={0} Oxigraph={1} engine={2} bridge={3}" -f `
    $PgPort, $OxigraphPort, $EnginePort, $BridgePort)

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

# ---- self-check (for the next person, not for debugging) -------------------
$health = Get-Json -Url "$BridgeBase/system-health"
$namespaces = Get-Json -Url "$BridgeBase/namespaces"
$search = Get-Json -Url "$BridgeBase/namespaces/$Namespace/graph/search?q=Party&limit=5"

$healthStatus = Get-HttpStatus -Url "$BridgeBase/health"
$systemHealthStatus = Get-HttpStatus -Url "$BridgeBase/system-health"
$namespacesStatus = Get-HttpStatus -Url "$BridgeBase/namespaces"
$searchStatus = Get-HttpStatus -Url "$BridgeBase/namespaces/$Namespace/graph/search?q=Party&limit=5"

$platformSchema = Get-ContainerLine -ComposeArgs @(
    'exec', '-T', 'postgres', 'psql', '-U', 'platform', '-d', 'platform',
    '-tAc', 'SELECT MAX(version) FROM platform.schema_version')
$serveLocalSchema = Get-ContainerLine -ComposeArgs @(
    'exec', '-T', 'postgres', 'psql', '-U', 'platform', '-d', 'serve_local',
    '-tAc', 'SELECT MAX(version) FROM platform.schema_version')
$routeCount = Get-ContainerLine -ComposeArgs @(
    'exec', '-T', 'bridge', 'python', '-c',
    "import sys; sys.path.insert(0,'/repo/doc/coa-x/tools'); import coa_api_local as m; print(len(m.ROUTES))")

$nsCount = @($namespaces.namespaces).Count
if ($null -ne $search.total_count) {
    $hitCount = [int]$search.total_count
} else {
    $hitCount = @($search.hits).Count
}
$consistent = $false
if ($null -ne $health.schemaVersion) { $consistent = [bool]$health.schemaVersion.consistent }

$routeVerdict = if ("$routeCount" -eq "$ExpectedRoutes") { "$routeCount (expected $ExpectedRoutes)" } else { "$routeCount (MISMATCH, expected $ExpectedRoutes)" }
$schemaVerdict = if ($consistent) { 'consistent=true' } else { 'consistent=FALSE' }
$overall = 'OK'
if ($systemHealthStatus -ne 200 -or $namespacesStatus -ne 200 -or -not $consistent -or "$routeCount" -ne "$ExpectedRoutes") {
    $overall = 'CHECK FAILED'
}

Write-Host ''
Write-Host '================ 起来了吗 ================'
Write-Host ("  结论                   {0}（到 /health 200 用时 {1}s）" -f $overall, $readySeconds)
Write-CheckRow 'host ports' ("PG={0} Oxigraph={1} engine={2} bridge={3}" -f $PgPort, $OxigraphPort, $EnginePort, $BridgePort)
Write-CheckRow 'platform.schema' ("{0} ({1})" -f $platformSchema, $schemaVerdict)
Write-CheckRow 'serve_local.schema' ("{0}" -f $serveLocalSchema)
Write-CheckRow 'bridge routes' $routeVerdict
Write-CheckRow 'GET /health' ("HTTP {0}" -f $healthStatus)
Write-CheckRow 'GET /system-health' ("HTTP {0}  status={1}" -f $systemHealthStatus, $health.status)
Write-CheckRow 'GET /namespaces' ("HTTP {0}  items={1}" -f $namespacesStatus, $nsCount)
Write-CheckRow 'GET /graph/search' ("HTTP {0}  matches={1}" -f $searchStatus, $hitCount)
Write-Host '  components:'
foreach ($c in $health.components) {
    Write-Host ("    {0,-16} {1}" -f $c.name, $c.status)
}
Write-Host ''

# Make an expected degraded state unmistakable.  Without this paragraph the
# next person reads "degraded" as "the stack is broken".
if ($health.status -ne 'healthy') {
    Write-Host '  为什么不是 healthy（预期内）：'
    $cm = $health.components | Where-Object { $_.name -eq 'contextManager' } | Select-Object -First 1
    if ($cm -and $cm.status -ne 'ok') {
        Write-Host '    - contextManager 未启动：本轮五个服务不含上下文服务（8091），该项恒为 error。'
    }
    if ($health.pointer -and -not $health.pointer.ok) {
        Write-Host ("    - tbox/current 指针为空：{0}。全新库尚未发布 T-Box 版本，属预期。" -f $health.pointer.status)
    }
    $other = @($health.components | Where-Object { $_.status -ne 'ok' -and $_.name -ne 'contextManager' })
    if ($other.Count -gt 0) {
        Write-Host '    - 以下异常不属于预期，需要排查：'
        foreach ($c in $other) {
            Write-Host ("      * {0} = {1} {2}" -f $c.name, $c.status, $c.detail)
        }
    }
    if (-not $health.pointer -or $health.pointer.ok) {
        Write-Host '    - 除上述项外没有额外异常。'
    }
}
Write-Host ''
Write-Host ("[stack] 本栈占用宿主端口: {0}(PG) {1}(Oxigraph) {2}(engine) {3}(bridge)" -f `
    $PgPort, $OxigraphPort, $EnginePort, $BridgePort)
if ($Seed -eq $false -and $hitCount -eq 0) {
    Write-Host '[stack] 未加 -Seed，/graph/search 针对空图返回 0 条属正常。'
}
Write-Host '[stack] stop: docker compose -f doc/coa-x/stack/docker-compose.yml down'
