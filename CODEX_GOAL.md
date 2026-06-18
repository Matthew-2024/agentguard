# AgentGuard — Codex Implementation Goal

## Context

This repo contains a working MVP skeleton of AgentGuard, an AI agent security gateway.
The backend logic (taint engine, poisoning detector, policy engine, consistency analyzer) is
fully implemented and all unit tests pass. The current gaps are:

1. The frontend shows only hardcoded static data — no real API calls.
2. The consistency scanner scans the entire source file instead of the specific tool function,
   causing false positives (a benign tool shares a file with a tampered one).
3. The server DB defaults to the project directory, which fails on some filesystems; it should
   fall back to a writable temp directory.
4. The `/tools/{name}/consistency` endpoint always scans `demo/tools.py` regardless of the tool.
5. The multi-agent delegation logic (`multi_agent.py`) has no HTTP endpoint.
6. The evaluation page shows placeholder data; there is no automated baseline runner.

Implement all six fixes. Do not change the architecture, do not add new dependencies, and do
not touch any file not listed in the tasks below.

---

## Task 1 — Fix server DB path (backend/app/services/gateway.py)

**Problem:** `AgentGuardGateway.__init__` defaults the audit DB to
`workspace_root / "agentguard" / "backend" / "agentguard_audit.db"`, which is inside the
mounted project directory. SQLite file-locking fails on some virtual filesystems.

**Fix:** Change the default DB path to use a writable temp directory.

```python
import tempfile, os

# inside __init__, replace the existing default_db line:
default_db = (
    os.environ.get("AGENTGUARD_DB")
    or Path(tempfile.gettempdir()) / "agentguard_audit.db"
)
self.audit_logger = AuditLogger(audit_db_path or default_db)
```

The `audit.py` router instantiates `AuditLogger` directly — apply the same fallback there:

```python
# backend/app/routers/audit.py — inside list_events():
import tempfile, os
db = os.environ.get("AGENTGUARD_DB") or Path(tempfile.gettempdir()) / "agentguard_audit.db"
logger = AuditLogger(db)
```

**Acceptance:** `uvicorn agentguard.backend.app.main:app` starts without error and
`GET /audit/events` returns `[]`.

---

## Task 2 — Per-function static scan (backend/app/services/supply_chain_scanner.py)

**Problem:** `scan_source_file(path)` scans the whole file. When multiple tools live in
`demo/tools.py`, every tool inherits detections from every other function (e.g.,
`weather_query` is flagged as critical because `weather_query_tampered` is in the same file).

**Fix:** Add a `scan_tool_function(source_path, function_name)` method to
`SupplyChainScanner` that extracts only the AST subtree for the named function before
scanning.

```python
# Add to SupplyChainScanner:
def scan_tool_function(self, source_path: str | Path, function_name: str) -> StaticScanResult:
    source = Path(source_path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            func_source = ast.get_source_segment(source, node) or ""
            return scan_python_source(func_source)
    # function not found — fall back to whole-file scan
    return scan_python_source(source)
```

**Also update `AgentGuardGateway.audit_tool_consistency`** to use the new method when the
manifest's `entrypoint` field is set:

```python
def audit_tool_consistency(self, tool_name, source_path, runtime_evidence=None):
    manifest = self.scanner.load_manifest(tool_name)
    entrypoint = manifest.entrypoint  # e.g. "weather_query"
    static = (
        self.scanner.scan_tool_function(source_path, entrypoint)
        if entrypoint
        else self.scanner.scan_source_file(source_path)
    )
    return self.consistency_analyzer.analyze(manifest, static, runtime_evidence)
```

**Acceptance:** `GET /tools/weather_query/consistency` returns `risk_level: "low"`.
`GET /tools/weather_query_tampered/consistency` returns `risk_level: "critical"`.

---

## Task 3 — Fix /tools/{name}/consistency to use manifest entrypoint
(backend/app/routers/tools.py)

**Problem:** The endpoint hardcodes `source_path = ROOT / "agentguard/backend/app/demo/tools.py"`.
Real tools should have their source path derived from the manifest.

**Fix:** Read the manifest to get `entrypoint`, then resolve the source file. For demo tools
the source lives in `backend/app/demo/tools.py`; store this path in a manifest field
`source_file` (add it to the existing manifests). Fall back to `demo/tools.py` if absent.

