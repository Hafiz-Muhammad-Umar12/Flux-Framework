"""Global configuration for the Flux framework."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models.base import ModelSettings
from .models.registry import ModelRegistry


@dataclass
class FluxConfig:
    """Global configuration."""

    default_model: str = "llama3.2"
    default_max_turns: int = 10
    default_model_settings: ModelSettings = field(default_factory=ModelSettings)
    event_bus_enabled: bool = True
    tracing_enabled: bool = False
    log_level: str = "INFO"
    model_registry: ModelRegistry | None = None


# Global config singleton
_config: FluxConfig | None = None


def get_config() -> FluxConfig:
    """Get the global configuration."""
    global _config
    if _config is None:
        _config = FluxConfig()
    return _config


def set_config(config: FluxConfig) -> None:
    """Set the global configuration."""
    global _config
    _config = config
