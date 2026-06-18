param(
    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

function Normalize-RepoPath {
    param([string]$Path)
    return ($Path -replace "\\", "/")
}

function Assert-Condition {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Test-PathInSet {
    param(
        [string[]]$Paths,
        [string]$ExpectedPath
    )

    return $Paths -contains (Normalize-RepoPath $ExpectedPath)
}

function Assert-RepoPathPresent {
    param(
        [string[]]$Paths,
        [string]$ExpectedPath
    )

    Assert-Condition (Test-PathInSet $Paths $ExpectedPath) "Required release file is missing from Git-visible files: $ExpectedPath"
}

function Test-HasPathSegment {
    param(
        [string]$Path,
        [string[]]$Segments
    )

    $parts = @((Normalize-RepoPath $Path) -split "/" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    foreach ($segment in $Segments) {
        if ($parts -contains $segment) {
            return $true
        }
    }
    return $false
}

function Test-ForbiddenPath {
    param([string]$Path)

    $normalized = Normalize-RepoPath $Path
    $leaf = Split-Path -Leaf $normalized
    $extension = [System.IO.Path]::GetExtension($normalized).ToLowerInvariant()

    if ($normalized -eq ".env.example" -or $normalized -eq "demo_data/benign/.env") {
        return $false
    }

    if ($leaf -eq ".env" -or $leaf.StartsWith(".env.")) {
        return $true
    }

    $forbiddenExact = @(
        ".npmrc",
        ".pypirc",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519"
    )
    if ($forbiddenExact -contains $leaf) {
        return $true
    }

    $forbiddenSegments = @(
        ".mypy_cache",
        ".pytest_cache",
        ".pytest_cache_local",
        ".ruff_cache",
        ".vite",
        "__pycache__",
        "node_modules",
        "secrets",
        "tmp-runtime"
    )
    if (Test-HasPathSegment $normalized $forbiddenSegments) {
        return $true
    }

    $forbiddenExtensions = @(
        ".crt",
        ".db",
        ".key",
        ".log",
        ".p12",
        ".pem",
        ".pfx",
        ".tmp"
    )
    if ($forbiddenExtensions -contains $extension) {
        return $true
    }

    if ($normalized.EndsWith(".db-journal")) {
        return $true
    }

    return $false
}

function Invoke-SelfTest {
    $cases = @(
        @{ Path = ".env"; Forbidden = $true },
        @{ Path = "backend/.env"; Forbidden = $true },
        @{ Path = "backend/.env.local"; Forbidden = $true },
        @{ Path = "demo_data/benign/.env"; Forbidden = $false },
        @{ Path = ".env.example"; Forbidden = $false },
        @{ Path = "frontend/node_modules/pkg/index.js"; Forbidden = $true },
        @{ Path = "backend/node_modules/pkg/index.js"; Forbidden = $true },
        @{ Path = "tmp-runtime/benchmark_verify/a.json"; Forbidden = $true },
        @{ Path = "backend/tmp-runtime/benchmark_verify/a.json"; Forbidden = $true },
        @{ Path = "backend/cache/__pycache__/x.pyc"; Forbidden = $true },
        @{ Path = "secrets/prod.txt"; Forbidden = $true },
        @{ Path = "backend/secrets/prod.txt"; Forbidden = $true },
        @{ Path = "backend/.pytest_cache/v/cache.json"; Forbidden = $true },
        @{ Path = "backend/cert.pem"; Forbidden = $true },
        @{ Path = "backend/app/main.py"; Forbidden = $false },
        @{ Path = "results/main_benchmark/benchmark.json"; Forbidden = $false }
    )

    foreach ($case in $cases) {
        $actual = Test-ForbiddenPath $case.Path
        Assert-Condition ($actual -eq $case.Forbidden) "Self-test failed for $($case.Path): expected forbidden=$($case.Forbidden), got $actual"
    }
    Write-Host "[AgentGuard] Release file validation self-test passed"
}

if ($SelfTest) {
    Invoke-SelfTest
    exit 0
}

Write-Host "[AgentGuard] Release file validation"

$GitFiles = git -c core.excludesFile= -c core.quotepath=false ls-files --cached --others --exclude-standard
if ($LASTEXITCODE -ne 0) {
    throw "Unable to enumerate Git-visible files"
}

$Paths = @(
    $GitFiles |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ForEach-Object { Normalize-RepoPath $_ }
)

$RequiredPaths = @(
    ".dockerignore",
    ".env.example",
    ".github/workflows/ci.yml",
    ".gitignore",
    "Dockerfile",
    "README.md",
    "docker-compose.yml",
    "pytest.ini",
    "backend/app/demo/baseline_eval.py",
    "backend/app/demo/benchmark.py",
    "backend/app/demo/live_demo.py",
    "backend/app/demo/tools.py",
    "backend/app/main.py",
    "backend/app/routers/demo.py",
    "backend/app/routers/report.py",
    "backend/app/services/audit_logger.py",
    "backend/app/services/consistency_analyzer.py",
    "backend/app/services/gateway.py",
    "backend/app/services/report_generator.py",
    "backend/manifests/read_public_doc_tampered.json",
    "backend/manifests/send_internal_tampered.json",
    "backend/policies/taint_policy.yaml",
    "backend/requirements.txt",
    "backend/run_demo_server.py",
    "backend/tests/test_api_contract.py",
    "backend/tests/test_benchmark.py",
    "backend/tests/test_consistency_analyzer.py",
    "backend/tests/test_live_demo.py",
    "backend/tests/test_report_generator.py",
    "backend/tests/test_taint_gateway.py",
    "demo_data/benign/.env",
    "demo_data/tampered_tools/overprivileged_tools.py",
    "docs/实验说明.md",
    "docs/工程交付说明.md",
    "docs/功能完整性审查报告.md",
    "docs/提交与验收清单.md",
    "docs/队友交付说明.md",
    "docs/答辩材料.md",
    "frontend/Dockerfile",
    "frontend/nginx.conf",
    "frontend/src/api/liveDemo.ts",
    "frontend/src/pages/Evaluation.tsx",
    "frontend/src/styles/app.css",
    "results/README.md",
    "results/main_benchmark_with_consistency_precheck_20260618_173045/benchmark.json",
    "scripts/check-demo.ps1",
    "scripts/final-audit.ps1",
    "scripts/save-benchmark.ps1",
    "scripts/scan-secrets.ps1",
    "scripts/start-backend.ps1",
    "scripts/start-demo.ps1",
    "scripts/start-frontend.ps1",
    "scripts/stop-demo.ps1",
    "scripts/verify-benchmark.ps1",
    "scripts/verify-docker.ps1",
    "scripts/verify-release-files.ps1",
    "scripts/verify-results.ps1",
    "scripts/verify.ps1"
)

foreach ($path in $RequiredPaths) {
    Assert-RepoPathPresent $Paths $path
}

$Forbidden = @(
    $Paths |
        Where-Object { Test-ForbiddenPath $_ }
)
Assert-Condition ($Forbidden.Count -eq 0) "Forbidden release files are Git-visible: $($Forbidden -join ', ')"

$ResultArtifacts = @(
    $Paths |
        Where-Object { $_ -like "results/*/benchmark.json" }
)
Assert-Condition ($ResultArtifacts.Count -ge 1) "No benchmark result artifact is Git-visible under results/*/benchmark.json"

$PlanFiles = @(
    $Paths |
        Where-Object { $_ -like "tmp-plans/*.md" }
)
Assert-Condition ($PlanFiles.Count -ge 1) "No stage summary is Git-visible under tmp-plans/*.md"

Write-Host "[AgentGuard] Required release files: $($RequiredPaths.Count)"
Write-Host "[AgentGuard] Benchmark artifacts: $($ResultArtifacts.Count)"
Write-Host "[AgentGuard] Stage summaries: $($PlanFiles.Count)"
Write-Host "[AgentGuard] Release file validation complete"
