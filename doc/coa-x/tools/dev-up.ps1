#requires -Version 5.1
<#
.SYNOPSIS
  一条命令起停本地演示栈：PostgreSQL + Oxigraph + 本体服务 + API 桥 + 前端 Vite。

.DESCRIPTION
  与 10-本地起栈.ps1（固定 5444/7878/8101/8099/5173）的区别：
  本脚本的整套端口可以平移。默认从 9300 起自动找一块连续空闲端口：

      9300  PostgreSQL   (容器 coa-devup-pg-<base>，命名卷 coa-devup-pg-data-<base>)
      9301  Oxigraph     (容器 coa-devup-oxi-<base>，命名卷 coa-devup-oxi-data-<base>)
      9302  本体服务     doc/coa-x/tools/coa_ontology_local.py
      9303  API 桥       doc/coa-x/tools/coa_api_local.py
      9304  前端 Vite    packages/web-app（vite.dev-local.config.mjs）
      9305  预留         context-manager（本轮不起，仅用于把探测指离别人的 8091）

  传 -BasePort 9400 就把整套平移到 9400..9404；任何一个端口被占用都会直接报错，
  不会静默改到别的服务上。默认自动选块，不会碰别人正在跑的 8080/8082/8210/7878/
  8131/8321/5331。

  三个反复踩到的坑写进了默认值（详见 README 段落与本文件 §默认配置）：

  1. COA_LOCAL_GRAPH_ALLOWED_EXTRA_PREFIXES 默认设为 https://coa.local/graph。
     不设时 F58/F59 术语页返回 403 E_GRAPH_GRAPH_NOT_ALLOWED。
  2. ONTOLOGY_ENGINE_ENDPOINT 默认指向“本脚本刚起的本体服务”（BasePort+2），
     不再落到 8101 那个不属于本工作树的旧进程（表现为 15 秒后 500）。
  3. 前端健康页的数据来源文案不再写死 8099/8101/8091，改为读 /system-health
     返回的 components[].url（代码改动，见 packages/web-app/src/pages/SystemHealthPage.tsx）。

  自检四项（任一项失败会指出是哪一环）：
    1) API 桥 GET /health -> 200
    2) 术语接口 GET /namespaces/<ns>/terms -> 200（验证图白名单生效）
    3) GET /namespaces/<ns>/ontologies/<id>/versions -> 200 且有版本行
    4) Oxigraph 命名图计数可读（-Seed 后应 >= 1）

.PARAMETER BasePort
  整套端口的起点。0（默认）= 从 9300 开始自动找一块 5 个连续空闲端口。

.PARAMETER PgDsn
  复用外部 PostgreSQL（例如演示库 5944），不再起 PG 容器，也不做迁移。
  要求该库 schema 版本与本工作树代码一致，否则直接失败（不擅自升级共享库）。

.PARAMETER OxigraphUrl
  复用外部 Oxigraph（例如 7878），不再起 Oxigraph 容器。

.PARAMETER Seed
  灌入 doc/_fsldm 三册并注册一个 draft 版本，使术语/版本接口有数据。
  默认：自建 PG/Oxigraph 时开启；复用外部数据时关闭（不写共享数据）。

.PARAMETER NoSeed
  即使自建数据也不灌数据。

.PARAMETER NoWeb
  只起后端，不起 Vite（前端依赖缺失时可用）。

.PARAMETER Stop
  停掉本脚本上一次启动的进程与容器（只按 state.json 记录操作，不按端口猜）。
  命名卷保留，数据不会丢。

.PARAMETER KeepData
  与 -Stop 一起用：保留自建 PG/Oxigraph 容器运行，只停进程。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File doc/coa-x/tools/dev-up.ps1
  powershell -ExecutionPolicy Bypass -File doc/coa-x/tools/dev-up.ps1 -BasePort 9400 -Seed
  powershell -ExecutionPolicy Bypass -File doc/coa-x/tools/dev-up.ps1 -PgDsn "postgresql://platform:platform_dev@127.0.0.1:5944/platform" -OxigraphUrl "http://127.0.0.1:7878"
  powershell -ExecutionPolicy Bypass -File doc/coa-x/tools/dev-up.ps1 -Stop
#>
[CmdletBinding()]
param(
    [int]$BasePort = 0,
    [int]$PgPort = 0,
    [int]$OxigraphPort = 0,
    [int]$OntologyPort = 0,
    [int]$BridgePort = 0,
    [int]$WebPort = 0,
    [string]$PgDsn = "",
    [string]$OxigraphUrl = "",
    [string]$Namespace = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd",
    [string]$EmbeddingEndpoint = "http://127.0.0.1:8081/v1",
    [switch]$Seed,
    [switch]$NoSeed,
    [switch]$NoWeb,
    [switch]$Stop,
    [switch]$KeepData,
    [int]$TimeoutSeconds = 240
)

# 默认配置：三个坑的默认值都在这里，改这里即可，不要散落到各分支。
$Defaults = @{
    BasePort                = 9300
    GraphUriBase            = "https://coa.local/graph"
    # 坑 1：不设这个前缀，术语接口 403。本地放宽，生产不得带该前缀。
    GraphAllowedExtraPrefixes = "https://coa.local/graph"
    # 坑 2：本体服务地址由本次实际端口推导，绝不沿用 8101 旧进程。
    #       见 Start-Ontology 之后的 $env:ONTOLOGY_ENGINE_ENDPOINT。
    Namespace               = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd"
    EmbeddingEndpoint       = "http://127.0.0.1:8081/v1"
    PgUser                  = "platform"
    PgPassword              = "platform_dev"
    PgImage                 = "pgvector/pgvector:pg18-trixie"
    OxigraphImage           = "oxigraph/oxigraph:0.5.7"
    # 端口偏移：整套平移时只改 BasePort，偏移保持不变。
    Offsets                 = @{ Pg = 0; Oxigraph = 1; Ontology = 2; Bridge = 3; Web = 4; ReservedContext = 5 }
}

$ErrorActionPreference = "Stop"

