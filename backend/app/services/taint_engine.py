from __future__ import annotations

from agentguard.backend.app.models import AuditEvent, TaintStatus
from agentguard.backend.app.services.audit_logger import AuditLogger


_TAINT_RANK = {
    TaintStatus.TRUSTED: 0,
    TaintStatus.UNTRUSTED: 1,
    TaintStatus.TAINTED: 2,
    TaintStatus.QUARANTINED: 3,
}


class TaintEngine:
    """Session-level taint state machine for AgentGuard MVP."""

    def __init__(self, audit_logger: AuditLogger) -> None:
        self.audit_logger = audit_logger

    def get_status(self, session_id: str) -> TaintStatus:
        return self.audit_logger.get_session_taint(session_id)

    def mark_external_content(
        self,
        session_id: str,
        source: str,
        suggested_status: TaintStatus = TaintStatus.UNTRUSTED,
        reason: str = "external content entered context",
    ) -> tuple[TaintStatus, int | None]:
        current = self.get_status(session_id)
        next_status = max_status(current, suggested_status)
        event_id: int | None = None
        if next_status != current:
            self.audit_logger.set_session_taint(session_id, next_status)
            event_id = self.audit_logger.record(
                AuditEvent(
                    session_id=session_id,
                    event_type="taint_transition",
                    taint_before=current,
                    taint_after=next_status,
                    decision="update",
                    metadata={"source": source, "reason": reason},
                )
            )
        return next_status, event_id

    def reset_to_trusted(self, session_id: str, reason: str = "manual reset") -> int:
        current = self.get_status(session_id)
        self.audit_logger.set_session_taint(session_id, TaintStatus.TRUSTED)
        return self.audit_logger.record(
            AuditEvent(
                session_id=session_id,
                event_type="taint_transition",
                taint_before=current,
                taint_after=TaintStatus.TRUSTED,
                decision="reset",
                metadata={"reason": reason},
            )
        )


def max_status(left: TaintStatus, right: TaintStatus) -> TaintStatus:
    return left if _TAINT_RANK[left] >= _TAINT_RANK[right] else right

