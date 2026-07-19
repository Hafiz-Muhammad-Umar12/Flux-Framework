# Building a Chatbot

A step-by-step guide to building a multi-turn chatbot with session persistence, streaming, and an interactive CLI using the Flux framework.

---

## Overview

In this guide you will build a chatbot that:

- Maintains conversation history across multiple turns
- Uses session persistence so conversations survive restarts
- Streams responses in real time
- Provides an interactive command-line interface

---

## Prerequisites

- Python 3.10+
- Flux installed (`pip install flux-agents`)
- An Ollama instance running locally (or swap in `OpenAIModel` / `AnthropicModel`)

---

## 1 -- Create the Agent

Start with a basic agent that has clear conversational instructions.

```python
from flux import Agent
from flux.models.ollama import OllamaModel

agent = Agent(
    name="chatbot",
    instructions=(
        "You are a friendly, helpful chatbot. "
        "Remember the context of the conversation and refer back to things "
        "the user has told you. Keep responses concise and conversational."
    ),
    model=OllamaModel(model="llama3.2"),
)
```

---

## 2 -- Understand Sessions

Sessions store conversation history so the agent can reference earlier messages. Flux ships two built-in session backends:

| Backend | Storage | Use Case |
|---|---|---|
| `InMemorySession` | RAM only | Prototyping, testing |
| `SQLiteSession` | SQLite file | Persistence across restarts |

### InMemorySession

```python
from flux import InMemorySession

session = InMemorySession()
```

!!! warning "InMemorySession is lost on restart"
    Data lives only in process memory. Use `SQLiteSession` if you need durability.

### SQLiteSession

```python
from flux import SQLiteSession

session = SQLiteSession(path="chatbot.db")
```

`SQLiteSession` writes conversation history to a local SQLite database. The file is created automatically on first use.

---

## 3 -- Run Multi-Turn Conversations

Pass the same `session` object to every `Runner.run()` call. The framework appends new messages to the session automatically.

```python
import asyncio
from flux import Agent, Runner, InMemorySession
from flux.models.ollama import OllamaModel

agent = Agent(
    name="chatbot",
    instructions="You are a friendly chatbot. Remember the conversation context.",
    model=OllamaModel(model="llama3.2"),
)

async def main():
    session = InMemorySession()

    # Turn 1
    result1 = await Runner.run(agent, "Hi, I'm Alice!", session=session)
    print("Bot:", result1.final_output)

    # Turn 2 -- agent remembers the name
    result2 = await Runner.run(agent, "What's my name?", session=session)
    print("Bot:", result2.final_output)

asyncio.run(main())
```

Expected output (exact text varies by model):

```
Bot: Hi Alice! Nice to meet you. How can I help you today?
Bot: Your name is Alice! You told me at the start of our conversation.
```

---

## 4 -- Streaming Responses

For a snappier user experience, stream tokens as they are generated.

```python
async def stream_chat(session, message: str):
    result = await Runner.run_streamed(agent, message, session=session)
    async for event in result.stream_events():
        if hasattr(event, "delta_text"):
            print(event.delta_text, end="", flush=True)
    print()  # newline after stream finishes
```

---

## 5 -- Interactive Chat Loop

Combine everything into a REPL-style loop.

```python
"""Interactive chatbot with session persistence."""

import asyncio
from flux import Agent, Runner, SQLiteSession
from flux.models.ollama import OllamaModel

agent = Agent(
    name="chatbot",
    instructions="You are a friendly chatbot. Remember the conversation context.",
    model=OllamaModel(model="llama3.2"),
)

async def main():
    session = SQLiteSession(path="chatbot.db")
    print("Chatbot ready! Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not user_input:
            continue

        result = await Runner.run_streamed(agent, user_input, session=session)
        print("Bot: ", end="")
        async for event in result.stream_events():
            if hasattr(event, "delta_text"):
                print(event.delta_text, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python chatbot.py
```

```
Chatbot ready! Type 'quit' to exit.

You: Hi, I'm Alice!
Bot: Hi Alice! Nice to meet you. How can I help you today?

You: What's my name?
Bot: Your name is Alice!

You: quit
Goodbye!
```

---

## 6 -- Adding a System Prompt with Tools

Give your chatbot extra capabilities by adding tools.

```python
from flux import tool

@tool
def get_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

agent = Agent(
    name="chatbot",
    instructions="You are a helpful assistant with access to the current time.",
    model=OllamaModel(model="llama3.2"),
    tools=[get_time],
)
```

Now the user can ask "What time is it?" and the agent will call the tool automatically.

---

## Next Steps

- Add a [RAG pipeline](rag.md) so the chatbot can answer questions from your documents
- Use [guardrails](weather-agent.md#3-add-input-guardrails) to filter sensitive input
- Deploy with [middleware](middleware.md) for logging and rate limiting