$Repo      = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Tools     = Join-Path $Repo "doc\coa-x\tools"
$WebApp    = Join-Path $Repo "packages\web-app"
$Bootstrap = Join-Path $Tools "local_bootstrap.py"
$ApiTool   = Join-Path $Tools "coa_api_local.py"
$OntoTool  = Join-Path $Tools "coa_ontology_local.py"
$FsldmTtl  = Join-Path $Repo "doc\_fsldm\fsldm-merged.ttl"

$RunRoot   = Join-Path $env:TEMP "coa-dev-up"
$StatePath = Join-Path $RunRoot "state.json"
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null

$script:Steps = New-Object System.Collections.Generic.List[object]
$script:Owned = @{
    Processes  = New-Object System.Collections.Generic.List[object]
    Containers = New-Object System.Collections.Generic.List[string]
}

# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

function Write-Step([string]$Name, [double]$Seconds, [string]$Detail = "") {
    $script:Steps.Add([pscustomobject]@{ Step = $Name; Seconds = $Seconds; Detail = $Detail })
    Write-Host ("  [ok] {0,-26} {1,5:n1}s  {2}" -f $Name, $Seconds, $Detail)
}

function Test-PortFree([int]$Port) {
    $listener = $null
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener) { $listener.Stop() }
    }
}

function Get-PortOwner([int]$Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $conn) { return "unknown" }
    $proc = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $conn.OwningProcess) -ErrorAction SilentlyContinue
    if ($proc) { return ("pid={0} {1}" -f $conn.OwningProcess, $proc.Name) }
    return ("pid={0}" -f $conn.OwningProcess)
}

function Assert-PortFree([int]$Port, [string]$Name) {
    if (-not (Test-PortFree $Port)) {
        throw ("{0} 端口 {1} 已被占用（{2}）。换一套端口：-BasePort <别的起点>" -f $Name, $Port, (Get-PortOwner $Port))
    }
}

function Select-BasePort {
    for ($b = $Defaults.BasePort; $b -le ($Defaults.BasePort + 500); $b += 10) {
        $ports = @(
            $b + $Defaults.Offsets.Pg
            $b + $Defaults.Offsets.Oxigraph
            $b + $Defaults.Offsets.Ontology
            $b + $Defaults.Offsets.Bridge
            $b + $Defaults.Offsets.Web
            $b + $Defaults.Offsets.ReservedContext
        )
        $allFree = $true
        foreach ($p in $ports) { if (-not (Test-PortFree $p)) { $allFree = $false; break } }
        if ($allFree) { return $b }
    }
    throw "在 $($Defaults.BasePort)..$($Defaults.BasePort + 500) 里找不到一整块连续空闲端口"
}

function Invoke-Json([string]$Method, [string]$Url, $Body, [hashtable]$Headers = @{}, [int]$TimeoutSec = 60) {
    $req = @{
        Uri                = $Url
        Method             = $Method
        UseBasicParsing    = $true
        TimeoutSec         = $TimeoutSec
        Headers            = $Headers
    }
    if ($null -ne $Body) {
        if ($Body -is [string]) {
            # 调用方自带 Content-Type（如 SPARQL）时不要再设一遍，否则 PowerShell
            # 会报“该请求头必须用对应参数修改”。
            $req["Body"] = [System.Text.Encoding]::UTF8.GetBytes($Body)
            if (-not $Headers.ContainsKey("Content-Type")) {
                $req["ContentType"] = "application/json; charset=utf-8"
            }
        } else {
            $json = $Body | ConvertTo-Json -Depth 8 -Compress
            $req["Body"] = [System.Text.Encoding]::UTF8.GetBytes($json)
            $req["ContentType"] = "application/json; charset=utf-8"
        }
    }
    $status = -1
    $text = ""
    try {
        $resp = Invoke-WebRequest @req
        $status = [int]$resp.StatusCode
        $text = [System.Text.Encoding]::UTF8.GetString($resp.RawContentStream.ToArray())
    } catch {
        $ex = $_.Exception
        if ($ex.Response) {
            $status = [int]$ex.Response.StatusCode
            try {
                $stream = $ex.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
                $text = $reader.ReadToEnd()
            } catch {
                $text = "$($_.ErrorDetails.Message)"
            }
        } else {
            $text = "$($ex.Message)"
        }
    }
    $obj = $null
    if ($text.Trim()) {
        try { $obj = $text | ConvertFrom-Json } catch { $obj = $null }
    }
    return [pscustomobject]@{ Status = $status; Text = $text; Json = $obj }
}

function Wait-Http200([string]$Url, [int]$Seconds) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        $r = Invoke-Json -Method GET -Url $Url -TimeoutSec 5
        if ($r.Status -eq 200) { return $true }
        Start-Sleep -Milliseconds 700
    }
    return $false
}

function Wait-Tcp([int]$Port, [string]$Name, [int]$Seconds) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if (-not (Test-PortFree $Port)) { return $true }
        Start-Sleep -Milliseconds 500
    }
    throw ("{0} 在 {1}s 内没有监听 :{2}" -f $Name, $Seconds, $Port)
}

function Invoke-Native([string]$File, [string[]]$NativeArgs) {
    # 探针类调用：非零退出是预期结果（容器不存在、PG 还没 ready），
    # 不能让它变成 NativeCommandError 终止整条脚本。
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $out = & $File @NativeArgs 2>&1 | ForEach-Object { "$_" }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prev
    }
    return [pscustomobject]@{ ExitCode = $code; Output = @($out) }
}

function Test-ContainerExists([string]$Name) {
    return (Invoke-Native docker @("inspect", $Name)).ExitCode -eq 0
}

function Wait-PgReady([string]$Container, [int]$Seconds) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        $r = Invoke-Native docker @("exec", $Container, "pg_isready", "-U", $Defaults.PgUser, "-d", "postgres")
        if ($r.ExitCode -eq 0) { return $true }
        Start-Sleep -Milliseconds 800
    }
    return $false
}

