# stack-verify.ps1 - 权威栈 AS-8080 身份五元组与关键计数校验（只读）
# 用法:
#   powershell -ExecutionPolicy Bypass -File platform/scripts/stack-verify.ps1
#   powershell -ExecutionPolicy Bypass -File platform/scripts/stack-verify.ps1 -ApiBase http://127.0.0.1:8080
# 退出码: 0=全部一致; 1=身份或计数不一致; 2=执行失败（容器/API/psql/基线比对不可用）
#
# 身份五元组（评审报告 §9.5）:
#   commit SHA（镜像构建来源）+ image id + schema max + 数据快照 id + 生效配置 sha256
# 数据快照 id 当前是“计数指纹”（非可恢复快照），算法与台账一致:
#   snap-counts- + sha256("docs=..;chunks=..;obs=..;definitions=..;facts=..")[:12]
# 台账: doc/_design/decisions/权威栈五元组台账-2026-11-07.md（脚本解析其最后一条身份条目）
#
# QA 加硬点:
#   * schema 必须精确等于期望值，不再接受“允许集合”；
#   * 容器 id 与 StartedAt 与台账最后一条比对，不是只打印；
#   * 仓库基线 platform/config/authoritative-8080.yaml 与生效配置逐键比对；
#   * manifest 关键数字（85/60/56/43/57/35/28/7/0）纳入断言。
#
# 本脚本只读：docker inspect / docker cp / sha256sum / SELECT / GET，不写任何表、不重启容器。

param(
    [string]$Container = 'agent-platform-api',
    [string]$DbContainer = 'agent-platform-postgres',
    [string]$Database = 'platform',
    [string]$DbUser = 'platform',
    [string]$ApiBase = 'http://127.0.0.1:8080',
    [string]$ExpectedCommit = '746b7a0cbb1641c7d74efb4f1131574013df9e5f',
    [string]$ExpectedImageId = 'sha256:85f5bc5fd540c8199e3006d4f7baa14bced57abf33f7c0767fc178b9b6d01675',
    [int]$ExpectedSchema = 43,
    [string]$ExpectedContainerId = 'd4536deccded89f26fbebe56a97eef1082ff33fc51d03651e68db9cd163ad740',
    [string]$ExpectedStartedAt = '2026-11-07T15:43:33.833916766Z',
    [string]$ExpectedSnapshot = 'snap-counts-489c77aa4d56',
    [string]$ExpectedConfigSha256 = '66a3b532479dcf7f2c2f39e4081b0b45c31f880f119a261d6d241b8751d407bd',
    [string]$LedgerPath = '',
    [string]$BaselineConfigPath = '',
    [string]$ExpectedProvider = 'full',
    [int]$ExpectedMetricDefinition = 85,
    [int]$ExpectedMetricObservation = 37477,
    [int]$ExpectedDocument = 3066,
    [int]$ExpectedDocumentChunk = 15218,
    [int]$ExpectedFactEvent = 10146,
    [int]$ExpectedStaleMarks = 144,
    # manifest 关键数字（2026-11-07 20:48 换栈后实测）
    [int]$ExpectedManifestTotal = 85,
    [int]$ExpectedPublishable = 60,
    [int]$ExpectedExecutable = 56,
    [int]$ExpectedPublishableExecutable = 43,
    [int]$ExpectedPublishableObserved = 44,
    [int]$ExpectedObservedMetricIds = 57,
    [int]$ExpectedExternalEligible = 35,
    [int]$ExpectedExternalCompute = 28,
    [int]$ExpectedExternalRuleSet = 7,
    [int]$ExpectedExternalUnavailable = 0
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$repoRoot = (& git -C $root rev-parse --show-toplevel 2>$null) -join ''
if ($LASTEXITCODE -ne 0 -or $repoRoot -eq '') { throw 'cannot resolve git top-level for repo root' }
$repoRoot = $repoRoot.Trim()

if ($LedgerPath -eq '') {
    $LedgerPath = Join-Path $repoRoot 'doc\_design\decisions\权威栈五元组台账-2026-11-07.md'
}
if ($BaselineConfigPath -eq '') {
    $BaselineConfigPath = Join-Path $root 'config\authoritative-8080.yaml'
}
if (-not (Test-Path -LiteralPath $LedgerPath)) { throw "ledger not found: $LedgerPath" }
if (-not (Test-Path -LiteralPath $BaselineConfigPath)) { throw "baseline config not found: $BaselineConfigPath" }

$tmpDir = Join-Path $env:TEMP ('stack-verify-' + [guid]::NewGuid().ToString('n'))
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

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
    Write-Output ("{0,-34}: {1}  actual={2} expected={3}" -f $Name, $verdict, $Actual, $Expected)
    if (-not $Ok) { $script:failures.Add($Name) }
}

