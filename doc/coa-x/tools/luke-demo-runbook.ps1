#requires -Version 5.1
<#
演示 runbook 复跑脚本（基线 luke @ 38b9c4c5，分支 verify/luke-runbook）。

一条命令：
    powershell -NoProfile -ExecutionPolicy Bypass -File doc\coa-x\tools\luke-demo-runbook.ps1 -Start -Check

默认行为：对"已在跑"的演示栈做只读校验（不写库）。
    -Start             起演示栈（oxigraph 容器 + 桥），不起 web
    -Check             只跑校验（默认）
    -Import            额外跑一次真实导入（向 5944 的 platform 库写入 1 个批次）
    -ImportDir <path>  -Import 的源目录；缺省用 .runbook\import-src（脚本自动生成 1 个 md）
    -Stop              停掉本脚本起的桥与 oxigraph 容器

自选端口（均为非保留端口，不碰 8080/8082/5444/5944/8799/8099/8102/5174）：
    8210  平台桥 doc/coa-x/tools/coa_api_local.py（指向 5944 的 platform 库）
    7878  oxigraph（容器 runbook-oxigraph，卷 runbook-oxigraph-data）
    8091  context-manager（SPARQL 经桥需要；本机起不来，见 evidence 文档）

不改仓库 DSN / compose / env 默认值：数据库指向只写在 .runbook\platform.yaml
这份临时 config（运行时从 packages/platform-core/config/authoritative-8080.yaml
复制并替换），以及本次进程的环境变量里。

不碰：8080 / 8082 运行态、D:\agentABC\data\READONLY 哨兵、任何既有容器与卷。
#>
[CmdletBinding()]
param(
  [switch]$Start,
  [switch]$Check,
  [switch]$Import,
  [string]$ImportDir,
  [switch]$Stop
)

$ErrorActionPreference = "Stop"

$Repo    = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$WorkDir = Join-Path $Repo ".runbook"
$LogDir  = Join-Path $WorkDir "logs"
$PidFile = Join-Path $WorkDir "pids.json"

$ApiPort = 8210
$OxiPort = 7878
$DimNs   = "5f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
$PgName  = "coa-takeover-pg"
$PgDsn   = "postgresql://platform:platform_dev@127.0.0.1:5944/platform"
$OxiName = "runbook-oxigraph"
$OxiVol  = "runbook-oxigraph-data"

$Python  = "D:\agentABC\coa\.venv-coa-local\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

New-Item -ItemType Directory -Force -Path $WorkDir, $LogDir | Out-Null

$Results = New-Object System.Collections.Generic.List[object]
function Record([string]$Step, [string]$Verdict, [string]$Detail) {
  $Results.Add([pscustomobject]@{ Step = $Step; Verdict = $Verdict; Detail = $Detail })
  $color = switch ($Verdict) { "PASS" { "Green" } "WARN" { "Yellow" } default { "Red" } }
  Write-Host ("[{0}] {1} — {2}" -f $Verdict, $Step, $Detail) -ForegroundColor $color
}

function Psql([string]$Sql) {
  $out = & docker exec $PgName psql -U platform -d platform -tAc $Sql 2>&1
  if ($LASTEXITCODE -ne 0) { throw "psql failed: $out" }
  return ($out | Where-Object { $_ -ne "" } | Select-Object -First 1)
}

