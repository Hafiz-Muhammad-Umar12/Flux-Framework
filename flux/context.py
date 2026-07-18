"""Run context and tool context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class Usage:
    """Token usage tracking."""

    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: Usage) -> None:
        """Aggregate usage from another Usage instance."""
        self.requests += other.requests
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_tokens += other.total_tokens

    def __iadd__(self, other: Usage) -> Usage:
        self.add(other)
        return self


@dataclass
class RunContext(Generic[T]):
    """Context carried through a run."""

    user_context: T | None = None
    usage: Usage = field(default_factory=Usage)
    turn_count: int = 0
    _metadata: dict[str, Any] = field(default_factory=dict)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata by key."""
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata."""
        self._metadata[key] = value


@dataclass
class ToolContext(Generic[T]):
    """Context for a single tool invocation."""

    run_context: RunContext[T]
    tool_name: str
    tool_call_id: str
    tool_arguments: str

    @property
    def user_context(self) -> T | None:
        return self.run_context.user_context

    @property
    def usage(self) -> Usage:
        return self.run_context.usage
