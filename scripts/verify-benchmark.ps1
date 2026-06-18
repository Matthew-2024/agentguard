param(
    [int]$Repetitions = 10,
    [int]$PressureIterations = 200
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WorkspaceRoot = Resolve-Path (Join-Path $RepoRoot "..")
$Python = Join-Path $WorkspaceRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Root venv not found: $Python"
}
if ($Repetitions -lt 10) {
    throw "Repetitions must be at least 10 for the benchmark threshold gate"
}
if ($PressureIterations -lt 200) {
    throw "PressureIterations must be at least 200 for the benchmark threshold gate"
}

$TempRoot = Join-Path $RepoRoot "tmp-runtime"
$RunId = "$(Get-Date -Format "yyyyMMdd_HHmmss")_$([guid]::NewGuid().ToString('N').Substring(0, 8))"
$OutputDir = Join-Path $TempRoot "benchmark_verify_$RunId"
$ResolvedTempRoot = (New-Item -ItemType Directory -Force -Path $TempRoot).FullName
$ResolvedOutputDir = (New-Item -ItemType Directory -Force -Path $OutputDir).FullName
if (-not ($ResolvedOutputDir.StartsWith($ResolvedTempRoot, [System.StringComparison]::OrdinalIgnoreCase))) {
    throw "Refusing to use benchmark output directory outside tmp-runtime: $ResolvedOutputDir"
}

try {
    Push-Location $WorkspaceRoot
    try {
        $benchmarkJson = & $Python -c "import json; from pathlib import Path; from agentguard.backend.app.demo.benchmark import run_full_benchmark; result=run_full_benchmark(Path.cwd(), repetitions=$Repetitions, pressure_iterations=$PressureIterations); print(json.dumps(result, ensure_ascii=False, indent=2))"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }

    $BenchmarkPath = Join-Path $ResolvedOutputDir "benchmark.json"
    $benchmarkJson | Out-File -FilePath $BenchmarkPath -Encoding utf8

    & (Join-Path $PSScriptRoot "verify-results.ps1") -ResultDir $ResolvedOutputDir
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "[AgentGuard] Current benchmark validation complete: $BenchmarkPath"
} finally {
    if ((Test-Path $ResolvedOutputDir) -and $ResolvedOutputDir.StartsWith($ResolvedTempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $ResolvedOutputDir -Recurse -Force
    }
}