function Invoke-Docker([string[]]$DockerArgs, [switch]$Quiet) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $out = & docker @DockerArgs 2>&1 | ForEach-Object { "$_" }
    } finally {
        $ErrorActionPreference = $prev
    }
    if (-not $Quiet -and $out) { $out | Where-Object { "$_".Trim() } | ForEach-Object { Write-Host ("    {0}" -f $_) } }
    if ($LASTEXITCODE -ne 0) {
        throw ("docker {0} 失败（exit {1}）：{2}" -f ($DockerArgs -join " "), $LASTEXITCODE, ($out -join " / "))
    }
}

function Resolve-Python {
    $candidates = @()
    $candidates += (Join-Path $Repo ".venv-coa-local\Scripts\python.exe")
    if ($env:COA_DEV_PYTHON) { $candidates += $env:COA_DEV_PYTHON }
    # 同机主树的 venv 是可复用依赖集；PYTHONPATH 会把本工作树的 src 排在前面。
    $sibling = Join-Path (Split-Path (Split-Path $Repo -Parent) -Parent) "coa\.venv-coa-local\Scripts\python.exe"
    $candidates += $sibling
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw "找不到 Python：请先创建本工作树 .venv-coa-local，或用 COA_DEV_PYTHON 指定解释器"
}

function Set-RepoPythonPath {
    $parts = @()
    foreach ($dir in @("packages", "libs")) {
        $root = Join-Path $Repo $dir
        if (Test-Path $root) {
            $parts += Get-ChildItem $root -Directory | ForEach-Object { Join-Path $_.FullName "src" }
        }
    }
    $parts += (Join-Path $Repo "smithy-generated\control-plane-python-server")
    $env:PYTHONPATH = ($parts -join ";")
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
}

function Get-DbSchemaVersion([string]$Dsn) {
    $code = "import sys, psycopg; c=psycopg.connect(sys.argv[1]); print(c.execute('select coalesce(max(version),0) from platform.schema_version').fetchone()[0])"
    $r = Invoke-Native $Python @("-c", $code, $Dsn)
    if ($r.ExitCode -ne 0) { return $null }
    $line = @($r.Output | Where-Object { "$_" -match '^\d+$' } | Select-Object -Last 1)
    if ($line.Count -eq 0) { return $null }
    return [int]$line[0]
}

function Get-SupportedSchemaVersion {
    $file = Join-Path $Repo "packages\control-plane\src\coa_control_plane\platform_db\registry.py"
    $match = Select-String -Path $file -Pattern "SUPPORTED_SCHEMA_VERSION\s*=\s*(\d+)" | Select-Object -First 1
    if ($match) { return [int]$match.Matches[0].Groups[1].Value }
    return $null
}

function Get-OxigraphNamedGraphs([string]$Base) {
    $q = "SELECT (COUNT(DISTINCT ?g) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }"
    $resp = Invoke-Json -Method POST -Url "$Base/query" -Body $q -Headers @{ "Content-Type" = "application/sparql-query"; "Accept" = "application/sparql-results+json" } -TimeoutSec 30
    if ($resp.Status -ne 200 -or -not $resp.Json) { return $null }
    try { return [int]$resp.Json.results.bindings[0].n.value } catch { return $null }
}

function Save-State {
    # PowerShell 5.1 对 @($listOfObject) 会抛 "Argument types do not match"，
    # 这里用 ToArray() 明确转成 object[]。
    $state = @{
        BasePort   = $BasePort
        Ports      = @{ Pg = $PgPort; Oxigraph = $OxigraphPort; Ontology = $OntologyPort; Bridge = $BridgePort; Web = $WebPort }
        Namespace  = $Namespace
        Processes  = $script:Owned.Processes.ToArray()
        Containers = $script:Owned.Containers.ToArray()
        StartedAt  = (Get-Date).ToString("o")
    }
    [System.IO.File]::WriteAllText($StatePath, ($state | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
}

function Stop-RecordedStack {
    if (-not (Test-Path $StatePath)) {
        Write-Host "[stack] 没有找到本脚本的 state.json（$StatePath），没有可停的东西。"
        return
    }
    $state = Get-Content $StatePath -Raw | ConvertFrom-Json
    Write-Host ("[stack] 停止上一次启动的栈（base={0}, started={1}）" -f $state.BasePort, $state.StartedAt)
    foreach ($p in @($state.Processes)) {
        if (-not $p -or -not $p.Pid) { continue }
        $proc = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $p.Pid) -ErrorAction SilentlyContinue
        if (-not $proc) {
            Write-Host ("  [--] pid={0} {1} 已退出" -f $p.Pid, $p.Name)
            continue
        }
        if ($proc.CommandLine -and $proc.CommandLine -like ("*" + $p.Marker + "*")) {
            Write-Host ("  [stop] {0} pid={1}" -f $p.Name, $p.Pid)
            Stop-Process -Id $p.Pid -Force -ErrorAction SilentlyContinue
        } else {
            Write-Host ("  [skip] pid={0} 的命令行不含 {1}（不是本脚本起的进程）" -f $p.Pid, $p.Marker)
        }
    }
    if (-not $KeepData) {
        foreach ($name in @($state.Containers)) {
            if (-not $name) { continue }
            if ((Invoke-Native docker @("inspect", "-f", "{{.State.Running}}", $name)).ExitCode -eq 0) {
                Write-Host ("  [stop] container {0}" -f $name)
                Invoke-Native docker @("stop", $name) | Out-Null
            }
        }
        Write-Host "  [keep] 命名卷保留；要清数据用 docker volume rm <name>"
    } else {
        Write-Host "  [keep] -KeepData：容器继续运行"
    }
    Remove-Item $StatePath -Force
    Write-Host "Done."
}

# ---------------------------------------------------------------------------
# -Stop
# ---------------------------------------------------------------------------
if ($Stop) {
    Stop-RecordedStack
    return
}

# 不允许悄悄覆盖一个仍在运行的 state：那会把上一套栈的 PID 记录弄丢。
if (Test-Path $StatePath) {
    $previous = Get-Content $StatePath -Raw | ConvertFrom-Json
    $liveProcs = @()
    foreach ($p in @($previous.Processes)) {
        if (-not $p -or -not $p.Pid) { continue }
        $proc = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $p.Pid) -ErrorAction SilentlyContinue
        if ($proc -and $proc.CommandLine -and $proc.CommandLine -like ("*" + $p.Marker + "*")) {
            $liveProcs += ("{0}(pid={1})" -f $p.Name, $p.Pid)
        }
    }
    if ($liveProcs.Count -gt 0) {
        throw ("上一次的栈还在运行（base={0}: {1}）。先执行 -Stop，或确认那套栈已经手工清理。" -f $previous.BasePort, ($liveProcs -join ", "))
    }
}

