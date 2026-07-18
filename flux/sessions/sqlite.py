"""SQLite session storage."""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any


class SQLiteSession:
    """Persistent session storage using SQLite."""

    def __init__(self, db_path: str = "flux_sessions.db", session_id: str | None = None) -> None:
        self._session_id = session_id or uuid.uuid4().hex[:16]
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)"
        )
        conn.commit()
        conn.close()

    @property
    def session_id(self) -> str:
        return self._session_id

    async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        query = "SELECT role, content, metadata FROM messages WHERE session_id = ? ORDER BY id"
        params: list[Any] = [self._session_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        result = []
        for row in rows:
            msg: dict[str, Any] = {"role": row["role"], "content": row["content"]}
            if row["metadata"]:
                msg["metadata"] = json.loads(row["metadata"])
            result.append(msg)
        return result

    async def add_messages(self, messages: list[dict[str, Any]]) -> None:
        conn = sqlite3.connect(self._db_path)
        for msg in messages:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, metadata) VALUES (?, ?, ?, ?)",
                (
                    self._session_id,
                    msg.get("role", "user"),
                    msg.get("content", ""),
                    json.dumps(msg.get("metadata")) if msg.get("metadata") else None,
                ),
            )
        conn.commit()
        conn.close()

    async def clear(self) -> None:
        conn = sqlite3.connect(self._db_path)
        conn.execute("DELETE FROM messages WHERE session_id = ?", (self._session_id,))
        conn.commit()
        conn.close()
