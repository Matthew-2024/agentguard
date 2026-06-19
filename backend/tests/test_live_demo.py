from __future__ import annotations

import os
import unittest
from pathlib import Path

from agentguard.backend.app.demo.live_demo import run_live_demo
from agentguard.backend.run_demo_server import ROOT as DEMO_SERVER_ROOT


ROOT = Path(__file__).resolve().parents[3]


class LiveDemoTests(unittest.TestCase):
    def test_live_demo_runs_real_gateway_chain(self) -> None:
        os.environ["AGENTGUARD_DB"] = str(ROOT / "agentguard" / "tmp-runtime" / "test_live_demo.db")
        result = run_live_demo(ROOT)
        steps = [
            step
            for scenario in result["scenario_runs"]
            for step in scenario["steps"]
        ]

        self.assertEqual(result["final_taint"], "quarantined")
        self.assertTrue(any(step["poison_decision"] == "quarantine" for step in steps))
        self.assertTrue(any(step["decision"] == "deny" for step in steps))
        self.assertTrue(any(step["runtime_evidence"]["requests"] for step in steps))
        self.assertTrue(
            any(
                item["report"]["risk_level"] == "critical"
                for item in result["consistency_reports"]
            )
        )
        self.assertEqual(result["baseline"]["case_count"], 7)
        self.assertGreaterEqual(len(result["events"]), len(steps))

    def test_demo_server_uses_same_workspace_root(self) -> None:
        self.assertEqual(DEMO_SERVER_ROOT, ROOT)


if __name__ == "__main__":
    unittest.main()
