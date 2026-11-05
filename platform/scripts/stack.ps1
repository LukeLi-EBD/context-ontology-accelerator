# stack.ps1 - parameterised docker compose stack (up / status / down).
#
# Defaults reproduce the historical single stack exactly:
#   name=agent-platform, api=8080, pg=5432, reasoner=7879, embedding=8081,
#   fuseki=3030, oxigraph not published, data root=D:/agentABC/data.
#
# Parallel stack example (short-lived verification only):
#   powershell -ExecutionPolicy Bypass -File scripts/stack.ps1 up -Name platform-b `
#     -ApiPort 8081 -PgPort 5433 -OxigraphPort 7879 -DataRoot D:/agentABC/data-b `
#     -Services postgres,oxigraph,platform
#
# Notes:
#   * Two stacks never share named volumes (compose scopes them by project) and
#     never share the bind data root (PLATFORM_DATA_ROOT).
#   * The heavy lock is per-stack: same stack still mutex, cross-stack is
#     intentionally not mutex; the 12-core Docker VM budget is the real limiter.
#   * Oxigraph has no auth, so its host port is opt-in via -OxigraphPort; the
#     default (0) keeps the base compose file without any host mapping.
param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'status', 'down', 'help')]
    [string]$Action = 'status',
    [string]$Name = 'agent-platform',
    [int]$ApiPort = 8080,
    [int]$PgPort = 5432,
    [int]$ReasonerPort = 7879,
    [int]$EmbeddingPort = 8081,
    [int]$FusekiPort = 3030,
    [int]$OxigraphPort = 0,
    [string]$DataRoot = 'D:/agentABC/data',
    [string[]]$Services = @(),
    [int]$WaitSeconds = 180,
    [int]$ProbeSeconds = 5,
    [switch]$RemoveDataRoot,
    [switch]$AssumeLock,
    [string]$Owner = ''
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
# -File passes "a,b,c" as one string; normalise both spellings to a service list.
$Services = @($Services | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$composeFiles = @('-f', 'docker-compose.yml')
$useOxigraphPort = ($OxigraphPort -gt 0)
if ($useOxigraphPort) { $composeFiles += @('-f', 'docker-compose.oxigraph-host.yml') }

# Compose bind mounts want forward slashes; keep the caller's display form too.
$dataRootNormalized = ($DataRoot -replace '\\', '/')

function Set-StackEnv {
    $env:COMPOSE_PROJECT_NAME = $Name
    $env:PLATFORM_PORT = "$ApiPort"
    $env:POSTGRES_PORT = "$PgPort"
    $env:REASONER_PORT = "$ReasonerPort"
    $env:EMBEDDING_PORT = "$EmbeddingPort"
    $env:FUSEKI_PORT = "$FusekiPort"
    $env:PLATFORM_DATA_ROOT = $dataRootNormalized
    if ($useOxigraphPort) { $env:OXIGRAPH_PORT = "$OxigraphPort" }
}

function Invoke-Compose {
    param([string[]]$ComposeArgs)
    $all = @('-p', $Name) + $composeFiles + $ComposeArgs
    & docker compose @all
    if ($LASTEXITCODE -ne 0) { throw "docker compose $($ComposeArgs -join ' ') failed (exit=$LASTEXITCODE)" }
}

function Get-PortListeners([int]$Port) {
    return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Get-ProjectContainersOnPort([int]$Port) {
    $names = & docker ps --filter "label=com.docker.compose.project=$Name" --filter "publish=$Port" --format "{{.Names}}" 2>$null
    return @($names | Where-Object { $_ })
}

function Test-Ready([int]$TimeoutSeconds) {
    $url = "http://127.0.0.1:$ApiPort/readyz"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = 'no response'
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec ([math]::Min(5, $TimeoutSeconds))
            if ($response.StatusCode -eq 200) { return $true }
            $lastError = "HTTP $($response.StatusCode)"
        }
        catch { $lastError = $_.Exception.Message }
        Start-Sleep -Seconds 2
    }
    Write-Host "[stack] E_STACK_NOT_READY: $url did not return 200 within ${TimeoutSeconds}s ($lastError)"
    return $false
}

