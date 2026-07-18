"""Test fixtures and FakeModel."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import pytest

from flux.agent import Agent
from flux.context import Usage
from flux.models.base import ModelRequest, ModelResponse, StreamChunk, ToolCall
from flux.tools.decorator import tool


class FakeModel:
    """Mock model that returns scripted responses."""

    def __init__(self, responses: list[ModelResponse] | None = None) -> None:
        self._responses = responses or []
        self._call_count = 0
        self.last_request: ModelRequest | None = None

    @property
    def call_count(self) -> int:
        return self._call_count

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self._call_count += 1
        self.last_request = request
        if self._call_count <= len(self._responses):
            return self._responses[self._call_count - 1]
        return ModelResponse(content="I have no more responses.")

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        self._call_count += 1
        self.last_request = request
        if self._call_count <= len(self._responses):
            resp = self._responses[self._call_count - 1]
            if resp.content:
                yield StreamChunk(delta_text=resp.content, done=True)
            for tc in resp.tool_calls:
                yield StreamChunk(tool_call=tc, done=True)
        else:
            yield StreamChunk(delta_text="No more responses.", done=True)


def fake_response(content: str) -> ModelResponse:
    """Create a simple fake response."""
    return ModelResponse(
        content=content,
        usage=Usage(input_tokens=10, output_tokens=20, total_tokens=30, requests=1),
    )


def fake_tool_response(tool_name: str, args: dict[str, Any]) -> ModelResponse:
    """Create a fake response with a tool call."""
    return ModelResponse(
        tool_calls=[
            ToolCall(
                id="call_1",
                name=tool_name,
                arguments=json.dumps(args),
            )
        ],
        usage=Usage(input_tokens=10, output_tokens=5, total_tokens=15, requests=1),
    )


@pytest.fixture
def fake_model() -> FakeModel:
    return FakeModel()


@pytest.fixture
def simple_agent(fake_model: FakeModel) -> Agent:
    return Agent(
        name="TestBot",
        instructions="You are a test bot.",
        model=fake_model,
    )


@pytest.fixture
def sample_tool() -> Any:
    @tool
    def echo(message: str) -> str:
        """Echo the message back."""
        return f"Echo: {message}"

    return echo
