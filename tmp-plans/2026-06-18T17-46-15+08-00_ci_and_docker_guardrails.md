# 2026-06-18T17:46:15+08:00 CI And Docker Guardrails

## Core Changes

- Added `.github/workflows/ci.yml`.
  - Runs on push, pull request, and manual dispatch.
  - Creates the required root venv.
  - Installs frontend dependencies with `npm ci`.
  - Runs `scripts/final-audit.ps1 -SkipDocker`.
  - Runs `docker compose config`.
  - Runs `docker compose build`.
- Improved `scripts/verify-docker.ps1`.
  - Performs an explicit Docker daemon precheck.
  - Fails with a clear message instructing users to start Docker Desktop.
- Updated README and engineering delivery docs with final audit commands and CI coverage.

## Verified Results

- `scripts/verify-docker.ps1` now fails clearly when Docker daemon is unavailable.
- `scripts/final-audit.ps1 -SkipDocker` passed:
  - backend pytest: 28 passed
  - compile check passed
  - baseline evaluation passed
  - benchmark and pressure test passed
  - frontend production build passed
  - diff check passed
  - benchmark JSON metric checks passed
- `git diff --check` passed.

## Remaining Work

- Docker Desktop daemon is still not running locally.
- Full final audit still requires:
  - `.\scripts\final-audit.ps1`
- CI Docker build will verify container image construction once changes are pushed to a remote with GitHub Actions enabled.

## Completion Status

- Local non-Docker engineering completion is strongly verified.
- Docker runtime verification remains unverified, so the overall goal remains active.
