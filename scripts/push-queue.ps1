<#
.SYNOPSIS
    Batch push queue for the coa repo. One branch failing must not stop the rest.

.DESCRIPTION
    For every requested branch:
      1. resolve local tip and refuse protected branches (main / master)
      2. scan the diff that will actually be pushed for plaintext secrets
      3. push to the SSH remote, retrying transient failures with backoff
      4. verify the remote sha and collect timing
    A summary table is printed at the end and written to logs/push/push-<ts>.log.

    `--force` is never used. Rejected (non-fast-forward) pushes are reported, not forced.

.PARAMETER Branches
    Branches to push. Defaults to the 6 delivery branches of the coa repo.

.PARAMETER Remote
    Git remote name. Defaults to `luke` (SSH), because `origin` in this repo points
    at the upstream aws/context-ontology-accelerator repo, not at LukeLi-EBD.

.PARAMETER MaxAttempts
    Attempts per branch, including the first one. Default 3.

.PARAMETER BackoffSeconds
    Sleep between attempts. Default 2 / 5 / 10.

.PARAMETER AllowDirty
    Push even when the worktree has uncommitted changes. Default is to skip.

.PARAMETER DryRun
    Run preflight + secret scan only, no network write.

.PARAMETER LogDir
    Directory for run logs. Defaults to <repo>/logs/push (git-ignored).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\push-queue.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\push-queue.ps1 feat/o-gov
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]] $Branches,

    [string] $Remote = 'luke',

    [int] $MaxAttempts = 3,

    [int[]] $BackoffSeconds = @(2, 5, 10),

    [switch] $AllowDirty,

    [switch] $DryRun,

    [string] $LogDir
)

$ErrorActionPreference = 'Continue'

# ---------------------------------------------------------------- bootstrap
$DefaultBranches = @(
    'feat/o-gov',
    'feat/m-core',
    'feat/m-report',
    'feat/r-qa',
    'feat/canvas',
    'feat/integration'
)

if (-not $Branches -or $Branches.Count -eq 0) { $Branches = $DefaultBranches }

