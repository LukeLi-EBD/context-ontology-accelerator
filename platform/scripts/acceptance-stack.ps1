# acceptance-stack.ps1 - 验收/烟测专用独立栈（与共享栈 agent-platform 完全隔离）。
#
# 隔离边界（全部独立，不共用任何持久状态）：
#   * PostgreSQL：compose 项目 platform-acceptance 的命名卷 + 宿主端口 5433
#   * Oxigraph：同项目独立命名卷，且不发布宿主端口（图库只能经 platform 访问）
#   * 对象存储/导出/配置：bind 数据根 D:/agentABC/data-acceptance（独立 platform.yaml）
#   * 指针（tbox/current 等）：随独立 PostgreSQL，不触碰共享栈
#   * 重型锁：.lock/platform-acceptance.heavy.lock（与共享栈 heavy.lock 分离）
# 共用项：Docker 镜像 agent-platform:0.1-s5；BGE-M3 模型文件（只读挂载，静态资产）；
# 宿主 CPU/内存预算。跨栈不互斥，重任务仍受 12 核/内存约束，不要同时跑两个长任务。
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts\acceptance-stack.ps1 up
#   powershell -ExecutionPolicy Bypass -File scripts\acceptance-stack.ps1 status
#   powershell -ExecutionPolicy Bypass -File scripts\acceptance-stack.ps1 down [-RemoveDataRoot]
#
# 起来后跑：powershell -ExecutionPolicy Bypass -File tests\acceptance.ps1
param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'status', 'down', 'help')]
    [string]$Action = 'status',
    [string]$ComposeProject = 'platform-acceptance',
    [int]$ApiPort = 8082,
    [int]$PgPort = 5433,
    [int]$ReasonerPort = 7882,
    [int]$EmbeddingPort = 8083,
    [int]$OxigraphPort = 0,
    [string]$DataRoot = 'D:\agentABC\data-acceptance',
    [string]$ConfigTemplate = '',
    [string]$ModelsDir = '',
    [switch]$RemoveDataRoot,
    [int]$WaitSeconds = 180,
    [int]$EmbeddingWaitSeconds = 600
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$stackScript = Join-Path $PSScriptRoot 'stack.ps1'
$dataPath = $DataRoot -replace '/', [IO.Path]::DirectorySeparatorChar
$dataRootNormalized = $DataRoot -replace '\\', '/'
$sharedDataPath = Split-Path -Parent (Split-Path -Parent $root)
$sharedDataRoot = Join-Path $sharedDataPath 'data'
if (-not $ModelsDir) { $ModelsDir = Join-Path $sharedDataRoot 'models' }
$modelsDirNormalized = ($ModelsDir -replace '\\', '/')
$acceptanceOverride = Join-Path $PSScriptRoot '..\docker-compose.acceptance.yml'
$env:ACCEPTANCE_MODELS_DIR = $modelsDirNormalized

function Get-PgPassword {
    # 与 compose 的插值顺序保持一致：shell 环境变量 > .env > 默认值。
    if ($env:POSTGRES_PASSWORD) { return $env:POSTGRES_PASSWORD }
    $envFile = Join-Path $root '.env'
    if (Test-Path -LiteralPath $envFile) {
        $match = [regex]::Match((Get-Content -LiteralPath $envFile -Raw), '(?m)^POSTGRES_PASSWORD=([^\r\n]+)')
        if ($match.Success) { return $match.Groups[1].Value.Trim() }
    }
    return 'platform_dev'
}

function Initialize-IsolatedDataRoot {
    # stack.ps1 只在 platform.yaml 缺失时从 example 复制（其中 db 口令是 CHANGE_ME）。
    # 独立栈的 CLI（smoke-s3 等）会绕过 compose env 直连，必须先把口令写成真实值。
    foreach ($sub in @('', 'blobs', 'tmp', 'shapes', 'ontology')) {
        $dir = $dataPath
        if ($sub) { $dir = Join-Path $dataPath $sub }
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $config = Join-Path $dataPath 'platform.yaml'
    if (-not (Test-Path -LiteralPath $config)) {
        $password = Get-PgPassword
        # 模板优先级：显式 -ConfigTemplate > 已跑通的共享栈 platform.yaml（仅复制文件，
        # 不共用卷/数据）> 仓库 example。复用共享配置是为了避开 example 里未经验证的
        # 默认值（实测 2026-11-06 的 example 有 canvas.provider: off 会被 YAML 读成 bool，
        # 独立栈直接 exit 78）。
        $template = $ConfigTemplate
        if (-not $template) {
            # 共享栈数据根 = 仓库父目录下的 data（D:\agentABC\data）
            $shared = Join-Path (Split-Path -Parent (Split-Path -Parent $root)) 'data\platform.yaml'
            if (Test-Path -LiteralPath $shared) { $template = $shared }
            else { $template = Join-Path $root 'platform.example.yaml' }
        }
        # 用 .NET UTF-8 读写：PS 5.1 的 Get-Content 默认按 ANSI 读无 BOM 文件，
        # 会把中文 pattern 变成乱码（实测导致 YAML 解析失败、platform exit 78）。
        $content = [System.IO.File]::ReadAllText($template)
        $content = $content -replace 'postgresql://platform:[^@]*@', "postgresql://platform:$password@"
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($config, $content, $utf8NoBom)
        Write-Host "[acceptance-stack] seeded $config from $template (db password from env/.env/default)"
    } elseif ([System.IO.File]::ReadAllText($config) -match 'CHANGE_ME') {
        Write-Host "[acceptance-stack] WARNING: $config still contains CHANGE_ME; CLI subcommands that bypass compose env may fail authentication."
    }
}

function Test-IsolatedConfig {
    # 在起容器之前先静态校验配置：失败要立刻报 E_CONFIG_INVALID，而不是让 API 反复
    # Restarting(78) 三分钟。
    $configHost = Join-Path $dataPath 'platform.yaml'
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $out = @(& docker run --rm --entrypoint platform `
        -v "${dataPath}:/data:ro" `
        agent-platform:0.1-s5 check-config --config /data/platform.yaml 2>&1)
    $ErrorActionPreference = $prevEap
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        $out | ForEach-Object { Write-Host $_ }
        Write-Host "[acceptance-stack] E_CONFIG_INVALID: $configHost failed check-config (exit=$code)"
        Write-Host "[acceptance-stack] fix the config or pass -ConfigTemplate <path>; refusing to start the isolated stack."
        exit 78
    }
    Write-Host "[acceptance-stack] config check-config OK ($configHost)"
}

