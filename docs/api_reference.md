# Flux API Reference

## Core Classes

### Agent

```python
from flux import Agent, AgentSettings
from flux.models.base import ModelSettings

agent = Agent(
    name="my_bot",                          # Required: agent name
    instructions="You are helpful",         # System prompt (str or callable)
    model="qwen2:0.5b",                    # Model name or Model instance
    tools=[tool1, tool2],                   # List of tools
    handoffs=[handoff1],                    # List of handoffs
    guardrails=[guardrail1],                # List of guardrails
    output_type=str,                        # Output type hint
    settings=AgentSettings(max_turns=10),   # Agent settings
)

# Methods
agent.get_instructions(context)  # Resolve instructions
agent.clone(name="new_name")    # Create modified copy
```

### Runner

```python
from flux import Runner

# Async run
result = await Runner.run(
    agent=agent,
    input="Hello!",
    context=None,          # User context object
    config=None,           # FluxConfig override
    session=None,          # Session for persistence
    model=None,            # Model override
)

# Sync run
result = Runner.run_sync(agent, "Hello!")

# Streaming
stream = await Runner.run_streamed(agent, "Hello!")
async for event in stream:
    if hasattr(event, "delta"):
        print(event.delta, end="")
```

### RunResult

```python
result.final_output    # str - Agent's response
result.last_agent      # Agent - Agent that produced output
result.usage           # Usage - Token usage
result.messages        # list[Message] - Full conversation
result.handoffs        # list[dict] - Handoff log
result.turns           # int - Number of turns
```

## Models

### OllamaModel

```python
from flux.models.ollama import OllamaModel

model = OllamaModel(
    model="qwen2:0.5b",           # Model name
    base_url="http://localhost:11434",  # Ollama URL
)
```

### OpenAIModel

```python
from flux.models.openai_provider import OpenAIModel

model = OpenAIModel(
    model="gpt-4o-mini",
    api_key="sk-...",             # Or use OPENAI_API_KEY env var
    base_url=None,                # For OpenRouter, DeepSeek, etc.
)
```

### AnthropicModel

```python
from flux.models.anthropic import AnthropicModel

model = AnthropicModel(
    model="claude-sonnet-4-20250514",
    api_key="sk-ant-...",         # Or use ANTHROPIC_API_KEY env var
)
```

### Model Protocol

```python
from flux.models.base import Model, ModelRequest, ModelResponse, StreamChunk

class MyModel:
    async def complete(self, request: ModelRequest) -> ModelResponse:
        ...

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        ...
        yield
```

### ModelRegistry

```python
from flux.models.registry import ModelRegistry, get_default_registry

registry = get_default_registry()
registry.register("my-model", my_model)
registry.register_provider("ollama", ollama_model)

model = registry.resolve("ollama/qwen2:0.5b")
```

## Tools

### @tool Decorator

```python
from flux import tool

@tool
def my_tool(x: str) -> str:
    """Description shown to model."""
    return f"Result: {x}"

@tool(name="custom_name", description="Custom description")
def my_tool(x: str) -> str:
    return x
```

### Tool Protocol

```python
from flux.tools.base import Tool, ToolResult

class MyTool:
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Does something"

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "x": {"type": "string", "description": "Input"}
            },
            "required": ["x"]
        }

    async def execute(self, ctx, args) -> ToolResult:
        return ToolResult(output="done")
```

### ToolRegistry

```python
from flux.tools.registry import ToolRegistry

registry = ToolRegistry()
registry.register(my_tool)
registry.get("my_tool")
registry.list_tools()
registry.to_tool_defs()
```

### Built-in Tools

```python
from flux.tools.builtins import ShellTool, FileReadTool, FileWriteTool

agent = Agent(
    name="bot",
    tools=[ShellTool(), FileReadTool(), FileWriteTool()],
    ...
)
```

## Handoffs

