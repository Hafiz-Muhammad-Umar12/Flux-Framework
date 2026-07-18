# Flux Examples

## Basic Examples

### 01_basic.py — Simple Chat

```python
from flux import Agent, Runner
from flux.models.ollama import OllamaModel

model = OllamaModel(model="qwen2:0.5b")
agent = Agent(name="assistant", instructions="You are helpful", model=model)
result = Runner.run_sync(agent, "Hello!")
print(result.final_output)
```

### 02_tools.py — Using Tools

```python
from flux import Agent, Runner, tool
from flux.models.ollama import OllamaModel

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

model = OllamaModel(model="qwen2:1.5b")  # Need bigger model for tools
agent = Agent(
    name="math_bot",
    instructions="Use calculator for math",
    model=model,
    tools=[calculator],
)

result = Runner.run_sync(agent, "What is 15 * 23?")
print(result.final_output)
```

### 03_handoffs.py — Multi-Agent

```python
import asyncio
from flux import Agent, Runner
from flux.handoffs.handoff import Handoff
from flux.models.ollama import OllamaModel

async def main():
    model = OllamaModel(model="qwen2:1.5b")

    coder = Agent(name="coder", instructions="Write code", model=model)
    writer = Agent(name="writer", instructions="Write content", model=model)

    router = Agent(
        name="router",
        instructions="Route to specialist",
        model=model,
        handoffs=(
            Handoff(source=router, target=coder),
            Handoff(source=router, target=writer),
        ),
    )

    result = await Runner.run(router, "Write Python hello world")
    print(f"Agent: {result.last_agent.name}")

asyncio.run(main())
```

### 04_streaming.py — Real-time Output

```python
import asyncio
from flux import Agent, Runner
from flux.models.ollama import OllamaModel

async def main():
    model = OllamaModel(model="qwen2:0.5b")
    agent = Agent(name="storyteller", instructions="Tell stories", model=model)

    stream = await Runner.run_streamed(agent, "Tell me a joke")
    async for event in stream:
        if hasattr(event, "delta"):
            print(event.delta, end="", flush=True)
    print()

asyncio.run(main())
```

### 05_guardrails.py — Safety

```python
from flux import Agent, Runner, LengthGuardrail, PIIGuardrail
from flux.guardrails.base import OutputGuardrail, GuardrailResult
from flux.models.ollama import OllamaModel

class NoCodeGuardrail(OutputGuardrail):
    @property
    def name(self): return "no_code"

    async def check(self, output, context=None):
        if "```" in output:
            return GuardrailResult(passed=False, message="No code allowed")
        return GuardrailResult(passed=True)

model = OllamaModel(model="qwen2:0.5b")
agent = Agent(
    name="safe_bot",
    instructions="Be helpful",
    model=model,
    guardrails=(
        LengthGuardrail(max_chars=5000),
        PIIGuardrail(),
        NoCodeGuardrail(),
    ),
)
```

### 06_memory.py — Conversation Memory

```python
import asyncio
from flux import Agent, Runner, InMemorySession
from flux.models.ollama import OllamaModel

async def main():
    model = OllamaModel(model="qwen2:0.5b")
    agent = Agent(name="bot", instructions="Remember everything", model=model)
    session = InMemorySession()

    r1 = await Runner.run(agent, "My name is Sara", session=session)
    r2 = await Runner.run(agent, "What is my name?", session=session)
    print(f"Bot: {r2.final_output}")

asyncio.run(main())
```

### 07_middleware.py — Middleware

```python
from flux.middleware.base import Middleware, NextFn, RequestContext, Response

class TimingMiddleware:
    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        import time
        start = time.time()
        response = await next(ctx)
        print(f"Time: {time.time() - start:.2f}s")
        return response
```

### 08_multi_agent.py — Complex Multi-Agent

```python
# Router with 3 specialists
router = Agent(
    name="router",
    instructions="Route to the right expert",
    model=model,
    handoffs=(
        Handoff(source=router, target=researcher),
        Handoff(source=router, target=coder),
        Handoff(source=router, target=analyst),
    ),
)
```

### 09_custom_model.py — Custom Provider

```python
from flux.models.base import ModelRequest, ModelResponse, StreamChunk
from flux.context import Usage

class MyModel:
    async def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            content="Custom response!",
            usage=Usage(input_tokens=10, output_tokens=20, total_tokens=30),
        )

    async def stream(self, request: ModelRequest):
        yield StreamChunk(delta_text="Hello!", done=True)
```

## Running Examples

```bash
cd C:\Users\FC\swarm

# Basic
python examples/01_basic.py

# Tools (need qwen2:1.5b or bigger)
python examples/02_tools.py

# Streaming
python examples/04_streaming.py

# Custom model (no Ollama needed)
python examples/09_custom_model.py
```
