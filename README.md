# Flux

**A Python-first Agentic AI Framework**

Provider-agnostic · Async-first · Middleware-driven · Zero core dependencies

---

## Quick Start

```python
import asyncio
from flux import Agent, Runner

# 3 lines to get started
agent = Agent(name="assistant", instructions="You are helpful")
result = asyncio.run(Runner.run(agent, "Hello!"))
print(result.final_output)
```

## Features

- **Provider Agnostic** — Ollama, OpenAI, Anthropic, Groq, DeepSeek, OpenRouter
- **Async First** — Non-blocking by default, sync wrappers available
- **Protocol Based** — Structural typing, no inheritance required
- **Middleware** — Composable middleware stack (logging, caching, retry, rate-limiting)
- **Event Driven** — Decoupled event bus for observability
- **Tools** — `@tool` decorator, tool registry, built-in tools
- **Handoffs** — Agent-to-agent routing
- **Guardrails** — Input/output validation
- **Sessions** — Conversation persistence (in-memory, SQLite)
- **Memory** — Short-term and long-term memory
- **Streaming** — Real-time token streaming
- **Tracing** — Console and file-based tracing

## Installation

```bash
# Core framework (zero dependencies)
pip install flux-agents

# With providers
pip install flux-agents[ollama]     # Ollama
pip install flux-agents[openai]     # OpenAI
pip install flux-agents[anthropic]  # Anthropic
pip install flux-agents[full]       # All providers
```

## Usage

### Basic Agent

```python
from flux import Agent, Runner

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant",
    model="ollama/llama3.2",
)

result = Runner.run_sync(agent, "What is the capital of France?")
print(result.final_output)
```

### With Tools

```python
from flux import Agent, Runner, tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Sunny in {city}"

agent = Agent(
    name="weather_bot",
    instructions="You help with weather queries",
    tools=[get_weather],
)

result = Runner.run_sync(agent, "What's the weather in NYC?")
print(result.final_output)
```

### With Handoffs

```python
from flux import Agent, Runner

router = Agent(
    name="router",
    instructions="Route to the right specialist",
    handoffs=[
        Agent(name="coder", instructions="You write code"),
        Agent(name="writer", instructions="You write content"),
    ],
)

result = Runner.run_sync(router, "Write a Python function to sort a list")
print(result.final_output)
```

### Streaming

```python
import asyncio
from flux import Agent, Runner

async def main():
    agent = Agent(name="assistant", instructions="You are helpful")
    stream = await Runner.run_streamed(agent, "Tell me a story")
    async for event in stream:
        if hasattr(event, "delta"):
            print(event.delta, end="", flush=True)

asyncio.run(main())
```

### With Guardrails

```python
from flux import Agent, Runner, LengthGuardrail, PIIGuardrail

agent = Agent(
    name="safe_assistant",
    instructions="You are helpful",
    guardrails=[
        LengthGuardrail(max_chars=5000),
        PIIGuardrail(),
    ],
)
```

### With Middleware

```python
from flux import Agent, Runner, LoggingMiddleware, RetryMiddleware

# Middleware wraps every request
runner = Runner(middlewares=[
    LoggingMiddleware(),
    RetryMiddleware(max_retries=3),
])
```

### With Sessions

```python
from flux import Agent, Runner, InMemorySession

session = InMemorySession()
agent = Agent(name="assistant", instructions="You remember our conversation")

# First turn
result1 = Runner.run_sync(agent, "My name is Alice", session=session)

# Second turn — agent remembers context
result2 = Runner.run_sync(agent, "What's my name?", session=session)
print(result2.final_output)  # "Your name is Alice"
```

### Custom Model

```python
from flux import Agent, Runner
from flux.models.ollama import OllamaModel

model = OllamaModel(model="llama3.2", base_url="http://localhost:11434")
agent = Agent(name="local", instructions="You run locally", model=model)

result = Runner.run_sync(agent, "Hello!")
```

### Custom Provider

```python
from flux.models.base import Model, ModelRequest, ModelResponse

class MyCustomModel:
    async def complete(self, request: ModelRequest) -> ModelResponse:
        # Your custom implementation
        return ModelResponse(content="Hello from custom model!")

    async def stream(self, request: ModelRequest):
        yield  # Your streaming implementation

agent = Agent(name="custom", instructions="Custom model", model=MyCustomModel())
```

## Architecture

```
flux/
├── agent.py          # Agent (immutable dataclass)
├── runner.py         # Runner (execution engine)
├── context.py        # RunContext, ToolContext
├── config.py         # Global configuration
├── exceptions.py     # Exception hierarchy
├── models/           # LLM providers (Ollama, OpenAI, Anthropic)
├── tools/            # Tool protocol, @tool decorator, registry
├── handoffs/         # Agent-to-agent routing
├── guardrails/       # Input/output validation
├── sessions/         # Conversation persistence
├── memory/           # Long-term memory
├── streaming/        # Stream event types
├── middleware/        # Composable middleware
├── events/           # Event bus
├── tracing/          # Observability
└── utils/            # JSON schema, tokens, pretty print
```

## Design Principles

1. **Protocol over ABC** — Structural typing, no inheritance required
2. **Async first** — Non-blocking by default
3. **Zero core deps** — Base framework needs no third-party packages
4. **Middleware over hooks** — Composable, testable, standard pattern
5. **Immutable agents** — Thread-safe, cloneable
6. **Event-driven** — Decoupled observability

## License

MIT