function Get-DataRootDefault {
    return 'D:/agentABC/data'
}

function Initialize-DataRoot {
    if ($dataRootNormalized -eq (Get-DataRootDefault)) { return }
    $path = $dataRootNormalized -replace '/', [IO.Path]::DirectorySeparatorChar
    foreach ($sub in @('', 'blobs', 'tmp', 'shapes', 'ontology')) {
        $dir = if ($sub) { Join-Path $path $sub } else { $path }
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $config = Join-Path $path 'platform.yaml'
    if (-not (Test-Path -LiteralPath $config)) {
        Copy-Item -LiteralPath (Join-Path $root 'platform.example.yaml') -Destination $config
        Write-Host "[stack] seeded $config from platform.example.yaml (database.url is overridden by compose env)"
    }
    $bootstrap = Join-Path $path 'ontology/bootstrap.ttl'
    if (-not (Test-Path -LiteralPath $bootstrap)) {
        $source = Join-Path ((Get-DataRootDefault) -replace '/', [IO.Path]::DirectorySeparatorChar) 'ontology/bootstrap.ttl'
        if (Test-Path -LiteralPath $source) {
            Copy-Item -LiteralPath $source -Destination $bootstrap
            Write-Host "[stack] seeded $bootstrap from the default data root"
        }
    }
    $targetShapes = Join-Path $path 'shapes'
    $sourceShapes = Join-Path ((Get-DataRootDefault) -replace '/', [IO.Path]::DirectorySeparatorChar) 'shapes'
    $existingShapes = @(Get-ChildItem -LiteralPath $targetShapes -Recurse -File -ErrorAction SilentlyContinue)
    if ((Test-Path -LiteralPath $sourceShapes) -and $existingShapes.Count -eq 0) {
        Copy-Item -Path (Join-Path $sourceShapes '*') -Destination $targetShapes -Recurse -Force
        Write-Host "[stack] seeded $targetShapes from the default data root"
    }
}

function Assert-PortsFreeOrOurs {
    $ports = [ordered]@{
        api       = $ApiPort
        postgres  = $PgPort
        reasoner  = $ReasonerPort
        embedding = $EmbeddingPort
        fuseki    = $FusekiPort
    }
    if ($useOxigraphPort) { $ports['oxigraph'] = $OxigraphPort }
    if ($Services.Count -gt 0) {
        $wanted = @{}
        foreach ($service in $Services) { $wanted[$service.ToLowerInvariant()] = $true }
        $mapped = [ordered]@{
            platform  = 'api'
            postgres  = 'postgres'
            oxigraph  = 'oxigraph'
            reasoner  = 'reasoner'
            embedding = 'embedding'
            fuseki    = 'fuseki'
        }
        $filtered = [ordered]@{}
        foreach ($service in $wanted.Keys) {
            $key = $mapped[$service]
            if ($key -and $ports.Contains($key)) { $filtered[$key] = $ports[$key] }
        }
        $ports = $filtered
    }
    $conflicts = @()
    foreach ($entry in $ports.GetEnumerator()) {
        $listeners = Get-PortListeners $entry.Value
        if ($listeners.Count -eq 0) { continue }
        $ours = Get-ProjectContainersOnPort $entry.Value
        if ($ours.Count -gt 0) { continue }
        $pidValue = ($listeners | Select-Object -First 1).OwningProcess
        $procName = (Get-Process -Id $pidValue -ErrorAction SilentlyContinue).ProcessName
        $conflicts += "[stack] E_STACK_PORT_IN_USE: $($entry.Key) host port $($entry.Value) is used by pid=$pidValue process=$procName (not project '$Name'). Pick another port or stop the other stack."
    }
    if ($conflicts.Count -gt 0) {
        $conflicts | ForEach-Object { Write-Host $_ }
        exit 1
    }
}

Set-StackEnv

switch ($Action) {
    'up' {
        $guardArgs = @{ Command = 'check'; Stack = $Name }
        if ($AssumeLock) { $guardArgs['Owner'] = $Owner }
        & (Join-Path $PSScriptRoot 'compose-guard.ps1') @guardArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[stack] E_STACK_LOCK_BUSY: stack '$Name' has a heavy task holding its lock; refusing to start."
            exit 75
        }

        Assert-PortsFreeOrOurs
        Initialize-DataRoot

        $already = (Get-ProjectContainersOnPort $ApiPort).Count -gt 0
        if ($already) {
            Write-Host "[stack] project '$Name' already publishes api port $ApiPort; skipping compose up."
        } else {
            $upArgs = @('up', '-d')
            if ($Services.Count -gt 0) { $upArgs += $Services }
            Write-Host "[stack] docker compose $($upArgs -join ' ') (project=$Name data=$dataRootNormalized)"
            Invoke-Compose -ComposeArgs $upArgs
        }

        Write-Host "[stack] waiting for /readyz on 127.0.0.1:$ApiPort (timeout ${WaitSeconds}s) ..."
        if (-not (Test-Ready $WaitSeconds)) {
            & docker compose -p $Name $composeFiles ps
            exit 1
        }
        & docker compose -p $Name $composeFiles ps
        Write-Host "[stack] ready: http://127.0.0.1:$ApiPort/readyz"
        exit 0
    }

    'status' {
        & (Join-Path $PSScriptRoot 'compose-guard.ps1') status -Stack $Name
        & docker compose -p $Name $composeFiles ps 2>$null
        if (Test-Ready $ProbeSeconds) {
            Write-Host "[stack] ready: http://127.0.0.1:$ApiPort/readyz"
            exit 0
        }
        exit 1
    }

    'down' {
        Write-Host "[stack] docker compose down -v --remove-orphans (project=$Name)"
        Invoke-Compose -ComposeArgs @('down', '-v', '--remove-orphans')
        if ($RemoveDataRoot) {
            if ($dataRootNormalized -eq (Get-DataRootDefault)) {
                Write-Host "[stack] refuse to remove the default data root; run it manually if truly intended."
            } else {
                $path = $dataRootNormalized -replace '/', [IO.Path]::DirectorySeparatorChar
                if (Test-Path -LiteralPath $path) {
                    Remove-Item -LiteralPath $path -Recurse -Force
                    Write-Host "[stack] removed bind data root $path"
                }
            }
        }
        $containers = @(& docker ps -a --filter "label=com.docker.compose.project=$Name" --format "{{.Names}}" 2>$null)
        $volumes = @(& docker volume ls --filter "label=com.docker.compose.project=$Name" --format "{{.Name}}" 2>$null)
        $containers = @($containers | Where-Object { $_ })
        $volumes = @($volumes | Where-Object { $_ })
        Write-Host "[stack] residual containers for '$Name': $(if ($containers.Count) { $containers -join ', ' } else { 'none' })"
        Write-Host "[stack] residual volumes for '$Name': $(if ($volumes.Count) { $volumes -join ', ' } else { 'none' })"
        exit 0
    }

    default {
        Write-Host 'usage: stack.ps1 {up|status|down} [-Name agent-platform] [-ApiPort 8080] [-PgPort 5432]'
        Write-Host '       [-ReasonerPort 7879] [-EmbeddingPort 8081] [-FusekiPort 3030] [-OxigraphPort 0]'
        Write-Host '       [-DataRoot D:/agentABC/data] [-Services postgres,oxigraph,platform]'
        Write-Host '       [-WaitSeconds 180] [-ProbeSeconds 5] [-RemoveDataRoot]'
        exit 0
    }
}
