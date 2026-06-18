from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

from agentguard.backend.app.models import AuditEvent
from agentguard.backend.app.services.audit_logger import AuditLogger


def generate_session_report(
    session_id: str,
    audit_logger: AuditLogger | None = None,
    limit: int = 300,
) -> dict:
    logger = audit_logger or AuditLogger()
    events = list(reversed(logger.list_events(session_id=session_id, limit=limit)))
    return _build_report(session_id, events)


def generate_latest_report(
    audit_logger: AuditLogger | None = None,
    limit: int = 300,
) -> dict:
    logger = audit_logger or AuditLogger()
    latest_events = logger.list_events(limit=1)
    if not latest_events:
        return _build_report("none", [])
    return generate_session_report(latest_events[0].session_id, logger, limit=limit)


def write_report_markdown(
    report: dict,
    output_dir: str | Path,
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    session_id = _safe_filename(str(report["session_id"]))
    path = output_path / f"agentguard_report_{session_id}.md"
    path.write_text(str(report["markdown"]), encoding="utf-8")
    return path


def _build_report(session_id: str, events: list[AuditEvent]) -> dict:
    decisions = Counter(event.decision or "unknown" for event in events)
    event_types = Counter(event.event_type for event in events)
    tools = Counter(event.tool_name or "session" for event in events)
    taint_states = Counter(
        event.taint_after.value
        for event in events
        if event.taint_after is not None
    )
    summary = {
        "event_count": len(events),
        "decisions": dict(sorted(decisions.items())),
        "event_types": dict(sorted(event_types.items())),
        "tools": dict(tools.most_common(8)),
        "taint_states": dict(sorted(taint_states.items())),
        "risk_events": sum(1 for event in events if _is_risk_event(event)),
    }
    payload_events = [_event_payload(event) for event in events]
    report = {
        "session_id": session_id,
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "events": payload_events,
    }
    report["markdown"] = _markdown(report)
    return report


def _event_payload(event: AuditEvent) -> dict:
    return {
        "id": event.id,
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "tool_name": event.tool_name,
        "taint_before": event.taint_before.value if event.taint_before else None,
        "taint_after": event.taint_after.value if event.taint_after else None,
        "decision": event.decision,
        "metadata": event.metadata,
    }


def _markdown(report: dict) -> str:
    lines = [
        "# AgentGuard Session Report",
        "",
        f"- Session: `{report['session_id']}`",
        f"- Generated at: `{report['generated_at']}`",
        f"- Event count: `{report['summary']['event_count']}`",
        f"- Risk events: `{report['summary']['risk_events']}`",
        "",
        "## Summary",
        "",
        _table("Decision", report["summary"]["decisions"].items()),
        "",
        _table("Event Type", report["summary"]["event_types"].items()),
        "",
        "## Timeline",
        "",
        "| # | Time | Event | Tool | Decision | Taint |",
        "|---:|---|---|---|---|---|",
    ]
    for index, event in enumerate(report["events"], start=1):
        taint = event["taint_after"] or event["taint_before"] or "-"
        lines.append(
            "| "
            f"{index} | "
            f"{_escape(event['timestamp'])} | "
            f"{_escape(event['event_type'])} | "
            f"{_escape(event['tool_name'] or 'session')} | "
            f"{_escape(event['decision'] or '-')} | "
            f"{_escape(taint)} |"
        )
    return "\n".join(lines) + "\n"


def _table(label: str, items: Iterable[tuple[str, object]]) -> str:
    lines = [
        f"| {label} | Count |",
        "|---|---:|",
    ]
    for key, value in items:
        lines.append(f"| `{_escape(str(key))}` | {value} |")
    if len(lines) == 2:
        lines.append("| `none` | 0 |")
    return "\n".join(lines)


def _is_risk_event(event: AuditEvent) -> bool:
    decision = event.decision or ""
    metadata_text = str(event.metadata).lower()
    return (
        decision in {"deny", "confirm", "flag", "quarantine"}
        or "critical" in metadata_text
        or "quarantined" in metadata_text
    )


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)[:80]
