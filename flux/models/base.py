"""Model protocol, request/response types, settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol, runtime_checkable

from ..context import Usage


@dataclass
class ModelSettings:
    """Model generation settings."""

    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: list[str] | None = None
    seed: int | None = None
    tool_choice: str | dict[str, Any] | None = None
    parallel_tool_calls: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def resolve(self, override: ModelSettings | None) -> ModelSettings:
        """Merge non-None values from override onto self."""
        if override is None:
            return self
        result = ModelSettings()
        for field_name in [
            "temperature",
            "top_p",
            "max_tokens",
            "frequency_penalty",
            "presence_penalty",
            "stop",
            "seed",
            "tool_choice",
            "parallel_tool_calls",
        ]:
            val = getattr(override, field_name, None)
            setattr(result, field_name, val if val is not None else getattr(self, field_name))
        result.extra = {**self.extra, **override.extra}
        return result


@dataclass
class ToolDef:
    """Tool definition sent to the model."""

    name: str
    description: str
    parameters: dict[str, Any]
    strict: bool = True


@dataclass
class ToolCall:
    """A tool call from the model."""

    id: str
    name: str
    arguments: str


@dataclass
class Message:
    """A message in the conversation."""

    role: str  # "system", "user", "assistant", "tool"
    content: str | None = None
    tool_call_id: str | None = None
    name: str | None = None
    tool_calls: list[ToolCall] | None = None


@dataclass
class ModelRequest:
    """Request to a model."""

    messages: list[Message]
    system_prompt: str | None = None
    tools: list[ToolDef] | None = None
    output_schema: dict[str, Any] | None = None
    settings: ModelSettings = field(default_factory=ModelSettings)
    stream: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Response from a model."""

    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage | None = None
    finish_reason: str | None = None
    raw: Any = None


@dataclass
class StreamChunk:
    """A chunk from a streaming model response."""

    delta_text: str | None = None
    tool_call: ToolCall | None = None
    usage: Usage | None = None
    done: bool = False
    raw: Any = None


@runtime_checkable
class Model(Protocol):
    """Protocol for an LLM provider."""

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Get a complete response from the model."""
        ...

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        """Stream a response from the model."""
        ...
        yield  # pragma: no cover
