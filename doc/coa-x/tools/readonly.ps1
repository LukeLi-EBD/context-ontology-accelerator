# 8080 只读冻结开关（设计见 doc/coa-x/26-8080只读冻结与8082退役清单.md）
# 用法:
#   powershell -ExecutionPolicy Bypass -File doc\coa-x\tools\readonly.ps1 on
#   powershell -ExecutionPolicy Bypass -File doc\coa-x\tools\readonly.ps1 off
#   powershell -ExecutionPolicy Bypass -File doc\coa-x\tools\readonly.ps1 status -ApiBaseUrl http://127.0.0.1:8080
# 开关是哨兵文件 <DataRoot>\READONLY：存在即冻结，删除即恢复写，进程内 1s 生效，无需重启。
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('on', 'off', 'status')]
    [string]$Action,
    [string]$DataRoot = 'D:\agentABC\data',
    [string]$ApiBaseUrl = ''
)
$ErrorActionPreference = 'Stop'
$sentinel = Join-Path $DataRoot 'READONLY'
$auditDir = Join-Path $DataRoot 'audit'

switch ($Action) {
    'on' {
        New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
        if (Test-Path -LiteralPath $sentinel) {
            Write-Host "already frozen: $sentinel"
        }
        else {
            New-Item -ItemType File -Path $sentinel | Out-Null
            Write-Host "frozen: $sentinel"
        }
        Write-Host '生效 <=1s；恢复写: readonly.ps1 off'
    }
    'off' {
        if (Test-Path -LiteralPath $sentinel) {
            Remove-Item -LiteralPath $sentinel
            Write-Host "unfrozen: removed $sentinel"
        }
        else {
            Write-Host "not frozen: $sentinel 不存在"
        }
    }
    'status' {
        $frozen = Test-Path -LiteralPath $sentinel
        $mode = if ($frozen) { 'read_only' } else { 'read_write' }
        Write-Host ("mode={0} sentinel={1} exists={2}" -f $mode, $sentinel, $frozen)
        $today = Join-Path $auditDir ("readonly-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd'))
        if (Test-Path -LiteralPath $today) {
            $lines = @(Get-Content -LiteralPath $today)
            $blocked = @($lines | Where-Object { $_ -match '"event":"blocked"' }).Count
            Write-Host ("audit={0} lines={1} blocked={2}" -f $today, $lines.Count, $blocked)
            $lines | Select-Object -Last 5
        }
        else {
            Write-Host "audit=missing ($today)"
        }
        if ($ApiBaseUrl) {
            $raw = & curl.exe -s --noproxy '*' "$ApiBaseUrl/readonly"
            Write-Host "api=$raw"
        }
    }
}

