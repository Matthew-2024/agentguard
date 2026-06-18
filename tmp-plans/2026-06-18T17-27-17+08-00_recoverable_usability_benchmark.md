# 2026-06-18T17:27:17+08:00 Recoverable Usability Benchmark

## Core Changes

- Changed `untrusted + external_send` from hard `deny` to `confirm`.
- Added benign external sharing cases to the benchmark:
  - `benign_external_share`
  - The task models normal user intent such as sharing a public webpage summary with an allowed partner domain.
- Added usability metrics:
  - `benign_recoverable_completion_rate`
  - `hard_block_rate`
  - `confirm_rate`
- Updated frontend Evaluation table:
  - Shows direct completion, recoverable completion, attack interception, and hard block rate.
- Updated experiment docs:
  - Clarified that `false_positive_rate` is a non-allow intervention rate and includes recoverable confirms.
  - Clarified that `hard_block_rate` is the hard usability failure metric.

## Verified Results

- `.\scripts\verify.ps1` passed.
- Backend pytest: 26 passed.
- Frontend production build passed.
- Formal benchmark archived at:
  - `results/main_benchmark_20260618_172552/benchmark.json`

Benchmark summary:

- `case_count`: 80
- `unique_case_count`: 8
- Groups:
  - `benign_normal`: 20
  - `benign_sensitive`: 10
  - `benign_external_share`: 10
  - `context_seed`: 10
  - `composition_attack`: 10
  - `poisoning_attack`: 20

AgentGuard row:

- Direct benign completion: 0.8
- Recoverable benign completion: 1.0
- Attack interception: 1.0
- Intervention rate on benign cases: 0.2
- Hard block rate on benign cases: 0.0
- Confirm rate: 0.25
- Policy match rate: 0.875

Consistency benchmark:

- Benign tools: 4
- Abnormal tools: 3
- False positive rate: 0.0
- Detection rate: 1.0
- Ablation:
  - `manifest_only`: detection 0.0
  - `static_only`: detection 0.667
  - `runtime_only`: detection 1.0
  - `tri_consistency`: detection 1.0

Pressure test:

- Serial P95: 111.67 ms
- Concurrent throughput: 11.565/s
- Concurrent P95: 733.007 ms

## Innovation Framing Update

- Taint is no longer framed only as blocking. It is framed as adaptive control:
  - trusted context: allow
  - untrusted context: confirm for recoverable sharing
  - quarantined context: deny
- This directly answers the expected question: "What if the user legitimately wants to summarize a webpage and send it?"
- The answer is now backed by a measurable distinction between intervention rate and hard block rate.

## Remaining Work

- Docker runtime verification is still pending because Docker Desktop daemon is not running.
- Consider adding optional consistency precheck enforcement so high/critical tool audit reports can block gateway calls before execution.
- Consider producing a concise submission checklist after Docker runtime verification.
