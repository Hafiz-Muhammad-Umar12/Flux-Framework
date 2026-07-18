"""@tool decorator for creating tools from functions."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable

from ..context import ToolContext
from ..utils.schema import function_to_schema
from .base import ToolResult


class FunctionTool:
    """A tool created from a Python function."""

    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        self._func = func
        self._name = name or func.__name__
        self._description = description or func.__doc__ or f"Tool: {self._name}"
        self._schema = function_to_schema(func)
        self._is_async = asyncio.iscoroutinefunction(func)
        self._accepts_context = _check_context_param(func)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return self._schema

    async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
        """Execute the wrapped function."""
        try:
            if self._accepts_context:
                result = self._func(ctx, **args) if self._is_async else self._func(ctx, **args)
            else:
                result = self._func(**args) if self._is_async else self._func(**args)

            if asyncio.iscoroutine(result):
                result = await result

            return ToolResult(output=str(result), success=True)
        except Exception as e:
            return ToolResult(output=f"Error: {e}", success=False)


def _check_context_param(func: Callable) -> bool:
    """Check if the function accepts a ToolContext or RunContext parameter."""
    sig = inspect.signature(func)
    skip_names = {"ctx", "context", "tool_context", "run_context"}
    for name, param in sig.parameters.items():
        if name in skip_names:
            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                continue
            # Check if annotation relates to context
            ann_str = str(annotation)
            if "context" in ann_str.lower() or "Context" in ann_str:
                return True
    return False


def tool(
    _func: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Callable:
    """Decorator to create a Tool from a function.

    Can be used with or without parentheses:
        @tool
        def my_tool(x: str) -> str: ...

        @tool(name="custom_name", description="Custom description")
        def my_tool(x: str) -> str: ...
    """

    def decorator(func: Callable) -> FunctionTool:
        return FunctionTool(func, name=name, description=description)

    if _func is not None:
        # @tool without parentheses
        return decorator(_func)

    # @tool() with parentheses or @tool(name=...)
    return decorator
