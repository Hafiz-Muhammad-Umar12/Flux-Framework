# Building a Weather Agent

A step-by-step guide to building a weather agent with tools, guardrails, and streaming output using the Flux framework.

---

## Overview

In this guide you will build a complete weather agent that can:

- Look up current weather for any city
- Provide multi-day forecasts
- Validate user input with guardrails
- Stream responses in real time

The full source code is at the end of the page.

---

## Prerequisites

- Python 3.10+
- Flux installed (`pip install flux-agents`)
- An Ollama instance running locally (or swap in `OpenAIModel` / `AnthropicModel`)

---

## 1 -- Define Weather Tools

Tools are plain functions decorated with `@tool`. The docstring becomes the tool description the LLM sees, and the type-annotated parameters become the tool schema.

```python
from flux import tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a specific city.

    Args:
        city: The city name to get weather for.
    """
    weather_data = {
        "new york": "Sunny, 72°F",
        "london": "Rainy, 58°F",
        "tokyo": "Clear, 68°F",
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")


@tool
def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for multiple days.

    Args:
        city: The city name.
        days: Number of days for the forecast.
    """
    return f"{days}-day forecast for {city}: Sunny with occasional clouds"
```

!!! tip "Production Tip"
    In a real application you would call an external API (OpenWeatherMap, WeatherAPI, etc.) inside these functions. The tool interface stays the same -- only the implementation changes.

---

## 2 -- Create the Agent

An `Agent` combines a model, a system prompt, and a set of tools.

```python
from flux import Agent
from flux.models.ollama import OllamaModel

weather_agent = Agent(
    name="weather_agent",
    instructions=(
        "You are a helpful weather assistant. "
        "Use the provided tools to look up weather and forecasts. "
        "Always report the city name and temperature clearly."
    ),
    model=OllamaModel(model="llama3.2"),
    tools=[get_weather, get_forecast],
)
```

You can swap the model for any supported provider:

=== "Ollama (local)"

    ```python
    from flux.models.ollama import OllamaModel
    model = OllamaModel(model="llama3.2")
    ```

=== "OpenAI"

    ```python
    from flux.models.openai_provider import OpenAIModel
    model = OpenAIModel(model="gpt-4o")
    ```

=== "Anthropic"

    ```python
    from flux.models.anthropic import AnthropicModel
    model = AnthropicModel(model="claude-sonnet-4-20250514")
    ```

---

## 3 -- Add Input Guardrails

Guardrails let you validate (and reject) user input before it reaches the model.

```python
from flux import LengthGuardrail

guardrails = [
    LengthGuardrail(max_length=500),
]
```

`LengthGuardrail` rejects messages longer than the specified limit. You can combine it with other built-in guardrails:

```python
from flux import LengthGuardrail, PIIGuardrail, ProfanityGuardrail

guardrails = [
    LengthGuardrail(max_length=500),
    PIIGuardrail(),          # blocks PII in user input
    ProfanityGuardrail(),    # blocks profane language
]
```

Attach guardrails to the agent:

```python
weather_agent = Agent(
    name="weather_agent",
    instructions="You are a helpful weather assistant.",
    model=OllamaModel(model="llama3.2"),
    tools=[get_weather, get_forecast],
    input_guardrails=guardrails,
)
```

---

## 4 -- Run the Agent

### Non-streaming

```python
import asyncio
from flux import Runner

async def main():
    result = await Runner.run(weather_agent, "What's the weather in Tokyo?")
    print(result.final_output)

asyncio.run(main())
```

### Streaming

For real-time token-by-token output, use `Runner.run_streamed()`:

```python
async def main_streaming():
    result = await Runner.run_streamed(weather_agent, "What's the weather in London?")
    async for event in result.stream_events():
        if hasattr(event, "delta_text"):
            print(event.delta_text, end="", flush=True)
    print()  # newline after stream

asyncio.run(main_streaming())
```

---

## 5 -- Full Working Example

```python
"""Weather agent with tools, guardrails, and streaming."""

import asyncio
from flux import Agent, Runner, tool, LengthGuardrail
from flux.models.ollama import OllamaModel


# --- Tools -----------------------------------------------------------

@tool
def get_weather(city: str) -> str:
    """Get current weather for a specific city.

    Args:
        city: The city name to get weather for.
    """
    weather_data = {
        "new york": "Sunny, 72°F",
        "london": "Rainy, 58°F",
        "tokyo": "Clear, 68°F",
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")


@tool
def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for multiple days.

    Args:
        city: The city name.
        days: Number of days for the forecast.
    """
    return f"{days}-day forecast for {city}: Sunny with occasional clouds"


# --- Agent -----------------------------------------------------------

weather_agent = Agent(
    name="weather_agent",
    instructions=(
        "You are a helpful weather assistant. "
        "Use the provided tools to look up weather and forecasts. "
        "Always report the city name and temperature clearly."
    ),
    model=OllamaModel(model="llama3.2"),
    tools=[get_weather, get_forecast],
    input_guardrails=[LengthGuardrail(max_length=500)],
)


# --- Main ------------------------------------------------------------

async def main():
    # Non-streaming
    result = await Runner.run(weather_agent, "What's the weather in Tokyo?")
    print(result.final_output)

    print("\n--- Streaming ---\n")

    # Streaming
    stream_result = await Runner.run_streamed(
        weather_agent, "What's the forecast for New York?"
    )
    async for event in stream_result.stream_events():
        if hasattr(event, "delta_text"):
            print(event.delta_text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Next Steps

- Add [session persistence](chatbot.md) to remember past weather queries
- Build a [multi-agent system](multi-agent.md) with a weather specialist and a travel advisor
- Explore [custom middleware](middleware.md) to cache weather API calls
