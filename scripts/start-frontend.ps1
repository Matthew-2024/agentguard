param(
    [int]$Port = 5173,
    [string]$ApiUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendRoot = Join-Path $RepoRoot "frontend"
Set-Location $FrontendRoot

if (-not (Test-Path "node_modules")) {
    npm.cmd install
}

$env:VITE_AGENTGUARD_API_URL = $ApiUrl
npm.cmd run dev -- --port $Port
