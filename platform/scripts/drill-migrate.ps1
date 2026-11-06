# drill-migrate.ps1 - export -> second stack -> import -> number comparison.
#
# It never stops, recreates or writes the default stack: the only action on the
# source stack is a read-only export-bundle. All writes go to the drill stack.
#
#   powershell -ExecutionPolicy Bypass -File scripts/drill-migrate.ps1 -DryRun
#   powershell -ExecutionPolicy Bypass -File scripts/drill-migrate.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/drill-migrate.ps1 -ResetTarget
#
# -ResetTarget tears the drill stack and its own data root down before starting
# again ("down -v -RemoveDataRoot"), which is required when the target database
# already holds data (import refuses with E_BUNDLE_TARGET_NOT_EMPTY otherwise).
param(
    [string]$SourceStack = 'agent-platform',
    [int]$SourceApiPort = 8080,
    [string]$SourceDataRoot = 'D:/agentABC/data',
    [string]$TargetStack = 'platform-drill',
    [int]$TargetApiPort = 8083,
    [int]$TargetPgPort = 5434,
    [int]$TargetReasonerPort = 7884,
    [int]$TargetOxigraphPort = 7882,
    [string]$TargetDataRoot = 'D:/agentABC/data-drill',
    [string]$Tag = '',
    [switch]$ResetTarget,
    [switch]$DryRun,
    [switch]$KeepTarget
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$stack = Join-Path $PSScriptRoot 'stack.ps1'
if (-not $Tag) { $Tag = 'drill-' + (Get-Date -Format 'yyyyMMddHHmmss') }

function Write-Plan([string]$text) {
    Write-Host ("[{0}] {1}" -f ($(if ($DryRun) { 'dry-run' } else { 'run' })), $text)
}

function Invoke-Docker([string[]]$arguments) {
    Write-Host ("+ docker " + ($arguments -join ' '))
    if ($DryRun) { return }
    & docker @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker command failed with exit code $LASTEXITCODE"
    }
}

function ContainerExists([string]$name) {
    $id = & docker ps -a --filter "name=^/$name$" --format '{{.ID}}'
    return [bool]$id
}

function Get-Counts([string]$container) {
    $tables = @(
        'document', 'document_chunk', 'chunk_embedding', 'document_page',
        'metric_definition', 'metric_observation',
        'ins_payment_record', 'loan_installment_plan', 'fact_event'
    )
    $sql = ($tables | ForEach-Object {
        if ($_ -eq 'chunk_embedding') {
            # The bundle only carries the active model partition; rows left
            # behind by other models (e.g. fake-hash smoke rows) are not migrated.
            "SELECT 'chunk_embedding='||COUNT(*) FROM platform.chunk_embedding c " +
                "JOIN platform.embedding_pointer p ON p.model = c.model AND p.id"
        } else {
            "SELECT '$_='||COUNT(*) FROM platform.$_"
        }
    }) -join ' UNION ALL '
    $lines = & docker exec $container psql -U platform -d platform -t -A -c $sql
    $counts = @{}
    foreach ($line in ($lines -split "`n")) {
        $line = $line.Trim()
        if ($line -match '^([a-z_]+)=(\d+)$') {
            $counts[$Matches[1]] = [int64]$Matches[2]
        }
    }
    return $counts
}

if (-not $DryRun -and -not (ContainerExists "$SourceStack-api")) {
    throw "source container $SourceStack-api not found; start the default stack first"
}

# 1) read-only export on the source stack --------------------------------------
Write-Plan "export $Tag from $SourceStack (read-only)"
Invoke-Docker @(
    'exec', "$SourceStack-api", 'python', '-m', 'platform_core.cli', 'export-bundle',
    '--config', '/data/platform.yaml', '--out', '/data/freeze', '--tag', $Tag
)

