"""File tracer implementation."""

from __future__ import annotations

import json
import time
from typing import Any

from .base import SpanError, _gen_id


class FileSpan:
    """Span that writes JSON to a file."""

    def __init__(
        self, name: str, trace_id: str, file_path: str, depth: int = 0
    ) -> None:
        self._name = name
        self._trace_id = trace_id
        self._span_id = _gen_id()
        self._file_path = file_path
        self._depth = depth
        self._attributes: dict[str, Any] = {}
        self._error: SpanError | None = None
        self._start_time = time.time()

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
        record = {
            "trace_id": self._trace_id,
            "span_id": self._span_id,
            "name": self._name,
            "depth": self._depth,
            "duration_ms": round(elapsed * 1000, 2),
            "attributes": self._attributes,
            "error": self._error.message if self._error else None,
            "timestamp": self._start_time,
        }
        with open(self._file_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def __enter__(self) -> FileSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        self.finish()

    async def __aenter__(self) -> FileSpan:
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.finish()


class FileTracer:
    """Tracer that writes span data as JSON lines to a file."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._trace_id = _gen_id()
        self._depth = 0

    def start_span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> FileSpan:
        span = FileSpan(name, self._trace_id, self._path, self._depth)
        self._depth += 1
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        return span

    def flush(self) -> None:
        pass
