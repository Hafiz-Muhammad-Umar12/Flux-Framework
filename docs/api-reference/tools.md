# Tools API Reference

Complete API reference for `Tool`, `ToolResult`, `FunctionTool`, the `@tool` decorator, `ToolRegistry`, and built-in tools.

---

## `Tool` (Protocol)

::: flux.tools.base.Tool

```python
@runtime_checkable
class Tool(Protocol):
    """Protocol for a tool that can be used by an agent."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters_schema(self) -> dict[str, Any]: ...

    async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult: ...
```

The `Tool` protocol defines the interface that all tools must implement. Because it uses `@runtime_checkable`, you can use `isinstance(obj, Tool)` to check whether an object satisfies the protocol.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Unique identifier for the tool. Used by the model to invoke it. |
| `description` | `str` | Human-readable description shown to the LLM. Should explain what the tool does and when to use it. |
| `parameters_schema` | `dict[str, Any]` | JSON Schema object describing the tool's accepted parameters. |

### Methods

#### `execute`

```python
async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
```

Execute the tool with the given arguments.

| Parameter | Type | Description |
|-----------|------|-------------|
| `ctx` | `ToolContext` | Context for this invocation, providing access to the `RunContext`, tool name, tool call ID, and raw arguments string. |
| `args` | `dict[str, Any]` | Parsed arguments from the model's tool call. |

**Returns:** `ToolResult`

### Implementing a Custom Tool

Any object with the correct properties and an async `execute` method satisfies the protocol:

```python
from flux.tools.base import Tool, ToolResult
from flux.context import ToolContext

class MyTool:
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Does something useful."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The query to process"}
            },
            "required": ["query"],
        }

    async def execute(self, ctx: ToolContext, args: dict) -> ToolResult:
        query = args.get("query", "")
        return ToolResult(output=f"Processed: {query}", success=True)

# Verify protocol compliance
assert isinstance(MyTool(), Tool)  # True
```

---

## `ToolResult`

::: flux.tools.base.ToolResult

```python
@dataclass
class ToolResult:
    """Result of a tool execution."""
    output: str
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
```

Returned by every tool's `execute` method. The `output` string is sent back to the model as a tool result message.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output` | `str` | *required* | The result string returned to the model. |
| `success` | `bool` | `True` | Whether the tool executed successfully. |
| `metadata` | `dict[str, Any]` | `{}` | Arbitrary metadata (e.g., execution time, source URL). |

### Usage

```python
from flux.tools.base import ToolResult

# Success
result = ToolResult(output="Temperature is 72F")

# Failure
result = ToolResult(
    output="File not found: /tmp/data.csv",
    success=False,
    metadata={"file_path": "/tmp/data.csv"},
)
```

---

## `FunctionTool`

::: flux.tools.decorator.FunctionTool

```python
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
```

Wraps a Python function into a `Tool`-compatible object. Schema generation, sync/async handling, and context injection are all handled automatically.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `Callable` | *required* | The function to wrap. |
| `name` | `str \| None` | `None` | Tool name. Defaults to `func.__name__`. |
| `description` | `str \| None` | `None` | Tool description. Defaults to the function's docstring. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | The tool's name. |
| `description` | `str` | The tool's description. |
| `parameters_schema` | `dict[str, Any]` | Auto-generated JSON Schema from type hints and docstring. |

### Methods

#### `execute`

```python
async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
```

Executes the wrapped function. Handles:

- **Async functions**: awaited automatically.
- **Sync functions**: called directly (no thread offload).
- **Context injection**: if the function has a parameter annotated with `ToolContext` or `RunContext` (named `ctx`, `context`, `tool_context`, or `run_context`), it is injected automatically.
- **Exceptions**: caught and returned as `ToolResult(success=False)`.

**Returns:** `ToolResult`

### Usage

```python
from flux.tools.decorator import FunctionTool

def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: First number.
        b: Second number.
    """
    return a + b

tool = FunctionTool(add)
print(tool.name)                # "add"
print(tool.parameters_schema)   # {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}
```

---

## `@tool` Decorator

::: flux.tools.decorator.tool

```python
def tool(
    _func: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Callable:
```

Decorator to create a `FunctionTool` from a Python function. The most common way to define tools in Flux.

Can be used **with or without parentheses**:

```python
from flux.tools.decorator import tool

# Without parentheses
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Sunny in {city}"

# With parentheses
@tool(name="fetch_weather", description="Fetch weather data")
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Sunny in {city}"
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `_func` | `Callable \| None` | `None` | The decorated function (set automatically when used without parentheses). |
| `name` | `str \| None` | `None` | Custom tool name. |
| `description` | `str \| None` | `None` | Custom description. |

**Returns:** `FunctionTool`

### Context Injection

If the function declares a parameter named `ctx`, `context`, `tool_context`, or `run_context` with a context-related type annotation, `ToolContext` is injected at call time:

```python
from flux.context import ToolContext

