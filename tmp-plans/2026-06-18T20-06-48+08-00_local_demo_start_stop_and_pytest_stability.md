# Stage Summary: Local Demo Start/Stop and Pytest Stability

Timestamp: 2026-06-18T20-06-48+08:00

## Core Changes

- Added scripts/stop-demo.ps1 to cleanly stop only the demo processes recorded by scripts/start-demo.ps1.
- Hardened scripts/start-demo.ps1 to write a PID manifest under 	mp-runtime/demo-processes.json.
- Added child-process-aware shutdown logic so the demo stop script can terminate the hidden backend/frontend wrapper chain.
- Updated scripts/verify.ps1 to run backend tests with -p no:cacheprovider, removing the pytest cache-provider hang seen during long local runs.
- Removed the obsolete cache_dir pytest option from pytest.ini.
- Added .pytest_cache_local/ to .gitignore and scripts/scan-secrets.ps1 exclusions to avoid stale cache permission noise.

## Verified Results

- scripts/start-demo.ps1 -BackendPort 8100 -FrontendPort 5174 started the demo and wrote the PID file.
- scripts/stop-demo.ps1 successfully stopped only the recorded demo processes and removed the PID file.
- scripts/verify.ps1 -SkipFrontend passed with 28 backend tests.
- scripts/final-audit.ps1 -SkipDocker passed.
- scripts/scan-secrets.ps1 passed.
- pytest backend/tests -p no:cacheprovider passed in the root venv.

## Current Boundary

- Docker runtime still remains the only unverified deployment gate.
- Docker Desktop daemon must be started before running the full container verification.

## Next Plan

- If Docker Desktop is available, run scripts/final-audit.ps1 without -SkipDocker.
- Otherwise keep the current local non-Docker delivery as the stable engineering baseline for the competition.
