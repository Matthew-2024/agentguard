from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentguard.backend.app.demo.scenarios import get_scenario
from agentguard.backend.app.models import ToolCallRequest
from agentguard.backend.app.services.audit_logger import AuditLogger
from agentguard.backend.app.services.gateway import AgentGuardGateway
from agentguard.backend.app.services.report_generator import (
    generate_latest_report,
    generate_session_report,
    write_report_markdown,
)


ROOT = Path(__file__).resolve().parents[3]


class ReportGeneratorTests(unittest.TestCase):
    def test_session_report_contains_summary_and_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = AgentGuardGateway(ROOT, audit_db_path=Path(tmp) / "audit.db")
            scenario = get_scenario("poisoned_api_triggers_taint")
            session_id = "report-poisoned"
            for step in scenario.steps:
                gateway.call_tool(
                    ToolCallRequest(
                        session_id=session_id,
                        tool_name=step.tool_name,
                        arguments=step.arguments,
                        context_source=step.context_source,
                        confirmed=step.confirmed,
                    )
                )

            report = generate_session_report(session_id, AuditLogger(Path(tmp) / "audit.db"))

            self.assertEqual(report["session_id"], session_id)
            self.assertGreater(report["summary"]["event_count"], 0)
            self.assertGreater(report["summary"]["risk_events"], 0)
            self.assertIn("# AgentGuard Session Report", report["markdown"])
            self.assertIn("## Timeline", report["markdown"])

    def test_latest_report_and_markdown_file_export(self) -> None:
        with TemporaryDirectory() as tmp:
            gateway = AgentGuardGateway(ROOT, audit_db_path=Path(tmp) / "audit.db")
            gateway.call_tool(
                ToolCallRequest(
                    session_id="report-latest",
                    tool_name="read_public_doc",
                    arguments={"path": "agentguard/demo_data/benign/public_note.md"},
                    context_source="user",
                )
            )

            report = generate_latest_report(AuditLogger(Path(tmp) / "audit.db"))
            path = write_report_markdown(report, Path(tmp) / "reports")

            self.assertEqual(report["session_id"], "report-latest")
            self.assertTrue(path.exists())
            self.assertIn("report-latest", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
