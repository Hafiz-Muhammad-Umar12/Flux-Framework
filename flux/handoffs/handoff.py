"""Handoff data structures for agent routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..agent import Agent
    from ..context import ToolContext


@dataclass
class HandoffData:
    """Data passed during a handoff."""

    source_agent_name: str
    target_agent_name: str
    input_text: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Handoff:
    """Agent-to-agent routing."""

    source: Agent
    target: Agent
    description: str = ""
    condition: Callable[[ToolContext, str], bool] | None = None
    input_filter: Callable[[HandoffData], HandoffData] | None = None

    @property
    def tool_name(self) -> str:
        """Tool name used to trigger this handoff."""
        return f"transfer_to_{self.target.name}"

    @property
    def tool_description(self) -> str:
        """Description shown to the model for this handoff."""
        return self.description or f"Transfer to {self.target.name}"

    def should_handoff(self, ctx: ToolContext, user_input: str) -> bool:
        """Check if handoff should trigger."""
        if self.condition is None:
            return True
        return self.condition(ctx, user_input)
