# Utilities API Reference

Complete API reference for utility functions, context types, exceptions, configuration, and tracing.

---

## Schema Utilities

### `function_to_schema`

::: flux.utils.schema.function_to_schema

```python
def function_to_schema(func: Any) -> dict[str, Any]:
```

Convert a Python function to a JSON Schema dict suitable for use as the `parameters` field in a tool definition.

| Parameter | Type | Description |
|-----------|------|-------------|
| `func` | `Callable` | The function to convert. |

**Returns:** `dict[str, Any]` — a JSON Schema object with `"type": "object"`, `"properties"`, and optionally `"required"`.

#### Type Mapping

| Python Type | JSON Schema Type |
|-------------|-----------------|
| `str` | `"string"` |
| `int` | `"integer"` |
| `float` | `"number"` |
| `bool` | `"boolean"` |
| `list[T]` | `{"type": "array", "items": <schema of T>}` |
| `dict` | `"object"` |
| `Optional[T]` | Schema of `T` |
| `Union[A, B]` | `{"anyOf": [<schema of A>, <schema of B>]}` |
| `Literal["a", "b"]` | `{"enum": ["a", "b"]}` |

#### Features

- Extracts parameter descriptions from **Google-style docstrings** (`Args:` section).
- Skips context parameters (`ctx`, `context`, `tool_context`, `run_context`) from the schema.
- Handles `from __future__ import annotations` (string annotations) by evaluating them.

#### Usage

```python
from flux.utils.schema import function_to_schema

def search(query: str, max_results: int = 5) -> str:
    """Search the web.

    Args:
        query: The search query string.
        max_results: Maximum results to return.
    """
    return f"Results for {query}"

schema = function_to_schema(search)
# {
#     "type": "object",
#     "properties": {
#         "query": {"type": "string", "description": "The search query string."},
#         "max_results": {"type": "integer", "description": "Maximum results to return."}
#     },
#     "required": ["query"]
# }
```

---

## Token Utilities

### `count_tokens`

::: flux.utils.tokens.count_tokens

```python
def count_tokens(text: str, model: str | None = None) -> int:
```

Count the number of tokens in a text string.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | *required* | The text to count tokens in. |
| `model` | `str \| None` | `None` | Model name for tiktoken encoding selection. Defaults to `"gpt-4"`. |

**Returns:** `int` — the number of tokens.

#### Behavior

- Uses `tiktoken` if available for accurate counting.
- Falls back to a rough estimate (`len(text) // 4`) when tiktoken is not installed.

```python
from flux.utils.tokens import count_tokens

count_tokens("Hello, world!")        # ~4
count_tokens("Hello, world!", model="gpt-4o")  # accurate with tiktoken
```

### `truncate_to_tokens`

::: flux.utils.tokens.truncate_to_tokens

```python
def truncate_to_tokens(text: str, max_tokens: int, model: str | None = None) -> str:
```

Truncate text to fit within a maximum token count.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | *required* | The text to truncate. |
| `max_tokens` | `int` | *required* | Maximum number of tokens allowed. |
| `model` | `str \| None` | `None` | Model name for tiktoken encoding. |

**Returns:** `str` — the truncated text (or the original if it fits).

```python
from flux.utils.tokens import truncate_to_tokens

long_text = "word " * 10000
short = truncate_to_tokens(long_text, max_tokens=100)
```

---

## Pretty-Print Utilities

### `pretty_result`

::: flux.utils.pretty.pretty_result

```python
def pretty_result(result: Any) -> str:
```

Format a `RunResult` as a human-readable string.

| Parameter | Type | Description |
|-----------|------|-------------|
| `result` | `Any` | A `RunResult` instance. |

**Returns:** `str`

```python
from flux.utils.pretty import pretty_result
print(pretty_result(run_result))
# ═══ Flux Run Result ═══
#   Agent:  WeatherBot
#   Turns:  1
#   Tokens: 42 (in=25, out=17)
# ────────────────────────
#   Output: The weather is sunny.
# ═══════════════════════
```

### `pretty_error`

::: flux.utils.pretty.pretty_error

```python
def pretty_error(error: Exception) -> str:
```

Format an exception as a short string.

| Parameter | Type | Description |
|-----------|------|-------------|
| `error` | `Exception` | The exception to format. |

**Returns:** `str` — e.g., `"ProviderError: Provider 'openai' error (429): Rate limited"`

```python
from flux.utils.pretty import pretty_error

try:
    ...
except Exception as e:
    print(pretty_error(e))
```

### `pretty_tool_call`