# Allow "a,b,c" as a single argument too.
$Branches = @($Branches | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

$RepoRoot = (& git --no-pager -C (Get-Location).Path rev-parse --show-toplevel 2>$null)
if (-not $RepoRoot) { Write-Host 'FATAL: not inside a git work tree.' -ForegroundColor Red; exit 2 }
$RepoRoot = $RepoRoot.Trim()

if (-not $LogDir) { $LogDir = Join-Path $RepoRoot 'logs\push' }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogFile = Join-Path $LogDir ('push-{0}.log' -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

$script:LogFile = $LogFile

function Write-Log {
    param([string] $Message, [string] $Color = 'Gray')
    $line = ('[{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $Message)
    Write-Host $line -ForegroundColor $Color
    Add-Content -Path $script:LogFile -Value $line -Encoding UTF8
}

function Invoke-GitText {
    param([string[]] $GitArgs)
    $raw = & git --no-pager -C $RepoRoot @GitArgs 2>&1
    $code = $LASTEXITCODE
    $text = if ($raw) { ($raw | Out-String).Trim() } else { '' }
    return [pscustomobject]@{ ExitCode = $code; Text = $text }
}

function Get-GitValue {
    param([string[]] $GitArgs)
    $r = Invoke-GitText $GitArgs
    if ($r.ExitCode -ne 0) { return '' }
    return $r.Text
}

function Get-Abbreviated {
    param([string] $Sha)
    if (-not $Sha) { return '-' }
    if ($Sha.Length -gt 12) { return $Sha.Substring(0, 12) }
    return $Sha
}

# ---------------------------------------------------------------- secret scan
$SecretPatterns = @(
    @{ Name = 'private-key-header'; Rx = '-----BEGIN (RSA |OPENSSH |EC |DSA |PGP |ENCRYPTED )?PRIVATE KEY-----' },
    @{ Name = 'github-token'      ; Rx = '(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{36})' },
    @{ Name = 'aws-access-key'    ; Rx = '(AKIA|ASIA)[0-9A-Z]{16}' },
    @{ Name = 'openai-style-key'  ; Rx = 'sk-[A-Za-z0-9]{32,}' },
    @{ Name = 'slack-token'       ; Rx = 'xox[abprs]-[A-Za-z0-9-]{10,}' },
    @{ Name = 'assigned-secret'   ; Rx = '(?i)(pass(word|wd)?|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)\s*[:=]\s*["'']?[A-Za-z0-9_\-\.]{12,}' }
)

$SecretFilePatterns = @(
    '(^|/)\.env(\.|\z|$)',
    '\.pem$', '\.p12$', '\.pfx$', '\.keystore$', '\.jks$',
    '(^|/)id_(rsa|dsa|ecdsa|ed25519)',
    '(^|/).*credential'
)

$PlaceholderHints = @('your_', 'your-', 'xxxx', 'example', 'sample', 'placeholder', 'changeme', 'redacted', 'dummy', 'fake_', '<', '${', '$(')

function Test-Placeholder {
    param([string] $Text)
    $lower = $Text.ToLowerInvariant()
    foreach ($h in $PlaceholderHints) { if ($lower.Contains($h)) { return $true } }
    return $false
}

function Get-ScanBase {
    param([string] $Branch)

    $remoteRef = "refs/remotes/$Remote/$Branch"
    $exists = (Invoke-GitText @('show-ref', '--verify', '--quiet', $remoteRef)).ExitCode -eq 0
    if ($exists) { return (Get-GitValue @('rev-parse', $remoteRef)) }

    foreach ($fallback in @("refs/remotes/$Remote/luke", "refs/remotes/$Remote/main", "refs/heads/luke")) {
        if ((Invoke-GitText @('show-ref', '--verify', '--quiet', $fallback)).ExitCode -eq 0) {
            $sha = Get-GitValue @('merge-base', $fallback, "refs/heads/$Branch")
            if ($sha) { return $sha }
        }
    }
    return ''
}

function Invoke-SecretScan {
    param([string] $Branch)

    $findings = New-Object System.Collections.ArrayList

    $base = Get-ScanBase -Branch $Branch
    if (-not $base) {
        return [pscustomobject]@{ Ok = $false; Findings = @('cannot determine scan base (no remote tracking ref)') }
    }

    $filesText = (Invoke-GitText @('diff', '--name-only', '--diff-filter=ACMR', "$base..refs/heads/$Branch")).Text
    $files = @($filesText -split "`r?`n" | Where-Object { $_ -and $_.Trim() })

    foreach ($f in $files) {
        foreach ($p in $SecretFilePatterns) {
            if ($f -match $p) { [void]$findings.Add("sensitive-file:$f") }
        }
    }

    $patch = (Invoke-GitText @('diff', '--no-color', '--unified=0', '--text', "$base..refs/heads/$Branch")).Text
    $currentFile = ''
    $newLine = 0
    foreach ($ln in ($patch -split "`r?`n")) {
        if ($ln -like '+++ *') {
            $currentFile = $ln.Substring(4).Trim()
            if ($currentFile -eq '/dev/null') { $currentFile = '' }
            elseif ($currentFile.StartsWith('b/')) { $currentFile = $currentFile.Substring(2) }
            continue
        }
        if ($ln -like '@@ *') {
            if ($ln -match '@@ .* \+([0-9]+)') { $newLine = [int]$Matches[1] }
            continue
        }
        if (-not $currentFile) { continue }
        if ($ln.StartsWith('+')) {
            $body = $ln.Substring(1)
            foreach ($sp in $SecretPatterns) {
                if ($body -match $sp.Rx) {
                    if (Test-Placeholder -Text $body) { continue }
                    [void]$findings.Add(('secret:{0}:{1}:{2}' -f $sp.Name, $currentFile, $newLine))
                }
            }
            $newLine++
        }
    }

    return [pscustomobject]@{ Ok = ($findings.Count -eq 0); Findings = @($findings) }
}

# ---------------------------------------------------------------- push
$PermanentFailureMarkers = @(
    '[rejected]',
    'non-fast-forward',
    'fetch first',
    '[remote rejected]',
    'Permission denied (publickey)',
    'denied',
    'Repository not found',
    'does not appear to be a git repository'
)

function Get-KeyErrorLine {
    param([string] $Text)
    if (-not $Text) { return '' }
    $lines = @($Text -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
    $hit = $lines | Where-Object { $_ -match '(fatal|error|rejected|denied|fail)' } | Select-Object -First 1
    if (-not $hit) { $hit = $lines | Select-Object -First 1 }
    if (-not $hit) { return '' }
    $hit = $hit.Trim()
    if ($hit.Length -gt 200) { $hit = $hit.Substring(0, 200) + '...' }
    return $hit
}

function Test-PermanentFailure {
    param([string] $Text)
    foreach ($m in $PermanentFailureMarkers) {
        if ($Text -match [regex]::Escape($m)) { return $true }
    }
    return $false
}

function Get-RemoteSha {
    param([string] $Branch)
    $out = (Invoke-GitText @('ls-remote', $Remote, "refs/heads/$Branch")).Text
    if (-not $out) { return '-' }
    $first = ($out -split "`r?`n")[0]
    if ($first -match '^([0-9a-f]{40})') { return $Matches[1] }
    return '-'
}

# ---------------------------------------------------------------- main
$startAll = Get-Date
Write-Log ''
Write-Log '==================== push-queue ===================='
Write-Log ("repo        : {0}" -f $RepoRoot)
Write-Log ("remote      : {0} -> {1}" -f $Remote, ((Invoke-GitText @('remote', 'get-url', $Remote)).Text))
Write-Log ("mode        : {0}" -f $(if ($DryRun) { 'DRY-RUN (no push)' } else { 'PUSH' }))
Write-Log ("branches    : {0}" -f ($Branches -join ', '))
Write-Log ("retry       : max {0} attempts, backoff {1}s" -f $MaxAttempts, ($BackoffSeconds -join '/'))
Write-Log ("log         : {0}" -f $LogFile)

$remoteUrl = (Invoke-GitText @('remote', 'get-url', $Remote)).Text
if (-not $remoteUrl) {
    Write-Log "FATAL: remote '$Remote' is not configured." 'Red'
    exit 2
}

# Guard: origin here is the read-only upstream aws repo. Never push to it.
if ($Remote -eq 'origin' -or $remoteUrl -match 'aws/context-ontology-accelerator') {
    Write-Log ("FATAL: remote '{0}' resolves to {1}, which is the upstream read-only repo. Use 'luke'." -f $Remote, $remoteUrl) 'Red'
    exit 2
}

$dirty = @((Invoke-GitText @('status', '--porcelain')).Text -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
$dirtySkipped = $false
if ($dirty.Count -gt 0) {
    if ($AllowDirty) {
        Write-Log ("worktree has {0} dirty path(s); -AllowDirty given, continue" -f $dirty.Count) 'Yellow'
    }
    else {
        Write-Log ("worktree has {0} dirty path(s); every branch will be skipped. Commit/stash first, or pass -AllowDirty." -f $dirty.Count) 'Red'
        foreach ($d in ($dirty | Select-Object -First 10)) { Write-Log ("  dirty: {0}" -f $d) 'DarkYellow' }
        $dirtySkipped = $true
    }
}

$rows = New-Object System.Collections.ArrayList

foreach ($branch in $Branches) {
    $row = [ordered]@{
        Branch   = $branch
        Result   = 'PENDING'
        RemoteSha = '-'
        LocalSha = '-'
        Elapsed  = 0.0
        Note     = ''
    }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        if ($branch -in @('main', 'master')) {
            $row.Result = 'REFUSED'
            $row.Note = 'protected branch: handled manually, never by this queue'
            continue
        }

        if ($dirtySkipped) {
            $row.Result = 'SKIPPED'
            $row.Note = 'worktree dirty'
            continue
        }

        $localSha = Get-GitValue @('rev-parse', '--verify', "refs/heads/$branch")
        if (-not $localSha) {
            $localSha = Get-GitValue @('rev-parse', '--verify', "refs/remotes/$Remote/$branch")
            if ($localSha) {
                $row.Result = 'ABSENT_LOCAL'
                $row.LocalSha = Get-Abbreviated $localSha
                $row.Note = 'branch only exists on remote'
            }
            else {
                $row.Result = 'MISSING'
                $row.Note = 'branch does not exist locally or on remote'
            }
            continue
        }
        $row.LocalSha = Get-Abbreviated $localSha

        $scan = Invoke-SecretScan -Branch $branch
        if (-not $scan.Ok) {
            $row.Result = 'BLOCKED_SECRET'
            $row.Note = ($scan.Findings -join '; ')
            Write-Log ("[{0}] SECRET SCAN FAILED: {1}" -f $branch, $row.Note) 'Red'
            continue
        }

        if ($DryRun) {
            $row.Result = 'DRY-RUN'
            $row.Note = 'preflight ok'
            continue
        }

        $attempt = 0
        while ($attempt -lt $MaxAttempts) {
            $attempt++
            $push = Invoke-GitText @('push', '-u', $Remote, "${branch}:refs/heads/${branch}")
            if ($push.ExitCode -eq 0) {
                $row.Result = 'OK'
                break
            }

            $errLine = Get-KeyErrorLine -Text $push.Text
            $row.Note = ("attempt {0}/{1}: {2}" -f $attempt, $MaxAttempts, $errLine)
            Write-Log ("[{0}] attempt {1}/{2} failed: {3}" -f $branch, $attempt, $MaxAttempts, $errLine) 'Yellow'

            if (Test-PermanentFailure -Text $push.Text) {
                $row.Result = 'FAILED'
                $row.Note = "non-retryable: $errLine"
                break
            }
            if ($attempt -lt $MaxAttempts) {
                $idx = [Math]::Min($attempt - 1, $BackoffSeconds.Count - 1)
                Start-Sleep -Seconds $BackoffSeconds[$idx]
            }
            else {
                $row.Result = 'FAILED'
                $row.Note = "exhausted {0} attempts: {1}" -f $MaxAttempts, $errLine
            }
        }

        if ($row.Result -eq 'OK') {
            $remoteSha = Get-RemoteSha -Branch $branch
            $row.RemoteSha = Get-Abbreviated $remoteSha
            if ($remoteSha -eq '-' -or $remoteSha -ne $localSha) {
                $row.Note = "pushed but remote sha unverified (remote=$remoteSha)"
                Write-Log ("[{0}] pushed, remote sha verification returned {1}" -f $branch, $remoteSha) 'Yellow'
            }
        }
    }
    catch {
        $row.Result = 'ERROR'
        $row.Note = $_.Exception.Message
        Write-Log ("[{0}] unexpected error: {1}" -f $branch, $_.Exception.Message) 'Red'
    }
    finally {
        $sw.Stop()
        $row.Elapsed = [Math]::Round($sw.Elapsed.TotalSeconds, 2)
        [void]$rows.Add([pscustomobject]$row)
    }
}

# ---------------------------------------------------------------- summary
$summaryLines = @()
$summaryLines += ''
$summaryLines += '==================== summary ===================='
$header = '{0,-18} {1,-14} {2,-14} {3,-14} {4,8}  {5}' -f 'BRANCH', 'RESULT', 'REMOTE_SHA', 'LOCAL_SHA', 'SECONDS', 'NOTE'
$summaryLines += $header
$summaryLines += ('-' * 118)
foreach ($r in $rows) {
    $note = $r.Note
    if ($note.Length -gt 90) { $note = $note.Substring(0, 90) + '...' }
    $summaryLines += ('{0,-18} {1,-14} {2,-14} {3,-14} {4,8}  {5}' -f $r.Branch, $r.Result, $r.RemoteSha, $r.LocalSha, $r.Elapsed, $note)
}

$okCount = @($rows | Where-Object { $_.Result -eq 'OK' -or $_.Result -eq 'DRY-RUN' }).Count
$badRows = @($rows | Where-Object { $_.Result -notin @('OK', 'DRY-RUN') })
$total = [Math]::Round(((Get-Date) - $startAll).TotalSeconds, 2)
$summaryLines += ('-' * 118)
$summaryLines += ("total {0} branch(es): {1} ok, {2} not ok, {3}s wall clock" -f $rows.Count, $okCount, $badRows.Count, $total)

foreach ($line in $summaryLines) {
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

if ($badRows.Count -gt 0) {
    Write-Host ''
    Write-Host 'Failing branches (raw error above / in log):' -ForegroundColor Red
    foreach ($r in $badRows) { Write-Host ("  {0}: {1}" -f $r.Branch, $r.Note) -ForegroundColor Red }
    exit 1
}
exit 0
