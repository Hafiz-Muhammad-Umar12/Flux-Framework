# Development Setup

Setting up a development environment for Flux Agents.

---

## Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Git**
- **Ollama** (optional, for local LLM testing)

### Installing Python

=== "macOS / Linux"

    ```bash
    # Using pyenv
    pyenv install 3.12
    pyenv local 3.12

    # Using Homebrew (macOS)
    brew install python@3.12
    ```

=== "Windows"

    ```bash
    # Using pyenv-win
    pyenv install 3.12
    pyenv local 3.12

    # Or download from python.org
    ```

### Installing Ollama

Ollama is required for running local LLM models during development.

=== "macOS"

    ```bash
    brew install ollama
    ollama serve
    ```

=== "Linux"

    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ollama serve
    ```

=== "Windows"

    ```bash
    # Download from https://ollama.com/download
    # Or using winget
    winget install Ollama.Ollama
    ```

After installing Ollama, pull a model for testing:

```bash
ollama pull llama3.2
```

---

## Clone and Install

```bash
# Clone the repository
git clone https://github.com/OWNER/flux-agents.git
cd flux-agents

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate   # Windows

# Install in development mode with all extras
make dev
# Equivalent to: pip install -e ".[dev,ollama]"
```

### Installation Variants

```bash
# Minimal (core only, no providers)
pip install -e .

# With Ollama support
pip install -e ".[ollama]"

# With OpenAI support
pip install -e ".[openai]"

# With Anthropic support
pip install -e ".[anthropic]"

# With all providers
pip install -e ".[full]"

# With memory (numpy)
pip install -e ".[memory]"

# Full development install
pip install -e ".[dev,full,memory]"
```

---

## Running Tests

### Basic Test Run

```bash
# Run all tests
make test
# Equivalent to: pytest tests/ -v
```

### Test with Coverage

```bash
# Run tests with coverage report
make test-cov
# Equivalent to: pytest tests/ -v --cov=flux --cov-report=term-missing
```

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/test_agent.py -v

# Run tests matching a pattern
pytest tests/ -k "test_middleware" -v

# Run with debug output
pytest tests/ -v -s --tb=long
```

### Test Configuration

The test configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Tests use `asyncio_mode = "auto"`, so all `async def test_*` functions are automatically treated as async tests without needing the `@pytest.mark.asyncio` decorator.

---

## Linting

### Ruff

```bash
# Check for lint issues
make lint
# Equivalent to: ruff check flux/ tests/

# Auto-fix issues and format
make format
# Equivalent to:
#   ruff format flux/ tests/
#   ruff check --fix flux/ tests/
```

### Ruff Configuration

From `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

| Rule Set | Description |
|---|---|
| `E` | Pycodestyle errors |
| `F` | Pyflakes |
| `I` | isort (import sorting) |
| `UP` | pyupgrade (modernize syntax) |
| `B` | flake8-bugbear (common bugs) |
| `SIM` | flake8-simplify (simplification suggestions) |

---

## Type Checking

### Mypy

```bash
# Run type checker
make typecheck
# Equivalent to: mypy flux/
```

### Mypy Configuration

From `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

!!! tip "Strict Mode"
    Flux uses mypy strict mode. This means all functions must have complete type annotations, and mypy will flag any untyped code. This is by design -- the framework prioritizes type safety.

---

## Makefile Targets

All development tasks are available as Makefile targets:

| Target | Command | Description |
|---|---|---|
| `make install` | `pip install -e .` | Install the package in editable mode |
| `make dev` | `pip install -e ".[dev,ollama]"` | Install with dev and Ollama extras |
| `make test` | `pytest tests/ -v` | Run all tests |
| `make test-cov` | `pytest tests/ -v --cov=flux --cov-report=term-missing` | Run tests with coverage |
| `make lint` | `ruff check flux/ tests/` | Run linter |
| `make format` | `ruff format flux/ tests/ && ruff check --fix flux/ tests/` | Format and auto-fix |
| `make typecheck` | `mypy flux/` | Run type checker |
| `make clean` | Remove caches and build artifacts | Clean the project |

### Using Make on Windows

If `make` is not available on Windows, you can run the commands directly:

```powershell
# Install
pip install -e ".[dev,ollama]"

# Test
pytest tests/ -v

# Lint
ruff check flux/ tests/

# Format
ruff format flux/ tests/

# Type check
mypy flux/
```

Or install `make` via Chocolatey: `choco install make`

---

## Project Structure

