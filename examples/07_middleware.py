"""Example 07: Middleware for logging, caching, and retry.

Requires: Ollama running locally.
    python examples/07_middleware.py
"""

import asyncio
import logging
from flux import Agent, Runner
from flux.middleware.base import Middleware, NextFn, RequestContext, Response
from flux.middleware.logging import LoggingMiddleware
from flux.middleware.cache import CacheMiddleware
from flux.models.ollama import OllamaModel


# Custom middleware
class TimingMiddleware:
    """Measures request duration."""

    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        import time
        start = time.time()
        response = await next(ctx)
        elapsed = time.time() - start
        print(f"[Timing] {ctx.agent_name}: {elapsed:.2f}s")
        return response


# Enable logging
logging.basicConfig(level=logging.INFO)

model = OllamaModel(model="llama3.2")
agent = Agent(
    name="timed_bot",
    instructions="You are helpful.",
    model=model,
)

async def main():
    # Note: middleware is applied at the Runner level in this example
    # In a real app, you'd configure the Runner with middleware

    print("--- First request (no cache) ---")
    result1 = await Runner.run(agent, "What is 2+2?")

    print("\n--- Second request (cache hit if configured) ---")
    result2 = await Runner.run(agent, "What is 2+2?")

    print(f"\nResult: {result1.final_output}")

asyncio.run(main())
