# Memory API Reference

Complete API reference for `Memory` protocol, `MemoryEntry`, `ConversationMemory`, and `VectorMemory`.

---

## `MemoryEntry`

::: flux.memory.base.MemoryEntry

```python
@dataclass
class MemoryEntry:
    """A memory entry."""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
```

A single memory record returned by search queries.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | *required* | The text content of the memory. |
| `metadata` | `dict[str, Any]` | `{}` | Arbitrary metadata (e.g., `{"role": "user"}`, `{"source": "doc.pdf"}`). |
| `score` | `float` | `0.0` | Relevance score assigned by the search method (higher = more relevant). |

### Usage

```python
from flux.memory.base import MemoryEntry

entry = MemoryEntry(
    content="The user prefers dark mode.",
    metadata={"source": "conversation"},
    score=0.95,
)
```

---

## `Memory` (Protocol)

::: flux.memory.base.Memory

```python
@runtime_checkable
class Memory(Protocol):
    """Protocol for long-term memory storage."""

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Search memory for relevant entries."""
        ...

    async def store(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Store a memory entry."""
        ...

    async def clear(self) -> None:
        """Clear all memories."""
        ...
```

The `Memory` protocol defines the interface for long-term memory backends. Memory stores information across conversations and can be searched by relevance.

### Methods

#### `search`

```python
async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
```

Search memory for entries relevant to the query.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | *required* | The search query. |
| `limit` | `int` | `5` | Maximum number of results to return. |

**Returns:** `list[MemoryEntry]` — entries ordered by relevance (most relevant first).

#### `store`

```python
async def store(self, content: str, metadata: dict[str, Any] | None = None) -> None:
```

Store a new memory entry.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | *required* | The text content to remember. |
| `metadata` | `dict[str, Any] \| None` | `None` | Optional metadata to attach. |

#### `clear`

```python
async def clear(self) -> None:
```

Remove all stored memories.

### Implementing a Custom Memory

```python
from typing import Any
from flux.memory.base import MemoryEntry

class PostgresMemory:
    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        # Your implementation (e.g., pgvector semantic search)
        ...

    async def store(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        # Your implementation
        ...

    async def clear(self) -> None:
        # Your implementation
        ...
```

---

## `ConversationMemory`

::: flux.memory.conversation.ConversationMemory

```python
class ConversationMemory:
    """Memory backed by conversation history (wraps a Session)."""

    def __init__(self, session: Any) -> None:
        self._session = session
```

A `Memory` implementation that wraps a `Session`. Search performs naive substring matching over stored conversation messages.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session` | `Any` | *required* | A `Session` instance to use as the backing store. |

### Methods

#### `search`

```python
async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
```

Performs case-insensitive substring matching over all stored messages. Returns up to `limit` matching entries.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | *required* | The search query. |
| `limit` | `int` | `5` | Maximum results. |

**Returns:** `list[MemoryEntry]` — each entry's `metadata` includes `{"role": "<message_role>"}`.

#### `store`

```python
async def store(self, content: str, metadata: dict[str, Any] | None = None) -> None:
```

Store a memory as a user message in the backing session.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | *required* | The text to store. |
| `metadata` | `dict[str, Any] \| None` | `None` | Optional metadata attached to the message. |

#### `clear`

```python
async def clear(self) -> None:
```

Delegates to `session.clear()`. Removes all messages from the backing session.

### Usage

```python
from flux.sessions.in_memory import InMemorySession
from flux.memory.conversation import ConversationMemory

session = InMemorySession()
memory = ConversationMemory(session)

await memory.store("User prefers TypeScript over JavaScript.")
await memory.store("User's project uses React 18.")

results = await memory.search("TypeScript")
for entry in results:
    print(entry.content)  # "User prefers TypeScript over JavaScript."
    print(entry.metadata)  # {"role": "user"}
```

!!! note
    `ConversationMemory` performs substring matching, not semantic search. For semantic search, use `VectorMemory` or implement a custom memory with embeddings.

---

## `VectorMemory`

::: flux.memory.vector.VectorMemory

```python
class VectorMemory:
    """Simple in-memory vector store using hash-based embeddings.
    For production use, replace with real embeddings (e.g., sentence-transformers).
    """

    def __init__(self) -> None:
        self._entries: list[tuple[list[float], MemoryEntry]] = []
```

A `Memory` implementation that uses simple hash-based vector embeddings for similarity search. Each stored text is converted to a 32-dimensional vector using character 3-gram (shingling) hashing and compared via cosine similarity.

### Parameters

None. `VectorMemory` is initialized with an empty store.

### Methods

#### `search`

```python
async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
```

Search by cosine similarity of hash-based embeddings. Returns the most similar entries.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | *required* | The search query. |
| `limit` | `int` | `5` | Maximum number of results. |

**Returns:** `list[MemoryEntry]` — entries ordered by similarity (most similar first).

#### `store`

```python
async def store(self, content: str, metadata: dict[str, Any] | None = None) -> None:
```

Store a memory entry and compute its vector embedding.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | *required* | The text to store. |
| `metadata` | `dict[str, Any] \| None` | `None` | Optional metadata. |

#### `clear`

```python
async def clear(self) -> None:
```

Remove all stored entries and their embeddings.

### Usage

```python
from flux.memory.vector import VectorMemory

memory = VectorMemory()

await memory.store("Python is a programming language.", metadata={"topic": "python"})
await memory.store("JavaScript runs in the browser.", metadata={"topic": "javascript"})
await memory.store("Rust is known for memory safety.", metadata={"topic": "rust"})

results = await memory.search("programming language", limit=2)
for entry in results:
    print(f"{entry.content} (score: {entry.score:.2f})")
```

### How Hash-Based Embeddings Work

`VectorMemory` uses a lightweight embedding technique:

1. **Shingling**: The input text is split into overlapping 3-character n-grams.
2. **Hashing**: Each shingle is hashed (MD5) and mapped to one of 32 dimensions.
3. **Counting**: The dimension value is incremented for each shingle that maps to it.
4. **Normalization**: The vector is L2-normalized.

Similarity is computed via cosine similarity between two normalized vectors.

!!! warning
    Hash-based embeddings provide only basic similarity matching. They work well for exact or near-exact text overlap but do not capture semantic meaning. For production use, integrate real embedding models (e.g., `sentence-transformers`, OpenAI embeddings) and store vectors in a dedicated vector database (e.g., Pinecone, Weaviate, pgvector).
