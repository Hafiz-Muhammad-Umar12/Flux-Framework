"""Example 09: Custom model provider implementation.

This example shows how to implement your own Model provider.
No external dependencies required — uses a simple echo model.
"""

import asyncio
from typing import AsyncIterator

from flux import Agent, Runner
from flux.context import Usage
from flux.models.base import ModelRequest, ModelResponse, StreamChunk


class EchoModel:
    """A simple echo model for testing. Implements the Model protocol."""

    def __init__(self, prefix: str = "Echo:") -> None:
        self.prefix = prefix

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Echo the last user message."""
        last_msg = request.messages[-1].content if request.messages else ""
        return ModelResponse(
            content=f"{self.prefix} {last_msg}",
            usage=Usage(
                input_tokens=10,
                output_tokens=20,
                total_tokens=30,
                requests=1,
            ),
        )

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        """Stream the echo response word by word."""
        last_msg = request.messages[-1].content if request.messages else ""
        response = f"{self.prefix} {last_msg}"
        words = response.split(" ")

        for i, word in enumerate(words):
            delta = word + (" " if i < len(words) - 1 else "")
            yield StreamChunk(delta_text=delta)

        yield StreamChunk(
            done=True,
            usage=Usage(input_tokens=10, output_tokens=20, total_tokens=30, requests=1),
        )


# ── Usage ──────────────────────────────────────────────────

async def main():
    model = EchoModel(prefix="Flux says:")

    agent = Agent(
        name="echo_bot",
        instructions="You are an echo bot.",
        model=model,
    )

    # Non-streaming
    result = await Runner.run(agent, "Hello, Flux!")
    print(f"Output: {result.final_output}")
    print(f"Tokens: {result.usage.total_tokens}")

    # Streaming
    print("\n--- Streaming ---")
    stream = await Runner.run_streamed(agent, "Hello, streaming Flux!")
    async for event in stream:
        if hasattr(event, "delta"):
            print(event.delta, end="", flush=True)
    print()


asyncio.run(main())
