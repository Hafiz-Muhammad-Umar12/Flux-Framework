# Middleware API Reference

Complete API reference for `Middleware` protocol, `RequestContext`, `Response`, and built-in middleware.

---

## `RequestContext`

::: flux.middleware.base.RequestContext

```python
@dataclass
class RequestContext:
    """Request context passed through middleware."""
    agent_name: str
    messages: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

Context object passed through the middleware chain. Contains information about the current agent run.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_name` | `str` | *required* | Name of the agent being processed. |
| `messages` | `list[Any]` | `[]` | The conversation messages. |
| `metadata` | `dict[str, Any]` | `{}` | Arbitrary metadata that middleware can read/write. |

### Usage

```python
from flux.middleware.base import RequestContext

ctx = RequestContext(
    agent_name="WeatherBot",
    messages=[{"role": "user", "content": "Hello!"}],
    metadata={"request_id": "abc-123"},
)
```

---

## `Response`

::: flux.middleware.base.Response

```python
@dataclass
class Response:
    """Response from the model/middleware chain."""
    content: str | None = None
    tool_calls: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

Response object returned by the middleware chain.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str \| None` | `None` | The response text content. |
| `tool_calls` | `list[Any]` | `[]` | Tool calls requested by the model. |
| `metadata` | `dict[str, Any]` | `{}` | Arbitrary metadata. |

### Usage

```python
from flux.middleware.base import Response

resp = Response(
    content="The weather is sunny.",
    metadata={"latency_ms": 250},
)
```

---

## `Middleware` (Protocol)

::: flux.middleware.base.Middleware

```python
@runtime_checkable
class Middleware(Protocol):
    """Protocol for middleware."""

    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        """Process the request, calling next() to continue the chain."""
        ...
```

Middleware components process requests before and after they reach the model. Each middleware receives a `RequestContext` and a `next` function that continues the chain.

### `NextFn`

```python
NextFn = Callable[[RequestContext], Awaitable[Response]]
```

The type alias for the next-function passed to each middleware. Call `await next(ctx)` to continue to the next middleware or the model.

### Methods

#### `process`

```python
async def process(self, ctx: RequestContext, next: NextFn) -> Response:
```

Process a request. Must call `await next(ctx)` to continue the chain (unless short-circuiting).

| Parameter | Type | Description |
|-----------|------|-------------|
| `ctx` | `RequestContext` | The request context. |
| `next` | `NextFn` | The next function in the chain. |

**Returns:** `Response`

### Middleware Chain Pattern

```python
from flux.middleware.base import Middleware, RequestContext, Response, NextFn

class MyMiddleware:
    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        # BEFORE: pre-processing
        print(f"Request for agent: {ctx.agent_name}")

        # Continue chain
        response = await next(ctx)

        # AFTER: post-processing
        print(f"Response: {response.content[:100]}")
        return response
```

### Implementing Custom Middleware

```python
from flux.middleware.base import Middleware, RequestContext, Response, NextFn
import time

class TimingMiddleware:
    """Measures request latency."""

    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        start = time.monotonic()
        response = await next(ctx)
        elapsed_ms = (time.monotonic() - start) * 1000
        ctx.metadata["latency_ms"] = elapsed_ms
        print(f"Agent {ctx.agent_name} responded in {elapsed_ms:.1f}ms")
        return response
```

---

## `LoggingMiddleware`

::: flux.middleware.logging.LoggingMiddleware

```python
class LoggingMiddleware:
    """Logs requests and responses."""

    def __init__(self, level: int = logging.DEBUG) -> None:
        self._level = level
```

Logs agent requests and responses using Python's `logging` module.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | `int` | `logging.DEBUG` | Log level for output messages. |

### Behavior

- Logs the agent name and message count before processing.
- Logs a preview (first 200 characters) of the response after processing.

### Usage

```python
import logging
from flux.middleware.logging import LoggingMiddleware

logging.basicConfig(level=logging.DEBUG)
middleware = LoggingMiddleware(level=logging.DEBUG)
```

### Output Example

```
DEBUG:flux.middleware:-> Agent: WeatherBot, messages: 2
DEBUG:flux.middleware:<- Response: The weather in NYC is sunny, 72F...
```

---

## `CacheMiddleware`

::: flux.middleware.cache.CacheMiddleware

```python
class CacheMiddleware:
    """Caches model responses by message hash with configurable TTL."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, Response]] = {}
```

Caches model responses based on the agent name and messages. Identical requests within the TTL window return cached results without hitting the model.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ttl_seconds` | `float` | `300.0` | Time-to-live in seconds. Cached responses expire after this duration. |

### Cache Key Generation

The cache key is a SHA-256 hash of the JSON-serialized `{"agent": agent_name, "messages": messages}`.

### Methods

#### `process`

```python
async def process(self, ctx: RequestContext, next: NextFn) -> Response:
```

Returns a cached response if the same request was seen within the TTL. Otherwise calls `next(ctx)` and caches the result.

#### `clear`

```python
def clear(self) -> None:
```

Clear all cached responses.

### Usage

```python
from flux.middleware.cache import CacheMiddleware