# ---------------------------------------------------------------------------
# 0) 环境检查
# ---------------------------------------------------------------------------
Write-Host "COA 本地演示栈 · dev-up"
$totalTimer = [System.Diagnostics.Stopwatch]::StartNew()

$Python = Resolve-Python
Set-RepoPythonPath
Write-Host ("  [env] python = {0}" -f $Python)
if ($Python -notlike "$Repo*") {
    Write-Host "  [warn] 使用工作树外的 Python；代码通过 PYTHONPATH 指回本工作树（$Repo）"
}

$externalPg = [bool]$PgDsn
$externalOxi = [bool]$OxigraphUrl

# 端口：显式 BasePort 固定，0 则自动选一块。
if ($BasePort -eq 0) {
    $BasePort = Select-BasePort
    Write-Host ("  [env] 自动选择端口块 base={0}" -f $BasePort)
}
$PgPort       = if ($PgPort -gt 0)       { $PgPort }       else { $BasePort + $Defaults.Offsets.Pg }
$OxigraphPort = if ($OxigraphPort -gt 0) { $OxigraphPort } else { $BasePort + $Defaults.Offsets.Oxigraph }
$OntologyPort = if ($OntologyPort -gt 0) { $OntologyPort } else { $BasePort + $Defaults.Offsets.Ontology }
$BridgePort   = if ($BridgePort -gt 0)   { $BridgePort }   else { $BasePort + $Defaults.Offsets.Bridge }
$WebPort      = if ($WebPort -gt 0)      { $WebPort }      else { $BasePort + $Defaults.Offsets.Web }
$ReservedContextPort = $BasePort + $Defaults.Offsets.ReservedContext

if ($externalPg) {
    if ($PgDsn -match ':(\d+)/[^/]+(?:\?|$)') { $PgPort = [int]$Matches[1] }
} else {
    Assert-PortFree $PgPort "PostgreSQL"
}
if ($externalOxi) {
    if ($OxigraphUrl -match ':(\d+)/?$') { $OxigraphPort = [int]$Matches[1] }
} else {
    Assert-PortFree $OxigraphPort "Oxigraph"
}
Assert-PortFree $OntologyPort "本体服务"
Assert-PortFree $BridgePort "API 桥"
if (-not $NoWeb) { Assert-PortFree $WebPort "前端 Vite" }
if (-not (Test-PortFree $ReservedContextPort)) {
    Write-Host ("  [warn] 预留的 context-manager 探测端口 {0} 被占用（{1}）；/system-health 会把它误报为 ok" -f $ReservedContextPort, (Get-PortOwner $ReservedContextPort))
}

$needDocker = (-not $externalPg) -or (-not $externalOxi)
if ($needDocker) {
    $dockerProbe = Invoke-Native docker @("version", "--format", "{{.Server.Version}}")
    if ($dockerProbe.ExitCode -ne 0) {
        throw "需要 Docker 来起本栈的 PG/Oxigraph，但 docker daemon 不可达（$($dockerProbe.Output -join ' ')）"
    }
    Write-Host "  [env] docker ok"
}

if (-not $NoWeb) {
    $viteJs = Join-Path $WebApp "node_modules\vite\bin\vite.js"
    if (-not (Test-Path $viteJs)) {
        throw "前端依赖缺失：$viteJs。先执行 `pnpm install --frozen-lockfile`，或加 -NoWeb 只起后端。"
    }
}
if (-not (Test-Path $FsldmTtl)) { throw "缺少本体数据：$FsldmTtl" }

$LogDir = Join-Path $RunRoot ("logs-" + $BasePort)
New-Item -ItemType Directory -Force -Path `
    $LogDir, `
    (Join-Path $RunRoot "objects"), `
    (Join-Path $RunRoot "data"), `
    (Join-Path $RunRoot "data\storage"), `
    (Join-Path $RunRoot "data\tmp"), `
    (Join-Path $RunRoot "data\shapes") | Out-Null

Write-Host ("  [env] 端口: PG={0} Oxigraph={1} 本体={2} 桥={3} 前端={4}" -f $PgPort, $OxigraphPort, $OntologyPort, $BridgePort, $WebPort)

# ---------------------------------------------------------------------------
# 1) PostgreSQL
# ---------------------------------------------------------------------------
$PgName = "coa-devup-pg-$BasePort"
$PlatformDsn = "postgresql://$($Defaults.PgUser):$($Defaults.PgPassword)@127.0.0.1:$PgPort/platform"
$ServeDsn    = "postgresql://$($Defaults.PgUser):$($Defaults.PgPassword)@127.0.0.1:$PgPort/serve_local"
$SupportedSchema = Get-SupportedSchemaVersion

