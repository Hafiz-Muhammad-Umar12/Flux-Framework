# Flux Architecture

## Overview

Flux is a Python-first Agentic AI Framework with these design principles:

1. **Protocol over ABC** — Structural typing, no inheritance required
2. **Async first** — Non-blocking by default
3. **Zero core deps** — Base framework needs no third-party packages
4. **Middleware over hooks** — Composable, testable, standard pattern
5. **Immutable agents** — Thread-safe via `clone()`
6. **Event-driven** — Decoupled observability

## Directory Structure

```
flux/
├── __init__.py          # Public API (200+ exports)
├── agent.py             # Agent (immutable dataclass)
├── runner.py            # Runner (execution engine)
├── context.py           # RunContext, ToolContext, Usage
├── config.py            # Global configuration
├── exceptions.py        # Exception hierarchy
│
├── models/              # LLM providers
│   ├── base.py          # Model Protocol, ModelRequest/Response
│   ├── registry.py      # ModelRegistry (name → Model)
│   ├── ollama.py        # Ollama provider
│   ├── openai_provider.py # OpenAI provider
│   └── anthropic.py     # Anthropic provider
│
├── tools/               # Tool system
│   ├── base.py          # Tool Protocol, ToolResult
│   ├── decorator.py     # @tool decorator
│   ├── registry.py      # ToolRegistry
│   ├── builtins.py      # Shell, FileRead, FileWrite
│   └── schema.py        # JSON Schema generation
│
├── handoffs/            # Agent routing
│   ├── handoff.py       # Handoff dataclass
│   └── router.py        # Routing logic
│
├── guardrails/          # Safety
│   ├── base.py          # InputGuardrail, OutputGuardrail
│   └── builtins.py      # Length, Profanity, PII
│
├── sessions/            # Persistence
│   ├── base.py          # Session Protocol
│   ├── in_memory.py     # InMemorySession
│   └── sqlite.py        # SQLiteSession
│
├── memory/              # Long-term memory
│   ├── base.py          # Memory Protocol
│   ├── conversation.py  # ConversationMemory
│   └── vector.py        # VectorMemory
│
├── streaming/           # Stream events
│   └── events.py        # TextDelta, ToolCall, etc.
│
├── middleware/           # Composable middleware
│   ├── base.py          # Middleware Protocol
│   ├── logging.py       # LoggingMiddleware
│   ├── rate_limit.py    # RateLimitMiddleware
│   ├── cache.py         # CacheMiddleware
│   └── retry.py         # RetryMiddleware
│
├── events/              # Event bus
│   └── bus.py           # EventBus
│
├── tracing/             # Observability
│   ├── base.py          # Tracer, Span Protocols
│   ├── console.py       # ConsoleTracer
│   └── file.py          # FileTracer
│
└── utils/               # Utilities
    ├── schema.py        # JSON Schema generation
    ├── tokens.py        # Token counting
    └── pretty.py        # Pretty printing
```

## Execution Flow

```
User Input
    │
    ▼
Runner.run(agent, input, context, session)
    │
    ├─► Create RunContext(user_context)
    ├─► Resolve Model (from agent or registry)
    ├─► Load session history (if provided)
    │
    ▼
┌─── Run Loop (max_turns) ───────────────────┐
│                                             │
│  [1] Run Input Guardrails (turn 0 only)     │
│                                             │
│  [2] Build ModelRequest                     │
│      - System prompt from agent             │
│      - Messages (history + user input)      │
│      - Tool definitions                     │
│                                             │
│  [3] Call Model.complete(request)           │
│                                             │
│  [4] Process Response                       │
│      ├─ Tool calls → Execute tools          │
│      ├─ Handoff → Switch agent              │
│      └─ Text → Final output                 │
│                                             │
│  [5] Run Output Guardrails                  │
│                                             │
└─────────────────────────────────────────────┘
    │
    ▼
RunResult(final_output, usage, messages, handoffs)
```

## Data Flow

```
Agent.tools → ToolDef (JSON Schema) → Model
Model → ModelResponse (content/tool_calls) → Runner
Runner → Tool.execute(ctx, args) → ToolResult
ToolResult → Message(role="tool") → Model (next turn)
```

## Component Relationships

```
Agent
  ├─ model: str | Model
  ├─ tools: list[Tool]
  ├─ handoffs: list[Handoff]
  └─ guardrails: list[Guardrail]

Runner
  ├─ creates RunContext
  ├─ resolves Model
  ├─ calls Model.complete()
  ├─ executes Tools
  ├─ evaluates Handoffs
  └─ returns RunResult

Model (Protocol)
  ├─ complete(request) → ModelResponse
  └─ stream(request) → AsyncIterator[StreamChunk]

Tool (Protocol)
  ├─ name, description, parameters_schema
  └─ execute(ctx, args) → ToolResult
```

## Design Decisions

### Why Protocol over ABC?

```python
# Protocol (Flux) — no inheritance needed
class MyModel:
    async def complete(self, request): ...
    async def stream(self, request): ...
    yield

# ABC (traditional) — must inherit
class MyModel(Model):  # Must import and inherit
    async def complete(self, request): ...
```

**Benefit**: Any class with the right methods works. No import needed.

### Why Immutable Agents?

```python
# Immutable — safe to share
agent = Agent(name="bot", instructions="Helpful")
agent2 = agent.clone(name="bot2")  # New instance

# Mutable — dangerous in concurrent code
agent.name = "bot2"  # Race condition risk
```

**Benefit**: Thread-safe, predictable, easy to test.

### Why Middleware over Hooks?

```python
# Middleware (Flux) — composable chain
class LoggingMiddleware:
    async def process(self, ctx, next):
        print("Before")
        response = await next(ctx)
        print("After")
        return response

# Hooks (traditional) — fixed extension points
class MyHooks:
    def on_llm_start(self): ...
    def on_llm_end(self): ...
    def on_tool_start(self): ...
    def on_tool_end(self): ...
```

**Benefit**: Middleware wraps the entire cycle. Can modify request/response, skip calls, etc.

### Why Event Bus?

```python
# Event Bus (Flux) — decoupled
bus.on("agent.start", my_handler)
bus.on("tool.end", analytics_handler)
bus.emit(Event(type="custom.event", data={}))

# Hooks (traditional) — coupled to runner
class MyHooks:
    def on_agent_start(self, agent): ...  # Must modify runner
```

**Benefit**: Any code can subscribe. No framework modification needed.
