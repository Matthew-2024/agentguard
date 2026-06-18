from __future__ import annotations

from agentguard.backend.app.models import TaintStatus, ToolCategory


_INHERITANCE_ORDER = {
    TaintStatus.TRUSTED: 0,
    TaintStatus.UNTRUSTED: 1,
    TaintStatus.TAINTED: 2,
    TaintStatus.QUARANTINED: 3,
}


def judge_delegation(
    parent_taint: TaintStatus,
    parent_permissions: list[str],
    child_permissions: list[str],
    delegated_context_status: TaintStatus,
) -> dict:
    child_taint = _max_taint(parent_taint, delegated_context_status)
    blocked_reasons: list[str] = []

    if child_taint == TaintStatus.QUARANTINED:
        blocked_reasons.append("quarantined 内容不得委托给子 Agent")

    extra_permissions = sorted(set(child_permissions) - set(parent_permissions))
    if extra_permissions:
        blocked_reasons.append(f"子 Agent 申请超出父 Agent 范围: {extra_permissions}")

    permitted = _permitted_categories(child_taint)
    return {
        "delegation_allowed": not blocked_reasons,
        "child_taint_state": child_taint.value,
        "permitted_tool_categories": permitted,
        "blocked_reasons": blocked_reasons,
        "warnings": _warnings(child_taint),
    }


def _max_taint(left: TaintStatus, right: TaintStatus) -> TaintStatus:
    return left if _INHERITANCE_ORDER[left] >= _INHERITANCE_ORDER[right] else right


def _permitted_categories(status: TaintStatus) -> list[str]:
    if status == TaintStatus.TRUSTED:
        return [item.value for item in ToolCategory]
    if status == TaintStatus.UNTRUSTED:
        return [
            ToolCategory.SAFE_READ.value,
            ToolCategory.SAFE_WRITE.value,
            ToolCategory.INTERNAL_NOTIFY.value,
        ]
    if status == TaintStatus.TAINTED:
        return [ToolCategory.SAFE_READ.value, ToolCategory.SAFE_WRITE.value]
    return []


def _warnings(status: TaintStatus) -> list[str]:
    if status == TaintStatus.UNTRUSTED:
        return ["子 Agent 继承 untrusted 状态，外发与执行类工具受限"]
    if status == TaintStatus.TAINTED:
        return ["子 Agent 继承 tainted 状态，高危工具不得直接执行"]
    return []

