"""Runner — the execution engine of the Flux framework."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable

from .agent import Agent
from .config import FluxConfig, get_config
from .context import RunContext, ToolContext, Usage
from .events import Event, get_event_bus, AGENT_START, AGENT_END, LLM_START, LLM_END, TOOL_START, TOOL_END, HANDOFF, RUN_START, RUN_END
from .exceptions import (
    FluxError,
    HandoffError,
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
    ModelBehaviorError,
    OutputGuardrailTripwireTriggered,
    ProviderError,
    ToolError,
)
from .handoffs.handoff import Handoff
from .handoffs.router import find_handoff_by_tool_name
from .models.base import (
    Message,
    Model,
    ModelRequest,
    ModelResponse,
    ModelSettings,
    ToolDef,
)
from .models.registry import get_default_registry
from .streaming.events import (
    AgentUpdatedEvent,
    MessageCompleteEvent,
    StreamEvent,
    TextDeltaEvent,
    ToolCallEvent,
    UsageEvent,
)
from .tools.base import Tool, ToolResult


@dataclass
class RunResult:
    """Result of a completed agent run."""

    final_output: Any = None
    last_agent: Agent | None = None
    usage: Usage = field(default_factory=Usage)
    messages: list[Message] = field(default_factory=list)
    handoffs: list[dict[str, Any]] = field(default_factory=list)
    turns: int = 0


class StreamResult:
    """Result of a streamed agent run."""

    def __init__(self, agent: Agent, gen: AsyncIterator[StreamEvent]) -> None:
        self._agent = agent
        self._gen = gen
        self.current_agent: Agent = agent

    def __aiter__(self) -> AsyncIterator[StreamEvent]:
        return self._gen

    async def receive(self) -> StreamEvent:
        return await self._gen.__anext__()


class Runner:
    """Execution engine for Flux agents."""

    @staticmethod
    async def run(
        agent: Agent,
        input: str | list[Message],
        *,
        context: Any = None,
        config: FluxConfig | None = None,
        session: Any = None,
        model: Model | None = None,
    ) -> RunResult:
        """Run an agent to completion.

        Args:
            agent: The agent to run.
            input: User input as string or message list.
            context: Optional user context object.
            config: Optional configuration override.
            session: Optional session for conversation persistence.
            model: Optional model override.

        Returns:
            RunResult with the agent's final output.
        """
        cfg = config or get_config()
        bus = get_event_bus() if cfg.event_bus_enabled else None
        run_ctx: RunContext = RunContext(user_context=context)
        current_agent = agent
        messages: list[Message] = []
        all_handoffs: list[dict[str, Any]] = []
        total_usage = Usage()

        # Load session history first, then add new user input
        if session:
            session_msgs = await session.get_messages()
            for sm in session_msgs:
                messages.append(Message(role=sm["role"], content=sm.get("content", "")))

        # Initialize messages
        if isinstance(input, str):
            messages.append(Message(role="user", content=input))
        else:
            messages.extend(input)

        # Resolve model
        resolved_model = model or _resolve_model(current_agent, cfg)

        # Emit run start
        if bus:
            bus.emit(Event(type=RUN_START, data={"agent": current_agent.name}))

        max_turns = agent.settings.max_turns or cfg.default_max_turns

        try:
            for turn in range(max_turns):
                run_ctx.turn_count = turn + 1

                # Emit agent start
                if bus:
                    bus.emit(Event(type=AGENT_START, data={"agent": current_agent.name}))

                # Run input guardrails (turn 0 only)
                if turn == 0:
                    await _run_input_guardrails(current_agent, input if isinstance(input, str) else "", run_ctx)

                # Build tool definitions
                tool_defs = _build_tool_defs(current_agent)

                # Build request
                system_prompt = current_agent.get_instructions(run_ctx)
                settings = current_agent.settings.model_settings.resolve(cfg.default_model_settings)

                request = ModelRequest(
                    messages=messages,
                    system_prompt=system_prompt or None,
                    tools=tool_defs if tool_defs else None,
                    settings=settings,
                )

                # Call model
                if bus:
                    bus.emit(Event(type=LLM_START, data={"agent": current_agent.name}))

                response = await resolved_model.complete(request)

                if bus:
                    bus.emit(Event(type=LLM_END, data={"agent": current_agent.name}))

                # Accumulate usage
                if response.usage:
                    total_usage += response.usage

                # Process response
                if response.tool_calls:
                    # Add assistant message with tool calls
                    messages.append(
                        Message(
                            role="assistant",
                            content=response.content,
                            tool_calls=response.tool_calls,
                        )
                    )

                    # Execute tools and handoffs
                    handoff_triggered = await _execute_tools_and_handoffs(
                        current_agent, response.tool_calls, messages, run_ctx, bus
                    )

                    # Check if a handoff was triggered
                    if handoff_triggered:
                        new_agent, handoff_data = handoff_triggered

                        # Inherit model from parent if target has none
                        if new_agent.model is None:
                            new_agent = new_agent.clone(model=current_agent.model)

                        all_handoffs.append(handoff_data)

                        if bus:
                            bus.emit(Event(type=HANDOFF, data=handoff_data))

                        current_agent = new_agent

                        # Switch model if the new agent has a different model
                        resolved_model = _resolve_model(current_agent, cfg)

                        if bus:
                            bus.emit(Event(type=AGENT_END, data={"agent": current_agent.name}))

                        continue

                    # Continue loop with tool results
                    continue

                elif response.content:
                    # Agent produced final text output
                    messages.append(Message(role="assistant", content=response.content))

                    # Run output guardrails
                    await _run_output_guardrails(current_agent, response.content, run_ctx)

                    # Save to session if available
                    if session:
                        await session.add_messages([
                            {"role": "user", "content": input if isinstance(input, str) else str(input)},
                            {"role": "assistant", "content": response.content},
                        ])

                    return RunResult(
                        final_output=response.content,
                        last_agent=current_agent,
                        usage=total_usage,
                        messages=messages,
                        handoffs=all_handoffs,
                        turns=turn + 1,
                    )

                else:
                    raise ModelBehaviorError("Model returned empty response")

            raise MaxTurnsExceeded(f"Exceeded {cfg.default_max_turns} turns")

        finally:
            if bus:
                bus.emit(Event(type=RUN_END, data={"agent": current_agent.name}))

    @staticmethod
    def run_sync(
        agent: Agent,
        input: str | list[Message],
        **kwargs: Any,
    ) -> RunResult:
        """Synchronous wrapper for Runner.run()."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an existing event loop — create a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, Runner.run(agent, input, **kwargs))
                return future.result()
        else:
            return asyncio.run(Runner.run(agent, input, **kwargs))

    @staticmethod
    async def run_streamed(
        agent: Agent,
        input: str | list[Message],
        *,
        context: Any = None,
        config: FluxConfig | None = None,
        model: Model | None = None,
    ) -> StreamResult:
        """Run an agent with streaming output."""
        cfg = config or get_config()
        resolved_model = model or _resolve_model(agent, cfg)

        messages: list[Message] = []
        if isinstance(input, str):
            messages.append(Message(role="user", content=input))
        else:
            messages.extend(input)

        async def _stream_gen() -> AsyncIterator[StreamEvent]:
            run_ctx = RunContext(user_context=context)
            current_agent = agent
            current_model = resolved_model
            total_usage = Usage()

            for turn in range(cfg.default_max_turns):
                run_ctx.turn_count = turn + 1
                yield AgentUpdatedEvent(agent_name=current_agent.name)

                system_prompt = current_agent.get_instructions(run_ctx)
                tool_defs = _build_tool_defs(current_agent)
                settings = current_agent.settings.model_settings.resolve(cfg.default_model_settings)

                request = ModelRequest(
                    messages=messages,
                    system_prompt=system_prompt or None,
                    tools=tool_defs if tool_defs else None,
                    settings=settings,
                    stream=True,
                )

                content_buffer = ""
                tool_calls: list = []

                async for chunk in current_model.stream(request):
                    if chunk.delta_text:
                        content_buffer += chunk.delta_text
                        yield TextDeltaEvent(delta=chunk.delta_text)

                    if chunk.tool_call:
                        tool_calls.append(chunk.tool_call)
                        yield ToolCallEvent(
                            tool_call_id=chunk.tool_call.id,
                            name=chunk.tool_call.name,
                            arguments=chunk.tool_call.arguments,
                        )

                    if chunk.usage:
                        total_usage += chunk.usage
                        yield UsageEvent(
                            input_tokens=chunk.usage.input_tokens,
                            output_tokens=chunk.usage.output_tokens,
                            total_tokens=chunk.usage.total_tokens,
                        )

                    if chunk.done:
                        break

                # Process completed message
                yield MessageCompleteEvent(
                    content=content_buffer if content_buffer else None,
                    tool_calls=[ToolCallEvent(
                        tool_call_id=tc.id,
                        name=tc.name,
                        arguments=tc.arguments,
                    ) for tc in tool_calls],
                )

                if tool_calls:
                    messages.append(
                        Message(role="assistant", content=content_buffer or None, tool_calls=tool_calls)
                    )

                    handoff_triggered = await _execute_tools_and_handoffs(
                        current_agent, tool_calls, messages, run_ctx, None
                    )

                    if handoff_triggered:
                        new_agent, _ = handoff_triggered
                        current_agent = new_agent
                        current_model = _resolve_model(current_agent, cfg)
                        yield AgentUpdatedEvent(agent_name=current_agent.name)
                        continue

                    continue

                elif content_buffer:
                    return

            yield UsageEvent(
                input_tokens=total_usage.input_tokens,
                output_tokens=total_usage.output_tokens,
                total_tokens=total_usage.total_tokens,
            )

        return StreamResult(agent, _stream_gen())


