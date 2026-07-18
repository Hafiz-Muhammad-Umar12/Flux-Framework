"""Handoff routing logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .handoff import Handoff


def find_handoff_by_tool_name(
    handoffs: list[Handoff], tool_name: str
) -> Handoff | None:
    """Find a handoff by its tool name."""
    for handoff in handoffs:
        if handoff.tool_name == tool_name:
            return handoff
    return None


def handoff_tool_names(handoffs: list[Handoff]) -> list[str]:
    """Get all handoff tool names."""
    return [h.tool_name for h in handoffs]
