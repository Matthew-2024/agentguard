from __future__ import annotations

import unittest
from pathlib import Path

from agentguard.backend.app.demo.benchmark import (
    generate_benchmark_cases,
    run_benchmark,
    run_concurrent_pressure_test,
    run_consistency_benchmark,
    run_consistency_enforcement_benchmark,
    run_pressure_test,
)


ROOT = Path(__file__).resolve().parents[3]


class BenchmarkTests(unittest.TestCase):
    def test_generated_cases_cover_required_groups(self) -> None:
        cases = generate_benchmark_cases(repetitions=5)
        groups = {case.group for case in cases}

        self.assertEqual(len(cases), 40)
        self.assertIn("benign_normal", groups)
        self.assertIn("benign_sensitive", groups)
        self.assertIn("benign_external_share", groups)
        self.assertIn("composition_attack", groups)
        self.assertIn("poisoning_attack", groups)

    def test_benchmark_reports_ablation_modes(self) -> None:
        result = run_benchmark(ROOT, repetitions=2)
        modes = {row["mode"] for row in result["rows"]}
        agentguard = next(row for row in result["rows"] if row["mode"] == "agentguard")
        minus_taint = next(row for row in result["rows"] if row["mode"] == "agentguard_minus_taint")

        self.assertEqual(result["case_count"], 16)
        self.assertIn("agentguard_minus_taint", modes)
        self.assertIn("agentguard_minus_consistency", modes)
        self.assertIn("benign_recoverable_completion_rate", agentguard)
        self.assertEqual(agentguard["benign_recoverable_completion_rate"], 1.0)
        self.assertLessEqual(agentguard["hard_block_rate"], agentguard["false_positive_rate"])
        self.assertGreater(
            agentguard["attack_interception_rate"],
            minus_taint["attack_interception_rate"],
        )

    def test_consistency_benchmark_has_benign_control(self) -> None:
        result = run_consistency_benchmark(ROOT)

        self.assertGreaterEqual(result["benign_tool_count"], 4)
        self.assertGreaterEqual(result["abnormal_tool_count"], 3)
        self.assertEqual(result["consistency_false_positive_rate"], 0.0)
        self.assertEqual(result["consistency_detection_rate"], 1.0)

    def test_consistency_enforcement_blocks_before_runtime(self) -> None:
        result = run_consistency_enforcement_benchmark(ROOT)

        self.assertEqual(result["benign_allow_rate"], 1.0)
        self.assertGreaterEqual(result["abnormal_preexecution_block_rate"], 0.667)

    def test_pressure_test_reports_latency_and_audit_events(self) -> None:
        result = run_pressure_test(ROOT, iterations=12)

        self.assertEqual(result["iterations"], 12)
        self.assertGreaterEqual(result["avg_latency_ms"], 0)
        self.assertGreaterEqual(result["p95_latency_ms"], 0)
        self.assertGreater(result["audit_event_count"], 0)

    def test_concurrent_pressure_test_reports_throughput(self) -> None:
        result = run_concurrent_pressure_test(ROOT, iterations=8, workers=2)

        self.assertEqual(result["iterations"], 8)
        self.assertEqual(result["workers"], 2)
        self.assertGreater(result["throughput_per_sec"], 0)
        self.assertGreater(result["audit_event_count"], 0)


if __name__ == "__main__":
    unittest.main()
