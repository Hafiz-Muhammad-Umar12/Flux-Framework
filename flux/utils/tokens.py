"""Token counting utilities."""

from __future__ import annotations


def count_tokens(text: str, model: str | None = None) -> int:
    """Count tokens in text.

    Uses tiktoken if available, otherwise falls back to a rough estimate.
    """
    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model(model or "gpt-4")
        return len(encoding.encode(text))
    except Exception:
        # Rough estimate: ~4 chars per token
        return max(1, len(text) // 4)


def truncate_to_tokens(text: str, max_tokens: int, model: str | None = None) -> str:
    """Truncate text to fit within max_tokens."""
    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model(model or "gpt-4")
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return encoding.decode(tokens[:max_tokens])
    except Exception:
        # Rough estimate
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars]
