from __future__ import annotations

from pydantic import BaseModel, Field

from agentguard.backend.app.models import TaintStatus
from agentguard.backend.app.services.multi_agent import judge_delegation

try:
    from fastapi import APIRouter
except ImportError:  # pragma: no cover
    APIRouter = None  # type: ignore


class DelegationRequest(BaseModel):
    parent_taint: TaintStatus
    parent_permissions: list[str] = Field(default_factory=list)
    child_permissions: list[str] = Field(default_factory=list)
    delegated_context_status: TaintStatus


if APIRouter is not None:
    router = APIRouter(prefix="/multi-agent", tags=["multi-agent"])

    @router.post("/delegate")
    def delegate(request: DelegationRequest):
        return judge_delegation(
            parent_taint=request.parent_taint,
            parent_permissions=request.parent_permissions,
            child_permissions=request.child_permissions,
            delegated_context_status=request.delegated_context_status,
        )

else:
    router = None
