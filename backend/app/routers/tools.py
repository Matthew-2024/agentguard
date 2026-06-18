from __future__ import annotations

from pathlib import Path

from agentguard.backend.app.services.gateway import AgentGuardGateway

try:
    from fastapi import APIRouter
except ImportError:  # pragma: no cover
    APIRouter = None  # type: ignore


ROOT = Path(__file__).resolve().parents[4]


if APIRouter is not None:
    router = APIRouter(prefix="/tools", tags=["tools"])

    @router.get("/manifests")
    def list_manifests():
        gateway = AgentGuardGateway(ROOT)
        return list(gateway.list_manifests())

    @router.get("/{tool_name}/consistency")
    def audit_tool(tool_name: str):
        gateway = AgentGuardGateway(ROOT)
        source_path = ROOT / "agentguard" / "backend" / "app" / "demo" / "tools.py"
        return gateway.audit_tool_consistency(tool_name, source_path)

else:
    router = None

