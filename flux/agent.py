"""Agent definition — the core user-facing abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Callable

from .context import RunContext
from .models.base import Model, ModelSettings

if TYPE_CHECKING:
    from .guardrails.base import InputGuardrail, OutputGuardrail
    from .handoffs.handoff import Handoff
    from .tools.base import Tool


@dataclass
class AgentSettings:
    """Agent-level settings."""

    max_turns: int = 10
    model_settings: ModelSettings = field(default_factory=ModelSettings)


@dataclass(frozen=True)
class Agent:
    """An agent that can use tools, hand off to other agents, and follow guardrails.

    Agent is immutable — use `clone()` to create modified copies.
    """

    name: str
    instructions: str | Callable[..., str] = ""
    model: str | Model | None = None
    tools: tuple[Tool, ...] = ()
    handoffs: tuple[Handoff | Agent, ...] = ()
    guardrails: tuple[InputGuardrail | OutputGuardrail, ...] = ()
    output_type: type | None = None
    settings: AgentSettings = field(default_factory=AgentSettings)

    def get_instructions(self, context: RunContext | None = None) -> str:
        """Resolve instructions (handles both string and callable)."""
        if callable(self.instructions):
            return self.instructions(context)
        return self.instructions

    def clone(self, **kwargs: Any) -> Agent:
        """Create a modified copy of this agent."""
        return replace(self, **kwargs)