::: flux.utils.pretty.pretty_tool_call

```python
def pretty_tool_call(name: str, args: dict[str, Any]) -> str:
```

Format a tool call as a readable string.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Tool name. |
| `args` | `dict[str, Any]` | Tool arguments. |

**Returns:** `str` — e.g., `"-> get_weather(city='NYC')"`

```python
from flux.utils.pretty import pretty_tool_call
print(pretty_tool_call("get_weather", {"city": "NYC", "units": "imperial"}))
# -> get_weather(city='NYC', units='imperial')
```

### `pretty_stream_delta`

::: flux.utils.pretty.pretty_stream_delta

```python
def pretty_stream_delta(delta: str) -> str:
```

Print a streaming text delta to stdout (no newline) and return the delta string.

| Parameter | Type | Description |
|-----------|------|-------------|
| `delta` | `str` | The text delta. |

**Returns:** `str` — the same delta string.

```python
from flux.utils.pretty import pretty_stream_delta

for event in stream:
    if hasattr(event, "delta"):
        pretty_stream_delta(event.delta)  # Prints inline
```

---

## Context Types

### `Usage`

::: flux.context.Usage

```python
@dataclass
class Usage:
    """Token usage tracking."""
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
```

Tracks cumulative token usage across an agent run.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `requests` | `int` | `0` | Number of model requests made. |
| `input_tokens` | `int` | `0` | Total input (prompt) tokens. |
| `output_tokens` | `int` | `0` | Total output (completion) tokens. |
| `total_tokens` | `int` | `0` | Total tokens (input + output). |

#### Methods

##### `add`

```python
def add(self, other: Usage) -> None:
```

Aggregate usage from another `Usage` instance by adding all fields.

| Parameter | Type | Description |
|-----------|------|-------------|
| `other` | `Usage` | The usage to add. |

Also supports `+=` via `__iadd__`.

```python
from flux.context import Usage

total = Usage()
total += Usage(input_tokens=100, output_tokens=50, total_tokens=150, requests=1)
total += Usage(input_tokens=80, output_tokens=30, total_tokens=110, requests=1)

print(total.input_tokens)   # 180
print(total.output_tokens)  # 80
print(total.total_tokens)   # 260
print(total.requests)       # 2
```

---

### `RunContext`

::: flux.context.RunContext

```python
@dataclass
class RunContext(Generic[T]):
    """Context carried through a run."""
    user_context: T | None = None
    usage: Usage = field(default_factory=Usage)
    turn_count: int = 0
    _metadata: dict[str, Any] = field(default_factory=dict)
```

Context object carried through an agent run. Provides access to user context, usage tracking, turn count, and arbitrary metadata.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_context` | `T \| None` | `None` | User-supplied context object (passed via `Runner.run(context=...)`). Generic type `T` can be any type. |
| `usage` | `Usage` | `Usage()` | Cumulative token usage for the run. |
| `turn_count` | `int` | `0` | Current turn number (1-indexed during execution). |

#### Methods

##### `get_metadata`

```python
def get_metadata(self, key: str, default: Any = None) -> Any:
```

Retrieve a metadata value by key.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `str` | *required* | The metadata key. |
| `default` | `Any` | `None` | Default value if key is not found. |

**Returns:** `Any`

##### `set_metadata`

```python
def set_metadata(self, key: str, value: Any) -> None:
```

Set a metadata value.

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `str` | The metadata key. |
| `value` | `Any` | The value to store. |

#### Usage

```python
from flux.context import RunContext

# In a Runner context
ctx = RunContext(user_context={"user_id": "u123", "name": "Alice"})

# Access user context
print(ctx.user_context["name"])  # "Alice"

# Use metadata
ctx.set_metadata("cache_hit", True)
ctx.get_metadata("cache_hit")  # True
```

---

### `ToolContext`

::: flux.context.ToolContext

```python
@dataclass
class ToolContext(Generic[T]):
    """Context for a single tool invocation."""
    run_context: RunContext[T]
    tool_name: str
    tool_call_id: str
    tool_arguments: str
```

Context object passed to every tool's `execute` method. Provides access to the current tool invocation details and the parent `RunContext`.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_context` | `RunContext[T]` | The parent run context. |
| `tool_name` | `str` | Name of the tool being invoked. |
| `tool_call_id` | `str` | Unique identifier for this tool call. |
| `tool_arguments` | `str` | Raw JSON arguments string from the model. |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `user_context` | `T \| None` | Shortcut to `run_context.user_context`. |
| `usage` | `Usage` | Shortcut to `run_context.usage`. |