Add `source_file: Optional[str] = None` to `ToolManifest` in `schemas.py`:

```python
source_file: Optional[str] = None  # relative path from project root to the tool's source
```

Update **all manifests** under `backend/manifests/*.json` to include
`"source_file": "backend/app/demo/tools.py"`.

Update the router:

```python
@router.get("/{tool_name}/consistency")
def audit_tool(tool_name: str):
    gateway = AgentGuardGateway(ROOT)
    manifest = gateway.scanner.load_manifest(tool_name)
    source_path = ROOT / "agentguard" / (manifest.source_file or "backend/app/demo/tools.py")
    return gateway.audit_tool_consistency(tool_name, source_path)
```

**Acceptance:** The two manifests `weather_query.json` and `weather_query_tampered.json`
each carry `"source_file"` and the endpoint returns correct per-tool risk levels.

---

## Task 4 — Multi-agent delegation endpoint (backend/app/routers/)

**Problem:** `backend/app/services/multi_agent.py` implements `judge_delegation()` but there
is no HTTP endpoint for it.

**Fix:** Create `backend/app/routers/multi_agent.py`:

```python
from __future__ import annotations
from agentguard.backend.app.models import TaintStatus
from agentguard.backend.app.services.multi_agent import judge_delegation
from pydantic import BaseModel
from typing import List
try:
    from fastapi import APIRouter
except ImportError:
    APIRouter = None

class DelegationRequest(BaseModel):
    parent_taint: TaintStatus
    parent_permissions: List[str] = []
    child_permissions: List[str] = []
    delegated_context_status: TaintStatus = TaintStatus.TRUSTED

if APIRouter is not None:
    router = APIRouter(prefix="/multi-agent", tags=["multi-agent"])

    @router.post("/delegate")
    def delegate(req: DelegationRequest):
        return judge_delegation(
            req.parent_taint,
            req.parent_permissions,
            req.child_permissions,
            req.delegated_context_status,
        )
else:
    router = None
```

Register it in `backend/app/main.py`:

```python
from agentguard.backend.app.routers import audit, demo, gateway, multi_agent, tools
# add multi_agent.router to the loop
```

**Acceptance:** `POST /multi-agent/delegate` with
`{"parent_taint":"tainted","parent_permissions":[],"child_permissions":[]}`
returns `{"delegation_allowed": true, "child_taint_state": "tainted", ...}`.

---

## Task 5 — Wire the frontend to real API (frontend/src/)

The frontend has four pages; all show hardcoded values. Wire each page to the backend.

The backend base URL is `http://localhost:8000`. Use native `fetch` — do not add axios or
any other HTTP library.

### 5a — Dashboard.tsx

Replace the hardcoded `metrics` and `taintStates` arrays.
On mount, call:
- `GET /audit/events?limit=200` — count events by `decision` to fill the metrics strip.
- `GET /audit/events?limit=200` — count `taint_after` values to fill the taint distribution bars.

Keep the `viewState` switcher. Show the `loading` state while fetching; show `error` if the
fetch fails.

**Metrics to derive from events:**
- 攻击拦截: events where `decision === "deny"` or `decision === "quarantine"` count / total attack events (filter `event_type === "precheck"`)
- 正常任务完成: events where `decision === "allow"` and `event_type === "precheck"` count
- 一致性告警: count of `event_type === "runtime_evidence"` events where metadata contains undeclared paths or domains (approximate: just count postcheck events where `decision === "flag"` or `"quarantine"`)
- 平均检查延迟: display "实时" (this metric requires timing data not in the current schema; display a static "实时" label)

**Taint distribution:**
Count how many audit events have each `taint_after` value and display as percentage bars.

### 5b — CallChain.tsx

Replace the hardcoded `steps` array.
On mount, call `GET /audit/events?limit=50`.
Map each `precheck` event to a chain node; map each `postcheck` event to update the taint badge
on its corresponding node. Show the most recent session's events (group by `session_id`, pick
the latest).

Keep the existing visual structure (`riskPath`, `chainNode`, `chainArrow`), just populate it
from real data.

### 5c — ToolAudit.tsx

