# Production Deployment

Best practices for deploying Flux Agents in production.

This guide covers configuration management, error handling, rate limiting, session persistence, monitoring, logging, security, and scaling for production-grade Flux Agents deployments.

---

## Configuration Management

### Environment-Based Configuration

Use environment variables to manage configuration across environments. Flux Agents supports a `FluxConfig` dataclass that maps to environment settings:

```python
from flux import FluxConfig, set_config

config = FluxConfig(
    default_model="gpt-4o",
    default_max_turns=15,
    event_bus_enabled=True,
    tracing_enabled=True,
    log_level="WARNING",
)
set_config(config)
```

### Per-Agent Configuration

Override settings at the agent level for fine-grained control:

```python
from flux import Agent, AgentSettings, ModelSettings

agent = Agent(
    name="production-agent",
    instructions="You are a helpful assistant.",
    model="gpt-4o",
    settings=AgentSettings(
        max_turns=20,
        model_settings=ModelSettings(
            temperature=0.7,
            max_tokens=4096,
            top_p=0.9,
        ),
    ),
)
```

### Twelve-Factor App Principles

Follow twelve-factor app methodology for production configurations:

1. **Config in environment** -- Store secrets and environment-specific values in environment variables, not in code.
2. **Separate config from code** -- Use `FluxConfig` to externalize all tunable parameters.
3. **Logs as event streams** -- Write logs to `stdout`/`stderr` for container orchestrators to capture.

---

## Error Handling Strategies

Flux Agents provides a hierarchy of typed exceptions under `FluxError`. Handle each appropriately in production:

```python
from flux import (
    Runner,
    FluxError,
    MaxTurnsExceeded,
    ProviderError,
    ToolError,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    ModelBehaviorError,
)

try:
    result = await Runner.run(agent, user_input, session=session)
except MaxTurnsExceeded:
    # Agent looped too many times -- return partial result or error message
    return "I wasn't able to complete your request. Please try again."
except ProviderError as e:
    # LLM provider returned an error (rate limit, auth, etc.)
    logger.error("Provider error: %s (status=%s)", e, e.status_code)
    if e.status_code == 429:
        return "Service is temporarily busy. Please retry in a moment."
    return "An error occurred with the AI service."
except ToolError as e:
    # A tool execution failed
    logger.error("Tool '%s' failed: %s", e.tool_name, e.tool_error)
    return f"Tool execution failed: {e.tool_name}"
except InputGuardrailTripwireTriggered as e:
    # Input was rejected by a guardrail
    logger.warning("Input guardrail triggered: %s", e.guardrail_name)
    return "Your input was rejected by our safety filters."
except OutputGuardrailTripwireTriggered as e:
    # Output was rejected by a guardrail
    logger.warning("Output guardrail triggered: %s", e.guardrail_name)
    return "The response was filtered. Please rephrase your question."
except ModelBehaviorError:
    # Model returned unexpected output
    logger.error("Model produced unexpected output format")
    return "An internal error occurred. Please try again."
except FluxError as e:
    # Catch-all for other Flux errors
    logger.error("Flux error: %s", e)
    return "An unexpected error occurred."
```

### Error Classification

| Exception | Category | Retryable | User-Facing |
|---|---|---|---|
| `MaxTurnsExceeded` | Logic | No | Yes |
| `ProviderError` (429) | Transient | Yes | Yes |
| `ProviderError` (500) | Transient | Yes | Yes |
| `ProviderError` (401) | Permanent | No | No |
| `ToolError` | Depends | Sometimes | Yes |
| `ToolTimeoutError` | Transient | Yes | Yes |
| `InputGuardrailTripwireTriggered` | Safety | No | Yes |
| `OutputGuardrailTripwireTriggered` | Safety | No | Yes |
| `ModelBehaviorError` | Transient | Yes | No |
| `ConfigurationError` | Permanent | No | No |

---

## Rate Limiting and Retry Policies

### Rate Limiting

Use `RateLimitMiddleware` to prevent excessive calls to LLM providers:

```python
from flux import Runner, RateLimitMiddleware

# Limit to 10 requests per second
rate_limiter = RateLimitMiddleware(max_per_second=10.0)
```

The rate limiter uses a token bucket algorithm with async locking. Requests that exceed the rate are automatically delayed until a token is available.

### Retry with Exponential Backoff

Use `RetryMiddleware` to handle transient failures (rate limits, temporary outages):

```python
from flux import Runner, RetryMiddleware

# Retry up to 3 times with exponential backoff (1s, 2s, 4s)
retrier = RetryMiddleware(max_retries=3, backoff_base=1.0)
```

