"""Pretty-printing utilities."""

from __future__ import annotations

from typing import Any


def pretty_result(result: Any) -> str:
    """Pretty-print a RunResult."""
    lines = [
        "═══ Flux Run Result ═══",
        f"  Agent:  {result.last_agent.name if result.last_agent else 'N/A'}",
        f"  Turns:  {result.turns}",
        f"  Tokens: {result.usage.total_tokens} "
        f"(in={result.usage.input_tokens}, out={result.usage.output_tokens})",
        "───────────────────────",
        f"  Output: {result.final_output}",
        "═══════════════════════",
    ]
    return "\n".join(lines)


def pretty_error(error: Exception) -> str:
    """Pretty-print an error."""
    return f"✗ {type(error).__name__}: {error}"


def pretty_tool_call(name: str, args: dict[str, Any]) -> str:
    """Pretty-print a tool call."""
    args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
    return f"→ {name}({args_str})"


def pretty_stream_delta(delta: str) -> str:
    """Print a streaming text delta (no newline)."""
    print(delta, end="", flush=True)
    return delta
