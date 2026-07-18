"""Tests for handoffs."""

from flux.agent import Agent
from flux.handoffs.handoff import Handoff, HandoffData
from flux.handoffs.router import find_handoff_by_tool_name, handoff_tool_names


def test_handoff_tool_name():
    source = Agent(name="router", instructions="Route")
    target = Agent(name="helper", instructions="Help")
    h = Handoff(source=source, target=target)
    assert h.tool_name == "transfer_to_helper"


def test_handoff_tool_description():
    source = Agent(name="router", instructions="Route")
    target = Agent(name="helper", instructions="Help")
    h = Handoff(source=source, target=target, description="Custom desc")
    assert h.tool_description == "Custom desc"


def test_handoff_default_description():
    source = Agent(name="router", instructions="Route")
    target = Agent(name="helper", instructions="Help")
    h = Handoff(source=source, target=target)
    assert "helper" in h.tool_description


def test_find_handoff_by_tool_name():
    source = Agent(name="router", instructions="Route")
    target1 = Agent(name="helper", instructions="Help")
    target2 = Agent(name="coder", instructions="Code")
    handoffs = [
        Handoff(source=source, target=target1),
        Handoff(source=source, target=target2),
    ]

    found = find_handoff_by_tool_name(handoffs, "transfer_to_coder")
    assert found is not None
    assert found.target.name == "coder"

    not_found = find_handoff_by_tool_name(handoffs, "transfer_to_unknown")
    assert not_found is None


def test_handoff_tool_names():
    source = Agent(name="router", instructions="Route")
    targets = [Agent(name=f"agent_{i}", instructions="Test") for i in range(3)]
    handoffs = [Handoff(source=source, target=t) for t in targets]

    names = handoff_tool_names(handoffs)
    assert len(names) == 3
    assert "transfer_to_agent_0" in names
    assert "transfer_to_agent_2" in names
