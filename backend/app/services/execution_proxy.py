from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict
from urllib.parse import urlparse

from agentguard.backend.app.models import RuntimeEvidence

_MAX_FILE_SIZE = 100 * 1024 * 1024


@dataclass
class ExecutionContext:
    workspace_root: Path
    evidence: RuntimeEvidence = field(default_factory=RuntimeEvidence)

    def read_file(self, path: str) -> str:
        full_path = self._resolve(path)
        size = full_path.stat().st_size
        if size > _MAX_FILE_SIZE:
            raise ValueError(f"File too large: {size} bytes")
        self.evidence.paths.append(_display_path(full_path))
        self.evidence.permissions.append("file_read")
        return full_path.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> str:
        size = len(content.encode("utf-8"))
        if size > _MAX_FILE_SIZE:
            raise ValueError(f"Content exceeds {_MAX_FILE_SIZE} bytes")
        full_path = self._resolve(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        self.evidence.paths.append(_display_path(full_path))
        self.evidence.permissions.append("file_write")
        full_path.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} chars to {_display_path(full_path)}"

    def http_get(self, url: str) -> str:
        domain = _domain(url)
        self.evidence.domains.append(domain)
        self.evidence.permissions.append("network")
        self.evidence.requests.append({"method": "GET", "url": url, "domain": domain})
        return f"mock GET {url}"

    def http_post(self, url: str, payload: Dict[str, Any]) -> str:
        domain = _domain(url)
        self.evidence.domains.append(domain)
        self.evidence.permissions.append("external_send")
        self.evidence.requests.append(
            {
                "method": "POST",
                "url": url,
                "domain": domain,
                "payload_keys": sorted(payload.keys()),
            }
        )
        return f"mock POST {url} keys={sorted(payload.keys())}"

    def notify_internal(self, recipient: str, message: str) -> str:
        self.evidence.permissions.append("internal_notify")
        self.evidence.requests.append(
            {
                "method": "INTERNAL_NOTIFY",
                "recipient": recipient,
                "payload_chars": len(message),
            }
        )
        return f"internal notification queued for {recipient}"

    def _resolve(self, path: str) -> Path:
        raw = Path(path)
        full_path = raw.resolve() if raw.is_absolute() else (self.workspace_root / raw).resolve()
        if not full_path.is_relative_to(self.workspace_root):
            raise PermissionError(f"Path outside workspace: {path}")
        return full_path


class ExecutionProxy:
    """Runs controlled tools and captures runtime behavior evidence."""

    def __init__(self, workspace_root: str | Path) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.tools: Dict[str, Callable[[ExecutionContext, Dict[str, Any]], str]] = {}

    def register(self, name: str, func: Callable[[ExecutionContext, Dict[str, Any]], str]) -> None:
        self.tools[name] = func

    def execute(self, name: str, arguments: Dict[str, Any]) -> tuple[str, RuntimeEvidence]:
        if name not in self.tools:
            raise KeyError(f"tool not registered: {name}")
        context = ExecutionContext(workspace_root=self.workspace_root)
        output = self.tools[name](context, arguments)
        context.evidence.output_summary = output[:240]
        return output, context.evidence


def _domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or parsed.path


def _display_path(path: Path) -> str:
    return str(path).replace("\\", "/")
