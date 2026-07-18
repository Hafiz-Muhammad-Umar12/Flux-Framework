"""Quick test with Ollama moondream model."""

import asyncio
from flux import Agent, Runner, tool
from flux.models.ollama import OllamaModel

# Moondream model
model = OllamaModel(model="qwen2:0.5b")

# ── Test 1: Basic conversation ─────────────────────────────
print("=" * 50)
print("TEST 1: Basic Conversation")
print("=" * 50)

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant. Answer briefly.",
    model=model,
)

result = Runner.run_sync(agent, "Hello! What is 2 + 2?")
print(f"Output: {result.final_output}")
print(f"Turns: {result.turns}")
print(f"Tokens: {result.usage.total_tokens}")

# ── Test 2: With tools ────────────────────────────────────
print("\n" + "=" * 50)
print("TEST 2: With Tools")
print("=" * 50)

@tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello {name}!"

agent_with_tools = Agent(
    name="math_bot",
    instructions="You are a math assistant. Use the add tool for calculations.",
    model=model,
    tools=[add, greet],
)

result2 = Runner.run_sync(agent_with_tools, "What is 5 + 3?")
print(f"Output: {result2.final_output}")
print(f"Turns: {result2.turns}")

# ── Test 3: Streaming ─────────────────────────────────────
print("\n" + "=" * 50)
print("TEST 3: Streaming")
print("=" * 50)

async def stream_test():
    stream = await Runner.run_streamed(
        agent,
        "Tell me a joke in one sentence",
    )
    print("Streaming: ", end="")
    async for event in stream:
        if hasattr(event, "delta"):
            print(event.delta, end="", flush=True)
    print()

asyncio.run(stream_test())

# ── Test 4: Multi-turn with session ────────────────────────
print("\n" + "=" * 50)
print("TEST 4: Multi-turn Conversation")
print("=" * 50)

from flux import InMemorySession

async def multi_turn():
    session = InMemorySession()

    r1 = await Runner.run(agent, "My name is Umar", session=session)
    print(f"Turn 1: {r1.final_output}")

    r2 = await Runner.run(agent, "What is my name?", session=session)
    print(f"Turn 2: {r2.final_output}")

asyncio.run(multi_turn())

print("\n" + "=" * 50)
print("ALL TESTS COMPLETE!")
print("=" * 50)
