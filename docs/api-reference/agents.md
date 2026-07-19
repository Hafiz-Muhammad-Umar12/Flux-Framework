# Agents API Reference

Complete API reference for `Agent`, `AgentSettings`, `Runner`, `RunResult`, and `StreamResult`.

---

## `AgentSettings`

::: flux.agent.AgentSettings

```python
@dataclass
class AgentSettings:
    """Agent-level settings."""
    max_turns: int = 10
    model_settings: ModelSettings = field(default_factory=ModelSettings)
```

Agent-level settings that control execution behavior. Passed as the `settings` field on an `Agent`.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_turns` | `int` | `10` | Maximum number of LLM turns before the run is aborted with `MaxTurnsExceeded`. |
| `model_settings` | `ModelSettings` | `ModelSettings()` | Model generation settings (temperature, max_tokens, etc.) applied to every request this agent makes. |

### Usage

```python
from flux.agent import AgentSettings
from flux.models.base import ModelSettings

# Use defaults
settings = AgentSettings()

# Custom settings
settings = AgentSettings(
    max_turns=20,
    model_settings=ModelSettings(temperature=0.5, max_tokens=4096),
)
```

!!! note
    `AgentSettings.max_turns` is resolved at run time: the Runner takes the **minimum** of `agent.settings.max_turns` and `config.default_max_turns`.

---

## `Agent`

::: flux.agent.Agent

```python
@dataclass(frozen=True)
class Agent:
    """An agent that can use tools, hand off to other agents, and follow guardrails.
    Agent is immutable — use clone() to create modified copies.
    """
    name: str
    instructions: str | Callable[..., str] = ""
    model: str | Model | None = None
    tools: tuple[Tool, ...] = ()
    handoffs: tuple[Handoff | Agent, ...] = ()
    guardrails: tuple[InputGuardrail | OutputGuardrail, ...] = ()
    output_type: type | None = None
    settings: AgentSettings = field(default_factory=AgentSettings)
```

The core abstraction in Flux. An `Agent` represents an autonomous entity that can:

- Receive instructions (static string or dynamic callable).
- Use tools to interact with external systems.
- Hand off conversations to other agents.
- Enforce input and output guardrails.
- Produce structured output via `output_type`.

Because the dataclass is **frozen**, all fields are immutable after construction. Use [`clone()`](#clone) to create modified copies.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | A human-readable name for the agent. Used in logs, events, and as the default handoff tool name prefix. |
| `instructions` | `str \| Callable[..., str]` | `""` | The system prompt. If a callable, it is invoked at run time with the current `RunContext` and must return a string. |
| `model` | `str \| Model \| None` | `None` | Model to use. A string is resolved via the `ModelRegistry`; a `Model` instance is used directly. When `None`, the config default is used. |
| `tools` | `tuple[Tool, ...]` | `()` | Tools the agent is allowed to call. |
| `handoffs` | `tuple[Handoff \| Agent, ...]` | `()` | Other agents this agent can hand off to. An `Agent` is auto-wrapped in a `Handoff` with a default tool name of `transfer_to_{agent.name}`. |
| `guardrails` | `tuple[InputGuardrail \| OutputGuardrail, ...]` | `()` | Guardrails evaluated before/after model calls. |
| `output_type` | `type \| None` | `None` | If set, the Runner expects structured output matching this type. |
| `settings` | `AgentSettings` | `AgentSettings()` | Agent-level execution settings. |

### Methods

#### `get_instructions`

```python
def get_instructions(self, context: RunContext | None = None) -> str:
```

Resolve instructions to a string. If `instructions` is a callable, it is called with the provided `RunContext` (or `None`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `context` | `RunContext \| None` | Optional run context passed to callable instructions. |

**Returns:** `str` — the resolved instruction string.

#### `clone`

```python
def clone(self, **kwargs: Any) -> Agent:
```

Create a modified copy of this agent. Accepts any field name as a keyword argument.

| Parameter | Type | Description |
|-----------|------|-------------|
| `**kwargs` | `Any` | Fields to override in the new agent. |

**Returns:** `Agent` — a new immutable `Agent` instance.

### Usage

```python
from flux.agent import Agent, AgentSettings
from flux.tools.decorator import tool
from flux.models.base import ModelSettings

