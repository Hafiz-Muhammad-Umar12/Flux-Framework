"""Interactive Flux chatbot — continuous chat."""

from flux import Agent, Runner, InMemorySession
from flux.models.ollama import OllamaModel

model = OllamaModel(model="qwen2:0.5b")
session = InMemorySession()

agent = Agent(
    name="chat_bot",
    instructions="Tum ek helpful assistant ho. Chote aur simple jawab do.",
    model=model,
)

print("=" * 50)
print("FLUX CHATBOT")
print("Type 'quit' to exit")
print("=" * 50)

while True:
    user_input = input("\nYou: ").strip()
    if user_input.lower() in ("quit", "exit", "q"):
        print("Allah hafiz!")
        break
    if not user_input:
        continue

    result = Runner.run_sync(agent, user_input, session=session)
    print(f"Bot: {result.final_output}")
