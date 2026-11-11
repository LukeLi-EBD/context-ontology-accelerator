<#
.SYNOPSIS
  One-command pre-land (pre-merge) gate for the COA repo.

.DESCRIPTION
  Runs the checks below in order and prints PASS / FAIL / SKIP plus a reason and
  duration for every item, then a summary, an exit code, and a markdown record
  under doc/coa-x/evidence/pre-land-gate/.

  1. smithy       regenerate codegen in a throwaway directory and diff against
                  the committed smithy-generated/ tree (plus inputs fingerprint)
  2. infra-tsc    infra: tsc --noEmit
  3. web-tsc      web-app: tsc --noEmit
  4. web-build    web-app: pnpm --filter coa-web-app build
  5. infra-jest   the five infra jest suites (--coverage=false)
  6. canvas-pytest  packages/platform-core/tests/test_d1_canvas*.py
  7. migration    scripts/ci/migration-idempotency.ps1 (throwaway container,
                  random port; never touches a running stack)

  Exit codes: 0 = every enabled item passed, 1 = at least one FAIL,
              2 = usage error.

.PARAMETER Skip
  Items to skip. Comma separated, e.g. -Skip web-build,canvas-pytest.
  A per-item reason can be attached with '=', e.g.
  -Skip "web-build=only docs changed". Use -Skip all to run nothing.
  Valid ids: smithy, infra-tsc, web-tsc, web-build, infra-jest, canvas-pytest,
  migration. Skips are always explicit and are recorded in the evidence file.

.PARAMETER Python
  Python interpreter used by the canvas tests, the smithy spec post-processing
  and the migration gate. Resolution order: this parameter, $env:COA_GATE_PYTHON,
  <repo>\.venv\Scripts\python.exe, then 'python' on PATH.

.PARAMETER JavaHome
  JDK 17+ home for the Smithy Gradle build and openapi-generator. Resolution
  order: this parameter, $env:JAVA_HOME, java on PATH, common JDK install
  locations. Smithy Gradle does not run on Java 8.

.PARAMETER EvidenceDir
  Override the evidence directory (default:
  <repo>\doc\coa-x\evidence\pre-land-gate). Files are never overwritten.

.PARAMETER ListOnly
  Print the check ids and their state, then exit. Does not run anything.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ci/pre-land-gate.ps1

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ci/pre-land-gate.ps1 -Skip "web-build=docs only,p2" -Skip web-tsc
#>
[CmdletBinding()]
param(
    [string[]]$Skip = @(),
    [string]$Python,
    [string]$JavaHome,
    [string]$EvidenceDir,
    [switch]$ListOnly
)

$ErrorActionPreference = 'Stop'
$script:Version = '1.0.0'
$script:Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

$script:CheckOrder = @('smithy', 'infra-tsc', 'web-tsc', 'web-build', 'infra-jest', 'canvas-pytest', 'migration')
$script:CheckLabels = @{
    'smithy'        = 'smithy codegen consistency (clean regen in temp dir)'
    'infra-tsc'     = 'infra: tsc --noEmit'
    'web-tsc'       = 'web-app: tsc --noEmit'
    'web-build'     = 'web-app: pnpm build'
    'infra-jest'    = 'infra: five jest suites (--coverage=false)'
    'canvas-pytest' = 'platform-core: canvas pytest (two files)'
    'migration'     = 'migration idempotency (throwaway container, random port)'
}

$script:JestFiles = @(
    'test/app-connector-tag.test.ts',
    'test/extraction-config-defaults.test.ts',
    'test/model-id-defaults.test.ts',
    'test/preflight-arm64.test.ts',
    'test/solution.test.ts'
)

$script:CanvasTestFiles = @(
    'packages/platform-core/tests/test_d1_canvas.py',
    'packages/platform-core/tests/test_d1_canvas_full.py'
)

$script:GeneratedClients = @('control-plane-typescript-client', 'data-layer-typescript-client')

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

function Format-Seconds([double]$Seconds) {
    return ('{0,6:N1}s' -f $Seconds)
}

function New-Result {
    param(
        [string]$Status,
        [string]$Detail,
        [string]$Log,
        [string]$Excerpt
    )
    return [pscustomobject]@{ Status = $Status; Detail = $Detail; Log = $Log; Excerpt = $Excerpt }
}

function Get-Tail {
    param([string]$Path, [int]$Count = 25)
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return $null }
    $all = @(Get-Content -LiteralPath $Path)
    if ($all.Count -le $Count) { return ($all -join "`n") }
    return (($all | Select-Object -Last $Count) -join "`n")
}

function Remove-Ansi {
    param([string]$Text)
    return ($Text -replace "\x1b\[[0-9;]*[A-Za-z]", '')
}

function Invoke-Native {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory,
        [hashtable]$Environment,
        [string]$LogPath
    )

    $savedEnv = @{}
    if ($Environment) {
        foreach ($key in $Environment.Keys) {
            $savedEnv[$key] = [Environment]::GetEnvironmentVariable($key)
            [Environment]::SetEnvironmentVariable($key, [string]$Environment[$key])
        }
    }

    $previousLocation = Get-Location
    $previousErrorAction = $ErrorActionPreference
    $buffer = New-Object System.Collections.ArrayList
    $code = -1
    try {
        $ErrorActionPreference = 'Continue'
        if ($WorkingDirectory) { Set-Location -LiteralPath $WorkingDirectory }
        & $FilePath @ArgumentList 2>&1 | ForEach-Object {
            $line = if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { "$_" }
            [void]$buffer.Add($line)
            Write-Host $line
        }
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
    } finally {
        $ErrorActionPreference = $previousErrorAction
        Set-Location -LiteralPath $previousLocation
        foreach ($key in $savedEnv.Keys) {
            [Environment]::SetEnvironmentVariable($key, $savedEnv[$key])
        }
    }

    if ($LogPath) {
        Set-Content -LiteralPath $LogPath -Value ($buffer -join "`n") -Encoding UTF8
    }
    return [pscustomobject]@{ Code = $code; Lines = $buffer.ToArray(); LogPath = $LogPath }
}

