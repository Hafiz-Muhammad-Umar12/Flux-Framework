"""Tests for tools."""

import json
import pytest
from flux.context import RunContext, ToolContext
from flux.models.base import ToolDef
from flux.tools.base import ToolResult
from flux.tools.decorator import FunctionTool, tool
from flux.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_tool_decorator():
    @tool
    def greet(name: str) -> str:
        """Say hello."""
        return f"Hello {name}"

    assert isinstance(greet, FunctionTool)
    assert greet.name == "greet"
    assert greet.description == "Say hello."
    assert "name" in greet.parameters_schema["properties"]


@pytest.mark.asyncio
async def test_tool_execute():
    @tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    ctx = ToolContext(
        run_context=RunContext(),
        tool_name="add",
        tool_call_id="call_1",
        tool_arguments="{}",
    )
    result = await add.execute(ctx, {"a": 2, "b": 3})
    assert result.success
    assert result.output == "5"


@pytest.mark.asyncio
async def test_tool_error_handling():
    @tool
    def fail() -> str:
        """Always fails."""
        raise ValueError("boom")

    ctx = ToolContext(
        run_context=RunContext(),
        tool_name="fail",
        tool_call_id="call_1",
        tool_arguments="{}",
    )
    result = await fail.execute(ctx, {})
    assert not result.success
    assert "boom" in result.output


def test_tool_decorator_with_custom_name():
    @tool(name="custom_name", description="Custom desc")
    def my_func(x: str) -> str:
        return x

    assert my_func.name == "custom_name"
    assert my_func.description == "Custom desc"


def test_tool_registry():
    registry = ToolRegistry()

    @tool
    def tool_a() -> str:
        """Tool A."""
        return "a"

    registry.register(tool_a)
    assert registry.has("tool_a")
    assert registry.get("tool_a") is tool_a
    assert len(registry.list_tools()) == 1

    registry.remove("tool_a")
    assert not registry.has("tool_a")


def test_tool_registry_to_tool_defs():
    registry = ToolRegistry()

    @tool
    def search(query: str) -> str:
        """Search something."""
        return "results"

    registry.register(search)
    defs = registry.to_tool_defs()
    assert len(defs) == 1
    assert isinstance(defs[0], ToolDef)
    assert defs[0].name == "search"


@pytest.mark.asyncio
async def test_async_tool():
    @tool
    async def async_greet(name: str) -> str:
        """Async greeting."""
        return f"Hello {name}"

    ctx = ToolContext(
        run_context=RunContext(),
        tool_name="async_greet",
        tool_call_id="call_1",
        tool_arguments="{}",
    )
    result = await async_greet.execute(ctx, {"name": "World"})
    assert result.success
    assert result.output == "Hello World"
