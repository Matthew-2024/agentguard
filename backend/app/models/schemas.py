from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaintStatus(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    TAINTED = "tainted"
    QUARANTINED = "quarantined"


class Decision(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


class PostcheckDecision(str, Enum):
    PASS = "pass"
    FLAG = "flag"
    QUARANTINE = "quarantine"


class ToolCategory(str, Enum):
    SAFE_READ = "safe_read"
    SENSITIVE_READ = "sensitive_read"
    SAFE_WRITE = "safe_write"
    SENSITIVE_WRITE = "sensitive_write"
    INTERNAL_NOTIFY = "internal_notify"
    EXTERNAL_SEND = "external_send"
    EXECUTE = "execute"


class ToolManifest(BaseModel):
    name: str
    description: str
    category: ToolCategory
    entrypoint: str
    permissions: List[str] = Field(default_factory=list)
    allowed_paths: List[str] = Field(default_factory=list)
    allowed_domains: List[str] = Field(default_factory=list)
    parameter_schema: Dict[str, Any] = Field(default_factory=dict)
    returns_external_content: bool = False
    hash_baseline: Optional[str] = None


class ToolCallRequest(BaseModel):
    session_id: str = "default"
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    context_source: str = "user"
    confirmed: bool = False


class PoisoningResult(BaseModel):
    poison_score: int
    labels: List[str] = Field(default_factory=list)
    taint_status: TaintStatus
    decision: PostcheckDecision
    reasoning: str


class PolicyDecisionResult(BaseModel):
    decision: Decision
    rule_matched: str
    reasoning: str
    risk_factors: List[str] = Field(default_factory=list)


class RuntimeEvidence(BaseModel):
    paths: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    requests: List[Dict[str, Any]] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    output_summary: str = ""


class StaticScanResult(BaseModel):
    file_ops: List[str] = Field(default_factory=list)
    network_calls: List[str] = Field(default_factory=list)
    subprocess: List[str] = Field(default_factory=list)
    sensitive_strings: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)


class ConsistencyDeviation(BaseModel):
    type: str
    layer_a: str
    layer_b: str
    evidence: str
    severity: str


class ConsistencyReport(BaseModel):
    consistency_score: int
    deviations: List[ConsistencyDeviation] = Field(default_factory=list)
    risk_level: str
    summary: str


class AuditEvent(BaseModel):
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=utc_now)
    session_id: str
    event_type: str
    tool_name: Optional[str] = None
    taint_before: Optional[TaintStatus] = None
    taint_after: Optional[TaintStatus] = None
    decision: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionSnapshot(BaseModel):
    session_id: str
    taint_status: TaintStatus = TaintStatus.TRUSTED
    updated_at: datetime = Field(default_factory=utc_now)


class GatewayResponse(BaseModel):
    session_id: str
    tool_name: str
    decision: Decision
    output: Optional[str] = None
    taint_status: TaintStatus
    policy: PolicyDecisionResult
    poison: Optional[PoisoningResult] = None
    runtime_evidence: RuntimeEvidence = Field(default_factory=RuntimeEvidence)
    audit_event_ids: List[int] = Field(default_factory=list)

