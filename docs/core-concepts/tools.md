# Tools

How tools extend agent capabilities with function calling.

---

## Overview

Tools are the mechanism by which agents interact with the outside world. A tool is any callable that an agent can invoke during a conversation -- from simple functions like calculators and string formatters to complex integrations like database queries, API calls, and shell commands.

Flux provides two ways to create tools:

1. **The `@tool` decorator** -- wrap any Python function into a tool in one line
2. **The `Tool` protocol** -- implement a custom tool class for full control

---

## The Tool Protocol

At its core, a tool in Flux satisfies the `Tool` protocol defined in `flux/tools/base.py`:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Tool(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters_schema(self) -> dict[str, Any]: ...

    async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult: ...
```

Any object that implements these four members is a valid Flux tool. The protocol is `@runtime_checkable`, so you can use `isinstance()` checks.

### ToolResult

Every tool execution returns a `ToolResult`:

```python
@dataclass
class ToolResult:
    output: str               # The string result to send back to the model
    success: bool = True      # Whether the execution succeeded
    metadata: dict[str, Any] = field(default_factory=dict)  # Optional metadata
```

The `output` field is always a string. If your tool produces structured data, serialize it to JSON:

```python
return ToolResult(
    output=json.dumps({"temperature": 22, "unit": "C"}),
    success=True,
    metadata={"source": "weather_api"},
)
```

---

## The `@tool` Decorator

The fastest way to create a tool is the `@tool` decorator from `flux/tools/decorator.py`. It wraps a Python function into a `FunctionTool` that auto-generates a JSON Schema from the function's type hints.

### Basic Usage

```python
from flux.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))
```

That is all that is needed. The decorator:

- Uses the function name as the tool name (`calculator`)
- Uses the docstring as the tool description
- Generates a JSON Schema from the `expression: str` parameter
- Handles both sync and async functions automatically

### With Custom Name and Description

Override defaults using keyword arguments:

```python
@tool(name="math_eval", description="Evaluate a mathematical expression safely.")
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))
```

### With Multiple Parameters

Type hints drive the schema generation:

```python
@tool
def search_database(query: str, limit: int = 10, category: str | None = None) -> str:
    """Search the product database.

    Args:
        query: The search query string
        limit: Maximum number of results (default 10)
        category: Optional category filter
    """
    # ... implementation
    return json.dumps(results)
