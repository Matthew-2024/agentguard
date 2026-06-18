param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [int]$Retries = 30,
    [int]$DelaySeconds = 2
)

$ErrorActionPreference = "Stop"

$BackendUrl = "http://127.0.0.1:$BackendPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort"

function Wait-HttpOk {
    param(
        [string]$Name,
        [string]$Url,
        [scriptblock]$Validator
    )

    for ($i = 0; $i -lt $Retries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 3
            if (& $Validator $response) {
                Write-Host "[AgentGuard] $Name ready: $Url"
                return
            }
        } catch {
            if ($i -eq ($Retries - 1)) {
                throw "[AgentGuard] $Name health check failed: $Url"
            }
        }
        Start-Sleep -Seconds $DelaySeconds
    }
    throw "[AgentGuard] $Name health check timed out: $Url"
}

Wait-HttpOk `
    -Name "Backend" `
    -Url "$BackendUrl/health" `
    -Validator {
        param($response)
        if ($response.StatusCode -ne 200) {
            return $false
        }
        $payload = $response.Content | ConvertFrom-Json
        return $payload.status -eq "ok"
    }

Wait-HttpOk `
    -Name "Frontend" `
    -Url $FrontendUrl `
    -Validator {
        param($response)
        return $response.StatusCode -eq 200 -and $response.Content.Contains("<html")
    }

Write-Host "[AgentGuard] Demo health check passed"
