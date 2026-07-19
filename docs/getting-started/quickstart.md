# Quickstart

Get up and running with Flux Agents in 5 minutes.

## Prerequisites

- Python 3.11 or later
- Ollama installed locally ([install guide](https://ollama.com/download))

## Step 1: Install Flux Agents

```bash
pip install "flux-agents[ollama]"
```

This installs the core framework plus the Ollama provider (which requires `aiohttp`).

## Step 2: Set Up Ollama

Pull a model that supports tool use:

```bash
ollama pull llama3.2
```

Verify Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

!!! tip "Alternative providers"
    You can skip Ollama entirely and use a cloud provider instead. See the [Provider Tips](#provider-tips) section below.

## Step 3: Create a Basic Agent

Create a file called `quickstart.py`:

```python
from flux import Agent, Runner
from flux.models.ollama import OllamaModel

# Create an agent
agent = Agent(
    name="greeter",
    instructions="You are a friendly assistant. Greet the user warmly.",
    model=OllamaModel(model="llama3.2"),
)

# Run it
result = Runner.run_sync(agent, "Hello! What is your name?")
print(result.final_output)
```

Run it:

```bash
python quickstart.py
```

Expected output:

```
Hello! I'm a friendly assistant. It's great to meet you! You can call me Flux. How can I help you today?
```

!!! note "First run may be slow"
    The first time you run this, Ollama needs to load the model into memory. Subsequent runs will be much faster.

## Step 4: Run It Asynchronously

Flux Agents is async-first. Here is the same example using async/await:

```python
import asyncio
from flux import Agent, Runner
from flux.models.ollama import OllamaModel

agent = Agent(
    name="greeter",
    instructions="You are a friendly assistant. Greet the user warmly.",
    model=OllamaModel(model="llama3.2"),
)

async def main():
    result = await Runner.run(agent, "Hello! What is your name?")
    print(result.final_output)

asyncio.run(main())
```

Both `Runner.run_sync()` and `await Runner.run()` produce the same result. Use `run_sync` for scripts and quick tests; use `await Runner.run()` inside async applications.

## Step 5: Add a Tool

Tools let your agent interact with the outside world. Use the `@tool` decorator to create one:

```python
import asyncio
from flux import Agent, Runner, tool
from flux.models.ollama import OllamaModel


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # In a real app, you'd call a weather API here
    weather_data = {
        "New York": "Sunny, 72F",
        "London": "Cloudy, 58F",
        "Tokyo": "Rainy, 65F",
    }
    return weather_data.get(city, f"Weather data not available for {city}")


agent = Agent(
    name="weather_bot",
    instructions="You are a helpful weather assistant. Use the get_weather tool to answer questions about weather.",
    model=OllamaModel(model="llama3.2"),
    tools=[get_weather],
)


async def main():
    result = await Runner.run(agent, "What's the weather in New York?")
    print(result.final_output)
    print(f"\nUsed {result.usage.total_tokens} tokens in {result.turns} turns")


asyncio.run(main())
```

Expected output:

```
The current weather in New York is Sunny and 72 degrees Fahrenheit!

Used 342 tokens in 2 turns
```

The `@tool` decorator automatically:

- Uses the function name as the tool name
- Uses the docstring as the tool description
- Generates a JSON Schema from the function signature and type hints
- Supports both sync and async functions

## Step 6: Add Streaming

Streaming gives you real-time token-by-token output instead of waiting for the full response:

```python
import asyncio
from flux import Agent, Runner, tool
from flux.models.ollama import OllamaModel
from flux.streaming.events import TextDeltaEvent, UsageEvent


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"The weather in {city} is sunny and 72F"


agent = Agent(
    name="weather_bot",
    instructions="You are a helpful weather assistant.",
    model=OllamaModel(model="llama3.2"),
    tools=[get_weather],
)


async def main():
    result = await Runner.run_streamed(agent, "What's the weather in Tokyo?")

    async for event in result:
        if isinstance(event, TextDeltaEvent):
            # Print each token as it arrives
            print(event.delta, end="", flush=True)
        elif isinstance(event, UsageEvent):
            print(f"\n\n[Tokens: {event.total_tokens}]")

    print()


asyncio.run(main())
```

Expected output:

```
The weather in Tokyo is rainy and 65F.

[Tokens: 156]
```

The `StreamResult` object yields these event types:

| Event | Description |
|---|---|
| `TextDeltaEvent` | Incremental text token from the model |
| `ToolCallEvent` | A complete tool call (name + arguments) |
| `MessageCompleteEvent` | Full assembled message from the model |
| `UsageEvent` | Token usage update |
| `AgentUpdatedEvent` | Agent changed due to a handoff |
| `ErrorEvent` | An error occurred during streaming |

## Provider Tips

### Using OpenAI

```bash
pip install "flux-agents[openai]"
export OPENAI_API_KEY="your-api-key"
```

```python
from flux.models.openai_provider import OpenAIModel

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant.",
    model=OpenAIModel(model="gpt-4o-mini"),
)
```

### Using Anthropic

```bash
pip install "flux-agents[anthropic]"
export ANTHROPIC_API_KEY="your-api-key"
```

```python
from flux.models.anthropic import AnthropicModel

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant.",
    model=AnthropicModel(model="claude-sonnet-4-20250514"),
)
```

### Using OpenRouter or DeepSeek

The OpenAI provider works with any OpenAI-compatible API:

```python
from flux.models.openai_provider import OpenAIModel

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant.",
    model=OpenAIModel(
        model="deepseek-chat",
        api_key="your-api-key",
        base_url="https://api.deepseek.com/v1",
    ),
)
```

## Complete Example

Here is the full quickstart with tools and streaming combined:

```python
import asyncio
from flux import Agent, Runner, tool
from flux.models.ollama import OllamaModel
from flux.streaming.events import TextDeltaEvent, UsageEvent


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    weather_data = {
        "New York": "Sunny, 72F",
        "London": "Cloudy, 58F",
        "Tokyo": "Rainy, 65F",
    }
    return weather_data.get(city, f"Weather data not available for {city}")


agent = Agent(
    name="weather_bot",
    instructions="You are a helpful weather assistant. Use the get_weather tool to answer questions about weather.",
    model=OllamaModel(model="llama3.2"),
    tools=[get_weather],
)


async def main():
    # Sync usage (simple)
    result = Runner.run_sync(agent, "What's the weather in London?")
    print(f"[Sync] {result.final_output}")
    print(f"  Turns: {result.turns}, Tokens: {result.usage.total_tokens}")

    print()

    # Async streaming usage
    result = await Runner.run_streamed(agent, "Compare weather in New York and Tokyo")
    async for event in result:
        if isinstance(event, TextDeltaEvent):
            print(event.delta, end="", flush=True)
        elif isinstance(event, UsageEvent):
            print(f"\n  [Streaming] Total tokens: {event.total_tokens}")


asyncio.run(main())
```

---

## Next Steps

- [Your First Agent](first-agent.md) -- A step-by-step tutorial covering tools, streaming, sessions, and guardrails
- [Project Structure](project-structure.md) -- Understand the Flux Agents architecture and module layout
