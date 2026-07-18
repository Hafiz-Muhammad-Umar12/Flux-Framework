"""Model registry for resolving model names to Model instances."""

from __future__ import annotations

from typing import Any

from .base import Model


class ModelRegistry:
    """Registry for resolving model names to Model instances."""

    def __init__(self) -> None:
        self._models: dict[str, Model] = {}
        self._providers: dict[str, Model] = {}

    def register(self, name: str, model: Model) -> None:
        """Register a model by exact name."""
        self._models[name] = model

    def register_provider(self, prefix: str, model: Model) -> None:
        """Register a model provider by prefix (e.g., 'ollama', 'openai')."""
        self._providers[prefix] = model

    def resolve(self, name: str) -> Model:
        """Resolve a model name to a Model instance.

        Tries exact match first, then prefix match (e.g., 'ollama/llama3').
        """
        if name in self._models:
            return self._models[name]

        # Try prefix match: "provider/model_name"
        if "/" in name:
            prefix = name.split("/", 1)[0]
            if prefix in self._providers:
                return self._providers[prefix]

        raise ValueError(
            f"Model '{name}' not found. "
            f"Available models: {list(self._models.keys())}. "
            f"Available providers: {list(self._providers.keys())}."
        )


# Global registry singleton
_default_registry: ModelRegistry | None = None


def get_default_registry() -> ModelRegistry:
    """Get the global model registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ModelRegistry()
    return _default_registry


def set_default_registry(registry: ModelRegistry) -> None:
    """Set the global model registry."""
    global _default_registry
    _default_registry = registry