The retry middleware catches `ProviderError` and `ToolError` exceptions and retries with exponential backoff:

```
Attempt 1: immediate
Attempt 2: wait 1s
Attempt 3: wait 2s
Attempt 4: wait 4s (then fail)
```

### Combined Middleware Stack

For production, combine rate limiting and retrying:

```python
# Middleware is applied in order: rate limit -> retry -> model call
# This means rate limiting happens first, then retries wrap the outer call
```

---

## Session Persistence

### SQLite Sessions

For production deployments, use `SQLiteSession` for persistent conversation history:

```python
from flux import SQLiteSession, Runner

# Create a persistent session per user
session = SQLiteSession(
    db_path="/app/data/flux_sessions.db",
    session_id=user_id,
)

result = await Runner.run(
    agent,
    "Hello, follow-up question!",
    session=session,
)
```

### Session Configuration

SQLite sessions use WAL (Write-Ahead Logging) mode by default for better concurrent read performance:

```sql
PRAGMA journal_mode=WAL
```

!!! tip "Database Location"
    In Docker deployments, mount a persistent volume for the SQLite database path to survive container restarts. See the [Docker Deployment](docker.md#volume-mounts) guide.

### Scaling Sessions

For multi-instance deployments:

- **SQLite with shared filesystem** -- Works with NFS or similar shared storage, but may have contention under heavy write loads.
- **Custom session backend** -- Implement the `Session` protocol with a database like PostgreSQL or Redis for horizontal scaling.

---

## Monitoring with Events and Tracing

### Event Bus

The Flux event bus provides decoupled observability. Subscribe to events for monitoring and alerting:

```python
from flux import get_event_bus, Event

bus = get_event_bus()

def on_agent_start(event: Event):
    logger.info("Agent started: %s", event.data.get("agent"))

def on_llm_end(event: Event):
    logger.info("LLM call completed: %s", event.data.get("agent"))

def on_tool_error(event: Event):
    logger.error("Tool error: %s", event.data)

def on_run_end(event: Event):
    logger.info("Run completed: agent=%s", event.data.get("agent"))

# Subscribe to specific events
bus.on("agent.start", on_agent_start)
bus.on("llm.end", on_llm_end)
bus.on("tool.end", on_tool_error)
bus.on("run.end", on_run_end)
```

### Available Event Types

| Event Type | Description | Data Fields |
|---|---|---|
| `run.start` | Agent run begins | `agent` |
| `run.end` | Agent run completes | `agent` |
| `agent.start` | Agent turn begins | `agent` |
| `agent.end` | Agent turn ends | `agent` |
| `llm.start` | LLM call begins | `agent` |
| `llm.end` | LLM call completes | `agent` |
| `tool.start` | Tool execution begins | `tool`, `args` |
| `tool.end` | Tool execution ends | `tool`, `success` |
| `handoff` | Agent handoff occurs | `source`, `target`, `tool_name` |
| `guardrail.check` | Guardrail check runs | — |
| `guardrail.triggered` | Guardrail blocks content | — |
| `stream.chunk` | Streaming chunk received | — |

### Tracing

Flux provides built-in tracing for detailed performance analysis:

```python
from flux import ConsoleTracer, FileTracer

# Console tracing (development / debugging)
tracer = ConsoleTracer()

# File tracing (production log analysis)
tracer = FileTracer(path="/app/logs/trace.jsonl")
```

Tracing produces structured spans with timing data:

```
▶ run
  ▶ agent:assistant
    ▶ llm.call
    ✓ llm.call (0.842s)
    ▶ tool:search
    ✓ tool:search (0.203s)
    ▶ llm.call
    ✓ llm.call (0.651s)
  ✓ agent:assistant (1.712s)
✓ run (1.715s)
```

---

## Logging Setup

### Configuration

Configure Python logging alongside Flux middleware logging:

```python
import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/app/logs/flux.log"),
    ],
)

# Set Flux-specific log levels
logging.getLogger("flux.middleware").setLevel(logging.DEBUG)
logging.getLogger("flux.runner").setLevel(logging.INFO)
```

### Log Levels in Production

| Component | Recommended Level | Purpose |
|---|---|---|
| Application | `INFO` | General operation logs |
| Flux middleware | `WARNING` | Only log retries, errors |
| Flux runner | `INFO` | Log agent runs and handoffs |
| Provider calls | `WARNING` | Log only errors and retries |
| Guardrails | `INFO` | Log triggered guardrails |

### Structured Logging

For production, use structured logging for machine-parseable output:

```python
import structlog

logger = structlog.get_logger()

def on_tool_end(event):
    logger.info(
        "tool_execution",
        tool=event.data.get("tool"),
        success=event.data.get("success"),
    )
```

---

## Security Considerations

### Guardrails

Use guardrails to enforce safety policies in production:

```python
from flux import Agent, PIIGuardrail, ProfanityGuardrail, LengthGuardrail

agent = Agent(
    name="safe-agent",
    instructions="You are a helpful assistant.",
    guardrails=[
        # Block personally identifiable information
        PIIGuardrail(),
        # Block profanity
        ProfanityGuardrail(word_list=["badword1", "badword2"]),
        # Limit input length
        LengthGuardrail(max_chars=10000),
    ],
)
```

### Custom Guardrails

Implement custom guardrails for domain-specific safety:

```python
from flux import InputGuardrail, OutputGuardrail, GuardrailResult

class NoCodeExecutionGuardrail(InputGuardrail):
    """Blocks attempts to execute arbitrary code."""

    @property
    def name(self) -> str:
        return "no_code_execution"

    async def check(self, user_input: str, context=None) -> GuardrailResult:
        dangerous_patterns = ["exec(", "eval(", "os.system(", "__import__("]
        for pattern in dangerous_patterns:
            if pattern in user_input:
                return GuardrailResult(
                    passed=False,
                    message=f"Dangerous pattern detected: {pattern}",
                )
        return GuardrailResult(passed=True)
```

### Security Checklist

!!! warning "Production Security"
    - [ ] Never hardcode API keys -- use environment variables
    - [ ] Implement input guardrails to filter malicious input
    - [ ] Implement output guardrails to prevent data leakage
    - [ ] Run containers as non-root users
    - [ ] Use HTTPS for all external API calls
    - [ ] Validate and sanitize all user inputs before passing to agents
    - [ ] Enable rate limiting to prevent abuse
    - [ ] Log all guardrail triggers for audit purposes
    - [ ] Restrict tool access (especially `ShellTool`) in production

### Tool Security

The built-in `ShellTool`, `FileReadTool`, and `FileWriteTool` execute system commands. In production:

```python
# DO: Only include safe tools in production agents
agent = Agent(
    name="production-agent",
    tools=[search_tool, lookup_tool],  # Safe tools only
)

# DO NOT: Include shell/file tools in user-facing agents
# ShellTool, FileReadTool, FileWriteTool should be restricted
```

---

## Scaling Considerations

### Horizontal Scaling

Flux Agents is stateless at the framework level (state lives in sessions). For horizontal scaling:

1. **Session storage** -- Use a shared session backend (PostgreSQL, Redis) instead of local SQLite.
2. **Model access** -- Use cloud-based LLM providers (OpenAI, Anthropic) rather than local Ollama.
3. **Load balancing** -- Deploy multiple agent instances behind a load balancer.

### Vertical Scaling

For single-instance deployments:

1. **Increase `max_turns`** for complex multi-step workflows.
2. **Tune `RateLimitMiddleware`** to match your provider's rate limits.
3. **Enable `CacheMiddleware`** to reduce redundant LLM calls.

### Caching

The `CacheMiddleware` caches model responses by message hash with a configurable TTL:

```python
from flux import CacheMiddleware

# Cache responses for 5 minutes
cache = CacheMiddleware(ttl_seconds=300.0)
```

Cache keys are computed from the agent name and message history using SHA-256 hashing.

---

## Production Readiness Checklist

### Before Deploying

- [ ] **Configuration** -- All settings externalized via environment variables
- [ ] **Error handling** -- All `FluxError` subtypes caught and handled gracefully
- [ ] **Rate limiting** -- `RateLimitMiddleware` configured for your provider's limits
- [ ] **Retry policy** -- `RetryMiddleware` configured with appropriate backoff
- [ ] **Session persistence** -- `SQLiteSession` (or custom) for conversation history
- [ ] **Guardrails** -- Input and output guardrails configured for safety
- [ ] **Logging** -- Structured logging configured at appropriate levels
- [ ] **Tracing** -- `FileTracer` enabled for production observability
- [ ] **Event bus** -- Subscribed to critical events for monitoring/alerting
- [ ] **Docker** -- Multi-stage Dockerfile with non-root user
- [ ] **Health checks** -- Container health checks configured
- [ ] **Secrets** -- No hardcoded API keys; all secrets in environment variables

### After Deploying

- [ ] **Monitor logs** for error rates and guardrail triggers
- [ ] **Track token usage** via `Usage` data in `RunResult`
- [ ] **Review traces** for performance bottlenecks
- [ ] **Test failover** -- Verify behavior when the LLM provider is unavailable
- [ ] **Load test** -- Validate performance under expected traffic
