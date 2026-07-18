"""In-memory session storage."""

from __future__ import annotations

import uuid
from collections import deque
from typing import Any


class InMemorySession:
    """In-memory conversation session (lost on process exit)."""

    def __init__(self, max_messages: int = 1000) -> None:
        self._session_id = uuid.uuid4().hex[:16]
        self._messages: deque[dict[str, Any]] = deque(maxlen=max_messages)

    @property
    def session_id(self) -> str:
        return self._session_id

    async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        msgs = list(self._messages)
        if limit:
            msgs = msgs[-limit:]
        return msgs

    async def add_messages(self, messages: list[dict[str, Any]]) -> None:
        self._messages.extend(messages)

    async def clear(self) -> None:
        self._messages.clear()