#### Usage

```python
from flux.tools.decorator import tool
from flux.context import ToolContext

@tool
def log_action(ctx: ToolContext, message: str) -> str:
    """Log an action with full context."""
    print(f"Tool: {ctx.tool_name}")
    print(f"Call ID: {ctx.tool_call_id}")
    print(f"User: {ctx.user_context}")
    print(f"Turn: {ctx.run_context.turn_count}")
    ctx.usage.requests += 1  # Track custom usage
    return f"Logged: {message}"
```

---

## Exceptions

::: flux.exceptions

All exceptions inherit from `FluxError`.

### Exception Hierarchy

```
FluxError
├── MaxTurnsExceeded
├── ModelBehaviorError
├── UserError
├── ToolError
├── ToolTimeoutError
├── GuardrailTripwireError
│   ├── InputGuardrailTripwireTriggered
│   └── OutputGuardrailTripwireTriggered
├── HandoffError
├── ProviderError
└── ConfigurationError
```

### `FluxError`

```python
class FluxError(Exception):
    """Base exception for all Flux errors."""
```

Base class for all Flux exceptions. Catch this to handle any Flux-related error.

### `MaxTurnsExceeded`

```python
class MaxTurnsExceeded(FluxError):
    """Raised when the agent exceeds the maximum number of turns."""
    def __init__(self, message: str = "Maximum turns exceeded"):
        self.message = message
```

Raised by the Runner when the agent exceeds `AgentSettings.max_turns` or `FluxConfig.default_max_turns`.

### `ModelBehaviorError`

```python
class ModelBehaviorError(FluxError):
    """Raised when the model produces unexpected output."""
    def __init__(self, message: str = "Model produced unexpected output"):
        self.message = message
```

Raised when the model returns an empty response or other unexpected output.

### `UserError`

```python
class UserError(FluxError):
    """Raised on developer misuse of the framework."""
    def __init__(self, message: str = "Invalid framework usage"):
        self.message = message
```

Raised when the framework is used incorrectly (e.g., invalid configuration).

### `ToolError`

```python
class ToolError(FluxError):
    """Raised when a tool execution fails."""
    def __init__(self, tool_name: str, tool_error: str):
        self.tool_name = tool_name
        self.tool_error = tool_error
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `tool_name` | `str` | Name of the failing tool. |
| `tool_error` | `str` | Error description. |

### `ToolTimeoutError`

```python
class ToolTimeoutError(FluxError):
    """Raised when a tool execution times out."""
    def __init__(self, tool_name: str, timeout_seconds: float):
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `tool_name` | `str` | Name of the timing-out tool. |
| `timeout_seconds` | `float` | Timeout duration in seconds. |

### `GuardrailTripwireError`

```python
class GuardrailTripwireError(FluxError):
    """Raised when a guardrail tripwire is triggered."""
    def __init__(self, guardrail_name: str, details: str = ""):
        self.guardrail_name = guardrail_name
        self.details = details
```

Base class for guardrail errors.

### `InputGuardrailTripwireTriggered`

```python
class InputGuardrailTripwireTriggered(GuardrailTripwireError):
    """Raised when an input guardrail is triggered."""
```

Raised when an input guardrail blocks the user's message.

### `OutputGuardrailTripwireTriggered`

```python
class OutputGuardrailTripwireTriggered(GuardrailTripwireError):
    """Raised when an output guardrail is triggered."""
```

Raised when an output guardrail blocks the model's response.

### `HandoffError`

```python
class HandoffError(FluxError):
    """Raised when a handoff fails."""
```

Raised when an agent handoff fails (e.g., target agent not found).

### `ProviderError`

```python
class ProviderError(FluxError):
    """Raised when an LLM provider returns an error."""
    def __init__(self, provider: str, message: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `provider` | `str` | Provider name (e.g., `"openai"`, `"anthropic"`, `"ollama"`). |
| `status_code` | `int \| None` | HTTP status code, if applicable. |

### `ConfigurationError`

```python
class ConfigurationError(FluxError):
    """Raised on invalid configuration."""
```

### Exception Handling Example

```python
from flux.runner import Runner
from flux.agent import Agent
from flux.exceptions import (
    FluxError,
    MaxTurnsExceeded,
    ProviderError,
    ToolError,
    InputGuardrailTripwireTriggered,
)

agent = Agent(name="Bot", instructions="You are helpful.")

try:
    result = await Runner.run(agent, "Hello!")
except InputGuardrailTripwireTriggered as e:
    print(f"Blocked by guardrail: {e.guardrail_name}")
