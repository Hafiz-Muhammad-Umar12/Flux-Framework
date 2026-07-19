# Contributing to Flux

How to contribute to the Flux Agents framework.

Thank you for your interest in contributing to Flux Agents! This guide covers everything you need to get started, from setting up your development environment to submitting your first pull request.

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Install** development dependencies
4. **Create** a feature branch
5. **Make** your changes
6. **Test** your changes
7. **Submit** a pull request

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/flux-agents.git
cd flux-agents

# Install in development mode
pip install -e ".[dev]"

# Create a branch
git checkout -b feature/my-feature
```

---

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Please be respectful and constructive in all interactions.

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy toward other contributors

---

## How to Report Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Reproduce the bug** with the latest `main` branch
3. **Minimal reproduction** -- create the smallest possible code example that demonstrates the bug

### Filing an Issue

Use the GitHub issue tracker with the **Bug Report** template. Include:

- **Environment**: Python version, OS, Flux version
- **Steps to reproduce**: Minimal code example
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Full traceback**: If applicable

```python
# Minimal reproduction example
import asyncio
from flux import Agent, Runner

agent = Agent(
    name="test",
    instructions="You are a test agent.",
    model="llama3.2",
)

async def main():
    result = await Runner.run(agent, "Hello")
    print(result.final_output)

asyncio.run(main())
```

---

## How to Suggest Features

Feature suggestions are welcome. Before creating a feature request:

1. **Check existing issues and discussions** for similar ideas
2. **Consider the scope** -- does this fit the Flux design principles?
3. **Provide a concrete proposal** with use cases

When proposing a feature, include:

- **Problem statement** -- What problem does this solve?
- **Proposed solution** -- How should it work?
- **Alternatives considered** -- What other approaches did you evaluate?
- **Use cases** -- Concrete examples of how it would be used

---

## How to Submit Pull Requests

### Workflow

1. **Create a feature branch** from `main`:

    ```bash
    git checkout -b feature/my-feature main
    ```

2. **Make your changes** following the code style guidelines below

3. **Write or update tests** for your changes

4. **Run the full test suite**:

    ```bash
    make test
    make lint
    make typecheck
    ```

5. **Commit** with a descriptive message following the conventions below

6. **Push** your branch and open a pull request

### Pull Request Guidelines

- **One change per PR** -- keep pull requests focused
- **Describe what and why** -- explain the motivation, not just the code
- **Link related issues** -- reference any relevant issue numbers
- **Include tests** -- all new functionality needs test coverage
- **Update documentation** -- if adding public API, update docstrings and docs
- **Pass CI** -- all checks must pass before merging

### PR Template

```markdown
## Description

Brief description of the changes.

## Motivation

Why these changes are needed.

## Changes

- Change 1
- Change 2

## Testing

How these changes were tested.

## Checklist

- [ ] Tests pass (`make test`)
- [ ] Lint passes (`make lint`)
- [ ] Type check passes (`make typecheck`)
- [ ] Documentation updated (if applicable)
```

---

## Development Setup

See the [Development Setup](development.md) guide for detailed instructions on setting up your local development environment.

### Quick Setup

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/flux-agents.git
cd flux-agents
pip install -e ".[dev,ollama]"

# Run tests
make test

# Run linter
make lint

# Run type checker
make typecheck
```

---

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run a specific test file
pytest tests/test_agent.py -v

# Run tests matching a pattern
pytest tests/ -k "test_tool" -v
```

### Writing Tests

- Tests live in the `tests/` directory
- Test files are named `test_<module>.py`
- Use `pytest-asyncio` for async tests (configured with `asyncio_mode = "auto"`)
- Use fixtures from `conftest.py` for common test data
- Aim for clear, descriptive test names

```python
import pytest
from flux import Agent, Runner

@pytest.mark.asyncio
async def test_agent_returns_response():
    agent = Agent(
        name="test",
        instructions="Reply with 'hello'.",
    )
    result = await Runner.run(agent, "Hi")
    assert result.final_output is not None
    assert isinstance(result.final_output, str)
```

### Test Categories

| File | Tests |
|---|---|
| `test_agent.py` | Agent creation, cloning, settings |
| `test_models.py` | Model protocol, settings resolution |
| `test_middleware.py` | All middleware (retry, rate limit, cache, logging) |
| `test_guardrails.py` | Input/output guardrails, built-in guardrails |
| `test_sessions.py` | Session persistence (in-memory, SQLite) |
| `test_events.py` | Event bus subscription and emission |
| `test_tracing.py` | Tracer and span lifecycle |
| `test_handoffs.py` | Agent handoff routing |

---

## Code Style

Flux Agents enforces consistent code style using **ruff** for linting/formatting and **mypy** for type checking.

### Ruff

```bash
# Check for lint issues
make lint

# Auto-fix lint issues and format
make format
```

Ruff configuration (from `pyproject.toml`):

- Line length: 100 characters
- Target: Python 3.11
- Enabled rules: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `UP` (pyupgrade), `B` (bugbear), `SIM` (simplify)

### Mypy

```bash
# Run type checker
make typecheck
```

Mypy configuration (from `pyproject.toml`):

- Python version: 3.11
- Strict mode enabled
- Warnings for unused configs and returning `Any`

### Style Guidelines

- **Type hints** -- All public functions must have complete type annotations
- **Docstrings** -- Use Google-style docstrings for public APIs
- **Imports** -- Use `from __future__ import annotations` in all modules
- **Protocols over ABCs** -- Use `typing.Protocol` for interfaces (not `abc.ABC`)
- **Dataclasses** -- Use `@dataclass` for data containers, `frozen=True` for immutable types
- **Async by default** -- All I/O operations must be `async`
- **No core dependencies** -- The `flux` package itself has zero required dependencies

---

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) for consistent, meaningful commit history.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting, no logic change) |
| `refactor` | Code refactoring (no feature or fix) |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks (CI, dependencies, etc.) |
| `perf` | Performance improvements |

### Scopes

| Scope | Description |
|---|---|
| `core` | Agent, Runner, Config |
| `models` | Model protocol and providers |
| `tools` | Tool system |
| `middleware` | Middleware pipeline |
| `guardrails` | Guardrail system |
| `sessions` | Session persistence |
| `events` | Event bus |
| `tracing` | Tracing system |
| `handoffs` | Agent handoffs |
| `memory` | Memory system |
| `docs` | Documentation |
| `ci` | CI/CD workflows |
| `deps` | Dependencies |

### Examples

```
feat(tools): add SQL query tool
fix(runner): handle empty model response gracefully
docs(deployment): add Docker Compose guide
refactor(middleware): simplify retry backoff calculation
test(guardrails): add PII detection edge cases
chore(ci): update Python matrix to include 3.13
```

---

## Questions?

If you have questions about contributing:

1. Check the [Architecture Guide](architecture.md) for framework design details
2. Search existing issues and discussions
3. Open a new discussion on GitHub