function Get-JavaMajor {
    param([string]$JavaExe)
    if (-not (Test-Path -LiteralPath $JavaExe)) { return 0 }
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & $JavaExe -version 2>&1
    } finally {
        $ErrorActionPreference = $previous
    }
    $first = ($output | Select-Object -First 1)
    if ("$first" -match 'version "(\d+)') { return [int]$Matches[1] }
    return 0
}

function Resolve-JavaHome {
    param([string]$Explicit)
    $candidates = New-Object System.Collections.ArrayList
    if ($Explicit) { [void]$candidates.Add($Explicit) }
    if ($env:JAVA_HOME) { [void]$candidates.Add($env:JAVA_HOME) }
    $javaCmd = Get-Command java -ErrorAction SilentlyContinue
    if ($javaCmd) {
        $binDir = Split-Path -Parent $javaCmd.Source
        $jdkHome = Split-Path -Parent $binDir
        if ($jdkHome) { [void]$candidates.Add($jdkHome) }
    }
    $globs = @(
        (Join-Path $env:ProgramFiles 'Java\jdk*'),
        (Join-Path $env:ProgramFiles 'Eclipse Adoptium\jdk*'),
        (Join-Path $env:ProgramFiles 'Microsoft\jdk*'),
        (Join-Path $env:ProgramFiles 'Amazon Corretto\jdk*'),
        (Join-Path $env:ProgramFiles 'Zulu\zulu*'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Eclipse Adoptium\jdk*'),
        (Join-Path $env:USERPROFILE '.jdks\*'),
        (Join-Path $env:USERPROFILE '.local\share\mise\installs\java\*')
    )
    foreach ($glob in $globs) {
        Get-ChildItem -Path $glob -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            [void]$candidates.Add($_.FullName)
        }
    }
    foreach ($candidate in $candidates) {
        $exe = Join-Path $candidate 'bin\java.exe'
        if ((Get-JavaMajor -JavaExe $exe) -ge 17) { return $candidate }
    }
    return $null
}

function Resolve-Python {
    param([string]$Explicit)
    $candidates = New-Object System.Collections.ArrayList
    if ($Explicit) { [void]$candidates.Add($Explicit) }
    if ($env:COA_GATE_PYTHON) { [void]$candidates.Add($env:COA_GATE_PYTHON) }
    [void]$candidates.Add((Join-Path $script:Root '.venv\Scripts\python.exe'))
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { [void]$candidates.Add($pythonCmd.Source) }

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            $resolved = (Resolve-Path -LiteralPath $candidate).Path
            $script:ResolvedPython = $resolved
            return $resolved
        }
    }
    throw "no python interpreter found; run 'uv sync' in the repo root or pass -Python <path>"
}

function Resolve-Pnpm {
    $cmd = Get-Command pnpm.cmd -ErrorAction SilentlyContinue
    if (-not $cmd) { $cmd = Get-Command pnpm -ErrorAction SilentlyContinue }
    if (-not $cmd) { throw 'pnpm not found on PATH' }
    return $cmd.Source
}

function Assert-NodeModules {
    param([string]$RelativePath)
    $path = Join-Path $script:Root $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        throw "$RelativePath missing; run 'pnpm install --frozen-lockfile' in the repo root first"
    }
}

function Test-PythonDeps {
    param([string]$PythonExe)
    $probe = Invoke-Native -FilePath $PythonExe -ArgumentList @('-c', 'import pytest, psycopg, fastapi, yaml') -LogPath (Join-Path $script:RunTemp 'python-deps.log')
    if ($probe.Code -ne 0) {
        throw "python $PythonExe lacks test dependencies (pytest/psycopg/fastapi/yaml); create the venv with 'uv sync' or pass -Python"
    }
}

function Get-RepoPythonPath {
    $parts = New-Object System.Collections.ArrayList
    Get-ChildItem (Join-Path $script:Root 'packages') -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { [void]$parts.Add((Join-Path $_.FullName 'src')) }
    Get-ChildItem (Join-Path $script:Root 'libs') -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { [void]$parts.Add((Join-Path $_.FullName 'src')) }
    [void]$parts.Add((Join-Path $script:Root 'smithy-generated\control-plane-python-server'))
    [void]$parts.Add((Join-Path $script:Root 'smithy-generated\data-layer-python-server'))
    return (($parts | Where-Object { Test-Path -LiteralPath $_ }) -join ';')
}

