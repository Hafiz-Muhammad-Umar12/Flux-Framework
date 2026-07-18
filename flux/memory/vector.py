"""Simple vector memory using hash-based embeddings."""

from __future__ import annotations

import hashlib
import math
from typing import Any

from .base import MemoryEntry


class VectorMemory:
    """Simple in-memory vector store using hash-based embeddings.

    For production use, replace with real embeddings (e.g., sentence-transformers).
    """

    def __init__(self) -> None:
        self._entries: list[tuple[list[float], MemoryEntry]] = []

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Search by cosine similarity of hash-based embeddings."""
        if not self._entries:
            return []

        query_vec = _text_to_vector(query)
        scored: list[tuple[float, MemoryEntry]] = []

        for vec, entry in self._entries:
            sim = _cosine_similarity(query_vec, vec)
            scored.append((sim, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    async def store(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Store a memory entry."""
        vec = _text_to_vector(content)
        entry = MemoryEntry(
            content=content,
            metadata=metadata or {},
        )
        self._entries.append((vec, entry))

    async def clear(self) -> None:
        self._entries.clear()


def _text_to_vector(text: str) -> list[float]:
    """Convert text to a simple hash-based vector (32 dimensions)."""
    text = text.lower()
    vec = [0.0] * 32
    # Use shingling (3-char n-grams) for basic similarity
    for i in range(len(text) - 2):
        shingle = text[i : i + 3]
        h = int(hashlib.md5(shingle.encode()).hexdigest(), 16)
        idx = h % 32
        vec[idx] += 1.0
    # Normalize
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (norm_a * norm_b)
