param(
    [switch]$RunContainers
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

docker info | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Docker daemon is not reachable. Start Docker Desktop, then rerun .\scripts\verify-docker.ps1 -RunContainers"
}

Write-Host "[AgentGuard] Docker compose config"
docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[AgentGuard] Docker compose build"
docker compose build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($RunContainers) {
    Write-Host "[AgentGuard] Docker compose up"
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    try {
        $ok = $false
        for ($i = 0; $i -lt 30; $i++) {
            try {
                $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
                if ($health.status -eq "ok") {
                    $ok = $true
                    break
                }
            } catch {
                Start-Sleep -Seconds 2
            }
        }
        if (-not $ok) {
            throw "Docker API health check did not pass"
        }
    } finally {
        docker compose down
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

Write-Host "[AgentGuard] Docker verification complete"
