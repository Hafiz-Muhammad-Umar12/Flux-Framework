# Providers API Reference

Complete API reference for `Model`, `ModelSettings`, `ModelRequest`, `ModelResponse`, `StreamChunk`, `Message`, `ToolCall`, `ToolDef`, `ModelRegistry`, and provider implementations.

---

## `ModelSettings`

::: flux.models.base.ModelSettings

```python
@dataclass
class ModelSettings:
    """Model generation settings."""
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: list[str] | None = None
    seed: int | None = None
    tool_choice: str | dict[str, Any] | None = None
    parallel_tool_calls: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)
```

Generation parameters passed to the LLM on every request. All fields are optional; `None` means the provider's default is used.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | `float \| None` | `None` | Sampling temperature (0.0–2.0). Higher values produce more random output. |
| `top_p` | `float \| None` | `None` | Nucleus sampling threshold (0.0–1.0). |
| `max_tokens` | `int \| None` | `None` | Maximum tokens in the response. |
| `frequency_penalty` | `float \| None` | `None` | Penalty for frequent token repetition (-2.0 to 2.0). |
| `presence_penalty` | `float \| None` | `None` | Penalty for token repetition (-2.0 to 2.0). |
| `stop` | `list[str] \| None` | `None` | Stop sequences. |
| `seed` | `int \| None` | `None` | Random seed for reproducibility. |
| `tool_choice` | `str \| dict[str, Any] \| None` | `None` | Tool selection strategy (`"auto"`, `"none"`, `"required"`, or `{"type": "function", "function": {"name": "..."}}`). |
| `parallel_tool_calls` | `bool \| None` | `None` | Whether the model may call multiple tools simultaneously. |
| `extra` | `dict[str, Any]` | `{}` | Provider-specific extra parameters. |

### Methods

#### `resolve`

```python
def resolve(self, override: ModelSettings | None) -> ModelSettings:
```

Merge non-`None` values from an override onto this instance. Used to layer config-level defaults under agent-level settings.

| Parameter | Type | Description |
|-----------|------|-------------|
| `override` | `ModelSettings \| None` | The override settings. `None` returns `self` unchanged. |

**Returns:** `ModelSettings` — merged settings.

### Usage

```python
from flux.models.base import ModelSettings

# Base settings from config
base = ModelSettings(temperature=0.7, max_tokens=2048)

# Agent-level override
override = ModelSettings(temperature=0.2)

# Merge: temperature becomes 0.2, max_tokens stays 2048
resolved = base.resolve(override)
```

---

## `ToolDef`

::: flux.models.base.ToolDef

```python
@dataclass
class ToolDef:
    """Tool definition sent to the model."""
    name: str
    description: str
    parameters: dict[str, Any]
    strict: bool = True
```

A tool definition as sent to the LLM in the API request.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Tool name. |
| `description` | `str` | *required* | Tool description. |
| `parameters` | `dict[str, Any]` | *required* | JSON Schema for the tool's parameters. |
| `strict` | `bool` | `True` | Whether strict parameter validation is enabled. |

---

## `ToolCall`

::: flux.models.base.ToolCall

```python
@dataclass
class ToolCall:
    """A tool call from the model."""
    id: str
    name: str
    arguments: str
```

Represents a tool invocation requested by the model.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `str` | *required* | Unique identifier for this tool call (provider-assigned). |
| `name` | `str` | *required* | The name of the tool to call. |
| `arguments` | `str` | *required* | JSON-encoded arguments string. |

---

## `Message`

::: flux.models.base.Message

```python
@dataclass
class Message:
    """A message in the conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str | None = None
    tool_call_id: str | None = None
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
```

A single message in the conversation history.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `role` | `str` | *required* | One of `"system"`, `"user"`, `"assistant"`, or `"tool"`. |
| `content` | `str \| None` | `None` | Message text content. |
| `tool_call_id` | `str \| None` | `None` | For tool messages, the ID of the tool call being responded to. |
| `name` | `str \| None` | `None` | For tool messages, the name of the tool. |
| `tool_calls` | `list[ToolCall] \| None` | `None` | For assistant messages, tool calls requested by the model. |

### Usage

```python
from flux.models.base import Message, ToolCall

# User message
msg = Message(role="user", content="What is the weather?")

# Assistant with tool calls
msg = Message(
    role="assistant",
    content="Let me check that.",
    tool_calls=[ToolCall(id="call_1", name="get_weather", arguments='{"city": "NYC"}')],
)

# Tool result
msg = Message(
    role="tool",
    content="Sunny, 72F",
    tool_call_id="call_1",
    name="get_weather",
)
```

