"""Example 03: Agent handoffs (multi-agent routing).

Requires: Ollama running locally.
    python examples/03_handoffs.py
"""

import asyncio
from flux import Agent, Runner
from flux.handoffs.handoff import Handoff
from flux.models.ollama import OllamaModel


model = OllamaModel(model="llama3.2")

# Create specialist agents
coder = Agent(
    name="coder",
    instructions="You are an expert programmer. Write clean, efficient code.",
    model=model,
)

writer = Agent(
    name="writer",
    instructions="You are an expert writer. Write clear, engaging content.",
    model=model,
)

# Create router that can hand off to specialists
router = Agent(
    name="router",
    instructions="""You are a router. Analyze the user's request and transfer to the
    appropriate specialist:
    - Use transfer_to_coder for programming questions
    - Use transfer_to_writer for writing questions""",
    model=model,
    handoffs=(
        Handoff(source=router, target=coder),
        Handoff(source=router, target=writer),
    ),
)

async def main():
    # This should route to the coder
    result = await Runner.run(
        router,
        "Write a Python function to check if a number is prime",
    )
    print(f"\n--- Result ---")
    print(f"Agent: {result.last_agent.name}")
    print(f"Output: {result.final_output[:200]}...")
    print(f"Handoffs: {result.handoffs}")

asyncio.run(main())
