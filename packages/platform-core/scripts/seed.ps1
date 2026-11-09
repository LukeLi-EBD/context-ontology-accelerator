# S7 demo seed: one sample ontology + two documents + indexing + extraction.
# Idempotent: identical ontology/document content is deduplicated by the platform.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/seed.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$base = 'http://127.0.0.1:8080'
try { Invoke-WebRequest "$base/healthz" -UseBasicParsing -TimeoutSec 3 | Out-Null }
catch {
    Write-Host '[seed] platform is down; running scripts/up.ps1 ...'
    & (Join-Path $PSScriptRoot 'up.ps1')
}

Write-Host '[seed] import sample ontology ...'
$importRaw = docker compose exec -T platform platform ontology import `
    --file /app/examples/ontology/sample.ttl --semver 1.0.0 --label 'coastal-sample'
if ($LASTEXITCODE -ne 0) { throw 'ontology import failed.' }
# The CLI emits structured log lines before a pretty JSON result; take the id.
$joined = ($importRaw -join "`n")
$match = [regex]::Match($joined, '"versionId"\s*:\s*"(ont-[^"]+)"')
$versionId = $match.Groups[1].Value
if (-not $versionId) { throw "import output has no versionId: $joined" }
docker compose exec -T platform platform ontology publish --version $versionId | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'ontology publish failed.' }
Write-Host "[seed] ontology published: $versionId"

# TEI loads 2.2 GB of BGE-M3 weights on first start (2-3 min). Indexing before
# that silently falls back to lexical, so wait explicitly rather than shipping a
# demo with zero vectors.
Write-Host '[seed] waiting for embedding (first model load can take ~3 min) ...'
$deadline = (Get-Date).AddSeconds(300)
$embeddingReady = $false
while ((Get-Date) -lt $deadline) {
    try {
        $overview = Invoke-RestMethod -Uri "$base/ui/api/overview" -TimeoutSec 5
        $service = $overview.services | Where-Object { $_.name -eq 'embedding' }
        if ($service -and $service.ok) { $embeddingReady = $true; break }
    }
    catch { }
    Start-Sleep -Seconds 3
}
if ($embeddingReady) {
    Write-Host '[seed] embedding ready.'
}
else {
    Write-Host '[seed] warning: embedding not ready; indexing falls back to lexical (degraded=true).'
}

foreach ($file in Get-ChildItem (Join-Path $root 'examples/documents') -Filter '*.txt') {
    Write-Host "[seed] upload $($file.Name) ..."
    $raw = & curl.exe -s -X POST -F "file=@$($file.FullName)" "$base/documents"
    $document = $raw | ConvertFrom-Json
    $documentId = $document.documentId
    if (-not $documentId) { throw "upload failed: $raw" }
    Write-Host "[seed]   documentId=$documentId"
    Invoke-RestMethod -Method Post -Uri "$base/documents/$documentId/index" | Out-Null
    Invoke-RestMethod -Method Post -Uri "$base/documents/$documentId/extract" `
        -ContentType 'application/json' -Body '{"mode":"auto"}' | Out-Null
    Write-Host '[seed]   indexed + extracted'
}

$overview = Invoke-RestMethod -Uri "$base/ui/api/overview"
$counts = $overview.counts
Write-Host ''
Write-Host ('[seed] done: documents={0} chunks={1} embeddings={2} pendingCandidates={3}' -f `
    $counts.documents, $counts.chunks, $counts.embeddings, $counts.candidatesPending)
Write-Host "[seed] open $base/ui/ ; use the approvals page to approve and materialize."
