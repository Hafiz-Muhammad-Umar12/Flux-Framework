# Docker Deployment

Deploying Flux Agents with Docker.

Flux Agents can be containerized for consistent deployments across environments. This guide covers Dockerfile creation, Docker Compose configurations with Ollama, multi-stage builds, environment variable management, volume mounts for sessions and memory, and health checks.

---

## Quick Start

The fastest way to get a Flux Agents application running in Docker:

```bash
# Build the image
docker build -t flux-agent .

# Run with Ollama
docker compose up -d
```

---

## Dockerfile

### Basic Dockerfile

A minimal Dockerfile for a Flux Agents application:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[ollama]"

# Copy application code
COPY . .
RUN pip install --no-cache-dir -e .

# Run the agent
CMD ["python", "my_agent.py"]
```

### Multi-Stage Build

Use a multi-stage build to produce a smaller final image by separating the build stage from the runtime stage:

```dockerfile
# ── Build stage ──────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install ".[ollama]"

COPY . .
RUN pip install --no-cache-dir --prefix=/install -e .

# ── Runtime stage ────────────────────────────────
FROM python:3.12-slim AS runtime

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app
COPY . .

# Create non-root user for security
RUN useradd --create-home appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import flux; print('ok')" || exit 1

CMD ["python", "my_agent.py"]
```

### Production Dockerfile with All Providers

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install ".[full]"

COPY . .
RUN pip install --no-cache-dir --prefix=/install -e .

FROM python:3.12-slim AS runtime

COPY --from=builder /install /usr/local

WORKDIR /app
COPY . .

RUN useradd --create-home appuser && \
    mkdir -p /app/data && chown -R appuser:appuser /app/data
USER appuser

ENV PYTHONUNBUFFERED=1
ENV FLUX_LOG_LEVEL=INFO

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import flux; print('ok')" || exit 1

EXPOSE 8000

CMD ["python", "my_agent.py"]
```

---

## Docker Compose with Ollama

The recommended way to run Flux Agents locally is with Docker Compose, pairing the agent container with a local Ollama instance.

### docker-compose.yml

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  agent:
    build: .
    depends_on:
      ollama:
        condition: service_healthy
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - FLUX_DEFAULT_MODEL=llama3.2
      - FLUX_LOG_LEVEL=INFO
      - FLUX_EVENT_BUS_ENABLED=true
      - FLUX_TRACING_ENABLED=false
    volumes:
      - ./data:/app/data
      - agent_sessions:/app/sessions
    restart: unless-stopped

volumes:
  ollama_data:
  agent_sessions:
```

### Starting Services

```bash
# Start everything (Ollama + agent)
docker compose up -d

# View logs
docker compose logs -f agent

# Pull a model into Ollama
docker compose exec ollama ollama pull llama3.2

# Stop everything
docker compose down

# Stop and remove volumes
docker compose down -v
```

---

## Environment Variable Configuration

Flux Agents reads configuration from environment variables, which map directly to `FluxConfig` fields:

| Environment Variable | Default | Description |
|---|---|---|
| `FLUX_DEFAULT_MODEL` | `llama3.2` | Default LLM model name |
| `FLUX_DEFAULT_MAX_TURNS` | `10` | Maximum conversation turns per run |
| `FLUX_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `FLUX_EVENT_BUS_ENABLED` | `true` | Enable/disable the event bus |
| `FLUX_TRACING_ENABLED` | `false` | Enable/disable tracing |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | — | OpenAI API key (when using OpenAI models) |
| `ANTHROPIC_API_KEY` | — | Anthropic API key (when using Anthropic models) |
| `FLUX_SESSION_DB_PATH` | `flux_sessions.db` | SQLite session database path |

### Using a .env File

Create a `.env` file in your project root for local development:

```env
# LLM Configuration
OLLAMA_BASE_URL=http://ollama:11434
FLUX_DEFAULT_MODEL=llama3.2

# OpenAI (optional)
# OPENAI_API_KEY=sk-...

# Anthropic (optional)
# ANTHROPIC_API_KEY=sk-ant-...

# Framework settings
FLUX_LOG_LEVEL=INFO
FLUX_EVENT_BUS_ENABLED=true
FLUX_TRACING_ENABLED=false
```

Reference it in your `docker-compose.yml`:

```yaml
services:
  agent:
    build: .
    env_file:
      - .env
```

---

## Volume Mounts

### Sessions Persistence

Mount a volume to persist conversation sessions across container restarts:

```yaml
services:
  agent:
    volumes:
      - agent_sessions:/app/sessions
      - ./data:/app/data

volumes:
  agent_sessions:
```

In your application code, point `SQLiteSession` to the mounted path:

```python
from flux import SQLiteSession

session = SQLiteSession(
    db_path="/app/sessions/flux_sessions.db",
    session_id="user-123",
)
```

### Memory Persistence

For vector memory persistence, mount a volume for the memory store:

```yaml
services:
  agent:
    volumes:
      - agent_memory:/app/memory

volumes:
  agent_memory:
```

### Ollama Model Storage

The Ollama container stores downloaded models in `/root/.ollama`. Always use a named volume to avoid re-downloading models:

```yaml
services:
  ollama:
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

---

## Health Checks

### Application Health Check

Add a health check to verify the Flux framework is importable and functional:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import flux; print('ok')" || exit 1
```

### Advanced Health Check

For a more thorough health check that verifies model connectivity:

```dockerfile
HEALTHCHECK --interval=60s --timeout=15s --retries=3 \
    CMD python -c "
import asyncio, aiohttp, os

async def check():
    url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    async with aiohttp.ClientSession() as s:
        async with s.get(f'{url}/api/tags') as r:
            assert r.status == 200

asyncio.run(check())
" || exit 1
```

### Docker Compose Health Check

```yaml
services:
  agent:
    healthcheck:
      test: ["CMD", "python", "-c", "import flux; print('ok')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
```

---

## Example Application Dockerfile

Here is a complete example for a custom Flux Agents application:

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /build

# Install project dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install ".[ollama]"

# Copy source and install
COPY . .
RUN pip install --no-cache-dir --prefix=/install -e .

FROM python:3.12-slim AS runtime

COPY --from=builder /install /usr/local

WORKDIR /app

# Copy only what is needed for the application
COPY my_agent.py .
COPY config/ ./config/

# Create non-root user
RUN useradd --create-home appuser && \
    mkdir -p /app/data /app/sessions && \
    chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV FLUX_LOG_LEVEL=INFO

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import flux; print('ok')" || exit 1

CMD ["python", "my_agent.py"]
```

---

## Best Practices

!!! tip "Layer Caching"
    Always copy `pyproject.toml` and install dependencies before copying application code. This ensures the dependency layer is cached and only rebuilt when dependencies change.

!!! tip "Non-Root User"
    Always create and switch to a non-root user in production Dockerfiles. This prevents the container from running as root, which is a security risk.

!!! tip "Multi-Stage Builds"
    Use multi-stage builds to keep final images small. The builder stage can include build tools, compilers, and development dependencies that are not needed at runtime.

!!! warning "GPU Support"
    If using Ollama with GPU acceleration, ensure the NVIDIA Container Toolkit is installed on the host and use the `deploy.resources.reservations.devices` configuration in Docker Compose.

!!! info "Image Size Comparison"
    | Build Type | Approximate Size |
    |---|---|
    | `python:3.12` (full) | ~1.0 GB |
    | `python:3.12-slim` (single stage) | ~450 MB |
    | Multi-stage with slim | ~200 MB |