@tool
def log_message(ctx: ToolContext, message: str) -> str:
    """Log a message with context."""
    print(f"Tool: {ctx.tool_name}, Turn: {ctx.run_context.turn_count}")
    return f"Logged: {message}"
```

### Async Support

Both sync and async functions are supported:

```python
import httpx

@tool
async def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.text
```

### Schema Generation

The `@tool` decorator automatically generates a JSON Schema from:

- **Type hints** on function parameters.
- **Google-style docstrings** (`Args:` section) for parameter descriptions.
- Parameters named `ctx`, `context`, `tool_context`, or `run_context` are excluded from the schema.

```python
@tool
def search(query: str, max_results: int = 5) -> str:
    """Search the web.

    Args:
        query: The search query.
        max_results: Maximum number of results to return.
    """
    return f"Results for: {query}"
```

Generated schema:

```json
{
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query."
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return."
        }
    },
    "required": ["query"]
}
```

---

## `ToolRegistry`

::: flux.tools.registry.ToolRegistry

```python
class ToolRegistry:
    """Registry for managing tools by name."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
```

A container for managing a collection of tools by name. Useful for organizing tools and converting them to `ToolDef` objects for model requests.

### Methods

#### `register`

```python
def register(self, tool: Tool) -> None:
```

Register a single tool. Overwrites any existing tool with the same name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `tool` | `Tool` | The tool to register. |

#### `register_many`

```python
def register_many(self, tools: list[Tool]) -> None:
```

Register multiple tools at once.

| Parameter | Type | Description |
|-----------|------|-------------|
| `tools` | `list[Tool]` | List of tools to register. |

#### `get`

```python
def get(self, name: str) -> Tool | None:
```

Retrieve a tool by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The tool name to look up. |

**Returns:** `Tool | None`

#### `has`

```python
def has(self, name: str) -> bool:
```

Check whether a tool is registered.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The tool name to check. |

**Returns:** `bool`

#### `remove`

```python
def remove(self, name: str) -> None:
```

Remove a tool by name. No error if the tool does not exist.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The tool name to remove. |

#### `clear`

```python
def clear(self) -> None:
```

Remove all registered tools.

#### `list_tools`

```python
def list_tools(self) -> list[Tool]:
```

Return a list of all registered tools.

**Returns:** `list[Tool]`

#### `to_tool_defs`

```python
def to_tool_defs(self) -> list[ToolDef]:
```

Convert all registered tools to `ToolDef` objects suitable for inclusion in a `ModelRequest`.

**Returns:** `list[ToolDef]`

### Usage

```python
from flux.tools.registry import ToolRegistry
from flux.tools.decorator import tool

registry = ToolRegistry()

@tool
def search(query: str) -> str:
    """Search the web."""
    return f"Results for {query}"

@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

# Register tools
registry.register_many([search, calculate])

# Check and retrieve
assert registry.has("search")
assert not registry.has("delete")

# Convert to tool definitions
tool_defs = registry.to_tool_defs()
for td in tool_defs:
    print(f"{td.name}: {td.description}")
```

---

## Built-in Tools

Flux ships with several built-in tools for common operations.

### `ShellTool`

```python
class ShellTool:
    """Execute shell commands."""
```

| Property | Value |
|----------|-------|
| `name` | `"shell"` |
| `description` | Executes a shell command and returns the output. |
| `parameters` | `{"command": str}` — the shell command to run. |

```python
from flux.tools.builtin import ShellTool

shell = ShellTool()
# Available as: Agent(tools=[ShellTool()])
```

!!! warning
    Shell execution can be dangerous. Use only in trusted environments with appropriate sandboxing.

### `FileReadTool`

```python
class FileReadTool:
    """Read file contents."""
```

| Property | Value |
|----------|-------|
| `name` | `"read_file"` |
| `description` | Reads the contents of a file at the given path. |
| `parameters` | `{"path": str}` — absolute or relative file path. |

```python
from flux.tools.builtin import FileReadTool

reader = FileReadTool()
```

### `FileWriteTool`

```python
class FileWriteTool:
    """Write file contents."""
```

| Property | Value |
|----------|-------|
| `name` | `"write_file"` |
| `description` | Writes content to a file at the given path. |
| `parameters` | `{"path": str, "content": str}` |

```python
from flux.tools.builtin import FileWriteTool

writer = FileWriteTool()
```

### Using Built-in Tools

```python
from flux.agent import Agent
from flux.tools.builtin import ShellTool, FileReadTool, FileWriteTool

agent = Agent(
    name="FileAssistant",
    instructions="You can read, write, and execute shell commands.",
    tools=[ShellTool(), FileReadTool(), FileWriteTool()],
)
```
