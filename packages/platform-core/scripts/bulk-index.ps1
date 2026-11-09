param(
    [string]$Filter = "d.filename not like 's2-%' and d.filename not like 's4-%' and d.filename not like 'bulk-%' and d.filename not like 's14h04-%' and d.filename not like 'bench-%' and d.filename not like 'smoke-%'"
)
# S14H-FULL: per-document /index loop. Safe to stop and re-run: the pending set
# is recomputed from chunk_embedding, so already-embedded chunks are skipped.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$log = Join-Path $root 'logs\bulk-index.jsonl'
$base = 'http://127.0.0.1:8080'

$sql = "select d.document_id, d.filename, d.chunk_count from platform.document d where d.chunk_count>0 and coalesce((select count(*) from platform.chunk_embedding e join platform.document_chunk c on c.chunk_id=e.chunk_id where c.document_id=d.document_id and e.model=(select model from platform.embedding_pointer) and e.dimensions=(select dimensions from platform.embedding_pointer)),0) < d.chunk_count and $Filter order by d.chunk_count asc"

$rows = docker compose -f (Join-Path $root 'docker-compose.yml') exec -T postgres psql -U platform -d platform -t -A -c $sql
if (-not $rows) { Write-Host '[bulk] no pending documents'; exit 0 }

foreach ($row in $rows) {
    if (-not $row) { continue }
    $parts = $row.Split('|')
    $id = $parts[0]; $name = $parts[1]; $chunks = [int]$parts[2]
    $sw = [Diagnostics.Stopwatch]::StartNew()
    try {
        $r = Invoke-RestMethod -Method Post -Uri "$base/documents/$id/index" -TimeoutSec 7200
    } catch {
        $r = [pscustomobject]@{ documentId = $id; chunks = $chunks; embedded = 0; remaining = $chunks; degraded = $true; failureCode = "$($_.Exception.Message)" }
    }
    $sw.Stop()
    $wall = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    $rate = [math]::Round([double]$r.embedded / [math]::Max($sw.Elapsed.TotalSeconds, 0.001), 3)
    [pscustomobject]@{
        time = (Get-Date -Format 'o'); filename = $name; documentId = $id
        chunks = $r.chunks; embedded = $r.embedded; remaining = $r.remaining
        degraded = $r.degraded; failureCode = $r.failureCode; wallS = $wall; chunkPerS = $rate
    } | ConvertTo-Json -Compress | Add-Content -LiteralPath $log -Encoding utf8
    Write-Host "[bulk] $name chunks=$($r.chunks) embedded=$($r.embedded) remaining=$($r.remaining) degraded=$($r.degraded) wall=${wall}s rate=$rate"
}
Write-Host '[bulk] done'
