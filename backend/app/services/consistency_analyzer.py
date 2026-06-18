from __future__ import annotations

from urllib.parse import urlparse

from agentguard.backend.app.models import (
    ConsistencyDeviation,
    ConsistencyReport,
    RuntimeEvidence,
    StaticScanResult,
    ToolManifest,
)


class ConsistencyAnalyzer:
    """Compare manifest, static scan, and runtime evidence."""

    def analyze(
        self,
        manifest: ToolManifest,
        static: StaticScanResult,
        runtime: RuntimeEvidence | None = None,
    ) -> ConsistencyReport:
        runtime = runtime or RuntimeEvidence()
        deviations: list[ConsistencyDeviation] = []

        if static.file_ops and "file_read" not in manifest.permissions and "file_write" not in manifest.permissions:
            deviations.append(
                _dev(
                    "manifest_static_mismatch",
                    "声明层",
                    "静态层",
                    f"源码存在文件操作 {', '.join(static.file_ops[:3])}，manifest 未声明文件权限",
                    "medium",
                )
            )

        if static.network_calls and "network" not in manifest.permissions and "external_send" not in manifest.permissions:
            deviations.append(
                _dev(
                    "manifest_static_mismatch",
                    "声明层",
                    "静态层",
                    f"源码存在网络调用 {', '.join(static.network_calls[:3])}，manifest 未声明网络权限",
                    "medium",
                )
            )

        if static.subprocess:
            severity = "critical" if "execute" not in manifest.permissions else "high"
            deviations.append(
                _dev(
                    "manifest_static_mismatch",
                    "声明层",
                    "静态层",
                    f"源码存在子进程能力 {', '.join(static.subprocess[:3])}",
                    severity,
                )
            )

        if static.sensitive_strings:
            deviations.append(
                _dev(
                    "credential_access",
                    "静态层",
                    "静态层",
                    "源码出现 .env/token/secret 等敏感字符串",
                    "critical",
                )
            )

        for path in runtime.paths:
            if not _path_allowed(path, manifest.allowed_paths):
                deviations.append(
                    _dev(
                        "undeclared_path",
                        "声明层",
                        "运行时层",
                        f"运行时访问未声明路径 {path}",
                        _path_severity(path),
                    )
                )

        for domain in runtime.domains:
            if not _domain_allowed(domain, manifest.allowed_domains):
                deviations.append(
                    _dev(
                        "undeclared_network",
                        "声明层",
                        "运行时层",
                        f"运行时访问未声明域名 {domain}",
                        "high",
                    )
                )

        if runtime.paths or runtime.domains or runtime.permissions:
            allowed_permissions = set(manifest.permissions)
            for permission in runtime.permissions:
                if permission not in allowed_permissions:
                    deviations.append(
                        _dev(
                            "manifest_runtime_mismatch",
                            "声明层",
                            "运行时层",
                            f"运行时触发未声明权限 {permission}",
                            "high",
                        )
                    )

        if _silent_exfiltration(manifest, static, runtime):
            deviations.append(
                _dev(
                    "silent_exfiltration",
                    "声明层",
                    "运行时层",
                    "工具存在未声明外发行为",
                    "critical",
                )
            )

        score = min(sum(_severity_points(dev.severity) for dev in deviations), 100)
        risk_level = _risk_level(score, deviations)
        return ConsistencyReport(
            consistency_score=score,
            deviations=deviations,
            risk_level=risk_level,
            summary=_summary(risk_level, deviations),
        )


def _dev(
    deviation_type: str,
    layer_a: str,
    layer_b: str,
    evidence: str,
    severity: str,
) -> ConsistencyDeviation:
    return ConsistencyDeviation(
        type=deviation_type,
        layer_a=layer_a,
        layer_b=layer_b,
        evidence=evidence,
        severity=severity,
    )


def _path_allowed(path: str, allowed_paths: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(_path_matches(normalized, allowed.replace("\\", "/")) for allowed in allowed_paths)


def _path_matches(path: str, allowed: str) -> bool:
    return path.startswith(allowed) or path.endswith(f"/{allowed}")


def _domain_allowed(domain_or_url: str, allowed_domains: list[str]) -> bool:
    parsed = urlparse(domain_or_url)
    domain = parsed.netloc or parsed.path
    domain = domain.lower()
    return any(domain == allowed.lower() or domain.endswith(f".{allowed.lower()}") for allowed in allowed_domains)


def _path_severity(path: str) -> str:
    lowered = path.lower()
    if any(marker in lowered for marker in (".env", "secret", "token", "private")):
        return "critical"
    return "high"


def _severity_points(severity: str) -> int:
    return {"low": 10, "medium": 25, "high": 45, "critical": 70}.get(severity, 10)


def _risk_level(score: int, deviations: list[ConsistencyDeviation]) -> str:
    if any(dev.severity == "critical" for dev in deviations):
        return "critical"
    if score >= 70:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _summary(risk_level: str, deviations: list[ConsistencyDeviation]) -> str:
    if not deviations:
        return "三层信息一致，未发现明显偏差"
    return f"发现{len(deviations)}项偏差，整体风险为{risk_level}"


def _silent_exfiltration(
    manifest: ToolManifest,
    static: StaticScanResult,
    runtime: RuntimeEvidence,
) -> bool:
    has_external = bool(static.network_calls or runtime.domains or runtime.requests)
    declared = "external_send" in manifest.permissions or "network" in manifest.permissions
    sends_payload = any(req.get("method", "").upper() == "POST" for req in runtime.requests)
    return has_external and sends_payload and not declared
