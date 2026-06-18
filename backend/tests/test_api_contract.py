from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from agentguard.backend.app.main import create_app


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_app())

    def test_health_contract(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "agentguard-api")

    def test_benchmark_contract(self) -> None:
        response = self.client.post("/demo/benchmark/run?repetitions=1&pressure_iterations=4")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("basic_benchmark", payload)
        self.assertIn("consistency_benchmark", payload)
        self.assertIn("pressure_test", payload)
        self.assertIn("concurrent_pressure_test", payload)

    def test_report_markdown_contract(self) -> None:
        self.client.post("/demo/live/run")
        response = self.client.get("/report/latest.md")

        self.assertEqual(response.status_code, 200)
        self.assertIn("AgentGuard Session Report", response.text)


if __name__ == "__main__":
    unittest.main()
