"""Mera pehla Flux chatbot."""

from flux import Agent, Runner
from flux.models.ollama import OllamaModel

# Model setup
model = OllamaModel(model="qwen2:0.5b")

# Agent banao
agent = Agent(
    name="mera_bot",
    instructions="Tum ek helpful assistant ho. Urdu aur English mein jawab do.",
    model=model,
)

# Chat karo
result = Runner.run_sync(agent, "Helo")
print(f"Bot: {result.final_output}")
