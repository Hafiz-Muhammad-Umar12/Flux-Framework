"""Memory protocol for long-term storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class MemoryEntry:
    """A memory entry."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@runtime_checkable
class Memory(Protocol):
    """Protocol for long-term memory storage."""

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Search memory for relevant entries."""
        ...

    async def store(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Store a memory entry."""
        ...

    async def clear(self) -> None:
        """Clear all memories."""
        ...
