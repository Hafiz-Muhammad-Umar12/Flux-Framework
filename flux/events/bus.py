"""Event bus for decoupled observability."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable


# Event type constants
AGENT_START = "agent.start"
AGENT_END = "agent.end"
LLM_START = "llm.start"
LLM_END = "llm.end"
TOOL_START = "tool.start"
TOOL_END = "tool.end"
HANDOFF = "handoff"
GUARDRAIL_CHECK = "guardrail.check"
GUARDRAIL_TRIGGERED = "guardrail.triggered"
STREAM_CHUNK = "stream.chunk"
RUN_START = "run.start"
RUN_END = "run.end"


@dataclass(frozen=True)
class Event:
    """Base event."""

    type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """Decoupled event bus for observability."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = {}
        self._global_handlers: list[Callable] = []

    def on(self, event_type: str, handler: Callable) -> None:
        """Subscribe to a specific event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def on_all(self, handler: Callable) -> None:
        """Subscribe to all events."""
        self._global_handlers.append(handler)

    def off(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    def emit(self, event: Event) -> None:
        """Emit an event (sync handlers only)."""
        for handler in self._handlers.get(event.type, []):
            handler(event)
        for handler in self._global_handlers:
            handler(event)

    async def emit_async(self, event: Event) -> None:
        """Emit an event (handles both sync and async handlers)."""
        for handler in self._handlers.get(event.type, []):
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        for handler in self._global_handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)

    def clear(self) -> None:
        """Remove all handlers."""
        self._handlers.clear()
        self._global_handlers.clear()


# Global event bus singleton
_default_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus."""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def set_event_bus(bus: EventBus) -> None:
    """Set the global event bus."""
    global _default_bus
    _default_bus = bus
