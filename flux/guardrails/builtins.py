"""Built-in guardrails."""

from __future__ import annotations

import re
from typing import Any

from .base import GuardrailResult, InputGuardrail, OutputGuardrail


class LengthGuardrail(InputGuardrail):
    """Rejects text exceeding a character limit."""

    def __init__(self, max_chars: int = 10000) -> None:
        self.max_chars = max_chars

    @property
    def name(self) -> str:
        return "length_guardrail"

    async def check(self, text: str, context: Any = None) -> GuardrailResult:
        if len(text) > self.max_chars:
            return GuardrailResult(
                passed=False,
                message=f"Text length {len(text)} exceeds maximum {self.max_chars}",
            )
        return GuardrailResult(passed=True)


class ProfanityGuardrail(InputGuardrail):
    """Checks for prohibited words."""

    def __init__(self, word_list: list[str] | None = None) -> None:
        self.word_list = [w.lower() for w in (word_list or [])]

    @property
    def name(self) -> str:
        return "profanity_guardrail"

    async def check(self, text: str, context: Any = None) -> GuardrailResult:
        text_lower = text.lower()
        for word in self.word_list:
            if word in text_lower:
                return GuardrailResult(
                    passed=False,
                    message="Prohibited word detected",
                    metadata={"word": word},
                )
        return GuardrailResult(passed=True)


class PIIGuardrail(InputGuardrail):
    """Detects personally identifiable information (emails, phones, SSNs)."""

    _EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    _PHONE_RE = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
    _SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    @property
    def name(self) -> str:
        return "pii_guardrail"

    async def check(self, text: str, context: Any = None) -> GuardrailResult:
        found: list[str] = []
        if self._EMAIL_RE.search(text):
            found.append("email")
        if self._PHONE_RE.search(text):
            found.append("phone")
        if self._SSN_RE.search(text):
            found.append("ssn")
        if found:
            return GuardrailResult(
                passed=False,
                message=f"PII detected: {', '.join(found)}",
                metadata={"pii_types": found},
            )
        return GuardrailResult(passed=True)