```python
from flux import Agent
from flux.handoffs.handoff import Handoff

agent_a = Agent(name="router", instructions="Route", model=model)
agent_b = Agent(name="helper", instructions="Help", model=model)

handoff = Handoff(
    source=agent_a,
    target=agent_b,
    description="Transfer to helper",
    condition=None,           # Optional: callable for conditional handoff
    input_filter=None,        # Optional: filter conversation history
)

agent_a = agent_a.clone(handoffs=(handoff,))
```

## Guardrails

```python
from flux import LengthGuardrail, PIIGuardrail, ProfanityGuardrail
from flux.guardrails.base import InputGuardrail, OutputGuardrail, GuardrailResult

# Built-in
agent = Agent(
    guardrails=(
        LengthGuardrail(max_chars=5000),
        PIIGuardrail(),
        ProfanityGuardrail(word_list=["bad", "word"]),
    ),
    ...
)

# Custom
class MyGuardrail(InputGuardrail):
    @property
    def name(self) -> str:
        return "my_guardrail"

    async def check(self, user_input, context=None) -> GuardrailResult:
        if "bad" in user_input.lower():
            return GuardrailResult(passed=False, message="Bad input")
        return GuardrailResult(passed=True)
```

## Sessions

```python
from flux import InMemorySession, SQLiteSession

# In-memory (lost on restart)
session = InMemorySession(max_messages=100)

# SQLite (persistent)
session = SQLiteSession(db_path="chat.db", session_id="user123")

# Use with Runner
result = await Runner.run(agent, "Hello", session=session)
```

## Memory

```python
from flux import ConversationMemory, VectorMemory

# Conversation-based (wraps Session)
memory = ConversationMemory(session)
await memory.store("Important fact")
results = await memory.search("fact", limit=5)

# Vector-based (hash embeddings)
memory = VectorMemory()
await memory.store("Some content", metadata={"source": "doc1"})
results = await memory.search("query", limit=5)
```

## Middleware

```python
from flux.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    CacheMiddleware,
    RetryMiddleware,
    Middleware,
    RequestContext,
    Response,
    NextFn,
)

# Built-in
logging_mw = LoggingMiddleware()
rate_limit_mw = RateLimitMiddleware(max_per_second=10)
cache_mw = CacheMiddleware(ttl_seconds=300)
retry_mw = RetryMiddleware(max_retries=3)

# Custom
class MyMiddleware:
    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        # Before
        response = await next(ctx)
        # After
        return response
```

## Events

```python
from flux import EventBus, Event, get_event_bus

bus = get_event_bus()

# Subscribe
def handler(event: Event):
    print(f"Event: {event.type}")

bus.on("agent.start", handler)
bus.on_all(handler)  # All events

# Emit
bus.emit(Event(type="custom.event", data={"key": "value"}))
```

## Tracing

```python
from flux import ConsoleTracer, FileTracer

# Console
tracer = ConsoleTracer()
with tracer.start_span("my_operation") as span:
    span.set_attribute("key", "value")
    # Do work
    span.finish()

# File (JSON lines)
tracer = FileTracer("trace.jsonl")
with tracer.start_span("my_operation") as span:
    # Do work
    span.finish()
```

## Configuration

```python
from flux import FluxConfig, set_config, get_config

config = FluxConfig(
    default_model="qwen2:0.5b",
    default_max_turns=10,
    default_model_settings=ModelSettings(temperature=0.7),
    event_bus_enabled=True,
    tracing_enabled=False,
    log_level="INFO",
)
set_config(config)

# Get current config
config = get_config()
```

## Exceptions

```python
from flux import (
    FluxError,              # Base exception
    MaxTurnsExceeded,       # Too many turns
    ModelBehaviorError,     # Unexpected model output
    UserError,              # Invalid usage
    ToolError,              # Tool execution failed
    ToolTimeoutError,       # Tool timed out
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    HandoffError,           # Handoff failed
    ProviderError,          # LLM provider error
    ConfigurationError,     # Invalid config
)
```
