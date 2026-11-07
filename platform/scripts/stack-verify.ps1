# stack-verify.ps1 - 权威栈 AS-8080 身份五元组与关键计数校验（只读）
# 用法:
#   powershell -ExecutionPolicy Bypass -File platform/scripts/stack-verify.ps1
#   powershell -ExecutionPolicy Bypass -File platform/scripts/stack-verify.ps1 -ApiBase http://127.0.0.1:8080
# 退出码: 0=全部一致; 1=身份或计数不一致; 2=执行失败（容器/API/psql 不可用）
#
# 身份五元组（评审报告 §9.5）:
#   commit SHA（镜像构建来源）+ image id + schema max + 数据快照 id + 生效配置 sha256
# 数据快照 id 当前是“计数指纹”（非可恢复快照），算法与台账一致:
#   snap-counts- + sha256("docs=..;chunks=..;obs=..;definitions=..;facts=..")[:12]
# 台账: doc/_design/decisions/权威栈五元组台账-2026-11-07.md
#
# 本脚本只读：docker inspect / sha256sum / SELECT / GET，不写任何表、不重启容器。

param(
    [string]$Container = 'agent-platform-api',
    [string]$DbContainer = 'agent-platform-postgres',
    [string]$Database = 'platform',
    [string]$DbUser = 'platform',
    [string]$ApiBase = 'http://127.0.0.1:8080',
    [string]$ExpectedCommit = '746b7a0cbb1641c7d74efb4f1131574013df9e5f',
    [string]$ExpectedImageId = 'sha256:85f5bc5fd540c8199e3006d4f7baa14bced57abf33f7c0767fc178b9b6d01675',
    [int[]]$AllowedSchema = @(42, 43),
    [string]$ExpectedSnapshot = 'snap-counts-489c77aa4d56',
    [string]$ExpectedConfigSha256 = '66a3b532479dcf7f2c2f39e4081b0b45c31f880f119a261d6d241b8751d407bd',
    [string]$ExpectedProvider = 'full',
    [int]$ExpectedMetricDefinition = 85,
    [int]$ExpectedMetricObservation = 37477,
    [int]$ExpectedDocument = 3066,
    [int]$ExpectedDocumentChunk = 15218,
    [int]$ExpectedFactEvent = 10146,
    [int]$ExpectedStaleMarks = 144
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot

function Invoke-Docker([string[]]$DockerArgs) {
    $out = & docker @DockerArgs 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($out | Out-String).Trim() }
    return @($out)
}

function Get-DbCounts([string]$Sql) {
    $out = Invoke-Docker @('exec', $DbContainer, 'psql', '-U', $DbUser, '-d', $Database, '-tA', '-F', '|', '-c', $Sql)
    $rows = @{}
    foreach ($line in $out) {
        $line = $line.Trim()
        if ($line -eq '') { continue }
        $i = $line.IndexOf('|')
        if ($i -lt 0) { continue }
        $rows[$line.Substring(0, $i)] = [int]$line.Substring($i + 1)
    }
    return $rows
}

$failures = New-Object System.Collections.Generic.List[string]
function Check([string]$Name, [bool]$Ok, [string]$Actual, [string]$Expected) {
    $verdict = if ($Ok) { 'PASS' } else { 'FAIL' }
    Write-Output ("{0,-28}: {1}  actual={2} expected={3}" -f $Name, $verdict, $Actual, $Expected)
    if (-not $Ok) { $script:failures.Add($Name) }
}

try {
    $inspect = (Invoke-Docker @('inspect', $Container, '--format', '{{.Image}}|{{.Id}}|{{.State.StartedAt}}|{{.State.Status}}')) -join ''
    $parts = $inspect -split '\|'
    if ($parts.Count -lt 4) { throw "unexpected docker inspect output: $inspect" }
    $actualImageId = $parts[0].Trim()
    $actualContainerId = $parts[1].Trim()
    $actualStartedAt = $parts[2].Trim()
    $actualStatus = $parts[3].Trim()

    $shaOut = (Invoke-Docker @('exec', $Container, 'sha256sum', '/data/platform.yaml')) -join ''
    if ($shaOut -notmatch '([0-9a-fA-F]{64})') { throw "cannot read config sha256: $shaOut" }
    $actualConfigSha = $Matches[1].ToLowerInvariant()

    $countsSql = @'
SELECT 'schema' || '|' || COALESCE(MAX(version), 0)::text FROM platform.schema_version
UNION ALL SELECT 'metric_definition' || '|' || count(*)::text FROM platform.metric_definition
UNION ALL SELECT 'metric_observation' || '|' || count(*)::text FROM platform.metric_observation
UNION ALL SELECT 'document' || '|' || count(*)::text FROM platform.document
UNION ALL SELECT 'document_chunk' || '|' || count(*)::text FROM platform.document_chunk
UNION ALL SELECT 'fact_event' || '|' || count(*)::text FROM platform.fact_event
UNION ALL SELECT 'stale_mark' || '|' || count(*)::text FROM platform.source_ref_stale_mark
'@
    $db = Get-DbCounts $countsSql
    foreach ($key in @('schema', 'metric_definition', 'metric_observation', 'document', 'document_chunk', 'fact_event', 'stale_mark')) {
        if (-not $db.ContainsKey($key)) { throw "missing count: $key" }
    }

    $manifest = Invoke-RestMethod -Uri "$ApiBase/browse/canvas/manifest" -TimeoutSec 5
    $actualProvider = [string]$manifest.provider
}
catch {
    Write-Output "VERIFY_FAILED: $($_.Exception.Message)"
    exit 2
}