if ($externalPg) {
    Write-Host "[1/5] PostgreSQL：复用外部 DSN（不迁移共享库）"
    if ($PgDsn -notmatch '/platform(\?|$)') {
        throw "外部 DSN 的库名必须是 platform（本栈按 platform + serve_local 两库约定）：$PgDsn"
    }
    $t = [System.Diagnostics.Stopwatch]::StartNew()
    $v = Get-DbSchemaVersion $PgDsn
    if ($null -eq $v) { throw "外部 PostgreSQL 不可达或没有 platform.schema_version：$PgDsn" }
    if ($null -ne $SupportedSchema -and $v -ne $SupportedSchema) {
        throw ("外部 PostgreSQL schema={0}，本工作树代码要求 {1}。不要擅自升级共享库；改用 -BasePort 起自建库。" -f $v, $SupportedSchema)
    }
    $PlatformDsn = $PgDsn
    $ServeDsn = ($PgDsn -replace '/platform(\?|$)', '/serve_local$1')
    $serveVersion = Get-DbSchemaVersion $ServeDsn
    if ($null -eq $serveVersion) { throw "外部 PostgreSQL 缺少 serve_local 库或未迁移：$ServeDsn" }
    Write-Step "PostgreSQL(复用)" $t.Elapsed.TotalSeconds ("schema platform={0} serve_local={1}" -f $v, $serveVersion)
} else {
    Write-Host "[1/5] PostgreSQL：容器 $PgName"
    $t = [System.Diagnostics.Stopwatch]::StartNew()
    if (Test-ContainerExists $PgName) {
        Invoke-Docker @("start", $PgName) -Quiet
    } else {
        Invoke-Docker @(
            "run", "-d", "--name", $PgName,
            "--publish", "127.0.0.1:${PgPort}:5432",
            "-e", "POSTGRES_USER=$($Defaults.PgUser)",
            "-e", "POSTGRES_PASSWORD=$($Defaults.PgPassword)",
            "-e", "POSTGRES_DB=platform",
            "-v", "coa-devup-pg-data-${BasePort}:/var/lib/postgresql/18/docker",
            $Defaults.PgImage
        ) -Quiet
    }
    if (-not $script:Owned.Containers.Contains($PgName)) { $script:Owned.Containers.Add($PgName) }
    Save-State
    if (-not (Wait-PgReady $PgName 90)) { throw "PostgreSQL 容器没有在 90s 内就绪：$PgName" }

    $hasServe = Invoke-Native docker @("exec", $PgName, "psql", "-U", $Defaults.PgUser, "-d", "postgres", "-tAc", "SELECT 1 FROM pg_database WHERE datname='serve_local'")
    if (-not (($hasServe.Output -join "").Trim() -eq "1")) {
        Invoke-Docker @("exec", $PgName, "psql", "-U", $Defaults.PgUser, "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-c", "CREATE DATABASE serve_local") -Quiet
    }
    foreach ($dsn in @($PlatformDsn, $ServeDsn)) {
        $db = ($dsn -split "/")[-1]
        $migrate = Invoke-Native $Python @($Bootstrap, "migrate", "--dsn", $dsn)
        if ($migrate.ExitCode -ne 0) {
            $migrate.Output | ForEach-Object { Write-Host ("    {0}" -f $_) }
            throw "迁移 $db 失败"
        }
    }
    $pv = Get-DbSchemaVersion $PlatformDsn
    $sv = Get-DbSchemaVersion $ServeDsn
    Write-Step "PostgreSQL(自建)" $t.Elapsed.TotalSeconds ("schema platform={0} serve_local={1}" -f $pv, $sv)
}

# ---------------------------------------------------------------------------
# 2) Oxigraph
# ---------------------------------------------------------------------------
$OxiName = "coa-devup-oxi-$BasePort"
$OxiBase = if ($externalOxi) { $OxigraphUrl.TrimEnd("/") } else { "http://127.0.0.1:$OxigraphPort" }

Write-Host "[2/5] Oxigraph：$OxiBase"
$t = [System.Diagnostics.Stopwatch]::StartNew()
if ($externalOxi) {
    $n = Get-OxigraphNamedGraphs $OxiBase
    if ($null -eq $n) { throw "外部 Oxigraph 不可达或 SPARQL 不返回结果：$OxiBase" }
    Write-Step "Oxigraph(复用)" $t.Elapsed.TotalSeconds ("namedGraphs={0}" -f $n)
} else {
    if (Test-ContainerExists $OxiName) {
        Invoke-Docker @("start", $OxiName) -Quiet
    } else {
        Invoke-Docker @(
            "run", "-d", "--name", $OxiName,
            "--publish", "127.0.0.1:${OxigraphPort}:7878",
            "-v", "coa-devup-oxi-data-${BasePort}:/data",
            $Defaults.OxigraphImage,
            "serve", "--location", "/data", "--bind", "0.0.0.0:7878", "--timeout-s", "20"
        ) -Quiet
    }
    $script:Owned.Containers.Add($OxiName) | Out-Null
    Save-State
    Wait-Tcp $OxigraphPort "Oxigraph" 60 | Out-Null
    $n = $null
    for ($i = 0; $i -lt 30; $i++) {
        $n = Get-OxigraphNamedGraphs $OxiBase
        if ($null -ne $n) { break }
        Start-Sleep -Seconds 1
    }
    if ($null -eq $n) { throw "Oxigraph 起来了但 SPARQL 不通：$OxiBase" }
    Write-Step "Oxigraph(自建)" $t.Elapsed.TotalSeconds ("namedGraphs={0}" -f $n)
}

# ---------------------------------------------------------------------------
# 3) 本体服务
# ---------------------------------------------------------------------------
Write-Host "[3/5] 本体服务：127.0.0.1:$OntologyPort"
$t = [System.Diagnostics.Stopwatch]::StartNew()
$env:COA_PROVIDER_ONTOLOGY_GRAPH      = "oxigraph"
$env:COA_ONTOLOGY_OXIGRAPH_URL        = $OxiBase
$env:COA_GRAPH_OXIGRAPH_URL           = $OxiBase
$env:COA_PROVIDER_ONTOLOGY_REGISTRY   = "postgres"
$env:COA_PROVIDER_ONTOLOGY_JOBS       = "postgres"
$env:COA_PROVIDER_ONTOLOGY_OBJECTS    = "fs"
$env:COA_PROVIDER_ONTOLOGY_VECTOR     = "pgvector"
$env:COA_PROVIDER_ONTOLOGY_EMBEDDING  = "http"
$env:COA_CONTROL_PLANE_PG_DSN         = $PlatformDsn
$env:PLATFORM__DATABASE__URL          = $ServeDsn
$env:COA_ONTOLOGY_PROPOSALS_PG_DSN    = $ServeDsn
$env:DYNAMODB_TABLE                   = "coa-local-ontologies"
$env:NDB_GRAPH_URI_BASE               = $Defaults.GraphUriBase
$env:COA_LOCAL_OBJECT_ROOT            = (Join-Path $RunRoot "objects")
$env:COA_LOCAL_OBJECT_BASE            = "http://127.0.0.1:$BridgePort/_local/objects"
$env:COA_EMBEDDING_URL                = $EmbeddingEndpoint
$env:COA_EMBEDDING_MODEL              = "BAAI/bge-m3"
$env:COA_EMBEDDING_DIMENSIONS         = "1024"
$env:COA_VECTOR_DIMENSIONS            = "1024"
$env:ALLOWED_ORIGIN                   = "http://127.0.0.1:$WebPort"
$env:COA_ONTOLOGY_HOST                = "127.0.0.1"
$env:COA_ONTOLOGY_PORT                = "$OntologyPort"

