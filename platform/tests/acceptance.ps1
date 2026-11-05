# S0 acceptance: happy path + two failure paths.
# Usage: powershell -ExecutionPolicy Bypass -File .\tests\acceptance.ps1 [-OnlyPreflight]
#        [-ApiBaseUrl http://127.0.0.1:8080] [-PgPort 5432] [-OxigraphPort 7878]
# 可选端口参数默认值与默认栈一致；用于在独立栈（如 platform-b 8082/5433/7881）上整跑。
# 互斥：全量验收属长任务，运行期间持 heavy.lock；容器启动一律先过 compose-guard（R1 技术拦截）。
param(
    [switch]$OnlyPreflight,
    [string]$ApiBaseUrl = 'http://127.0.0.1:8080',
    [int]$PgPort = 5432,
    [int]$OxigraphPort = 7878
)
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
# Runtime data lives outside the repo (compose binds D:/agentABC/data -> /data);
# host-side assertions on exported files must use the bind source, not ./data.
$dataRoot = if ($env:PLATFORM_DATA_DIR) { $env:PLATFORM_DATA_DIR } else { 'D:\agentABC\data' }

$script:passed = 0
$script:failed = 0
$script:skipped = 0
$script:degraded = 0
$script:lockHeld = $false
$script:skipBlockedStart = $false
$script:owner = "$env:COMPUTERNAME\$env:USERNAME#$PID"   # 带 PID：同用户的不同会话也能区分
$guardScript = (Resolve-Path (Join-Path $PSScriptRoot '..\scripts\compose-guard.ps1')).Path
$lockPath = Join-Path (Split-Path -Parent $PSScriptRoot) '.lock\heavy.lock'

function Get-HeavyLock {
    if (-not (Test-Path -LiteralPath $lockPath)) { return $null }
    try { return (Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json) } catch { return [pscustomobject]@{ owner = 'unknown'; purpose = 'corrupt' } }
}

$script:lockSnapshot = Get-HeavyLock
$lockState = if ($script:lockSnapshot) { "busy owner=$($script:lockSnapshot.owner) purpose=$($script:lockSnapshot.purpose)" } else { 'free' }
Write-Host "heavy_lock=$lockState"

function Report([string]$name, [bool]$ok, [string]$detail) {
    if ($ok) {
        $script:passed++
        Write-Host "[PASS] $name $detail"
    } else {
        $script:failed++
        Write-Host "[FAIL] $name $detail"
    }
}

function Report-Smoke([string]$name, [int]$exitCode, [string]$detail) {
    # S13H-13: exit 75 = blocked_by_heavy -> SKIP, never counted as failed.
    if ($exitCode -eq 75) {
        $script:skipped++
        Write-Host "[SKIP] $name exit=75 blocked_by_heavy"
    } else {
        Report $name ($exitCode -eq 0) $detail
    }
}

function Report-Skip([string]$name, [string]$detail) {
    $script:skipped++
    Write-Host "[SKIP] $name $detail"
}

function Get-HttpStatus([string]$url) {
    $code = & curl.exe -s -o NUL -w "%{http_code}" $url
    if ($LASTEXITCODE -ne 0) { return 0 }
    return [int]$code
}

function Get-SparqlCount([string]$query) {
    # S14H-P0: oxigraph no longer publishes a host port (GSP ban), so counts must
    # be read through the platform (graph-count), not a direct 127.0.0.1:7878 call.
    $raw = docker compose exec -T platform platform graph-count --query $query 2>$null | Out-String
    if ($LASTEXITCODE -ne 0 -or -not $raw) { return -1 }
    # graph-count prints one migration log line before the JSON payload.
    $line = ($raw -split "`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
    try { return [int](($line | ConvertFrom-Json).count) } catch { return -1 }
}

function Wait-Ready([string]$url, [int]$seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        if ((Get-HttpStatus $url) -eq 200) { return $true }
        Start-Sleep -Seconds 3
    }
    return $false
}

Write-Host "== compose config =="
docker compose config *> $null
Report "docker compose config" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== containers (no blind 'compose up -d') =="
$services = @(& docker compose config --services 2>$null)
$psLines = @(& docker compose ps -a --format '{{.Service}}|{{.State}}|{{.Health}}' 2>$null)
$cstate = @{}
foreach ($l in $psLines) {
    $p = $l -split '\|'
    if ($p.Count -ge 2) { $cstate[$p[0]] = @{ State = $p[1]; Health = $(if ($p.Count -ge 3) { $p[2] } else { '' }) } }
}
$notRunning = @()
$unhealthy = @()
foreach ($s in $services) {
    $st = $cstate[$s]
    if ($null -eq $st -or $st.State -ne 'running') { $notRunning += $s }
    elseif ($st.Health -and $st.Health -ne 'healthy') { $unhealthy += $s }
}
$lockNow = Get-HeavyLock
$busyByOther = ($lockNow -and $lockNow.owner -ne $script:owner)
# reasoner 由 profile 控制；独立栈（如 platform-b）不启动它时，相关生命周期断言应记为 SKIP
$script:reasonerPresent = $cstate.ContainsKey('reasoner')

if ($busyByOther) {
    Write-Host "skipped: heavy lock busy (owner=$($lockNow.owner), purpose=$($lockNow.purpose))"
    $script:skipped++
    if ($notRunning.Count -gt 0) {
        Write-Host "  pending services (NOT started): $($notRunning -join ',')"
        $script:skipBlockedStart = $true
        Write-Host "WARN: acceptance incomplete (heavy lock busy, container start skipped)"
    }
}
elseif ($notRunning.Count -eq 0) {
    Report "containers running (no restart needed)" $true "services=$($services.Count)"
}
else {
    Write-Host "not running: $($notRunning -join ',')"
    docker compose up -d
    Report "docker compose up (missing/stopped only)" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
}
if ($unhealthy.Count -gt 0) {
    Write-Host "[DEGRADED] unhealthy=$($unhealthy -join ',') (不重建，由调用方决定)"
    $script:degraded++
}

if ($OnlyPreflight) {
    Write-Host "preflight: heavy_lock=$lockState services=$($services.Count) not_running=$($notRunning.Count) unhealthy=$($unhealthy.Count) api=$ApiBaseUrl pg=$PgPort oxigraph=$OxigraphPort"
    exit 0
}

# 全量验收属长任务（>2min）：持 heavy.lock，避免并行会话中途 rebuild/重启
& $guardScript acquire -Purpose "acceptance full run" -TtlMinutes 30 -Owner $script:owner | ForEach-Object { Write-Host $_ }
$script:lockHeld = ($LASTEXITCODE -eq 0)
if (-not $script:lockHeld) { Write-Host "warn: heavy lock busy (another task holds it); 本脚本无 import/reindex 步骤" }

try {

$base = $ApiBaseUrl
if (-not (Wait-Ready "$base/healthz" 120)) {
    Report "healthz 200" $false "timeout waiting for $base/healthz"
    docker compose logs --tail 40 platform
} else {
    Report "healthz 200" ((Get-HttpStatus "$base/healthz") -eq 200) ""
}

if ((Get-HttpStatus "$base/readyz") -eq 200) {
    Report "readyz 200" $true ""
} else {
    Report "readyz 200" $false "status=$(Get-HttpStatus "$base/readyz")"
}

$demoQuery = 'SELECT (COUNT(*) AS ?n) WHERE { GRAPH <urn:platform:graph:abox:main> { ?s ?p ?o } }'
$aboxBaseline = Get-SparqlCount $demoQuery
Write-Host "demo abox baseline triples=$aboxBaseline"

Write-Host "== smoke =="
docker compose exec -T platform platform smoke
Report "platform smoke" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S1 =="
docker compose exec -T platform platform smoke-s1
Report "platform smoke-s1" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S2 =="
docker compose exec -T platform platform smoke-s2
Report "platform smoke-s2" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S3 =="
docker compose exec -T platform platform smoke-s3
Report "platform smoke-s3" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S4 =="
docker compose exec -T platform platform smoke-s4
Report "platform smoke-s4" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S5 =="
docker compose exec -T platform platform smoke-s5
Report "platform smoke-s5" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S6 =="
docker compose exec -T platform platform smoke-s6
Report "platform smoke-s6" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S7 =="
docker compose exec -T platform platform smoke-s7
Report "platform smoke-s7" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S8 =="
docker compose exec -T platform platform smoke-s8
Report "platform smoke-s8" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S9 =="
docker compose exec -T platform platform smoke-s9
Report "platform smoke-s9" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S10 =="
docker compose exec -T platform platform smoke-s10
Report "platform smoke-s10" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S11 =="
docker compose exec -T platform platform smoke-s11
Report "platform smoke-s11" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S12 =="
docker compose exec -T platform platform smoke-s12
Report "platform smoke-s12" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== smoke S13 =="
docker compose exec -T platform platform smoke-s13
Report-Smoke "platform smoke-s13" $LASTEXITCODE "exit=$LASTEXITCODE"

Write-Host "== smoke S13b embedding partitions =="
docker compose exec -T platform platform smoke-embed
Report "platform smoke-embed" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== demo abox purity (OQ-31) =="
$aboxAfter = Get-SparqlCount $demoQuery
$testQuery = "SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } FILTER regex(str(?g), 'urn:platform:test') }"
$testLeftover = Get-SparqlCount $testQuery
$smokeQuery = "SELECT (COUNT(*) AS ?n) WHERE { GRAPH <urn:platform:graph:abox:main> { ?s ?p ?o } FILTER regex(str(?s), 'urn:platform:smoke') }"
$smokeLeftover = Get-SparqlCount $smokeQuery
Report "demo abox purity" ($aboxBaseline -ge 0 -and $aboxAfter -eq $aboxBaseline -and $testLeftover -eq 0 -and $smokeLeftover -eq 0) "baseline=$aboxBaseline after=$aboxAfter testGraphs=$testLeftover smokeSubjects=$smokeLeftover"

Write-Host "== audit export =="
$exportRaw = docker compose exec -T platform platform facts-export --out /data/tmp/s9-export 2>&1 | Out-String
$exportCode = $LASTEXITCODE
$exportMatch = [regex]::Match($exportRaw, '"count":\s*(\d+)')
$exportCount = if ($exportMatch.Success) { [int]$exportMatch.Groups[1].Value } else { -1 }
$exportFile = Join-Path $dataRoot 'tmp\s9-export\events.ndjson'
$exportLines = if (Test-Path $exportFile) { @(Get-Content $exportFile | Where-Object { $_.Trim() }).Count } else { -1 }
Report "facts-export count" ($exportCode -eq 0 -and $exportCount -ge 0 -and $exportLines -eq $exportCount) "exit=$exportCode count=$exportCount lines=$exportLines"

docker compose exec -T platform platform facts-verify --file /data/tmp/s9-export/events.ndjson
Report "facts-verify ok" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

docker compose exec -T platform platform facts-replay --file /data/tmp/s9-export/events.ndjson --dry-run
Report "facts-replay dry-run" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

if (Test-Path $exportFile) {
    $raw = Get-Content -Raw $exportFile
    $tampered = ([regex]'"payload":\{').Replace($raw, '"payload":{"tampered":1,', 1)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Resolve-Path $exportFile).Path, $tampered, $utf8NoBom)
}
docker compose exec -T platform platform facts-verify --file /data/tmp/s9-export/events.ndjson
Report "facts-verify rejects tampering" ($LASTEXITCODE -ne 0) "exit=$LASTEXITCODE expected!=0"

docker compose exec -T platform platform facts-replay --file /data/tmp/s9-export/events.ndjson --dry-run
Report "facts-replay rejects tampering" ($LASTEXITCODE -ne 0) "exit=$LASTEXITCODE expected!=0"