try {
    # ---------- 1. 台账最后一条身份条目 ----------
    $ledgerText = Get-Content -LiteralPath $LedgerPath -Raw -Encoding UTF8

    function Get-LedgerField([string]$Text, [string]$Pattern, [string]$Label) {
        # 台账是 append-only：同一字段在旧条目里也出现，取最后一次匹配（最新条目）。
        $matches = [regex]::Matches($Text, $Pattern)
        if ($matches.Count -eq 0) { throw "ledger missing field: $Label" }
        return $matches[$matches.Count - 1].Groups[1].Value.Trim()
    }

    $ledgerCommit = Get-LedgerField $ledgerText '\| 2 \| commit SHA（镜像构建来源） \| `([0-9a-f]{40})`' 'commit'
    $ledgerImage = Get-LedgerField $ledgerText '\| 3 \| image id \| `(sha256:[0-9a-f]{64})`' 'image_id'
    $ledgerSchema = Get-LedgerField $ledgerText '\| 5 \| schema max \| `(\d+)`' 'schema_max'
    $ledgerConfig = Get-LedgerField $ledgerText '\| 7 \| 生效配置 sha256 \| `([0-9a-f]{64})`' 'config_sha256'
    $ledgerContainer = Get-LedgerField $ledgerText '\| 8 \| 新容器 id \| `([0-9a-f]{64})`' 'container_id'
    $ledgerStartedAt = Get-LedgerField $ledgerText '\| 10 \| 新 StartedAt \| `([^`]+)`' 'startedAt'

    # ---------- 2. 运行态身份 ----------
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

    # ---------- 3. 关键只读计数 ----------
    $countsSql = @'
SELECT 'schema' || '|' || COALESCE(MAX(version), 0)::text FROM platform.schema_version
UNION ALL SELECT 'metric_definition' || '|' || count(*)::text FROM platform.metric_definition
UNION ALL SELECT 'metric_observation' || '|' || count(*)::text FROM platform.metric_observation
UNION ALL SELECT 'document' || '|' || count(*)::text FROM platform.document
UNION ALL SELECT 'document_chunk' || '|' || count(*)::text FROM platform.document_chunk
UNION ALL SELECT 'fact_event' || '|' || count(*)::text FROM platform.fact_event
UNION ALL SELECT 'stale_mark' || '|' || count(*)::text FROM platform.source_ref_stale_mark
UNION ALL SELECT 'observed_metrics' || '|' || count(DISTINCT metric_id)::text FROM platform.metric_observation
'@
    $db = Get-DbCounts $countsSql
    foreach ($key in @('schema', 'metric_definition', 'metric_observation', 'document', 'document_chunk', 'fact_event', 'stale_mark', 'observed_metrics')) {
        if (-not $db.ContainsKey($key)) { throw "missing count: $key" }
    }

    # ---------- 4. manifest 关键数字 ----------
    $manifest = Invoke-RestMethod -Uri "$ApiBase/metrics/report/manifest" -TimeoutSec 20
    $items = @($manifest.items)
    $actualProvider = [string](Invoke-RestMethod -Uri "$ApiBase/browse/canvas/manifest" -TimeoutSec 5).provider

    $mTotal = $items.Count
    $mPublishable = @($items | Where-Object { $_.publishable -eq $true }).Count
    $mExecutable = @($items | Where-Object { $_.executable -eq $true }).Count
    $mPubExec = @($items | Where-Object { $_.publishable -eq $true -and $_.executable -eq $true }).Count
    $mPubObs = @($items | Where-Object { $_.publishable -eq $true -and [int]$_.observationCount -gt 0 }).Count
    $ext = @($items | Where-Object { $_.externalEligible -eq $true })
    $mExtTotal = $ext.Count
    $mExtCompute = @($ext | Where-Object { [string]$_.executionPath -eq 'compute' }).Count
    $mExtRule = @($ext | Where-Object { [string]$_.executionPath -eq 'rule_set' }).Count
    $mExtUnavail = $mExtTotal - $mExtCompute - $mExtRule

    # ---------- 5. 仓库基线与生效配置逐键比对 ----------
    $liveCopy = Join-Path $tmpDir 'platform.yaml'
    Invoke-Docker @('cp', "$Container`:/data/platform.yaml", $liveCopy)

    $baselineInRepo = $false
    & git -C $root ls-files --error-unmatch 'config/authoritative-8080.yaml' *> $null
    if ($LASTEXITCODE -eq 0) { $baselineInRepo = $true }
    & git -C $root diff --quiet -- 'config/authoritative-8080.yaml'
    $baselineClean = ($LASTEXITCODE -eq 0)

    $py = @'
import json, re, sys, yaml

def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

base = load('/cfg/base.yaml')
live = load('/live/platform.yaml')

IGNORE_LIVE = {('database', 'url')}
ALLOW_BASE_ONLY = {
    ('terms',),
    ('entity_view',),
    ('reasoning', 'max_source_bytes'),
    ('reasoning', 'max_assembly_bytes'),
    ('reasoning', 'materialize_online'),
}

diffs = []

def walk(b, l, path):
    if isinstance(b, dict) and isinstance(l, dict):
        for k, _v in l.items():
            if path + (k,) in IGNORE_LIVE:
                continue
            if k not in b:
                diffs.append('missing_in_baseline:' + '.'.join(path + (k,)))
            else:
                walk(b[k], l[k], path + (k,))
        for k, _v in b.items():
            if k not in l and path + (k,) not in ALLOW_BASE_ONLY:
                diffs.append('missing_in_live:' + '.'.join(path + (k,)))
    elif isinstance(b, list) and isinstance(l, list):
        if len(b) != len(l):
            diffs.append('list_len:' + '.'.join(path) + ' base=%d live=%d' % (len(b), len(l)))
        else:
            for i, (x, y) in enumerate(zip(b, l)):
                walk(x, y, path + ('[%d]' % i,))
    else:
        if b != l:
            diffs.append('value:' + '.'.join(path) + ' base=%r live=%r' % (b, l))

walk(base, live, ())

url = str((live.get('database') or {}).get('url', ''))
if not re.match(r'^postgresql://[^:]+:(?!CHANGE_ME)[^@]+@postgres:5432/platform$', url):
    diffs.append('database.url: expected postgresql://<user>:<real-password>@postgres:5432/platform')

print('BASELINE ' + json.dumps({'ok': not diffs, 'diffs': diffs}, ensure_ascii=False))
sys.exit(0 if not diffs else 1)
'@

    $cfgMount = $BaselineConfigPath.Replace('\', '/')
    $liveMount = $tmpDir.Replace('\', '/')
    $pyOut = @($py | & docker run --rm -i --entrypoint python `
        -v "${cfgMount}:/cfg/base.yaml:ro" -v "${liveMount}:/live:ro" `
        $actualImageId - 2>&1)
    $pyExit = $LASTEXITCODE
    $baselineLine = @($pyOut | Where-Object { $_ -match '^BASELINE ' } | Select-Object -Last 1)
    if ($baselineLine.Count -eq 0) {
        throw ("baseline comparison produced no result (exit=$pyExit): " + (($pyOut | Out-String).Trim()))
    }
    $baselineResult = ($baselineLine[0].Substring(9) | ConvertFrom-Json)
    $baselineDiffText = if ($baselineResult.diffs.Count -gt 0) { ($baselineResult.diffs -join '; ') } else { '(no diff)' }

    # ---------- 6. commit 与仓库 ----------
    $commitPresent = $false
    & git -C $repoRoot cat-file -e "$ExpectedCommit^{commit}" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $commitPresent = $true }
    $repoHead = (& git -C $repoRoot rev-parse HEAD 2>$null) -join ''
    if ($LASTEXITCODE -ne 0) { $repoHead = '(git unavailable)' }

    $fingerprint = "docs=$($db['document']);chunks=$($db['document_chunk']);obs=$($db['metric_observation']);definitions=$($db['metric_definition']);facts=$($db['fact_event'])"
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $digest = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($fingerprint)) | ForEach-Object { $_.ToString('x2') })
    }
    finally { $sha.Dispose() }
    $actualSnapshot = 'snap-counts-' + $digest.Substring(0, 12)
}
catch {
    Write-Output "VERIFY_FAILED: $($_.Exception.Message)"
    Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    exit 2
}