```

This generates a JSON Schema with:

| Parameter | Type | Required |
|---|---|---|
| `query` | `string` | Yes |
| `limit` | `integer` | No (default: 10) |
| `category` | `string` | No (nullable) |

### Async Tools

The `@tool` decorator handles both sync and async functions transparently:

```python
@tool
async def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()
```

### Sync Tools

Synchronous functions work too -- they are called normally inside the async execution path:

```python
@tool
def get_timestamp() -> str:
    """Get the current UTC timestamp."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
```

---

## Context Injection

Tools can receive a `ToolContext` (or `RunContext`) as their first parameter. The decorator detects this automatically and injects the context at execution time:

```python
from flux.context import ToolContext, RunContext

@tool
def get_user_info(ctx: ToolContext, user_id: str) -> str:
    """Get information about a user.

    Args:
        user_id: The unique user identifier
    """
    # Access the run context
    run_ctx: RunContext = ctx.run_context
    usage = ctx.usage
    return f"User {user_id}, requests so far: {usage.requests}"
```

The context parameter is **not** exposed in the JSON Schema -- it is injected silently by the framework. The decorator checks for parameters named `ctx`, `context`, `tool_context`, or `run_context` with context-related type annotations.

---

## JSON Schema Generation

The `function_to_schema()` utility in `flux/utils/schema.py` converts Python function signatures into JSON Schema dictionaries. It handles:

| Python Type | JSON Schema |
|---|---|
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `list[T]` | `{"type": "array", "items": ...}` |
| `dict` | `{"type": "object"}` |
| `T \| None` (Optional) | Schema for `T` (nullable) |
| `Literal["a", "b"]` | `{"enum": ["a", "b"]}` |

Parameters with default values are marked as optional. Parameters without defaults are marked as required.

Docstrings in Google style (`Args:` section) are parsed to provide parameter descriptions in the schema:

```python
@tool
def create_task(title: str, priority: int, tags: list[str]) -> str:
    """Create a new task.

    Args:
        title: The task title
        priority: Priority level (1-5)
        tags: List of tag strings
    """
    return f"Created: {title}"
```

---

## Custom Tool Implementation

For tools that need full control over naming, schema, and execution, implement the `Tool` protocol directly:

```python
from flux.tools.base import Tool, ToolResult
from flux.context import ToolContext

class DatabaseQueryTool:
    """Custom tool that queries a database."""

    def __init__(self, db_connection) -> None:
        self._db = db_connection

    @property
    def name(self) -> str:
        return "db_query"

    @property
    def description(self) -> str:
        return "Execute a read-only SQL query against the database."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL SELECT query to execute",
                }
            },
            "required": ["query"],
        }

    async def execute(self, ctx: ToolContext, args: dict) -> ToolResult:
        query = args.get("query", "")
        if not query.strip().upper().startswith("SELECT"):
            return ToolResult(
                output="Error: Only SELECT queries are allowed",
                success=False,
            )
        try:
            results = await self._db.fetch(query)
            return ToolResult(
                output=json.dumps(results),
                metadata={"row_count": len(results)},
            )
        except Exception as e:
            return ToolResult(output=f"Query error: {e}", success=False)
```

---

## Built-in Tools

Flux ships with three built-in tools in `flux/tools/builtins.py`:

### ShellTool

Executes shell commands and returns their output:

```python
from flux.tools.builtins import ShellTool

agent = Agent(
    name="sys_admin",
    tools=(ShellTool(),),
    instructions="You can run shell commands to help with system administration.",
)
```

| Property | Value |
|---|---|
| Name | `shell` |
| Description | Execute a shell command and return its output |
| Parameters | `command` (string, required) |

The tool runs commands via `asyncio.create_subprocess_shell`, captures both stdout and stderr, and reports success based on the exit code.

### FileReadTool

Reads file contents:

```python
from flux.tools.builtins import FileReadTool

agent = Agent(
    name="reader",
    tools=(FileReadTool(),),
    instructions="You can read files to help users understand code.",
)
```

| Property | Value |
|---|---|
| Name | `file_read` |
| Description | Read the contents of a file |
| Parameters | `path` (string, required) |

### FileWriteTool

Writes content to files, creating parent directories as needed:

```python
from flux.tools.builtins import FileWriteTool

agent = Agent(
    name="writer",
    tools=(FileWriteTool(),),
    instructions="You can create and modify files.",
)
```

| Property | Value |
|---|---|
| Name | `file_write` |
| Description | Write content to a file |
| Parameters | `path` (string, required), `content` (string, required) |

---

## ToolRegistry

The `ToolRegistry` manages a collection of tools by name. It provides lookup, registration, and conversion utilities:

```python
from flux.tools import ToolRegistry, tool

registry = ToolRegistry()

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

@tool
def get_time() -> str:
    """Get current time."""
    return datetime.now().isoformat()

# Register tools
registry.register(calculator)
registry.register(get_time)

# Look up tools
calc = registry.get("calculator")  # Returns the FunctionTool
assert registry.has("calculator")  # True

# List all tools
all_tools = registry.list_tools()  # [calculator, get_time]

# Convert to ToolDef for model requests
tool_defs = registry.to_tool_defs()
# [ToolDef(name="calculator", ...), ToolDef(name="get_time", ...)]
```

### Registry Operations

| Method | Description |
|---|---|
| `register(tool)` | Register a single tool by name |
| `register_many(tools)` | Register a list of tools |
| `get(name)` | Look up a tool by name |
| `has(name)` | Check if a tool exists |
| `remove(name)` | Remove a tool by name |
| `clear()` | Remove all tools |
| `list_tools()` | Return all registered tools |
| `to_tool_defs()` | Convert to `ToolDef` list for model requests |

---

## Using Tools with Agents

Pass tools to an agent as a tuple:

```python
from flux.agent import Agent
from flux.tools import tool

@tool
def lookup_price(product_id: str) -> str:
    """Look up the price of a product by ID."""
    return f"${19.99}"

@tool
def apply_discount(code: str, amount: float) -> str:
    """Apply a discount code to an amount."""
    return f"${amount * 0.9:.2f}"

agent = Agent(
    name="shop_assistant",
    instructions="You help users with product pricing and discounts.",
    tools=(lookup_price, apply_discount),
)
```

---

## Best Practices

!!! tip "Write clear docstrings"
    The docstring becomes the tool description sent to the model. A clear description helps the model decide when and how to use the tool. Describe what it does, when to use it, and any constraints.

!!! tip "Use type hints for schema generation"
    Every parameter should have a type hint. The `@tool` decorator uses these to generate JSON Schema, which the model uses to format its tool calls correctly.

!!! tip "Return string results"
    `ToolResult.output` is always a string. If you return structured data, serialize it to JSON. The model receives this string as the tool's response.

!!! tip "Use ToolResult.metadata for side-channel info"
    Metadata is not sent to the model -- it is available in the runner and middleware for logging, analytics, or debugging.

!!! tip "Keep tools small and focused"
    Each tool should do one thing well. Instead of one `do_everything()` tool, create separate tools for each capability. This gives the model better granularity.

!!! warning "Validate tool inputs"
    Even though the schema constrains what the model sends, always validate inputs inside your tool. Models can and do produce unexpected arguments.

!!! warning "Be cautious with shell and file tools"
    The built-in `ShellTool`, `FileReadTool`, and `FileWriteTool` have broad capabilities. Use guardrails to restrict what the agent can access in production environments.

---

## See Also

- [Agents](agents.md) -- How agents use tools
- [Providers](providers.md) -- How tool calls flow through the model provider
- [Guardrails](guardrails.md) -- Validating tool inputs and outputs
- [Middleware](middleware.md) -- Intercepting and modifying tool execution