---

## `ModelRequest`

::: flux.models.base.ModelRequest

```python
@dataclass
class ModelRequest:
    """Request to a model."""
    messages: list[Message]
    system_prompt: str | None = None
    tools: list[ToolDef] | None = None
    output_schema: dict[str, Any] | None = None
    settings: ModelSettings = field(default_factory=ModelSettings)
    stream: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
```

A complete request sent to a model provider.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | `list[Message]` | *required* | Conversation messages. |
| `system_prompt` | `str \| None` | `None` | System/instructions prompt. |
| `tools` | `list[ToolDef] \| None` | `None` | Available tools. |
| `output_schema` | `dict[str, Any] \| None` | `None` | JSON Schema for structured output (OpenAI `response_format`). |
| `settings` | `ModelSettings` | `ModelSettings()` | Generation settings. |
| `stream` | `bool` | `False` | Whether to stream the response. |
| `extra` | `dict[str, Any]` | `{}` | Provider-specific extra parameters. |

---

## `ModelResponse`

::: flux.models.base.ModelResponse

```python
@dataclass
class ModelResponse:
    """Response from a model."""
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage | None = None
    finish_reason: str | None = None
    raw: Any = None
```

A complete (non-streamed) response from a model.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str \| None` | `None` | Text content of the response. |
| `tool_calls` | `list[ToolCall]` | `[]` | Tool calls requested by the model. |
| `usage` | `Usage \| None` | `None` | Token usage for this request. |
| `finish_reason` | `str \| None` | `None` | Why the model stopped (e.g., `"stop"`, `"tool_calls"`, `"length"`). |
| `raw` | `Any` | `None` | The raw provider response object. |

---

## `StreamChunk`

::: flux.models.base.StreamChunk

```python
@dataclass
class StreamChunk:
    """A chunk from a streaming model response."""
    delta_text: str | None = None
    tool_call: ToolCall | None = None
    usage: Usage | None = None
    done: bool = False
    raw: Any = None
```

A single chunk yielded during streaming.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delta_text` | `str \| None` | `None` | Incremental text content. |
| `tool_call` | `ToolCall \| None` | `None` | A completed tool call (emitted once when fully accumulated). |
| `usage` | `Usage \| None` | `None` | Token usage (typically in the final chunk). |
| `done` | `bool` | `False` | Whether this is the final chunk. |
| `raw` | `Any` | `None` | Raw provider chunk data. |

---

## `Model` (Protocol)

::: flux.models.base.Model

```python
@runtime_checkable
class Model(Protocol):
    """Protocol for an LLM provider."""

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Get a complete response from the model."""
        ...

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        """Stream a response from the model."""
        ...
```

The protocol that all LLM providers must implement.

### Methods

#### `complete`

```python
async def complete(self, request: ModelRequest) -> ModelResponse:
```

Send a request and receive a complete response.

| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | `ModelRequest` | The request to send. |

**Returns:** `ModelResponse`

#### `stream`

```python
async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
```

Send a request and stream the response as chunks.

| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | `ModelRequest` | The request to send. |

**Returns:** `AsyncIterator[StreamChunk]`

---

## `ModelRegistry`

::: flux.models.registry.ModelRegistry

```python
class ModelRegistry:
    """Registry for resolving model names to Model instances."""

    def __init__(self) -> None:
        self._models: dict[str, Model] = {}
        self._providers: dict[str, Model] = {}
```

Resolves model name strings to `Model` instances. Supports exact name matches and prefix-based provider routing (e.g., `"ollama/llama3"`).

### Methods

#### `register`

```python
def register(self, name: str, model: Model) -> None:
```

Register a model by exact name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Exact model name to register. |
| `model` | `Model` | The model instance. |

#### `register_provider`

```python
def register_provider(self, prefix: str, model: Model) -> None:
```

Register a model provider by prefix. Any model name starting with `{prefix}/` resolves to this model.

| Parameter | Type | Description |
|-----------|------|-------------|
| `prefix` | `str` | Provider prefix (e.g., `"ollama"`, `"openai"`). |
| `model` | `Model` | The model instance to use for this provider. |

#### `resolve`

```python
def resolve(self, name: str) -> Model:
```

Resolve a model name to a `Model` instance. Tries exact match first, then prefix match.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Model name (e.g., `"gpt-4o"`, `"ollama/llama3"`). |

**Returns:** `Model`

**Raises:** `ValueError` — if the model is not found.

### Global Registry Functions

