from __future__ import annotations

import os
import secrets

try:
    from fastapi import Depends, FastAPI, HTTPException, Security
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import APIKeyHeader
except ImportError as exc:  # pragma: no cover
    Depends = None  # type: ignore
    FastAPI = None  # type: ignore
    HTTPException = None  # type: ignore
    Security = None  # type: ignore
    CORSMiddleware = None  # type: ignore
    APIKeyHeader = None  # type: ignore
    _API_KEY_HEADER = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None
    _API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)


def _cors_origins() -> list[str]:
    raw = os.getenv("AGENTGUARD_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://127.0.0.1:5173"]


if Security is not None:
    def verify_api_key(key: str = Security(_API_KEY_HEADER)):  # type: ignore[valid-type]
        expected = os.getenv("AGENTGUARD_API_KEY", "")
        if not expected or not secrets.compare_digest(key, expected):
            raise HTTPException(status_code=403, detail="Invalid API key")
        return True
else:  # pragma: no cover
    def verify_api_key():
        raise RuntimeError("FastAPI is not installed.")


def create_app():
    if FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed. Install backend requirements before running the API."
        ) from _IMPORT_ERROR

    from agentguard.backend.app.routers import audit, demo, gateway, multi_agent, report, tools

    app = FastAPI(
        title="AgentGuard",
        version="0.1.0",
        description="Taint-aware agent tool gateway and consistency auditor.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    )
    for router in (gateway.router, audit.router, tools.router, demo.router, multi_agent.router, report.router):
        if router is not None:
            app.include_router(router, dependencies=[Depends(verify_api_key)])

    @app.get("/health", tags=["system"])
    def health():
        return {
            "status": "ok",
            "service": "agentguard-api",
            "version": app.version,
        }

    return app


app = create_app() if FastAPI is not None else None