$ontoOut = Join-Path $LogDir "ontology.log"
$ontoErr = Join-Path $LogDir "ontology.err.log"
$ontoProc = Start-Process -FilePath $Python -ArgumentList @($OntoTool) -WorkingDirectory $Repo `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput $ontoOut -RedirectStandardError $ontoErr
$script:Owned.Processes.Add(@{ Name = "ontology"; Pid = $ontoProc.Id; Marker = "coa_ontology_local.py"; Port = $OntologyPort })
Set-Content -Path (Join-Path $LogDir "ontology.pid") -Value $ontoProc.Id
Save-State
if (-not (Wait-Http200 -Url "http://127.0.0.1:$OntologyPort/health" -Seconds 120)) {
    Write-Host "  本体服务日志尾部："
    Get-Content $ontoErr -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host ("    {0}" -f $_) }
    throw "本体服务没有在 :$OntologyPort 上返回 /health 200"
}
Write-Step "本体服务" $t.Elapsed.TotalSeconds ("pid={0}" -f $ontoProc.Id)

# ---------------------------------------------------------------------------
# 4) API 桥
# ---------------------------------------------------------------------------
Write-Host "[4/5] API 桥：127.0.0.1:$BridgePort"
$t = [System.Diagnostics.Stopwatch]::StartNew()
$env:COA_LOCAL_API_HOST = "127.0.0.1"
$env:COA_LOCAL_API_PORT = "$BridgePort"
$env:COA_CONTROL_PLANE_PG_DSN = $PlatformDsn
$env:COA_METADATA_PG_DSN = $ServeDsn
$env:PLATFORM__DATABASE__URL = $ServeDsn
$env:PLATFORM__DATA_DIR = (Join-Path $RunRoot "data")
$env:PLATFORM__GRAPH__ENDPOINT = $OxiBase
$env:PLATFORM__STORAGE__ROOT = (Join-Path $RunRoot "data\storage")
$env:PLATFORM__STORAGE__TMP_DIR = (Join-Path $RunRoot "data\tmp")
$env:PLATFORM__REASONING__SHAPES_DIR = (Join-Path $RunRoot "data\shapes")
$env:PLATFORM__EMBEDDING__ENDPOINT = $EmbeddingEndpoint
$env:COA_GRAPH_OXIGRAPH_URL = $OxiBase
$env:COA_ONTOLOGY_OXIGRAPH_URL = $OxiBase
# 坑 2：必须指向“本栈刚起的本体服务”，默认的 8101 是别人的旧进程。
$env:ONTOLOGY_ENGINE_ENDPOINT = "http://127.0.0.1:$OntologyPort"
# 不把探测留给 8091：那个端口可能属于别的会话。
$env:COA_CONTEXT_MANAGER_ENDPOINT = "http://127.0.0.1:$ReservedContextPort"
# 坑 1：本地放宽图白名单（生产不得带该前缀）。
$env:COA_LOCAL_GRAPH_ALLOWED_EXTRA_PREFIXES = $Defaults.GraphAllowedExtraPrefixes
$env:COA_LOCAL_REASONING_ABOX_GRAPH = "$($Defaults.GraphUriBase)/$Namespace/urn%3Acoa%3Aabox%3Aplatform-synthetic"
$env:PLATFORM__REASONING__MAX_ASSEMBLY_BYTES = "157286400"
$env:COA_LOCAL_DEV_AUTH = "on"
$env:COA_LOCAL_DEV_USERS = "local-dev@example.invalid"
$env:COA_LOCAL_DEV_ADMIN_USER = "local-dev@example.invalid"
$env:COA_LOCAL_OBJECT_ROOT = (Join-Path $RunRoot "objects")
$env:COA_LOCAL_OBJECT_BASE = "http://127.0.0.1:$BridgePort/_local/objects"
$env:BUCKET_NAME = "coa-local-documents"
$env:COA_PROVIDER_CONTEXT_MANAGER = "local-http"

$apiOut = Join-Path $LogDir "bridge.log"
$apiErr = Join-Path $LogDir "bridge.err.log"
$apiProc = Start-Process -FilePath $Python -ArgumentList @($ApiTool) -WorkingDirectory $Repo `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput $apiOut -RedirectStandardError $apiErr
$script:Owned.Processes.Add(@{ Name = "bridge"; Pid = $apiProc.Id; Marker = "coa_api_local.py"; Port = $BridgePort })
Save-State
if (-not (Wait-Http200 -Url "http://127.0.0.1:$BridgePort/health" -Seconds 180)) {
    Write-Host "  API 桥日志尾部："
    Get-Content $apiErr -Tail 30 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host ("    {0}" -f $_) }
    throw "API 桥没有在 :$BridgePort 上返回 /health 200"
}
Write-Step "API 桥" $t.Elapsed.TotalSeconds ("pid={0}" -f $apiProc.Id)

# 本地 dev token：后面注册版本与自检都要用。桥的 /system-health 还会顺手把
# 进程内的 platform_core 应用装配起来（/local/ontology/register 只有在装配后
# 才存在，这是路由按需注册的副作用，不是缺配置）。
$tokenResp = Invoke-Json -Method POST -Url "http://127.0.0.1:$BridgePort/local/auth/token" -Body @{ email = "local-dev@example.invalid" } -TimeoutSec 30
$token = $null
if ($tokenResp.Status -eq 200 -and $tokenResp.Json) { $token = $tokenResp.Json.accessToken }
if ($token) {
    $warm = Invoke-Json -Method GET -Url "http://127.0.0.1:$BridgePort/system-health" -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 120
    if ($warm.Status -ne 200) {
        Write-Host ("  [warn] 预热 /system-health 返回 HTTP {0}；注册版本可能不可用" -f $warm.Status)
    }
} else {
    Write-Host ("  [warn] 取不到本地 dev token（HTTP {0}）：{1}" -f $tokenResp.Status, $tokenResp.Text)
}

