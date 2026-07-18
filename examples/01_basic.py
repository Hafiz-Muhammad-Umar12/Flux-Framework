"""Example 01: Basic agent usage.

Requires: Ollama running locally with llama3.2 model.
    ollama pull llama3.2
    python examples/01_basic.py
"""

import asyncio

from flux import Agent, Runner
from flux.models.ollama import OllamaModel

# Create a model (Ollama by default)
model = OllamaModel(model="llama3.2")

# Create an agent
agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant. Be concise.",
    model=model,
)

# Run synchronously
result = Runner.run_sync(agent, "What is the capital of France?")
print(f"\n--- Result ---")
print(f"Output: {result.final_output}")
print(f"Turns: {result.turns}")
print(f"Tokens: {result.usage.total_tokens}")
