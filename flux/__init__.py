"""Flux — A Python-first Agentic AI Framework.

Provider-agnostic, async-first, middleware-driven.
"""

__version__ = "0.1.0"

# Core
from .agent import Agent, AgentSettings
from .config import FluxConfig, get_config, set_config
from .context import RunContext, ToolContext, Usage
from .exceptions import (
    ConfigurationError,
    FluxError,
    GuardrailTripwireError,
    HandoffError,
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
    ModelBehaviorError,
    OutputGuardrailTripwireTriggered,
    ProviderError,
    ToolError,
    ToolTimeoutError,
    UserError,
)

# Models
from .models.base import (
    Message,
    Model,
    ModelRequest,
    ModelResponse,
    ModelSettings,
    StreamChunk,
    ToolCall,
    ToolDef,
)
from .models.registry import ModelRegistry, get_default_registry, set_default_registry

# Tools
from .tools.base import Tool, ToolResult
from .tools.decorator import FunctionTool, tool
from .tools.registry import ToolRegistry

# Handoffs
from .handoffs.handoff import Handoff, HandoffData

# Guardrails
from .guardrails.base import GuardrailResult, InputGuardrail, OutputGuardrail
from .guardrails.builtins import PIIGuardrail, ProfanityGuardrail, LengthGuardrail

# Runner
from .runner import Runner, RunResult, StreamResult

# Streaming
from .streaming.events import (
    AgentUpdatedEvent,
    ErrorEvent,
    MessageCompleteEvent,
    StreamEvent,
    TextDeltaEvent,
    ToolCallDeltaEvent,
    ToolCallEvent,
    UsageEvent,
)

# Events
from .events.bus import Event, EventBus, get_event_bus, set_event_bus

# Tracing
from .tracing.base import Span, SpanData, SpanError, Tracer
from .tracing.console import ConsoleTracer
from .tracing.file import FileTracer

# Sessions
from .sessions.base import Session
from .sessions.in_memory import InMemorySession
from .sessions.sqlite import SQLiteSession

# Memory
from .memory.base import Memory, MemoryEntry
from .memory.conversation import ConversationMemory
from .memory.vector import VectorMemory

# Middleware
from .middleware.base import Middleware, RequestContext, Response
from .middleware.cache import CacheMiddleware
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.retry import RetryMiddleware

# Built-in tools
from .tools.builtins import FileReadTool, FileWriteTool, ShellTool

__all__ = [
    # Core
    "Agent",
    "AgentSettings",
    "Runner",
    "RunResult",
    "StreamResult",
    "FluxConfig",
    "get_config",
    "set_config",
    "RunContext",
    "ToolContext",
    "Usage",
    # Models
    "Model",
    "ModelRequest",
    "ModelResponse",
    "ModelSettings",
    "StreamChunk",
    "Message",
    "ToolCall",
    "ToolDef",
    "ModelRegistry",
    "get_default_registry",
    "set_default_registry",
    # Tools
    "Tool",
    "ToolResult",
    "FunctionTool",
    "tool",
    "ToolRegistry",
    "ShellTool",
    "FileReadTool",
    "FileWriteTool",
    # Handoffs
    "Handoff",
    "HandoffData",
    # Guardrails
    "GuardrailResult",
    "InputGuardrail",
    "OutputGuardrail",
    "LengthGuardrail",
    "ProfanityGuardrail",
    "PIIGuardrail",
    # Streaming
    "StreamEvent",
    "TextDeltaEvent",
    "ToolCallDeltaEvent",
    "ToolCallEvent",
    "MessageCompleteEvent",
    "UsageEvent",
    "ErrorEvent",
    "AgentUpdatedEvent",
    # Events
    "Event",
    "EventBus",
    "get_event_bus",
    "set_event_bus",
    # Tracing
    "Span",
    "SpanData",
    "SpanError",
    "Tracer",
    "ConsoleTracer",
    "FileTracer",
    # Sessions
    "Session",
    "InMemorySession",
    "SQLiteSession",
    # Memory
    "Memory",
    "MemoryEntry",
    "ConversationMemory",
    "VectorMemory",
    # Middleware
    "Middleware",
    "RequestContext",
    "Response",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "CacheMiddleware",
    "RetryMiddleware",
    # Exceptions
    "FluxError",
    "MaxTurnsExceeded",
    "ModelBehaviorError",
    "UserError",
    "ToolError",
    "ToolTimeoutError",
    "GuardrailTripwireError",
    "InputGuardrailTripwireTriggered",
    "OutputGuardrailTripwireTriggered",
    "HandoffError",
    "ProviderError",
    "ConfigurationError",
]