```
flux-agents/
├── flux/                        # Main package
│   ├── __init__.py              # Public API exports
│   ├── agent.py                 # Agent definition (frozen dataclass)
│   ├── runner.py                # Execution engine
│   ├── config.py                # Global configuration
│   ├── context.py               # RunContext, ToolContext, Usage
│   ├── exceptions.py            # Exception hierarchy
│   ├── cli.py                   # CLI entry point
│   │
│   ├── models/                  # LLM provider abstraction
│   │   ├── base.py              # Model protocol, Message, ModelRequest/Response
│   │   ├── registry.py          # Model registry (name -> provider)
│   │   ├── openai_provider.py   # OpenAI implementation
│   │   └── anthropic.py         # Anthropic implementation
│   │
│   ├── tools/                   # Tool system
│   │   ├── base.py              # Tool protocol, ToolResult
│   │   ├── decorator.py         # @tool decorator, FunctionTool
│   │   ├── registry.py          # ToolRegistry
│   │   ├── schema.py            # JSON Schema generation
│   │   └── builtins.py          # ShellTool, FileReadTool, FileWriteTool
│   │
│   ├── middleware/               # Middleware pipeline
│   │   ├── base.py              # Middleware protocol, RequestContext, Response
│   │   ├── retry.py             # RetryMiddleware (exponential backoff)
│   │   ├── rate_limit.py        # RateLimitMiddleware (token bucket)
│   │   ├── cache.py             # CacheMiddleware (TTL-based)
│   │   └── logging.py           # LoggingMiddleware
│   │
│   ├── guardrails/              # Safety guardrails
│   │   ├── base.py              # GuardrailResult, InputGuardrail, OutputGuardrail
│   │   └── builtins.py          # PIIGuardrail, ProfanityGuardrail, LengthGuardrail
│   │
│   ├── handoffs/                # Agent-to-agent routing
│   │   ├── handoff.py           # Handoff, HandoffData
│   │   └── router.py            # Handoff lookup utilities
│   │
│   ├── sessions/                # Conversation persistence
│   │   ├── base.py              # Session protocol
│   │   ├── in_memory.py         # InMemorySession
│   │   └── sqlite.py            # SQLiteSession (persistent)
│   │
│   ├── memory/                  # Long-term memory
│   │   ├── base.py              # Memory protocol, MemoryEntry
│   │   ├── conversation.py      # ConversationMemory (wraps Session)
│   │   └── vector.py            # VectorMemory (hash-based embeddings)
│   │
│   ├── events/                  # Event bus
│   │   └── bus.py               # EventBus, Event, event type constants
│   │
│   ├── streaming/               # Streaming support
│   │   └── events.py            # StreamEvent types (TextDelta, ToolCall, etc.)
│   │
│   ├── tracing/                 # Distributed tracing
│   │   ├── base.py              # Span, Tracer protocols, NoopSpan
│   │   ├── console.py           # ConsoleTracer (stderr output)
│   │   └── file.py              # FileTracer (JSONL output)
│   │
│   └── utils/                   # Utilities
│       ├── schema.py            # JSON Schema helpers
│       ├── tokens.py            # Token counting
│       └── pretty.py            # Pretty printing
│
├── tests/                       # Test suite
│   ├── conftest.py              # Shared fixtures
│   ├── test_agent.py            # Agent tests
│   ├── test_models.py           # Model protocol tests
│   ├── test_middleware.py        # Middleware tests
│   ├── test_guardrails.py       # Guardrail tests
│   ├── test_sessions.py         # Session tests
│   ├── test_events.py           # Event bus tests
│   ├── test_tracing.py          # Tracing tests
│   └── test_handoffs.py         # Handoff tests
│
├── docs/                        # Documentation (MkDocs)
│   ├── deployment/              # Deployment guides
│   └── contributing/            # Contributor guides
│
├── pyproject.toml               # Project config, tools config
├── Makefile                     # Development commands
├── README.md                    # Project overview
└── LICENSE                      # MIT License
```

### Key Design Decisions in the Structure

- **Protocols, not ABCs** -- Interfaces like `Model`, `Tool`, `Session`, and `Memory` use `typing.Protocol` for structural subtyping rather than inheritance.
- **Frozen dataclasses** -- Core types like `Agent` use `frozen=True` for immutability. Use `.clone()` to create modified copies.
- **Async-first** -- All I/O operations (`Runner.run`, `Tool.execute`, `Session.get_messages`) are async.
- **Zero core dependencies** -- The `flux` package itself has no required dependencies. Provider libraries (OpenAI, Anthropic, aiohttp) are optional extras.

---

## IDE Setup

### VS Code

Recommended extensions:

- **Python** (`ms-python.python`)
- **Pylance** (`ms-python.vscode-pylance`)
- **Ruff** (`charliermarsh.ruff`)

`.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.typeCheckingMode": "strict",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    }
}
```

---

## Common Development Tasks

### Adding a New Tool

1. Create the tool class implementing the `Tool` protocol
2. Add tests in `tests/test_tools.py`
3. Export from `flux/__init__.py` if public

### Adding a New Middleware

1. Create the middleware class implementing the `Middleware` protocol
2. Add tests in `tests/test_middleware.py`
3. Export from `flux/__init__.py` if public

### Adding a New Guardrail

1. Subclass `InputGuardrail` or `OutputGuardrail`
2. Implement the `check` method
3. Add tests in `tests/test_guardrails.py`

### Adding a New Model Provider

1. Implement the `Model` protocol with `complete` and `stream` methods
2. Register in the `ModelRegistry`
3. Add tests in `tests/test_models.py`
