param(
    [int]$Repetitions = 10,
    [int]$PressureIterations = 200,
    [string]$ExperimentName = "benchmark"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WorkspaceRoot = Resolve-Path (Join-Path $RepoRoot "..")
$Python = Join-Path $WorkspaceRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Root venv not found: $Python"
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SafeName = $ExperimentName -replace "[^A-Za-z0-9_-]", "_"
$OutputDir = Join-Path $RepoRoot "results\$SafeName`_$Timestamp"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Push-Location $WorkspaceRoot
try {
    $json = & $Python -c "import json; from pathlib import Path; from agentguard.backend.app.demo.benchmark import run_full_benchmark; result=run_full_benchmark(Path.cwd(), repetitions=$Repetitions, pressure_iterations=$PressureIterations); print(json.dumps(result, ensure_ascii=False, indent=2))"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $json | Out-File -FilePath (Join-Path $OutputDir "benchmark.json") -Encoding utf8
} finally {
    Pop-Location
}

Write-Host "Saved benchmark result to $OutputDir"
