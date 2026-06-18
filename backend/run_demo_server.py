from __future__ import annotations

import json
import argparse
import sys
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentguard.backend.app.demo.benchmark import run_full_benchmark
from agentguard.backend.app.demo.baseline_eval import run_baseline_eval
from agentguard.backend.app.demo.live_demo import run_live_demo
from agentguard.backend.app.demo.scenarios import SCENARIOS, get_scenario
from agentguard.backend.app.models import RuntimeEvidence, TaintStatus, ToolCallRequest
from agentguard.backend.app.services.audit_logger import AuditLogger, default_audit_db_path
from agentguard.backend.app.services.gateway import AgentGuardGateway
from agentguard.backend.app.services.multi_agent import judge_delegation
from agentguard.backend.app.services.report_generator import generate_latest_report, generate_session_report



class DemoRequestHandler(BaseHTTPRequestHandler):
    server_version = "AgentGuardDemo/0.1"

    def do_OPTIONS(self) -> None:
        self._send_empty(204)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/demo/scenarios":
            self._send_json([asdict(scenario) for scenario in SCENARIOS])
            return
        if parsed.path == "/health":
            self._send_json({"status": "ok"})
            return
        if parsed.path == "/audit/events":
            query = parse_qs(parsed.query)
            session_id = query.get("session_id", [None])[0]
            limit = int(query.get("limit", ["100"])[0])
            self._send_json(
                [
                    _model_dump(event)
                    for event in AuditLogger(default_audit_db_path()).list_events(
                        session_id=session_id,
                        limit=limit,
                    )
                ]
            )
            return
        if parsed.path == "/tools/manifests":
            gateway = AgentGuardGateway(ROOT)
            self._send_json([_model_dump(manifest) for manifest in gateway.list_manifests()])
            return
        if parsed.path.startswith("/tools/") and parsed.path.endswith("/consistency"):
            tool_name = parsed.path.removeprefix("/tools/").removesuffix("/consistency").strip("/")
            self._send_json(_tool_consistency_payload(tool_name))
            return
        if parsed.path == "/report/latest":
            self._send_json(generate_latest_report())
            return
        if parsed.path == "/report/latest.md":
            self._send_text(generate_latest_report()["markdown"])
            return
        if parsed.path.startswith("/report/session/"):
            session_part = parsed.path.removeprefix("/report/session/").strip("/")
            as_markdown = session_part.endswith(".md")
            session_id = session_part.removesuffix(".md")
            report = generate_session_report(session_id)
            if as_markdown:
                self._send_text(report["markdown"])
            else:
                self._send_json(report)
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/demo/live/run":
            self._send_json(run_live_demo(ROOT))
            return
        if parsed.path == "/demo/evaluation/run":
            self._send_json(run_baseline_eval(ROOT))
            return
        if parsed.path == "/demo/benchmark/run":
            query = parse_qs(parsed.query)
            repetitions = int(query.get("repetitions", ["10"])[0])
            pressure_iterations = int(query.get("pressure_iterations", ["200"])[0])
            self._send_json(
                run_full_benchmark(
                    ROOT,
                    repetitions=max(1, min(repetitions, 50)),
                    pressure_iterations=max(1, min(pressure_iterations, 5000)),
                )
            )
            return
        if parsed.path.startswith("/demo/scenarios/") and parsed.path.endswith("/run"):
            scenario_id = parsed.path.removeprefix("/demo/scenarios/").removesuffix("/run").strip("/")
            self._send_json(_run_scenario_payload(scenario_id))
            return
        if parsed.path == "/multi-agent/delegate":
            payload = self._read_json()
            self._send_json(
                judge_delegation(
                    parent_taint=TaintStatus(payload.get("parent_taint", "trusted")),
                    parent_permissions=list(payload.get("parent_permissions", [])),
                    child_permissions=list(payload.get("child_permissions", [])),
                    delegated_context_status=TaintStatus(payload.get("delegated_context_status", "trusted")),
                )
            )
            return
        self._send_json({"error": "not found"}, status=404)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[demo-server] {self.address_string()} {format % args}")

    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, payload: str, status: int = 200) -> None:
        body = payload.encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, status: int) -> None:
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}


def _run_scenario_payload(scenario_id: str) -> dict:
    scenario = get_scenario(scenario_id)
    session_id = f"{scenario_id}-{uuid4().hex[:8]}"
    gateway = AgentGuardGateway(ROOT)
    responses = [
        gateway.call_tool(
            ToolCallRequest(
                session_id=session_id,
                tool_name=step.tool_name,
                arguments=step.arguments,
                context_source=step.context_source,
                confirmed=step.confirmed,
            )
        )
        for step in scenario.steps
    ]
    payload = {
        "scenario": asdict(scenario),
        "session_id": session_id,
        "responses": [_model_dump(response) for response in responses],
    }
    if scenario_id == "tampered_tool_consistency" and responses:
        payload["consistency_report"] = _model_dump(
            gateway.audit_tool_consistency(
                "weather_query_tampered",
                ROOT / "agentguard" / "demo_data" / "tampered_tools" / "weather_tampered.py",
                responses[0].runtime_evidence,
            )
        )
    if scenario_id == "multi_agent_taint_propagation":
        inherited_taint = gateway.taint_engine.get_status(session_id)
        payload["delegation"] = judge_delegation(
            parent_taint=inherited_taint,
            parent_permissions=["safe_read", "safe_write", "internal_notify"],
            child_permissions=["safe_read", "sensitive_read", "external_send"],
            delegated_context_status=inherited_taint,
        )
    return payload


def _tool_consistency_payload(tool_name: str) -> dict:
    gateway = AgentGuardGateway(ROOT)
    source_path = ROOT / "agentguard" / "backend" / "app" / "demo" / "tools.py"
    runtime = None
    if tool_name == "weather_query_tampered":
        response = gateway.call_tool(
            ToolCallRequest(
                session_id=f"consistency-{uuid4().hex[:8]}",
                tool_name=tool_name,
                arguments={"city": "Hangzhou"},
                context_source="user",
            )
        )
        runtime = response.runtime_evidence
        source_path = ROOT / "agentguard" / "demo_data" / "tampered_tools" / "weather_tampered.py"
    elif tool_name == "weather_query":
        runtime = RuntimeEvidence(domains=["api.weather.local"], permissions=["network"])
    return _model_dump(gateway.audit_tool_consistency(tool_name, source_path, runtime))


def _model_dump(value: object) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")  # type: ignore[no-any-return]
    return value


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), DemoRequestHandler)
    print(f"AgentGuard demo server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AgentGuard standard-library demo server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(args.host, args.port)
