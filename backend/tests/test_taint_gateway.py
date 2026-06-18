from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentguard.backend.app.models import Decision, TaintStatus, ToolCallRequest, ToolCategory
from agentguard.backend.app.services.audit_logger import AuditLogger, default_audit_db_path
from agentguard.backend.app.services.gateway import AgentGuardGateway
from agentguard.backend.app.services.policy_engine import PolicyEngine
from agentguard.backend.app.services.poisoning_detector import PoisoningDetector


ROOT = Path(__file__).resolve().parents[3]


class GatewayTaintTests(unittest.TestCase):
    def make_gateway(self, tmp: str) -> AgentGuardGateway:
        return AgentGuardGateway(ROOT, audit_db_path=Path(tmp) / "audit.db")

    def test_poisoned_external_return_quarantines_session(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = self.make_gateway(tmp)
            response = gateway.call_tool(
                ToolCallRequest(
                    session_id="s1",
                    tool_name="search_api",
                    arguments={"query": "agentguard", "variant": "poisoned"},
                    context_source="external_api",
                )
            )
            self.assertEqual(response.decision, Decision.ALLOW)
            self.assertEqual(response.taint_status, TaintStatus.QUARANTINED)
            self.assertIsNotNone(response.poison)
            self.assertIn("secret_request", response.poison.labels)

    def test_quarantined_session_denies_sensitive_read(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = self.make_gateway(tmp)
            gateway.call_tool(
                ToolCallRequest(
                    session_id="s2",
                    tool_name="search_api",
                    arguments={"variant": "poisoned"},
                    context_source="external_api",
                )
            )
            denied = gateway.call_tool(
                ToolCallRequest(
                    session_id="s2",
                    tool_name="read_secret",
                    arguments={"path": "agentguard/demo_data/benign/.env"},
                    context_source="external_api",
                )
            )
            self.assertEqual(denied.decision, Decision.DENY)
            self.assertIsNone(denied.output)

    def test_benign_task_can_write_report(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = self.make_gateway(tmp)
            response = gateway.call_tool(
                ToolCallRequest(
                    session_id="s3",
                    tool_name="write_report",
                    arguments={
                        "path": str(Path(tmp) / "test_report.md"),
                        "content": "hello",
                    },
                    context_source="user",
                )
            )
            self.assertEqual(response.decision, Decision.ALLOW)
            self.assertEqual(response.taint_status, TaintStatus.TRUSTED)

    def test_external_context_marks_untrusted_before_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = self.make_gateway(tmp)
            response = gateway.call_tool(
                ToolCallRequest(
                    session_id="s4",
                    tool_name="send_external",
                    arguments={"url": "https://partner.example/collect", "message": "hello"},
                    context_source="external_api",
                )
            )
            self.assertEqual(response.decision, Decision.DENY)
            self.assertEqual(response.taint_status, TaintStatus.UNTRUSTED)
            events = gateway.audit_logger.list_events(session_id="s4", limit=10)
            self.assertTrue(any(event.event_type == "taint_transition" for event in events))

    def test_reset_to_trusted_records_transition(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = self.make_gateway(tmp)
            gateway.taint_engine.mark_external_content("s5", "external_api")
            gateway.taint_engine.reset_to_trusted("s5", "test reset")
            self.assertEqual(gateway.taint_engine.get_status("s5"), TaintStatus.TRUSTED)
            events = gateway.audit_logger.list_events(session_id="s5", limit=10)
            self.assertTrue(
                any(event.decision == "reset" and event.taint_after == TaintStatus.TRUSTED for event in events)
            )

    def test_confirm_only_upgrades_confirm_decisions(self) -> None:
        engine = PolicyEngine()
        confirmed_sensitive = engine.decide(
            TaintStatus.UNTRUSTED,
            ToolCategory.SENSITIVE_READ,
            confirmed=True,
        )
        confirmed_external = engine.decide(
            TaintStatus.UNTRUSTED,
            ToolCategory.EXTERNAL_SEND,
            confirmed=True,
        )
        self.assertEqual(confirmed_sensitive.decision, Decision.ALLOW)
        self.assertIn("manual_override", confirmed_sensitive.risk_factors)
        self.assertEqual(confirmed_external.decision, Decision.DENY)

    def test_default_audit_db_uses_temp_directory(self) -> None:
        logger = AuditLogger()
        self.assertEqual(logger.db_path, default_audit_db_path())
        self.assertNotIn(str(ROOT / "agentguard" / "backend"), str(logger.db_path))


class PoisoningDetectorTests(unittest.TestCase):
    def test_clean_external_content_is_untrusted_not_trusted(self) -> None:
        detector = PoisoningDetector()
        result = detector.detect("search_api", "search", "天气晴朗，资料正常。")
        self.assertEqual(result.taint_status, TaintStatus.UNTRUSTED)
        self.assertEqual(result.poison_score, 0)


if __name__ == "__main__":
    unittest.main()
