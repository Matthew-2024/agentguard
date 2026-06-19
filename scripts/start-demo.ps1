param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [string]$ApiKey = "agentguard-local-dev",
    [switch]$Wait
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WorkspaceRoot = Resolve-Path (Join-Path $RepoRoot "..")
$Python = Join-Path $WorkspaceRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Root venv not found: $Python"
}

$CheckScript = Join-Path $PSScriptRoot "check-demo.ps1"
$FrontendRoot = Join-Path $RepoRoot "frontend"
$ApiUrl = "http://127.0.0.1:$BackendPort"
$CorsOrigins = "http://127.0.0.1:$FrontendPort,http://localhost:$FrontendPort"
$RuntimeDir = Join-Path $RepoRoot "tmp-runtime"
$PidFile = Join-Path $RuntimeDir "demo-processes.json"
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

function Test-PortListening {
    param([int]$Port)

    $matches = netstat -ano | Select-String -Pattern ":$Port\s+.*LISTENING"
    return $null -ne $matches
}

foreach ($port in @($BackendPort, $FrontendPort)) {
    if (Test-PortListening -Port $port) {
        throw "[AgentGuard] Port is already in use: $port"
    }
}

Write-Host "[AgentGuard] Starting demo backend on $ApiUrl"
$env:AGENTGUARD_API_KEY = $ApiKey
$env:AGENTGUARD_CORS_ORIGINS = $CorsOrigins
$backendProcess = Start-Process -FilePath $Python `
    -ArgumentList @("agentguard\backend\run_demo_server.py", "--port", "$BackendPort") `
    -WorkingDirectory $WorkspaceRoot `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 2

Write-Host "[AgentGuard] Starting demo frontend on http://127.0.0.1:$FrontendPort"
$env:VITE_AGENTGUARD_API_URL = $ApiUrl
$env:VITE_AGENTGUARD_API_KEY = $ApiKey
if (-not (Test-Path (Join-Path $FrontendRoot "node_modules"))) {
    Push-Location $FrontendRoot
    npm.cmd install
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Pop-Location
}
$frontendProcess = Start-Process -FilePath "npm.cmd" `
    -ArgumentList @("run", "dev", "--", "--port", "$FrontendPort") `
    -WorkingDirectory $FrontendRoot `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 5

@{
    started_at = (Get-Date).ToString("o")
    backend = @{
        pid = $backendProcess.Id
        port = $BackendPort
        url = $ApiUrl
        script = "agentguard\backend\run_demo_server.py"
        api_key = $ApiKey
    }
    frontend = @{
        pid = $frontendProcess.Id
        port = $FrontendPort
        url = "http://127.0.0.1:$FrontendPort"
        script = "npm.cmd run dev"
    }
} | ConvertTo-Json -Depth 4 | Set-Content -Path $PidFile -Encoding utf8

Write-Host "[AgentGuard] Demo started"
Write-Host "Backend:  $ApiUrl"
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
Write-Host "PID file: $PidFile"

if ($Wait) {
    try {
        & $CheckScript -BackendPort $BackendPort -FrontendPort $FrontendPort -ApiKey $ApiKey
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } catch {
        Write-Host "[AgentGuard] Demo readiness failed, stopping recorded processes"
        & (Join-Path $PSScriptRoot "stop-demo.ps1")
        throw
    }
}
