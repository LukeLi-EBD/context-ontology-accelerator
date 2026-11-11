<#
.SYNOPSIS
  Isolated stack for the COA performance baseline (no shared ports touched).

.DESCRIPTION
  Ports (all loopback, all dedicated):
    PG          127.0.0.1:6144  container perf-baseline-pg
    Oxigraph    127.0.0.1:8088  container perf-baseline-oxigraph
    engine      127.0.0.1:8812  doc/coa-x/tools/coa_ontology_local.py
    context-mgr 127.0.0.1:8898  doc/coa-x/tools/run_local.py context-manager
    bridge      127.0.0.1:8899  doc/coa-x/tools/coa_api_local.py

  Never touches 8099/5173/7878/5444/8080/8082 and never restarts another
  session's containers.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\perf-baseline-stack.ps1 -Start
  powershell -ExecutionPolicy Bypass -File .\perf-baseline-stack.ps1 -Seed -Namespace <uuid>
  powershell -ExecutionPolicy Bypass -File .\perf-baseline-stack.ps1 -Stop
#>
[CmdletBinding()]
param(
    [switch]$Start,
    [switch]$Seed,
    [switch]$Stop,
    # With -Stop: leave PG/Oxigraph running, so restarting the Python processes
    # to pick up code changes does not drop the seeded dataset.
    [switch]$KeepContainers,
    # Run the runaway-query watchdog in the foreground. Oxigraph's --timeout-s
    # cancels most shapes but not a cross product over >=3 unbound GRAPH
    # variables (measured: still 99% CPU after 180 s). The watchdog restarts the
    # container once CPU stays pinned. It must call `docker restart` itself:
    # `docker kill` counts as a manual stop, and `unless-stopped` therefore does
    # NOT bring the container back (measured: exited 137, never restarted).
    # Do not run it during load.
    [switch]$Watchdog,
    [int]$WatchdogCpuPercent = 80,
    [int]$WatchdogSeconds = 90,
    [string]$Namespace = "3f2a9c1e-7b4d-4e2a-9c6f-1a2b3c4d5e6f"
)

$ErrorActionPreference = "Stop"

$Repo    = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Tools   = Join-Path $Repo "doc\coa-x\tools"
$Python  = "D:\agentABC\coa\.venv-coa-local\Scripts\python.exe"
$RunDir  = Join-Path $env:TEMP "perf-baseline"
$PgName  = "perf-baseline-pg"
$OxiName = "perf-baseline-oxigraph"
$PlatformDsn = "postgresql://platform:platform_dev@127.0.0.1:6144/platform"
$ServeDsn    = "postgresql://platform:platform_dev@127.0.0.1:6144/serve_local"

if (-not (Test-Path $Python)) { throw "venv python not found: $Python" }
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Test-PortListening([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Port([int]$Port, [string]$Name, [int]$Seconds = 60) {
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Test-PortListening $Port) { Write-Host ("  [ok] {0} :{1}" -f $Name, $Port); return }
        Start-Sleep -Seconds 1
    }
    throw ("{0} did not listen on :{1} within {2}s" -f $Name, $Port, $Seconds)
}

function Get-ContainerRunning([string]$Name) {
    try {
        $state = docker inspect -f "{{.State.Running}}" $Name 2>$null
        return ($LASTEXITCODE -eq 0 -and $state.Trim() -eq "true")
    } catch {
        return $false
    }
}

function Test-ContainerExists([string]$Name) {
    try {
        docker inspect $Name 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Stop-PortOwner([int]$Port, [string]$Marker) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) { Write-Host ("  [--] :{0} not listening" -f $Port); return }
    $procId = ($conn | Select-Object -First 1).OwningProcess
    $proc = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $procId) -ErrorAction SilentlyContinue
    if ($proc -and $proc.CommandLine -like ("*" + $Marker + "*")) {
        Write-Host ("  [stop] {0} pid={1} (:{2})" -f $Marker, $procId, $Port)
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host ("  [skip] :{0} owned by pid={1}, not {2}" -f $Port, $procId, $Marker)
    }
}

