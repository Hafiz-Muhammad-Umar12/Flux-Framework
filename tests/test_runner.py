"""Tests for Runner."""

import pytest

from flux.agent import Agent
from flux.context import RunContext, Usage
from flux.exceptions import InputGuardrailTripwireTriggered, MaxTurnsExceeded, OutputGuardrailTripwireTriggered
from flux.guardrails.base import GuardrailResult
from flux.handoffs.handoff import Handoff
from flux.models.base import ModelResponse, ToolCall
from flux.runner import Runner
from flux.tools.decorator import tool

from .conftest import FakeModel, fake_response, fake_tool_response


@pytest.mark.asyncio
async def test_basic_run():
    model = FakeModel([fake_response("Hello world!")])
    agent = Agent(name="test", instructions="Be helpful", model=model)
    result = await Runner.run(agent, "Hi")

    assert result.final_output == "Hello world!"
    assert result.turns == 1
    assert result.last_agent.name == "test"
    assert result.usage.input_tokens == 10


@pytest.mark.asyncio
async def test_multi_turn_tool_call():
    """Agent calls a tool, then responds with final text."""
    @tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    model = FakeModel([
        fake_tool_response("add", {"a": 2, "b": 3}),
        fake_response("The answer is 5."),
    ])
    agent = Agent(name="calc", instructions="Use tools", model=model, tools=[add])
    result = await Runner.run(agent, "What is 2+3?")

    assert result.final_output == "The answer is 5."
    assert result.turns == 2
    assert model.call_count == 2


@pytest.mark.asyncio
async def test_max_turns_exceeded():
    """Infinite tool loop should raise MaxTurnsExceeded."""
    model = FakeModel([
        fake_tool_response("unknown_tool", {}),
        fake_tool_response("unknown_tool", {}),
        fake_tool_response("unknown_tool", {}),
    ])
    agent = Agent(name="loop", instructions="Loop forever", model=model)
    # Override max_turns to 2
    from flux.agent import AgentSettings
    agent = agent.clone(settings=AgentSettings(max_turns=2))

    with pytest.raises(MaxTurnsExceeded):
        await Runner.run(agent, "Go")


@pytest.mark.asyncio
async def test_handoff():
    """Test agent-to-agent handoff."""
    model = FakeModel([
        # First agent responds with handoff tool call
        ModelResponse(
            tool_calls=[ToolCall(id="call_1", name="transfer_to_helper", arguments="{}")],
        ),
        # Second agent responds with text
        fake_response("I'm the helper!"),
    ])
    router = Agent(name="router", instructions="Route to helper", model=model)
    helper = Agent(name="helper", instructions="Be helpful")
    router = router.clone(handoffs=(Handoff(source=router, target=helper),))

    result = await Runner.run(router, "Help me")
    assert result.final_output == "I'm the helper!"
    assert len(result.handoffs) == 1
    assert result.handoffs[0]["target"] == "helper"


@pytest.mark.asyncio
async def test_input_guardrail():
    """Input guardrail should block input."""
    class BlockAll:
        guardrail_type = "input"
        @property
        def name(self) -> str:
            return "block_all"
        async def check(self, user_input, context=None):
            return GuardrailResult(passed=False, message="Blocked")

    model = FakeModel([fake_response("Should not reach")])
    agent = Agent(
        name="guarded",
        instructions="Test",
        model=model,
        guardrails=(BlockAll(),),
    )

    with pytest.raises(InputGuardrailTripwireTriggered):
        await Runner.run(agent, "Hello")


@pytest.mark.asyncio
async def test_output_guardrail():
    """Output guardrail should block output."""
    class BlockOutput:
        guardrail_type = "output"
        @property
        def name(self) -> str:
            return "block_output"
        async def check(self, output, context=None):
            return GuardrailResult(passed=False, message="Bad output")

    model = FakeModel([fake_response("Bad content")])
    agent = Agent(
        name="guarded",
        instructions="Test",
        model=model,
        guardrails=(BlockOutput(),),
    )

    with pytest.raises(OutputGuardrailTripwireTriggered):
        await Runner.run(agent, "Hello")


@pytest.mark.asyncio
async def test_empty_response_raises():
    """Empty model response should raise ModelBehaviorError."""
    model = FakeModel([ModelResponse()])
    agent = Agent(name="empty", instructions="Test", model=model)

    from flux.exceptions import ModelBehaviorError
    with pytest.raises(ModelBehaviorError):
        await Runner.run(agent, "Hi")
