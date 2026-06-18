from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from agentguard.backend.app.demo.benchmark import run_full_benchmark
from agentguard.backend.app.demo.live_demo import run_live_demo
from agentguard.backend.app.demo.baseline_eval import run_baseline_eval
from agentguard.backend.app.demo.scenarios import SCENARIOS, get_scenario
from agentguard.backend.app.models import ToolCallRequest
from agentguard.backend.app.services.gateway import AgentGuardGateway
from agentguard.backend.app.services.multi_agent import judge_delegation

try:
    from fastapi import APIRouter
except ImportError:  # pragma: no cover
    APIRouter = None  # type: ignore


ROOT = Path(__file__).resolve().parents[4]


if APIRouter is not None:
    router = APIRouter(prefix="/demo", tags=["demo"])

    @router.get("/scenarios")
    def list_scenarios():
        return SCENARIOS

    @router.post("/scenarios/{scenario_id}/run")
    def run_scenario(scenario_id: str):
        scenario = get_scenario(scenario_id)
        session_id = f"{scenario_id}-{uuid4().hex[:8]}"
        gateway = AgentGuardGateway(ROOT)
        responses = []
        for step in scenario.steps:
            responses.append(
                gateway.call_tool(
                    ToolCallRequest(
                        session_id=session_id,
                        tool_name=step.tool_name,
                        arguments=step.arguments,
                        context_source=step.context_source,
                        confirmed=step.confirmed,
                    )
                )
            )
        payload = {"scenario": scenario, "session_id": session_id, "responses": responses}
        if scenario_id == "tampered_tool_consistency" and responses:
            payload["consistency_report"] = gateway.audit_tool_consistency(
                "weather_query_tampered",
                ROOT / "agentguard" / "demo_data" / "tampered_tools" / "weather_tampered.py",
                responses[0].runtime_evidence,
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

    @router.post("/live/run")
    def run_live_demo_route():
        return run_live_demo(ROOT)

    @router.post("/evaluation/run")
    def run_evaluation():
        return run_baseline_eval(ROOT)

    @router.post("/benchmark/run")
    def run_benchmark_route(repetitions: int = 10, pressure_iterations: int = 200):
        return run_full_benchmark(
            ROOT,
            repetitions=max(1, min(repetitions, 50)),
            pressure_iterations=max(1, min(pressure_iterations, 5000)),
        )

else:
    router = None
