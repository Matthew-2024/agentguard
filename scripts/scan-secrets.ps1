param(
    [switch]$IncludeArtifacts,
    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$AllowedDemoEnvPath = "demo_data/benign/.env"
$AllowedDemoEnvLines = @(
    "AGENTGUARD_DEMO_TOKEN=demo-secret-not-real",
    "DATABASE_URL=sqlite:///demo.db"
)

$ExcludedExactPaths = @(
    "frontend/package-lock.json"
)

$DeniedExactPaths = @(
    ".npmrc",
    ".pypirc",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa"
)

$DeniedSegments = @(
    "secrets"
)

$DeniedExtensions = @(
    ".crt",
    ".key",
    ".p12",
    ".pem",
    ".pfx"
)

$ExcludedSegments = @(
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".pytest_cache_local",
    ".ruff_cache",
    ".vite",
    "__pycache__",
    "node_modules"
)

$ExcludedPrefixes = @(
    "frontend/dist/"
)

$ArtifactPrefixes = @(
    "results/",
    "tmp-plans/"
)

$TextExtensions = @(
    "",
    ".css",
    ".dockerignore",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml"
)

$HighConfidencePatterns = @(
    @{ Name = "AWS access key"; Regex = [regex]"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])" },
    @{ Name = "Google API key"; Regex = [regex]"AIza[0-9A-Za-z\-_]{35}" },
    @{ Name = "GitHub token"; Regex = [regex]"(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{20,})" },
    @{ Name = "Slack token"; Regex = [regex]"xox[baprs]-[0-9A-Za-z-]{20,}" },
    @{ Name = "OpenAI-style key"; Regex = [regex]"sk-(?:proj-|live-|test-)?[A-Za-z0-9_\-]{20,}" },
    @{ Name = "Stripe secret key"; Regex = [regex]"(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}" },
    @{ Name = "Private key block"; Regex = [regex]"-----BEGIN (?:RSA |DSA |EC |OPENSSH |)?PRIVATE KEY-----" },
    @{ Name = "JWT token"; Regex = [regex]"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}" }
)

$GenericAssignmentPattern = [regex]"(?i)^\s*(?:export\s+)?[""']?[A-Z0-9_.-]*(?:API[_-]?KEY|ACCESS[_-]?KEY|TOKEN|SECRET|PASSWORD|PRIVATE[_-]?KEY|CREDENTIAL|AUTH)[A-Z0-9_.-]*[""']?\s*[:=]\s*[""']?([^""',\s#;]+)"

function Normalize-RepoPath {
    param([string]$Path)
    return ($Path -replace "\\", "/")
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

function Test-IsExcludedPath {
    param([string]$RelativePath)

    $normalized = Normalize-RepoPath $RelativePath
    if ($ExcludedExactPaths -contains $normalized) {
        return $true
    }
    if (Test-HasPathSegment $normalized $ExcludedSegments) {
        return $true
    }
    foreach ($prefix in $ExcludedPrefixes) {
        if ($normalized.StartsWith($prefix)) {
            return $true
        }
    }
    if (-not $IncludeArtifacts) {
        foreach ($prefix in $ArtifactPrefixes) {
            if ($normalized.StartsWith($prefix)) {
                return $true
            }
        }
    }
    return $false
}

function Test-IsTextFile {
    param([string]$RelativePath)

    $normalized = Normalize-RepoPath $RelativePath
    $leaf = Split-Path -Leaf $normalized
    if ($leaf -in @(".gitignore", ".dockerignore")) {
        return $true
    }

    $extension = [System.IO.Path]::GetExtension($normalized).ToLowerInvariant()
    return $TextExtensions -contains $extension
}

function Test-IsAllowedPlaceholder {
    param([string]$Value)

    $normalized = $Value.Trim().Trim('"').Trim("'").TrimEnd(",").TrimEnd(";")
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return $true
    }
    $lowered = $normalized.ToLowerInvariant()
    $allowedFragments = @(
        "demo",
        "dummy",
        "example",
        "fake",
        "placeholder",
        "not-real",
        "changeme",
        "your-",
        "localhost",
        "127.0.0.1",
        "sqlite://",
        "none",
        "null",
        "false",
        "true"
    )
    foreach ($fragment in $allowedFragments) {
        if ($lowered.Contains($fragment)) {
            return $true
        }
    }
    return $false
}

function Get-MaskedValue {
    param([string]$Value)

    $trimmed = $Value.Trim()
    if ($trimmed.Length -le 8) {
        return "<redacted>"
    }
    return "$($trimmed.Substring(0, 4))...$($trimmed.Substring($trimmed.Length - 4))"
}

function Invoke-SelfTest {
    $excludedCases = @(
        @{ Path = "frontend/node_modules/pkg/index.js"; Excluded = $true },
        @{ Path = "backend/node_modules/pkg/index.js"; Excluded = $true },
        @{ Path = ".pytest_cache/v/cache.json"; Excluded = $true },
        @{ Path = "backend/.pytest_cache/v/cache.json"; Excluded = $true },
        @{ Path = "results/main/benchmark.json"; Excluded = -not $IncludeArtifacts },
        @{ Path = "tmp-plans/stage.md"; Excluded = -not $IncludeArtifacts },
        @{ Path = "backend/app/main.py"; Excluded = $false }
    )
    foreach ($case in $excludedCases) {
        $actual = Test-IsExcludedPath $case.Path
        if ($actual -ne $case.Excluded) {
            throw "Secret scan self-test failed for exclusion $($case.Path): expected $($case.Excluded), got $actual"
        }
    }

    $segmentCases = @(
        @{ Path = "secrets/prod.txt"; Denied = $true },
        @{ Path = "backend/secrets/prod.txt"; Denied = $true },
        @{ Path = "backend/app/main.py"; Denied = $false }
    )
    foreach ($case in $segmentCases) {
        $actual = Test-HasPathSegment $case.Path $DeniedSegments
        if ($actual -ne $case.Denied) {
            throw "Secret scan self-test failed for denied segment $($case.Path): expected $($case.Denied), got $actual"
        }
    }

    $placeholderCases = @(
        @{ Value = "demo-secret-not-real"; Allowed = $true },
        @{ Value = "your-api-key"; Allowed = $true },
        @{ Value = "prodSecretValue123"; Allowed = $false }
    )
    foreach ($case in $placeholderCases) {
        $actual = Test-IsAllowedPlaceholder $case.Value
        if ($actual -ne $case.Allowed) {
            throw "Secret scan self-test failed for placeholder $($case.Value): expected $($case.Allowed), got $actual"
        }
    }

    Write-Host "[AgentGuard] Secret scan self-test passed"
}

if ($SelfTest) {
    Invoke-SelfTest
    exit 0
}

$findings = New-Object System.Collections.Generic.List[object]
$files = git -c core.excludesFile= -c core.quotepath=false ls-files --cached --others --exclude-standard -- ':!.pytest_cache_local'
if ($LASTEXITCODE -ne 0) {
    throw "Unable to enumerate Git-visible files"
}

$scannedCount = 0
foreach ($relativePath in $files) {
    if ([string]::IsNullOrWhiteSpace($relativePath)) {
        continue
    }

    $normalizedPath = Normalize-RepoPath $relativePath
    if (Test-IsExcludedPath $normalizedPath) {
        continue
    }

    $extension = [System.IO.Path]::GetExtension($normalizedPath).ToLowerInvariant()
    $leaf = Split-Path -Leaf $normalizedPath
    if (($DeniedExactPaths -contains $leaf) -or ($DeniedExtensions -contains $extension)) {
        $findings.Add([pscustomobject]@{
            Path = $normalizedPath
            Line = 1
            Rule = "Committed credential file"
            Evidence = "Credential carrier files are not allowed in the repository"
        }) | Out-Null
        continue
    }
    $isDeniedCarrier = $false
    if (Test-HasPathSegment $normalizedPath $DeniedSegments) {
            $findings.Add([pscustomobject]@{
                Path = $normalizedPath
                Line = 1
                Rule = "Committed secrets directory"
                Evidence = "secrets directory content is not allowed in the repository"
            }) | Out-Null
            $isDeniedCarrier = $true
    }
    if ($isDeniedCarrier) {
        continue
    }

    if (-not (Test-IsTextFile $normalizedPath)) {
        continue
    }

    $fullPath = Join-Path $RepoRoot $normalizedPath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        continue
    }

    $item = Get-Item -LiteralPath $fullPath
    if ($item.Length -gt 1MB) {
        continue
    }

    $scannedCount += 1
    $lines = @(Get-Content -LiteralPath $fullPath)

    if ((Split-Path -Leaf $normalizedPath) -eq ".env" -and $normalizedPath -ne $AllowedDemoEnvPath) {
        $findings.Add([pscustomobject]@{
            Path = $normalizedPath
            Line = 1
            Rule = "Committed env file"
            Evidence = "Only .env.example and the fixed demo placeholder env file are allowed"
        }) | Out-Null
    }

    if ($normalizedPath -eq $AllowedDemoEnvPath) {
        $unexpectedDemoLines = $lines | Where-Object {
            -not [string]::IsNullOrWhiteSpace($_) -and $AllowedDemoEnvLines -notcontains $_
        }
        foreach ($line in $unexpectedDemoLines) {
            $findings.Add([pscustomobject]@{
                Path = $normalizedPath
                Line = [array]::IndexOf($lines, $line) + 1
                Rule = "Unexpected demo env content"
                Evidence = "demo_data/benign/.env may only contain fixed placeholder values"
            }) | Out-Null
        }
    }

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = [string]$lines[$i]
        $lineNumber = $i + 1

        foreach ($pattern in $HighConfidencePatterns) {
            $match = $pattern.Regex.Match($line)
            if ($match.Success) {
                $findings.Add([pscustomobject]@{
                    Path = $normalizedPath
                    Line = $lineNumber
                    Rule = $pattern.Name
                    Evidence = Get-MaskedValue $match.Value
                }) | Out-Null
            }
        }

        $assignment = $GenericAssignmentPattern.Match($line)
        if ($assignment.Success) {
            $value = $assignment.Groups[1].Value.Trim().Trim('"').Trim("'").TrimEnd(",").TrimEnd(";")
            if ((-not (Test-IsAllowedPlaceholder $value)) -and $value.Length -ge 16) {
                $findings.Add([pscustomobject]@{
                    Path = $normalizedPath
                    Line = $lineNumber
                    Rule = "Suspicious secret assignment"
                    Evidence = Get-MaskedValue $value
                }) | Out-Null
            }
        }
    }
}

if ($findings.Count -gt 0) {
    Write-Host "[AgentGuard] Secret scan failed:" -ForegroundColor Red
    foreach ($finding in $findings) {
        Write-Host ("  {0}:{1} [{2}] {3}" -f $finding.Path, $finding.Line, $finding.Rule, $finding.Evidence)
    }
    exit 1
}

Write-Host "[AgentGuard] Secret scan passed ($scannedCount files)"
