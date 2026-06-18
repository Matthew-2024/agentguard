# Segment-level Release and Secret Gates

Time: 2026-06-18T21:53:20+08:00

## Scope

Hardened release and secret gates from root-prefix checks to path-segment checks. Docker was not started.

## Core Changes

- Updated `scripts/verify-release-files.ps1`.
  - Added `Test-HasPathSegment`.
  - Blocks sensitive/runtime directories at any path depth, including nested `node_modules`, `tmp-runtime`, `secrets`, `__pycache__`, and cache directories.
  - Extended `-SelfTest` cases for nested directories.
- Updated `scripts/scan-secrets.ps1`.
  - Added `Test-HasPathSegment`.
  - Treats `secrets` as a denied path segment at any depth.
  - Excludes cache/dependency directories by path segment instead of only root prefixes.
  - Added `-SelfTest` for exclusion, denied-segment, and placeholder rules.
- Updated `scripts/final-audit.ps1`.
  - Runs `scan-secrets.ps1 -SelfTest` before the actual secret scan.

## Bug Found and Fixed

The first segment implementation used `Normalize-RepoPath $Path -split "/"`, which did not force normalization before splitting. `verify-release-files.ps1 -SelfTest` caught this because `frontend/node_modules/pkg/index.js` was not classified as forbidden. The function was fixed to use:

```powershell
@((Normalize-RepoPath $Path) -split "/")
```

The same fix was applied to `scan-secrets.ps1`.

## Verified Evidence

- `.\scripts\verify-release-files.ps1 -SelfTest` passed.
- `.\scripts\scan-secrets.ps1 -SelfTest` passed.
- `.\scripts\verify-release-files.ps1` passed.
- `.\scripts\scan-secrets.ps1` passed and scanned 99 files.
- All `scripts/*.ps1` files passed PowerShell syntax parsing.
- `git -c core.excludesFile= diff --check` passed.
- `.\scripts\final-audit.ps1 -SkipDocker` passed:
  - backend pytest 28/28 passed
  - backend compile check passed
  - baseline evaluation passed
  - current-code benchmark metric gate passed
  - frontend production build passed
  - secret scan self-test and scan passed
  - release file validation self-test and validation passed
  - authoritative result artifact gate passed
- No Git-visible files remained under `tmp-runtime`.

## Remaining Boundary

Docker runtime verification remains intentionally unverified. Full completion still requires `.\scripts\final-audit.ps1` without `-SkipDocker`, unless the accepted scope explicitly excludes Docker runtime verification.
