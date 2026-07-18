"""Session protocol for conversation persistence."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Session(Protocol):
    """Protocol for conversation session storage."""

    @property
    def session_id(self) -> str:
        """Unique session identifier."""
        ...

    async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Retrieve stored messages."""
        ...

    async def add_messages(self, messages: list[dict[str, Any]]) -> None:
        """Store messages."""
        ...

    async def clear(self) -> None:
        """Clear all messages."""
        ...
