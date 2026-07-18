"""Tool protocol and result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ..context import ToolContext


@dataclass
class ToolResult:
    """Result of a tool execution."""

    output: str
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Tool(Protocol):
    """Protocol for a tool that can be used by an agent."""

    @property
    def name(self) -> str:
        """Unique name of the tool."""
        ...

    @property
    def description(self) -> str:
        """Description shown to the model."""
        ...

    @property
    def parameters_schema(self) -> dict[str, Any]:
        """JSON Schema for the tool's parameters."""
        ...

    async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given arguments."""
        ...