# ---------------------------------------------------------------------------
# 5) 可选：灌数据（自建数据默认灌，外部数据默认不写）
# ---------------------------------------------------------------------------
$doSeed = $Seed -or (-not $NoSeed -and -not $externalPg -and -not $externalOxi)
if ($doSeed) {
    Write-Host "[5/6] 灌入 FSLDM 三册并注册 draft 版本（namespace=$Namespace）"
    $t = [System.Diagnostics.Stopwatch]::StartNew()
    $seedRun = Invoke-Native $Python @($OntoTool, "--seed", "--namespace", $Namespace)
    if ($seedRun.ExitCode -ne 0) {
        $seedRun.Output | ForEach-Object { Write-Host ("    {0}" -f $_) }
        throw "FSLDM seed 失败"
    }
    Write-Step "FSLDM seed" $t.Elapsed.TotalSeconds ("namespace={0}" -f $Namespace)

    # 版本行：走公开的 ImportOntology（内部落到 /local/ontology/register），
    # 这样 /versions 才有数据；同时把 KERNEL 应用装配起来。
    $t = [System.Diagnostics.Stopwatch]::StartNew()
    $ttl = [System.IO.File]::ReadAllText($FsldmTtl, [System.Text.Encoding]::UTF8)
    $regBody = @{
        content       = $ttl
        format        = "turtle"
        semver        = "1.0.0"
        changeSummary = "dev-up demo seed"
    }
    $ontoId = [uri]::EscapeDataString("https://w3id.org/fsldm/codes")
    $reg = Invoke-Json -Method POST -Url "http://127.0.0.1:$BridgePort/namespaces/$Namespace/ontologies/$ontoId/import" `
        -Body $regBody -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 240
    if ($reg.Status -ne 200) {
        Write-Host ("  [warn] 注册 draft 版本失败（HTTP {0}）：{1}" -f $reg.Status, $reg.Text.Substring(0, [Math]::Min(300, $reg.Text.Length)))
        Write-Host "         /versions 自检会记为 WARN，不影响栈可用。"
    } else {
        Write-Step "注册 draft 版本" $t.Elapsed.TotalSeconds ("versionId={0}" -f $reg.Json.versionId)
    }
} else {
    Write-Host "[5/6] 跳过 seed（复用外部数据，默认不写共享库；需要时显式加 -Seed）"
}

# ---------------------------------------------------------------------------
# 6) 前端 Vite
# ---------------------------------------------------------------------------
if (-not $NoWeb) {
    Write-Host "[6/6] 前端 Vite：127.0.0.1:$WebPort"
    $t = [System.Diagnostics.Stopwatch]::StartNew()
    $stubDir = Join-Path $WebApp ".dev-local\auth-stub"
    New-Item -ItemType Directory -Force -Path $stubDir | Out-Null
    $stub = @'
// LOCAL-ONLY @auth entry, generated by doc/coa-x/tools/dev-up.ps1.
// Delegates to the tracked provider, which gets a real token from the local bridge.
export * from "../../src/auth/LocalDevAuthProvider";
'@
    [System.IO.File]::WriteAllText((Join-Path $stubDir "index.ts"), $stub, (New-Object System.Text.UTF8Encoding($false)))

    $runtimeConfig = [ordered]@{
        region      = "us-east-1"
        authority   = "http://LOCAL-dev-bypass.invalid"
        clientId    = "local-dev"
        apiEndpoint = "http://127.0.0.1:$BridgePort"
        version     = "dev-up"
    } | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText((Join-Path $WebApp "public\runtime-config.json"), $runtimeConfig, (New-Object System.Text.UTF8Encoding($false)))

    $viteConfig = @"
// LOCAL-ONLY vite config, generated by doc/coa-x/tools/dev-up.ps1 (git info/exclude).
// Ports follow the dev-up stack; do not commit.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const ROOT = __dirname;

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@coa/shared": path.resolve(ROOT, "../../libs/ts-shared/src/index.ts"),
      "@auth": path.resolve(ROOT, ".dev-local/auth-stub"),
      "@app-types": path.resolve(ROOT, "src/app-types"),
      "@api-hooks": path.resolve(ROOT, "src/api-hooks"),
      "@components": path.resolve(ROOT, "src/components"),
      "@pages": path.resolve(ROOT, "src/pages"),
      "@utils": path.resolve(ROOT, "src/utils"),
      "@constants": path.resolve(ROOT, "src/constants"),
    },
  },
  server: {
    host: "127.0.0.1",
    port: $WebPort,
    strictPort: true,
    proxy: {
      "/api/ontology": {
        target: "http://127.0.0.1:$BridgePort",
        rewrite: (p) => p.replace(/^\/api\/ontology/, ""),
      },
    },
  },
});
"@
    [System.IO.File]::WriteAllText((Join-Path $WebApp "vite.dev-local.config.mjs"), $viteConfig, (New-Object System.Text.UTF8Encoding($false)))

    $viteJs = Join-Path $WebApp "node_modules\vite\bin\vite.js"
    $webOut = Join-Path $LogDir "web.log"
    $webErr = Join-Path $LogDir "web.err.log"
    $webProc = Start-Process -FilePath "node" -ArgumentList @($viteJs, "--config", "vite.dev-local.config.mjs") `
        -WorkingDirectory $WebApp -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $webOut -RedirectStandardError $webErr
    $script:Owned.Processes.Add(@{ Name = "web"; Pid = $webProc.Id; Marker = "vite"; Port = $WebPort })
    if (-not (Wait-Http200 -Url "http://127.0.0.1:$WebPort/" -Seconds 120)) {
        Get-Content $webErr -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host ("    {0}" -f $_) }
        throw "Vite 没有在 :$WebPort 上返回 200"
    }
    Write-Step "前端 Vite" $t.Elapsed.TotalSeconds ("pid={0}" -f $webProc.Id)
}

