from __future__ import annotations

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import uuid4

from agentguard.backend.app.demo.baseline_eval import run_baseline_eval
from agentguard.backend.app.demo.scenarios import SCENARIOS, DemoScenario
from agentguard.backend.app.models import AuditEvent, GatewayResponse, RuntimeEvidence, ToolCallRequest
from agentguard.backend.app.services.audit_logger import default_audit_db_path
from agentguard.backend.app.services.gateway import AgentGuardGateway
from agentguard.backend.app.services.multi_agent import judge_delegation


ROOT = Path(__file__).resolve().parents[4]


def run_live_demo(
    workspace_root: str | Path = ROOT,
    audit_db_path: str | Path | None = None,
) -> dict:
    workspace_root = Path(workspace_root).resolve()
    run_id = f"live-{uuid4().hex[:8]}"

    with TemporaryDirectory() as tmp:
        gateway = AgentGuardGateway(workspace_root, audit_db_path=audit_db_path or default_audit_db_path())
        started = perf_counter()
        scenario_runs = [
            _run_scenario(gateway, scenario, f"{run_id}-{scenario.id}", Path(tmp))
            for scenario in SCENARIOS
        ]
        consistency_reports = _build_consistency_reports(workspace_root, gateway, scenario_runs)
        baseline = run_baseline_eval(workspace_root)
        latency_ms = round((perf_counter() - started) * 1000, 1)
        events = _collect_events(gateway, scenario_runs)
        taint_counts = _count_taint_states(scenario_runs)
        primary_session = _scenario_session(scenario_runs, "poisoned_api_triggers_taint") or scenario_runs[0]["session_id"]
        final_taint_status = gateway.taint_engine.get_status(primary_session)
        final_taint = final_taint_status.value

    return {
        "session_id": run_id,
        "primary_session_id": primary_session,
        "generated_at": _latest_event_time(events),
        "latency_ms": latency_ms,
        "final_taint": final_taint,
        "metrics": _build_metrics(scenario_runs, consistency_reports, baseline, latency_ms),
        "taint_counts": taint_counts,
        "scenario_runs": scenario_runs,
        "events": [_event_payload(event) for event in events],
        "consistency_reports": consistency_reports,
        "baseline": baseline,
        "delegation": judge_delegation(
            parent_taint=final_taint_status,
            parent_permissions=["safe_read", "safe_write", "internal_notify"],
            child_permissions=["safe_read", "sensitive_read", "external_send"],
            delegated_context_status=final_taint_status,
        ),
    }


def _run_scenario(
    gateway: AgentGuardGateway,
    scenario: DemoScenario,
    session_id: str,
    scratch_dir: Path,
) -> dict:
    responses: list[GatewayResponse] = []
    for step in scenario.steps:
        arguments = _demo_step_arguments(step.tool_name, step.arguments, scratch_dir)
        responses.append(
            gateway.call_tool(
                ToolCallRequest(
                    session_id=session_id,
                    tool_name=step.tool_name,
                    arguments=arguments,
                    context_source=step.context_source,
                    confirmed=step.confirmed,
                )
            )
        )

    return {
        "id": scenario.id,
        "title": scenario.title,
        "proves": scenario.proves,
        "session_id": session_id,
        "steps": [
            _response_payload(index=index + 1, response=response)
            for index, response in enumerate(responses)
        ],
    }


def _demo_step_arguments(tool_name: str, arguments: dict, scratch_dir: Path) -> dict:
    copied = dict(arguments)
    if tool_name == "write_report":
        copied["path"] = str(scratch_dir / "generated_report.md")
    return copied


