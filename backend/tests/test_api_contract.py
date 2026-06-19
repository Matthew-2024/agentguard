from __future__ import annotations

import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from agentguard.backend.app.main import create_app

ROOT = Path(__file__).resolve().parents[3]


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["AGENTGUARD_API_KEY"] = "test-key"
        os.environ["AGENTGUARD_DB"] = str(ROOT / "agentguard" / "tmp-runtime" / "test_api_contract.db")
        cls.client = TestClient(create_app())
        cls.headers = {"X-API-Key": "test-key"}

    def test_health_contract(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "agentguard-api")

    def test_benchmark_contract(self) -> None:
        response = self.client.post(
            "/demo/benchmark/run?repetitions=1&pressure_iterations=4",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("basic_benchmark", payload)
        self.assertIn("consistency_benchmark", payload)
        self.assertIn("pressure_test", payload)
        self.assertIn("concurrent_pressure_test", payload)

    def test_report_markdown_contract(self) -> None:
        self.client.post("/demo/live/run", headers=self.headers)
        response = self.client.get("/report/latest.md", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn("AgentGuard Session Report", response.text)

    def test_protected_routes_require_api_key(self) -> None:
        response = self.client.post("/demo/live/run")

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
