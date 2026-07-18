"""Example 06: Session memory and conversation persistence.

Requires: Ollama running locally.
    python examples/06_memory.py
"""

import asyncio
from flux import Agent, Runner, InMemorySession
from flux.models.ollama import OllamaModel


model = OllamaModel(model="llama3.2")
agent = Agent(
    name="memory_bot",
    instructions="You remember everything about the user. Reference past conversations.",
    model=model,
)

async def main():
    session = InMemorySession()

    # First turn — introduce yourself
    result1 = await Runner.run(
        agent,
        "My name is Alice and I love painting",
        session=session,
    )
    print(f"Turn 1: {result1.final_output[:100]}...")

    # Second turn — agent should remember
    result2 = await Runner.run(
        agent,
        "What's my name and what do I love?",
        session=session,
    )
    print(f"\nTurn 2: {result2.final_output}")

    # Check session history
    messages = await session.get_messages()
    print(f"\nSession has {len(messages)} messages")

asyncio.run(main())