# Simple agent with a tool
@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Sunny, 72F in {city}"

assistant = Agent(
    name="WeatherBot",
    instructions="You are a helpful weather assistant.",
    tools=[get_weather],
    settings=AgentSettings(max_turns=5),
)

# Dynamic instructions
def dynamic_instructions(ctx):
    return f"The user's name is {ctx.user_context}." if ctx else "Hello!"

agent = Agent(
    name="DynamicAgent",
    instructions=dynamic_instructions,
)

# Clone with overrides
specialist = assistant.clone(
    name="WeatherSpecialist",
    instructions="You specialize in weather forecasts.",
)
```

---

## `Runner`

::: flux.runner.Runner

```python
class Runner:
    """Execution engine for Flux agents."""
```

The `Runner` drives the agent loop: it sends messages to the LLM, executes tools, processes handoffs, and enforces guardrails. All methods are static.

### Methods

#### `run`

```python
@staticmethod
async def run(
    agent: Agent,
    input: str | list[Message],
    *,
    context: Any = None,
    config: FluxConfig | None = None,
    session: Any = None,
    model: Model | None = None,
) -> RunResult:
```

Run an agent to completion. This is the primary entry point for executing an agent.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent` | `Agent` | *required* | The agent to run. |
| `input` | `str \| list[Message]` | *required* | User input as a plain string or a pre-built list of `Message` objects. |
| `context` | `Any` | `None` | Optional user context object, accessible via `RunContext.user_context`. |
| `config` | `FluxConfig \| None` | `None` | Configuration override. Falls back to the global config via `get_config()`. |
| `session` | `Any` | `None` | Optional `Session` instance for conversation persistence. History is loaded before the run and new messages are saved after. |
| `model` | `Model \| None` | `None` | Model override. Takes precedence over the agent's own model. |

**Returns:** `RunResult`

**Raises:**

| Exception | Condition |
|-----------|-----------|
| `MaxTurnsExceeded` | The agent exceeds the configured maximum turns. |
| `ModelBehaviorError` | The model returns an empty response. |
| `InputGuardrailTripwireTriggered` | An input guardrail blocks the request. |
| `OutputGuardrailTripwireTriggered` | An output guardrail blocks the response. |
| `ProviderError` | The LLM provider returns an error. |

#### `run_sync`

```python
@staticmethod
def run_sync(
    agent: Agent,
    input: str | list[Message],
    **kwargs: Any,
) -> RunResult:
```

Synchronous wrapper around `Runner.run()`. Blocks until the run completes.

Uses `asyncio.run()` when no event loop is running, or delegates to a thread pool when an event loop is already active.

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent` | `Agent` | The agent to run. |
| `input` | `str \| list[Message]` | User input. |
| `**kwargs` | `Any` | All keyword arguments accepted by `Runner.run()`. |

**Returns:** `RunResult`

#### `run_streamed`

```python
@staticmethod
async def run_streamed(
    agent: Agent,
    input: str | list[Message],
    *,
    context: Any = None,
    config: FluxConfig | None = None,
    model: Model | None = None,
) -> StreamResult:
```

Run an agent with streaming output. Returns a `StreamResult` that yields `StreamEvent` objects as they arrive.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent` | `Agent` | *required* | The agent to run. |
| `input` | `str \| list[Message]` | *required* | User input. |
| `context` | `Any` | `None` | Optional user context. |
| `config` | `FluxConfig \| None` | `None` | Configuration override. |
| `model` | `Model \| None` | `None` | Model override. |

**Returns:** `StreamResult`

### Usage

