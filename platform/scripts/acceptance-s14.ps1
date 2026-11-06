# S14 acceptance: run the FULL unittest tree in platform/tests inside the platform
# image and print one unified summary.
#
# Coverage rule (2026-11-06): no `-k` keyword filter anymore. Everything that
# `unittest` discovers is executed. If grouping is ever unavoidable, pass
# -ExcludeFiles with explicit module stems; the script prints the excluded
# files and their case counts and exits 3 (coverage gap), never 0.
#
# Verdict rule: skipped > 0 is NOT a pass. A skip is labelled
# SKIPPED_DEPENDENCY (reasoner absent / dependency unavailable) or
# SKIPPED_OTHER, and both make the run incomplete (exit 1). No failure is ever
# downgraded to a skip.
#
# Self-check: the in-container runner reports discovered vs executed counts and
# the ids of any discovered case that never ran; a mismatch exits 2.
#
# Evidence: every run writes a transcript under doc/evidence/ (git-tracked),
# named acceptance-s14-<project>-<timestamp>-<git-sha>.log.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\acceptance-s14.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\acceptance-s14.ps1 `
#     -ComposeProject agent-platform -ApiBaseUrl http://127.0.0.1:8080 -DataRoot D:\agentABC\data
#
# Exit codes: 0 all pass; 1 failed/error/skipped; 2 coverage self-check failed
# (discovered != executed) or runner protocol broken; 3 explicit exclusions.
param(
    # 默认指向独立验收栈（与 acceptance.ps1 同一套端口/项目/数据根），
    # 跑共享栈必须显式传 -ComposeProject agent-platform 等参数。
    [string]$ComposeProject = 'platform-acceptance',
    [string]$Image = 'agent-platform:0.1-s5',
    [string]$DataRoot = 'D:\agentABC\data-acceptance',
    [string]$ApiBaseUrl = 'http://127.0.0.1:8082',
    [int]$WaitSeconds = 120,
    [string[]]$ExcludeFiles = @(),
    [string]$EvidenceDir = '',
    [switch]$NoLock
)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $root
Set-Location $root
if (-not $EvidenceDir) { $EvidenceDir = Join-Path $repoRoot 'doc\evidence' }
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
$gitSha = (& git -C $repoRoot rev-parse --short HEAD 2>$null | Select-Object -First 1)
if (-not $gitSha) { $gitSha = 'nogit' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$evidenceFile = Join-Path $EvidenceDir "acceptance-s14-$ComposeProject-$stamp-$gitSha.log"
$transcript = $null
try { $transcript = Start-Transcript -Path $evidenceFile -Force } catch { Write-Host "WARN: transcript unavailable: $_" }

$owner = "$env:COMPUTERNAME\$env:USERNAME#$PID"
$guardScript = (Resolve-Path (Join-Path $PSScriptRoot 'compose-guard.ps1')).Path
$network = "$ComposeProject`_default"

function Get-HttpStatus([string]$url) {
    $code = & curl.exe -s -o NUL -w "%{http_code}" $url
    if ($LASTEXITCODE -ne 0) { return 0 }
    return [int]$code
}

function Write-Summary(
    [int]$discoveredTotal, [int]$excluded, [int]$discovered, [int]$executed,
    [int]$passed, [int]$failed, [int]$skipped, [int]$exitCode, [string]$note
) {
    Write-Host "S14 ACCEPTANCE discovered_total=$discoveredTotal excluded=$excluded discovered=$discovered executed=$executed passed=$passed failed=$failed skipped=$skipped exit=$exitCode note=$note"
    Write-Host "evidence=$evidenceFile"
}

Write-Host "S14 acceptance start ts=$stamp git=$gitSha image=$Image network=$network api=$ApiBaseUrl"
Write-Host "evidence_file=$evidenceFile excludes=$($ExcludeFiles -join ',')"

$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    if ((Get-HttpStatus "$ApiBaseUrl/readyz") -eq 200) { break }
    Start-Sleep -Seconds 3
}
if ((Get-HttpStatus "$ApiBaseUrl/readyz") -ne 200) {
    Write-Summary 0 0 0 0 0 1 0 1 'readyz_not_200'
    Write-Host "[FAIL] readyz 200 status=$((Get-HttpStatus "$ApiBaseUrl/readyz"))"
    if ($transcript) { Stop-Transcript | Out-Null }
    exit 1
}
Write-Host "readyz=200 network=$network image=$Image"

