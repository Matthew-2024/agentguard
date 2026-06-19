from __future__ import annotations

import os
import unittest
from unittest import mock
from pathlib import Path
from tempfile import TemporaryDirectory

from agentguard.backend.app.models import Decision, TaintStatus, ToolCallRequest, ToolCategory
from agentguard.backend.app.services.audit_logger import AuditLogger, default_audit_db_path
from agentguard.backend.app.services.execution_proxy import ExecutionContext
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
            report_path = ROOT / "agentguard" / "tmp-runtime" / "test_report.md"
            response = gateway.call_tool(
                ToolCallRequest(
                    session_id="s3",
                    tool_name="write_report",
                    arguments={
                        "path": str(report_path),
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
            self.assertEqual(response.decision, Decision.CONFIRM)
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
        self.assertEqual(confirmed_external.decision, Decision.ALLOW)

    def test_default_audit_db_uses_persistent_home_directory(self) -> None:
        old = os.environ.pop("AGENTGUARD_DB", None)
        try:
            path = default_audit_db_path()
            self.assertEqual(path, Path.home() / ".agentguard" / "agentguard_audit.db")
        finally:
            if old is not None:
                os.environ["AGENTGUARD_DB"] = old

    def test_env_can_override_default_audit_db_path(self) -> None:
        with TemporaryDirectory() as tmp:
            old = os.environ.get("AGENTGUARD_DB")
            os.environ["AGENTGUARD_DB"] = str(Path(tmp) / "audit.db")
            try:
                logger = AuditLogger()
                self.assertEqual(logger.db_path, default_audit_db_path())
                self.assertNotIn(str(ROOT / "agentguard" / "backend"), str(logger.db_path))
            finally:
                if old is None:
                    os.environ.pop("AGENTGUARD_DB", None)
                else:
                    os.environ["AGENTGUARD_DB"] = old

    def test_execution_context_denies_paths_outside_workspace(self) -> None:
        context = ExecutionContext(workspace_root=ROOT)

        with self.assertRaises(PermissionError):
            context.read_file(str(ROOT.parent / "outside.txt"))

    def test_execution_context_denies_oversized_reads(self) -> None:
        context = ExecutionContext(workspace_root=ROOT)
        target = ROOT / "agentguard" / "demo_data" / "benign" / "public_note.md"

        with mock.patch.object(Path, "stat") as stat:
            stat.return_value.st_size = 101 * 1024 * 1024
            with self.assertRaises(ValueError):
                context.read_file(str(target))

    def test_execution_context_denies_oversized_writes(self) -> None:
        context = ExecutionContext(workspace_root=ROOT)

        with self.assertRaises(ValueError):
            context.write_file("agentguard/tmp-runtime/too-large.txt", "x" * (101 * 1024 * 1024))


class PoisoningDetectorTests(unittest.TestCase):
    def test_clean_external_content_is_untrusted_not_trusted(self) -> None:
        detector = PoisoningDetector()
        result = detector.detect("search_api", "search", "天气晴朗，资料正常。")
        self.assertEqual(result.taint_status, TaintStatus.UNTRUSTED)
        self.assertEqual(result.poison_score, 0)


if __name__ == "__main__":
    unittest.main()