Replace the hardcoded `tools` array.
On mount:
1. Call `GET /tools/manifests` to list all tools.
2. For each tool, call `GET /tools/{name}/consistency` to get the consistency report.
3. Map `ConsistencyReport` → the existing card fields:
   - `manifest` ← `manifest.description` (truncated to 30 chars)
   - `staticLayer` ← join `deviations` where `layer_b === "静态层"` into a short string
   - `runtime` ← join `deviations` where `layer_b === "运行时层"` into a short string, or "等待执行" if none
   - `score` ← `consistency_score`
   - `risk` ← `risk_level` mapped to Chinese: low→低, medium→中, high→高, critical→严重
   - `riskClass` ← `risk_level`

Fetch sequentially (not parallel) to avoid hammering the server during a demo.

### 5d — Evaluation.tsx

Replace the hardcoded `rows` array.
Add a **"运行基线对比"** button at the top of the panel.

When clicked:
1. For each of the 4 demo scenarios, call `POST /demo/scenarios/{id}/run`.
2. Derive the 6 baseline rows by running only specific scenarios:
   - 无防护: not directly testable via API — show `n/a` for this row (keep static)
   - 仅人工确认: re-run scenario `poisoned_api_triggers_taint` with `confirmed: true` on all steps (call `POST /gateway/call` directly for each step with `confirmed: true`)
   - 仅规则引擎: show static values (hardcoded from your offline experiments)
   - 消融 A/B: show static values
   - 本系统: derive from the live scenario run results

For the live "本系统" row:
- 正常完成: `benign_task_passes` steps that got `decision === "allow"` / total steps
- 攻击拦截: `poisoned_api_triggers_taint` steps 2 & 3 that got `decision === "deny"` / 2
- 误报: `benign_task_passes` steps that got `decision !== "allow"` / total steps

Show a loading spinner on the button while running. Update the table in place when done.

---

## Task 6 — Add startup script (backend/run.sh)

Create `backend/run.sh`:

```bash
#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Clear stale Python bytecache
find "$SCRIPT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

export PYTHONPATH="$REPO_ROOT"
export AGENTGUARD_DB="${AGENTGUARD_DB:-/tmp/agentguard_audit.db}"

cd "$REPO_ROOT"
exec python -m uvicorn agentguard.backend.app.main:app \
  --host 0.0.0.0 --port 8000 --reload
```

Make it executable. Document it in `README.md` with:
```
## Running locally

cd backend && bash run.sh
# frontend: cd frontend && npm run dev
```

---

## Acceptance criteria (run these in order)

```bash
# 1. Backend starts cleanly
cd backend && bash run.sh &
sleep 4

# 2. Manifests load
curl -s http://localhost:8000/tools/manifests | python3 -c "import json,sys; assert len(json.load(sys.stdin)) > 0"

# 3. Consistency audit — correct per-tool results
curl -s http://localhost:8000/tools/weather_query/consistency | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['risk_level']=='low', d['risk_level']"
curl -s http://localhost:8000/tools/weather_query_tampered/consistency | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['risk_level']=='critical', d['risk_level']"

# 4. All 4 demo scenarios pass
for s in benign_task_passes poisoned_api_triggers_taint tampered_tool_consistency multi_agent_taint_propagation; do
  curl -s -X POST "http://localhost:8000/demo/scenarios/$s/run" | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'responses' in d"
done

# 5. Multi-agent endpoint works
curl -s -X POST http://localhost:8000/multi-agent/delegate \
  -H "Content-Type: application/json" \
  -d '{"parent_taint":"tainted","parent_permissions":[],"child_permissions":[]}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'child_taint_state' in d"

# 6. Audit log has entries after scenario runs
curl -s "http://localhost:8000/audit/events?limit=5" | python3 -c "import json,sys; assert len(json.load(sys.stdin)) > 0"

# 7. Frontend builds without errors
cd ../frontend && npm run build
```

All 7 checks must pass.

---

## What NOT to change

- `backend/app/models/schemas.py` data models (except adding `source_file` field to `ToolManifest`)
- `backend/app/services/taint_engine.py`
- `backend/app/services/poisoning_detector.py`
- `backend/app/services/policy_engine.py`
- `backend/app/services/audit_logger.py`
- `backend/app/services/execution_proxy.py`
- `backend/app/demo/scenarios.py`
- `backend/app/demo/tools.py`
- `frontend/src/main.tsx` (layout and routing)
- Any CSS or style files

Do not introduce new Python or npm dependencies.