cache = CacheMiddleware(ttl_seconds=600)  # Cache for 10 minutes

# In a middleware chain:
response = await cache.process(ctx, next_fn)

# Clear cache manually
cache.clear()
```

### Notes

- Cached responses are shared across all agents unless the agent name differs.
- Cache entries expire lazily (checked on access).
- The cache lives in memory and is lost on process restart.

---

## `RateLimitMiddleware`

::: flux.middleware.rate_limit.RateLimitMiddleware

```python
class RateLimitMiddleware:
    """Token bucket rate limiter."""

    def __init__(self, max_per_second: float = 10.0) -> None:
        self._max_per_second = max_per_second
        self._tokens = max_per_second
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()
```

Enforces a token bucket rate limit on requests. When the bucket is empty, requests are delayed until a token becomes available.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_per_second` | `float` | `10.0` | Maximum requests per second. The bucket refills at this rate. |

### Behavior

- Uses a **token bucket** algorithm with asyncio locking.
- Tokens refill based on elapsed time since last request.
- When fewer than 1 token is available, the middleware sleeps for the required wait time.
- Thread-safe via `asyncio.Lock`.

### Usage

```python
from flux.middleware.rate_limit import RateLimitMiddleware

# Allow 5 requests per second
limiter = RateLimitMiddleware(max_per_second=5.0)

# Use in middleware chain
response = await limiter.process(ctx, next_fn)
```

### Algorithm

1. On each request, compute elapsed time since last refill.
2. Add `elapsed * max_per_second` tokens (capped at `max_per_second`).
3. If tokens >= 1, consume one and proceed.
4. If tokens < 1, sleep for `(1 - tokens) / max_per_second` seconds, then proceed.

---

## `RetryMiddleware`

::: flux.middleware.retry.RetryMiddleware

```python
class RetryMiddleware:
    """Retries failed requests with exponential backoff."""

    def __init__(self, max_retries: int = 3, backoff_base: float = 1.0) -> None:
        self._max_retries = max_retries
        self._backoff_base = backoff_base
```

Automatically retries failed requests with exponential backoff. Only retries on `ProviderError` and `ToolError` exceptions.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | `int` | `3` | Maximum number of retries (total attempts = `max_retries + 1`). |
| `backoff_base` | `float` | `1.0` | Base delay in seconds. The delay for attempt `n` is `backoff_base * 2^n`. |

### Retry Schedule

| Attempt | Delay Before Retry |
|---------|-------------------|
| 1st retry | `backoff_base * 1` = 1.0s |
| 2nd retry | `backoff_base * 2` = 2.0s |
| 3rd retry | `backoff_base * 4` = 4.0s |

### Retried Exceptions

| Exception | Description |
|-----------|-------------|
| `ProviderError` | LLM provider returned an error. |
| `ToolError` | A tool execution failed. |

### Usage

```python
from flux.middleware.retry import RetryMiddleware

retry = RetryMiddleware(max_retries=3, backoff_base=1.0)

# Use in middleware chain
response = await retry.process(ctx, next_fn)
```

!!! note
    After exhausting all retries, the last exception is re-raised. Other exceptions (e.g., `MaxTurnsExceeded`, `GuardrailTripwireError`) are not retried.

---

## Middleware Chain Example

Combine multiple middleware into a chain:

```python
from flux.middleware.logging import LoggingMiddleware
from flux.middleware.cache import CacheMiddleware
from flux.middleware.rate_limit import RateLimitMiddleware
from flux.middleware.retry import RetryMiddleware
from flux.middleware.base import RequestContext, Response, NextFn

# Define your middleware stack
middleware_stack = [
    LoggingMiddleware(),
    CacheMiddleware(ttl_seconds=300),
    RateLimitMiddleware(max_per_second=10),
    RetryMiddleware(max_retries=3),
]

# Build the chain
async def build_chain(middlewares, final_handler):
    """Build a middleware chain from a list of middleware."""
    handler = final_handler

    for mw in reversed(middlewares):
        # Capture mw and handler in closure
        prev_handler = handler
        async def chain_handler(ctx, _next=prev_handler, _mw=mw):
            return await _mw.process(ctx, _next)
        handler = chain_handler

    return handler

# Create chain
async def model_handler(ctx: RequestContext) -> Response:
    # Your actual model call here
    return Response(content="Hello!")

chain = await build_chain(middleware_stack, model_handler)

# Execute
ctx = RequestContext(agent_name="MyAgent", messages=[...])
response = await chain(ctx)
```
