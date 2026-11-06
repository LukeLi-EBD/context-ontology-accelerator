# S14 acceptance: run the g01 / governance / browse / terms / metric / q7 / q8
# unittest suites inside the platform image and print one unified summary.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\acceptance-s14.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\acceptance-s14.ps1 -ComposeProject platform-b `
#     -Image agent-platform:0.1-s5 -ApiBaseUrl http://127.0.0.1:8082 -DataRoot D:\agentABC\data-b
#
# A failure is always counted as failed: no failure is downgraded to SKIP.
param(
    [string]$ComposeProject = 'agent-platform',
    [string]$Image = 'agent-platform:0.1-s5',
    [string]$DataRoot = 'D:\agentABC\data',
    [string]$ApiBaseUrl = 'http://127.0.0.1:8080',
    [int]$WaitSeconds = 120,
    [switch]$NoLock
)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$owner = "$env:COMPUTERNAME\$env:USERNAME#$PID"
$guardScript = (Resolve-Path (Join-Path $PSScriptRoot 'compose-guard.ps1')).Path
$network = "$ComposeProject`_default"

function Get-HttpStatus([string]$url) {
    $code = & curl.exe -s -o NUL -w "%{http_code}" $url
    if ($LASTEXITCODE -ne 0) { return 0 }
    return [int]$code
}

$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    if ((Get-HttpStatus "$ApiBaseUrl/readyz") -eq 200) { break }
    Start-Sleep -Seconds 3
}
if ((Get-HttpStatus "$ApiBaseUrl/readyz") -ne 200) {
    Write-Host "S14 ACCEPTANCE passed=0 failed=1 skipped=0"
    Write-Host "[FAIL] readyz 200 status=$((Get-HttpStatus "$ApiBaseUrl/readyz"))"
    exit 1
}
Write-Host "readyz=200 network=$network image=$Image"

$lockHeld = $false
if (-not $NoLock) {
    & $guardScript acquire -Purpose "S14 acceptance (g01/governance/browse/terms/metric/q7/q8)" `
        -TtlMinutes 30 -Owner $owner | ForEach-Object { Write-Host $_ }
    $lockHeld = ($LASTEXITCODE -eq 0)
    if (-not $lockHeld) {
        Write-Host "S14 ACCEPTANCE passed=0 failed=1 skipped=0"
        Write-Host "[FAIL] heavy lock busy (another task holds it)"
        exit 1
    }
}

$dockerArgs = @(
    'run', '--rm', '--network', $network, '--entrypoint', 'python',
    '-e', 'TEST_PG_DSN=postgresql://platform:platform_dev@postgres:5432/platform',
    '-e', 'TEST_OXIGRAPH_URL=http://oxigraph:7878',
    '-e', 'TEST_REASONER_URL=http://reasoner:7879',
    '-v', "$root\src:/app/src:ro",
    '-v', "$root\tests:/hosttests:ro",
    '-v', "${DataRoot}:/data",
    $Image,
    '-m', 'unittest', 'discover', '-s', '/hosttests', '-t', '/hosttests',
    '-p', 'test_*.py',
    '-k', 'g01', '-k', 'governance', '-k', 'browse', '-k', 'terms',
    '-k', 'metric', '-k', 'q7', '-k', 'q8'
)

$out = @(& docker @dockerArgs 2>&1)
$code = $LASTEXITCODE
$lines = @($out | ForEach-Object {
    if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.Exception.Message }
    else { "$_" }
})
$lines | ForEach-Object { Write-Host $_ }

if ($lockHeld) {
    & $guardScript release -Owner $owner | ForEach-Object { Write-Host $_ }
}

$ran = 0
$failed = 0
$errors = 0
$skipped = 0
foreach ($line in $lines) {
    if ($line -match '^Ran (\d+) tests') { $ran = [int]$Matches[1] }
    if ($line -match 'failures=(\d+)') { $failed = [int]$Matches[1] }
    if ($line -match 'errors=(\d+)') { $errors = [int]$Matches[1] }
    if ($line -match 'skipped=(\d+)') { $skipped = [int]$Matches[1] }
}
if ($code -ne 0) { $errors += 1 }
$bad = $failed + $errors
$passed = [Math]::Max(0, $ran - $bad - $skipped)

Write-Host "S14 ACCEPTANCE passed=$passed failed=$bad skipped=$skipped (ran=$ran)"
if ($bad -gt 0 -or $ran -eq 0) { exit 1 }
exit 0
