# compose-guard.ps1 - 跨会话构建/重建互斥（R1 技术拦截 + R2 心跳有效性 + 旧格式锁策略）
# 用法:
#   powershell -ExecutionPolicy Bypass -File scripts/compose-guard.ps1 check
#   powershell -ExecutionPolicy Bypass -File scripts/compose-guard.ps1 acquire -Purpose "acceptance run" -TtlMinutes 30
#   powershell -ExecutionPolicy Bypass -File scripts/compose-guard.ps1 heartbeat
#   powershell -ExecutionPolicy Bypass -File scripts/compose-guard.ps1 release
#   powershell -ExecutionPolicy Bypass -File scripts/compose-guard.ps1 status
#   powershell -ExecutionPolicy Bypass -File scripts/compose-guard.ps1 acquire -Force   # 仅旧格式/跨主机时显式接管
# 退出码: 0=成功/空闲; 75=锁被占用(E_BUILD_CONFLICT); 76=持有者存活或无法验活(含旧格式);
#         1=参数或所有权错误
param(
    [Parameter(Position = 0)]
    [ValidateSet('acquire', 'release', 'check', 'status', 'heartbeat', 'help')]
    [string]$Command = 'status',
    [string]$Purpose = 'unspecified',
    [int]$TtlMinutes = 30,
    [string]$Owner = '',
    [switch]$Force
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$lockDir = Join-Path $root '.lock'
$lockPath = Join-Path $lockDir 'heavy.lock'
$HeartbeatIntervalMinutes = 5   # 长任务每 <=5 分钟必须 heartbeat

if (-not $Owner) { $Owner = "$env:COMPUTERNAME\$env:USERNAME#$PID" }

function Get-NowUtc { (Get-Date).ToUniversalTime() }

function Read-Lock {
    if (-not (Test-Path -LiteralPath $lockPath)) { return $null }
    try { return (Get-Content -LiteralPath $lockPath -Raw -ErrorAction Stop | ConvertFrom-Json) }
    catch { return [pscustomobject]@{ owner = 'corrupt'; started_at = $null; heartbeat_at = $null; purpose = 'corrupt lock file'; pid = $null; host = $null } }
}

function Get-AgeMinutes([string]$iso) {
    if (-not $iso) { return [double]::MaxValue }
    try { return ((Get-NowUtc) - ([datetime]$iso).ToUniversalTime()).TotalMinutes }
    catch { return [double]::MaxValue }
}

# 旧格式锁：没有 pid 或 host（无法验活）-> 一律按"可能存活"处理
function Test-IsLegacy($lock) { return ((-not $lock.pid) -or (-not $lock.host)) }

# 返回 $true=同机且进程存活; $false=同机且进程不存在; $null=无法验证(跨机/旧格式)
function Test-HolderAlive($lock) {
    if (Test-IsLegacy $lock) { return $null }
    if ($lock.host -ne $env:COMPUTERNAME) { return $null }
    $p = Get-Process -Id ([int]$lock.pid) -ErrorAction SilentlyContinue
    if ($p) { return $true }
    return $false
}

function Format-Alive($lock, $alive) {
    if (Test-IsLegacy $lock) { return 'unknown (legacy)' }
    if ($alive -eq $true) { return 'True' }
    if ($alive -eq $false) { return 'False' }
    return 'unverifiable'
}

function Write-Lock {
    if (-not (Test-Path -LiteralPath $lockDir)) { New-Item -ItemType Directory -Path $lockDir -Force | Out-Null }
    $now = (Get-NowUtc).ToString('o')
    $obj = [ordered]@{
        owner        = $Owner
        pid          = $PID
        host         = $env:COMPUTERNAME
        started_at   = $now
        heartbeat_at = $now
        purpose      = $Purpose
        ttl_minutes  = $TtlMinutes
    }
    ($obj | ConvertTo-Json) | Set-Content -LiteralPath $lockPath -Encoding UTF8 -Force
}

switch ($Command) {

    'check' {
        $lock = Read-Lock
        if ($null -eq $lock) { Write-Output 'free'; exit 0 }
        $age = Get-AgeMinutes $lock.heartbeat_at
        $alive = Test-HolderAlive $lock
        $aliveTxt = Format-Alive $lock $alive
        $desc = "owner=$($lock.owner) pid=$($lock.pid) host=$($lock.host) purpose=$($lock.purpose) holder_alive=$aliveTxt heartbeat_age=$([math]::Round($age))min"

        if ($Owner -and $lock.owner -eq $Owner) {
            Write-Output "owner-match $desc"
            exit 0
        }
        if ($age -lt $TtlMinutes) {
            if ($age -ge (2 * $HeartbeatIntervalMinutes)) {
                if (Test-IsLegacy $lock) { Write-Output "warn: holder not heartbeating (legacy lock, age=$([math]::Round($age))min)" }
                else { Write-Output "warn: holder not heartbeating (pid $($lock.pid) alive, age=$([math]::Round($age))min)" }
            }
            Write-Output "busy $desc"
            exit 75
        }

        # 心跳超时：必须验证持有者是否真的死了
        if ($alive -eq $true) {
            Write-Output "warn: holder not heartbeating (pid $($lock.pid) alive, age=$([math]::Round($age))min)"
            Write-Output "busy $desc"
            exit 75
        }
        if ($alive -eq $null) {
            $why = if (Test-IsLegacy $lock) { 'legacy lock, 无法验证持有者' } else { "cross-host ($($lock.host))" }
            Write-Output "busy (stale but unverifiable: $why; 需 acquire -Force) $desc"
            exit 75
        }
        Write-Output "free (stale lock, holder pid $($lock.pid) not alive) $desc"
        exit 0
    }

    'acquire' {
        $lock = Read-Lock
        if ($null -eq $lock) {
            Write-Lock
            Write-Output "acquired owner=$Owner pid=$PID host=$env:COMPUTERNAME purpose=$Purpose"
            exit 0
        }

        $age = Get-AgeMinutes $lock.heartbeat_at
        if ($age -lt $TtlMinutes) {
            Write-Output 'E_BUILD_CONFLICT: 已有重任务持锁，拒绝获取。'
            Write-Output "  holder.owner=$($lock.owner)"
            Write-Output "  holder.pid=$($lock.pid) host=$($lock.host)"
            Write-Output "  holder.purpose=$($lock.purpose)"
            Write-Output "  holder.started_at=$($lock.started_at)"
            Write-Output "  heartbeat_age=$([math]::Round($age))min (ttl=${TtlMinutes}min)"
            Write-Output '  处理: 等任务结束或确认后 release，不要直接 compose up -d。'
            exit 75
        }

        # 心跳超时 -> 验活
        $alive = Test-HolderAlive $lock
        if ($alive -eq $true) {
            Write-Output "E_LOCK_HOLDER_ALIVE: 心跳超时但持有进程仍存活，拒绝接管。"
            Write-Output "  holder.owner=$($lock.owner) pid=$($lock.pid) host=$($lock.host)"
            Write-Output "  heartbeat_age=$([math]::Round($age))min (ttl=${TtlMinutes}min)"
            Write-Output '  长任务必须每 <=5 分钟 heartbeat；若确需接管，先确认 holder 已退出。'
            exit 76
        }

        if ($alive -eq $null) {
            if (Test-IsLegacy $lock) {
                if (-not $Force) {
                    Write-Output 'E_LOCK_LEGACY_UNKNOWN: 锁为旧格式（无 pid/host），无法验证持有者，拒绝接管。'
                    Write-Output "  holder.owner=$($lock.owner) owner 记录于 $($lock.started_at)"
                    Write-Output "  heartbeat_age=$([math]::Round($age))min (ttl=${TtlMinutes}min)；旧格式一律按“可能存活”处理。"
                    Write-Output '  如确认已失效请用 -Force：compose-guard.ps1 acquire -Force -Purpose ...'
                    exit 76
                }
                Write-Output "warn: legacy lock takeover forced (previous owner=$($lock.owner) heartbeat_age=$([math]::Round($age))min)"
                Write-Lock
                Write-Output "acquired owner=$Owner pid=$PID purpose=$Purpose"
                exit 0
            }

            $crossHost = ($lock.host -and $lock.host -ne $env:COMPUTERNAME)
            if (-not $Force) {
                Write-Output "E_LOCK_HOLDER_ALIVE: 无法验证持有者是否存活（host=$($lock.host) pid=$($lock.pid)），拒绝接管。"
                Write-Output "  heartbeat_age=$([math]::Round($age))min (ttl=${TtlMinutes}min)"
                Write-Output '  确需接管请显式加 -Force。'
                exit 76
            }
            if ($crossHost) { Write-Output "warn: cross-host takeover forced (previous host=$($lock.host) pid=$($lock.pid), heartbeat_age=$([math]::Round($age))min)" }
            else { Write-Output "warn: stale lock taken over (holder unverifiable: pid=$($lock.pid), heartbeat_age=$([math]::Round($age))min)" }
            Write-Lock
            Write-Output "acquired owner=$Owner pid=$PID purpose=$Purpose"
            exit 0
        }

        Write-Output "warn: stale lock taken over (previous owner=$($lock.owner) pid=$($lock.pid) heartbeat_age=$([math]::Round($age))min > ttl=${TtlMinutes}min, process not alive)"
        Write-Lock
        Write-Output "acquired owner=$Owner pid=$PID purpose=$Purpose"
        exit 0
    }

    'release' {
        $lock = Read-Lock
        if ($null -eq $lock) { Write-Output 'no lock to release'; exit 0 }
        if ($lock.owner -ne $Owner) {
            Write-Output "E_OWNER_MISMATCH: 拒绝释放。锁持有者=$($lock.owner)，请求者=$Owner"
            exit 1
        }
        Remove-Item -LiteralPath $lockPath -Force
        Write-Output "released owner=$Owner"
        exit 0
    }

    'heartbeat' {
        $lock = Read-Lock
        if ($null -eq $lock) { Write-Output 'E_NO_LOCK: 无锁可心跳'; exit 1 }
        if (Test-IsLegacy $lock) {
            $lock | Add-Member -NotePropertyName pid -NotePropertyValue $PID -Force
            $lock | Add-Member -NotePropertyName host -NotePropertyValue $env:COMPUTERNAME -Force
            Write-Output 'info: lock upgraded to pid/host format'
        }
        $now = (Get-NowUtc).ToString('o')
        $lock.heartbeat_at = $now
        ($lock | ConvertTo-Json) | Set-Content -LiteralPath $lockPath -Encoding UTF8 -Force
        Write-Output "heartbeat ok at $now (owner=$($lock.owner) pid=$($lock.pid) host=$($lock.host))"
        exit 0
    }

    'status' {
        $lock = Read-Lock
        if ($null -eq $lock) { Write-Output 'free (no lock)'; exit 0 }
        $age = Get-AgeMinutes $lock.heartbeat_at
        $alive = Test-HolderAlive $lock
        Write-Output '--- heavy.lock ---'
        Get-Content -LiteralPath $lockPath -Raw
        $state = if ($age -lt $TtlMinutes) { 'busy' } elseif ($alive -eq $true) { 'stale-but-holder-alive' } elseif ($alive -eq $null) { 'stale-unverifiable' } else { 'stale-holder-dead' }
        Write-Output "state=$state heartbeat_age=$([math]::Round($age))min ttl=${TtlMinutes}min holder_alive=$(Format-Alive $lock $alive)"
        exit 0
    }

    default {
        Write-Output 'usage: compose-guard.ps1 {acquire|release|check|status|heartbeat} [-Purpose <str>] [-TtlMinutes 30] [-Owner <str>] [-Force]'
        exit 0
    }
}
