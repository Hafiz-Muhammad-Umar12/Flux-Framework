"""Conversation-based memory (wraps a Session)."""

from __future__ import annotations

from typing import Any

from .base import MemoryEntry


class ConversationMemory:
    """Memory backed by conversation history (wraps a Session)."""

    def __init__(self, session: Any) -> None:
        self._session = session

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Naive substring search over stored messages."""
        messages = await self._session.get_messages()
        query_lower = query.lower()
        results: list[MemoryEntry] = []

        for msg in messages:
            content = msg.get("content", "")
            if query_lower in content.lower():
                results.append(
                    MemoryEntry(
                        content=content,
                        metadata={"role": msg.get("role", "unknown")},
                    )
                )

        return results[:limit]

    async def store(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Store a memory as a user message."""
        msg: dict[str, Any] = {"role": "user", "content": content}
        if metadata:
            msg["metadata"] = metadata
        await self._session.add_messages([msg])

    async def clear(self) -> None:
        await self._session.clear()
