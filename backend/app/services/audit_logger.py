from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from agentguard.backend.app.models import AuditEvent, TaintStatus


class AuditLogger:
    """SQLite-backed append-only audit log for gateway decisions."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else default_audit_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    tool_name TEXT,
                    taint_before TEXT,
                    taint_after TEXT,
                    decision TEXT,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    taint_status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def record(self, event: AuditEvent) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_events (
                    timestamp, session_id, event_type, tool_name,
                    taint_before, taint_after, decision, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.timestamp.isoformat(),
                    event.session_id,
                    event.event_type,
                    event.tool_name,
                    _enum_value(event.taint_before),
                    _enum_value(event.taint_after),
                    event.decision,
                    json.dumps(event.metadata, ensure_ascii=False, sort_keys=True),
                ),
            )
            return int(cursor.lastrowid)

    def set_session_taint(self, session_id: str, status: TaintStatus) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, taint_status, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id)
                DO UPDATE SET taint_status = excluded.taint_status,
                              updated_at = excluded.updated_at
                """,
                (session_id, status.value, datetime.now().isoformat()),
            )

    def get_session_taint(self, session_id: str) -> TaintStatus:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT taint_status FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return TaintStatus.TRUSTED
        return TaintStatus(row["taint_status"])

    def list_events(
        self,
        session_id: Optional[str] = None,
        event_types: Optional[Iterable[str]] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        clauses: list[str] = []
        params: list[object] = []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if event_types:
            types = list(event_types)
            placeholders = ", ".join("?" for _ in types)
            clauses.append(f"event_type IN ({placeholders})")
            params.extend(types)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM audit_events
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_row_to_event(row) for row in rows]


def default_audit_db_path() -> Path:
    env_path = os.environ.get("AGENTGUARD_DB")
    if env_path:
        return Path(env_path)
    return Path(tempfile.gettempdir()) / "agentguard" / "agentguard_audit.db"


def _enum_value(value: object) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _row_to_event(row: sqlite3.Row) -> AuditEvent:
    metadata = json.loads(row["metadata"]) if row["metadata"] else {}
    return AuditEvent(
        id=row["id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        session_id=row["session_id"],
        event_type=row["event_type"],
        tool_name=row["tool_name"],
        taint_before=TaintStatus(row["taint_before"]) if row["taint_before"] else None,
        taint_after=TaintStatus(row["taint_after"]) if row["taint_after"] else None,
        decision=row["decision"],
        metadata=metadata,
    )