$lockHeld = $false
if (-not $NoLock) {
    & $guardScript acquire -Purpose "S14 acceptance (full unittest tree, $ComposeProject)" `
        -TtlMinutes 10 -Owner $owner -Stack $ComposeProject | ForEach-Object { Write-Host $_ }
    $lockHeld = ($LASTEXITCODE -eq 0)
    if (-not $lockHeld) {
        Write-Summary 0 0 0 0 0 1 0 75 'heavy_lock_busy'
        Write-Host "[FAIL] E_BUILD_CONFLICT: lock busy for stack '$ComposeProject'; S14 aborted before running any test."
        Write-Host "  inspect: powershell -ExecutionPolicy Bypass -File scripts\compose-guard.ps1 check -Stack $ComposeProject"
        Write-Host "  after holder exits: ... release -Stack $ComposeProject -Owner '<owner>'"
        if ($transcript) { Stop-Transcript | Out-Null }
        exit 75
    }
}

$excludeArg = ($ExcludeFiles -join ',')
$dockerArgs = @(
    'run', '--rm', '--network', $network, '--entrypoint', 'python',
    '-e', 'TEST_PG_DSN=postgresql://platform:platform_dev@postgres:5432/platform',
    '-e', 'TEST_OXIGRAPH_URL=http://oxigraph:7878',
    '-e', 'TEST_REASONER_URL=http://reasoner:7879',
    '-v', "$root\src:/app/src:ro",
    '-v', "$root\tests:/hosttests:ro",
    '-v', "${DataRoot}:/data",
    $Image,
    '/hosttests/_acceptance_runner.py',
    '--start-dir', '/hosttests', '--top-level', '/hosttests', '--pattern', 'test_*.py'
)
if ($excludeArg) { $dockerArgs += @('--exclude', $excludeArg) }

$out = @(& docker @dockerArgs 2>&1)
$code = $LASTEXITCODE
$lines = @($out | ForEach-Object {
    if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.Exception.Message }
    else { "$_" }
})
$lines | ForEach-Object { Write-Host $_ }

if ($lockHeld) {
    & $guardScript release -Owner $owner -Stack $ComposeProject | ForEach-Object { Write-Host $_ }
}

$resultLine = $lines | Where-Object { $_ -match '^ACCEPTANCE_RESULT ' } | Select-Object -Last 1
if (-not $resultLine) {
    Write-Summary 0 0 0 0 0 1 0 2 'runner_protocol_missing'
    if ($transcript) { Stop-Transcript | Out-Null }
    exit 2
}
$r = $resultLine.Substring('ACCEPTANCE_RESULT '.Length) | ConvertFrom-Json
$discoveredTotal = [int]$r.discovered_total
$discovered = [int]$r.discovered
$executed = [int]$r.executed
$passed = [int]$r.passed
$failed = [int]$r.failed
$errors = [int]$r.errors
$skipped = [int]$r.skipped
$excludedCount = 0
$excludedFiles = @()
if ($r.excluded) {
    foreach ($p in $r.excluded.PSObject.Properties) {
        $excludedCount += [int]$p.Value
        $excludedFiles += "$($p.Name)=$($p.Value)"
    }
}
$importFailures = @($r.import_failures)
$skipDetails = @($r.skip_details)
$notExecuted = @($r.not_executed)
$unknownExcludes = @($r.unknown_excludes)

Write-Host "coverage: discovered_total=$discoveredTotal excluded=$excludedCount discovered=$discovered executed=$executed"
if ($excludedCount -gt 0) { Write-Host "excluded_files: $($excludedFiles -join ', ')" }
foreach ($item in $skipDetails) {
    $label = if ($item.reason -match 'reasoner|E_REASONER_UNAVAILABLE|dependency') { 'SKIPPED_DEPENDENCY' } else { 'SKIPPED_OTHER' }
    Write-Host "[$label] $($item.test) reason=$($item.reason)"
}
foreach ($item in $notExecuted) {
    Write-Host "[NOT_EXECUTED] $item"
}

$bad = $failed + $errors + $importFailures.Count
$note = 'ok'
$exitCode = 0
if ($unknownExcludes.Count -gt 0) {
    $note = "unknown_exclude:$($unknownExcludes -join ',')"
    $exitCode = 2
}
elseif ($discovered -ne $executed -or $notExecuted.Count -gt 0) {
    $note = "coverage_mismatch:discovered=$discovered executed=$executed missing=$($notExecuted.Count)"
    $exitCode = 2
}
elseif ($excludedCount -gt 0) {
    $note = "explicit_exclusions:$($excludedFiles -join ',')"
    $exitCode = 3
}
elseif ($bad -gt 0) {
    $note = 'tests_failed'
    $exitCode = 1
}
elseif ($skipped -gt 0) {
    $note = 'skipped_is_not_pass'
    $exitCode = 1
}
elseif ($code -ne 0) {
    $note = "runner_exit=$code"
    $exitCode = 2
}

if ($exitCode -eq 0) {
    Write-Host "S14 ACCEPTANCE PASS (full tree)"
} else {
    Write-Host "S14 ACCEPTANCE NOT PASS: $note"
}
Write-Summary $discoveredTotal $excludedCount $discovered $executed $passed $bad $skipped $exitCode $note
if ($transcript) { Stop-Transcript | Out-Null }
exit $exitCode
