"""Console tracer implementation."""

from __future__ import annotations

import sys
import time
from typing import Any

from .base import SpanError, _gen_id


class ConsoleSpan:
    """Span that prints to stderr."""

    def __init__(self, name: str, trace_id: str, depth: int = 0) -> None:
        self._name = name
        self._trace_id = trace_id
        self._span_id = _gen_id()
        self._depth = depth
        self._attributes: dict[str, Any] = {}
        self._error: SpanError | None = None
        self._start_time = time.time()
        prefix = "  " * depth
        print(f"{prefix}▶ {name}", file=sys.stderr)

    @property
    def trace_id(self) -> str:
        return self._trace_id

    @property
    def span_id(self) -> str:
        return self._span_id

    @property
    def name(self) -> str:
        return self._name

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def set_error(self, error: SpanError) -> None:
        self._error = error

    def finish(self) -> None:
        elapsed = time.time() - self._start_time
        prefix = "  " * self._depth
        status = "✗" if self._error else "✓"
        print(
            f"{prefix}{status} {self._name} ({elapsed:.3f}s)",
            file=sys.stderr,
        )
        if self._error:
            print(f"{prefix}  Error: {self._error.message}", file=sys.stderr)

    def __enter__(self) -> ConsoleSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        self.finish()

    async def __aenter__(self) -> ConsoleSpan:
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.finish()


class ConsoleTracer:
    """Tracer that prints spans to stderr."""

    def __init__(self) -> None:
        self._trace_id = _gen_id()
        self._depth = 0

    def start_span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> ConsoleSpan:
        span = ConsoleSpan(name, self._trace_id, self._depth)
        self._depth += 1
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        return span

    def flush(self) -> None:
        pass
