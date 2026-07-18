"""Guardrail protocol and result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""

    passed: bool
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class InputGuardrail:
    """Base class for input guardrails.

    Subclass this or implement `name` and `check` attributes.
    """

    guardrail_type: str = "input"

    @property
    def name(self) -> str:
        """Name of the guardrail."""
        return self.__class__.__name__

    async def check(self, user_input: str, context: Any = None) -> GuardrailResult:
        """Check if the input passes the guardrail."""
        return GuardrailResult(passed=True)


class OutputGuardrail:
    """Base class for output guardrails.

    Subclass this or implement `name` and `check` attributes.
    """

    guardrail_type: str = "output"

    @property
    def name(self) -> str:
        """Name of the guardrail."""
        return self.__class__.__name__

    async def check(self, output: str, context: Any = None) -> GuardrailResult:
        """Check if the output passes the guardrail."""
        return GuardrailResult(passed=True)