switch ($Action) {
    'up' {
        Initialize-IsolatedDataRoot
        Test-IsolatedConfig
        if (-not (Test-Path -LiteralPath (Join-Path $ModelsDir 'bge-m3'))) {
            Write-Host "[acceptance-stack] WARNING: BGE-M3 not found at $ModelsDir\bge-m3; smoke-s13 will fail E_EMBED_UNAVAILABLE."
        }
        $freeGB = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
        if ($freeGB -lt 4) {
            Write-Host "[acceptance-stack] E_RESOURCE_UNAVAILABLE: free physical memory ${freeGB}GB < 4GB; refusing to start a second embedding (S13 needs it, but memory safety wins)."
            Write-Host "  stop other stacks/tasks first, or run with -ModelsDir ... after freeing memory."
            exit 69
        }
        Write-Host "[acceptance-stack] project=$ComposeProject api=$ApiPort pg=$PgPort reasoner=$ReasonerPort embedding=$EmbeddingPort data=$dataRootNormalized models=$modelsDirNormalized"
        Write-Host "[acceptance-stack] embedding sees shared models READ-ONLY (static asset); DB/graph/object-store/pointer stay isolated."
        & $stackScript up -Name $ComposeProject -ApiPort $ApiPort -PgPort $PgPort `
            -ReasonerPort $ReasonerPort -EmbeddingPort $EmbeddingPort -OxigraphPort $OxigraphPort `
            -DataRoot $dataRootNormalized -Services postgres,oxigraph,platform,reasoner,embedding `
            -ExtraComposeFiles $acceptanceOverride -WaitSeconds $WaitSeconds
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        # stack.ps1 只等 API /readyz；TEI 模型 warmup 需要额外时间，必须等 /health 200
        # 否则 smoke-s13 会在 E_EMBED_UNAVAILABLE 上失败（实测 2026-11-07）。
        $deadline = (Get-Date).AddSeconds($EmbeddingWaitSeconds)
        $embedCode = '000'
        while ((Get-Date) -lt $deadline) {
            $embedCode = (& curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:$EmbeddingPort/health")
            if ($embedCode -eq '200') { break }
            Start-Sleep -Seconds 5
        }
        if ($embedCode -ne '200') {
            Write-Host "[acceptance-stack] E_EMBED_NOT_READY: http://127.0.0.1:$EmbeddingPort/health = $embedCode after ${EmbeddingWaitSeconds}s"
            exit 1
        }
        Write-Host "[acceptance-stack] embedding ready: http://127.0.0.1:$EmbeddingPort/health"
        exit 0
    }
    'status' {
        & $stackScript status -Name $ComposeProject -ApiPort $ApiPort -PgPort $PgPort `
            -ReasonerPort $ReasonerPort -EmbeddingPort $EmbeddingPort -OxigraphPort $OxigraphPort `
            -DataRoot $dataRootNormalized
        exit $LASTEXITCODE
    }
    'down' {
        $downArgs = @{ Action = 'down'; Name = $ComposeProject; DataRoot = $dataRootNormalized }
        if ($RemoveDataRoot) { $downArgs['RemoveDataRoot'] = $true }
        & $stackScript @downArgs
        exit $LASTEXITCODE
    }
    default {
        Write-Host 'usage: acceptance-stack.ps1 {up|status|down} [-ComposeProject platform-acceptance]'
        Write-Host '       [-ApiPort 8082] [-PgPort 5433] [-ReasonerPort 7882] [-EmbeddingPort 8083]'
        Write-Host '       [-DataRoot D:/agentABC/data-acceptance] [-RemoveDataRoot]'
        exit 0
    }
}
