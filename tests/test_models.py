"""Tests for models."""

import pytest
from flux.context import Usage
from flux.models.base import ModelSettings, ModelRequest, ModelResponse, Message
from flux.models.registry import ModelRegistry


def test_model_settings_default():
    s = ModelSettings()
    assert s.temperature is None
    assert s.max_tokens is None


def test_model_settings_resolve():
    base = ModelSettings(temperature=0.7, max_tokens=100)
    override = ModelSettings(temperature=0.3)
    result = base.resolve(override)
    assert result.temperature == 0.3
    assert result.max_tokens == 100


def test_model_settings_resolve_none():
    base = ModelSettings(temperature=0.7)
    result = base.resolve(None)
    assert result.temperature == 0.7


def test_model_request():
    req = ModelRequest(
        messages=[Message(role="user", content="Hello")],
        system_prompt="Be helpful",
    )
    assert len(req.messages) == 1
    assert req.system_prompt == "Be helpful"


def test_model_response():
    resp = ModelResponse(content="Hello!")
    assert resp.content == "Hello!"
    assert resp.tool_calls == []
    assert resp.usage is None


def test_model_registry():
    registry = ModelRegistry()

    class FakeModel:
        async def complete(self, request):
            return ModelResponse(content="ok")
        async def stream(self, request):
            yield

    model = FakeModel()
    registry.register("test-model", model)
    resolved = registry.resolve("test-model")
    assert resolved is model


def test_model_registry_provider():
    registry = ModelRegistry()

    class FakeProvider:
        async def complete(self, request):
            return ModelResponse(content="ok")
        async def stream(self, request):
            yield

    provider = FakeProvider()
    registry.register_provider("ollama", provider)
    resolved = registry.resolve("ollama/llama3")
    assert resolved is provider


def test_model_registry_not_found():
    registry = ModelRegistry()
    with pytest.raises(ValueError, match="not found"):
        registry.resolve("nonexistent")


def test_usage_aggregation():
    u1 = Usage(input_tokens=10, output_tokens=5, total_tokens=15, requests=1)
    u2 = Usage(input_tokens=20, output_tokens=10, total_tokens=30, requests=1)
    u1 += u2
    assert u1.input_tokens == 30
    assert u1.output_tokens == 15
    assert u1.total_tokens == 45
    assert u1.requests == 2
