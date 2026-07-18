"""Tool registry for managing tools."""

from __future__ import annotations

from typing import Any

from ..models.base import ToolDef
from .base import Tool


class ToolRegistry:
    """Registry for managing tools by name."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def register_many(self, tools: list[Tool]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def remove(self, name: str) -> None:
        """Remove a tool by name."""
        self._tools.pop(name, None)

    def clear(self) -> None:
        """Remove all tools."""
        self._tools.clear()

    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def to_tool_defs(self) -> list[ToolDef]:
        """Convert all tools to ToolDef list for model requests."""
        return [
            ToolDef(
                name=t.name,
                description=t.description,
                parameters=t.parameters_schema,
            )
            for t in self._tools.values()
        ]
