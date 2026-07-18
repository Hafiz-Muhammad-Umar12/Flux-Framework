"""Tools test with Flux."""

from flux import Agent, Runner, tool
from flux.models.ollama import OllamaModel


@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@tool
def greet(name: str) -> str:
    """Greet someone."""
    return f"Assalam o Alaikum {name}!"


model = OllamaModel(model="qwen2:0.5b")
agent = Agent(
    name="math_bot",
    instructions="You are a math helper. Use tools for calculations.",
    model=model,
    tools=[add, greet],
)

# Note: qwen2:0.5b tool calling support nahi karta
# Bigger model use karo for tools: ollama pull qwen2:1.5b
result = Runner.run_sync(agent, "What is 10 + 20?")
print(f"Bot: {result.final_output}")
