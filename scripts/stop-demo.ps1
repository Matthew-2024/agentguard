param(
    [switch]$KeepPidFile,
    [int]$PortReleaseTimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeDir = Join-Path $RepoRoot "tmp-runtime"
$PidFile = Join-Path $RuntimeDir "demo-processes.json"

if (-not (Test-Path $PidFile)) {
    Write-Host "[AgentGuard] No demo PID file found: $PidFile"
    exit 0
}

$payload = Get-Content -Path $PidFile -Raw | ConvertFrom-Json
$processes = @(
    @{ Name = "backend"; Pid = [int]$payload.backend.pid },
    @{ Name = "frontend"; Pid = [int]$payload.frontend.pid }
)
$ports = @(
    [int]$payload.backend.port,
    [int]$payload.frontend.port
)

function Get-ChildProcessIds {
    param([int]$ParentPid)

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentPid" -ErrorAction SilentlyContinue
    $ids = New-Object System.Collections.Generic.List[int]
    foreach ($child in $children) {
        foreach ($descendant in Get-ChildProcessIds -ParentPid ([int]$child.ProcessId)) {
            $ids.Add($descendant) | Out-Null
        }
        $ids.Add([int]$child.ProcessId) | Out-Null
    }
    return $ids
}

$idsToStop = New-Object System.Collections.Generic.List[object]
foreach ($item in $processes) {
    $process = Get-Process -Id $item.Pid -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Write-Host "[AgentGuard] $($item.Name) process already stopped: $($item.Pid)"
        continue
    }
    foreach ($childPid in Get-ChildProcessIds -ParentPid $item.Pid) {
        $idsToStop.Add([pscustomobject]@{
            Name = "$($item.Name) child"
            Pid = $childPid
        }) | Out-Null
    }
    $idsToStop.Add([pscustomobject]@{
        Name = $item.Name
        Pid = $item.Pid
    }) | Out-Null
}

foreach ($item in $idsToStop) {
    $process = Get-Process -Id $item.Pid -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        continue
    }
    Write-Host "[AgentGuard] Stopping $($item.Name) process: $($item.Pid) ($($process.ProcessName))"
    Stop-Process -Id $item.Pid -Force
}

function Test-PortListening {
    param([int]$Port)

    $matches = netstat -ano | Select-String -Pattern ":$Port\s+.*LISTENING"
    return $null -ne $matches
}

function Get-ListeningProcessIds {
    param([int]$Port)

    $matches = netstat -ano | Select-String -Pattern ":$Port\s+.*LISTENING"
    $ids = New-Object System.Collections.Generic.HashSet[int]
    foreach ($match in $matches) {
        $parts = ($match.Line.Trim() -split "\s+")
        if ($parts.Count -ge 5) {
            $ids.Add([int]$parts[-1]) | Out-Null
        }
    }
    return $ids
}

foreach ($port in $ports) {
    foreach ($listenerPid in Get-ListeningProcessIds -Port $port) {
        $process = Get-Process -Id $listenerPid -ErrorAction SilentlyContinue
        if ($null -eq $process) {
            continue
        }
        Write-Host "[AgentGuard] Stopping process still listening on port ${port}: $listenerPid ($($process.ProcessName))"
        Stop-Process -Id $listenerPid -Force
    }
}

foreach ($port in $ports) {
    for ($i = 0; $i -lt $PortReleaseTimeoutSeconds; $i++) {
        if (-not (Test-PortListening -Port $port)) {
            break
        }
        Start-Sleep -Seconds 1
    }
    if (Test-PortListening -Port $port) {
        throw "[AgentGuard] Port still listening after stop: $port"
    }
}

if (-not $KeepPidFile) {
    Remove-Item -Path $PidFile -Force
}

Write-Host "[AgentGuard] Demo stop complete"