function Test-Port([int]$Port) {
  return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

# 从仓库内的权威基线复制一份临时 config，只改本演示需要的四项。
function New-DemoConfig {
  $src = Join-Path $Repo "packages\platform-core\config\authoritative-8080.yaml"
  $dst = Join-Path $WorkDir "platform.yaml"
  $storage = ((Join-Path $WorkDir "storage") -replace '\\', '/')
  $tmp = ((Join-Path $WorkDir "storage\tmp") -replace '\\', '/')
  $out = foreach ($l in (Get-Content -Encoding UTF8 $src)) {
    if     ($l -match '^\s*url:\s*postgresql://')                { "  url: $PgDsn" }
    elseif ($l -match '^\s*endpoint:\s*http://oxigraph:7878')    { "  endpoint: http://127.0.0.1:$OxiPort" }
    elseif ($l -match '^\s*endpoint:\s*http://embedding:80/v1')  { "  endpoint: http://127.0.0.1:8081/v1" }
    elseif ($l -match '^\s*root:\s*/data\s*$')                   { "  root: $storage" }
    elseif ($l -match '^\s*tmp_dir:\s*/data/tmp\s*$')            { "  tmp_dir: $tmp" }
    else   { $l }
  }
  [IO.File]::WriteAllLines($dst, $out, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "  [config] $dst（database/graph/storage 指向本机 5944/$OxiPort）"
}

function New-ImportSample {
  # 每次跑都用一个新的源目录：批次按 root 去重，复用同一目录只会新增 item run、
  # 不会在 ingestion-runs 列表里多出一行。
  $dir = Join-Path $WorkDir ("import-src\run-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $f = Join-Path $dir "loan-account-metrics.md"
  $body = @(
    "# 演示导入样本：贷款账户口径说明",
    "",
    "本文档用于 luke 演示 runbook 的导入环节，内容为该平台的贷款账户口径说明。",
    "",
    "- institution：金融机构名称，必填。",
    "- loan_id：贷款合同号，必填，全局唯一。",
    "- amount：合同金额，数值型，单位为本币元。",
    "- status：合同状态，取值 active / closed / delinquent。",
    "- origination_date：放款日期，格式 YYYY-MM-DD。",
    "",
    "口径约定：金额为合同本金，不含应计利息；状态以核心系统日终快照为准。"
  ) -join "`r`n"
  [IO.File]::WriteAllText($f, $body, (New-Object System.Text.UTF8Encoding($false)))
  return $dir
}

function Start-Oxigraph {
  if (Test-Port $OxiPort) { Write-Host "  [ok] :$OxiPort 已在监听（复用）"; return }
  & docker run -d --name $OxiName -p "127.0.0.1:$OxiPort`:7878" -v "${OxiVol}:/data" `
      oxigraph/oxigraph:0.5.7 serve --location /data --bind 0.0.0.0:7878 | Out-Null
  for ($i = 0; $i -lt 30; $i++) { if (Test-Port $OxiPort) { break }; Start-Sleep -Seconds 1 }
  if (-not (Test-Port $OxiPort)) { throw "oxigraph 未能在 :$OxiPort 起来" }
  Write-Host "  [start] oxigraph :$OxiPort"
  $n = (curl.exe -s -X POST -H "Content-Type: application/sparql-query" `
        --data "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }" "http://127.0.0.1:$OxiPort/query")
  if ($n -match '"value":\s*"0"') {
    $ttl = Join-Path $Repo "doc\_fsldm\fsldm-merged.ttl"
    curl.exe -s -o NUL -X PUT -H "Content-Type: text/turtle" --data-binary "@$ttl" `
      "http://127.0.0.1:$OxiPort/store" | Out-Null
    Write-Host "  [seed] 已写入 $ttl 到默认图"
  }
}

function Set-RepoPythonPath {
  $env:PYTHONUTF8 = "1"
  $env:PYTHONIOENCODING = "utf-8"
  $env:PYTHONPATH = ((Get-ChildItem (Join-Path $Repo "packages"), (Join-Path $Repo "libs") -Directory |
      ForEach-Object { Join-Path $_.FullName "src" }) -join ';') + ';' +
      (Join-Path $Repo "smithy-generated\control-plane-python-server")
}

function Start-Bridge {
  if (Test-Port $ApiPort) { Write-Host "  [ok] :$ApiPort 已在监听（复用）"; return }
  Set-RepoPythonPath
  $env:COA_LOCAL_API_PORT = "$ApiPort"
  $env:COA_CONTROL_PLANE_PG_DSN = $PgDsn
  $env:COA_METADATA_PG_DSN = $PgDsn
  $env:PLATFORM__DATABASE__URL = $PgDsn
  $env:PLATFORM__GRAPH__ENDPOINT = "http://127.0.0.1:$OxiPort"
  $env:PLATFORM__STORAGE__ROOT = Join-Path $WorkDir "storage"
  $env:PLATFORM__STORAGE__TMP_DIR = Join-Path $WorkDir "storage\tmp"
  $env:COA_GRAPH_OXIGRAPH_URL = "http://127.0.0.1:$OxiPort"
  $env:COA_ONTOLOGY_OXIGRAPH_URL = "http://127.0.0.1:$OxiPort"
  $env:COA_PROVIDER_METRIC_GRAPH = "oxigraph"
  $env:COA_PROVIDER_ONTOLOGY_GRAPH = "oxigraph"
  $env:COA_PROVIDER_ONTOLOGY_REGISTRY = "postgres"
  $env:COA_PROVIDER_ONTOLOGY_JOBS = "postgres"
  $env:COA_PROVIDER_ONTOLOGY_OBJECTS = "fs"
  $env:COA_LOCAL_DEV_AUTH = "on"
  $env:COA_LOCAL_DEV_USERS = "local-dev@example.invalid"
  $env:COA_LOCAL_DEV_ADMIN_USER = "local-dev@example.invalid"
  $env:COA_LOCAL_OBJECT_ROOT = Join-Path $WorkDir "objects"
  $env:COA_LOCAL_OBJECT_BASE = "http://127.0.0.1:$ApiPort/_local/objects"
  $env:NDB_GRAPH_URI_BASE = "https://coa.local/graph"
  $env:COA_LOCAL_GRAPH_ALLOWED_EXTRA_PREFIXES = "https://coa.local/graph"

  $p = Start-Process -FilePath $Python -ArgumentList "doc\coa-x\tools\coa_api_local.py" `
        -WorkingDirectory $Repo -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "api-$ApiPort.log") `
        -RedirectStandardError  (Join-Path $LogDir "api-$ApiPort.err.log")
  for ($i = 0; $i -lt 90; $i++) { if (Test-Port $ApiPort) { break }; Start-Sleep -Seconds 1 }
  if (-not (Test-Port $ApiPort)) { throw "桥未能在 :$ApiPort 起来，见 $LogDir\api-$ApiPort.err.log" }
  @{ api = $p.Id } | ConvertTo-Json | Set-Content -Encoding UTF8 $PidFile
  Write-Host "  [start] api :$ApiPort pid=$($p.Id)"
}

function Get-Token {
  $body = '{"email":"local-dev@example.invalid"}'
  $req = Join-Path $WorkDir "token-req.json"
  [IO.File]::WriteAllText($req, $body, (New-Object System.Text.UTF8Encoding($false)))
  $resp = curl.exe -s -X POST -H "Content-Type: application/json" --data-binary "@$req" `
            "http://127.0.0.1:$ApiPort/local/auth/token"
  return ($resp | ConvertFrom-Json).accessToken
}

function Invoke-Api([string]$Token, [string]$Path) {
  return curl.exe -s -H "Authorization: Bearer $Token" "http://127.0.0.1:$ApiPort$Path"
}

function Invoke-ApiRaw([string]$Token, [string]$Path) {
  return curl.exe -s -w "|%{http_code}" -H "Authorization: Bearer $Token" "http://127.0.0.1:$ApiPort$Path"
}

# ---------------------------------------------------------------------------
# -Stop
# ---------------------------------------------------------------------------
if ($Stop) {
  if (Test-Path $PidFile) {
    $ids = Get-Content $PidFile -Raw | ConvertFrom-Json
    foreach ($k in $ids.PSObject.Properties.Name) { Stop-Process -Id $ids.$k -Force -ErrorAction SilentlyContinue }
    Remove-Item $PidFile -Force
  }
  $owner = (Get-NetTCPConnection -LocalPort $ApiPort -State Listen -ErrorAction SilentlyContinue).OwningProcess
  foreach ($p in $owner) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }
  & docker rm -f $OxiName 2>$null | Out-Null
  Write-Host "已停止演示栈（8080/8082 未触碰）"
  return
}

# ---------------------------------------------------------------------------
# 准备 + 起栈
# ---------------------------------------------------------------------------
New-DemoConfig
if ($Import) {
  if (-not $ImportDir) { $ImportDir = New-ImportSample }
  elseif (-not (Test-Path $ImportDir)) { throw "导入源目录不存在: $ImportDir" }
}

if ($Start) { Start-Oxigraph; Start-Bridge }

$Token = Get-Token
if (-not $Token) { throw "拿不到本地 dev token，桥可能没起或 /local/auth/token 不可用" }
Write-Host "  [auth] local dev token ok"

# ---------------------------------------------------------------------------
# 1) 列表页数字 vs 库里 count
# ---------------------------------------------------------------------------
$dbV = [int](Psql "select count(*) from platform.ontology_version")
$dbP = [int](Psql "select count(*) from platform.ontology_proposal")
$vj = (Invoke-Api $Token "/namespaces/$DimNs/ontologies/ont-demo/versions") | ConvertFrom-Json
$pj = (Invoke-Api $Token "/namespaces/$DimNs/ontologies/ont-demo/proposals") | ConvertFrom-Json
if ([int]$vj.total -eq $dbV) { Record "版本列表 total = DB count" "PASS" "API total=$($vj.total) = DB $dbV（本页 items=$($vj.count)）" }
else { Record "版本列表 total = DB count" "FAIL" "API total=$($vj.total) vs DB $dbV" }
if ([int]$pj.count -eq $dbP) { Record "提案列表 count = DB count" "PASS" "API count=$($pj.count) = DB $dbP（本页 items=$(@($pj.items).Count)）" }
else { Record "提案列表 count = DB count" "FAIL" "API count=$($pj.count) vs DB $dbP" }

# ---------------------------------------------------------------------------
# 2) 详情页逐值核对（库里最新一条版本 + 最新一条提案）
# ---------------------------------------------------------------------------
$vRow = (Psql "select version_id||'|'||semver||'|'||status||'|'||trim(content_hash)||'|'||triple_count from platform.ontology_version order by created_at desc limit 1").Split('|')
$vd = (Invoke-Api $Token "/namespaces/$DimNs/ontologies/$($vRow[0])/versions/$($vRow[0])") | ConvertFrom-Json
$okV = ($vd.id -eq $vRow[0]) -and ($vd.semver -eq $vRow[1]) -and ($vd.status -eq $vRow[2]) -and
       ($vd.contentHash -eq $vRow[3]) -and ([int]$vd.tripleCount -eq [int]$vRow[4])
if ($okV) { Record "版本详情逐值核对" "PASS" "$($vRow[0]) semver=$($vRow[1]) status=$($vRow[2]) hash=$($vRow[3].Substring(0,12))… triple=$($vRow[4])" }
else { Record "版本详情逐值核对" "FAIL" "API 与 DB 不一致: $($vd | ConvertTo-Json -Compress)" }

$pRow = (Psql "select proposal_id||'|'||coalesce(version_id,'-')||'|'||status from platform.ontology_proposal order by created_at desc limit 1").Split('|')
$pd = (Invoke-Api $Token "/namespaces/$DimNs/ontologies/ont-demo/proposals/$($pRow[0])") | ConvertFrom-Json
$okP = ($pd.proposal.proposalId -eq $pRow[0]) -and ($pd.proposal.versionId -eq $pRow[1]) -and ($pd.proposal.status -eq $pRow[2])
if ($okP) { Record "提案详情逐值核对" "PASS" "$($pRow[0]) versionId=$($pRow[1]) status=$($pRow[2])" }
else { Record "提案详情逐值核对" "FAIL" "API 与 DB 不一致: $($pd | ConvertTo-Json -Compress)" }

# ---------------------------------------------------------------------------
# 3) 图查询：直连 oxigraph 必须返回行；桥的 /sparql 受 context-manager 限制
# ---------------------------------------------------------------------------
$direct = curl.exe -s -w "|%{http_code}" -X POST -H "Content-Type: application/sparql-query" `
            --data "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 3" "http://127.0.0.1:$OxiPort/query"
if ($direct -match '"bindings"') {
  $cnt = ([regex]::Matches($direct, '"type"')).Count
  Record "SPARQL 直连 :$OxiPort" "PASS" "返回 bindings（$cnt 个 term）"
} else { Record "SPARQL 直连 :$OxiPort" "FAIL" "无 bindings: $direct" }

$q = '{"sparql":"SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 3"}'
$qf = Join-Path $WorkDir "sparql.json"
[IO.File]::WriteAllText($qf, $q, (New-Object System.Text.UTF8Encoding($false)))
$viaBridge = curl.exe -s -w "|%{http_code}" -X POST -H "Authorization: Bearer $Token" `
               -H "Content-Type: application/json" --data-binary "@$qf" `
               "http://127.0.0.1:$ApiPort/namespaces/$DimNs/sparql"
$code = ($viaBridge -split '\|')[-1]
$body = ($viaBridge -split '\|')[0]
if ($code -eq "200") {
  if ($body -match '"bindings"') { Record "SPARQL 经桥 :$ApiPort" "PASS" "HTTP 200，返回 bindings" }
  else { Record "SPARQL 经桥 :$ApiPort" "FAIL" "HTTP 200 但无 bindings: $body" }
} else {
  Record "SPARQL 经桥 :$ApiPort" "WARN" "HTTP $code — $body（context-manager :8091 依赖 bedrock_agentcore，本机起不来；见 evidence）"
}

# ---------------------------------------------------------------------------
# 4) 可选：真实导入一条（会写 5944 的 platform 库）
# ---------------------------------------------------------------------------
if ($Import) {
  $beforeDb  = [int](Psql "select count(*) from platform.import_run")
  $beforeIds = @(((Invoke-Api $Token "/namespaces/$DimNs/ingestion-runs") | ConvertFrom-Json).items |
                 ForEach-Object { $_.runId })
  Set-RepoPythonPath
  $cfg = Join-Path $WorkDir "platform.yaml"
  $out = & $Python -m platform_core.cli import $ImportDir --namespace-id $DimNs --config $cfg `
           --parse-concurrency 1 --embed-concurrency 1 --batch-size 5 2>&1
  $afterDb  = [int](Psql "select count(*) from platform.import_run")
  $afterList = (Invoke-Api $Token "/namespaces/$DimNs/ingestion-runs") | ConvertFrom-Json
  $newIds = @($afterList.items | Where-Object { $beforeIds -notcontains $_.runId } | ForEach-Object { $_.runId })
  if (($afterDb -eq $beforeDb + 1) -and ($newIds.Count -ge 1)) {
    $bid = $newIds[0]
    $detRaw = Invoke-ApiRaw $Token "/namespaces/$DimNs/ingestion-runs/$bid"
    $detCode = ($detRaw -split '\|')[-1]
    $det = ($detRaw -split '\|')[0] | ConvertFrom-Json
    $rv = $det.run
    if ($detCode -eq "200" -and $rv -and [int]$rv.total -ge 1 -and [int]$rv.indexed -ge 1) {
      Record "导入一条" "PASS" "import_run $beforeDb -> $afterDb；列表新批次 $bid（total=$($rv.total) indexed=$($rv.indexed) documentsAdded=$($rv.lastRun.counters.documentsAdded) status=$($rv.status)）；详情 200"
    } else {
      Record "导入一条" "FAIL" "import_run $beforeDb -> $afterDb，但批次详情 HTTP $detCode / run.total=$($rv.total) / run.indexed=$($rv.indexed)"
    }
  } else {
    Record "导入一条" "FAIL" "import_run $beforeDb -> $afterDb；列表新增批次数=$($newIds.Count)；CLI 尾部: $($out | Select-Object -Last 3)"
  }
}

# ---------------------------------------------------------------------------
# 5) 冻结护栏：8080 只读仍 200，哨兵仍在（本脚本从不写 8080）
# ---------------------------------------------------------------------------
$ro = curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8080/readonly"
$sentinel = Test-Path "D:\agentABC\data\READONLY"
if ($ro -eq "200" -and $sentinel) { Record "8080 冻结护栏" "PASS" "/readonly=200，哨兵 D:\agentABC\data\READONLY 存在" }
else { Record "8080 冻结护栏" "FAIL" "/readonly=$ro，哨兵=$sentinel" }

# ---------------------------------------------------------------------------
Write-Host ""
$Results | Format-Table -AutoSize
$fail = @($Results | Where-Object { $_.Verdict -eq "FAIL" }).Count
$warn = @($Results | Where-Object { $_.Verdict -eq "WARN" }).Count
Write-Host ("总计 {0} 项：PASS {1} / WARN {2} / FAIL {3}" -f $Results.Count, ($Results.Count - $fail - $warn), $warn, $fail)
if ($fail -gt 0) { exit 1 }
