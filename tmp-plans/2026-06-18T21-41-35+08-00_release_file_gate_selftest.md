# Release File Gate Self-test

Time: 2026-06-18T21:41:35+08:00

## Scope

Hardened the release file gate so it independently catches nested env files and common secret/runtime carriers. Docker was not started.

## Core Changes

- Updated `scripts/verify-release-files.ps1`.
- Added `-SelfTest` mode with built-in path classification cases.
- Tightened env-file blocking from root-only `.env` checks to leaf-name checks:
  - blocks `.env`
  - blocks `backend/.env`
  - blocks `backend/.env.local`
  - allows only `.env.example` and `demo_data/benign/.env`
- Integrated `verify-release-files.ps1 -SelfTest` into `scripts/final-audit.ps1`.
- Updated `docs/提交与验收清单.md` with the self-test command.

## Verified Evidence

- `.\scripts\verify-release-files.ps1 -SelfTest` passed.
- `.\scripts\verify-release-files.ps1` passed.
- `scripts/verify-release-files.ps1` passed PowerShell syntax parsing.
- `.\scripts\final-audit.ps1 -SkipDocker` passed:
  - backend pytest 28/28 passed
  - backend compile check passed
  - baseline evaluation passed
  - current-code benchmark metric gate passed
  - frontend production build passed
  - secret scan passed
  - release file validation self-test passed
  - release file validation passed
  - git diff check passed
  - authoritative result artifact gate passed
- No Git-visible files remained under `tmp-runtime`.

## Remaining Boundary

Docker runtime verification remains intentionally unverified. Full completion still requires `.\scripts\final-audit.ps1` without `-SkipDocker`, unless the accepted scope explicitly excludes Docker runtime verification.
