"""Tests for Agent."""

from flux.agent import Agent, AgentSettings
from flux.context import RunContext
from flux.models.base import ModelSettings


def test_agent_creation():
    agent = Agent(name="test", instructions="You are test")
    assert agent.name == "test"
    assert agent.instructions == "You are test"


def test_agent_immutability():
    agent = Agent(name="test", instructions="Hello")
    try:
        agent.name = "other"  # type: ignore
        assert False, "Should not be mutable"
    except AttributeError:
        pass


def test_agent_clone():
    agent = Agent(name="test", instructions="Hello")
    cloned = agent.clone(name="cloned")
    assert cloned.name == "cloned"
    assert cloned.instructions == "Hello"
    assert agent.name == "test"


def test_agent_dynamic_instructions():
    def dynamic(ctx: RunContext) -> str:
        return f"Context: {ctx.user_context}"

    agent = Agent(name="test", instructions=dynamic)
    ctx = RunContext(user_context="hello")
    assert agent.get_instructions(ctx) == "Context: hello"


def test_agent_static_instructions():
    agent = Agent(name="test", instructions="Static")
    assert agent.get_instructions() == "Static"


def test_agent_default_settings():
    agent = Agent(name="test")
    assert agent.settings.max_turns == 10
    assert isinstance(agent.settings.model_settings, ModelSettings)


def test_agent_custom_settings():
    settings = AgentSettings(max_turns=5, model_settings=ModelSettings(temperature=0.5))
    agent = Agent(name="test", settings=settings)
    assert agent.settings.max_turns == 5
    assert agent.settings.model_settings.temperature == 0.5
