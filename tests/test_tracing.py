"""Tests for tracing."""

import tempfile
import os
from flux.tracing.base import _NoopSpan, _NoopTracer
from flux.tracing.console import ConsoleTracer
from flux.tracing.file import FileTracer


def test_noop_span():
    span = _NoopSpan("test")
    assert span.name == "test"
    assert span.trace_id
    assert span.span_id
    span.set_attribute("key", "value")
    span.finish()  # Should not raise


def test_noop_span_context_manager():
    with _NoopSpan("test") as span:
        span.set_attribute("x", 1)
    # Should not raise


def test_noop_tracer():
    tracer = _NoopTracer()
    span = tracer.start_span("test")
    assert span.name == "test"
    tracer.flush()  # Should not raise


def test_console_tracer():
    tracer = ConsoleTracer()
    span = tracer.start_span("test_span")
    assert span.name == "test_span"
    span.set_attribute("key", "value")
    span.finish()  # Should print to stderr


def test_console_tracer_context_manager():
    tracer = ConsoleTracer()
    with tracer.start_span("test") as span:
        span.set_attribute("x", 1)
    # Should print start and finish


def test_file_tracer():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "trace.jsonl")
        tracer = FileTracer(path)
        span = tracer.start_span("test_span")
        span.set_attribute("key", "value")
        span.finish()

        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 1

        import json
        record = json.loads(lines[0])
        assert record["name"] == "test_span"
        assert record["attributes"]["key"] == "value"
