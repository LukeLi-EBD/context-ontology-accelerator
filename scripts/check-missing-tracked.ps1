<#
.SYNOPSIS
    Watchdog: tracked files that exist in HEAD but are gone from disk, checked in every worktree.

.DESCRIPTION
    Why this exists: on 2026-11-11 11:14 the main worktree lost 9 tracked files under
    libs/ts-shared to an external process. There was no checkout / reset / stash / reflog
    trace, the directory was left empty, and the actor could not be identified. This script
    is meant to shout immediately the next time something like that happens.

    Per worktree (git worktree list --porcelain):
      1. `git ls-files -d`  - tracked but missing on disk
      2. own index mtime (.git/index, or .git/worktrees/<name>/index) and whether it moved
         within the last -IndexMinutes minutes (someone touched the index behind our back)
      3. current branch and HEAD
      4. in-progress merge / cherry-pick / revert / rebase / sequencer (MERGE_HEAD, ...)

    Repo-wide:
      5. `git stash list` entries

    Exit codes:
      0  clean - no output at all
      1  tracked files missing (CRIT)
      2  other anomaly - index touched recently, merge/rebase in progress, stash entries,
         or a listed worktree whose directory is gone
      3  usage / environment error

.PARAMETER RepoPath
    Any worktree of the repo. Defaults to the parent of this script's directory.

.PARAMETER IndexMinutes
    Freshness threshold for the per-worktree index mtime, in minutes. Default 15.
    Pass 0 to disable that check (e.g. right after running -Fix yourself).

.PARAMETER Fix
    For each file that is (a) missing on disk, (b) present in HEAD, and (c) still identical
    in the index at stage 0, run `git checkout HEAD -- <path>` for that single path.
    Worktrees with a merge / rebase / cherry-pick / revert in progress are skipped.
    Never runs reset, stash, clean, or any branch switch.

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

# Keep this file ASCII-only: Windows PowerShell 5.1 reads BOM-less files as ANSI.

function Write-Err([string]$msg) {
    [Console]::Error.WriteLine("[COA-WATCH][ERR] $msg")
}

if (-not $RepoPath) {
    $RepoPath = Join-Path $PSScriptRoot '..'
}
if (-not (Test-Path -LiteralPath $RepoPath)) {
    Write-Err "repo path not found: $RepoPath"
    exit 3
}
$RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path

& git -C $RepoPath rev-parse --git-dir 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Err "not a git repository: $RepoPath"
    exit 3
}

function Get-Worktrees([string]$Repo) {
    $raw = & git -C $Repo worktree list --porcelain 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    $list = New-Object System.Collections.ArrayList
    $cur = $null
    foreach ($line in $raw) {
        if ($line -match '^worktree (.+)$') {
            if ($cur) { [void]$list.Add($cur) }
            $cur = [pscustomobject]@{ Path = $Matches[1]; Head = ''; Branch = '(detached)' }
        }
        elseif ($cur -and $line -match '^HEAD (.+)$') { $cur.Head = $Matches[1] }
        elseif ($cur -and $line -match '^branch refs/heads/(.+)$') { $cur.Branch = $Matches[1] }
    }
    if ($cur) { [void]$list.Add($cur) }
    return $list
}

function Get-WorktreeState($Wt) {
    $exists = Test-Path -LiteralPath $Wt.Path
    $missing = @()
    $ops = @()
    $lsFailed = $false
    $indexAge = $null
    $indexPath = ''

    if ($exists) {
        $raw = & git -C $Wt.Path ls-files -d 2>$null
        if ($LASTEXITCODE -ne 0) {
            $lsFailed = $true
        }
        else {
            $missing = @($raw | Where-Object { $_ -and ("$_".Trim() -ne '') } | ForEach-Object { "$_".Trim() })
        }
    }

    # "gitdir" is not part of the porcelain output, so ask git directly. This is
    # .git for the main worktree and .git/worktrees/<name> for linked ones.
    $gitDir = ''
    if ($exists) {
        $gd = & git -C $Wt.Path rev-parse --absolute-git-dir 2>$null
        if ($LASTEXITCODE -eq 0 -and $gd) { $gitDir = "$gd".Trim() }
    }

    if ($gitDir) {
        $markers = [ordered]@{
            'MERGE_HEAD'       = 'merge'
            'CHERRY_PICK_HEAD' = 'cherry-pick'
            'REVERT_HEAD'      = 'revert'
            'rebase-merge'     = 'rebase'
            'rebase-apply'     = 'rebase'
            'sequencer'        = 'sequencer'
        }
        foreach ($k in $markers.Keys) {
            if (Test-Path -LiteralPath (Join-Path $gitDir $k)) { $ops += $markers[$k] }
        }
        $indexPath = Join-Path $gitDir 'index'
        if (Test-Path -LiteralPath $indexPath) {
            $ageMin = ((Get-Date) - (Get-Item -LiteralPath $indexPath).LastWriteTime).TotalMinutes
            $indexAge = [math]::Round($ageMin, 1)
        }
    }

    $headShort = if ($Wt.Head) { $Wt.Head.Substring(0, [Math]::Min(8, $Wt.Head.Length)) } else { '' }

    return [pscustomobject]@{
        Path        = $Wt.Path
        Branch      = $Wt.Branch
        Head        = $headShort
        Exists      = $exists
        LsFailed    = $lsFailed
        Missing     = @($missing)
        Ops         = @($ops)
        IndexAgeMin = $indexAge
        IndexPath   = $indexPath
    }
}

