"""Middleware protocol and base types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol, runtime_checkable


@dataclass
class RequestContext:
    """Request context passed through middleware."""

    agent_name: str
    messages: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Response from the model/middleware chain."""

    content: str | None = None
    tool_calls: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


NextFn = Callable[[RequestContext], Awaitable[Response]]


@runtime_checkable
class Middleware(Protocol):
    """Protocol for middleware."""

    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        """Process the request, calling next() to continue the chain."""
        ...
