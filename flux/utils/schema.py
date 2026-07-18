"""JSON Schema generation from Python functions."""

from __future__ import annotations

import inspect
import typing
from typing import Any, get_type_hints


# Python type → JSON Schema type mapping
_TYPE_MAP: dict[type, dict[str, str]] = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    bool: {"type": "boolean"},
    list: {"type": "array"},
    dict: {"type": "object"},
}


def _resolve_type_annotation(annotation: Any) -> dict[str, Any]:
    """Convert a Python type annotation to JSON Schema."""
    if annotation is inspect.Parameter.empty or annotation is None:
        return {"type": "string"}

    # Handle string annotations (from __future__ import annotations)
    if isinstance(annotation, str):
        annotation = _eval_string_annotation(annotation)

    # Direct type mapping
    if annotation in _TYPE_MAP:
        return dict(_TYPE_MAP[annotation])

    # Handle typing module generics
    origin = getattr(annotation, "__origin__", None)

    if origin is list:
        args = getattr(annotation, "__args__", None)
        if args:
            return {"type": "array", "items": _resolve_type_annotation(args[0])}
        return {"type": "array"}

    if origin is dict:
        return {"type": "object"}

    if origin is typing.Union:
        args = getattr(annotation, "__args__", ())
        # Handle Optional[T] = Union[T, None]
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _resolve_type_annotation(non_none[0])
        return {"anyOf": [_resolve_type_annotation(a) for a in non_none]}

    if origin is typing.Literal:
        args = getattr(annotation, "__args__", ())
        return {"enum": list(args)}

    return {"type": "string"}


def _eval_string_annotation(annotation: str) -> Any:
    """Try to evaluate a string annotation."""
    try:
        return eval(annotation, {"typing": typing, "__builtins__": {}})
    except Exception:
        return str


def _extract_docstring_params(func: Any) -> dict[str, str]:
    """Extract parameter descriptions from docstrings (Google-style)."""
    doc = inspect.getdoc(func) or ""
    params: dict[str, str] = {}
    lines = doc.split("\n")
    in_args = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("args:") or stripped.lower().startswith(
            "parameters:"
        ):
            in_args = True
            continue
        if in_args:
            if ":" in stripped and not stripped.startswith(" "):
                parts = stripped.split(":", 1)
                name = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ""
                params[name] = desc
            elif stripped == "" or (not stripped.startswith(" ") and ":" not in stripped):
                in_args = False
    return params


# Parameters to skip from schema (context injection)
_SKIP_PARAM_NAMES = {"ctx", "context", "tool_context", "run_context"}


def function_to_schema(func: Any) -> dict[str, Any]:
    """Convert a Python function to a JSON Schema dict.

    Suitable for use as the `parameters` field in a tool definition.
    """
    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    doc_params = _extract_docstring_params(func)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in _SKIP_PARAM_NAMES:
            continue

        annotation = hints.get(name, param.annotation)
        prop = _resolve_type_annotation(annotation)

        # Add description from docstring
        if name in doc_params:
            prop["description"] = doc_params[name]

        properties[name] = prop

        if param.default is inspect.Parameter.empty:
            required.append(name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema
