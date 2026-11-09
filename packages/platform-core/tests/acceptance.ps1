# S0 acceptance: happy path + two failure paths.
# Usage: powershell -ExecutionPolicy Bypass -File .\tests\acceptance.ps1 [-OnlyPreflight]
# 默认跑独立栈 platform-acceptance：api 8082 / pg 5433 / reasoner 7882 / embedding 8083,
# 数据根 D:\agentABC\data-acceptance，图库不发布宿主端口。
# 共享栈属显式少数派行为，必须同时传：
#   -ComposeProject agent-platform -ApiBaseUrl http://127.0.0.1:8080 -PgPort 5432 `
#   -ReasonerPort 7879 -EmbeddingPort 8081 -DataRoot D:\agentABC\data
# 互斥：全量验收属长任务，运行期间持 heavy.lock；容器启动一律先过 compose-guard（R1 技术拦截）。
# 判定（2026-11-06）：skipped > 0 即不通过（退出码 2）；reasoner 缺失的派生跳过标注
# SKIPPED_DEPENDENCY，不静默放过。锁被他人持有时直接中止（退出码 75）。
# 自检：每个 smoke suite 必须打印 passed/total 且 passed == total，否则退出 0 也判 FAIL。
# 证据：transcript 固定写入 doc/evidence/acceptance-s0s13-<project>-<时间戳>-<git sha>.log（git 跟踪）。
param(
    [switch]$OnlyPreflight,
    # 默认指向独立验收栈（platform-acceptance），不是共享栈 8080/5432。
    # 显式跑共享栈必须同时指定这些参数（少数派行为），见 doc/_design 的说明。
    [string]$ComposeProject = 'platform-acceptance',
    [string]$ApiBaseUrl = 'http://127.0.0.1:8082',
    [int]$PgPort = 5433,
    [int]$ReasonerPort = 7882,
    [int]$EmbeddingPort = 8083,
    [int]$OxigraphPort = 0,     # 0 = 不给宿主发布图库端口（GSP 治理面之外不可直连）
    [string]$DataRoot = 'D:\agentABC\data-acceptance'
)
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
# 运行时数据根：独立栈默认 D:/agentABC/data-acceptance，与共享栈 D:/agentABC/data
# 完全分离（对象存储、导出目录、platform.yaml 均不共用）。
$dataRoot = $DataRoot
$dataRootNormalized = ($DataRoot -replace '\\', '/')

# 项目名决定容器名、网络、命名卷（compose 按 project 隔离）；端口/数据根由 env 注入，
# 供 compose 的 ${...} 插值使用。所有 compose 调用都带 -p 与这两份 file。
$env:COMPOSE_PROJECT_NAME = $ComposeProject
$env:PLATFORM_PORT = "$([int]($ApiBaseUrl -replace '.*:', ''))"
$env:POSTGRES_PORT = "$PgPort"
$env:REASONER_PORT = "$ReasonerPort"
$env:EMBEDDING_PORT = "$EmbeddingPort"
$env:PLATFORM_DATA_ROOT = $dataRootNormalized
if ($OxigraphPort -gt 0) { $env:OXIGRAPH_PORT = "$OxigraphPort" }
$composeFiles = @('-f', 'docker-compose.yml')
if ($OxigraphPort -gt 0) { $composeFiles += @('-f', 'docker-compose.oxigraph-host.yml') }
$composeArgs = @('compose', '-p', $ComposeProject) + $composeFiles
$effectiveStack = $ComposeProject
$lockFileName = if ($effectiveStack -eq 'agent-platform') { 'heavy.lock' } else { "$effectiveStack.heavy.lock" }

# 证据入仓：每次验收写一份 transcript 到 git 跟踪目录 doc/evidence/，
# 固定命名 acceptance-s0s13-<时间戳>-<git sha>.log（不再只写在 .gitignore 的 logs/ 下）。
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$evidenceDir = Join-Path $repoRoot 'doc\evidence'
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
$gitSha = (& git -C $repoRoot rev-parse --short HEAD 2>$null | Select-Object -First 1)
if (-not $gitSha) { $gitSha = 'nogit' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$evidenceFile = Join-Path $evidenceDir "acceptance-s0s13-$ComposeProject-$stamp-$gitSha.log"
$script:transcript = $null
try { $script:transcript = Start-Transcript -Path $evidenceFile -Force } catch { Write-Host "WARN: transcript unavailable: $_" }
Write-Host "S0-S13 acceptance start ts=$stamp git=$gitSha project=$ComposeProject api=$ApiBaseUrl pg=$PgPort reasoner=$ReasonerPort data=$dataRoot evidence_file=$evidenceFile"

$script:passed = 0
$script:failed = 0
$script:skipped = 0
$script:degraded = 0
$script:lockHeld = $false
$script:owner = "$env:COMPUTERNAME\$env:USERNAME#$PID"   # 带 PID：同用户的不同会话也能区分
$guardScript = (Resolve-Path (Join-Path $PSScriptRoot '..\scripts\compose-guard.ps1')).Path
$lockPath = Join-Path (Split-Path -Parent $PSScriptRoot) ".lock\$lockFileName"

function Get-HeavyLock {
    if (-not (Test-Path -LiteralPath $lockPath)) { return $null }
    try { return (Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json) } catch { return [pscustomobject]@{ owner = 'unknown'; purpose = 'corrupt' } }
}

function Get-TboxPointer {
    # 只读查询：当前已发布的 T-Box 版本 id（用于 smoke 后恢复指针）。
    $out = & docker @composeArgs exec -T postgres psql -U platform -d platform -tAc "SELECT version_id FROM platform.graph_pointer WHERE name='tbox/current'" 2>$null
    $line = @($out | Where-Object { $_ -and "$_" -notmatch '^ERROR' } | Select-Object -First 1)
    if ($line.Count -eq 0) { return '' }
    return "$($line[0])".Trim()
}

function Get-LockAgeMinutes([string]$iso) {
    if (-not $iso) { return -1 }
    try { return [math]::Round(((Get-Date).ToUniversalTime() - ([datetime]$iso).ToUniversalTime()).TotalMinutes, 1) } catch { return -1 }
}

$script:lockSnapshot = Get-HeavyLock
$lockState = if ($script:lockSnapshot) { "busy owner=$($script:lockSnapshot.owner) purpose=$($script:lockSnapshot.purpose)" } else { 'free' }
Write-Host "heavy_lock=$lockState"

# 止血（2026-11-06）：锁被他人持有 = 本脚本没有执行权。旧行为只跳过"起容器"，
# 之后仍照跑全部 smoke，锁形同虚设，导致同栈被多个会话交替改写。
# 新行为：在任何 compose config / 容器检查 / smoke 之前直接中止，退出码 75
# （E_BUILD_CONFLICT，与 compose-guard 一致）。-OnlyPreflight 是只读诊断，不跑 smoke，
# 允许继续，但同样打印持有者信息。
$busyByOther = ($script:lockSnapshot -and $script:lockSnapshot.owner -ne $script:owner)
if ($busyByOther -and -not $OnlyPreflight) {
    $age = Get-LockAgeMinutes $script:lockSnapshot.heartbeat_at
    Write-Host "[FAIL] E_BUILD_CONFLICT: $lockFileName 被其他任务持有，验收已在任何检查/smoke 之前中止。"
    Write-Host "  holder.owner=$($script:lockSnapshot.owner)"
    Write-Host "  holder.pid=$($script:lockSnapshot.pid) host=$($script:lockSnapshot.host)"
    Write-Host "  holder.purpose=$($script:lockSnapshot.purpose)"
    Write-Host "  holder.started_at=$($script:lockSnapshot.started_at) heartbeat_at=$($script:lockSnapshot.heartbeat_at) age=${age}min"
    Write-Host "  lock_file=$lockPath"
    Write-Host "  处理: 等 holder 结束；若确认其已退出，执行"
    Write-Host "        powershell -ExecutionPolicy Bypass -File scripts\compose-guard.ps1 release -Owner '$($script:lockSnapshot.owner)' -Stack $effectiveStack"
    Write-Host "        然后复核: powershell -ExecutionPolicy Bypass -File scripts\compose-guard.ps1 check -Stack $effectiveStack"
    Write-Host "  不要使用 compose up -d / restart 绕过。"
    if ($script:transcript) { Stop-Transcript | Out-Null }
    exit 75
}

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
    # exit 75 = blocked_by_heavy -> SKIP, but a skip is NOT a pass: it is
    # labelled SKIPPED_BLOCKED and makes the final verdict non-zero.
    if ($exitCode -eq 75) {
        $script:skipped++
        Write-Host "[SKIPPED_BLOCKED] $name exit=75 blocked_by_heavy"
    } else {
        Report $name ($exitCode -eq 0) $detail
    }
}

function Report-SkipDependency([string]$name, [string]$detail) {
    # reasoner 缺失导致的派生跳过：显式标注为 SKIPPED_DEPENDENCY，计入 skipped，
    # 最终判定为“不通过”（不再静默放过）。
    $script:skipped++
    Write-Host "[SKIPPED_DEPENDENCY] $name $detail"
}

function Assert-CliRejects([string]$name, [int]$code, [string]$expected) {
    # 负向断言只能接受被系统"判定为拒绝"的退出码；125/126/127 是 docker/命令自身
    # 用法或执行失败，不代表被测对象拒绝了输入，不能算通过。
    $ok = ($code -ne 0 -and $code -ne 125 -and $code -ne 126 -and $code -ne 127)
    Report $name $ok "exit=$code expected=$expected"
}

function Get-SmokeCounts([string[]]$lines) {
    # 自检：解析 suite 自己打印的汇总行，防止“退出 0 但一条都没跑”。
    $passed = 0
    $total = -1
    foreach ($l in $lines) {
        if ($l -match 'SMOKE(?:-S\d+)?\s+(\d+)/(\d+)') {
            $passed = [int]$Matches[1]
            $total = [int]$Matches[2]
        } elseif ($l -match 'SUMMARY passed=(\d+) failed=(\d+) total=(\d+)') {
            $passed = [int]$Matches[1]
            $total = [int]$Matches[3]
        }
    }
    return [pscustomobject]@{ passed = $passed; total = $total }
}

function Invoke-SmokeCheck([string]$slice) {
    # reasoner 由 profile 控制。只有 reasoner 容器不存在时，才允许把"纯 reasoner
    # 缺失"导致的 smoke 失败记为 SKIP。判定必须逐行严格：每一条 [FAIL] 行都要带
    # 错误码，且该行出现的所有 E_* 码只能是 E_REASONER_UNAVAILABLE；无错误码的
    # 派生断言、或出现任何其他错误码（如 E_GRAPH_BAD_REQUEST / E_EMBED_UNAVAILABLE）
    # 一律记 FAIL。输出照常打印，不改动 smoke 内部任何断言。
    $cmd = "smoke-$slice"
    $out = @(& docker @composeArgs exec -T platform platform $cmd 2>&1)
    $code = $LASTEXITCODE
    foreach ($l in $out) { Write-Host $l }
    $counts = Get-SmokeCounts $out
    if ($code -eq 0 -and ($counts.total -le 0 -or $counts.passed -ne $counts.total)) {
        Report "platform $cmd" $false "exit=0 but self-check failed passed=$($counts.passed) total=$($counts.total)"
        return
    }
    if ($code -eq 0) {
        Report "platform $cmd" $true "exit=0 passed=$($counts.passed)/$($counts.total)"
        return
    }
    if (-not $script:reasonerPresent) {
        $failLines = @($out | Where-Object { $_ -match '^\s*\[FAIL\]' })
        $mixed = @($failLines | Where-Object {
            $codes = @([regex]::Matches($_, 'E_[A-Z_]+') | ForEach-Object { $_.Value })
            ($codes.Count -eq 0) -or (@($codes | Where-Object { $_ -ne 'E_REASONER_UNAVAILABLE' }).Count -gt 0)
        })
        if ($failLines.Count -gt 0 -and $mixed.Count -eq 0) {
            Report-SkipDependency "platform $cmd" "reasoner-only failure(s), reasoner profile absent (exit=$code)"
            return
        }
    }
    Report "platform $cmd" $false "exit=$code"
}

function Get-HttpStatus([string]$url) {
    $code = & curl.exe -s -o NUL -w "%{http_code}" $url
    if ($LASTEXITCODE -ne 0) { return 0 }
    return [int]$code
}

function Get-SparqlCount([string]$query) {
    # S14H-P0: oxigraph no longer publishes a host port (GSP ban), so counts must
    # be read through the platform (graph-count), not a direct 127.0.0.1:7878 call.
    $raw = docker @composeArgs exec -T platform platform graph-count --query $query 2>$null | Out-String
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
docker @composeArgs config *> $null
Report "docker compose config" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== containers (no blind 'compose up -d') =="
$services = @(& docker @composeArgs config --services 2>$null)
$servicesCode = $LASTEXITCODE
$psLines = @(& docker @composeArgs ps -a --format '{{.Service}}|{{.State}}|{{.Health}}' 2>$null)
$psCode = $LASTEXITCODE
if ($servicesCode -ne 0 -or $psCode -ne 0 -or $services.Count -eq 0) {
    # compose 自身失败（125=用法/参数错误、126/127=命令不可执行）时，后面所有负向断言
    # 都会"因错误而看起来通过"。必须在跑 smoke 之前中止。
    Write-Host "[FAIL] compose query failed: config-services=$servicesCode ps=$psCode services=$($services.Count)"
    Write-Host "  compose_args=$($composeArgs -join ' ')"
    if ($script:transcript) { Stop-Transcript | Out-Null }
    exit 1
}
$cstate = @{}
foreach ($l in $psLines) {
    $p = $l -split '\|'
    if ($p.Count -ge 2) { $cstate[$p[0]] = @{ State = $p[1]; Health = $(if ($p.Count -ge 3) { $p[2] } else { '' }) } }
}
$notRunning = @()
$unhealthy = @()
# 验收必需的 5 个服务。smoke-s13 的 good 文档会走真实 embedding（provider=local-bge），
# 所以 embedding 必须在跑。独立栈通过 docker-compose.acceptance.yml 以 :ro 挂载共享栈
# 的 BGE-M3 模型文件（只读静态资产，不共用数据库/图库/对象存储/指针）。
$requiredServices = @('postgres', 'oxigraph', 'platform', 'reasoner', 'embedding')
foreach ($s in $requiredServices) {
    $st = $cstate[$s]
    if ($null -eq $st -or $st.State -ne 'running') { $notRunning += $s }
    elseif ($st.Health -and $st.Health -ne 'healthy') { $unhealthy += $s }
}
$lockNow = Get-HeavyLock
$busyByOther = ($lockNow -and $lockNow.owner -ne $script:owner)
# reasoner 由 profile 控制；独立栈（如 platform-b）不启动它时，相关生命周期断言应记为 SKIP
$script:reasonerPresent = $cstate.ContainsKey('reasoner')

if ($OnlyPreflight) {
    Write-Host "preflight: project=$ComposeProject heavy_lock=$lockState services=$($services.Count) not_running=$($notRunning.Count) unhealthy=$($unhealthy.Count) api=$ApiBaseUrl pg=$PgPort oxigraph=$OxigraphPort data=$dataRoot"
    if ($script:transcript) { Stop-Transcript | Out-Null }
    exit 0
}

if ($busyByOther) {
    # 全量验收已在脚本开头中止；能到这里的只有上面的 -OnlyPreflight 分支。
    Write-Host "[PREFLIGHT] heavy lock busy (owner=$($lockNow.owner), purpose=$($lockNow.purpose))"
}
elseif ($notRunning.Count -eq 0) {
    Report "containers running (no restart needed)" $true "services=$($services.Count)"
}
elseif ($ComposeProject -eq 'agent-platform') {
    Write-Host "not running: $($notRunning -join ',')"
    docker @composeArgs up -d
    Report "docker compose up (missing/stopped only)" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
}
else {
    # 独立栈必须由 acceptance-stack.ps1 先建好（它会初始化独立数据根与 platform.yaml）。
    # 这里绝不"顺手 up"：半初始化的独立栈会让 smoke 在错误配置上跑。
    Write-Host "[FAIL] isolated stack '$ComposeProject' is not running: $($notRunning -join ',')"
    Write-Host "  start it first:"
    Write-Host "    powershell -ExecutionPolicy Bypass -File scripts\acceptance-stack.ps1 up"
    Write-Host "  (project=$ComposeProject api=$ApiBaseUrl pg=$PgPort data=$dataRoot)"
    if ($script:transcript) { Stop-Transcript | Out-Null }
    exit 1
}
if ($unhealthy.Count -gt 0) {
    Write-Host "[DEGRADED] unhealthy=$($unhealthy -join ',') (不重建，由调用方决定)"
    $script:degraded++
}

# 全量验收属长任务（>2min）：持 heavy.lock，避免并行会话中途 rebuild/重启
& $guardScript acquire -Purpose "acceptance full run ($ComposeProject)" -TtlMinutes 10 -Owner $script:owner -Stack $effectiveStack | ForEach-Object { Write-Host $_ }
$script:lockHeld = ($LASTEXITCODE -eq 0)
if (-not $script:lockHeld) {
    # 竞态：快照时还空闲，acquire 时被别人抢到。同样中止，不再"warn 后继续"。
    Write-Host "[FAIL] E_BUILD_CONFLICT: heavy.lock acquire 失败，验收中止（未执行任何 smoke）。"
    Write-Host "  lock_file=$lockPath"
    Write-Host "  处理: 先执行 scripts\compose-guard.ps1 check 查看持有者，等其结束后重跑；确认已退出则 release -Owner '<owner>'。"
    if ($script:transcript) { Stop-Transcript | Out-Null }
    exit 75
}
Write-Host "lock_acquired owner=$script:owner ttl=10min lock_file=$lockPath"
Write-Host "lock_release_on_exit: powershell -ExecutionPolicy Bypass -File scripts\compose-guard.ps1 release -Owner '$script:owner'"

try {

$base = $ApiBaseUrl
if (-not (Wait-Ready "$base/healthz" 120)) {
    Report "healthz 200" $false "timeout waiting for $base/healthz"
    docker @composeArgs logs --tail 40 platform
} else {
    Report "healthz 200" ((Get-HttpStatus "$base/healthz") -eq 200) ""
}

if ((Get-HttpStatus "$base/readyz") -eq 200) {
    Report "readyz 200" $true ""
} else {
    Report "readyz 200" $false "status=$(Get-HttpStatus "$base/readyz")"
}

# 记录进入 smoke 前的已发布 T-Box 指针：smoke 会发布临时版本，跑完必须用官方
# "激活已有版本"（publish --existing）恢复，既避免留下探针 pointer，也让紧随其后
# 的 S14（按当前指针解析版本）看到 baseline 而不是探针版本。
$pointerBefore = Get-TboxPointer
if ($pointerBefore) { Write-Host "pointer_before=$pointerBefore" }
else { Write-Host "[DEGRADED] 无法读取 tbox/current 指针，跳过指针恢复" ; $script:degraded++ }

$demoQuery = 'SELECT (COUNT(*) AS ?n) WHERE { GRAPH <urn:platform:graph:abox:main> { ?s ?p ?o } }'
$aboxBaseline = Get-SparqlCount $demoQuery
Write-Host "demo abox baseline triples=$aboxBaseline"

Write-Host "== smoke =="
$smokeOut = @(docker @composeArgs exec -T platform platform smoke 2>&1)
$smokeCode = $LASTEXITCODE
$smokeOut | ForEach-Object { Write-Host $_ }
$smokeCounts = Get-SmokeCounts $smokeOut
Report "platform smoke" ($smokeCode -eq 0 -and $smokeCounts.total -gt 0 -and $smokeCounts.passed -eq $smokeCounts.total) "exit=$smokeCode passed=$($smokeCounts.passed)/$($smokeCounts.total)"

Write-Host "== smoke S1 =="
Invoke-SmokeCheck "s1"

Write-Host "== smoke S2 =="
Invoke-SmokeCheck "s2"

Write-Host "== smoke S3 =="
Invoke-SmokeCheck "s3"

Write-Host "== smoke S4 =="
Invoke-SmokeCheck "s4"

Write-Host "== smoke S5 =="
Invoke-SmokeCheck "s5"

Write-Host "== smoke S6 =="
Invoke-SmokeCheck "s6"

Write-Host "== smoke S7 =="
Invoke-SmokeCheck "s7"

Write-Host "== smoke S8 =="
Invoke-SmokeCheck "s8"

Write-Host "== smoke S9 =="
Invoke-SmokeCheck "s9"

Write-Host "== smoke S10 =="
Invoke-SmokeCheck "s10"

Write-Host "== smoke S11 =="
Invoke-SmokeCheck "s11"

Write-Host "== smoke S12 =="
Invoke-SmokeCheck "s12"

Write-Host "== smoke S13 =="
$s13Out = @(docker @composeArgs exec -T platform platform smoke-s13 2>&1)
$s13Code = $LASTEXITCODE
$s13Out | ForEach-Object { Write-Host $_ }
$s13Counts = Get-SmokeCounts $s13Out
if ($s13Code -eq 0 -and ($s13Counts.total -le 0 -or $s13Counts.passed -ne $s13Counts.total)) {
    Report "platform smoke-s13" $false "exit=0 but self-check failed passed=$($s13Counts.passed) total=$($s13Counts.total)"
} else {
    Report-Smoke "platform smoke-s13" $s13Code "exit=$s13Code passed=$($s13Counts.passed)/$($s13Counts.total)"
}

Write-Host "== smoke S13b embedding partitions =="
$embedOut = @(docker @composeArgs exec -T platform platform smoke-embed 2>&1)
$embedCode = $LASTEXITCODE
$embedOut | ForEach-Object { Write-Host $_ }
$embedCounts = Get-SmokeCounts $embedOut
Report "platform smoke-embed" ($embedCode -eq 0 -and $embedCounts.total -gt 0 -and $embedCounts.passed -eq $embedCounts.total) "exit=$embedCode passed=$($embedCounts.passed)/$($embedCounts.total)"

if ($pointerBefore) {
    $pointerNow = Get-TboxPointer
    if ($pointerNow -ne $pointerBefore) {
        Write-Host "== restore pointer $pointerNow -> $pointerBefore =="
        # 恢复指针是显式治理动作：smoke 已把指针推到临时 T-Box，切回基线相对当前版本
        # 必然被判为 breaking，平台要求人工 acknowledge + 记录 reason 才能落地。
        # 这不是放宽断言：恢复后的指针仍要与 pointerBefore 严格一致才判 PASS。
        $restoreOut = @(& docker @composeArgs exec -T platform platform ontology publish --version $pointerBefore --existing --acknowledge-breaking --reason "restore baseline T-Box pointer after smoke suites" 2>&1)
        $restoreCode = $LASTEXITCODE
        $restoreOut | ForEach-Object { Write-Host $_ }
        $pointerFinal = Get-TboxPointer
        Report "pointer restored" ($restoreCode -eq 0 -and $pointerFinal -eq $pointerBefore) "exit=$restoreCode pointer=$pointerFinal expected=$pointerBefore"
    } else {
        Report "pointer unchanged" $true "pointer=$pointerNow"
    }
}

Write-Host "== demo abox purity (OQ-31) =="
$aboxAfter = Get-SparqlCount $demoQuery
$testQuery = "SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } FILTER regex(str(?g), 'urn:platform:test') }"
$testLeftover = Get-SparqlCount $testQuery
$smokeQuery = "SELECT (COUNT(*) AS ?n) WHERE { GRAPH <urn:platform:graph:abox:main> { ?s ?p ?o } FILTER regex(str(?s), 'urn:platform:smoke') }"
$smokeLeftover = Get-SparqlCount $smokeQuery
Report "demo abox purity" ($aboxBaseline -ge 0 -and $aboxAfter -eq $aboxBaseline -and $testLeftover -eq 0 -and $smokeLeftover -eq 0) "baseline=$aboxBaseline after=$aboxAfter testGraphs=$testLeftover smokeSubjects=$smokeLeftover"

Write-Host "== audit export =="
$exportRaw = docker @composeArgs exec -T platform platform facts-export --out /data/tmp/s9-export 2>&1 | Out-String
$exportCode = $LASTEXITCODE
$exportMatch = [regex]::Match($exportRaw, '"count":\s*(\d+)')
$exportCount = if ($exportMatch.Success) { [int]$exportMatch.Groups[1].Value } else { -1 }
$exportFile = Join-Path $dataRoot 'tmp\s9-export\events.ndjson'
$exportLines = if (Test-Path $exportFile) { @(Get-Content $exportFile | Where-Object { $_.Trim() }).Count } else { -1 }
Report "facts-export count" ($exportCode -eq 0 -and $exportCount -ge 0 -and $exportLines -eq $exportCount) "exit=$exportCode count=$exportCount lines=$exportLines"

docker @composeArgs exec -T platform platform facts-verify --file /data/tmp/s9-export/events.ndjson
Report "facts-verify ok" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

docker @composeArgs exec -T platform platform facts-replay --file /data/tmp/s9-export/events.ndjson --dry-run
Report "facts-replay dry-run" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

if (Test-Path $exportFile) {
    $raw = Get-Content -Raw $exportFile
    $tampered = ([regex]'"payload":\{').Replace($raw, '"payload":{"tampered":1,', 1)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Resolve-Path $exportFile).Path, $tampered, $utf8NoBom)
}
docker @composeArgs exec -T platform platform facts-verify --file /data/tmp/s9-export/events.ndjson
Assert-CliRejects "facts-verify rejects tampering" $LASTEXITCODE "non-zero (not 125/126/127)"

docker @composeArgs exec -T platform platform facts-replay --file /data/tmp/s9-export/events.ndjson --dry-run
Assert-CliRejects "facts-replay rejects tampering" $LASTEXITCODE "non-zero (not 125/126/127)"

Write-Host "== config good =="
docker @composeArgs exec -T platform platform check-config --config /data/platform.yaml *> $null
Report "check-config good" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "== config bad (type error) =="
docker @composeArgs exec -T platform platform check-config --config /app/tests/bad_config.yaml *> $null
Report "check-config bad type" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (invalid provider) =="
docker @composeArgs exec -T platform platform check-config --config /app/tests/bad_config_unsupported_provider.yaml *> $null
Report "check-config bad provider" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (chunk overlap) =="
docker @composeArgs exec -T platform platform check-config --config /app/tests/bad_config_documents.yaml *> $null
Report "check-config bad chunk overlap" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (search range) =="
docker @composeArgs exec -T platform platform check-config --config /app/tests/bad_config_search.yaml *> $null
Report "check-config bad search range" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (extraction rule) =="
docker @composeArgs exec -T platform platform check-config --config /app/tests/bad_config_extraction.yaml *> $null
Report "check-config bad extraction rule" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (reasoning profile) =="
docker @composeArgs exec -T platform platform check-config --config /app/tests/bad_config_reasoning.yaml *> $null
Report "check-config bad reasoning profile" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== config bad (context budget) =="
docker @composeArgs exec -T platform platform check-config --config /app/tests/bad_config_context.yaml *> $null
Report "check-config bad context budget" ($LASTEXITCODE -eq 78) "exit=$LASTEXITCODE expected=78"

Write-Host "== failure path: reasoner container stopped =="
if ($script:reasonerPresent) {
    docker @composeArgs stop reasoner *> $null
    Report "stop reasoner" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
} else {
    Report-SkipDependency "stop reasoner" "reasoner profile not started in this stack"
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
    docker @composeArgs start reasoner *> $null
    Report "start reasoner" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

    if (Wait-Ready "http://127.0.0.1:$ReasonerPort/healthz" 120) {
        Report "reasoner recovers to 200" $true ""
    } else {
        Report "reasoner recovers to 200" $false "timeout"
    }
} else {
    Report-SkipDependency "start reasoner" "reasoner profile not started in this stack"
    Report-SkipDependency "reasoner recovers to 200" "reasoner profile not started in this stack"
}

Write-Host "== failure path: graph unavailable =="
docker @composeArgs stop oxigraph *> $null
Report "stop oxigraph" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

docker @composeArgs exec -T platform platform probe --config /data/platform.yaml --retry-seconds 0 *> $null
Report "probe fails fast (69)" ($LASTEXITCODE -eq 69) "exit=$LASTEXITCODE expected=69"

$readyStatus = Get-HttpStatus "$base/readyz"
Report "readyz 503 while graph down" ($readyStatus -eq 503) "status=$readyStatus"

docker @composeArgs start oxigraph *> $null
Report "start oxigraph" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

if (Wait-Ready "$base/readyz" 90) {
    Report "readyz recovers to 200" $true ""
} else {
    Report "readyz recovers to 200" $false "timeout"
}

Write-Host ""
$checks = $script:passed + $script:failed + $script:skipped
Write-Host "ACCEPTANCE passed=$script:passed failed=$script:failed skipped=$script:skipped degraded=$script:degraded checks=$checks evidence=$evidenceFile"
if ($checks -eq 0) { Write-Host "[FAIL] self-check: no acceptance check ran" }
}
finally {
    if ($script:lockHeld) {
        & $guardScript release -Owner $script:owner -Stack $effectiveStack | ForEach-Object { Write-Host $_ }
    }
    if ($script:transcript) { Stop-Transcript | Out-Null }
}
if ($script:passed + $script:failed + $script:skipped -eq 0) { exit 1 }
if ($script:failed -gt 0) { exit 1 }
elseif ($script:skipped -gt 0) {
    # 跳过不是通过：reasoner 缺失（SKIPPED_DEPENDENCY）意味着本轮验收不完整，退出码非 0。
    # 锁被他人持有时已在脚本开头直接 exit 75，不会走到这里。
    Write-Host "WARN: skipped=$script:skipped -> NOT PASS (验收不完整；跳过项已在输出中逐条标注)"
    exit 2
}
elseif ($script:degraded -gt 0) {
    Write-Host "WARN: degraded=$script:degraded (容器不健康且未重建；由 guard 持有者或人工拉起)"
    exit 69   # EX_UNAVAILABLE：环境不可用但未重建；区别于 1=断言失败、75=锁冲突、78=配置错误
}
else { exit 0 }
