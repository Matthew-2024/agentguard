# Result Gate Extraction

Time: 2026-06-18T21:07:54+08:00

## Scope

Improved the non-Docker delivery gate for reportable benchmark results. Docker was not started.

## Core Changes

- Added `scripts/verify-results.ps1` as an independent result artifact validator.
- Refactored `scripts/final-audit.ps1` to call `verify-results.ps1` instead of keeping benchmark checks inline.
- Updated `README.md` with the standalone result verification command.
- Updated `docs/实验说明.md` to require the result gate before writing benchmark numbers into the report.

## Validation Coverage

`verify-results.ps1` checks the authoritative `results/main_benchmark_with_consistency_precheck_*/benchmark.json` artifact for:

- Required benchmark sections.
- Minimum benchmark sample counts and unique template counts.
- Six expected baseline/ablation modes.
- Required case groups.
- AgentGuard attack interception, recoverable benign completion, and hard block thresholds.
- Rule-only and minus-taint ablation thresholds.
- Taint ablation delta.
- Consistency benign/abnormal controls and ablation rows.
- Consistency precheck enforcement metrics.
- Serial and concurrent pressure-test fields.

## Verified Evidence

- `.\scripts\verify-results.ps1` passed.
- All `scripts/*.ps1` files passed PowerShell syntax parsing.
- `git -c core.excludesFile= diff --check` passed.
- `.\scripts\scan-secrets.ps1` passed and scanned 96 files.
- `.\scripts\final-audit.ps1 -SkipDocker` passed:
  - 28 backend tests passed.
  - Backend compile check passed.
  - Baseline evaluation passed.
  - Benchmark and pressure test passed.
  - Frontend production build passed.
  - Secret scan passed.
  - Git diff check passed.
  - Authoritative benchmark result gate passed.

## Remaining Boundary

Docker runtime verification is still intentionally unverified. The project should not be marked fully complete until Docker is allowed and `.\scripts\final-audit.ps1` passes without `-SkipDocker`, or the accepted scope explicitly excludes Docker runtime verification.
