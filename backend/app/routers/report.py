from __future__ import annotations

from agentguard.backend.app.services.report_generator import (
    generate_latest_report,
    generate_session_report,
)

try:
    from fastapi import APIRouter
    from fastapi.responses import PlainTextResponse
except ImportError:  # pragma: no cover
    APIRouter = None  # type: ignore
    PlainTextResponse = None  # type: ignore


if APIRouter is not None:
    router = APIRouter(prefix="/report", tags=["report"])

    @router.get("/session/{session_id}")
    def session_report(session_id: str):
        return generate_session_report(session_id)

    @router.get("/session/{session_id}.md", response_class=PlainTextResponse)
    def session_report_markdown(session_id: str):
        return generate_session_report(session_id)["markdown"]

    @router.get("/latest")
    def latest_report():
        return generate_latest_report()

    @router.get("/latest.md", response_class=PlainTextResponse)
    def latest_report_markdown():
        return generate_latest_report()["markdown"]

else:
    router = None
