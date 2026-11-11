<#
.SYNOPSIS
  P1 导入 run 回归门禁。

.DESCRIPTION
  packages/platform-core/tests/test_importer_runs.py 用 skipUnless(TEST_PG_DSN)
  保护：缺变量时整组 6 条会被 skip，pytest 仍返回 0，等于一个静默的「绿」。
  本脚本不修改测试里的 skipUnless（其他机器没有 PG 时不会炸），而是在门禁层
  显式传 TEST_PG_DSN，并把「N skipped，回归未生效」打到输出里、以退出码 2
  结束，使这种结果不可能被当成通过。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File doc\coa-x\tools\run-p1-gate.ps1
  powershell -ExecutionPolicy Bypass -File doc\coa-x\tools\run-p1-gate.ps1 -Dsn "postgresql://platform:platform_dev@127.0.0.1:5444/platform"
#>
param(
    [string]$Python = "python",
    [string]$Dsn = $env:TEST_PG_DSN,
    [int]$ExpectedPassed = 6
)

# pytest 把告警写到 stderr；Stop 会把 stderr 当成异常抛出，这里靠退出码判断。
$ErrorActionPreference = "Continue"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$testFile = "packages/platform-core/tests/test_importer_runs.py"

Push-Location $repo
try {
    $paths = @()
    $paths += Get-ChildItem "packages" -Directory |
        ForEach-Object { Join-Path $_.FullName "src" } |
        Where-Object { Test-Path $_ }
    $paths += Get-ChildItem "libs" -Directory |
        ForEach-Object { Join-Path $_.FullName "src" } |
        Where-Object { Test-Path $_ }
    $paths += Join-Path $repo "packages/platform-core/tests"
    $paths += Join-Path $repo "smithy-generated/control-plane-python-server"
    $env:PYTHONPATH = ($paths -join ";")

    if ($Dsn) {
        $env:TEST_PG_DSN = $Dsn
    }
    else {
        Remove-Item Env:TEST_PG_DSN -ErrorAction SilentlyContinue
    }

    $output = & $Python -m pytest $testFile -q -rs --import-mode=importlib -p no:cacheprovider 2>&1
    $pytestExit = $LASTEXITCODE
    $output | ForEach-Object { Write-Host $_ }

    $text = ($output | Out-String)
    $passed = 0
    $skipped = 0
    $failed = 0
    if ($text -match "(\d+) passed") { $passed = [int]$Matches[1] }
    if ($text -match "(\d+) skipped") { $skipped = [int]$Matches[1] }
    if ($text -match "(\d+) failed") { $failed = [int]$Matches[1] }

    Write-Host ""

    if ($skipped -gt 0 -or -not $Dsn) {
        $why = "TEST_PG_DSN 未设置"
        if ($Dsn) { $why = "TEST_PG_DSN 已设置但仍有 skip，检查连接与权限" }
        Write-Host "[gate] $skipped skipped，回归未生效（$why；本次结果不计为通过）" -ForegroundColor Red
        exit 2
    }

    if ($failed -gt 0 -or $passed -ne $ExpectedPassed -or $pytestExit -ne 0) {
        Write-Host "[gate] $passed passed / $failed failed（期望 $ExpectedPassed passed）—— 不合格" -ForegroundColor Red
        exit 1
    }

    Write-Host "[gate] $passed passed，回归生效（TEST_PG_DSN 已设置）" -ForegroundColor Green
    exit 0
}
finally {
    Pop-Location
}
