# 2026-06-18T17:32:10+08:00 Optional Consistency Precheck

## Core Changes

- Added optional consistency precheck to `AgentGuardGateway`:
  - `enforce_consistency_precheck=True`
  - Default remains `False` so normal demo and runtime evidence collection are not disrupted.
- The precheck uses manifest + static entrypoint analysis before tool execution.
- High/critical precheck findings return `deny` before runtime execution.
- Added benchmark section:
  - `consistency_enforcement`
- Added tests for optional precheck behavior.
- Updated frontend Evaluation page to show consistency precheck block rate.
- Updated docs to state the boundary clearly:
  - Static precheck is conservative.
  - Runtime-only deviations still require execution proxy evidence.

## Verified Results

- `.\scripts\verify.ps1` passed.
- Backend pytest: 28 passed.
- Frontend production build passed.
- Formal benchmark archived at:
  - `results/main_benchmark_with_consistency_precheck_20260618_173045/benchmark.json`

Latest benchmark summary:

- Basic benchmark:
  - `case_count`: 80
  - `unique_case_count`: 8
  - AgentGuard direct benign completion: 0.8
  - AgentGuard recoverable benign completion: 1.0
  - AgentGuard attack interception: 1.0
  - AgentGuard hard block rate on benign tasks: 0.0
  - AgentGuard confirm rate: 0.25
- Consistency audit:
  - Detection rate: 1.0
  - False positive rate: 0.0
- Optional consistency precheck:
  - Benign allow rate: 1.0
  - Abnormal pre-execution block rate: 0.667
  - Boundary: `send_internal_tampered` is only visible after runtime evidence, so it is not claimed as statically pre-blocked.
- Pressure:
  - Serial P95: 115.583 ms
  - Concurrent throughput: 11.611/s
  - Concurrent P95: 728.295 ms

## Innovation Framing Update

- The project now has a closed loop for the second innovation:
  - audit mode: manifest/static/runtime tri-consistency detects 3/3 abnormal tools.
  - optional precheck mode: static consistency blocks 2/3 abnormal tools before execution.
- This is more defensible than claiming complete pre-execution detection for runtime-only behavior.

## Remaining Work

- Docker runtime verification remains pending until Docker Desktop daemon is running.
- Final completion audit still needed before marking the overall goal complete.
