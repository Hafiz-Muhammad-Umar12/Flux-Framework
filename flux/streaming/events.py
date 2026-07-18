"""Stream event types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union


@dataclass(frozen=True)
class TextDeltaEvent:
    """Incremental text from the model."""

    delta: str


@dataclass(frozen=True)
class ToolCallDeltaEvent:
    """Incremental tool call arguments."""

    tool_call_id: str
    name: str | None = None
    arguments_delta: str = ""


@dataclass(frozen=True)
class ToolCallEvent:
    """Complete tool call."""

    tool_call_id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class MessageCompleteEvent:
    """Full message from the model."""

    content: str | None = None
    tool_calls: list[ToolCallEvent] = field(default_factory=list)


@dataclass(frozen=True)
class UsageEvent:
    """Token usage update."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class ErrorEvent:
    """Error during streaming."""

    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentUpdatedEvent:
    """Agent changed (on handoff)."""

    agent_name: str


StreamEvent = Union[
    TextDeltaEvent,
    ToolCallDeltaEvent,
    ToolCallEvent,
    MessageCompleteEvent,
    UsageEvent,
    ErrorEvent,
    AgentUpdatedEvent,
]