# Returns 'ok' when the file can be restored from HEAD without touching anyone's work.
function Test-Repairable([string]$WtPath, [string]$RelPath) {
    if (Test-Path -LiteralPath (Join-Path $WtPath $RelPath)) { return 'present-on-disk' }

    $headSha = & git -C $WtPath rev-parse --verify --quiet "HEAD:$RelPath" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $headSha) { return 'head-blob-missing' }

    $entry = & git -C $WtPath ls-files -s -- $RelPath 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $entry) { return 'not-in-index' }
    $line = @($entry)[0]
    $m = [regex]::Match("$line", '^(?<mode>\d{6}) (?<sha>[0-9a-fA-F]{40}) (?<stage>\d)\t')
    if (-not $m.Success) { return 'index-entry-unparsed' }
    if ($m.Groups['stage'].Value -ne '0') { return ('index-stage-' + $m.Groups['stage'].Value) }
    if ($m.Groups['sha'].Value.ToLower() -ne "$headSha".Trim().ToLower()) { return 'index-differs-from-head' }

    return 'ok'
}

$worktrees = Get-Worktrees $RepoPath
if (-not $worktrees -or $worktrees.Count -eq 0) {
    Write-Err "git worktree list returned nothing for $RepoPath"
    exit 3
}

if ($WorktreePath) {
    if (-not (Test-Path -LiteralPath $WorktreePath)) {
        Write-Err "worktree path not found: $WorktreePath"
        exit 3
    }
    $want = (Resolve-Path -LiteralPath $WorktreePath).Path.Replace('\', '/').TrimEnd('/')
    $matched = @($worktrees | Where-Object { $_.Path.Replace('\', '/').TrimEnd('/') -eq $want })
    if ($matched.Count -eq 0) {
        Write-Err "$WorktreePath is not in git worktree list"
        exit 3
    }
    $worktrees = $matched
}

$states = @()
foreach ($wt in $worktrees) { $states += Get-WorktreeState $wt }

$stashRaw = & git -C $RepoPath stash list 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Err 'git stash list failed'
    exit 3
}
$stash = @($stashRaw | Where-Object { $_ -and ("$_".Trim() -ne '') })

# --- optional repair -------------------------------------------------------
$fixLines = New-Object System.Collections.ArrayList
$fixApplied = $false
if ($Fix) {
    foreach ($s in $states) {
        if ($s.Missing.Count -eq 0) { continue }
        if (-not $s.Exists) {
            [void]$fixLines.Add("skip  $($s.Path) (worktree dir missing)")
            continue
        }
        if ($s.Ops.Count -gt 0) {
            [void]$fixLines.Add("skip  $($s.Path) ($($s.Ops -join ',') in progress)")
            continue
        }
        foreach ($p in $s.Missing) {
            $verdict = Test-Repairable $s.Path $p
            if ($verdict -ne 'ok') {
                [void]$fixLines.Add("skip  $($s.Path)/$p ($verdict)")
                continue
            }
            & git -C $s.Path checkout HEAD -- $p 2>$null
            if ($LASTEXITCODE -ne 0) {
                [void]$fixLines.Add("fail  $($s.Path)/$p (git checkout exit $LASTEXITCODE)")
            }
            else {
                [void]$fixLines.Add("fixed $($s.Path)/$p")
                $fixApplied = $true
            }
        }
    }

    # Re-scan after the repair so the report is about the current truth.
    $states = @()
    foreach ($wt in $worktrees) { $states += Get-WorktreeState $wt }
    $stashRaw = & git -C $RepoPath stash list 2>$null
    $stash = @($stashRaw | Where-Object { $_ -and ("$_".Trim() -ne '') })
}

# --- evaluate --------------------------------------------------------------
$missingTotal = 0
$missingFiles = New-Object System.Collections.ArrayList
$realWarn = New-Object System.Collections.ArrayList   # merge/rebase, stash, broken worktree
$indexWarn = New-Object System.Collections.ArrayList  # index mtime inside the threshold
$detailLines = New-Object System.Collections.ArrayList

foreach ($s in $states) {
    $flags = New-Object System.Collections.ArrayList
    if (-not $s.Exists) { [void]$flags.Add('worktree-dir-missing'); [void]$realWarn.Add("$($s.Path): worktree dir missing") }
    if ($s.LsFailed) { [void]$flags.Add('ls-files-failed'); [void]$realWarn.Add("$($s.Path): git ls-files -d failed"); }
    if ($s.Ops.Count -gt 0) {
        [void]$flags.Add(('op:' + ($s.Ops -join ',')))
        [void]$realWarn.Add("$($s.Path): $($s.Ops -join ',') in progress")
    }
    if ($IndexMinutes -gt 0 -and $null -ne $s.IndexAgeMin -and $s.IndexAgeMin -le $IndexMinutes) {
        [void]$flags.Add(('index-touched-' + $s.IndexAgeMin + 'm'))
        [void]$indexWarn.Add("$($s.Path): index touched $($s.IndexAgeMin)m ago ($($s.IndexPath))")
    }
    if ($s.Missing.Count -gt 0) {
        $missingTotal += $s.Missing.Count
        foreach ($p in $s.Missing) { [void]$missingFiles.Add((Join-Path $s.Path $p).Replace('\', '/')) }
        [void]$flags.Add(('missing=' + $s.Missing.Count))
    }

    if ($flags.Count -gt 0) {
        $ageStr = if ($null -eq $s.IndexAgeMin) { 'n/a' } else { "$($s.IndexAgeMin)m" }
        [void]$detailLines.Add("wt=$($s.Path) branch=$($s.Branch) head=$($s.Head) index_age=$ageStr [$($flags -join ' ')]")
        foreach ($p in $s.Missing) { [void]$detailLines.Add("  missing: $p") }
    }
}

if ($stash.Count -gt 0) {
    foreach ($l in $stash) { [void]$realWarn.Add("stash: $l") }
}

$warnTotal = $realWarn.Count + $indexWarn.Count
if ($missingTotal -eq 0 -and $warnTotal -eq 0 -and $fixLines.Count -eq 0) {
    exit 0
}

# --- report ----------------------------------------------------------------
if ($fixLines.Count -gt 0) {
    Write-Output ("[COA-WATCH] fix pass ($($fixLines.Count) decision(s))")
    foreach ($l in $fixLines) { Write-Output "  $l" }
}

if ($missingTotal -gt 0 -or $warnTotal -gt 0) {
    foreach ($l in $detailLines) { Write-Output $l }
    foreach ($l in $realWarn) { Write-Output "WARN $l" }
    foreach ($l in $indexWarn) { Write-Output "WARN $l" }

    $stamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
    if ($missingTotal -gt 0) {
        $shown = @($missingFiles | Select-Object -First 5)
        $more = if ($missingFiles.Count -gt 5) { " +$($missingFiles.Count - 5) more" } else { '' }
        $summary = "[COA-WATCH][CRIT] $stamp repo=$($RepoPath.Replace('\', '/')) worktrees=$($states.Count) missing=$missingTotal warn=$warnTotal stash=$($stash.Count) files=$($shown -join ';')$more"
    }
    else {
        $summary = "[COA-WATCH][WARN] $stamp repo=$($RepoPath.Replace('\', '/')) worktrees=$($states.Count) missing=0 warn=$warnTotal stash=$($stash.Count)"
    }
    Write-Output $summary
}

# --- exit code -------------------------------------------------------------
if ($missingTotal -gt 0) { exit 1 }
if ($realWarn.Count -gt 0) { exit 2 }
if ($indexWarn.Count -gt 0) {
    # A fresh index that this very -Fix run caused is not an alarm; anything else is.
    if ($fixApplied) {
        Write-Output "[COA-WATCH] note: the index freshness above was caused by this -Fix run; pass -IndexMinutes 0 to silence it"
        exit 0
    }
    exit 2
}
exit 0
