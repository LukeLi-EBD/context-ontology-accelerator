# Windows local runner for the migration idempotency gate.
#
# Same assertions as scripts/ci/migration-idempotency.sh (CI uses the POSIX
# script); this wrapper only starts the throwaway PostgreSQL and wires
# PYTHONPATH so a Windows interpreter can run the checker unchanged.
#
#   powershell -File scripts/ci/migration-idempotency.ps1 -Python D:\path\to\python.exe
#
# The container is removed on exit, pass or fail; no volume is mounted and the
# host port is random (never 5444/5944/8799/8099/8102).

param(
  [string]$Python = $env:PYTHON,
  [string]$Image = $(if ($env:MIGRATION_GATE_PG_IMAGE) { $env:MIGRATION_GATE_PG_IMAGE } else { "pgvector/pgvector:pg18-trixie" })
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

if (-not $Python) { $Python = "python" }
$blocked = @(5444, 5944, 8799, 8099, 8102)
do {
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
  $listener.Start()
  $port = $listener.LocalEndpoint.Port
  $listener.Stop()
} while ($blocked -contains $port)

$container = "p1-mig-gate-$PID"
try {
  Write-Host "migration-gate: starting $Image on 127.0.0.1:$port ($container)"
  docker run -d --rm --name $container `
    -e POSTGRES_USER=platform -e POSTGRES_PASSWORD=gate -e POSTGRES_DB=platform `
    -p "127.0.0.1:${port}:5432" $Image | Out-Null

  $ready = $false
  foreach ($i in 1..60) {
    docker exec $container pg_isready -U platform -d platform *> $null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 1
  }
  if (-not $ready) { throw "PostgreSQL did not become ready" }

  $env:MIGRATION_GATE_PG_DSN = "postgresql://platform:gate@127.0.0.1:$port/platform"
  $parts = @((Join-Path $root "packages\platform-core\src"))
  $parts += Get-ChildItem (Join-Path $root "packages") -Directory | ForEach-Object { Join-Path $_.FullName "src" }
  $parts += Get-ChildItem (Join-Path $root "libs") -Directory | ForEach-Object { Join-Path $_.FullName "src" }
  $parts += (Join-Path $root "smithy-generated\control-plane-python-server")
  $env:PYTHONPATH = ($parts | Where-Object { Test-Path $_ }) -join ";"

  Write-Host "migration-gate: apply twice and assert schema invariants"
  & $Python (Join-Path $root "scripts\ci\migration_idempotency_gate.py")
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host "migration-gate: pass; removing $container"
}
finally {
  docker rm -f $container *> $null
}