# ─── Internal Helpers ───────────────────────────────────────────────


def _resolve_model(agent: Agent, config: FluxConfig) -> Model:
    """Resolve the model for an agent."""
    if isinstance(agent.model, Model):
        return agent.model
    if isinstance(agent.model, str):
        registry = config.model_registry or get_default_registry()
        return registry.resolve(agent.model)
    # Use config default
    registry = config.model_registry or get_default_registry()
    return registry.resolve(config.default_model)


def _build_tool_defs(agent: Agent) -> list[ToolDef]:
    """Build tool definitions including handoff tools."""
    tool_defs: list[ToolDef] = []

    # Regular tools
    for tool in agent.tools:
        tool_defs.append(
            ToolDef(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters_schema,
            )
        )

    # Handoff tools
    for h in agent.handoffs:
        if isinstance(h, Agent):
            handoff = Handoff(source=agent, target=h)
        else:
            handoff = h

        tool_defs.append(
            ToolDef(
                name=handoff.tool_name,
                description=handoff.tool_description,
                parameters={"type": "object", "properties": {}, "required": []},
                strict=False,
            )
        )

    return tool_defs


async def _execute_tools_and_handoffs(
    agent: Agent,
    tool_calls: list,
    messages: list[Message],
    run_ctx: RunContext,
    bus: Any,
) -> tuple[Agent, dict[str, Any]] | None:
    """Execute tool calls and check for handoffs.

    Returns (new_agent, handoff_data) if a handoff was triggered, else None.
    """
    # Check if any tool call is a handoff
    handoff_tool_names = set()
    for h in agent.handoffs:
        if isinstance(h, Agent):
            handoff_tool_names.add(f"transfer_to_{h.name}")
        else:
            handoff_tool_names.add(h.tool_name)

    for tc in tool_calls:
        if tc.name in handoff_tool_names:
            # Find the handoff
            handoff = find_handoff_by_tool_name(agent.handoffs if isinstance(agent.handoffs, list) else list(agent.handoffs), tc.name)
            if handoff:
                tool_ctx = ToolContext(
                    run_context=run_ctx,
                    tool_name=tc.name,
                    tool_call_id=tc.id,
                    tool_arguments=tc.arguments,
                )
                handoff_data = {
                    "source": agent.name,
                    "target": handoff.target.name,
                    "tool_name": tc.name,
                }
                return (handoff.target, handoff_data)

        # Regular tool execution
        tool = _find_tool(agent, tc.name)
        if tool:
            if bus:
                bus.emit(Event(type=TOOL_START, data={"tool": tc.name, "args": tc.arguments}))

            tool_ctx = ToolContext(
                run_context=run_ctx,
                tool_name=tc.name,
                tool_call_id=tc.id,
                tool_arguments=tc.arguments,
            )

            try:
                args = json.loads(tc.arguments) if tc.arguments else {}
            except json.JSONDecodeError:
                args = {}

            result = await tool.execute(tool_ctx, args)

            if bus:
                bus.emit(Event(type=TOOL_END, data={"tool": tc.name, "success": result.success}))

            # Add tool result message
            messages.append(
                Message(
                    role="tool",
                    content=result.output,
                    tool_call_id=tc.id,
                    name=tc.name,
                )
            )
        else:
            # Unknown tool — add error message
            messages.append(
                Message(
                    role="tool",
                    content=f"Error: Tool '{tc.name}' not found",
                    tool_call_id=tc.id,
                    name=tc.name,
                )
            )

    return None


def _find_tool(agent: Agent, name: str) -> Tool | None:
    """Find a tool by name in the agent's tool list."""
    for tool in agent.tools:
        if tool.name == name:
            return tool
    return None


async def _run_input_guardrails(
    agent: Agent, user_input: str, run_ctx: RunContext
) -> None:
    """Run input guardrails."""
    for g in agent.guardrails:
        if hasattr(g, "check") and hasattr(g, "name") and getattr(g, "guardrail_type", None) == "input":
            result = await g.check(user_input, run_ctx)
            if not result.passed:
                raise InputGuardrailTripwireTriggered(
                    g.name, result.message or "Input guardrail triggered"
                )


async def _run_output_guardrails(
    agent: Agent, output: str, run_ctx: RunContext
) -> None:
    """Run output guardrails."""
    for g in agent.guardrails:
        if hasattr(g, "check") and hasattr(g, "name") and getattr(g, "guardrail_type", None) == "output":
            result = await g.check(output, run_ctx)
            if not result.passed:
                raise OutputGuardrailTripwireTriggered(
                    g.name, result.message or "Output guardrail triggered"
                )