except MaxTurnsExceeded:
    print("Agent took too many turns")
except ProviderError as e:
    print(f"Provider {e.provider} failed (HTTP {e.status_code}): {e}")
except ToolError as e:
    print(f"Tool {e.tool_name} failed: {e.tool_error}")
except FluxError as e:
    print(f"General Flux error: {e}")
```

---

## Configuration

### `FluxConfig`

::: flux.config.FluxConfig

```python
@dataclass
class FluxConfig:
    """Global configuration."""
    default_model: str = "llama3.2"
    default_max_turns: int = 10
    default_model_settings: ModelSettings = field(default_factory=ModelSettings)
    event_bus_enabled: bool = True
    tracing_enabled: bool = False
    log_level: str = "INFO"
    model_registry: ModelRegistry | None = None
```

Global configuration for the Flux framework. Controls default model selection, turn limits, observability, and more.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `default_model` | `str` | `"llama3.2"` | Default model name resolved via `ModelRegistry`. |
| `default_max_turns` | `int` | `10` | Default maximum turns for all runs. |
| `default_model_settings` | `ModelSettings` | `ModelSettings()` | Default generation settings applied to all model requests. |
| `event_bus_enabled` | `bool` | `True` | Whether the Runner emits events to the global `EventBus`. |
| `tracing_enabled` | `bool` | `False` | Whether tracing is active. |
| `log_level` | `str` | `"INFO"` | Logging level for framework internals. |
| `model_registry` | `ModelRegistry \| None` | `None` | Custom model registry. Falls back to the global default registry if `None`. |

### `get_config`

```python
def get_config() -> FluxConfig:
```

Get the global `FluxConfig` singleton. Creates a default config if none has been set.

**Returns:** `FluxConfig`

### `set_config`

```python
def set_config(config: FluxConfig) -> None:
```

Set the global `FluxConfig` singleton.

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `FluxConfig` | The configuration to set globally. |

### Usage

```python
from flux.config import FluxConfig, set_config, get_config
from flux.models.base import ModelSettings

# Set a custom configuration
set_config(FluxConfig(
    default_model="gpt-4o",
    default_max_turns=20,
    default_model_settings=ModelSettings(temperature=0.7),
    event_bus_enabled=False,
    tracing_enabled=True,
))

# Retrieve it later
config = get_config()
print(config.default_model)  # "gpt-4o"
```

---

## Tracing

The tracing package (`flux.tracing`) provides structured tracing for debugging and performance monitoring.

---

### `Tracer` (Protocol)

::: flux.tracing.base.Tracer

```python
@runtime_checkable
class Tracer(Protocol):
    """Protocol for a tracing backend."""

    def start_span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> Span: ...

    def flush(self) -> None: ...
```

The interface for all tracer implementations.

#### Methods

##### `start_span`

```python
def start_span(
    self, name: str, attributes: dict[str, Any] | None = None
) -> Span:
```

Start a new tracing span.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Span name (e.g., `"agent.run"`, `"llm.complete"`). |
| `attributes` | `dict[str, Any] \| None` | `None` | Initial attributes to set on the span. |

**Returns:** `Span`

##### `flush`

```python
def flush(self) -> None:
```

Flush any buffered span data to the output destination.

---

### `Span` (Protocol)

::: flux.tracing.base.Span

```python
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
```

A tracing span represents a unit of work. Spans support both synchronous (`with`) and asynchronous (`async with`) context managers.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `trace_id` | `str` | The trace identifier (shared across all spans in a trace). |
| `span_id` | `str` | This span's unique identifier. |
| `name` | `str` | The span name. |

#### Methods

##### `set_attribute`

```python
def set_attribute(self, key: str, value: Any) -> None:
```

Set an attribute on the span.

##### `set_error`

```python
def set_error(self, error: SpanError) -> None:
```

Record an error on the span.

##### `finish`

```python
def finish(self) -> None:
```

Mark the span as complete. Calculates duration and outputs the span data.

#### Context Manager Usage

```python
from flux.tracing import Tracer

tracer = MyTracer()

# Sync
with tracer.start_span("my_operation") as span:
    span.set_attribute("key", "value")
    # ... do work ...

# Async
async with tracer.start_span("my_async_operation") as span:
    # ... do async work ...
    pass
```

---

### `SpanData`

::: flux.tracing.base.SpanData

```python
@dataclass
class SpanData:
    """Data associated with a span."""
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
```

A data container for span information.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | The span name. |
| `attributes` | `dict[str, Any]` | `{}` | Key-value attributes. |

---

### `SpanError`

::: flux.tracing.base.SpanError

```python
@dataclass
class SpanError:
    """Error information for a span."""
    message: str
    data: dict[str, Any] | None = None