$actualSchema = [int]$db['schema']
$fpInput = "docs=$($db['document']);chunks=$($db['document_chunk']);obs=$($db['metric_observation']);definitions=$($db['metric_definition']);facts=$($db['fact_event'])"
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    $digest = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($fpInput)) | ForEach-Object { $_.ToString('x2') })
}
finally {
    $sha.Dispose()
}
$actualSnapshot = 'snap-counts-' + $digest.Substring(0, 12)

$commitPresent = $false
$commitOut = & git -C $root cat-file -e "$ExpectedCommit^{commit}" 2>&1
if ($LASTEXITCODE -eq 0) { $commitPresent = $true }
$repoHead = (& git -C $root rev-parse HEAD 2>$null) -join ''
if ($LASTEXITCODE -ne 0) { $repoHead = '(git unavailable)' }

Write-Output "========== stack verify (AS-8080 / $Container) =========="
Write-Output ("container_id                : {0}" -f $actualContainerId)
Write-Output ("container_status            : {0}" -f $actualStatus)
Write-Output ("container_startedAt         : {0}" -f $actualStartedAt)
Write-Output ("image_id                    : {0}" -f $actualImageId)
Write-Output ("repo_head                   : {0}  (informational; identity uses image source commit)" -f $repoHead)
Write-Output ("config_sha256               : {0}" -f $actualConfigSha)
Write-Output ("data_snapshot_id            : {0}  (restorable=false)" -f $actualSnapshot)
Write-Output ("manifest.provider           : {0}" -f $actualProvider)
Write-Output "---------- identity five-tuple ----------"
Check 'commit.in_repo' $commitPresent $ExpectedCommit $ExpectedCommit
Check 'image_id' ($actualImageId -eq $ExpectedImageId) $actualImageId $ExpectedImageId
Check 'schema_max' ($AllowedSchema -contains $actualSchema) ([string]$actualSchema) (($AllowedSchema | ForEach-Object { $_ }) -join '/')
Check 'data_snapshot_id' ($actualSnapshot -eq $ExpectedSnapshot) $actualSnapshot $ExpectedSnapshot
Check 'config_sha256' ($actualConfigSha -eq $ExpectedConfigSha256.ToLowerInvariant()) $actualConfigSha $ExpectedConfigSha256
Write-Output "---------- key counts (read-only SQL) ----------"
Check 'metric_definition' ([int]$db['metric_definition'] -eq $ExpectedMetricDefinition) ([string]$db['metric_definition']) ([string]$ExpectedMetricDefinition)
Check 'metric_observation' ([int]$db['metric_observation'] -eq $ExpectedMetricObservation) ([string]$db['metric_observation']) ([string]$ExpectedMetricObservation)
Check 'document' ([int]$db['document'] -eq $ExpectedDocument) ([string]$db['document']) ([string]$ExpectedDocument)
Check 'document_chunk' ([int]$db['document_chunk'] -eq $ExpectedDocumentChunk) ([string]$db['document_chunk']) ([string]$ExpectedDocumentChunk)
Check 'fact_event' ([int]$db['fact_event'] -eq $ExpectedFactEvent) ([string]$db['fact_event']) ([string]$ExpectedFactEvent)
Check 'source_ref_stale_mark' ([int]$db['stale_mark'] -eq $ExpectedStaleMarks) ([string]$db['stale_mark']) ([string]$ExpectedStaleMarks)
Check 'canvas.provider' ($actualProvider -eq $ExpectedProvider) $actualProvider $ExpectedProvider

if ($failures.Count -gt 0) {
    Write-Output ("VERDICT: FAIL ({0} mismatch: {1})" -f $failures.Count, (($failures | ForEach-Object { $_ }) -join ', '))
    exit 1
}
Write-Output "VERDICT: PASS (AS-8080 identity and key counts match the ledger)"
exit 0