$actualSchema = [int]$db['schema']

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
Check 'commit.ledger_match' ($ExpectedCommit -eq $ledgerCommit) $ExpectedCommit $ledgerCommit
Check 'image_id' ($actualImageId -eq $ExpectedImageId) $actualImageId $ExpectedImageId
Check 'image_id.ledger_match' ($actualImageId -eq $ledgerImage) $actualImageId $ledgerImage
Check 'container_id.ledger_match' ($actualContainerId -eq $ledgerContainer) $actualContainerId $ledgerContainer
Check 'container_id.expected_match' ($ExpectedContainerId -eq $ledgerContainer) $ExpectedContainerId $ledgerContainer
Check 'startedAt.ledger_match' ($actualStartedAt -eq $ledgerStartedAt) $actualStartedAt $ledgerStartedAt
Check 'startedAt.expected_match' ($ExpectedStartedAt -eq $ledgerStartedAt) $ExpectedStartedAt $ledgerStartedAt
Check 'schema_max.exact' ($actualSchema -eq $ExpectedSchema) ([string]$actualSchema) ([string]$ExpectedSchema)
Check 'schema_max.ledger_match' (([string]$actualSchema) -eq $ledgerSchema) ([string]$actualSchema) $ledgerSchema
Check 'data_snapshot_id' ($actualSnapshot -eq $ExpectedSnapshot) $actualSnapshot $ExpectedSnapshot
Check 'config_sha256' ($actualConfigSha -eq $ExpectedConfigSha256.ToLowerInvariant()) $actualConfigSha $ExpectedConfigSha256
Check 'config_sha256.ledger_match' ($actualConfigSha -eq $ledgerConfig) $actualConfigSha $ledgerConfig
Check 'baseline.in_repo' ($baselineInRepo -and $baselineClean) ("in_repo=$baselineInRepo clean=$baselineClean") 'in_repo=True clean=True'
Check 'config.baseline_key_by_key' ([bool]$baselineResult.ok) $baselineDiffText '(no diff)'
Write-Output "---------- key counts (read-only SQL) ----------"
Check 'metric_definition' ([int]$db['metric_definition'] -eq $ExpectedMetricDefinition) ([string]$db['metric_definition']) ([string]$ExpectedMetricDefinition)
Check 'metric_observation' ([int]$db['metric_observation'] -eq $ExpectedMetricObservation) ([string]$db['metric_observation']) ([string]$ExpectedMetricObservation)
Check 'document' ([int]$db['document'] -eq $ExpectedDocument) ([string]$db['document']) ([string]$ExpectedDocument)
Check 'document_chunk' ([int]$db['document_chunk'] -eq $ExpectedDocumentChunk) ([string]$db['document_chunk']) ([string]$ExpectedDocumentChunk)
Check 'fact_event' ([int]$db['fact_event'] -eq $ExpectedFactEvent) ([string]$db['fact_event']) ([string]$ExpectedFactEvent)
Check 'source_ref_stale_mark' ([int]$db['stale_mark'] -eq $ExpectedStaleMarks) ([string]$db['stale_mark']) ([string]$ExpectedStaleMarks)
Check 'observed_metric_ids' ([int]$db['observed_metrics'] -eq $ExpectedObservedMetricIds) ([string]$db['observed_metrics']) ([string]$ExpectedObservedMetricIds)
Check 'canvas.provider' ($actualProvider -eq $ExpectedProvider) $actualProvider $ExpectedProvider
Write-Output "---------- manifest key numbers ----------"
Check 'manifest.total' ($mTotal -eq $ExpectedManifestTotal) ([string]$mTotal) ([string]$ExpectedManifestTotal)
Check 'manifest.publishable' ($mPublishable -eq $ExpectedPublishable) ([string]$mPublishable) ([string]$ExpectedPublishable)
Check 'manifest.executable' ($mExecutable -eq $ExpectedExecutable) ([string]$mExecutable) ([string]$ExpectedExecutable)
Check 'manifest.publishable_executable' ($mPubExec -eq $ExpectedPublishableExecutable) ([string]$mPubExec) ([string]$ExpectedPublishableExecutable)
Check 'manifest.publishable_observed' ($mPubObs -eq $ExpectedPublishableObserved) ([string]$mPubObs) ([string]$ExpectedPublishableObserved)
Check 'manifest.external_eligible' ($mExtTotal -eq $ExpectedExternalEligible) ([string]$mExtTotal) ([string]$ExpectedExternalEligible)
Check 'manifest.external_compute' ($mExtCompute -eq $ExpectedExternalCompute) ([string]$mExtCompute) ([string]$ExpectedExternalCompute)
Check 'manifest.external_rule_set' ($mExtRule -eq $ExpectedExternalRuleSet) ([string]$mExtRule) ([string]$ExpectedExternalRuleSet)
Check 'manifest.external_unavailable' ($mExtUnavail -eq $ExpectedExternalUnavailable) ([string]$mExtUnavail) ([string]$ExpectedExternalUnavailable)

Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue

if ($failures.Count -gt 0) {
    Write-Output ("VERDICT: FAIL ({0} mismatch: {1})" -f $failures.Count, (($failures | ForEach-Object { $_ }) -join ', '))
    exit 1
}
Write-Output "VERDICT: PASS (AS-8080 identity, baseline config and key numbers match the ledger)"
exit 0
