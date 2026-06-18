from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from agentguard.backend.app.models import Decision, PolicyDecisionResult, TaintStatus, ToolCategory


DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[2] / "policies" / "taint_policy.yaml"
)


class PolicyEngine:
    """YAML-configured mapping from session taint to tool-call decisions."""

    def __init__(self, policy_path: str | Path = DEFAULT_POLICY_PATH) -> None:
        self.policy_path = Path(policy_path)
        self.rules = load_policy_rules(self.policy_path).get("rules", [])

    def decide(
        self,
        session_taint: TaintStatus,
        tool_category: ToolCategory,
        confirmed: bool = False,
    ) -> PolicyDecisionResult:
        for rule in self.rules:
            if _match(rule.get("session_taint"), session_taint.value) and _match(
                rule.get("tool_category"), tool_category.value
            ):
                decision = Decision(rule["decision"])
                risk_factors = list(rule.get("risk_factors", []))
                if confirmed and decision == Decision.CONFIRM:
                    return PolicyDecisionResult(
                        decision=Decision.ALLOW,
                        rule_matched=f"{rule.get('session_taint')} + {rule.get('tool_category')}",
                        reasoning="用户已确认原本需要确认的调用",
                        risk_factors=risk_factors + ["manual_override"],
                    )
                return PolicyDecisionResult(
                    decision=decision,
                    rule_matched=f"{rule.get('session_taint')} + {rule.get('tool_category')}",
                    reasoning=rule.get("reason", "策略表命中"),
                    risk_factors=risk_factors,
                )

        return PolicyDecisionResult(
            decision=Decision.DENY,
            rule_matched="default_deny",
            reasoning="未命中策略，默认拒绝",
            risk_factors=["missing_policy_rule"],
        )


def _match(pattern: str | None, value: str) -> bool:
    return pattern in ("*", value)


def load_policy_rules(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return _parse_minimal_rules_yaml(text)


def _parse_minimal_rules_yaml(text: str) -> Dict[str, Any]:
    """Parse the small policy YAML subset used by this prototype.

    This keeps tests runnable in offline environments where PyYAML is absent.
    The project still stores policy as YAML, and production installs should use
    PyYAML through requirements.txt.
    """

    rules: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    in_rules = False

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped == "rules:":
            in_rules = True
            continue
        if not in_rules:
            continue
        if stripped.startswith("- "):
            if current:
                rules.append(current)
            current = {}
            tail = stripped[2:].strip()
            if tail:
                key, value = tail.split(":", 1)
                current[key.strip()] = _parse_value(value.strip())
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = _parse_value(value.strip())

    if current:
        rules.append(current)
    return {"rules": rules}


def _parse_value(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(part.strip()) for part in inner.split(",")]
    return _strip_quotes(value)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
