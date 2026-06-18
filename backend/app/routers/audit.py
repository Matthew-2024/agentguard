from __future__ import annotations

from typing import Optional

from agentguard.backend.app.services.audit_logger import AuditLogger

try:
    from fastapi import APIRouter
except ImportError:  # pragma: no cover
    APIRouter = None  # type: ignore


if APIRouter is not None:
    router = APIRouter(prefix="/audit", tags=["audit"])

    @router.get("/events")
    def list_events(session_id: Optional[str] = None, limit: int = 100):
        logger = AuditLogger()
        return logger.list_events(session_id=session_id, limit=limit)

else:
    router = None
