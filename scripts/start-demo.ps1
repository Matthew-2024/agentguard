param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$Wait
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WorkspaceRoot = Resolve-Path (Join-Path $RepoRoot "..")
$Python = Join-Path $WorkspaceRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Root venv not found: $Python"
}

$BackendScript = Join-Path $PSScriptRoot "start-backend.ps1"
$FrontendScript = Join-Path $PSScriptRoot "start-frontend.ps1"
$CheckScript = Join-Path $PSScriptRoot "check-demo.ps1"
$ApiUrl = "http://127.0.0.1:$BackendPort"
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
$backendProcess = Start-Process -FilePath "powershell.exe" `
    -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$BackendScript`"",
        "-DemoServer",
        "-Port", "$BackendPort"
    ) `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 2

Write-Host "[AgentGuard] Starting demo frontend on http://127.0.0.1:$FrontendPort"
$frontendProcess = Start-Process -FilePath "powershell.exe" `
    -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$FrontendScript`"",
        "-Port", "$FrontendPort",
        "-ApiUrl", $ApiUrl
    ) `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Hidden `
    -PassThru

@{
    started_at = (Get-Date).ToString("o")
    backend = @{
        pid = $backendProcess.Id
        port = $BackendPort
        url = $ApiUrl
        script = $BackendScript
    }
    frontend = @{
        pid = $frontendProcess.Id
        port = $FrontendPort
        url = "http://127.0.0.1:$FrontendPort"
        script = $FrontendScript
    }
} | ConvertTo-Json -Depth 4 | Set-Content -Path $PidFile -Encoding utf8

Write-Host "[AgentGuard] Demo started"
Write-Host "Backend:  $ApiUrl"
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
Write-Host "PID file: $PidFile"

if ($Wait) {
    try {
        & $CheckScript -BackendPort $BackendPort -FrontendPort $FrontendPort
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } catch {
        Write-Host "[AgentGuard] Demo readiness failed, stopping recorded processes"
        & (Join-Path $PSScriptRoot "stop-demo.ps1")
        throw
    }
}
