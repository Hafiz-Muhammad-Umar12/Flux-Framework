"""Example 08: Multi-agent system with tools and handoffs.

Requires: Ollama running locally.
    python examples/08_multi_agent.py
"""

import asyncio
from flux import Agent, Runner, tool
from flux.handoffs.handoff import Handoff
from flux.models.ollama import OllamaModel


model = OllamaModel(model="llama3.2")


# ── Tools ──────────────────────────────────────────────────
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Simulated web search
    return f"Search results for '{query}': Found relevant information about {query}."


@tool
def write_code(description: str) -> str:
    """Write code based on a description."""
    return f"# Code for: {description}\ndef solution():\n    pass"


@tool
def analyze_data(data: str) -> str:
    """Analyze the given data."""
    return f"Analysis of '{data}': The data shows interesting patterns."


# ── Agents ─────────────────────────────────────────────────
researcher = Agent(
    name="researcher",
    instructions="You research topics thoroughly using the search tool.",
    model=model,
    tools=[search_web],
)

coder = Agent(
    name="coder",
    instructions="You write clean, efficient code using the write_code tool.",
    model=model,
    tools=[write_code],
)

analyst = Agent(
    name="analyst",
    instructions="You analyze data and provide insights using the analyze_data tool.",
    model=model,
    tools=[analyze_data],
)

# ── Router ─────────────────────────────────────────────────
router = Agent(
    name="router",
    instructions="""You are a multi-agent router. Analyze the request and transfer:
    - transfer_to_researcher for research questions
    - transfer_to_coder for coding tasks
    - transfer_to_analyst for data analysis""",
    model=model,
    handoffs=(
        Handoff(source=router, target=researcher),
        Handoff(source=router, target=coder),
        Handoff(source=router, target=analyst),
    ),
)


async def main():
    tasks = [
        "Research the latest trends in AI",
        "Write a Python function to merge two sorted lists",
        "Analyze the performance metrics of our system",
    ]

    for task in tasks:
        print(f"\n{'='*60}")
        print(f"Task: {task}")
        print(f"{'='*60}")

        result = await Runner.run(router, task)
        print(f"Agent: {result.last_agent.name}")
        print(f"Output: {result.final_output[:200]}")
        print(f"Handoffs: {len(result.handoffs)}")

asyncio.run(main())
