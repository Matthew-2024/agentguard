from __future__ import annotations

import os

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as exc:  # pragma: no cover
    FastAPI = None  # type: ignore
    CORSMiddleware = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _cors_origins() -> list[str]:
    raw = os.getenv("AGENTGUARD_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://127.0.0.1:5173"]


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
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (gateway.router, audit.router, tools.router, demo.router, multi_agent.router, report.router):
        if router is not None:
            app.include_router(router)

    @app.get("/health", tags=["system"])
    def health():
        return {
            "status": "ok",
            "service": "agentguard-api",
            "version": app.version,
        }

    return app


app = create_app() if FastAPI is not None else None