Write-Host "== config good =="
docker compose exec -T platform platform check-config --config /data/platform.yaml *> $null
Report "check-config good" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== config bad (type error) =="
docker compose exec -T platform platform check-config --config /app/tests/bad_config.yaml *> $null
Report "check-config bad type" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (invalid provider) =="
docker compose exec -T platform platform check-config --config /app/tests/bad_config_unsupported_provider.yaml *> $null
Report "check-config bad provider" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (chunk overlap) =="
docker compose exec -T platform platform check-config --config /app/tests/bad_config_documents.yaml *> $null
Report "check-config bad chunk overlap" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (search range) =="
docker compose exec -T platform platform check-config --config /app/tests/bad_config_search.yaml *> $null
Report "check-config bad search range" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (extraction rule) =="
docker compose exec -T platform platform check-config --config /app/tests/bad_config_extraction.yaml *> $null
Report "check-config bad extraction rule" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (reasoning profile) =="
docker compose exec -T platform platform check-config --config /app/tests/bad_config_reasoning.yaml *> $null
Report "check-config bad reasoning profile" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (context budget) =="
docker compose exec -T platform platform check-config --config /app/tests/bad_config_context.yaml *> $null
Report "check-config bad context budget" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== failure path: reasoner container stopped =="
if ($script:reasonerPresent) {
    docker compose stop reasoner *> $null
    Report "stop reasoner" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
} else {
    Report-Skip "stop reasoner" "reasoner profile not started in this stack"
}

$healthStatus = Get-HttpStatus "$base/healthz"
Report "healthz 200 with reasoner down" ($healthStatus -eq 200) "status=$healthStatus"

$matBody = Join-Path $env:TEMP "platform-reasoner-outage-body.json"
$matOut = Join-Path $env:TEMP "platform-reasoner-outage.json"
Set-Content -Path $matBody -Value '{"force":true}' -NoNewline -Encoding utf8
$matCode = & curl.exe -s -o $matOut -w "%{http_code}" -X POST -H "Content-Type: application/json" --data-binary "@$matBody" "$base/reasoning/materialize"
$matText = Get-Content $matOut -Raw -ErrorAction SilentlyContinue
Report "materialize 503 E_REASONER_UNAVAILABLE" ([int]$matCode -eq 503 -and ($matText -match "E_REASONER_UNAVAILABLE")) "status=$matCode"

if ($script:reasonerPresent) {
    docker compose start reasoner *> $null
    Report "start reasoner" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

    if (Wait-Ready "http://127.0.0.1:7879/healthz" 120) {
        Report "reasoner recovers to 200" $true ""
    } else {
        Report "reasoner recovers to 200" $false "timeout"
    }
} else {
    Report-Skip "start reasoner" "reasoner profile not started in this stack"
    Report-Skip "reasoner recovers to 200" "reasoner profile not started in this stack"
}

Write-Host "== failure path: graph unavailable =="
docker compose stop oxigraph *> $null
Report "stop oxigraph" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

docker compose exec -T platform platform probe --config /data/platform.yaml --retry-seconds 0 *> $null
Report "probe fails fast (69)" ($LASTEXITCODE -eq 69) "exit=$LASTEXITCODE expected=69"

$readyStatus = Get-HttpStatus "$base/readyz"
Report "readyz 503 while graph down" ($readyStatus -eq 503) "status=$readyStatus"

docker compose start oxigraph *> $null
Report "start oxigraph" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

if (Wait-Ready "$base/readyz" 90) {
    Report "readyz recovers to 200" $true ""
} else {
    Report "readyz recovers to 200" $false "timeout"
}

Write-Host ""
Write-Host "ACCEPTANCE passed=$script:passed failed=$script:failed skipped=$script:skipped degraded=$script:degraded"
}
finally {
    if ($script:lockHeld) {
        & $guardScript release -Owner $script:owner | ForEach-Object { Write-Host $_ }
    }
}
if ($script:failed -gt 0) { exit 1 }
elseif ($script:degraded -gt 0) {
    Write-Host "WARN: degraded=$script:degraded (容器不健康且未重建；由 guard 持有者或人工拉起)"
    exit 69   # EX_UNAVAILABLE：环境不可用但未重建；区别于 1=断言失败、75=锁冲突、78=配置错误
}
elseif ($script:skipBlockedStart) {
    Write-Host "WARN: acceptance incomplete (容器缺失/停止且因锁未启动)"
    exit 75   # E_BUILD_CONFLICT：因他人持锁未能准备环境
}
else { exit 0 }