function Get-InputsHash {
    param([string]$Root)
    $relativePaths = New-Object System.Collections.ArrayList
    Get-ChildItem (Join-Path $Root 'models\src') -Recurse -File | ForEach-Object {
        [void]$relativePaths.Add(($_.FullName.Substring($Root.Length + 1) -replace '\\', '/'))
    }
    foreach ($extra in 'models/build.gradle.kts', 'models/smithy-build.json', 'models/gradle/wrapper/gradle-wrapper.properties', 'scripts/smithy-generate.sh') {
        if (Test-Path -LiteralPath (Join-Path $Root $extra)) { [void]$relativePaths.Add($extra) }
    }
    $sorted = $relativePaths.ToArray()
    [Array]::Sort($sorted, [StringComparer]::Ordinal)

    $builder = New-Object System.Text.StringBuilder
    foreach ($relative in $sorted) {
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Root ($relative -replace '/', '\'))).Hash.ToLower()
        [void]$builder.Append($hash + ' ' + $relative + "`n")
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $digest = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($builder.ToString()))
    return (($digest | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Get-NormalizedText {
    param([string]$Path, [string]$RelativePath)
    $text = [IO.File]::ReadAllText($Path) -replace "`r`n", "`n"
    if ($RelativePath -like '*.ts') {
        # Smithy's TypeScript codegen emits Windows separators in module
        # specifiers on this platform; the committed artifacts use '/'.
        $text = [regex]::Replace($text, '(?<=from ")[^"]*(?=")', { param($m) $m.Value -replace '\\', '/' })
        if ((Split-Path -Leaf $RelativePath) -eq 'index.ts') {
            # Windows codegen also fails to relativize barrel specifiers.
            $text = [regex]::Replace($text, '(?<=from ")\./src/[^"/]+/', './')
        }
    }
    return $text
}

function Get-TrimmedText {
    param([string]$Text)
    return ((($Text -split "`n") | ForEach-Object { $_.TrimEnd() }) -join "`n")
}

function Get-DirtyPaths {
    $raw = & git -C $script:Root status --porcelain 2>$null
    if ($LASTEXITCODE -ne 0) { throw "git status failed in $($script:Root)" }
    # the evidence directory is this gate's own output; it must not count as a dirty tree
    return @($raw | Where-Object { "$_".Trim().Length -gt 0 -and "$_" -notmatch 'doc/coa-x/evidence/pre-land-gate/' })
}

function Ensure-GeneratedClientDists {
    param([string]$Pnpm)
    $built = @()
    foreach ($name in $script:GeneratedClients) {
        $types = Join-Path $script:Root "smithy-generated\$name\dist-types\index.d.ts"
        if (Test-Path -LiteralPath $types) { continue }
        Write-Host "  prep: building generated client $name (dist-types missing)"
        $result = Invoke-Native -FilePath $Pnpm -ArgumentList @('--filter', "./smithy-generated/$name", 'run', 'build') -WorkingDirectory $script:Root -LogPath (Join-Path $script:RunTemp "prep-$name.log")
        if ($result.Code -ne 0) {
            throw "failed to build generated client $name (needed by tsc); see $($result.LogPath)"
        }
        $built += $name
    }
    return $built
}

# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------

function Invoke-SmithyCheck {
    $log = Join-Path $script:RunTemp 'smithy.log'
    $dirty = & git -C $script:Root status --porcelain -- models/src smithy-generated 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'git status failed' }
    if (($dirty | Out-String).Trim().Length -gt 0) {
        return New-Result 'FAIL' 'models/src or smithy-generated/ has uncommitted changes; commit or stash them first' $null $null
    }

    $javaHome = Resolve-JavaHome -Explicit $JavaHome
    if (-not $javaHome) {
        throw 'no JDK 17+ found (Smithy Gradle does not run on Java 8); pass -JavaHome <jdk17+>'
    }
    $script:ResolvedJavaHome = $javaHome
    Write-Host "  java: $javaHome"

    $work = Join-Path $script:RunTemp 'smithy'
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    $tarPath = Join-Path $script:RunTemp 'src.tar'
    $archive = Invoke-Native -FilePath 'git' -ArgumentList @('-C', $script:Root, 'archive', '--format=tar', '-o', $tarPath, 'HEAD') -LogPath (Join-Path $script:RunTemp 'git-archive.log')
    if ($archive.Code -ne 0) { throw 'git archive HEAD failed' }
    $extract = Invoke-Native -FilePath 'tar' -ArgumentList @('-xf', $tarPath, '-C', $work) -LogPath (Join-Path $script:RunTemp 'tar.log')
    if ($extract.Code -ne 0) { throw 'tar extraction failed' }
    Remove-Item -LiteralPath (Join-Path $work 'smithy-generated') -Recurse -Force -ErrorAction SilentlyContinue

    $gradleLog = Join-Path $script:RunTemp 'smithy-gradle.log'
    Write-Host '  running gradle clean build (models/)'
    $gradle = Invoke-Native -FilePath (Join-Path $work 'models\gradlew.bat') -ArgumentList @('clean', 'build', '--console=plain') -WorkingDirectory (Join-Path $work 'models') -Environment @{ JAVA_HOME = $javaHome } -LogPath $gradleLog
    if ($gradle.Code -ne 0) {
        return New-Result 'FAIL' "gradle build failed (exit $($gradle.Code))" $gradleLog (Get-Tail $gradleLog 30)
    }

    $projection = Join-Path $work 'models\build\smithyprojections\models'
    $generated = Join-Path $work 'smithy-generated'
    New-Item -ItemType Directory -Path $generated -Force | Out-Null

    foreach ($pair in @(@('control-plane-ts', 'control-plane-typescript-client'), @('data-layer-ts', 'data-layer-typescript-client'))) {
        $source = Join-Path $projection ($pair[0] + '\typescript-client-codegen')
        if (-not (Test-Path -LiteralPath $source)) { throw "missing codegen output: $source" }
        Copy-Item -LiteralPath $source -Destination (Join-Path $generated $pair[1]) -Recurse -Force
        # match the pnpm-friendly build script that smithy-generate.sh writes in place
        $packageJson = Join-Path $generated ($pair[1] + '\package.json')
        $text = [IO.File]::ReadAllText($packageJson)
        $patched = [regex]::Replace($text, '"build": "concurrently[^"]*"', '"build": "pnpm run build:cjs && pnpm run build:es && pnpm run build:types"')
        [IO.File]::WriteAllText($packageJson, $patched)
    }

    New-Item -ItemType Directory -Path (Join-Path $generated 'openapi') -Force | Out-Null
    foreach ($name in 'openapi-control-plane', 'openapi-data-layer') {
        Copy-Item -Path (Join-Path $projection ($name + '\*')) -Destination (Join-Path $generated 'openapi') -Recurse -Force
    }

    $pythonExe = Resolve-Python -Explicit $Python
    $stripScript = Join-Path $script:RunTemp 'strip_password.py'
    $stripSource = @'
import json, sys, os

def strip(node):
    if isinstance(node, dict):
        if node.get("format") == "password":
            del node["format"]
        for value in node.values():
            strip(value)
    elif isinstance(node, list):
        for value in node:
            strip(value)

for spec in sys.argv[1:]:
    dst = os.path.join(os.path.dirname(os.path.dirname(spec)), "python-codegen", os.path.basename(spec))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(spec) as handle:
        data = json.load(handle)
    strip(data)
    with open(dst, "w") as handle:
        json.dump(data, handle, indent=4)
'@
    [IO.File]::WriteAllText($stripScript, $stripSource, (New-Object System.Text.UTF8Encoding($false)))

    $specControlPlane = Join-Path $generated 'openapi\openapi\ControlPlaneService.openapi.json'
    $specDataLayer = Join-Path $generated 'openapi\openapi\DataLayerService.openapi.json'
    $strip = Invoke-Native -FilePath $pythonExe -ArgumentList @($stripScript, $specControlPlane, $specDataLayer) -LogPath (Join-Path $script:RunTemp 'strip.log')
    if ($strip.Code -ne 0) { throw "failed to strip password formats from the OpenAPI specs; see $($strip.LogPath)" }

    $generatorJar = Resolve-OpenApiGenerator
    $javaExe = Join-Path $javaHome 'bin\java.exe'
    $generations = @(
        @('ControlPlaneService', 'control-plane-python-server', 'coa_control_plane_server'),
        @('DataLayerService', 'data-layer-python-server', 'coa_data_layer_server')
    )
    foreach ($generation in $generations) {
        $spec = Join-Path $generated ("openapi\python-codegen\" + $generation[0] + '.openapi.json')
        $output = Join-Path $generated $generation[1]
        $generatorLog = Join-Path $script:RunTemp ("generator-" + $generation[1] + '.log')
        $arguments = @('-jar', $generatorJar, 'generate', '-i', $spec, '-g', 'python', '-o', $output,
            '--package-name', $generation[2], '--global-property', 'models,supportingFiles=__init__.py',
            '--additional-properties', 'generateSourceCodeOnly=true')
        $run = Invoke-Native -FilePath $javaExe -ArgumentList $arguments -LogPath $generatorLog
        if ($run.Code -ne 0) {
            return New-Result 'FAIL' "openapi-generator failed for $($generation[0]) (exit $($run.Code))" $generatorLog (Get-Tail $generatorLog 30)
        }
        Write-CodegenPostProcessing -PackageDir (Join-Path $output $generation[2]) -PackageName $generation[2]
        $projectName = $generation[2].Replace('_', '-')
        $pyproject = @'
[project]
name = "__NAME__"
version = "0.0.1"
description = "__DESCRIPTION__"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["__PACKAGE__"]
'@
        $title = if ($generation[0] -eq 'ControlPlaneService') { 'Control Plane' } else { 'Data Layer' }
        $pyproject = $pyproject.Replace('__NAME__', $projectName).Replace('__DESCRIPTION__', $title + ' server models (generated from OpenAPI)').Replace('__PACKAGE__', $generation[2])
        $pyproject = ($pyproject -replace "`r`n", "`n").TrimEnd() + "`n"
        [IO.File]::WriteAllText((Join-Path $output 'pyproject.toml'), $pyproject)
    }

    $inputsHash = Get-InputsHash -Root $work
    [IO.File]::WriteAllText((Join-Path $generated '.inputs.sha256'), $inputsHash + "`n")

    return Compare-SmithyOutput -Regenerated $generated -InputsHash $inputsHash -LogPath $log
}

function Write-CodegenPostProcessing {
    param([string]$PackageDir, [string]$PackageName)
    $initPath = Join-Path $PackageDir '__init__.py'
    $header = '# Auto-generated ' + [char]0x2014 + ' models only (see smithy-generate.sh)'
    $imports = @(Get-Content -LiteralPath $initPath | Where-Object { $_ -match ('^from ' + [regex]::Escape($PackageName) + '\.models\.') })
    $content = $header + "`n" + (($imports -join "`n") + "`n")
    [IO.File]::WriteAllText($initPath, $content)
}

function Resolve-OpenApiGenerator {
    $generatorHome = $env:OPENAPI_GENERATOR_HOME
    if (-not $generatorHome) { $generatorHome = Join-Path $env:USERPROFILE '.local\share\openapi-generator' }
    $jar = Join-Path $generatorHome 'openapi-generator-cli-7.12.0.jar'
    if (Test-Path -LiteralPath $jar) { return $jar }

    Write-Host "  openapi-generator jar not found, downloading to $jar"
    New-Item -ItemType Directory -Path $generatorHome -Force | Out-Null
    $url = 'https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.12.0/openapi-generator-cli-7.12.0.jar'
    try {
        Invoke-WebRequest -Uri $url -OutFile $jar -UseBasicParsing
    } catch {
        throw "openapi-generator jar is missing and could not be downloaded ($url); install it under $generatorHome"
    }
    return $jar
}

function Compare-SmithyOutput {
    param([string]$Regenerated, [string]$InputsHash, [string]$LogPath)

    $tracked = @(& git -C $script:Root ls-files -- smithy-generated)
    $tracked = @($tracked | Where-Object { $_ -and $_ -ne 'smithy-generated/.inputs.sha256' -and $_ -notmatch '/build-info/' })

    $prefix = 'smithy-generated/'
    $identical = 0
    $normalized = 0
    $diffs = New-Object System.Collections.ArrayList
    $missing = New-Object System.Collections.ArrayList

    foreach ($relative in $tracked) {
        $committed = Join-Path $script:Root ($relative -replace '/', '\')
        $fresh = Join-Path $Regenerated ($relative.Substring($prefix.Length) -replace '/', '\')
        if (-not (Test-Path -LiteralPath $fresh)) { [void]$missing.Add($relative); continue }
        $a = Get-NormalizedText -Path $committed -RelativePath $relative
        $b = Get-NormalizedText -Path $fresh -RelativePath $relative
        if ($a -ceq $b) { $identical++; continue }
        if ((Get-TrimmedText $a) -ceq (Get-TrimmedText $b)) { $normalized++; continue }
        [void]$diffs.Add($relative)
    }

    $trackedSet = @($tracked | ForEach-Object { $_.Substring($prefix.Length) -replace '/', '\' })
    $extra = New-Object System.Collections.ArrayList
    foreach ($file in Get-ChildItem -LiteralPath $Regenerated -Recurse -File) {
        $relative = $file.FullName.Substring($Regenerated.Length + 1)
        if ($relative -eq '.inputs.sha256') { continue }
        if ($relative -match '\\build-info\\') { continue }
        if ($relative -match '^\.openapi-generator\\') { continue }
        if ($trackedSet -notcontains $relative) { [void]$extra.Add($relative) }
    }

    $stampPath = Join-Path $script:Root 'smithy-generated\.inputs.sha256'
    $stamp = if (Test-Path -LiteralPath $stampPath) { (Get-Content -LiteralPath $stampPath -Raw).Trim() } else { '' }
    $stampFresh = ($stamp -eq $InputsHash)

    $report = New-Object System.Collections.ArrayList
    [void]$report.Add("tracked artifacts: $($tracked.Count)")
    [void]$report.Add("byte-identical: $identical")
    [void]$report.Add("identical after EOL / Windows path normalization: $normalized")
    [void]$report.Add("real diffs: $($diffs.Count)")
    [void]$report.Add("missing in regeneration: $($missing.Count)")
    [void]$report.Add("untracked output: $($extra.Count)")
    [void]$report.Add("inputs fingerprint current: $stampFresh")
    [void]$report.Add("inputs fingerprint: $InputsHash")
    foreach ($item in $diffs) { [void]$report.Add("DIFF $item") }
    foreach ($item in $missing) { [void]$report.Add("MISSING $item") }
    foreach ($item in $extra) { [void]$report.Add("EXTRA $item") }
    Set-Content -LiteralPath $LogPath -Value ($report -join "`n") -Encoding UTF8

    if ($diffs.Count -gt 0 -or $missing.Count -gt 0 -or -not $stampFresh) {
        $excerpt = ($report | Select-Object -Last 25) -join "`n"
        return New-Result 'FAIL' "$($diffs.Count) tracked artifacts differ after regeneration, $($missing.Count) missing, fingerprint current: $stampFresh" $LogPath $excerpt
    }
    if ($extra.Count -gt 0) {
        $excerpt = ($report | Where-Object { $_ -like 'EXTRA *' } | Select-Object -First 25) -join "`n"
        return New-Result 'FAIL' "$($extra.Count) generated files are not committed under smithy-generated/" $LogPath $excerpt
    }

    $detail = "$identical identical, $normalized after EOL/Windows-path normalization, fingerprint current"
    return New-Result 'PASS' $detail $LogPath $null
}

function Invoke-InfraTscCheck {
    Assert-NodeModules 'infra\node_modules'
    $pnpm = Resolve-Pnpm
    $log = Join-Path $script:RunTemp 'infra-tsc.log'
    $run = Invoke-Native -FilePath $pnpm -ArgumentList @('exec', 'tsc', '--noEmit') -WorkingDirectory (Join-Path $script:Root 'infra') -LogPath $log
    if ($run.Code -ne 0) {
        return New-Result 'FAIL' "tsc --noEmit failed (exit $($run.Code))" $log (Get-Tail $log 30)
    }
    return New-Result 'PASS' 'no type errors' $log $null
}

function Invoke-WebTscCheck {
    Assert-NodeModules 'packages\web-app\node_modules'
    $pnpm = Resolve-Pnpm
    $built = Ensure-GeneratedClientDists -Pnpm $pnpm
    $log = Join-Path $script:RunTemp 'web-tsc.log'
    $run = Invoke-Native -FilePath $pnpm -ArgumentList @('--filter', 'coa-web-app', 'exec', 'tsc', '--noEmit') -WorkingDirectory $script:Root -LogPath $log
    if ($run.Code -ne 0) {
        return New-Result 'FAIL' "tsc --noEmit failed (exit $($run.Code))" $log (Get-Tail $log 30)
    }
    $detail = 'no type errors'
    if ($built.Count -gt 0) { $detail += " (built generated client dist: $($built -join ', '))" }
    return New-Result 'PASS' $detail $log $null
}

function Invoke-WebBuildCheck {
    Assert-NodeModules 'packages\web-app\node_modules'
    $pnpm = Resolve-Pnpm
    [void](Ensure-GeneratedClientDists -Pnpm $pnpm)
    $log = Join-Path $script:RunTemp 'web-build.log'
    $run = Invoke-Native -FilePath $pnpm -ArgumentList @('--filter', 'coa-web-app', 'build') -WorkingDirectory $script:Root -LogPath $log
    if ($run.Code -ne 0) {
        return New-Result 'FAIL' "web-app build failed (exit $($run.Code))" $log (Get-Tail $log 30)
    }
    $built = @(Get-Content -LiteralPath $log | Where-Object { $_ -match 'built in' }) | Select-Object -Last 1
    $detail = if ($built) { (Remove-Ansi $built).Trim() } else { 'build succeeded' }
    return New-Result 'PASS' $detail $log $null
}

function Invoke-InfraJestCheck {
    Assert-NodeModules 'infra\node_modules'
    $pnpm = Resolve-Pnpm
    $log = Join-Path $script:RunTemp 'infra-jest.log'
    $arguments = @('exec', 'jest') + $script:JestFiles + @('--coverage=false', '--maxWorkers=2')
    $run = Invoke-Native -FilePath $pnpm -ArgumentList $arguments -WorkingDirectory (Join-Path $script:Root 'infra') -LogPath $log
    if ($run.Code -ne 0) {
        return New-Result 'FAIL' "jest failed (exit $($run.Code))" $log (Get-Tail $log 30)
    }
    $text = ($run.Lines -join "`n")
    $suites = if ($text -match 'Test Suites:\s*(.+)') { $Matches[1].Trim() } else { '5 suites' }
    $tests = if ($text -match 'Tests:\s*(.+)') { $Matches[1].Trim() } else { 'ok' }
    return New-Result 'PASS' "$suites / tests: $tests" $log $null
}

function Invoke-CanvasPytestCheck {
    $pythonExe = Resolve-Python -Explicit $Python
    Test-PythonDeps -PythonExe $pythonExe
    $log = Join-Path $script:RunTemp 'canvas-pytest.log'
    $environment = @{ PYTHONPATH = (Get-RepoPythonPath) }
    $arguments = @('-m', 'pytest') + $script:CanvasTestFiles + @('-q')
    $run = Invoke-Native -FilePath $pythonExe -ArgumentList $arguments -WorkingDirectory $script:Root -Environment $environment -LogPath $log
    if ($run.Code -ne 0) {
        return New-Result 'FAIL' "pytest failed (exit $($run.Code))" $log (Get-Tail $log 30)
    }
    $text = ($run.Lines -join "`n")
    $summary = if ($text -match '(\d+ passed[^=]*)') { $Matches[1].Trim() } else { 'passed' }
    return New-Result 'PASS' "$summary" $log $null
}

function Invoke-MigrationCheck {
    $pythonExe = Resolve-Python -Explicit $Python
    Test-PythonDeps -PythonExe $pythonExe
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) { throw 'docker not found on PATH; the migration gate needs a throwaway postgres container' }
    $probe = Invoke-Native -FilePath $docker.Source -ArgumentList @('version', '--format', '{{.Server.Version}}') -LogPath (Join-Path $script:RunTemp 'docker-version.log')
    if ($probe.Code -ne 0) { throw 'docker daemon is not reachable; start Docker Desktop first' }

    $scriptPath = Join-Path $script:Root 'scripts\ci\migration-idempotency.ps1'
    if (-not (Test-Path -LiteralPath $scriptPath)) { throw "missing $scriptPath" }
    $log = Join-Path $script:RunTemp 'migration.log'
    $shell = (Get-Command powershell).Source
    $run = Invoke-Native -FilePath $shell -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $scriptPath, '-Python', $pythonExe) -WorkingDirectory $script:Root -LogPath $log
    if ($run.Code -ne 0) {
        return New-Result 'FAIL' "migration idempotency failed (exit $($run.Code))" $log (Get-Tail $log 30)
    }
    $text = ($run.Lines -join "`n")
    $summary = if ($text -match 'RESULT:\s*(.+)') { $Matches[1].Trim() } else { 'idempotent' }
    return New-Result 'PASS' $summary $log $null
}

# ---------------------------------------------------------------------------
# evidence
# ---------------------------------------------------------------------------

function Write-Evidence {
    param(
        [System.Collections.ArrayList]$Results,
        [hashtable]$Skipped,
        [string]$Overall,
        [int]$ExitCode,
        [double]$TotalSeconds,
        [string]$Directory,
        [string]$Commit,
        [string]$Branch,
        [string[]]$DirtyPaths
    )

    if (-not (Test-Path -LiteralPath $Directory)) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }

    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $fileName = "pre-land-gate-$stamp.md"
    $path = Join-Path $Directory $fileName
    $suffix = 2
    while (Test-Path -LiteralPath $path) {
        $path = Join-Path $Directory ("pre-land-gate-$stamp-$suffix.md")
        $suffix++
    }

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add('# Pre-land gate run')
    [void]$lines.Add('')
    [void]$lines.Add("- Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')")
    [void]$lines.Add("- Machine: $env:COMPUTERNAME")
    [void]$lines.Add("- OS: $([Environment]::OSVersion.VersionString)")
    [void]$lines.Add("- Repo: $script:Root")
    [void]$lines.Add("- Branch: $Branch")
    [void]$lines.Add("- Commit: $Commit")
    [void]$lines.Add("- Script: scripts/ci/pre-land-gate.ps1 v$script:Version")
    [void]$lines.Add("- Result: $Overall (exit $ExitCode)")
    [void]$lines.Add("- Total time: $((Format-Seconds $TotalSeconds).Trim())")
    [void]$lines.Add("- Python: $(if ($script:ResolvedPython) { $script:ResolvedPython } else { 'not resolved' })")
    [void]$lines.Add("- JavaHome: $(if ($script:ResolvedJavaHome) { $script:ResolvedJavaHome } else { 'not resolved' })")
    if ($DirtyPaths.Count -gt 0) {
        [void]$lines.Add("- Working tree: dirty ($($DirtyPaths.Count) paths). The smithy check signs off HEAD, not these edits.")
        foreach ($item in ($DirtyPaths | Select-Object -First 10)) { [void]$lines.Add("  - $item") }
        if ($DirtyPaths.Count -gt 10) { [void]$lines.Add('  - ...') }
    } else {
        [void]$lines.Add('- Working tree: clean')
    }
    [void]$lines.Add('')
    [void]$lines.Add('## Checks')
    [void]$lines.Add('')
    [void]$lines.Add('| # | Check | Result | Detail | Time |')
    [void]$lines.Add('|---|-------|--------|--------|------|')
    $index = 1
    foreach ($result in $Results) {
        $detail = $result.Detail -replace '\|', '\|'
        [void]$lines.Add("| $index | $($result.Id) | $($result.Status) | $detail | $((Format-Seconds $result.Seconds).Trim()) |")
        $index++
    }
    [void]$lines.Add('')
    [void]$lines.Add('## Skipped')
    [void]$lines.Add('')
    if ($Skipped.Count -eq 0) {
        [void]$lines.Add('none')
    } else {
        foreach ($key in $script:CheckOrder) {
            if ($Skipped.ContainsKey($key)) { [void]$lines.Add("- $key : $($Skipped[$key])") }
        }
    }

    $failures = @($Results | Where-Object { $_.Status -eq 'FAIL' -and $_.Excerpt })
    [void]$lines.Add('')
    [void]$lines.Add('## Failure output')
    [void]$lines.Add('')
    if ($failures.Count -eq 0) {
        [void]$lines.Add('none')
    } else {
        foreach ($failure in $failures) {
            [void]$lines.Add("### $($failure.Id)")
            [void]$lines.Add('')
            [void]$lines.Add('```')
            [void]$lines.Add($failure.Excerpt.TrimEnd())
            [void]$lines.Add('```')
            [void]$lines.Add('')
        }
    }

    [void]$lines.Add('')
    [void]$lines.Add('## How to reproduce')
    [void]$lines.Add('')
    [void]$lines.Add('```')
    $reproduce = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $script:Root 'scripts\ci\pre-land-gate.ps1') + '"'
    if ($Skipped.Count -gt 0) {
        $pairs = @()
        foreach ($key in $script:CheckOrder) {
            if ($Skipped.ContainsKey($key)) { $pairs += "$key=$($Skipped[$key])" }
        }
        $reproduce += ' -Skip "' + ($pairs -join ',') + '"'
    }
    [void]$lines.Add($reproduce)
    [void]$lines.Add('```')

    [IO.File]::WriteAllText($path, (($lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))
    return $path
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

if ($ListOnly) {
    foreach ($id in $script:CheckOrder) {
        Write-Output ("{0,-14} {1}" -f $id, $script:CheckLabels[$id])
    }
    exit 0
}

$script:SkipMap = @{}
foreach ($entry in $Skip) {
    if ([string]::IsNullOrWhiteSpace($entry)) { continue }
    # when invoked via 'powershell -File', a comma separated list arrives as one string
    foreach ($id in ($entry -split ',')) {
        if ([string]::IsNullOrWhiteSpace($id)) { continue }
        $name = $id.Trim()
        $reason = 'explicitly skipped by -Skip'
        if ($name.Contains('=')) {
            $reason = $name.Substring($name.IndexOf('=') + 1).Trim()
            $name = $name.Substring(0, $name.IndexOf('=')).Trim()
        }
        if ($name -eq 'all') {
            foreach ($check in $script:CheckOrder) { $script:SkipMap[$check] = $reason }
            continue
        }
        if ($script:CheckOrder -notcontains $name) {
            Write-Host "unknown check id '$name' in -Skip. Valid ids: $($script:CheckOrder -join ', '), all" -ForegroundColor Red
            exit 2
        }
        $script:SkipMap[$name] = $reason
    }
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$script:RunTemp = Join-Path $env:TEMP "coa-pre-land-gate-$stamp-$PID"
New-Item -ItemType Directory -Path $script:RunTemp -Force | Out-Null

$branch = (& git -C $script:Root rev-parse --abbrev-ref HEAD).Trim()
$commit = (& git -C $script:Root rev-parse HEAD).Trim()
$dirtyPaths = @(Get-DirtyPaths)

Write-Host ''
Write-Host "pre-land gate v$script:Version"
Write-Host "repo:   $script:Root"
Write-Host "branch: $branch @ $commit"
if ($dirtyPaths.Count -gt 0) {
    Write-Host "warning: working tree has $($dirtyPaths.Count) uncommitted path(s); smithy signs off HEAD" -ForegroundColor Yellow
}
Write-Host ''

$results = New-Object System.Collections.ArrayList
$totalWatch = [Diagnostics.Stopwatch]::StartNew()

foreach ($id in $script:CheckOrder) {
    $label = $script:CheckLabels[$id]
    if ($script:SkipMap.ContainsKey($id)) {
        $result = [pscustomobject]@{
            Id      = $id
            Label   = $label
            Status  = 'SKIP'
            Detail  = $script:SkipMap[$id]
            Seconds = 0.0
            Log     = $null
            Excerpt = $null
        }
        [void]$results.Add($result)
        Write-Host ("[SKIP] {0}  ({1})" -f $label, $result.Detail) -ForegroundColor Yellow
        continue
    }

    Write-Host ("[RUN ] {0}" -f $label) -ForegroundColor Cyan
    $watch = [Diagnostics.Stopwatch]::StartNew()
    try {
        switch ($id) {
            'smithy' { $result = Invoke-SmithyCheck }
            'infra-tsc' { $result = Invoke-InfraTscCheck }
            'web-tsc' { $result = Invoke-WebTscCheck }
            'web-build' { $result = Invoke-WebBuildCheck }
            'infra-jest' { $result = Invoke-InfraJestCheck }
            'canvas-pytest' { $result = Invoke-CanvasPytestCheck }
            'migration' { $result = Invoke-MigrationCheck }
        }
    } catch {
        $result = New-Result 'FAIL' $_.Exception.Message $null $null
    }
    $watch.Stop()

    $entry = [pscustomobject]@{
        Id      = $id
        Label   = $label
        Status  = $result.Status
        Detail  = $result.Detail
        Seconds = [math]::Round($watch.Elapsed.TotalSeconds, 1)
        Log     = $result.Log
        Excerpt = $result.Excerpt
    }
    [void]$results.Add($entry)

    $color = if ($entry.Status -eq 'PASS') { 'Green' } elseif ($entry.Status -eq 'FAIL') { 'Red' } else { 'Yellow' }
    Write-Host ("[{0}] {1}  {2}  {3}" -f $entry.Status, $label, (Format-Seconds $entry.Seconds).Trim(), $entry.Detail) -ForegroundColor $color
    Write-Host ''
}

$totalWatch.Stop()
$totalSeconds = [math]::Round($totalWatch.Elapsed.TotalSeconds, 1)

$failed = @($results | Where-Object { $_.Status -eq 'FAIL' })
$passed = @($results | Where-Object { $_.Status -eq 'PASS' })
$skipped = @($results | Where-Object { $_.Status -eq 'SKIP' })
$overall = if ($failed.Count -gt 0) { 'FAIL' } else { 'PASS' }
$exitCode = if ($failed.Count -gt 0) { 1 } else { 0 }

$evidencePath = $null
$evidenceError = $null
try {
    $evidenceDir = if ($EvidenceDir) { $EvidenceDir } else { Join-Path $script:Root 'doc\coa-x\evidence\pre-land-gate' }
    $evidencePath = Write-Evidence -Results $results -Skipped $script:SkipMap -Overall $overall -ExitCode $exitCode -TotalSeconds $totalSeconds -Directory $evidenceDir -Commit $commit -Branch $branch -DirtyPaths $dirtyPaths
} catch {
    $evidenceError = $_.Exception.Message
    $exitCode = 1
}

Write-Host '================ PRE-LAND GATE SUMMARY ================'
foreach ($result in $results) {
    $statusColor = if ($result.Status -eq 'PASS') { 'Green' } elseif ($result.Status -eq 'FAIL') { 'Red' } else { 'Yellow' }
    Write-Host ("{0,-4} {1,-14} {2,7}  {3}" -f $result.Status, $result.Id, (Format-Seconds $result.Seconds).Trim(), $result.Detail) -ForegroundColor $statusColor
}
Write-Host ''
Write-Host ("overall: {0}  passed: {1}  failed: {2}  skipped: {3}  total: {4}s" -f $overall, $passed.Count, $failed.Count, $skipped.Count, $totalSeconds)
if ($evidencePath) { Write-Host "evidence: $evidencePath" }
if ($evidenceError) { Write-Host "evidence write failed: $evidenceError" -ForegroundColor Red }
Write-Host ''

Remove-Item -LiteralPath $script:RunTemp -Recurse -Force -ErrorAction SilentlyContinue

if ($failed.Count -gt 0) {
    Write-Host 'At least one check failed. Fix it or skip it explicitly with -Skip "<id>=<reason>".' -ForegroundColor Red
}
exit $exitCode
