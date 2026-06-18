param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WorkspaceRoot = Resolve-Path (Join-Path $RepoRoot "..")
$Python = Join-Path $WorkspaceRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Root venv not found: $Python"
}
Set-Location $RepoRoot

Write-Host "[AgentGuard] Backend tests"
& $Python -m pytest backend\tests -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[AgentGuard] Backend compile check"
Push-Location ..
& $Python -m compileall agentguard\backend
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Pop-Location

Write-Host "[AgentGuard] Baseline evaluation"
Push-Location ..
& $Python -m agentguard.backend.app.demo.baseline_eval | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Pop-Location

Write-Host "[AgentGuard] Benchmark and pressure test"
& (Join-Path $PSScriptRoot "verify-benchmark.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $SkipFrontend) {
    Write-Host "[AgentGuard] Frontend build"
    Push-Location frontend
    if (-not (Test-Path "node_modules")) {
        npm.cmd install
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Pop-Location
}

Write-Host "[AgentGuard] Verification complete"