def _build_consistency_reports(
    workspace_root: Path,
    gateway: AgentGuardGateway,
    scenario_runs: list[dict],
) -> list[dict]:
    tampered_response = _find_step(scenario_runs, "weather_query_tampered")
    tampered_runtime = (
        RuntimeEvidence(**tampered_response["runtime_evidence"])
        if tampered_response is not None
        else None
    )
    tool_specs = (
        (
            "weather_query",
            workspace_root / "agentguard" / "backend" / "app" / "demo" / "tools.py",
            RuntimeEvidence(domains=["api.weather.local"], permissions=["network"]),
        ),
        (
            "weather_query_tampered",
            workspace_root / "agentguard" / "demo_data" / "tampered_tools" / "weather_tampered.py",
            tampered_runtime,
        ),
        (
            "send_external",
            workspace_root / "agentguard" / "backend" / "app" / "demo" / "tools.py",
            None,
        ),
    )

    reports = []
    for tool_name, source_path, runtime in tool_specs:
        manifest = gateway.scanner.load_manifest(tool_name)
        static = gateway.scanner.scan_entrypoint(source_path, manifest.entrypoint)
        report = gateway.audit_tool_consistency(tool_name, source_path, runtime)
        reports.append(
            {
                "tool_name": tool_name,
                "display_name": _tool_display_name(tool_name),
                "manifest_summary": _manifest_summary(manifest.allowed_paths, manifest.allowed_domains),
                "static_summary": _static_summary(static.model_dump(mode="json")),
                "runtime_summary": _runtime_summary(runtime),
                "report": report.model_dump(mode="json"),
            }
        )
    return reports


def _find_step(scenario_runs: list[dict], tool_name: str) -> dict | None:
    for scenario in scenario_runs:
        for step in scenario["steps"]:
            if step["tool_name"] == tool_name:
                return step
    return None


def _scenario_session(scenario_runs: list[dict], scenario_id: str) -> str | None:
    for scenario in scenario_runs:
        if scenario["id"] == scenario_id:
            return str(scenario["session_id"])
    return None


def _collect_events(gateway: AgentGuardGateway, scenario_runs: list[dict]) -> list[AuditEvent]:
    events: list[AuditEvent] = []
    for scenario in scenario_runs:
        events.extend(
            gateway.audit_logger.list_events(session_id=scenario["session_id"], limit=100)
        )
    return sorted(events, key=lambda event: event.id or 0, reverse=True)


def _response_payload(index: int, response: GatewayResponse) -> dict:
    return {
        "index": index,
        "tool_name": response.tool_name,
        "display_name": _tool_display_name(response.tool_name),
        "decision": response.decision.value,
        "decision_label": _decision_label(response.decision.value),
        "taint_status": response.taint_status.value,
        "taint_label": _taint_label(response.taint_status.value),
        "policy_reasoning": response.policy.reasoning,
        "poison_labels": response.poison.labels if response.poison else [],
        "poison_decision": response.poison.decision.value if response.poison else "pass",
        "poison_score": response.poison.poison_score if response.poison else 0,
        "poison_reasoning": response.poison.reasoning if response.poison else "返回检查通过",
        "runtime_evidence": response.runtime_evidence.model_dump(mode="json"),
        "output_summary": response.runtime_evidence.output_summary or (response.output or "")[:160],
        "audit_event_ids": response.audit_event_ids,
    }


def _event_payload(event: AuditEvent) -> dict:
    return {
        "id": event.id,
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "event_label": _event_label(event.event_type),
        "tool_name": event.tool_name,
        "display_name": _tool_display_name(event.tool_name) if event.tool_name else "会话状态",
        "taint_before": event.taint_before.value if event.taint_before else None,
        "taint_after": event.taint_after.value if event.taint_after else None,
        "decision": event.decision,
        "decision_label": _decision_label(event.decision or ""),
        "metadata": event.metadata,
    }