# 2) make sure the drill stack is up -------------------------------------------
$stackArgs = @(
    '-ExecutionPolicy', 'Bypass', '-File', $stack
)
if ($ResetTarget) {
    Write-Plan "reset $TargetStack (down -v) and remove $TargetDataRoot"
    Write-Host ("+ powershell " + ($stackArgs -join ' ') + " down -Name $TargetStack -DataRoot $TargetDataRoot -RemoveDataRoot")
    if (-not $DryRun) {
        & powershell @stackArgs down -Name $TargetStack -DataRoot $TargetDataRoot -RemoveDataRoot
        if ($LASTEXITCODE -ne 0) { throw "stack.ps1 down failed" }
    }
}
Write-Plan "start $TargetStack on $TargetApiPort/$TargetPgPort/$TargetReasonerPort/$TargetOxigraphPort"
Write-Host ("+ powershell " + ($stackArgs -join ' ') + " up -Name $TargetStack -ApiPort $TargetApiPort -PgPort $TargetPgPort -ReasonerPort $TargetReasonerPort -OxigraphPort $TargetOxigraphPort -DataRoot $TargetDataRoot -Services postgres,oxigraph,platform,reasoner")
if (-not $DryRun) {
    & powershell @stackArgs up -Name $TargetStack -ApiPort $TargetApiPort -PgPort $TargetPgPort `
        -ReasonerPort $TargetReasonerPort -OxigraphPort $TargetOxigraphPort `
        -DataRoot $TargetDataRoot -Services postgres,oxigraph,platform,reasoner
    if ($LASTEXITCODE -ne 0) { throw "stack.ps1 up failed" }
}

# 3) stage the bundle inside the target data root ------------------------------
$sourceBundle = Join-Path ($SourceDataRoot -replace '/', [IO.Path]::DirectorySeparatorChar) "freeze/$Tag"
$targetBundle = Join-Path ($TargetDataRoot -replace '/', [IO.Path]::DirectorySeparatorChar) "freeze/$Tag"
if (Test-Path -LiteralPath $sourceBundle) {
    Write-Plan "copy $sourceBundle -> $targetBundle"
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targetBundle) | Out-Null
        if (Test-Path -LiteralPath $targetBundle) { Remove-Item -Recurse -Force $targetBundle }
        Copy-Item -Recurse -LiteralPath $sourceBundle -Destination $targetBundle
    }
} else {
    Write-Host "WARNING: bundle not found at $sourceBundle (dry-run?)"
}

$containerBundle = "/data/freeze/$Tag"

# 4) import into the (empty) drill platform database ---------------------------
Write-Plan "import $containerBundle into $TargetStack/platform"
Invoke-Docker @(
    'exec', "$TargetStack-api", 'python', '-m', 'platform_core.cli', 'import-bundle',
    '--config', '/data/platform.yaml', '--bundle', $containerBundle,
    '--database', 'platform', '--into-empty-platform', '--keep-db-on-failure'
)

# 5) number comparison ---------------------------------------------------------
if ($DryRun) {
    Write-Plan "compare counts: documents/chunks/embeddings/pages/metrics/entities/facts"
    Write-Host "dry-run complete; nothing was changed."
    exit 0
}

$src = Get-Counts "$SourceStack-postgres"
$dst = Get-Counts "$TargetStack-postgres"
$keys = @(
    'document', 'document_chunk', 'chunk_embedding', 'document_page',
    'metric_definition', 'metric_observation',
    'ins_payment_record', 'loan_installment_plan', 'fact_event'
)
$failed = 0
Write-Host ""
Write-Host ("{0,-24} {1,10} {2,10}  {3}" -f 'table', 'source', 'target', 'result')
foreach ($key in $keys) {
    $a = if ($src.ContainsKey($key)) { $src[$key] } else { 'n/a' }
    $b = if ($dst.ContainsKey($key)) { $dst[$key] } else { 'n/a' }
    $ok = ($a -ne 'n/a' -and $a -eq $b)
    $label = if ($ok) { 'OK' } else { 'MISMATCH'; }
    if (-not $ok) { $failed++ }
    Write-Host ("{0,-24} {1,10} {2,10}  {3}" -f $key, $a, $b, $label)
}
Write-Host ""
if ($failed -gt 0) {
    Write-Host "MISMATCH: $failed table(s) differ; target stack kept for inspection."
    exit 2
}
Write-Host "all $($keys.Count) table counts match (chunk_embedding limited to the active model);"
Write-Host "T-Box/terms/metric hashes/ledger chain were asserted by import checks[]."
if (-not $KeepTarget) {
    Write-Host "target stack '$TargetStack' is left running on port $TargetApiPort; tear it down with:"
    Write-Host "  powershell -File scripts/stack.ps1 down -Name $TargetStack -DataRoot $TargetDataRoot -RemoveDataRoot"
}
exit 0
