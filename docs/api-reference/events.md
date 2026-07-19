# Events & Streaming API Reference

Complete API reference for `Event`, `EventBus`, event type constants, and stream event types.

---

## Event Type Constants

The following constants are defined in `flux.events.bus` for use with the `EventBus`:

| Constant | Value | Description |
|----------|-------|-------------|
| `AGENT_START` | `"agent.start"` | Emitted when an agent begins processing. |
| `AGENT_END` | `"agent.end"` | Emitted when an agent finishes processing. |
| `LLM_START` | `"llm.start"` | Emitted just before calling the model. |
| `LLM_END` | `"llm.end"` | Emitted just after the model returns. |
| `TOOL_START` | `"tool.start"` | Emitted before a tool is executed. |
| `TOOL_END` | `"tool.end"` | Emitted after a tool finishes execution. |
| `HANDOFF` | `"handoff"` | Emitted when a handoff to another agent occurs. |
| `GUARDRAIL_CHECK` | `"guardrail.check"` | Emitted when a guardrail is being evaluated. |
| `GUARDRAIL_TRIGGERED` | `"guardrail.triggered"` | Emitted when a guardrail tripwire fires. |
| `STREAM_CHUNK` | `"stream.chunk"` | Emitted for each streaming chunk. |
| `RUN_START` | `"run.start"` | Emitted at the start of a `Runner.run()` call. |
| `RUN_END` | `"run.end"` | Emitted at the end of a `Runner.run()` call. |

### Usage

```python
from flux.events import AGENT_START, LLM_END, TOOL_START, HANDOFF

def on_event(event):
    if event.type == AGENT_START:
        print(f"Agent started: {event.data['agent']}")
    elif event.type == HANDOFF:
        print(f"Handoff: {event.data['source']} -> {event.data['target']}")
```

---

## `Event`

::: flux.events.bus.Event

```python
@dataclass(frozen=True)
class Event:
    """Base event."""
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
```

An immutable event object emitted by the Runner and consumed by event handlers.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | `str` | *required* | The event type (one of the event type constants). |
| `data` | `dict[str, Any]` | `{}` | Event payload. Structure varies by event type. |
| `timestamp` | `float` | `time.time()` | Unix timestamp when the event was created. |

### Event Data by Type

| Event Type | Data Fields |
|------------|-------------|
| `AGENT_START` | `{"agent": str}` |
| `AGENT_END` | `{"agent": str}` |
| `LLM_START` | `{"agent": str}` |
| `LLM_END` | `{"agent": str}` |
| `TOOL_START` | `{"tool": str, "args": str}` |
| `TOOL_END` | `{"tool": str, "success": bool}` |
| `HANDOFF` | `{"source": str, "target": str, "tool_name": str}` |
| `RUN_START` | `{"agent": str}` |
| `RUN_END` | `{"agent": str}` |

### Usage

```python
from flux.events.bus import Event

event = Event(type="agent.start", data={"agent": "WeatherBot"})
print(event.type)       # "agent.start"
print(event.data)       # {"agent": "WeatherBot"}
print(event.timestamp)  # 1721234567.89
```

---

## `EventBus`

::: flux.events.bus.EventBus

```python
class EventBus:
    """Decoupled event bus for observability."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = {}
        self._global_handlers: list[Callable] = []
```

A pub/sub event bus for decoupled observability. Handlers subscribe to specific event types or all events, and are invoked when events are emitted.

### Methods

#### `on`

```python
def on(self, event_type: str, handler: Callable) -> None:
```

Subscribe a handler to a specific event type. Multiple handlers can subscribe to the same type.

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_type` | `str` | The event type to subscribe to (e.g., `"agent.start"`). |
| `handler` | `Callable` | The handler function. Receives an `Event` argument. |

#### `on_all`

```python
def on_all(self, handler: Callable) -> None:
```

Subscribe a handler to all events.

| Parameter | Type | Description |
|-----------|------|-------------|
| `handler` | `Callable` | The handler function. Receives an `Event` argument. |

#### `off`

```python
def off(self, event_type: str, handler: Callable) -> None:
```

Unsubscribe a handler from a specific event type.

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_type` | `str` | The event type. |
| `handler` | `Callable` | The handler to remove. |

#### `emit`

```python
def emit(self, event: Event) -> None:
```

Emit an event synchronously. All subscribed handlers are called in registration order.

| Parameter | Type | Description |
|-----------|------|-------------|
| `event` | `Event` | The event to emit. |

#### `emit_async`

```python
async def emit_async(self, event: Event) -> None:
```

Emit an event asynchronously. Handles both sync and async handlers. Async handlers are awaited.

| Parameter | Type | Description |
|-----------|------|-------------|
| `event` | `Event` | The event to emit. |

#### `clear`

```python
def clear(self) -> None:
```

Remove all handlers (both type-specific and global).

### Global Event Bus Functions

```python
def get_event_bus() -> EventBus:
    """Get the global event bus singleton."""

def set_event_bus(bus: EventBus) -> None:
    """Set the global event bus singleton."""
```

### Usage

