"""Example 04: Streaming responses.

Requires: Ollama running locally.
    python examples/04_streaming.py
"""

import asyncio
from flux import Agent, Runner
from flux.models.ollama import OllamaModel


model = OllamaModel(model="llama3.2")
agent = Agent(
    name="storyteller",
    instructions="You are a storyteller. Tell short, creative stories.",
    model=model,
)

async def main():
    stream = await Runner.run_streamed(
        agent,
        "Tell me a short story about a robot learning to paint",
    )

    print("--- Streaming Response ---")
    async for event in stream:
        if hasattr(event, "delta"):
            print(event.delta, end="", flush=True)
        elif hasattr(event, "agent_name"):
            print(f"\n[Agent: {event.agent_name}]")
    print("\n--- End ---")

asyncio.run(main())