Save-State

# ---------------------------------------------------------------------------
# 自检：四个点
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "================ 演示栈自检 ================"
$failures = New-Object System.Collections.Generic.List[string]

# 1) /health
$t = [System.Diagnostics.Stopwatch]::StartNew()
$health = Invoke-Json -Method GET -Url "http://127.0.0.1:$BridgePort/health" -TimeoutSec 30
$ok1 = ($health.Status -eq 200)
Write-Host ("  [1] GET /health                      HTTP {0}   ({1:n1}s)" -f $health.Status, $t.Elapsed.TotalSeconds)
if (-not $ok1) { $failures.Add("/health 不是 200（桥没起或启动被拒绝）") }

# token（起栈阶段已取；失败时再取一次）
if (-not $token) {
    $tokenResp = Invoke-Json -Method POST -Url "http://127.0.0.1:$BridgePort/local/auth/token" -Body @{ email = "local-dev@example.invalid" } -TimeoutSec 30
    if ($tokenResp.Status -eq 200 -and $tokenResp.Json) { $token = $tokenResp.Json.accessToken }
}
if (-not $token) {
    $failures.Add("取不到本地 dev token（COA_LOCAL_DEV_AUTH=on 未生效）")
}
$authHeaders = @{ Authorization = "Bearer $token" }

# 2) terms 200（白名单）
$t = [System.Diagnostics.Stopwatch]::StartNew()
$terms = Invoke-Json -Method GET -Url "http://127.0.0.1:$BridgePort/namespaces/$Namespace/terms" -Headers $authHeaders -TimeoutSec 60
$ok2 = ($terms.Status -eq 200)
Write-Host ("  [2] GET terms (白名单)               HTTP {0}   ({1:n1}s)" -f $terms.Status, $t.Elapsed.TotalSeconds)
if (-not $ok2) {
    if ($terms.Status -eq 403) {
        $failures.Add("terms 403：图白名单未生效（COA_LOCAL_GRAPH_ALLOWED_EXTRA_PREFIXES）")
    } else {
        $failures.Add(("terms 返回 HTTP {0}（本环节失败）" -f $terms.Status))
    }
}

# 3) /versions 有数
$t = [System.Diagnostics.Stopwatch]::StartNew()
$ontologyId = "https://w3id.org/fsldm/codes"
$ontoList = Invoke-Json -Method GET -Url "http://127.0.0.1:$OntologyPort/ontologies?namespace=$Namespace" -TimeoutSec 30
if ($ontoList.Status -eq 200 -and $ontoList.Json -and @($ontoList.Json.ontologies).Count -gt 0) {
    $ontologyId = @($ontoList.Json.ontologies)[0].ontologyId
}
$encoded = [uri]::EscapeDataString($ontologyId)
$versions = Invoke-Json -Method GET -Url "http://127.0.0.1:$BridgePort/namespaces/$Namespace/ontologies/$encoded/versions" -Headers $authHeaders -TimeoutSec 60
$versionTotal = $null
if ($versions.Status -eq 200 -and $versions.Json) {
    if ($null -ne $versions.Json.total) { $versionTotal = [int]$versions.Json.total }
    elseif ($null -ne $versions.Json.items) { $versionTotal = @($versions.Json.items).Count }
}
Write-Host ("  [3] GET versions                     HTTP {0}   total={1}   ({2:n1}s)" -f $versions.Status, $versionTotal, $t.Elapsed.TotalSeconds)
if ($versions.Status -ne 200) {
    $failures.Add(("versions 返回 HTTP {0}（本环节失败）" -f $versions.Status))
} elseif ($null -eq $versionTotal) {
    $failures.Add("versions 返回 200 但没有 total/items")
} elseif ($versionTotal -le 0) {
    Write-Host "      [warn] 0 个版本：自建空库没有发布过 T-Box。链路是通的，只是没有数据。"
}

# 4) Oxigraph 命名图
$t = [System.Diagnostics.Stopwatch]::StartNew()
$namedGraphs = Get-OxigraphNamedGraphs $OxiBase
Write-Host ("  [4] Oxigraph named graphs            n={0}   ({1:n1}s)" -f $namedGraphs, $t.Elapsed.TotalSeconds)
if ($null -eq $namedGraphs) {
    $failures.Add("Oxigraph 命名图计数读不到（SPARQL 失败）")
} elseif ($doSeed -and $namedGraphs -lt 1) {
    $failures.Add("seed 之后命名图仍为 0（图写入没有落库）")
}

$totalTimer.Stop()
Write-Host ""
Write-Host ("  结论：" + $(if ($failures.Count -eq 0) { "OK" } else { "CHECK FAILED" }))
foreach ($f in $failures) { Write-Host ("    - " + $f) }
Write-Host ""
Write-Host "  地址："
Write-Host ("    前端      http://127.0.0.1:{0}" -f $WebPort)
Write-Host ("    API 桥    http://127.0.0.1:{0}" -f $BridgePort)
Write-Host ("    本体服务  http://127.0.0.1:{0}" -f $OntologyPort)
Write-Host ("    Oxigraph  {0}" -f $OxiBase)
Write-Host ("    PG        postgresql://{0}:***@127.0.0.1:{1}/platform" -f $Defaults.PgUser, $PgPort)
Write-Host ("    日志      {0}" -f $LogDir)
Write-Host ""
Write-Host "  步骤耗时："
foreach ($s in $script:Steps) { Write-Host ("    {0,-26} {1,6:n1}s  {2}" -f $s.Step, $s.Seconds, $s.Detail) }
Write-Host ("    合计 {0:n1}s" -f $totalTimer.Elapsed.TotalSeconds)
Write-Host ""
Write-Host "  收栈：powershell -ExecutionPolicy Bypass -File doc/coa-x/tools/dev-up.ps1 -Stop"
if ($failures.Count -gt 0) { exit 1 }
