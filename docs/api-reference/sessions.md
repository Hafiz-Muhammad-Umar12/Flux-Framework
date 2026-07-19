# Sessions API Reference

Complete API reference for `Session` protocol, `InMemorySession`, and `SQLiteSession`.

---

## `Session` (Protocol)

::: flux.sessions.base.Session

```python
@runtime_checkable
class Session(Protocol):
    """Protocol for conversation session storage."""

    @property
    def session_id(self) -> str:
        """Unique session identifier."""
        ...

    async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Retrieve stored messages."""
        ...

    async def add_messages(self, messages: list[dict[str, Any]]) -> None:
        """Store messages."""
        ...

    async def clear(self) -> None:
        """Clear all messages."""
        ...
```

The `Session` protocol defines the interface for conversation persistence backends. The `Runner` uses sessions to load conversation history before a run and save new messages after completion.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `session_id` | `str` | A unique identifier for this session. |

### Methods

#### `get_messages`

```python
async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
```

Retrieve stored messages, ordered oldest to newest.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int \| None` | `None` | Maximum number of messages to return. `None` returns all. |

**Returns:** `list[dict[str, Any]]` — each dict has at minimum `"role"` and `"content"` keys.

#### `add_messages`

```python
async def add_messages(self, messages: list[dict[str, Any]]) -> None:
```

Store one or more messages.

| Parameter | Type | Description |
|-----------|------|-------------|
| `messages` | `list[dict[str, Any]]` | Messages to store. Each must have at minimum `"role"` and optionally `"content"`. |

#### `clear`

```python
async def clear(self) -> None:
```

Delete all messages in this session.

### Message Format

Messages stored in sessions use the following dict structure:

```python
{
    "role": "user",           # Required: "user", "assistant", "system", "tool"
    "content": "Hello!",      # Optional: message text
    "metadata": {...},        # Optional: arbitrary metadata dict
}
```

### Implementing a Custom Session

```python
from typing import Any

class RedisSession:
    @property
    def session_id(self) -> str:
        return self._session_id

    async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        # Your implementation
        ...

    async def add_messages(self, messages: list[dict[str, Any]]) -> None:
        # Your implementation
        ...

    async def clear(self) -> None:
        # Your implementation
        ...
```

---

## `InMemorySession`

::: flux.sessions.in_memory.InMemorySession

```python
class InMemorySession:
    """In-memory conversation session (lost on process exit)."""

    def __init__(self, max_messages: int = 1000) -> None:
        self._session_id = uuid.uuid4().hex[:16]
        self._messages: deque[dict[str, Any]] = deque(maxlen=max_messages)
```

A session backed by an in-memory deque. Messages are lost when the process exits. Useful for testing and short-lived interactions.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_messages` | `int` | `1000` | Maximum number of messages to retain. Oldest messages are discarded when this limit is exceeded. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `session_id` | `str` | A random 16-character hex string generated at initialization. |

### Methods

#### `get_messages`

```python
async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
```

Return stored messages. If `limit` is set, returns only the most recent `limit` messages.

#### `add_messages`

```python
async def add_messages(self, messages: list[dict[str, Any]]) -> None:
```

Append messages to the internal deque. Evicts oldest messages when `max_messages` is exceeded.

#### `clear`

```python
async def clear(self) -> None:
```

Remove all messages from the session.

### Usage

```python
from flux.sessions.in_memory import InMemorySession

session = InMemorySession(max_messages=500)

await session.add_messages([
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
])

messages = await session.get_messages()
# [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi there!"}]

recent = await session.get_messages(limit=1)
# [{"role": "assistant", "content": "Hi there!"}]

await session.clear()
```

### Using with Runner

```python
from flux.agent import Agent
from flux.runner import Runner
from flux.sessions.in_memory import InMemorySession

session = InMemorySession()
agent = Agent(name="Assistant", instructions="You are helpful.")

# First turn
result = await Runner.run(agent, "Hello!", session=session)
print(result.final_output)

# Second turn — history is loaded from the session
result = await Runner.run(agent, "What did I just say?", session=session)
print(result.final_output)
```

---

## `SQLiteSession`

::: flux.sessions.sqlite.SQLiteSession

```python
class SQLiteSession:
    """Persistent session storage using SQLite."""

    def __init__(
        self,
        db_path: str = "flux_sessions.db",
        session_id: str | None = None,
    ) -> None:
        self._session_id = session_id or uuid.uuid4().hex[:16]
        self._db_path = db_path
        self._init_db()
```

A session backed by a SQLite database. Messages persist across process restarts. Uses WAL journal mode for concurrent read performance.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_path` | `str` | `"flux_sessions.db"` | Path to the SQLite database file. Created automatically if it does not exist. |
| `session_id` | `str \| None` | `None` | Session identifier. If `None`, a random 16-character hex string is generated. Use a fixed ID to resume a previous session. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `session_id` | `str` | The session identifier. |

### Methods

#### `get_messages`

```python
async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
```

Retrieve messages from the database, ordered by insertion time. If `limit` is set, returns only the most recent `limit` messages.

#### `add_messages`

```python
async def add_messages(self, messages: list[dict[str, Any]]) -> None:
```

Insert messages into the database. Each message stores `role`, `content`, and optional `metadata` (serialized as JSON).

#### `clear`

```python
async def clear(self) -> None:
```

Delete all messages for this session from the database.

### Database Schema

The SQLite database uses the following schema:

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    metadata TEXT,          -- JSON-encoded metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id);
```

### Usage

```python
from flux.sessions.sqlite import SQLiteSession

# New session
session = SQLiteSession(db_path="my_app.db")

# Resume a previous session
session = SQLiteSession(db_path="my_app.db", session_id="abc123def456")

await session.add_messages([
    {"role": "user", "content": "Hello!"},
])

messages = await session.get_messages()
```

### Notes

- Each `SQLiteSession` instance opens its own connection per operation. For high-concurrency workloads, consider connection pooling.
- The `metadata` field supports arbitrary JSON-serializable dicts.
- Sessions with different `session_id` values in the same database are fully isolated.
