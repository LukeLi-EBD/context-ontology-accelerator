# source-ref-health.ps1 - 值级溯源断链检测（只读）
# 用法:
#   powershell -ExecutionPolicy Bypass -File platform/scripts/source-ref-health.ps1
#   powershell -ExecutionPolicy Bypass -File platform/scripts/source-ref-health.ps1 -Detail
#   powershell -ExecutionPolicy Bypass -File platform/scripts/source-ref-health.ps1 -Container platform-acceptance-postgres
# 退出码: 0=无未标记断链; 1=存在未标记断链（需标记或重发）; 2=执行失败
#
# 检测口径与 platform/src/platform_core/source_ref.py 的解析器一致：
#   obs      -> (metric_id, definition_version, entity_key, window_start, window_end)
#   obs-set  -> asOf 命中 as_of，或 periodStart/periodEnd 覆盖 window_start/window_end，
#               叠加可选 entityKey / institution / fixture
# 已失效引用记录在 platform.source_ref_stale_mark（append-only，见 doc/_design/decisions/
# 值级溯源档1-2026-11-07.md）；本脚本只读，不写任何表。

param(
    [string]$Container = 'agent-platform-postgres',
    [string]$Database = 'platform',
    [string]$DbUser = 'platform',
    [switch]$Detail
)
$ErrorActionPreference = 'Stop'

$livenessSql = @'
WITH live AS (
  SELECT r.source_ref, r.ref_kind, r.locator,
    CASE r.ref_kind
      WHEN 'metric_observation_row' THEN EXISTS (
        SELECT 1 FROM platform.metric_observation o
        WHERE o.metric_id = r.locator->>'metricId'
          AND o.definition_version = r.locator->>'definitionVersion'
          AND o.entity_key = r.locator->>'entityKey'
          AND o.window_start = (r.locator->>'windowStart')::date
          AND o.window_end = (r.locator->>'windowEnd')::date)
      WHEN 'metric_observation_set' THEN EXISTS (
        SELECT 1 FROM platform.metric_observation o
        WHERE o.metric_id = r.locator->>'metricId'
          AND o.definition_version = r.locator->>'definitionVersion'
          AND (((r.locator->>'asOf') IS NOT NULL AND o.as_of = (r.locator->>'asOf')::date)
            OR ((r.locator->>'periodStart') IS NOT NULL AND (r.locator->>'periodEnd') IS NOT NULL
                AND o.window_start >= (r.locator->>'periodStart')::date
                AND o.window_end <= (r.locator->>'periodEnd')::date))
          AND ((r.locator->>'entityKey') IS NULL OR o.entity_key = r.locator->>'entityKey')
          AND ((r.locator->>'institution') IS NULL OR o.institution = r.locator->>'institution')
          AND ((r.locator->>'fixture') IS NULL OR o.fixture = (r.locator->>'fixture')::boolean))
      ELSE TRUE
    END AS ok
  FROM platform.source_ref_registry r
  WHERE r.ref_kind IN ('metric_observation_row','metric_observation_set')
)
SELECT source_ref || '|' || CASE WHEN ok THEN '1' ELSE '0' END FROM live
'@

function Invoke-Sql([string]$Sql) {
    $out = docker exec $Container psql -U $DbUser -d $Database -tA -F '|' -c $Sql 2>&1
    if ($LASTEXITCODE -ne 0) { throw "psql failed: $out" }
    return ($out | Where-Object { $_ -ne '' })
}

try {
    $raw = Invoke-Sql $livenessSql
    $refs = foreach ($line in $raw) {
        $i = $line.LastIndexOf('|')
        [pscustomobject]@{ ref = $line.Substring(0, $i); ok = ($line.Substring($i + 1) -eq '1') }
    }
    $refs = @($refs)

    $hasMarkTable = (Invoke-Sql "SELECT to_regclass('platform.source_ref_stale_mark') IS NOT NULL")[0] -eq 't'
    $marked = @()
    $byCause = @{}
    if ($hasMarkTable) {
        $marked = @(Invoke-Sql "SELECT source_ref FROM platform.source_ref_stale_mark WHERE NOT active")
        foreach ($line in (Invoke-Sql "SELECT cause || '|' || count(*) FROM platform.source_ref_stale_mark WHERE NOT active GROUP BY cause")) {
            $parts = $line -split '\|'
            $byCause[$parts[0]] = [int]$parts[1]
        }
    }
    $markSet = @{}
    foreach ($m in $marked) { $markSet[$m] = $true }
}
catch {
    Write-Output "DETECT_FAILED: $($_.Exception.Message)"
    exit 2
}

$total = $refs.Count
$live = @($refs | Where-Object { $_.ok }).Count
$stale = $total - $live
$staleMarked = @($refs | Where-Object { -not $_.ok -and $markSet.ContainsKey($_.ref) }).Count
$staleUnmarked = @($refs | Where-Object { -not $_.ok -and -not $markSet.ContainsKey($_.ref) })
$activeTotal = $total - $staleMarked

$rawPct = if ($total -gt 0) { [math]::Round(100 * $live / $total, 2) } else { 0 }
$activePct = if ($activeTotal -gt 0) { [math]::Round(100 * $live / $activeTotal, 2) } else { 0 }

Write-Output "========== source_ref health ($Container / $Database) =========="
Write-Output ("mark_table_present      : {0}" -f $hasMarkTable)
Write-Output ("observation_refs_total  : {0}" -f $total)
Write-Output ("live                    : {0}" -f $live)
Write-Output ("stale_total             : {0}" -f $stale)
Write-Output ("stale_marked            : {0}" -f $staleMarked)
Write-Output ("stale_unmarked          : {0}" -f $staleUnmarked.Count)
Write-Output ("freshness_raw           : {0} %  (live / all refs)" -f $rawPct)
Write-Output ("freshness_active        : {0} %  (live / refs not marked stale)" -f $activePct)
if ($byCause.Count -gt 0) {
    foreach ($k in ($byCause.Keys | Sort-Object)) { Write-Output ("mark_cause[{0}]        : {1}" -f $k, $byCause[$k]) }
}

if ($Detail -or $staleUnmarked.Count -gt 0) {
    Write-Output "---------- unmarked broken refs ----------"
    foreach ($item in $staleUnmarked) { Write-Output ("BROKEN  {0}" -f $item.ref) }
}

if ($staleUnmarked.Count -gt 0) {
    Write-Output "VERDICT: FAIL (unmarked broken refs present)"
    exit 1
}
Write-Output "VERDICT: PASS (all observation refs are live or explicitly marked stale)"
exit 0
