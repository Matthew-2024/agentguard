from __future__ import annotations

from pathlib import Path

from agentguard.backend.app.models import ToolCallRequest
from agentguard.backend.app.services.gateway import AgentGuardGateway

try:
    from fastapi import APIRouter, Depends
except ImportError:  # pragma: no cover - lets service tests run without FastAPI installed.
    APIRouter = None  # type: ignore
    Depends = None  # type: ignore


ROOT = Path(__file__).resolve().parents[4]


def get_gateway() -> AgentGuardGateway:
    return AgentGuardGateway(ROOT)


if APIRouter is not None:
    router = APIRouter(prefix="/gateway", tags=["gateway"])

    @router.post("/call")
    def call_tool(
        request: ToolCallRequest,
        gateway: AgentGuardGateway = Depends(get_gateway),
    ):
        return gateway.call_tool(request)

    @router.post("/sessions/{session_id}/reset")
    def reset_session(
        session_id: str,
        gateway: AgentGuardGateway = Depends(get_gateway),
    ):
        event_id = gateway.taint_engine.reset_to_trusted(session_id)
        return {
            "session_id": session_id,
            "taint_status": "trusted",
            "audit_event_id": event_id,
        }

else:
    router = None
