"""Tracer protocol and span abstractions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class SpanData:
    """Data associated with a span."""

    name: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanError:
    """Error information for a span."""

    message: str
    data: dict[str, Any] | None = None


@runtime_checkable
class Span(Protocol):
    """Protocol for a tracing span."""

    @property
    def trace_id(self) -> str: ...

    @property
    def span_id(self) -> str: ...

    @property
    def name(self) -> str: ...

    def set_attribute(self, key: str, value: Any) -> None: ...

    def set_error(self, error: SpanError) -> None: ...

    def finish(self) -> None: ...

    def __enter__(self) -> Span: ...

    def __exit__(self, *args: Any) -> None: ...

    async def __aenter__(self) -> Span: ...

    async def __aexit__(self, *args: Any) -> None: ...


@runtime_checkable
class Tracer(Protocol):
    """Protocol for a tracing backend."""

    def start_span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> Span: ...

    def flush(self) -> None: ...


class _NoopSpan:
    """No-op span used when tracing is disabled."""

    def __init__(self, name: str = "noop") -> None:
        self._trace_id = _gen_id()
        self._span_id = _gen_id()
        self._name = name

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
        pass

    def set_error(self, error: SpanError) -> None:
        pass

    def finish(self) -> None:
        pass

    def __enter__(self) -> _NoopSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    async def __aenter__(self) -> _NoopSpan:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


class _NoopTracer:
    """No-op tracer that returns no-op spans."""

    def start_span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> _NoopSpan:
        return _NoopSpan(name)

    def flush(self) -> None:
        pass


def _gen_id() -> str:
    return uuid.uuid4().hex[:16]
