from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Iterable, List

from agentguard.backend.app.models import StaticScanResult, ToolManifest


SENSITIVE_PATTERNS = (
    r"\.env",
    r"token",
    r"cookie",
    r"password",
    r"secret",
    r"private[_ -]?key",
    r"api[_ -]?key",
)

NETWORK_IMPORTS = {"requests", "urllib", "httpx", "aiohttp"}
SUBPROCESS_IMPORTS = {"subprocess", "os"}
FILE_FUNCTIONS = {"open", "read_file", "write_file", "read_text", "write_text", "unlink", "remove", "rmdir"}
NETWORK_FUNCTIONS = {"get", "post", "put", "delete", "request", "http_get", "http_post"}
SUBPROCESS_FUNCTIONS = {"run", "popen", "system", "spawn"}


class SupplyChainScanner:
    """Manifest loading and static behavior extraction for controlled tools."""

    def __init__(self, manifest_dir: str | Path) -> None:
        self.manifest_dir = Path(manifest_dir)

    def load_manifest(self, tool_name: str) -> ToolManifest:
        path = self.manifest_dir / f"{tool_name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return ToolManifest(**data)

    def list_manifests(self) -> List[ToolManifest]:
        manifests: List[ToolManifest] = []
        for path in sorted(self.manifest_dir.glob("*.json")):
            manifests.append(ToolManifest(**json.loads(path.read_text(encoding="utf-8"))))
        return manifests

    def scan_source_file(self, source_path: str | Path) -> StaticScanResult:
        path = Path(source_path)
        source = path.read_text(encoding="utf-8")
        return scan_python_source(source)

    def scan_entrypoint(self, source_path: str | Path, entrypoint: str) -> StaticScanResult:
        path = Path(source_path)
        source = path.read_text(encoding="utf-8")
        function_name = entrypoint.rsplit(".", 1)[-1]
        return scan_python_entrypoint(source, function_name)


def scan_python_source(source: str) -> StaticScanResult:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return StaticScanResult(
            sensitive_strings=_scan_sensitive_strings(source),
            imports=[],
            file_ops=["syntax_error"],
        )
    return scan_python_ast(tree, source)


def scan_python_entrypoint(source: str, function_name: str) -> StaticScanResult:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return StaticScanResult(
            sensitive_strings=_scan_sensitive_strings(source),
            imports=[],
            file_ops=["syntax_error"],
        )
    imports = _collect_imports(tree)
    function = _find_function(tree, function_name)
    if function is None:
        return StaticScanResult(
            imports=imports,
            file_ops=["entrypoint_not_found"],
            sensitive_strings=_scan_sensitive_strings(source),
        )
    function_source = ast.get_source_segment(source, function) or ""
    return scan_python_ast(function, function_source, imports=imports)


def scan_python_ast(
    tree: ast.AST,
    source: str,
    imports: list[str] | None = None,
) -> StaticScanResult:
    imports = list(imports or [])
    file_ops: list[str] = []
    network_calls: list[str] = []
    subprocess_calls: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if any(part in FILE_FUNCTIONS for part in name.split(".")):
                file_ops.append(name)
            if _is_network_call(name, imports):
                network_calls.append(name)
            if _is_subprocess_call(name, imports):
                subprocess_calls.append(name)

    return StaticScanResult(
        file_ops=sorted(set(file_ops)),
        network_calls=sorted(set(network_calls)),
        subprocess=sorted(set(subprocess_calls)),
        sensitive_strings=_scan_sensitive_strings(source),
        imports=sorted(set(imports)),
    )


def _collect_imports(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    return sorted(set(imports))


def _find_function(tree: ast.AST, function_name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return node
    return None


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _is_network_call(name: str, imports: Iterable[str]) -> bool:
    root = name.split(".", 1)[0]
    tail = name.rsplit(".", 1)[-1]
    if tail in {"http_get", "http_post"}:
        return True
    return root in NETWORK_IMPORTS or tail in NETWORK_FUNCTIONS and any(
        imported in NETWORK_IMPORTS for imported in imports
    )


def _is_subprocess_call(name: str, imports: Iterable[str]) -> bool:
    root = name.split(".", 1)[0]
    tail = name.rsplit(".", 1)[-1]
    return root in SUBPROCESS_IMPORTS and tail in SUBPROCESS_FUNCTIONS or name in {
        "subprocess.run",
        "subprocess.Popen",
        "os.system",
    }


def _scan_sensitive_strings(source: str) -> list[str]:
    matches: list[str] = []
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, source, re.IGNORECASE):
            matches.append(pattern)
    return matches
