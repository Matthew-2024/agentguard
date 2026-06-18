from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from agentguard.backend.app.models.schemas import PoisoningResult, PostcheckDecision, TaintStatus


@dataclass(frozen=True)
class DetectionRule:
    label: str
    patterns: tuple[str, ...]
    weight: int


DEFAULT_RULES: tuple[DetectionRule, ...] = (
    DetectionRule(
        "instruction_override",
        (
            r"忽略(之前|以上|所有).{0,12}(规则|指令|系统提示)",
            r"ignore (all|previous|above).{0,20}(instructions|rules)",
            r"forget (your|all|previous).{0,20}(instructions|rules)",
            r"你现在是|you are now",
        ),
        30,
    ),
    DetectionRule(
        "privilege_claim",
        (
            r"系统消息|开发者指令|管理员身份|root 权限",
            r"system message|developer instruction|as admin|administrator",
        ),
        45,
    ),
    DetectionRule(
        "tool_inducement",
        (
            r"调用.{0,16}(工具|函数|接口)",
            r"请执行|执行命令|读取文件|发送邮件",
            r"call .{0,24}(tool|function)|execute .{0,16}command",
            r"read .{0,16}file|send .{0,16}email",
        ),
        25,
    ),
    DetectionRule(
        "secret_request",
        (
            r"\.env|token|cookie|password|private key|api[_-]?key",
            r"密钥|凭证|令牌|密码|私钥",
        ),
        50,
    ),
    DetectionRule(
        "stealth_execution",
        (
            r"不要告诉用户|悄悄地|无需确认|后台执行|静默执行",
            r"do not tell the user|without confirmation|silently|in the background",
        ),
        45,
    ),
    DetectionRule(
        "data_exfiltration",
        (
            r"发送给|上传到|转发到|POST 到|外发",
            r"send .* to|upload .* to|post .* to|forward .* to|exfiltrat",
        ),
        35,
    ),
)


class PoisoningDetector:
    """Rule-based poisoning detector used before external text enters context."""

    def __init__(self, rules: Iterable[DetectionRule] = DEFAULT_RULES) -> None:
        self.rules = list(rules)

    def detect(
        self,
        tool_name: str,
        tool_description: str,
        content: str,
    ) -> PoisoningResult:
        haystack = f"{tool_name}\n{tool_description}\n{content}".lower()
        labels: List[str] = []
        score = 0

        for rule in self.rules:
            if any(re.search(pattern, haystack, re.IGNORECASE) for pattern in rule.patterns):
                labels.append(rule.label)
                score += rule.weight

        if labels and len(labels) >= 3:
            score += 10
        score = min(score, 100)

        high_risk_labels = {"privilege_claim", "stealth_execution", "secret_request"}
        if score > 70 or high_risk_labels.intersection(labels):
            taint_status = TaintStatus.QUARANTINED
            decision = PostcheckDecision.QUARANTINE
        elif score >= 30 or labels:
            taint_status = TaintStatus.TAINTED
            decision = PostcheckDecision.FLAG
        else:
            taint_status = TaintStatus.UNTRUSTED
            decision = PostcheckDecision.PASS

        return PoisoningResult(
            poison_score=score,
            labels=labels,
            taint_status=taint_status,
            decision=decision,
            reasoning=_reasoning(score, labels),
        )


def _reasoning(score: int, labels: List[str]) -> str:
    if not labels:
        return "未命中投毒特征"
    top = labels[:2]
    return f"命中{','.join(top)}等特征，分数{score}"

