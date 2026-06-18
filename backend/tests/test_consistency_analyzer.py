from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentguard.backend.app.models import RuntimeEvidence
from agentguard.backend.app.services.gateway import AgentGuardGateway


ROOT = Path(__file__).resolve().parents[3]


class ConsistencyAnalyzerTests(unittest.TestCase):
    def test_tampered_weather_runtime_is_critical(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = AgentGuardGateway(ROOT, audit_db_path=Path(tmp) / "audit.db")
            response = gateway.call_tool(
                gateway_request(
                    session_id="tool-audit",
                    tool_name="weather_query_tampered",
                    arguments={"city": "Hangzhou"},
                )
            )
            report = gateway.audit_tool_consistency(
                "weather_query_tampered",
                ROOT / "agentguard" / "demo_data" / "tampered_tools" / "weather_tampered.py",
                runtime_evidence=response.runtime_evidence,
            )
            self.assertEqual(report.risk_level, "critical")
            self.assertTrue(any(dev.type == "undeclared_network" for dev in report.deviations))
            self.assertTrue(any(dev.type == "credential_access" for dev in report.deviations))

    def test_clean_runtime_can_be_low_risk(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = AgentGuardGateway(ROOT, audit_db_path=Path(tmp) / "audit.db")
            manifest = gateway.scanner.load_manifest("weather_query")
            static = gateway.scanner.scan_source_file(
                ROOT / "agentguard" / "demo_data" / "tampered_tools" / "weather_tampered.py"
            )
            clean_static = static.model_copy(
                update={
                    "file_ops": [],
                    "network_calls": ["ctx.http_get"],
                    "sensitive_strings": [],
                }
            )
            report = gateway.consistency_analyzer.analyze(
                manifest,
                clean_static,
                RuntimeEvidence(domains=["api.weather.local"], permissions=["network"]),
            )
            self.assertEqual(report.risk_level, "low")

    def test_static_scan_uses_manifest_entrypoint_function(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = AgentGuardGateway(ROOT, audit_db_path=Path(tmp) / "audit.db")
            report = gateway.audit_tool_consistency(
                "weather_query",
                ROOT / "agentguard" / "backend" / "app" / "demo" / "tools.py",
                runtime_evidence=RuntimeEvidence(domains=["api.weather.local"], permissions=["network"]),
            )
            self.assertFalse(
                any(dev.type == "credential_access" for dev in report.deviations),
                "weather_query 审计不应扫描到同文件 weather_query_tampered 的敏感字符串",
            )
            self.assertEqual(report.risk_level, "low")


def gateway_request(session_id: str, tool_name: str, arguments: dict):
    from agentguard.backend.app.models import ToolCallRequest

    return ToolCallRequest(
        session_id=session_id,
        tool_name=tool_name,
        arguments=arguments,
        context_source="user",
    )


if __name__ == "__main__":
    unittest.main()
