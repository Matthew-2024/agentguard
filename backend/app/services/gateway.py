from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from agentguard.backend.app.demo.tools import register_demo_tools
from agentguard.backend.app.models import (
    AuditEvent,
    Decision,
    GatewayResponse,
    PolicyDecisionResult,
    RuntimeEvidence,
    ToolCallRequest,
    ToolManifest,
    TaintStatus,
)
from agentguard.backend.app.services.audit_logger import AuditLogger, default_audit_db_path
from agentguard.backend.app.services.consistency_analyzer import ConsistencyAnalyzer
from agentguard.backend.app.services.execution_proxy import ExecutionProxy
from agentguard.backend.app.services.poisoning_detector import PoisoningDetector
from agentguard.backend.app.services.policy_engine import PolicyEngine
from agentguard.backend.app.services.supply_chain_scanner import SupplyChainScanner
from agentguard.backend.app.services.taint_engine import TaintEngine

LOCAL_CONTEXT_SOURCES = {"user", "local", "trusted", "agent"}
SENSITIVE_MARKERS = ("secret", "token", "password", "api_key", "apikey", "authorization", ".env")


class AgentGuardGateway:
    """Unified Agent -> Gateway -> Tool -> Postcheck execution path."""

    def __init__(
        self,
        workspace_root: str | Path,
        audit_db_path: str | Path | None = None,
        manifest_dir: str | Path | None = None,
        enforce_consistency_precheck: bool = False,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.enforce_consistency_precheck = enforce_consistency_precheck
        self.audit_logger = AuditLogger(audit_db_path or default_audit_db_path())
        self.taint_engine = TaintEngine(self.audit_logger)
        self.policy_engine = PolicyEngine()
        self.poisoning_detector = PoisoningDetector()
        self.execution_proxy = ExecutionProxy(self.workspace_root)
        register_demo_tools(self.execution_proxy)
        self.manifest_dir = Path(manifest_dir or self.workspace_root / "agentguard" / "backend" / "manifests")
        self.scanner = SupplyChainScanner(self.manifest_dir)
        self.consistency_analyzer = ConsistencyAnalyzer()

    def call_tool(self, request: ToolCallRequest) -> GatewayResponse:
        manifest = self.scanner.load_manifest(request.tool_name)
        audit_event_ids: List[int] = []
        taint_before = self.taint_engine.get_status(request.session_id)
        if request.context_source not in LOCAL_CONTEXT_SOURCES:
            taint_before, transition_event_id = self.taint_engine.mark_external_content(
                request.session_id,
                source=request.context_source,
                suggested_status=TaintStatus.UNTRUSTED,
                reason="外部来源内容进入上下文",
            )
            if transition_event_id is not None:
                audit_event_ids.append(transition_event_id)

        consistency_gate = self._consistency_precheck(manifest) if self.enforce_consistency_precheck else None
        if consistency_gate is not None:
            report, decision = consistency_gate
            audit_event_ids.append(
                self.audit_logger.record(
                    AuditEvent(
                        session_id=request.session_id,
                        event_type="consistency_precheck",
                        tool_name=request.tool_name,
                        taint_before=taint_before,
                        taint_after=taint_before,
                        decision=decision,
                        metadata=report.model_dump(mode="json"),
                    )
                )
            )
            if decision == Decision.DENY.value:
                return GatewayResponse(
                    session_id=request.session_id,
                    tool_name=request.tool_name,
                    decision=Decision.DENY,
                    output=None,
                    taint_status=taint_before,
                    policy=PolicyDecisionResult(
                        decision=Decision.DENY,
                        rule_matched="consistency_precheck",
                        reasoning="工具静态行为与 manifest 存在高风险偏差",
                        risk_factors=["consistency_precheck", report.risk_level],
                    ),
                    runtime_evidence=RuntimeEvidence(),
                    audit_event_ids=audit_event_ids,
                )

        policy = self.policy_engine.decide(
            taint_before,
            manifest.category,
            confirmed=request.confirmed,
        )

        audit_event_ids.append(
            self.audit_logger.record(
                AuditEvent(
                    session_id=request.session_id,
                    event_type="precheck",
                    tool_name=request.tool_name,
                    taint_before=taint_before,
                    taint_after=taint_before,
                    decision=policy.decision.value,
                    metadata={
                        "tool_category": manifest.category.value,
                        "context_source": request.context_source,
                        "arguments_summary": _summarize_args(request.arguments),
                        "rule_matched": policy.rule_matched,
                    },
                )
            )
        )

        if policy.decision != Decision.ALLOW:
            return GatewayResponse(
                session_id=request.session_id,
                tool_name=request.tool_name,
                decision=policy.decision,
                output=None,
                taint_status=taint_before,
                policy=policy,
                runtime_evidence=RuntimeEvidence(),
                audit_event_ids=audit_event_ids,
            )

        output, evidence = self.execution_proxy.execute(request.tool_name, request.arguments)
        audit_event_ids.append(
            self.audit_logger.record(
                AuditEvent(
                    session_id=request.session_id,
                    event_type="runtime_evidence",
                    tool_name=request.tool_name,
                    taint_before=taint_before,
                    taint_after=taint_before,
                    decision="observed",
                    metadata=_redact_metadata(evidence.model_dump()),
                )
            )
        )

        poison = None
        taint_after = taint_before
        if manifest.returns_external_content or request.context_source not in LOCAL_CONTEXT_SOURCES:
            poison = self.poisoning_detector.detect(
                request.tool_name,
                manifest.description,
                output,
            )
            taint_after, transition_event_id = self.taint_engine.mark_external_content(
                request.session_id,
                source=request.context_source,
                suggested_status=poison.taint_status,
                reason=poison.reasoning,
            )
            if transition_event_id is not None:
                audit_event_ids.append(transition_event_id)

        audit_event_ids.append(
            self.audit_logger.record(
                AuditEvent(
                    session_id=request.session_id,
                    event_type="postcheck",
                    tool_name=request.tool_name,
                    taint_before=taint_before,
                    taint_after=taint_after,
                    decision=poison.decision.value if poison else "pass",
                    metadata={
                        "poison": poison.model_dump() if poison else None,
                        "output_summary": _redact_text(output[:240]),
                    },
                )
            )
        )

        return GatewayResponse(
            session_id=request.session_id,
            tool_name=request.tool_name,
            decision=policy.decision,
            output=output,
            taint_status=taint_after,
            policy=policy,
            poison=poison,
            runtime_evidence=evidence,
            audit_event_ids=audit_event_ids,
        )

    def audit_tool_consistency(
        self,
        tool_name: str,
        source_path: str | Path,
        runtime_evidence: RuntimeEvidence | None = None,
    ):
        manifest = self.scanner.load_manifest(tool_name)
        static = self.scanner.scan_entrypoint(source_path, manifest.entrypoint)
        return self.consistency_analyzer.analyze(manifest, static, runtime_evidence)

    def list_manifests(self) -> Iterable[ToolManifest]:
        return self.scanner.list_manifests()

    def _consistency_precheck(self, manifest: ToolManifest):
        source_path = self._source_path_for_manifest(manifest)
        static = self.scanner.scan_entrypoint(source_path, manifest.entrypoint)
        report = self.consistency_analyzer.analyze(manifest, static, RuntimeEvidence())
        decision = Decision.DENY.value if report.risk_level in {"high", "critical"} else "pass"
        return report, decision

    def _source_path_for_manifest(self, manifest: ToolManifest) -> Path:
        return self.workspace_root / "agentguard" / "backend" / "app" / "demo" / "tools.py"


def _summarize_args(arguments: dict) -> dict:
    summary = {}
    for key, value in arguments.items():
        if _is_sensitive(str(key)) or _is_sensitive(str(value)):
            summary[key] = "[redacted]"
            continue
        text = str(value)
        summary[key] = text if len(text) <= 80 else f"{text[:77]}..."
    return summary


def _redact_metadata(value):
    if isinstance(value, dict):
        return {
            key: "[redacted]" if _is_sensitive(str(key)) else _redact_metadata(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_metadata(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _redact_text(value: str) -> str:
    return "[redacted]" if _is_sensitive(value) else value


def _is_sensitive(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SENSITIVE_MARKERS)