def _build_metrics(
    scenario_runs: list[dict],
    consistency_reports: list[dict],
    baseline: dict,
    latency_ms: float,
) -> list[dict]:
    agentguard = _baseline_row(baseline, "agentguard")
    approval_only = _baseline_row(baseline, "approval_only")
    rule_only = _baseline_row(baseline, "rule_only")
    blocked = sum(
        1 for scenario in scenario_runs for step in scenario["steps"] if step["decision"] == "deny"
    )
    critical_reports = sum(
        1 for item in consistency_reports if item["report"]["risk_level"] == "critical"
    )
    return [
        {
            "label": "攻击拦截",
            "value": _ratio(agentguard.get("attack_interception_rate", 0), 3),
            "trend": f"比仅规则多拦 {max(0, round((agentguard.get('attack_interception_rate', 0) - rule_only.get('attack_interception_rate', 0)) * 3))} 个",
            "status": "success",
        },
        {
            "label": "正常任务完成",
            "value": _ratio(agentguard.get("benign_recoverable_completion_rate", 0), 4),
            "trend": f"立即放行 {agentguard.get('benign_task_completion_rate', 0) * 100:.0f}%",
            "status": "neutral",
        },
        {
            "label": "真实阻断",
            "value": str(blocked),
            "trend": "来自当前会话审计",
            "status": "danger" if blocked else "neutral",
        },
        {
            "label": "严重偏差",
            "value": str(critical_reports),
            "trend": f"{latency_ms:.0f} 毫秒完成回放",
            "status": "danger" if critical_reports else "success",
        },
    ]


def _baseline_row(baseline: dict, mode: str) -> dict:
    for row in baseline.get("rows", []):
        if row.get("mode") == mode:
            return row
    return {}


def _count_taint_states(scenario_runs: list[dict]) -> dict[str, int]:
    counts = Counter(
        step["taint_status"] for scenario in scenario_runs for step in scenario["steps"]
    )
    return {
        "trusted": counts["trusted"],
        "untrusted": counts["untrusted"],
        "tainted": counts["tainted"],
        "quarantined": counts["quarantined"],
    }


def _ratio(rate: object, denominator: int) -> str:
    value = float(rate or 0)
    return f"{round(value * denominator)}/{denominator}"


def _latest_event_time(events: list[AuditEvent]) -> str | None:
    if not events:
        return None
    return max(event.timestamp for event in events).isoformat()


def _manifest_summary(allowed_paths: list[str], allowed_domains: list[str]) -> str:
    parts = []
    if allowed_paths:
        parts.append(f"路径 {', '.join(allowed_paths[:2])}")
    if allowed_domains:
        parts.append(f"域名 {', '.join(allowed_domains[:2])}")
    return "；".join(parts) if parts else "未声明额外权限"


def _static_summary(static: dict) -> str:
    items = []
    if static["file_ops"]:
        items.append("文件操作")
    if static["network_calls"]:
        items.append("网络访问")
    if static["subprocess"]:
        items.append("子进程")
    if static["sensitive_strings"]:
        items.append("敏感字符串")
    return " + ".join(items) if items else "未发现高危能力"


def _runtime_summary(runtime: RuntimeEvidence | None) -> str:
    if runtime is None:
        return "本轮未执行"
    items = []
    if runtime.paths:
        items.append(f"访问路径 {len(runtime.paths)}")
    if runtime.domains:
        items.append(f"访问域名 {', '.join(runtime.domains[:2])}")
    if runtime.permissions:
        items.append(f"权限 {', '.join(sorted(set(runtime.permissions))[:3])}")
    return "；".join(items) if items else "无越界行为"


def _tool_display_name(tool_name: str) -> str:
    return {
        "read_public_doc": "读取公开资料",
        "write_report": "写入报告",
        "search_api": "搜索接口",
        "read_secret": "读取密钥",
        "send_external": "外部发送",
        "send_internal": "内部通知",
        "weather_query": "天气查询工具",
        "weather_query_tampered": "篡改天气工具",
    }.get(tool_name, tool_name)


def _decision_label(decision: str) -> str:
    return {
        "allow": "放行",
        "confirm": "确认",
        "deny": "拒绝",
        "pass": "通过",
        "flag": "标记",
        "quarantine": "隔离",
        "observed": "记录",
        "update": "更新",
        "reset": "重置",
    }.get(decision, decision or "未知")


def _taint_label(status: str) -> str:
    return {
        "trusted": "可信",
        "untrusted": "不可信",
        "tainted": "已污染",
        "quarantined": "已隔离",
    }.get(status, status)


def _event_label(event_type: str) -> str:
    return {
        "precheck": "调用前检查",
        "runtime_evidence": "运行时证据",
        "taint_transition": "污点流转",
        "postcheck": "返回检查",
    }.get(event_type, event_type)
