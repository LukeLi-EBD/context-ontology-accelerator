# burst.ps1 - embedding throughput tier switch (S14H-17). NOT enabled by default.
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/burst.ps1 status
#   powershell -ExecutionPolicy Bypass -File scripts/burst.ps1 on
#   powershell -ExecutionPolicy Bypass -File scripts/burst.ps1 off
#   powershell -ExecutionPolicy Bypass -File scripts/burst.ps1 on -DryRun
# on  : embedding cpus 4->8, RAYON 3->8, max_chunks_per_sec 1.0->0 (unlimited)
# off : restore 4 cpus / RAYON 3 / rate 1.0, then smoke-embed 8/8 + /readyz
# Both on/off hold the heavy lock (compose-guard) and append a WORKLOG entry.
param(
    [Parameter(Position = 0)]
    [ValidateSet('on', 'off', 'status')]
    [string]$Command = 'status',
    [string]$Deadline = '',
    # S14H-CORES: explicit tier override for the 8 -> 12 -> 16 ladder test.
    [int]$Cpus = 0,
    [int]$Rayon = 0,
    [switch]$Force,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$owner = "$env:COMPUTERNAME\$env:USERNAME#$PID"
$guard = Join-Path $PSScriptRoot 'compose-guard.ps1'

function Get-BurstCpus {
    # S14H-BURST: never hard-code 8. <=8 logical -> total-2 (min 4); >=12 -> 8.
    $cores = [Environment]::ProcessorCount
    if ($cores -ge 12) { return 8 }
    if ($cores -le 8) { return [math]::Max(4, $cores - 2) }
    return 6
}

function Show-Deadline([string]$when) {
    if (-not $when) { return }
    try {
        $target = [datetime]::Parse($when)
        $left = $target - (Get-Date)
        Write-Host ("[burst] deadline={0} remaining={1:hh}h{2:mm}m" -f $target, $left, $left)
    } catch {
        Write-Host "[burst] deadline parse failed: $when"
    }
}

function Get-Cpus([string]$name) {
    $nano = docker inspect -f '{{.HostConfig.NanoCpus}}' $name 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $nano -or [double]$nano -le 0) { return 'n/a' }
    return [math]::Round([double]$nano / 1e9, 2)
}

function Get-Rayon([string]$name) {
    $envs = docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' $name 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $envs) { return 'n/a' }
    $line = $envs | Select-String '^RAYON_NUM_THREADS=' | Select-Object -First 1
    if (-not $line) { return 'unset' }
    return ($line.ToString().Trim() -replace '^RAYON_NUM_THREADS=', '')
}

function Get-Rate {
    try {
        return (Invoke-RestMethod -Uri 'http://127.0.0.1:8080/status' -TimeoutSec 5).providers.embedding.limits.max_chunks_per_sec
    } catch { return 'n/a' }
}

function Show-Tier {
    Write-Host ("[burst] cpus={0} rayon={1} rate={2}" -f `
        (Get-Cpus 'agent-platform-embedding'), (Get-Rayon 'agent-platform-embedding'), (Get-Rate))
}

if ($Command -eq 'status') {
    Show-Tier
    exit 0
}

if ($DryRun) {
    Show-Tier
    Write-Host "[burst] dry-run: would acquire heavy lock and switch tier=$Command; no container was changed."
    exit 0
}

$acquired = $false
try {
    & $guard acquire -Purpose "burst $Command" -TtlMinutes 30 -Owner $owner -Force:$Force
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[burst] E_BUILD_CONFLICT: heavy lock busy, refusing to switch.'
        exit 75
    }
    $acquired = $true

    $desiredRate = '0'
    if ($Command -eq 'on') {
        $cpus = if ($Cpus -gt 0) { $Cpus } else { Get-BurstCpus }
        $rayon = if ($Rayon -gt 0) { $Rayon } else { $cpus }
        Write-Host "[burst] logicalCores=$([Environment]::ProcessorCount) chosenCpus=$cpus chosenRayon=$rayon"
        Show-Deadline $Deadline
        $env:EMBEDDING_CPUS = "$cpus"
        $env:RAYON_NUM_THREADS = "$rayon"
        $env:EMBED_MAX_CHUNKS_PER_SEC = $desiredRate
    } else {
        $desiredRate = '1.0'
        $env:EMBEDDING_CPUS = '4'
        $env:RAYON_NUM_THREADS = '3'
        $env:EMBED_MAX_CHUNKS_PER_SEC = $desiredRate
    }

    # S14H-CORES: a core change only needs the embedding container. Recreating
    # platform would drop in-flight indexes and the locally synced sources, so
    # only touch it when the rate tier actually has to change.
    $currentRate = Get-Rate
    $rateNow = 0.0
    $rateOk = [double]::TryParse(([string]$currentRate).Trim(), [ref]$rateNow)
    $needPlatform = (-not $rateOk) -or ($rateNow -ne [double]$desiredRate)
    if ($needPlatform) { $services = @('embedding', 'platform') } else { $services = @('embedding') }
    Write-Host "[burst] services=$($services -join ',') currentRate=$currentRate desiredRate=$desiredRate"

    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    docker compose up -d --force-recreate @services *> (Join-Path $root "logs\burst-$Command.log")
    $composeExit = $LASTEXITCODE
    $ErrorActionPreference = $previous
    if ($composeExit -ne 0) {
        throw "compose up failed for burst $Command; see logs/burst-$Command.log"
    }
    if ($needPlatform) {
        # keep the dev sources in sync with the running image (no rebuild).
        $srcDir = Join-Path $root 'src\platform_core'
        if (Test-Path -LiteralPath $srcDir) {
            docker cp "$srcDir\." agent-platform-api:/app/src/platform_core | Out-Null
            docker restart agent-platform-api | Out-Null
            Write-Host '[burst] synced src/platform_core into platform and restarted it'
        }
    }

    # S14H-CORES: every tier switch must pass readyz + smoke-embed 8/8 before use.
    for ($i = 0; $i -lt 40; $i++) {
        try {
            if ((Invoke-WebRequest -Uri 'http://127.0.0.1:8080/readyz' -TimeoutSec 3).StatusCode -eq 200) { break }
        } catch { Start-Sleep -Seconds 2 }
    }
    $ready = (Invoke-WebRequest -Uri 'http://127.0.0.1:8080/readyz' -TimeoutSec 5).StatusCode
    $smoke = docker compose exec -T platform python -m platform_core.cli smoke-embed --config /data/platform.yaml 2>&1 | Select-Object -Last 1
    Write-Host "[burst] readyz=$ready"
    Write-Host "[burst] $smoke"
    if ($smoke -notmatch 'SMOKE (\d+)/\1') {
        Write-Host '[burst] SMOKE FAILED - switch this tier back before running bulk work'
        exit 1
    }

    Show-Tier
    Add-Content -LiteralPath (Join-Path $root 'WORKLOG.md') -Value `
        ("- {0} burst {1}: cpus={2} rayon={3} rate={4}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm'), $Command, `
            (Get-Cpus 'agent-platform-embedding'), (Get-Rayon 'agent-platform-embedding'), (Get-Rate))
} finally {
    if ($acquired) {
        & $guard release -Owner $owner | Out-Null
        Write-Host '[burst] guard released'
    }
}
