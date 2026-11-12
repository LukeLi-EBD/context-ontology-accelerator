<#
.SYNOPSIS
    Thin Windows launcher for check-missing-tracked.py (the real implementation).

.DESCRIPTION
    Finds a Python 3 interpreter and forwards every argument to the .py next to this
    file. No logic lives here; output and the exit code (0/1/2/3) come from Python.

    Interpreter search order: $env:COA_PYTHON, `py -3`, `python`, `python3`.
    Each candidate is probed with `-c "import sys"` so the Microsoft Store alias stub
    (which exits 9009) is skipped instead of silently swallowing the run.

.PARAMETER RepoPath
    Any worktree of the repo. Defaults to the parent of this script's directory.

.PARAMETER IndexMinutes
    Freshness threshold for the per-worktree index mtime, in minutes. Default 15.
    Pass 0 to disable that check (e.g. right after running -Fix yourself).

.PARAMETER Fix
    Restore each missing file that is still identical to HEAD in the index, via
    `git checkout HEAD -- <path>`. Never runs reset, stash, clean, or a branch switch.

.PARAMETER WorktreePath
    Limit the check (and -Fix) to one worktree. Default is every worktree.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\check-missing-tracked.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\check-missing-tracked.ps1 -IndexMinutes 0 -Fix
#>
[CmdletBinding()]
param(
    [string]$RepoPath = '',
    [int]$IndexMinutes = 15,
    [switch]$Fix,
    [string]$WorktreePath = ''
)

$ErrorActionPreference = 'Stop'

$script = Join-Path $PSScriptRoot 'check-missing-tracked.py'
$exe = $null
$prefix = @()

function Test-PythonCandidate([string]$Path, [string[]]$Pre) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Path @Pre -c 'import sys' 2>&1 | Out-Null
        return ($LASTEXITCODE -eq 0)
    } finally {
        $ErrorActionPreference = $previous
    }
}

if ($env:COA_PYTHON -and (Test-PythonCandidate $env:COA_PYTHON @())) {
    $exe = $env:COA_PYTHON
}
if (-not $exe) {
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd -and (Test-PythonCandidate $cmd.Source @('-3'))) {
        $exe = $cmd.Source
        $prefix = @('-3')
    }
}
if (-not $exe) {
    foreach ($name in 'python', 'python3') {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and (Test-PythonCandidate $cmd.Source @())) {
            $exe = $cmd.Source
            break
        }
    }
}
if (-not $exe) {
    [Console]::Error.WriteLine('[COA-WATCH][ERR] no Python 3 found; install Python 3.8+ or set COA_PYTHON')
    exit 3
}

$pyArgs = @($script)
if ($RepoPath) { $pyArgs += @('-RepoPath', $RepoPath) }
$pyArgs += @('-IndexMinutes', [string]$IndexMinutes)
if ($Fix) { $pyArgs += '-Fix' }
if ($WorktreePath) { $pyArgs += @('-WorktreePath', $WorktreePath) }

& $exe @prefix @pyArgs
exit $LASTEXITCODE
