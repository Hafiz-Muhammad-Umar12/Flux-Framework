"""Flux framework exceptions."""


class FluxError(Exception):
    """Base exception for all Flux errors."""


class MaxTurnsExceeded(FluxError):
    """Raised when the agent exceeds the maximum number of turns."""

    def __init__(self, message: str = "Maximum turns exceeded"):
        self.message = message
        super().__init__(message)


class ModelBehaviorError(FluxError):
    """Raised when the model produces unexpected output."""

    def __init__(self, message: str = "Model produced unexpected output"):
        self.message = message
        super().__init__(message)


class UserError(FluxError):
    """Raised on developer misuse of the framework."""

    def __init__(self, message: str = "Invalid framework usage"):
        self.message = message
        super().__init__(message)


class ToolError(FluxError):
    """Raised when a tool execution fails."""

    def __init__(self, tool_name: str, tool_error: str):
        self.tool_name = tool_name
        self.tool_error = tool_error
        super().__init__(f"Tool '{tool_name}' failed: {tool_error}")


class ToolTimeoutError(FluxError):
    """Raised when a tool execution times out."""

    def __init__(self, tool_name: str, timeout_seconds: float):
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Tool '{tool_name}' timed out after {timeout_seconds}s")


class GuardrailTripwireError(FluxError):
    """Raised when a guardrail tripwire is triggered."""

    def __init__(self, guardrail_name: str, details: str = ""):
        self.guardrail_name = guardrail_name
        self.details = details
        super().__init__(f"Guardrail '{guardrail_name}' triggered: {details}")


class InputGuardrailTripwireTriggered(GuardrailTripwireError):
    """Raised when an input guardrail is triggered."""

    def __init__(self, guardrail_name: str, details: str = ""):
        super().__init__(guardrail_name, details)


class OutputGuardrailTripwireTriggered(GuardrailTripwireError):
    """Raised when an output guardrail is triggered."""

    def __init__(self, guardrail_name: str, details: str = ""):
        super().__init__(guardrail_name, details)


class HandoffError(FluxError):
    """Raised when a handoff fails."""


class ProviderError(FluxError):
    """Raised when an LLM provider returns an error."""

    def __init__(self, provider: str, message: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"Provider '{provider}' error ({status_code}): {message}")


class ConfigurationError(FluxError):
    """Raised on invalid configuration."""
