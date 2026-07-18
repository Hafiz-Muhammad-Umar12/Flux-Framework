"""Example 02: Using tools with agents.

Requires: Ollama running locally.
    python examples/02_tools.py
"""

import asyncio
from flux import Agent, Runner, tool
from flux.models.ollama import OllamaModel


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Use Python syntax (e.g., '2 + 3 * 4')."""
    try:
        result = eval(expression)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


model = OllamaModel(model="llama3.2")
agent = Agent(
    name="math_bot",
    instructions="You are a math assistant. Use the calculator tool for calculations.",
    model=model,
    tools=[calculator, get_current_time],
)

async def main():
    result = await Runner.run(
        agent,
        "What is 15 * 23 + 7? Also, what time is it?",
    )
    print(f"\n--- Result ---")
    print(f"Output: {result.final_output}")
    print(f"Turns: {result.turns}")

asyncio.run(main())
