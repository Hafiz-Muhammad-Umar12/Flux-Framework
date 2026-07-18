# Getting Started with Flux

## Installation

```bash
cd C:\Users\FC\swarm
pip install -e .
```

## Requirements

- Python 3.11+
- Ollama (for local models)

## Quick Start

```python
from flux import Agent, Runner
from flux.models.ollama import OllamaModel

model = OllamaModel(model="qwen2:0.5b")
agent = Agent(name="bot", instructions="You are helpful", model=model)
result = Runner.run_sync(agent, "Hello!")
print(result.final_output)
```

## First Steps

### 1. Basic Chat

```python
from flux import Agent, Runner
from flux.models.ollama import OllamaModel

model = OllamaModel(model="qwen2:0.5b")
agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant",
    model=model,
)

result = Runner.run_sync(agent, "What is Python?")
print(result.final_output)
```

### 2. With Tools

```python
from flux import Agent, Runner, tool
from flux.models.ollama import OllamaModel

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

model = OllamaModel(model="qwen2:1.5b")  # Need bigger model for tools
agent = Agent(
    name="math_bot",
    instructions="Use tools for calculations",
    model=model,
    tools=[add],
)

result = Runner.run_sync(agent, "What is 5 + 3?")
print(result.final_output)
```

### 3. Streaming

```python
import asyncio
from flux import Agent, Runner
from flux.models.ollama import OllamaModel

async def main():
    model = OllamaModel(model="qwen2:0.5b")
    agent = Agent(name="bot", instructions="Be concise", model=model)

    stream = await Runner.run_streamed(agent, "Tell me a joke")
    async for event in stream:
        if hasattr(event, "delta"):
            print(event.delta, end="", flush=True)
    print()

asyncio.run(main())
```

### 4. Multi-turn with Memory

```python
import asyncio
from flux import Agent, Runner, InMemorySession
from flux.models.ollama import OllamaModel

async def main():
    model = OllamaModel(model="qwen2:0.5b")
    agent = Agent(name="bot", instructions="Remember the conversation", model=model)
    session = InMemorySession()

    r1 = await Runner.run(agent, "My name is Ali", session=session)
    print(f"Bot: {r1.final_output}")

    r2 = await Runner.run(agent, "What is my name?", session=session)
    print(f"Bot: {r2.final_output}")

asyncio.run(main())
```

### 5. Handoffs (Multi-Agent)

```python
import asyncio
from flux import Agent, Runner
from flux.handoffs.handoff import Handoff
from flux.models.ollama import OllamaModel

async def main():
    model = OllamaModel(model="qwen2:1.5b")

    coder = Agent(name="coder", instructions="You write code", model=model)
    writer = Agent(name="writer", instructions="You write content", model=model)

    router = Agent(
        name="router",
        instructions="Route to specialist",
        model=model,
        handoffs=(
            Handoff(source=router, target=coder),
            Handoff(source=router, target=writer),
        ),
    )

    result = await Runner.run(router, "Write a Python hello world")
    print(f"Agent: {result.last_agent.name}")
    print(f"Output: {result.final_output}")

asyncio.run(main())
```

### 6. Guardrails

```python
from flux import Agent, Runner, LengthGuardrail, PIIGuardrail
from flux.models.ollama import OllamaModel

model = OllamaModel(model="qwen2:0.5b")
agent = Agent(
    name="safe_bot",
    instructions="Be helpful",
    model=model,
    guardrails=(
        LengthGuardrail(max_chars=5000),
        PIIGuardrail(),
    ),
)

# This will be blocked if output contains PII
result = Runner.run_sync(agent, "Tell me about Python")
```

### 7. Sessions (Persistence)

```python
import asyncio
from flux import Agent, Runner, SQLiteSession
from flux.models.ollama import OllamaModel

async def main():
    model = OllamaModel(model="qwen2:0.5b")
    agent = Agent(name="bot", instructions="Be helpful", model=model)

    # Persistent session (survives restarts)
    session = SQLiteSession(db_path="chat.db")

    r1 = await Runner.run(agent, "I like pizza", session=session)
    r2 = await Runner.run(agent, "What do I like?", session=session)
    print(f"Bot: {r2.final_output}")

asyncio.run(main())
```

### 8. Custom Model

```python
from flux import Agent, Runner
from flux.models.base import ModelRequest, ModelResponse, StreamChunk
from flux.context import Usage
from typing import AsyncIterator

class MyModel:
    async def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(content="Hello from my model!")

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(delta_text="Hello!", done=True)

agent = Agent(name="custom", instructions="Be helpful", model=MyModel())
result = Runner.run_sync(agent, "Hi")
print(result.final_output)
```

## Configuration

```python
from flux import FluxConfig, set_config

config = FluxConfig(
    default_model="qwen2:0.5b",
    default_max_turns=10,
    event_bus_enabled=True,
    tracing_enabled=False,
)
set_config(config)
```

## Next Steps

- [API Reference](api_reference.md)
- [Architecture](architecture.md)
- [Examples](../examples/)