```python
from flux.events.bus import EventBus, Event, AGENT_START, LLM_END, get_event_bus

# Create a custom bus
bus = EventBus()

# Subscribe to specific events
def on_agent_start(event: Event):
    print(f"Agent starting: {event.data['agent']}")

bus.on(AGENT_START, on_agent_start)

# Subscribe to all events
def log_all(event: Event):
    print(f"[{event.type}] {event.data}")

bus.on_all(log_all)

# Emit events
bus.emit(Event(type=AGENT_START, data={"agent": "MyBot"}))

# Remove a handler
bus.off(AGENT_START, on_agent_start)

# Use the global bus
global_bus = get_event_bus()
```

### Disabling Events

Events are controlled by the `FluxConfig.event_bus_enabled` flag. When disabled (`False`), the Runner skips all `bus.emit()` calls.

```python
from flux.config import FluxConfig, set_config

set_config(FluxConfig(event_bus_enabled=False))
```

---

## Stream Event Types

Stream events are yielded by `StreamResult` during `Runner.run_streamed()`. All stream events are frozen dataclasses.

---

### `TextDeltaEvent`

::: flux.streaming.events.TextDeltaEvent

```python
@dataclass(frozen=True)
class TextDeltaEvent:
    """Incremental text from the model."""
    delta: str
```

Emitted for each incremental text token during streaming.

| Field | Type | Description |
|-------|------|-------------|
| `delta` | `str` | The text delta to append. |

```python
async for event in stream:
    if isinstance(event, TextDeltaEvent):
        print(event.delta, end="", flush=True)
```

---

### `ToolCallDeltaEvent`

::: flux.streaming.events.ToolCallDeltaEvent

```python
@dataclass(frozen=True)
class ToolCallDeltaEvent:
    """Incremental tool call arguments."""
    tool_call_id: str
    name: str | None = None
    arguments_delta: str = ""
```

Emitted for incremental tool call argument updates during streaming.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tool_call_id` | `str` | *required* | The tool call identifier. |
| `name` | `str \| None` | `None` | The tool name (set on first delta). |
| `arguments_delta` | `str` | `""` | Incremental JSON argument string. |

---

### `ToolCallEvent`

::: flux.streaming.events.ToolCallEvent

```python
@dataclass(frozen=True)
class ToolCallEvent:
    """Complete tool call."""
    tool_call_id: str
    name: str
    arguments: str
```

Emitted when a complete tool call has been accumulated during streaming.

| Field | Type | Description |
|-------|------|-------------|
| `tool_call_id` | `str` | Unique tool call identifier. |
| `name` | `str` | The tool name. |
| `arguments` | `str` | Complete JSON-encoded arguments string. |

---

### `MessageCompleteEvent`

::: flux.streaming.events.MessageCompleteEvent

```python
@dataclass(frozen=True)
class MessageCompleteEvent:
    """Full message from the model."""
    content: str | None = None
    tool_calls: list[ToolCallEvent] = field(default_factory=list)
```

Emitted when the model has finished producing a complete message during streaming.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | `str \| None` | `None` | The complete text content. |
| `tool_calls` | `list[ToolCallEvent]` | `[]` | All tool calls in this message. |

---

### `UsageEvent`

::: flux.streaming.events.UsageEvent

```python
@dataclass(frozen=True)
class UsageEvent:
    """Token usage update."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
```

Emitted to report token usage during streaming.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `input_tokens` | `int` | `0` | Tokens in the prompt. |
| `output_tokens` | `int` | `0` | Tokens in the completion. |
| `total_tokens` | `int` | `0` | Total tokens used. |

---

### `ErrorEvent`

::: flux.streaming.events.ErrorEvent

```python
@dataclass(frozen=True)
class ErrorEvent:
    """Error during streaming."""
    message: str
    details: dict[str, Any] = field(default_factory=dict)
```

Emitted when an error occurs during streaming.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `message` | `str` | *required* | Error description. |
| `details` | `dict[str, Any]` | `{}` | Additional error details. |

---

### `AgentUpdatedEvent`

::: flux.streaming.events.AgentUpdatedEvent

```python
@dataclass(frozen=True)
class AgentUpdatedEvent:
    """Agent changed (on handoff)."""
    agent_name: str
```

Emitted when the active agent changes, typically during a handoff.

| Field | Type | Description |
|-------|------|-------------|
| `agent_name` | `str` | Name of the new active agent. |

---

## `StreamEvent` (Union Type)

::: flux.streaming.events.StreamEvent

```python
StreamEvent = Union[
    TextDeltaEvent,
    ToolCallDeltaEvent,
    ToolCallEvent,
    MessageCompleteEvent,
    UsageEvent,
    ErrorEvent,
    AgentUpdatedEvent,
]
```

The union type representing all possible stream events. Use `isinstance()` to check the event type.

### Handling All Event Types

```python
from flux.streaming.events import (
    StreamEvent, TextDeltaEvent, ToolCallEvent,
    MessageCompleteEvent, UsageEvent, ErrorEvent, AgentUpdatedEvent,
)

async def process_stream(stream):
    async for event in stream:
        match event:
            case TextDeltaEvent(delta=text):
                print(text, end="", flush=True)
            case ToolCallEvent(name=name, arguments=args):
                print(f"\nTool call: {name}({args})")
            case MessageCompleteEvent(content=content):
                print(f"\nMessage complete: {content}")
            case UsageEvent(total_tokens=tokens):
                print(f"\nTokens used: {tokens}")
            case ErrorEvent(message=msg):
                print(f"\nError: {msg}")
            case AgentUpdatedEvent(agent_name=name):
                print(f"\nAgent changed to: {name}")
```
