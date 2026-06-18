param(
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

Write-Host "[AgentGuard] Full local verification"
& (Join-Path $PSScriptRoot "verify.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[AgentGuard] Secret scan"
& (Join-Path $PSScriptRoot "scan-secrets.ps1") -SelfTest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $PSScriptRoot "scan-secrets.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[AgentGuard] Release file validation"
& (Join-Path $PSScriptRoot "verify-release-files.ps1") -SelfTest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $PSScriptRoot "verify-release-files.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[AgentGuard] Git diff check"
git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[AgentGuard] Authoritative result artifact"
& (Join-Path $PSScriptRoot "verify-results.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $SkipDocker) {
    Write-Host "[AgentGuard] Docker runtime verification"
    & (Join-Path $PSScriptRoot "verify-docker.ps1") -RunContainers
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "[AgentGuard] Docker runtime verification skipped"
}

Write-Host "[AgentGuard] Final audit complete"
