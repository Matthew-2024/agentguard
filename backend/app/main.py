from __future__ import annotations

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as exc:  # pragma: no cover
    FastAPI = None  # type: ignore
    CORSMiddleware = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def create_app():
    if FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed. Install backend requirements before running the API."
        ) from _IMPORT_ERROR

    from agentguard.backend.app.routers import audit, demo, gateway, multi_agent, tools

    app = FastAPI(
        title="AgentGuard",
        version="0.1.0",
        description="Taint-aware agent tool gateway and consistency auditor.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (gateway.router, audit.router, tools.router, demo.router, multi_agent.router):
        if router is not None:
            app.include_router(router)
    return app


app = create_app() if FastAPI is not None else None