function Set-StackEnv() {
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    # engine
    $env:COA_PROVIDER_ONTOLOGY_GRAPH = "oxigraph"
    $env:COA_ONTOLOGY_OXIGRAPH_URL = "http://127.0.0.1:8088"
    $env:COA_PROVIDER_ONTOLOGY_REGISTRY = "postgres"
    $env:COA_PROVIDER_ONTOLOGY_JOBS = "postgres"
    $env:COA_PROVIDER_ONTOLOGY_OBJECTS = "fs"
    $env:COA_PROVIDER_ONTOLOGY_VECTOR = "pgvector"
    $env:COA_PROVIDER_ONTOLOGY_EMBEDDING = "http"
    $env:COA_CONTROL_PLANE_PG_DSN = $PlatformDsn
    $env:DYNAMODB_TABLE = "coa-local-ontologies"
    $env:NDB_GRAPH_URI_BASE = "https://coa.local/graph"
    $env:COA_LOCAL_GRAPH_ALLOWED_EXTRA_PREFIXES = "https://coa.local/graph"
    $env:COA_ONTOLOGY_PORT = "8812"
    $env:COA_LOCAL_OBJECT_ROOT = (Join-Path $RunDir "objects")
    $env:COA_LOCAL_OBJECT_BASE = "http://127.0.0.1:8899/_local/objects"
    $env:COA_EMBEDDING_URL = "http://127.0.0.1:8081/v1"
    $env:COA_EMBEDDING_MODEL = "BAAI/bge-m3"
    $env:COA_EMBEDDING_DIMENSIONS = "1024"
    $env:COA_VECTOR_DIMENSIONS = "1024"
    # bridge
    $env:COA_LOCAL_API_PORT = "8899"
    $env:ONTOLOGY_ENGINE_ENDPOINT = "http://127.0.0.1:8812"
    $env:COA_CONTEXT_MANAGER_ENDPOINT = "http://127.0.0.1:8898"
    $env:PLATFORM__DATABASE__URL = $ServeDsn
    $env:PLATFORM__GRAPH__ENDPOINT = "http://127.0.0.1:8088"
    $env:PLATFORM__EMBEDDING__ENDPOINT = "http://127.0.0.1:8081/v1"
    $env:COA_GRAPH_OXIGRAPH_URL = "http://127.0.0.1:8088"
    $env:COA_PROVIDER_METRIC_GRAPH = "oxigraph"
    # context-manager
    $env:COA_PROVIDER_CONFIG = "env"
    $env:COA_PROVIDER_SECRETS = "env"
    $env:COA_PROVIDER_EMBEDDING = "bge-local"
    $env:COA_EMBEDDING_BGE_ENDPOINT = "http://127.0.0.1:8081/v1"
    $env:COA_PROVIDER_GRAPH = "oxigraph"
    $env:COA_PROVIDER_GRAPH_ADMIN = "oxigraph"
    $env:COA_PROVIDER_METRIC_INDEX = "platform-pg"
    $env:COA_PROVIDER_VECTOR = "platform-pgvector"
    $env:COA_VECTOR_PG_DSN = $ServeDsn
    $env:COA_PROVIDER_METADATA_STORE = "postgres"
    $env:COA_METADATA_PG_DSN = $ServeDsn
    $env:COA_PROVIDER_QUERY_EXECUTOR = "postgres"
    $env:COA_EXECUTOR_POSTGRES_DSN = $ServeDsn
    $env:COA_PROVIDER_WAREHOUSE_ADMIN = "postgres"
    $env:COA_WAREHOUSE_ADMIN_PG_DSN = $ServeDsn
    $env:COA_METRIC_INDEX_PG_DSN = $ServeDsn
    $env:GRAPH_URI_TEMPLATE = "https://coa.local/graph/{namespace}"
    $env:COA_PROVIDER_AUTHORIZATION = "local-file"
    $env:COA_AUTHORIZATION_FILE = (Join-Path $RunDir "authz.json")
    $env:RESOLVE_TIMEOUT_S = "420"
    $env:SERVE_VKG_TRANSLATION_TIMEOUT_S = "60"
}

Set-StackEnv

if ($Watchdog) {
    # CPU-pinning watchdog. A cheap probe is not enough: during a runaway the
    # store still answers `SELECT ... LIMIT` in ~230 ms, so only CPU tells us a
    # query escaped --timeout-s.
    Write-Host ("Watching {0}: restart when CPU >= {1}% for {2}s" -f $OxiName, $WatchdogCpuPercent, $WatchdogSeconds)
    $interval = 5
    $pinned = 0
    while ($true) {
        $raw = docker stats --no-stream --format "{{.CPUPerc}} {{.MemUsage}}" $OxiName 2>$null
        $cpu = 0.0
        if ($raw -match "([0-9.]+)%") { $cpu = [double]$Matches[1] }
        if ($cpu -ge $WatchdogCpuPercent) { $pinned += $interval } else { $pinned = 0 }
        Write-Host ("  [{0}] cpu={1:N1}% {2} pinned={3}s" -f (Get-Date -Format "HH:mm:ss"), $cpu, ($raw -replace "^[0-9.]+% ", ""), $pinned)
        if ($pinned -ge $WatchdogSeconds) {
            $before = docker inspect -f "{{.State.StartedAt}}" $OxiName 2>$null
            Write-Host ("  [{0}] pinned >= {1}s -> docker restart {2} (started {3}); no manual action" -f (Get-Date -Format "HH:mm:ss"), $WatchdogSeconds, $OxiName, $before)
            docker restart $OxiName | Out-Null
            Start-Sleep -Seconds 6
            $after = docker inspect -f "{{.State.Status}} started {{.State.StartedAt}}" $OxiName 2>$null
            Write-Host ("  [{0}] back up: {1}" -f (Get-Date -Format "HH:mm:ss"), $after)
            $pinned = 0
        }
        Start-Sleep -Seconds $interval
    }
}

