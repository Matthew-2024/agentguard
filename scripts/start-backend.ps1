param(
    [int]$Port = 8000,
    [switch]$DemoServer
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WorkspaceRoot = Resolve-Path (Join-Path $RepoRoot "..")
$Python = Join-Path $WorkspaceRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Root venv not found: $Python"
}
Set-Location $WorkspaceRoot

if ($DemoServer) {
    & $Python agentguard\backend\run_demo_server.py --port $Port
} else {
    & $Python -m uvicorn agentguard.backend.app.main:app --host 127.0.0.1 --port $Port
}