```python
import asyncio
from flux.agent import Agent
from flux.runner import Runner

agent = Agent(name="Assistant", instructions="You are helpful.")

# Async
async def main():
    result = await Runner.run(agent, "Hello!")
    print(result.final_output)

# Sync
result = Runner.run_sync(agent, "Hello!")
print(result.final_output)

# Streaming
async def stream_main():
    stream = await Runner.run_streamed(agent, "Tell me a story.")
    async for event in stream:
        if hasattr(event, "delta"):
            print(event.delta, end="")
```

---

## `RunResult`

::: flux.runner.RunResult

```python
@dataclass
class RunResult:
    """Result of a completed agent run."""
    final_output: Any = None
    last_agent: Agent | None = None
    usage: Usage = field(default_factory=Usage)
    messages: list[Message] = field(default_factory=list)
    handoffs: list[dict[str, Any]] = field(default_factory=list)
    turns: int = 0
```

Returned by `Runner.run()` and `Runner.run_sync()` when a run completes successfully.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `final_output` | `Any` | The agent's final output. Typically a string, but can be any type if `output_type` is set. |
| `last_agent` | `Agent \| None` | The agent that produced the final output (may differ from the original if handoffs occurred). |
| `usage` | `Usage` | Aggregated token usage across all model calls. |
| `messages` | `list[Message]` | Full conversation history for the run. |
| `handoffs` | `list[dict[str, Any]]` | List of handoff events. Each dict contains `source`, `target`, and `tool_name`. |
| `turns` | `int` | Total number of LLM turns executed. |

### Usage

```python
result = Runner.run_sync(agent, "What is the capital of France?")

print(result.final_output)       # "The capital of France is Paris."
print(result.last_agent.name)    # "Assistant"
print(result.turns)              # 1
print(result.usage.total_tokens) # 42

for msg in result.messages:
    print(f"{msg.role}: {msg.content}")
```

---

## `StreamResult`

::: flux.runner.StreamResult

```python
class StreamResult:
    """Result of a streamed agent run."""
    current_agent: Agent

    def __init__(self, agent: Agent, gen: AsyncIterator[StreamEvent]) -> None: ...
    def __aiter__(self) -> AsyncIterator[StreamEvent]: ...
    async def receive(self) -> StreamEvent: ...
```

Returned by `Runner.run_streamed()`. Provides an async iterator over `StreamEvent` objects and tracks the current active agent.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `current_agent` | `Agent` | The currently active agent. Updates on handoffs. |

### Methods

#### `receive`

```python
async def receive(self) -> StreamEvent:
```

Receive the next streaming event. Raises `StopAsyncIteration` when the stream is exhausted.

**Returns:** `StreamEvent` — one of `TextDeltaEvent`, `ToolCallEvent`, `MessageCompleteEvent`, `UsageEvent`, `AgentUpdatedEvent`, or `ErrorEvent`.

### Usage

```python
import asyncio
from flux.runner import Runner

async def main():
    agent = Agent(name="Writer", instructions="You write stories.")
    stream = await Runner.run_streamed(agent, "Write a haiku about code.")

    # Option 1: async for
    async for event in stream:
        if hasattr(event, "delta"):
            print(event.delta, end="", flush=True)

    # Option 2: explicit receive
    stream = await Runner.run_streamed(agent, "Write a haiku about code.")
    try:
        while True:
            event = await stream.receive()
            if hasattr(event, "delta"):
                print(event.delta, end="", flush=True)
    except StopAsyncIteration:
        pass

asyncio.run(main())
```

### Stream Event Types

| Event | Description |
|-------|-------------|
| `AgentUpdatedEvent` | Emitted when the active agent changes (handoff). |
| `TextDeltaEvent` | Incremental text token from the model. |
| `ToolCallEvent` | A complete tool call with id, name, and arguments. |
| `MessageCompleteEvent` | The full message after streaming finishes. |
| `UsageEvent` | Token usage update. |
| `ErrorEvent` | An error during streaming. |