```

Error information attached to a span.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | *required* | Error description. |
| `data` | `dict[str, Any] \| None` | `None` | Additional error data (e.g., stack trace, error code). |

### Usage

```python
from flux.tracing.base import SpanError

error = SpanError(
    message="Model returned 429 Too Many Requests",
    data={"status_code": 429, "retry_after": 30},
)

with tracer.start_span("llm_request") as span:
    try:
        response = await model.complete(request)
    except Exception as e:
        span.set_error(SpanError(message=str(e)))
        raise
```

---

### `ConsoleTracer`

::: flux.tracing.console.ConsoleTracer

```python
class ConsoleTracer:
    """Tracer that prints spans to stderr."""

    def __init__(self) -> None:
        self._trace_id = _gen_id()
        self._depth = 0
```

A tracer that outputs span information to stderr with indentation reflecting nesting depth.

#### Behavior

- Prints `"<span_name>"` when a span starts.
- Prints `"* <span_name> (<duration>s)"` when a span finishes.
- Prints `"  Error: <message>"` if the span has an error.
- Nested spans are indented by depth level.

#### Usage

```python
from flux.tracing import ConsoleTracer

tracer = ConsoleTracer()

with tracer.start_span("agent.run") as outer:
    outer.set_attribute("agent", "WeatherBot")

    with tracer.start_span("llm.complete") as inner:
        inner.set_attribute("model", "gpt-4o")
        # ... model call ...

    with tracer.start_span("tool.execute") as tool_span:
        tool_span.set_attribute("tool", "get_weather")
        # ... tool call ...
```

**stderr output:**

```
> agent.run
  > llm.complete
  * llm.complete (0.342s)
  > tool.execute
  * tool.execute (0.015s)
* agent.run (0.361s)
```

---

### `FileTracer`

::: flux.tracing.file.FileTracer

```python
class FileTracer:
    """Tracer that writes span data as JSON lines to a file."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._trace_id = _gen_id()
        self._depth = 0
```

A tracer that writes span data as newline-delimited JSON (JSONL) to a file. Useful for post-run analysis and visualization.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | *required* | Path to the output file. Created or appended to on each span finish. |

#### Output Format

Each span is written as a single JSON line:

```json
{
    "trace_id": "a1b2c3d4e5f6",
    "span_id": "f6e5d4c3b2a1",
    "name": "llm.complete",
    "depth": 1,
    "duration_ms": 342.15,
    "attributes": {"model": "gpt-4o", "tokens": 42},
    "error": null,
    "timestamp": 1721234567.89
}
```

#### Usage

```python
from flux.tracing import FileTracer

tracer = FileTracer("traces.jsonl")

with tracer.start_span("agent.run") as span:
    span.set_attribute("agent", "WeatherBot")
    # ... run agent ...

tracer.flush()
```

#### Analyzing Traces

```python
import json

with open("traces.jsonl") as f:
    for line in f:
        span = json.loads(line)
        print(f"{span['name']}: {span['duration_ms']}ms (depth={span['depth']})")
```

---

## Complete Example

Here is a complete example tying together context, tracing, configuration, and error handling:

```python
import asyncio
from flux.agent import Agent, AgentSettings
from flux.runner import Runner
from flux.config import FluxConfig, set_config
from flux.context import RunContext
from flux.tools.decorator import tool
from flux.models.openai_provider import OpenAIModel
from flux.exceptions import FluxError, ProviderError
from flux.tracing import ConsoleTracer

# Configure
set_config(FluxConfig(
    default_model="gpt-4o-mini",
    default_max_turns=10,
    tracing_enabled=True,
))

# Define a tool
@tool
def get_time(ctx) -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().isoformat()

# Define the agent
agent = Agent(
    name="TimeBot",
    instructions="You tell users the current time.",
    tools=[get_time],
    settings=AgentSettings(max_turns=5),
)

# Run with context and error handling
async def main():
    try:
        result = await Runner.run(
            agent,
            "What time is it?",
            context={"user_id": "u123"},
        )
        print(f"Output: {result.final_output}")
        print(f"Turns: {result.turns}")
        print(f"Tokens: {result.usage.total_tokens}")
    except ProviderError as e:
        print(f"Provider error: {e.provider} - {e}")
    except FluxError as e:
        print(f"Flux error: {e}")

asyncio.run(main())
```