```python
def get_default_registry() -> ModelRegistry:
    """Get the global model registry singleton."""

def set_default_registry(registry: ModelRegistry) -> None:
    """Set the global model registry singleton."""
```

### Usage

```python
from flux.models.registry import ModelRegistry, get_default_registry, set_default_registry
from flux.models.ollama import OllamaModel
from flux.models.openai_provider import OpenAIModel

# Create and configure a registry
registry = ModelRegistry()
registry.register("gpt-4o", OpenAIModel(model="gpt-4o"))
registry.register_provider("ollama", OllamaModel(model="llama3.2"))
registry.register_provider("openai", OpenAIModel(model="gpt-4o-mini"))

# Resolve models
gpt = registry.resolve("gpt-4o")           # exact match
llama = registry.resolve("ollama/llama3")   # prefix match -> OllamaModel

# Set as global
set_default_registry(registry)

# Later, retrieve it
reg = get_default_registry()
```

---

## `OllamaModel`

::: flux.models.ollama.OllamaModel

```python
class OllamaModel:
    """Ollama model provider using aiohttp."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
```

Provider for locally-running Ollama models.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"llama3.2"` | Ollama model name. |
| `base_url` | `str` | `"http://localhost:11434"` | Ollama API base URL. |

### Requirements

Install with: `pip install flux-agents[ollama]` (requires `aiohttp`).

### Methods

#### `complete`

```python
async def complete(self, request: ModelRequest) -> ModelResponse:
```

Get a complete response from Ollama. Automatically retries without tools if the model does not support them.

#### `stream`

```python
async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
```

Stream a response from Ollama via newline-delimited JSON.

### Usage

```python
from flux.models.ollama import OllamaModel

# Default (localhost)
model = OllamaModel()

# Custom model and URL
model = OllamaModel(model="codellama", base_url="http://my-server:11434")
```

---

## `OpenAIModel`

::: flux.models.openai_provider.OpenAIModel

```python
class OpenAIModel:
    """OpenAI-compatible model provider.
    Works with OpenAI, OpenRouter, DeepSeek, Groq, and any OpenAI-compatible API.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
```

Provider for OpenAI and any OpenAI-compatible API.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"gpt-4o-mini"` | Model identifier. |
| `api_key` | `str \| None` | `None` | API key. Falls back to `OPENAI_API_KEY` environment variable. |
| `base_url` | `str \| None` | `None` | Custom API base URL (for OpenRouter, DeepSeek, etc.). |

### Requirements

Install with: `pip install flux-agents[openai]` (requires `openai`).

### Methods

#### `complete`

```python
async def complete(self, request: ModelRequest) -> ModelResponse:
```

Get a complete response from OpenAI.

#### `stream`

```python
async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
```

Stream a response from OpenAI. Accumulates tool call deltas and emits them as complete `ToolCall` objects on `finish_reason`.

### Usage

```python
from flux.models.openai_provider import OpenAIModel

# OpenAI
model = OpenAIModel(model="gpt-4o")

# OpenRouter
model = OpenAIModel(
    model="anthropic/claude-3.5-sonnet",
    api_key="sk-or-...",
    base_url="https://openrouter.ai/api/v1",
)

# DeepSeek
model = OpenAIModel(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
)
```

---

## `AnthropicModel`

::: flux.models.anthropic.AnthropicModel

```python
class AnthropicModel:
    """Anthropic Claude model provider."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
```

Provider for Anthropic Claude models.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"claude-sonnet-4-20250514"` | Claude model identifier. |
| `api_key` | `str \| None` | `None` | Anthropic API key. Falls back to `ANTHROPIC_API_KEY` environment variable. |

### Requirements

Install with: `pip install flux-agents[anthropic]` (requires `anthropic`).

### Methods

#### `complete`

```python
async def complete(self, request: ModelRequest) -> ModelResponse:
```

Get a complete response from Anthropic. Handles the Anthropic content-block format (text + tool_use blocks).

#### `stream`

```python
async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
```

Stream a response from Anthropic. Tracks tool use content blocks and emits complete `ToolCall` objects on `content_block_stop`.

### Usage

```python
from flux.models.anthropic import AnthropicModel

model = AnthropicModel(model="claude-sonnet-4-20250514")
model = AnthropicModel(model="claude-haiku-4-20250514", api_key="sk-ant-...")
```

### Notes

- Anthropic uses a separate `system` parameter (not a message). The provider handles this automatically.
- `max_tokens` defaults to `4096` if not specified in `ModelSettings`.
- Tool definitions use `input_schema` instead of `parameters` (the provider handles the mapping).
