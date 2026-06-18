# 2026-06-18T17:17:14+08:00 Engineering Benchmark Hardening

## Core Changes

- Created and used the workspace root venv at `E:\study\code\agent_guard\venv`.
- Added missing backend test dependency `httpx2`.
- Forced PowerShell backend verification/start scripts to use the root venv.
- Added API/report/benchmark delivery surface already present in the working tree and verified it under the root venv.
- Reworked benchmark attribution:
  - Added true session-level taint propagation cases where external content seeds the session and later `context_source="agent"` calls are controlled by inherited taint.
  - Strengthened `rule_only` baseline with sensitive marker, external domain, and execute-category checks.
  - Added `unique_case_count`, environment metadata, `policy_match_rate`, and raw per-case details.
  - Kept `agentguard_minus_consistency` for UI/API compatibility but documented that consistency is measured by a separate ablation.
- Reworked consistency benchmark:
  - Benign runtime evidence now comes from actual `gateway.call_tool()` execution.
  - Added three abnormal tools: weather exfiltration, overprivileged public read, internal-notify external exfiltration.
  - Added `manifest_only / static_only / runtime_only / tri_consistency` consistency ablation rows.
- Stabilized SQLite audit logging for concurrent pressure tests with WAL, busy timeout, and an in-process write lock.
- Fixed verification scripts so external command failures propagate as non-zero exits.
- Added Docker delivery files and hardened them:
  - `.dockerignore` excludes env/secrets/key material.
  - backend container runs as a non-root user.
  - CORS origins are environment-configurable.
- Added documentation:
  - `docs/实验说明.md`
  - `docs/工程交付说明.md`
- Added result archival script:
  - `scripts/save-benchmark.ps1`

## Verified Results

- `.\scripts\verify.ps1` passed:
  - backend pytest: 26 passed
  - backend compile check passed
  - baseline evaluation passed
  - benchmark and pressure test passed
  - frontend production build passed
- `docker compose config` passed.
- `.\scripts\verify-docker.ps1` correctly fails during build because Docker Desktop daemon is not running on this machine.
- Smoke benchmark result archived at:
  - `results/smoke_benchmark_20260618_171452/benchmark.json`

Smoke benchmark summary:

- `case_count`: 14
- `unique_case_count`: 7
- `agentguard attack_interception_rate`: 1.0
- `agentguard false_positive_rate`: 0.0
- `agentguard_minus_taint attack_interception_rate`: 0.333
- consistency abnormal tools: 3
- consistency detection rate: 1.0
- consistency false positive rate: 0.0

## Innovation Framing

- Main mechanism: coarse session-level taint propagation from external content to later agent-originated tool calls.
- Attribution proof: composition attack uses individually legal actions, so stronger rule-only still misses part of the attack while taint propagation blocks it.
- Second mechanism: manifest/static/runtime consistency with runtime evidence collected through execution proxy.
- Attribution proof: consistency benchmark now separates manifest-only, static-only, runtime-only, and tri-consistency modes.

## Remaining Work

- Start Docker Desktop and rerun `.\scripts\verify-docker.ps1 -RunContainers`.
- Consider adding a benign external-sharing task to measure usability cost of `untrusted + external_send`.
- Consider making consistency enforcement optionally block gateway calls for tools with high/critical audit reports.
- If preparing final report, run a larger formal benchmark with `.\scripts\save-benchmark.ps1 -ExperimentName "main_benchmark" -Repetitions 10 -PressureIterations 200`.
