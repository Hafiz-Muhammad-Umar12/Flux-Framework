# Installation

How to install Flux Agents and its optional dependencies.

## Requirements

Flux Agents requires **Python 3.11 or later**. You can check your Python version with:

```bash
python --version
```

!!! tip "Recommended Python versions"
    Flux Agents is tested on Python 3.11, 3.12, and 3.13. For the best experience, use one of these versions.

## Core Installation

Flux Agents ships with **zero required dependencies**. Install the core package with:

```bash
pip install flux-agents
```

This gives you the entire framework -- Agent, Runner, tools, handoffs, guardrails, sessions, streaming, middleware, events, and tracing -- without pulling in any third-party libraries. Model providers are added via optional extras.

## Provider-Specific Installs

Flux Agents uses a provider-agnostic design. You only install the dependencies for the providers you need:

| Command | Adds | Use Case |
|---|---|---|
| `pip install flux-agents[ollama]` | `aiohttp>=3.9.0` | Local models via Ollama |
| `pip install flux-agents[openai]` | `openai>=2.0.0` | OpenAI, OpenRouter, DeepSeek, Groq |
| `pip install flux-agents[anthropic]` | `anthropic>=0.40.0` | Claude models via Anthropic |
| `pip install flux-agents[full]` | All three above | All providers |
| `pip install flux-agents[memory]` | `numpy>=1.26.0` | Enhanced memory features |

!!! note "Ollama requires aiohttp"
    The Ollama provider uses `aiohttp` for async HTTP requests. Without it, you will get a `ProviderError` at runtime.

For example, if you plan to use Ollama locally and OpenAI:

```bash
pip install "flux-agents[ollama,openai]"
```

If you want everything:

```bash
pip install flux-agents[full]
```

## Development Install

If you want to contribute to Flux Agents or run the test suite:

```bash
git clone https://github.com/flux-agents/flux-agents.git
cd flux-agents
pip install -e ".[dev]"
```

This installs the package in editable mode along with development dependencies:

- `pytest` and `pytest-asyncio` for testing
- `ruff` for linting and formatting
- `mypy` for type checking
- `coverage` for test coverage

Run the full test suite with:

```bash
pytest
```

Lint and type-check with:

```bash
ruff check .
mypy flux/
```

## Verify Installation

After installing, verify everything works with a quick test:

```bash
python -c "import flux; print(f'Flux Agents v{flux.__version__} installed successfully')"
```

Expected output:

```
Flux Agents v0.1.0 installed successfully
```

You can also verify the CLI entry point:

```bash
flux --version
```

Expected output:

```
Flux Agents 0.2.0
```

!!! warning "Version mismatch"
    The library version reported by `flux.__version__` and the CLI may differ slightly during active development. This is expected and will be resolved in the next release.

## Troubleshooting

### Python Version Error

If you see an error like `requires-python >=3.11`:

```
ERROR: Package 'flux-agents' requires a different Python: 3.x.x not in '>=3.11'
```

You are running a Python version older than 3.11. Install a newer version from [python.org](https://www.python.org/downloads/) or use a version manager like `pyenv`:

```bash
pyenv install 3.12
pyenv local 3.12
```

### aiohttp Build Failures on Windows

On Windows, `aiohttp` may fail to install due to missing build tools. Try one of these solutions:

1. **Use a pre-built wheel** (recommended):

    ```bash
    pip install flux-agents[ollama] --only-binary=aiohttp
    ```

2. **Install Visual C++ Build Tools**:

    Download and install the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

3. **Use conda**:

    ```bash
    conda install aiohttp
    pip install flux-agents[ollama] --no-deps
    ```

### Import Errors for Provider Packages

If you see a `ProviderError` mentioning a missing package:

```
ProviderError: Provider 'openai' error: openai package is required. Install with: pip install flux-agents[openai]
```

Install the relevant extra:

```bash
pip install "flux-agents[openai]"
```

### Permission Errors on Install

If you get a permission error during installation:

```bash
pip install flux-agents --user
```

Or use a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
pip install flux-agents
```

### pytest-asyncio Compatibility

If you see warnings or errors about `asyncio_mode`:

```bash
pip install "pytest-asyncio>=0.24.0"
```

Flux Agents requires pytest-asyncio 0.24 or later. The test suite is configured with `asyncio_mode = "auto"` in `pyproject.toml`.

!!! tip "Use a virtual environment"
    Always use a virtual environment when installing Flux Agents to avoid conflicts with other packages:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install "flux-agents[ollama]"
    ```

---

## Next Steps

Now that Flux Agents is installed, head to the [Quickstart](quickstart.md) guide to build your first agent in 5 minutes.