if ($Stop) {
    Write-Host "Stopping perf-baseline stack"
    Stop-PortOwner 8899 "coa_api_local.py"
    Stop-PortOwner 8812 "coa_ontology_local.py"
    Stop-PortOwner 8898 "run_local.py"
    foreach ($name in @($PgName, $OxiName)) {
        if ($KeepContainers) {
            Write-Host ("  [keep] container {0}" -f $name)
            continue
        }
        if (Get-ContainerRunning $name) { Write-Host ("  [stop] container {0}" -f $name); docker stop $name | Out-Null }
    }
    Write-Host "Done."
    return
}

if ($Start) {
    Write-Host "Starting perf-baseline stack"
    if (-not (Get-ContainerRunning $PgName)) {
        if (Test-ContainerExists $PgName) { docker start $PgName | Out-Null }
        else {
            docker run -d --name $PgName --publish 127.0.0.1:6144:5432 `
                -e POSTGRES_USER=platform -e POSTGRES_PASSWORD=platform_dev -e POSTGRES_DB=platform `
                -v perf-baseline-pg-data:/var/lib/postgresql/18/docker pgvector/pgvector:pg18-trixie | Out-Null
        }
    }
    if (-not (Get-ContainerRunning $OxiName)) {
        if (Test-ContainerExists $OxiName) { docker start $OxiName | Out-Null }
        else {
            # --timeout-s is the only thing that actually stops a query: closing
            # the HTTP connection leaves Oxigraph evaluating it (measured ~1 core
            # held afterwards). --cpus/--memory bound the blast radius, and
            # `--restart unless-stopped` brings the store back if it is OOM-killed.
            # 20 s sits above the slowest accepted route (statements ~10 s at 100k)
            # and below the 28 s gateway budget.
            docker run -d --name $OxiName --publish 127.0.0.1:8088:7878 `
                --cpus 2 --memory 2g --restart unless-stopped `
                -v perf-baseline-oxigraph-data:/data oxigraph/oxigraph:0.5.7 serve --location /data --bind 0.0.0.0:7878 --timeout-s 20 | Out-Null
        }
    }
    Wait-Port 6144 "perf-pg" 90
    Wait-Port 8088 "perf-oxigraph" 60

    $serveExists = docker exec $PgName psql -U platform -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='serve_local'" 2>$null
    if (-not ($serveExists -match "1")) {
        docker exec $PgName psql -U platform -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE serve_local" | Out-Null
    }
    foreach ($dsn in @($PlatformDsn, $ServeDsn)) {
        & $Python (Join-Path $Tools "local_bootstrap.py") migrate --dsn $dsn | Out-Null
        if ($LASTEXITCODE -ne 0) { throw ("migration failed: {0}" -f $dsn) }
    }

    $authz = '{"policies":{"default":"// local baseline: no static forbids","platform-admin":"permit(principal, action, resource);"},"principals":{"User::local-user":[{"resourceId":"GLOBAL","role":"platform-admin"}]}}'
    [System.IO.File]::WriteAllText($env:COA_AUTHORIZATION_FILE, $authz, (New-Object System.Text.UTF8Encoding($false)))

    if (-not (Test-PortListening 8812)) {
        Start-Process -FilePath $Python -ArgumentList "doc\coa-x\tools\coa_ontology_local.py" `
            -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $RunDir "engine-8812.log") `
            -RedirectStandardError  (Join-Path $RunDir "engine-8812.err.log") | Out-Null
        Wait-Port 8812 "engine" 120
    } else { Write-Host "  [ok] engine already listening on :8812" }

    if (-not (Test-PortListening 8898)) {
        Start-Process -FilePath $Python -ArgumentList "doc\coa-x\tools\run_local.py", "context-manager", "--port", "8898" `
            -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $RunDir "ctx-8898.log") `
            -RedirectStandardError  (Join-Path $RunDir "ctx-8898.err.log") | Out-Null
        Wait-Port 8898 "context-manager" 90
    } else { Write-Host "  [ok] context-manager already listening on :8898" }

    if (-not (Test-PortListening 8899)) {
        Start-Process -FilePath $Python -ArgumentList "doc\coa-x\tools\coa_api_local.py" `
            -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $RunDir "bridge-8899.log") `
            -RedirectStandardError  (Join-Path $RunDir "bridge-8899.err.log") | Out-Null
        Wait-Port 8899 "bridge" 120
    } else { Write-Host "  [ok] bridge already listening on :8899" }

    Write-Host "Stack up: PG 6144 | Oxigraph 8088 | engine 8812 | ctx 8898 | bridge 8899"
    return
}

if ($Seed) {
    Write-Host ("Seeding base ontology into namespace {0}" -f $Namespace)
    & $Python (Join-Path $Tools "coa_ontology_local.py") --seed --namespace $Namespace
    if ($LASTEXITCODE -ne 0) { throw "seed failed" }
    return
}
